from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timezone
from ..models import User, RefreshToken, AuditLog, db
from ..auth_utils import JWTService, jwt_required, get_client_info, get_token_from_header

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """JWT 기반 로그인 API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON 데이터가 필요합니다."}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "사용자명과 비밀번호가 필요합니다."}), 400
        
        # 클라이언트 정보 추출
        ip_address, user_agent = get_client_info()
        
        # 사용자 조회 (username 또는 email로 로그인 가능)
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                # 감사 로그 기록
                AuditLog.log_action(
                    user_id=user.id,
                    action="LOGIN_FAILED_INACTIVE",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return jsonify({"error": "비활성화된 계정입니다."}), 403
            
            # JWT 토큰 생성
            access_token = JWTService.generate_access_token(user.id, user.username)
            refresh_token = JWTService.generate_refresh_token(user.id, ip_address, user_agent)
            
            # 마지막 로그인 시간 업데이트
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            # 성공 로그 기록
            AuditLog.log_action(
                user_id=user.id,
                action="LOGIN_SUCCESS",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return jsonify({
                "success": True,
                "message": "로그인에 성공했습니다.",
                "access_token": access_token,
                "refresh_token": refresh_token.token,
                "expires_in": 3600,  # 1시간 (초 단위)
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            })
        else:
            # 실패 로그 기록
            AuditLog.log_action(
                user_id=user.id if user else None,
                action="LOGIN_FAILED",
                ip_address=ip_address,
                user_agent=user_agent,
                details={"username": username}
            )
            return jsonify({"error": "잘못된 사용자명 또는 비밀번호입니다."}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Access Token 갱신 API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON 데이터가 필요합니다."}), 400
        
        refresh_token_str = data.get('refresh_token')
        if not refresh_token_str:
            return jsonify({"error": "Refresh token이 필요합니다."}), 400
        
        # 클라이언트 정보 추출
        ip_address, user_agent = get_client_info()
        
        # Refresh Token 검증
        refresh_token = JWTService.verify_refresh_token(refresh_token_str, ip_address)
        
        # 새 Access Token 생성
        user = refresh_token.user
        new_access_token = JWTService.generate_access_token(user.id, user.username)
        
        # 감사 로그 기록
        AuditLog.log_action(
            user_id=user.id,
            action="TOKEN_REFRESH",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify({
            "success": True,
            "access_token": new_access_token,
            "expires_in": 3600,  # 1시간 (초 단위)
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """JWT 기반 로그아웃 API"""
    try:
        data = request.get_json() or {}
        refresh_token_str = data.get('refresh_token')
        
        # 클라이언트 정보 추출
        ip_address, user_agent = get_client_info()
        
        # 현재 사용자 정보
        user = request.current_user
        
        # Refresh Token 무효화
        if refresh_token_str:
            JWTService.revoke_refresh_token(refresh_token_str)
        else:
            # refresh_token이 없으면 해당 사용자의 모든 토큰 무효화
            JWTService.revoke_all_user_tokens(user.id)
        
        # 감사 로그 기록
        AuditLog.log_action(
            user_id=user.id,
            action="LOGOUT",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
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
@jwt_required
def get_current_user():
    """현재 로그인된 사용자 정보 조회"""
    try:
        user = request.current_user
        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """JWT 기반 인증 상태 확인 (로그인 필요 없음)"""
    try:
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                "authenticated": False,
                "user": None
            })
        
        try:
            payload = JWTService.verify_access_token(token)
            user = User.query.get(payload['user_id'])
            
            if user and user.is_active:
                return jsonify({
                    "authenticated": True,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email
                    }
                })
            else:
                return jsonify({
                    "authenticated": False,
                    "user": None
                })
                
        except:
            return jsonify({
                "authenticated": False,
                "user": None
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/revoke-all', methods=['POST'])
@jwt_required
def revoke_all_tokens():
    """사용자의 모든 Refresh Token 무효화 (보안 강화)"""
    try:
        user = request.current_user
        ip_address, user_agent = get_client_info()
        
        # 모든 토큰 무효화
        revoked_count = JWTService.revoke_all_user_tokens(user.id)
        
        # 감사 로그 기록
        AuditLog.log_action(
            user_id=user.id,
            action="REVOKE_ALL_TOKENS",
            ip_address=ip_address,
            user_agent=user_agent,
            details={"revoked_count": revoked_count}
        )
        
        return jsonify({
            "success": True,
            "message": f"{revoked_count}개의 토큰이 무효화되었습니다.",
            "revoked_count": revoked_count
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/test-jwt', methods=['GET'])
@jwt_required
def test_jwt():
    """JWT 인증 테스트 엔드포인트"""
    try:
        user = request.current_user
        payload = request.token_payload
        
        return jsonify({
            "success": True,
            "message": "JWT 인증이 성공적으로 작동합니다.",
            "user_info": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            },
            "token_info": {
                "user_id": payload.get('user_id'),
                "username": payload.get('username'),
                "token_type": payload.get('type'),
                "issued_at": payload.get('iat'),
                "expires_at": payload.get('exp')
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/token-stats', methods=['GET'])
@jwt_required
def get_token_stats():
    """토큰 통계 조회 (관리자용)"""
    try:
        from ..auth_scheduler import get_auth_scheduler
        
        scheduler = get_auth_scheduler()
        if scheduler:
            stats = scheduler.get_token_statistics()
        else:
            # 스케줄러가 없을 때 직접 계산
            from datetime import datetime, timezone
            current_time = datetime.now(timezone.utc)
            
            total_tokens = RefreshToken.query.count()
            active_tokens = RefreshToken.query.filter(
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > current_time
            ).count()
            expired_tokens = RefreshToken.query.filter(
                RefreshToken.expires_at <= current_time
            ).count()
            revoked_tokens = RefreshToken.query.filter(
                RefreshToken.is_revoked == True
            ).count()
            
            stats = {
                "total_tokens": total_tokens,
                "active_tokens": active_tokens,
                "expired_tokens": expired_tokens,
                "revoked_tokens": revoked_tokens,
                "timestamp": current_time.isoformat()
            }
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500