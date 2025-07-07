import React, { useState } from 'react';
import {
  Button,
  Input,
  VStack,
  Field,
  NumberInput,
  Card,
  Heading,
  Spinner,
  Alert,
  createToaster,
} from '@chakra-ui/react';
import { apiClient, API_ENDPOINTS } from '../../lib/api';

interface DividendFormData {
  ticker: string;
  amount: number;
  date: string;
}

const AddDividends: React.FC = () => {
  const [formData, setFormData] = useState<DividendFormData>({
    ticker: '',
    amount: 0,
    date: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const toaster = createToaster({
    placement: 'top',
  });

  const handleInputChange = (field: keyof DividendFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const requestData = {
        ticker: formData.ticker.toUpperCase(),
        amount: formData.amount,
        date: formData.date,
      };

      await apiClient.post(API_ENDPOINTS.dividends, requestData);

      toaster.create({
        title: '배당금 내역이 성공적으로 저장되었습니다.',
        duration: 3000,
      });

      // 폼 초기화
      setFormData({
        ticker: '',
        amount: 0,
        date: '',
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
      setIsSubmitting(false);
    }
  };

  return (
    <Card.Root maxW="2xl" mx="auto" p={6}>
      <Card.Header>
        <Heading size="lg">배당금 내역 추가</Heading>
      </Card.Header>

      <Card.Body>
        <form onSubmit={handleSubmit}>
          <VStack gap={4} align="stretch">
            {/* 종목 */}
            <Field.Root required>
              <Field.Label>종목</Field.Label>
              <Input
                value={formData.ticker}
                onChange={e => handleInputChange('ticker', e.target.value)}
                placeholder="예: NVDY, TSLY"
                textTransform="uppercase"
              />
            </Field.Root>

            {/* 날짜 */}
            <Field.Root required>
              <Field.Label>배당금 수령 날짜</Field.Label>
              <Input
                type="date"
                value={formData.date}
                onChange={e => handleInputChange('date', e.target.value)}
              />
            </Field.Root>

            {/* 배당금 금액 */}
            <Field.Root required>
              <Field.Label>배당금 금액 ($)</Field.Label>
              <NumberInput.Root
                value={formData.amount.toString()}
                onValueChange={details =>
                  handleInputChange('amount', parseFloat(details.value) || 0)
                }
                min={0}
              >
                <NumberInput.Input placeholder="예: 50.25" />
              </NumberInput.Root>
            </Field.Root>

            {/* 입력 요약 정보 */}
            <Alert.Root status="info">
              <Alert.Indicator />
              <Alert.Content>
                <Alert.Title>입력 요약</Alert.Title>
                <Alert.Description>
                  {formData.ticker && `종목: ${formData.ticker}`}
                  {formData.amount > 0 && ` | 배당금: $${formData.amount.toFixed(2)}`}
                  {formData.date && ` | 수령일: ${formData.date}`}
                </Alert.Description>
              </Alert.Content>
            </Alert.Root>

            {/* 제출 버튼 */}
            <Button
              type="submit"
              colorScheme="blue"
              size="lg"
              disabled={isSubmitting}
              mt={4}
            >
              {isSubmitting ? (
                <>
                  <Spinner size="sm" mr={2} />
                  저장 중...
                </>
              ) : (
                '배당금 내역 저장'
              )}
            </Button>
          </VStack>
        </form>
      </Card.Body>
    </Card.Root>
  );
};

export default AddDividends;
