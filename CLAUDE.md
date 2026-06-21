# Claude 공유 두뇌 (Shared Brain)

> **단일 원본**: 구글 드라이브 두 문서가 원본입니다. 이 파일은 그 내용의 로컬 스냅샷입니다.
> 내용을 바꾸려면 구글 드라이브 문서를 직접 편집하고, Claude에게 "두뇌 동기화해줘"라고 하면 이 파일이 갱신됩니다.
>
> - 공통 지침 원본: https://docs.google.com/document/d/1wuEFRrBKVLRhYMnFLijOmUYuBMzVcQ0TdbmWd7fNw4M/edit
> - 자동화 정리 원본: https://docs.google.com/document/d/1FAihsQKoClKzY_ZDIP6ICf_jwkTk1HWQBFc7TA-jqzA/edit
> - 최종 동기화: 2026-06-21

---

## 1. 사용자 / 환경

- 이메일(개인): jechanghyun@gmail.com
- 이메일(회사): jch@poscoenc.com (포스코이앤씨)
- 사용 환경: 집 PC / 회사 PC / **아이패드** — 이 레포지토리를 통해 공통 지침 공유
- 답변은 **한국어**로

---

## 2. 작업 선호

- Notion 페이지는 토글로 접어 짧게 유지
- Notion 개인(jechanghyun@gmail.com) / 회사(poscoenc.com) 계정 구분하고 섞지 않음
- 답변은 한국어로

---

## 3. 아침 뉴스 브리핑 자동화 (핵심 워크플로우)

| 항목 | 내용 |
|------|------|
| **실행 시각** | 매일 07:00 KST (UTC 22:00, cron `0 22 * * *`) |
| **방식** | Anthropic 클라우드 예약 실행 — PC·NAS 불필요 |
| **모델** | claude-sonnet-4-6 |
| **Routine ID** | `trig_01T1HWXPXp3TbrQw3aLrkWuR` |
| **관리 링크** | https://claude.ai/code/routines/trig_01T1HWXPXp3TbrQw3aLrkWuR |

**6개 섹션 구성:**
1. 날씨 — 인천 송도, 오늘·내일
2. 일정 — 전체 캘린더, 오늘·내일·모레 (제목 클릭 = 캘린더 이동)
3. 포스코이앤씨 뉴스
4. 힐스테이트 메디알레 (은평구 대조동) 뉴스
5. 건설업계 뉴스
6. 주요뉴스

**뉴스 규칙:** 당일·전일 발표 기사만 (월요일은 금~월), 각 기사에 발표 날짜 표기

**출력 흐름:** 구글 독스 생성 → 카카오톡 '나에게' 링크 전송 → 이메일 초안(jch@poscoenc.com)

**아침브리핑 공유 폴더:**
- 폴더 ID: `1SxCVyHZpW66u8ns5xknNm8VIEB0_jgnD`
- 링크: https://drive.google.com/drive/folders/1SxCVyHZpW66u8ns5xknNm8VIEB0_jgnD
- 공개 링크(뷰어) 설정됨 → 회사·폰 어디서나 로그인 없이 열림

---

## 4. 진행 예정 / 보류 중

| 항목 | 상태 |
|------|------|
| 이메일 완전 자동발송 (SMTP 앱 비번) | 보류 — 현재는 초안만 |
| 회사 PC 공통지침 포인터 설치 | 미완 — 회원님이 직접 |
| 메모리·프로젝트 지침 완전 동기화(Git) | 회사 GitHub 접속 확인 후 결정 |
| 회사 노션 페이지 연동 | 불가 — 게스트 권한 (회사 정책) |

---

## 5. 자주 쓰는 링크

- 브리핑 routine 관리: https://claude.ai/code/routines/trig_01T1HWXPXp3TbrQw3aLrkWuR
- 아침브리핑 폴더: https://drive.google.com/drive/folders/1SxCVyHZpW66u8ns5xknNm8VIEB0_jgnD
- 공통 지침 원본: https://docs.google.com/document/d/1wuEFRrBKVLRhYMnFLijOmUYuBMzVcQ0TdbmWd7fNw4M/edit
- 자동화 정리 원본: https://docs.google.com/document/d/1FAihsQKoClKzY_ZDIP6ICf_jwkTk1HWQBFc7TA-jqzA/edit

---

## 6. 공유 두뇌 동기화 방법

어떤 환경에서 Claude Code에 접속해도 이 파일이 자동으로 읽힙니다.

**내용 업데이트 방법:**
1. 구글 드라이브 문서를 직접 편집
2. Claude에게 "두뇌 동기화해줘" 또는 "CLAUDE.md 업데이트해줘"라고 입력
3. Claude가 구글 드라이브 MCP로 최신 내용 읽어서 이 파일 갱신 후 커밋·푸시

**아이패드 환경 참고:**
- 웹 Claude Code (claude.ai/code) 에서 이 레포지토리가 자동으로 로드됨
- Google Drive MCP 연결되어 있어 동기화 즉시 가능
