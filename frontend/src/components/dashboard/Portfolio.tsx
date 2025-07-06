import React from 'react';
import { Chart, useChart } from '@chakra-ui/charts';
import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts';
import { Box, Text, VStack, HStack } from '@chakra-ui/react';

const Portfolio = () => {
  const chart = useChart({
    data: [
      { name: 'TSLY', value: 400, color: 'blue.solid' },
      { name: 'NVDY', value: 300, color: 'orange.solid' },
      { name: 'SMCY', value: 250, color: 'green.solid' },
      { name: 'JEPI', value: 200, color: 'purple.solid' },
      { name: 'SCHD', value: 150, color: 'teal.solid' },
    ],
  });

  const totalValue = chart.data.reduce((sum, item) => sum + item.value, 0);

  return (
    <VStack gap={6} align='stretch'>
      <Box>
        <Text fontSize='xl' fontWeight='bold' mb={4}>
          포트폴리오 분포
        </Text>

        <HStack gap={8} align='flex-start'>
          {/* 차트 */}
          <Box flex={1}>
            <Chart.Root boxSize='300px' mx='auto' chart={chart}>
              <ResponsiveContainer width='100%' height={300}>
                <PieChart>
                  <Pie
                    isAnimationActive={false}
                    data={chart.data}
                    dataKey={chart.key('value')}
                    cx='50%'
                    cy='50%'
                    outerRadius={100}
                    label={({ name, percent }) =>
                      `${name} ${percent ? (percent * 100).toFixed(0) : 0}%`
                    }
                  >
                    {chart.data.map(item => (
                      <Cell key={item.name} fill={chart.color(item.color)} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </Chart.Root>
          </Box>

          {/* 통계 */}
          <VStack gap={4} flex={1} align='stretch'>
            <Box p={4} bg='blue.50' borderRadius='lg'>
              <Text fontSize='sm' color='blue.600' fontWeight='medium'>
                총 포트폴리오 가치
              </Text>
              <Text fontSize='2xl' fontWeight='bold' color='blue.700'>
                ${totalValue.toLocaleString()}
                <Text as='span' fontSize='lg' color='blue.600' ml={2}>
                  ₩{(totalValue * 1300).toLocaleString()}
                </Text>
              </Text>
              <Text fontSize='xs' color='blue.500'>
                USD / KRW
              </Text>
            </Box>

            <VStack gap={2} align='stretch'>
              {chart.data.map(item => (
                <HStack
                  key={item.name}
                  justify='space-between'
                  p={2}
                  bg='gray.50'
                  borderRadius='md'
                >
                  <HStack>
                    <Box
                      w={3}
                      h={3}
                      borderRadius='full'
                      bg={chart.color(item.color)}
                    />
                    <Text fontWeight='medium'>{item.name}</Text>
                  </HStack>
                  <VStack gap={1} align='flex-end' minW='120px'>
                    <Text fontSize='lg' fontWeight='semibold'>
                      ${item.value.toLocaleString()}
                    </Text>
                    <Text fontSize='sm' color='gray.500'>
                      ₩{(item.value * 1300).toLocaleString()}
                    </Text>
                  </VStack>
                </HStack>
              ))}
            </VStack>
          </VStack>
        </HStack>
      </Box>
    </VStack>
  );
};

export default Portfolio;
