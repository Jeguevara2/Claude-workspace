#!/usr/bin/env bash
# 공유 두뇌 동기화 스크립트
# 사용: Claude에게 "두뇌 동기화해줘"라고 하면 Claude가 이 로직을 실행합니다.
#
# Claude는 다음 순서로 동기화합니다:
#   1. Google Drive MCP로 두 문서 읽기
#      - 공통 지침: 1wuEFRrBKVLRhYMnFLijOmUYuBMzVcQ0TdbmWd7fNw4M
#      - 자동화 정리: 1FAihsQKoClKzY_ZDIP6ICf_jwkTk1HWQBFc7TA-jqzA
#   2. CLAUDE.md 내용 갱신
#   3. git add CLAUDE.md && git commit -m "sync: 공유 두뇌 업데이트 (YYYY-MM-DD)"
#   4. git push -u origin claude/shared-brain-cross-env-bm5f2d

GDOC_GUIDELINE_ID="1wuEFRrBKVLRhYMnFLijOmUYuBMzVcQ0TdbmWd7fNw4M"
GDOC_WORKFLOW_ID="1FAihsQKoClKzY_ZDIP6ICf_jwkTk1HWQBFc7TA-jqzA"
BRANCH="claude/shared-brain-cross-env-bm5f2d"

echo "두뇌 동기화를 시작합니다..."
echo "Claude가 Google Drive MCP를 통해 다음 문서를 읽어 CLAUDE.md를 갱신해야 합니다:"
echo "  - 공통 지침 ID: $GDOC_GUIDELINE_ID"
echo "  - 자동화 정리 ID: $GDOC_WORKFLOW_ID"
echo "  - 대상 브랜치: $BRANCH"
