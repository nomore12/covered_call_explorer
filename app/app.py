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

# 허용된 사용자 ID 목록을 환경 변수에서 불러옵니다.
# 쉼표로 구분된 문자열을 리스트로 변환하고 각 ID를 정수형으로 변환합니다.
ALLOWED_USER_IDS_STR = os.environ.get('ALLOWED_TELEGRAM_USER_IDS', '')
ALLOWED_USER_IDS = [int(user_id.strip()) for user_id in ALLOWED_USER_IDS_STR.split(',') if user_id.strip()]

if not ALLOWED_USER_IDS:
    print("WARNING: No ALLOWED_TELEGRAM_USER_IDS found in .env. The bot will not restrict access.")
    # 실제 운영 시에는 이 경고를 FATAL_ERROR로 바꾸어 봇이 시작되지 않게 할 수도 있습니다.

# 사용자 인증 데코레이터 함수
def restricted(func):
    """
    허용된 사용자만 봇 명령어를 사용할 수 있도록 제한하는 데코레이터
    """
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USER_IDS:
            print(f"Unauthorized access attempt by user ID: {user_id}")
            await update.message.reply_text(
                '죄송합니다. 이 봇은 특정 사용자만 이용할 수 있습니다.'
            )
            return # 허용되지 않은 사용자의 요청은 더 이상 처리하지 않고 종료
        return await func(update, context, *args, **kwargs)
    return wrapper


# 봇 시작 명령어 핸들러 (제한 적용)
@restricted # <-- 데코레이터 적용
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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 명령어 핸들러 등록 (여기서 start 함수에 restricted 데코레이터가 적용됨)
    application.add_handler(CommandHandler("start", start))

    # 다른 모든 메시지에 대한 핸들러 (선택 사항: 제한된 메시지 처리)
    # restricted 데코레이터를 적용하면 이 핸들러도 제한됩니다.
    # 만약 제한되지 않은 메시지(예: 오류 발생 시 관리자에게 ID 요청)를 처리하고 싶다면
    # 별도의 핸들러를 restricted 데코레이터 없이 추가해야 합니다.
    async def handle_unrecognized_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            user_id = update.effective_user.id
            if user_id not in ALLOWED_USER_IDS:
                await update.message.reply_text(
                    f"죄송합니다. 이 봇은 특정 사용자만 이용할 수 있습니다. 당신의 사용자 ID는 {user_id} 입니다. 이 ID를 봇 관리자에게 알려주세요."
                )
            else:
                await update.message.reply_text("알 수 없는 명령입니다. /start 를 입력하여 사용법을 확인하세요.")

    # 모든 텍스트 메시지에 대한 핸들러. 명령어 핸들러 이후에 등록해야 합니다.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unrecognized_message))


    # 에러 핸들러 등록
    application.add_error_handler(error_handler)

    print("Telegram Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=[])
    print("Telegram Bot stopped.")


# --- Flask 앱 실행 부분 ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables checked/created.")

    bot_thread = threading.Thread(target=run_telegram_bot_in_thread)
    bot_thread.start()

    print("Starting Flask web server...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

