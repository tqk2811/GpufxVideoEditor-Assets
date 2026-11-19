"""Draw the tqk2811 animated sticker pack (animated WebP) and zip it.

    py -I stickers/tqk2811-animated-stickers/generate.py -o dist-stickers [--images <folder>]

Every frame is drawn by this script with Pillow (pip install pillow): simple shapes, icons and words in
Aileron Regular, the font built into Pillow (ImageFont.load_default, CC0), made bold with a stroke.
Nothing is copied from another project. Shapes are drawn at twice the size and scaled down for smooth
edges. Each sticker is 512x512 with a transparent background, 20 frames a second, and loops: the frame
after the last one is the first one again. The frames are stored as a lossy animated WebP (quality 70, alpha 70) with
loop 0 (forever); the editor loops it over the length of the clip.

The zip, `tqk2811-animated-stickers.zip`, has `manifest.json` (format 1, type "sticker", items
`{id, file, name, tags, category}`), `LICENSE.txt` and `NOTICE.txt` (stickers/tqk2811-animated-stickers/)
and `images/<id>.webp`. With the same Pillow and libwebp it is reproducible byte for byte.
--images also writes the WebP files to a folder, to look at them.
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
PACK_ID = "tqk2811-animated-stickers"
PACK_NAME = "Stickers: animated labels and marks"
ZIP_NAME = "tqk2811-animated-stickers.zip"
SIZE = 512
SS = 2  # supersampling
C = SIZE * SS // 2  # centre of the canvas, at canvas scale
FPS = 20
QUALITY = 70  # lossy WebP: lossless frames of turned, anti-aliased shapes were 1-2 MB each
ALPHA_QUALITY = 70

WHITE = (255, 255, 255, 255)
DARK = (30, 30, 36, 255)
RED = (230, 33, 23, 255)
BLUE = (24, 119, 242, 255)
YELLOW = (255, 196, 0, 255)
ORANGE = (255, 120, 20, 255)
PINK = (240, 50, 90, 255)
GREEN = (30, 170, 90, 255)
PURPLE = (130, 70, 220, 255)
GOLD = (255, 205, 40, 255)


def u(v):
    """512-pixel units to canvas pixels."""
    return v * SS


def font(size):
    return ImageFont.load_default(u(size))


def canvas():
    return Image.new("RGBA", (u(SIZE), u(SIZE)), (0, 0, 0, 0))


def finish(image):
    return image.resize((SIZE, SIZE), Image.LANCZOS)


def with_shadow(image, offset=(0, 6), blur=7, alpha=100):
    a = image.getchannel("A").point(lambda v: v * alpha // 255)
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow.putalpha(a)
    shadow = shadow.filter(ImageFilter.GaussianBlur(u(blur)))
    out = Image.new("RGBA", image.size, (0, 0, 0, 0))
    out.alpha_composite(shadow, (u(offset[0]), u(offset[1])))
    out.alpha_composite(image)
    return out


def place(layer, scale=1.0, angle=0.0, dx=0.0, dy=0.0, pivot=None):
    """The layer scaled and turned (degrees, counter-clockwise) about pivot (canvas pixels), then moved."""
    px, py = pivot if pivot else (C, C)
    if scale <= 0.01:
        return canvas()
    a = math.radians(angle)
    cos, sin = math.cos(a) / scale, math.sin(a) / scale
    tx, ty = px + u(dx), py + u(dy)
    # inverse map: output (x, y) -> input
    coeffs = (cos, -sin, px - cos * tx + sin * ty, sin, cos, py - sin * tx - cos * ty)
    return layer.transform(layer.size, Image.AFFINE, coeffs, resample=Image.BICUBIC)


def fade(image, alpha):
    if alpha >= 1:
        return image
    out = image.copy()
    out.putalpha(image.getchannel("A").point(lambda v: int(v * max(alpha, 0) + 0.5)))
    return out


def layers(*images):
    out = canvas()
    for image in images:
        out.alpha_composite(image)
    return out


# ---- easing ----

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def seg(t, a, b):
    """0 before a, 1 after b, linear between."""
    return clamp((t - a) / (b - a))


def smooth(v):
    return v * v * (3 - 2 * v)


def ease_out_back(v, k=2.2):
    v -= 1
    return 1 + (k + 1) * v ** 3 + k * v ** 2


def elastic(v):
    """0 -> 1 with a damped wobble."""
    if v <= 0:
        return 0.0
    if v >= 1:
        return 1.0
    return 1 - math.exp(-6 * v) * math.cos(v * math.pi * 4.5)


def wave(t, cycles=1.0):
    return math.sin(t * math.tau * cycles)


# ---- drawing helpers (canvas pixels) ----

def text(d, xy, words, size, fill, stroke=2, stroke_fill=None, anchor="mm"):
    d.text(xy, words, font=font(size), fill=fill, anchor=anchor, stroke_width=u(stroke),
           stroke_fill=stroke_fill or fill)


def text_size(words, size, stroke=2):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    box = d.textbbox((0, 0), words, font=font(size), stroke_width=u(stroke))
    return box[2] - box[0], box[3] - box[1]


def pill(words, bg, fg=WHITE, size=64, pad=(44, 26), border=None, icon=None):
    """A rounded label in the middle of a canvas."""
    image = canvas()
    d = ImageDraw.Draw(image)
    tw, th = text_size(words, size)
    iw = u(size) * 1.1 if icon else 0
    w = tw + iw + u(pad[0]) * 2
    h = max(th, u(size)) + u(pad[1]) * 2
    box = (C - w / 2, C - h / 2, C + w / 2, C + h / 2)
    if border:
        grow = u(8)
        d.rounded_rectangle((box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow), radius=h / 2 + grow, fill=border)
    d.rounded_rectangle(box, radius=h / 2, fill=bg)
    x = box[0] + u(pad[0])
    if icon:
        s = u(size) * 0.9
        icon(d, x, C - s / 2, s, fg)
        x += iw
    text(d, (x + tw / 2, C + u(2)), words, size, fg)
    return with_shadow(image)


def star_points(cx, cy, r_out, r_in, n=5, turn=-90):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(turn + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def heart_points(cx, cy, r, n=160):
    pts = []
    for i in range(n):
        a = i / n * math.tau
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((cx + x * r / 16, cy - y * r / 16))
    return pts


def thick_path(d, pts, width, fill):
    """A polyline with round joints and ends."""
    d.line(pts, fill=fill, width=int(width), joint="curve")
    r = width / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def icon_thumb(d, x, y, s, c):
    d.rounded_rectangle((x, y + s * 0.42, x + s * 0.24, y + s), radius=s * 0.05, fill=c)
    d.rounded_rectangle((x + s * 0.3, y + s * 0.4, x + s * 0.95, y + s), radius=s * 0.12, fill=c)
    d.polygon([(x + s * 0.3, y + s * 0.5), (x + s * 0.48, y + s * 0.05), (x + s * 0.62, y + s * 0.08),
               (x + s * 0.62, y + s * 0.42), (x + s * 0.3, y + s * 0.6)], fill=c)
    d.ellipse((x + s * 0.44, y, x + s * 0.64, y + s * 0.2), fill=c)


def icon_play(d, x, y, s, c):
    d.polygon([(x + s * 0.2, y + s * 0.1), (x + s * 0.2, y + s * 0.9), (x + s * 0.9, y + s * 0.5)], fill=c)


def cursor_layer(pressed=False):
    """A mouse arrow with its tip at the centre of the canvas."""
    image = canvas()
    d = ImageDraw.Draw(image)
    k = u(1) * (0.9 if pressed else 1.0)
    pts = [(0, 0), (0, 92), (24, 70), (40, 106), (56, 99), (40, 64), (72, 64)]
    pts = [(C + x * k, C + y * k) for x, y in pts]
    d.polygon(pts, fill=WHITE, outline=DARK, width=u(6))
    d.line(pts + [pts[0]], fill=DARK, width=u(6), joint="curve")
    return with_shadow(image, offset=(3, 5), blur=4)


def hand_layer():
    """A pointing hand, the finger to the right, the fingertip at the centre of the canvas."""
    image = canvas()
    d = ImageDraw.Draw(image)
    skin, line = (255, 206, 120, 255), (150, 90, 30, 255)
    ox, oy = C - u(300), C - u(40)

    def box(x0, y0, x1, y1, r):
        d.rounded_rectangle((ox + u(x0), oy + u(y0), ox + u(x1), oy + u(y1)), radius=u(r), fill=skin,
                            outline=line, width=u(6))

    d.rounded_rectangle((ox + u(-24), oy + u(-10), ox + u(46), oy + u(150)), radius=u(14), fill=(60, 120, 220, 255),
                        outline=(30, 60, 130, 255), width=u(6))
    box(30, -6, 170, 150, 40)  # palm
    for i in range(3):  # folded fingers
        box(120, 46 + i * 34, 196, 84 + i * 34, 18)
    box(120, 0, 300, 44, 22)  # index finger
    box(70, -30, 150, 14, 20)  # thumb
    return with_shadow(image, offset=(3, 6), blur=5)


# ---- stickers: each is fn(t) with t in [0, 1) ----

def subscribe_click():
    base = pill("SUBSCRIBE", RED, size=50, icon=icon_play)
    done = pill("SUBSCRIBED", (110, 110, 118, 255), size=50, icon=icon_play)
    up, down = cursor_layer(), cursor_layer(True)

    def frame(t):
        clicked = 0.42 <= t < 0.9
        pulse = 1 + 0.05 * wave(t, 4) if not clicked else 1.0
        press = 1 - 0.08 * math.sin(math.pi * seg(t, 0.38, 0.48))
        button = place(done if clicked else base, pulse * press)
        out = layers(button)
        if 0.42 <= t < 0.62:  # ripple
            v = seg(t, 0.42, 0.62)
            r = u(40 + 120 * v)
            ring = canvas()
            ImageDraw.Draw(ring).ellipse((C + u(70) - r, C + u(10) - r, C + u(70) + r, C + u(10) + r),
                                         outline=(255, 255, 255, int(230 * (1 - v))), width=u(8))
            out.alpha_composite(ring)
        # cursor: in from the bottom right, click, out again
        come, go = smooth(seg(t, 0.05, 0.38)), smooth(seg(t, 0.62, 0.95))
        x = 70 + (1 - come) * 170 + go * 170
        y = 10 + (1 - come) * 180 + go * 180
        out.alpha_composite(place(down if 0.38 <= t < 0.5 else up, dx=x, dy=y))
        return out
    return frame, 2.0


def bell_ring():
    image = canvas()
    d = ImageDraw.Draw(image)
    s = u(260)
    x, y = C - s / 2, C - s / 2 - u(10)
    d.ellipse((C - u(22), y - u(24), C + u(22), y + u(20)), fill=GOLD, outline=(190, 130, 0, 255), width=u(5))
    d.pieslice((x + s * 0.15, y + s * 0.05, x + s * 0.85, y + s * 0.75), 180, 360, fill=GOLD)
    d.rectangle((x + s * 0.15, y + s * 0.39, x + s * 0.85, y + s * 0.72), fill=GOLD)
    d.polygon([(x + s * 0.02, y + s * 0.86), (x + s * 0.15, y + s * 0.66), (x + s * 0.85, y + s * 0.66),
               (x + s * 0.98, y + s * 0.86)], fill=GOLD)
    d.rounded_rectangle((x, y + s * 0.8, x + s, y + s * 0.9), radius=u(10), fill=(240, 170, 0, 255))
    d.arc((x + s * 0.27, y + s * 0.16, x + s * 0.5, y + s * 0.5), 190, 260, fill=(255, 240, 170, 255), width=u(12))
    clapper = canvas()
    ImageDraw.Draw(clapper).ellipse((C - u(26), y + s * 0.88, C + u(26), y + s * 0.88 + u(52)), fill=(200, 130, 0, 255))
    body = with_shadow(image)
    pivot = (C, y - u(10))

    def frame(t):
        ring = seg(t, 0, 0.7)
        amp = 22 * (1 - ring) * math.sin(ring * math.pi) * 1.6
        angle = amp * math.sin(ring * math.tau * 4)
        out = layers(place(clapper, angle=angle * 1.6, pivot=pivot), place(body, angle=angle, pivot=pivot))
        if 0.05 < t < 0.7:
            d2 = ImageDraw.Draw(out)
            a = int(255 * math.sin(math.pi * seg(t, 0.05, 0.7)))
            for side in (-1, 1):
                for i, r in enumerate((150, 190)):
                    cx = C
                    box = (cx - u(r), C - u(r) - u(10), cx + u(r), C + u(r) - u(10))
                    start = -25 if side > 0 else 155
                    d2.arc(box, start, start + 50, fill=(255, 170, 0, a), width=u(10 - i * 2))
        return out
    return frame, 1.5


def heart_beat():
    image = canvas()
    d = ImageDraw.Draw(image)
    d.polygon(heart_points(C, C, u(170)), fill=PINK)
    d.ellipse((C - u(120), C - u(110), C - u(60), C - u(60)), fill=(255, 150, 175, 255))
    heart = with_shadow(image)

    def frame(t):
        b1 = math.exp(-((t - 0.15) / 0.06) ** 2)
        b2 = math.exp(-((t - 0.38) / 0.07) ** 2)
        b1 += math.exp(-((t - 1.15) / 0.06) ** 2)
        return place(heart, 0.88 + 0.2 * b1 + 0.14 * b2)
    return frame, 1.2


def like_pop():
    image = canvas()
    d = ImageDraw.Draw(image)
    r = u(150)
    d.ellipse((C - r, C - r, C + r, C + r), fill=BLUE)
    s = u(170)
    icon_thumb(d, C - s / 2, C - s / 2 - u(6), s, WHITE)
    badge = with_shadow(image)

    def frame(t):
        v = seg(t, 0, 0.45)
        scale = 1 + 0.3 * math.sin(math.pi * seg(t, 0, 0.18)) - 0.08 * math.sin(math.pi * seg(t, 0.18, 0.4))
        angle = -14 * math.sin(math.pi * seg(t, 0, 0.3))
        out = layers(place(badge, scale, angle))
        if 0.08 < t < 0.5:
            d2 = ImageDraw.Draw(out)
            w = seg(t, 0.08, 0.5)
            a = int(255 * (1 - w))
            for i in range(10):
                ang = math.radians(i * 36 + 18)
                r0, r1 = u(175 + 60 * w), u(195 + 80 * w)
                d2.line((C + r0 * math.cos(ang), C + r0 * math.sin(ang), C + r1 * math.cos(ang), C + r1 * math.sin(ang)),
                        fill=(BLUE[:3] if i % 2 else YELLOW[:3]) + (a,), width=u(12))
        del v
        return out
    return frame, 1.5


def arrow_run(direction):
    angle = {"right": 0, "up": 90, "left": 180, "down": 270}[direction]

    def frame(t):
        image = canvas()
        d = ImageDraw.Draw(image)
        # three chevrons flowing to the right, each fading in on the left and out on the right
        for i in range(3):
            p = (t + i / 3) % 1
            x = C + u(-180 + 300 * p)
            a = math.sin(math.pi * p)
            w = u(70)
            col = (255, 90 + int(60 * a), 20, int(255 * a))
            pts = [(x - w, C - u(110)), (x + w * 0.6, C), (x - w, C + u(110))]
            d.line(pts, fill=col, width=u(46), joint="curve")
            for px, py in (pts[0], pts[2]):
                d.ellipse((px - u(23), py - u(23), px + u(23), py + u(23)), fill=col)
        return place(with_shadow(image, alpha=80), angle=angle)
    return frame, 1.0


def circle_draw():
    pts = []
    n = 120
    for i in range(n + 14):  # a little more than one turn, like a hand-drawn ring
        a = math.radians(-200 + i * 360 / n)
        wob = 1 + 0.03 * math.sin(i / n * math.tau * 2)
        pts.append((C + u(200) * wob * math.cos(a), C + u(150) * wob * math.sin(a) + u(i * 0.12)))

    def frame(t):
        image = canvas()
        d = ImageDraw.Draw(image)
        v = smooth(seg(t, 0.05, 0.55))
        k = max(2, int(len(pts) * v))
        if v > 0:
            thick_path(d, pts[:k], u(18), RED)
        return fade(with_shadow(image, alpha=60), 1 - seg(t, 0.85, 0.98))
    return frame, 2.0


def underline_draw():
    pts = [(C + u(-200 + 4 * i), C + u(20) + u(14) * math.sin(i / 100 * math.tau * 1.5) - u(i * 0.2)) for i in range(101)]
    pts2 = [(C + u(-150 + 3.3 * i), C + u(70) + u(8) * math.sin(i / 100 * math.tau + 1)) for i in range(101)]

    def frame(t):
        image = canvas()
        d = ImageDraw.Draw(image)
        v1, v2 = smooth(seg(t, 0.05, 0.4)), smooth(seg(t, 0.35, 0.6))
        if v1 > 0:
            thick_path(d, pts[:max(2, int(101 * v1))], u(20), YELLOW)
        if v2 > 0:
            thick_path(d, pts2[:max(2, int(101 * v2))], u(14), YELLOW)
        return fade(with_shadow(image, alpha=70), 1 - seg(t, 0.85, 0.98))
    return frame, 2.0


def sparkle_stars():
    spots = [(0, 0, 150, 0.0, GOLD), (-150, -120, 70, 0.33, YELLOW), (150, -90, 85, 0.6, (255, 240, 140, 255)),
             (-130, 130, 75, 0.8, YELLOW)]

    def frame(t):
        image = canvas()
        d = ImageDraw.Draw(image)
        for x, y, r, phase, col in spots:
            p = (t + phase) % 1
            s = 0.25 + 0.75 * math.sin(math.pi * p) ** 2
            rr = u(r) * s
            cx, cy = C + u(x), C + u(y)
            d.polygon(star_points(cx, cy, rr, rr * 0.22, n=4, turn=-90 + 45 * p), fill=col)
            d.ellipse((cx - rr * 0.18, cy - rr * 0.18, cx + rr * 0.18, cy + rr * 0.18), fill=WHITE)
        return with_shadow(image, alpha=60, blur=5)
    return frame, 1.5


def firework():
    bursts = [(-60, -50, 0.0, (255, 80, 80)), (90, 40, 0.5, (90, 200, 255)), (-40, 110, 0.25, (255, 210, 60))]

    def frame(t):
        image = canvas()
        d = ImageDraw.Draw(image)
        for x, y, phase, col in bursts:
            p = (t + phase) % 1
            if p > 0.75:
                continue
            v = p / 0.75
            spread = 1 - (1 - v) ** 3
            a = int(255 * (1 - v ** 2))
            cx, cy = C + u(x), C + u(y)
            for i in range(14):
                ang = math.radians(i * 360 / 14 + phase * 90)
                r1 = u(150) * spread
                r0 = max(0, r1 - u(46) * (1 - v))
                drop = u(30) * v * v
                p0 = (cx + r0 * math.cos(ang), cy + r0 * math.sin(ang) + drop)
                p1 = (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang) + drop)
                d.line((p0, p1), fill=col + (a,), width=u(10))
                d.ellipse((p1[0] - u(9), p1[1] - u(9), p1[0] + u(9), p1[1] + u(9)), fill=(255, 255, 230, a))
        return image
    return frame, 1.6


def mark_bounce(glyph, color):
    image = canvas()
    d = ImageDraw.Draw(image)
    text(d, (C, C), glyph, 330, color, stroke=12, stroke_fill=WHITE)
    text(d, (C, C), glyph, 330, color, stroke=4)
    mark = with_shadow(image)
    foot = (C, C + u(170))

    def frame(t):
        h = abs(math.sin(math.pi * t))  # one hop a loop
        squash = math.exp(-(min(t, 1 - t) / 0.06) ** 2)
        sx, sy = 1 + 0.18 * squash, 1 - 0.18 * squash
        img = mark.transform(mark.size, Image.AFFINE,
                             (1 / sx, 0, foot[0] - foot[0] / sx, 0, 1 / sy, foot[1] - foot[1] / sy),
                             resample=Image.BICUBIC)
        return place(img, dy=-110 * h + 50, angle=8 * wave(t))
    return frame, 1.0


def bubble(words, color):
    image = canvas()
    d = ImageDraw.Draw(image)
    w, h = u(390), u(250)
    box = (C - w / 2, C - h / 2 - u(30), C + w / 2, C + h / 2 - u(30))
    tail = [(C - u(110), box[3] - u(10)), (C - u(160), box[3] + u(90)), (C - u(20), box[3] - u(10))]
    for grow, col in ((u(12), DARK), (0, WHITE)):
        d.ellipse((box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow), fill=col)
        d.polygon([(x + (grow if i == 1 else 0) * -0.5, y + grow) for i, (x, y) in enumerate(tail)], fill=col)
    text(d, (C, box[1] + h / 2 + u(4)), words, 110, color, stroke=5, stroke_fill=DARK)
    layer = with_shadow(image)
    pivot = (C - u(150), C + u(170))

    def frame(t):
        v = seg(t, 0, 0.35)
        scale = elastic(v) if t < 0.35 else 1.0
        scale *= 1 - smooth(seg(t, 0.88, 1.0))
        angle = 0.0
        return place(layer, scale, angle, pivot=pivot)
    return frame, 2.0


def countdown():
    digits = {}
    for n in (3, 2, 1):
        image = canvas()
        text(ImageDraw.Draw(image), (C, C + u(6)), str(n), 260, WHITE, stroke=6)
        digits[n] = image
    colors = {3: (230, 60, 60, 255), 2: (240, 150, 20, 255), 1: (40, 170, 80, 255)}

    def frame(t):
        n = 3 - min(2, int(t * 3))
        v = t * 3 % 1
        image = canvas()
        d = ImageDraw.Draw(image)
        r = u(190)
        d.ellipse((C - r, C - r, C + r, C + r), fill=(40, 40, 48, 235))
        d.arc((C - r + u(14), C - r + u(14), C + r - u(14), C + r - u(14)), -90, -90 + 360 * (1 - v) + 0.01,
              fill=colors[n], width=u(22))
        image.alpha_composite(place(digits[n], 1 + 0.25 * (1 - ease_out_back(seg(v, 0, 0.25))) if v < 0.25 else 1.0))
        return with_shadow(image)
    return frame, 3.0


def spinner():
    def frame(t):
        image = canvas()
        d = ImageDraw.Draw(image)
        n = 10
        for i in range(n):
            ang = math.tau * i / n - math.pi / 2
            age = (t * n - i) % n / n  # 0 = the lead dot
            a = 1 - age
            r = u(18 + 16 * a)
            x, y = C + u(150) * math.cos(ang), C + u(150) * math.sin(ang)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(BLUE[0], BLUE[1], BLUE[2], int(60 + 195 * a)))
        return with_shadow(image, alpha=60)
    return frame, 1.0


def live_blink():
    def make(dot):
        image = canvas()
        d = ImageDraw.Draw(image)
        w, h = u(330), u(140)
        d.rounded_rectangle((C - w / 2, C - h / 2, C + w / 2, C + h / 2), radius=u(22), fill=RED)
        r = u(24)
        cx = C - w / 2 + u(58)
        if dot:
            d.ellipse((cx - r, C - r, cx + r, C + r), fill=WHITE)
        text(d, (C + u(36), C + u(3)), "LIVE", 84, WHITE, stroke=3)
        return with_shadow(image)
    on, off = make(True), make(False)

    def frame(t):
        v = t * 2 % 1
        return place(on if v < 0.55 else off, 1 + 0.04 * math.sin(math.pi * v))
    return frame, 1.0


def label_shake(words, bg, spikes):
    image = canvas()
    d = ImageDraw.Draw(image)
    d.polygon(star_points(C, C, u(220), u(178), n=spikes, turn=0), fill=bg)
    d.polygon(star_points(C, C, u(186), u(150), n=spikes, turn=0), outline=WHITE, width=u(6))
    text(d, (C, C + u(4)), words, 112 if len(words) <= 3 else 94, WHITE, stroke=5, stroke_fill=DARK)
    text(d, (C, C + u(4)), words, 112 if len(words) <= 3 else 94, WHITE, stroke=2)
    layer = with_shadow(image)

    def frame(t):
        shake = math.sin(math.pi * seg(t, 0, 0.4))
        angle = 12 * shake * math.sin(seg(t, 0, 0.4) * math.tau * 4)
        scale = 1 + 0.08 * shake  # still after the shake, so the held frames cost nothing
        return place(layer, scale, angle)
    return frame, 1.5


def finger_point():
    hand = hand_layer()

    def frame(t):
        return place(hand, 1.3, dx=170 + 40 * wave(t), dy=0)
    return frame, 1.0


def click_here():
    base = pill("CLICK HERE", GREEN, size=56)
    up, down = cursor_layer(), cursor_layer(True)

    def frame(t):
        tap = math.exp(-((t - 0.5) / 0.07) ** 2)
        out = layers(place(base, 1 - 0.07 * tap + 0.03 * wave(t, 2) * (1 - tap)))
        out.alpha_composite(place(down if tap > 0.5 else up, dx=110 - 10 * tap, dy=40 + 70 * (1 - tap) * 0.5 + 25 * wave(t)))
        return out
    return frame, 1.2


# id, name, category, tags, builder
STICKERS = [
    ("subscribe-click", "Subscribe click", "Labels", ["subscribe", "button", "cursor", "click", "youtube"], subscribe_click),
    ("bell-ring", "Bell ring", "Marks", ["bell", "notification", "ring", "alert"], bell_ring),
    ("heart-beat", "Heart beat", "Marks", ["heart", "love", "beat", "like"], heart_beat),
    ("like-pop", "Like pop", "Marks", ["like", "thumbs up", "pop"], like_pop),
    ("arrow-right", "Arrow right", "Arrows", ["arrow", "right", "chevron", "next"], lambda: arrow_run("right")),
    ("arrow-left", "Arrow left", "Arrows", ["arrow", "left", "chevron", "back"], lambda: arrow_run("left")),
    ("arrow-up", "Arrow up", "Arrows", ["arrow", "up", "chevron"], lambda: arrow_run("up")),
    ("arrow-down", "Arrow down", "Arrows", ["arrow", "down", "chevron"], lambda: arrow_run("down")),
    ("finger-point", "Finger point", "Arrows", ["finger", "hand", "point", "look"], finger_point),
    ("circle-draw", "Circle draw", "Highlights", ["circle", "ring", "highlight", "attention"], circle_draw),
    ("underline-draw", "Underline draw", "Highlights", ["underline", "line", "highlight", "marker"], underline_draw),
    ("sparkle-stars", "Sparkle stars", "Highlights", ["sparkle", "star", "twinkle", "shine"], sparkle_stars),
    ("firework", "Firework", "Highlights", ["firework", "spark", "burst", "celebrate"], firework),
    ("question-bounce", "Question bounce", "Marks", ["question", "mark", "bounce"], lambda: mark_bounce("?", BLUE)),
    ("exclamation-bounce", "Exclamation bounce", "Marks", ["exclamation", "mark", "bounce", "alert"], lambda: mark_bounce("!", RED)),
    ("bubble-wow", "WOW bubble", "Bubbles", ["wow", "speech", "bubble"], lambda: bubble("WOW!", ORANGE)),
    ("bubble-omg", "OMG bubble", "Bubbles", ["omg", "speech", "bubble"], lambda: bubble("OMG!", PURPLE)),
    ("countdown-3-2-1", "Countdown 3 2 1", "Marks", ["countdown", "timer", "three", "two", "one"], countdown),
    ("loading-spinner", "Loading spinner", "Marks", ["loading", "spinner", "wait"], spinner),
    ("live-blink", "Live blink", "Labels", ["live", "stream", "blink", "red"], live_blink),
    ("new-shake", "New shake", "Labels", ["new", "badge", "shake"], lambda: label_shake("NEW", GREEN, 16)),
    ("hot-shake", "Hot shake", "Labels", ["hot", "badge", "shake", "fire"], lambda: label_shake("HOT", ORANGE, 16)),
    ("sale-shake", "Sale shake", "Labels", ["sale", "badge", "shake", "discount"], lambda: label_shake("SALE", RED, 18)),
    ("click-here", "Click here", "Labels", ["click", "here", "cursor", "button"], click_here),
]


def frames_of(builder):
    fn, seconds = builder()
    count = round(seconds * FPS)
    return [finish(fn(i / count)) for i in range(count)]


def webp_bytes(frames):
    buf = io.BytesIO()
    frames[0].save(buf, "WEBP", save_all=True, append_images=frames[1:], duration=1000 // FPS, loop=0,
                   lossless=False, quality=QUALITY, alpha_quality=ALPHA_QUALITY, method=6,
                   minimize_size=True)
    return buf.getvalue()


def read_text(name):
    return (SOURCE_DIR / name).read_text(encoding="utf-8").replace("\r\n", "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", type=Path, required=True, help="output directory")
    parser.add_argument("--images", type=Path, help="also write the WebP files here")
    parser.add_argument("--only", help="build only this sticker id (with --images, no zip)")
    args = parser.parse_args()

    items = []
    for sticker_id, name, category, tags, builder in STICKERS:
        if args.only and sticker_id != args.only:
            continue
        data = webp_bytes(frames_of(builder))
        item = {"id": sticker_id, "file": f"images/{sticker_id}.webp", "name": name, "tags": tags + ["animated"],
                "category": category}
        items.append((item, data))
        print(f"  {sticker_id}\t{len(data)} bytes")
        if args.images:
            args.images.mkdir(parents=True, exist_ok=True)
            (args.images / f"{sticker_id}.webp").write_bytes(data)
    if args.only:
        return
    manifest = {
        "format": FORMAT,
        "type": "sticker",
        "id": PACK_ID,
        "name": PACK_NAME,
        "version": VERSION,
        "license": {"spdx": "MIT", "files": ["LICENSE.txt", "NOTICE.txt"]},
        "items": [item for item, _ in items],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / ZIP_NAME
    write_zip(target, manifest, items, read_text("LICENSE.txt"), read_text("NOTICE.txt"))
    print(f"{ZIP_NAME}\t{len(items)} items\t{target.stat().st_size} bytes")


if __name__ == "__main__":
    main()
