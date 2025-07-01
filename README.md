# 커버드 콜 익스플로러 - 사용 가이드

## 프로젝트 개요

이 프로젝트는 주식 투자 포트폴리오와 커버드 콜 전략을 관리하기 위한 Flask 웹 애플리케이션입니다. **대화형 텔레그램 봇**을 통해 매수/매도 거래를 기록하고, **환율과 배당금 재투자를 정확히 추적**하여 실시간 수익률을 모니터링할 수 있습니다.

## 기술 스택

- **백엔드**: Flask (Python)
- **데이터베이스**: MySQL
- **ORM**: SQLAlchemy
- **봇**: Python Telegram Bot (ConversationHandler)
- **배포**: Docker, Docker Compose
- **정확도**: Decimal 타입으로 금융 계산 정밀도 보장

## 주요 특징

### 🎯 정확한 수익률 계산
- **환율 추적**: 매수 시점의 달러-원화 환율 기록
- **배당금 재투자 분리**: 신규 투자금과 배당금 재투자 구분 추적
- **원화 기준 수익률**: 실제 투입한 원화 대비 수익률 계산

### 💬 직관적인 대화형 봇
- **단계별 입력**: 복잡한 명령어 대신 5단계 대화로 매수 기록
- **실수 방지**: 각 단계별 확인과 재입력 옵션 제공
- **배당금 전용 매수**: 배당금으로만 추가 매수하는 케이스 지원

## 텔레그램 봇 명령어

### 핵심 명령어

#### `/buy` - 매수 기록 (대화형)
```
사용자: /buy
봇: 어떤 종목을 매수하셨나요? (예: NVDY)
사용자: NVDY
봇: NVDY 매수 정보를 순서대로 입력해주세요.
    1️⃣ 몇 주를 매수하셨나요?
사용자: 10
봇: 2️⃣ 1주당 가격을 입력하세요
    달러 가격만 입력 (예: 150.50):
사용자: 150.50
봇: 3️⃣ 총 구매금액(달러)을 입력하세요:
    계산된 금액: $1,505.00
사용자: 1505.00
봇: 4️⃣ 주문 중 환전한 달러를 입력하세요:
    (배당금으로만 구매한 경우 0 입력)
사용자: 1000.00
봇: 5️⃣ 환전에 사용한 원화를 입력하세요:
    (수수료 포함, 환전하지 않았으면 0 입력)
사용자: 1400500
봇: ✅ 매수 내역 확인
    [상세 내역 표시]
    저장하시겠습니까? (예/아니오/다시)
```

#### `/dividend` - 배당금 수령
```
/dividend <티커> <배당금액> [날짜]
예시: /dividend NVDY 50.25
예시: /dividend NVDY 50.25 2024-12-15
```

#### `/status` - 현재 상태 조회
```
/status              # 전체 포트폴리오
/status NVDY         # 특정 종목
```

### 보조 명령어

#### `/set_price` - 현재가 업데이트
```
/set_price <티커> <현재가>
예시: /set_price NVDY 155.25
```

#### `/db_status` - 데이터베이스 상태 확인
```
/db_status
```

## 데이터베이스 구조

### 주요 테이블

#### `transactions` - 거래 내역
- 모든 매수/매도/배당금 거래 기록
- **환율 정보**: `exchange_rate`, `amount_krw`
- **자금 출처**: `dividend_used`, `cash_invested_krw`

#### `holdings` - 보유 현황
- 종목별 현재 보유량 및 수익률
- **정확한 원가 계산**: `avg_purchase_price`, `avg_exchange_rate`
- **배당금 분석**: `dividends_reinvested`, `dividends_withdrawn`

#### `dividends` - 배당금 내역
- 배당금 수령 및 재투자 추적
- 세후 실제 수령액 기록

#### `exchange_rates` - 환율 이력 (선택사항)
- 일별 환율 데이터 저장

## 개발 환경 설정

### 필수 환경 변수

```bash
# .env 파일 생성
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ALLOWED_TELEGRAM_USER_IDS=your_user_id1,your_user_id2

# 데이터베이스 설정
MYSQL_ROOT_PASSWORD=your_mysql_password
MYSQL_DATABASE=covered_call_db
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
DATABASE_URL=mysql+pymysql://user:password@db:3306/covered_call_db
```

### 실행 방법

```bash
# Docker Compose로 전체 시스템 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f app

# 개발 모드 실행 (로컬)
cd app
pip install -r requirements.txt
python -m app.main
```

## 사용 시나리오

### 1. 신규 투자금으로 매수
```
/buy → NVDY → 10주 → $150.50 → $1,505.00 → $1,505.00 → ₩2,100,000
```

### 2. 배당금으로만 매수
```
/buy → NVDY → 5주 → $150.50 → $752.50 → 0 → 0
```

### 3. 배당금 + 신규 투자금 혼합
```
/buy → NVDY → 10주 → $150.50 → $1,505.00 → $1,000.00 → ₩1,400,000
(배당금 $505.00 + 신규 투자금 ₩1,400,000)
```

## 주의사항

- **환경 변수 보안**: 텔레그램 봇 토큰은 절대 코드에 하드코딩 금지
- **사용자 제한**: `ALLOWED_TELEGRAM_USER_IDS`로 봇 접근 제한 필수
- **데이터 백업**: 영구 볼륨 설정으로 데이터 손실 방지
- **입력 검증**: 모든 사용자 입력에 대한 유효성 검사

## 프로젝트 구조

```bash
/
├── app/
│   ├── __init__.py          # Flask 앱 초기화
│   ├── main.py             # 메인 실행 파일
│   ├── models.py           # 데이터베이스 모델
│   ├── routes.py           # 웹 라우트
│   ├── telegram_bot.py     # 텔레그램 봇 로직
│   ├── requirements.txt    # Python 의존성
│   ├── Dockerfile         # Docker 설정
│   └── wait-for-db.sh     # DB 연결 대기 스크립트
├── docker-compose.yml      # Docker Compose 설정
├── init.db.sql            # 데이터베이스 초기화 스크립트
├── migrate_db.sql         # 데이터베이스 마이그레이션 스크립트
├── CLAUDE.md              # 개발 가이드
└── README.md              # 사용 가이드
```

## 정확한 수익률 계산 방식

### 달러 기준 수익률
```
(현재가 - 평균매수가) / 평균매수가 × 100
```

### 원화 기준 수익률
```
(현재가치 - 실투입원화) / 실투입원화 × 100
```

### 배당금 수익률
```
총배당금 / 총투자금 × 100
```

## 향후 개선 사항

- **자동화**: 실시간 주가 및 환율 API 연동
- **고급 분석**: 섹터별, 기간별 수익률 분석 및 배당금 수익률 추적
- **알림 시스템**: 목표 수익률 달성 시 자동 텔레그램 알림
- **웹 대시보드**: 시각적 포트폴리오 관리 인터페이스
- **데이터 백업**: 자동 백업 및 복구 시스템
- **다중 사용자**: 사용자별 독립 포트폴리오 관리
- **매도 기능**: 매도 거래 및 실현 손익 계산 기능

## 문제 해결

### 봇이 응답하지 않는 경우
```bash
# 봇 로그 확인
docker-compose logs -f app

# 봇 재시작
docker-compose restart app
```

### 데이터베이스 연결 오류
```bash
# DB 상태 확인
docker-compose ps
docker-compose logs -f db

# DB 재시작
docker-compose restart db
```

### 환경 변수 설정 확인
```bash
# 환경 변수 확인
docker-compose config
```