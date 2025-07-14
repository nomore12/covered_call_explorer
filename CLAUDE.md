# 커버드 콜 익스플로러 프로젝트

## 프로젝트 개요

이 프로젝트는 주식 투자 포트폴리오와 커버드 콜 전략을 관리하기 위한 Flask 웹 애플리케이션입니다. **대화형 텔레그램 봇**을 통해 매수/매도 거래를 기록하고, **환율과 배당금 재투자를 정확히 추적**하여 실시간 수익률을 모니터링할 수 있습니다.

## 기술 스택

- **백엔드**: Flask (Python)
- **프론트엔드**: React 19.1.0 + TypeScript + Vite
- **UI 라이브러리**: Chakra UI v3, React Icons
- **차트**: Recharts, Chakra UI Charts
- **라우팅**: React Router DOM v7
- **상태 관리**: Zustand (중앙집중식 상태 관리로 중복 API 호출 방지)
- **데이터베이스**: MySQL
- **ORM**: SQLAlchemy
- **봇**: Python Telegram Bot (ConversationHandler)
- **주가 API**: Toss API (1차), Finnhub API (fallback)
- **배포**: Docker, Docker Compose
- **정확도**: Decimal 타입으로 금융 계산 정밀도 보장

## 프로젝트 구조

```bash
/
├── app/
│   ├── __init__.py              # Flask 앱 초기화
│   ├── main.py                 # 메인 실행 파일
│   ├── models.py               # 데이터베이스 모델
│   ├── routes/
│   │   └── stock_routes.py     # 주식 관련 API 라우트
│   ├── toss_api/               # Toss API 통합
│   │   ├── __init__.py
│   │   ├── client.py           # Toss API 클라이언트
│   │   ├── parser.py           # 응답 데이터 파싱
│   │   ├── service.py          # 서비스 레이어
│   │   ├── tickers.py          # 종목 코드 매핑
│   │   └── example.py          # 사용 예제
│   ├── telegram_bot.py         # 텔레그램 봇 로직
│   ├── scheduler.py            # 주가 업데이트 스케줄러
│   ├── price_updater.py        # 주가 업데이트 로직
│   ├── exchange_rate_service.py # 환율 서비스
│   ├── requirements.txt        # Python 의존성
│   ├── Dockerfile             # Docker 설정
│   └── wait-for-db.sh         # DB 연결 대기 스크립트
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── dashboard/
│   │   │   │   ├── AddDividends.tsx    # 배당금 추가 폼
│   │   │   │   ├── AddTransaction.tsx  # 거래 추가 폼
│   │   │   │   ├── ClosedTag.tsx       # 종료된 거래 태그
│   │   │   │   ├── DividendHistory.tsx # 배당금 이력 (종목별 필터링)
│   │   │   │   ├── Portfolio.tsx       # 포트폴리오 현황 (배당금+손익 통합)
│   │   │   │   └── TradeHistory.tsx    # 거래 이력 (상세 정보)
│   │   │   └── ui/
│   │   │       ├── color-mode.tsx      # 다크모드 토글
│   │   │       ├── provider.tsx        # Chakra UI 프로바이더
│   │   │       ├── toaster.tsx         # 토스트 알림
│   │   │       └── tooltip.tsx         # 툴팁
│   │   ├── store/
│   │   │   ├── dashboardStore.ts       # 통합 상태 관리 (포트폴리오/거래/배당금)
│   │   │   ├── exchangeRateStore.ts    # 환율 상태 관리
│   │   │   └── portfolioStore.ts       # 포트폴리오 상태 관리
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx           # 대시보드 페이지 (중앙집중식 데이터 로딩)
│   │   │   └── Login.tsx               # 로그인 페이지
│   │   ├── routes/
│   │   │   └── Routes.tsx              # 라우터 설정
│   │   ├── App.tsx                     # 메인 앱 컴포넌트
│   │   └── main.tsx                    # 엔트리 포인트
│   ├── package.json                   # Node.js 의존성
│   ├── vite.config.ts                 # Vite 설정
│   ├── tsconfig.json                  # TypeScript 설정
│   └── eslint.config.js               # ESLint 설정
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
- **총 수익 통합**: 미실현 손익 + 실현 배당금 = 총 투자 성과 실시간 표시
- **실시간 환율 적용**: 모든 원화 계산에 현재 환율 자동 적용

### 📊 실시간 주가 업데이트 시스템

- **Toss API 우선**: 한국 토스 증권 API를 통한 정확한 실시간 주가
- **Finnhub 백업**: Toss API 실패 시 Finnhub API로 자동 fallback 처리
- **스마트 업데이트**: 가격 변동이 있을 때만 데이터베이스 업데이트 (성능 최적화)
- **소스 추적**: 어떤 API에서 가격을 가져왔는지 price_updates 테이블에 기록

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

# 백엔드 개발 모드 실행 (로컬)
cd app
pip install -r requirements.txt
python -m app.main

# 프론트엔드 개발 모드 실행 (로컬)
cd frontend
yarn install
yarn dev
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

- **백엔드 API**: `http://localhost:5000`으로 접속하여 기본 상태 확인
- **프론트엔드**: `http://localhost:5173`으로 접속하여 React 애플리케이션 확인

