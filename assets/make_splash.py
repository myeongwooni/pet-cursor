"""Generate splash.png used by PyInstaller bootloader. Run once."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 480, 260
BG = (35, 35, 40)
FG = (235, 235, 240)
SUB = (160, 160, 170)
ACCENT = (255, 140, 90)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)


def load(size: int) -> ImageFont.ImageFont:
    for name in ("segoeuib.ttf", "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


title_font = load(34)
sub_font = load(13)

title = "Pet Cursor"
tb = draw.textbbox((0, 0), title, font=title_font)
tw, th = tb[2] - tb[0], tb[3] - tb[1]
draw.text(((W - tw) // 2, 80), title, fill=FG, font=title_font)

sub = "Loading..."
sb = draw.textbbox((0, 0), sub, font=sub_font)
sw = sb[2] - sb[0]
draw.text(((W - sw) // 2, 140), sub, fill=SUB, font=sub_font)

# accent bar
bar_y = 175
draw.rectangle((W // 2 - 60, bar_y, W // 2 + 60, bar_y + 3), fill=ACCENT)

out = Path(__file__).parent / "splash.png"
img.save(out)
print(f"wrote {out} ({W}x{H})")
