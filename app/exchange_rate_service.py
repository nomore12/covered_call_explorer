#!/usr/bin/env python3
"""
환율 업데이트 서비스 모듈
ExchangeRate-API를 사용하여 USD/KRW 환율을 정기적으로 업데이트하는 서비스
"""

import requests
import os
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional

from .__init__ import app, db
from .models import ExchangeRate

logger = logging.getLogger(__name__)

class ExchangeRateService:
    """환율 업데이트 서비스 클래스"""
    
    def __init__(self):
        self.api_key = os.getenv('EXCHANGE_RATE_API') or os.getenv('EXCHANGERATE_API_KEY')
        self.base_url = 'https://v6.exchangerate-api.com/v6'
        
        if not self.api_key:
            logger.warning("환율 API 키가 설정되지 않았습니다. 환율 업데이트를 사용할 수 없습니다.")
    
    def get_usd_krw_rate(self) -> Dict:
        """USD/KRW 환율 정보 가져오기"""
        if not self.api_key:
            return {
                'success': False,
                'error': 'API 키가 설정되지 않았습니다.'
            }
        
        try:
            url = f"{self.base_url}/{self.api_key}/latest/USD"
            
            logger.info(f"환율 API 요청: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('result') == 'success':
                    krw_rate = data['conversion_rates'].get('KRW')
                    if krw_rate:
                        return {
                            'success': True,
                            'usd_krw': Decimal(str(krw_rate)),
                            'timestamp': datetime.now(timezone.utc),
                            'source': 'ExchangeRate-API',
                            'raw_data': data
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'KRW 환율 정보를 찾을 수 없습니다.'
                        }
                else:
                    return {
                        'success': False,
                        'error': f"API 오류: {data.get('error-type', 'Unknown error')}"
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP 오류: {response.status_code}"
                }
                
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"네트워크 오류: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"예상치 못한 오류: {str(e)}"
            }
    
    def save_exchange_rate(self, rate_info: Dict) -> bool:
        """환율 정보를 데이터베이스에 저장"""
        if not rate_info['success']:
            logger.error(f"환율 정보 저장 실패: {rate_info['error']}")
            return False
        
        try:
            with app.app_context():
                # 새로운 환율 정보 저장
                exchange_rate = ExchangeRate(
                    timestamp=rate_info['timestamp'],
                    usd_krw=rate_info['usd_krw'],
                    source=rate_info['source']
                )
                
                db.session.add(exchange_rate)
                db.session.commit()
                
                logger.info(f"환율 정보 저장 완료: USD/KRW {rate_info['usd_krw']} at {rate_info['timestamp']}")
                return True
                
        except Exception as e:
            logger.error(f"환율 정보 저장 중 오류: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return False
    
    def get_latest_rate(self) -> Optional[ExchangeRate]:
        """데이터베이스에서 최신 환율 정보 가져오기"""
        try:
            with app.app_context():
                latest_rate = ExchangeRate.query.order_by(ExchangeRate.timestamp.desc()).first()
                return latest_rate
        except Exception as e:
            logger.error(f"최신 환율 정보 조회 중 오류: {e}")
            return None
    
    def get_api_usage_info(self) -> Dict:
        """API 사용량 정보 가져오기"""
        if not self.api_key:
            return {
                'success': False,
                'error': 'API 키가 설정되지 않았습니다.'
            }
        
        try:
            url = f"{self.base_url}/{self.api_key}/quota"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('result') == 'success':
                    return {
                        'success': True,
                        'plan_quota': data.get('plan_quota', 0),
                        'requests_quota': data.get('requests_quota', 0),
                        'requests_remaining': data.get('requests_remaining', 0),
                        'hours_until_reset': data.get('hours_until_reset', 0)
                    }
                else:
                    return {
                        'success': False,
                        'error': f"API 오류: {data.get('error-type', 'Unknown error')}"
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP 오류: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"오류: {str(e)}"
            }
    
    def update_exchange_rate(self) -> Dict:
        """환율 업데이트 실행 (API 호출 + DB 저장)"""
        logger.info("환율 업데이트 시작...")
        
        # 1. API에서 최신 환율 정보 가져오기
        rate_info = self.get_usd_krw_rate()
        
        if not rate_info['success']:
            logger.error(f"환율 정보 가져오기 실패: {rate_info['error']}")
            return {
                'success': False,
                'message': f"환율 정보 가져오기 실패: {rate_info['error']}",
                'old_rate': None,
                'new_rate': None
            }
        
        # 2. 기존 환율과 비교
        latest_rate = self.get_latest_rate()
        old_rate = float(latest_rate.usd_krw) if latest_rate else None
        new_rate = float(rate_info['usd_krw'])
        
        # 3. 변화가 있거나 첫 번째 저장인 경우에만 저장
        if old_rate is None or abs(new_rate - old_rate) > 0.01:  # 0.01원 이상 차이날 때만 저장
            if self.save_exchange_rate(rate_info):
                change = new_rate - old_rate if old_rate else 0
                change_pct = (change / old_rate * 100) if old_rate else 0
                
                logger.info(f"환율 업데이트 완료: {old_rate} → {new_rate} (변화: {change:+.2f}원, {change_pct:+.2f}%)")
                
                return {
                    'success': True,
                    'message': '환율 업데이트 완료',
                    'old_rate': old_rate,
                    'new_rate': new_rate,
                    'change': change,
                    'change_pct': change_pct,
                    'timestamp': rate_info['timestamp']
                }
            else:
                return {
                    'success': False,
                    'message': '환율 정보 저장 실패',
                    'old_rate': old_rate,
                    'new_rate': new_rate
                }
        else:
            logger.info(f"환율 변화 없음: {new_rate} (변화: {new_rate - old_rate:+.4f}원)")
            return {
                'success': True,
                'message': '환율 변화 없음',
                'old_rate': old_rate,
                'new_rate': new_rate,
                'change': 0,
                'change_pct': 0
            }

# 전역 서비스 인스턴스
exchange_rate_service = ExchangeRateService()

def update_exchange_rate():
    """스케줄러에서 호출될 환율 업데이트 함수"""
    return exchange_rate_service.update_exchange_rate()

def get_latest_exchange_rate():
    """최신 환율 정보 조회"""
    return exchange_rate_service.get_latest_rate()

def get_exchange_rate_usage():
    """API 사용량 정보 조회"""
    return exchange_rate_service.get_api_usage_info()