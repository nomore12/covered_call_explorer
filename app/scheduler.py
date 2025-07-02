import os
import yfinance as yf
import logging
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from decimal import Decimal

from .__init__ import app, db
from .models import Holding

scheduler = BackgroundScheduler()
is_scheduler_running = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_stock_price(ticker=None, notify_telegram=False):
    """
    yfinance를 사용해 주가를 업데이트하는 함수
    
    Args:
        ticker (str, optional): 특정 종목만 업데이트할 경우
        notify_telegram (bool): 텔레그램 알림 여부
    
    Returns:
        dict: 업데이트 결과 {'success': bool, 'message': str, 'updated': list}
    """
    with app.app_context():
        try:
            if ticker:
                holdings = Holding.query.filter_by(ticker=ticker.upper()).all()
                if not holdings:
                    return {
                        'success': False,
                        'message': f'{ticker} 종목을 찾을 수 없습니다.',
                        'updated': []
                    }
            else:
                holdings = Holding.query.filter(Holding.current_shares > 0).all()
            
            if not holdings:
                return {
                    'success': False,
                    'message': '업데이트할 보유 종목이 없습니다.',
                    'updated': []
                }
            
            updated_stocks = []
            failed_stocks = []
            
            for holding in holdings:
                try:
                    # yfinance로 주가 조회
                    stock = yf.Ticker(holding.ticker)
                    info = stock.info
                    
                    # 현재가 추출 (여러 필드 시도)
                    current_price = None
                    price_fields = ['regularMarketPrice', 'currentPrice', 'price', 'previousClose']
                    
                    for field in price_fields:
                        if field in info and info[field] is not None:
                            current_price = info[field]
                            break
                    
                    if current_price is None or current_price <= 0:
                        failed_stocks.append(f"{holding.ticker} (가격 정보 없음)")
                        continue
                    
                    # 기존 가격과 비교하여 변화가 있을 때만 업데이트
                    old_price = float(holding.current_market_price)
                    new_price = Decimal(str(current_price))
                    
                    if abs(float(new_price) - old_price) > 0.001:  # 0.001달러 이상 차이날 때만 업데이트
                        holding.current_market_price = new_price
                        holding.last_price_update_date = datetime.now().date()
                        
                        updated_stocks.append({
                            'ticker': holding.ticker,
                            'old_price': old_price,
                            'new_price': float(new_price),
                            'change': float(new_price) - old_price,
                            'change_pct': ((float(new_price) - old_price) / old_price * 100) if old_price > 0 else 0
                        })
                        
                        logger.info(f"Updated {holding.ticker}: ${old_price:.3f} -> ${float(new_price):.3f}")
                    
                except Exception as e:
                    failed_stocks.append(f"{holding.ticker} ({str(e)[:50]}...)")
                    logger.error(f"Failed to update {holding.ticker}: {e}")
            
            # 데이터베이스에 변경사항 저장
            if updated_stocks:
                db.session.commit()
            
            # 결과 메시지 생성
            message_parts = []
            if updated_stocks:
                message_parts.append(f"✅ {len(updated_stocks)}개 종목 업데이트 완료")
                for stock in updated_stocks[:5]:  # 최대 5개만 표시
                    change_symbol = "📈" if stock['change'] > 0 else "📉" if stock['change'] < 0 else "➡️"
                    message_parts.append(
                        f"{change_symbol} {stock['ticker']}: ${stock['old_price']:.3f} → ${stock['new_price']:.3f} "
                        f"({stock['change']:+.3f}, {stock['change_pct']:+.2f}%)"
                    )
                if len(updated_stocks) > 5:
                    message_parts.append(f"... 외 {len(updated_stocks) - 5}개")
            
            if failed_stocks:
                message_parts.append(f"❌ {len(failed_stocks)}개 종목 업데이트 실패")
                for failed in failed_stocks[:3]:  # 최대 3개만 표시
                    message_parts.append(f"  • {failed}")
                if len(failed_stocks) > 3:
                    message_parts.append(f"  ... 외 {len(failed_stocks) - 3}개")
            
            return {
                'success': len(updated_stocks) > 0 or len(failed_stocks) == 0,
                'message': '\n'.join(message_parts) if message_parts else '변경된 주가가 없습니다.',
                'updated': updated_stocks,
                'failed': failed_stocks
            }
            
        except Exception as e:
            logger.error(f"Error in update_stock_price: {e}")
            return {
                'success': False,
                'message': f'주가 업데이트 중 오류 발생: {e}',
                'updated': [],
                'failed': []
            }

def scheduled_price_update():
    """스케줄러에서 호출되는 자동 주가 업데이트 함수"""
    logger.info("Starting scheduled price update...")
    
    # 주말 체크 (토요일=5, 일요일=6)
    if datetime.now().weekday() >= 5:
        logger.info("Weekend detected, skipping price update")
        return
    
    # 한국 시간 기준으로 미국 시장 시간 체크 (대략적으로)
    current_time = datetime.now().time()
    
    # 미국 시장이 열려있을 가능성이 높은 시간만 업데이트
    # 한국시간 기준 22:30 ~ 다음날 05:00 (서머타임 고려 안함, 대략적)
    market_open_start = time(22, 30)  # 22:30
    market_open_end = time(5, 0)      # 05:00
    
    is_market_hours = current_time >= market_open_start or current_time <= market_open_end
    
    if not is_market_hours:
        # 시장 시간이 아니어도 업데이트 (종가 반영 등을 위해)
        logger.info("Outside market hours, but proceeding with update")
    
    result = update_stock_price()
    
    if result['updated']:
        logger.info(f"Scheduled update completed: {len(result['updated'])} stocks updated")
    else:
        logger.info("Scheduled update completed: no changes")

def start_scheduler():
    """스케줄러 시작"""
    global is_scheduler_running
    
    if is_scheduler_running:
        logger.info("Scheduler is already running")
        return
    
    try:
        # 한국 시간 기준으로 스케줄링
        # 오전 9시 (장 시작 후)
        scheduler.add_job(
            func=scheduled_price_update,
            trigger=CronTrigger(hour=9, minute=0, timezone='Asia/Seoul'),
            id='morning_price_update',
            name='Morning Price Update',
            replace_existing=True
        )
        
        # 오후 6시 (장 마감 후)
        scheduler.add_job(
            func=scheduled_price_update,
            trigger=CronTrigger(hour=18, minute=0, timezone='Asia/Seoul'),
            id='evening_price_update',
            name='Evening Price Update',
            replace_existing=True
        )
        
        scheduler.start()
        is_scheduler_running = True
        logger.info("Price update scheduler started successfully")
        logger.info("Scheduled times: 09:00 and 18:00 (Asia/Seoul)")
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

def stop_scheduler():
    """스케줄러 중지"""
    global is_scheduler_running
    
    if scheduler.running:
        scheduler.shutdown()
        is_scheduler_running = False
        logger.info("Scheduler stopped")

def get_scheduler_status():
    """스케줄러 상태 조회"""
    if not is_scheduler_running:
        return "스케줄러가 실행되지 않았습니다."
    
    jobs = scheduler.get_jobs()
    if not jobs:
        return "스케줄러가 실행 중이지만 등록된 작업이 없습니다."
    
    status_lines = ["📅 스케줄러 상태: 실행 중"]
    for job in jobs:
        next_run = job.next_run_time
        if next_run:
            status_lines.append(f"  • {job.name}: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            status_lines.append(f"  • {job.name}: 다음 실행 시간 미정")
    
    return '\n'.join(status_lines)