-- ExchangeRate 테이블 마이그레이션 SQL
-- 기존 exchange_rates 테이블을 새로운 구조로 변경

-- 1. 기존 데이터 백업 (선택사항)
CREATE TABLE IF NOT EXISTS exchange_rates_backup AS 
SELECT * FROM exchange_rates;

-- 2. 기존 테이블 삭제 (MySQL 버전 호환성 고려)
DROP TABLE exchange_rates;

-- 3. 새로운 구조로 테이블 생성
CREATE TABLE exchange_rates (
    rate_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usd_krw DECIMAL(10, 4) NOT NULL,  -- 정밀도 증가 (10, 2) -> (10, 4)
    source VARCHAR(50) DEFAULT 'ExchangeRate-API',  -- 환율 출처 추가
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 인덱스 추가
CREATE INDEX idx_exchange_rates_timestamp ON exchange_rates (timestamp);

-- 5. 기존 데이터 복원 (필요한 경우)
-- 기존 date 컬럼을 timestamp로 변환하여 복원
INSERT INTO exchange_rates (timestamp, usd_krw, source, created_at)
SELECT 
    CONVERT_TZ(CONCAT(date, ' 00:00:00'), '+00:00', '+00:00') as timestamp,
    usd_krw,
    'ExchangeRate-API' as source,
    created_at
FROM exchange_rates_backup;

-- 6. 백업 테이블 삭제 (선택사항)
-- DROP TABLE exchange_rates_backup;

-- 완료 메시지
SELECT 'ExchangeRate 테이블 마이그레이션이 완료되었습니다.' as message; 