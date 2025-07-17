"""
JWT 인증 관련 유틸리티 함수들
시나리오 2: Access Token 1시간, Refresh Token 7일
"""

import jwt
import hashlib
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional, Dict, Any, Tuple, Callable
from flask import request, jsonify, current_app
from .models import User, RefreshToken, AuditLog, db


class TokenConfig:
    """토큰 설정 - 시나리오 2번"""
    ACCESS_TOKEN_EXPIRES = timedelta(hours=1)      # 1시간
    REFRESH_TOKEN_EXPIRES = timedelta(days=7)      # 7일
    ALGORITHM = 'HS256'


class JWTService:
    """JWT 토큰 관리 서비스"""
    
    @staticmethod
    def generate_access_token(user_id: int, username: str) -> str:
        """Access Token 생성"""
        payload = {
            'user_id': user_id,
            'username': username,
            'type': 'access',
            'exp': datetime.now(timezone.utc) + TokenConfig.ACCESS_TOKEN_EXPIRES,
            'iat': datetime.now(timezone.utc),
            'nbf': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm=TokenConfig.ALGORITHM)
    
    @staticmethod
    def generate_refresh_token(user_id: int, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> RefreshToken:
        """Refresh Token 생성 및 DB 저장"""
        # 기존 활성 토큰 무효화 (선택적 - 보안 강화)
        RefreshToken.query.filter_by(user_id=user_id, is_revoked=False).update({'is_revoked': True})
        
        # 새 토큰 생성
        token_string = RefreshToken.generate_token()
        expires_at = datetime.now(timezone.utc) + TokenConfig.REFRESH_TOKEN_EXPIRES
        
        # 디바이스 핑거프린트 생성
        device_fingerprint = None
        if user_agent:
            fingerprint_input = f"{user_agent}{ip_address or ''}"
            device_fingerprint = hashlib.sha256(fingerprint_input.encode()).hexdigest()[:64]
        
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token_string,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint
        )
        
        db.session.add(refresh_token)
        db.session.commit()
        
        return refresh_token
    
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """Access Token 검증"""
        try:
            payload = jwt.decode(
                token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=[TokenConfig.ALGORITHM]
            )
            
            # 토큰 타입 확인
            if payload.get('type') != 'access':
                raise jwt.InvalidTokenError("Invalid token type")
            
            return payload
        
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Access token has expired")
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid access token")
    
    @staticmethod
    def verify_refresh_token(token: str, ip_address: Optional[str] = None) -> RefreshToken:
        """Refresh Token 검증"""
        refresh_token = RefreshToken.query.filter_by(token=token).first()
        
        if not refresh_token:
            raise jwt.InvalidTokenError("Refresh token not found")
        
        if not refresh_token.is_valid():
            raise jwt.InvalidTokenError("Refresh token is invalid or expired")
        
        # IP 주소 검증 (선택적 보안 강화)
        if ip_address and refresh_token.ip_address and refresh_token.ip_address != ip_address:
            # 감사 로그 기록
            AuditLog.log_action(
                user_id=refresh_token.user_id,
                action="SUSPICIOUS_TOKEN_USE",
                ip_address=ip_address,
                details={"original_ip": refresh_token.ip_address, "current_ip": ip_address}
            )
            raise jwt.InvalidTokenError("Token used from different IP address")
        
        return refresh_token
    
    @staticmethod
    def revoke_refresh_token(token: str) -> bool:
        """Refresh Token 무효화"""
        refresh_token = RefreshToken.query.filter_by(token=token).first()
        if refresh_token:
            refresh_token.revoke()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def revoke_all_user_tokens(user_id: int) -> int:
        """사용자의 모든 Refresh Token 무효화"""
        count = RefreshToken.query.filter_by(user_id=user_id, is_revoked=False).update({
            'is_revoked': True,
            'revoked_at': datetime.now(timezone.utc)
        })
        db.session.commit()
        return count


def get_token_from_header() -> Optional[str]:
    """Authorization 헤더에서 토큰 추출"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        scheme, token = auth_header.split(' ', 1)
        if scheme.lower() != 'bearer':
            return None
        return token
    except ValueError:
        return None


def get_client_info() -> Tuple[Optional[str], Optional[str]]:
    """클라이언트 정보 추출"""
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if ip_address and ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()
    
    user_agent = request.headers.get('User-Agent')
    return ip_address, user_agent


def jwt_required(f: Callable) -> Callable:
    """JWT 인증 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({'error': 'Access token is required'}), 401
        
        try:
            payload = JWTService.verify_access_token(token)
            
            # 사용자 존재 확인
            user = User.query.get(payload['user_id'])
            if not user or not user.is_active:
                return jsonify({'error': 'Invalid user'}), 401
            
            # request 객체에 사용자 정보 저장
            request.current_user = user
            request.token_payload = payload
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Access token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid access token'}), 401
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function


def optional_jwt(f: Callable) -> Callable:
    """선택적 JWT 인증 데코레이터 (토큰이 있으면 검증, 없어도 허용)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        
        if token:
            try:
                payload = JWTService.verify_access_token(token)
                user = User.query.get(payload['user_id'])
                if user and user.is_active:
                    request.current_user = user
                    request.token_payload = payload
            except:
                pass  # 토큰이 유효하지 않아도 계속 진행
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f: Callable) -> Callable:
    """관리자 권한 필요 데코레이터"""
    @wraps(f)
    @jwt_required
    def decorated_function(*args, **kwargs):
        # 현재는 단일 사용자이므로 모든 인증된 사용자를 관리자로 간주
        # 추후 User 모델에 role 필드 추가 시 확장 가능
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit_by_user(max_requests: int = 100, per_minutes: int = 60):
    """사용자별 API 호출 제한 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 토큰에서 사용자 ID 추출
            token = get_token_from_header()
            if not token:
                return f(*args, **kwargs)  # 인증되지 않은 요청은 통과
            
            try:
                payload = JWTService.verify_access_token(token)
                user_id = payload['user_id']
                
                # 여기에 Redis 또는 메모리 기반 레이트 리미터 구현
                # 현재는 단순히 로그만 기록
                AuditLog.log_action(
                    user_id=user_id,
                    action="API_CALL",
                    resource=f.__name__,
                    ip_address=get_client_info()[0]
                )
                
            except:
                pass  # 토큰 검증 실패 시 그냥 진행
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator