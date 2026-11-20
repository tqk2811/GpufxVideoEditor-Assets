"""Build the Noto Emoji sticker pack (emotions, arrows and marks) from a checkout of googlefonts/noto-emoji.

    py -I stickers/noto-stickers/generate.py --source <noto-emoji checkout> -o dist-stickers

Binary images are never committed to this repository. This script reads `2D/png/512/emoji_u<code>.png`
of a checkout of https://github.com/googlefonts/noto-emoji and writes one pack per sticker, `sticker-packs/noto-stickers-<id>.zip`. The images
are under the Apache License 2.0 (README of that repository: "Tools and most image resources are under
the Apache license, version 2.0"; `2D/svg/LICENSE`, the licence of the drawings the PNG files are
rendered from). The fonts of that repository are under the OFL and are not used. The checkout must be
at the commit pinned in NOTO_COMMIT and its `2D/svg/LICENSE` must be the Apache header kept in
stickers/noto-stickers/LICENSE.txt; otherwise the script stops. A sparse checkout of `2D/svg/LICENSE` and
`2D/png/512/` is enough.

Each zip has, at its root, `manifest.json` (format 1, type "sticker", items `{id, file, name, tags,
category}`), `LICENSE.txt` and `NOTICE.txt` (the files of stickers/noto-stickers/) and `images/<id>.png`.
Names and ids come from the Unicode name of the emoji (Python's unicodedata), tags from the name's
words. It is reproducible byte for byte (sorted entries, fixed timestamps, PNG stored as is). Standard
library only; run it with `py -I`: the checkout is data, the script only reads it.
"""

import argparse
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from pack_stickers import FORMAT, ID_PATTERN, fail, png_size, slugify, write_packs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = Path(__file__).resolve().parent
VERSION = "1.0.0"
PACK_ID = "noto-stickers"
PACK_NAME = "Stickers: Noto Emoji"
NOTO_COMMIT = "99701e07d3d1fe1bdbcdb14964547f0fd592966f"

# Code points (one emoji each), by category, in the order the panel shows them.
STICKERS = {
    "Emotions": (
        0x1F600, 0x1F603, 0x1F604, 0x1F601, 0x1F606, 0x1F605, 0x1F923, 0x1F602, 0x1F642, 0x1F609, 0x1F60A,
        0x1F607, 0x1F970, 0x1F60D, 0x1F929, 0x1F618, 0x1F60B, 0x1F61C, 0x1F92A, 0x1F911, 0x1F917, 0x1F92D,
        0x1F92B, 0x1F914, 0x1F610, 0x1F644, 0x1F60F, 0x1F62C, 0x1F60C, 0x1F614, 0x1F634, 0x1F637, 0x1F922,
        0x1F975, 0x1F976, 0x1F635, 0x1F92F, 0x1F973, 0x1F60E, 0x1F913, 0x1F615, 0x1F62E, 0x1F633, 0x1F97A,
        0x1F628, 0x1F622, 0x1F62D, 0x1F631, 0x1F629, 0x1F971, 0x1F624, 0x1F621, 0x1F92C, 0x1F608, 0x1F480,
        0x1F921, 0x1F47B, 0x1F47D, 0x1F916,
    ),
    "Arrows": (
        0x2B06, 0x2197, 0x27A1, 0x2198, 0x2B07, 0x2199, 0x2B05, 0x2196, 0x2195, 0x2194, 0x21A9, 0x21AA,
        0x2934, 0x2935, 0x1F503, 0x1F504, 0x1F519, 0x1F51D, 0x25B6, 0x25C0, 0x1F53C, 0x1F53D, 0x23E9,
        0x23EA, 0x261D, 0x1F446, 0x1F447, 0x1F448, 0x1F449,
    ),
    "Marks": (
        0x2705, 0x2714, 0x274C, 0x2757, 0x2753, 0x203C, 0x2049, 0x26A0, 0x1F6AB, 0x26D4, 0x1F4AF, 0x1F525,
        0x2728, 0x1F4A5, 0x1F4A2, 0x1F4AC, 0x1F4AD, 0x1F4A4, 0x1F4A6, 0x1F4A8, 0x2B50, 0x1F31F, 0x1F4AB,
        0x2764, 0x1F494, 0x1F496, 0x1F195, 0x1F193, 0x1F199, 0x1F192, 0x1F198, 0x1F197,
    ),
}

STOP_WORDS = {"with", "and", "of", "the", "a", "in", "face"}


def read_text(name):
    return (SOURCE_DIR / name).read_text(encoding="utf-8").replace("\r\n", "\n")


def normalize(text):
    return "\n".join(line.strip() for line in text.strip().splitlines())


def check_source(source):
    """The checkout must be the pinned commit and carry the licence header we ship."""
    header = source / "2D" / "svg" / "LICENSE"
    if not header.is_file():
        fail(f"{header} not found")
    if normalize(header.read_text(encoding="utf-8")) not in normalize(read_text("LICENSE.txt")):
        fail("2D/svg/LICENSE of the checkout is not the header in stickers/noto-stickers/LICENSE.txt")
    try:
        head = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        fail(f"{source}: cannot read the commit (git is needed to check the pin)")
    if head != NOTO_COMMIT:
        fail(f"{source} is at {head}, the script pins {NOTO_COMMIT}")


def load_items(source):
    items = []  # (item, image path)
    for category, codes in STICKERS.items():
        for code in codes:
            name = unicodedata.name(chr(code), "")
            if not name:
                fail(f"U+{code:04X} has no Unicode name")
            image = source / "2D" / "png" / "512" / f"emoji_u{code:04x}.png"
            if not image.is_file():
                fail(f"{image} not found")
            slug = slugify(name)
            words = [w for w in re.split(r"[^a-z0-9]+", name.lower()) if w and w not in STOP_WORDS]
            tags = [name.lower()] + [w for i, w in enumerate(words) if w not in words[:i]]
            item = {"id": slug, "file": f"images/{slug}.png", "name": name.capitalize(), "tags": tags,
                    "category": category}
            items.append((item, image))
    return items


def validate(items):
    ids = set()
    for item, image in items:
        if not ID_PATTERN.match(item["id"]) or item["id"] in ids:
            fail(f"bad or duplicate id '{item['id']}'")
        ids.add(item["id"])
        if png_size(image.read_bytes(), image.name) != (512, 512):
            fail(f"{image.name} is not 512x512")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, required=True, help="checkout of googlefonts/noto-emoji at the pinned commit")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output directory")
    args = parser.parse_args()

    check_source(args.source)
    items = load_items(args.source)
    validate(items)
    manifest = {
        "format": FORMAT,
        "type": "sticker",
        "id": PACK_ID,
        "name": PACK_NAME,
        "version": VERSION,
        "license": {"spdx": "Apache-2.0", "files": ["LICENSE.txt", "NOTICE.txt"]},
        "items": [item for item, _ in items],
    }
    write_packs(args.output, manifest, items, read_text("LICENSE.txt"), read_text("NOTICE.txt"))
    for category, codes in STICKERS.items():
        print(f"  {category}\t{len(codes)}")


if __name__ == "__main__":
    main()
