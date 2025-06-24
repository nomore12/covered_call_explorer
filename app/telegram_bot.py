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
        '/db_status - 데이터베이스 상태 (테이블 목록 및 데이터 유무) 확인\n' # <-- 새 명령어 추가
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
            await update.message.reply_text('날짜 형식이 잘못되었습니다.YYYY-MM-DD 형식으로 입력해주세요.')
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
                old_total_cost = holding.current_shares * holding.total_cost_basis
                new_total_cost = old_total_cost + amount
                new_total_shares = holding.current_shares + shares

                if new_total_shares > 0:
                    holding.total_cost_basis = new_total_cost / new_total_shares
                else:
                    holding.total_cost_basis = 0 # 모든 주식을 매도하여 0이 되는 경우
                
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
                f'✅ {ticker} {shares}주를 ${price_per_share:.2f}에 매수 기록했습니다. (총 ${amount:.2f})\n'
                f'현재 {ticker} 총 보유 주식: {holding.current_shares:.2f}주'
            )
        except Exception as e:
            db.session.rollback() # 오류 발생 시 롤백
            await update.message.reply_text(f'❌ 매수 기록 중 오류가 발생했습니다: {e}')
            print(f"Error adding buy transaction: {e}")

@restricted # <-- 제한 데코레이터 적용
async def get_db_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    데이터베이스의 테이블 목록과 각 테이블의 데이터 유무(레코드 수)를 확인합니다.
    """
    message_parts = ["📊 데이터베이스 상태:"]
    
    with app.app_context():
        try:
            # 현재 데이터베이스 이름 가져오기
            db_name_result = db.session.execute(db.text("SELECT DATABASE();")).scalar()
            if db_name_result:
                message_parts.append(f"DB 이름: `{db_name_result}`")
            else:
                message_parts.append("DB 이름을 가져올 수 없습니다.")
                
            message_parts.append("\n**테이블 목록:**")

            # information_schema에서 테이블 목록 조회
            # SQLAlchemy의 session.execute(text())를 사용하여 Raw SQL 쿼리 실행
            # db.metadata.tables.keys()를 사용하여 SQLAlchemy가 아는 테이블만 가져올 수도 있음
            tables_result = db.session.execute(
                db.text("SELECT table_name FROM information_schema.tables WHERE table_schema = :db_name")
            ).scalars().all() # scalars()는 단일 컬럼 결과만 가져올 때 유용

            if not tables_result:
                message_parts.append("테이블이 존재하지 않습니다.")
            else:
                for table_name in tables_result:
                    try:
                        # 각 테이블의 레코드 수 조회
                        count = db.session.execute(
                            db.text(f"SELECT COUNT(*) FROM `{table_name}`") # 백틱(``)으로 테이블명 감싸기
                        ).scalar()
                        message_parts.append(f"- `{table_name}`: {count}개 레코드")
                    except Exception as e_count:
                        message_parts.append(f"- `{table_name}`: (레코드 수 확인 불가 - {e_count})")
            
            await update.message.reply_text("\n".join(message_parts), parse_mode='Markdown')

        except Exception as e:
            await update.message.reply_text(f'❌ 데이터베이스 상태 확인 중 오류가 발생했습니다: {e}')
            print(f"Error checking DB status: {e}")


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
    application.add_handler(CommandHandler("db_status", get_db_status)) # <-- 새 핸들러 등록

    # 모든 텍스트 메시지에 대한 핸들러. 명령어 핸들러 이후에 등록해야 합니다.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unrecognized_message))

    # 에러 핸들러 등록
    application.add_error_handler(error_handler)

    print("Telegram Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=[])
    print("Telegram Bot stopped.")

