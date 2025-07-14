import {
  Box,
  Text,
  VStack,
  HStack,
  Stack,
  Badge,
  Spinner,
  Alert,
  Card,
  Separator,
} from '@chakra-ui/react';
import { useDashboardStore } from '@/store/dashboardStore';
import { useExchangeRateStore } from '@/store/exchangeRateStore';
import { useMemo } from 'react';

interface DividendStats {
  ticker: string;
  totalInvested: number;
  totalDividends: number;
  dividendCount: number;
  monthlyAvg: number;
  annualizedYield: number;
  firstDividendDate: string | null;
  lastDividendDate: string | null;
  monthsActive: number;
}

interface MonthlyDividendTrend {
  ticker: string;
  totalInvested: number;
  months: Array<{
    month: string;
    amount: number;
    yield: number; // 월 배당률 (%)
    yieldChange: number | null; // 배당률 변화 (포인트)
    yieldChangePercent: number | null; // 배당률 변화율 (%)
  }>;
}

const DividendAnalysis = () => {
  const { holdings, dividends, holdingsLoading, dividendsLoading } = useDashboardStore();
  const { currentRate } = useExchangeRateStore();

  // 배당금 통계 계산
  const dividendStats = useMemo(() => {
    const stats: DividendStats[] = [];

    holdings.forEach(holding => {
      const tickerDividends = dividends.filter(d => d.ticker === holding.ticker);
      
      if (tickerDividends.length === 0) return;

      // 날짜 정렬
      const sortedDividends = [...tickerDividends].sort((a, b) => 
        new Date(a.payment_date).getTime() - new Date(b.payment_date).getTime()
      );

      const firstDate = sortedDividends[0]?.payment_date;
      const lastDate = sortedDividends[sortedDividends.length - 1]?.payment_date;
      
      // 활동 개월 수 계산 (첫 달과 마지막 달 포함)
      let monthsActive = 1;
      if (firstDate && lastDate) {
        const firstDateObj = new Date(firstDate);
        const lastDateObj = new Date(lastDate);
        
        // 연도와 월의 차이를 계산
        const yearDiff = lastDateObj.getFullYear() - firstDateObj.getFullYear();
        const monthDiff = lastDateObj.getMonth() - firstDateObj.getMonth();
        
        // 총 개월 수 계산 (첫 달 포함)
        monthsActive = Math.max(1, yearDiff * 12 + monthDiff + 1);
      }

      const totalDividends = tickerDividends.reduce((sum, d) => sum + d.amount_usd, 0);
      const monthlyAvg = totalDividends / monthsActive;
      const annualizedYield = (monthlyAvg * 12 / holding.total_invested_usd) * 100;

      stats.push({
        ticker: holding.ticker,
        totalInvested: holding.total_invested_usd,
        totalDividends,
        dividendCount: tickerDividends.length,
        monthlyAvg,
        annualizedYield,
        firstDividendDate: firstDate,
        lastDividendDate: lastDate,
        monthsActive,
      });
    });

    // 연환산 수익률로 정렬
    return stats.sort((a, b) => b.annualizedYield - a.annualizedYield);
  }, [holdings, dividends]);

  // 표준화 비교 (10,000달러 기준)
  const standardizedComparison = useMemo(() => {
    const STANDARD_AMOUNT = 10000;
    
    return dividendStats.map(stat => ({
      ticker: stat.ticker,
      monthlyDividend: (stat.monthlyAvg / stat.totalInvested) * STANDARD_AMOUNT,
      annualDividend: ((stat.monthlyAvg / stat.totalInvested) * STANDARD_AMOUNT) * 12,
      yield: stat.annualizedYield,
    }));
  }, [dividendStats]);

  // 전체 포트폴리오 통계
  const portfolioStats = useMemo(() => {
    const totalInvested = holdings.reduce((sum, h) => sum + h.total_invested_usd, 0);
    const totalDividends = dividends.reduce((sum, d) => sum + d.amount_usd, 0);
    
    // 배당금이 없는 경우 기본값 반환
    if (dividends.length === 0 || totalDividends === 0) {
      return {
        totalInvested,
        totalDividends: 0,
        monthlyAvg: 0,
        annualizedYield: 0,
        dividendCount: 0,
      };
    }
    
    // 전체 기간 계산
    const allDates = dividends.map(d => new Date(d.payment_date));
    const minDate = new Date(Math.min(...allDates.map(d => d.getTime())));
    const maxDate = new Date(Math.max(...allDates.map(d => d.getTime())));
    
    // 연도와 월의 차이를 계산하여 정확한 개월 수 계산
    const yearDiff = maxDate.getFullYear() - minDate.getFullYear();
    const monthDiff = maxDate.getMonth() - minDate.getMonth();
    const monthsActive = Math.max(1, yearDiff * 12 + monthDiff + 1);
    
    const monthlyAvg = totalDividends / monthsActive;
    const annualizedYield = totalInvested > 0 ? (monthlyAvg * 12 / totalInvested) * 100 : 0;

    return {
      totalInvested,
      totalDividends,
      monthlyAvg: isNaN(monthlyAvg) ? 0 : monthlyAvg,
      annualizedYield: isNaN(annualizedYield) ? 0 : annualizedYield,
      dividendCount: dividends.length,
    };
  }, [holdings, dividends]);

  // 월별 배당률 변화 추이 계산 (최근 5개월) - $100 투자 기준 표준화
  const monthlyDividendTrends = useMemo(() => {
    const trends: MonthlyDividendTrend[] = [];
    const STANDARD_INVESTMENT = 100; // $100 기준
    
    holdings.forEach(holding => {
      const tickerDividends = dividends
        .filter(d => d.ticker === holding.ticker)
        .sort((a, b) => new Date(b.payment_date).getTime() - new Date(a.payment_date).getTime());
      
      if (tickerDividends.length < 2) return; // 최소 2개월 데이터 필요
      
      // 월별로 그룹화
      const monthlyData: { [key: string]: number } = {};
      tickerDividends.forEach(dividend => {
        const date = new Date(dividend.payment_date);
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        monthlyData[monthKey] = (monthlyData[monthKey] || 0) + dividend.amount_usd;
      });
      
      // 최근 5개월 데이터 추출
      const sortedMonths = Object.keys(monthlyData).sort().reverse().slice(0, 5).reverse();
      const monthlyTrend = sortedMonths.map((month, index) => {
        const actualAmount = monthlyData[month];
        // $100 투자 시 받을 배당금으로 표준화
        const standardizedAmount = (actualAmount / holding.total_invested_usd) * STANDARD_INVESTMENT;
        const monthlyYield = (standardizedAmount / STANDARD_INVESTMENT) * 100; // 월 배당률
        
        let yieldChange = null;
        let yieldChangePercent = null;
        
        if (index > 0) {
          const prevMonth = sortedMonths[index - 1];
          const prevActualAmount = monthlyData[prevMonth];
          const prevStandardizedAmount = (prevActualAmount / holding.total_invested_usd) * STANDARD_INVESTMENT;
          const prevYield = (prevStandardizedAmount / STANDARD_INVESTMENT) * 100;
          
          yieldChange = monthlyYield - prevYield; // 배당률 포인트 변화
          yieldChangePercent = prevYield > 0 ? (yieldChange / prevYield) * 100 : 0; // 배당률 변화율
        }
        
        // 월 이름 포맷
        const [year, monthNum] = month.split('-');
        const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
        const monthName = `${monthNames[parseInt(monthNum) - 1]}`;
        
        return {
          month: monthName,
          amount: standardizedAmount, // 표준화된 금액
          yield: monthlyYield,
          yieldChange,
          yieldChangePercent,
        };
      });
      
      if (monthlyTrend.length >= 2) {
        trends.push({
          ticker: holding.ticker,
          totalInvested: STANDARD_INVESTMENT, // $100로 표준화
          months: monthlyTrend,
        });
      }
    });
    
    return trends;
  }, [holdings, dividends]);

  const isLoading = holdingsLoading || dividendsLoading;

  if (isLoading) {
    return (
      <VStack gap={6} align='stretch'>
        <Text fontSize='xl' fontWeight='bold'>
          배당 분석
        </Text>
        <Box textAlign='center' py={8}>
          <Spinner size='lg' />
          <Text mt={4} color='gray.500'>
            배당 데이터를 분석하는 중...
          </Text>
        </Box>
      </VStack>
    );
  }

  if (dividendStats.length === 0) {
    return (
      <VStack gap={6} align='stretch'>
        <Text fontSize='xl' fontWeight='bold'>
          배당 분석
        </Text>
        <Box textAlign='center' py={8}>
          <Text fontSize='lg' color='gray.500'>
            아직 받은 배당금이 없습니다.
          </Text>
        </Box>
      </VStack>
    );
  }

  return (
    <VStack gap={6} align='stretch'>
      <Text fontSize='xl' fontWeight='bold'>
        배당 분석
      </Text>

      {/* 포트폴리오 전체 요약 */}
      <Card.Root>
        <Card.Body>
          <Card.Title fontSize='lg' mb={4}>
            포트폴리오 배당 요약
          </Card.Title>
          <Stack direction={{ base: 'column', md: 'row' }} gap={6}>
            <Box flex={1}>
              <Text fontSize='sm' color='gray.600' mb={1}>
                총 투자금액
              </Text>
              <Text fontSize='xl' fontWeight='bold'>
                ${portfolioStats.totalInvested.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </Box>
            <Box flex={1}>
              <Text fontSize='sm' color='gray.600' mb={1}>
                총 받은 배당금
              </Text>
              <Text fontSize='xl' fontWeight='bold' color='blue.600'>
                ${portfolioStats.totalDividends.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
              <Text fontSize='sm' color='gray.500'>
                {portfolioStats.dividendCount}회 수령
              </Text>
            </Box>
            <Box flex={1}>
              <Text fontSize='sm' color='gray.600' mb={1}>
                월평균 배당금
              </Text>
              <Text fontSize='xl' fontWeight='bold' color='green.600'>
                ${(portfolioStats.monthlyAvg || 0).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </Box>
            <Box flex={1}>
              <Text fontSize='sm' color='gray.600' mb={1}>
                연환산 배당 수익률
              </Text>
              <Text fontSize='xl' fontWeight='bold' color='purple.600'>
                {(portfolioStats.annualizedYield || 0).toFixed(2)}%
              </Text>
            </Box>
          </Stack>
        </Card.Body>
      </Card.Root>

      {/* 종목별 배당 수익률 랭킹 */}
      <Card.Root>
        <Card.Body>
          <Card.Title fontSize='lg' mb={4}>
            종목별 배당 수익률 랭킹
          </Card.Title>
          <VStack gap={3} align='stretch'>
            {dividendStats.map((stat, index) => (
              <Box
                key={stat.ticker}
                p={4}
                bg={index === 0 ? 'blue.50' : 'gray.50'}
                borderRadius='lg'
                border={index === 0 ? '2px solid' : '1px solid'}
                borderColor={index === 0 ? 'blue.300' : 'gray.200'}
              >
                <Stack direction={{ base: 'column', md: 'row' }} gap={4} align='stretch'>
                  <HStack flex={1} justify='space-between'>
                    <HStack gap={3}>
                      <Badge
                        size='lg'
                        colorScheme={index === 0 ? 'blue' : index === 1 ? 'gray' : 'gray'}
                      >
                        {index + 1}위
                      </Badge>
                      <Text fontSize='lg' fontWeight='bold'>
                        {stat.ticker}
                      </Text>
                    </HStack>
                    <VStack align='flex-end' gap={0}>
                      <Text fontSize='lg' fontWeight='bold' color='purple.600'>
                        {stat.annualizedYield.toFixed(2)}%
                      </Text>
                      <Text fontSize='xs' color='gray.500'>
                        연환산
                      </Text>
                    </VStack>
                  </HStack>

                  <Separator orientation='vertical' display={{ base: 'none', md: 'block' }} />

                  <Stack flex={1} direction={{ base: 'row', sm: 'row' }} gap={4} justify='space-between'>
                    <VStack align='flex-start' gap={0}>
                      <Text fontSize='sm' color='gray.600'>
                        월평균
                      </Text>
                      <Text fontWeight='semibold'>
                        ${stat.monthlyAvg.toFixed(2)}
                      </Text>
                    </VStack>
                    <VStack align='flex-end' gap={0}>
                      <Text fontSize='sm' color='gray.600'>
                        총 배당금
                      </Text>
                      <Text fontWeight='semibold'>
                        ${stat.totalDividends.toFixed(2)}
                      </Text>
                      <Text fontSize='xs' color='gray.500'>
                        {stat.dividendCount}회 / {stat.monthsActive}개월
                      </Text>
                    </VStack>
                  </Stack>
                </Stack>
              </Box>
            ))}
          </VStack>
        </Card.Body>
      </Card.Root>

      {/* 표준화 비교 ($10,000 기준) */}
      <Card.Root>
        <Card.Body>
          <Card.Title fontSize='lg' mb={4}>
            표준화 비교 ($10,000 투자 시)
          </Card.Title>
          <Text fontSize='sm' color='gray.600' mb={4}>
            각 종목에 $10,000를 투자했을 때 예상되는 배당금입니다.
          </Text>
          <VStack gap={3} align='stretch'>
            {standardizedComparison.map(comp => (
              <Box
                key={comp.ticker}
                p={4}
                bg='gray.50'
                borderRadius='lg'
                border='1px solid'
                borderColor='gray.200'
              >
                <Stack direction={{ base: 'column', sm: 'row' }} justify='space-between' gap={3}>
                  <Text fontSize='lg' fontWeight='bold'>
                    {comp.ticker}
                  </Text>
                  <HStack gap={6}>
                    <VStack align='flex-end' gap={0}>
                      <Text fontSize='sm' color='gray.600'>
                        월 배당금
                      </Text>
                      <Text fontSize='lg' fontWeight='semibold' color='green.600'>
                        ${comp.monthlyDividend.toFixed(2)}
                      </Text>
                    </VStack>
                    <VStack align='flex-end' gap={0}>
                      <Text fontSize='sm' color='gray.600'>
                        연 배당금
                      </Text>
                      <Text fontSize='lg' fontWeight='semibold' color='blue.600'>
                        ${comp.annualDividend.toFixed(2)}
                      </Text>
                    </VStack>
                  </HStack>
                </Stack>
              </Box>
            ))}
          </VStack>

          {/* 최고 효율 종목 하이라이트 */}
          {standardizedComparison.length > 0 && (
            <Box mt={4} p={4} bg='green.50' borderRadius='lg'>
              <Text fontSize='sm' color='green.700'>
                💡 <strong>{standardizedComparison[0].ticker}</strong>가 가장 높은 배당 효율을 보이고 있습니다.
                $10,000 투자 시 월 ${standardizedComparison[0].monthlyDividend.toFixed(2)}의 배당금을 받을 수 있습니다.
              </Text>
            </Box>
          )}
        </Card.Body>
      </Card.Root>

      {/* 월별 배당률 변화 추이 */}
      {monthlyDividendTrends.length > 0 && (
        <Card.Root>
          <Card.Body>
            <Card.Title fontSize='lg' mb={4}>
              월별 배당률 변화 추이 (최근 5개월)
            </Card.Title>
            <Text fontSize='sm' color='gray.600' mb={4}>
              각 종목에 $100를 투자했을 때의 월 배당률 변화를 보여줍니다.
            </Text>
            <VStack gap={4} align='stretch'>
              {monthlyDividendTrends.map(trend => (
                <Box
                  key={trend.ticker}
                  p={4}
                  bg='gray.50'
                  borderRadius='lg'
                  border='1px solid'
                  borderColor='gray.200'
                >
                  <HStack justify='space-between' mb={3}>
                    <Text fontSize='lg' fontWeight='bold'>
                      {trend.ticker}
                    </Text>
                    <Text fontSize='sm' color='gray.600'>
                      기준 투자금: ${trend.totalInvested.toFixed(2)}
                    </Text>
                  </HStack>
                  <Stack direction={{ base: 'column', md: 'row' }} gap={3}>
                    {trend.months.map((monthData, index) => (
                      <Box
                        key={`${trend.ticker}-${monthData.month}`}
                        flex={1}
                        p={3}
                        bg='white'
                        borderRadius='md'
                        border='1px solid'
                        borderColor='gray.200'
                        position='relative'
                      >
                        <Text fontSize='sm' color='gray.600' fontWeight='medium'>
                          {monthData.month}
                        </Text>
                        <Text fontSize='lg' fontWeight='bold' mt={1} color='purple.600'>
                          {monthData.yield.toFixed(3)}%
                        </Text>
                        <Text fontSize='xs' color='gray.500'>
                          ${monthData.amount.toFixed(2)}
                        </Text>
                        {monthData.yieldChangePercent !== null && (
                          <Badge
                            size='sm'
                            colorScheme={monthData.yieldChangePercent >= 0 ? 'green' : 'red'}
                            mt={1}
                          >
                            {monthData.yieldChangePercent >= 0 ? '+' : ''}
                            {monthData.yieldChangePercent.toFixed(1)}%
                          </Badge>
                        )}
                        {index < trend.months.length - 1 && (
                          <Box
                            position='absolute'
                            right='-12px'
                            top='50%'
                            transform='translateY(-50%)'
                            display={{ base: 'none', md: 'block' }}
                          >
                            <Text fontSize='lg' color='gray.400'>
                              →
                            </Text>
                          </Box>
                        )}
                      </Box>
                    ))}
                  </Stack>
                  {/* 전체 추세 요약 */}
                  {trend.months.length > 1 && (() => {
                    const firstYield = trend.months[0].yield;
                    const lastYield = trend.months[trend.months.length - 1].yield;
                    const yieldPointChange = lastYield - firstYield;
                    const yieldPercentChange = (yieldPointChange / firstYield) * 100;
                    
                    return (
                      <Box mt={3} p={3} bg={yieldPointChange >= 0 ? 'green.50' : 'red.50'} borderRadius='md'>
                        <Text fontSize='sm' color={yieldPointChange >= 0 ? 'green.700' : 'red.700'}>
                          {trend.months.length}개월 간 배당률 변화: {yieldPointChange >= 0 ? '+' : ''}{yieldPointChange.toFixed(3)}%p
                          ({yieldPercentChange >= 0 ? '+' : ''}{yieldPercentChange.toFixed(1)}%)
                          {yieldPointChange >= 0 ? ' 📈' : ' 📉'}
                        </Text>
                      </Box>
                    );
                  })()}
                </Box>
              ))}
            </VStack>
          </Card.Body>
        </Card.Root>
      )}
    </VStack>
  );
};

export default DividendAnalysis;