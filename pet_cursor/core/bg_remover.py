from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PIL import Image, ImageOps
from rembg import remove, new_session


class BgRemoverWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)

    _session = None

    @classmethod
    def get_session(cls):
        if cls._session is None:
            cls._session = new_session("isnet-general-use")
        return cls._session

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self._path = image_path

    def run(self):
        try:
            with Image.open(self._path) as source:
                img = ImageOps.exif_transpose(source).convert("RGBA")
            result = remove(img, session=self.get_session())
            if result.mode != "RGBA":
                result = result.convert("RGBA")
            self.finished_ok.emit(result)
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")

