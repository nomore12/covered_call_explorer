import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';
import { apiClient } from '../lib/api';

interface ExchangeRate {
  rate_id: number;
  timestamp: string;
  usd_krw: number;
  source: string;
  created_at: string;
}

interface ExchangeRateState {
  // 상태
  currentRate: number | null;
  lastUpdated: string | null;
  isLoading: boolean;
  error: string | null;
  rateHistory: ExchangeRate[];

  // 액션
  fetchCurrentRate: () => Promise<void>;
  updateExchangeRate: () => Promise<void>;
  clearError: () => void;
  setCurrentRate: (rate: number) => void;
}

export const useExchangeRateStore = create<ExchangeRateState>()(
  devtools(
    persist(
      (set, get) => ({
        // 초기 상태
        currentRate: null,
        lastUpdated: null,
        isLoading: false,
        error: null,
        rateHistory: [],

        // 현재 환율 가져오기
        fetchCurrentRate: async () => {
          try {
            set({ isLoading: true, error: null });

            const response = await apiClient.get('/update_exchange_rate', {
              timeout: 30000, // 30초 타임아웃
            });

            if (response.data.success) {
              set({
                currentRate: response.data.new_rate,
                lastUpdated:
                  response.data.timestamp || new Date().toISOString(),
                isLoading: false,
                error: null,
              });
            } else {
              set({
                isLoading: false,
                error:
                  response.data.message ||
                  '환율 정보를 가져오는데 실패했습니다.',
              });
            }
          } catch (error: any) {
            console.error('환율 정보 가져오기 오류:', error);
            
            // 타임아웃 에러 처리
            if (error.code === 'ECONNABORTED') {
              set({
                isLoading: false,
                error: '환율 API 응답 시간 초과 (네트워크 문제)',
              });
            } else {
              set({
                isLoading: false,
                error: '환율 정보를 가져오는데 실패했습니다.',
              });
            }
          }
        },

        // 환율 업데이트
        updateExchangeRate: async () => {
          try {
            set({ isLoading: true, error: null });

            const response = await apiClient.get('/update_exchange_rate');

            if (response.data.success) {
              const { new_rate, old_rate, change, change_pct, timestamp } =
                response.data;

              set({
                currentRate: new_rate,
                lastUpdated: timestamp || new Date().toISOString(),
                isLoading: false,
                error: null,
              });

              // 변화가 있었을 때만 알림 (선택사항)
              if (change !== 0) {
                console.log(
                  `환율 업데이트: ${old_rate} → ${new_rate} (${change > 0 ? '+' : ''}${change.toFixed(2)}원, ${change_pct.toFixed(2)}%)`
                );
              }
            } else {
              set({
                isLoading: false,
                error: response.data.message || '환율 업데이트에 실패했습니다.',
              });
            }
          } catch (error) {
            console.error('환율 업데이트 오류:', error);
            set({
              isLoading: false,
              error: '환율 업데이트에 실패했습니다.',
            });
          }
        },

        // 에러 초기화
        clearError: () => {
          set({ error: null });
        },

        // 현재 환율 수동 설정
        setCurrentRate: (rate: number) => {
          set({
            currentRate: rate,
            lastUpdated: new Date().toISOString(),
          });
        },
      }),
      {
        name: 'exchange-rate-storage', // localStorage 키 이름
        partialize: state => ({
          currentRate: state.currentRate,
          lastUpdated: state.lastUpdated,
          rateHistory: state.rateHistory,
        }),
      }
    ),
    {
      name: 'exchange-rate-store', // Redux DevTools에서 보일 이름
    }
  )
);
