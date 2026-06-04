from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QMessageBox,
)

from PIL import Image

from pet_cursor.ui.drop_zone import DropZone
from pet_cursor.ui.preview_panel import PreviewPanel
from pet_cursor.ui.cursor_targets_panel import CursorTargetsPanel
from pet_cursor.ui.presets_panel import PresetsPanel
from pet_cursor.core.bg_remover import BgRemoverWorker
from pet_cursor.core.cur_builder import build_cur
from pet_cursor.core import cursor_applier
from pet_cursor.core.preset_store import PresetStore


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pet Cursor")
        self.resize(820, 760)

        self._store = PresetStore()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        top = QHBoxLayout()
        self.drop_zone = DropZone()
        self.preview = PreviewPanel()
        top.addWidget(self.drop_zone, 1)
        top.addWidget(self.preview, 1)
        root.addLayout(top)

        self.status = QLabel("이미지를 선택해 주세요.")
        self.status.setStyleSheet("padding: 6px;")
        root.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        root.addWidget(self.progress)

        self.targets_panel = CursorTargetsPanel()
        root.addWidget(self.targets_panel)

        self.presets_panel = PresetsPanel(self._store)
        root.addWidget(self.presets_panel)

        btn_row = QHBoxLayout()
        self.apply_btn = QPushButton("커서로 적용")
        self.apply_btn.setEnabled(False)
        self.restore_btn = QPushButton("원본 복원")
        btn_row.addStretch(1)
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(self.restore_btn)
        root.addLayout(btn_row)

        self.drop_zone.file_dropped.connect(self.on_file_selected)
        self.preview.hotspot_changed.connect(self._on_hotspot_changed)
        self.apply_btn.clicked.connect(self.on_apply)
        self.restore_btn.clicked.connect(self.on_restore)
        self.presets_panel.save_requested.connect(self.on_save_preset)
        self.presets_panel.load_requested.connect(self.on_load_preset)
        self.presets_panel.delete_requested.connect(self.on_delete_preset)

        self._worker: BgRemoverWorker | None = None
        self._cur_path: Path | None = None
        self._cursor_applied = False

    def on_file_selected(self, path: str):
        self.drop_zone.show_preview(path)
        self.status.setText("누끼 따는 중... (첫 실행 시 모델 다운로드, ~170MB)")
        self.progress.show()
        self.apply_btn.setEnabled(False)

        self._worker = BgRemoverWorker(path)
        self._worker.finished_ok.connect(self.on_bg_removed)
        self._worker.failed.connect(self.on_bg_failed)
        self._worker.start()

    def on_bg_removed(self, img: Image.Image):
        self.progress.hide()
        self.preview.set_image(img)
        self.apply_btn.setEnabled(True)
        self.status.setText(
            "완료. 미리보기를 클릭해 핫스팟을 조정하거나, 적용할 시스템 커서를 선택하세요."
        )

    def on_bg_failed(self, msg: str):
        self.progress.hide()
        self.status.setText("누끼 실패")
        QMessageBox.critical(self, "누끼 실패", msg)

    def _on_hotspot_changed(self, x: int, y: int):
        if self.preview.source_image():
            self.status.setText(f"핫스팟: ({x}, {y})")

    def on_apply(self):
        img = self.preview.source_image()
        hotspot = self.preview.hotspot()
        targets = self.targets_panel.selected()
        if not img or not hotspot:
            return
        if not targets:
            QMessageBox.information(self, "선택 없음", "적용할 시스템 커서를 하나 이상 선택해 주세요.")
            return
        try:
            tmp = Path(tempfile.gettempdir()) / "pet_cursor.cur"
            build_cur(img, hotspot, tmp)
            cursor_applier.apply_cursor(tmp, targets)
            self._cur_path = tmp
            self._cursor_applied = True
            self.status.setText(f"적용 완료 ✓  ({len(targets)}개 커서, 핫스팟 {hotspot})")
        except Exception as e:
            QMessageBox.critical(self, "적용 실패", f"{type(e).__name__}: {e}")

    def on_restore(self):
        try:
            cursor_applier.restore_cursor()
            self._cursor_applied = False
            self.status.setText("원본 커서로 복원되었습니다 (모든 시스템 커서).")
        except Exception as e:
            QMessageBox.critical(self, "복원 실패", f"{type(e).__name__}: {e}")

    def on_save_preset(self, slot: int):
        img = self.preview.source_image()
        hotspot = self.preview.hotspot()
        targets = self.targets_panel.selected()
        if not img or not hotspot:
            QMessageBox.information(
                self, "저장할 내용 없음", "먼저 이미지를 업로드하고 누끼가 끝난 뒤에 저장할 수 있어요."
            )
            return
        try:
            self._store.save(slot, img, hotspot, targets)
            self.presets_panel.refresh()
            self.status.setText(f"슬롯 {slot + 1}에 저장됨.")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"{type(e).__name__}: {e}")

    def on_load_preset(self, slot: int):
        preset = self._store.load(slot)
        if not preset:
            return
        self.preview.set_image(preset.image, hotspot=preset.hotspot)
        self.targets_panel.set_selected(preset.targets)
        self.apply_btn.setEnabled(True)
        self.status.setText(f"슬롯 {slot + 1} 불러옴 — '커서로 적용'을 누르면 즉시 반영됩니다.")

    def on_delete_preset(self, slot: int):
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"슬롯 {slot + 1}의 프리셋을 삭제할까요?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self._store.delete(slot)
            self.presets_panel.refresh()
            self.status.setText(f"슬롯 {slot + 1} 삭제됨.")
        except Exception as e:
            QMessageBox.critical(self, "삭제 실패", f"{type(e).__name__}: {e}")

    def closeEvent(self, event):
        if self._cursor_applied:
            reply = QMessageBox.question(
                self, "종료 확인",
                "커서가 변경된 상태입니다. 원본으로 복원하고 종료할까요?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.Yes:
                try:
                    cursor_applier.restore_cursor()
                except Exception:
                    pass
        event.accept()
