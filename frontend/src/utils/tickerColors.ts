const TICKER_COLORS = [
  'blue.400',
  '#8B5CF6', // violet
  'orange.600',
  '#10B981', // emerald
  'teal.400',
  '#F59E0B', // amber
  'red.400',
  '#06B6D4', // cyan
  'purple.600',
  '#EC4899', // pink
  'green.400',
  '#8B5A2B', // brown
  'cyan.600',
  '#DC2626', // red
  'pink.400',
  '#059669', // emerald
  'yellow.600',
  '#7C3AED', // violet
  'blue.600',
  '#F97316', // orange
  'orange.400',
  '#0EA5E9', // sky
  'teal.600',
  '#84CC16', // lime
  'red.600',
  '#A855F7', // purple
  'purple.400',
  '#22C55E', // green
  'green.600',
  '#EF4444', // red
  'cyan.400',
  '#FBBF24', // amber
  'pink.600',
  '#14B8A6', // teal
  'yellow.400',
  '#6366F1', // indigo
];

// 종목별 컬러 매핑 함수
export const getTickerColor = (ticker: string): string => {
  // 간단하고 안정적인 해시 알고리즘
  let hash = 0;
  for (let i = 0; i < ticker.length; i++) {
    hash = ((hash << 5) - hash + ticker.charCodeAt(i)) >>> 0;
  }
  return TICKER_COLORS[hash % TICKER_COLORS.length];
};
