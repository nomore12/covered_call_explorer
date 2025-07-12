"""
Toss API Data Parser
토스 API 응답 데이터 파싱 및 처리
"""

from typing import Dict, Any, Optional, List
from decimal import Decimal


class TossDataParser:
    """토스 API 응답 데이터 파서"""
    
    @staticmethod
    def extract_basic_info(stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        기본 종목 정보 추출
        
        Args:
            stock_data: 토스 API 응답의 단일 종목 데이터
            
        Returns:
            추출된 기본 정보
        """
        return {
            'code': stock_data.get('code'),
            'symbol': stock_data.get('symbol'),
            'name': stock_data.get('name'),
            'english_name': stock_data.get('englishName'),
            'company_name': stock_data.get('companyName'),
            'currency': stock_data.get('currency', 'KRW'),
            'isin_code': stock_data.get('isinCode'),
            'guid': stock_data.get('guid')
        }
    
    @staticmethod
    def extract_market_info(stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        시장 정보 추출
        
        Args:
            stock_data: 토스 API 응답의 단일 종목 데이터
            
        Returns:
            시장 관련 정보
        """
        market = stock_data.get('market', {})
        group = stock_data.get('group', {})
        
        return {
            'market_code': market.get('code'),
            'market_name': market.get('displayName'),
            'group_code': group.get('code'),
            'group_name': group.get('displayName'),
            'list_date': stock_data.get('listDate'),
            'delist_date': stock_data.get('delistDate'),
            'shares_outstanding': stock_data.get('sharesOutstanding')
        }
    
    @staticmethod
    def extract_trading_info(stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        거래 관련 정보 추출
        
        Args:
            stock_data: 토스 API 응답의 단일 종목 데이터
            
        Returns:
            거래 관련 정보
        """
        return {
            'trading_suspended': stock_data.get('tradingSuspended', False),
            'krx_trading_suspended': stock_data.get('krxTradingSuspended', False),
            'nxt_trading_suspended': stock_data.get('nxtTradingSuspended', False),
            'user_trading_suspended': stock_data.get('userTradingSuspended', False),
            'nxt_supported': stock_data.get('nxtSupported', False),
            'nxt_open_date': stock_data.get('nxtOpenDate'),
            'option_supported': stock_data.get('optionSupported', False),
            'daytime_price_supported': stock_data.get('daytimePriceSupported', False)
        }
    
    @staticmethod
    def extract_risk_info(stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        위험도 및 특수 정보 추출
        
        Args:
            stock_data: 토스 API 응답의 단일 종목 데이터
            
        Returns:
            위험도 및 특수 정보
        """
        return {
            'risk_level': stock_data.get('riskLevel'),
            'spac': stock_data.get('spac', False),
            'spac_merger_date': stock_data.get('spacMergerDate'),
            'leverage_factor': stock_data.get('leverageFactor', 0),
            'derivative_etp': stock_data.get('derivativeEtp', False),
            'derivative_etf': stock_data.get('derivativeEtf', False),
            'pooling_stock': stock_data.get('poolingStock', False),
            'clearance': stock_data.get('clearance', False),
            'purchase_prerequisite': stock_data.get('purchasePrerequisite')
        }
    
    @staticmethod
    def extract_ui_info(stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        UI 표시용 정보 추출
        
        Args:
            stock_data: 토스 API 응답의 단일 종목 데이터
            
        Returns:
            UI 표시용 정보
        """
        return {
            'logo_url': stock_data.get('logoImageUrl'),
            'detail_name': stock_data.get('detailName'),
            'display_name': stock_data.get('name'),
            'common_share': stock_data.get('commonShare', True)
        }
    
    @staticmethod
    def parse_full_stock_data(stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        전체 종목 데이터 파싱
        
        Args:
            stock_data: 토스 API 응답의 단일 종목 데이터
            
        Returns:
            파싱된 전체 정보
        """
        return {
            'basic': TossDataParser.extract_basic_info(stock_data),
            'market': TossDataParser.extract_market_info(stock_data),
            'trading': TossDataParser.extract_trading_info(stock_data),
            'risk': TossDataParser.extract_risk_info(stock_data),
            'ui': TossDataParser.extract_ui_info(stock_data),
            'raw': stock_data  # 원본 데이터 보존
        }
    
    @staticmethod
    def is_tradeable(stock_data: Dict[str, Any]) -> bool:
        """
        거래 가능 여부 확인
        
        Args:
            stock_data: 토스 API 응답의 단일 종목 데이터
            
        Returns:
            거래 가능 여부
        """
        return not any([
            stock_data.get('tradingSuspended', False),
            stock_data.get('krxTradingSuspended', False),
            stock_data.get('userTradingSuspended', False)
        ])
    
    @staticmethod
    def format_for_portfolio(stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        포트폴리오 표시용 데이터 포맷
        
        Args:
            stock_data: 토스 API 응답의 단일 종목 데이터
            
        Returns:
            포트폴리오 표시용 포맷
        """
        basic = TossDataParser.extract_basic_info(stock_data)
        trading = TossDataParser.extract_trading_info(stock_data)
        market = TossDataParser.extract_market_info(stock_data)
        
        return {
            'ticker': basic['symbol'],
            'name': basic['name'],
            'company_name': basic['company_name'],
            'currency': basic['currency'],
            'market': market['market_name'],
            'tradeable': TossDataParser.is_tradeable(stock_data),
            'logo_url': stock_data.get('logoImageUrl'),
            'risk_level': stock_data.get('riskLevel'),
            'is_spac': stock_data.get('spac', False)
        }