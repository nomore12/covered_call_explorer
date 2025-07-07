from .__init__ import app, db
from .scheduler import start_scheduler

# routes.py에 정의된 라우트들이 Flask 앱에 등록되도록 임포트합니다.
# 직접 사용하지 않더라도, 임포트해야 라우트 데코레이터가 실행됩니다.
from . import routes
# models.py에 정의된 모델들이 SQLAlchemy에 등록되도록 임포트합니다.
# db.create_all()을 위해 필요합니다.
from . import models

if __name__ == '__main__':
    # 데이터베이스 테이블 생성 (최초 실행 시 또는 테이블이 없을 경우)
    # app_context() 내에서 실행해야 db 객체가 올바르게 작동합니다.
    with app.app_context():
        db.create_all()
        print("Database tables checked/created.")

    # 주가 업데이트 스케줄러를 시작합니다.
    print("Starting price update scheduler...")
    start_scheduler()

    # 텔레그램 봇을 별도의 스레드에서 시작합니다.
    # Flask 웹 서버와 독립적으로 봇이 계속 폴링하도록 합니다.
    # 일시적으로 비활성화 - 네트워크 문제로 인한 타임아웃 방지
    # bot_thread = threading.Thread(target=run_telegram_bot_in_thread)
    # bot_thread.start()
    print("Telegram bot disabled temporarily for debugging")

    # Flask 웹 서버를 시작합니다 (메인 스레드).
    # 개발 서버이므로 프로덕션 환경에서는 Gunicorn과 같은 WSGI 서버를 사용해야 합니다.
    print("Starting Flask web server...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)