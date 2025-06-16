from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import date, datetime
import threading
import asyncio

# python-telegram-bot 라이브러리 임포트
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

app = Flask(__name__)

# 데이터베이스 설정 (환경 변수 사용)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'mysql+pymysql://user:password@db:3306/mydb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 데이터베이스 모델 정의 (이전과 동일) ---

class Transaction(db.Model):
    __tablename__ = 'transactions'
    transaction_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    type = db.Column(db.String(50), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    shares = db.Column(db.DECIMAL(18, 8), nullable=False)
    price_per_share = db.Column(db.DECIMAL(18, 8), nullable=False)
    amount = db.Column(db.DECIMAL(18, 8), nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction {self.type} {self.ticker} {self.shares}@{self.price_per_share} on {self.date}>"

class Holding(db.Model):
    __tablename__ = 'holdings'
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


# --- API 라우트 정의 (이전과 동일) ---

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


# --- 텔레그램 봇 기능 시작 ---

# 텔레그램 봇 토큰을 환경 변수에서 불러옵니다.
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    print("FATAL ERROR: TELEGRAM_BOT_TOKEN environment variable not set.")
    print("Please add TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE to your .env file.")
    exit(1) # 토큰이 없으면 프로그램 종료

# 봇 시작 명령어 핸들러
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사용자가 /start 명령어를 보냈을 때 실행됩니다."""
    await update.message.reply_text(
        '안녕하세요! 재정 관리 봇입니다.\n\n'
        '주식 매수, 배당금 기록, 현재 주가 설정, 수익률 조회 등의 기능을 제공합니다.\n'
        '아직 개발 중이지만, 곧 유용한 기능을 사용할 수 있을 거예요!'
    )

# 에러 핸들러
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """봇 업데이트 중 발생한 에러를 로깅합니다."""
    print(f'Update {update} caused error {context.error}')

def run_telegram_bot_in_thread():
    """텔레그램 봇을 시작하는 함수 (asyncio 이벤트 루프 설정 포함)"""
    # 현재 스레드에 대한 새로운 asyncio 이벤트 루프를 설정
    # 이 루프는 텔레그램 봇의 비동기 작업을 처리합니다.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Application builder를 사용하여 봇 인스턴스를 생성합니다.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 명령어 핸들러 등록
    application.add_handler(CommandHandler("start", start))

    # 에러 핸들러 등록
    application.add_error_handler(error_handler)

    print("Telegram Bot is starting...")
    # 봇을 폴링 방식으로 시작합니다.
    # stop_signals=[] 옵션을 추가하여 시그널 핸들러를 비활성화합니다.
    # 이는 'set_wakeup_fd only works in main thread' 오류를 방지합니다.
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=[]) # <-- 이 부분을 수정했습니다.
    print("Telegram Bot stopped.")


# --- Flask 앱 실행 부분 ---
if __name__ == '__main__':
    # 데이터베이스 테이블 생성 (최초 실행 시 또는 테이블이 없을 경우)
    with app.app_context():
        db.create_all()
        print("Database tables checked/created.")

    # 텔레그램 봇을 별도의 스레드에서 시작합니다.
    bot_thread = threading.Thread(target=run_telegram_bot_in_thread)
    bot_thread.start()

    # Flask 웹 서버를 시작합니다 (메인 스레드).
    print("Starting Flask web server...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

