import struct
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from pet_cursor.core.cur_builder import CURSOR_SIZES, build_cur


class CursorBuilderTests(unittest.TestCase):
    def test_frames_and_hotspots_are_valid(self):
        image = Image.new('RGBA', (200, 100), (255, 0, 0, 255))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'cursor.cur'
            build_cur(image, (100, 50), output)
            data = output.read_bytes()
        self.assertEqual(struct.unpack_from('<HHH', data), (0, 2, len(CURSOR_SIZES)))
        previous_end = 6 + 16 * len(CURSOR_SIZES)
        for i, size in enumerate(CURSOR_SIZES):
            w, h, _, _, x, y, length, offset = struct.unpack_from('<BBBBHHII', data, 6 + i * 16)
            self.assertEqual((w, h), (size, size))
            self.assertEqual((x, y), (size // 2, size // 2))
            self.assertEqual(offset, previous_end)
            self.assertEqual(struct.unpack_from('<IiiHH', data, offset), (40, size, size * 2, 1, 32))
            previous_end = offset + length
        self.assertEqual(previous_end, len(data))


if __name__ == '__main__':
    unittest.main()
