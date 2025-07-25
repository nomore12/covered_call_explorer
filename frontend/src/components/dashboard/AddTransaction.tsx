import React, { useState } from 'react';
import {
  Button,
  Input,
  VStack,
  HStack,
  Field,
  Select,
  NumberInput,
  Card,
  Heading,
  Spinner,
  Alert,
  createToaster,
  createListCollection,
} from '@chakra-ui/react';
import { useDashboardStore } from '@/store/dashboardStore';

interface TransactionFormData {
  transactionType: 'buy' | 'sell';
  ticker: string;
  transactionDate: string;
  transactionTime: string;
  pricePerShareUSD: number;
  pricePerShareKRW: number;
  baseExchangeRate: number;
  quantity: number;
  totalAmountUSD: number;
  totalAmountKRW: number;
  exchangedUSD: number;
  appliedExchangeRate: number;
  usedKRW: number;
}

const tickers = createListCollection({
  items: [
    { label: 'TSLY', value: 'TSLY' },
    { label: 'NVDY', value: 'NVDY' },
    { label: 'SMCY', value: 'SMCY' },
  ],
});

const transactionTypes = createListCollection({
  items: [
    { label: '매수 (Buy)', value: 'buy' },
    { label: '매도 (Sell)', value: 'sell' },
  ],
});

