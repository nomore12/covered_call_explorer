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

from .models import Holding, Dividend, ExchangeRate, db
from flask import current_app
from .exchange_rate_service import update_exchange_rate

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

def _get_price_direct_yahoo(ticker, session=None):
    """Yahoo Finance API 직접 호출 (Docker 환경용)"""
    import requests
    
    if session is None:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        })
    
    # 여러 Yahoo Finance API 엔드포인트 시도
    endpoints = [
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
        f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}",
        f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=price,summaryDetail"
    ]
    
    for url in endpoints:
        try:
            logger.info(f"Trying direct API: {url}")
            response = session.get(url, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Got response for {ticker}: {len(str(data))} chars")
                
                # chart API 응답 처리
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    if 'meta' in result:
                        # 현재가 필드들 시도
                        price_fields = ['regularMarketPrice', 'currentPrice', 'price', 'previousClose']
                        for field in price_fields:
                            if field in result['meta'] and result['meta'][field] is not None:
                                price = float(result['meta'][field])
                                logger.info(f"Found {field} for {ticker}: ${price:.3f}")
                                return price
                
                # quoteSummary API 응답 처리
                if 'quoteSummary' in data and 'result' in data['quoteSummary'] and data['quoteSummary']['result']:
                    result = data['quoteSummary']['result'][0]
                    if 'price' in result and 'regularMarketPrice' in result['price']:
                        price_info = result['price']['regularMarketPrice']
                        if isinstance(price_info, dict) and 'raw' in price_info:
                            price = float(price_info['raw'])
                            logger.info(f"Found quoteSummary price for {ticker}: ${price:.3f}")
                            return price
                        elif isinstance(price_info, (int, float)):
                            price = float(price_info)
                            logger.info(f"Found direct price for {ticker}: ${price:.3f}")
                            return price
                            
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                
        except Exception as e:
            logger.warning(f"Direct API error for {url}: {e}")
            continue
    
    logger.error(f"All direct API endpoints failed for {ticker}")
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
    from .__init__ import get_app
    app = get_app()
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
                    # 간단한 간격 조절
                    if i > 0:
                        delay = random.uniform(2.0, 4.0)  # 2-4초 대기
                        logger.info(f"Waiting {delay:.1f}s before updating {holding.ticker}")
                        time.sleep(delay)
                    
                    # 간단한 yfinance history 방식 사용
                    current_price = None
                    
                    try:
                        import yfinance as yf
                        import requests
                        
                        # Docker 환경에서 User-Agent 설정이 중요함
                        session = requests.Session()
                        session.headers.update({
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'DNT': '1',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                        })
                        
                        # 세션과 함께 Ticker 생성
                        ticker_obj = yf.Ticker(holding.ticker, session=session)
                        
                        # 최근 1일 데이터 조회
                        hist = ticker_obj.history(period="1d", interval="1d")
                        
                        if not hist.empty and 'Close' in hist.columns:
                            current_price = float(hist['Close'].iloc[-1])
                            logger.info(f"Got price for {holding.ticker}: ${current_price:.3f}")
                        else:
                            # 1일 데이터가 없으면 5일 시도
                            hist = ticker_obj.history(period="5d", interval="1d")
                            if not hist.empty and 'Close' in hist.columns:
                                current_price = float(hist['Close'].iloc[-1])
                                logger.info(f"Got price for {holding.ticker} (5d): ${current_price:.3f}")
                            else:
                                # history도 실패하면 직접 API 호출 시도
                                logger.warning(f"yfinance history failed for {holding.ticker}, trying direct API")
                                current_price = _get_price_direct_yahoo(holding.ticker, session)
                            
                    except Exception as e:
                        logger.error(f"yfinance error for {holding.ticker}: {e}")
                        # 마지막 수단으로 직접 API 호출
                        try:
                            current_price = _get_price_direct_yahoo(holding.ticker)
                        except Exception as e2:
                            logger.error(f"Direct API also failed for {holding.ticker}: {e2}")
                    
                    if current_price is None or current_price <= 0:
                        failed_stocks.append(f"{holding.ticker} (가격 조회 실패)")
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

def scheduled_exchange_rate_update():
    """스케줄러에서 호출되는 자동 환율 업데이트 함수"""
    logger.info("Starting scheduled exchange rate update...")
    
    try:
        result = update_exchange_rate()
        
        # 텔레그램 알림 전송 (환율 변화가 있을 때만)
        if result['success'] and result.get('change', 0) != 0:
            try:
                current_time_str = datetime.now().strftime('%H:%M')
                
                change_symbol = "📈" if result['change'] > 0 else "📉"
                message_parts = [f"💱 <b>환율 업데이트</b> ({current_time_str})"]
                message_parts.append("")
                message_parts.append(f"{change_symbol} <b>USD/KRW</b>")
                message_parts.append(f"  • 이전: ₩{result['old_rate']:.2f}")
                message_parts.append(f"  • 현재: ₩{result['new_rate']:.2f}")
                message_parts.append(f"  • 변화: {result['change']:+.2f}원 ({result['change_pct']:+.2f}%)")
                
                notification_message = '\n'.join(message_parts)
                send_notification_sync(notification_message)
                
            except Exception as e:
                logger.error(f"Error sending exchange rate notification: {e}")
        
        if result['success']:
            if result.get('change', 0) != 0:
                logger.info(f"Exchange rate update completed: {result['old_rate']} → {result['new_rate']}")
            else:
                logger.info("Exchange rate update completed: no changes")
        else:
            logger.error(f"Exchange rate update failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"Error in scheduled_exchange_rate_update: {e}")

def start_scheduler():
    """스케줄러 시작"""
    global is_scheduler_running
    
    # 스케줄러 활성화 (일일 리포트 기능 추가)
    # logger.info("Scheduler disabled by user request - not starting")
    # return
    
    if is_scheduler_running:
        logger.info("Scheduler is already running")
        return
    
    try:
        # 한국 시간 기준으로 스케줄링 (안전한 시간대로 조정)
        
        # 주가 업데이트 스케줄 (기존)
        # 오전 10시 (미국 장 마감 1시간 후, 데이터 안정화 시간 확보)
        scheduler.add_job(
            func=scheduled_price_update,
            trigger=CronTrigger(hour=10, minute=30, timezone='Asia/Seoul'),
            id='morning_price_update',
            name='Morning Price Update (Post-Market)',
            replace_existing=True
        )
        
        # 저녁 11시 30분 (미국 장 개장 1시간 후, 거래 데이터 안정화)
        scheduler.add_job(
            func=scheduled_price_update,
            trigger=CronTrigger(hour=23, minute=30, timezone='Asia/Seoul'),
            id='evening_price_update',
            name='Evening Price Update (Market Active)',
            replace_existing=True
        )
        
        # 환율 업데이트 스케줄 (2시간마다)
        scheduler.add_job(
            func=scheduled_exchange_rate_update,
            trigger=CronTrigger(minute=0, hour='*/2', timezone='Asia/Seoul'),
            id='exchange_rate_update',
            name='Exchange Rate Update (Every 2 hours)',
            replace_existing=True
        )
        
        # 일일 포트폴리오 리포트 스케줄 (미국 시장 마감 1시간 후 - 한국시간 오전 6시)
        scheduler.add_job(
            func=send_daily_portfolio_report,
            trigger=CronTrigger(hour=6, minute=0, timezone='Asia/Seoul'),
            id='daily_portfolio_report',
            name='Daily Portfolio Report (Post-Market Close)',
            replace_existing=True
        )
        
        scheduler.start()
        is_scheduler_running = True
        logger.info("Scheduler started successfully")
        logger.info("Price update times: 10:30 (Post-Market) and 23:30 (Market Active) (Asia/Seoul)")
        logger.info("Exchange rate update: Every 2 hours (Asia/Seoul)")
        logger.info("Daily portfolio report: 06:00 (Post-Market Close) (Asia/Seoul)")
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

def stop_scheduler():
    """스케줄러 중지"""
    global is_scheduler_running
    
    if scheduler.running:
        scheduler.shutdown()
        is_scheduler_running = False
        logger.info("Scheduler stopped")

def calculate_portfolio_pnl():
    """포트폴리오 총 손익 계산 (미실현 + 배당금)"""
    from .__init__ import get_app
    app = get_app()
    with app.app_context():
        try:
            # 현재 보유 종목들 조회
            holdings = Holding.query.filter(Holding.current_shares > 0).all()
            if not holdings:
                return {
                    'success': False,
                    'message': '보유 중인 종목이 없습니다.',
                    'total_pnl_usd': 0,
                    'total_return_rate': 0,
                    'holdings_data': []
                }
            
            # 현재 환율 조회
            latest_exchange_rate = ExchangeRate.query.order_by(ExchangeRate.timestamp.desc()).first()
            current_rate = float(latest_exchange_rate.usd_krw) if latest_exchange_rate else 1400.0
            
            # 전체 배당금 조회
            all_dividends = Dividend.query.all()
            total_dividends_usd = sum(float(d.amount) for d in all_dividends)
            
            holdings_data = []
            total_invested_usd = 0
            total_current_value_usd = 0
            total_unrealized_pnl_usd = 0
            
            for holding in holdings:
                # 종목별 기본 정보
                shares = float(holding.current_shares)
                avg_price = float(holding.avg_purchase_price) if holding.avg_purchase_price else 0
                current_price = float(holding.current_market_price)
                
                # 종목별 투자금액 및 현재가치
                invested_usd = shares * avg_price
                current_value_usd = shares * current_price
                unrealized_pnl_usd = current_value_usd - invested_usd
                
                # 종목별 배당금 계산
                ticker_dividends = [d for d in all_dividends if d.ticker == holding.ticker]
                ticker_dividends_usd = sum(float(d.amount) for d in ticker_dividends)
                
                # 종목별 총 손익 (미실현 + 배당금)
                total_pnl_usd = unrealized_pnl_usd + ticker_dividends_usd
                
                # 종목별 수익률
                return_rate = (total_pnl_usd / invested_usd * 100) if invested_usd > 0 else 0
                
                holdings_data.append({
                    'ticker': holding.ticker,
                    'shares': shares,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'invested_usd': invested_usd,
                    'current_value_usd': current_value_usd,
                    'unrealized_pnl_usd': unrealized_pnl_usd,
                    'dividends_usd': ticker_dividends_usd,
                    'total_pnl_usd': total_pnl_usd,
                    'return_rate': return_rate,
                    'dividend_count': len(ticker_dividends)
                })
                
                total_invested_usd += invested_usd
                total_current_value_usd += current_value_usd
                total_unrealized_pnl_usd += unrealized_pnl_usd
            
            # 전체 포트폴리오 총 손익 및 수익률
            total_pnl_usd = total_unrealized_pnl_usd + total_dividends_usd
            total_return_rate = (total_pnl_usd / total_invested_usd * 100) if total_invested_usd > 0 else 0
            
            return {
                'success': True,
                'total_invested_usd': total_invested_usd,
                'total_current_value_usd': total_current_value_usd,
                'total_unrealized_pnl_usd': total_unrealized_pnl_usd,
                'total_dividends_usd': total_dividends_usd,
                'total_pnl_usd': total_pnl_usd,
                'total_return_rate': total_return_rate,
                'current_rate': current_rate,
                'holdings_data': holdings_data
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio PnL: {e}")
            return {
                'success': False,
                'message': f'포트폴리오 손익 계산 중 오류 발생: {e}',
                'total_pnl_usd': 0,
                'total_return_rate': 0,
                'holdings_data': []
            }

def send_daily_portfolio_report():
    """일일 포트폴리오 리포트 전송"""
    logger.info("Starting daily portfolio report...")
    
    # 주말 체크 (토요일=5, 일요일=6)
    if datetime.now().weekday() >= 5:
        logger.info("Weekend detected, skipping daily report")
        return
    
    try:
        pnl_data = calculate_portfolio_pnl()
        
        if not pnl_data['success']:
            logger.error(f"Failed to calculate portfolio PnL: {pnl_data['message']}")
            return
        
        # 경고 레벨 설정
        return_rate = pnl_data['total_return_rate']
        warning_level = ""
        warning_emoji = ""
        
        if return_rate <= -5.0:
            warning_level = "🚨 심각한 손실 경고!"
            warning_emoji = "🚨"
        elif return_rate <= -3.0:
            warning_level = "⚠️ 손실 주의 경고!"
            warning_emoji = "⚠️"
        elif return_rate >= 5.0:
            warning_emoji = "🎉"
        elif return_rate >= 3.0:
            warning_emoji = "📈"
        else:
            warning_emoji = "📊"
        
        # 리포트 메시지 작성
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        message_parts = [f"{warning_emoji} <b>일일 포트폴리오 리포트</b> ({current_time_str})"]
        message_parts.append("")
        
        # 경고 메시지 추가
        if warning_level:
            message_parts.append(f"{warning_level}")
            message_parts.append("")
        
        # 전체 포트폴리오 요약
        message_parts.append(f"💰 <b>총 포트폴리오 가치</b>")
        message_parts.append(f"  • 투자금: ${pnl_data['total_invested_usd']:,.2f}")
        message_parts.append(f"  • 현재가치: ${pnl_data['total_current_value_usd']:,.2f}")
        message_parts.append(f"  • 받은 배당금: ${pnl_data['total_dividends_usd']:,.2f}")
        message_parts.append("")
        
        # 총 손익 및 수익률
        pnl_symbol = "+" if pnl_data['total_pnl_usd'] >= 0 else ""
        rate_symbol = "+" if return_rate >= 0 else ""
        
        message_parts.append(f"📊 <b>총 손익 (미실현 + 배당)</b>")
        message_parts.append(f"  • 미실현 손익: {pnl_symbol}${pnl_data['total_unrealized_pnl_usd']:,.2f}")
        message_parts.append(f"  • 총 손익: {pnl_symbol}${pnl_data['total_pnl_usd']:,.2f}")
        message_parts.append(f"  • 총 수익률: {rate_symbol}{return_rate:.2f}%")
        message_parts.append("")
        
        # 종목별 상세 (모든 종목 표시)
        sorted_holdings = sorted(pnl_data['holdings_data'], key=lambda x: x['total_pnl_usd'], reverse=True)
        
        message_parts.append(f"📈 <b>종목별 현황 (전체 {len(sorted_holdings)}개)</b>")
        for holding in sorted_holdings:
            pnl_emoji = "📈" if holding['total_pnl_usd'] >= 0 else "📉"
            pnl_sign = "+" if holding['total_pnl_usd'] >= 0 else ""
            rate_sign = "+" if holding['return_rate'] >= 0 else ""
            
            message_parts.append(
                f"{pnl_emoji} <code>{holding['ticker']}</code>: "
                f"{pnl_sign}${holding['total_pnl_usd']:,.2f} ({rate_sign}{holding['return_rate']:.1f}%)"
            )
            
            if holding['dividends_usd'] > 0:
                message_parts.append(f"     배당: ${holding['dividends_usd']:,.2f} ({holding['dividend_count']}회)")
        
        # 원화 환산 정보
        total_pnl_krw = pnl_data['total_pnl_usd'] * pnl_data['current_rate']
        message_parts.append("")
        message_parts.append(f"💱 <b>원화 환산</b> (₩{pnl_data['current_rate']:,.0f})")
        message_parts.append(f"  • 총 손익: {pnl_symbol}₩{total_pnl_krw:,.0f}")
        
        notification_message = '\n'.join(message_parts)
        send_notification_sync(notification_message)
        
        logger.info(f"Daily portfolio report sent: Total return {return_rate:.2f}%")
        
    except Exception as e:
        logger.error(f"Error in send_daily_portfolio_report: {e}")

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