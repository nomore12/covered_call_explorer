#!/usr/bin/env python3
"""
스케줄러 및 환율 업데이트 기능 테스트 스크립트
"""

import os
import sys
import logging
from datetime import datetime

# 현재 디렉터리를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 로드
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Flask 앱 초기화
from __init__ import app, db
from models import ExchangeRate
from exchange_rate_service import ExchangeRateService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_exchange_rate_service():
    """환율 업데이트 서비스 테스트"""
    logger.info("=" * 50)
    logger.info("환율 업데이트 서비스 테스트")
    logger.info("=" * 50)
    
    service = ExchangeRateService()
    
    # 1. API 키 확인
    if not service.api_key:
        logger.error("❌ API 키가 설정되지 않았습니다.")
        return False
    
    logger.info(f"✓ API 키 설정됨: {service.api_key[:10]}...")
    
    # 2. API 사용량 확인
    usage_info = service.get_api_usage_info()
    if usage_info['success']:
        logger.info("✓ API 사용량 정보:")
        logger.info(f"  - 월간 한도: {usage_info['plan_quota']:,} requests")
        logger.info(f"  - 남은 요청: {usage_info['requests_remaining']:,} requests")
    else:
        logger.warning(f"⚠ API 사용량 확인 실패: {usage_info['error']}")
    
    # 3. 환율 정보 가져오기
    rate_info = service.get_usd_krw_rate()
    if rate_info['success']:
        logger.info("✓ 환율 정보 조회 성공:")
        logger.info(f"  - USD/KRW: {rate_info['usd_krw']}")
        logger.info(f"  - 조회 시간: {rate_info['timestamp']}")
    else:
        logger.error(f"❌ 환율 정보 조회 실패: {rate_info['error']}")
        return False
    
    # 4. 데이터베이스 저장 테스트
    with app.app_context():
        try:
            # 기존 데이터 확인
            existing_count = ExchangeRate.query.count()
            logger.info(f"✓ 기존 환율 데이터: {existing_count}개")
            
            # 환율 업데이트 실행
            result = service.update_exchange_rate()
            
            if result['success']:
                logger.info("✓ 환율 업데이트 성공:")
                logger.info(f"  - 메시지: {result['message']}")
                if result.get('new_rate'):
                    logger.info(f"  - 새 환율: {result['new_rate']}")
                    if result.get('old_rate'):
                        logger.info(f"  - 이전 환율: {result['old_rate']}")
                        logger.info(f"  - 변화: {result.get('change', 0):+.2f}원")
                
                # 저장 후 데이터 확인
                new_count = ExchangeRate.query.count()
                logger.info(f"✓ 업데이트 후 환율 데이터: {new_count}개")
                
                # 최신 데이터 확인
                latest = ExchangeRate.query.order_by(ExchangeRate.timestamp.desc()).first()
                if latest:
                    logger.info(f"✓ 최신 환율 데이터: {latest.usd_krw} ({latest.timestamp})")
                
                return True
            else:
                logger.error(f"❌ 환율 업데이트 실패: {result['message']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 데이터베이스 테스트 중 오류: {e}")
            return False

def test_scheduler_setup():
    """스케줄러 설정 테스트"""
    logger.info("=" * 50)
    logger.info("스케줄러 설정 테스트")
    logger.info("=" * 50)
    
    try:
        from scheduler import scheduler, is_scheduler_running, start_scheduler, get_scheduler_status
        
        # 1. 스케줄러 상태 확인
        logger.info(f"✓ 스케줄러 실행 상태: {is_scheduler_running}")
        
        # 2. 스케줄러 시작 (이미 실행 중이 아닌 경우)
        if not is_scheduler_running:
            logger.info("스케줄러 시작 중...")
            start_scheduler()
        
        # 3. 등록된 작업 확인
        jobs = scheduler.get_jobs()
        logger.info(f"✓ 등록된 작업 수: {len(jobs)}")
        
        for job in jobs:
            logger.info(f"  - {job.id}: {job.name}")
            next_run = job.next_run_time
            if next_run:
                logger.info(f"    다음 실행: {next_run}")
            else:
                logger.info("    다음 실행 시간 미정")
        
        # 4. 스케줄러 상태 메시지 확인
        status_msg = get_scheduler_status()
        logger.info("✓ 스케줄러 상태:")
        for line in status_msg.split('\\n'):
            logger.info(f"  {line}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 스케줄러 테스트 중 오류: {e}")
        return False

def test_scheduled_functions():
    """스케줄러 함수 직접 실행 테스트"""
    logger.info("=" * 50)
    logger.info("스케줄러 함수 직접 실행 테스트")
    logger.info("=" * 50)
    
    try:
        from scheduler import scheduled_exchange_rate_update
        
        # 환율 업데이트 함수 직접 실행
        logger.info("환율 업데이트 함수 직접 실행...")
        scheduled_exchange_rate_update()
        
        logger.info("✓ 환율 업데이트 함수 실행 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ 스케줄러 함수 실행 중 오류: {e}")
        return False

def main():
    """메인 테스트 실행"""
    logger.info("스케줄러 및 환율 업데이트 테스트 시작")
    logger.info(f"시작 시간: {datetime.now()}")
    
    tests = [
        ("환율 업데이트 서비스", test_exchange_rate_service),
        ("스케줄러 설정", test_scheduler_setup),
        ("스케줄러 함수 직접 실행", test_scheduled_functions)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            logger.info(f"{'✓' if result else '❌'} {name}: {'통과' if result else '실패'}")
        except Exception as e:
            logger.error(f"❌ {name} 테스트 중 예외 발생: {e}")
            results.append((name, False))
        
        logger.info("")
    
    # 결과 요약
    logger.info("=" * 50)
    logger.info("테스트 결과 요약")
    logger.info("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        logger.info(f"{'✓' if result else '❌'} {name}")
    
    logger.info(f"\\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 모든 테스트 통과!")
        return 0
    else:
        logger.error("⚠ 일부 테스트 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())