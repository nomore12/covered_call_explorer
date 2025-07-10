// - holdings (보유 종목)
// - transactions (거래 내역)
// - dividends (배당금)
// - portfolio (포트폴리오 요약)
// - priceUpdates (실시간 주가)

import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';
import { apiClient } from '../lib/api';
