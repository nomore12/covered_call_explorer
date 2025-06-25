-- 데이터베이스 선택 (docker-compose.yml의 MYSQL_DATABASE 환경변수에 설정된 DB 사용)
-- USE mydb;

-- 1. transactions 테이블 생성
-- 모든 거래 내역(매수, 매도, 배당금 수령)을 기록합니다.
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'BUY', 'SELL', 'DIVIDEND', 'PRICE_UPDATE' 등
    ticker VARCHAR(10) NOT NULL,
    shares DECIMAL(18, 8) NOT NULL, -- 주식 수 (매도는 음수, 배당금에는 0)
    price_per_share DECIMAL(18, 8) NOT NULL, -- 주당 가격 (거래 시 가격, 배당금에는 0)
    amount DECIMAL(18, 8) NOT NULL, -- 총 거래 금액 (shares * price_per_share 또는 배당금액)
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 추가 (조회 성능 향상)
CREATE INDEX idx_transactions_ticker_date ON transactions (ticker, date);

-- 2. holdings 테이블 생성
-- 각 종목별 현재 보유 현황 및 요약 정보를 기록합니다.
CREATE TABLE IF NOT EXISTS holdings (
    holding_id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE, -- 종목 코드는 유니크해야 함
    current_shares DECIMAL(18, 8) NOT NULL DEFAULT 0, -- 현재 보유 주식 수
    total_cost_basis DECIMAL(18, 8) NOT NULL DEFAULT 0, -- 현재 보유 주식의 총 매수 원가
    accumulated_dividends DECIMAL(18, 8) NOT NULL DEFAULT 0, -- 해당 종목으로부터 받은 총 누적 배당금
    current_market_price DECIMAL(18, 8) NOT NULL DEFAULT 0, -- 사용자가 마지막으로 입력한 현재 시장 가격
    last_price_update_date DATE, -- current_market_price가 마지막으로 업데이트된 날짜
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 추가 (조회 성능 향상)
CREATE INDEX idx_holdings_ticker ON holdings (ticker);

-- 초기 데이터 삽입 (선택 사항)
-- 필요한 경우 여기에 초기 데이터를 삽입할 수 있습니다.
-- 예: INSERT INTO holdings (ticker, current_shares, total_cost_basis) VALUES ('NVDY', 0, 0);