-- 데이터베이스 선택 (docker-compose.yml의 MYSQL_DATABASE 환경변수에 설정된 DB 사용)
-- USE mydb;

-- 1. transactions 테이블 생성 (확장된 버전)
-- 모든 거래 내역(매수, 매도, 배당금 수령)과 환율, 자금 출처 정보를 기록합니다.
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'BUY', 'SELL', 'DIVIDEND', 'PRICE_UPDATE' 등
    ticker VARCHAR(10) NOT NULL,
    shares DECIMAL(18, 8) NOT NULL, -- 주식 수 (매도는 음수, 배당금에는 0)
    price_per_share DECIMAL(18, 8) NOT NULL, -- 주당 가격 (거래 시 가격, 배당금에는 0)
    amount DECIMAL(18, 8) NOT NULL, -- 총 거래 금액 (shares * price_per_share 또는 배당금액)
    
    -- 환율 관련 필드 추가
    exchange_rate DECIMAL(10, 2), -- 거래 시점 환율
    amount_krw DECIMAL(18, 2), -- 원화 금액
    
    -- 자금 출처 추적 (재투자 시)
    dividend_used DECIMAL(18, 8) DEFAULT 0, -- 사용한 배당금
    cash_invested_krw DECIMAL(18, 2) DEFAULT 0, -- 추가 투입 원화
    
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 추가 (조회 성능 향상)
CREATE INDEX idx_transactions_ticker_date ON transactions (ticker, date);

-- 2. holdings 테이블 생성 (확장된 버전)
-- 각 종목별 현재 보유 현황 및 정확한 수익률 계산을 위한 정보를 기록합니다.
CREATE TABLE IF NOT EXISTS holdings (
    holding_id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE, -- 종목 코드는 유니크해야 함
    current_shares DECIMAL(18, 8) NOT NULL DEFAULT 0, -- 현재 보유 주식 수
    
    -- 원가 정보 개선
    total_cost_basis DECIMAL(18, 8) NOT NULL DEFAULT 0, -- 달러 기준 총 매수 원가
    avg_purchase_price DECIMAL(18, 8), -- 평균 매수가
    avg_exchange_rate DECIMAL(10, 2), -- 평균 매수 환율
    
    -- 원화 투자 정보
    total_invested_krw DECIMAL(18, 2) DEFAULT 0, -- 총 투입 원화
    
    -- 배당금 정보 세분화
    total_dividends_received DECIMAL(18, 8) DEFAULT 0, -- 총 수령 배당금
    dividends_reinvested DECIMAL(18, 8) DEFAULT 0, -- 재투자한 배당금
    dividends_withdrawn DECIMAL(18, 8) DEFAULT 0, -- 인출한 배당금
    
    current_market_price DECIMAL(18, 8) NOT NULL DEFAULT 0, -- 사용자가 마지막으로 입력한 현재 시장 가격
    last_price_update_date DATE, -- current_market_price가 마지막으로 업데이트된 날짜
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 추가 (조회 성능 향상)
CREATE INDEX idx_holdings_ticker ON holdings (ticker);

-- 3. dividends 테이블 생성 (새로 추가)
-- 배당금 수령 내역을 별도로 관리
CREATE TABLE IF NOT EXISTS dividends (
    dividend_id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    shares_held DECIMAL(18, 8), -- 배당 시점 보유 주식수
    dividend_per_share DECIMAL(18, 8), -- 주당 배당금
    amount DECIMAL(18, 8) NOT NULL, -- 실제 수령한 배당금 (세후)
    
    -- 재투자 추적
    reinvested_amount DECIMAL(18, 8) DEFAULT 0, -- 재투자한 금액
    withdrawn_amount DECIMAL(18, 8) DEFAULT 0, -- 인출한 금액
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. exchange_rates 테이블 생성 (선택사항)
-- 환율 이력 관리
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_id INT AUTO_INCREMENT PRIMARY KEY,
    usd_krw DECIMAL(10, 2) NOT NULL,
    source VARCHAR(50), -- 환율 출처
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. users 테이블 생성 (Flask-Login 사용자 관리)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- 6. refresh_tokens 테이블 생성 (JWT 인증)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP NULL,
    
    -- 보안 강화 필드
    ip_address VARCHAR(45), -- IPv6 지원
    user_agent TEXT,
    device_fingerprint VARCHAR(64),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 7. audit_logs 테이블 생성 (보안 감사)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 8. price_updates 테이블 수정 (기존 테이블이 있다면)
CREATE TABLE IF NOT EXISTS price_updates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    old_price DECIMAL(18, 8),
    new_price DECIMAL(18, 8) NOT NULL,
    source VARCHAR(50) DEFAULT 'api', -- 'toss', 'finnhub', 'manual' 등
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 추가
CREATE INDEX idx_dividends_ticker_date ON dividends (ticker, date);
CREATE INDEX idx_exchange_rates_date ON exchange_rates (date);
CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens (token);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens (expires_at);
CREATE INDEX idx_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs (action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs (timestamp);
CREATE INDEX idx_price_updates_ticker ON price_updates (ticker);

-- 초기 데이터 삽입 (선택 사항)
-- 필요한 경우 여기에 초기 데이터를 삽입할 수 있습니다.
-- 예: INSERT INTO holdings (ticker, current_shares, total_cost_basis) VALUES ('NVDY', 0, 0);