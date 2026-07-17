#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../apps/web"
BACKEND_DIR="$SCRIPT_DIR/../apps/backend"

# 1. 기존 실행 중인 PM2 프로세스 정리
echo "기존 실행 중인 PM2 프로세스가 있다면 정리합니다..."
pm2 delete klb 2>/dev/null || true
pm2 delete klb-backend 2>/dev/null || true

# 2. 백엔드 실행
echo "Python 백엔드(klb-backend) 서버 실행 중..."
pm2 start uv --name "klb-backend" --cwd "$BACKEND_DIR" --kill-timeout 10000 -- run python -m uvicorn main:klb_backend --host 0.0.0.0 --port 3000

# 3. 프론트엔드 의존성 설치 및 빌드
echo "프론트엔드 의존성 패키지 설치 중..."
cd "$FRONTEND_DIR"
pnpm install || { echo "오류: pnpm install에 실패했습니다." >&2; exit 1; }

echo "Vite 애플리케이션 빌드 중..."
pnpm build || { echo "오류: 빌드에 실패했습니다." >&2; exit 1; }

# 4. 프론트엔드 실행
echo "Vite 프로덕션 프리뷰 서버 실행 중..."
pm2 start pnpm --name "klb" --cwd "$FRONTEND_DIR" --update-env -- run preview --port 5500 --host 0.0.0.0

echo "KLB 애플리케이션(프론트엔드/백엔드)이 PM2 백그라운드에서 시작되었습니다!"
echo "상태를 보려면 'pm2 status'를 입력하세요."
echo "백엔드 로그: 'pm2 logs klb-backend'"
echo "프론트엔드 로그: 'pm2 logs klb'"
exit 0