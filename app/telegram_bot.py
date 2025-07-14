import os
import asyncio
import threading
import logging
from datetime import date, datetime, timedelta

# 데이터베이스 모델 임포트
from .models import Transaction, Holding, Dividend, db
# Flask 앱 임포트
from flask import current_app
# 스케줄러 임포트
from .scheduler import update_stock_price, get_scheduler_status, calculate_portfolio_pnl, send_daily_portfolio_report

# python-telegram-bot 라이브러리 임포트
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from decimal import Decimal

# HTTP 로깅 레벨 조정 (과도한 로그 방지)
logging.getLogger("httpx").setLevel(logging.WARNING)  # INFO -> WARNING로 변경
logging.getLogger("telegram.ext").setLevel(logging.WARNING)  # 텔레그램 관련 로그도 WARNING 이상만

# 텔레그램 봇 토큰을 환경 변수에서 불러옵니다.
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    print("FATAL ERROR: TELEGRAM_BOT_TOKEN environment variable not set.")
    print("Please add TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE to your .env file.")
    exit(1) # 토큰이 없으면 프로그램 종료

# 타입 안전성을 위해 토큰 존재 확인 후 변수 할당
BOT_TOKEN: str = TELEGRAM_BOT_TOKEN

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
async def portfolio_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/portfolio_report 명령어 처리 - 포트폴리오 리포트 조회"""
    await update.message.reply_text('📊 포트폴리오 리포트를 생성하고 있습니다...')
    
    try:
        # Flask 앱 컨텍스트에서 실행
        from .__init__ import get_app
        app = get_app()
        with app.app_context():
            pnl_data = calculate_portfolio_pnl()
            
            if not pnl_data['success']:
                await update.message.reply_text(f'❌ 오류: {pnl_data["message"]}')
                return
            
            # 리포트 메시지 생성 (send_daily_portfolio_report와 유사하지만 간소화)
            return_rate = pnl_data['total_return_rate']
            
            # 경고 이모지 설정
            if return_rate <= -5.0:
                warning_emoji = "🚨"
            elif return_rate <= -3.0:
                warning_emoji = "⚠️"
            elif return_rate >= 5.0:
                warning_emoji = "🎉"
            elif return_rate >= 3.0:
                warning_emoji = "📈"
            else:
                warning_emoji = "📊"
            
            # 경고 레벨 설정 (스케줄러와 동일)
            warning_level = ""
            
            if return_rate <= -5.0:
                warning_level = "🚨 심각한 손실 경고!"
            elif return_rate <= -3.0:
                warning_level = "⚠️ 손실 주의 경고!"
            
            # 현재 시간 표시 (스케줄러와 동일)
            from datetime import datetime
            current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            message_parts = [f"{warning_emoji} <b>포트폴리오 현황 리포트</b> ({current_time_str})"]
            message_parts.append("")
            
            # 경고 메시지 추가 (스케줄러와 동일)
            if warning_level:
                message_parts.append(f"{warning_level}")
                message_parts.append("")
            
            # 전체 포트폴리오 요약
            message_parts.append(f"💰 <b>총 포트폴리오 가치</b>")
            message_parts.append(f"  • 투자금: ${pnl_data['total_invested_usd']:,.2f}")
            message_parts.append(f"  • 현재가치: ${pnl_data['total_current_value_usd']:,.2f}")
            message_parts.append(f"  • 받은 배당금: ${pnl_data['total_dividends_usd']:,.2f}")
            message_parts.append("")
            
            # 총 손익 및 수익률
            pnl_symbol = "+" if pnl_data['total_pnl_usd'] >= 0 else ""
            rate_symbol = "+" if return_rate >= 0 else ""
            
            message_parts.append(f"📊 <b>총 손익 (미실현 + 배당)</b>")
            message_parts.append(f"  • 미실현 손익: {pnl_symbol}${pnl_data['total_unrealized_pnl_usd']:,.2f}")
            message_parts.append(f"  • 총 손익: {pnl_symbol}${pnl_data['total_pnl_usd']:,.2f}")
            message_parts.append(f"  • 총 수익률: {rate_symbol}{return_rate:.2f}%")
            message_parts.append("")
            
            # 종목별 상세 (모든 종목 표시)
            sorted_holdings = sorted(pnl_data['holdings_data'], key=lambda x: x['total_pnl_usd'], reverse=True)
            
            message_parts.append(f"📈 <b>종목별 현황 (전체 {len(sorted_holdings)}개)</b>")
            for holding in sorted_holdings:
                pnl_emoji = "📈" if holding['total_pnl_usd'] >= 0 else "📉"
                pnl_sign = "+" if holding['total_pnl_usd'] >= 0 else ""
                rate_sign = "+" if holding['return_rate'] >= 0 else ""
                
                message_parts.append(
                    f"{pnl_emoji} <code>{holding['ticker']}</code>: "
                    f"{pnl_sign}${holding['total_pnl_usd']:,.2f} ({rate_sign}{holding['return_rate']:.1f}%)"
                )
                
                if holding['dividends_usd'] > 0:
                    message_parts.append(f"     배당: ${holding['dividends_usd']:,.2f} ({holding['dividend_count']}회)")
            
            message_parts.append("")
            
            # 원화 환산
            total_pnl_krw = pnl_data['total_pnl_usd'] * pnl_data['current_rate']
            message_parts.append(f"💱 <b>원화 환산</b> (₩{pnl_data['current_rate']:,.0f})")
            message_parts.append(f"  • 총 손익: {pnl_symbol}₩{total_pnl_krw:,.0f}")
            
            response = '\n'.join(message_parts)
            await update.message.reply_text(response, parse_mode='HTML')
            
    except Exception as e:
        await update.message.reply_text(f'❌ 포트폴리오 리포트 생성 중 오류 발생: {e}')

@restricted  
async def test_daily_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/test_report 명령어 처리 - 일일 리포트 테스트"""
    await update.message.reply_text('🧪 일일 리포트 테스트를 실행합니다...')
    
    try:
        # Flask 앱 컨텍스트에서 실행
        from .__init__ import get_app
        app = get_app()
        with app.app_context():
            send_daily_portfolio_report()
            await update.message.reply_text('✅ 일일 리포트 테스트가 완료되었습니다!')
            
    except Exception as e:
        await update.message.reply_text(f'❌ 일일 리포트 테스트 중 오류 발생: {e}')

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사용자가 /start 명령어를 보냈을 때 실행됩니다."""
    await update.message.reply_text(
        '🤖 커버드 콜 포트폴리오 관리 봇입니다!\n\n'
        '📊 포트폴리오 리포트:\n'
        '/portfolio_report - 현재 포트폴리오 리포트 (미실현 + 배당금)\n'
        '/test_report - 일일 리포트 테스트 전송\n\n'
        
        '💡 자동 일일 리포트:\n'
        '• 매일 한국시간 오전 6시 (미국 증시 마감 1시간 후)\n'
        '• 총 손익률이 -3% 이하일 때 경고 메시지 포함\n'
        '• 총 손익률이 -5% 이하일 때 심각한 경고 메시지 포함\n\n'
        
        '📱 투자 현황을 실시간으로 확인하세요! 💰'
    )

# 대화 상태 상수
TICKER, SHARES, PRICE, TOTAL_AMOUNT, EXCHANGE_AMOUNT, EXCHANGE_KRW, DATE, CONFIRM = range(8)

# 사용자별 데이터 저장
user_data = {}

# @restricted
# async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """/buy 명령어 시작 - 티커 입력 요청"""
#     await update.message.reply_text('어떤 종목을 매수하셨나요? (예: NVDY)\n\n입력을 취소하려면 /cancel 을 입력하세요.')
#     return TICKER

# @restricted
# async def buy_ticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """티커 입력 처리"""
#     ticker = update.message.text.upper().strip()
#     user_id = update.effective_user.id
    
#     if user_id not in user_data:
#         user_data[user_id] = {}
    
#     user_data[user_id]['ticker'] = ticker
    
#     await update.message.reply_text(
#         f'{ticker} 매수 정보를 순서대로 입력해주세요.\n\n'
#         '1️⃣ 몇 주를 매수하셨나요?'
#     )
#     return SHARES

# @restricted
# async def buy_shares(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """주식 수 입력 처리"""
#     try:
#         shares = Decimal(update.message.text.strip())
#         if shares <= 0:
#             await update.message.reply_text('주식 수는 0보다 커야 합니다. 다시 입력해주세요.')
#             return SHARES
#     except:
#         await update.message.reply_text('올바른 숫자를 입력해주세요. 다시 입력해주세요.')
#         return SHARES
    
#     user_id = update.effective_user.id
#     user_data[user_id]['shares'] = shares
    
#     await update.message.reply_text(
#         '2️⃣ 1주당 가격을 입력하세요\n'
#         '달러 가격만 입력 (예: 150.50):'
#     )
#     return PRICE

# @restricted
# async def buy_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """주당 가격 입력 처리"""
#     try:
#         price = Decimal(update.message.text.strip())
#         if price <= 0:
#             await update.message.reply_text('가격은 0보다 커야 합니다. 다시 입력해주세요.')
#             return PRICE
#     except:
#         await update.message.reply_text('올바른 숫자를 입력해주세요. 다시 입력해주세요.')
#         return PRICE
    
#     user_id = update.effective_user.id
#     user_data[user_id]['price'] = price
#     total_amount = user_data[user_id]['shares'] * price
#     user_data[user_id]['total_amount'] = total_amount
    
#     await update.message.reply_text(
#         f'3️⃣ 총 구매금액(달러)을 입력하세요:\n'
#         f'계산된 금액: ${total_amount:.3f}\n'
#         f'(다른 금액이면 직접 입력)'
#     )
#     return TOTAL_AMOUNT

# @restricted
# async def buy_total_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """총 구매금액 입력 처리"""
#     try:
#         total_amount = Decimal(update.message.text.strip())
#         if total_amount <= 0:
#             await update.message.reply_text('총 금액은 0보다 커야 합니다. 다시 입력해주세요.')
#             return TOTAL_AMOUNT
#     except:
#         await update.message.reply_text('올바른 숫자를 입력해주세요. 다시 입력해주세요.')
#         return TOTAL_AMOUNT
    
#     user_id = update.effective_user.id
#     user_data[user_id]['total_amount'] = total_amount
    
#     await update.message.reply_text(
#         '4️⃣ 주문 중 환전한 달러를 입력하세요:\n'
#         '(배당금으로만 구매한 경우 0 입력)'
#     )
#     return EXCHANGE_AMOUNT

# @restricted
# async def buy_exchange_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """환전 달러 금액 입력 처리"""
#     try:
#         exchange_amount = Decimal(update.message.text.strip())
#         if exchange_amount < 0:
#             await update.message.reply_text('환전 금액은 0 이상이어야 합니다. 다시 입력해주세요.')
#             return EXCHANGE_AMOUNT
#     except:
#         await update.message.reply_text('올바른 숫자를 입력해주세요. 다시 입력해주세요.')
#         return EXCHANGE_AMOUNT
    
#     user_id = update.effective_user.id
#     user_data[user_id]['exchange_amount'] = exchange_amount
    
#     if exchange_amount == 0:
#         user_data[user_id]['exchange_krw'] = 0
#         user_data[user_id]['dividend_used'] = user_data[user_id]['total_amount']
#         await show_confirmation(update, user_id)
#         return CONFIRM
#     else:
#         await update.message.reply_text(
#             '5️⃣ 환전에 사용한 원화를 입력하세요:\n'
#             '(수수료 포함, 환전하지 않았으면 0 입력)'
#         )
#         return EXCHANGE_KRW

# @restricted
# async def buy_exchange_krw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """환전 원화 금액 입력 처리"""
#     try:
#         exchange_krw = Decimal(update.message.text.strip())
#         if exchange_krw < 0:
#             await update.message.reply_text('원화 금액은 0 이상이어야 합니다. 다시 입력해주세요.')
#             return EXCHANGE_KRW
#     except:
#         await update.message.reply_text('올바른 숫자를 입력해주세요. 다시 입력해주세요.')
#         return EXCHANGE_KRW
    
#     user_id = update.effective_user.id
#     user_data[user_id]['exchange_krw'] = exchange_krw
    
#     # 계산
#     exchange_amount = user_data[user_id]['exchange_amount']
#     total_amount = user_data[user_id]['total_amount']
#     user_data[user_id]['dividend_used'] = total_amount - exchange_amount
    
#     if exchange_krw > 0 and exchange_amount > 0:
#         user_data[user_id]['exchange_rate'] = exchange_krw / exchange_amount
#     else:
#         user_data[user_id]['exchange_rate'] = None
    
#     await update.message.reply_text(
#         f'6️⃣ 거래 날짜를 입력하세요:\n'
#         f'(YYYY-MM-DD 형식, 예: 2024-07-01)\n'
#         f'오늘 날짜로 하려면 "오늘" 입력'
#     )
#     return DATE

# @restricted
# async def buy_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """6단계: 거래 날짜 입력"""
#     user_id = update.effective_user.id
#     date_input = update.message.text.strip()
    
#     if date_input == "다시":
#         await update.message.reply_text(
#             f'6️⃣ 거래 날짜를 입력하세요:\n'
#             f'(YYYY-MM-DD 형식, 예: 2024-07-01)\n'
#             f'오늘 날짜로 하려면 "오늘" 입력'
#         )
#         return DATE
    
#     if date_input == "오늘":
#         trade_date = date.today()
#     else:
#         try:
#             trade_date = datetime.strptime(date_input, '%Y-%m-%d').date()
#         except ValueError:
#             await update.message.reply_text(
#                 '❌ 날짜 형식이 잘못되었습니다.\n'
#                 'YYYY-MM-DD 형식으로 입력하거나 "오늘"을 입력하세요.\n'
#                 '예: 2024-07-01'
#             )
#             return DATE
    
#     user_data[user_id]['trade_date'] = trade_date
    
#     await show_confirmation(update, user_id)
#     return CONFIRM

# async def show_confirmation(update: Update, user_id: int):
#     """최종 확인 메시지 생성"""
#     data = user_data[user_id]
    
#     ticker = data['ticker']
#     shares = data['shares']
#     price = data['price']
#     total_amount = data['total_amount']
#     exchange_amount = data.get('exchange_amount', 0)
#     exchange_krw = data.get('exchange_krw', 0)
#     dividend_used = data.get('dividend_used', 0)
#     exchange_rate = data.get('exchange_rate')
#     trade_date = data.get('trade_date', date.today())
    
#     message = f"✅ 매수 내역 확인\n"
#     message += f"━" * 18 + "\n"
#     message += f"📈 {ticker} {int(shares)}주 매수\n"
#     message += f"📅 거래일: {trade_date}\n\n"
#     message += f"- 주당가: ${price:.3f}\n"
#     message += f"- 총 구매: ${total_amount:.3f}\n\n"
    
#     if exchange_amount > 0:
#         message += f"💱 환전 정보\n\n"
#         message += f"- 환전액: ${exchange_amount:.3f}\n"
#         message += f"- 사용 원화: ₩{exchange_krw:,.0f}\n"
#         if exchange_rate:
#             message += f"- 적용 환율: ₩{exchange_rate:.3f}\n\n"
#         if dividend_used > 0:
#             message += f"💰 배당금 사용: ${dividend_used:.3f}\n"
#     else:
#         message += f"💰 배당금으로만 구매하신 것으로 확인됩니다.\n"
#         message += f"사용한 배당금: ${dividend_used:.3f}\n"
    
#     message += f"━" * 18 + "\n\n"
#     message += f"저장하시겠습니까? (예/아니오/다시)"
    
#     await update.message.reply_text(message)

# @restricted
# async def buy_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """최종 확인 및 데이터베이스 저장"""
#     response = update.message.text.strip().lower()
#     user_id = update.effective_user.id
    
#     if response in ['다시', '재입력', 'again', 'retry']:
#         await update.message.reply_text('처음부터 다시 입력해주세요. /buy 를 입력하세요.')
#         if user_id in user_data:
#             del user_data[user_id]
#         return ConversationHandler.END
    
#     if response not in ['예', 'yes', 'y', '네', '저장']:
#         await update.message.reply_text('입력을 취소했습니다.')
#         if user_id in user_data:
#             del user_data[user_id]
#         return ConversationHandler.END
    
#     # 데이터베이스에 저장
#     data = user_data[user_id]
    
#     with app.app_context():
#         try:
#             # Transaction 기록
#             new_transaction = Transaction(
#                 date=data.get('trade_date', date.today()),
#                 type='BUY',
#                 ticker=data['ticker'],
#                 shares=data['shares'],
#                 price_per_share=data['price'],
#                 amount=data['total_amount'],
#                 exchange_rate=data.get('exchange_rate'),
#                 amount_krw=data.get('exchange_krw', 0),
#                 dividend_used=data.get('dividend_used', 0),
#                 cash_invested_krw=data.get('exchange_krw', 0)
#             )
#             db.session.add(new_transaction)
            
#             # Holding 업데이트 (기존 테이블 구조에 맞게 수정)
#             holding = Holding.query.filter_by(ticker=data['ticker']).first()
#             if holding:
#                 # 기존 보유량 업데이트
#                 old_total_cost = holding.current_shares * holding.total_cost_basis
#                 new_total_cost = old_total_cost + data['total_amount']
#                 new_total_shares = holding.current_shares + data['shares']
                
#                 holding.total_cost_basis = new_total_cost / new_total_shares if new_total_shares > 0 else 0
#                 holding.current_shares = new_total_shares
#             else:
#                 # 새 보유 종목 (기존 컴럼만 사용)
#                 holding = Holding(
#                     ticker=data['ticker'],
#                     current_shares=data['shares'],
#                     total_cost_basis=data['price'],
#                     total_dividends_received=0,
#                     current_market_price=0
#                 )
#                 db.session.add(holding)
            
#             db.session.commit()
            
#             await update.message.reply_text(
#                 f"✅ {data['ticker']} {int(data['shares'])}주 매수 기록 완료!\n"
#                 f"현재 {data['ticker']} 총 보유: {int(holding.current_shares)}주"
#             )
            
#         except Exception as e:
#             db.session.rollback()
#             await update.message.reply_text(f"❌ 오류가 발생했습니다: {e}")
#             print(f"Error in buy transaction: {e}")
    
#     # 데이터 정리
#     if user_id in user_data:
#         del user_data[user_id]
    
#     return ConversationHandler.END

# @restricted
# async def buy_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """매수 입력 취소"""
#     user_id = update.effective_user.id
#     if user_id in user_data:
#         del user_data[user_id]
    
#     await update.message.reply_text('매수 입력을 취소했습니다.')
#     return ConversationHandler.END

# @restricted # <-- 제한 데코레이터 적용
# async def get_db_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """
#     데이터베이스의 테이블 목록과 각 테이블의 데이터 유무(레코드 수)를 확인합니다.
#     """
#     message_parts = ["📊 데이터베이스 상태:"]
    
