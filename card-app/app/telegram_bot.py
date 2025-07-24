import os
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import calendar
from pytz import timezone as pytz_timezone
from .models import db, CreditCard
from sqlalchemy import and_

# 한국 시간대
KST = pytz_timezone('Asia/Seoul')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """봇 시작 명령어"""
    await update.message.reply_text(
        "💳 신용카드 지출 통계 봇\n\n"
        "사용 가능한 명령어:\n"
        "/week - 이번 주 통계 (예정된 할부 포함)\n"
        "/last_week - 지난 주 통계\n"
        "/month - 이번 달 통계 (예정된 할부 포함)\n"
        "/last_month - 지난 달 통계"
    )

def get_week_range(date):
    """주어진 날짜가 속한 주의 월요일과 일요일을 반환"""
    # 월요일 (weekday=0)
    monday = date - timedelta(days=date.weekday())
    # 일요일
    sunday = monday + timedelta(days=6)
    return monday, sunday

async def week_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """이번 주 통계 (월~일, 예정된 할부 포함)"""
    try:
        # Flask 앱 컨텍스트 가져오기
        flask_app = context.bot_data.get('flask_app')
        if not flask_app:
            await update.message.reply_text("서버 오류가 발생했습니다.")
            return
            
        with flask_app.app_context():
            # 현재 한국 시간
            now_kst = datetime.now(KST)
            today = now_kst.date()
            
            # 이번 주 월요일과 일요일
            monday, sunday = get_week_range(today)
            
            # 이번 주의 시작과 끝 시간 (한국 시간 기준)
            week_start = KST.localize(datetime.combine(monday, datetime.min.time()))
            week_end = KST.localize(datetime.combine(sunday, datetime.max.time()))
            
            # 이번 주 데이터 조회 (예정된 할부 포함)
            week_data = db.session.query(CreditCard).filter(
                and_(
                    CreditCard.datetime >= week_start,
                    CreditCard.datetime <= week_end
                )
            ).all()
        
            # 통계 계산
            total_spending = sum(card.money_spend for card in week_data)
            transaction_count = len(week_data)
            
            # 일별 지출 계산
            daily_spending = {}
            for card in week_data:
                date_key = card.datetime.astimezone(KST).date()
                daily_spending[date_key] = daily_spending.get(date_key, 0) + card.money_spend
            
            # 메시지 생성
            message = f"📊 이번 주 통계 (예정된 할부 포함)\n"
            message += f"━━━━━━━━━━━━━━━━\n"
            message += f"📅 기간: {monday.strftime('%Y-%m-%d')} ~ {sunday.strftime('%Y-%m-%d')}\n"
            message += f"💸 총 지출: {total_spending:,}원\n"
            message += f"📝 거래 건수: {transaction_count}건\n"
            message += f"━━━━━━━━━━━━━━━━\n"
            message += f"📆 일별 지출:\n"
            
            # 월요일부터 일요일까지 모든 날짜 표시
            current_date = monday
            while current_date <= sunday:
                spending = daily_spending.get(current_date, 0)
                weekday_names = ['월', '화', '수', '목', '금', '토', '일']
                weekday_name = weekday_names[current_date.weekday()]
                
                # 오늘 표시
                today_marker = " 📍" if current_date == today else ""
                # 미래 날짜는 다른 색으로 표시
                if current_date > today:
                    message += f"  {current_date.strftime('%m/%d')} ({weekday_name}) - {spending:,}원 (예정){today_marker}\n"
                else:
                    message += f"  {current_date.strftime('%m/%d')} ({weekday_name}) - {spending:,}원{today_marker}\n"
                
                current_date += timedelta(days=1)
            
            await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"오류가 발생했습니다: {str(e)}")

