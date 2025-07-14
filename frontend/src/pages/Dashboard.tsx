import React, { useEffect } from 'react';
import {
  Container,
  Heading,
  Text,
  Box,
  Tabs,
  Spinner,
  Alert,
  Button,
  Flex,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import Portfolio from '@/components/dashboard/Portfolio';
import TradeHistory from '@/components/dashboard/TradeHistory';
import DividendHistory from '@/components/dashboard/DividendHistory';
import AddTransaction from '@/components/dashboard/AddTransaction';
import AddDividends from '@/components/dashboard/AddDividends';
import SystemStatus from '@/components/dashboard/SystemStatus';
import DividendAnalysis from '@/components/dashboard/DividendAnalysis';
import { useExchangeRateStore } from '../store/exchangeRateStore';
import { useDashboardStore } from '../store/dashboardStore';
import { useAuthStore } from '../store/authStore';

const Dashboard = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout, checkAuth } = useAuthStore();
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

  // 인증 상태 확인 및 대시보드 초기화
  useEffect(() => {
    const initializeDashboard = async () => {
      // 먼저 인증 상태 확인
      await checkAuth();
    };

    initializeDashboard();
  }, [checkAuth]);

  // 인증 상태가 확인된 후 데이터 로딩
  useEffect(() => {
    if (isAuthenticated) {
      const loadDashboardData = async () => {
        // 환율 정보와 대시보드 데이터를 병렬로 가져오기
        await Promise.allSettled([fetchCurrentRate(), fetchAllData()]);
      };
      loadDashboardData();
    } else if (isAuthenticated === false) {
      // 인증되지 않은 경우 로그인 페이지로 리다이렉트
      navigate('/login');
    }
  }, [isAuthenticated, fetchCurrentRate, fetchAllData, navigate]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // 인증 상태가 아직 확인되지 않은 경우 로딩 표시
  if (isAuthenticated === null) {
    return (
      <Container
        maxW={{ base: '100%', md: 'container.md', lg: 'container.lg' }}
        px={{ base: 0, md: 4 }}
      >
        <Box textAlign='center' py={8} px={{ base: 4, md: 0 }}>
          <Spinner size='xl' />
          <Text mt={4} fontSize={{ base: 'md', md: 'lg' }}>
            인증 상태를 확인하는 중...
          </Text>
        </Box>
      </Container>
    );
  }

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
      {/* 사용자 정보 및 로그아웃 버튼 */}
      <Flex
        justify='space-between'
        align='center'
        p={{ base: 2, md: 4 }}
        borderBottom='1px solid'
        borderColor='gray.200'
        bg={{ base: 'white', _dark: 'gray.800' }}
      >
        <Box>
          <Text fontSize={{ base: 'md', md: 'lg' }} fontWeight='semibold'>
            안녕하세요, {user?.username}님
          </Text>
          <Text fontSize={{ base: 'xs', md: 'sm' }} color='gray.500'>
            {user?.email}
          </Text>
        </Box>
        <Button
          size={{ base: 'sm', md: 'md' }}
          variant='outline'
          onClick={handleLogout}
        >
          로그아웃
        </Button>
      </Flex>

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
                value='dividend_analysis'
                fontSize={{ base: 'xs', sm: 'sm', md: 'md' }}
                px={{ base: 2, sm: 3, md: 4 }}
                py={{ base: 2, md: 3 }}
                whiteSpace='nowrap'
                flexShrink={0}
                minW='fit-content'
              >
                배당 분석
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
              <Tabs.Trigger
                value='system_monitor'
                fontSize={{ base: 'xs', sm: 'sm', md: 'md' }}
                px={{ base: 2, sm: 3, md: 4 }}
                py={{ base: 2, md: 3 }}
                whiteSpace='nowrap'
                flexShrink={0}
                minW='fit-content'
              >
                <Box display={{ base: 'none', lg: 'block' }}>
                  System Monitor
                </Box>
                <Box display={{ base: 'block', lg: 'none' }}>+sys</Box>
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

          <Tabs.Content value='dividend_analysis'>
            <Box p={{ base: 2, md: 4 }}>
              <DividendAnalysis />
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

          <Tabs.Content value='system_monitor'>
            <Box p={{ base: 2, md: 4 }}>
              <SystemStatus />
            </Box>
          </Tabs.Content>
        </Tabs.Root>
      </Box>
    </Container>
  );
};

export default Dashboard;
