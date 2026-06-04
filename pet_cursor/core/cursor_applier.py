from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path

# (OCR_* id, label, default_checked)
# Order = visual layout order in the UI.
SYSTEM_CURSORS: list[tuple[int, str, bool]] = [
    (32512, "화살표 (기본)",    True),
    (32513, "텍스트",          False),
    (32514, "대기",            False),
    (32650, "백그라운드 작업",  False),
    (32649, "링크 선택",        False),
    (32651, "도움말",          False),
    (32515, "정밀 (십자)",     False),
    (32648, "사용 안 함",       False),
    (32646, "이동",            False),
    (32644, "수평 크기",        False),
    (32645, "수직 크기",        False),
    (32642, "대각 크기 ↘",     False),
    (32643, "대각 크기 ↙",     False),
    (32516, "수직 화살표",      False),
]

SPI_SETCURSORS = 0x0057

_user32 = ctypes.WinDLL("user32", use_last_error=True)

_user32.LoadCursorFromFileW.argtypes = [wintypes.LPCWSTR]
_user32.LoadCursorFromFileW.restype = wintypes.HANDLE

_user32.SetSystemCursor.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_user32.SetSystemCursor.restype = wintypes.BOOL

_user32.SystemParametersInfoW.argtypes = [
    wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT,
]
_user32.SystemParametersInfoW.restype = wintypes.BOOL


def apply_cursor(cur_path: Path, targets: list[int]) -> None:
    """Apply the given .cur to each OCR_* system cursor id in `targets`.

    SetSystemCursor takes ownership of the HCURSOR, so we load a fresh handle
    per target (same handle reused across calls would be invalid after the first).
    """
    if not targets:
        return
    path_str = str(cur_path)
    for ocr in targets:
        hcursor = _user32.LoadCursorFromFileW(path_str)
        if not hcursor:
            raise OSError(
                f"LoadCursorFromFileW failed (err={ctypes.get_last_error()}, path={cur_path})"
            )
        if not _user32.SetSystemCursor(hcursor, ocr):
            raise OSError(
                f"SetSystemCursor failed (OCR={ocr}, err={ctypes.get_last_error()})"
            )


def restore_cursor() -> None:
    """Restore ALL system cursors to user defaults in one shot."""
    if not _user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0):
        raise OSError(
            f"SystemParametersInfoW(SPI_SETCURSORS) failed (err={ctypes.get_last_error()})"
        )
