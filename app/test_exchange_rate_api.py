#!/usr/bin/env python3
"""
ExchangeRate-API 테스트 파일
ExchangeRate-API (https://exchangerate-api.com)를 사용하여 USD/KRW 환율 정보를 가져오고 테스트하는 파일
"""

import requests
import json
from datetime import datetime, timezone
from decimal import Decimal
import sys
import os

# 환경 변수에서 API 키 가져오기
API_KEY = os.getenv('EXCHANGE_RATE_API') or os.getenv('EXCHANGERATE_API_KEY')
if not API_KEY:
    print("경고: EXCHANGE_RATE_API 또는 EXCHANGERATE_API_KEY 환경 변수가 설정되지 않았습니다.")
    print("무료 API 키를 https://exchangerate-api.com 에서 발급받으세요.")
    API_KEY = 'demo'  # 테스트용 (제한적)

# API 엔드포인트 URL
BASE_URL = 'https://v6.exchangerate-api.com/v6'

def get_usd_krw_rate():
    """USD/KRW 환율 정보 가져오기"""
    try:
        # USD 기준 환율 정보 가져오기
        url = f"{BASE_URL}/{API_KEY}/latest/USD"
        
        print(f"API 요청: {url}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # API 응답 상태 확인
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

def get_api_usage_info():
    """API 사용량 정보 가져오기"""
    try:
        url = f"{BASE_URL}/{API_KEY}/quota"
        
        print(f"API 사용량 확인: {url}")
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

def test_api():
    """API 테스트 실행"""
    print("=" * 60)
    print("ExchangeRate-API 테스트 시작")
    print("=" * 60)
    
    # 1. API 사용량 정보 확인
    print("\n1. API 사용량 정보:")
    print("-" * 40)
    usage_info = get_api_usage_info()
    if usage_info['success']:
        print(f"요금제 한도: {usage_info['plan_quota']:,} requests/month")
        print(f"월간 할당량: {usage_info['requests_quota']:,} requests")
        print(f"남은 요청수: {usage_info['requests_remaining']:,} requests")
        print(f"리셋까지 남은 시간: {usage_info['hours_until_reset']} hours")
    else:
        print(f"❌ 사용량 정보 오류: {usage_info['error']}")
    
    # 2. USD/KRW 환율 정보 가져오기
    print("\n2. USD/KRW 환율 정보:")
    print("-" * 40)
    rate_info = get_usd_krw_rate()
    
    if rate_info['success']:
        print(f"✅ 환율 정보 조회 성공!")
        print(f"USD/KRW: {rate_info['usd_krw']}")
        print(f"조회 시간: {rate_info['timestamp']}")
        print(f"데이터 소스: {rate_info['source']}")
        
        # 추가 정보 출력
        raw_data = rate_info['raw_data']
        print(f"\n📊 API 응답 상세 정보:")
        print(f"  • 기준 통화: {raw_data.get('base_code', 'N/A')}")
        print(f"  • 마지막 업데이트: {raw_data.get('time_last_update_utc', 'N/A')}")
        print(f"  • 다음 업데이트: {raw_data.get('time_next_update_utc', 'N/A')}")
        
        # 다른 주요 통화 환율도 출력
        rates = raw_data.get('conversion_rates', {})
        major_currencies = ['EUR', 'JPY', 'GBP', 'CNY', 'AUD']
        print(f"\n🌍 기타 주요 통화 환율:")
        for currency in major_currencies:
            if currency in rates:
                print(f"  • USD/{currency}: {rates[currency]}")
        
        return True
    else:
        print(f"❌ 환율 정보 오류: {rate_info['error']}")
        return False

def save_exchange_rate_to_db(rate_info):
    """환율 정보를 데이터베이스에 저장 (테스트용)"""
    print("\n3. 데이터베이스 저장 시뮬레이션:")
    print("-" * 40)
    
    if not rate_info['success']:
        print("❌ 환율 정보가 없어 저장할 수 없습니다.")
        return False
    
    # 실제 데이터베이스 저장 로직 시뮬레이션
    print("📝 데이터베이스 저장 시뮬레이션:")
    print(f"  • 테이블: exchange_rates")
    print(f"  • timestamp: {rate_info['timestamp']}")
    print(f"  • usd_krw: {rate_info['usd_krw']}")
    print(f"  • source: {rate_info['source']}")
    print("✅ 데이터베이스 저장 완료 (시뮬레이션)")
    
    return True

def main():
    """메인 실행 함수"""
    print("ExchangeRate-API 테스트 도구")
    print("사용법: python test_exchange_rate_api.py")
    print()
    
    # API 테스트 실행
    success = test_api()
    
    if success:
        # 환율 정보 다시 가져와서 DB 저장 시뮬레이션
        rate_info = get_usd_krw_rate()
        save_exchange_rate_to_db(rate_info)
        
        print("\n" + "=" * 60)
        print("✅ 모든 테스트 완료!")
        print("=" * 60)
        print()
        print("다음 단계:")
        print("1. .env 파일에 EXCHANGERATE_API_KEY 설정")
        print("2. Flask 앱에 환율 업데이트 스케줄러 추가")
        print("3. 실제 데이터베이스 저장 기능 구현")
        
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ 테스트 실패!")
        print("=" * 60)
        print()
        print("문제 해결:")
        print("1. 인터넷 연결 확인")
        print("2. API 키 확인 (https://exchangerate-api.com)")
        print("3. 환경 변수 EXCHANGERATE_API_KEY 설정")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())