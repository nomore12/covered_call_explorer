import {
  Accordion,
  Span,
  Box,
  Text,
  HStack,
  VStack,
  Stack,
  Spinner,
  Alert,
} from '@chakra-ui/react';
import { getTickerColor } from '@/utils/tickerColors';
import { useDashboardStore, type TransactionData } from '@/store/dashboardStore';

const TradeHistory = () => {
  const { 
    transactions, 
    transactionsLoading: isLoading, 
    transactionsError: error 
  } = useDashboardStore();

  // 날짜 순서대로 정렬 (최신순) - API에서 이미 정렬되어 오지만 안전하게 재정렬
  const sortedItems = transactions.sort(
    (a: TransactionData, b: TransactionData) =>
      new Date(b.transaction_date).getTime() -
      new Date(a.transaction_date).getTime()
  );

  // 로딩 상태 렌더링
  if (isLoading) {
    return (
      <VStack gap={4} align='stretch'>
        <Text fontSize='xl' fontWeight='bold' mb={4}>
          거래 내역
        </Text>
        <Box textAlign='center' py={8}>
          <Spinner size='lg' />
          <Text mt={4} color='gray.500'>
            거래 데이터를 불러오는 중...
          </Text>
        </Box>
      </VStack>
    );
  }

  // 에러 상태 렌더링
  if (error) {
    return (
      <VStack gap={4} align='stretch'>
        <Text fontSize='xl' fontWeight='bold' mb={4}>
          거래 내역
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
    <VStack gap={4} align='stretch'>
      <Accordion.Root collapsible defaultValue={[]}>
        {sortedItems.map((item: TransactionData) => (
          <Accordion.Item key={item.id} value={`trade-${item.id}`}>
            <Accordion.ItemTrigger>
              <Stack 
                direction={{ base: 'column', lg: 'row' }} 
                justify='space-between' 
                w='100%'
                gap={{ base: 2, lg: 4 }}
                align={{ base: 'stretch', lg: 'center' }}
              >
                <Stack 
                  direction={{ base: 'column', md: 'row' }} 
                  gap={{ base: 2, md: 4 }}
                  flex={1}
                >
                  <Stack 
                    direction={{ base: 'row', sm: 'column', md: 'row' }}
                    gap={{ base: 3, sm: 1, md: 4 }}
                    align={{ base: 'center', sm: 'flex-start', md: 'center' }}
                  >
                    <Span 
                      fontSize={{ base: 'xs', md: 'sm' }} 
                      color='gray.600'
                      minW={{ base: 'auto', lg: '100px' }}
                    >
                      {item.transaction_date}
                    </Span>
                    <Span
                      fontWeight='semibold'
                      fontSize={{ base: 'sm', md: 'md' }}
                      color={getTickerColor(item.ticker)}
                    >
                      {item.ticker}
                    </Span>
                  </Stack>
                  
                  <Stack 
                    direction={{ base: 'row', sm: 'column', md: 'row' }}
                    gap={{ base: 3, sm: 1, md: 4 }}
                    align={{ base: 'center', sm: 'flex-start', md: 'center' }}
                  >
                    <Span fontSize={{ base: 'xs', md: 'sm' }}>
                      {item.shares}주{' '}
                      <Span fontSize='xs' color='gray.500'>
                        (${item.price_per_share.toFixed(2)})
                      </Span>
                    </Span>
                    <Span 
                      fontWeight='medium' 
                      color='blue.600'
                      fontSize={{ base: 'xs', md: 'sm' }}
                    >
                      ${item.total_amount_usd.toLocaleString()}
                    </Span>
                    <Span 
                      fontWeight='medium' 
                      color='gray.500'
                      fontSize={{ base: 'xs', md: 'sm' }}
                    >
                      ₩{item.krw_amount.toLocaleString()}
                    </Span>
                  </Stack>
                  
                  {item.dividend_reinvestment > 0 && (
                    <Span
                      fontSize='xs'
                      color='green.600'
                      bg='green.50'
                      px={2}
                      py={1}
                      borderRadius='md'
                      alignSelf={{ base: 'flex-start', md: 'center' }}
                      mt={{ base: 1, md: 0 }}
                    >
                      배당금 재투자
                    </Span>
                  )}
                </Stack>
                <Box alignSelf={{ base: 'flex-end', lg: 'center' }}>
                  <Accordion.ItemIndicator />
                </Box>
              </Stack>
            </Accordion.ItemTrigger>
            <Accordion.ItemContent>
              <Accordion.ItemBody>
                <Stack
                  direction={{ base: 'column', md: 'row' }}
                  gap={{ base: 4, md: 8 }}
                  p={{ base: 3, md: 4 }}
                  bg='gray.50'
                  borderRadius='md'
                  align='stretch'
                >
                  {/* 구매 내역 섹션 */}
                  <Box flex={1}>
                    <Text
                      fontSize={{ base: 'sm', md: 'md' }}
                      fontWeight='bold'
                      color='blue.700'
                      mb={3}
                    >
                      구매 내역
                    </Text>
                    <VStack gap={2} align='stretch'>
                      <Stack 
                        direction={{ base: 'column', sm: 'row' }}
                        justify='space-between'
                        align={{ base: 'flex-start', sm: 'center' }}
                        gap={{ base: 1, sm: 2 }}
                      >
                        <Text fontSize={{ base: 'xs', sm: 'sm' }} color='gray.600'>
                          1주 당 가격:
                        </Text>
                        <Stack 
                          direction={{ base: 'row', sm: 'row' }}
                          gap={2}
                          align='center'
                        >
                          <Text fontSize={{ base: 'sm', md: 'md' }} fontWeight='semibold'>
                            ${item.price_per_share.toFixed(2)}
                          </Text>
                          <Text fontSize={{ base: 'xs', sm: 'sm' }} color='gray.500'>
                            ₩
                            {(
                              item.price_per_share *
                              (item.exchange_rate || 1400)
                            ).toLocaleString()}
                          </Text>
                        </Stack>
                      </Stack>
                      <Stack 
                        direction={{ base: 'column', sm: 'row' }}
                        justify='space-between'
                        align={{ base: 'flex-start', sm: 'center' }}
                        gap={{ base: 1, sm: 2 }}
                      >
                        <Text fontSize={{ base: 'xs', sm: 'sm' }} color='gray.600'>
                          기준 환율:
                        </Text>
                        <Text fontSize={{ base: 'xs', sm: 'sm' }}>
                          ₩{(item.exchange_rate || 1400).toLocaleString()}
                        </Text>
                      </Stack>
                      <Stack 
                        direction={{ base: 'column', sm: 'row' }}
                        justify='space-between'
                        align={{ base: 'flex-start', sm: 'center' }}
                        gap={{ base: 1, sm: 2 }}
                      >
                        <Text fontSize={{ base: 'xs', sm: 'sm' }} color='gray.600'>
                          수량:
                        </Text>
                        <Text fontSize={{ base: 'xs', sm: 'sm' }}>{item.shares}주</Text>
                      </Stack>
                      <Stack 
                        direction={{ base: 'column', sm: 'row' }}
                        justify='space-between'
                        align={{ base: 'flex-start', sm: 'center' }}
                        gap={{ base: 1, sm: 2 }}
                      >
                        <Text fontSize={{ base: 'xs', sm: 'sm' }} color='gray.600'>
                          총 구매금액:
                        </Text>
                        <Stack 
                          direction={{ base: 'row', sm: 'row' }}
                          gap={2}
                          align='center'
                        >
                          <Text fontSize={{ base: 'sm', md: 'md' }} fontWeight='semibold'>
                            ${item.total_amount_usd.toLocaleString()}
                          </Text>
                          <Text fontSize={{ base: 'xs', sm: 'sm' }} color='gray.500'>
                            ₩
                            {(
                              item.total_amount_usd *
                              (item.exchange_rate || 1400)
                            ).toLocaleString()}
                          </Text>
                        </Stack>
                      </Stack>
                    </VStack>
                  </Box>

                  {/* 구분선 - 세로(데스크톱) 또는 가로(모바일) */}
                  <Box 
                    w={{ base: '100%', md: '1px' }} 
                    h={{ base: '1px', md: 'auto' }}
                    bg='gray.300' 
                  />

                  {/* 달러 환전 내역 섹션 */}
                  <Box flex={1}>
                    <Text
                      fontSize={{ base: 'sm', md: 'md' }}
                      fontWeight='bold'
                      color='green.700'
                      mb={3}
                    >
                      달러 환전 내역
                    </Text>
                    <VStack gap={2} align='stretch'>
                      <Stack 
                        direction={{ base: 'column', sm: 'row' }}
                        justify='space-between'
                        align={{ base: 'flex-start', sm: 'center' }}
                        gap={{ base: 1, sm: 2 }}
                      >
                        <Text fontSize={{ base: 'xs', sm: 'sm' }} color='gray.600'>
                          주문 중 환전한 달러:
                        </Text>
                        <Text fontSize={{ base: 'sm', md: 'md' }} fontWeight='semibold'>
                          $
                          {item.dividend_reinvestment > 0
                            ? (
                                item.total_amount_usd -
                                item.dividend_reinvestment
                              ).toLocaleString()
                            : item.total_amount_usd.toLocaleString()}
                        </Text>
                      </Stack>
                      <Stack 
                        direction={{ base: 'column', sm: 'row' }}
                        justify='space-between'
                        align={{ base: 'flex-start', sm: 'center' }}
                        gap={{ base: 1, sm: 2 }}
                      >
                        <Text fontSize={{ base: 'xs', sm: 'sm' }} color='gray.600'>
                          적용환율:
                        </Text>
                        <Text fontSize={{ base: 'xs', sm: 'sm' }}>
                          ₩{(item.exchange_rate || 1400).toLocaleString()}
                        </Text>
                      </Stack>
                      <Stack 
                        direction={{ base: 'column', sm: 'row' }}
                        justify='space-between'
                        align={{ base: 'flex-start', sm: 'center' }}
                        gap={{ base: 1, sm: 2 }}
                      >
                        <Text fontSize={{ base: 'xs', sm: 'sm' }} color='gray.600'>
                          사용한 원화:
                        </Text>
                        <Text fontSize={{ base: 'sm', md: 'md' }} fontWeight='semibold'>
                          ₩{(item.krw_amount || 0).toLocaleString()}
                        </Text>
                      </Stack>
                    </VStack>
                  </Box>
                </Stack>
              </Accordion.ItemBody>
            </Accordion.ItemContent>
          </Accordion.Item>
        ))}
      </Accordion.Root>
    </VStack>
  );
};

export default TradeHistory;
