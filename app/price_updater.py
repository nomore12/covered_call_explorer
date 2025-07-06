import yfinance as yf
import requests
from datetime import datetime, timedelta
import time

def get_stock_price(ticker, session=None):
    """
    여러 방법으로 주식 가격을 가져오는 함수
    """
    if session is None:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    try:
        # 방법 1: yfinance로 역사적 데이터 가져오기
        ticker_obj = yf.Ticker(ticker, session=session)
        
        # 5일 데이터로 시도
        hist = ticker_obj.history(period="5d")
        
        if not hist.empty:
            latest_price = float(hist['Close'].iloc[-1])
            print(f"✓ {ticker}: ${latest_price} (from history)")
            return latest_price
        
        # 방법 2: ticker.info에서 가져오기
        info = ticker_obj.info
        if 'regularMarketPrice' in info and info['regularMarketPrice']:
            latest_price = float(info['regularMarketPrice'])
            print(f"✓ {ticker}: ${latest_price} (from info)")
            return latest_price
        
        # 방법 3: currentPrice 필드 시도
        if 'currentPrice' in info and info['currentPrice']:
            latest_price = float(info['currentPrice'])
            print(f"✓ {ticker}: ${latest_price} (from currentPrice)")
            return latest_price
            
        # 방법 4: ask/bid 평균
        if 'ask' in info and 'bid' in info and info['ask'] and info['bid']:
            latest_price = (float(info['ask']) + float(info['bid'])) / 2
            print(f"✓ {ticker}: ${latest_price} (from ask/bid)")
            return latest_price
            
        print(f"✗ {ticker}: No price data available")
        return None
        
    except Exception as e:
        print(f"✗ {ticker}: Error - {str(e)}")
        return None

# 캐시 저장소 (메모리)
price_cache = {}
CACHE_DURATION = timedelta(hours=1)  # 1시간 캐시 (증시 마감 후 고려)

def should_update_price(ticker, last_update_date):
    """
    주가를 업데이트해야 하는지 확인
    - 캐시에 있고 1시간 이내면 업데이트 안함
    - 마지막 업데이트가 오늘이 아니면 업데이트
    """
    now = datetime.now()
    
    # 캐시 확인
    if ticker in price_cache:
        cache_time, _ = price_cache[ticker]
        if now - cache_time < CACHE_DURATION:
            return False
    
    # 마지막 업데이트가 오늘이 아니면 업데이트 필요
    if last_update_date != now.date():
        return True
    
    return False

def update_stock_prices(holdings):
    """
    모든 holdings의 주가를 업데이트하는 함수 (캐시 및 제한 적용)
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    updated_prices = {}
    now = datetime.now()
    
    for i, holding in enumerate(holdings):
        try:
            # 캐시 확인
            if holding.ticker in price_cache:
                cache_time, cached_price = price_cache[holding.ticker]
                if now - cache_time < CACHE_DURATION:
                    print(f"📦 {holding.ticker}: Using cached price ${cached_price} (cached {int((now - cache_time).total_seconds() / 60)}min ago)")
                    updated_prices[holding.ticker] = cached_price
                    continue
            
            # 업데이트가 필요한지 확인
            if not should_update_price(holding.ticker, holding.last_price_update_date):
                print(f"⏭ {holding.ticker}: Skipping (recently updated)")
                continue
            
            # API 호출 제한 (각 요청 사이에 1초 대기)
            if i > 0:
                time.sleep(1)
            
            latest_price = get_stock_price(holding.ticker, session)
            
            if latest_price is not None:
                # 데이터베이스 업데이트
                holding.current_market_price = latest_price
                holding.last_price_update_date = now.date()
                updated_prices[holding.ticker] = latest_price
                
                # 캐시 저장
                price_cache[holding.ticker] = (now, latest_price)
                
            else:
                print(f"⚠ {holding.ticker}: Using existing price ${holding.current_market_price}")
                # 기존 가격을 캐시에 저장
                price_cache[holding.ticker] = (now, float(holding.current_market_price))
                
        except Exception as e:
            print(f"✗ {holding.ticker}: Unexpected error - {str(e)}")
    
    return updated_prices

def get_cached_price(ticker):
    """
    캐시된 가격을 가져오는 함수
    """
    if ticker in price_cache:
        cache_time, cached_price = price_cache[ticker]
        if datetime.now() - cache_time < CACHE_DURATION:
            return cached_price
    return None