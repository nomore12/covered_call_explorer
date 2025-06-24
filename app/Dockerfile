# 파이썬 공식 이미지를 기반으로 사용 (alpine은 경량화된 리눅스 배포판)
FROM python:3.9-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 파이썬 의존성 파일 먼저 복사하여 캐싱 활용
COPY requirements.txt .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Flask 애플리케이션을 실행할 포트 노출
EXPOSE 5000

# 애플리케이션 실행 명령어
# 이제 main.py를 실행하여 모든 서비스(Flask, 봇)를 시작합니다.
CMD ["python", "main.py"] # <-- 변경된 부분