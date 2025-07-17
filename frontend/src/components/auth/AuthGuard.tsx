import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, Spinner, Text, VStack } from '@chakra-ui/react';
import { useAuthStore } from '../../store/authStore';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean; // true면 인증 필요, false면 인증된 사용자는 리다이렉트
}

const AuthGuard: React.FC<AuthGuardProps> = ({ 
  children, 
  requireAuth = true 
}) => {
  const { isAuthenticated, isLoading, checkAuth, error } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    // 앱 시작 시 인증 상태 확인
    if (isAuthenticated === null) {
      checkAuth();
    }
  }, [checkAuth, isAuthenticated]);

  // 로딩 중
  if (isLoading || isAuthenticated === null) {
    return (
      <Box
        height="100vh"
        display="flex"
        alignItems="center"
        justifyContent="center"
      >
        <VStack gap={4}>
          <Spinner size="xl" color="blue.500" />
          <Text fontSize="lg" color="gray.600">
            인증 상태를 확인하는 중...
          </Text>
        </VStack>
      </Box>
    );
  }

  // 에러 발생 시 (토큰이 유효하지 않거나 서버 오류)
  if (error && requireAuth) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 인증이 필요한 페이지인데 인증되지 않은 경우
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 인증된 사용자가 로그인 페이지에 접근하는 경우
  if (!requireAuth && isAuthenticated) {
    const from = (location.state as any)?.from?.pathname || '/dashboard';
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
};

export default AuthGuard;