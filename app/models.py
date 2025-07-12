from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
from datetime import date, datetime, timezone
from pytz import timezone as pytz_timezone

class Transaction(db.Model):
    """
    모든 주식 거래 내역(매수, 매도, 배당금 수령, 주가 업데이트 등)을 기록하는 모델
    환율 추적과 배당금 재투자 정보를 포함하여 정확한 수익률 계산 지원
    """
    __tablename__ = 'transactions'
    
    transaction_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    type = db.Column(db.String(50), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    shares = db.Column(db.DECIMAL(18, 8), nullable=False)
    price_per_share = db.Column(db.DECIMAL(18, 8), nullable=False)
    amount = db.Column(db.DECIMAL(18, 8), nullable=False)
    
    # 환율 관련 필드 추가
    exchange_rate = db.Column(db.DECIMAL(10, 2))  # 거래 시점 환율
    amount_krw = db.Column(db.DECIMAL(18, 2))  # 원화 금액
    
    # 자금 출처 추적 (재투자 시)
    dividend_used = db.Column(db.DECIMAL(18, 8), default=0)  # 사용한 배당금
    cash_invested_krw = db.Column(db.DECIMAL(18, 2), default=0)  # 추가 투입 원화
    
    note = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Transaction {self.type} {self.ticker} {self.shares}@{self.price_per_share} on {self.date}>"

class Holding(db.Model):
    """
    각 종목별 현재 보유 현황 및 요약 정보를 기록하는 모델
    환율 정보와 배당금 재투자 추적을 포함하여 정확한 수익률 계산 지원
    """
    __tablename__ = 'holdings'
    
    holding_id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, unique=True)
    current_shares = db.Column(db.DECIMAL(18, 8), nullable=False, default=0)
    
    # 원가 정보 개선
    total_cost_basis = db.Column(db.DECIMAL(18, 8), nullable=False, default=0)  # 달러 기준
    avg_purchase_price = db.Column(db.DECIMAL(18, 8))  # 평균 매수가
    avg_exchange_rate = db.Column(db.DECIMAL(10, 2))  # 평균 매수 환율
    
    # 원화 투자 정보
    total_invested_krw = db.Column(db.DECIMAL(18, 2), default=0)  # 총 투입 원화
    
    # 배당금 정보 세분화
    total_dividends_received = db.Column(db.DECIMAL(18, 8), default=0)  # 총 수령 배당금
    dividends_reinvested = db.Column(db.DECIMAL(18, 8), default=0)  # 재투자한 배당금
    dividends_withdrawn = db.Column(db.DECIMAL(18, 8), default=0)  # 인출한 배당금
    
    current_market_price = db.Column(db.DECIMAL(18, 8), nullable=False, default=0)
    last_price_update_date = db.Column(db.Date)
    updated_at = db.Column(db.TIMESTAMP, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Holding {self.ticker} Shares:{self.current_shares} Current Price:{self.current_market_price}>"


class Dividend(db.Model):
    """배당금 수령 내역을 별도로 관리"""
    __tablename__ = 'dividends'
    
    dividend_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    ticker = db.Column(db.String(10), nullable=False)
    shares_held = db.Column(db.DECIMAL(18, 8))  # 배당 시점 보유 주식수
    dividend_per_share = db.Column(db.DECIMAL(18, 8))  # 주당 배당금
    amount = db.Column(db.DECIMAL(18, 8), nullable=False)  # 실제 수령한 배당금 (세후)
    
    # 재투자 추적
    reinvested_amount = db.Column(db.DECIMAL(18, 8), default=0)  # 재투자한 금액
    withdrawn_amount = db.Column(db.DECIMAL(18, 8), default=0)  # 인출한 금액
    
    created_at = db.Column(db.TIMESTAMP, default=lambda: datetime.now(timezone.utc))


class ExchangeRate(db.Model):
    """실시간 환율 정보 관리"""
    __tablename__ = 'exchange_rates'
    
    rate_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc))
    usd_krw = db.Column(db.DECIMAL(10, 4), nullable=False)  # 정밀도 증가
    source = db.Column(db.String(50), default='ExchangeRate-API')  # 환율 출처
    created_at = db.Column(db.TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<ExchangeRate USD/KRW:{self.usd_krw} at {self.timestamp}>"
    
    
class CreditCard(db.Model):
    """카드 결제 내역"""
    __tablename__ = 'credit_card'
    
    spend_id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(
        db.TIMESTAMP,
        nullable=False,
        default=lambda: datetime.now(pytz_timezone('Asia/Seoul'))
    )
    money_spend = db.Column(db.Integer, nullable=False, default=0)
    
    def __init__(self, datetime=None, money_spend=0):
        if datetime is not None:
            self.datetime = datetime
        if money_spend is not None:
            self.money_spend = money_spend
    
    def __repr__(self):
        return f"<CreditCard {self.money_spend}원 at {self.datetime}>"