#     with app.app_context():
#         try:
#             # 현재 데이터베이스 이름 가져오기
#             db_name_result = db.session.execute(db.text("SELECT DATABASE();")).scalar()
#             if db_name_result:
#                 message_parts.append(f"DB 이름: `{db_name_result}`")
                
#                 message_parts.append("\n**테이블 목록:**")

#                 # information_schema에서 테이블 목록 조회
#                 tables_result = db.session.execute(
#                     db.text("SELECT table_name FROM information_schema.tables WHERE table_schema = :db_name"),
#                     {"db_name": db_name_result}
#                 ).scalars().all()
#             else:
#                 message_parts.append("DB 이름을 가져올 수 없습니다.")
#                 message_parts.append("\n**테이블 목록:** (DB 연결 오류로 확인 불가)")
#                 tables_result = []

#             if not tables_result:
#                 message_parts.append("테이블이 존재하지 않습니다.")
#             else:
#                 for table_name in tables_result:
#                     try:
#                         # 각 테이블의 레코드 수 조회
#                         count = db.session.execute(
#                             db.text(f"SELECT COUNT(*) FROM `{table_name}`") # 백틱(``)으로 테이블명 감싸기
#                         ).scalar()
#                         message_parts.append(f"- `{table_name}`: {count}개 레코드")
#                     except Exception as e_count:
#                         message_parts.append(f"- `{table_name}`: (레코드 수 확인 불가 - {e_count})")
            
