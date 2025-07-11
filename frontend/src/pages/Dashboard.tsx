import React, { useEffect } from 'react';
import { Container, Heading, Text, Box, Tabs } from '@chakra-ui/react';
import Portfolio from '@/components/dashboard/Portfolio';
import TradeHistory from '@/components/dashboard/TradeHistory';
import DividendHistory from '@/components/dashboard/DividendHistory';
import AddTransaction from '@/components/dashboard/AddTransaction';
import { useHoldings, usePortfolio } from '../hooks/useApi';
import AddDividends from '@/components/dashboard/AddDividends';
import { useExchangeRateStore } from '../store/exchangeRateStore';

const Dashboard = () => {
  const { fetchCurrentRate, currentRate, lastUpdated } = useExchangeRateStore();

  // Dashboard 컴포넌트가 처음 렌더링될 때 한 번만 환율 정보 가져오기
  useEffect(() => {
    fetchCurrentRate();
    console.log(currentRate, lastUpdated);
  }, []); // 빈 의존성 배열로 한 번만 실행

  // const {
  //   holdings,
  //   isLoading: holdingsLoading,
  //   error: holdingsError,
  // } = useHoldings();
  // const {
  //   portfolio,
  //   isLoading: portfolioLoading,
  //   error: portfolioError,
  // } = usePortfolio();

  // useEffect(() => {
  //   console.log('Holdings:', holdings);
  //   console.log('Portfolio:', portfolio);
  // }, [holdings, portfolio]);

  // const isLoading = holdingsLoading || portfolioLoading;
  // const error = holdingsError || portfolioError;

  // if (isLoading) {
  //   return (
  //     <Container maxW='container.md'>
  //       <Heading as='h1' size='lg'>
  //         Dashboard
  //       </Heading>
  //       <Text mt={4}>데이터를 불러오는 중...</Text>
  //     </Container>
  //   );
  // }

  // if (error) {
  //   return (
  //     <Container maxW='container.md'>
  //       <Heading as='h1' size='lg'>
  //         Dashboard
  //       </Heading>
  //       <Text mt={4} color='red.500'>
  //         데이터를 불러오는 중 오류가 발생했습니다: {error.message}
  //       </Text>
  //     </Container>
  //   );
  // }

  return (
    <Container maxW='container.md'>
      <Box w='100%' mt={6}>
        <Tabs.Root defaultValue='portfolio'>
          <Tabs.List>
            <Tabs.Trigger value='portfolio'>포트폴리오</Tabs.Trigger>
            <Tabs.Trigger value='transactions'>거래 내역</Tabs.Trigger>
            <Tabs.Trigger value='dividends'>배당금 내역</Tabs.Trigger>
            <Tabs.Trigger value='returns'>수익률</Tabs.Trigger>
            <Tabs.Trigger value='add_transactions'>거래 내역 추가</Tabs.Trigger>
            <Tabs.Trigger value='add_dividends'>배당금 추가</Tabs.Trigger>
          </Tabs.List>

          <Tabs.Content value='portfolio'>
            <Box p={4}>
              <Portfolio />
            </Box>
          </Tabs.Content>

          <Tabs.Content value='transactions'>
            <Box p={4}>
              <TradeHistory />
            </Box>
          </Tabs.Content>

          <Tabs.Content value='dividends'>
            <Box p={4}>
              <DividendHistory />
            </Box>
          </Tabs.Content>

          <Tabs.Content value='returns'>
            <Box p={4}>
              <Text fontSize='lg' fontWeight='bold' mb={4}>
                수익률
              </Text>
              <Text>수익률이 여기에 표시됩니다.</Text>
            </Box>
          </Tabs.Content>

          <Tabs.Content value='add_transactions'>
            <Box p={4}>
              <AddTransaction />
            </Box>
          </Tabs.Content>

          <Tabs.Content value='add_dividends'>
            <Box p={4}>
              <AddDividends />
            </Box>
          </Tabs.Content>
        </Tabs.Root>
      </Box>
    </Container>
  );
};

export default Dashboard;
