from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pytz import timezone as pytz_timezone

db = SQLAlchemy()

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

    def __repr__(self):
        return f"<CreditCard {self.spend_id}: {self.money_spend}원 at {self.datetime}>"