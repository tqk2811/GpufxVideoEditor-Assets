"""Build the sticker pack (107 Fluent Emoji, 3D style) from a checkout of microsoft/fluentui-emoji.

    py -I scripts/pack_stickers.py --source <fluentui-emoji checkout> -o dist-stickers

Binary images are never committed to this repository. This script reads the `assets/<Name>/` folders
of a checkout of https://github.com/microsoft/fluentui-emoji (MIT) and writes `stickers.zip`. The
checkout must be at the commit pinned in FLUENT_COMMIT, and its LICENSE must be the text in
LICENSE_TEXT; otherwise the script stops. The zip has, at its root, `manifest.json`, `LICENSE.txt`,
`NOTICE.txt` and `images/<id>.png`. It is reproducible byte for byte (sorted entries, fixed
timestamps); PNG is stored without recompression. Standard library only; run it with the `py`
launcher on Windows. Run it with `py -I`: the checkout is data, the script only reads it.

Manifest (the contract with the editor): format 1, type "sticker", and items
`{id, file, name, tags, category}`. `name`, `tags` and `category` come from the `metadata.json` of
each emoji (CLDR name, keywords, Unicode group); `id` is the CLDR name as a slug. Items keep the order
of STICKERS below. Fluent Emoji has a 3D PNG for every emoji listed, so none is replaced.

Where the 3D file is: `assets/<Name>/3D/<name>_3d.png`, or, for emoji with skin tones,
`assets/<Name>/Default/3D/<name>_3d_default.png`. Folder names have spaces; the zip never does.
"""

import argparse
import json
import re
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

FIXED_TIME = (1980, 1, 1, 0, 0, 0)
ID_PATTERN = re.compile(r"^[a-z0-9._-]+$")
FORMAT = 1  # same value as the audio packs written by pack_audio.py
VERSION = "1.0.0"
PACK_ID = "avs-stickers"
PACK_NAME = "Stickers: Fluent Emoji"
ZIP_NAME = "stickers.zip"
FLUENT_REPO = "https://github.com/microsoft/fluentui-emoji"
FLUENT_COMMIT = "1ffb34c752ecf5d402f04cfb4b392c77f57c54bc"

# The 107 emoji of the sticker panel of AI Video Studio, as folder names of fluentui-emoji/assets.
STICKERS = (
    "Fire", "Hundred points", "Rocket", "Sparkles", "Star", "Glowing star", "Light bulb", "Red heart",
    "Orange heart", "Blue heart", "Green heart", "Purple heart", "Face with tears of joy",
    "Rolling on the floor laughing", "Smiling face with heart-eyes", "Smiling face with hearts",
    "Star-struck", "Exploding head", "Face screaming in fear", "Smiling face with sunglasses",
    "Thinking face", "Face with peeking eye", "Grinning face with sweat", "Partying face",
    "Loudly crying face", "Pouting face", "Sleeping face", "Money-mouth face", "Clapping hands",
    "Thumbs up", "Thumbs down", "Folded hands", "Flexed biceps", "Handshake",
    "Backhand index pointing right", "Eyes", "Heart hands", "Crown", "Gem stone", "Party popper",
    "Bullseye", "Trophy", "1st place medal", "Chart increasing", "Chart decreasing", "Money bag",
    "Money with wings", "Coin", "House", "House with garden", "Office building", "Key", "Round pushpin",
    "World map", "Shopping cart", "Shopping bags", "Wrapped gift", "Package", "Label", "Mobile phone",
    "Laptop", "Desktop computer", "Robot", "Brain", "High voltage", "Check mark button", "Cross mark",
    "Warning", "Red question mark", "Red exclamation mark", "Speech balloon", "Speaking head", "Megaphone",
    "Bell", "Clapper board", "Musical note", "Microphone", "Camera with flash", "Alarm clock", "Calendar",
    "Memo", "Books", "Graduation cap", "Writing hand", "Pushpin", "Magnifying glass tilted left", "Locked",
    "Puzzle piece", "Video game", "Sun", "Crescent moon", "Rainbow", "Hot beverage", "Four leaf clover",
    "Cherry blossom", "Pizza", "Hamburger", "Bubble tea", "Airplane", "Automobile", "Beach with umbrella",
    "Lipstick", "Dress", "Person lifting weights", "Person in lotus position", "Dog face", "Cat face",
)

LICENSE_TEXT = """\
MIT License

Copyright (c) Microsoft Corporation.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE
"""

