from flask import Flask
from flask_cors import CORS
import os

def create_app():
    # Flask 앱 인스턴스 생성
    app = Flask(__name__)

    # CORS 설정 추가 (개발 환경용 - 모든 origin 허용)
    CORS(app, 
         origins="*",
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"])

    # 데이터베이스 설정 (환경 변수 사용)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://user:password@db:3306/mydb'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # SQLAlchemy 초기화
    from .models import db
    db.init_app(app)

    # Blueprint 등록
    register_blueprints(app)
    
    return app

def register_blueprints(app):
    from .routes.common_routes import common_bp
    from .routes.stock_routes import stock_bp
    from .routes.card_routes import card_bp
    
    app.register_blueprint(common_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(card_bp)

# 앱 인스턴스 생성
app = create_app()