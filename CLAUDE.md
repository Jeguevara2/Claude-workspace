# 넥서스(NEXUS) — 공유 두뇌

> **단일 원본(SSOT): 노션이 마스터입니다.**
> 구글 드라이브 md는 백업. 내용을 바꾸려면 노션 마스터 페이지를 직접 편집하세요.
>
> - NEXUS 노션 마스터: https://app.notion.com/p/388d60207bf980cdac56fea299a382f5
> - NEXUS 상위 페이지(클로드): https://app.notion.com/p/36dd60207bf9801ca766eef6087cf0b4
> - 클로드 지침 목록: https://app.notion.com/p/36dd60207bf980c3b5efc88cf540bd17
> - 구글 드라이브 NEXUS 폴더: https://drive.google.com/drive/folders/1CIBrGRVRn6s0Oc9vhfi_Up7LrdCMhu0Y
> - 최종 동기화: 2026-06-24

---

## ★ NEXUS 수정 시 체크리스트 (작업 완료 전 반드시 확인)

- [ ] **MD 버전** (노션 NEXUS 마스터지침.MD) 반영했는가?
- [ ] **일반용어 버전** (노션 클로드 페이지) 동일하게 반영했는가?
- [ ] **git 레포 CLAUDE.md** 갱신이 필요한가?
- [ ] 위 항목 중 하나라도 빠졌다면 → 완료 선언 전에 먼저 처리할 것

---

## ★ 운영 규칙 (모든 환경 공통 — 최우선)

- **세션 시작 시**: 노션 NEXUS 마스터 페이지와 「클로드 지침 목록」을 읽어 컨텍스트로 반영. 접속 중인 환경의 `workflows` 폴더에 누락된 md가 있으면 다운로드해 채운다.
- **세션 종료 전 / 의미 있는 산출물**: 새 자동화·결정·선호·용어·진행상황을 **노션 마스터에 제자리 갱신** (먼저 제안 후 수행). 로컬·로컬 메모리에만 적기 금지.
- **단일 원본(SSOT)**: 노션이 마스터. 구글 드라이브 md는 백업.
- **증류된 핵심만** 담는다. raw 대화 로그는 claude.ai 대화 기록에 있음.

---

## ★ 작업 스타일 (사용자 피드백)

- "무조건 안 된다"로 끝내지 말 것 — ①왜 안 되는지 간단히 ②우회책·대안 1~2개 ③추천안을 함께 제시. **파트너형 조력.**
- **선택지는 항상 번호를 매겨서 보여줄 것.** 사용자는 번호로 명령한다.

---

## 용어

- **넥서스(NEXUS)** = 사용자가 구축한 공유 두뇌. **마스터는 노션 페이지.** 구글 드라이브 폴더 "A AI(클로드)"(ID `1CIBrGRVRn6s0Oc9vhfi_Up7LrdCMhu0Y`)는 md 백업·자동화 산출물 저장소.

---

## 1. 사용자 / 환경

- 이메일(개인): jechanghyun@gmail.com
- 이메일(회사): jch@poscoenc.com (포스코이앤씨)
- **집 PC**: 구글드라이브 E:\\ 로컬 미러링 (NEXUS = E:\\A AI(클로드)), K: 도 마운트. `~/.claude/CLAUDE.md` NEXUS 포인터 설치 완료 ✅
- **회사 PC**: 드라이브 데스크톱 동기화 차단 (커넥터/브라우저만). 개인 구글 브라우저 로그인 가능. `~/.claude/CLAUDE.md` NEXUS 포인터 설치 완료 ✅ (2026-06-22)
- **아이패드**: 웹 Claude Code (claude.ai/code) + Google Drive MCP + 이 git 레포 → 이 `CLAUDE.md`가 자동으로 로드됨

---

## 2. 작업 선호

- Notion 페이지는 토글로 접어 짧게 유지
- Notion 개인(jechanghyun@gmail.com) / 회사(poscoenc.com) 계정 구분하고 섞지 않음
- 답변은 **한국어**로

---