#             await update.message.reply_text("\n".join(message_parts), parse_mode='Markdown')

#         except Exception as e:
#             await update.message.reply_text(f'❌ 데이터베이스 상태 확인 중 오류가 발생했습니다: {e}')
#             print(f"Error checking DB status: {e}")

# @restricted
# async def dividend_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/dividend 명령어 처리"""
#     args = context.args
#     if len(args) < 2 or len(args) > 3:
#         await update.message.reply_text(
#             '사용법: /dividend <티커> <배당금액> [날짜]\n'
#             '예시: /dividend NVDY 50.25\n'
#             '예시: /dividend NVDY 50.25 2024-12-15'
#         )
#         return
    
#     ticker = args[0].upper()
#     try:
#         amount = Decimal(args[1])
#     except:
#         await update.message.reply_text('배당금 금액은 올바른 숫자여야 합니다.')
#         return
    
#     dividend_date = date.today()
#     if len(args) == 3:
#         try:
#             dividend_date = datetime.strptime(args[2], '%Y-%m-%d').date()
#         except ValueError:
#             await update.message.reply_text('날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해주세요.')
#             return
    
#     with app.app_context():
#         try:
#             # Dividend 테이블에 배당금 기록
#             new_dividend = Dividend(
#                 date=dividend_date,
#                 ticker=ticker,
#                 amount=amount
#             )
#             db.session.add(new_dividend)
            
