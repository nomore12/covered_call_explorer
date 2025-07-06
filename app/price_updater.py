import yfinance as yf
import requests
from datetime import datetime

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

def update_stock_prices(holdings):
    """
    모든 holdings의 주가를 업데이트하는 함수
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    updated_prices = {}
    
    for holding in holdings:
        try:
            latest_price = get_stock_price(holding.ticker, session)
            
            if latest_price is not None:
                # 데이터베이스 업데이트
                holding.current_market_price = latest_price
                holding.last_price_update_date = datetime.now().date()
                updated_prices[holding.ticker] = latest_price
            else:
                print(f"⚠ {holding.ticker}: Using existing price ${holding.current_market_price}")
                
        except Exception as e:
            print(f"✗ {holding.ticker}: Unexpected error - {str(e)}")
    
    return updated_prices