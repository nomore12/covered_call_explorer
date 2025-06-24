from .__init__ import db # __init__.py에서 db 객체를 가져옵니다.
from datetime import date, datetime

class Transaction(db.Model):
    """
    모든 주식 거래 내역(매수, 매도, 배당금 수령, 주가 업데이트 등)을 기록하는 모델
    init_db.sql의 transactions 테이블 스키마에 맞춰 정의
    """
    __tablename__ = 'transactions' # 테이블 이름 명시

    transaction_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    type = db.Column(db.String(50), nullable=False) # 'BUY', 'SELL', 'DIVIDEND', 'PRICE_UPDATE'
    ticker = db.Column(db.String(10), nullable=False)
    shares = db.Column(db.DECIMAL(18, 8), nullable=False)
    price_per_share = db.Column(db.DECIMAL(18, 8), nullable=False)
    amount = db.Column(db.DECIMAL(18, 8), nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction {self.type} {self.ticker} {self.shares}@{self.price_per_share} on {self.date}>"

class Holding(db.Model):
    """
    각 종목별 현재 보유 현황 및 요약 정보를 기록하는 모델
    init_db.sql의 holdings 테이블 스키마에 맞춰 정의
    """
    __tablename__ = 'holdings' # 테이블 이름 명시

    holding_id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, unique=True)
    current_shares = db.Column(db.DECIMAL(18, 8), nullable=False, default=0)
    total_cost_basis = db.Column(db.DECIMAL(18, 8), nullable=False, default=0)
    accumulated_dividends = db.Column(db.DECIMAL(18, 8), nullable=False, default=0)
    current_market_price = db.Column(db.DECIMAL(18, 8), nullable=False, default=0)
    last_price_update_date = db.Column(db.Date)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<Holding {self.ticker} Shares:{self.current_shares} Current Price:{self.current_market_price}>"