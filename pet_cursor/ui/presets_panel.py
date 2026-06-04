from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QPixmap, QImage, QPainter, QColor
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QMenu, QPushButton, QVBoxLayout, QWidget, QLabel,
)

from PIL import Image

from pet_cursor.core.preset_store import MAX_SLOTS, PresetStore


def _pil_thumb(img: Image.Image, size: int) -> QPixmap:
    rgba = img.convert("RGBA") if img.mode != "RGBA" else img
    rgba = rgba.copy()
    rgba.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (45, 45, 50, 255))
    ox = (size - rgba.width) // 2
    oy = (size - rgba.height) // 2
    canvas.alpha_composite(rgba, (ox, oy))
    data = canvas.tobytes("raw", "RGBA")
    qimg = QImage(data, size, size, size * 4, QImage.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimg)


def _empty_pixmap(size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(QColor(45, 45, 50))
    painter = QPainter(pm)
    painter.setPen(QColor(110, 110, 120))
    f = painter.font()
    f.setPointSize(24)
    painter.setFont(f)
    painter.drawText(pm.rect(), Qt.AlignCenter, "+")
    painter.end()
    return pm


class _SlotButton(QPushButton):
    save_requested = Signal(int)
    load_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, slot: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.slot = slot
        self._has_preset = False
        self.setFixedSize(80, 80)
        self.setIconSize(self.size() - self.size() / 5)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.clicked.connect(self._on_clicked)

    def set_thumbnail(self, pixmap: QPixmap | None) -> None:
        self._has_preset = pixmap is not None
        if pixmap is None:
            self.setIcon(_empty_pixmap(72))
        else:
            self.setIcon(pixmap)
        self.setToolTip(
            f"슬롯 {self.slot + 1}: " +
            ("클릭=불러오기 / 우클릭=메뉴" if self._has_preset else "클릭=현재 상태 저장")
        )

    def _on_clicked(self) -> None:
        if self._has_preset:
            self.load_requested.emit(self.slot)
        else:
            self.save_requested.emit(self.slot)

    def _show_menu(self, pos) -> None:
        if not self._has_preset:
            return
        menu = QMenu(self)
        act_load = QAction("불러오기", menu)
        act_save = QAction("현재 상태로 덮어쓰기", menu)
        act_delete = QAction("삭제", menu)
        act_load.triggered.connect(lambda: self.load_requested.emit(self.slot))
        act_save.triggered.connect(lambda: self.save_requested.emit(self.slot))
        act_delete.triggered.connect(lambda: self.delete_requested.emit(self.slot))
        menu.addAction(act_load)
        menu.addAction(act_save)
        menu.addSeparator()
        menu.addAction(act_delete)
        menu.exec(self.mapToGlobal(pos))


class PresetsPanel(QGroupBox):
    save_requested = Signal(int)
    load_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, store: PresetStore, parent: QWidget | None = None):
        super().__init__(f"프리셋 (최대 {MAX_SLOTS}개)", parent)
        self.store = store
        root = QVBoxLayout(self)

        hint = QLabel("빈 슬롯 클릭 → 현재 상태 저장. 채워진 슬롯 클릭 → 불러오기. 우클릭 → 메뉴")
        hint.setStyleSheet("color: #999; font-size: 11px;")
        root.addWidget(hint)

        row = QHBoxLayout()
        self._slots: list[_SlotButton] = []
        for i in range(MAX_SLOTS):
            btn = _SlotButton(i)
            btn.save_requested.connect(self.save_requested)
            btn.load_requested.connect(self.load_requested)
            btn.delete_requested.connect(self.delete_requested)
            row.addWidget(btn)
            self._slots.append(btn)
        row.addStretch(1)
        root.addLayout(row)

        self.refresh()

    def refresh(self) -> None:
        for btn in self._slots:
            preset = self.store.load(btn.slot)
            btn.set_thumbnail(_pil_thumb(preset.image, 72) if preset else None)
