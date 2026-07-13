#!/bin/bash
cd "$(dirname "$0")/../apps/web"

echo "의존성 패키지 설치 중..."
pnpm install || { echo "오류: pnpm install에 실패했습니다." >&2; exit 1; }

echo "Vite 애플리케이션 빌드 중..."
pnpm build || { echo "오류: 빌드에 실패했습니다." >&2; exit 1; }

echo "기존 실행 중인 PM2 프로세스가 있다면 정리합니다..."
pm2 delete klb 2>/dev/null || true

echo "Vite 프로덕션 프리뷰 서버 실행 중..."
# PM2를 사용하여 pnpm run preview 명령어를 백그라운드에서 실행 (작업 디렉토리를 apps/web으로 고정)
pm2 start pnpm --name "klb" --cwd "$(pwd)" --update-env -- run preview -- --port 5500 --host 0.0.0.0

echo "애플리케이션이 PM2 백그라운드에서 시작되었습니다!"
echo "상태를 보려면 'pm2 status' 또는 실시간 로그를 보려면 'pm2 logs klb'를 입력하세요."
exit 0