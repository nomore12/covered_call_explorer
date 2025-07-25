import React, { useMemo, useState } from 'react';
import {
  Box,
  Text,
  VStack,
  HStack,
  Stack,
  Badge,
  Spinner,
  Alert,
  SimpleGrid,
  Card,
  Table,
  Button,
} from '@chakra-ui/react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useExchangeRateStore } from '@/store/exchangeRateStore';
import {
  useDashboardStore,
  type TransactionData,
  type HoldingData,
} from '@/store/dashboardStore';

const InvestmentAnalysis = () => {
  const { currentRate } = useExchangeRateStore();
  const {
    holdings,
    transactions,
    holdingsLoading: isLoading,
    holdingsError: error,
  } = useDashboardStore();

  // 페이지네이션 상태
  const [rankingDisplayCount, setRankingDisplayCount] = useState(5);
  const [holdingDisplayCount, setHoldingDisplayCount] = useState(5);

  // 디버깅을 위한 콘솔 로그
  console.log('InvestmentAnalysis - 데이터 상태:', {
    holdingsCount: holdings?.length || 0,
    transactionsCount: transactions?.length || 0,
    isLoading,
    error,
    currentRate,
  });

  console.log('Holdings 데이터:', holdings);
  console.log('Transactions 데이터:', transactions);

  // 월별 투자금 추이 계산
  const monthlyInvestmentData = useMemo(() => {
    if (!transactions || transactions.length === 0) {
      console.log('월별 투자금 추이: transactions가 없음');
      return [];
    }

    const monthlyData: {
      [key: string]: {
        invested_krw: number;
        invested_usd: number;
        count: number;
      };
    } = {};

    const buyTransactions = transactions.filter(
      tx => tx.transaction_type === 'BUY'
    );
    console.log('BUY 거래 수:', buyTransactions.length);

    buyTransactions.forEach(tx => {
      const month = new Date(tx.transaction_date).toISOString().slice(0, 7); // YYYY-MM 형태
      if (!monthlyData[month]) {
        monthlyData[month] = { invested_krw: 0, invested_usd: 0, count: 0 };
      }
      monthlyData[month].invested_krw += tx.krw_amount || 0;
      monthlyData[month].invested_usd += tx.total_amount_usd || 0;
      monthlyData[month].count += 1;
    });

    const result = Object.entries(monthlyData)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, data]) => ({
        month: new Date(month + '-01').toLocaleDateString('ko-KR', {
          year: 'numeric',
          month: 'short',
        }),
        invested_krw: Math.round(data.invested_krw),
        invested_usd: Math.round(data.invested_usd),
        count: data.count,
      }));

    console.log('월별 투자금 데이터:', result);
    return result;
  }, [transactions]);

  // 종목별 수익률 랭킹 계산
  const stockRankingData = useMemo(() => {
    return holdings
      .map((holding: HoldingData) => {
        const totalValue = holding.current_value_usd;
        const totalInvested = holding.total_invested_usd;
        const returnRate =
          totalInvested > 0
            ? ((totalValue - totalInvested) / totalInvested) * 100
            : 0;
        const returnAmount = totalValue - totalInvested;

        return {
          ticker: holding.ticker,
          return_rate: returnRate,
          return_amount_usd: returnAmount,
          return_amount_krw: returnAmount * Number(currentRate || 1400),
          current_value_usd: totalValue,
          invested_usd: totalInvested,
        };
      })
      .sort((a, b) => b.return_rate - a.return_rate);
  }, [holdings, currentRate]);

  // 평균 보유 기간 분석
  const holdingPeriodData = useMemo(() => {
    if (
      !holdings ||
      holdings.length === 0 ||
      !transactions ||
      transactions.length === 0
    ) {
      console.log('보유 기간 분석: 데이터가 없음');
      return [];
    }

    const today = new Date();

    const result = holdings
      .map((holding: HoldingData) => {
        // 해당 종목의 첫 매수일 찾기
        const stockTransactions = transactions.filter(
          tx => tx.ticker === holding.ticker && tx.transaction_type === 'BUY'
        );

        if (stockTransactions.length === 0) {
          return {
            ticker: holding.ticker,
            first_buy_date: null,
            holding_days: 0,
            holding_months: 0,
          };
        }

        const firstBuyDate = new Date(
          Math.min(
            ...stockTransactions.map(tx =>
              new Date(tx.transaction_date).getTime()
            )
          )
        );
        const holdingDays = Math.floor(
          (today.getTime() - firstBuyDate.getTime()) / (1000 * 60 * 60 * 24)
        );
        const holdingMonths = Math.round(holdingDays / 30.44); // 평균 월일수

        return {
          ticker: holding.ticker,
          first_buy_date: firstBuyDate.toLocaleDateString('ko-KR'),
          holding_days: holdingDays,
          holding_months: holdingMonths,
        };
      })
      .sort((a, b) => b.holding_days - a.holding_days);

    console.log('보유 기간 데이터:', result);
    return result;
  }, [holdings, transactions]);

  // 로딩 상태
  if (isLoading) {
    return (
      <VStack gap={6} align='stretch'>
        <Text fontSize='xl' fontWeight='bold'>
          투자 분석
        </Text>
        <Box textAlign='center' py={8}>
          <Spinner size='lg' />
          <Text mt={4} color='gray.500'>
            투자 분석 데이터를 불러오는 중...
          </Text>
        </Box>
      </VStack>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <VStack gap={6} align='stretch'>
        <Text fontSize='xl' fontWeight='bold'>
          투자 분석
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

  const COLORS = [
    '#0088FE',
    '#00C49F',
    '#FFBB28',
    '#FF8042',
    '#8884D8',
    '#82CA9D',
  ];

  return (
    <VStack gap={6} align='stretch'>
      <Text fontSize='xl' fontWeight='bold'>
        투자 분석
      </Text>

      {/* 월별 투자금 추이 */}
      <Card.Root>
        <Card.Header>
          <Card.Title>월별 투자금 추이</Card.Title>
        </Card.Header>
        <Card.Body>
          <Box h='300px'>
            <ResponsiveContainer width='100%' height='100%'>
              <ComposedChart data={monthlyInvestmentData}>
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis dataKey='month' fontSize={12} />
                <YAxis
                  yAxisId='left'
                  orientation='left'
                  tickFormatter={value => `₩${Math.round(value / 10000)}만`}
                  domain={[0, 'dataMax']}
                  width={50}
                />
                <YAxis
                  yAxisId='right'
                  orientation='right'
                  tickFormatter={value => `${value}건`}
                  domain={[0, 'dataMax']}
                  width={35}
                />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    name === 'invested_krw'
                      ? `₩${value.toLocaleString()}`
                      : `${value}건`,
                    name === 'invested_krw'
                      ? '월별 투자금 (원화)'
                      : '월별 거래건수',
                  ]}
                  labelStyle={{ color: '#374151' }}
                  contentStyle={{
                    backgroundColor: '#f9fafb',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                  }}
                />
                <Bar
                  yAxisId='left'
                  dataKey='invested_krw'
                  fill='#3b82f6'
                  name='invested_krw'
                  radius={[2, 2, 0, 0]}
                />
                <Line
                  yAxisId='right'
                  type='monotone'
                  dataKey='count'
                  stroke='#ef4444'
                  strokeWidth={3}
                  dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
                  name='count'
                />
              </ComposedChart>
            </ResponsiveContainer>
          </Box>

          {/* Y축 범례 추가 */}
          <Box mt={2} display='flex' justifyContent='space-between' px={4}>
            <HStack>
              <Box w={3} h={3} bg='#3b82f6' borderRadius='sm' />
              <Text fontSize='xs' color='gray.600'>
                월별 투자금 (원화) - 왼쪽 축
              </Text>
            </HStack>
            <HStack>
              <Box w={3} h={3} bg='#ef4444' borderRadius='full' />
              <Text fontSize='xs' color='gray.600'>
                월별 거래건수 - 오른쪽 축
              </Text>
            </HStack>
          </Box>
        </Card.Body>
      </Card.Root>

      <SimpleGrid columns={{ base: 1, lg: 2 }} gap={6}>
        {/* 종목별 수익률 랭킹 */}
        <Card.Root>
          <Card.Header>
            <Card.Title>종목별 수익률 랭킹</Card.Title>
          </Card.Header>
          <Card.Body>
            <Table.Root size='sm'>
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>순위</Table.ColumnHeader>
                  <Table.ColumnHeader>종목</Table.ColumnHeader>
                  <Table.ColumnHeader textAlign='right'>
                    수익률
                  </Table.ColumnHeader>
                  <Table.ColumnHeader textAlign='right'>
                    수익금
                  </Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {stockRankingData
                  .slice(0, rankingDisplayCount)
                  .map((stock, index) => (
                    <Table.Row key={stock.ticker}>
                      <Table.Cell>{index + 1}</Table.Cell>
                      <Table.Cell fontWeight='semibold'>
                        {stock.ticker}
                      </Table.Cell>
                      <Table.Cell textAlign='right'>
                        <Badge
                          colorScheme={stock.return_rate >= 0 ? 'green' : 'red'}
                          size='sm'
                        >
                          {stock.return_rate >= 0 ? '+' : ''}
                          {stock.return_rate.toFixed(2)}%
                        </Badge>
                      </Table.Cell>
                      <Table.Cell textAlign='right'>
                        <VStack gap={0} align='end'>
                          <Text
                            fontSize='sm'
                            fontWeight='semibold'
                            color={
                              stock.return_amount_usd >= 0
                                ? 'green.600'
                                : 'red.600'
                            }
                          >
                            {stock.return_amount_usd >= 0 ? '+' : ''}$
                            {stock.return_amount_usd.toLocaleString('en-US', {
                              minimumFractionDigits: 0,
                              maximumFractionDigits: 0,
                            })}
                          </Text>
                          <Text
                            fontSize='xs'
                            color={
                              stock.return_amount_usd >= 0
                                ? 'green.500'
                                : 'red.500'
                            }
                          >
                            {stock.return_amount_usd >= 0 ? '+' : ''}₩
                            {stock.return_amount_krw.toLocaleString('ko-KR', {
                              minimumFractionDigits: 0,
                              maximumFractionDigits: 0,
                            })}
                          </Text>
                        </VStack>
                      </Table.Cell>
                    </Table.Row>
                  ))}
              </Table.Body>
            </Table.Root>
            {stockRankingData.length > rankingDisplayCount && (
              <Box textAlign='center' mt={4}>
                <Button
                  size='sm'
                  variant='outline'
                  onClick={() => setRankingDisplayCount(prev => prev + 5)}
                >
                  더보기 ({stockRankingData.length - rankingDisplayCount}개
                  남음)
                </Button>
              </Box>
            )}
          </Card.Body>
        </Card.Root>

        {/* 평균 보유 기간 */}
        <Card.Root>
          <Card.Header>
            <Card.Title>보유 기간 분석</Card.Title>
          </Card.Header>
          <Card.Body>
            <Table.Root size='sm'>
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>종목</Table.ColumnHeader>
                  <Table.ColumnHeader>첫 매수일</Table.ColumnHeader>
                  <Table.ColumnHeader textAlign='right'>
                    보유 기간
                  </Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {holdingPeriodData.slice(0, holdingDisplayCount).map(stock => (
                  <Table.Row key={stock.ticker}>
                    <Table.Cell fontWeight='semibold'>
                      {stock.ticker}
                    </Table.Cell>
                    <Table.Cell fontSize='sm' color='gray.600'>
                      {stock.first_buy_date || '-'}
                    </Table.Cell>
                    <Table.Cell textAlign='right'>
                      <VStack gap={0} align='end'>
                        <Text fontSize='sm' fontWeight='semibold'>
                          {stock.holding_months}개월
                        </Text>
                        <Text fontSize='xs' color='gray.500'>
                          ({stock.holding_days}일)
                        </Text>
                      </VStack>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
            {holdingPeriodData.length > holdingDisplayCount && (
              <Box textAlign='center' mt={4}>
                <Button
                  size='sm'
                  variant='outline'
                  onClick={() => setHoldingDisplayCount(prev => prev + 5)}
                >
                  더보기 ({holdingPeriodData.length - holdingDisplayCount}개
                  남음)
                </Button>
              </Box>
            )}
          </Card.Body>
        </Card.Root>
      </SimpleGrid>

      {/* 투자 요약 통계 */}
      <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
        <Card.Root>
          <Card.Body textAlign='center'>
            <Text fontSize='sm' color='gray.600'>
              총 투자 종목
            </Text>
            <Text fontSize='2xl' fontWeight='bold' color='blue.600'>
              {holdings.length}개
            </Text>
          </Card.Body>
        </Card.Root>

        <Card.Root>
          <Card.Body textAlign='center'>
            <Text fontSize='sm' color='gray.600'>
              총 거래 횟수
            </Text>
            <Text fontSize='2xl' fontWeight='bold' color='green.600'>
              {transactions.filter(tx => tx.transaction_type === 'BUY').length}
              회
            </Text>
          </Card.Body>
        </Card.Root>

        <Card.Root>
          <Card.Body textAlign='center'>
            <Text fontSize='sm' color='gray.600'>
              평균 보유 기간
            </Text>
            <Text fontSize='2xl' fontWeight='bold' color='purple.600'>
              {holdingPeriodData.length > 0
                ? Math.round(
                    holdingPeriodData.reduce(
                      (sum, stock) => sum + stock.holding_months,
                      0
                    ) / holdingPeriodData.length
                  )
                : 0}
              개월
            </Text>
          </Card.Body>
        </Card.Root>

        <Card.Root>
          <Card.Body textAlign='center'>
            <Text fontSize='sm' color='gray.600'>
              최고 수익률
            </Text>
            <Text fontSize='2xl' fontWeight='bold' color='red.600'>
              {stockRankingData.length > 0
                ? `${stockRankingData[0].return_rate >= 0 ? '+' : ''}${stockRankingData[0].return_rate.toFixed(1)}%`
                : '0%'}
            </Text>
          </Card.Body>
        </Card.Root>
      </SimpleGrid>
    </VStack>
  );
};

export default InvestmentAnalysis;
