from flask import Flask
from .models import db
from .routes import card_bp
import os

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

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)