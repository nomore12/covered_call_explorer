import {
  Box,
  Button,
  Container,
  Input,
  Text,
  VStack,
  Flex,
  Alert,
} from '@chakra-ui/react';
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

const Login = () => {
  const [id, setId] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const { login, isLoading, error, clearError, isAuthenticated } = useAuthStore();

  // 이미 로그인된 경우 대시보드로 리다이렉트
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!id.trim() || !password.trim()) {
      return;
    }

    try {
      await login(id.trim(), password);
      navigate('/dashboard');
    } catch (error) {
      // 에러는 store에서 관리됨
      console.error('Login failed:', error);
    }
  };

  return (
    <Container
      maxW={{ base: '100%' }}
      minW={{ sm: 'container.xl', md: 'container.2xl' }}
      height='100vh'
      p={0}
      centerContent
    >
      <Flex
        direction='column'
        alignItems='center'
        justifyContent='center'
        height='100%'
        w='100%'
      >
        <Box
          w={{ base: '100%', md: '480px' }}
          bg='white'
          p={4}
          borderRadius='lg'
          boxShadow='lg'
          border='1px'
          borderColor='gray.200'
        >
          <VStack gap={6}>
            <Text fontSize='2xl' fontWeight='bold' color='gray.800'>
              로그인
            </Text>

            {error && (
              <Alert.Root status='error' w='100%'>
                <Alert.Indicator />
                <Alert.Content>
                  <Alert.Title>로그인 실패</Alert.Title>
                  <Alert.Description>{error}</Alert.Description>
                </Alert.Content>
              </Alert.Root>
            )}

            <form onSubmit={handleSubmit} style={{ width: '100%' }}>
              <VStack gap={4} w='100%'>
                <Box w='100%'>
                  <Text mb={2} fontWeight='medium'>
                    아이디
                  </Text>
                  <Input
                    type='text'
                    value={id}
                    onChange={e => setId(e.target.value)}
                    placeholder='아이디를 입력하세요'
                    size='lg'
                    required
                  />
                </Box>

                <Box w='100%'>
                  <Text mb={2} fontWeight='medium'>
                    비밀번호
                  </Text>
                  <Input
                    type='password'
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder='비밀번호를 입력하세요'
                    size='lg'
                    required
                  />
                </Box>

                <Button
                  type='submit'
                  colorScheme='blue'
                  size='lg'
                  w='100%'
                  loading={isLoading}
                >
                  {isLoading ? '로그인 중...' : '로그인'}
                </Button>
              </VStack>
            </form>
          </VStack>
        </Box>
      </Flex>
    </Container>
  );
};

export default Login;
