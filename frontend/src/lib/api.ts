import axios from 'axios';

// API 기본 설정
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (process.env.NODE_ENV === 'production' 
    ? '/api'  // 프로덕션에서는 nginx 프록시 사용
    : 'http://localhost:5000');  // 개발 환경에서는 직접 Flask 서버 호출

// Axios 인스턴스 생성
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    // 요청 전에 로깅 (개발 환경에서만)
    if (process.env.NODE_ENV === 'development' && import.meta.env.VITE_ENABLE_API_LOGS !== 'false') {
      console.log('API Request:', config.method?.toUpperCase(), config.url);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => {
    // 응답 성공 시 로깅 (개발 환경에서만)
    if (process.env.NODE_ENV === 'development' && import.meta.env.VITE_ENABLE_API_LOGS !== 'false') {
      console.log('API Response:', response.status, response.config.url);
    }
    return response;
  },
  (error) => {
    // 에러 처리
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', error.response?.status, error.response?.data);
    }
    
    // 공통 에러 처리
    if (error.response?.status === 401) {
      // 인증 실패 시 로그인 페이지로 리다이렉트
      window.location.href = '/login';
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