from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from pet_cursor.core.cursor_applier import SYSTEM_CURSORS


class CursorTargetsPanel(QGroupBox):
    """Checkboxes that pick which OCR_* system cursors get replaced."""

    changed = Signal(list)  # current list of OCR ids

    def __init__(self, parent: QWidget | None = None):
        super().__init__("적용할 시스템 커서", parent)
        root = QVBoxLayout(self)

        toggle_row = QHBoxLayout()
        all_btn = QPushButton("전체 선택")
        none_btn = QPushButton("전체 해제")
        default_btn = QPushButton("기본만")
        all_btn.clicked.connect(self._check_all)
        none_btn.clicked.connect(self._check_none)
        default_btn.clicked.connect(self._check_default)
        toggle_row.addWidget(all_btn)
        toggle_row.addWidget(none_btn)
        toggle_row.addWidget(default_btn)
        toggle_row.addStretch(1)
        root.addLayout(toggle_row)

        grid = QGridLayout()
        self._checkboxes: list[QCheckBox] = []
        cols = 4
        for i, (ocr, label, default) in enumerate(SYSTEM_CURSORS):
            cb = QCheckBox(label)
            cb.setChecked(default)
            cb.setProperty("ocr", ocr)
            cb.toggled.connect(self._emit)
            grid.addWidget(cb, i // cols, i % cols)
            self._checkboxes.append(cb)
        root.addLayout(grid)

    def selected(self) -> list[int]:
        return [cb.property("ocr") for cb in self._checkboxes if cb.isChecked()]

    def set_selected(self, ocr_ids: list[int]) -> None:
        ids = set(ocr_ids)
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(cb.property("ocr") in ids)
            cb.blockSignals(False)
        self._emit()

    def _check_all(self) -> None:
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
        self._emit()

    def _check_none(self) -> None:
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)
        self._emit()

    def _check_default(self) -> None:
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(bool(cb.property("ocr") == 32512))
            cb.blockSignals(False)
        self._emit()

    def _emit(self) -> None:
        self.changed.emit(self.selected())
