"""Draw the tqk2811 sticker pack (labels such as Subscribe and Like, and frames) and zip it.

    py -I stickers/tqk2811-stickers/generate.py -o dist-stickers

Every image is drawn by this script with Pillow (pip install pillow): rounded boxes, simple icons and
the words in Aileron Regular, the font built into Pillow (ImageFont.load_default, CC0), made bold with
a stroke. Nothing is copied from another project. Shapes are drawn at twice the size and scaled down
for smooth edges. The zip, `tqk2811-stickers.zip`, has `manifest.json` (format 1, type "sticker",
items `{id, file, name, tags, category}`), `LICENSE.txt` and `NOTICE.txt` (stickers/tqk2811-stickers/) and
`images/<id>.png`. With the same Pillow version it is reproducible byte for byte.
"""

import argparse
import io
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    sys.exit("error: Pillow is needed: py -m pip install pillow")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from pack_stickers import FORMAT, write_zip  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = Path(__file__).resolve().parent
VERSION = "1.0.0"
PACK_ID = "tqk2811-stickers"
PACK_NAME = "Stickers: labels and frames"
ZIP_NAME = "tqk2811-stickers.zip"
SS = 2  # supersampling

WHITE = (255, 255, 255, 255)
DARK = (30, 30, 36, 255)


def font(size):
    return ImageFont.load_default(size * SS)


def canvas(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def finish(image):
    w, h = image.size
    return image.resize((w // SS, h // SS), Image.LANCZOS)


def with_shadow(image, offset=(0, 6), blur=8, alpha=110):
    """A soft drop shadow under the opaque parts."""
    a = image.getchannel("A").point(lambda v: v * alpha // 255)
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow.putalpha(a)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur * SS))
    out = Image.new("RGBA", image.size, (0, 0, 0, 0))
    out.alpha_composite(shadow, (offset[0] * SS, offset[1] * SS))
    out.alpha_composite(image)
    return out


def text_width(draw, words, size, stroke):
    box = draw.textbbox((0, 0), words, font=font(size), stroke_width=stroke * SS)
    return box[2] - box[0]


def draw_text(draw, center, words, size, fill, stroke=2):
    draw.text(center, words, font=font(size), fill=fill, anchor="mm", stroke_width=stroke * SS, stroke_fill=fill)


# ---- icons, drawn in a square box (x, y, s) at canvas scale ----

def icon_bell(d, x, y, s, c):
    d.pieslice((x + s * 0.15, y + s * 0.08, x + s * 0.85, y + s * 0.78), 180, 360, fill=c)
    d.rectangle((x + s * 0.15, y + s * 0.42, x + s * 0.85, y + s * 0.72), fill=c)
    d.polygon([(x + s * 0.05, y + s * 0.8), (x + s * 0.15, y + s * 0.66), (x + s * 0.85, y + s * 0.66), (x + s * 0.95, y + s * 0.8)], fill=c)
    d.ellipse((x + s * 0.4, y + s * 0.8, x + s * 0.6, y + s), fill=c)


def heart_points(cx, cy, r, n=120):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        hx = 16 * math.sin(t) ** 3
        hy = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + hx * r / 17, cy - hy * r / 17))
    return pts


def icon_heart(d, x, y, s, c):
    d.polygon(heart_points(x + s / 2, y + s * 0.48, s * 0.5), fill=c)


def icon_share(d, x, y, s, c):
    w = s * 0.1
    d.line([(x + s * 0.12, y + s * 0.9), (x + s * 0.12, y + s * 0.55), (x + s * 0.35, y + s * 0.38), (x + s * 0.62, y + s * 0.38)], fill=c, width=int(w * 1.6), joint="curve")
    d.polygon([(x + s * 0.55, y + s * 0.1), (x + s * 0.95, y + s * 0.38), (x + s * 0.55, y + s * 0.66)], fill=c)


def icon_bubble(d, x, y, s, c):
    d.rounded_rectangle((x + s * 0.05, y + s * 0.1, x + s * 0.95, y + s * 0.72), radius=s * 0.18, fill=c)
    d.polygon([(x + s * 0.25, y + s * 0.65), (x + s * 0.5, y + s * 0.65), (x + s * 0.22, y + s * 0.95)], fill=c)


