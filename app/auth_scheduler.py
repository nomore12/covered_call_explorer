"""
JWT 토큰 관리 및 보안 관련 스케줄러
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone, timedelta
from .models import RefreshToken, AuditLog, db
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AuthScheduler:
    """JWT 인증 관련 스케줄링 작업"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # 매일 자정에 만료된 토큰 정리
        self.scheduler.add_job(
            func=self.cleanup_expired_tokens,
            trigger="cron",
            hour=0,
            minute=0,
            id='cleanup_expired_tokens'
        )
        
        # 매주 월요일 자정에 오래된 감사 로그 정리 (3개월 이상)
        self.scheduler.add_job(
            func=self.cleanup_old_audit_logs,
            trigger="cron",
            day_of_week='mon',
            hour=0,
            minute=0,
            id='cleanup_old_audit_logs'
        )
        
        logger.info("AuthScheduler initialized and started")
    
    def cleanup_expired_tokens(self):
        """만료된 Refresh Token 정리"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # 만료된 토큰 조회
            expired_tokens = RefreshToken.query.filter(
                RefreshToken.expires_at < current_time
            ).all()
            
            if not expired_tokens:
                logger.info("No expired tokens found")
                return
            
            # 만료된 토큰 삭제
            deleted_count = 0
            for token in expired_tokens:
                db.session.delete(token)
                deleted_count += 1
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} expired refresh tokens")
            
            # 감사 로그 기록
            AuditLog.log_action(
                user_id=None,
                action="CLEANUP_EXPIRED_TOKENS",
                details={"deleted_count": deleted_count}
            )
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            db.session.rollback()
    
    def cleanup_old_audit_logs(self):
        """오래된 감사 로그 정리 (3개월 이상)"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
            
            # 3개월 이상 된 로그 조회
            old_logs = AuditLog.query.filter(
                AuditLog.timestamp < cutoff_date
            ).all()
            
            if not old_logs:
                logger.info("No old audit logs found")
                return
            
            # 오래된 로그 삭제
            deleted_count = 0
            for log in old_logs:
                db.session.delete(log)
                deleted_count += 1
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old audit logs (older than 90 days)")
            
            # 정리 작업 로그 기록
            AuditLog.log_action(
                user_id=None,
                action="CLEANUP_OLD_AUDIT_LOGS",
                details={"deleted_count": deleted_count, "cutoff_days": 90}
            )
            
        except Exception as e:
            logger.error(f"Error cleaning up old audit logs: {e}")
            db.session.rollback()
    
    def cleanup_revoked_tokens(self):
        """무효화된 토큰 중 오래된 것들 정리 (30일 이상)"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            # 30일 이상 된 무효화된 토큰 조회
            old_revoked_tokens = RefreshToken.query.filter(
                RefreshToken.is_revoked == True,
                RefreshToken.revoked_at < cutoff_date
            ).all()
            
            if not old_revoked_tokens:
                logger.info("No old revoked tokens found")
                return
            
            # 오래된 무효화된 토큰 삭제
            deleted_count = 0
            for token in old_revoked_tokens:
                db.session.delete(token)
                deleted_count += 1
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old revoked tokens (older than 30 days)")
            
            # 감사 로그 기록
            AuditLog.log_action(
                user_id=None,
                action="CLEANUP_REVOKED_TOKENS",
                details={"deleted_count": deleted_count, "cutoff_days": 30}
            )
            
        except Exception as e:
            logger.error(f"Error cleaning up revoked tokens: {e}")
            db.session.rollback()
    
    def get_token_statistics(self) -> Optional[Dict[str, Any]]:
        """토큰 관련 통계 조회"""
        try:
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
            
            logger.info(f"Token statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting token statistics: {e}")
            return None
    
    def shutdown(self):
        """스케줄러 종료"""
        try:
            self.scheduler.shutdown()
            logger.info("AuthScheduler shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down AuthScheduler: {e}")


# 전역 스케줄러 인스턴스
auth_scheduler: Optional[AuthScheduler] = None


def start_auth_scheduler() -> AuthScheduler:
    """인증 스케줄러 시작"""
    global auth_scheduler
    if auth_scheduler is None:
        auth_scheduler = AuthScheduler()
        logger.info("Auth scheduler started")
    return auth_scheduler


def stop_auth_scheduler() -> None:
    """인증 스케줄러 중지"""
    global auth_scheduler
    if auth_scheduler is not None:
        auth_scheduler.shutdown()
        auth_scheduler = None
        logger.info("Auth scheduler stopped")


def get_auth_scheduler() -> Optional[AuthScheduler]:
    """현재 스케줄러 인스턴스 반환"""
    global auth_scheduler
    return auth_scheduler