import React, { useState, useEffect } from 'react';
import {
  SegmentGroup,
  Text,
  VStack,
  Box,
  HStack,
  Spinner,
  Alert,
} from '@chakra-ui/react';
import { apiClient, API_ENDPOINTS } from '../../lib/api';

interface DividendData {
  id: number;
  date: string;
  ticker: string;
  amount: number;
  shares?: number;
  dividendPerShare?: number;
}

const DividendHistory = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('전체');
  const [dividendHistory, setDividendHistory] = useState<DividendData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 배당금 데이터 가져오기
  useEffect(() => {
    const fetchDividends = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await apiClient.get(API_ENDPOINTS.dividends);
        // API 응답 데이터 검증 및 정규화
        const normalizedData = Array.isArray(response.data)
          ? response.data.map((item: any) => ({
              id: item.id || Date.now() + Math.random(),
              date: item.date || new Date().toISOString().split('T')[0],
              ticker: item.ticker || 'UNKNOWN',
              amount: typeof item.amount === 'number' ? item.amount : 0,
              shares: typeof item.shares === 'number' ? item.shares : undefined,
              dividendPerShare:
                typeof item.dividendPerShare === 'number'
                  ? item.dividendPerShare
                  : undefined,
            }))
          : [];
        console.log(normalizedData);
        setDividendHistory(normalizedData);
      } catch (err) {
        console.error('배당금 데이터 가져오기 실패:', err);
        setError('배당금 데이터를 불러오는데 실패했습니다.');
        // 에러 발생 시 빈 배열로 초기화
        setDividendHistory([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDividends();
  }, []);

  // 고유한 종목 목록 추출
  const symbols = [
    '전체',
    ...Array.from(new Set(dividendHistory.map(item => item.ticker))),
  ];

  // 선택된 종목에 따라 필터링
  const filteredHistory =
    selectedSymbol === '전체'
      ? dividendHistory
      : dividendHistory.filter(item => item.ticker === selectedSymbol);

  // 날짜 순서대로 정렬 (최신순)
  const sortedHistory = filteredHistory.sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  // 로딩 상태 렌더링
  if (isLoading) {
    return (
      <VStack gap={6} align='stretch'>
        <Text fontSize='xl' fontWeight='bold'>
          배당금 내역
        </Text>
        <Box textAlign='center' py={8}>
          <Spinner size='lg' />
          <Text mt={4} color='gray.500'>
            배당금 데이터를 불러오는 중...
          </Text>
        </Box>
      </VStack>
    );
  }

  // 에러 상태 렌더링
  if (error) {
    return (
      <VStack gap={6} align='stretch'>
        <Text fontSize='xl' fontWeight='bold'>
          배당금 내역
        </Text>
        <Alert.Root status='error'>
          <Alert.Indicator />
          <Alert.Content>
            <Alert.Title>오류 발생</Alert.Title>
            <Alert.Description>{error}</Alert.Description>
          </Alert.Content>
        </Alert.Root>
      </VStack>
    );
  }

  return (
    <VStack gap={6} align='stretch'>
      <Text fontSize='xl' fontWeight='bold'>
        배당금 내역
      </Text>

      {/* 종목 필터 */}
      <VStack align='flex-start' gap={3}>
        <Text fontSize='md' fontWeight='semibold' color='gray.700'>
          종목별 필터
        </Text>
        <SegmentGroup.Root
          defaultValue='전체'
          onValueChange={details => setSelectedSymbol(details.value || '전체')}
        >
          <SegmentGroup.Indicator />
          <SegmentGroup.Items items={symbols} />
        </SegmentGroup.Root>
      </VStack>

      {/* 총 배당금 요약 */}
      <Box
        p={4}
        bg='green.50'
        borderRadius='lg'
        border='1px solid'
        borderColor='green.200'
      >
        <HStack justify='space-between' align='center'>
          <VStack align='flex-start' gap={1}>
            <Text fontSize='sm' color='green.700' fontWeight='medium'>
              {selectedSymbol === '전체' ? '전체 종목' : selectedSymbol} 총
              배당금
            </Text>
            <Text fontSize='xs' color='green.600'>
              {sortedHistory.length}건의 배당금 내역
            </Text>
          </VStack>
          <Text fontSize='2xl' fontWeight='bold' color='green.700'>
            $
            {sortedHistory
              .reduce((sum, item) => sum + (item.amount || 0), 0)
              .toFixed(2)}
          </Text>
        </HStack>
      </Box>

      {/* 배당금 내역 리스트 */}
      <VStack gap={3} align='stretch'>
        {sortedHistory.map(item => (
          <Box
            key={item.id}
            p={4}
            bg='white'
            borderRadius='lg'
            border='1px solid'
            borderColor='gray.200'
            _hover={{
              borderColor: 'blue.300',
              boxShadow: 'md',
            }}
            transition='all 0.2s'
          >
            <HStack justify='space-between' align='center'>
              <HStack gap={6}>
                <VStack align='flex-start' gap={1}>
                  <Text fontSize='sm' color='gray.600'>
                    {item.date}
                  </Text>
                  <Text fontSize='lg' fontWeight='bold' color='blue.600'>
                    {item.ticker}
                  </Text>
                </VStack>

                <VStack align='flex-start' gap={1}>
                  <Text fontSize='sm' color='gray.600'>
                    주식 수량
                  </Text>
                  <Text fontSize='md' fontWeight='semibold'>
                    {item.shares ? `${item.shares}주` : '-'}
                  </Text>
                </VStack>

                <VStack align='flex-start' gap={1}>
                  <Text fontSize='sm' color='gray.600'>
                    1주당 배당금
                  </Text>
                  <Text fontSize='md' fontWeight='semibold'>
                    {item.dividendPerShare
                      ? `$${item.dividendPerShare.toFixed(4)}`
                      : '-'}
                  </Text>
                </VStack>
              </HStack>

              <VStack align='flex-end' gap={1}>
                <Text fontSize='sm' color='gray.600'>
                  총 배당금
                </Text>
                <Text fontSize='xl' fontWeight='bold' color='green.600'>
                  ${(item.amount || 0).toFixed(2)}
                </Text>
              </VStack>
            </HStack>
          </Box>
        ))}
      </VStack>

      {/* 배당금 내역이 없을 때 */}
      {sortedHistory.length === 0 && (
        <Box
          p={8}
          textAlign='center'
          bg='gray.50'
          borderRadius='lg'
          border='1px dashed'
          borderColor='gray.300'
        >
          <Text fontSize='md' color='gray.500'>
            선택한 종목의 배당금 내역이 없습니다.
          </Text>
        </Box>
      )}
    </VStack>
  );
};

export default DividendHistory;
