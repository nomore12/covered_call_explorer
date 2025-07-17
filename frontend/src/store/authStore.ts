import { create } from 'zustand';
import { apiClient } from '../lib/api';
import { authTokenManager, logTokenInfo } from '../lib/auth';
import type { TokenResponse, RefreshTokenResponse } from '../lib/auth';

interface User {
  id: number;
  username: string;
  email: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean | null; // null = 확인 중, true = 인증됨, false = 미인증
  isLoading: boolean;
  error: string | null;
  tokenInfo: {
    hasTokens: boolean;
    hasValidAccessToken: boolean;
    isExpired: boolean;
    isExpiringSoon: boolean;
    expiryTime: Date | null;
  } | null;

  // Actions
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  clearError: () => void;
  updateTokenInfo: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: null, // 초기 상태는 null (확인 중)
  isLoading: false,
  error: null,
  tokenInfo: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });

    try {
      const response = await apiClient.post('/auth/login', {
        username,
        password,
      });

      const data: { success: boolean } & TokenResponse = response.data;

      if (data.success) {
        // JWT 토큰 저장
        authTokenManager.setTokens({
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          expires_in: data.expires_in,
          user: data.user,
        });

        // 상태 업데이트
        set({
          user: data.user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
          tokenInfo: authTokenManager.getTokenInfo(),
        });

        // 개발 환경에서 토큰 정보 로깅
        if (import.meta.env.DEV) {
          logTokenInfo();
        }
      } else {
        throw new Error(data.success || '로그인에 실패했습니다.');
      }
    } catch (error: any) {
      // 토큰 정리
      authTokenManager.clearTokens();

      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error:
          error.response?.data?.error ||
          error.message ||
          '로그인 중 오류가 발생했습니다.',
        tokenInfo: null,
      });
      throw error;
    }
  },

  refreshToken: async (): Promise<boolean> => {
    const refreshToken = authTokenManager.getRefreshToken();
    if (!refreshToken) {
      return false;
    }

    try {
      const response = await apiClient.post('/auth/refresh', {
        refresh_token: refreshToken,
      });

      const data: { success: boolean } & RefreshTokenResponse = response.data;

      if (data.success) {
        // Access Token 업데이트
        authTokenManager.updateAccessToken({
          access_token: data.access_token,
          expires_in: data.expires_in,
          user: data.user,
        });

        // 상태 업데이트
        set({
          user: data.user,
          isAuthenticated: true,
          tokenInfo: authTokenManager.getTokenInfo(),
        });

        return true;
      } else {
        throw new Error('토큰 갱신에 실패했습니다.');
      }
    } catch (error) {
      console.error('토큰 갱신 실패:', error);

      // 갱신 실패 시 모든 토큰 정리
      authTokenManager.clearTokens();
      set({
        user: null,
        isAuthenticated: false,
        tokenInfo: null,
      });

      return false;
    }
  },

  logout: async () => {
    set({ isLoading: true });

    try {
      const refreshToken = authTokenManager.getRefreshToken();

      // 서버에 로그아웃 요청 (Refresh Token 무효화)
      await apiClient.post('/auth/logout', {
        refresh_token: refreshToken,
      });
    } catch (error) {
      console.error('로그아웃 중 오류:', error);
    } finally {
      // 로컬 토큰 정리
      authTokenManager.clearTokens();

      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        tokenInfo: null,
      });
    }
  },

  checkAuth: async () => {
    console.log('🔄 checkAuth 시작');
    set({ isLoading: true });

    try {
      // 저장된 토큰 확인
      const hasTokens = authTokenManager.hasTokens();
      const isExpired = authTokenManager.isTokenExpired();
      const user = authTokenManager.getUser();
      
      console.log('🔍 토큰 상태:', { hasTokens, isExpired, user });

      if (!hasTokens) {
        console.log('❌ 로컬 토큰 없음 - 로그인 필요');
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          tokenInfo: null,
        });
        return;
      }

      if (isExpired) {
        console.log('⏰ 토큰 만료 - 갱신 필요');
        // 토큰 갱신은 API 인터셉터에서 자동으로 처리하므로 여기서는 하지 않음
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          tokenInfo: null,
        });
        return;
      }

      // 토큰이 유효하면 인증 상태로 설정
      console.log('✅ 유효한 토큰 존재 - 인증 상태로 설정');
      set({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        tokenInfo: authTokenManager.getTokenInfo(),
      });
    } catch (error) {
      console.error('❌ checkAuth 오류:', error);
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        tokenInfo: null,
      });
    }
  },

  updateTokenInfo: () => {
    set({
      tokenInfo: authTokenManager.getTokenInfo(),
    });
  },

  clearError: () => {
    set({ error: null });
  },
}));
