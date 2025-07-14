from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
import os
import logging

# 지연 임포트를 위한 전역 변수
_app = None

def create_app():
    global _app
    # Flask 앱 인스턴스 생성
    app = Flask(__name__)

    # 로깅 설정 (텔레그램 봇 관련 과도한 로그 방지)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Flask 앱 자체 로깅은 INFO 유지
    app.logger.setLevel(logging.INFO)

    # CORS 설정 추가 (개발 환경용)
    CORS(app, 
         origins=[
             "http://localhost",      # 포트 80 (기본)
             "http://localhost:80", 
             "http://localhost:3000", 
             "http://localhost:5173",
             "http://127.0.0.1",      # 포트 80 (기본)
             "http://127.0.0.1:80",
             "http://127.0.0.1:3000", 
             "http://127.0.0.1:5173",
             "http://0.0.0.0",        # Docker 네트워크
             "http://0.0.0.0:80",
             "http://0.0.0.0:3000",
             "http://0.0.0.0:5173",
             "http://115.68.219.189", # 실제 서버 IP
             "http://115.68.219.189:80",
             "http://115.68.219.189:3000",
             "https://115.68.219.189", # HTTPS도 대비
             "https://115.68.219.189:443"
         ],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         supports_credentials=True,
         expose_headers=["Content-Type", "Authorization"])

    # 데이터베이스 설정 (환경 변수 사용)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://user:password@db:3306/mydb'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # SQLAlchemy 초기화
    from .models import db
    db.init_app(app)

    # Flask-Login 초기화
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '로그인이 필요합니다.'

    # 사용자 로더 함수
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # 세션 보안을 위한 SECRET_KEY 설정
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
    
    # CORS 관련 추가 Flask 설정
    app.config['CORS_ALLOW_CREDENTIALS'] = True
    app.config['CORS_EXPOSE_HEADERS'] = ['Content-Type', 'Authorization']

    _app = app
    
    # 지연 Blueprint 등록
    with app.app_context():
        register_blueprints(app)
    
    return app

def register_blueprints(app):
    from .routes.common_routes import common_bp
    from .routes.stock_routes import stock_bp
    from .routes.card_routes import card_bp
    from .routes.auth_routes import auth_bp
    
    app.register_blueprint(common_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(card_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

def get_app():
    """앱 인스턴스를 가져오는 함수"""
    global _app
    if _app is None:
        _app = create_app()
    return _app

# 앱 인스턴스 생성
app = create_app()