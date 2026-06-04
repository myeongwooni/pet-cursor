from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

MAX_SLOTS = 5


@dataclass
class Preset:
    slot: int
    image: Image.Image
    hotspot: tuple[int, int]
    targets: list[int]


class PresetStore:
    """Filesystem-backed preset storage under %LOCALAPPDATA%\\PetCursor\\presets."""

    def __init__(self) -> None:
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        self.root = Path(base) / "PetCursor" / "presets"
        self.root.mkdir(parents=True, exist_ok=True)

    def slot_dir(self, slot: int) -> Path:
        return self.root / f"slot_{slot}"

    def exists(self, slot: int) -> bool:
        d = self.slot_dir(slot)
        return (d / "image.png").exists() and (d / "meta.json").exists()

    def load(self, slot: int) -> Preset | None:
        if not self.exists(slot):
            return None
        d = self.slot_dir(slot)
        img = Image.open(d / "image.png").convert("RGBA")
        img.load()  # detach from file handle
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        return Preset(
            slot=slot,
            image=img,
            hotspot=(int(meta["hotspot"][0]), int(meta["hotspot"][1])),
            targets=[int(x) for x in meta["targets"]],
        )

    def save(
        self,
        slot: int,
        image: Image.Image,
        hotspot: tuple[int, int],
        targets: list[int],
    ) -> None:
        if not (0 <= slot < MAX_SLOTS):
            raise ValueError(f"slot {slot} out of range")
        d = self.slot_dir(slot)
        d.mkdir(parents=True, exist_ok=True)
        rgba = image if image.mode == "RGBA" else image.convert("RGBA")
        rgba.save(d / "image.png", format="PNG")
        meta = {"hotspot": [int(hotspot[0]), int(hotspot[1])], "targets": list(targets)}
        (d / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def delete(self, slot: int) -> None:
        d = self.slot_dir(slot)
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    def first_empty(self) -> int | None:
        for i in range(MAX_SLOTS):
            if not self.exists(i):
                return i
        return None
