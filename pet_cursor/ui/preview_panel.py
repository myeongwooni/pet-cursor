from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QPainter, QPen, QPixmap, QImage, QColor
from PySide6.QtWidgets import QLabel

from PIL import Image


def _pil_to_qimage(img: Image.Image) -> QImage:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, img.width * 4, QImage.Format_RGBA8888)
    return qimg.copy()  # detach from Python-owned buffer


class PreviewPanel(QLabel):
    hotspot_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(256, 256)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: #2d2d2d; border: 1px solid #444; color: #aaa;")
        self.setText("누끼 결과가 여기에 표시됩니다")
        self._source: Image.Image | None = None
        self._hotspot: tuple[int, int] | None = None
        self._scaled_pixmap: QPixmap | None = None
        self._pixmap_rect: tuple[int, int, int, int] | None = None

    def set_image(self, image: Image.Image) -> None:
        self._source = image
        bbox = image.getbbox()
        if bbox:
            self._hotspot = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
        else:
            self._hotspot = (image.width // 2, image.height // 2)
        self.hotspot_changed.emit(*self._hotspot)
        self._rebuild_pixmap()
        self.update()

    def hotspot(self) -> tuple[int, int] | None:
        return self._hotspot

    def source_image(self) -> Image.Image | None:
        return self._source

    def _rebuild_pixmap(self) -> None:
        if not self._source:
            self._scaled_pixmap = None
            return
        qimg = _pil_to_qimage(self._source)
        self._scaled_pixmap = QPixmap.fromImage(qimg).scaled(
            self.width(), self.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )

    def resizeEvent(self, event):
        self._rebuild_pixmap()
        super().resizeEvent(event)

    def paintEvent(self, event):
        if not self._scaled_pixmap or not self._source:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#2d2d2d"))
        pm_w = self._scaled_pixmap.width()
        pm_h = self._scaled_pixmap.height()
        x = (self.width() - pm_w) // 2
        y = (self.height() - pm_h) // 2
        painter.drawPixmap(x, y, self._scaled_pixmap)
        self._pixmap_rect = (x, y, pm_w, pm_h)

        if self._hotspot:
            src_w, src_h = self._source.size
            hx, hy = self._hotspot
            mx = x + int(hx / src_w * pm_w)
            my = y + int(hy / src_h * pm_h)
            painter.setPen(QPen(QColor("red"), 2))
            painter.drawLine(mx - 8, my, mx + 8, my)
            painter.drawLine(mx, my - 8, mx, my + 8)
            painter.drawEllipse(QPoint(mx, my), 6, 6)

    def mousePressEvent(self, event):
        if not self._source or not self._pixmap_rect:
            return
        x, y, pm_w, pm_h = self._pixmap_rect
        cx = event.pos().x() - x
        cy = event.pos().y() - y
        if 0 <= cx < pm_w and 0 <= cy < pm_h:
            src_w, src_h = self._source.size
            self._hotspot = (
                int(cx / pm_w * src_w),
                int(cy / pm_h * src_h),
            )
            self.hotspot_changed.emit(*self._hotspot)
            self.update()
