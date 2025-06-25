# 베이스 이미지
FROM python:3.9-slim-buster

# Debian/Ubuntu 패키지 관리자 non-interactive 모드 설정 (빌드 중 사용자 입력 방지)
ENV DEBIAN_FRONTEND=noninteractive

# [추가] wait-for-db.sh 스크립트가 사용할 netcat 설치
RUN apt-get update && apt-get install -y --no-install-recommends netcat && \
    # 패키지 캐시를 삭제하여 최종 이미지 크기 최적화
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /

# requirements.txt 복사 및 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 현재 디렉토리(app/)의 모든 파일을 컨테이너의 작업 디렉토리(/app)로 복사
COPY . .

# [추가] wait-for-db.sh 스크립트에 실행 권한 부여
RUN chmod +x ./wait-for-db.sh