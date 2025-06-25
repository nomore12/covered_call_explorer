#!/bin/sh
# wait-for-db.sh

# 오류 발생 시 즉시 스크립트 중단
set -e

# 첫 번째 인자를 host 변수에 저장
host="$1"
# 첫 번째 인자를 제외한 나머지 모든 인자를 shift 하고 cmd 변수에 저장
shift
cmd="$@"

# nc(netcat) 명령어를 사용하여 host와 3306 포트로의 TCP 연결이 성공할 때까지 반복
# -z 옵션: 포트 스캐닝 모드 (실제 데이터 전송 없이 연결만 확인)
until nc -z "$host" 3306; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

# 루프가 끝나면(연결 성공) 메시지 출력
>&2 echo "MySQL is up - executing command"
# 전달받은 cmd(예: python -m app.main)를 실행
exec $cmd