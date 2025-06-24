# 파이썬 공식 이미지를 기반으로 사용
FROM python:3.9-slim-buster

# 작업 디렉토리 설정: 이제 컨테이너의 루트 디렉토리에서 시작합니다.
# 이렇게 하면 'app' 디렉토리가 파이썬 패키지 루트로 올바르게 인식됩니다.
WORKDIR /

# 파이썬 의존성 파일 먼저 복사 (Host의 app/requirements.txt를 Container의 /requirements.txt로 복사)
# 빌드 컨텍스트는 docker-compose.yml에서 './app'으로 설정되어 있음.
COPY requirements.txt .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
# Host의 './app' 디렉토리 전체를 Container의 '/app' 디렉토리로 복사합니다.
# 이제 컨테이너 루트(/)에는 'app'이라는 파이썬 패키지 디렉토리가 생깁니다.
COPY . /app

# Flask 애플리케이션을 실행할 포트 노출
EXPOSE 5000

# 애플리케이션 실행 명령어 (Docker Compose에서 오버라이드될 수 있음)
# CMD ["python", "-m", "app.main"] # docker-compose.yml의 command가 우선 적용됩니다.

