import os
import asyncio
import threading
from datetime import date, datetime

# Flask 앱 및 DB 객체 임포트
from .__init__ import app, db
# 데이터베이스 모델 임포트
from .models import Transaction, Holding

# python-telegram-bot 라이브러리 임포트
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 텔레그램 봇 토큰을 환경 변수에서 불러옵니다.
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    print("FATAL ERROR: TELEGRAM_BOT_TOKEN environment variable not set.")
    print("Please add TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE to your .env file.")
    exit(1) # 토큰이 없으면 프로그램 종료

# 허용된 사용자 ID 목록을 환경 변수에서 불러옵니다.
ALLOWED_USER_IDS_STR = os.environ.get('ALLOWED_TELEGRAM_USER_IDS', '')
ALLOWED_USER_IDS = [int(user_id.strip()) for user_id in ALLOWED_USER_IDS_STR.split(',') if user_id.strip()]

if not ALLOWED_USER_IDS:
    print("WARNING: No ALLOWED_TELEGRAM_USER_IDS found in .env. The bot will not restrict access.")

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
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사용자가 /start 명령어를 보냈을 때 실행됩니다."""
    await update.message.reply_text(
        '안녕하세요! 재정 관리 봇입니다.\n\n'
        '현재 지원되는 명령어:\n'
        '/start - 봇 소개 및 명령어 안내\n'
        '/add_buy <티커> <주식수> <주당가격> [YYYY-MM-DD] - 주식 매수 내역 추가\n'
        '예시: /add_buy NVDY 10 150.50\n'
        '예시: /add_buy TSLA 5 200.00 2024-06-01\n'
        '(나머지 기능들은 곧 추가될 예정입니다!)'
    )

@restricted
async def add_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /add_buy 명령어를 처리하여 주식 매수 내역을 추가합니다.
    사용법: /add_buy <티커> <주식수> <주당가격> [YYYY-MM-DD]
    """
    args = context.args # 명령어 뒤의 인자들을 리스트로 가져옴
    if len(args) < 3 or len(args) > 4:
        await update.message.reply_text(
            '잘못된 형식입니다. 사용법:\n'
            '/add_buy <티커> <주식수> <주당가격> [YYYY-MM-DD]\n'
            '예시: /add_buy NVDY 10 150.50\n'
            '예시: /add_buy TSLA 5 200.00 2024-06-01'
        )
        return

    ticker = args[0].upper() # 티커는 대문자로 변환
    try:
        shares = float(args[1])
        price_per_share = float(args[2])
    except ValueError:
        await update.message.reply_text('주식수와 주당가격은 유효한 숫자여야 합니다.')
        return

    transaction_date = date.today() # 기본값은 오늘 날짜
    if len(args) == 4:
        try:
            transaction_date = datetime.strptime(args[3], '%Y-%m-%d').date()
        except ValueError:
            await update.message.reply_text('날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해주세요.')
            return

    amount = shares * price_per_share

    # 데이터베이스 작업은 Flask 앱 컨텍스트 내에서 실행되어야 합니다.
    # 봇 핸들러는 별도 스레드에서 실행되므로, app_context()를 사용합니다.
    with app.app_context():
        try:
            # 1. Transaction 테이블에 기록
            new_transaction = Transaction(
                date=transaction_date,
                type='BUY',
                ticker=ticker,
                shares=shares,
                price_per_share=price_per_share,
                amount=amount
            )
            db.session.add(new_transaction)

            # 2. Holding 테이블 업데이트 또는 생성
            holding = Holding.query.filter_by(ticker=ticker).first()
            if holding:
                # 기존 보유량에 추가
                # 총 매수 원가를 업데이트할 때 평균 단가를 고려하여 계산합니다.
                # (기존 총 원가 + 새로운 매수 원가)를 새로운 총 주식수로 나눕니다.
                # 단순 누적 합계가 아니라 평균 매수 단가에 기반한 총 원가를 유지
                new_total_value = (holding.current_shares * holding.total_cost_basis) + amount
                new_total_shares = holding.current_shares + shares

                # 0으로 나누는 오류 방지 (shares가 0일 경우)
                if new_total_shares > 0:
                    holding.total_cost_basis = new_total_value / new_total_shares
                else: # 모든 주식을 매도하여 0이 되는 경우 (shares가 음수일 때 발생 가능)
                    holding.total_cost_basis = 0
                
                holding.current_shares = new_total_shares
            else:
                # 새로운 보유 종목 생성
                holding = Holding(
                    ticker=ticker,
                    current_shares=shares,
                    total_cost_basis=price_per_share, # 첫 매수는 주당가격이 원가
                    accumulated_dividends=0,
                    current_market_price=0,
                    last_price_update_date=None
                )
                db.session.add(holding)

            db.session.commit()
            await update.message.reply_text(
                f'{ticker} {shares}주를 ${price_per_share}에 매수 기록했습니다. (총 ${amount:.2f})\n'
                f'현재 {ticker} 총 보유 주식: {holding.current_shares:.2f}주'
            )
        except Exception as e:
            db.session.rollback() # 오류 발생 시 롤백
            await update.message.reply_text(f'매수 기록 중 오류가 발생했습니다: {e}')
            print(f"Error adding buy transaction: {e}")

# 에러 핸들러
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """봇 업데이트 중 발생한 에러를 로깅합니다."""
    print(f'Update {update} caused error {context.error}')

# 다른 모든 메시지에 대한 핸들러 (선택 사항: 제한된 메시지 처리)
async def handle_unrecognized_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USER_IDS:
            await update.message.reply_text(
                f"죄송합니다. 이 봇은 특정 사용자만 이용할 수 있습니다. 당신의 사용자 ID는 {user_id} 입니다. 이 ID를 봇 관리자에게 알려주세요."
            )
        else:
            await update.message.reply_text("알 수 없는 명령입니다. /start 를 입력하여 사용법을 확인하세요.")

def run_telegram_bot_in_thread():
    """텔레그램 봇을 시작하는 함수 (asyncio 이벤트 루프 설정 포함)"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 명령어 핸들러 등록
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_buy", add_buy))

    # 모든 텍스트 메시지에 대한 핸들러. 명령어 핸들러 이후에 등록해야 합니다.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unrecognized_message))

    # 에러 핸들러 등록
    application.add_error_handler(error_handler)

    print("Telegram Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=[])
    print("Telegram Bot stopped.")