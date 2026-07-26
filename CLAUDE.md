# 넥서스(NEXUS) — 공유 두뇌

> **단일 원본(SSOT): 구글 드라이브가 마스터입니다.**
> 노션 연동은 2026-07(경) 사용자 결정으로 **잠시 보류** — 갱신 대상 아님. 내용을 바꾸려면 아래 구글 드라이브 마스터 md를 직접 편집하거나 Claude에게 요청하세요.
>
> - NEXUS 마스터 (구글 드라이브 md): https://drive.google.com/file/d/17vlALvcCHZr8gr6SFZOI2qAqVcdpr3pO/view
> - 구글 드라이브 NEXUS 폴더: https://drive.google.com/drive/folders/1CIBrGRVRn6s0Oc9vhfi_Up7LrdCMhu0Y
> - (참고, 보류 중) NEXUS 노션 마스터: https://app.notion.com/p/388d60207bf980cdac56fea299a382f5
> - 최종 동기화: 2026-07-27

---

## ★ NEXUS 수정 시 체크리스트 (작업 완료 전 반드시 확인)

- [ ] **구글 드라이브 NEXUS 마스터 지침.md** 반영했는가?
- [ ] **git 레포 CLAUDE.md** 갱신이 필요한가?
- [ ] 노션은 보류 중이므로 갱신 대상 아님 (재개 결정이 나면 구글 드라이브 마스터에 먼저 기록)
- [ ] 위 항목 중 하나라도 빠졌다면 → 완료 선언 전에 먼저 처리할 것

## ★ 워크플로우/작업 저장 규칙 (묻지 않고 자동 수행)

- 새 워크플로우 설계가 어느 정도 윤곽 잡히면 → 사용자 요청 없이 즉시 구글 드라이브 마스터 + CLAUDE.md에 저장
- 환경 전환 예상 시 (아이패드→회사 PC 등) → 진행 상황·다음 단계를 반드시 저장 후 마무리
- '설계 중' 상태도 저장 대상 — 완성 전이라도 중간 저장이 연속성을 보장함

---

## ★ 운영 규칙 (모든 환경 공통 — 최우선)

- **세션 시작 시**: 구글 드라이브 NEXUS 마스터 지침.md(위 링크)와 NEXUS 폴더 현황을 읽어 컨텍스트로 반영.
- **세션 종료 전 / 의미 있는 산출물**: 새 자동화·결정·선호·용어·진행상황을 **구글 드라이브 마스터에 갱신** (드라이브 커넥터는 제자리 수정이 안 되므로 같은 제목의 새 문서 생성 → 구버전은 "claude.me 구버전(삭제)" 폴더로 이동 안내). 로컬·로컬 메모리에만 적기 금지.
- **단일 원본(SSOT)**: 구글 드라이브가 마스터. 노션은 보류 중.
- **증류된 핵심만** 담는다. raw 대화 로그는 claude.ai 대화 기록에 있음.

---

## ★ 작업 스타일 (사용자 피드백)

- "무조건 안 된다"로 끝내지 말 것 — ①왜 안 되는지 간단히 ②우회책·대안 1~2개 ③추천안을 함께 제시. **파트너형 조력.**
- **선택지는 항상 번호를 매겨서 보여줄 것.** 사용자는 번호로 명령한다.

---

## 용어

- **넥서스(NEXUS)** = 사용자가 구축한 공유 두뇌. **마스터는 구글 드라이브 "NEXUS 마스터 지침.md"** (폴더 "A AI(클로드)", ID `1CIBrGRVRn6s0Oc9vhfi_Up7LrdCMhu0Y`). 노션은 보류 중(재개 전까지 참고용으로만 남겨둠).

---

## 1. 사용자 / 환경

- 이메일(개인): jechanghyun@gmail.com
- 이메일(회사): jch@poscoenc.com (포스코이앤씨)
- **집 PC**: 구글드라이브 E:\\ 로컬 미러링 (NEXUS = E:\\A AI(클로드)), K: 도 마운트. `~/.claude/CLAUDE.md` NEXUS 포인터 설치 완료 ✅
- **회사 PC**: 드라이브 데스크톱 동기화 차단 (커넥터/브라우저만). 개인 구글 브라우저 로그인 가능. `~/.claude/CLAUDE.md` NEXUS 포인터 설치 완료 ✅ (2026-06-22)
- **아이패드/웹**: Claude Code (claude.ai/code) + Google Drive MCP + 이 git 레포 → 이 `CLAUDE.md`가 자동으로 로드됨

---

## 2. 작업 선호

