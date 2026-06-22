# 넥서스(NEXUS) — 공유 두뇌

> **단일 원본**: 구글 드라이브 "A AI(클로드)" 폴더가 NEXUS의 원본입니다.
> 내용을 바꾸려면 드라이브 문서를 직접 편집하고, Claude에게 "두뇌 동기화해줘"라고 하면 이 파일이 갱신됩니다.
>
> - NEXUS 폴더: https://drive.google.com/drive/folders/1CIBrGRVRn6s0Oc9vhfi_Up7LrdCMhu0Y
> - NEXUS 마스터 지침.md ID: `1-N9BkEMJg18CBxGzQHEJ9JWP6S3wTXRu`
> - Claude 공통 지침 ID: `1lx5uo3FyU6tfoKBiceOvGJZm7tLyLfTd44JmVY0LYBQ`
> - 자동화 정리 ID: `1FAihsQKoClKzY_ZDIP6ICf_jwkTk1HWQBFc7TA-jqzA`
> - 최종 동기화: 2026-06-22

---

## ★ 운영 규칙 (모든 환경 공통 — 최우선)

- **세션 시작 시**: NEXUS 폴더(ID `1CIBrGRVRn6s0Oc9vhfi_Up7LrdCMhu0Y`)를 조회해 마스터 지침과 워크플로우 현황을 컨텍스트로 반영
- **세션 종료 전 / 의미 있는 산출물**: 새 자동화·결정·선호·용어·진행상황을 드라이브 원본에 갱신(먼저 제안 후 수행). 로컬 파일·로컬 메모리에만 적기 금지
- **버전관리**: NEXUS md 문서를 새 버전으로 만들면 옛 버전은 "claude.me 구버전(삭제)" 폴더(ID `1dCcLYVSYbmOVPk5LlEeGZLn1sDrpKZoO`)로 이동. 집 PC는 E:\\A AI(클로드) 로컬 미러로 직접 이동 가능
- **증류된 핵심만** 담는다. raw 대화 로그는 claude.ai 대화 기록에 있음

---

## ★ 작업 스타일 (사용자 피드백)

"무조건 안 된다"로 끝내지 말 것 — 제약이 있으면 ①왜 안 되는지 간단히 ②우회책·대안 1~2개 ③추천안을 함께 제시. **파트너형 조력**.

---

## 용어

- **넥서스(NEXUS)** = 구글 드라이브에 구축한 공유 두뇌. 폴더 "A AI(클로드)"(ID `1CIBrGRVRn6s0Oc9vhfi_Up7LrdCMhu0Y`)와 그 안의 자동화·워크플로우·지침 전체. 사용자가 "넥서스"라 하면 이것.

---

## 1. 사용자 / 환경

- 이메일(개인): jechanghyun@gmail.com
- 이메일(회사): jch@poscoenc.com (포스코이앤씨)
- **집 PC**: 구글드라이브 E:\\ 로컬 미러링 (NEXUS = E:\\A AI(클로드)), K: 도 마운트 → 로컬 파일 직접 처리·이동 가능
- **회사 PC**: 드라이브 데스크톱 동기화 차단 (커넥터/브라우저만). 개인 구글 브라우저 로그인 가능
- **아이패드**: 웹 Claude Code (claude.ai/code) + Google Drive MCP + 이 git 레포

---

## 2. 작업 선호

- Notion 페이지는 토글로 접어 짧게 유지
- Notion 개인(jechanghyun@gmail.com) / 회사(poscoenc.com) 계정 구분하고 섞지 않음
- 답변은 **한국어**로

---

## 3. 아침 뉴스 브리핑 자동화 (핵심 워크플로우)

| 항목 | 내용 |
|------|------|
| **실행 시각** | 매일 07:00 KST (UTC 22:00, cron `0 22 * * *`) |
| **방식** | Anthropic 클라우드 예약 실행 — PC·NAS 불필요 |
| **모델** | claude-sonnet-4-6 |
| **Routine ID** | `trig_01T1HWXPXp3TbrQw3aLrkWuR` |
| **관리 링크** | https://claude.ai/code/routines/trig_01T1HWXPXp3TbrQw3aLrkWuR |

**6개 섹션:** ①날씨(인천 송도, 오늘·내일) ②일정(전체 캘린더, 오늘·내일·모레, 제목 클릭=이동) ③포스코이앤씨 ④힐스테이트 메디알레(은평구 대조동) ⑤건설업계 ⑥주요뉴스

**뉴스 규칙:** 당일·전일 발표 기사만 (월요일은 금~월), 각 기사에 발표 날짜 표기

**출력 흐름:** 구글 독스 생성 → 카카오톡 '나에게' 링크 전송 → 이메일 초안(jch@poscoenc.com)

**아침브리핑 폴더 ID:** `1SxCVyHZpW66u8ns5xknNm8VIEB0_jgnD`

---

## 4. 진행 중인 워크플로우

| 항목 | 상태 |
|------|------|
| 아침 뉴스 브리핑 자동화 | ● 작동 중 |
| NEXUS 공유 두뇌 운영 | ● 작동 중 |
| 폰 사진 정리 워크플로우 | ◐ 설계 중 |
| 이메일 완전 자동발송 (SMTP) | 보류 — 현재 초안만 |
| 회사 PC NEXUS 포인터 설치 | 미완 — 직접 설치 필요 |
| 회사 노션 페이지 연동 | 불가 — 게스트 권한 |

**폰 사진 정리 워크플로우 (설계 중):**
DriveSync Ultimate로 폰→드라이브 → Claude가 '명백한 업무자료'만 positive 선별 (업무자료만 선별, 가족 제외 방식 아님) → 업무 폴더 → PC 다운로드 후 드라이브 삭제. 최신순 100개씩 시험.

---

## 5. NEXUS 폴더 구조

| 파일/폴더 | ID | 설명 |
|-----------|-----|------|
| A AI(클로드) (폴더) | `1CIBrGRVRn6s0Oc9vhfi_Up7LrdCMhu0Y` | NEXUS 루트 |
| NEXUS 마스터 지침.md | `1-N9BkEMJg18CBxGzQHEJ9JWP6S3wTXRu` | Claude 작업용 단일 원본 |
| Claude 공통 지침 | `1lx5uo3FyU6tfoKBiceOvGJZm7tLyLfTd44JmVY0LYBQ` | 모든 환경 공통 지침 |
| 자동화·워크플로우 정리 | `1FAihsQKoClKzY_ZDIP6ICf_jwkTk1HWQBFc7TA-jqzA` | 관제탑 문서 |
| NEXUS 현황 보고.pptx | `1LKSrB4q-kRA2GQchgFdnmqlwrIaWIJdk` | 사람용 상태 보고서 |
| A 아침뉴스브리핑 (폴더) | `1SxCVyHZpW66u8ns5xknNm8VIEB0_jgnD` | 브리핑 문서 저장소 |
| claude.me 구버전(삭제) (폴더) | `1dCcLYVSYbmOVPk5LlEeGZLn1sDrpKZoO` | 구버전 아카이브 |

---

## 6. 공유 두뇌(넥서스) 동기화 방법

어떤 환경에서 Claude Code에 접속해도 이 파일이 자동으로 읽힙니다.

**내용 업데이트:**
1. 구글 드라이브 NEXUS 문서를 직접 편집
2. Claude에게 "두뇌 동기화해줘" 입력
3. Claude가 Google Drive MCP로 최신 내용 읽어서 이 파일 갱신 후 커밋·푸시

**아이패드 환경:** 웹 Claude Code + Google Drive MCP 연결됨 → 동기화 즉시 가능