## 3. 진행 중인 워크플로우

| 항목 | 상태 |
|------|------|
| 아침 뉴스 브리핑 자동화 | ● 작동 중 |
| NEXUS 공유 두뇌 운영 | ● 작동 중 |
| 품질기술 워크플로우 (회사 업무) | ● 작동 중 |
| 폰 사진 정리 워크플로우 | ◐ 설계 중 |
| 이메일 완전 자동발송 (SMTP) | 보류 — 현재 초안만 |

### 아침 뉴스 브리핑 자동화

| 항목 | 내용 |
|------|------|
| **실행 시각** | 매일 07:00 KST (UTC 22:00, cron `0 22 * * *`) |
| **방식** | Anthropic 클라우드 예약 실행 — PC·NAS 불필요 |
| **모델** | claude-sonnet-4-6 |
| **Routine ID** | `trig_01T1HWXPXp3TbrQw3aLrkWuR` |
| **관리 링크** | https://claude.ai/code/routines/trig_01T1HWXPXp3TbrQw3aLrkWuR |

**6개 섹션:** ①날씨(인천 송도) ②일정(전체 캘린더, 오늘·내일·모레) ③포스코이앤씨 ④힐스테이트 메디알레(은평구 대조동) ⑤건설업계 ⑥주요뉴스

**뉴스 규칙:** 당일·전일 기사만 (월요일은 금~월), 각 기사에 발표 날짜 표기

**출력:** 구글 독스 → 카카오톡 '나에게' 링크 → 이메일 초안(jch@poscoenc.com)

**아침브리핑 폴더 ID:** `1SxCVyHZpW66u8ns5xknNm8VIEB0_jgnD`

### 품질기술 워크플로우 (회사 업무)

- 선행마감교육 보고서 작성
- PDF 기술자료 → Notion 연동
- 로컬 동영상 → Notion 재생링크
- 구글 드라이브 업무자료 추출
- 회사 PC 로컬(D:\\OneDrive...\\workflows) 원본 + NEXUS 하위폴더 "품질기술 워크플로우 (회사PC 미러)"에 열람용 미러 (2026-06-22)

### 폰 사진 정리 워크플로우 (설계 중)

DriveSync Ultimate로 폰→드라이브 → Claude가 '명백한 업무자료'만 positive 선별 (업무자료만 선별, 가족 제외 방식 아님) → 업무 폴더 → PC 다운로드 후 드라이브 삭제. 최신순 100개씩 시험.

---

## 4. NEXUS 폴더 구조 (구글 드라이브 백업)

| 파일/폴더 | ID |
|-----------|-----|
| A AI(클로드) (폴더 — NEXUS 루트) | `1CIBrGRVRn6s0Oc9vhfi_Up7LrdCMhu0Y` |
| NEXUS 마스터 지침.md (백업) | `1-N9BkEMJg18CBxGzQHEJ9JWP6S3wTXRu` |
| Claude 공통 지침 (백업) | `1lx5uo3FyU6tfoKBiceOvGJZm7tLyLfTd44JmVY0LYBQ` |
| 자동화·워크플로우 정리 (백업) | `1FAihsQKoClKzY_ZDIP6ICf_jwkTk1HWQBFc7TA-jqzA` |
| A 아침뉴스브리핑 (폴더) | `1SxCVyHZpW66u8ns5xknNm8VIEB0_jgnD` |
| claude.me 구버전(삭제) (폴더) | `1dCcLYVSYbmOVPk5LlEeGZLn1sDrpKZoO` |

---

## 5. 아이패드 환경 동기화 방법

아이패드에서 Claude Code 접속 시 이 파일이 자동으로 로드됩니다.

**"두뇌 동기화해줘"** 라고 입력하면:
1. Claude가 노션 NEXUS 마스터 페이지를 읽어 최신 내용 확인
2. 이 `CLAUDE.md` 갱신
3. git 커밋 · 푸시

**집·회사 PC는** `~/.claude/CLAUDE.md` 포인터가 노션을 직접 읽도록 설정되어 있습니다.
