# 커버드 콜 익스플로러 프로젝트

## 프로젝트 개요

이 프로젝트는 주식 투자 포트폴리오와 커버드 콜 전략을 관리하기 위한 Flask 웹 애플리케이션입니다. **대화형 텔레그램 봇**을 통해 매수/매도 거래를 기록하고, **환율과 배당금 재투자를 정확히 추적**하여 실시간 수익률을 모니터링할 수 있습니다.

## 기술 스택

- **백엔드**: Flask (Python)
- **데이터베이스**: MySQL
- **ORM**: SQLAlchemy
- **봇**: Python Telegram Bot (ConversationHandler)
- **배포**: Docker, Docker Compose
- **정확도**: Decimal 타입으로 금융 계산 정밀도 보장

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
└── README.md              # 개발 가이드
```

## 주요 기능

### 🎯 정확한 수익률 계산 시스템

- **환율 추적**: 매수 시점의 달러-원화 환율 자동 기록
- **배당금 재투자 분리**: 신규 투자금과 배당금 재투자 구분 추적
- **원화 기준 수익률**: 실제 투입한 원화 대비 정확한 수익률 계산
- **복합 투자 지원**: 배당금 + 신규 투자금 혼합 매수 케이스 처리

### 💬 직관적인 대화형 봇 인터페이스

- **5단계 대화**: 복잡한 한 줄 명령어 대신 단계별 안내
- **실수 방지**: 각 단계별 확인과 '다시' 옵션 제공
- **배당금 전용 매수**: 환전 없이 배당금으로만 추가 매수 지원
- **입력 취소**: 언제든 /cancel로 입력 중단 가능

### 데이터베이스 테이블

- **transactions**: 모든 거래 내역 + 환율 + 자금 출처 추적
- **holdings**: 현재 보유 종목 + 평균 환율 + 배당금 분석
- **dividends**: 배당금 수령 및 재투자 내역 별도 관리
- **exchange_rates**: 환율 이력 관리 (선택사항)

### 텔레그램 봇 명령어

#### 핵심 명령어 (3개)
- **`/buy`** - 매수 기록 (5단계 대화형)
  - 티커 → 주수 → 주당가 → 총액 → 환전액 → 원화액 → 확인
  - 배당금 전용 매수 자동 처리
  - 환율 자동 계산 및 저장
  - ConversationHandler로 단계별 입력 관리

- **`/dividend <ticker> <amount> [date]`** - 배당금 수령
  - 예: `/dividend NVDY 50.25`
  - 세후 실제 수령액 기록
  - 자동으로 dividends 테이블에 기록

- **`/status [ticker]`** - 현재 상태 조회
  - 전체 포트폴리오 또는 특정 종목
  - 달러/원화 수익률 분리 표시
  - 실시간 수익률 계산

#### 보조 명령어 (3개)
- **`/set_price <ticker> <price>`** - 현재가 업데이트
- **`/db_status`** - 데이터베이스 상태 확인
- **`/cancel`** - 현재 대화 취소 (ConversationHandler 종료)

## 개발 환경 설정

### 필수 환경 변수

```bash
# 텔레그램 봇 설정
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
docker-compose logs -f

# 개발 모드 실행 (로컬)
cd app
pip install -r requirements.txt
python -m app.main
```

## 테스트 및 디버깅

### 데이터베이스 접속

```bash
docker exec -it covered_call_explorer_db_1 mysql -u root -p covered_call_db
```

### 봇 테스트

```bash
# 1. 봇 시작 테스트
/start

# 2. 매수 기록 테스트 (대화형)
/buy
# → NVDY → 10 → 150.50 → 1505.00 → 1000.00 → 1400500 → 예

# 3. 배당금 기록 테스트
/dividend NVDY 50.25

# 4. 상태 조회 테스트
/status
/status NVDY
```

### 웹 인터페이스

브라우저에서 `http://localhost:5000`으로 접속하여 기본 상태 확인

## 주요 구현 특징

### 보안 및 접근 제어
- **사용자 인증**: `@restricted` 데코레이터로 봇 명령어 접근 제한
- **환경 변수 관리**: 민감한 정보는 모두 환경 변수로 관리
- **토큰 검증**: 봇 토큰이 없으면 프로그램 종료

### 데이터 정확성
- **Decimal 타입**: 모든 금융 계산에 Decimal 사용으로 정밀도 보장
- **환율 추적**: 매수 시점의 정확한 환율 기록
- **자금 출처 분리**: 신규 투자금과 배당금 재투자 구분

### 대화형 인터페이스
- **ConversationHandler**: 단계별 매수 입력 프로세스
- **상태 관리**: 사용자별 독립적인 대화 상태 관리
- **입력 검증**: 각 단계별 유효성 검사 및 오류 처리

## 주의사항

- **보안**: 텔레그램 봇 토큰은 절대 코드에 하드코딩 금지, 환경 변수 관리 필수
- **접근 제한**: `ALLOWED_TELEGRAM_USER_IDS`로 봇 사용자 제한 설정 필수
- **데이터 안전성**: 데이터베이스 볼륨 영구 저장 설정으로 데이터 손실 방지
- **입력 검증**: 모든 사용자 입력에 대한 유효성 검사 및 Decimal 타입 사용
- **환율 정확성**: 매수 시점의 환율을 정확히 기록하여 원화 기준 수익률 계산
- **대화 상태 관리**: ConversationHandler로 사용자별 입력 상태 독립 관리

## 향후 개선 사항

- **자동화**: 실시간 주가 및 환율 API 연동
- **고급 분석**: 섹터별, 기간별 수익률 분석 및 배당금 수익률 추적
- **알림 시스템**: 목표 수익률 달성 시 자동 텔레그램 알림
- **웹 대시보드**: 시각적 포트폴리오 관리 인터페이스
- **데이터 백업**: 자동 백업 및 복구 시스템
- **다중 사용자**: 사용자별 독립 포트폴리오 관리
- **매도 기능**: 매도 거래 및 실현 손익 계산 기능

## 사용 시나리오 예시

### 1. 신규 투자금으로 매수
```
/buy → NVDY → 10주 → $150.50 → $1,505.00 → $1,505.00 → ₩2,100,000
결과: 환율 ₩1,394.70 자동 계산 및 기록
```

### 2. 배당금으로만 매수
```
/buy → NVDY → 5주 → $150.50 → $752.50 → 0 → 0
결과: 배당금 재투자로 분류, 원화 투입 없음 기록
```

### 3. 배당금 + 신규 투자금 혼합
```
/buy → NVDY → 10주 → $150.50 → $1,505.00 → $1,000.00 → ₩1,400,000
결과: 배당금 $505.00 + 신규 투자금 ₩1,400,000 구분 기록
```

### 4. 정확한 수익률 계산
- **달러 기준**: (현재가 - 평균매수가) / 평균매수가 × 100
- **원화 기준**: (현재가치 - 실투입원화) / 실투입원화 × 100
- **배당금 수익률**: 총배당금 / 총투자금 × 100
