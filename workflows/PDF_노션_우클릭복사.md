PC의 아무 PDF 파일이나 우클릭 -> "PDF to Notion" 클릭 한 번으로, 페이지별 이미지를 클립보드에 담아
원하는 Notion 페이지에 Ctrl+V로 바로 붙여넣는다. (🖥️ 공통 - 집PC/회사PC 모두, Python 설치 필요)

## 기존 워크플로우와의 차이
- "기술자료 PDF → Notion 이미지 삽입 (로컬)" / "PDF자료 → Notion 이관 (Selenium 무인)"은
  특정 폴더(기술브리프 378개)를 파일명=페이지제목으로 자동 매칭해 일괄 업로드하는 배치 자동화.
- 이 워크플로우는 임의의 PDF 1개를 그때그때 원하는 Notion 페이지에 수동으로 붙여넣는
  경량 대화형 도구. API 토큰/Selenium 불필요, 클립보드만 사용.

## 스크립트
`tools/pdf_to_notion/pdf_to_notion.py`
- PyMuPDF(fitz)로 PDF 각 페이지를 PNG(DPI 200)로 렌더링 -> 임시폴더 저장
- pywin32로 Windows 클립보드에 CF_HDROP(파일 목록) 포맷으로 담음
  (파일 탐색기에서 여러 파일을 Ctrl+C 한 것과 동일한 포맷)
- 완료/실패 시 메시지박스로 알림

## 설치
`tools/pdf_to_notion/install_pdf_to_notion.ps1`
1. PyMuPDF, pywin32 pip 설치
2. 스크립트를 `%LOCALAPPDATA%\NexusTools\pdf_to_notion\`에 복사
3. `HKCU:\Software\Classes\SystemFileAssociations\.pdf\shell\PDFtoNotion` 레지스트리에
   "PDF to Notion" 우클릭 메뉴 등록 (관리자 권한 불필요)

제거: `tools/pdf_to_notion/uninstall_pdf_to_notion.ps1`

## 사용법
1. PDF 파일 우클릭 -> "PDF to Notion" 클릭
2. "N페이지 이미지 복사 완료" 메시지 확인
3. Notion에서 원하는 페이지 열고 원하는 위치에 Ctrl+V

## 주요 설정값
- `DPI` 200 (150=용량 절약, 300=고화질) — 스크립트 상단 상수 직접 수정

## 검증 필요 항목 (설계중 -> 검증중 전환 조건)
- Notion 웹/데스크톱 앱에서 CF_HDROP(여러 이미지 파일) 붙여넣기 시 실제로
  페이지 순서대로 이미지 블록이 연속 삽입되는지 실PC에서 확인
- 회사 PC의 보안 정책이 레지스트리 등록/pip 설치를 막는지 확인 (집 PC에서 우선 검증 권장)
