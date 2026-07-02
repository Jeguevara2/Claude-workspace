# PDF to Notion - 우클릭 컨텍스트 메뉴 설치 스크립트
# 관리자 권한 불필요 (HKCU 레지스트리에만 등록, 로그인 사용자에게만 적용됨)
#
# 사용법: 이 폴더(pdf_to_notion.py 와 같은 위치)에서 PowerShell로 실행
#   powershell -ExecutionPolicy Bypass -File .\install_pdf_to_notion.ps1

$ErrorActionPreference = "Stop"

$installDir = Join-Path $env:LOCALAPPDATA "NexusTools\pdf_to_notion"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

$scriptSource = Join-Path $PSScriptRoot "pdf_to_notion.py"
$scriptDest = Join-Path $installDir "pdf_to_notion.py"
Copy-Item $scriptSource $scriptDest -Force

Write-Host "필요 패키지 설치 확인 (PyMuPDF, pywin32)..."
python -m pip install --quiet --upgrade PyMuPDF pywin32

$pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $pythonw) {
    $pythonExe = (Get-Command python.exe -ErrorAction Stop).Source
    $pythonw = Join-Path (Split-Path $pythonExe) "pythonw.exe"
}
if (-not (Test-Path $pythonw)) {
    throw "pythonw.exe를 찾을 수 없습니다. Python 설치를 확인하세요."
}

$command = "`"$pythonw`" `"$scriptDest`" `"%1`""

$keyPath = "HKCU:\Software\Classes\SystemFileAssociations\.pdf\shell\PDFtoNotion"
New-Item -Path $keyPath -Force | Out-Null
Set-ItemProperty -Path $keyPath -Name "(Default)" -Value "PDF to Notion"
Set-ItemProperty -Path $keyPath -Name "Icon" -Value $pythonw

$commandKeyPath = Join-Path $keyPath "command"
New-Item -Path $commandKeyPath -Force | Out-Null
Set-ItemProperty -Path $commandKeyPath -Name "(Default)" -Value $command

Write-Host "설치 완료."
Write-Host "PDF 파일 우클릭 -> 'PDF to Notion' 메뉴가 보이면 정상입니다."
