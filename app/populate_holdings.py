#!/usr/bin/env python3
"""
transactions 데이터를 기반으로 holdings 테이블을 채우는 스크립트
"""

import sys
import os
from decimal import Decimal
from collections import defaultdict

# Flask 앱 경로 추가
sys.path.append('/app')

from app import app, db
from app.models import Transaction, Holding

def calculate_holdings():
    """
    transactions 테이블의 데이터를 기반으로 holdings 테이블을 계산하고 채움
    """
    
    with app.app_context():
        try:
            print("🔄 Holdings 테이블 계산 시작...")
            
            # 기존 holdings 데이터 삭제
            print("📝 기존 holdings 데이터 삭제...")
            Holding.query.delete()
            
            # 모든 거래 내역 가져오기 (날짜순 정렬)
            transactions = Transaction.query.order_by(Transaction.date.asc()).all()
            print(f"📊 총 {len(transactions)}건의 거래 내역 발견")
            
            # 종목별로 거래 내역 그룹화 및 계산
            holdings_data = {}
            
            for txn in transactions:
                ticker = txn.ticker
                
                if ticker not in holdings_data:
                    holdings_data[ticker] = {
                        'total_shares': Decimal('0'),
                        'total_cost_basis': Decimal('0'),  # 총 투자 금액 (USD)
                        'total_invested_krw': Decimal('0'),  # 총 투자 금액 (KRW)
                        'weighted_exchange_rate': Decimal('0'),  # 가중평균 환율
                        'weighted_price': Decimal('0'),  # 가중평균 매수가
                        'transactions': []
                    }
                
                data = holdings_data[ticker]
                shares = Decimal(str(txn.shares))
                price_per_share = Decimal(str(txn.price_per_share))
                total_amount_usd = Decimal(str(txn.amount))
                exchange_rate = Decimal(str(txn.exchange_rate or 1400))
                amount_krw = Decimal(str(txn.amount_krw or 0))
                
                if txn.type == 'BUY':
                    # 매수의 경우
                    prev_total_shares = data['total_shares']
                    prev_total_cost = data['total_cost_basis']
                    prev_total_krw = data['total_invested_krw']
                    
                    # 새로운 총 수량 및 비용
                    new_total_shares = prev_total_shares + shares
                    new_total_cost = prev_total_cost + total_amount_usd
                    new_total_krw = prev_total_krw + amount_krw
                    
                    # 가중평균 매수가 계산
                    if new_total_shares > 0:
                        data['weighted_price'] = new_total_cost / new_total_shares
                    
                    # 가중평균 환율 계산
                    if new_total_krw > 0 and new_total_cost > 0:
                        data['weighted_exchange_rate'] = new_total_krw / new_total_cost
                    
                    data['total_shares'] = new_total_shares
                    data['total_cost_basis'] = new_total_cost
                    data['total_invested_krw'] = new_total_krw
                    
                elif txn.type == 'SELL':
                    # 매도의 경우 (현재는 매수만 있지만 확장성을 위해)
                    data['total_shares'] -= shares
                    # 매도 시 비례적으로 cost basis 감소
                    if data['total_shares'] > 0:
                        ratio = shares / (data['total_shares'] + shares)
                        data['total_cost_basis'] *= (1 - ratio)
                        data['total_invested_krw'] *= (1 - ratio)
                
                data['transactions'].append(txn)
                
                print(f"  📈 {ticker}: {shares}주 매수 @ ${price_per_share} (환율: {exchange_rate})")
            
            # Holdings 테이블에 데이터 삽입
            print("💾 Holdings 테이블에 데이터 저장...")
            
            for ticker, data in holdings_data.items():
                if data['total_shares'] > 0:  # 보유 수량이 있는 경우만
                    holding = Holding()
                    holding.ticker = ticker
                    holding.current_shares = float(data['total_shares'])
                    holding.avg_purchase_price = float(data['weighted_price'])
                    holding.total_cost_basis = float(data['total_cost_basis'])
                    holding.total_invested_krw = float(data['total_invested_krw'])
                    holding.avg_exchange_rate = float(data['weighted_exchange_rate'])
                    
                    # 현재 시장가는 임시로 평균 매수가로 설정 (나중에 API로 업데이트)
                    holding.current_market_price = float(data['weighted_price'])
                    
                    db.session.add(holding)
                    
                    print(f"  ✅ {ticker}: {data['total_shares']}주, 평균가: ${data['weighted_price']:.4f}, 평균환율: {data['weighted_exchange_rate']:.2f}")
            
            # 변경사항 커밋
            db.session.commit()
            print("✨ Holdings 테이블 업데이트 완료!")
            
            # 결과 확인
            holdings = Holding.query.all()
            print(f"📋 총 {len(holdings)}개 종목 보유 중:")
            for holding in holdings:
                print(f"  📊 {holding.ticker}: {holding.current_shares}주, ${holding.avg_purchase_price:.4f}, ₩{holding.total_invested_krw:,.0f}")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    calculate_holdings()