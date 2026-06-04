# Pet Cursor

반려동물 사진을 업로드하면 자동으로 누끼를 따고 Windows 마우스 커서를 즉시 교체하는 데스크톱 앱.
**Windows 설정에 들어가지 않아도 됩니다.**

![status](https://img.shields.io/badge/platform-Windows-blue)
![python](https://img.shields.io/badge/python-3.12-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

## 기능

- **자동 누끼**: `rembg` (`isnet-general-use` 모델) 로컬 실행. 반려동물 털 가장자리에 잘 맞음.
- **즉시 커서 적용**: `SetSystemCursor` Win32 API 호출 — 제어판 진입 불필요, 관리자 권한 불필요.
- **핫스팟 편집**: 미리보기에서 클릭하면 그 지점이 클릭 좌표가 됨.
- **멀티 해상도 커서**: 32 / 48 / 64 / 96 / 128 px을 한 `.cur`에 담아 DPI 자동 대응.
- **원클릭 복원**: `SystemParametersInfo(SPI_SETCURSORS)`로 시스템 기본 커서 복원.

## 화면 흐름

```
[이미지 업로드] → [누끼 자동 처리] → [미리보기 + 핫스팟 클릭] → [커서로 적용 ✓]
```

## 빠른 실행 (배포본)

릴리즈에서 `PetCursor-win64.zip` 다운로드 → 압축 풀고 `PetCursor.exe` 실행.

> 첫 실행 시 rembg가 모델(~170 MB)을 `~/.u2net/`에 1회 다운로드합니다.

## 개발 환경 실행

요구사항: Windows 10/11, Python 3.12+

```powershell
pip install -r requirements.txt
python main.py
```

## 직접 빌드 (PyInstaller)

```powershell
.\build.ps1 -Python "C:\Path\to\python.exe"
```

옵션:
- `-Clean` — `.venv`, `build`, `dist` 모두 삭제하고 처음부터
- `-OneFile` — 단일 `.exe`로 빌드 (배포 편하지만 시작이 ~10초 느려짐)

산출물:
- onedir(기본): `dist\PetCursor\PetCursor.exe` + `_internal\` 폴더 (전체 ~380 MB)
- onefile: `dist\PetCursor.exe` 하나

## 프로젝트 구조

```
pet_cursor/
├── ui/
│   ├── main_window.py    Qt 메인 윈도우, 워크플로우 오케스트레이션
│   ├── drop_zone.py      드래그앤드롭 + 파일 다이얼로그
│   └── preview_panel.py  누끼 미리보기 + 핫스팟 클릭 편집
└── core/
    ├── bg_remover.py     rembg 래퍼 (QThread)
    ├── cur_builder.py    PIL.Image → 멀티 해상도 .cur 변환
    └── cursor_applier.py ctypes Win32 SetSystemCursor/복원
```

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| GUI | PySide6 |
| 배경 제거 | rembg + ONNX Runtime (isnet-general-use) |
| 이미지 처리 | Pillow |
| 시스템 API | ctypes → user32.dll |
| 패키징 | PyInstaller (onedir + Splash) |

## 동작 원리

1. **누끼**: PIL 이미지 → `rembg.remove()` → RGBA 출력.
2. **.cur 생성**: 멀티 해상도(32–128 px)로 정사각 캔버스에 종횡비 유지 패딩 → 각 프레임을 BITMAPINFOHEADER + 32-bit BGRA(bottom-up) + AND 마스크로 인코딩 → ICO 파일 헤더(type=2) + 디렉토리 엔트리(핫스팟 좌표 포함) + 데이터 블롭으로 조립.
3. **적용**: `LoadCursorFromFileW(path)` → HCURSOR → `SetSystemCursor(hcursor, OCR_NORMAL)`. OS가 핸들 소유권을 가져가므로 재사용 금지.
4. **복원**: `SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)` 한 호출로 사용자 기본값 복귀.

자세한 기획·개발 기록은 [`PROCESS.md`](PROCESS.md).

## 알려진 한계

- 기본 화살표 커서(`OCR_NORMAL`)만 교체 — 텍스트, 대기 등 다른 시스템 커서는 v2 이후.
- 세션 한정 적용 (재부팅 시 사라짐) — 영구 적용은 레지스트리 수정 필요, v2 이후.
- rembg 모델은 첫 실행 시 다운로드 — 오프라인 환경 미지원.
- 털이 매우 가는 영역은 가장자리가 다소 부자연스러울 수 있음 (알파 매팅 후처리 미적용).

## 라이선스

MIT
