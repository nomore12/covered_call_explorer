from flask import jsonify, request, render_template_string
from .__init__ import app, db # __init__.py에서 app 객체를 가져옵니다.
from .models import Holding, Transaction, Dividend
from .scheduler import update_stock_price
import yfinance as yf
from datetime import datetime

@app.route('/')
def hello_world():
    """기본 홈 라우트"""
    return 'Hello, Flask in Docker! (Financial Tracker App)'

@app.route('/echo', methods=['POST'])
def echo_message():
    """
    POST 요청으로 받은 'message'를 그대로 응답하는 테스트용 라우트
    """
    data = request.get_json()
    if data and 'message' in data:
        received_message = data['message']
        return jsonify({"response_message": received_message})
    return jsonify({"error": "No 'message' field found in request"}), 400

@app.route('/update_prices')
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

@app.route('/update_price/<ticker>')
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

@app.route('/test_yfinance/<ticker>')
def test_yfinance_direct(ticker):
    """yfinance 직접 테스트"""
    try:
        ticker = ticker.upper()
        
        # 간단한 yfinance 테스트
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="1d")
        
        if not hist.empty:
            latest_price = float(hist['Close'].iloc[-1])
            return jsonify({
                "success": True,
                "ticker": ticker,
                "price": latest_price,
                "data_points": len(hist),
                "last_date": str(hist.index[-1].date())
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

@app.route('/holdings', methods=['GET'])
def get_holdings():
    """현재 보유 종목 목록 조회 - 프론트엔드 API 호환 + 실시간 주가 업데이트"""
    try:
        holdings = Holding.query.filter(Holding.current_shares > 0).all()
        
        # yfinance를 사용해서 모든 종목의 현재가 업데이트
        for holding in holdings:
            try:
                ticker_obj = yf.Ticker(holding.ticker)
                hist = ticker_obj.history(period="1d")
                
                if not hist.empty:
                    latest_price = float(hist['Close'].iloc[-1])
                    # 데이터베이스 업데이트
                    holding.current_market_price = latest_price
                    holding.last_price_update_date = datetime.now().date()
                    print(f"Updated {holding.ticker}: ${latest_price}")
                else:
                    print(f"No data for {holding.ticker}")
            except Exception as e:
                print(f"Error updating {holding.ticker}: {str(e)}")
                # 에러가 발생해도 기존 가격 사용
        
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
        
        return jsonify(holdings_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/holdings/<ticker>', methods=['GET'])
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

@app.route('/portfolio', methods=['GET'])
def get_portfolio():
    print("get portfolio")
    """포트폴리오 전체 요약 정보 조회 - yfinance로 실시간 주가 업데이트"""
    try:
        holdings = Holding.query.filter(Holding.current_shares > 0).all()
        
        # yfinance를 사용해서 모든 종목의 현재가 업데이트
        updated_prices = {}
        for holding in holdings:
            try:
                ticker_obj = yf.Ticker(holding.ticker)
                hist = ticker_obj.history(period="1d")
                
                if not hist.empty:
                    latest_price = float(hist['Close'].iloc[-1])
                    # 데이터베이스 업데이트
                    holding.current_market_price = latest_price
                    holding.last_price_update_date = datetime.now().date()
                    updated_prices[holding.ticker] = latest_price
                    print(f"Updated {holding.ticker}: ${latest_price}")
                else:
                    print(f"No data for {holding.ticker}")
            except Exception as e:
                print(f"Error updating {holding.ticker}: {str(e)}")
                # 에러가 발생해도 기존 가격 사용
        
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
        
        # 총 배당금 계산
        total_dividends = Dividend.query.all()
        total_dividends_usd = sum(float(div.amount) for div in total_dividends)
        total_dividends_krw = total_dividends_usd * 1400  # 평균 환율 적용
        
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
            "price_updates": updated_prices,  # 업데이트된 주가 정보
            "last_updated": datetime.now().isoformat()  # 마지막 업데이트 시간
        }
        
        return jsonify(portfolio_summary)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transactions', methods=['GET', 'POST'])
def handle_transactions():
    """거래 내역 조회 및 생성"""
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
                    "dividend_reinvestment": bool(txn.dividend_used > 0),
                    "transaction_date": txn.date.isoformat(),
                    "created_at": txn.created_at.isoformat() if txn.created_at else None
                })
            
            return jsonify(transactions_data)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # 새 거래 생성
            new_transaction = Transaction(
                date=datetime.strptime(data.get('transaction_date', datetime.now().date().isoformat()), '%Y-%m-%d').date(),
                type=data['transaction_type'],
                ticker=data['ticker'].upper(),
                shares=data['shares'],
                price_per_share=data['price_per_share'],
                amount=data['total_amount_usd'],
                exchange_rate=data.get('exchange_rate'),
                amount_krw=data.get('krw_amount'),
                dividend_used=data['total_amount_usd'] if data.get('dividend_reinvestment') else 0,
                cash_invested_krw=data.get('krw_amount', 0) if not data.get('dividend_reinvestment') else 0
            )
            
            db.session.add(new_transaction)
            db.session.commit()
            
            return jsonify({
                "id": new_transaction.transaction_id,
                "message": "거래가 성공적으로 생성되었습니다."
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

@app.route('/dividends', methods=['GET', 'POST'])
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
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # 새 배당금 기록 생성
            new_dividend = Dividend(
                date=datetime.strptime(data.get('payment_date', datetime.now().date().isoformat()), '%Y-%m-%d').date(),
                ticker=data['ticker'].upper(),
                amount=data['amount_usd']
            )
            
            db.session.add(new_dividend)
            db.session.commit()
            
            return jsonify({
                "id": new_dividend.dividend_id,
                "message": "배당금이 성공적으로 기록되었습니다."
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

@app.route('/update-price', methods=['POST'])
def update_price():
    """주가 업데이트 API"""
    try:
        data = request.get_json()
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

@app.route('/dashboard')
def dashboard():
    """주가 업데이트 대시보드"""
    dashboard_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>커버드 콜 ETF 투자 수익률 계산기</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: inline-block;
            width: 150px;
            font-weight: bold;
            color: #555;
        }
        input, select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 200px;
            font-size: 14px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .profit {
            color: #4CAF50;
            font-weight: bold;
        }
        .loss {
            color: #f44336;
            font-weight: bold;
        }
        .summary {
            background-color: #e8f5e9;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 10px;
            background-color: white;
            border-radius: 5px;
        }
        .metric-label {
            font-weight: bold;
            color: #555;
        }
        .metric-value {
            font-size: 18px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>커버드 콜 ETF 투자 수익률 계산기</h1>
        
        <div class="section">
            <h2>보유 주식 정보 입력</h2>
            <div class="form-group">
                <label>종목:</label>
                <select id="ticker">
                    <option value="TSLY">TSLY</option>
                    <option value="NVDY">NVDY</option>
                    <option value="SMCY">SMCY</option>
                </select>
            </div>
            <div class="form-group">
                <label>1주당 가격 ($):</label>
                <input type="number" id="purchasePrice" step="0.0001" placeholder="예: 8.2692">
            </div>
            <div class="form-group">
                <label>수량:</label>
                <input type="number" id="quantity" placeholder="예: 92">
            </div>
            <div class="form-group">
                <label>총 구매 금액 ($):</label>
                <input type="number" id="totalPurchaseUSD" step="0.01" placeholder="예: 759.92" readonly style="background-color: #f0f0f0;">
            </div>
            <div class="form-group">
                <label>주문일:</label>
                <input type="date" id="purchaseDate">
            </div>
            <div class="form-group">
                <label>주문 중 환전한 달러 ($):</label>
                <input type="number" id="exchangedUSD" step="0.01" placeholder="예: 761.84">
            </div>
            <div class="form-group">
                <label>적용 환율 (₩/$):</label>
                <input type="number" id="exchangeRate" step="0.01" placeholder="예: 1430.06">
            </div>
            <div class="form-group">
                <label>사용한 원화 (₩):</label>
                <input type="number" id="usedKRW" step="1" placeholder="예: 1089480" readonly style="background-color: #f0f0f0;">
            </div>
            <button onclick="addPosition()">포지션 추가</button>
            <button onclick="clearPositionForm()" style="background-color: #ff9800;">초기화</button>
        </div>
        
        <div class="section">
            <h2>현재 주가 업데이트</h2>
            <div class="form-group">
                <label>종목:</label>
                <select id="priceUpdateTicker">
                    <option value="TSLY">TSLY</option>
                    <option value="NVDY">NVDY</option>
                    <option value="SMCY">SMCY</option>
                </select>
            </div>
            <div class="form-group">
                <label>현재 주가 ($):</label>
                <input type="number" id="updateCurrentPrice" step="0.01" placeholder="예: 10.50">
            </div>
            <button onclick="updateCurrentPrice()">주가 업데이트</button>
        </div>
        
        <div class="section">
            <h2>배당금 정보 입력</h2>
            <div class="form-group">
                <label>종목:</label>
                <select id="divTicker">
                    <option value="TSLY">TSLY</option>
                    <option value="NVDY">NVDY</option>
                    <option value="SMCY">SMCY</option>
                </select>
            </div>
            <div class="form-group">
                <label>주당 배당금 ($):</label>
                <input type="number" id="divPerShare" step="0.0001" placeholder="예: 0.4028">
            </div>
            <div class="form-group">
                <label>배당 기준일:</label>
                <input type="date" id="divDate">
            </div>
            <button onclick="addDividend()">배당금 추가</button>
        </div>
        
        <div class="section">
            <h2>보유 포지션</h2>
            <table id="positionsTable">
                <thead>
                    <tr>
                        <th>종목</th>
                        <th>구매가</th>
                        <th>수량</th>
                        <th>투자금($)</th>
                        <th>투자금(₩)</th>
                        <th>현재가</th>
                        <th>현재가치($)</th>
                        <th>손익($)</th>
                        <th>손익률(%)</th>
                    </tr>
                </thead>
                <tbody id="positionsBody">
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>배당금 내역</h2>
            <table id="dividendsTable">
                <thead>
                    <tr>
                        <th>종목</th>
                        <th>배당일</th>
                        <th>주당 배당금</th>
                        <th>수량</th>
                        <th>총 배당금($)</th>
                    </tr>
                </thead>
                <tbody id="dividendsBody">
                </tbody>
            </table>
        </div>
        
        <div class="summary">
            <h2>종합 수익률 분석</h2>
            <div class="metric">
                <span class="metric-label">총 투자금액:</span>
                <span class="metric-value" id="totalInvestment">₩0</span>
            </div>
            <div class="metric">
                <span class="metric-label">현재 포트폴리오 가치:</span>
                <span class="metric-value" id="currentValue">₩0</span>
            </div>
            <div class="metric">
                <span class="metric-label">총 배당금 수령액:</span>
                <span class="metric-value" id="totalDividends">₩0</span>
            </div>
            <div class="metric">
                <span class="metric-label">주가 손익:</span>
                <span class="metric-value" id="priceGainLoss">₩0</span>
            </div>
            <div class="metric">
                <span class="metric-label">총 수익 (배당 포함):</span>
                <span class="metric-value" id="totalReturn">₩0</span>
            </div>
            <div class="metric">
                <span class="metric-label">총 수익률:</span>
                <span class="metric-value" id="totalReturnRate">0%</span>
            </div>
            <div class="metric">
                <span class="metric-label">연환산 수익률 (CAGR):</span>
                <span class="metric-value" id="annualizedReturn">0%</span>
            </div>
        </div>
    </div>
    
    <script>
        let positions = [];
        let dividends = [];
        
        // 입력 필드 자동 계산
        document.addEventListener('DOMContentLoaded', function() {
            // 1주당 가격과 수량 입력 시 총 구매 금액 자동 계산
            document.getElementById('purchasePrice').addEventListener('input', calculateTotalPurchase);
            document.getElementById('quantity').addEventListener('input', calculateTotalPurchase);
            
            // 환전한 달러와 적용 환율 입력 시 사용한 원화 자동 계산
            document.getElementById('exchangedUSD').addEventListener('input', calculateUsedKRW);
            document.getElementById('exchangeRate').addEventListener('input', calculateUsedKRW);
            
            loadInitialData();
        });
        
        function calculateTotalPurchase() {
            const price = parseFloat(document.getElementById('purchasePrice').value) || 0;
            const qty = parseInt(document.getElementById('quantity').value) || 0;
            const total = price * qty;
            document.getElementById('totalPurchaseUSD').value = total.toFixed(2);
        }
        
        function calculateUsedKRW() {
            const exchangedUSD = parseFloat(document.getElementById('exchangedUSD').value) || 0;
            const rate = parseFloat(document.getElementById('exchangeRate').value) || 0;
            const usedKRW = Math.round(exchangedUSD * rate);
            document.getElementById('usedKRW').value = usedKRW;
        }
        
        // 초기 데이터 로드
        function loadInitialData() {
            // 사용자가 제공한 데이터를 자동으로 로드
            positions = [
                {
                    ticker: 'TSLY', 
                    purchasePrice: 8.2692, 
                    quantity: 92, 
                    totalPurchaseUSD: 759.92,
                    purchaseDate: '2025-04-16', 
                    exchangedUSD: 761.84,
                    exchangeRate: 1430.06, 
                    usedKRW: 1089480,
                    currentPrice: 8.10
                },
                {
                    ticker: 'SMCY', 
                    purchasePrice: 19.0425, 
                    quantity: 25, 
                    totalPurchaseUSD: 476.00,
                    purchaseDate: '2025-04-23', 
                    exchangedUSD: 423.16,
                    exchangeRate: 1432.89, 
                    usedKRW: 606341,
                    currentPrice: 20.69
                },
                {
                    ticker: 'NVDY', 
                    purchasePrice: 14.4225, 
                    quantity: 25, 
                    totalPurchaseUSD: 360.50,
                    purchaseDate: '2025-04-23', 
                    exchangedUSD: 360.61,
                    exchangeRate: 1432.89, 
                    usedKRW: 516714,
                    currentPrice: 15.99
                },
                {
                    ticker: 'NVDY', 
                    purchasePrice: 14.1743, 
                    quantity: 43, 
                    totalPurchaseUSD: 609.31,
                    purchaseDate: '2025-04-25', 
                    exchangedUSD: 610.78,
                    exchangeRate: 1450.77, 
                    usedKRW: 886099,
                    currentPrice: 15.99
                },
                {
                    ticker: 'TSLY', 
                    purchasePrice: 9.5848, 
                    quantity: 48, 
                    totalPurchaseUSD: 459.84,
                    purchaseDate: '2025-05-28', 
                    exchangedUSD: 262.55,
                    exchangeRate: 1373.19, 
                    usedKRW: 360530,
                    currentPrice: 8.10
                },
                {
                    ticker: 'NVDY', 
                    purchasePrice: 15.3330, 
                    quantity: 30, 
                    totalPurchaseUSD: 459.90,
                    purchaseDate: '2025-05-28', 
                    exchangedUSD: 460.35,
                    exchangeRate: 1373.54, 
                    usedKRW: 632307,
                    currentPrice: 15.99
                }
            ];
            updateDisplay();
        }
        
        function addPosition() {
            const ticker = document.getElementById('ticker').value;
            const purchasePrice = parseFloat(document.getElementById('purchasePrice').value);
            const quantity = parseInt(document.getElementById('quantity').value);
            const totalPurchaseUSD = parseFloat(document.getElementById('totalPurchaseUSD').value);
            const purchaseDate = document.getElementById('purchaseDate').value;
            const exchangedUSD = parseFloat(document.getElementById('exchangedUSD').value);
            const exchangeRate = parseFloat(document.getElementById('exchangeRate').value);
            const usedKRW = parseInt(document.getElementById('usedKRW').value);
            const currentPrice = parseFloat(document.getElementById('currentPrice').value);
            
            if (ticker && purchasePrice && quantity && purchaseDate && exchangedUSD && exchangeRate && currentPrice) {
                positions.push({
                    ticker, 
                    purchasePrice, 
                    quantity, 
                    totalPurchaseUSD,
                    purchaseDate, 
                    exchangedUSD,
                    exchangeRate, 
                    usedKRW,
                    currentPrice
                });
                updateDisplay();
                clearPositionForm();
            } else {
                alert('모든 필수 항목을 입력해주세요.');
            }
        }
        
        function addDividend() {
            const ticker = document.getElementById('divTicker').value;
            const divPerShare = parseFloat(document.getElementById('divPerShare').value);
            const divDate = document.getElementById('divDate').value;
            
            if (ticker && divPerShare && divDate) {
                dividends.push({ticker, divPerShare, divDate});
                updateDisplay();
                clearDividendForm();
            }
        }
        
        function updateDisplay() {
            updatePositionsTable();
            updateDividendsTable();
            updateSummary();
        }
        
        function updatePositionsTable() {
            const tbody = document.getElementById('positionsBody');
            tbody.innerHTML = '';
            
            positions.forEach(pos => {
                const currentValueUSD = pos.currentPrice * pos.quantity;
                const gainLossUSD = currentValueUSD - pos.totalPurchaseUSD;
                const gainLossRate = (gainLossUSD / pos.totalPurchaseUSD * 100).toFixed(2);
                
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${pos.ticker}</td>
                    <td>${pos.purchasePrice.toFixed(4)}</td>
                    <td>${pos.quantity}</td>
                    <td>${pos.totalPurchaseUSD.toFixed(2)}</td>
                    <td>₩${pos.usedKRW.toLocaleString()}</td>
                    <td>${pos.currentPrice.toFixed(2)}</td>
                    <td>${currentValueUSD.toFixed(2)}</td>
                    <td class="${gainLossUSD >= 0 ? 'profit' : 'loss'}">${gainLossUSD.toFixed(2)}</td>
                    <td class="${gainLossRate >= 0 ? 'profit' : 'loss'}">${gainLossRate}%</td>
                `;
            });
        }
        
        function updateDividendsTable() {
            const tbody = document.getElementById('dividendsBody');
            tbody.innerHTML = '';
            
            dividends.forEach(div => {
                const totalQuantity = positions
                    .filter(p => p.ticker === div.ticker && new Date(p.purchaseDate) <= new Date(div.divDate))
                    .reduce((sum, p) => sum + p.quantity, 0);
                const totalDiv = div.divPerShare * totalQuantity;
                
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${div.ticker}</td>
                    <td>${div.divDate}</td>
                    <td>${div.divPerShare.toFixed(4)}</td>
                    <td>${totalQuantity}</td>
                    <td>${totalDiv.toFixed(2)}</td>
                `;
            });
        }
        
        function updateSummary() {
            // 총 투자금액 계산 (실제 사용한 원화 기준)
            const totalInvestmentKRW = positions.reduce((sum, pos) => sum + pos.usedKRW, 0);
            
            // 현재 가치 계산 (최신 환율 1450원 가정)
            const currentExchangeRate = 1450;
            const currentValueUSD = positions.reduce((sum, pos) => 
                sum + (pos.currentPrice * pos.quantity), 0);
            const currentValueKRW = currentValueUSD * currentExchangeRate;
            
            // 총 배당금 계산
            let totalDividendsUSD = 0;
            dividends.forEach(div => {
                const totalQuantity = positions
                    .filter(p => p.ticker === div.ticker && new Date(p.purchaseDate) <= new Date(div.divDate))
                    .reduce((sum, p) => sum + p.quantity, 0);
                totalDividendsUSD += div.divPerShare * totalQuantity;
            });
            const totalDividendsKRW = totalDividendsUSD * currentExchangeRate;
            
            // 주가 손익
            const priceGainLossKRW = currentValueKRW - totalInvestmentKRW;
            
            // 총 수익 (배당 포함)
            const totalReturnKRW = priceGainLossKRW + totalDividendsKRW;
            
            // 수익률
            const totalReturnRate = (totalReturnKRW / totalInvestmentKRW * 100).toFixed(2);
            
            // 연환산 수익률 (최초 투자일 기준)
            if (positions.length > 0) {
                const firstPurchaseDate = new Date(Math.min(...positions.map(p => new Date(p.purchaseDate))));
                const daysDiff = (new Date() - firstPurchaseDate) / (1000 * 60 * 60 * 24);
                const annualizedReturn = (Math.pow((currentValueKRW + totalDividendsKRW) / totalInvestmentKRW, 365 / daysDiff) - 1) * 100;
                document.getElementById('annualizedReturn').textContent = annualizedReturn.toFixed(2) + '%';
                document.getElementById('annualizedReturn').className = annualizedReturn >= 0 ? 'metric-value profit' : 'metric-value loss';
            }
            
            // UI 업데이트
            document.getElementById('totalInvestment').textContent = '₩' + totalInvestmentKRW.toLocaleString();
            document.getElementById('currentValue').textContent = '₩' + currentValueKRW.toLocaleString();
            document.getElementById('totalDividends').textContent = '₩' + totalDividendsKRW.toLocaleString();
            document.getElementById('priceGainLoss').textContent = '₩' + priceGainLossKRW.toLocaleString();
            document.getElementById('priceGainLoss').className = priceGainLossKRW >= 0 ? 'metric-value profit' : 'metric-value loss';
            document.getElementById('totalReturn').textContent = '₩' + totalReturnKRW.toLocaleString();
            document.getElementById('totalReturn').className = totalReturnKRW >= 0 ? 'metric-value profit' : 'metric-value loss';
            document.getElementById('totalReturnRate').textContent = totalReturnRate + '%';
            document.getElementById('totalReturnRate').className = totalReturnRate >= 0 ? 'metric-value profit' : 'metric-value loss';
        }
        
        function clearPositionForm() {
            document.getElementById('purchasePrice').value = '';
            document.getElementById('quantity').value = '';
            document.getElementById('totalPurchaseUSD').value = '';
            document.getElementById('purchaseDate').value = '';
            document.getElementById('exchangedUSD').value = '';
            document.getElementById('exchangeRate').value = '';
            document.getElementById('usedKRW').value = '';
        }
        
        function clearDividendForm() {
            document.getElementById('divPerShare').value = '';
            document.getElementById('divDate').value = '';
        }
    </script>
</body>
</html>
    """
    return dashboard_html