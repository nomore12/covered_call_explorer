import os
import yfinance as yf
import logging
import time
import asyncio
from datetime import datetime, time as dt_time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from decimal import Decimal
import random

from .__init__ import app, db
from .models import Holding

scheduler = BackgroundScheduler()
is_scheduler_running = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 텔레그램 봇 토큰과 허용된 사용자 ID
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ALLOWED_USER_IDS_STR = os.environ.get('ALLOWED_TELEGRAM_USER_IDS', '')
ALLOWED_USER_IDS = [int(user_id.strip()) for user_id in ALLOWED_USER_IDS_STR.split(',') if user_id.strip()]

async def send_telegram_notification(message):
    """텔레그램으로 알림 메시지 전송"""
    if not TELEGRAM_BOT_TOKEN or not ALLOWED_USER_IDS:
        logger.warning("Telegram bot token or user IDs not configured, skipping notification")
        return
    
    try:
        import aiohttp
        
        for user_id in ALLOWED_USER_IDS:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': user_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        logger.info(f"Notification sent to user {user_id}")
                    else:
                        logger.error(f"Failed to send notification to user {user_id}: {response.status}")
                        
    except Exception as e:
        logger.error(f"Error sending telegram notification: {e}")

def send_notification_sync(message):
    """동기 함수에서 비동기 텔레그램 알림 호출"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_telegram_notification(message))
        loop.close()
    except Exception as e:
        logger.error(f"Error in send_notification_sync: {e}")

def _get_price_yahoo_direct(ticker):
    """Yahoo Finance API 직접 호출"""
    import requests
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # 여러 Yahoo Finance 엔드포인트 시도
    urls = [
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
        f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}",
        f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=price"
    ]
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                # chart API 응답 처리
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    if 'meta' in result and 'regularMarketPrice' in result['meta']:
                        return result['meta']['regularMarketPrice']
                
                # quoteSummary API 응답 처리
                if 'quoteSummary' in data and 'result' in data['quoteSummary'] and data['quoteSummary']['result']:
                    result = data['quoteSummary']['result'][0]
                    if 'price' in result and 'regularMarketPrice' in result['price']:
                        price_info = result['price']['regularMarketPrice']
                        if 'raw' in price_info:
                            return price_info['raw']
                        
        except Exception as e:
            logger.warning(f"Yahoo direct API error for {ticker}: {e}")
            continue
    
    return None

def _get_price_alpha_vantage(ticker):
    """Alpha Vantage API 사용 (무료 API 키 필요)"""
    # 환경변수에서 API 키 확인
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        return None
    
    import requests
    
    url = f"https://www.alphavantage.co/query"
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': ticker,
        'apikey': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                return float(data['Global Quote']['05. price'])
    except:
        pass
    
    return None

def _get_price_yfinance_fallback(ticker):
    """yfinance 백업 시도 (긴 대기시간 포함)"""
    import yfinance as yf
    import requests
    
    try:
        # 긴 대기 후 yfinance 재시도
        time.sleep(random.uniform(5, 10))
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        })
        
        stock = yf.Ticker(ticker, session=session)
        
        # history 메소드로 시도 (더 안정적)
        hist = stock.history(period="1d", interval="1d")
        if not hist.empty and 'Close' in hist.columns:
            return float(hist['Close'].iloc[-1])
            
    except Exception as e:
        logger.warning(f"yfinance fallback failed for {ticker}: {e}")
    
    return None

def _get_price_fmp(ticker):
    """Financial Modeling Prep API 사용"""
    api_key = os.environ.get('FMP_API_KEY')
    if not api_key:
        return None
    
    import requests
    
    url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}"
    params = {'apikey': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0 and 'price' in data[0]:
                return float(data[0]['price'])
    except:
        pass
    
    return None

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
            
            for i, holding in enumerate(holdings):
                try:
                    # 요청 간격 조절 (429 에러 방지) - 더 긴 대기 시간
                    if i > 0:
                        delay = random.uniform(3.0, 7.0)  # 3-7초 랜덤 지연 (증가)
                        logger.info(f"Waiting {delay:.1f}s before updating {holding.ticker}")
                        time.sleep(delay)
                    
                    # 재시도 로직
                    current_price = None
                    max_retries = 5  # 재시도 횟수 증가
                    
                    # 여러 API를 순차적으로 시도하는 전략
                    api_methods = [
                        ('yahoo_direct', _get_price_yahoo_direct),
                        ('alpha_vantage', _get_price_alpha_vantage),
                        ('yfinance_fallback', _get_price_yfinance_fallback),
                        ('financial_modeling', _get_price_fmp)
                    ]
                    
                    for api_name, api_method in api_methods:
                        try:
                            logger.info(f"Trying {api_name} for {holding.ticker}")
                            current_price = api_method(holding.ticker)
                            
                            if current_price and current_price > 0:
                                logger.info(f"Success with {api_name} for {holding.ticker}: ${current_price:.3f}")
                                break
                            else:
                                logger.warning(f"{api_name} returned invalid price for {holding.ticker}: {current_price}")
                                
                        except Exception as e:
                            error_str = str(e).lower()
                            if any(x in error_str for x in ["429", "too many requests", "rate limit"]):
                                logger.warning(f"{api_name} rate limited for {holding.ticker}: {e}")
                                # 429 에러 시 다른 API로 즉시 전환
                                continue
                            else:
                                logger.error(f"{api_name} error for {holding.ticker}: {e}")
                                continue
                        
                        # API 간 간격
                        time.sleep(random.uniform(1, 2))
                    
                    if current_price is None or current_price <= 0:
                        failed_stocks.append(f"{holding.ticker} (모든 API 실패)")
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
                    error_msg = str(e)
                    if "429" in error_msg:
                        failed_stocks.append(f"{holding.ticker} (요청 한도 초과)")
                    else:
                        failed_stocks.append(f"{holding.ticker} ({error_msg[:50]}...)")
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
    market_open_start = dt_time(22, 30)  # 22:30
    market_open_end = dt_time(5, 0)      # 05:00
    
    is_market_hours = current_time >= market_open_start or current_time <= market_open_end
    
    if not is_market_hours:
        # 시장 시간이 아니어도 업데이트 (종가 반영 등을 위해)
        logger.info("Outside market hours, but proceeding with update")
    
    result = update_stock_price()
    
    # 텔레그램 알림 전송
    try:
        current_time_str = datetime.now().strftime('%H:%M')
        
        if result['updated'] or result['failed']:
            # 업데이트 결과가 있을 때만 알림
            message_parts = [f"🤖 <b>자동 주가 업데이트</b> ({current_time_str})"]
            message_parts.append("")
            
            if result['updated']:
                message_parts.append(f"✅ <b>{len(result['updated'])}개 종목 업데이트 완료</b>")
                for stock in result['updated'][:3]:  # 최대 3개만 표시
                    change_symbol = "📈" if stock['change'] > 0 else "📉" if stock['change'] < 0 else "➡️"
                    message_parts.append(
                        f"{change_symbol} <code>{stock['ticker']}</code>: "
                        f"${stock['old_price']:.3f} → ${stock['new_price']:.3f} "
                        f"({stock['change']:+.3f}, {stock['change_pct']:+.2f}%)"
                    )
                if len(result['updated']) > 3:
                    message_parts.append(f"... 외 {len(result['updated']) - 3}개")
                message_parts.append("")
            
            if result['failed']:
                message_parts.append(f"❌ <b>{len(result['failed'])}개 종목 업데이트 실패</b>")
                for failed in result['failed'][:2]:  # 최대 2개만 표시
                    message_parts.append(f"  • {failed}")
                if len(result['failed']) > 2:
                    message_parts.append(f"  ... 외 {len(result['failed']) - 2}개")
            
            notification_message = '\n'.join(message_parts)
            send_notification_sync(notification_message)
        
    except Exception as e:
        logger.error(f"Error sending scheduled update notification: {e}")
    
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