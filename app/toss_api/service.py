"""
Toss API Service
토스 API를 활용한 종목 정보 서비스
"""

from typing import Dict, Any, Optional, List
from .client import TossAPIClient
from .parser import TossDataParser


class TossStockService:
    """토스 API를 활용한 종목 정보 서비스"""
    
    def __init__(self, rate_limit_delay: float = 0.1):
        """
        Args:
            rate_limit_delay: API 호출 간 지연 시간 (초)
        """
        self.client = TossAPIClient(rate_limit_delay)
        self.parser = TossDataParser()
    
    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        종목 기본 정보 조회
        
        Args:
            stock_code: 종목 코드 (예: 'A322000')
            
        Returns:
            기본 정보 딕셔너리 또는 None
        """
        stock_data = self.client.get_single_stock_info(stock_code)
        if stock_data:
            return self.parser.extract_basic_info(stock_data)
        return None
    
    def get_stock_for_portfolio(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        포트폴리오용 종목 정보 조회
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            포트폴리오용 정보 또는 None
        """
        stock_data = self.client.get_single_stock_info(stock_code)
        if stock_data:
            return self.parser.format_for_portfolio(stock_data)
        return None
    
    def check_tradeable(self, stock_code: str) -> bool:
        """
        종목 거래 가능 여부 확인
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            거래 가능 여부
        """
        stock_data = self.client.get_single_stock_info(stock_code)
        if stock_data:
            return self.parser.is_tradeable(stock_data)
        return False
    
    def get_multiple_stocks_info(self, stock_codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        다중 종목 정보 조회
        
        Args:
            stock_codes: 종목 코드 리스트
            
        Returns:
            종목별 정보 딕셔너리 {종목코드: 정보}
        """
        result = {}
        
        if not stock_codes:
            return result
        
        # API 응답 받기
        api_response = self.client.get_stock_info(stock_codes)
        
        if api_response and api_response.get('result'):
            for stock_data in api_response['result']:
                code = stock_data.get('code')
                if code:
                    result[code] = self.parser.format_for_portfolio(stock_data)
        
        return result
    
    def get_stock_display_name(self, stock_code: str) -> Optional[str]:
        """
        종목 표시명 조회 (한글명)
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            한글 종목명 또는 None
        """
        basic_info = self.get_stock_basic_info(stock_code)
        if basic_info:
            return basic_info.get('name')
        return None
    
    def is_korean_stock(self, stock_code: str) -> bool:
        """
        한국 주식 여부 확인
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            한국 주식 여부
        """
        basic_info = self.get_stock_basic_info(stock_code)
        if basic_info:
            return basic_info.get('currency') == 'KRW'
        return False