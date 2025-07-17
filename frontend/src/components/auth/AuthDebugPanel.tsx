import React from 'react';
import {
  Box,
  Button,
  Text,
  VStack,
  HStack,
  Badge,
  Textarea,
  Separator,
} from '@chakra-ui/react';
import { useAuthStore } from '../../store/authStore';
import { authTokenManager, logTokenInfo } from '../../lib/auth';
import { apiClient } from '../../lib/api';

const AuthDebugPanel: React.FC = () => {
  const { 
    user, 
    isAuthenticated, 
    tokenInfo, 
    refreshToken, 
    updateTokenInfo,
    logout 
  } = useAuthStore();

  const [testResult, setTestResult] = React.useState<string>('');

  const handleTestAPI = async () => {
    try {
      setTestResult('API 테스트 중...');
      const response = await apiClient.get('/auth/test-jwt');
      setTestResult(JSON.stringify(response.data, null, 2));
    } catch (error: any) {
      setTestResult(`API 테스트 실패: ${error.response?.data?.error || error.message}`);
    }
  };

  const handleRefreshToken = async () => {
    try {
      setTestResult('토큰 갱신 중...');
      const success = await refreshToken();
      setTestResult(`토큰 갱신 ${success ? '성공' : '실패'}`);
      updateTokenInfo();
    } catch (error: any) {
      setTestResult(`토큰 갱신 실패: ${error.message}`);
    }
  };

  const handleLogTokenInfo = () => {
    logTokenInfo();
    setTestResult('콘솔에서 토큰 정보를 확인하세요.');
  };

  const formatDate = (date: Date | null) => {
    return date ? date.toLocaleString() : 'N/A';
  };

  const getStatusColor = (status: boolean | null) => {
    if (status === null) return 'gray';
    return status ? 'green' : 'red';
  };

  const getStatusText = (status: boolean | null) => {
    if (status === null) return '확인 중';
    return status ? '인증됨' : '미인증';
  };

  if (import.meta.env.PROD) {
    return null; // 프로덕션에서는 표시하지 않음
  }

  return (
    <Box
      position="fixed"
      bottom={4}
      left={4}
      p={4}
      bg="white"
      borderRadius="md"
      boxShadow="xl"
      border="1px"
      borderColor="gray.200"
      maxW="400px"
      maxH="600px"
      overflowY="auto"
      zIndex={1000}
    >
      <VStack gap={3} align="stretch">
        <Text fontWeight="bold" fontSize="md">
          🔐 JWT 인증 디버그 패널
        </Text>

        <Separator />

        {/* 인증 상태 */}
        <Box>
          <Text fontSize="sm" fontWeight="semibold" mb={2}>
            인증 상태:
          </Text>
          <HStack>
            <Badge colorScheme={getStatusColor(isAuthenticated)}>
              {getStatusText(isAuthenticated)}
            </Badge>
            {user && (
              <Text fontSize="xs" color="gray.600">
                {user.username}
              </Text>
            )}
          </HStack>
        </Box>

        {/* 토큰 정보 */}
        {tokenInfo && (
          <Box>
            <Text fontSize="sm" fontWeight="semibold" mb={2}>
              토큰 정보:
            </Text>
            <VStack gap={1} align="stretch" fontSize="xs">
              <HStack justify="space-between">
                <Text>토큰 보유:</Text>
                <Badge colorScheme={tokenInfo.hasTokens ? 'green' : 'red'}>
                  {tokenInfo.hasTokens ? 'Yes' : 'No'}
                </Badge>
              </HStack>
              <HStack justify="space-between">
                <Text>유효한 토큰:</Text>
                <Badge colorScheme={tokenInfo.hasValidAccessToken ? 'green' : 'red'}>
                  {tokenInfo.hasValidAccessToken ? 'Yes' : 'No'}
                </Badge>
              </HStack>
              <HStack justify="space-between">
                <Text>만료됨:</Text>
                <Badge colorScheme={tokenInfo.isExpired ? 'red' : 'green'}>
                  {tokenInfo.isExpired ? 'Yes' : 'No'}
                </Badge>
              </HStack>
              <HStack justify="space-between">
                <Text>곧 만료:</Text>
                <Badge colorScheme={tokenInfo.isExpiringSoon ? 'orange' : 'green'}>
                  {tokenInfo.isExpiringSoon ? 'Yes' : 'No'}
                </Badge>
              </HStack>
              <Text color="gray.600">
                만료 시간: {formatDate(tokenInfo.expiryTime)}
              </Text>
            </VStack>
          </Box>
        )}

        <Separator />

        {/* 테스트 버튼들 */}
        <VStack gap={2}>
          <Button size="sm" onClick={updateTokenInfo} w="100%">
            토큰 정보 갱신
          </Button>
          <Button size="sm" onClick={handleRefreshToken} w="100%">
            토큰 갱신 테스트
          </Button>
          <Button size="sm" onClick={handleTestAPI} w="100%">
            API 테스트
          </Button>
          <Button size="sm" onClick={handleLogTokenInfo} w="100%">
            콘솔 로그 출력
          </Button>
          <Button size="sm" colorScheme="red" onClick={logout} w="100%">
            강제 로그아웃
          </Button>
        </VStack>

        {/* 테스트 결과 */}
        {testResult && (
          <Box>
            <Text fontSize="sm" fontWeight="semibold" mb={2}>
              테스트 결과:
            </Text>
            <Textarea
              value={testResult}
              readOnly
              size="sm"
              fontSize="xs"
              rows={6}
              resize="none"
            />
          </Box>
        )}
      </VStack>
    </Box>
  );
};

export default AuthDebugPanel;