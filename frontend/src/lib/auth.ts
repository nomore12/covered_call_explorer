/**
 * JWT 토큰 관리 유틸리티
 * localStorage를 사용하여 토큰을 안전하게 저장하고 관리합니다.
 */

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: {
    id: number;
    username: string;
    email: string;
  };
};

export type RefreshTokenResponse = {
  access_token: string;
  expires_in: number;
  user: {
    id: number;
    username: string;
    email: string;
  };
};

class AuthTokenManager {
  private readonly ACCESS_TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly TOKEN_EXPIRY_KEY = 'token_expiry';
  private readonly USER_KEY = 'auth_user';

  /**
   * 토큰 저장
   */
  setTokens(tokenResponse: TokenResponse): void {
    const expiryTime = Date.now() + (tokenResponse.expires_in * 1000);
    
    localStorage.setItem(this.ACCESS_TOKEN_KEY, tokenResponse.access_token);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, tokenResponse.refresh_token);
    localStorage.setItem(this.TOKEN_EXPIRY_KEY, expiryTime.toString());
    localStorage.setItem(this.USER_KEY, JSON.stringify(tokenResponse.user));
  }

  /**
   * Access Token 업데이트 (refresh 시)
   */
  updateAccessToken(refreshResponse: RefreshTokenResponse): void {
    const expiryTime = Date.now() + (refreshResponse.expires_in * 1000);
    
    localStorage.setItem(this.ACCESS_TOKEN_KEY, refreshResponse.access_token);
    localStorage.setItem(this.TOKEN_EXPIRY_KEY, expiryTime.toString());
    localStorage.setItem(this.USER_KEY, JSON.stringify(refreshResponse.user));
  }

  /**
   * Access Token 가져오기
   */
  getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  /**
   * Refresh Token 가져오기
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * 저장된 사용자 정보 가져오기
   */
  getUser(): TokenResponse['user'] | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) return null;
    
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  /**
   * 토큰 만료 여부 확인
   */
  isTokenExpired(): boolean {
    const expiryStr = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    if (!expiryStr) return true;
    
    const expiry = parseInt(expiryStr);
    // 5분 여유를 두고 만료 판단 (자동 갱신을 위해)
    return Date.now() >= (expiry - 5 * 60 * 1000);
  }

  /**
   * 토큰이 곧 만료되는지 확인 (1분 이내)
   */
  isTokenExpiringSoon(): boolean {
    const expiryStr = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    if (!expiryStr) return true;
    
    const expiry = parseInt(expiryStr);
    return Date.now() >= (expiry - 1 * 60 * 1000);
  }

  /**
   * 토큰 존재 여부 확인
   */
  hasTokens(): boolean {
    return !!(this.getAccessToken() && this.getRefreshToken());
  }

  /**
   * 유효한 Access Token 여부 확인
   */
  hasValidAccessToken(): boolean {
    return !!(this.getAccessToken() && !this.isTokenExpired());
  }

  /**
   * 모든 토큰 및 사용자 정보 삭제
   */
  clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  /**
   * Authorization 헤더 값 생성
   */
  getAuthHeader(): string | null {
    const token = this.getAccessToken();
    return token ? `Bearer ${token}` : null;
  }

  /**
   * 토큰 정보 요약
   */
  getTokenInfo(): {
    hasTokens: boolean;
    hasValidAccessToken: boolean;
    isExpired: boolean;
    isExpiringSoon: boolean;
    expiryTime: Date | null;
  } {
    const expiryStr = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    const expiryTime = expiryStr ? new Date(parseInt(expiryStr)) : null;

    return {
      hasTokens: this.hasTokens(),
      hasValidAccessToken: this.hasValidAccessToken(),
      isExpired: this.isTokenExpired(),
      isExpiringSoon: this.isTokenExpiringSoon(),
      expiryTime,
    };
  }
}

// 싱글톤 인스턴스 생성
export const authTokenManager = new AuthTokenManager();

/**
 * JWT 토큰 디코딩 (클라이언트 사이드 검증용)
 * 보안에 의존하지 말고 디버깅/UI 목적으로만 사용
 */
export function decodeJWT(token: string): any {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

/**
 * 토큰 만료 시간 계산
 */
export function getTokenExpiryDate(token: string): Date | null {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) return null;
  
  return new Date(payload.exp * 1000);
}

/**
 * 개발 환경에서 토큰 정보 로깅
 */
export function logTokenInfo(): void {
  if (import.meta.env.DEV) {
    const info = authTokenManager.getTokenInfo();
    console.group('🔑 Token Info');
    console.log('Has tokens:', info.hasTokens);
    console.log('Has valid access token:', info.hasValidAccessToken);
    console.log('Is expired:', info.isExpired);
    console.log('Is expiring soon:', info.isExpiringSoon);
    console.log('Expiry time:', info.expiryTime?.toLocaleString());
    
    const accessToken = authTokenManager.getAccessToken();
    if (accessToken) {
      const payload = decodeJWT(accessToken);
      console.log('Token payload:', payload);
    }
    console.groupEnd();
  }
}

