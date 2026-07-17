#!/bin/bash

echo "KLB 애플리케이션(프론트엔드 및 백엔드)을 완전히 종료합니다..."

pm2 delete klb 2>/dev/null || true
pm2 delete klb-backend 2>/dev/null || true

echo "애플리케이션이 PM2 목록에서 깔끔하게 삭제되었습니다."