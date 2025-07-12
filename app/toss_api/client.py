"""
Toss API Client
토스 증권 API 클라이언트
"""

import requests
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin


class TossAPIClient:
    """토스 증권 API 클라이언트"""
    
    BASE_URL = "https://wts-info-api.tossinvest.com/api/v2/"
    STOCK_INFO_ENDPOINT = "stock-infos"
    
    def __init__(self, rate_limit_delay: float = 0.1):
        """
        Args:
            rate_limit_delay: API 호출 간 지연 시간 (초)
        """
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Referer': 'https://tossinvest.com/'
        })
        self._last_request_time = 0
    
    def _wait_for_rate_limit(self):
        """Rate limiting을 위한 대기"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    def get_stock_info(self, 
                      stock_codes: List[str], 
                      timeout: int = 10, 
                      retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        주식 정보 조회
        
        Args:
            stock_codes: 종목 코드 리스트 (예: ['A322000', 'A005930'])
            timeout: 요청 타임아웃 (초)
            retries: 재시도 횟수
            
        Returns:
            API 응답 JSON 또는 None (실패 시)
        """
        if not stock_codes:
            return None
            
        self._wait_for_rate_limit()
        
        # 종목 코드를 쉼표로 구분하여 조인
        codes_param = ','.join(stock_codes)
        url = urljoin(self.BASE_URL, self.STOCK_INFO_ENDPOINT)
        
        params = {'codes': codes_param}
        
        for attempt in range(retries):
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=timeout
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    print(f"Toss API 요청 실패 (최종): {e}")
                    return None
                else:
                    print(f"Toss API 요청 실패 (재시도 {attempt + 1}/{retries}): {e}")
                    time.sleep(1 * (attempt + 1))  # 지수 백오프
        
        return None
    
    def get_single_stock_info(self, 
                             stock_code: str, 
                             timeout: int = 10, 
                             retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        단일 종목 정보 조회
        
        Args:
            stock_code: 종목 코드 (예: 'A322000')
            timeout: 요청 타임아웃 (초)
            retries: 재시도 횟수
            
        Returns:
            단일 종목 정보 딕셔너리 또는 None
        """
        result = self.get_stock_info([stock_code], timeout, retries)
        if result and result.get('result') and len(result['result']) > 0:
            return result['result'][0]
        return None
    
    def __del__(self):
        """세션 정리"""
        if hasattr(self, 'session'):
            self.session.close()