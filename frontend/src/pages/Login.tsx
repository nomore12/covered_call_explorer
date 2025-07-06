import {
  Box,
  Button,
  Container,
  Input,
  Text,
  VStack,
  Flex,
} from '@chakra-ui/react';
import React, { useState } from 'react';

const Login = () => {
  const [id, setId] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // // 로그인 로직 구현
    // try {
    //   // API 호출 로직
    //   console.log('Login attempt:', { email, password });

    //   // 성공 메시지
    //   alert('로그인 성공');
    // } catch (error) {
    //   // 에러 메시지
    //   alert('로그인 실패: 이메일과 비밀번호를 확인해주세요.');
    // } finally {
    //   setIsLoading(false);
    // }
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
