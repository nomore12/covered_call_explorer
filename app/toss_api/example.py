"""
Toss API 사용 예제
"""

from .service import TossStockService


def example_usage():
    """토스 API 사용 예제"""
    
    # 서비스 초기화
    toss_service = TossStockService(rate_limit_delay=0.2)
    
    # 1. 단일 종목 기본 정보 조회
    print("=== 단일 종목 기본 정보 ===")
    basic_info = toss_service.get_stock_basic_info('A322000')
    if basic_info:
        print(f"종목명: {basic_info['name']}")
        print(f"회사명: {basic_info['company_name']}")
        print(f"통화: {basic_info['currency']}")
    
    # 2. 포트폴리오용 정보 조회
    print("\n=== 포트폴리오용 정보 ===")
    portfolio_info = toss_service.get_stock_for_portfolio('A322000')
    if portfolio_info:
        print(f"티커: {portfolio_info['ticker']}")
        print(f"이름: {portfolio_info['name']}")
        print(f"시장: {portfolio_info['market']}")
        print(f"거래가능: {portfolio_info['tradeable']}")
        print(f"위험도: {portfolio_info['risk_level']}")
    
    # 3. 거래 가능 여부 확인
    print("\n=== 거래 가능 여부 ===")
    is_tradeable = toss_service.check_tradeable('A322000')
    print(f"거래 가능: {is_tradeable}")
    
    # 4. 다중 종목 조회
    print("\n=== 다중 종목 조회 ===")
    multiple_stocks = toss_service.get_multiple_stocks_info(['A322000', 'A005930'])
    for code, info in multiple_stocks.items():
        print(f"{code}: {info['name']} - {info['market']}")
    
    # 5. 한국 주식 여부 확인
    print("\n=== 한국 주식 여부 ===")
    is_korean = toss_service.is_korean_stock('A322000')
    print(f"한국 주식: {is_korean}")


if __name__ == "__main__":
    example_usage()