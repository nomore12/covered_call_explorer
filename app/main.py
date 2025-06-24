import threading
import time
from sqlalchemy.exc import OperationalError
from .__init__ import app, db
from .telegram_bot import run_telegram_bot_in_thread

# routes.py와 models.py 임포트는 그대로 유지합니다.
from . import routes
from . import models

def connect_to_db_with_retries():
    """
    데이터베이스 연결을 재시도하는 함수.
    성공적으로 연결될 때까지 일정 횟수만큼 재시도합니다.
    """
    retries = 15
    delay = 5  # 재시도 사이의 대기 시간 (초)
    for i in range(retries):
        try:
            # app_context 내에서 데이터베이스 작업을 시도합니다.
            with app.app_context():
                db.create_all()
            print("✅ 데이터베이스 연결 성공 및 테이블 생성 확인 완료.")
            return True # 성공 시 True를 반환하고 함수 종료
        except OperationalError as e:
            print(f"❌ 데이터베이스 연결 실패 (시도 {i + 1}/{retries}): {e}")
            if i < retries - 1:
                print(f"➡️ {delay}초 후 재시도합니다...")
                time.sleep(delay)
            else:
                print("🚨 여러 번의 시도 후에도 데이터베이스에 연결할 수 없습니다. 앱을 종료합니다.")
                return False # 모든 재시도 실패 시 False 반환

if __name__ == '__main__':
    # 데이터베이스 연결 및 테이블 생성을 시도합니다.
    if connect_to_db_with_retries():
        # 연결에 성공한 경우에만 봇과 웹 서버를 시작합니다.
        
        # 텔레그램 봇을 별도의 스레드에서 시작합니다.
        bot_thread = threading.Thread(target=run_telegram_bot_in_thread)
        bot_thread.daemon = True # 메인 프로그램이 종료될 때 스레드도 함께 종료되도록 설정
        bot_thread.start()

        # Flask 웹 서버를 시작합니다.
        print("🚀 Flask 웹 서버를 시작합니다...")
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)