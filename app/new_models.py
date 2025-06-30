from .__init__ import db # __init__.py에서 db 객체를 가져옵니다.
from datetime import date, datetime


"""
주요 개선 사항 요약

1. 환율 추적: 모든 거래에 환율과 원화 금액 기록
2. 자금 출처 구분: 배당금 재투자와 신규 투자금 구분
3. 배당금 상세 관리: 별도 테이블로 재투자 등 추적
4. 원화 기준 계산: 실제 투입한 원화 금액 정확히 기록

이렇게 하면 달러 수익률과 원화 수익률을 정확히 분리해서 계산할 수 있고, 배당금 재투자 효과도 명확히 파악할 수 있습니다.
"""

class Transaction(db.Model):
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
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)


class Holding(db.Model):
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
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)


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
    
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)


class ExchangeRate(db.Model):
    """환율 이력 관리 (선택사항)"""
    __tablename__ = 'exchange_rates'
    
    rate_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    usd_krw = db.Column(db.DECIMAL(10, 2), nullable=False)
    source = db.Column(db.String(50))  # 환율 출처
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)