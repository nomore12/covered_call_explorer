#!/usr/bin/env python3
"""
ExchangeRate 모델 변경사항에 대한 데이터베이스 마이그레이션 스크립트

변경사항:
1. date (DATE) → timestamp (TIMESTAMP)
2. usd_krw DECIMAL(10, 2) → DECIMAL(10, 4) (정밀도 증가)
3. source 기본값 추가
"""

import os
import sys
import logging
from datetime import datetime, timezone
from sqlalchemy import text

# 현재 스크립트 위치를 기준으로 앱 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import app, db
from models import ExchangeRate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_current_schema():
    """현재 exchange_rates 테이블 스키마 확인"""
    try:
        with app.app_context():
            result = db.session.execute(text("DESCRIBE exchange_rates"))
            columns = result.fetchall()
            
            logger.info("현재 exchange_rates 테이블 스키마:")
            for col in columns:
                logger.info(f"  {col[0]}: {col[1]} {col[2] if col[2] else ''}")
            
            return {col[0]: col[1] for col in columns}
    except Exception as e:
        logger.error(f"스키마 확인 중 오류: {e}")
        return None

def check_data_exists():
    """기존 데이터가 있는지 확인"""
    try:
        with app.app_context():
            result = db.session.execute(text("SELECT COUNT(*) FROM exchange_rates"))
            count = result.fetchone()[0]
            logger.info(f"기존 데이터 개수: {count}")
            return count > 0
    except Exception as e:
        logger.error(f"데이터 확인 중 오류: {e}")
        return False

