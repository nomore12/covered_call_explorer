# 🚀 개발 순서 및 구체적인 구현 사항

---

## **1. 데이터 모델 및 데이터베이스 인터페이스 구현**
  - **목표:** Flask 앱에서 MySQL 데이터베이스에 접근하여 `transactions` 및 `holdings` 테이블을 조작할 수 있도록 준비합니다.
    - **구현 사항:**
      - **`app/app.py` 수정:**
        - `db.Model`을 상속받아 `Transaction` 및 `Holding` 모델 클래스 정의. `init_db.sql`의 테이블 스키마에 맞춰 각 컬럼 정의 (데이터 타입, Primary Key, Unique, Nullable 등).
        - `__repr__` 메서드를 각 모델에 추가하여 객체 출력 시 가독성 높이기.
        - (선택 사항) 초기 `db_test` 라우트 제거 또는 주석 처리.

---

## **2. 텔레그램 봇 기본 기능 구현**
  - **목표:** 텔레그램 봇이 메시지를 수신하고, 기본적인 "Hello" 응답을 할 수 있도록 설정합니다.
    - **구현 사항:**
      - **`app/app.py` 또는 별도 봇 파일 (`app/bot.py`) 생성:**
      - `python-telegram-bot` 라이브러리 임포트.
      - 봇 토큰을 환경 변수에서 불러오기 (예: `TELEGRAM_BOT_TOKEN`).
      - `Updater`와 `Dispatcher` 객체 초기화.
      - `/start` 명령어 핸들러 (사용자에게 환영 메시지 전송).
      - 에러 핸들러 추가.
      - 봇을 폴링(polling) 방식으로 시작하는 코드 작성. (개발 초기에는 Flask 앱과 별도의 스크립트로 봇을 실행하는 것이 편리합니다. 이후 통합 고려)

---

## **3. 매수 내역 추가 기능 (`/add_buy`) 구현**
  - **목표:** 사용자가 텔레그램을 통해 매수 내역을 입력하면, 이를 파싱하여 `transactions` 테이블에 저장하고 `holdings` 테이블을 업데이트합니다.
  - **구현 사항:**
    - **텔레그램 명령어 핸들러 (`/add_buy <ticker> <shares> <price> <date (optional)>`):**
      - 사용자 메시지 파싱 (정규표현식 또는 `split()` 사용).
      - 입력 값 유효성 검사 (숫자 형식, 날짜 형식 등).
      - `Transaction` 객체 생성 및 `transactions` 테이블에 저장.
      - **`holdings` 테이블 업데이트 로직:**
        - 해당 `ticker`의 `Holding` 레코드 조회.
        - 없으면 새로 생성.
        - `current_shares`, `total_cost_basis` 업데이트:
          - `current_shares += new_shares`
          - `total_cost_basis += (new_shares * price)`
      - `db.session.commit()`으로 변경사항 반영.
      - 성공/실패 메시지를 텔레그램으로 응답.
    - **Tip:** `current_shares`와 `total_cost_basis`를 계산하는 함수를 별도로 만들면 좋습니다.

---

## **4. 배당금 수령 내역 추가 기능 (`/add_dividend`) 구현**
  - **목표:** 사용자가 배당금 수령 내역을 입력하면 `transactions` 테이블에 기록하고 `holdings` 테이블의 누적 배당금을 업데이트합니다.
  - **구현 사항:**
    - **텔레그램 명령어 핸들러 (`/add_dividend <ticker> <amount> <date (optional)>`):**
      - 사용자 메시지 파싱 및 유효성 검사.
      - `Transaction` 객체 생성 (type='DIVIDEND', shares=0, price_per_share=0) 및 `transactions` 테이블에 저장.
      - **`holdings` 테이블 업데이트 로직:**
        - 해당 `ticker`의 `Holding` 레코드 조회.
        - `accumulated_dividends += received_amount`
        - `db.session.commit()`
      - 성공/실패 메시지를 텔레그램으로 응답.

