from flask import jsonify, request, Blueprint
from .models import CreditCard, db
from .telegram_utils import send_message_to_telegram
from pytz import timezone as pytz_timezone
from datetime import datetime, timedelta
import re

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
        
        # body에서 금액 추출 (할부가 아닌 경우에만)
        body = data['body']
        money_spend = 0
        is_cancellation = "취소" in body
        
        # "할부"가 없는 경우에만 금액 파싱
        if "할부" not in body:
            # 금액 패턴 찾기 (예: "11,060원")
            money_pattern = r'([\d,]+)원'
            match = re.search(money_pattern, body)
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
        
        credit_card = CreditCard(
            datetime=dt_with_tz,
            money_spend=money_spend
        )
        
        db.session.add(credit_card)
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
        else:
            message = f"💳 신용카드 결제 알림\n"
        
        message += f"━━━━━━━━━━━━━━━━\n"
        
        if money_spend == 0 and "할부" in body:
            message += f"💰 금액: 할부 결제\n"
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