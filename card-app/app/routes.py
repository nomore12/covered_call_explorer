from flask import jsonify, request, Blueprint
from .models import CreditCard, db
from .telegram_utils import send_message_to_telegram
from pytz import timezone as pytz_timezone
from datetime import datetime, timedelta
import re
import calendar

card_bp = Blueprint('card', __name__)

@card_bp.route('/credit_card', methods=['POST'])
def credit_card():
    """신용카드 정보를 받아서 데이터베이스에 저장하고 텔레그램 봇에 메시지 전송"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON 데이터가 필요합니다."}), 400
        
        # 필수 필드 검증
        if 'date' not in data or 'body' not in data:
            return jsonify({"error": "date와 body 필드가 필요합니다."}), 400
        
        # body에서 금액 추출
        body = data['body']
        money_spend = 0
        is_cancellation = "취소" in body
        installment_months = 0
        total_amount = 0
        
        # 할부 패턴 찾기 (예: "71,040원 05개월")
        installment_pattern = r'([\d,]+)원\s+(\d+)개월'
        installment_match = re.search(installment_pattern, body)
        
        if installment_match:
            # 할부 거래인 경우
            total_str = installment_match.group(1).replace(',', '')
            months_str = installment_match.group(2)
            try:
                total_amount = int(total_str)
                installment_months = int(months_str)
                # 첫 달 금액 계산 (나머지가 있으면 첫 달에 추가)
                money_spend = total_amount // installment_months
                first_month_extra = total_amount % installment_months
                if first_month_extra > 0:
                    money_spend += first_month_extra
            except ValueError:
                money_spend = 0
        else:
            # 일반 거래인 경우
            # 금액 패턴 찾기 - 두 가지 형식 지원
            # 1. "11,060원" 형식
            # 2. "9,500(KRW)" 형식 (KB카드)
            money_pattern_won = r'([\d,]+)원'
            money_pattern_krw = r'([\d,]+)\(KRW\)'
            
            match = re.search(money_pattern_won, body)
            if not match:
                # "원" 패턴이 없으면 "(KRW)" 패턴 검색
                match = re.search(money_pattern_krw, body)
            
            if match:
                # 쉼표 제거하고 정수로 변환
                money_str = match.group(1).replace(',', '')
                try:
                    money_spend = int(money_str)
                    # 취소인 경우 마이너스로 변환
                    if is_cancellation:
                        money_spend = -money_spend
                except ValueError:
                    money_spend = 0
        
        # 날짜 파싱 ("2025. 7. 10. 오전 11:27" 형식)
        date_str = data['date']
        try:
            # 날짜 문자열을 파싱
            
            # "2025. 7. 10. 오전 11:27" 형식 파싱
            date_pattern = r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(오전|오후)\s*(\d{1,2}):(\d{2})'
            match = re.match(date_pattern, date_str)
            
            if match:
                year, month, day, ampm, hour, minute = match.groups()
                hour = int(hour)
                if ampm == '오후' and hour != 12:
                    hour += 12
                elif ampm == '오전' and hour == 12:
                    hour = 0
                
                # 한국 시간으로 datetime 생성
                dt = datetime(int(year), int(month), int(day), hour, int(minute))
                korea_tz = pytz_timezone('Asia/Seoul')
                dt_with_tz = korea_tz.localize(dt)
            else:
                # 파싱 실패시 현재 시간 사용
                dt_with_tz = datetime.now(pytz_timezone('Asia/Seoul'))
                
        except Exception as e:
            print(f"Date parsing error: {e}")
            # 파싱 실패시 현재 시간 사용
            dt_with_tz = datetime.now(pytz_timezone('Asia/Seoul'))
        
        # 첫 번째 거래 저장
        credit_card = CreditCard(
            datetime=dt_with_tz,
            money_spend=money_spend
        )
        
        db.session.add(credit_card)
        
        # 할부인 경우 나머지 개월도 추가
        if installment_months > 1:
            # 각 달의 금액 계산
            remaining_amount = total_amount - money_spend
            monthly_payment = remaining_amount // (installment_months - 1)
            
            # 나머지 할부 개월 추가
            for month_offset in range(1, installment_months):
                # 다음 달 같은 날짜 계산
                next_month_date = dt_with_tz + timedelta(days=30 * month_offset)
                # 정확한 날짜 계산을 위해 월 단위로 이동
                year = dt_with_tz.year
                month = dt_with_tz.month + month_offset
                day = dt_with_tz.day
                
                # 연도 넘어가는 경우 처리
                while month > 12:
                    month -= 12
                    year += 1
                
                # 해당 월의 마지막 날보다 큰 경우 처리 (예: 1월 31일 -> 2월 28일)
                try:
                    next_month_date = dt_with_tz.replace(year=year, month=month, day=day)
                except ValueError:
                    # 해당 월에 그 날짜가 없는 경우 (예: 2월 30일)
                    import calendar
                    last_day = calendar.monthrange(year, month)[1]
                    next_month_date = dt_with_tz.replace(year=year, month=month, day=last_day)
                
                # 마지막 달인 경우 남은 금액 전부
                if month_offset == installment_months - 1:
                    payment = remaining_amount - (monthly_payment * (installment_months - 2))
                else:
                    payment = monthly_payment
                
                future_credit_card = CreditCard(
                    datetime=next_month_date,
                    money_spend=payment
                )
                db.session.add(future_credit_card)
        
        db.session.commit()
        
        # 1. 이번 주(월요일부터 오늘까지) 총 소비 금액 계산
        today = dt_with_tz.date()
        monday = today - timedelta(days=today.weekday())  # 월요일 계산
        start_of_week = monday
        
        # 이번 주 신용카드 사용 내역 조회
        weekly_spending = db.session.query(db.func.sum(CreditCard.money_spend)).filter(
            CreditCard.datetime >= start_of_week,
            CreditCard.datetime <= today + timedelta(days=1)  # 오늘 포함
        ).scalar() or 0
        
        # 2. 경보 단계 계산 (20만원을 100%로 설정)
        max_weekly_budget = 200000  # 20만원
        warning_levels = [50000, 100000, 150000, 200000]  # 5만, 10만, 15만, 20만
        current_percentage = (weekly_spending / max_weekly_budget) * 100
        
        # 경보 메시지 생성
        warning_message = ""
        if weekly_spending >= warning_levels[3]:  # 20만원 이상
            warning_message = f"🚨 4단계 경보: 주간 예산 초과! ({current_percentage:.1f}%)"
        elif weekly_spending >= warning_levels[2]:  # 15만원 이상
            warning_message = f"⚠️ 3단계 경보: 주간 예산 75% 도달! ({current_percentage:.1f}%)"
        elif weekly_spending >= warning_levels[1]:  # 10만원 이상
            warning_message = f"🟡 2단계 경보: 주간 예산 50% 도달! ({current_percentage:.1f}%)"
        elif weekly_spending >= warning_levels[0]:  # 5만원 이상
            warning_message = f"✅ 1단계 경보: 주간 예산 25% 도달! ({current_percentage:.1f}%)"
        
        # 3. 텔레그램 메시지 생성
        if is_cancellation:
            message = f"💳 신용카드 취소 알림\n"
        elif installment_months > 0:
            message = f"💳 신용카드 할부 결제 알림\n"
        else:
            message = f"💳 신용카드 결제 알림\n"
        
        message += f"━━━━━━━━━━━━━━━━\n"
        
        if installment_months > 0:
            message += f"💰 총 금액: {total_amount:,}원\n"
            message += f"📅 할부: {installment_months}개월\n"
            message += f"💸 이번 달: {money_spend:,}원\n"
            if installment_months > 1:
                remaining_amount = total_amount - money_spend
                monthly_payment = remaining_amount // (installment_months - 1)
                message += f"💵 남은 달: {monthly_payment:,}원 × {installment_months-1}개월\n"
        elif is_cancellation:
            message += f"💰 금액: {abs(money_spend):,}원 (카드 취소)\n"
        else:
            message += f"💰 금액: {money_spend:,}원\n"
            
        message += f"⏰ 시간: {dt_with_tz.strftime('%Y-%m-%d %H:%M')}\n"
        message += f"━━━━━━━━━━━━━━━━\n"
        message += f"📊 이번 주 소비 현황\n"
        message += f"📅 기간: {start_of_week.strftime('%m/%d')} ~ {today.strftime('%m/%d')}\n"
        message += f"💸 총 사용액: {weekly_spending:,}원\n"
        message += f"🎯 예산 대비: {current_percentage:.1f}% ({max_weekly_budget:,}원 중)\n"
        
        if warning_message:
            message += f"\n{warning_message}"
        
        # 텔레그램 봇으로 메시지 전송
        send_message_to_telegram(message)
        
        return jsonify({
            "success": True,
            "message": "신용카드 정보가 저장되고 텔레그램으로 전송되었습니다.",
            "spend_id": credit_card.spend_id,
            "money_spend": money_spend,
            "datetime": dt_with_tz.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500