def icon_plus(d, x, y, s, c):
    w = s * 0.22
    d.rectangle((x + s / 2 - w / 2, y + s * 0.1, x + s / 2 + w / 2, y + s * 0.9), fill=c)
    d.rectangle((x + s * 0.1, y + s / 2 - w / 2, x + s * 0.9, y + s / 2 + w / 2), fill=c)


def icon_check(d, x, y, s, c):
    d.line([(x + s * 0.1, y + s * 0.55), (x + s * 0.4, y + s * 0.82), (x + s * 0.92, y + s * 0.2)], fill=c, width=int(s * 0.18), joint="curve")


def icon_dot(d, x, y, s, c):
    d.ellipse((x + s * 0.2, y + s * 0.2, x + s * 0.8, y + s * 0.8), fill=c)


def icon_flame(d, x, y, s, c):
    # A teardrop with its tip up.
    pts = []
    for i in range(80):
        t = 2 * math.pi * i / 80
        pts.append((x + s / 2 + s * 0.62 * math.sin(t) * math.sin(t / 2), y + s * 0.5 - s * 0.48 * math.cos(t)))
    d.polygon(pts, fill=c)


def icon_pointer(d, x, y, s, c):
    d.polygon([(x + s * 0.15, y + s * 0.05), (x + s * 0.85, y + s * 0.5), (x + s * 0.5, y + s * 0.55), (x + s * 0.35, y + s * 0.95)], fill=c)


def icon_link(d, x, y, s, c):
    w = int(s * 0.13)
    d.rounded_rectangle((x + s * 0.02, y + s * 0.3, x + s * 0.6, y + s * 0.7), radius=s * 0.2, outline=c, width=w)
    d.rounded_rectangle((x + s * 0.4, y + s * 0.3, x + s * 0.98, y + s * 0.7), radius=s * 0.2, outline=c, width=w)


