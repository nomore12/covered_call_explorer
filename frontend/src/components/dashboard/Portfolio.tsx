import { Chart, useChart } from '@chakra-ui/charts';
import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts';
import {
  Box,
  Text,
  VStack,
  HStack,
  Stack,
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

  // ① 이미 계산된 미실현 손익
  const totalUnrealizedPnlUSD = holdings.reduce(
    (sum, h) => sum + h.unrealized_pnl_usd,
    0
  );

  // ② 이미 계산된 배당 합계
  const totalDividendsUSD = dividends.reduce((sum, d) => sum + d.amount_usd, 0);

  // ③ “미실현 손익 + 배당” → 총 손익 (USD·KRW)
  const totalNetPnlUSD = totalUnrealizedPnlUSD + totalDividendsUSD;
  const totalNetPnlKRW = totalNetPnlUSD * Number(currentRate || 1400);

  // ④ “투입 원금” 대비 총 수익률
  const totalNetReturnRateUSD =
    totalInvestedUSD > 0 ? (totalNetPnlUSD / totalInvestedUSD) * 100 : 0;
  const totalNetReturnRateKRW =
    totalInvestedKRW > 0 ? (totalNetPnlKRW / totalInvestedKRW) * 100 : 0;

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
        <Stack 
          direction={{ base: 'column', lg: 'row' }} 
          gap={4} 
          align='stretch'
        >
          <Box 
            p={4} 
            bg='blue.50' 
            borderRadius='lg' 
            flex={1} 
            minW={{ base: 'auto', md: '250px' }}
          >
            <Text fontSize='sm' color='blue.600' fontWeight='medium'>
              총 포트폴리오 가치 (보유 + 총 수익)
            </Text>
            <Text 
              fontSize={{ base: 'xl', md: '2xl' }} 
              fontWeight='bold' 
              color='blue.700'
            >
              $
              {(totalValueUSD + totalAllDividendsUSD).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
              <Text
                as='span'
                fontSize='sm'
                color={
                  totalCombinedReturnRateUSD >= 0 ? 'green.600' : 'red.600'
                }
                ml={2}
              >
                ({totalCombinedReturnRateUSD >= 0 ? '+' : ''}
                {totalCombinedReturnRateUSD.toFixed(2)}%)
              </Text>
            </Text>
            <Text fontSize={{ base: 'md', md: 'lg' }} color='blue.600'>
              ₩
              {(
                (totalValueUSD + totalAllDividendsUSD) *
                Number(currentRate || 1400)
              ).toLocaleString('ko-KR', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}
              <Text
                as='span'
                fontSize='sm'
                color={
                  totalCombinedReturnRateKRW >= 0 ? 'green.600' : 'red.600'
                }
                ml={2}
              >
                ({totalCombinedReturnRateKRW >= 0 ? '+' : ''}
                {totalCombinedReturnRateKRW.toFixed(2)}%)
              </Text>
            </Text>
            <Text fontSize='xs' color='blue.500' mt={1}>
              현재 보유가치: $
              {totalValueUSD.toLocaleString('en-US', {
                maximumFractionDigits: 0,
              })}{' '}
              + 받은 배당금: $
              {totalAllDividendsUSD.toLocaleString('en-US', {
                maximumFractionDigits: 0,
              })}
            </Text>
          </Box>

          <Box 
            p={4} 
            bg='gray.50' 
            borderRadius='lg' 
            flex={1} 
            minW={{ base: 'auto', lg: '400px' }}
          >
            <Stack 
              direction={{ base: 'column', md: 'row' }} 
              gap={{ base: 4, md: 6 }} 
              align='stretch' 
              h='100%'
            >
              {/* 총 손익 */}
              <Box
                flex={1}
                p={3}
                bg={totalNetPnlUSD >= 0 ? 'green.50' : 'red.50'}
                borderRadius='md'
              >
                <Text
                  fontSize='sm'
                  color={totalNetPnlUSD >= 0 ? 'green.600' : 'red.600'}
                  fontWeight='medium'
                  mb={2}
                >
                  총 손익 (미실현 + 배당)
                </Text>

                {/* USD 기준 손익 */}
                <Text
                  fontSize={{ base: 'lg', md: 'xl' }}
                  fontWeight='bold'
                  color={totalNetPnlUSD >= 0 ? 'green.700' : 'red.700'}
                >
                  {totalNetPnlUSD >= 0 ? '+' : ''}$
                  {totalNetPnlUSD.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </Text>

                {/* KRW 기준 손익 */}
                <Text
                  fontSize='md'
                  color={totalNetPnlKRW >= 0 ? 'green.600' : 'red.600'}
                  mb={2}
                >
                  {totalNetPnlKRW >= 0 ? '+' : ''}₩
                  {totalNetPnlKRW.toLocaleString('ko-KR', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                  })}
                </Text>

                {/* 손익률 뱃지 */}
                <Stack direction={{ base: 'column', sm: 'row' }} gap={1}>
                  <Badge
                    colorScheme={totalNetReturnRateUSD >= 0 ? 'green' : 'red'}
                    size='sm'
                  >
                    {totalNetReturnRateUSD >= 0 ? '+' : ''}
                    {totalNetReturnRateUSD.toFixed(2)}% (USD)
                  </Badge>
                  <Badge
                    colorScheme={totalNetReturnRateKRW >= 0 ? 'green' : 'red'}
                    size='sm'
                  >
                    {totalNetReturnRateKRW >= 0 ? '+' : ''}
                    {totalNetReturnRateKRW.toFixed(2)}% (KRW)
                  </Badge>
                </Stack>
              </Box>

              {/* 구분선 - 데스크톱에서는 세로, 모바일에서는 가로 */}
              <Box 
                w={{ base: '100%', md: '1px' }} 
                h={{ base: '1px', md: 'auto' }} 
                bg='gray.300' 
              />

              {/* 받은 배당금 */}
              <Box flex={1} p={3} bg='blue.50' borderRadius='md'>
                <Text fontSize='sm' color='blue.600' fontWeight='medium' mb={2}>
                  받은 총 배당금
                </Text>
                <Text 
                  fontSize={{ base: 'lg', md: 'xl' }} 
                  fontWeight='bold' 
                  color='blue.700'
                >
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
            </Stack>
          </Box>
        </Stack>
      </VStack>

      {/* 포트폴리오 분포 */}
      <Box>
        <Text fontSize='xl' fontWeight='bold' mb={4}>
          포트폴리오 분포
        </Text>

        <Stack 
          direction={{ base: 'column', lg: 'row' }} 
          gap={8} 
          align='flex-start'
        >
          {/* 차트 */}
          <Box 
            flex={{ base: 'none', lg: 1 }}
            w={{ base: '100%', lg: 'auto' }}
            display='flex'
            justifyContent='center'
          >
            <Chart.Root 
              boxSize={{ base: '280px', md: '300px' }} 
              chart={chart}
            >
              <ResponsiveContainer width='100%' height='100%'>
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
          <VStack 
            gap={2} 
            flex={{ base: 'none', lg: 1 }} 
            align='stretch'
            w={{ base: '100%', lg: 'auto' }}
          >
            {holdings.map((holding: HoldingData, index: number) => {
              const dividendInfo = calculateDividendsForTicker(holding.ticker);

              /* ① 배당까지 합산한 손익·수익률 */
              const netPnlUSD =
                holding.unrealized_pnl_usd + dividendInfo.totalDividendsUSD;
              const netPnlKRW = netPnlUSD * Number(currentRate || 1400);

              const netReturnRateUSD =
                holding.total_invested_usd > 0
                  ? (netPnlUSD / holding.total_invested_usd) * 100
                  : 0;

              const netReturnRateKRW =
                holding.total_invested_krw > 0
                  ? (netPnlKRW / holding.total_invested_krw) * 100
                  : 0;

              return (
                <Stack
                  key={holding.ticker}
                  direction={{ base: 'column', md: 'row' }}
                  justify={{ base: 'flex-start', md: 'space-between' }}
                  p={3}
                  bg='gray.50'
                  borderRadius='md'
                  gap={3}
                >
                  <VStack align='flex-start' gap={1} flex={1}>
                    <Stack 
                      direction={{ base: 'column', sm: 'row' }}
                      align='flex-start'
                      gap={2}
                      w='100%'
                    >
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
                      </HStack>
                      <Text fontSize='sm' color='gray.600'>
                        현재가: {holding.current_price}
                      </Text>
                    </Stack>
                    
                    <Text fontSize='sm' color='gray.600'>
                      {holding.total_shares.toFixed(0)}주 / 내 평균 $
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

                    <Box
                      mt={2}
                      pt={2}
                      borderTop='1px solid'
                      borderColor='gray.200'
                      w='100%'
                    >
                      <Text
                        fontSize='xs'
                        color={netPnlUSD >= 0 ? 'green.600' : 'red.600'}
                        fontWeight='medium'
                        mb={1}
                      >
                        총 손익 (미실현 + 배당)
                      </Text>

                      {/* 손익 금액 */}
                      <Stack 
                        direction={{ base: 'column', sm: 'row' }}
                        gap={2}
                        mb={2}
                      >
                        <Text
                          fontSize='sm'
                          fontWeight='semibold'
                          color={netPnlUSD >= 0 ? 'green.700' : 'red.700'}
                        >
                          {netPnlUSD >= 0 ? '+' : ''}$
                          {netPnlUSD.toLocaleString('en-US', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </Text>
                        <Text
                          fontSize='sm'
                          fontWeight='semibold'
                          color={netPnlUSD >= 0 ? 'green.600' : 'red.600'}
                        >
                          {netPnlUSD >= 0 ? '+' : ''}₩
                          {netPnlKRW.toLocaleString('ko-KR', {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 0,
                          })}
                        </Text>
                      </Stack>

                      {/* 손익률 배지 */}
                      <Badge
                        w='fit-content'
                        colorScheme={netReturnRateUSD >= 0 ? 'green' : 'red'}
                        size='sm'
                      >
                        {netReturnRateUSD >= 0 ? '+' : ''}
                        {netReturnRateUSD.toFixed(2)}%
                      </Badge>
                    </Box>
                  </VStack>

                  <VStack 
                    align={{ base: 'flex-start', md: 'flex-end' }}
                    gap={1}
                    minW={{ base: 'auto', md: '150px' }}
                  >
                    <Text 
                      fontSize={{ base: 'md', md: 'lg' }} 
                      fontWeight='semibold'
                    >
                      현재 가치: $
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
                    
                    <Stack 
                      direction={{ base: 'column', sm: 'row' }}
                      align={{ base: 'flex-start', md: 'flex-end' }}
                      gap={1}
                      mt={2}
                    >
                      <Text
                        fontSize='sm'
                        color={
                          holding.unrealized_pnl_usd >= 0
                            ? 'green.600'
                            : 'red.600'
                        }
                        fontWeight='medium'
                      >
                        미실현: {holding.unrealized_pnl_usd >= 0 ? '+' : ''}$
                        {holding.unrealized_pnl_usd.toLocaleString('en-US', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </Text>
                      <Text
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
                    </Stack>

                    {/* 배당금 정보 추가 */}
                    {dividendInfo.totalDividendsUSD > 0 && (
                      <Box
                        mt={2}
                        pt={2}
                        borderTop='1px solid'
                        borderColor='gray.200'
                        w='100%'
                      >
                        <VStack 
                          align={{ base: 'flex-start', md: 'flex-end' }}
                          gap={1}
                        >
                          <Text
                            fontSize='xs'
                            color='gray.500'
                            fontWeight='medium'
                          >
                            받은 배당금 ({dividendInfo.dividendCount}회)
                          </Text>
                          <Stack 
                            direction={{ base: 'column', sm: 'row' }}
                            gap={2}
                          >
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
                          </Stack>
                        </VStack>
                      </Box>
                    )}
                  </VStack>
                </Stack>
              );
            })}
          </VStack>
        </Stack>
      </Box>
    </VStack>
  );
};

export default Portfolio;