async def last_week_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """지난 주 통계"""
    try:
        # Flask 앱 컨텍스트 가져오기
        flask_app = context.bot_data.get('flask_app')
        if not flask_app:
            await update.message.reply_text("서버 오류가 발생했습니다.")
            return
            
        with flask_app.app_context():
            # 현재 한국 시간
            now_kst = datetime.now(KST)
            today = now_kst.date()
            
            # 지난 주 월요일과 일요일
            last_week = today - timedelta(days=7)
            monday, sunday = get_week_range(last_week)
            
            # 지난 주의 시작과 끝 시간 (한국 시간 기준)
            week_start = KST.localize(datetime.combine(monday, datetime.min.time()))
            week_end = KST.localize(datetime.combine(sunday, datetime.max.time()))
            
            # 지난 주 데이터 조회
            week_data = db.session.query(CreditCard).filter(
                and_(
                    CreditCard.datetime >= week_start,
                    CreditCard.datetime <= week_end
                )
            ).all()
        
            # 통계 계산
            total_spending = sum(card.money_spend for card in week_data)
            transaction_count = len(week_data)
            
            # 일별 지출 계산
            daily_spending = {}
            for card in week_data:
                date_key = card.datetime.astimezone(KST).date()
                daily_spending[date_key] = daily_spending.get(date_key, 0) + card.money_spend
            
            # 메시지 생성
            message = f"📊 지난 주 통계\n"
            message += f"━━━━━━━━━━━━━━━━\n"
            message += f"📅 기간: {monday.strftime('%Y-%m-%d')} ~ {sunday.strftime('%Y-%m-%d')}\n"
            message += f"💸 총 지출: {total_spending:,}원\n"
            message += f"📝 거래 건수: {transaction_count}건\n"
            message += f"━━━━━━━━━━━━━━━━\n"
            message += f"📆 일별 지출:\n"
            
            # 월요일부터 일요일까지 모든 날짜 표시
            current_date = monday
            while current_date <= sunday:
                spending = daily_spending.get(current_date, 0)
                weekday_names = ['월', '화', '수', '목', '금', '토', '일']
                weekday_name = weekday_names[current_date.weekday()]
                message += f"  {current_date.strftime('%m/%d')} ({weekday_name}) - {spending:,}원\n"
                current_date += timedelta(days=1)
            
            await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"오류가 발생했습니다: {str(e)}")

async def month_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """이번 달 통계 (1일~말일, 예정된 할부 포함)"""
    try:
        # Flask 앱 컨텍스트 가져오기
        flask_app = context.bot_data.get('flask_app')
        if not flask_app:
            await update.message.reply_text("서버 오류가 발생했습니다.")
            return
            
        with flask_app.app_context():
            # 현재 한국 시간
            now_kst = datetime.now(KST)
            today = now_kst.date()
            
            # 이번 달의 첫날과 마지막날
            month_start_date = today.replace(day=1)
            month_end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
            
            # 시작과 끝 시간 (한국 시간 기준)
            month_start = KST.localize(datetime.combine(month_start_date, datetime.min.time()))
            month_end = KST.localize(datetime.combine(month_end_date, datetime.max.time()))
            
            # 이번 달 데이터 조회 (예정된 할부 포함)
            month_data = db.session.query(CreditCard).filter(
                and_(
                    CreditCard.datetime >= month_start,
                    CreditCard.datetime <= month_end
                )
            ).all()
        
            # 통계 계산
            total_spending = sum(card.money_spend for card in month_data)
            transaction_count = len(month_data)
            
            # 주차별 지출 계산
            weekly_spending = {}
            for card in month_data:
                date_key = card.datetime.astimezone(KST).date()
                # 주차 계산 (월의 몇 번째 주인지)
                week_of_month = (date_key.day - 1) // 7 + 1
                weekly_spending[week_of_month] = weekly_spending.get(week_of_month, 0) + card.money_spend
            
            # 메시지 생성
            message = f"📊 이번 달 통계 (예정된 할부 포함)\n"
            message += f"━━━━━━━━━━━━━━━━\n"
            message += f"📅 기간: {month_start_date.strftime('%Y년 %m월')}\n"
            message += f"💸 총 지출: {total_spending:,}원\n"
            message += f"📝 거래 건수: {transaction_count}건\n"
            message += f"💰 일평균: {total_spending // today.day:,}원\n"
            message += f"━━━━━━━━━━━━━━━━\n"
            message += f"📆 주차별 지출:\n"
            
            # 주차별 표시
            for week in range(1, 6):  # 최대 5주차까지
                if week in weekly_spending:
                    message += f"  {week}주차 - {weekly_spending[week]:,}원\n"
            
            # 예상 월 총 지출 (오늘까지의 평균으로 계산)
            if today.day < month_end_date.day:
                daily_average = total_spending / today.day
                estimated_total = int(daily_average * month_end_date.day)
                message += f"━━━━━━━━━━━━━━━━\n"
                message += f"📈 예상 월 총 지출: {estimated_total:,}원"
            
            await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"오류가 발생했습니다: {str(e)}")

