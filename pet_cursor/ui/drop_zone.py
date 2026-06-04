from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import QLabel, QFileDialog

_SUPPORTED = "이미지 파일 (*.png *.jpg *.jpeg *.webp *.bmp)"


class DropZone(QLabel):
    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(256, 256)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)
        self._placeholder = "이미지를 드래그하거나\n클릭해서 업로드"
        self.setText(self._placeholder)
        self.setStyleSheet(
            "QLabel {"
            "  background: #2d2d2d;"
            "  border: 2px dashed #666;"
            "  color: #aaa;"
            "  font-size: 14px;"
            "}"
            "QLabel:hover {"
            "  border-color: #888;"
            "  color: #ddd;"
            "}"
        )

    def show_preview(self, path: str) -> None:
        pm = QPixmap(path)
        if pm.isNull():
            self.setText(self._placeholder)
            return
        self.setPixmap(
            pm.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def mousePressEvent(self, event):
        path, _ = QFileDialog.getOpenFileName(self, "이미지 선택", "", _SUPPORTED)
        if path:
            self.file_dropped.emit(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self.file_dropped.emit(path)
                return