def backup_existing_data():
    """기존 데이터 백업"""
    try:
        with app.app_context():
            result = db.session.execute(text("SELECT * FROM exchange_rates"))
            data = result.fetchall()
            
            if data:
                # 백업 테이블 생성
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS exchange_rates_backup (
                        rate_id INT,
                        date DATE,
                        usd_krw DECIMAL(10, 2),
                        source VARCHAR(50),
                        created_at TIMESTAMP,
                        backup_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # 기존 데이터 백업
                db.session.execute(text("""
                    INSERT INTO exchange_rates_backup (rate_id, date, usd_krw, source, created_at)
                    SELECT rate_id, date, usd_krw, source, created_at FROM exchange_rates
                """))
                
                db.session.commit()
                logger.info(f"기존 데이터 {len(data)}개 백업 완료")
                return data
            else:
                logger.info("백업할 데이터가 없습니다.")
                return []
    except Exception as e:
        logger.error(f"데이터 백업 중 오류: {e}")
        db.session.rollback()
        return None

def migrate_schema():
    """스키마 마이그레이션 실행"""
    try:
        with app.app_context():
            logger.info("스키마 마이그레이션 시작...")
            
            # 1. 기존 테이블 삭제 (백업 완료 후)
            db.session.execute(text("DROP TABLE IF EXISTS exchange_rates"))
            logger.info("기존 exchange_rates 테이블 삭제 완료")
            
            # 2. 새 스키마로 테이블 재생성
            db.session.execute(text("""
                CREATE TABLE exchange_rates (
                    rate_id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    usd_krw DECIMAL(10, 4) NOT NULL,
                    source VARCHAR(50) DEFAULT 'ExchangeRate-API',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.info("새 exchange_rates 테이블 생성 완료")
            
            # 3. 인덱스 추가
            db.session.execute(text("CREATE INDEX idx_exchange_rates_timestamp ON exchange_rates (timestamp)"))
            logger.info("인덱스 생성 완료")
            
            db.session.commit()
            logger.info("스키마 마이그레이션 완료")
            return True
            
    except Exception as e:
        logger.error(f"스키마 마이그레이션 중 오류: {e}")
        db.session.rollback()
        return False

def migrate_data(backup_data):
    """백업된 데이터를 새 스키마로 마이그레이션"""
    if not backup_data:
        logger.info("마이그레이션할 데이터가 없습니다.")
        return True
    
    try:
        with app.app_context():
            logger.info(f"데이터 마이그레이션 시작... ({len(backup_data)}개)")
            
            for row in backup_data:
                rate_id, date, usd_krw, source, created_at = row
                
                # date를 timestamp로 변환 (해당 날짜의 12:00:00으로 설정)
                if isinstance(date, str):
                    timestamp = datetime.strptime(date, '%Y-%m-%d').replace(hour=12, minute=0, second=0)
                else:
                    timestamp = datetime.combine(date, datetime.min.time().replace(hour=12))
                
                # usd_krw 정밀도 유지 (DECIMAL(10,4)로 변환)
                usd_krw_decimal = float(usd_krw)
                
                # source가 None인 경우 기본값 설정
                if not source:
                    source = 'Legacy-Data'
                
                # 새 테이블에 데이터 삽입
                db.session.execute(text("""
                    INSERT INTO exchange_rates (timestamp, usd_krw, source, created_at)
                    VALUES (:timestamp, :usd_krw, :source, :created_at)
                """), {
                    'timestamp': timestamp,
                    'usd_krw': usd_krw_decimal,
                    'source': source,
                    'created_at': created_at
                })
            
            db.session.commit()
            logger.info(f"데이터 마이그레이션 완료: {len(backup_data)}개")
            return True
            
    except Exception as e:
        logger.error(f"데이터 마이그레이션 중 오류: {e}")
        db.session.rollback()
        return False

def verify_migration():
    """마이그레이션 결과 검증"""
    try:
        with app.app_context():
            # 1. 스키마 확인
            result = db.session.execute(text("DESCRIBE exchange_rates"))
            columns = result.fetchall()
            
            logger.info("마이그레이션 후 스키마:")
            for col in columns:
                logger.info(f"  {col[0]}: {col[1]} {col[2] if col[2] else ''}")
            
            # 2. 데이터 확인
            result = db.session.execute(text("SELECT COUNT(*) FROM exchange_rates"))
            count = result.fetchone()[0]
            logger.info(f"마이그레이션 후 데이터 개수: {count}")
            
            # 3. 최신 데이터 확인
            if count > 0:
                result = db.session.execute(text("""
                    SELECT timestamp, usd_krw, source 
                    FROM exchange_rates 
                    ORDER BY timestamp DESC 
                    LIMIT 3
                """))
                recent_data = result.fetchall()
                
                logger.info("최신 데이터:")
                for row in recent_data:
                    logger.info(f"  {row[0]}: {row[1]} ({row[2]})")
            
            return True
            
    except Exception as e:
        logger.error(f"마이그레이션 검증 중 오류: {e}")
        return False

def main():
    """메인 마이그레이션 실행"""
    logger.info("=" * 60)
    logger.info("ExchangeRate 테이블 마이그레이션 시작")
    logger.info("=" * 60)
    
    # 1. 현재 스키마 확인
    current_schema = check_current_schema()
    if current_schema is None:
        logger.error("현재 스키마를 확인할 수 없습니다.")
        return 1
    
    # 2. 마이그레이션 필요성 확인
    needs_migration = False
    
    if 'date' in current_schema:
        logger.info("✓ date 컬럼이 timestamp로 변경 필요")
        needs_migration = True
    
    if 'usd_krw' in current_schema and 'decimal(10,2)' in current_schema['usd_krw'].lower():
        logger.info("✓ usd_krw 정밀도가 DECIMAL(10,4)로 변경 필요")
        needs_migration = True
    
    if not needs_migration:
        logger.info("✅ 마이그레이션이 필요하지 않습니다.")
        return 0
    
    # 3. 사용자 확인
    response = input("\\n마이그레이션을 진행하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        logger.info("마이그레이션이 취소되었습니다.")
        return 0
    
    # 4. 기존 데이터 백업
    logger.info("\\n기존 데이터 백업 중...")
    backup_data = backup_existing_data()
    if backup_data is None:
        logger.error("데이터 백업 실패")
        return 1
    
    # 5. 스키마 마이그레이션
    logger.info("\\n스키마 마이그레이션 중...")
    if not migrate_schema():
        logger.error("스키마 마이그레이션 실패")
        return 1
    
    # 6. 데이터 마이그레이션
    logger.info("\\n데이터 마이그레이션 중...")
    if not migrate_data(backup_data):
        logger.error("데이터 마이그레이션 실패")
        return 1
    
    # 7. 마이그레이션 검증
    logger.info("\\n마이그레이션 검증 중...")
    if not verify_migration():
        logger.error("마이그레이션 검증 실패")
        return 1
    
    logger.info("\\n" + "=" * 60)
    logger.info("✅ 마이그레이션 완료!")
    logger.info("=" * 60)
    logger.info("\\n백업 데이터는 exchange_rates_backup 테이블에 저장되었습니다.")
    logger.info("문제가 없다면 나중에 백업 테이블을 삭제할 수 있습니다:")
    logger.info("  DROP TABLE exchange_rates_backup;")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())