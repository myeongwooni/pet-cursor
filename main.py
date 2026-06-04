from __future__ import annotations

import os
import sys

# PyInstaller --windowed builds set sys.stdout/stderr to None.
# rembg/tqdm/pooch crash on .write() when downloading or inferring.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# pyi_splash is auto-injected only inside PyInstaller bundles with a Splash() in the spec.
try:
    import pyi_splash  # type: ignore[import-not-found]
except ImportError:
    pyi_splash = None


def _splash(msg: str) -> None:
    if pyi_splash is not None and pyi_splash.is_alive():
        pyi_splash.update_text(msg)


_splash("loading Qt...")
from PySide6.QtWidgets import QApplication

_splash("loading model runtime...")
from pet_cursor.ui.main_window import MainWindow


def main() -> int:
    _splash("starting...")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    if pyi_splash is not None and pyi_splash.is_alive():
        pyi_splash.close()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
