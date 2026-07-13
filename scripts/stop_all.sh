#!/bin/bash

echo "klb 애플리케이션을 완전히 종료합니다..."

pm2 delete klb 2>/dev/null || true

echo "애플리케이션이 PM2 목록에서 깔끔하게 삭제되었습니다."