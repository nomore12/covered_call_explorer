import React, { useEffect, useState } from 'react';
import { Box, Button, Text, VStack, Alert } from '@chakra-ui/react';
import { useAuthStore } from '../../store/authStore';
import { authTokenManager } from '../../lib/auth';

const TokenExpiryNotification: React.FC = () => {
  const [showNotification, setShowNotification] = useState(false);
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const { refreshToken, logout, updateTokenInfo } = useAuthStore();

  useEffect(() => {
    const checkTokenExpiry = () => {
      updateTokenInfo();
      
      // 토큰 정보를 직접 가져와서 사용 (의존성 제거)
      const currentTokenInfo = authTokenManager.getTokenInfo();
      
      if (currentTokenInfo?.isExpiringSoon && !currentTokenInfo.isExpired) {
        setShowNotification(true);
        
        // 남은 시간 계산
        if (currentTokenInfo.expiryTime) {
          const remaining = Math.max(0, currentTokenInfo.expiryTime.getTime() - Date.now());
          setTimeLeft(Math.floor(remaining / 1000));
        }
      } else {
        setShowNotification(false);
      }
    };

    // 초기 체크
    checkTokenExpiry();

    // 30초마다 체크
    const interval = setInterval(checkTokenExpiry, 30000);

    return () => clearInterval(interval);
  }, [updateTokenInfo]); // tokenInfo 의존성 제거

  // 카운트다운 타이머
  useEffect(() => {
    if (timeLeft > 0) {
      const timer = setTimeout(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [timeLeft]);

  const handleExtendSession = async () => {
    try {
      const success = await refreshToken();
      if (success) {
        setShowNotification(false);
      } else {
        // 갱신 실패 시 로그아웃
        await logout();
      }
    } catch (error) {
      console.error('세션 연장 실패:', error);
      await logout();
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  if (!showNotification) {
    return null;
  }

  return (
    <Box
      position="fixed"
      top={4}
      right={4}
      zIndex={9999}
      maxW="400px"
      bg="white"
      borderRadius="md"
      boxShadow="xl"
      border="1px"
      borderColor="orange.200"
    >
      <Alert.Root status="warning" p={4}>
        <Alert.Indicator />
        <VStack gap={3} align="stretch" w="100%">
          <Box>
            <Alert.Title>세션 만료 임박</Alert.Title>
            <Alert.Description>
              {timeLeft > 60 
                ? `${formatTime(timeLeft)} 후에 세션이 만료됩니다.`
                : `${timeLeft}초 후에 세션이 만료됩니다.`
              }
            </Alert.Description>
          </Box>
          
          <Box display="flex" gap={2}>
            <Button
              size="sm"
              colorScheme="orange"
              onClick={handleExtendSession}
              flex={1}
            >
              세션 연장
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleLogout}
              flex={1}
            >
              로그아웃
            </Button>
          </Box>
        </VStack>
      </Alert.Root>
    </Box>
  );
};

export default TokenExpiryNotification;