#             # Holding 업데이트
#             holding = Holding.query.filter_by(ticker=ticker).first()
#             if holding:
#                 # 기존 total_dividends_received 컴럼 사용
#                 current_dividends = getattr(holding, 'total_dividends_received', 0) or 0
#                 holding.total_dividends_received = current_dividends + amount
            
#             db.session.commit()
#             await update.message.reply_text(
#                 f'✅ {ticker} 배당금 ${amount} 수령 기록 완료!'
#             )
            
#         except Exception as e:
#             db.session.rollback()
#             await update.message.reply_text(f'❌ 배당금 기록 중 오류: {e}')
#             print(f"Error recording dividend: {e}")

# @restricted
# async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/history 명령어 처리 - 매수/배당금 거래 내역 통합 조회"""
#     args = context.args
#     ticker = args[0].upper() if args else None
#     days = int(args[1]) if len(args) > 1 else None
    
#     with app.app_context():
#         try:
#             history_items = []
            
#             # Transaction 테이블에서 거래 내역 조회
#             transaction_query = Transaction.query
#             if ticker:
#                 transaction_query = transaction_query.filter_by(ticker=ticker)
#             if days:
#                 cutoff_date = date.today() - timedelta(days=days)
#                 transaction_query = transaction_query.filter(Transaction.date >= cutoff_date)
            
#             transactions = transaction_query.order_by(Transaction.date.desc()).all()
            
#             for t in transactions:
#                 history_items.append({
#                     'date': t.date,
#                     'type': '매수' if t.type.lower() == 'buy' else t.type,
#                     'ticker': t.ticker,
#                     'shares': t.shares,
#                     'price': t.price_per_share,
#                     'amount': t.amount,
#                     'exchange_rate': t.exchange_rate,
#                     'dividend_used': t.dividend_used,
#                     'id': t.transaction_id
#                 })
            
#             # Dividend 테이블에서 배당금 내역 조회
#             dividend_query = Dividend.query
#             if ticker:
#                 dividend_query = dividend_query.filter_by(ticker=ticker)
#             if days:
#                 cutoff_date = date.today() - timedelta(days=days)
#                 dividend_query = dividend_query.filter(Dividend.date >= cutoff_date)
            
#             dividends = dividend_query.order_by(Dividend.date.desc()).all()
            
#             for d in dividends:
#                 history_items.append({
#                     'date': d.date,
#                     'type': '배당금',
#                     'ticker': d.ticker,
#                     'amount': d.amount,
#                     'shares': d.shares_held,
#                     'dividend_per_share': d.dividend_per_share,
#                     'id': d.dividend_id
#                 })
            
#             # 날짜순 정렬
#             history_items.sort(key=lambda x: x['date'], reverse=True)
            
#             if not history_items:
#                 if ticker:
#                     await update.message.reply_text(f'{ticker} 거래 내역이 없습니다.')
#                 else:
#                     await update.message.reply_text('거래 내역이 없습니다.')
#                 return
            
#             # 메시지 작성
#             title = f'📋 {ticker + " " if ticker else ""}거래 내역'
#             if days:
#                 title += f' (최근 {days}일)'
            
#             message = title + '\n' + '━' * 25 + '\n'
            
#             for item in history_items:
#                 date_str = item['date'].strftime('%m/%d')
#                 line = ""
                
#                 if item['type'] == '매수':
#                     shares = float(item['shares'])
#                     price = float(item['price'])
#                     amount = float(item['amount'])
                    
#                     line = f"{date_str} 매수 {item['ticker']} [ID:{item.get('id', 'N/A')}]\n"
#                     line += f"   {int(shares)}주 @ ${price:.3f} = ${amount:.3f}\n"
                    
#                     if item.get('exchange_rate'):
#                         exchange_rate = float(item['exchange_rate'])
#                         line += f"   환율: ₩{exchange_rate:.3f}\n"
                    
#                     if item.get('dividend_used') and item['dividend_used'] > 0:
#                         dividend_used = float(item['dividend_used'])
#                         line += f"   배당금 사용: ${dividend_used:.3f}\n"
                    
#                 elif item['type'] == '배당금':
#                     amount = float(item['amount'])
#                     line = f"{date_str} 배당금 {item['ticker']} [ID:{item.get('id', 'N/A')}]\n"
#                     line += f"   ${amount:.3f}"
                    
#                     if item.get('dividend_per_share'):
#                         dividend_per_share = float(item['dividend_per_share'])
#                         line += f" (${dividend_per_share:.3f}/주)"
                    
#                     line += '\n'
                
#                 message += line + '\n'
            
#             await update.message.reply_text(message)
            
#         except Exception as e:
#             await update.message.reply_text(f'❌ 거래 내역 조회 중 오류: {e}')
#             print(f"Error in history command: {e}")

# @restricted
# async def edit_dividend_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/edit_dividend 명령어 처리 - 배당금 날짜 수정"""
#     args = context.args
    
