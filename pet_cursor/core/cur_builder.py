from __future__ import annotations

import struct
from pathlib import Path
from PIL import Image

CURSOR_SIZES = [32, 48, 64, 96, 128]


def _build_dib_frame(img: Image.Image) -> bytes:
    img = img.convert("RGBA")
    w, h = img.size

    # DIB is bottom-up — flip vertically before extracting raw bytes.
    flipped = img.transpose(Image.FLIP_TOP_BOTTOM)
    r, g, b, a = flipped.split()
    bgra = Image.merge("RGBA", (b, g, r, a)).tobytes()

    alpha_bytes = a.tobytes()
    mask_row_bytes = ((w + 31) // 32) * 4
    mask = bytearray(mask_row_bytes * h)
    for y in range(h):
        base_pix = y * w
        base_mask = y * mask_row_bytes
        for x in range(w):
            if alpha_bytes[base_pix + x] == 0:
                mask[base_mask + (x // 8)] |= 1 << (7 - (x % 8))

    header = struct.pack(
        "<IiiHHIIiiII",
        40,        # biSize
        w,         # biWidth
        h * 2,     # biHeight (doubled to include AND mask)
        1,         # biPlanes
        32,        # biBitCount
        0,         # biCompression (BI_RGB)
        0, 0, 0, 0, 0,
    )
    return header + bgra + bytes(mask)


def _fit_to_canvas(image: Image.Image, size: int) -> tuple[Image.Image, float, int, int]:
    src_w, src_h = image.size
    scale = size / max(src_w, src_h)
    new_w = max(1, int(round(src_w * scale)))
    new_h = max(1, int(round(src_h * scale)))
    resized = image.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox = (size - new_w) // 2
    oy = (size - new_h) // 2
    canvas.paste(resized, (ox, oy))
    return canvas, scale, ox, oy


def build_cur(image: Image.Image, hotspot: tuple[int, int], output: Path) -> None:
    """Write a multi-resolution Windows cursor (.cur) from a PIL RGBA image.

    hotspot is (x, y) in source image coordinates.
    """
    entries: list[tuple[int, int, int, bytes]] = []

    for size in CURSOR_SIZES:
        canvas, scale, ox, oy = _fit_to_canvas(image, size)
        hs_x = max(0, min(size - 1, int(round(hotspot[0] * scale)) + ox))
        hs_y = max(0, min(size - 1, int(round(hotspot[1] * scale)) + oy))
        entries.append((size, hs_x, hs_y, _build_dib_frame(canvas)))

    count = len(entries)
    file_header = struct.pack("<HHH", 0, 2, count)  # type=2 → cursor

    dir_size = 6 + 16 * count
    data_offset = dir_size
    dir_entries = bytearray()
    blob = bytearray()

    for size, hs_x, hs_y, dib in entries:
        size_byte = size if size < 256 else 0
        dir_entries += struct.pack(
            "<BBBBHHII",
            size_byte,
            size_byte,
            0, 0,
            hs_x, hs_y,
            len(dib),
            data_offset,
        )
        blob += dib
        data_offset += len(dib)

    output.write_bytes(file_header + bytes(dir_entries) + bytes(blob))
