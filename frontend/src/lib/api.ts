import axios from 'axios';
import { authTokenManager } from './auth';

// API 기본 설정
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD
    ? '/api' // 프로덕션에서는 nginx 프록시 사용
    : 'http://localhost:5001'); // 개발 환경에서는 직접 Flask 서버 호출

// Axios 인스턴스 생성
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // JWT 방식에서는 쿠키 대신 Authorization 헤더 사용
});

// 토큰 갱신 중인지 체크하는 플래그
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: string) => void;
  reject: (error: any) => void;
}> = [];

// 실패한 요청들을 처리하는 함수
const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token!);
    }
  });

  failedQueue = [];
};

// 요청 인터셉터
apiClient.interceptors.request.use(
  config => {
    // JWT 토큰을 Authorization 헤더에 추가
    const authHeader = authTokenManager.getAuthHeader();
    if (authHeader) {
      config.headers.Authorization = authHeader;
    }

    // 요청 전에 로깅 (개발 환경에서만)
    if (
      import.meta.env.DEV &&
      import.meta.env.VITE_ENABLE_API_LOGS !== 'false'
    ) {
      // console.log('API Request:', config.method?.toUpperCase(), config.url);
      if (authHeader) {
        // console.log('  Authorization:', authHeader.substring(0, 20) + '...');
      }
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
apiClient.interceptors.response.use(
  response => {
    // 응답 성공 시 로깅 (개발 환경에서만)
    if (
      import.meta.env.DEV &&
      import.meta.env.VITE_ENABLE_API_LOGS !== 'false'
    ) {
      console.log(
        'API Response:',
        response.status,
        response.data,
        response.config.url
      );
    }
    return response;
  },
  async error => {
    const originalRequest = error.config;

    // 에러 처리
    if (import.meta.env.DEV) {
      console.error('API Error:', error.response?.status, error.response?.data);
    }

    // 401 에러 (인증 실패) 처리
    if (error.response?.status === 401 && !originalRequest._retry) {
      console.log('🔒 401 에러 감지:', originalRequest.url);
      
      // 로그인/회원가입/체크 요청은 토큰 갱신하지 않음
      if (
        originalRequest.url?.includes('/auth/login') ||
        originalRequest.url?.includes('/auth/signup') ||
        originalRequest.url?.includes('/auth/refresh') ||
        originalRequest.url?.includes('/auth/check')
      ) {
        console.log('🚫 인증 관련 요청 - 토큰 갱신 생략');
        return Promise.reject(error);
      }

      // 토큰 갱신이 이미 진행 중인 경우
      if (isRefreshing) {
        console.log('⏳ 토큰 갱신 진행 중 - 대기열 추가');
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch(err => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = authTokenManager.getRefreshToken();

      if (!refreshToken) {
        console.log('❌ Refresh Token 없음 - 로그인 필요');
        authTokenManager.clearTokens();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        console.log('🔄 토큰 갱신 시도');
        // 토큰 갱신 시도
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const data = response.data;

        if (data.success) {
          console.log('✅ 토큰 갱신 성공');
          // Access Token 업데이트
          authTokenManager.updateAccessToken({
            access_token: data.access_token,
            expires_in: data.expires_in,
            user: data.user,
          });

          const newToken = data.access_token;

          // 대기 중인 요청들에 새 토큰 제공
          processQueue(null, newToken);

          // 원래 요청 재시도
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return apiClient(originalRequest);
        } else {
          throw new Error('토큰 갱신 실패');
        }
      } catch (refreshError) {
        console.log('❌ 토큰 갱신 실패');
        // 토큰 갱신 실패
        processQueue(refreshError, null);
        authTokenManager.clearTokens();

        // 개발 환경에서만 상세 로그
        if (import.meta.env.DEV) {
          console.error('Token refresh failed:', refreshError);
        }

        // 로그인 페이지로 리다이렉트
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // 기타 에러 처리
    if (error.response?.status === 403) {
      console.error('권한이 없습니다.');
    } else if (error.response?.status >= 500) {
      console.error('서버 오류가 발생했습니다.');
    }

    return Promise.reject(error);
  }
);

// API 엔드포인트 타입 정의
export interface ApiEndpoints {
  // 포트폴리오 관련
  holdings: '/holdings';
  portfolio: '/portfolio';

  // 거래 관련
  transactions: '/transactions';

  // 배당금 관련
  dividends: '/dividends';

  // 상태 관련
  status: '/status';

  // 가격 업데이트
  updatePrice: '/update-price';
}

// API 엔드포인트 상수
export const API_ENDPOINTS: ApiEndpoints = {
  holdings: '/holdings',
  portfolio: '/portfolio',
  transactions: '/transactions',
  dividends: '/dividends',
  status: '/status',
  updatePrice: '/update-price',
};