#     if len(args) < 3:
#         await update.message.reply_text(
#             '사용법: /edit_dividend <배당금ID> <새날짜> <새금액>\n'
#             '예: /edit_dividend 1 2024-07-01 50.25\n\n'
#             '배당금 ID는 /history 명령어로 확인하세요.'
#         )
#         return
    
#     try:
#         dividend_id = int(args[0])
#         new_date = datetime.strptime(args[1], '%Y-%m-%d').date()
#         new_amount = Decimal(args[2])
#     except (ValueError, IndexError):
#         await update.message.reply_text('잘못된 형식입니다. 날짜는 YYYY-MM-DD 형식으로 입력하세요.')
#         return
    
#     with app.app_context():
#         try:
#             dividend = Dividend.query.get(dividend_id)
#             if not dividend:
#                 await update.message.reply_text(f'ID {dividend_id} 배당금 기록을 찾을 수 없습니다.')
#                 return
            
#             old_date = dividend.date
#             old_amount = dividend.amount
            
#             dividend.date = new_date
#             dividend.amount = new_amount
#             db.session.commit()
            
#             await update.message.reply_text(
#                 f'✅ 배당금 기록이 수정되었습니다!\n'
#                 f'{dividend.ticker}\n'
#                 f'날짜: {old_date} → {new_date}\n'
#                 f'금액: ${float(old_amount):.3f} → ${float(new_amount):.3f}'
#             )
            
#         except Exception as e:
#             db.session.rollback()
#             await update.message.reply_text(f'❌ 배당금 수정 중 오류: {e}')
#             print(f"Error editing dividend: {e}")

# @restricted
# async def delete_dividend_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/delete_dividend 명령어 처리 - 배당금 삭제"""
#     args = context.args
    
#     if len(args) < 1:
#         await update.message.reply_text(
#             '사용법: /delete_dividend <배당금ID>\n'
#             '예: /delete_dividend 1\n\n'
#             '배당금 ID는 /history 명령어로 확인하세요.'
#         )
#         return
    
#     try:
#         dividend_id = int(args[0])
#     except ValueError:
#         await update.message.reply_text('배당금 ID는 숫자로 입력하세요.')
#         return
    
#     with app.app_context():
#         try:
#             dividend = Dividend.query.get(dividend_id)
#             if not dividend:
#                 await update.message.reply_text(f'ID {dividend_id} 배당금 기록을 찾을 수 없습니다.')
#                 return
            
#             ticker = dividend.ticker
#             amount = dividend.amount
#             date_str = dividend.date
            
#             # Holding에서 배당금 차감
#             holding = Holding.query.filter_by(ticker=ticker).first()
#             if holding:
#                 current_dividends = getattr(holding, 'total_dividends_received', 0) or 0
#                 holding.total_dividends_received = current_dividends - amount
            
#             db.session.delete(dividend)
#             db.session.commit()
            
#             await update.message.reply_text(
#                 f'✅ 배당금 기록이 삭제되었습니다!\n'
#                 f'{ticker} ${float(amount):.3f} ({date_str})'
#             )
            
#         except Exception as e:
#             db.session.rollback()
#             await update.message.reply_text(f'❌ 배당금 삭제 중 오류: {e}')
#             print(f"Error deleting dividend: {e}")

# @restricted
# async def edit_transaction_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/edit_transaction 명령어 처리 - 매수 거래 수정"""
#     args = context.args
    
#     if len(args) < 4:
#         await update.message.reply_text(
#             '사용법: /edit_transaction <거래ID> <주수> <단가> <환율> [날짜]\n'
#             '예: /edit_transaction 1 10 150.50 1400 2024-07-01\n'
#             '날짜 생략 시 기존 날짜 유지\n\n'
#             '거래 ID는 /history 명령어로 확인하세요.'
#         )
#         return
    
#     try:
#         transaction_id = int(args[0])
#         new_shares = Decimal(args[1])
#         new_price = Decimal(args[2])
#         new_exchange_rate = Decimal(args[3]) if len(args) > 3 else None
#         new_date = datetime.strptime(args[4], '%Y-%m-%d').date() if len(args) > 4 else None
#     except (ValueError, IndexError):
#         await update.message.reply_text('잘못된 형식입니다. 숫자나 날짜 형식을 확인하세요.')
#         return
    
#     with app.app_context():
#         try:
#             transaction = Transaction.query.get(transaction_id)
#             if not transaction:
#                 await update.message.reply_text(f'ID {transaction_id} 거래 기록을 찾을 수 없습니다.')
#                 return
            
#             old_shares = transaction.shares
#             old_price = transaction.price_per_share
#             old_amount = transaction.amount
#             old_exchange_rate = transaction.exchange_rate
#             old_date = transaction.date
            
#             # 새 값 계산
#             new_amount = new_shares * new_price
            
#             # 기존 Holding에서 차감
#             holding = Holding.query.filter_by(ticker=transaction.ticker).first()
#             if holding:
#                 # 기존 거래 차감
#                 holding.current_shares -= old_shares
#                 holding.total_cost_basis = ((holding.total_cost_basis * (holding.current_shares + old_shares)) - old_amount) / holding.current_shares if holding.current_shares > 0 else 0
                
#                 # 새 거래 추가
#                 holding.current_shares += new_shares
#                 if holding.current_shares > 0:
#                     holding.total_cost_basis = ((holding.total_cost_basis * (holding.current_shares - new_shares)) + new_amount) / holding.current_shares
#                     holding.avg_purchase_price = holding.total_cost_basis
                
#                 if new_exchange_rate:
#                     # 환율 가중평균 재계산
#                     total_shares_before = holding.current_shares - new_shares
#                     if total_shares_before > 0:
#                         holding.avg_exchange_rate = ((holding.avg_exchange_rate * total_shares_before) + (new_exchange_rate * new_shares)) / holding.current_shares
#                     else:
#                         holding.avg_exchange_rate = new_exchange_rate
            
#             # 거래 기록 업데이트
#             transaction.shares = new_shares
#             transaction.price_per_share = new_price
#             transaction.amount = new_amount
#             if new_exchange_rate:
#                 transaction.exchange_rate = new_exchange_rate
#             if new_date:
#                 transaction.date = new_date
            
#             db.session.commit()
            
#             message = f'✅ 거래 기록이 수정되었습니다!\n{transaction.ticker}\n'
#             message += f'주수: {int(old_shares)} → {int(new_shares)}\n'
#             message += f'단가: ${float(old_price):.3f} → ${float(new_price):.3f}\n'
#             message += f'총액: ${float(old_amount):.3f} → ${float(new_amount):.3f}\n'
            
#             if new_exchange_rate and old_exchange_rate:
#                 message += f'환율: ₩{float(old_exchange_rate):.3f} → ₩{float(new_exchange_rate):.3f}\n'
            
