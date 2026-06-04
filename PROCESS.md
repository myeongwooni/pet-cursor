# Pet Cursor — 기획 및 개발 기록

> 반려동물 사진 → 자동 누끼 → Windows 마우스 커서 자동 변경 (시스템 설정 진입 불필요)

작성일: 2026-06-04

---

## 1. 출발점 — 사용자의 요구

원문 요구사항:

> 윈도우 프로그램을 만들고 싶어. 반려동물 사진을 업로드하면, 누끼를 자연스럽게 딴 후 마우스 커서 변경까지 자동으로 되는 프로그램. 사용자는 윈도우 설정 들어가서 하지 않고 프로그램만 사용을 하면 마우스 커서 변경을 할 수 있는 거지.

핵심 제약 3가지로 분해:

1. **누끼를 "자연스럽게"** — 반려동물 사진은 털 가장자리가 까다로워서, 자연스러움이 핵심 품질 지표가 됨.
2. **자동 커서 적용** — Windows 제어판/설정 진입 없이 프로그램 안에서 끝나야 함.
3. **Windows 데스크톱 앱** — 웹앱이나 모바일이 아닌 로컬 실행 프로그램.

---

## 2. 1단계: 기술적 실현 가능성 검토

세 핵심 제약을 각각 기술 옵션으로 매핑.

### 2.1 누끼 (배경 제거)

| 옵션 | 장점 | 단점 |
|---|---|---|
| `rembg` (U2Net) | 무료, 로컬 실행, Python 통합 쉬움 | 털 디테일에서 약간 부자연스러울 수 있음 |
| `BiRefNet` / `RMBG-2.0` | 최신 모델, 털 디테일 자연스러움 | 모델 크기/추론 시간 부담 |
| Remove.bg API | 결과 품질 최상 | 유료, 네트워크 의존, 비용 누적 |

→ 로컬 실행이며 반려동물 사진에 적합한 `isnet-general-use` 모델(`rembg` 내) 선택 가능 확인.

### 2.2 시스템 설정 없이 커서 변경

핵심 API:

- `SetSystemCursor(hcursor, OCR_NORMAL)` — 시스템 커서를 즉시 교체. **관리자 권한 불필요.**
- `LoadCursorFromFileW(path)` — `.cur` 파일에서 커서 핸들 로드.
- `SystemParametersInfoW(SPI_SETCURSORS, ...)` — 사용자 기본 커서로 일괄 복원.

→ "사용자가 설정에 들어가지 않아도 된다"는 요구 충족 가능 확인.

### 2.3 PNG → .cur 변환

- Windows 커서는 `.cur`/`.ani` 전용 포맷.
- `.cur`는 `.ico`와 거의 동일한 구조 (`type` 필드 = 2, 디렉토리 엔트리에 핫스팟 좌표).
- 멀티 해상도(32/48/64/96/128 px) 포함하면 DPI 대응 가능.

### 2.4 결론

**가능.** 모든 기술 요소가 존재하며 무료/로컬로 구현 가능.

---

## 3. 2단계: 스택 결정

후보:

| 스택 | 장점 | 단점 |
|---|---|---|
| **Python + PySide6** | rembg 통합 쉬움, 개발 속도 빠름, ctypes로 Win32 API 직접 호출 | 배포 사이즈 큼 (PyInstaller) |
| C# WPF/.NET | 단일 exe 깔끔, Win32 API 자연스러움 | ONNX Runtime으로 모델 직접 다뤄야 함 |
| Electron / Tauri | UI 자유도 | 네이티브 API/모델 연동 부가 작업 |

**결정: Python + PySide6.** AI 모델 통합 부담이 가장 낮고, MVP 검증 속도가 가장 빠름.

---

## 4. 3단계: MVP 설계

### 4.1 범위

**MVP 포함**
- 이미지 1장 업로드 (파일 다이얼로그 + 드래그앤드롭)
- 자동 누끼 (rembg)
- 미리보기 + 클릭으로 핫스팟 설정
- 기본 화살표 커서(`OCR_NORMAL`)만 교체
- 원복 버튼

**MVP 제외 (v2 이후)**
- 17종 시스템 커서 전체 교체
- 애니메이션 커서(.ani)
- 프리셋 저장, 부팅 시 자동 적용
- 알파 매팅 후처리

### 4.2 모듈 구조

```
pet_cursor/
├── main.py
├── pet_cursor/
│   ├── ui/
│   │   ├── main_window.py    — QMainWindow, 전체 레이아웃 + 워크플로우
│   │   ├── drop_zone.py      — 드래그앤드롭/클릭 업로드 위젯
│   │   └── preview_panel.py  — 누끼 결과 + 핫스팟 표시/편집
│   └── core/
│       ├── bg_remover.py     — rembg 래퍼 (QThread 워커)
│       ├── cur_builder.py    — PIL.Image → .cur 변환
│       └── cursor_applier.py — Win32 API 호출 (적용/복원)
└── requirements.txt
```

### 4.3 데이터 플로우

```
[파일 선택/드롭]
   ↓
[원본 미리보기 표시]  ─→  [BgRemoverWorker (QThread)]
                                ↓ RGBA PIL.Image
                       [PreviewPanel.set_image()]
                                ↓ 사용자 클릭
                       [핫스팟 좌표 갱신]
                                ↓ "커서로 적용"
                       [cur_builder.build_cur()]
                                ↓ %TEMP%/pet_cursor.cur
                       [cursor_applier.apply_cursor()]
                                ↓ Win32 SetSystemCursor
                              [✓ 즉시 반영]
```

