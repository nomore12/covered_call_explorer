import { useState, useEffect } from 'react';
import { Chart, useChart } from '@chakra-ui/charts';
import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts';
import {
  Box,
  Text,
  VStack,
  HStack,
  Badge,
  Spinner,
  Alert,
} from '@chakra-ui/react';
import { apiClient, API_ENDPOINTS } from '../../lib/api';
import { useExchangeRateStore } from '@/store/exchangeRateStore';

interface HoldingData {
  holdings: {
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
  }[];
  price_updates: {
    ticker: string;
    old_price: number;
    new_price: number;
    source: string;
  };
  last_updated: string;
}

const Portfolio = () => {
  const [holdings, setHoldings] = useState<HoldingData>({
    holdings: [],
    price_updates: {
      ticker: '',
      old_price: 0,
      new_price: 0,
      source: '',
    },
    last_updated: '',
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { currentRate } = useExchangeRateStore();

  // 보유 종목 데이터 가져오기
  useEffect(() => {
    const fetchHoldings = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await apiClient.get(API_ENDPOINTS.holdings);
        setHoldings(response.data);
        console.log(response.data);
      } catch (err) {
        console.error('보유 종목 데이터 가져오기 실패:', err);
        setError('보유 종목 데이터를 불러오는데 실패했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHoldings();
  }, []);
  // 홀딩 데이터를 차트용 데이터로 변환
  const chartData = holdings.holdings.map((holding, index) => ({
    name: holding.ticker,
    value: holding.current_value_usd,
    color: [
      'blue.solid',
      'orange.solid',
      'green.solid',
      'purple.solid',
      'teal.solid',
      'red.solid',
    ][index % 6],
  }));

  const chart = useChart({
    data: chartData
      ? chartData
      : [{ name: 'none', value: 100, color: 'blue.solid' }],
  });

  // 포트폴리오 총 가치 계산
  const totalValueUSD =
    holdings &&
    holdings.holdings.reduce(
      (sum, holding) => sum + holding.current_value_usd,
      0
    );
  const totalValueKRW = holdings.holdings.reduce(
    (sum, holding) => sum + holding.current_value_krw,
    0
  );

  // 총 투자 금액
  const totalInvestedUSD = holdings.holdings.reduce(
    (sum, holding) => sum + holding.total_invested_usd,
    0
  );
  const totalInvestedKRW = holdings.holdings.reduce(
    (sum, holding) => sum + holding.total_invested_krw,
    0
  );

  // 총 손익
  const totalPnlUSD = holdings.holdings.reduce(
    (sum, holding) => sum + holding.unrealized_pnl_usd,
    0
  );
  const totalPnlKRW = holdings.holdings.reduce(
    (sum, holding) => sum + holding.unrealized_pnl_krw,
    0
  );

  // 총 수익률
  const totalReturnRateUSD =
    totalInvestedUSD > 0 ? (totalPnlUSD / totalInvestedUSD) * 100 : 0;
  const totalReturnRateKRW =
    totalInvestedKRW > 0 ? (totalPnlKRW / totalInvestedKRW) * 100 : 0;

  // 로딩 상태 렌더링
  if (isLoading) {
    return (
      <VStack gap={6} align='stretch'>
        <Text fontSize='xl' fontWeight='bold'>
          포트폴리오
        </Text>
        <Box textAlign='center' py={8}>
          <Spinner size='lg' />
          <Text mt={4} color='gray.500'>
            보유 종목 데이터를 불러오는 중...
          </Text>
        </Box>
      </VStack>
    );
  }

  // 에러 상태 렌더링
  if (error) {
    return (
      <VStack gap={6} align='stretch'>
        <Text fontSize='xl' fontWeight='bold'>
          포트폴리오
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

  if (holdings.holdings.length === 0) {
    return (
      <VStack gap={6} align='stretch'>
        <Text fontSize='xl' fontWeight='bold'>
          포트폴리오
        </Text>
        <Box textAlign='center' py={8}>
          <Text fontSize='lg' color='gray.500'>
            보유 중인 종목이 없습니다.
          </Text>
        </Box>
      </VStack>
    );
  }

  return (
    <VStack gap={6} align='stretch'>
      {/* 포트폴리오 요약 */}
      <VStack gap={4} align='stretch'>
        <Text fontSize='xl' fontWeight='bold'>
          포트폴리오 요약
        </Text>

        <HStack gap={4} wrap='wrap'>
          <Box p={4} bg='blue.50' borderRadius='lg' flex={1} minW='250px'>
            <Text fontSize='sm' color='blue.600' fontWeight='medium'>
              총 포트폴리오 가치
            </Text>
            <Text fontSize='2xl' fontWeight='bold' color='blue.700'>
              $
              {totalValueUSD.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
              <Text
                as='span'
                fontSize='sm'
                color={totalReturnRateUSD >= 0 ? 'green.600' : 'red.600'}
                ml={2}
              >
                ({totalReturnRateUSD >= 0 ? '+' : ''}
                {totalReturnRateUSD.toFixed(2)}%)
              </Text>
            </Text>
            <Text fontSize='lg' color='blue.600'>
              ₩
              {(totalValueUSD * Number(currentRate)).toLocaleString('ko-KR', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}
              <Text
                as='span'
                fontSize='sm'
                color={totalReturnRateKRW >= 0 ? 'green.600' : 'red.600'}
                ml={2}
              >
                ({totalReturnRateKRW >= 0 ? '+' : ''}
                {totalReturnRateKRW.toFixed(2)}%)
              </Text>
            </Text>
          </Box>

          <Box
            p={4}
            bg={totalPnlUSD >= 0 ? 'green.50' : 'red.50'}
            borderRadius='lg'
            flex={1}
            minW='250px'
          >
            <Text
              fontSize='sm'
              color={totalPnlUSD >= 0 ? 'green.600' : 'red.600'}
              fontWeight='medium'
            >
              총 손익 (미실현)
            </Text>
            <Text
              fontSize='2xl'
              fontWeight='bold'
              color={totalPnlUSD >= 0 ? 'green.700' : 'red.700'}
            >
              {totalPnlUSD >= 0 ? '+' : ''}$
              {totalPnlUSD.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </Text>
            <Text
              fontSize='lg'
              color={totalPnlKRW >= 0 ? 'green.600' : 'red.600'}
            >
              {totalPnlKRW >= 0 ? '+' : ''}₩
              {totalPnlKRW.toLocaleString('ko-KR', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}
            </Text>
            <HStack>
              <Badge colorScheme={totalReturnRateUSD >= 0 ? 'green' : 'red'}>
                {totalReturnRateUSD >= 0 ? '+' : ''}
                {totalReturnRateUSD.toFixed(2)}% (USD)
              </Badge>
              <Badge colorScheme={totalReturnRateKRW >= 0 ? 'green' : 'red'}>
                {totalReturnRateKRW >= 0 ? '+' : ''}
                {totalReturnRateKRW.toFixed(2)}% (KRW)
              </Badge>
            </HStack>
          </Box>
        </HStack>
      </VStack>

      {/* 포트폴리오 분포 */}
      <Box>
        <Text fontSize='xl' fontWeight='bold' mb={4}>
          포트폴리오 분포
        </Text>

        <HStack gap={8} align='flex-start'>
          {/* 차트 */}
          <Box flex={1}>
            <Chart.Root boxSize='300px' mx='auto' chart={chart}>
              <ResponsiveContainer width='100%' height={300}>
                <PieChart>
                  <Pie
                    isAnimationActive={false}
                    data={chart.data}
                    dataKey={chart.key('value')}
                    cx='50%'
                    cy='50%'
                    outerRadius={100}
                    label={({ name, percent }) =>
                      `${name} ${percent ? (percent * 100).toFixed(0) : 0}%`
                    }
                  >
                    {chart.data.map(item => (
                      <Cell key={item.name} fill={chart.color(item.color)} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </Chart.Root>
          </Box>

          {/* 종목별 상세 정보 */}
          <VStack gap={2} flex={1} align='stretch'>
            {holdings.holdings.map((holding, index) => (
              <HStack
                key={holding.ticker}
                justify='space-between'
                p={3}
                bg='gray.50'
                borderRadius='md'
              >
                <VStack align='flex-start' gap={1}>
                  <HStack>
                    <Box
                      w={3}
                      h={3}
                      borderRadius='full'
                      bg={chart.color(chartData[index]?.color || 'gray.solid')}
                    />
                    <Text fontWeight='bold' fontSize='lg'>
                      {holding.ticker}
                    </Text>
                    <Text>현재가: {holding.current_price}</Text>
                  </HStack>
                  <Text fontSize='sm' color='gray.600'>
                    {holding.total_shares.toFixed(0)}주/내 평균 $
                    {holding.average_price.toFixed(2)}
                  </Text>
                  <Badge
                    colorScheme={holding.return_rate_usd >= 0 ? 'green' : 'red'}
                    size='sm'
                  >
                    {holding.return_rate_usd >= 0 ? '+' : ''}
                    {holding.return_rate_usd.toFixed(2)}%
                  </Badge>
                </VStack>

                <VStack align='flex-end' gap={1}>
                  <Text fontSize='lg' fontWeight='semibold'>
                    $
                    {holding.current_value_usd.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </Text>
                  <Text fontSize='sm' color='gray.500'>
                    ₩
                    {(holding.current_value_usd * Number(currentRate)).toFixed(
                      0
                    )}
                  </Text>
                  <HStack align='flex-end' gap={1}>
                    <Text
                      fontSize='sm'
                      color={
                        holding.unrealized_pnl_usd >= 0
                          ? 'green.600'
                          : 'red.600'
                      }
                      fontWeight='medium'
                    >
                      {holding.unrealized_pnl_usd >= 0 ? '+' : ''}$
                      {holding.unrealized_pnl_usd.toFixed(2)}
                    </Text>
                    <Text
                      pl={1}
                      fontSize='sm'
                      color={
                        holding.unrealized_pnl_usd >= 0
                          ? 'green.600'
                          : 'red.600'
                      }
                      fontWeight='medium'
                    >
                      {holding.unrealized_pnl_usd >= 0 ? '+' : ''}₩
                      {(
                        holding.unrealized_pnl_usd * Number(currentRate)
                      ).toFixed(0)}
                    </Text>
                  </HStack>
                </VStack>
              </HStack>
            ))}
          </VStack>
        </HStack>
      </Box>
    </VStack>
  );
};

export default Portfolio;