#             if new_date:
#                 message += f'날짜: {old_date} → {new_date}\n'
                
#             await update.message.reply_text(message.rstrip())
            
#         except Exception as e:
#             db.session.rollback()
#             await update.message.reply_text(f'❌ 거래 수정 중 오류: {e}')
#             print(f"Error editing transaction: {e}")

# @restricted
# async def delete_transaction_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/delete_transaction 명령어 처리 - 매수 거래 삭제"""
#     args = context.args
    
#     if len(args) < 1:
#         await update.message.reply_text(
#             '사용법: /delete_transaction <거래ID>\n'
#             '예: /delete_transaction 1\n\n'
#             '거래 ID는 /history 명령어로 확인하세요.'
#         )
#         return
    
#     try:
#         transaction_id = int(args[0])
#     except ValueError:
#         await update.message.reply_text('거래 ID는 숫자로 입력하세요.')
#         return
    
#     with app.app_context():
#         try:
#             transaction = Transaction.query.get(transaction_id)
#             if not transaction:
#                 await update.message.reply_text(f'ID {transaction_id} 거래 기록을 찾을 수 없습니다.')
#                 return
            
#             ticker = transaction.ticker
#             shares = transaction.shares
#             amount = transaction.amount
#             price = transaction.price_per_share
            
#             # Holding에서 해당 거래 차감
#             holding = Holding.query.filter_by(ticker=ticker).first()
#             if holding:
#                 holding.current_shares -= shares
                
#                 if holding.current_shares > 0:
#                     # 평균 단가 재계산
#                     total_cost = (holding.total_cost_basis * (holding.current_shares + shares)) - amount
#                     holding.total_cost_basis = total_cost / holding.current_shares
#                     holding.avg_purchase_price = holding.total_cost_basis
#                 else:
#                     # 모든 주식 매도됨
#                     holding.current_shares = 0
#                     holding.total_cost_basis = 0
#                     holding.avg_purchase_price = 0
#                     holding.avg_exchange_rate = 0
            
#             db.session.delete(transaction)
#             db.session.commit()
            
#             await update.message.reply_text(
#                 f'✅ 거래 기록이 삭제되었습니다!\n'
#                 f'{ticker} {int(shares)}주 @ ${float(price):.3f}'
#             )
            
#         except Exception as e:
#             db.session.rollback()
#             await update.message.reply_text(f'❌ 거래 삭제 중 오류: {e}')
#             print(f"Error deleting transaction: {e}")

# @restricted
# async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/status 명령어 처리"""
#     args = context.args
    
#     with app.app_context():
#         try:
#             if not args:  # 전체 포트폴리오
#                 holdings = Holding.query.all()
#                 if not holdings:
#                     await update.message.reply_text('보유 중인 주식이 없습니다.')
#                     return
                
#                 message = '📈 포트폴리오 현황\n' + '━' * 20 + '\n'
#                 total_cost = Decimal('0')
#                 total_value = Decimal('0')
                
#                 total_dividends = Decimal('0')
                
#                 # 포트폴리오 전체 배당금 제외 투자금 계산용
#                 total_cash_invested = Decimal('0')
#                 total_cash_invested_usd = Decimal('0')
                
#                 for holding in holdings:
#                     cost_basis = holding.current_shares * holding.total_cost_basis
#                     current_value = holding.current_shares * holding.current_market_price
#                     profit_loss = current_value - cost_basis
#                     profit_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
                    
#                     # 해당 종목의 배당금 정보 조회
#                     total_dividends_received = db.session.query(db.func.sum(Dividend.amount)).filter_by(ticker=holding.ticker).scalar() or 0
#                     total_dividend_reinvested = db.session.query(db.func.sum(Transaction.dividend_used)).filter_by(ticker=holding.ticker).scalar() or 0
#                     cash_only_investment = db.session.query(db.func.sum(Transaction.cash_invested_krw)).filter_by(ticker=holding.ticker).scalar() or 0
#                     cash_only_investment_usd = db.session.query(db.func.sum(Transaction.amount - Transaction.dividend_used)).filter_by(ticker=holding.ticker).scalar() or 0
                    
#                     total_profit_with_dividends = profit_loss + total_dividends_received
#                     total_profit_pct_with_dividends = (total_profit_with_dividends / cost_basis * 100) if cost_basis > 0 else 0
                    
#                     total_cost += cost_basis
#                     total_value += current_value
#                     total_dividends += total_dividends_received
#                     total_cash_invested += cash_only_investment
#                     total_cash_invested_usd += cash_only_investment_usd
                    
#                     message += f'{holding.ticker}: {int(holding.current_shares)}주\n'
#                     message += f'  배당금 제외 투자금: ${float(cash_only_investment_usd):.3f} (₩{float(cash_only_investment):,.0f})\n'
#                     message += f'  총 투자금: ${float(cost_basis):.3f}\n'
#                     message += f'  현재 가치: ${float(current_value):.3f}\n'
#                     message += f'  평균단가: ${float(holding.total_cost_basis):.3f}\n'
#                     message += f'  현재가: ${float(holding.current_market_price):.3f}\n'
#                     message += f'  주식수익률: {float(profit_pct):+.3f}%\n'
                    
#                     if total_dividends_received > 0:
#                         message += f'  배당금 수령: ${float(total_dividends_received):.3f}\n'
#                     if total_dividend_reinvested > 0:
#                         message += f'  배당금 재투자: ${float(total_dividend_reinvested):.3f}\n'
#                     if total_dividends_received > 0:
#                         message += f'  배당금포함 수익률: {float(total_profit_pct_with_dividends):+.3f}%\n'
#                     message += '\n'
                
#                 # 전체 포트폴리오 배당금 재투자 총액
#                 total_dividend_reinvested = db.session.query(db.func.sum(Transaction.dividend_used)).scalar() or 0
                
#                 total_profit = total_value - total_cost
#                 total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
#                 total_profit_with_dividends = total_profit + total_dividends
#                 total_profit_pct_with_dividends = (total_profit_with_dividends / total_cost * 100) if total_cost > 0 else 0
                
#                 message += f'━' * 20 + '\n'
#                 message += f'📊 포트폴리오 요약\n'
#                 message += f'배당금 제외 투자금: ${float(total_cash_invested_usd):.3f} (₩{float(total_cash_invested):,.0f})\n'
#                 message += f'총 투자금: ${float(total_cost):.3f}\n'
#                 message += f'현재 가치: ${float(total_value):.3f}\n'
#                 message += f'주식 수익: ${float(total_profit):+.3f} ({float(total_profit_pct):+.3f}%)\n'
                
