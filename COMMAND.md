# 텔레그램 봇 명령어 구조

## 핵심 명령어 (3개)

### /buy - 매수 기록

사용자: /buy

봇: 어떤 종목을 매수하셨나요? (예: NVDY)
사용자: NVDY

봇: NVDY 매수 정보를 순서대로 입력해주세요.

1️⃣ 몇 주를 매수하셨나요?
사용자: 10

2️⃣ 1주당 가격을 입력하세요
달러 가격만 입력 (예: 150.50):
사용자: 150.50

3️⃣ 총 구매금액(달러)을 입력하세요:
사용자: 1505.00

4️⃣ 주문 중 환전한 달러를 입력하세요:
(배당금으로만 구매한 경우 0 입력)
사용자: 1000.00

5️⃣ 환전에 사용한 원화를 입력하세요:
(수수료 포함, 환전하지 않았으면 0 입력)
사용자: 1400500

봇: ✅ 매수 내역 확인
━━━━━━━━━━━━━━━━━━
📊 NVDY 10주 매수

- 주당가: $150.50
- 총 구매: $1,505.00

💱 환전 정보

- 환전액: $1,000.00
- 사용 원화: ₩1,400,500
- 적용 환율: ₩1,400.50

💰 배당금 사용: $505.00
━━━━━━━━━━━━━━━━━━

저장하시겠습니까? (예/아니오/다시)

- 티커 별도 입력: 오타 수정 기회 제공
- 원화 가격 생략: 달러 가격과 환율로 자동 계산
- 명확한 안내: 각 단계마다 예시 제공
- 0 입력 처리: 배당금만 사용한 경우 대응
- '다시' 옵션: 처음부터 재입력 가능
- 단계별 입력 중 quit 또는 exit 입력 시 입력 취소.

#### 예외사항 처리

- 배당금으로만 구매한 경우
  - 4️⃣ 주문 중 환전한 달러: 0
  - 5️⃣ 환전에 사용한 원화: 0

- 봇: 💰 배당금으로만 구매하신 것으로 확인됩니다.
- 사용한 배당금: $1,505.00
- 일부만 배당금 사용
  - 4️⃣ 주문 중 환전한 달러: 1000
  - 5️⃣ 환전에 사용한 원화: 1400500
- 봇: 💰 배당금 $505.00 + 신규 투자금 ₩1,400,500

### /dividend - 배당금 수령

/dividend <티커> <배당금액(달러)> <날짜>

- **예시**: `/dividend NVDY 50.25`
- **날짜 포함**: `/dividend NVDY 50.25 2024-12-15`

### /status - 현재 상태 조회

/status <티커:옵션>

- **전체 포트폴리오**: `/status`
- **특정 종목**: `/status NVDY`

## 보조 명령어 (2개)

### /history - 거래 내역 조회

/history <티커:옵션> <기간:옵션>

- **전체 내역**: `/history`
- **특정 종목**: `/history NVDY`
- **기간 지정**: `/history NVDY 30` (최근 30일)

### /set_price - 현재가 업데이트

/set_price <티커> <현재가>

- **예시**: `/set_price NVDY 155.25`
- 수익률 계산을 위한 현재 시장가 업데이트