### 프론트엔드 개발 도구

```bash
# 린트 검사
yarn lint

# 린트 자동 수정
yarn lint:fix

# 코드 포맷팅
yarn format

# 포맷팅 검사
yarn format:check

# 빌드
yarn build

# 프로덕션 미리보기
yarn preview
```

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

### 프론트엔드 아키텍처
- **컴포넌트 구조**: 재사용 가능한 UI 컴포넌트와 페이지별 컴포넌트 분리
- **중앙집중식 상태 관리**: Zustand를 활용한 효율적인 상태 관리
  - `dashboardStore`: 포트폴리오, 거래, 배당금 데이터 통합 관리
  - `exchangeRateStore`: 환율 정보 관리
  - 불필요한 중복 API 호출 방지로 성능 최적화
- **타입 안전성**: TypeScript로 전체 애플리케이션 타입 안전성 확보
- **스타일링**: Chakra UI 컴포넌트 시스템으로 일관된 디자인
- **차트 및 시각화**: Recharts와 Chakra UI Charts로 데이터 시각화
- **반응형 디자인**: 모바일 및 데스크톱 환경 지원
- **배당금 통합 UI**: 포트폴리오 화면에 배당금 정보 실시간 표시
- **직관적인 색상 구분**: 손익(초록/빨강), 배당금(파랑), 포트폴리오 가치(파랑) 계열

## 주의사항

- **보안**: 텔레그램 봇 토큰은 절대 코드에 하드코딩 금지, 환경 변수 관리 필수
- **접근 제한**: `ALLOWED_TELEGRAM_USER_IDS`로 봇 사용자 제한 설정 필수
- **데이터 안전성**: 데이터베이스 볼륨 영구 저장 설정으로 데이터 손실 방지
- **입력 검증**: 모든 사용자 입력에 대한 유효성 검사 및 Decimal 타입 사용
- **환율 정확성**: 매수 시점의 환율을 정확히 기록하여 원화 기준 수익률 계산
- **대화 상태 관리**: ConversationHandler로 사용자별 입력 상태 독립 관리

## 향후 개선 사항

- **고급 분석**: 섹터별, 기간별 수익률 분석 및 배당금 수익률 추적
- **알림 시스템**: 목표 수익률 달성 시 자동 텔레그램 알림
- **웹 대시보드 고도화**: 
  - 대화형 차트 및 필터링 기능
  - 포트폴리오 비교 및 벤치마킹 도구
  - 배당금 예측 및 연간 배당 수익률 계산
- **데이터 백업**: 자동 백업 및 복구 시스템
- **다중 사용자**: 사용자별 독립 포트폴리오 관리
- **매도 기능**: 매도 거래 및 실현 손익 계산 기능
- **모바일 앱**: React Native 또는 PWA 형태의 모바일 애플리케이션
- **추가 API 연동**: Yahoo Finance, Alpha Vantage 등 추가 주가 소스
- **성능 최적화**: 
  - 가상화된 리스트로 대량 데이터 처리
  - 캐싱 전략으로 API 호출 최적화
  - 코드 스플리팅으로 번들 크기 최적화

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
- **총 수익률**: (미실현 손익 + 배당금) / 총투자금 × 100

