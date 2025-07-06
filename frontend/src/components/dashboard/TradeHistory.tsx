import React from 'react';
import { Accordion, Span, Box, Text, HStack, VStack } from '@chakra-ui/react';

const TradeHistory = () => {
  const tradeItems = [
    {
      value: 'trade-1',
      date: '2024-01-15',
      symbol: 'TSLY',
      quantity: 100,
      pricePerShare: 45.0,
      totalPrice: 4500,
      exchangeRate: 1300,
      exchangedUSD: 4500,
      usedKRW: 5850000,
      title: 'TSLY 100주 매수',
    },
    {
      value: 'trade-2',
      date: '2024-01-10',
      symbol: 'NVDY',
      quantity: 50,
      pricePerShare: 64.0,
      totalPrice: 3200,
      exchangeRate: 1295,
      exchangedUSD: 3200,
      usedKRW: 4144000,
      title: 'NVDY 50주 매수',
    },
    {
      value: 'trade-3',
      date: '2024-01-05',
      symbol: 'SMCY',
      quantity: 75,
      pricePerShare: 37.33,
      totalPrice: 2800,
      exchangeRate: 1305,
      exchangedUSD: 2800,
      usedKRW: 3654000,
      title: 'SMCY 75주 매수',
    },
    {
      value: 'trade-4',
      date: '2023-12-28',
      symbol: 'JEPI',
      quantity: 200,
      pricePerShare: 19.0,
      totalPrice: 3800,
      exchangeRate: 1290,
      exchangedUSD: 3800,
      usedKRW: 4902000,
      title: 'JEPI 200주 매수',
    },
    {
      value: 'trade-5',
      date: '2023-12-20',
      symbol: 'SCHD',
      quantity: 150,
      pricePerShare: 14.67,
      totalPrice: 2200,
      exchangeRate: 1310,
      exchangedUSD: 2200,
      usedKRW: 2882000,
      title: 'SCHD 150주 매수',
    },
  ];

  // 날짜 순서대로 정렬 (최신순)
  const sortedItems = tradeItems.sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  return (
    <VStack gap={4} align='stretch'>
      <Text fontSize='xl' fontWeight='bold' mb={4}>
        거래 내역
      </Text>

      <Accordion.Root collapsible defaultValue={['trade-1']}>
        {sortedItems.map(item => (
          <Accordion.Item key={item.value} value={item.value}>
            <Accordion.ItemTrigger>
              <HStack justify='space-between' w='100%'>
                <HStack gap={4}>
                  <Span fontSize='sm' color='gray.600' minW='100px'>
                    {item.date}
                  </Span>
                  <Span fontWeight='semibold' minW='60px'>
                    {item.symbol}
                  </Span>
                  <Span fontSize='sm' minW='60px'>
                    {item.quantity}주
                  </Span>
                  <Span fontWeight='medium' color='blue.600'>
                    ${item.totalPrice.toLocaleString()}
                  </Span>
                </HStack>
                <Accordion.ItemIndicator />
              </HStack>
            </Accordion.ItemTrigger>
            <Accordion.ItemContent>
              <Accordion.ItemBody>
                <HStack
                  gap={8}
                  p={4}
                  bg='gray.50'
                  borderRadius='md'
                  align='stretch'
                  h='100%'
                >
                  {/* 구매 내역 섹션 */}
                  <Box flex={1}>
                    <Text
                      fontSize='md'
                      fontWeight='bold'
                      color='blue.700'
                      mb={3}
                    >
                      구매 내역
                    </Text>
                    <VStack gap={2} align='stretch'>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          1주 당 가격:
                        </Text>
                        <HStack gap={2}>
                          <Text fontSize='md' fontWeight='semibold'>
                            ${item.pricePerShare.toFixed(2)}
                          </Text>
                          <Text fontSize='sm' color='gray.500'>
                            ₩
                            {(
                              item.pricePerShare * item.exchangeRate
                            ).toLocaleString()}
                          </Text>
                        </HStack>
                      </HStack>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          기준 환율:
                        </Text>
                        <Text fontSize='sm'>
                          ₩{item.exchangeRate.toLocaleString()}
                        </Text>
                      </HStack>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          수량:
                        </Text>
                        <Text fontSize='sm'>{item.quantity}주</Text>
                      </HStack>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          총 구매금액:
                        </Text>
                        <HStack gap={2}>
                          <Text fontSize='md' fontWeight='semibold'>
                            ${item.totalPrice.toLocaleString()}
                          </Text>
                          <Text fontSize='sm' color='gray.500'>
                            ₩
                            {(
                              item.totalPrice * item.exchangeRate
                            ).toLocaleString()}
                          </Text>
                        </HStack>
                      </HStack>
                    </VStack>
                  </Box>

                  {/* 세로 구분선 */}
                  <Box w='1px' bg='gray.300' />

                  {/* 달러 환전 내역 섹션 */}
                  <Box flex={1}>
                    <Text
                      fontSize='md'
                      fontWeight='bold'
                      color='green.700'
                      mb={3}
                    >
                      달러 환전 내역
                    </Text>
                    <VStack gap={2} align='stretch'>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          주문 중 환전한 달러:
                        </Text>
                        <Text fontSize='md' fontWeight='semibold'>
                          ${item.exchangedUSD.toLocaleString()}
                        </Text>
                      </HStack>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          적용환율:
                        </Text>
                        <Text fontSize='sm'>
                          ₩{item.exchangeRate.toLocaleString()}
                        </Text>
                      </HStack>
                      <HStack justify='space-between'>
                        <Text fontSize='sm' color='gray.600'>
                          사용한 원화:
                        </Text>
                        <Text fontSize='md' fontWeight='semibold'>
                          ₩{item.usedKRW.toLocaleString()}
                        </Text>
                      </HStack>
                    </VStack>
                  </Box>
                </HStack>
              </Accordion.ItemBody>
            </Accordion.ItemContent>
          </Accordion.Item>
        ))}
      </Accordion.Root>
    </VStack>
  );
};

export default TradeHistory;
