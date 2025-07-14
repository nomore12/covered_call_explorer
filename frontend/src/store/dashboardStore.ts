import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { apiClient, API_ENDPOINTS } from '../lib/api';

// Type definitions - moved exports above

export interface DividendData {
  id: number;
  created_at: string;
  ticker: string;
  amount_usd: number;
  shares?: number;
  dividendPerShare?: number;
  dividend_per_share?: number; // API 전송 시 사용
  payment_date: string;
}

export interface TransactionData {
  id: number;
  ticker: string;
  transaction_type: string;
  shares: number;
  price_per_share: number;
  total_amount_usd: number;
  exchange_rate: number;
  krw_amount: number;
  dividend_reinvestment: number;
  transaction_date: string;
  created_at: string;
}

export interface HoldingData {
  id: number;
  ticker: string;
  total_shares: number;
  total_invested_usd: number;
  total_invested_krw: number;
  average_price: number;
  current_price: number;
  current_value_usd: number;
  current_value_krw: number;
  unrealized_pnl_usd: number;
  unrealized_pnl_krw: number;
  return_rate_usd: number;
  return_rate_krw: number;
  created_at: string;
  updated_at: string;
}

interface PriceUpdate {
  ticker: string;
  old_price: number;
  new_price: number;
  source: string;
  difference: number;
}

interface HoldingsResponse {
  holdings: HoldingData[];
  price_updates: PriceUpdate[];
  last_updated: string;
}

interface PortfolioData {
  total_invested_usd: number;
  total_invested_krw: number;
  total_current_value_usd: number;
  total_current_value_krw: number;
  total_unrealized_pnl_usd: number;
  total_unrealized_pnl_krw: number;
  total_return_rate_usd: number;
  total_return_rate_krw: number;
  total_dividends_usd: number;
  total_dividends_krw: number;
  total_pnl_with_dividends_usd: number;
  total_pnl_with_dividends_krw: number;
  total_return_with_dividends_usd: number;
  total_return_with_dividends_krw: number;
  price_updates: PriceUpdate[];
  last_updated: string;
}

// Dashboard Store State
interface DashboardState {
  // Holdings data
  holdings: HoldingData[];
  holdingsLoading: boolean;
  holdingsError: string | null;
  priceUpdates: PriceUpdate[];
  holdingsLastUpdated: string | null;

  // Portfolio summary
  portfolio: PortfolioData | null;
  portfolioLoading: boolean;
  portfolioError: string | null;

  // Transactions
  transactions: TransactionData[];
  transactionsLoading: boolean;
  transactionsError: string | null;

  // Dividends
  dividends: DividendData[];
  dividendsLoading: boolean;
  dividendsError: string | null;

  // Global loading state
  isInitialized: boolean;

  // Actions
  fetchHoldings: () => Promise<void>;
  fetchPortfolio: () => Promise<void>;
  fetchTransactions: () => Promise<void>;
  fetchDividends: () => Promise<void>;
  fetchAllData: () => Promise<void>;

  // Add new data actions
  addTransaction: (
    transaction: Omit<TransactionData, 'id' | 'created_at'>
  ) => Promise<void>;
  addDividend: (
    dividend: Omit<DividendData, 'id' | 'created_at'>
  ) => Promise<void>;

  // Clear errors
  clearErrors: () => void;
  clearHoldingsError: () => void;
  clearPortfolioError: () => void;
  clearTransactionsError: () => void;
  clearDividendsError: () => void;
}

