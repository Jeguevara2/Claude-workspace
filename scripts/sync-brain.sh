#!/usr/bin/env bash
# 공유 두뇌 동기화 스크립트
# 사용: Claude에게 "두뇌 동기화해줘"라고 하면 Claude가 이 로직을 실행합니다.
#
# Claude는 다음 순서로 동기화합니다:
#   1. 노션 NEXUS 마스터 페이지 읽기
#      - NEXUS 마스터: 388d60207bf980cdac56fea299a382f5
#      - 클로드 지침 목록: 36dd60207bf980c3b5efc88cf540bd17
#   2. CLAUDE.md 내용 갱신 (워크플로우 상태, 최종 동기화 날짜 등)
#   3. git add CLAUDE.md && git commit -m "sync: 공유 두뇌 업데이트 (YYYY-MM-DD)"
#   4. git push -u origin <current-branch>

NEXUS_MASTER_ID="388d60207bf980cdac56fea299a382f5"
WORKFLOW_LIST_ID="36dd60207bf980c3b5efc88cf540bd17"
BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "두뇌 동기화를 시작합니다..."
echo "Claude가 노션 MCP를 통해 다음 페이지를 읽어 CLAUDE.md를 갱신해야 합니다:"
echo "  - NEXUS 마스터 ID: $NEXUS_MASTER_ID"
echo "  - 클로드 지침 목록 ID: $WORKFLOW_LIST_ID"
echo "  - 현재 브랜치: $BRANCH"