#                 if total_dividends > 0:
#                     message += f'배당금 수령: ${float(total_dividends):.3f}\n'
#                 if total_dividend_reinvested > 0:
#                     message += f'배당금 재투자: ${float(total_dividend_reinvested):.3f}\n'
#                 if total_dividends > 0:
#                     message += f'배당포함 총수익: ${float(total_profit_with_dividends):+.3f} ({float(total_profit_pct_with_dividends):+.3f}%)'
#                 else:
#                     message += f'총 수익: ${float(total_profit):+.3f} ({float(total_profit_pct):+.3f}%)'
                
#                 await update.message.reply_text(message)
                
#             else:  # 특정 종목
#                 ticker = args[0].upper()
#                 holding = Holding.query.filter_by(ticker=ticker).first()
                
#                 if not holding:
#                     await update.message.reply_text(f'{ticker} 주식을 보유하고 있지 않습니다.')
#                     return
                
#                 cost_basis = holding.current_shares * holding.total_cost_basis
#                 current_value = holding.current_shares * holding.current_market_price
#                 profit_loss = current_value - cost_basis
#                 profit_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
                
#                 # 해당 종목의 배당금 정보 조회
#                 total_dividends_received = db.session.query(db.func.sum(Dividend.amount)).filter_by(ticker=ticker).scalar() or 0
#                 total_dividend_reinvested = db.session.query(db.func.sum(Transaction.dividend_used)).filter_by(ticker=ticker).scalar() or 0
#                 cash_only_investment = db.session.query(db.func.sum(Transaction.cash_invested_krw)).filter_by(ticker=ticker).scalar() or 0
#                 cash_only_investment_usd = db.session.query(db.func.sum(Transaction.amount - Transaction.dividend_used)).filter_by(ticker=ticker).scalar() or 0
                
#                 total_profit_with_dividends = profit_loss + total_dividends_received
#                 total_profit_pct_with_dividends = (total_profit_with_dividends / cost_basis * 100) if cost_basis > 0 else 0
                
#                 message = f'📈 {ticker} 상세 정보\n' + '━' * 20 + '\n'
#                 message += f'보유 주수: {int(holding.current_shares)}주\n'
#                 message += f'배당금 제외 투자금: ${float(cash_only_investment_usd):.3f} (₩{float(cash_only_investment):,.0f})\n'
#                 message += f'총 투자금: ${float(cost_basis):.3f}\n'
#                 message += f'현재 가치: ${float(current_value):.3f}\n'
#                 message += f'평균 매수가: ${float(holding.total_cost_basis):.3f}\n'
#                 message += f'현재 주가: ${float(holding.current_market_price):.3f}\n'
#                 message += f'주식 수익: ${float(profit_loss):+.3f} ({float(profit_pct):+.3f}%)\n'
                
#                 if total_dividends_received > 0:
#                     message += f'배당금 수령: ${float(total_dividends_received):.3f}\n'
#                 if total_dividend_reinvested > 0:
#                     message += f'배당금 재투자: ${float(total_dividend_reinvested):.3f}\n'
#                 if total_dividends_received > 0:
#                     message += f'배당포함 총수익: ${float(total_profit_with_dividends):+.3f} ({float(total_profit_pct_with_dividends):+.3f}%)'
#                 else:
#                     message += f'총 수익: ${float(profit_loss):+.3f} ({float(profit_pct):+.3f}%)'
                
#                 await update.message.reply_text(message)
                
#         except Exception as e:
#             await update.message.reply_text(f'❌ 상태 조회 중 오류: {e}')
#             print(f"Error in status command: {e}")

# @restricted
# async def set_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/set_price 명령어 처리"""
#     args = context.args
#     if len(args) != 2:
#         await update.message.reply_text(
#             '사용법: /set_price <티커> <현재가>\n'
#             '예시: /set_price NVDY 155.25'
#         )
#         return
    
#     ticker = args[0].upper()
#     try:
#         price = Decimal(args[1])
#     except:
#         await update.message.reply_text('가격은 올바른 숫자여야 합니다.')
#         return
    
#     with app.app_context():
#         try:
#             holding = Holding.query.filter_by(ticker=ticker).first()
#             if not holding:
#                 await update.message.reply_text(f'{ticker} 주식을 보유하고 있지 않습니다.')
#                 return
            
#             old_price = holding.current_market_price
#             holding.current_market_price = price
#             holding.last_price_update_date = date.today()
            
#             db.session.commit()
            
#             await update.message.reply_text(
#                 f'✅ {ticker} 현재가 업데이트 완료!\n'
#                 f'${old_price:.3f} → ${price:.3f}'
#             )
            
#         except Exception as e:
#             db.session.rollback()
#             await update.message.reply_text(f'❌ 가격 업데이트 중 오류: {e}')
#             print(f"Error updating price: {e}")

# @restricted
# async def update_prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/update_prices 명령어 처리 - 모든 보유 종목 주가 업데이트"""
#     await update.message.reply_text('📈 모든 보유 종목의 주가를 업데이트하고 있습니다...')
    
#     try:
#         result = update_stock_price()
        
#         if result['success']:
#             message = f"✅ 주가 업데이트 완료!\n\n{result['message']}"
#         else:
#             message = f"❌ 주가 업데이트 실패\n\n{result['message']}"
        
#         await update.message.reply_text(message)
        
#     except Exception as e:
#         await update.message.reply_text(f'❌ 주가 업데이트 중 오류: {e}')
#         print(f"Error in update_prices_command: {e}")

# @restricted
# async def update_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/update_price 명령어 처리 - 특정 종목 주가 업데이트"""
#     args = context.args
#     if len(args) != 1:
#         await update.message.reply_text(
#             '사용법: /update_price <티커>\n'
#             '예시: /update_price NVDY'
#         )
#         return
    
#     ticker = args[0].upper()
#     await update.message.reply_text(f'📈 {ticker} 주가를 업데이트하고 있습니다...')
    
#     try:
#         result = update_stock_price(ticker=ticker)
        
#         if result['success']:
#             message = f"✅ {ticker} 주가 업데이트 완료!\n\n{result['message']}"
#         else:
#             message = f"❌ {ticker} 주가 업데이트 실패\n\n{result['message']}"
        
#         await update.message.reply_text(message)
        
#     except Exception as e:
#         await update.message.reply_text(f'❌ {ticker} 주가 업데이트 중 오류: {e}')
#         print(f"Error in update_price_command: {e}")

# @restricted
# async def scheduler_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """/scheduler_status 명령어 처리 - 스케줄러 상태 확인"""
#     try:
#         status = get_scheduler_status()
#         await update.message.reply_text(status)
        
#     except Exception as e:
#         await update.message.reply_text(f'❌ 스케줄러 상태 확인 중 오류: {e}')
#         print(f"Error in scheduler_status_command: {e}")


