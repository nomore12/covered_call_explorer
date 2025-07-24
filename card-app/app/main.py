from flask import Flask
from .models import db
from .routes import card_bp
from .telegram_bot import create_telegram_bot
import os
import asyncio
import threading

def create_app():
    """Flask 앱 팩토리 함수"""
    app = Flask(__name__)
    
    # 데이터베이스 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # 블루프린트 등록
    app.register_blueprint(card_bp)
    
    # 기본 라우트
    @app.route('/')
    def health_check():
        return {"status": "healthy", "service": "card-tracker"}, 200
    
    return app

def run_telegram_bot(flask_app):
    """텔레그램 봇을 별도 스레드에서 실행"""
    # 새로운 이벤트 루프 생성
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Flask 앱 컨텍스트 내에서 봇 생성 및 실행
    with flask_app.app_context():
        bot = create_telegram_bot(flask_app)
        if bot:
            print("텔레그램 봇을 시작합니다...")
            loop.run_until_complete(bot.run_polling())

if __name__ == '__main__':
    app = create_app()
    
    # 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()
    
    # 텔레그램 봇을 별도 스레드에서 실행
    bot_thread = threading.Thread(target=run_telegram_bot, args=(app,))
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask 앱 실행
    app.run(host='0.0.0.0', port=5000, debug=False)  # debug=False로 변경 (다중 스레드 환경)