const AddTransaction: React.FC = () => {
  const { addTransaction } = useDashboardStore();
  const [formData, setFormData] = useState<TransactionFormData>({
    transactionType: 'buy',
    ticker: '',
    transactionDate: '',
    transactionTime: '',
    pricePerShareUSD: 0,
    pricePerShareKRW: 0,
    baseExchangeRate: 1400,
    quantity: 0,
    totalAmountUSD: 0,
    totalAmountKRW: 0,
    exchangedUSD: 0,
    appliedExchangeRate: 1400,
    usedKRW: 0,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const toaster = createToaster({
    placement: 'top',
  });

  const handleInputChange = (field: keyof TransactionFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted, formData:', formData);
    setIsSubmitting(true);

    try {
      // API 요청 데이터 준비
      const requestData = {
        transaction_type: formData.transactionType.toUpperCase(),
        ticker: formData.ticker.toUpperCase(),
        shares:
          formData.transactionType === 'sell'
            ? -formData.quantity
            : formData.quantity,
        price_per_share: formData.pricePerShareUSD,
        total_amount_usd: formData.totalAmountUSD,
        exchange_rate: formData.appliedExchangeRate,
        krw_amount: formData.usedKRW,
        transaction_date: formData.transactionDate,
        dividend_reinvestment: 0,
      };

      console.log('Request data:', requestData);
      console.log(
        'Making POST request to:',
        'http://localhost:5000/transactions'
      );

      // Store를 통해 거래 추가
      await addTransaction(requestData);
      console.log('Transaction added successfully via store');

      toaster.create({
        title: `${formData.transactionType === 'buy' ? '매수' : '매도'} 거래 내역이 성공적으로 저장되었습니다.`,
        duration: 3000,
      });

      // 폼 초기화
      setFormData({
        transactionType: 'buy',
        ticker: '',
        transactionDate: '',
        transactionTime: '',
        pricePerShareUSD: 0,
        pricePerShareKRW: 0,
        baseExchangeRate: 1400,
        quantity: 0,
        totalAmountUSD: 0,
        totalAmountKRW: 0,
        exchangedUSD: 0,
        appliedExchangeRate: 1400,
        usedKRW: 0,
      });
    } catch (error) {
      console.error('Submit error:', error);
      toaster.create({
        title: '오류가 발생했습니다.',
        description:
          error instanceof Error
            ? error.message
            : '알 수 없는 오류가 발생했습니다.',
        duration: 5000,
      });
    } finally {
      console.log('Setting isSubmitting to false');
      setIsSubmitting(false);
    }
  };

  return (
    <Card.Root maxW='2xl' mx='auto'>
      <Card.Header>
        <Heading size='lg'>거래 내역 추가</Heading>
      </Card.Header>

      <Card.Body>
        <form onSubmit={handleSubmit}>
          <VStack gap={4} align='stretch'>
            {/* 거래 유형 */}
            <Field.Root required>
              <Field.Label>거래 유형</Field.Label>
              <Select.Root
                collection={transactionTypes}
                value={[formData.transactionType]}
                onValueChange={details =>
                  handleInputChange('transactionType', details.value[0])
                }
              >
                <Select.Trigger>
                  <Select.ValueText placeholder='거래 유형을 선택하세요' />
                </Select.Trigger>
                <Select.Content>
                  {transactionTypes.items.map(item => (
                    <Select.Item item={item} key={item.value}>
                      {item.label}
                    </Select.Item>
                  ))}
                </Select.Content>
              </Select.Root>
            </Field.Root>

            {/* 종목 */}
            <Field.Root required>
              <Field.Label>종목</Field.Label>
              <Input
                value={formData.ticker}
                onChange={e => handleInputChange('ticker', e.target.value)}
                placeholder='예: NVDY, TSLY'
                textTransform='uppercase'
              />
            </Field.Root>

            {/* 거래완료 날짜 및 시간 */}
            <HStack>
              <Field.Root required>
                <Field.Label>
                  {formData.transactionType === 'buy'
                    ? '구매완료 날짜'
                    : '매도완료 날짜'}
                </Field.Label>
                <Input
                  type='date'
                  value={formData.transactionDate}
                  onChange={e =>
                    handleInputChange('transactionDate', e.target.value)
                  }
                />
              </Field.Root>
              <Field.Root required>
                <Field.Label>시간</Field.Label>
                <Input
                  type='time'
                  value={formData.transactionTime}
                  onChange={e =>
                    handleInputChange('transactionTime', e.target.value)
                  }
                />
              </Field.Root>
            </HStack>

            {/* 1주당 가격 */}
            <HStack>
              <Field.Root required flex={1}>
                <Field.Label>
                  1주당 {formData.transactionType === 'buy' ? '구매' : '매도'}
                  가격($)
                </Field.Label>
                <NumberInput.Root
                  value={formData.pricePerShareUSD.toString()}
                  onValueChange={details =>
                    handleInputChange(
                      'pricePerShareUSD',
                      parseFloat(details.value) || 0
                    )
                  }
                  min={0}
                >
                  <NumberInput.Input placeholder='예: 150.5000' />
                </NumberInput.Root>
              </Field.Root>
              <Field.Root flex={1}>
                <Field.Label>
                  1주당 {formData.transactionType === 'buy' ? '구매' : '매도'}
                  가격(₩)
                </Field.Label>
                <NumberInput.Root
                  value={formData.pricePerShareKRW.toString()}
                  onValueChange={details =>
                    handleInputChange(
                      'pricePerShareKRW',
                      parseFloat(details.value) || 0
                    )
                  }
                  min={0}
                >
                  <NumberInput.Input placeholder='예: 210,700' />
                </NumberInput.Root>
              </Field.Root>
            </HStack>

            {/* 기준 환율 */}
            <Field.Root required>
              <Field.Label>기준 환율 (KRW/USD)</Field.Label>
              <NumberInput.Root
                value={formData.baseExchangeRate.toString()}
                onValueChange={details =>
                  handleInputChange(
                    'baseExchangeRate',
                    parseFloat(details.value) || 1400
                  )
                }
                min={1000}
                max={2000}
              >
                <NumberInput.Input placeholder='예: 1400.50' />
              </NumberInput.Root>
            </Field.Root>

            {/* 수량 */}
            <Field.Root required>
              <Field.Label>수량</Field.Label>
              <NumberInput.Root
                value={formData.quantity.toString()}
                onValueChange={details =>
                  handleInputChange('quantity', parseInt(details.value) || 0)
                }
                min={1}
              >
                <NumberInput.Input placeholder='예: 10' />
              </NumberInput.Root>
            </Field.Root>

            {/* 총 거래 금액 */}
            <HStack>
              <Field.Root flex={1}>
                <Field.Label>
                  총 {formData.transactionType === 'buy' ? '구매' : '매도'}{' '}
                  금액($)
                </Field.Label>
                <NumberInput.Root
                  value={formData.totalAmountUSD.toString()}
                  onValueChange={details =>
                    handleInputChange(
                      'totalAmountUSD',
                      parseFloat(details.value) || 0
                    )
                  }
                  min={0}
                >
                  <NumberInput.Input placeholder='예: 1,505.00' />
                </NumberInput.Root>
              </Field.Root>
              <Field.Root flex={1}>
                <Field.Label>
                  총 {formData.transactionType === 'buy' ? '구매' : '매도'}{' '}
                  금액(₩)
                </Field.Label>
                <NumberInput.Root
                  value={formData.totalAmountKRW.toString()}
                  onValueChange={details =>
                    handleInputChange(
                      'totalAmountKRW',
                      parseFloat(details.value) || 0
                    )
                  }
                  min={0}
                >
                  <NumberInput.Input placeholder='예: 2,107,000' />
                </NumberInput.Root>
              </Field.Root>
            </HStack>

            {/* 주문 중 환전한 달러 */}
            <Field.Root required>
              <Field.Label>주문 중 환전한 달러</Field.Label>
              <NumberInput.Root
                value={formData.exchangedUSD.toString()}
                onValueChange={details =>
                  handleInputChange(
                    'exchangedUSD',
                    parseFloat(details.value) || 0
                  )
                }
                min={0}
              >
                <NumberInput.Input placeholder='예: 1505.00' />
              </NumberInput.Root>
            </Field.Root>

            {/* 적용 환율 */}
            <Field.Root required>
              <Field.Label>적용 환율 (KRW/USD)</Field.Label>
              <NumberInput.Root
                value={formData.appliedExchangeRate.toString()}
                onValueChange={details =>
                  handleInputChange(
                    'appliedExchangeRate',
                    parseFloat(details.value) || 1400
                  )
                }
                min={1000}
                max={2000}
              >
                <NumberInput.Input placeholder='예: 1394.70' />
              </NumberInput.Root>
            </Field.Root>

            {/* 사용한 원화 */}
            <Field.Root required>
              <Field.Label>사용한 원화</Field.Label>
              <NumberInput.Root
                value={formData.usedKRW.toString()}
                onValueChange={details =>
                  handleInputChange('usedKRW', parseFloat(details.value) || 0)
                }
                min={0}
              >
                <NumberInput.Input placeholder='예: 2,100,000' />
              </NumberInput.Root>
            </Field.Root>

            {/* 입력 요약 정보 */}
            <Alert.Root status='info'>
              <Alert.Indicator />
              <Alert.Content>
                <Alert.Title>입력 요약</Alert.Title>
                <Alert.Description>
                  {formData.transactionType &&
                    `거래유형: ${formData.transactionType === 'buy' ? '매수' : '매도'}`}
                  {formData.ticker && ` | 종목: ${formData.ticker}`}
                  {formData.quantity > 0 && ` | 수량: ${formData.quantity}주`}
                  {formData.pricePerShareUSD > 0 &&
                    ` | 1주당 가격: $${formData.pricePerShareUSD}`}
                  {formData.totalAmountUSD > 0 &&
                    ` | 총 ${formData.transactionType === 'buy' ? '구매' : '매도'}금액: $${formData.totalAmountUSD.toFixed(2)}`}
                </Alert.Description>
              </Alert.Content>
            </Alert.Root>

            {/* 제출 버튼 */}
            <Button
              type='submit'
              colorScheme='blue'
              size='lg'
              disabled={isSubmitting}
              mt={4}
            >
              {isSubmitting ? (
                <>
                  <Spinner size='sm' mr={2} />
                  저장 중...
                </>
              ) : (
                `${formData.transactionType === 'buy' ? '매수' : '매도'} 내역 저장`
              )}
            </Button>
          </VStack>
        </form>
      </Card.Body>
    </Card.Root>
  );
};

export default AddTransaction;