async def last_month_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """지난 달 통계"""
    try:
        # Flask 앱 컨텍스트 가져오기
        flask_app = context.bot_data.get('flask_app')
        if not flask_app:
            await update.message.reply_text("서버 오류가 발생했습니다.")
            return
            
        with flask_app.app_context():
            # 현재 한국 시간
            now_kst = datetime.now(KST)
            today = now_kst.date()
            
            # 지난 달 계산
            if today.month == 1:
                last_month_year = today.year - 1
                last_month_month = 12
            else:
                last_month_year = today.year
                last_month_month = today.month - 1
            
            # 지난 달의 첫날과 마지막날
            month_start_date = today.replace(year=last_month_year, month=last_month_month, day=1)
            month_end_date = month_start_date.replace(
                day=calendar.monthrange(last_month_year, last_month_month)[1]
            )
            
            # 시작과 끝 시간 (한국 시간 기준)
            month_start = KST.localize(datetime.combine(month_start_date, datetime.min.time()))
            month_end = KST.localize(datetime.combine(month_end_date, datetime.max.time()))
            
            # 지난 달 데이터 조회
            month_data = db.session.query(CreditCard).filter(
                and_(
                    CreditCard.datetime >= month_start,
                    CreditCard.datetime <= month_end
                )
            ).all()
        
            # 통계 계산
            total_spending = sum(card.money_spend for card in month_data)
            transaction_count = len(month_data)
            
            # 주차별 지출 계산
            weekly_spending = {}
            for card in month_data:
                date_key = card.datetime.astimezone(KST).date()
                # 주차 계산 (월의 몇 번째 주인지)
                week_of_month = (date_key.day - 1) // 7 + 1
                weekly_spending[week_of_month] = weekly_spending.get(week_of_month, 0) + card.money_spend
            
            # 메시지 생성
            message = f"📊 지난 달 통계\n"
            message += f"━━━━━━━━━━━━━━━━\n"
            message += f"📅 기간: {month_start_date.strftime('%Y년 %m월')}\n"
            message += f"💸 총 지출: {total_spending:,}원\n"
            message += f"📝 거래 건수: {transaction_count}건\n"
            message += f"💰 일평균: {total_spending // month_end_date.day:,}원\n"
            message += f"━━━━━━━━━━━━━━━━\n"
            message += f"📆 주차별 지출:\n"
            
            # 주차별 표시
            for week in range(1, 6):  # 최대 5주차까지
                if week in weekly_spending:
                    message += f"  {week}주차 - {weekly_spending[week]:,}원\n"
            
            await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"오류가 발생했습니다: {str(e)}")

def create_telegram_bot(flask_app):
    """텔레그램 봇 생성 및 설정"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
        return None
    
    # Application 생성
    application = Application.builder().token(bot_token).build()
    
    # Flask 앱 컨텍스트를 봇 핸들러에서 사용하기 위한 설정
    application.bot_data['flask_app'] = flask_app
    
    # 명령어 핸들러 등록
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("week", week_stats))
    application.add_handler(CommandHandler("last_week", last_week_stats))
    application.add_handler(CommandHandler("month", month_stats))
    application.add_handler(CommandHandler("last_month", last_month_stats))
    
    return application