from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

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

# SQLAlchemy 객체 초기화
db = SQLAlchemy(app)