from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path

OCR_NORMAL = 32512
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


def apply_cursor(cur_path: Path) -> None:
    hcursor = _user32.LoadCursorFromFileW(str(cur_path))
    if not hcursor:
        raise OSError(
            f"LoadCursorFromFileW failed (err={ctypes.get_last_error()}, path={cur_path})"
        )
    # SetSystemCursor takes ownership of hcursor.
    if not _user32.SetSystemCursor(hcursor, OCR_NORMAL):
        raise OSError(f"SetSystemCursor failed (err={ctypes.get_last_error()})")


def restore_cursor() -> None:
    if not _user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0):
        raise OSError(
            f"SystemParametersInfoW(SPI_SETCURSORS) failed (err={ctypes.get_last_error()})"
        )
