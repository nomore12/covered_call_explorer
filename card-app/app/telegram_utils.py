import requests
import os

def send_message_to_telegram(message):
    """텔레그램 봇으로 메시지 전송"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        allowed_users = os.getenv('ALLOWED_TELEGRAM_USER_IDS', '').split(',')
        
        if not bot_token or not allowed_users[0]:
            print("텔레그램 설정이 없습니다.")
            return False
            
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # 허용된 모든 사용자에게 메시지 전송
        for user_id in allowed_users:
            user_id = user_id.strip()
            if user_id:
                data = {
                    'chat_id': user_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, data=data)
                if response.status_code != 200:
                    print(f"텔레그램 메시지 전송 실패 (사용자 {user_id}): {response.text}")
                    
        return True
        
    except Exception as e:
        print(f"텔레그램 메시지 전송 중 오류 발생: {e}")
        return False