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
import { useExchangeRateStore } from '@/store/exchangeRateStore';
import { useDashboardStore, type HoldingData } from '@/store/dashboardStore';

const Portfolio = () => {
  const { currentRate } = useExchangeRateStore();
  const {
    holdings,
    dividends,
    holdingsLoading: isLoading,
    holdingsError: error,
    priceUpdates,
  } = useDashboardStore();
  // 홀딩 데이터를 차트용 데이터로 변환
  const chartData = holdings.map((holding: HoldingData, index: number) => ({
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
    data:
      chartData.length > 0
        ? chartData
        : [{ name: 'none', value: 100, color: 'blue.solid' }],
  });

  // 포트폴리오 총 가치 계산
  const totalValueUSD = holdings.reduce(
    (sum: number, holding: HoldingData) => sum + holding.current_value_usd,
    0
  );
  const totalValueKRW = holdings.reduce(
    (sum: number, holding: HoldingData) => sum + holding.current_value_krw,
    0
  );

  // 총 투자 금액
  const totalInvestedUSD = holdings.reduce(
    (sum: number, holding: HoldingData) => sum + holding.total_invested_usd,
    0
  );
  const totalInvestedKRW = holdings.reduce(
    (sum: number, holding: HoldingData) => sum + holding.total_invested_krw,
    0
  );

  // 총 손익
  const totalPnlUSD = holdings.reduce(
    (sum: number, holding: HoldingData) => sum + holding.unrealized_pnl_usd,
    0
  );
  const totalPnlKRW = holdings.reduce(
    (sum: number, holding: HoldingData) => sum + holding.unrealized_pnl_krw,
    0
  );

  // 총 수익률
  const totalReturnRateUSD =
    totalInvestedUSD > 0 ? (totalPnlUSD / totalInvestedUSD) * 100 : 0;
  const totalReturnRateKRW =
    totalInvestedKRW > 0 ? (totalPnlKRW / totalInvestedKRW) * 100 : 0;

  // 종목별 배당금 계산 함수
  const calculateDividendsForTicker = (ticker: string) => {
    const tickerDividends = dividends.filter(
      dividend => dividend.ticker === ticker
    );
    const totalDividendsUSD = tickerDividends.reduce(
      (sum, dividend) => sum + dividend.amount_usd,
      0
    );
    const totalDividendsKRW = totalDividendsUSD * Number(currentRate || 1400);

    return {
      totalDividendsUSD,
      totalDividendsKRW,
      dividendCount: tickerDividends.length,
    };
  };

  // 전체 배당금 계산
  const totalAllDividendsUSD = dividends.reduce(
    (sum, dividend) => sum + dividend.amount_usd,
    0
  );
  const totalAllDividendsKRW =
    totalAllDividendsUSD * Number(currentRate || 1400);

  // 총 수익 계산 (미실현 손익 + 배당금)
  const totalCombinedPnlUSD = totalPnlUSD + totalAllDividendsUSD;
  const totalCombinedPnlKRW = totalCombinedPnlUSD * Number(currentRate || 1400);
  
  // 총 수익률 계산
  const totalCombinedReturnRateUSD = 
    totalInvestedUSD > 0 ? (totalCombinedPnlUSD / totalInvestedUSD) * 100 : 0;
  const totalCombinedReturnRateKRW = 
    totalInvestedKRW > 0 ? (totalCombinedPnlKRW / totalInvestedKRW) * 100 : 0;

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

  if (holdings.length === 0) {
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
        <HStack gap={4} wrap='wrap'>
          <Box p={4} bg='blue.50' borderRadius='lg' flex={1} minW='250px'>
            <Text fontSize='sm' color='blue.600' fontWeight='medium'>
              총 포트폴리오 가치 (보유 + 총 수익)
            </Text>
            <Text fontSize='2xl' fontWeight='bold' color='blue.700'>
              $
              {(totalValueUSD + totalAllDividendsUSD).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
              <Text
                as='span'
                fontSize='sm'
                color={totalCombinedReturnRateUSD >= 0 ? 'green.600' : 'red.600'}
                ml={2}
              >
                ({totalCombinedReturnRateUSD >= 0 ? '+' : ''}
                {totalCombinedReturnRateUSD.toFixed(2)}%)
              </Text>
            </Text>
            <Text fontSize='lg' color='blue.600'>
              ₩
              {((totalValueUSD + totalAllDividendsUSD) * Number(currentRate || 1400)).toLocaleString('ko-KR', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}
              <Text
                as='span'
                fontSize='sm'
                color={totalCombinedReturnRateKRW >= 0 ? 'green.600' : 'red.600'}
                ml={2}
              >
                ({totalCombinedReturnRateKRW >= 0 ? '+' : ''}
                {totalCombinedReturnRateKRW.toFixed(2)}%)
              </Text>
            </Text>
            <Text fontSize='xs' color='blue.500' mt={1}>
              현재 보유가치: ${totalValueUSD.toLocaleString('en-US', { maximumFractionDigits: 0 })} + 받은 배당금: ${totalAllDividendsUSD.toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </Text>
          </Box>

          <Box p={4} bg='gray.50' borderRadius='lg' flex={1} minW='500px'>
            <HStack gap={6} align='stretch' h='100%'>
              {/* 왼쪽: 미실현 손익 */}
              <Box
                flex={1}
                p={3}
                bg={totalPnlUSD >= 0 ? 'green.50' : 'red.50'}
                borderRadius='md'
              >
                <Text
                  fontSize='sm'
                  color={totalPnlUSD >= 0 ? 'green.600' : 'red.600'}
                  fontWeight='medium'
                  mb={2}
                >
                  총 손익 (미실현)
                </Text>
                <Text
                  fontSize='xl'
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
                  fontSize='md'
                  color={totalPnlKRW >= 0 ? 'green.600' : 'red.600'}
                  mb={2}
                >
                  {totalPnlKRW >= 0 ? '+' : ''}₩
                  {(totalPnlUSD * Number(currentRate)).toLocaleString('ko-KR', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                  })}
                </Text>
                <HStack wrap='wrap' gap={1}>
                  <Badge
                    colorScheme={totalReturnRateUSD >= 0 ? 'green' : 'red'}
                    size='sm'
                  >
                    {totalReturnRateUSD >= 0 ? '+' : ''}
                    {totalReturnRateUSD.toFixed(2)}% (USD)
                  </Badge>
                  <Badge
                    colorScheme={totalReturnRateKRW >= 0 ? 'green' : 'red'}
                    size='sm'
                  >
                    {totalReturnRateKRW >= 0 ? '+' : ''}
                    {totalReturnRateKRW.toFixed(2)}% (KRW)
                  </Badge>
                </HStack>
              </Box>

              {/* 세로 구분선 */}
              <Box w='1px' bg='gray.300' />

              {/* 오른쪽: 받은 배당금 */}
              <Box flex={1} p={3} bg='blue.50' borderRadius='md'>
                <Text fontSize='sm' color='blue.600' fontWeight='medium' mb={2}>
                  받은 총 배당금
                </Text>
                <Text fontSize='xl' fontWeight='bold' color='blue.700'>
                  $
                  {totalAllDividendsUSD.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </Text>
                <Text fontSize='md' color='blue.600' mb={2}>
                  ₩
                  {totalAllDividendsKRW.toLocaleString('ko-KR', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                  })}
                </Text>
                <Badge colorScheme='blue' size='sm'>
                  총 {dividends.length}회 수령
                </Badge>
              </Box>
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
            {holdings.map((holding: HoldingData, index: number) => {
              const dividendInfo = calculateDividendsForTicker(holding.ticker);

              return (
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
                        bg={chart.color(
                          chartData[index]?.color || 'gray.solid'
                        )}
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
                      colorScheme={
                        holding.return_rate_usd >= 0 ? 'green' : 'red'
                      }
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
                      {(
                        holding.current_value_usd * Number(currentRate)
                      ).toLocaleString('ko-KR', {
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0,
                      })}
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
                        {holding.unrealized_pnl_usd.toLocaleString('en-US', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
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
                        ).toLocaleString('ko-KR', {
                          minimumFractionDigits: 0,
                          maximumFractionDigits: 0,
                        })}
                      </Text>
                    </HStack>

                    {/* 배당금 정보 추가 */}
                    {dividendInfo.totalDividendsUSD > 0 && (
                      <Box
                        mt={2}
                        pt={2}
                        borderTop='1px solid'
                        borderColor='gray.200'
                        w='100%'
                      >
                        <VStack align='flex-end' gap={1}>
                          <Text
                            fontSize='xs'
                            color='gray.500'
                            fontWeight='medium'
                          >
                            받은 배당금 ({dividendInfo.dividendCount}회)
                          </Text>
                          <HStack gap={2}>
                            <Text
                              fontSize='sm'
                              color='blue.600'
                              fontWeight='medium'
                            >
                              $
                              {dividendInfo.totalDividendsUSD.toLocaleString(
                                'en-US',
                                {
                                  minimumFractionDigits: 2,
                                  maximumFractionDigits: 2,
                                }
                              )}
                            </Text>
                            <Text
                              fontSize='sm'
                              color='blue.500'
                              fontWeight='medium'
                            >
                              ₩
                              {dividendInfo.totalDividendsKRW.toLocaleString(
                                'ko-KR',
                                {
                                  minimumFractionDigits: 0,
                                  maximumFractionDigits: 0,
                                }
                              )}
                            </Text>
                          </HStack>
                        </VStack>
                      </Box>
                    )}
                  </VStack>
                </HStack>
              );
            })}
          </VStack>
        </HStack>
      </Box>
    </VStack>
  );
};

export default Portfolio;