export const useDashboardStore = create<DashboardState>()(
  devtools(
    (set, get) => ({
      // Initial state
      holdings: [],
      holdingsLoading: false,
      holdingsError: null,
      priceUpdates: [],
      holdingsLastUpdated: null,

      portfolio: null,
      portfolioLoading: false,
      portfolioError: null,

      transactions: [],
      transactionsLoading: false,
      transactionsError: null,

      dividends: [],
      dividendsLoading: false,
      dividendsError: null,

      isInitialized: false,

      // Fetch holdings
      fetchHoldings: async () => {
        try {
          set({ holdingsLoading: true, holdingsError: null });

          const response = await apiClient.get<HoldingsResponse>(
            API_ENDPOINTS.holdings
          );

          set({
            holdings: response.data.holdings,
            priceUpdates: response.data.price_updates,
            holdingsLastUpdated: response.data.last_updated,
            holdingsLoading: false,
            holdingsError: null,
          });
        } catch (error) {
          console.error('Holdings fetch error:', error);
          set({
            holdingsLoading: false,
            holdingsError: '보유 종목 데이터를 불러오는데 실패했습니다.',
          });
        }
      },

      // Fetch portfolio summary
      fetchPortfolio: async () => {
        try {
          set({ portfolioLoading: true, portfolioError: null });

          const response = await apiClient.get<PortfolioData>(
            API_ENDPOINTS.portfolio
          );

          set({
            portfolio: response.data,
            portfolioLoading: false,
            portfolioError: null,
          });
        } catch (error) {
          console.error('Portfolio fetch error:', error);
          set({
            portfolioLoading: false,
            portfolioError: '포트폴리오 데이터를 불러오는데 실패했습니다.',
          });
        }
      },

      // Fetch transactions
      fetchTransactions: async () => {
        try {
          set({ transactionsLoading: true, transactionsError: null });

          const response = await apiClient.get<TransactionData[]>(
            API_ENDPOINTS.transactions
          );

          set({
            transactions: response.data,
            transactionsLoading: false,
            transactionsError: null,
          });
        } catch (error) {
          console.error('Transactions fetch error:', error);
          set({
            transactionsLoading: false,
            transactionsError: '거래 데이터를 불러오는데 실패했습니다.',
          });
        }
      },

      // Fetch dividends
      fetchDividends: async () => {
        try {
          set({ dividendsLoading: true, dividendsError: null });

          const response = await apiClient.get<DividendData[]>(
            API_ENDPOINTS.dividends
          );

          // Normalize dividend data
          const normalizedData = Array.isArray(response.data)
            ? response.data.map((item: any) => ({
                id: item.id || Date.now() + Math.random(),
                created_at:
                  item.created_at || new Date().toISOString().split('T')[0],
                ticker: item.ticker || 'UNKNOWN',
                amount_usd:
                  typeof item.amount_usd === 'number' ? item.amount_usd : 0,
                shares:
                  typeof item.shares === 'number' ? item.shares : undefined,
                dividendPerShare:
                  typeof item.dividend_per_share === 'number'
                    ? item.dividend_per_share
                    : undefined,
                payment_date: item.payment_date || item.created_at || new Date().toISOString().split('T')[0],
              }))
            : [];

          set({
            dividends: normalizedData,
            dividendsLoading: false,
            dividendsError: null,
          });
        } catch (error) {
          console.error('Dividends fetch error:', error);
          set({
            dividends: [],
            dividendsLoading: false,
            dividendsError: '배당금 데이터를 불러오는데 실패했습니다.',
          });
        }
      },

      // Fetch all data at once
      fetchAllData: async () => {
        const state = get();

        // Run all fetches in parallel
        await Promise.allSettled([
          state.fetchHoldings(),
          state.fetchPortfolio(),
          state.fetchTransactions(),
          state.fetchDividends(),
        ]);

        set({ isInitialized: true });
      },

      // Add new transaction
      addTransaction: async transactionData => {
        try {
          const response = await apiClient.post(
            API_ENDPOINTS.transactions,
            transactionData
          );

          // Refresh transactions and holdings after adding
          const state = get();
          await Promise.all([
            state.fetchTransactions(),
            state.fetchHoldings(),
            state.fetchPortfolio(),
          ]);
        } catch (error) {
          console.error('Add transaction error:', error);
          throw error;
        }
      },

      // Add new dividend
      addDividend: async dividendData => {
        try {
          const response = await apiClient.post(
            API_ENDPOINTS.dividends,
            dividendData
          );

          // Refresh dividends and portfolio after adding
          const state = get();
          await Promise.all([state.fetchDividends(), state.fetchPortfolio()]);
        } catch (error) {
          console.error('Add dividend error:', error);
          throw error;
        }
      },

      // Clear all errors
      clearErrors: () => {
        set({
          holdingsError: null,
          portfolioError: null,
          transactionsError: null,
          dividendsError: null,
        });
      },

      // Clear specific errors
      clearHoldingsError: () => set({ holdingsError: null }),
      clearPortfolioError: () => set({ portfolioError: null }),
      clearTransactionsError: () => set({ transactionsError: null }),
      clearDividendsError: () => set({ dividendsError: null }),
    }),
    {
      name: 'dashboard-store',
    }
  )
);