- Notion 페이지는 (재개 시) 토글로 접어 짧게 유지
- Notion 개인(jechanghyun@gmail.com) / 회사(poscoenc.com) 계정 구분하고 섞지 않음
- 답변은 **한국어**로

---

## 3. 진행 중인 워크플로우

- **아침 뉴스 브리핑 자동화** — ● 운영중. 매일 07:00 KST 클라우드 routine(ID `trig_01T1HWXPXp3TbrQw3aLrkWuR`). 날씨·일정·시장동향·관심ETF·포스코이앤씨·힐스테이트 메디알레·건설·주요뉴스 → 구글독스 → 카톡 → 이메일 초안.
- **NEXUS 업무 콘솔 (신규, 2026-07-26~)** — ● 운영중. 구글드라이브 전용 공유 업무 현황판. 폴더 "NEXUS콘솔"(ID `1RvfWm1gMF7VdHMeAT895jHiBjaGSyo1o`) 안 `tasks.json` + edu_console용 FastAPI 드롭인 라우터. 노션 미사용.
- **클로드코드 직장꿀팁 공유사이트 (신규, 2026-07-27)** — ◐ 기획 단계, 실행 보류. 클로드코드에 익숙하지 않은 직장인이 이미 성공한 실전 자동화 사례를 md로 공유받는 웹사이트 구상(제출은 폼 → 표준 md 자동 생성). 기획 문서: NEXUS 폴더 내 `클로드코드 직장꿀팁 공유사이트 기획.md` (ID `1Yi2aL2920Ns2GCOdQvn91iRaWBhJHQML`). 사용자가 다시 열어 상세 확정 예정.
- **교육용 동영상 제작** — ◐ 설계중. ffmpeg 컷 → 자막 분할 → SRT → 캡컷.
- **폰 사진 정리** — ◐ 설계중. DriveSync Ultimate → Claude 업무자료 선별 → 정리.
- **품질기술 워크플로우(회사 업무)** — ● 운영중. PDF→Notion, 로컬동영상→Notion 등. 회사 PC 로컬(D:\\OneDrive...\\workflows\\) 원본.
- **일본 쇼츠 스튜디오 앱** — ● 운영중. 로컬 데스크톱(D:\\Claude\\jp-shorts-auto\\studio). 노션 토큰 발급 미해결 이슈 있음(노션 보류와 별개 사안).
- **블로그/쓰레드 자동 글쓰기** — ◐ 설계중/재개 대기. 첫 게시 성공(2026-07-18), 토큰 60일 후 만료 예정.

---

## 4. NEXUS 폴더 구조 (구글 드라이브)

| 파일/폴더 | ID |
|-----------|-----|
| A AI(클로드) (폴더 — NEXUS 루트) | `1CIBrGRVRn6s0Oc9vhfi_Up7LrdCMhu0Y` |
| NEXUS 마스터 지침.md (현재 정본) | `17vlALvcCHZr8gr6SFZOI2qAqVcdpr3pO` |
| NEXUS콘솔 (업무 콘솔 폴더) | `1RvfWm1gMF7VdHMeAT895jHiBjaGSyo1o` |
| 직장꿀팁 공유사이트 기획.md | `1Yi2aL2920Ns2GCOdQvn91iRaWBhJHQML` |
| A 아침뉴스브리핑 (폴더) | `1SxCVyHZpW66u8ns5xknNm8VIEB0_jgnD` |
| claude.me 구버전(삭제) (폴더) | `1dCcLYVSYbmOVPk5LlEeGZLn1sDrpKZoO` |

---

## 5. 아이패드/웹 환경 동기화 방법

이 환경에서 Claude Code 접속 시 이 파일이 자동으로 로드됩니다.

**"두뇌 동기화해줘"** 라고 입력하면:
1. Claude가 구글 드라이브 NEXUS 마스터 지침.md를 읽어 최신 내용 확인
2. 이 `CLAUDE.md` 갱신
3. git 커밋 · 푸시

**집·회사 PC는** `~/.claude/CLAUDE.md` 포인터가 구글 드라이브 마스터를 직접 읽도록 설정되어 있습니다.

---

## 6. 참고 — 이 CLAUDE.md가 `main`에 없던 문제 (2026-07-26 발견)

이 파일은 이전에 `claude/shared-brain-cross-env-bm5f2d` 브랜치에만 존재하고 `main`에 병합된 적이 없어, `main`에서 새로 갈라친 세션은 NEXUS를 전혀 모르는 채로 시작하는 문제가 있었다. 이번에 `main` 기반 브랜치에 이 파일을 추가해 해당 문제를 해소한다. 앞으로 이 브랜치가 `main`에 머지되어야 재발하지 않는다.
