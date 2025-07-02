from flask import jsonify, request, render_template_string
from .__init__ import app, db # __init__.py에서 app 객체를 가져옵니다.
from .models import Holding
from .scheduler import update_stock_price
import yfinance as yf

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

@app.route('/holdings')
def get_holdings():
    """현재 보유 종목 목록 조회"""
    try:
        holdings = Holding.query.filter(Holding.current_shares > 0).all()
        
        holdings_data = []
        for holding in holdings:
            holdings_data.append({
                "ticker": holding.ticker,
                "shares": float(holding.current_shares),
                "avg_price": float(holding.total_cost_basis),
                "current_price": float(holding.current_market_price),
                "last_update": str(holding.last_price_update_date) if holding.last_price_update_date else None
            })
        
        return jsonify({
            "success": True,
            "holdings": holdings_data,
            "total_holdings": len(holdings_data)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/dashboard')
def dashboard():
    """주가 업데이트 대시보드"""
    dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>주가 업데이트 대시보드</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .button { 
            background-color: #4CAF50; 
            color: white; 
            padding: 10px 20px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            margin: 5px;
            text-decoration: none;
            display: inline-block;
        }
        .button:hover { background-color: #45a049; }
        .result { 
            margin: 10px 0; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 4px;
            background-color: #f9f9f9;
        }
        .holdings { border-collapse: collapse; width: 100%; }
        .holdings th, .holdings td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .holdings th { background-color: #f2f2f2; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <h1>📈 주가 업데이트 대시보드</h1>
    
    <div>
        <h2>빠른 업데이트</h2>
        <button class="button" onclick="updateAllPrices()">모든 종목 업데이트</button>
        <button class="button" onclick="loadHoldings()">보유 종목 조회</button>
        <button class="button" onclick="testYfinance()">yfinance 테스트 (NVDY)</button>
    </div>
    
    <div>
        <h2>개별 종목 테스트</h2>
        <input type="text" id="tickerInput" placeholder="티커 입력 (예: NVDY)" value="NVDY">
        <button class="button" onclick="updateSinglePrice()">개별 업데이트</button>
        <button class="button" onclick="testSingleYfinance()">yfinance 테스트</button>
    </div>
    
    <div id="result" class="result" style="display:none;"></div>
    
    <div>
        <h2>보유 종목</h2>
        <div id="holdings"></div>
    </div>

    <script>
        function showResult(message, isError = false) {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = message;
            resultDiv.className = isError ? 'result error' : 'result success';
            resultDiv.style.display = 'block';
        }

        async function updateAllPrices() {
            showResult('모든 종목 업데이트 중...');
            try {
                const response = await fetch('/update_prices');
                const data = await response.json();
                showResult(`업데이트 완료: ${data.message}`, !data.success);
            } catch (error) {
                showResult(`오류: ${error.message}`, true);
            }
        }

        async function updateSinglePrice() {
            const ticker = document.getElementById('tickerInput').value.trim();
            if (!ticker) {
                showResult('티커를 입력하세요', true);
                return;
            }
            
            showResult(`${ticker} 업데이트 중...`);
            try {
                const response = await fetch(`/update_price/${ticker}`);
                const data = await response.json();
                showResult(`${ticker} 업데이트 완료: ${data.message}`, !data.success);
            } catch (error) {
                showResult(`오류: ${error.message}`, true);
            }
        }

        async function testYfinance() {
            showResult('NVDY yfinance 테스트 중...');
            try {
                const response = await fetch('/test_yfinance/NVDY');
                const data = await response.json();
                if (data.success) {
                    showResult(`yfinance 성공: NVDY = $${data.price} (${data.last_date})`);
                } else {
                    showResult(`yfinance 실패: ${data.error}`, true);
                }
            } catch (error) {
                showResult(`오류: ${error.message}`, true);
            }
        }

        async function testSingleYfinance() {
            const ticker = document.getElementById('tickerInput').value.trim();
            if (!ticker) {
                showResult('티커를 입력하세요', true);
                return;
            }
            
            showResult(`${ticker} yfinance 테스트 중...`);
            try {
                const response = await fetch(`/test_yfinance/${ticker}`);
                const data = await response.json();
                if (data.success) {
                    showResult(`yfinance 성공: ${ticker} = $${data.price} (${data.last_date})`);
                } else {
                    showResult(`yfinance 실패: ${data.error}`, true);
                }
            } catch (error) {
                showResult(`오류: ${error.message}`, true);
            }
        }

        async function loadHoldings() {
            showResult('보유 종목 조회 중...');
            try {
                const response = await fetch('/holdings');
                const data = await response.json();
                
                if (data.success) {
                    let html = `<table class="holdings">
                        <tr>
                            <th>티커</th>
                            <th>보유 주수</th>
                            <th>평균 단가</th>
                            <th>현재가</th>
                            <th>마지막 업데이트</th>
                            <th>액션</th>
                        </tr>`;
                    
                    data.holdings.forEach(holding => {
                        html += `<tr>
                            <td>${holding.ticker}</td>
                            <td>${holding.shares}</td>
                            <td>$${holding.avg_price.toFixed(3)}</td>
                            <td>$${holding.current_price.toFixed(3)}</td>
                            <td>${holding.last_update || 'N/A'}</td>
                            <td>
                                <button class="button" onclick="updateSinglePriceByTicker('${holding.ticker}')">업데이트</button>
                                <button class="button" onclick="testYfinanceByTicker('${holding.ticker}')">테스트</button>
                            </td>
                        </tr>`;
                    });
                    
                    html += '</table>';
                    document.getElementById('holdings').innerHTML = html;
                    showResult(`${data.total_holdings}개 종목 조회 완료`);
                } else {
                    showResult(`조회 실패: ${data.error}`, true);
                }
            } catch (error) {
                showResult(`오류: ${error.message}`, true);
            }
        }

        async function updateSinglePriceByTicker(ticker) {
            showResult(`${ticker} 업데이트 중...`);
            try {
                const response = await fetch(`/update_price/${ticker}`);
                const data = await response.json();
                showResult(`${ticker} 업데이트 완료: ${data.message}`, !data.success);
                if (data.success) {
                    loadHoldings(); // 새로고침
                }
            } catch (error) {
                showResult(`오류: ${error.message}`, true);
            }
        }

        async function testYfinanceByTicker(ticker) {
            showResult(`${ticker} yfinance 테스트 중...`);
            try {
                const response = await fetch(`/test_yfinance/${ticker}`);
                const data = await response.json();
                if (data.success) {
                    showResult(`yfinance 성공: ${ticker} = $${data.price} (${data.last_date})`);
                } else {
                    showResult(`yfinance 실패: ${data.error}`, true);
                }
            } catch (error) {
                showResult(`오류: ${error.message}`, true);
            }
        }

        // 페이지 로드 시 보유 종목 자동 조회
        window.onload = function() {
            loadHoldings();
        };
    </script>
</body>
</html>
    """
    return dashboard_html