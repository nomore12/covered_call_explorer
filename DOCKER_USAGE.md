# 🐳 Docker 환경 사용법

## 📁 파일 구조

```
├── docker-compose.yml          # 배포용 (프로덕션)
├── docker-compose.dev.yml      # 개발용 (로컬 개발)
├── app/
│   ├── Dockerfile             # 배포용 백엔드
│   └── Dockerfile.dev         # 개발용 백엔드
└── frontend/
    ├── Dockerfile             # 배포용 프론트엔드
    └── Dockerfile.dev         # 개발용 프론트엔드
```

## 🚀 개발 환경 (로컬 개발)

### 시작하기

```bash
# 개발 환경 시작
docker-compose -f docker-compose.dev.yml up --build -d

# 로그 확인
docker-compose -f docker-compose.dev.yml logs -f

# 중지
docker-compose -f docker-compose.dev.yml down
```

### 접속 주소

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:5001
- **Database**: localhost:3306

### 특징

- ✅ **실시간 반영**: 코드 수정 시 자동 반영
- ✅ **Hot Reloading**: 프론트엔드 자동 새로고침
- ✅ **Debug 모드**: 백엔드 디버그 로그 활성화
- ✅ **볼륨 마운트**: 로컬 코드와 컨테이너 동기화

## 🚀 배포 환경 (프로덕션)

### 시작하기

```bash
# 배포 환경 시작
docker-compose up --build -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

### 접속 주소

- **Frontend**: http://localhost:80
- **Backend**: http://localhost:5001
- **Database**: localhost:3306

### 특징

- ✅ **최적화된 빌드**: 프로덕션용 최적화
- ✅ **Nginx 서버**: 정적 파일 서빙
- ✅ **보안 강화**: 개발 도구 비활성화
- ✅ **성능 최적화**: 압축 및 캐싱

## 🔧 유용한 명령어

### 개발 환경

```bash
# 특정 서비스만 재시작
docker-compose -f docker-compose.dev.yml restart web

# 특정 서비스 로그만 확인
docker-compose -f docker-compose.dev.yml logs -f frontend

# 컨테이너 내부 접속
docker-compose -f docker-compose.dev.yml exec web bash
docker-compose -f docker-compose.dev.yml exec frontend sh
```

### 배포 환경

```bash
# 특정 서비스만 재시작
docker-compose restart web

# 특정 서비스 로그만 확인
docker-compose logs -f frontend

# 컨테이너 내부 접속
docker-compose exec web bash
docker-compose exec frontend sh
```

## 🧹 정리 명령어

### 개발 환경 정리

```bash
# 컨테이너와 볼륨 모두 삭제
docker-compose -f docker-compose.dev.yml down -v

# 이미지까지 삭제
docker-compose -f docker-compose.dev.yml down --rmi all
```

### 배포 환경 정리

```bash
# 컨테이너와 볼륨 모두 삭제
docker-compose down -v

# 이미지까지 삭제
docker-compose down --rmi all
```

## ⚠️ 주의사항

1. **포트 충돌**: 개발/배포 환경을 동시에 실행하지 마세요
2. **데이터베이스**: 개발/배포 환경의 DB는 분리되어 있습니다
3. **환경변수**: `.env` 파일이 필요합니다
4. **볼륨**: 개발 환경에서는 로컬 코드가 실시간 반영됩니다

## 🔄 환경 전환

### 개발 → 배포

```bash
# 개발 환경 중지
docker-compose -f docker-compose.dev.yml down

# 배포 환경 시작
docker-compose up --build -d
```

### 배포 → 개발

```bash
# 배포 환경 중지
docker-compose down

# 개발 환경 시작
docker-compose -f docker-compose.dev.yml up --build -d
```