## 최근 업데이트 내역

### 2025년 7월 14일 - Claude Code 환경 업데이트

#### 🛠️ 개발 환경 현황
- **Claude Code 모델**: Default (Opus 4 for up to 20% of usage limits, then use Sonnet 4) - 현재 Opus 사용 중
- **IDE 통합**: Cursor 익스텐션 연결 완료
- **계정**: noprefab@gmail.com (Claude Max Account)
- **프로젝트 메모리**: CLAUDE.md 파일 인식 완료
- **설치 방법**: npm-global로 설치됨 (Config mismatch 경고는 무시 가능)

#### 📁 현재 작업 디렉토리
```
/Users/noseongho/Documents/my-works/covered_call_explorer
```

#### 🔧 Git 상태
- **현재 브랜치**: main
- **수정된 파일**: frontend/src/pages/Dashboard.tsx (수정 상태)
- **최근 커밋**: authStore.ts 업데이트 관련

### 2025년 1월 13일 - 주요 기능 개선

#### 🔄 Toss API 통합 및 이중 주가 소스 시스템
- **Toss API 우선 사용**: 한국 토스 증권 API를 통한 정확한 실시간 주가 조회
- **Finnhub 자동 백업**: Toss API 실패 시 기존 Finnhub API로 자동 전환
- **스마트 업데이트**: 가격 변동이 있을 때만 데이터베이스 업데이트 (0.001달러 이상)
- **소스 추적**: 어떤 API를 사용했는지 price_updates 테이블에 기록
- **종목 코드 매핑**: `tickers.py`에서 Toss/일반 종목 코드 매핑 관리

#### 🏪 Zustand 중앙집중식 상태 관리 시스템
- **dashboardStore**: 포트폴리오, 거래, 배당금 데이터 통합 관리
- **성능 최적화**: 개별 컴포넌트의 중복 API 호출 완전 제거
- **실시간 동기화**: 데이터 추가/수정 시 관련 데이터 자동 새로고침
- **타입 안전성**: TypeScript로 완전한 타입 정의 및 인터페이스 구축
- **통합 로딩/에러 상태**: 모든 컴포넌트에서 일관된 상태 관리

#### 💰 포트폴리오 화면 배당금 완전 통합
- **총 포트폴리오 가치**: 현재 보유가치 + 받은 총 배당금으로 실제 자산 가치 표시
- **총 손익 분할 표시**: 미실현 손익과 배당금을 좌우로 분리하여 직관적 표시
- **종목별 배당금**: 각 종목별로 받은 배당금 총액, 수령 횟수 상세 표시
- **실시간 환율 적용**: 모든 USD를 현재 환율로 정확한 원화 환산
- **총 수익률 계산**: (미실현 손익 + 배당금) / 총투자금 × 100 정확한 계산

#### 🎨 UI/UX 혁신적 개선
- **색상 구분 체계**: 손익(초록/빨강), 배당금(파랑), 포트폴리오 가치(파랑) 계열로 직관적 구분
- **정보 밀도 최적화**: 한 화면에서 포트폴리오 전체 현황 완전 파악 가능
- **반응형 디자인**: 모바일과 데스크톱 환경 모두 완벽 최적화
- **통합 로딩 상태**: 일관된 로딩 및 에러 처리로 향상된 사용자 경험
- **종목별 필터링**: 배당금 이력에서 종목별 상세 필터링 기능

#### 📊 데이터 정확성 및 성능 향상
- **실시간 환율 적용**: 모든 원화 계산에 최신 환율 자동 적용
- **배당금 추적 시스템**: 종목별, 전체 배당금 수령 내역 정확한 집계 및 분석
- **수익률 계산 고도화**: 미실현 손익과 배당금을 포함한 총 수익률 실시간 표시
- **API 호출 최적화**: 중복 호출 제거로 페이지 로딩 속도 대폭 향상
- **타입 안전성 강화**: 모든 데이터 흐름에서 TypeScript 타입 검증 적용
