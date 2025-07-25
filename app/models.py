from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

db = SQLAlchemy()
from datetime import date, datetime, timezone

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
    
    

class User(UserMixin, db.Model):
    """사용자 계정 관리"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.TIMESTAMP)
    
    def set_password(self, password):
        """비밀번호 해시 생성"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """비밀번호 확인"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"


class RefreshToken(db.Model):
    """JWT Refresh Token 관리"""
    __tablename__ = 'refresh_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.TIMESTAMP, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    revoked_at = db.Column(db.TIMESTAMP)
    
    # 보안 강화 필드
    ip_address = db.Column(db.String(45))  # IPv6 지원
    user_agent = db.Column(db.Text)
    device_fingerprint = db.Column(db.String(64))
    
    # 관계 설정
    user = db.relationship('User', backref=db.backref('refresh_tokens', lazy=True))
    
    @staticmethod
    def generate_token():
        """안전한 랜덤 토큰 생성"""
        return secrets.token_urlsafe(32)
    
    def revoke(self):
        """토큰 무효화"""
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)
    
    def is_expired(self):
        """토큰 만료 확인"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_valid(self):
        """토큰 유효성 확인"""
        return not self.is_revoked and not self.is_expired()
    
    def __repr__(self):
        return f"<RefreshToken {self.user_id} expires:{self.expires_at}>"


class AuditLog(db.Model):
    """보안 감사 로그"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    details = db.Column(db.JSON)
    timestamp = db.Column(db.TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    
    # 관계 설정
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))
    
    @staticmethod
    def log_action(user_id, action, resource=None, ip_address=None, user_agent=None, details=None):
        """감사 로그 기록"""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
        db.session.add(log)
        db.session.commit()
    
    def __repr__(self):
        return f"<AuditLog {self.user_id} {self.action} at {self.timestamp}>"