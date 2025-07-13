import React, { useEffect } from 'react';
import {
  Container,
  Heading,
  Text,
  Box,
  Tabs,
  Spinner,
  Alert,
} from '@chakra-ui/react';
import Portfolio from '@/components/dashboard/Portfolio';
import TradeHistory from '@/components/dashboard/TradeHistory';
import DividendHistory from '@/components/dashboard/DividendHistory';
import AddTransaction from '@/components/dashboard/AddTransaction';
import AddDividends from '@/components/dashboard/AddDividends';
import { useExchangeRateStore } from '../store/exchangeRateStore';
import { useDashboardStore } from '../store/dashboardStore';

const Dashboard = () => {
  const { fetchCurrentRate } = useExchangeRateStore();
  const {
    isInitialized,
    holdingsLoading,
    portfolioLoading,
    transactionsLoading,
    dividendsLoading,
    holdingsError,
    portfolioError,
    transactionsError,
    dividendsError,
    fetchAllData,
    clearErrors,
  } = useDashboardStore();

  // Dashboard 컴포넌트가 처음 렌더링될 때 환율 정보와 모든 대시보드 데이터 가져오기
  useEffect(() => {
    const initializeDashboard = async () => {
      // 환율 정보와 대시보드 데이터를 병렬로 가져오기
      await Promise.allSettled([fetchCurrentRate(), fetchAllData()]);
    };

    initializeDashboard();
  }, []); // 빈 의존성 배열로 한 번만 실행

  // 전체 로딩 상태 계산
  const isLoading =
    !isInitialized ||
    holdingsLoading ||
    portfolioLoading ||
    transactionsLoading ||
    dividendsLoading;

  // 에러 상태 계산
  const hasError =
    holdingsError || portfolioError || transactionsError || dividendsError;

  // 로딩 상태 렌더링
  if (isLoading) {
    return (
      <Container
        maxW={{ base: '100%', md: 'container.md', lg: 'container.lg' }}
        px={{ base: 0, md: 4 }}
      >
        <Box textAlign='center' py={8} px={{ base: 4, md: 0 }}>
          <Spinner size='xl' />
          <Text mt={4} fontSize={{ base: 'md', md: 'lg' }}>
            대시보드 데이터를 불러오는 중...
          </Text>
          <Text mt={2} color='gray.500' fontSize={{ base: 'xs', md: 'sm' }}>
            포트폴리오, 거래 내역, 배당금 데이터를 가져오고 있습니다.
          </Text>
        </Box>
      </Container>
    );
  }

  // 에러 상태 렌더링 (데이터가 로드된 후에도 일부 에러가 있을 수 있음)
  if (hasError) {
    return (
      <Container
        maxW={{ base: '100%', md: 'container.md', lg: 'container.lg' }}
        px={{ base: 0, md: 4 }}
      >
        <Box mt={{ base: 2, md: 6 }} px={{ base: 4, md: 0 }}>
          <Alert.Root status='error'>
            <Alert.Indicator />
            <Alert.Content>
              <Alert.Title>데이터 로드 중 오류 발생</Alert.Title>
              <Alert.Description>
                {holdingsError && <div>• 보유 종목: {holdingsError}</div>}
                {portfolioError && <div>• 포트폴리오: {portfolioError}</div>}
                {transactionsError && (
                  <div>• 거래 내역: {transactionsError}</div>
                )}
                {dividendsError && <div>• 배당금: {dividendsError}</div>}
              </Alert.Description>
            </Alert.Content>
          </Alert.Root>
          <Box mt={4} textAlign='center'>
            <Text
              as='button'
              color='blue.500'
              textDecoration='underline'
              fontSize={{ base: 'sm', md: 'md' }}
              onClick={() => {
                clearErrors();
                fetchAllData();
              }}
            >
              다시 시도
            </Text>
          </Box>
        </Box>
      </Container>
    );
  }

  return (
    <Container
      maxW={{
        base: '100%',
        md: 'container.md',
        lg: 'container.lg',
        xl: 'container.xl',
      }}
      px={{ base: 0, md: 4 }}
    >
      <Box w='100%' mt={{ base: 0, md: 6 }}>
        <Tabs.Root defaultValue='portfolio'>
          <Box
            overflowX='auto'
            overflowY='hidden'
            css={{
              /* Chrome / Edge / Safari */
              '&::-webkit-scrollbar': { display: 'none' },

              /* Firefox */
              scrollbarWidth: 'none',
            }}
          >
            <Tabs.List
              gap={0}
              py={{ base: 1, md: 2 }}
              px={{ base: 2, md: 0 }}
              display='flex'
              flexWrap='nowrap'
              minW='fit-content'
              bg={{ base: 'white', _dark: 'gray.800' }}
              borderBottom='1px solid'
              borderColor='gray.200'
            >
              <Tabs.Trigger
                value='portfolio'
                fontSize={{ base: 'xs', sm: 'sm', md: 'md' }}
                px={{ base: 2, sm: 3, md: 4 }}
                py={{ base: 2, md: 3 }}
                whiteSpace='nowrap'
                flexShrink={0}
                minW='fit-content'
              >
                포트폴리오
              </Tabs.Trigger>
              <Tabs.Trigger
                value='transactions'
                fontSize={{ base: 'xs', sm: 'sm', md: 'md' }}
                px={{ base: 2, sm: 3, md: 4 }}
                py={{ base: 2, md: 3 }}
                whiteSpace='nowrap'
                flexShrink={0}
                minW='fit-content'
              >
                거래내역
              </Tabs.Trigger>
              <Tabs.Trigger
                value='dividends'
                fontSize={{ base: 'xs', sm: 'sm', md: 'md' }}
                px={{ base: 2, sm: 3, md: 4 }}
                py={{ base: 2, md: 3 }}
                whiteSpace='nowrap'
                flexShrink={0}
                minW='fit-content'
              >
                배당금
              </Tabs.Trigger>
              <Tabs.Trigger
                value='returns'
                fontSize={{ base: 'xs', sm: 'sm', md: 'md' }}
                px={{ base: 2, sm: 3, md: 4 }}
                py={{ base: 2, md: 3 }}
                whiteSpace='nowrap'
                flexShrink={0}
                minW='fit-content'
              >
                수익률
              </Tabs.Trigger>
              <Tabs.Trigger
                value='add_transactions'
                fontSize={{ base: 'xs', sm: 'sm', md: 'md' }}
                px={{ base: 2, sm: 3, md: 4 }}
                py={{ base: 2, md: 3 }}
                whiteSpace='nowrap'
                flexShrink={0}
                minW='fit-content'
              >
                <Box display={{ base: 'none', lg: 'block' }}>거래내역 추가</Box>
                <Box display={{ base: 'block', lg: 'none' }}>+거래</Box>
              </Tabs.Trigger>
              <Tabs.Trigger
                value='add_dividends'
                fontSize={{ base: 'xs', sm: 'sm', md: 'md' }}
                px={{ base: 2, sm: 3, md: 4 }}
                py={{ base: 2, md: 3 }}
                whiteSpace='nowrap'
                flexShrink={0}
                minW='fit-content'
              >
                <Box display={{ base: 'none', lg: 'block' }}>배당금 추가</Box>
                <Box display={{ base: 'block', lg: 'none' }}>+배당</Box>
              </Tabs.Trigger>
            </Tabs.List>
          </Box>

          <Tabs.Content value='portfolio'>
            <Box p={{ base: 2, md: 4 }}>
              <Portfolio />
            </Box>
          </Tabs.Content>

          <Tabs.Content value='transactions'>
            <Box p={{ base: 2, md: 4 }}>
              <TradeHistory />
            </Box>
          </Tabs.Content>

          <Tabs.Content value='dividends'>
            <Box p={{ base: 2, md: 4 }}>
              <DividendHistory />
            </Box>
          </Tabs.Content>

          <Tabs.Content value='returns'>
            <Box p={{ base: 2, md: 4 }}>
              <Text
                fontSize={{ base: 'lg', md: 'xl' }}
                fontWeight='bold'
                mb={4}
              >
                수익률
              </Text>
              <Text>수익률이 여기에 표시됩니다.</Text>
            </Box>
          </Tabs.Content>

          <Tabs.Content value='add_transactions'>
            <Box p={{ base: 2, md: 4 }}>
              <AddTransaction />
            </Box>
          </Tabs.Content>

          <Tabs.Content value='add_dividends'>
            <Box p={{ base: 2, md: 4 }}>
              <AddDividends />
            </Box>
          </Tabs.Content>
        </Tabs.Root>
      </Box>
    </Container>
  );
};

export default Dashboard;
