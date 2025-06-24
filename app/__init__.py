from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Flask 앱 인스턴스 생성
app = Flask(__name__)

# 데이터베이스 설정 (환경 변수 사용)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'mysql+pymysql://user:password@db:3306/mydb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy 객체 초기화
db = SQLAlchemy(app)