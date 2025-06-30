import os
import asyncio
import threading
from datetime import date, datetime

# Flask 앱 및 DB 객체 임포트
from .__init__ import app, db
# 데이터베이스 모델 임포트
from .models import Transaction, Holding, Dividend

# python-telegram-bot 라이브러리 임포트
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from decimal import Decimal

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
        '/buy - 매수 기록 (대화형)\n'
        '/dividend <티커> <배당금액> [날짜] - 배당금 수령\n'
        '/status [티커] - 현재 상태 조회\n'
        '/history [티커] [기간] - 거래 내역 조회\n'
        '/set_price <티커> <현재가> - 현재가 업데이트\n'
        '/db_status - 데이터베이스 상태 확인'
    )

# 대화 상태 상수
TICKER, SHARES, PRICE, TOTAL_AMOUNT, EXCHANGE_AMOUNT, EXCHANGE_KRW, CONFIRM = range(7)

# 사용자별 데이터 저장
user_data = {}

@restricted
async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/buy 명령어 시작 - 티커 입력 요청"""
    await update.message.reply_text('어떤 종목을 매수하셨나요? (예: NVDY)\n\n입력을 취소하려면 /cancel 을 입력하세요.')
    return TICKER

@restricted
async def buy_ticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """티커 입력 처리"""
    ticker = update.message.text.upper().strip()
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['ticker'] = ticker
    
    await update.message.reply_text(
        f'{ticker} 매수 정보를 순서대로 입력해주세요.\n\n'
        '1️⃣ 몇 주를 매수하셨나요?'
    )
    return SHARES

@restricted
async def buy_shares(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """주식 수 입력 처리"""
    try:
        shares = Decimal(update.message.text.strip())
        if shares <= 0:
            await update.message.reply_text('주식 수는 0보다 커야 합니다. 다시 입력해주세요.')
            return SHARES
    except:
        await update.message.reply_text('올바른 숫자를 입력해주세요. 다시 입력해주세요.')
        return SHARES
    
    user_id = update.effective_user.id
    user_data[user_id]['shares'] = shares
    
    await update.message.reply_text(
        '2️⃣ 1주당 가격을 입력하세요\n'
        '달러 가격만 입력 (예: 150.50):'
    )
    return PRICE

@restricted
async def buy_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """주당 가격 입력 처리"""
    try:
        price = Decimal(update.message.text.strip())
        if price <= 0:
            await update.message.reply_text('가격은 0보다 커야 합니다. 다시 입력해주세요.')
            return PRICE
    except:
        await update.message.reply_text('올바른 숫자를 입력해주세요. 다시 입력해주세요.')
        return PRICE
    
    user_id = update.effective_user.id
    user_data[user_id]['price'] = price
    total_amount = user_data[user_id]['shares'] * price
    user_data[user_id]['total_amount'] = total_amount
    
    await update.message.reply_text(
        f'3️⃣ 총 구매금액(달러)을 입력하세요:\n'
        f'계산된 금액: ${total_amount:.2f}\n'
        f'(다른 금액이면 직접 입력)'
    )
    return TOTAL_AMOUNT

@restricted
async def buy_total_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """총 구매금액 입력 처리"""
    try:
        total_amount = Decimal(update.message.text.strip())
        if total_amount <= 0:
            await update.message.reply_text('총 금액은 0보다 커야 합니다. 다시 입력해주세요.')
            return TOTAL_AMOUNT
    except:
        await update.message.reply_text('올바른 숫자를 입력해주세요. 다시 입력해주세요.')
        return TOTAL_AMOUNT
    
    user_id = update.effective_user.id
    user_data[user_id]['total_amount'] = total_amount
    
    await update.message.reply_text(
        '4️⃣ 주문 중 환전한 달러를 입력하세요:\n'
        '(배당금으로만 구매한 경우 0 입력)'
    )
    return EXCHANGE_AMOUNT

@restricted
async def buy_exchange_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """환전 달러 금액 입력 처리"""
    try:
        exchange_amount = Decimal(update.message.text.strip())
        if exchange_amount < 0:
            await update.message.reply_text('환전 금액은 0 이상이어야 합니다. 다시 입력해주세요.')
            return EXCHANGE_AMOUNT
    except:
        await update.message.reply_text('올바른 숫자를 입력해주세요. 다시 입력해주세요.')
        return EXCHANGE_AMOUNT
    
    user_id = update.effective_user.id
    user_data[user_id]['exchange_amount'] = exchange_amount
    
    if exchange_amount == 0:
        user_data[user_id]['exchange_krw'] = 0
        user_data[user_id]['dividend_used'] = user_data[user_id]['total_amount']
        await show_confirmation(update, user_id)
        return CONFIRM
    else:
        await update.message.reply_text(
            '5️⃣ 환전에 사용한 원화를 입력하세요:\n'
            '(수수료 포함, 환전하지 않았으면 0 입력)'
        )
        return EXCHANGE_KRW

@restricted
async def buy_exchange_krw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """환전 원화 금액 입력 처리"""
    try:
        exchange_krw = Decimal(update.message.text.strip())
        if exchange_krw < 0:
            await update.message.reply_text('원화 금액은 0 이상이어야 합니다. 다시 입력해주세요.')
            return EXCHANGE_KRW
    except:
        await update.message.reply_text('올바른 숫자를 입력해주세요. 다시 입력해주세요.')
        return EXCHANGE_KRW
    
    user_id = update.effective_user.id
    user_data[user_id]['exchange_krw'] = exchange_krw
    
    # 계산
    exchange_amount = user_data[user_id]['exchange_amount']
    total_amount = user_data[user_id]['total_amount']
    user_data[user_id]['dividend_used'] = total_amount - exchange_amount
    
    if exchange_krw > 0 and exchange_amount > 0:
        user_data[user_id]['exchange_rate'] = exchange_krw / exchange_amount
    else:
        user_data[user_id]['exchange_rate'] = None
    
    await show_confirmation(update, user_id)
    return CONFIRM

async def show_confirmation(update: Update, user_id: int):
    """최종 확인 메시지 생성"""
    data = user_data[user_id]
    
    ticker = data['ticker']
    shares = data['shares']
    price = data['price']
    total_amount = data['total_amount']
    exchange_amount = data.get('exchange_amount', 0)
    exchange_krw = data.get('exchange_krw', 0)
    dividend_used = data.get('dividend_used', 0)
    exchange_rate = data.get('exchange_rate')
    
    message = f"✅ 매수 내역 확인\n"
    message += f"━" * 18 + "\n"
    message += f"📈 {ticker} {shares}주 매수\n\n"
    message += f"- 주당가: ${price:.2f}\n"
    message += f"- 총 구매: ${total_amount:.2f}\n\n"
    
    if exchange_amount > 0:
        message += f"💱 환전 정보\n\n"
        message += f"- 환전액: ${exchange_amount:.2f}\n"
        message += f"- 사용 원화: ₩{exchange_krw:,.0f}\n"
        if exchange_rate:
            message += f"- 적용 환율: ₩{exchange_rate:.2f}\n\n"
        if dividend_used > 0:
            message += f"💰 배당금 사용: ${dividend_used:.2f}\n"
    else:
        message += f"💰 배당금으로만 구매하신 것으로 확인됩니다.\n"
        message += f"사용한 배당금: ${dividend_used:.2f}\n"
    
    message += f"━" * 18 + "\n\n"
    message += f"저장하시겠습니까? (예/아니오/다시)"
    
    await update.message.reply_text(message)

@restricted
async def buy_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """최종 확인 및 데이터베이스 저장"""
    response = update.message.text.strip().lower()
    user_id = update.effective_user.id
    
    if response in ['다시', '재입력', 'again', 'retry']:
        await update.message.reply_text('처음부터 다시 입력해주세요. /buy 를 입력하세요.')
        if user_id in user_data:
            del user_data[user_id]
        return ConversationHandler.END
    
    if response not in ['예', 'yes', 'y', '네', '저장']:
        await update.message.reply_text('입력을 취소했습니다.')
        if user_id in user_data:
            del user_data[user_id]
        return ConversationHandler.END
    
    # 데이터베이스에 저장
    data = user_data[user_id]
    
    with app.app_context():
        try:
            # Transaction 기록
            new_transaction = Transaction(
                date=date.today(),
                type='BUY',
                ticker=data['ticker'],
                shares=data['shares'],
                price_per_share=data['price'],
                amount=data['total_amount'],
                exchange_rate=data.get('exchange_rate'),
                amount_krw=data.get('exchange_krw', 0),
                dividend_used=data.get('dividend_used', 0),
                cash_invested_krw=data.get('exchange_krw', 0)
            )
            db.session.add(new_transaction)
            
            # Holding 업데이트
            holding = Holding.query.filter_by(ticker=data['ticker']).first()
            if holding:
                # 기존 보유량 업데이트
                old_total_cost = holding.current_shares * holding.total_cost_basis
                new_total_cost = old_total_cost + data['total_amount']
                new_total_shares = holding.current_shares + data['shares']
                
                holding.total_cost_basis = new_total_cost / new_total_shares if new_total_shares > 0 else 0
                holding.current_shares = new_total_shares
                holding.avg_purchase_price = new_total_cost / new_total_shares if new_total_shares > 0 else 0
                
                # 평균 환율 계산
                old_krw = holding.total_invested_krw or 0
                new_krw = old_krw + data.get('exchange_krw', 0)
                holding.total_invested_krw = new_krw
                
                if new_krw > 0 and new_total_cost > 0:
                    holding.avg_exchange_rate = new_krw / (new_total_cost - holding.dividends_reinvested)
                
                # 배당금 재투자 추적
                if data.get('dividend_used', 0) > 0:
                    holding.dividends_reinvested = (holding.dividends_reinvested or 0) + data['dividend_used']
            else:
                # 새 보유 종목
                holding = Holding(
                    ticker=data['ticker'],
                    current_shares=data['shares'],
                    total_cost_basis=data['price'],
                    avg_purchase_price=data['price'],
                    avg_exchange_rate=data.get('exchange_rate'),
                    total_invested_krw=data.get('exchange_krw', 0),
                    total_dividends_received=0,
                    dividends_reinvested=data.get('dividend_used', 0),
                    dividends_withdrawn=0,
                    current_market_price=0
                )
                db.session.add(holding)
            
            db.session.commit()
            
            await update.message.reply_text(
                f"✅ {data['ticker']} {data['shares']}주 매수 기록 완료!\n"
                f"현재 {data['ticker']} 총 보유: {holding.current_shares}주"
            )
            
        except Exception as e:
            db.session.rollback()
            await update.message.reply_text(f"❌ 오류가 발생했습니다: {e}")
            print(f"Error in buy transaction: {e}")
    
    # 데이터 정리
    if user_id in user_data:
        del user_data[user_id]
    
    return ConversationHandler.END

@restricted
async def buy_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """매수 입력 취소"""
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text('매수 입력을 취소했습니다.')
    return ConversationHandler.END

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

@restricted
async def dividend_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/dividend 명령어 처리"""
    args = context.args
    if len(args) < 2 or len(args) > 3:
        await update.message.reply_text(
            '사용법: /dividend <티커> <배당금액> [날짜]\n'
            '예시: /dividend NVDY 50.25\n'
            '예시: /dividend NVDY 50.25 2024-12-15'
        )
        return
    
    ticker = args[0].upper()
    try:
        amount = Decimal(args[1])
    except:
        await update.message.reply_text('배당금 금액은 올바른 숫자여야 합니다.')
        return
    
    dividend_date = date.today()
    if len(args) == 3:
        try:
            dividend_date = datetime.strptime(args[2], '%Y-%m-%d').date()
        except ValueError:
            await update.message.reply_text('날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해주세요.')
            return
    
    with app.app_context():
        try:
            # Dividend 테이블에 배당금 기록
            new_dividend = Dividend(
                date=dividend_date,
                ticker=ticker,
                amount=amount
            )
            db.session.add(new_dividend)
            
            # Holding 업데이트
            holding = Holding.query.filter_by(ticker=ticker).first()
            if holding:
                holding.total_dividends_received = (holding.total_dividends_received or 0) + amount
            
            db.session.commit()
            await update.message.reply_text(
                f'✅ {ticker} 배당금 ${amount} 수령 기록 완료!'
            )
            
        except Exception as e:
            db.session.rollback()
            await update.message.reply_text(f'❌ 배당금 기록 중 오류: {e}')
            print(f"Error recording dividend: {e}")

