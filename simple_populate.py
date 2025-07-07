import sys
sys.path.insert(0, '/app')

from decimal import Decimal
from app import app, db
from app.models import Transaction, Holding

def calculate_holdings():
    with app.app_context():
        try:
            print('Holdings calculation started...')
            
            # Clear existing holdings
            Holding.query.delete()
            
            # Get all transactions
            transactions = Transaction.query.order_by(Transaction.date.asc()).all()
            print(f'Found {len(transactions)} transactions')
            
            # Group by ticker
            holdings_data = {}
            
            for txn in transactions:
                ticker = txn.ticker
                
                if ticker not in holdings_data:
                    holdings_data[ticker] = {
                        'total_shares': Decimal('0'),
                        'total_cost_basis': Decimal('0'),
                        'total_invested_krw': Decimal('0'),
                        'weighted_exchange_rate': Decimal('0'),
                        'weighted_price': Decimal('0'),
                    }
                
                data = holdings_data[ticker]
                shares = Decimal(str(txn.shares))
                price_per_share = Decimal(str(txn.price_per_share))
                total_amount_usd = Decimal(str(txn.amount))
                exchange_rate = Decimal(str(txn.exchange_rate or 1400))
                amount_krw = Decimal(str(txn.amount_krw or 0))
                
                if txn.type == 'BUY':
                    prev_total_shares = data['total_shares']
                    prev_total_cost = data['total_cost_basis']
                    prev_total_krw = data['total_invested_krw']
                    
                    new_total_shares = prev_total_shares + shares
                    new_total_cost = prev_total_cost + total_amount_usd
                    new_total_krw = prev_total_krw + amount_krw
                    
                    if new_total_shares > 0:
                        data['weighted_price'] = new_total_cost / new_total_shares
                    
                    if new_total_krw > 0 and new_total_cost > 0:
                        data['weighted_exchange_rate'] = new_total_krw / new_total_cost
                    
                    data['total_shares'] = new_total_shares
                    data['total_cost_basis'] = new_total_cost
                    data['total_invested_krw'] = new_total_krw
                    
                    print(f'  {ticker}: {shares} shares @ ${price_per_share}')
            
            # Insert into Holdings table
            print('Saving to Holdings table...')
            
            for ticker, data in holdings_data.items():
                if data['total_shares'] > 0:
                    holding = Holding()
                    holding.ticker = ticker
                    holding.current_shares = float(data['total_shares'])
                    holding.avg_purchase_price = float(data['weighted_price'])
                    holding.total_cost_basis = float(data['total_cost_basis'])
                    holding.total_invested_krw = float(data['total_invested_krw'])
                    holding.avg_exchange_rate = float(data['weighted_exchange_rate'])
                    holding.current_market_price = float(data['weighted_price'])
                    
                    db.session.add(holding)
                    
                    print(f'  Added {ticker}: {data["total_shares"]} shares, avg price: ${data["weighted_price"]:.4f}')
            
            db.session.commit()
            print('Holdings table updated successfully!')
            
            holdings = Holding.query.all()
            print(f'Total holdings: {len(holdings)}')
            
        except Exception as e:
            print(f'Error: {e}')
            db.session.rollback()
            raise

calculate_holdings()