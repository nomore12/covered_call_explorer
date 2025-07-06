import React from 'react';
import { SWRConfig } from 'swr';
import { apiClient } from './api';

// SWR 기본 fetcher 함수
export const fetcher = async (url: string) => {
  const response = await apiClient.get(url);
  return response.data;
};

// SWR 설정 옵션
export const swrConfig = {
  fetcher,
  refreshInterval: 30000, // 30초마다 자동 새로고침
  revalidateOnFocus: true, // 포커스 시 재검증
  revalidateOnReconnect: true, // 재연결 시 재검증
  errorRetryCount: 3, // 에러 시 3번 재시도
  errorRetryInterval: 1000, // 1초 간격으로 재시도
  dedupingInterval: 2000, // 2초 내 중복 요청 제거
  onError: (error: any) => {
    // 에러 발생 시 로깅
    console.error('SWR Error:', error);
    
    // 개발 환경에서는 더 자세한 에러 정보 출력
    if (import.meta.env.DEV) {
      console.error('Error details:', {
        url: error.config?.url,
        status: error.response?.status,
        data: error.response?.data,
      });
    }
  },
  onSuccess: (data: any, key: string) => {
    // 성공 시 로깅 (개발 환경에서만)
    if (import.meta.env.DEV) {
      console.log('SWR Success:', key, data);
    }
  },
};

// SWR 설정 컴포넌트
export const SWRProvider = ({ children }: { children: React.ReactNode }) => {
  return <SWRConfig value={swrConfig}>{children}</SWRConfig>;
};