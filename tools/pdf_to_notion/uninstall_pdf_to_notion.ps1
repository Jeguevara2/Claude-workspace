# PDF to Notion - 우클릭 컨텍스트 메뉴 제거 스크립트
# 사용법: powershell -ExecutionPolicy Bypass -File .\uninstall_pdf_to_notion.ps1

Remove-Item -Path "HKCU:\Software\Classes\SystemFileAssociations\.pdf\shell\PDFtoNotion" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path (Join-Path $env:LOCALAPPDATA "NexusTools\pdf_to_notion") -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "제거 완료."
