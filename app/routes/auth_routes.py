from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timezone
from ..models import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """로그인 API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON 데이터가 필요합니다."}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "사용자명과 비밀번호가 필요합니다."}), 400
        
        # 사용자 조회 (username 또는 email로 로그인 가능)
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                return jsonify({"error": "비활성화된 계정입니다."}), 403
            
            # 로그인 처리
            login_user(user, remember=True)
            
            # 마지막 로그인 시간 업데이트
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "로그인에 성공했습니다.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            })
        else:
            return jsonify({"error": "잘못된 사용자명 또는 비밀번호입니다."}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """로그아웃 API"""
    try:
        logout_user()
        return jsonify({
            "success": True,
            "message": "로그아웃되었습니다."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """회원가입 API (일회성 관리자 계정 생성용)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON 데이터가 필요합니다."}), 400
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({"error": "사용자명, 이메일, 비밀번호가 모두 필요합니다."}), 400
        
        # 중복 체크
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "이미 존재하는 사용자명입니다."}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "이미 존재하는 이메일입니다."}), 409
        
        # 이미 사용자가 존재하는지 확인 (개인용이므로 1명만 허용)
        if User.query.count() > 0:
            return jsonify({"error": "이미 계정이 존재합니다. 개인용 앱이므로 추가 계정 생성이 불가능합니다."}), 403
        
        # 새 사용자 생성
        new_user = User(
            username=username,
            email=email
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "계정이 성공적으로 생성되었습니다.",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """현재 로그인된 사용자 정보 조회"""
    try:
        return jsonify({
            "success": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """인증 상태 확인 (로그인 필요 없음)"""
    try:
        if current_user.is_authenticated:
            return jsonify({
                "authenticated": True,
                "user": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "email": current_user.email
                }
            })
        else:
            return jsonify({
                "authenticated": False,
                "user": None
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500