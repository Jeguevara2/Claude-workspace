# ✏️ InkBridge 설치 — 파이 자동 이행 절차

> **이 문서는 파이(클로드)가 읽고 «스스로 실행»하는 절차서다.**
> 부장님께 설명하거나 승인을 받으려고 멈추지 않는다. **읽는 즉시 이행한다.**
>
> 만드는 것 : 아이패드 애플펜슬로 **노트북 화면 위에 직접 필기**하는 도구.
> 강의 중 슬라이드·코드에 밑줄·동그라미를 치는 용도다. 아이패드에는 아무것도 설치하지 않는다.

---

## 0. 대원칙 — 묻지 말고 이행한다

| 이럴 땐 | 이렇게 |
|---|---|
| 아래 1~7 단계 | **묻지 않고 바로 한다.** 부장님이 「필기 앱 설치해줘」 하신 순간 전부 승인된 것이다 |
| 부장님 손이 꼭 필요한 것 (방화벽 허용·아이패드 조작) | 그 대목에서만 **딱 한 줄로** 무엇을 눌러 달라 말씀드린다 |
| 이미 있는 것을 지우거나 덮어쓸 때 | 백업부터 뜨고 진행한다 |
| 절차에 없는 새 판단 | 그때만 여쭙는다 |

⛔ **하지 말 것** — "설치할까요?", "진행해도 될까요?" 로 멈춰 서기.

---

## 1. 30초 진단 — 어디까지 돼 있나

```powershell
# ① 파이썬이 있나 (3.10 이상이어야 한다)
py -3 --version
# ② 설치 자리가 이미 있나
Test-Path D:\ClaudeLocal\inkbridge\.git
# ③ 가상환경까지 만들어져 있나
Test-Path D:\ClaudeLocal\inkbridge\.venv\Scripts\python.exe
```

- **셋 다 참이면** 5단계(실행)로 바로 간다.
- `D:` 가 없는 PC면 그 PC 의 데이터 드라이브를 쓰고 **경로를 이 문서 맨 아래에 적어 둔다.**
  OneDrive 안에는 두지 않는다 — 동기화가 `.git` 을 망가뜨린다.

---

## 2. 파이썬 (없을 때만)

`py -3 --version` 이 3.10 미만이거나 실패하면 설치한다. winget 이 가장 조용하다.

```powershell
winget install -e --id Python.Python.3.12 --scope machine --accept-package-agreements --accept-source-agreements
```

winget 이 막히면 https://www.python.org/downloads/ 에서 받되,
설치 첫 화면의 **`Add python.exe to PATH` 를 반드시 체크**해야 한다. 이걸 빠뜨리면 뒤가 전부 막힌다.
설치 후 **새 PowerShell 창**을 열어야 PATH 가 잡힌다.

---

## 3. 내려받기

```powershell
New-Item -ItemType Directory -Force -Path D:\ClaudeLocal | Out-Null
git clone -b claude/ipad-pencil-notebook-drawing-0ctzrl `
  https://github.com/Jeguevara2/Claude-workspace.git D:\ClaudeLocal\inkbridge
```

이미 있으면 최신화만 한다.

```powershell
git -C D:\ClaudeLocal\inkbridge pull
```

---

## 4. 준비

```powershell
cd D:\ClaudeLocal\inkbridge
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

PySide6 내려받는 데 1~2분 걸린다. 정상이다.

### 4-1. 반드시 시험을 먼저 돌린다

```powershell
.\.venv\Scripts\python.exe -m pip install pytest pytest-asyncio
.\.venv\Scripts\python.exe -m pytest tests\ -q
```

**34개가 전부 통과해야 한다.** 하나라도 실패하면 실행하지 말고,
실패한 시험 이름과 메시지를 부장님께 그대로 보고한다. 넘겨짚어 고치지 않는다.

---

## 5. 실행

```powershell
cd D:\ClaudeLocal\inkbridge
.\run.bat
```

- 검은 창에 주소가 뜨고, 화면 가운데에 **QR 코드 창**이 뜬다.
- **방화벽 창이 뜨면** 부장님께 한 줄로 말씀드린다 :
  > 「방화벽 창에서 **개인 네트워크**에 체크하고 **액세스 허용**을 눌러 주세요. 여기서 취소하면 아이패드가 못 붙습니다.」

### 온라인 강의(Zoom·Teams)로 쓰실 때

기본값은 필기가 화면 캡처에서 제외된다. 프로젝터에는 나오지만 **Zoom 공유에는 안 보인다.**
원격 수강생에게 보여야 하면 이렇게 띄운다.

```powershell
.\run.bat --share-ink
```

---

## 6. 아이패드 붙이기

부장님 아이패드는 **셀룰러 모델**이다. USB 케이블이 가장 낫다.

부장님께 드릴 말 (한 번에 묶어서) :

> 1. 아이패드를 USB 로 꽂고, 아이패드에 뜨는 **신뢰** 를 눌러 주세요.
> 2. 아이패드 **설정 → 개인용 핫스팟 → 다른 사람의 연결 허용** 을 켜 주세요.
> 3. 아이패드 **카메라** 앱으로 노트북 화면의 **QR 코드를 비추고**, 위에 뜨는 알림을 눌러 주세요.