NOTICE_TEXT = f"""\
Fluent Emoji (3D) by Microsoft
Copyright (c) Microsoft Corporation.
{FLUENT_REPO}
Source commit: {FLUENT_COMMIT}

The images are the unmodified 3D PNG files of that repository, renamed to ASCII file names.
Names, tags and categories are taken from the metadata.json of each emoji.
The choice of the 107 emoji follows the sticker panel of AI Video Studio by Nguyễn Tất Kiểm
(https://github.com/nguyentatkiem/ai-video-studio, MIT).
"""

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message):
    sys.exit(f"error: {message}")


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def normalize_license(text):
    return "\n".join(line.strip() for line in text.strip().splitlines())


def check_source(source):
    """The checkout must be the pinned commit and carry the licence text we ship."""
    license_file = source / "LICENSE"
    if not license_file.is_file():
        fail(f"{license_file} not found")
    if normalize_license(license_file.read_text(encoding="utf-8")) != normalize_license(LICENSE_TEXT):
        fail("LICENSE of the checkout differs from LICENSE_TEXT")
    try:
        head = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        fail(f"{source}: cannot read the commit (git is needed to check the pin)")
    if head != FLUENT_COMMIT:
        fail(f"{source} is at {head}, the script pins {FLUENT_COMMIT}")


def png_size(data, name):
    if data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        fail(f"{name}: not a PNG file")
    return struct.unpack(">II", data[16:24])


def find_image(folder):
    for sub in ("3D", "Default/3D"):
        found = sorted((folder / sub).glob("*.png")) if (folder / sub).is_dir() else []
        if len(found) == 1:
            return found[0]
        if len(found) > 1:
            fail(f"{folder.name}: more than one 3D PNG in {sub}")
    fail(f"{folder.name}: no 3D PNG file")


def load_items(source):
    items = []  # (item, image path)
    for folder_name in STICKERS:
        folder = source / "assets" / folder_name
        metadata_file = folder / "metadata.json"
        if not metadata_file.is_file():
            fail(f"{folder_name}: metadata.json not found")
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        cldr = metadata.get("cldr") or folder_name.lower()
        slug = slugify(cldr)
        keywords = []
        for tag in [cldr] + list(metadata.get("keywords", [])):
            tag = tag.strip().lower()
            if tag and tag not in keywords:
                keywords.append(tag)
        item = {
            "id": slug,
            "file": f"images/{slug}.png",
            "name": folder_name,
            "tags": keywords,
            "category": metadata["group"],
        }
        items.append((item, find_image(folder)))
    return items


def build_manifest(items):
    return {
        "format": FORMAT,
        "type": "sticker",
        "id": PACK_ID,
        "name": PACK_NAME,
        "version": VERSION,
        "license": {"spdx": "MIT", "files": ["LICENSE.txt", "NOTICE.txt"]},
        "items": [item for item, _ in items],
    }


def validate(items):
    if len(items) != len(STICKERS) or len(set(STICKERS)) != len(STICKERS):
        fail("STICKERS has duplicates")
    ids, files = set(), set()
    for item, source in items:
        if not ID_PATTERN.match(item["id"]):
            fail(f"id '{item['id']}' does not match [a-z0-9._-]+")
        if item["id"] in ids or item["file"] in files:
            fail(f"duplicate id or file '{item['id']}'")
        ids.add(item["id"])
        files.add(item["file"])
        if not re.fullmatch(r"images/[a-z0-9._-]+\.png", item["file"]):
            fail(f"file '{item['file']}' is not a safe ASCII path")
        png_size(source.read_bytes(), source.name)


def write_zip(target, manifest, items):
    text_files = [
        ("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"),
        ("LICENSE.txt", LICENSE_TEXT),
        ("NOTICE.txt", NOTICE_TEXT),
    ]
    temporary = target.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w") as archive:
        def add(entry_name, data, compress):
            info = zipfile.ZipInfo(entry_name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o644 << 16
            info.compress_type = compress
            archive.writestr(info, data, compresslevel=9 if compress == zipfile.ZIP_DEFLATED else None)

        for entry_name, text in text_files:
            add(entry_name, text.encode("utf-8"), zipfile.ZIP_DEFLATED)
        for item, source in sorted(items, key=lambda pair: pair[0]["file"]):
            add(item["file"], source.read_bytes(), zipfile.ZIP_STORED)
    temporary.replace(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, required=True, help="checkout of microsoft/fluentui-emoji at the pinned commit")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output directory")
    args = parser.parse_args()

    check_source(args.source)
    items = load_items(args.source)
    manifest = build_manifest(items)
    validate(items)

    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / ZIP_NAME
    write_zip(target, manifest, items)
    print(f"{ZIP_NAME}\t{len(items)} items\t{target.stat().st_size} bytes")
    categories = {}
    for item, _ in items:
        categories[item["category"]] = categories.get(item["category"], 0) + 1
    for category, count in sorted(categories.items()):
        print(f"  {category}\t{count}")


if __name__ == "__main__":
    main()