---

## **5. 현재 주가 업데이트 기능 (`/set_price`) 구현**
  - **목표:** 사용자가 특정 종목의 현재 주가를 수동으로 입력하면 `holdings` 테이블을 업데이트합니다.
  - **구현 사항:**
    - **텔레그램 명령어 핸들러 (`/set_price <ticker> <price> <date (optional)>`):**
      - 사용자 메시지 파싱 및 유효성 검사.
      - `holdings` 테이블에서 해당 `ticker`의 `Holding` 레코드 조회.
      - `current_market_price` 및 `last_price_update_date` 업데이트.
      - `db.session.commit()`
      - 성공/실패 메시지 응답.
      - (선택 사항) `transactions` 테이블에 `type='PRICE_UPDATE'` 트랜잭션 기록도 고려할 수 있으나, `holdings`에만 반영해도 무방합니다.

---

## **6. 수익률 조회 기능 (`/get_profit` 또는 `/status`) 구현**
  - **목표:** 현재 보유 중인 종목들의 수익률 및 전체 계좌 수익률을 계산하여 텔레그램으로 전송합니다.
  - **구현 사항:**
    - **텔레그램 명령어 핸들러:**
      - `holdings` 테이블의 모든 레코드를 조회.
      - 각 종목별 수익률 계산:
        - **매수 원가:** `holding.total_cost_basis`
        - **현재 자산 가치:** `holding.current_shares * holding.current_market_price`
        - **누적 수익:** `(현재 자산 가치 + holding.accumulated_dividends) - holding.total_cost_basis`
        - **수익률 (%):** `(누적 수익 / holding.total_cost_basis) * 100` (원가가 0인 경우 예외 처리)
      - 전체 계좌 수익률 계산 (모든 종목의 총 수익 합산 / 총 매수 원가 합산).
      - 계산된 정보를 보기 좋게 포맷하여 텔레그램 메시지로 전송. (예: 표 형식, 요약 등)

---

## **7. 자동 알림 스케줄러 구현**
  - **목표:** 특정 시간 또는 주기로 수익률 정보를 자동으로 텔레그램으로 전송합니다.
  - **구현 사항:**
    - **`APScheduler` 라이브러리 사용:**
      - `BackgroundScheduler` 객체 초기화.
      - 정기적으로 실행될 함수 정의 (예: 위 6번의 수익률 조회 로직을 호출하고 텔레그램으로 메시지를 보내는 함수).
      - 스케줄러에 `add_job`으로 작업 추가 (예: `cron` 표현식으로 매일 특정 시간 설정).
      - 스케줄러 시작.
    - **Flask 앱과 통합:** `app.py` 내에서 스케줄러를 초기화하고 실행하거나, 별도의 스케줄링 스크립트를 만들어 Docker Compose로 관리할 수 있습니다. (초기에는 단일 Flask 앱 내에서 통합하는 것이 간단)

---

## **8. 배포 및 유지보수**
  - **목표:** 시스템을 안정적으로 운영하고, 향후 발생할 수 있는 문제에 대비합니다.
  - **구현 사항:**
    - **코드 리팩토링:** 함수 분리, 클래스화 등을 통해 코드의 가독성과 유지보수성을 높입니다.
    - **로깅:** 에러 및 중요한 이벤트 로깅 설정.
    - **에러 핸들링:** 사용자 입력 오류, DB 오류, 텔레그램 API 오류 등 다양한 예외 상황 처리.
    - **Dockerfile 최적화:** 프로덕션 환경에 맞게 `Dockerfile` 최적화 (예: Gunicorn 사용, `WORKDIR` 설정 등).
    - **볼륨 설정:** `db_data` 볼륨이 `docker-compose.yml`에 제대로 설정되어 DB 데이터가 영구적으로 저장되도록 확인.
    - **텔레그램 봇 안정화:** 봇이 갑자기 죽지 않도록 에러 처리 강화 및 재시작 로직 고려.