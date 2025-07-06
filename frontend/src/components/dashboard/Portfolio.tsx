import React from 'react';
import { Chart, useChart } from '@chakra-ui/charts';
import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts';
import { Box, Text, VStack, HStack, Badge } from '@chakra-ui/react';
import type { Holding, PortfolioSummary } from '../../hooks/useApi';

interface PortfolioProps {
  holdings?: Holding[];
  portfolio?: PortfolioSummary;
}

const Portfolio = ({ holdings = [], portfolio }: PortfolioProps) => {
  // 홀딩 데이터를 차트용 데이터로 변환
  const chartData = holdings.map((holding, index) => ({
    name: holding.ticker,
    value: holding.current_value_usd,
    color: ['blue.solid', 'orange.solid', 'green.solid', 'purple.solid', 'teal.solid', 'red.solid'][index % 6],
  }));

  const chart = useChart({
    data: chartData,
  });

  // 포트폴리오 총 가치 (USD)
  const totalValueUSD = portfolio?.total_current_value_usd || 0;
  const totalValueKRW = portfolio?.total_current_value_krw || 0;
  
  // 배당금 포함 총 손익
  const totalPnlUSD = portfolio?.total_pnl_with_dividends_usd || 0;
  const totalPnlKRW = portfolio?.total_pnl_with_dividends_krw || 0;
  
  // 배당금 포함 총 수익률
  const totalReturnRateUSD = portfolio?.total_return_with_dividends_usd || 0;
  const totalReturnRateKRW = portfolio?.total_return_with_dividends_krw || 0;

  if (holdings.length === 0) {
    return (
      <VStack gap={6} align='stretch'>
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
              ${totalValueUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              <Text as='span' fontSize='sm' color={totalReturnRateUSD >= 0 ? 'green.600' : 'red.600'} ml={2}>
                ({totalReturnRateUSD >= 0 ? '+' : ''}{totalReturnRateUSD.toFixed(2)}%)
              </Text>
            </Text>
            <Text fontSize='lg' color='blue.600'>
              ₩{totalValueKRW.toLocaleString('ko-KR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              <Text as='span' fontSize='sm' color={totalReturnRateKRW >= 0 ? 'green.600' : 'red.600'} ml={2}>
                ({totalReturnRateKRW >= 0 ? '+' : ''}{totalReturnRateKRW.toFixed(2)}%)
              </Text>
            </Text>
          </Box>

          <Box p={4} bg={totalPnlUSD >= 0 ? 'green.50' : 'red.50'} borderRadius='lg' flex={1} minW='250px'>
            <Text fontSize='sm' color={totalPnlUSD >= 0 ? 'green.600' : 'red.600'} fontWeight='medium'>
              총 손익 (배당금 포함)
            </Text>
            <Text fontSize='2xl' fontWeight='bold' color={totalPnlUSD >= 0 ? 'green.700' : 'red.700'}>
              {totalPnlUSD >= 0 ? '+' : ''}${totalPnlUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Text>
            <HStack>
              <Badge colorScheme={totalReturnRateUSD >= 0 ? 'green' : 'red'}>
                {totalReturnRateUSD >= 0 ? '+' : ''}{totalReturnRateUSD.toFixed(2)}% (USD)
              </Badge>
              <Badge colorScheme={totalReturnRateKRW >= 0 ? 'green' : 'red'}>
                {totalReturnRateKRW >= 0 ? '+' : ''}{totalReturnRateKRW.toFixed(2)}% (KRW)
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
            {holdings.map((holding, index) => (
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
                    <Text fontWeight='bold' fontSize='lg'>{holding.ticker}</Text>
                  </HStack>
                  <Text fontSize='sm' color='gray.600'>
                    {holding.total_shares.toFixed(2)} 주 @ ${holding.current_price.toFixed(2)}
                  </Text>
                  <Badge colorScheme={holding.return_rate_usd >= 0 ? 'green' : 'red'} size='sm'>
                    {holding.return_rate_usd >= 0 ? '+' : ''}{holding.return_rate_usd.toFixed(2)}%
                  </Badge>
                </VStack>
                
                <VStack align='flex-end' gap={1}>
                  <Text fontSize='lg' fontWeight='semibold'>
                    ${holding.current_value_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Text>
                  <Text fontSize='sm' color='gray.500'>
                    ₩{holding.current_value_krw.toLocaleString('ko-KR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </Text>
                  <Text 
                    fontSize='sm' 
                    color={holding.unrealized_pnl_usd >= 0 ? 'green.600' : 'red.600'}
                    fontWeight='medium'
                  >
                    {holding.unrealized_pnl_usd >= 0 ? '+' : ''}${holding.unrealized_pnl_usd.toFixed(2)}
                  </Text>
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
