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
    </VStack>
  );
};

export default DividendAnalysis;