from flask import jsonify, request, Blueprint
from ..models import Holding, Transaction, Dividend, db
from ..scheduler import update_stock_price
from ..price_updater import update_stock_prices
from ..exchange_rate_service import exchange_rate_service
import yfinance as yf
from pytz import timezone as pytz_timezone
from datetime import datetime
import finnhub
import os

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/update_prices')
def update_all_prices():
    """모든 보유 종목의 주가를 업데이트"""
    try:
        result = update_stock_price()
        
        return jsonify({
            "success": result['success'],
            "message": result['message'],
            "updated": result['updated'],
            "failed": result.get('failed', [])
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"오류가 발생했습니다: {str(e)}",
            "updated": [],
            "failed": []
        }), 500

@stock_bp.route('/update_price/<ticker>')
def update_single_price(ticker):
    """특정 종목의 주가를 업데이트"""
    try:
        ticker = ticker.upper()
        result = update_stock_price(ticker=ticker)
        
        return jsonify({
            "success": result['success'],
            "message": result['message'],
            "updated": result['updated'],
            "failed": result.get('failed', [])
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"오류가 발생했습니다: {str(e)}",
            "updated": [],
            "failed": []
        }), 500


@stock_bp.route('/finnhub/<ticker>')
def finnhub_ticker(ticker):
    finnhub_client = finnhub.Client(api_key=os.getenv('FINNHUB_API'))
    
    try:
        quote = finnhub_client.quote(ticker.upper())
        
        # timestamp를 읽기 쉬운 날짜로 변환
        from datetime import datetime
        timestamp = datetime.fromtimestamp(quote['t'])
        
        return {
            "ticker": ticker,
            "current_price": quote['c'],
            "change": {
                "amount": quote['d'],
                "percent": f"{quote['dp']:.2f}%"
            },
            "range": {
                "high": quote['h'],
                "low": quote['l']
            },
            "open": quote['o'],
            "previous_close": quote['pc'],
            "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {"error": str(e)}, 403


@stock_bp.route('/test_yfinance/<ticker>')
def test_yfinance_direct(ticker):
    """yfinance 직접 테스트"""
    try:
        ticker = ticker.upper()
        
        # 간단한 yfinance 테스트
        ticker_obj = yf.Ticker(ticker)
        print(ticker_obj.info, ticker_obj.analyst_price_targets)
        hist = ticker_obj.history(period="1d")
        
        if not hist.empty:
            latest_price = float(hist['Close'].iloc[-1])
            # DatetimeIndex의 마지막 날짜를 가져오기
            last_datetime = hist.index[-1]
            try:
                # pandas Timestamp 객체에서 날짜 추출
                last_date = str(last_datetime)[:10]  # YYYY-MM-DD 형식으로 자르기
            except:
                last_date = str(last_datetime)[:10]
            
            return jsonify({
                "success": True,
                "ticker": ticker,
                "price": latest_price,
                "data_points": len(hist),
                "last_date": last_date
            })
        else:
            return jsonify({
                "success": False,
                "ticker": ticker,
                "error": "No data returned from yfinance"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "ticker": ticker,
            "error": str(e)
        })


@stock_bp.route('/holdings', methods=['GET'])
def get_holdings():
    """현재 보유 종목 목록 조회 - 프론트엔드 API 호환 + finnhub 실시간 주가 업데이트"""
    print("🚀 get_holdings function called")
    try:
        print("📋 Querying holdings from database...")
        holdings = Holding.query.filter(Holding.current_shares > 0).all()
        print(f"📊 Found {len(holdings)} holdings")
        
        # finnhub를 이용한 실시간 주가 업데이트
        finnhub_client = finnhub.Client(api_key=os.getenv('FINNHUB_API'))
        price_updates = []
        
        print(f"🔄 Updating prices for {len(holdings)} holdings using Finnhub...")
        
        for holding in holdings:
            try:
                print(f"  📊 Fetching price for {holding.ticker}...")
                # finnhub에서 현재 주가 가져오기
                quote = finnhub_client.quote(holding.ticker)
                current_price = quote['c']  # current price
                
                
                print(f"  📈 {holding.ticker}: API price = ${current_price}, DB price = ${holding.current_market_price}")
                
                if current_price and current_price > 0:
                    # 기존 가격과 비교하여 변화가 있을 때만 업데이트
                    old_price = float(holding.current_market_price)
                    price_diff = abs(current_price - old_price)
                    
                    print(f"  🔍 {holding.ticker}: Price difference = ${price_diff:.6f}")
                    
                    if price_diff > 0.001:  # 0.001달러 이상 차이날 때만 업데이트
                        holding.current_market_price = current_price
                        holding.last_price_update_date = datetime.now().date()
                        price_updates.append({
                            'ticker': holding.ticker,
                            'old_price': old_price,
                            'new_price': current_price,
                            'source': 'finnhub',
                            'difference': price_diff
                        })
                        print(f"  ✅ {holding.ticker}: Updated ${old_price:.3f} → ${current_price:.3f}")
                    else:
                        price_updates.append({
                            'ticker': holding.ticker,
                            'old_price': old_price,
                            'new_price': current_price,
                            'source': 'finnhub',
                            'difference': price_diff
                        })
                        print(f"  ➡️ {holding.ticker}: No significant change (diff: ${price_diff:.6f})")
                else:
                    print(f"  ❌ {holding.ticker}: Invalid price from API: {current_price}")
                        
            except Exception as e:
                print(f"  ❌ Failed to update price for {holding.ticker}: {e}")
                # finnhub 실패시 기존 가격 유지
                continue
        
        print(f"📝 Total price updates: {len(price_updates)}")
        
        # 변경사항 커밋
        db.session.commit()
        
        holdings_data = []
        for holding in holdings:
            # 현재 가치 계산
            current_value_usd = float(holding.current_shares) * float(holding.current_market_price)
            current_value_krw = current_value_usd * float(holding.avg_exchange_rate or 1400)  # 기본 환율
            
            # 손익 계산
            total_invested_usd = float(holding.total_cost_basis)
            total_invested_krw = float(holding.total_invested_krw or 0)
            
            unrealized_pnl_usd = current_value_usd - total_invested_usd
            unrealized_pnl_krw = current_value_krw - total_invested_krw
            
            # 수익률 계산
            return_rate_usd = (unrealized_pnl_usd / total_invested_usd * 100) if total_invested_usd > 0 else 0
            return_rate_krw = (unrealized_pnl_krw / total_invested_krw * 100) if total_invested_krw > 0 else 0
            
            holdings_data.append({
                "id": holding.holding_id,
                "ticker": holding.ticker,
                "total_shares": float(holding.current_shares),
                "total_invested_usd": total_invested_usd,
                "total_invested_krw": total_invested_krw,
                "average_price": float(holding.avg_purchase_price or 0),
                "current_price": float(holding.current_market_price),
                "current_value_usd": current_value_usd,
                "current_value_krw": current_value_krw,
                "unrealized_pnl_usd": unrealized_pnl_usd,
                "unrealized_pnl_krw": unrealized_pnl_krw,
                "return_rate_usd": return_rate_usd,
                "return_rate_krw": return_rate_krw,
                "created_at": holding.created_at.isoformat() if holding.created_at else None,
                "updated_at": holding.updated_at.isoformat() if holding.updated_at else None
            })
        
        return jsonify({
            "holdings": holdings_data,
            "price_updates": price_updates,
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error in get_holdings: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@stock_bp.route('/holdings/<ticker>', methods=['GET'])
def get_holding(ticker):
    """특정 종목의 보유 현황 조회"""
    try:
        ticker = ticker.upper()
        holding = Holding.query.filter_by(ticker=ticker).first()
        
        if not holding:
            return jsonify({"error": "종목을 찾을 수 없습니다"}), 404
        
        # 현재 가치 및 손익 계산
        current_value_usd = float(holding.current_shares) * float(holding.current_market_price)
        current_value_krw = current_value_usd * float(holding.avg_exchange_rate or 1400)
        
        total_invested_usd = float(holding.total_cost_basis)
        total_invested_krw = float(holding.total_invested_krw or 0)
        
        unrealized_pnl_usd = current_value_usd - total_invested_usd
        unrealized_pnl_krw = current_value_krw - total_invested_krw
        
        return_rate_usd = (unrealized_pnl_usd / total_invested_usd * 100) if total_invested_usd > 0 else 0
        return_rate_krw = (unrealized_pnl_krw / total_invested_krw * 100) if total_invested_krw > 0 else 0
        
        holding_data = {
            "id": holding.holding_id,
            "ticker": holding.ticker,
            "total_shares": float(holding.current_shares),
            "total_invested_usd": total_invested_usd,
            "total_invested_krw": total_invested_krw,
            "average_price": float(holding.avg_purchase_price or 0),
            "current_price": float(holding.current_market_price),
            "current_value_usd": current_value_usd,
            "current_value_krw": current_value_krw,
            "unrealized_pnl_usd": unrealized_pnl_usd,
            "unrealized_pnl_krw": unrealized_pnl_krw,
            "return_rate_usd": return_rate_usd,
            "return_rate_krw": return_rate_krw,
            "created_at": holding.created_at.isoformat() if holding.created_at else None,
            "updated_at": holding.updated_at.isoformat() if holding.updated_at else None
        }
        
        return jsonify(holding_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stock_bp.route('/portfolio', methods=['GET'])
def get_portfolio():
    print("get portfolio")
    """포트폴리오 전체 요약 정보 조회 - yfinance로 실시간 주가 업데이트"""
    try:
        holdings = Holding.query.filter(Holding.current_shares > 0).all()
        
        # 개선된 주가 업데이트 함수 사용
        print("🔄 Updating stock prices for portfolio...")
        updated_prices = update_stock_prices(holdings)
        
        # 변경사항 커밋
        db.session.commit()
        
        total_invested_usd = 0
        total_invested_krw = 0
        total_current_value_usd = 0
        total_current_value_krw = 0
        
        for holding in holdings:
            # 개별 종목 계산
            current_value_usd = float(holding.current_shares) * float(holding.current_market_price)
            current_value_krw = current_value_usd * float(holding.avg_exchange_rate or 1400)
            
            total_invested_usd += float(holding.total_cost_basis)
            total_invested_krw += float(holding.total_invested_krw or 0)
            total_current_value_usd += current_value_usd
            total_current_value_krw += current_value_krw
        
        # 손익 계산
        total_unrealized_pnl_usd = total_current_value_usd - total_invested_usd
        total_unrealized_pnl_krw = total_current_value_krw - total_invested_krw
        
        # 수익률 계산
        total_return_rate_usd = (total_unrealized_pnl_usd / total_invested_usd * 100) if total_invested_usd > 0 else 0
        total_return_rate_krw = (total_unrealized_pnl_krw / total_invested_krw * 100) if total_invested_krw > 0 else 0
        
        # 총 배당금 계산 (현재 보유 종목의 배당금만 포함)
        total_dividends_usd = 0
        total_dividends_krw = 0
        
        # 각 보유 종목별 배당금 계산
        for holding in holdings:
            # 해당 종목의 배당금만 조회
            ticker_dividends = Dividend.query.filter_by(ticker=holding.ticker).all()
            
            for dividend in ticker_dividends:
                # 현금으로 수령한 배당금만 계산 (인출한 배당금)
                withdrawn_amount = float(dividend.withdrawn_amount or 0)
                if withdrawn_amount > 0:
                    total_dividends_usd += withdrawn_amount
                    # 배당금 수령 시점의 환율 적용 (기본값 1400 사용)
                    total_dividends_krw += withdrawn_amount * 1400
        
        # 배당금 포함 총 손익 계산
        # USD: 미실현 손익 + 현금 수령 배당금
        total_pnl_with_dividends_usd = total_unrealized_pnl_usd + total_dividends_usd
        
        # KRW: 미실현 손익 + 현금 수령 배당금 (원화 환산)
        total_pnl_with_dividends_krw = total_unrealized_pnl_krw + total_dividends_krw
        
        # 배당금 포함 총 수익률 계산
        total_return_with_dividends_usd = (total_pnl_with_dividends_usd / total_invested_usd * 100) if total_invested_usd > 0 else 0
        total_return_with_dividends_krw = (total_pnl_with_dividends_krw / total_invested_krw * 100) if total_invested_krw > 0 else 0
        
        portfolio_summary = {
            "total_invested_usd": total_invested_usd,
            "total_invested_krw": total_invested_krw,
            "total_current_value_usd": total_current_value_usd,
            "total_current_value_krw": total_current_value_krw,
            "total_unrealized_pnl_usd": total_unrealized_pnl_usd,
            "total_unrealized_pnl_krw": total_unrealized_pnl_krw,
            "total_return_rate_usd": total_return_rate_usd,
            "total_return_rate_krw": total_return_rate_krw,
            "total_dividends_usd": total_dividends_usd,
            "total_dividends_krw": total_dividends_krw,
            # 배당금 포함 총 손익 추가
            "total_pnl_with_dividends_usd": total_pnl_with_dividends_usd,
            "total_pnl_with_dividends_krw": total_pnl_with_dividends_krw,
            "total_return_with_dividends_usd": total_return_with_dividends_usd,
            "total_return_with_dividends_krw": total_return_with_dividends_krw,
            "price_updates": updated_prices,  # 업데이트된 주가 정보
            "last_updated": datetime.now().isoformat()  # 마지막 업데이트 시간
        }
        
        return jsonify(portfolio_summary)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stock_bp.route('/transactions', methods=['GET', 'POST'])
def handle_transactions():
    """거래 내역 조회 및 생성"""
    print(f"Received {request.method} request to /transactions")
    
    if request.method == 'GET':
        try:
            transactions = Transaction.query.order_by(Transaction.date.desc()).all()
            
            transactions_data = []
            for txn in transactions:
                transactions_data.append({
                    "id": txn.transaction_id,
                    "ticker": txn.ticker,
                    "transaction_type": txn.type,
                    "shares": float(txn.shares),
                    "price_per_share": float(txn.price_per_share),
                    "total_amount_usd": float(txn.amount),
                    "exchange_rate": float(txn.exchange_rate or 0),
                    "krw_amount": float(txn.amount_krw or 0),
                    "dividend_reinvestment": float(txn.dividend_used or 0),
                    "transaction_date": txn.date.isoformat(),
                    "created_at": txn.created_at.isoformat() if txn.created_at else None
                })
            
            return jsonify(transactions_data)
            
        except Exception as e:
            print(f"GET /transactions error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    # POST 요청 처리
    try:
        print("Processing POST request...")
        data = request.get_json()
        print(f"Received data: {data}")
        
        if not data:
            print("No JSON data received")
            return jsonify({"error": "JSON 데이터가 필요합니다."}), 400
        
        # 필수 필드 검증
        required_fields = ['transaction_type', 'ticker', 'shares', 'price_per_share', 'total_amount_usd']
        for field in required_fields:
            if field not in data:
                print(f"Missing required field: {field}")
                return jsonify({"error": f"필수 필드가 누락되었습니다: {field}"}), 400
        
        print("Creating new transaction...")
        # 새 거래 생성
        new_transaction = Transaction()
        new_transaction.date = datetime.strptime(data.get('transaction_date', datetime.now().date().isoformat()), '%Y-%m-%d').date()
        new_transaction.type = data['transaction_type']
        new_transaction.ticker = data['ticker'].upper()
        new_transaction.shares = data['shares']
        new_transaction.price_per_share = data['price_per_share']
        new_transaction.amount = data['total_amount_usd']
        new_transaction.exchange_rate = data.get('exchange_rate')
        new_transaction.amount_krw = data.get('krw_amount')
        new_transaction.dividend_used = data['total_amount_usd'] if data.get('dividend_reinvestment') else 0
        new_transaction.cash_invested_krw = data.get('krw_amount', 0) if not data.get('dividend_reinvestment') else 0
        
        print("Adding to database...")
        db.session.add(new_transaction)
        db.session.commit()
        print(f"Transaction created with ID: {new_transaction.transaction_id}")
        
        return jsonify({
            "id": new_transaction.transaction_id,
            "message": "거래가 성공적으로 생성되었습니다."
        }), 201
        
    except Exception as e:
        print(f"POST /transactions error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@stock_bp.route('/dividends', methods=['GET', 'POST'])
def handle_dividends():
    """배당금 내역 조회 및 생성"""
    if request.method == 'GET':
        try:
            dividends = Dividend.query.order_by(Dividend.date.desc()).all()
            
            dividends_data = []
            for div in dividends:
                dividends_data.append({
                    "id": div.dividend_id,
                    "ticker": div.ticker,
                    "amount_usd": float(div.amount),
                    "amount_krw": float(div.amount) * 1400,  # 평균 환율 적용
                    "payment_date": div.date.isoformat(),
                    "created_at": div.created_at.isoformat() if div.created_at else None
                })
            
            return jsonify(dividends_data)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # POST 요청 처리
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON 데이터가 필요합니다."}), 400
        
        # 필수 필드 검증
        required_fields = ['ticker', 'amount_usd']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"필수 필드가 누락되었습니다: {field}"}), 400
        
        # 새 배당금 기록 생성
        new_dividend = Dividend()
        new_dividend.date = datetime.strptime(data.get('payment_date', datetime.now().date().isoformat()), '%Y-%m-%d').date()
        new_dividend.ticker = data['ticker'].upper()
        new_dividend.amount = data['amount_usd']
        
        db.session.add(new_dividend)
        db.session.commit()
        
        return jsonify({
            "id": new_dividend.dividend_id,
            "message": "배당금이 성공적으로 기록되었습니다."
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@stock_bp.route('/update-price', methods=['POST'])
def update_price():
    """주가 업데이트 API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON 데이터가 필요합니다."}), 400
        
        # 필수 필드 검증
        required_fields = ['ticker', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"필수 필드가 누락되었습니다: {field}"}), 400
        
        ticker = data['ticker'].upper()
        price = data['price']
        
        # 종목 찾기
        holding = Holding.query.filter_by(ticker=ticker).first()
        if not holding:
            return jsonify({"error": "종목을 찾을 수 없습니다"}), 404
        
        # 주가 업데이트
        holding.current_market_price = price
        holding.last_price_update_date = datetime.now().date()
        
        db.session.commit()
        
        return jsonify({
            "message": f"{ticker} 주가가 ${price}로 업데이트되었습니다.",
            "ticker": ticker,
            "price": price
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@stock_bp.route('/populate-holdings', methods=['POST'])
def populate_holdings():
    """transactions 데이터를 기반으로 holdings 테이블을 다시 계산하고 채움"""
    try:
        from decimal import Decimal
        
        print("🔄 Holdings 테이블 재계산 시작...")
        
        # 기존 holdings 데이터 삭제
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
                    'total_cost_krw': Decimal('0'),  # 환율 계산용
                }
            
            data = holdings_data[ticker]
            shares = Decimal(str(txn.shares))
            total_amount_usd = Decimal(str(txn.amount))
            exchange_rate = Decimal(str(txn.exchange_rate or 1400))
            amount_krw = Decimal(str(txn.amount_krw or 0))
            
            if txn.type == 'BUY':
                data['total_shares'] += shares
                data['total_cost_basis'] += total_amount_usd
                data['total_invested_krw'] += amount_krw
                data['total_cost_krw'] += total_amount_usd * exchange_rate
                
                print(f"  📈 {ticker}: {shares}주 매수 @ ${txn.price_per_share}")
        
        # Holdings 테이블에 데이터 삽입
        print("💾 Holdings 테이블에 데이터 저장...")
        
        results = []
        for ticker, data in holdings_data.items():
            if data['total_shares'] > 0:  # 보유 수량이 있는 경우만
                avg_price = data['total_cost_basis'] / data['total_shares']
                avg_exchange_rate = data['total_cost_krw'] / data['total_cost_basis'] if data['total_cost_basis'] > 0 else Decimal('1400')
                
                holding = Holding()
                holding.ticker = ticker
                holding.current_shares = float(data['total_shares'])
                holding.avg_purchase_price = float(avg_price)
                holding.total_cost_basis = float(data['total_cost_basis'])
                holding.total_invested_krw = float(data['total_invested_krw'])
                holding.avg_exchange_rate = float(avg_exchange_rate)
                
                # 현재 시장가는 임시로 평균 매수가로 설정 (나중에 API로 업데이트)
                holding.current_market_price = float(avg_price)
                
                db.session.add(holding)
                
                result_item = {
                    "ticker": ticker,
                    "total_shares": float(data['total_shares']),
                    "avg_price": float(avg_price),
                    "total_cost_usd": float(data['total_cost_basis']),
                    "total_invested_krw": float(data['total_invested_krw']),
                    "avg_exchange_rate": float(avg_exchange_rate)
                }
                results.append(result_item)
                
                print(f"  ✅ {ticker}: {data['total_shares']}주, 평균가: ${avg_price:.4f}, 평균환율: {avg_exchange_rate:.2f}")
        
        # 변경사항 커밋
        db.session.commit()
        print("✨ Holdings 테이블 업데이트 완료!")
        
        return jsonify({
            "success": True,
            "message": f"Holdings 테이블이 성공적으로 업데이트되었습니다. 총 {len(results)}개 종목",
            "holdings": results
        })
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@stock_bp.route('/update_exchange_rate', methods=['GET'])
def update_exchange_rate():
    """ExchangeRate-API를 이용해서 USD/KRW 환율을 한 번 업데이트하고 응답"""
    try:
        # 환율 업데이트 실행
        result = exchange_rate_service.update_exchange_rate()
        
        if result['success']:
            # timestamp가 None이 아닌 경우에만 isoformat() 호출
            timestamp_str = None
            if result.get('timestamp') is not None:
                timestamp_str = result['timestamp'].isoformat()
            
            response_data = {
                "success": True,
                "message": result['message'],
                "old_rate": result['old_rate'],
                "new_rate": result['new_rate'],
                "change": result.get('change', 0),
                "change_pct": result.get('change_pct', 0),
                "timestamp": timestamp_str
            }
            
            # 환율 변화가 있었다면 200, 없었다면 200 반환 (항상 데이터 포함)
            status_code = 200
            return jsonify(response_data), status_code
        else:
            return jsonify({
                "success": False,
                "message": result['message'],
                "old_rate": result.get('old_rate'),
                "new_rate": result.get('new_rate')
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"환율 업데이트 중 오류가 발생했습니다: {str(e)}",
            "old_rate": None,
            "new_rate": None
        }), 500