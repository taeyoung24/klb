#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."
BACKEND_DIR="$SCRIPT_DIR/../apps/backend"

command="$1"

case "$command" in
  start)
    echo "데이터베이스 컨테이너(Docker Compose)를 실행합니다..."
    cd "$ROOT_DIR"
    docker compose up -d
    echo "데이터베이스가 백그라운드에서 실행 중입니다."
    ;;
  stop)
    echo "데이터베이스 컨테이너를 중지합니다..."
    cd "$ROOT_DIR"
    docker compose down
    echo "데이터베이스가 정상 중지 및 정리되었습니다."
    ;;
  status)
    echo "데이터베이스 컨테이너 상태:"
    cd "$ROOT_DIR"
    docker compose ps
    ;;
  seed)
    echo "데이터베이스 테이블 생성 및 초기 데이터 시딩(Seed)을 실행합니다..."
    cd "$BACKEND_DIR"
    uv run -m scripts.seed_db
    echo "시딩이 완료되었습니다."
    ;;
  *)
    echo "사용법: $0 {start|stop|status|seed}"
    exit 1
    ;;
esac

exit 0
