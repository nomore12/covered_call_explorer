-- 기존 데이터를 보존하면서 새로운 컬럼 추가
-- 이 스크립트는 기존 데이터베이스를 새로운 스키마로 마이그레이션합니다.

-- transactions 테이블에 새 컬럼 추가
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS exchange_rate DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS amount_krw DECIMAL(18, 2),
ADD COLUMN IF NOT EXISTS dividend_used DECIMAL(18, 8) DEFAULT 0,
ADD COLUMN IF NOT EXISTS cash_invested_krw DECIMAL(18, 2) DEFAULT 0;

-- holdings 테이블에 새 컬럼 추가 (accumulated_dividends를 여러 컬럼으로 분리)
ALTER TABLE holdings 
ADD COLUMN IF NOT EXISTS avg_purchase_price DECIMAL(18, 8),
ADD COLUMN IF NOT EXISTS avg_exchange_rate DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS total_invested_krw DECIMAL(18, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_dividends_received DECIMAL(18, 8) DEFAULT 0,
ADD COLUMN IF NOT EXISTS dividends_reinvested DECIMAL(18, 8) DEFAULT 0,
ADD COLUMN IF NOT EXISTS dividends_withdrawn DECIMAL(18, 8) DEFAULT 0;

-- 기존 accumulated_dividends 데이터를 total_dividends_received로 복사
UPDATE holdings 
SET total_dividends_received = COALESCE(accumulated_dividends, 0)
WHERE total_dividends_received = 0 AND accumulated_dividends IS NOT NULL;

-- accumulated_dividends 컬럼 제거 (기존 데이터 이전 후)
ALTER TABLE holdings DROP COLUMN IF EXISTS accumulated_dividends;

-- 새 테이블들 생성
CREATE TABLE IF NOT EXISTS dividends (
    dividend_id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    shares_held DECIMAL(18, 8),
    dividend_per_share DECIMAL(18, 8),
    amount DECIMAL(18, 8) NOT NULL,
    reinvested_amount DECIMAL(18, 8) DEFAULT 0,
    withdrawn_amount DECIMAL(18, 8) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    usd_krw DECIMAL(10, 2) NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_dividends_ticker_date ON dividends (ticker, date);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_date ON exchange_rates (date);