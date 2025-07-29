from .__init__ import app
from .models import db
from .scheduler import start_scheduler
from .auth_scheduler import start_auth_scheduler

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
    # print("Starting price update scheduler...")
    # start_scheduler()
    print("Scheduler disabled by user request")
    
    # JWT 인증 스케줄러 시작
    print("Starting JWT auth scheduler...")
    start_auth_scheduler(app)
    print("JWT auth scheduler started")

    # 텔레그램 봇을 별도의 스레드에서 시작합니다.
    # Flask 웹 서버와 독립적으로 봇이 계속 폴링하도록 합니다.
    import threading
    from .telegram_bot import run_telegram_bot_in_thread
    
    bot_thread = threading.Thread(target=run_telegram_bot_in_thread)
    bot_thread.start()
    print("Telegram bot started in separate thread")

    # Flask 웹 서버를 시작합니다 (메인 스레드).
    # 개발 서버이므로 프로덕션 환경에서는 Gunicorn과 같은 WSGI 서버를 사용해야 합니다.
    print("Starting Flask web server...")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule} {list(rule.methods)}")
    print("Server will be available at http://0.0.0.0:5000")
    
    # Docker 개발 환경에서는 debug=False로 설정하여 재시작 문제 방지
    # 대신 FLASK_DEBUG=1 환경 변수로 디버그 기능 활성화
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)