def label(words, bg, fg=WHITE, icon=None, size=64, radius=None, border=None):
    """A pill with an optional icon on the left and the words."""
    probe = ImageDraw.Draw(canvas(1, 1))
    tw = text_width(probe, words, size, 2) // SS
    h = int(size * 1.9)
    icon_w = int(size * 0.95) if icon else 0
    gap = int(size * 0.35) if icon else 0
    pad = int(size * 0.65)
    w = pad * 2 + icon_w + gap + tw
    margin = 24
    image = canvas(w + margin * 2, h + margin * 2)
    d = ImageDraw.Draw(image)
    box = (margin * SS, margin * SS, (margin + w) * SS, (margin + h) * SS)
    d.rounded_rectangle(box, radius=(radius if radius is not None else h // 2) * SS, fill=bg,
                        outline=border, width=6 * SS if border else 0)
    if icon:
        s = icon_w * SS
        icon(d, (margin + pad) * SS, (margin + (h - icon_w) / 2) * SS, s, fg)
    draw_text(d, ((margin + pad + icon_w + gap + tw / 2) * SS, (margin + h / 2 + size * 0.04) * SS), words, size, fg)
    return finish(with_shadow(image))


def burst(words, bg, fg=WHITE, size=96, spikes=16):
    side = 420
    image = canvas(side, side)
    d = ImageDraw.Draw(image)
    c = side * SS / 2
    pts = []
    for i in range(spikes * 2):
        r = (0.47 if i % 2 == 0 else 0.38) * side * SS
        t = math.pi * i / spikes - math.pi / 2
        pts.append((c + r * math.cos(t), c + r * math.sin(t)))
    d.polygon(pts, fill=bg)
    d.polygon([(x * 0.86 + c * 0.14, y * 0.86 + c * 0.14) for x, y in pts], outline=fg, width=4 * SS)
    draw_text(d, (c, c + size * 0.05 * SS), words, size, fg, stroke=3)
    return finish(with_shadow(image.rotate(-12, resample=Image.BICUBIC)))


# ---- frames: transparent inside, so a clip under them shows through ----

def frame_rounded():
    image = canvas(512, 512)
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((16 * SS, 16 * SS, 496 * SS, 496 * SS), radius=56 * SS, outline=WHITE, width=22 * SS)
    return finish(with_shadow(image, (0, 4), 6))


def frame_dashed():
    image = canvas(512, 512)
    d = ImageDraw.Draw(image)
    lo, hi, step, dash = 24 * SS, 488 * SS, 48 * SS, 30 * SS
    w = 12 * SS
    for p in range(lo, hi, step):
        e = min(p + dash, hi)
        d.rectangle((p, lo - w // 2, e, lo + w // 2), fill=WHITE)
        d.rectangle((p, hi - w // 2, e, hi + w // 2), fill=WHITE)
        d.rectangle((lo - w // 2, p, lo + w // 2, e), fill=WHITE)
        d.rectangle((hi - w // 2, p, hi + w // 2, e), fill=WHITE)
    return finish(with_shadow(image, (0, 3), 4))


def frame_corners():
    image = canvas(512, 512)
    d = ImageDraw.Draw(image)
    a, b, arm, w = 24 * SS, 488 * SS, 110 * SS, 18 * SS
    for x, sx in ((a, 1), (b, -1)):
        for y, sy in ((a, 1), (b, -1)):
            d.line([(x, y + sy * arm), (x, y), (x + sx * arm, y)], fill=WHITE, width=w, joint="curve")
    return finish(with_shadow(image, (0, 3), 4))


def frame_circle():
    image = canvas(512, 512)
    d = ImageDraw.Draw(image)
    d.ellipse((18 * SS, 18 * SS, 494 * SS, 494 * SS), outline=WHITE, width=24 * SS)
    d.ellipse((50 * SS, 50 * SS, 462 * SS, 462 * SS), outline=(255, 255, 255, 140), width=4 * SS)
    return finish(with_shadow(image, (0, 4), 6))


def frame_polaroid():
    w, h = 460, 540
    image = canvas(w, h)
    d = ImageDraw.Draw(image)
    d.rectangle((10 * SS, 10 * SS, (w - 10) * SS, (h - 10) * SS), fill=(250, 250, 246, 255))
    d.rectangle((38 * SS, 38 * SS, (w - 38) * SS, (h - 120) * SS), fill=(0, 0, 0, 0))
    return finish(with_shadow(image, (0, 6), 10).rotate(-4, resample=Image.BICUBIC, expand=True))


def frame_film():
    w, h = 640, 440
    image = canvas(w, h)
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, w * SS, h * SS), fill=(20, 20, 22, 255))
    d.rectangle((24 * SS, 70 * SS, (w - 24) * SS, (h - 70) * SS), fill=(0, 0, 0, 0))
    for x in range(30, w - 20, 52):
        for y in (22, h - 52):
            d.rounded_rectangle((x * SS, y * SS, (x + 30) * SS, (y + 30) * SS), radius=6 * SS, fill=(0, 0, 0, 0))
    return finish(image)


def speech_bubble():
    w, h = 560, 440
    image = canvas(w, h)
    d = ImageDraw.Draw(image)
    o = 10 * SS
    d.ellipse((20 * SS, 20 * SS, (w - 20) * SS, 340 * SS), fill=DARK)
    d.polygon([(120 * SS, 270 * SS), (230 * SS, 300 * SS), (70 * SS, 420 * SS)], fill=DARK)
    d.ellipse((20 * SS + o, 20 * SS + o, (w - 20) * SS - o, 340 * SS - o), fill=WHITE)
    d.polygon([(128 * SS, 262 * SS), (218 * SS, 288 * SS), (90 * SS, 392 * SS)], fill=WHITE)
    return finish(with_shadow(image, (0, 5), 8))


def thought_bubble():
    w, h = 560, 500
    image = canvas(w, h)
    d = ImageDraw.Draw(image)
    o = 10
    puffs = [(150, 170, 105), (280, 140, 120), (410, 175, 105), (440, 270, 90), (320, 310, 110), (180, 300, 100), (110, 240, 85)]
    for grow, color in ((o, DARK), (0, WHITE)):
        for x, y, r in puffs:
            d.ellipse(((x - r - grow) * SS, (y - r - grow) * SS, (x + r + grow) * SS, (y + r + grow) * SS), fill=color)
        for x, y, r in ((120, 415, 30), (75, 465, 18)):
            d.ellipse(((x - r - grow) * SS, (y - r - grow) * SS, (x + r + grow) * SS, (y + r + grow) * SS), fill=color)
    return finish(with_shadow(image, (0, 5), 8))


RED = (229, 45, 39, 255)
STICKERS = [
    # id, name, category, tags, draw
    ("subscribe", "Subscribe", "Labels", ["subscribe", "button", "bell"], lambda: label("SUBSCRIBE", RED, icon=icon_bell)),
    ("subscribed", "Subscribed", "Labels", ["subscribed", "button", "check"], lambda: label("SUBSCRIBED", (96, 96, 104, 255), icon=icon_check)),
    ("like", "Like", "Labels", ["like", "heart", "button"], lambda: label("LIKE", (33, 120, 243, 255), icon=icon_heart)),
    ("share", "Share", "Labels", ["share", "button", "arrow"], lambda: label("SHARE", (46, 160, 67, 255), icon=icon_share)),
    ("comment", "Comment", "Labels", ["comment", "button", "speech"], lambda: label("COMMENT", (124, 77, 255, 255), icon=icon_bubble)),
    ("follow", "Follow", "Labels", ["follow", "button", "plus"], lambda: label("FOLLOW", (255, 45, 120, 255), icon=icon_plus)),
    ("live", "Live", "Labels", ["live", "stream", "badge"], lambda: label("LIVE", RED, icon=icon_dot, radius=18)),
    ("hot", "Hot", "Labels", ["hot", "fire", "badge"], lambda: label("HOT", (255, 120, 0, 255), icon=icon_flame)),
    ("click-here", "Click here", "Labels", ["click here", "pointer", "button"], lambda: label("CLICK HERE", (255, 210, 0, 255), DARK, icon=icon_pointer)),
    ("link-in-bio", "Link in bio", "Labels", ["link in bio", "link", "badge"], lambda: label("LINK IN BIO", WHITE, DARK, icon=icon_link, border=DARK)),
    ("new", "New", "Labels", ["new", "badge", "burst"], lambda: burst("NEW", (255, 200, 0, 255), DARK)),
    ("sale", "Sale", "Labels", ["sale", "badge", "burst"], lambda: burst("SALE", RED)),
    ("frame-rounded", "Rounded frame", "Frames", ["frame", "border", "rounded"], frame_rounded),
    ("frame-dashed", "Dashed frame", "Frames", ["frame", "border", "dashed"], frame_dashed),
    ("frame-corners", "Corner frame", "Frames", ["frame", "corners", "viewfinder"], frame_corners),
    ("frame-circle", "Circle frame", "Frames", ["frame", "circle", "ring"], frame_circle),
    ("frame-polaroid", "Photo frame", "Frames", ["frame", "photo", "polaroid"], frame_polaroid),
    ("frame-film", "Film frame", "Frames", ["frame", "film", "strip"], frame_film),
    ("speech-bubble", "Speech bubble", "Frames", ["speech", "bubble", "talk"], speech_bubble),
    ("thought-bubble", "Thought bubble", "Frames", ["thought", "bubble", "cloud"], thought_bubble),
]


def png_bytes(image):
    out = io.BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", type=Path, required=True, help="output directory")
    parser.add_argument("--images", type=Path, help="also write the PNG files here, to look at them")
    args = parser.parse_args()

    items = []
    for sticker_id, name, category, tags, draw in STICKERS:
        data = png_bytes(draw())
        items.append(({"id": sticker_id, "file": f"images/{sticker_id}.png", "name": name, "tags": tags, "category": category}, data))
        if args.images:
            args.images.mkdir(parents=True, exist_ok=True)
            (args.images / f"{sticker_id}.png").write_bytes(data)
    manifest = {
        "format": FORMAT,
        "type": "sticker",
        "id": PACK_ID,
        "name": PACK_NAME,
        "version": VERSION,
        "license": {"spdx": "MIT", "files": ["LICENSE.txt", "NOTICE.txt"]},
        "items": [item for item, _ in items],
    }
    read = lambda name: (SOURCE_DIR / name).read_text(encoding="utf-8")
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / ZIP_NAME
    write_zip(target, manifest, items, read("LICENSE.txt"), read("NOTICE.txt"))
    print(f"{ZIP_NAME}\t{len(items)} items\t{target.stat().st_size} bytes")


if __name__ == "__main__":
    main()
