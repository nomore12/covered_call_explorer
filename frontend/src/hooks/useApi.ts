import useSWR from 'swr';
import { apiClient, API_ENDPOINTS } from '../lib/api';

// 데이터 타입 정의
export interface Holding {
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

export interface Transaction {
  id: number;
  ticker: string;
  transaction_type: 'buy' | 'sell';
  shares: number;
  price_per_share: number;
  total_amount_usd: number;
  exchange_rate: number;
  krw_amount: number;
  dividend_reinvestment: boolean;
  transaction_date: string;
  created_at: string;
}

export interface Dividend {
  id: number;
  ticker: string;
  amount_usd: number;
  amount_krw: number;
  payment_date: string;
  created_at: string;
}

export interface PortfolioSummary {
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
}

// API 훅들
export const useHoldings = () => {
  const { data, error, isLoading, mutate } = useSWR<Holding[]>(
    API_ENDPOINTS.holdings,
    { refreshInterval: 60000 } // 1분마다 새로고침
  );

  return {
    holdings: data,
    error,
    isLoading,
    mutate,
  };
};

export const usePortfolio = () => {
  const { data, error, isLoading, mutate } = useSWR<PortfolioSummary>(
    API_ENDPOINTS.portfolio,
    { refreshInterval: 60000 }
  );

  return {
    portfolio: data,
    error,
    isLoading,
    mutate,
  };
};

export const useTransactions = () => {
  const { data, error, isLoading, mutate } = useSWR<Transaction[]>(
    API_ENDPOINTS.transactions,
    { refreshInterval: 300000 } // 5분마다 새로고침
  );

  return {
    transactions: data,
    error,
    isLoading,
    mutate,
  };
};

export const useDividends = () => {
  const { data, error, isLoading, mutate } = useSWR<Dividend[]>(
    API_ENDPOINTS.dividends,
    { refreshInterval: 300000 }
  );

  return {
    dividends: data,
    error,
    isLoading,
    mutate,
  };
};

// 특정 종목의 상세 정보 조회
export const useHolding = (ticker: string) => {
  const { data, error, isLoading, mutate } = useSWR<Holding>(
    ticker ? `${API_ENDPOINTS.holdings}/${ticker}` : null,
    { refreshInterval: 60000 }
  );

  return {
    holding: data,
    error,
    isLoading,
    mutate,
  };
};

// API 호출 함수들 (POST, PUT, DELETE 등)
export const updatePrice = async (ticker: string, price: number) => {
  try {
    const response = await apiClient.post(API_ENDPOINTS.updatePrice, {
      ticker,
      price,
    });
    return response.data;
  } catch (error) {
    console.error('Failed to update price:', error);
    throw error;
  }
};

export const createTransaction = async (transactionData: {
  ticker: string;
  transaction_type: 'buy' | 'sell';
  shares: number;
  price_per_share: number;
  total_amount_usd: number;
  exchange_rate: number;
  krw_amount: number;
  dividend_reinvestment: boolean;
  transaction_date?: string;
}) => {
  try {
    const response = await apiClient.post(API_ENDPOINTS.transactions, transactionData);
    return response.data;
  } catch (error) {
    console.error('Failed to create transaction:', error);
    throw error;
  }
};

export const createDividend = async (dividendData: {
  ticker: string;
  amount_usd: number;
  amount_krw: number;
  payment_date?: string;
}) => {
  try {
    const response = await apiClient.post(API_ENDPOINTS.dividends, dividendData);
    return response.data;
  } catch (error) {
    console.error('Failed to create dividend:', error);
    throw error;
  }
};