노트북이 아이패드를 못 알아보면 `winget install -e --id Apple.AppleDevices` 로 드라이버를 넣고
run.bat 을 다시 띄운다.

### 6-1. 데이터 요금 방어 — 이건 파이가 챙긴다

USB 테더링이 붙으면 Windows 가 **노트북 인터넷 전부를 아이패드 셀룰러로 내보낸다.**
강의 중 Windows 업데이트가 돌면 요금이 샌다. 연결이 잡힌 뒤 종량제로 돌려 둔다.

유선(이더넷)의 종량제 표시는 보호된 레지스트리 키에 들어 있어서 **명령으로 깔끔하게 못 바꾼다.**
스크립트로 우회하려 들지 말 것. 파이가 할 일은 **어느 어댑터인지 찾아서 짚어 드리는 것**까지다.

```powershell
# 아이패드 테더링 어댑터가 무엇인지 찾아 이름을 확인한다
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -like '172.20.10.*' } |
  ForEach-Object {
    $n = (Get-NetAdapter -InterfaceIndex $_.InterfaceIndex).Name
    Write-Host "→ 종량제로 바꿀 어댑터 : $n  (IP $($_.IPAddress))"
  }
```

그 이름을 넣어 부장님께 한 줄로 드린다 :

> 「**설정 → 네트워크 및 인터넷 → 이더넷 → 〈찾은 이름〉 → 종량제 연결 켬**
> 으로 바꿔 주세요. 한 번만 하시면 계속 유지되고, 강의 중 Windows 업데이트가
> 셀룰러 데이터를 쓰는 걸 막아 줍니다.」

---

## 7. 바탕화면 단추 만들기 — 「자동수행」의 핵심

부장님이 매번 폴더를 찾아 들어가지 않도록, 넥서스 단추들과 같은 자리에 하나 더 둔다.

```powershell
$W = New-Object -ComObject WScript.Shell
$S = $W.CreateShortcut("$env:USERPROFILE\Desktop\✏️ 필기 시작.lnk")
$S.TargetPath       = "D:\ClaudeLocal\inkbridge\run.bat"
$S.WorkingDirectory = "D:\ClaudeLocal\inkbridge"
$S.IconLocation     = "shell32.dll,70"
$S.Description      = "아이패드 펜슬로 노트북 화면에 필기"
$S.Save()
```

이걸로 **다음 강의부터는 바탕화면 아이콘 한 번 + 아이패드 홈 아이콘 한 번**이면 끝난다.

> **부팅 시 자동 시작은 걸지 않는다.** 강의 때만 쓰는 도구인데 늘 떠 있으면
> 화면 캡처가 계속 돌아 배터리만 먹는다. 부장님이 따로 원하시면 그때 건다.

---

## 8. 안 될 때

| 증상 | 원인과 조치 |
|---|---|
| 아이패드 Safari 가 「서버에 연결할 수 없음」 | 거의 항상 방화벽이다. 5단계 허용을 다시 확인 |
| 「Python을 찾을 수 없습니다」 | PATH 체크 누락. 파이썬 재설치 후 **새 창**에서 다시 |
| 개인용 핫스팟이 회색 | 데이터 요금제가 비활성. Wi-Fi 라면 노트북 **모바일 핫스팟**을 켜고 그쪽으로 붙인다 |
| 그림이 끊긴다 | `.\run.bat --width 960` 으로 화질을 낮춰 속도를 올린다 |
| 필기가 펜 위치와 어긋난다 | 배율 조정 화면 문제. **얼마나 어긋나는지** 적어서 보고 |

---

## 9. 끝나고 이것만 확인해서 알려줄 것

이 프로그램은 **리눅스에서 만들어져 실제 Windows + 아이패드로는 검증되지 않았다.**
아래 네 가지는 Windows 에서만 확인되는 것이니, 첫 실행 때 직접 보고 결과를 적어 준다.

| 확인할 것 | 정상이면 |
|---|---|
| **클릭 통과** | 필기가 떠 있는 상태에서 노트북 아이콘·버튼이 그대로 눌린다 |
| **포커스 안 뺏김** | 필기가 떠도 워드·파워포인트의 커서가 그대로 살아 있다 |
| **캡처 제외** | 아이패드에 보이는 화면에 내 필기가 **겹쳐 두 번** 보이지 않는다 |
| **좌표 정확도** | 펜 끝과 노트북에 그려지는 선의 위치가 일치한다 (배율 조정 화면에서 특히) |

넷 다 정상이면 「4가지 확인 완료」 한 줄이면 된다.
어긋나는 게 있으면 **증상만** 적어 준다 — 고치는 건 이쪽에서 한다.

---

## 부록 · 이 PC 의 설치 경로

| 항목 | 값 |
|---|---|
| 설치 자리 | `D:\ClaudeLocal\inkbridge` *(D: 없으면 실제 경로로 고쳐 적을 것)* |
| 저장소 | `Jeguevara2/Claude-workspace` |
| 가지 | `claude/ipad-pencil-notebook-drawing-0ctzrl` |
| 띄우는 법 | 바탕화면 **✏️ 필기 시작** |