# # 에러 핸들러
# async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """봇 업데이트 중 발생한 에러를 로깅합니다."""
#     print(f'Update {update} caused error {context.error}')

# # 다른 모든 메시지에 대한 핸들러 (선택 사항: 제한된 메시지 처리)
# async def handle_unrecognized_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if update.message:
#         user_id = update.effective_user.id
#         if user_id not in ALLOWED_USER_IDS:
#             await update.message.reply_text(
#                 f"죄송합니다. 이 봇은 특정 사용자만 이용할 수 있습니다. 당신의 사용자 ID는 {user_id} 입니다. 이 ID를 봇 관리자에게 알려주세요."
#             )
#         else:
#             await update.message.reply_text("알 수 없는 명령입니다. /start 를 입력하여 사용법을 확인하세요.")

# 글로벌 변수로 봇 애플리케이션 저장
bot_application = None

async def send_message_with_retry(bot, user_id, message, max_retries=3):
    """재시도 로직이 포함된 메시지 전송"""
    for attempt in range(max_retries):
        try:
            await bot.send_message(chat_id=user_id, text=message, parse_mode='HTML')
            print(f"Message sent to user {user_id} (attempt {attempt + 1})")
            return True
        except Exception as e:
            print(f"Failed to send message to user {user_id} (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return False
            # 지수 백오프: 2초, 4초, 8초 대기
            await asyncio.sleep(2 ** attempt)
    return False

def send_message_to_telegram(message):
    """텔레그램 봇으로 메시지 전송 (개선된 버전)"""
    global bot_application
    
    if not bot_application:
        print("Bot application is not initialized yet.")
        return
    
    if not hasattr(bot_application, 'bot') or bot_application.bot is None:
        print("Bot instance is not available in application.")
        return
    
    try:
        # 허용된 모든 사용자에게 메시지 전송
        async def send_to_all_users():
            if bot_application and bot_application.bot:
                bot = bot_application.bot
                success_count = 0
                for user_id in ALLOWED_USER_IDS:
                    if await send_message_with_retry(bot, user_id, message):
                        success_count += 1
                print(f"Message sent to {success_count}/{len(ALLOWED_USER_IDS)} users")
        
        # 현재 스레드에서 실행
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 이벤트 루프가 있으면 태스크로 생성
                asyncio.create_task(send_to_all_users())
            else:
                # 새로운 이벤트 루프 실행
                loop.run_until_complete(send_to_all_users())
        except RuntimeError:
            # 이벤트 루프가 없으면 새로 생성
            asyncio.run(send_to_all_users())
            
    except Exception as e:
        print(f"Error sending message to telegram: {e}")

def run_telegram_bot_in_thread():
    """텔레그램 봇을 시작하는 함수 (asyncio 이벤트 루프 설정 포함)"""
    global bot_application
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 타임아웃 및 재시도 설정 추가 (API 제한 방지)
    application = Application.builder().token(BOT_TOKEN)\
        .connect_timeout(30.0)\
        .read_timeout(30.0)\
        .write_timeout(30.0)\
        .pool_timeout(30.0)\
        .get_updates_connect_timeout(30.0)\
        .get_updates_read_timeout(30.0)\
        .get_updates_pool_timeout(30.0)\
        .concurrent_updates(1)\
        .build()
    bot_application = application

    # 애플리케이션 초기화
    loop.run_until_complete(application.initialize())

    # 명령어 핸들러 등록
    application.add_handler(CommandHandler("start", start))
    
    # Buy 기능 주석 처리 (현재 사용하지 않음)
    # buy_conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler('buy', buy_start)],
    #     states={
    #         TICKER: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_ticker)],
    #         SHARES: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_shares)],
    #         PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_price)],
    #         TOTAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_total_amount)],
    #         EXCHANGE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_exchange_amount)],
    #         EXCHANGE_KRW: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_exchange_krw)],
    #         DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_date)],
    #         CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_confirm)],
    #     },
    #     fallbacks=[CommandHandler('cancel', buy_cancel)],
    # )
    # application.add_handler(buy_conv_handler)
    
    # 기타 명령어 핸들러 (주석 처리된 함수들은 제외)
    # application.add_handler(CommandHandler("dividend", dividend_command))
    # application.add_handler(CommandHandler("status", status_command))
    # application.add_handler(CommandHandler("set_price", set_price_command))
    # application.add_handler(CommandHandler("db_status", get_db_status))
    # application.add_handler(CommandHandler("history", history_command))
    # application.add_handler(CommandHandler("edit_dividend", edit_dividend_command))
    # application.add_handler(CommandHandler("delete_dividend", delete_dividend_command))
    # application.add_handler(CommandHandler("edit_transaction", edit_transaction_command))
    # application.add_handler(CommandHandler("delete_transaction", delete_transaction_command))
    
    # 주가 업데이트 명령어 핸들러 (주석 처리된 함수들은 제외)
    # application.add_handler(CommandHandler("update_prices", update_prices_command))
    # application.add_handler(CommandHandler("update_price", update_price_command))
    # application.add_handler(CommandHandler("scheduler_status", scheduler_status_command))
    
    # 포트폴리오 리포트 관련 명령어
    application.add_handler(CommandHandler("portfolio_report", portfolio_report_command))
    application.add_handler(CommandHandler("test_report", test_daily_report_command))

    # 간단한 메시지 핸들러와 에러 핸들러 추가
    async def handle_unrecognized_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """인식되지 않은 메시지 처리"""
        await update.message.reply_text('🤔 죄송합니다. 이해하지 못했습니다. /start를 입력해 사용 가능한 명령어를 확인하세요.')
    
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """에러 핸들러"""
        print(f"Update {update} caused error {context.error}")
        if update and update.message:
            await update.message.reply_text('❌ 처리 중 오류가 발생했습니다. 다시 시도해주세요.')

    # 모든 텍스트 메시지에 대한 핸들러. 명령어 핸들러 이후에 등록해야 합니다.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unrecognized_message))

    # 에러 핸들러 등록
    application.add_error_handler(error_handler)

    print("Telegram Bot is starting...")
    print("폴링 설정: 2초 간격, 10초 타임아웃 (최대 12초마다 API 요청)")
    print("메시지 응답 지연: 최대 12초 (일반적으로 2-10초 이내)")
    print("업그레이드된 서버 사양(2 vCPU, 2GB RAM)에 최적화된 설정")
    # 반응성과 효율성의 균형을 맞춘 설정
    application.run_polling(
        allowed_updates=Update.ALL_TYPES, 
        stop_signals=[],
        poll_interval=2.0,   # 2초마다 폴링 (반응적)
        timeout=10,          # 롱폴링으로 10초 대기 (합리적)
        bootstrap_retries=3, # 재시도 횟수
        close_loop=False
    )
    print("Telegram Bot stopped.")