@restricted
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/status 명령어 처리"""
    args = context.args
    
    with app.app_context():
        try:
            if not args:  # 전체 포트폴리오
                holdings = Holding.query.all()
                if not holdings:
                    await update.message.reply_text('보유 중인 주식이 없습니다.')
                    return
                
                message = '📈 포트폴리오 현황\n' + '━' * 20 + '\n'
                total_cost = Decimal('0')
                total_value = Decimal('0')
                
                for holding in holdings:
                    cost_basis = holding.current_shares * holding.total_cost_basis
                    current_value = holding.current_shares * holding.current_market_price
                    profit_loss = current_value - cost_basis
                    profit_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
                    
                    total_cost += cost_basis
                    total_value += current_value
                    
                    message += f'{holding.ticker}: {holding.current_shares}주\n'
                    message += f'  평균단가: ${holding.total_cost_basis:.2f}\n'
                    message += f'  현재가: ${holding.current_market_price:.2f}\n'
                    message += f'  수익률: {profit_pct:+.2f}%\n'
                    message += f'  배당금: ${holding.total_dividends_received or 0:.2f}\n\n'
                
                total_profit = total_value - total_cost
                total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
                
                message += f'━' * 20 + '\n'
                message += f'총 투자: ${total_cost:.2f}\n'
                message += f'현재 가치: ${total_value:.2f}\n'
                message += f'총 수익률: {total_profit_pct:+.2f}%'
                
                await update.message.reply_text(message)
                
            else:  # 특정 종목
                ticker = args[0].upper()
                holding = Holding.query.filter_by(ticker=ticker).first()
                
                if not holding:
                    await update.message.reply_text(f'{ticker} 주식을 보유하고 있지 않습니다.')
                    return
                
                cost_basis = holding.current_shares * holding.total_cost_basis
                current_value = holding.current_shares * holding.current_market_price
                profit_loss = current_value - cost_basis
                profit_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
                
                message = f'📈 {ticker} 상세 정보\n' + '━' * 20 + '\n'
                message += f'보유 주수: {holding.current_shares}주\n'
                message += f'평균 매수가: ${holding.total_cost_basis:.2f}\n'
                message += f'현재 주가: ${holding.current_market_price:.2f}\n'
                message += f'투자 금액: ${cost_basis:.2f}\n'
                message += f'현재 가치: ${current_value:.2f}\n'
                message += f'수익금: ${profit_loss:+.2f}\n'
                message += f'수익률: {profit_pct:+.2f}%\n\n'
                message += f'배당금 수령: ${holding.total_dividends_received or 0:.2f}\n'
                message += f'배당금 재투자: ${holding.dividends_reinvested or 0:.2f}'
                
                await update.message.reply_text(message)
                
        except Exception as e:
            await update.message.reply_text(f'❌ 상태 조회 중 오류: {e}')
            print(f"Error in status command: {e}")

@restricted
async def set_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/set_price 명령어 처리"""
    args = context.args
    if len(args) != 2:
        await update.message.reply_text(
            '사용법: /set_price <티커> <현재가>\n'
            '예시: /set_price NVDY 155.25'
        )
        return
    
    ticker = args[0].upper()
    try:
        price = Decimal(args[1])
    except:
        await update.message.reply_text('가격은 올바른 숫자여야 합니다.')
        return
    
    with app.app_context():
        try:
            holding = Holding.query.filter_by(ticker=ticker).first()
            if not holding:
                await update.message.reply_text(f'{ticker} 주식을 보유하고 있지 않습니다.')
                return
            
            old_price = holding.current_market_price
            holding.current_market_price = price
            holding.last_price_update_date = date.today()
            
            db.session.commit()
            
            await update.message.reply_text(
                f'✅ {ticker} 현재가 업데이트 완료!\n'
                f'${old_price:.2f} → ${price:.2f}'
            )
            
        except Exception as e:
            db.session.rollback()
            await update.message.reply_text(f'❌ 가격 업데이트 중 오류: {e}')
            print(f"Error updating price: {e}")


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
    
    # 대화형 /buy 명령어 핸들러
    buy_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('buy', buy_start)],
        states={
            TICKER: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_ticker)],
            SHARES: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_shares)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_price)],
            TOTAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_total_amount)],
            EXCHANGE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_exchange_amount)],
            EXCHANGE_KRW: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_exchange_krw)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_confirm)],
        },
        fallbacks=[CommandHandler('cancel', buy_cancel)],
    )
    application.add_handler(buy_conv_handler)
    
    # 기타 명령어 핸들러
    application.add_handler(CommandHandler("dividend", dividend_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("set_price", set_price_command))
    application.add_handler(CommandHandler("db_status", get_db_status))

    # 모든 텍스트 메시지에 대한 핸들러. 명령어 핸들러 이후에 등록해야 합니다.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unrecognized_message))

    # 에러 핸들러 등록
    application.add_error_handler(error_handler)

    print("Telegram Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=[])
    print("Telegram Bot stopped.")

