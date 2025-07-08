import { useState, useEffect } from 'react';
import {
  Accordion,
  Span,
  Box,
  Text,
  HStack,
  VStack,
  Spinner,
  Alert,
} from '@chakra-ui/react';
import { apiClient, API_ENDPOINTS } from '../../lib/api';

// 종목별 컬러 팔레트 - Chakra UI 색상 + 헥스 컬러 (총 30개) - 무작위 순서
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

interface TransactionData {
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

const TradeHistory = () => {
  const [tradeItems, setTradeItems] = useState<TransactionData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 종목별 컬러 매핑 함수
  const getTickerColor = (ticker: string, index: number): string => {
    // 간단하고 안정적인 해시 알고리즘
    let hash = 0;
    for (let i = 0; i < ticker.length; i++) {
      hash = ((hash << 5) - hash + ticker.charCodeAt(i)) >>> 0;
    }
    return TICKER_COLORS[hash % TICKER_COLORS.length];
  };

  // 거래 데이터 가져오기
  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await apiClient.get(API_ENDPOINTS.transactions);
        setTradeItems(response.data);
      } catch (err) {
        console.error('거래 데이터 가져오기 실패:', err);
        setError('거래 데이터를 불러오는데 실패했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchTransactions();
  }, []);

  // 날짜 순서대로 정렬 (최신순) - API에서 이미 정렬되어 오지만 안전하게 재정렬
  const sortedItems = tradeItems.sort(
    (a, b) =>
      new Date(b.transaction_date).getTime() -
      new Date(a.transaction_date).getTime()
  );

  // 로딩 상태 렌더링
  if (isLoading) {
    return (
      <VStack gap={4} align='stretch'>
        <Text fontSize='xl' fontWeight='bold' mb={4}>
          거래 내역
        </Text>
        <Box textAlign='center' py={8}>
          <Spinner size='lg' />
          <Text mt={4} color='gray.500'>
            거래 데이터를 불러오는 중...
          </Text>
        </Box>
      </VStack>
    );
  }

  // 에러 상태 렌더링
  if (error) {
    return (
      <VStack gap={4} align='stretch'>
        <Text fontSize='xl' fontWeight='bold' mb={4}>
          거래 내역
        </Text>
        <Alert.Root status='error'>
          <Alert.Indicator />
          <Alert.Content>
            <Alert.Title>오류 발생</Alert.Title>
            <Alert.Description>{error}</Alert.Description>
          </Alert.Content>
        </Alert.Root>
      </VStack>
    );
  }

  return (
    <VStack gap={4} align='stretch'>
      <Text fontSize='xl' fontWeight='bold' mb={4}>
        거래 내역
      </Text>

      <Accordion.Root collapsible defaultValue={[]}>
        {sortedItems.map((item, index) => (
          <Accordion.Item key={item.id} value={`trade-${item.id}`}>
            <Accordion.ItemTrigger>
              <HStack justify='space-between' w='100%'>
                <HStack gap={4}>
                  <Span fontSize='sm' color='gray.600' minW='100px'>
                    {item.transaction_date}
                  </Span>
                  <Span
                    fontWeight='semibold'
                    minW='60px'
                    color={getTickerColor(item.ticker, index)}
                  >
                    {item.ticker}
                  </Span>
                  <Span fontSize='sm' minW='60px'>
                    {item.shares}주{' '}
                    <Span fontSize='xs' color='gray.500'>
                      (${item.price_per_share.toFixed(2)})
                    </Span>
                  </Span>
                  <Span fontWeight='medium' color='blue.600'>
                    ${item.total_amount_usd.toLocaleString()}
                  </Span>
                  <Span fontWeight='medium' color='gray.500'>
                    ₩{item.krw_amount.toLocaleString()}
                  </Span>
                  {item.dividend_reinvestment > 0 && (
                    <Span
                      fontSize='xs'
                      color='green.600'
                      bg='green.50'
                      px={2}
                      py={1}
                      borderRadius='md'
                    >
                      배당금 재투자
                    </Span>
                  )}
                </HStack>
                <Accordion.ItemIndicator />
              </HStack>
            </Accordion.ItemTrigger>
            <Accordion.ItemContent>
              <Accordion.ItemBody>
                <HStack
                  gap={8}
                  p={4}
                  bg='gray.50'
                  borderRadius='md'
                  align='stretch'
                  h='100%'
                >
                  {/* 구매 내역 섹션 */}
                  <Box flex={1}>
                    <Text
                      fontSize='md'
                      fontWeight='bold'
                      color='blue.700'
                      mb={3}
                    >
                      구매 내역
                    </Text>
                    <VStack gap={2} align='stretch'>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          1주 당 가격:
                        </Text>
                        <HStack gap={2}>
                          <Text fontSize='md' fontWeight='semibold'>
                            ${item.price_per_share.toFixed(2)}
                          </Text>
                          <Text fontSize='sm' color='gray.500'>
                            ₩
                            {(
                              item.price_per_share *
                              (item.exchange_rate || 1400)
                            ).toLocaleString()}
                          </Text>
                        </HStack>
                      </HStack>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          기준 환율:
                        </Text>
                        <Text fontSize='sm'>
                          ₩{(item.exchange_rate || 1400).toLocaleString()}
                        </Text>
                      </HStack>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          수량:
                        </Text>
                        <Text fontSize='sm'>{item.shares}주</Text>
                      </HStack>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          총 구매금액:
                        </Text>
                        <HStack gap={2}>
                          <Text fontSize='md' fontWeight='semibold'>
                            ${item.total_amount_usd.toLocaleString()}
                          </Text>
                          <Text fontSize='sm' color='gray.500'>
                            ₩
                            {(
                              item.total_amount_usd *
                              (item.exchange_rate || 1400)
                            ).toLocaleString()}
                          </Text>
                        </HStack>
                      </HStack>
                    </VStack>
                  </Box>

                  {/* 세로 구분선 */}
                  <Box w='1px' bg='gray.300' />

                  {/* 달러 환전 내역 섹션 */}
                  <Box flex={1}>
                    <Text
                      fontSize='md'
                      fontWeight='bold'
                      color='green.700'
                      mb={3}
                    >
                      달러 환전 내역
                    </Text>
                    <VStack gap={2} align='stretch'>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          주문 중 환전한 달러:
                        </Text>
                        <Text fontSize='md' fontWeight='semibold'>
                          $
                          {item.dividend_reinvestment > 0
                            ? (
                                item.total_amount_usd -
                                item.dividend_reinvestment
                              ).toLocaleString()
                            : item.total_amount_usd.toLocaleString()}
                        </Text>
                      </HStack>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          적용환율:
                        </Text>
                        <Text fontSize='sm'>
                          ₩{(item.exchange_rate || 1400).toLocaleString()}
                        </Text>
                      </HStack>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          사용한 원화:
                        </Text>
                        <Text fontSize='md' fontWeight='semibold'>
                          ₩{(item.krw_amount || 0).toLocaleString()}
                        </Text>
                      </HStack>
                    </VStack>
                  </Box>
                </HStack>
              </Accordion.ItemBody>
            </Accordion.ItemContent>
          </Accordion.Item>
        ))}
      </Accordion.Root>
    </VStack>
  );
};

export default TradeHistory;
