import React, { useEffect, useRef } from 'react';
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
import TokenExpiryNotification from '../components/auth/TokenExpiryNotification';
import { useExchangeRateStore } from '../store/exchangeRateStore';
import { useDashboardStore } from '../store/dashboardStore';
import { useAuthStore } from '../store/authStore';
import { authTokenManager } from '../lib/auth';

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

  const isInitializing = useRef(false);
  const isDataLoading = useRef(false);

  // 인증 상태 확인 및 대시보드 초기화 (한 번만 실행)
  useEffect(() => {
    if (isInitializing.current) return;
    isInitializing.current = true;

    console.log('🔄 인증 상태 확인 시작...');
    checkAuth()
      .then(() => console.log('✅ 인증 상태 확인 완료'))
      .catch(error => console.error('❌ 인증 확인 실패:', error));
  }, []); // 빈 배열 - 컴포넌트 마운트 시에만 실행

  // 인증 상태가 확인된 후 데이터 로딩
  useEffect(() => {
    if (isAuthenticated === true && !isDataLoading.current) {
      isDataLoading.current = true;

      console.log('🚀 대시보드 데이터 로딩 시작...');
      console.log('🔑 현재 토큰 상태:', authTokenManager.getTokenInfo());

      // 환율 정보와 대시보드 데이터를 병렬로 가져오기
      Promise.allSettled([fetchCurrentRate(), fetchAllData()])
        .then(() => console.log('✅ 대시보드 데이터 로딩 완료'))
        .catch(error => console.error('❌ 데이터 로딩 실패:', error))
        .finally(() => {
          isDataLoading.current = false;
        });
    } else if (isAuthenticated === false) {
      console.log('❌ 인증되지 않음 - 로그인 페이지로 리다이렉트');
      navigate('/login');
    }
  }, [isAuthenticated]); // isAuthenticated만 의존성으로 유지

  // const handleLogout = async () => {
  //   await logout();
  //   navigate('/login');
  // };

  // 디버깅 정보 출력
  console.log('🔍 Dashboard 렌더링 상태:', {
    isAuthenticated,
    isInitialized,
    holdingsLoading,
    portfolioLoading,
    transactionsLoading,
    dividendsLoading,
    holdingsError,
    portfolioError,
    transactionsError,
    dividendsError,
  });

  // 인증 상태가 아직 확인되지 않은 경우 로딩 표시
  if (isAuthenticated === null) {
    console.log('🔄 인증 상태 확인 중...');
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

  console.log('🔍 렌더링 조건:', { isLoading, hasError });

  // 로딩 상태 렌더링
  if (isLoading) {
    console.log('🔄 데이터 로딩 중...');
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

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('로그아웃 실패:', error);
    }
  };

  console.log('🎯 메인 렌더링 시작 - 인증됨:', isAuthenticated);

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
        p={{ base: 3, md: 4 }}
        borderBottom='1px solid'
        borderColor='gray.200'
        bg='white'
        mb={{ base: 2, md: 4 }}
      >
        <Box>
          <Heading size={{ base: 'md', md: 'lg' }} color='gray.800'>
            커버드 콜 익스플로러
          </Heading>
          {user && (
            <Text fontSize={{ base: 'sm', md: 'md' }} color='gray.600' mt={1}>
              환영합니다, {user.username}님
            </Text>
          )}
        </Box>

        <Button
          colorScheme='red'
          variant='outline'
          size={{ base: 'sm', md: 'md' }}
          onClick={handleLogout}
        >
          로그아웃
        </Button>
      </Flex>

      {/* 토큰 만료 알림 */}
      <TokenExpiryNotification />

      {/* 메인 탭 인터페이스 */}
      <Tabs.Root defaultValue='portfolio'>
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
            <Box display={{ base: 'none', lg: 'block' }}>System Monitor</Box>
            <Box display={{ base: 'block', lg: 'none' }}>+sys</Box>
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value='portfolio' px={{ base: 3, sm: 3, md: 0 }}>
          <Portfolio />
        </Tabs.Content>

        <Tabs.Content value='transactions' px={{ base: 3, sm: 3, md: 0 }}>
          <TradeHistory />
        </Tabs.Content>

        <Tabs.Content value='dividends' px={{ base: 3, sm: 3, md: 0 }}>
          <DividendHistory />
        </Tabs.Content>

        <Tabs.Content value='add_transactions' px={{ base: 3, sm: 3, md: 0 }}>
          <AddTransaction />
        </Tabs.Content>

        <Tabs.Content value='add_dividends' px={{ base: 3, sm: 3, md: 0 }}>
          <AddDividends />
        </Tabs.Content>

        <Tabs.Content value='dividend_analysis' px={{ base: 3, sm: 3, md: 0 }}>
          <DividendAnalysis />
        </Tabs.Content>

        <Tabs.Content value='system_monitor' px={{ base: 3, sm: 3, md: 0 }}>
          <SystemStatus />
        </Tabs.Content>
      </Tabs.Root>
    </Container>
  );
};

export default Dashboard;
