#!/bin/bash

SCRIPT_PATH="$0"
HAD_EXECUTE_PERMISSION=0
if [ -x "$SCRIPT_PATH" ]; then
  HAD_EXECUTE_PERMISSION=1
fi

read -p "강제로 가져올 브랜치 이름을 입력하세요: " BRANCH_NAME

if [ -z "$BRANCH_NAME" ]; then
  echo "오류: 브랜치 이름은 비워둘 수 없습니다." >&2
  exit 1
fi

git fetch origin || { echo "오류: origin에서 가져오는데 실패했습니다." >&2; exit 1; }
git reset --hard "origin/$BRANCH_NAME" || { echo "오류: 브랜치 '$BRANCH_NAME'을(를) origin/$BRANCH_NAME (으)로 리셋하는데 실패했습니다." >&2; exit 1; }
git checkout "$BRANCH_NAME" || { echo "오류: 브랜치 '$BRANCH_NAME'(으)로 체크아웃하는데 실패했습니다." >&2; exit 1; }

if [ "$HAD_EXECUTE_PERMISSION" -eq 1 ]; then
  chmod +x "$SCRIPT_PATH" || { echo "경고: 스크립트 '$SCRIPT_PATH'에 실행 권한을 다시 설정하는데 실패했습니다." >&2; }
fi

echo "브랜치 '$BRANCH_NAME'을(를) origin/$BRANCH_NAME (으)로 성공적으로 가져오고 리셋했습니다."
exit 0
