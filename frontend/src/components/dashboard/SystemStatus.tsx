import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Spinner,
  Badge,
  Alert,
  Progress,
  Code,
  Textarea,
} from '@chakra-ui/react';
import { apiClient } from '@/lib/api';

interface BotStatus {
  status: 'ok' | 'warning' | 'error';
  message: string;
  bot_running: boolean;
  bot_info?: {
    id: number;
    username: string;
    first_name: string;
  };
  connection_error?: string;
  last_check: string;
}

const SystemStatus = () => {
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [testMessage, setTestMessage] = useState(
    '🧪 텔레그램 봇 테스트 메시지입니다!'
  );
  const [sendingTest, setSendingTest] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [updatingPrices, setUpdatingPrices] = useState(false);
  const [priceUpdateResult, setPriceUpdateResult] = useState<string | null>(null);

  const checkBotStatus = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/bot-status');
      setBotStatus(response.data);
    } catch (error: any) {
      setBotStatus({
        status: 'error',
        message: error.response?.data?.message || '봇 상태 확인 실패',
        bot_running: false,
        last_check: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  };

  const sendTestMessage = async () => {
    setSendingTest(true);
    setTestResult(null);
    try {
      const response = await apiClient.post('/send-test-message', {
        message: testMessage,
      });
      setTestResult(`✅ ${response.data.message}`);
    } catch (error: any) {
      setTestResult(
        `❌ ${error.response?.data?.message || '테스트 메시지 전송 실패'}`
      );
    } finally {
      setSendingTest(false);
    }
  };

  const updatePrices = async () => {
    setUpdatingPrices(true);
    setPriceUpdateResult(null);
    try {
      const response = await apiClient.get('/holdings?update_prices=true');
      const updates = response.data.price_updates || [];
      setPriceUpdateResult(
        `✅ 주가 업데이트 완료: ${updates.length}개 종목 업데이트됨`
      );
    } catch (error: any) {
      setPriceUpdateResult(
        `❌ ${error.response?.data?.message || '주가 업데이트 실패'}`
      );
    } finally {
      setUpdatingPrices(false);
    }
  };

  useEffect(() => {
    checkBotStatus();
    // 30초마다 자동 상태 확인
    const interval = setInterval(checkBotStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ok':
        return 'green';
      case 'warning':
        return 'yellow';
      case 'error':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ok':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      default:
        return '❓';
    }
  };

  return (
    <VStack gap={6} align='stretch'>
      <Text fontSize='xl' fontWeight='bold'>
        시스템 상태 모니터링
      </Text>

      {/* 봇 상태 카드 */}
      <Box
        p={6}
        bg='white'
        borderRadius='lg'
        border='1px solid'
        borderColor='gray.200'
        boxShadow='sm'
      >
        <VStack gap={4} align='stretch'>
          <HStack justify='space-between' align='center'>
            <Text fontSize='lg' fontWeight='semibold'>
              텔레그램 봇 상태
            </Text>
            <Button
              size='sm'
              onClick={checkBotStatus}
              loading={loading}
              loadingText='확인중...'
            >
              상태 새로고침
            </Button>
          </HStack>

          {loading && !botStatus ? (
            <HStack>
              <Spinner size='sm' />
              <Text>봇 상태를 확인하는 중...</Text>
            </HStack>
          ) : botStatus ? (
            <VStack gap={3} align='stretch'>
              <HStack>
                <Text fontSize='2xl'>{getStatusIcon(botStatus.status)}</Text>
                <Badge
                  colorScheme={getStatusColor(botStatus.status)}
                  fontSize='sm'
                  px={3}
                  py={1}
                  borderRadius='full'
                >
                  {botStatus.status.toUpperCase()}
                </Badge>
                <Text color='gray.600'>
                  {botStatus.bot_running ? '실행 중' : '중지됨'}
                </Text>
              </HStack>

              <Text fontSize='sm' color='gray.700'>
                {botStatus.message}
              </Text>

              {botStatus.bot_info && (
                <Box
                  p={3}
                  bg='gray.50'
                  borderRadius='md'
                  border='1px solid'
                  borderColor='gray.200'
                >
                  <Text fontSize='sm' fontWeight='medium' mb={1}>
                    봇 정보:
                  </Text>
                  <Code fontSize='xs'>
                    ID: {botStatus.bot_info.id} | @{botStatus.bot_info.username}{' '}
                    | {botStatus.bot_info.first_name}
                  </Code>
                </Box>
              )}

              {botStatus.connection_error && (
                <Alert.Root status='warning' size='sm'>
                  <Alert.Indicator />
                  <Alert.Content>
                    <Alert.Title>연결 오류</Alert.Title>
                    <Alert.Description>
                      {botStatus.connection_error}
                    </Alert.Description>
                  </Alert.Content>
                </Alert.Root>
              )}

              <Text fontSize='xs' color='gray.500'>
                마지막 확인: {new Date(botStatus.last_check).toLocaleString()}
              </Text>
            </VStack>
          ) : (
            <Text color='gray.500'>상태 정보를 불러올 수 없습니다.</Text>
          )}
        </VStack>
      </Box>

      {/* 테스트 메시지 전송 */}
      <Box
        p={6}
        bg='white'
        borderRadius='lg'
        border='1px solid'
        borderColor='gray.200'
        boxShadow='sm'
      >
        <VStack gap={4} align='stretch'>
          <Text fontSize='lg' fontWeight='semibold'>
            텔레그램 봇 테스트
          </Text>

          <VStack gap={3} align='stretch'>
            <Box>
              <Text fontSize='sm' fontWeight='medium' mb={2}>
                테스트 메시지:
              </Text>
              <Textarea
                value={testMessage}
                onChange={e => setTestMessage(e.target.value)}
                placeholder='전송할 테스트 메시지를 입력하세요...'
                rows={3}
              />
            </Box>

            <Button
              colorScheme='blue'
              onClick={sendTestMessage}
              loading={sendingTest}
              loadingText='전송 중...'
              disabled={!testMessage.trim() || !botStatus?.bot_running}
            >
              테스트 메시지 전송
            </Button>

            {testResult && (
              <Alert.Root
                status={testResult.startsWith('✅') ? 'success' : 'error'}
                size='sm'
              >
                <Alert.Indicator />
                <Alert.Content>
                  <Alert.Description>{testResult}</Alert.Description>
                </Alert.Content>
              </Alert.Root>
            )}
          </VStack>
        </VStack>
      </Box>

      {/* 주가 업데이트 */}
      <Box
        p={6}
        bg='white'
        borderRadius='lg'
        border='1px solid'
        borderColor='gray.200'
        boxShadow='sm'
      >
        <VStack gap={4} align='stretch'>
          <Text fontSize='lg' fontWeight='semibold'>
            수동 주가 업데이트
          </Text>

          <VStack gap={3} align='stretch'>
            <Text fontSize='sm' color='gray.600'>
              현재 자동 주가 업데이트가 비활성화되어 있습니다. 필요시 수동으로 업데이트할 수 있습니다.
            </Text>

            <Button
              colorScheme='orange'
              onClick={updatePrices}
              loading={updatingPrices}
              loadingText='업데이트 중...'
            >
              Toss API로 주가 업데이트
            </Button>

            {priceUpdateResult && (
              <Alert.Root
                status={priceUpdateResult.startsWith('✅') ? 'success' : 'error'}
                size='sm'
              >
                <Alert.Indicator />
                <Alert.Content>
                  <Alert.Description>{priceUpdateResult}</Alert.Description>
                </Alert.Content>
              </Alert.Root>
            )}
          </VStack>
        </VStack>
      </Box>

      {/* 시스템 헬스 체크 */}
      <Box
        p={6}
        bg='white'
        borderRadius='lg'
        border='1px solid'
        borderColor='gray.200'
        boxShadow='sm'
      >
        <VStack gap={4} align='stretch'>
          <Text fontSize='lg' fontWeight='semibold'>
            시스템 헬스 체크
          </Text>

          <VStack gap={3} align='stretch'>
            <HStack justify='space-between'>
              <Text fontSize='sm'>API 서버</Text>
              <Badge colorScheme='green'>정상</Badge>
            </HStack>

            <HStack justify='space-between'>
              <Text fontSize='sm'>데이터베이스</Text>
              <Badge colorScheme='green'>정상</Badge>
            </HStack>

            <HStack justify='space-between'>
              <Text fontSize='sm'>텔레그램 봇</Text>
              <Badge colorScheme={botStatus?.bot_running ? 'green' : 'red'}>
                {botStatus?.bot_running ? '정상' : '오류'}
              </Badge>
            </HStack>
          </VStack>
        </VStack>
      </Box>
    </VStack>
  );
};

export default SystemStatus;