### 4.4 의사결정 항목

| 항목 | 채택 | 근거 |
|---|---|---|
| 모델 번들 vs 다운로드 | **첫 실행 시 다운로드** | 모델 ~170MB → 배포 사이즈/업데이트 부담 회피 |
| 핫스팟 기본값 | **불투명 영역 bbox 중심, 사용자 클릭으로 변경** | 자동 추정 가능 + 미세 조정 여지 |
| 영구 적용 | **세션 한정, 종료 시 복원 안내** | 레지스트리 수정 없이 안전. 사용자 되돌리기 쉬움 |
| 누끼 모델 | **`isnet-general-use`** | 반려동물 털 디테일이 `u2net`보다 자연스러움 |

### 4.5 핵심 기술 노트

**`.cur` 포맷**
- 헤더(6B) + 디렉토리 엔트리들(16B each) + 이미지 데이터 블롭.
- `.ico`와 거의 동일하지만 `type=2`, 그리고 디렉토리 엔트리에서 planes/bitcount 자리에 hotspot_x/hotspot_y가 들어감.
- 이미지 데이터는 BMP/DIB 포맷: BITMAPINFOHEADER + BGRA(bottom-up) + AND 마스크.
- BITMAPINFOHEADER의 `biHeight`는 실제 높이의 2배로 적어야 함 (AND 마스크 영역 포함).

**`SetSystemCursor` 주의점**
- HCURSOR의 소유권이 OS로 이전됨 → 동일 핸들 재사용 금지.
- 복원은 별도 백업 없이 `SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)` 한 줄.

**`rembg` 세션**
- 모델 로딩이 무거우므로 `new_session()`은 한 번만 호출 후 캐싱 (`BgRemoverWorker._session` 클래스 변수).
- 추론은 `QThread`로 분리해서 UI 블로킹 방지.

---

## 5. 4단계: 구현

### 5.1 파일별 책임

| 파일 | 책임 |
|---|---|
| `main.py` | QApplication 부트스트랩 |
| `ui/main_window.py` | 워크플로우 오케스트레이션, 워커 라이프사이클, 종료 시 복원 확인 |
| `ui/drop_zone.py` | 파일 입력 (드래그앤드롭 + 클릭) |
| `ui/preview_panel.py` | PIL ↔ Qt 이미지 변환, 핫스팟 표시/편집 (클릭 좌표 ↔ 소스 좌표 매핑) |
| `core/bg_remover.py` | rembg 호출 (QThread), 세션 캐싱 |
| `core/cur_builder.py` | RGBA → 멀티 해상도 .cur 바이너리 작성 |
| `core/cursor_applier.py` | ctypes 기반 Win32 API 호출 |

### 5.2 구현 시 주의한 부분

- **PIL → QImage 변환**: `tobytes` 결과를 그대로 `QImage`에 넘기면 GC 시점에 댕글링 포인터가 됨 → `qimg.copy()`로 분리.
- **핫스팟 좌표 매핑**: 미리보기는 위젯 크기에 맞춰 스케일·중앙 정렬되므로, 사용자 클릭 좌표를 원본 이미지 좌표로 역변환 필요. `_pixmap_rect`(위젯 내 픽스맵 영역)를 paintEvent에서 기록해 두고 mousePressEvent에서 사용.
- **각 해상도별 핫스팟**: 정사각 캔버스에 패딩하므로 `(hotspot * scale) + offset` 으로 보정.
- **종료 시 복원 안내**: 사용자가 커서 변경 상태로 종료하면 마우스 추적이 어려울 수 있어 `closeEvent`에서 복원 옵션 제공.

---

## 6. 5단계: 실행

```bash
pip install -r requirements.txt
python main.py
```

- 첫 실행: rembg가 모델을 `~/.u2net/`에 다운로드 (~170MB, 한 번만).
- 이미지 업로드 → 자동 누끼 → 미리보기 클릭으로 핫스팟 설정 → "커서로 적용" 클릭 → 즉시 반영.
- "원본 복원" 버튼 또는 창 닫을 때 복원 선택.

**배포 (선택):**
```bash
pyinstaller --onefile --windowed --name PetCursor main.py
```

---

## 7. 향후 개선 (v2+)

| 우선순위 | 항목 |
|---|---|
| 높음 | 17종 시스템 커서 일괄 교체 옵션 |
| 높음 | 영구 적용 (레지스트리 + 재부팅 후 유지) |
| 중간 | 알파 매팅 후처리 (털 가장자리 자연스러움) |
| 중간 | 프리셋 저장/관리 (여러 반려동물) |
| 낮음 | 애니메이션 커서(.ani) — 짧은 영상/GIF 입력 |
| 낮음 | 자동 핫스팟 추정 (얼굴/코 검출) |

---

## 8. 의사결정 로그

| 날짜 | 결정 | 근거 |
|---|---|---|
| 2026-06-04 | 스택: Python + PySide6 | rembg 통합 용이성, 빠른 MVP |
| 2026-06-04 | 모델: isnet-general-use | 반려동물 털 디테일 |
| 2026-06-04 | 모델 배포: 첫 실행 시 다운로드 | 배포 사이즈 절감 |
| 2026-06-04 | 영구 적용: 세션 한정 | 사용자 복구 용이성 |
| 2026-06-04 | 핫스팟 기본값: bbox 중심 + 클릭 편집 | 자동 추정 + 미세 조정 |
| 2026-06-04 | MVP 커서 범위: `OCR_NORMAL`만 | 범위 최소화, 검증 우선 |
