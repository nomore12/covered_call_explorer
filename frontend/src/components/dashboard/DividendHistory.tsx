import React, { useState } from 'react';
import {
  SegmentGroup,
  Stack,
  Text,
  VStack,
  Box,
  HStack,
  Span,
} from '@chakra-ui/react';

const DividendHistory = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('전체');

  // 배당금 내역 데이터
  const dividendHistory = [
    {
      id: 1,
      date: '2024-01-15',
      symbol: 'TSLY',
      dividendAmount: 125.5,
      shares: 100,
      dividendPerShare: 1.255,
    },
    {
      id: 2,
      date: '2024-01-10',
      symbol: 'NVDY',
      dividendAmount: 89.25,
      shares: 50,
      dividendPerShare: 1.785,
    },
    {
      id: 3,
      date: '2024-01-05',
      symbol: 'SMCY',
      dividendAmount: 67.8,
      shares: 75,
      dividendPerShare: 0.904,
    },
    {
      id: 4,
      date: '2023-12-28',
      symbol: 'JEPI',
      dividendAmount: 152.0,
      shares: 200,
      dividendPerShare: 0.76,
    },
    {
      id: 5,
      date: '2023-12-20',
      symbol: 'SCHD',
      dividendAmount: 44.0,
      shares: 150,
      dividendPerShare: 0.293,
    },
    {
      id: 6,
      date: '2023-12-15',
      symbol: 'TSLY',
      dividendAmount: 118.75,
      shares: 100,
      dividendPerShare: 1.1875,
    },
    {
      id: 7,
      date: '2023-12-10',
      symbol: 'NVDY',
      dividendAmount: 82.5,
      shares: 50,
      dividendPerShare: 1.65,
    },
  ];

  // 고유한 종목 목록 추출
  const symbols = [
    '전체',
    ...Array.from(new Set(dividendHistory.map(item => item.symbol))),
  ];

  // 선택된 종목에 따라 필터링
  const filteredHistory =
    selectedSymbol === '전체'
      ? dividendHistory
      : dividendHistory.filter(item => item.symbol === selectedSymbol);

  // 날짜 순서대로 정렬 (최신순)
  const sortedHistory = filteredHistory.sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

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
                    {item.symbol}
                  </Text>
                </VStack>

                <VStack align='flex-start' gap={1}>
                  <Text fontSize='sm' color='gray.600'>
                    주식 수량
                  </Text>
                  <Text fontSize='md' fontWeight='semibold'>
                    {item.shares}주
                  </Text>
                </VStack>

                <VStack align='flex-start' gap={1}>
                  <Text fontSize='sm' color='gray.600'>
                    1주당 배당금
                  </Text>
                  <Text fontSize='md' fontWeight='semibold'>
                    ${item.dividendPerShare.toFixed(4)}
                  </Text>
                </VStack>
              </HStack>

              <VStack align='flex-end' gap={1}>
                <Text fontSize='sm' color='gray.600'>
                  총 배당금
                </Text>
                <Text fontSize='xl' fontWeight='bold' color='green.600'>
                  ${item.dividendAmount.toFixed(2)}
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
