#!/usr/bin/env python3
"""Build the text style and subtitle style packs of AI Video Studio.

    py -I scripts/pack_text_styles.py            # -> dist/<pack id>.zip for every pack
    py -I scripts/pack_text_styles.py -o out     # into out/
    py -I scripts/pack_text_styles.py --check    # only validate the sources

Source: text-styles/<pack>/pack.json (type, id, name, version, items), LICENSE.txt and NOTICE.txt. Each
zip has, at its root, manifest.json (format 1, type "text-style" or "subtitle-style"), LICENSE.txt and
NOTICE.txt. It is reproducible byte for byte (sorted entries, fixed timestamps). Standard library only.

Before writing, every manifest is checked with the rules of the editor's strict reader
(crates/gpufx-editor/src/text_style_install.rs, subtitle_style_install.rs, asset_install.rs and
engine::text_style_problems): known fields only, safe ids, unique item ids, texts of 1 to 200
characters, colours [r, g, b, a] of 0..255, size 0.01..0.5, weight 100..900, letter spacing within
+-2, glow radius 0..2, intensity 0..4, falloff 0.1..8, animation presets '<pack>/<item>' lasting
0..60 s, subtitle layout and karaoke ranges. Animation presets must also name an item of the clip
animation pack (animations/avs/pack.json) of the right kind.
"""

import argparse
import json
import math
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "text-styles"
ANIMATIONS = ROOT / "animations" / "avs" / "pack.json"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
MAX_ID_LENGTH = 128
MAX_ITEMS = 16_384
MAX_TEXT_CHARS = 200
MAX_FONT_HINTS = 16
SIZE_RANGE = (0.01, 0.5)
MAX_LINE_SPACING = 10.0
WEIGHT_RANGE = (100, 900)
MAX_LETTER_SPACING = 2.0
MAX_GLOW_RADIUS = 2.0
MAX_GLOW_INTENSITY = 4.0
GLOW_FALLOFF_RANGE = (0.1, 8.0)
MAX_ANIMATION_SECONDS = 60.0
MAX_SUBTITLE_LINES = 10
MAX_KARAOKE_SCALE = 4.0
TYPES = ("text-style", "subtitle-style")
ALIGNS = ("left", "center", "right")
TRANSFORMS = ("none", "uppercase", "lowercase")
KARAOKE_MODES = ("none", "color", "box", "scale")
GROUPS = {"in": "in", "out": "out", "loop": "loop"}
LICENSE_FILES = ["LICENSE.txt", "NOTICE.txt"]
SPDX = {
    "avs-text-style": "MIT",
    "avs-subtitle-style": "MIT",
    "avs-subtitle-style-ghost": "MIT",
    "avs-subtitle-style-hf": "MIT AND Apache-2.0",
}


def fail(message):
    sys.exit(f"error: {message}")


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def safe_id(value):
    return isinstance(value, str) and 0 < len(value) <= MAX_ID_LENGTH and SAFE_ID.match(value) and value not in (".", "..")


def check_fields(where, obj, required, optional=()):
    if not isinstance(obj, dict):
        fail(f"{where} is not an object")
    for name in required:
        if name not in obj:
            fail(f"{where} lacks '{name}'")
    for name in obj:
        if name not in required and name not in optional:
            fail(f"{where} has the unknown field '{name}'")


def short_text(where, value):
    if not isinstance(value, str) or not value.strip():
        fail(f"{where} is empty")
    if len(value) > MAX_TEXT_CHARS:
        fail(f"{where} is longer than {MAX_TEXT_CHARS} characters")


def check_color(where, value):
    if not (isinstance(value, list) and len(value) == 4 and all(isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 255 for v in value)):
        fail(f"{where} must be [r, g, b, a] with each 0 to 255")


def not_negative(where, value):
    if not (number(value) and value >= 0):
        fail(f"{where} must be 0 or more")


def check_style(where, style):
    check_fields(where, style, (), ("size", "color", "outline", "background", "shadow", "glow", "align", "line_spacing",
                                    "weight", "italic", "transform", "letter_spacing", "font_hint"))
    if "size" in style and not (number(style["size"]) and SIZE_RANGE[0] <= style["size"] <= SIZE_RANGE[1]):
        fail(f"{where}: size must be from {SIZE_RANGE[0]} to {SIZE_RANGE[1]}")
    if "color" in style:
        check_color(f"{where} color", style["color"])
    if "outline" in style:
        check_fields(f"{where} outline", style["outline"], ("color", "width"))
        check_color(f"{where} outline.color", style["outline"]["color"])
        not_negative(f"{where} outline.width", style["outline"]["width"])
    if "background" in style:
        check_fields(f"{where} background", style["background"], ("color", "padding", "radius"))
        check_color(f"{where} background.color", style["background"]["color"])
        not_negative(f"{where} background.padding", style["background"]["padding"])
        not_negative(f"{where} background.radius", style["background"]["radius"])
    if "shadow" in style:
        shadow = style["shadow"]
        check_fields(f"{where} shadow", shadow, ("color", "offset", "blur"))
        check_color(f"{where} shadow.color", shadow["color"])
        if not (isinstance(shadow["offset"], list) and len(shadow["offset"]) == 2 and all(number(v) for v in shadow["offset"])):
            fail(f"{where}: shadow.offset must be two finite numbers")
        not_negative(f"{where} shadow.blur", shadow["blur"])
    if "glow" in style:
        glow = style["glow"]
        check_fields(f"{where} glow", glow, ("color", "radius"), ("outer_color", "intensity", "falloff"))
        check_color(f"{where} glow.color", glow["color"])
        if "outer_color" in glow:
            check_color(f"{where} glow.outer_color", glow["outer_color"])
        if not (number(glow["radius"]) and 0 <= glow["radius"] <= MAX_GLOW_RADIUS):
            fail(f"{where}: glow.radius must be from 0 to {MAX_GLOW_RADIUS}")
        if "intensity" in glow and not (number(glow["intensity"]) and 0 <= glow["intensity"] <= MAX_GLOW_INTENSITY):
            fail(f"{where}: glow.intensity must be from 0 to {MAX_GLOW_INTENSITY}")
        if "falloff" in glow and not (number(glow["falloff"]) and GLOW_FALLOFF_RANGE[0] <= glow["falloff"] <= GLOW_FALLOFF_RANGE[1]):
            fail(f"{where}: glow.falloff must be from {GLOW_FALLOFF_RANGE[0]} to {GLOW_FALLOFF_RANGE[1]}")
    if "align" in style and style["align"] not in ALIGNS:
        fail(f"{where}: align must be one of {ALIGNS}")
    if "line_spacing" in style and not (number(style["line_spacing"]) and 0 < style["line_spacing"] <= MAX_LINE_SPACING):
        fail(f"{where}: line_spacing must be above 0 and at most {MAX_LINE_SPACING}")
    if "weight" in style:
        weight = style["weight"]
        if not (isinstance(weight, int) and not isinstance(weight, bool) and WEIGHT_RANGE[0] <= weight <= WEIGHT_RANGE[1]):
            fail(f"{where}: weight must be a whole number from {WEIGHT_RANGE[0]} to {WEIGHT_RANGE[1]}")
    if "italic" in style and not isinstance(style["italic"], bool):
        fail(f"{where}: italic must be true or false")
    if "transform" in style and style["transform"] not in TRANSFORMS:
        fail(f"{where}: transform must be one of {TRANSFORMS}")
    if "letter_spacing" in style and not (number(style["letter_spacing"]) and abs(style["letter_spacing"]) <= MAX_LETTER_SPACING):
        fail(f"{where}: letter_spacing must be from -{MAX_LETTER_SPACING} to {MAX_LETTER_SPACING}")
    if "font_hint" in style:
        hints = style["font_hint"]
        if not isinstance(hints, list) or len(hints) > MAX_FONT_HINTS:
            fail(f"{where}: font_hint must be a list of at most {MAX_FONT_HINTS} fonts")
        for hint in hints:
            short_text(f"{where} a font_hint", hint)


def check_animation(where, animation, presets):
    check_fields(where, animation, (), tuple(GROUPS))
    for group, ref in animation.items():
        check_fields(f"{where} {group}", ref, ("preset", "duration"))
        preset = ref["preset"]
        pack, sep, item = preset.partition("/") if isinstance(preset, str) else ("", "", "")
        if not (sep and safe_id(pack) and safe_id(item)):
            fail(f"{where}: the '{group}' preset '{preset}' is not '<pack>/<item>'")
        if presets.get(preset) != GROUPS[group]:
            fail(f"{where}: the '{group}' preset '{preset}' is not an '{group}' item of the clip animation pack")
        if not (number(ref["duration"]) and 0 < ref["duration"] <= MAX_ANIMATION_SECONDS):
            fail(f"{where}: the '{group}' animation must last more than 0 and at most {MAX_ANIMATION_SECONDS} seconds")


def check_layout(where, layout):
    check_fields(where, layout, ("anchor_y", "max_width", "max_lines"))
    if not (number(layout["anchor_y"]) and 0 <= layout["anchor_y"] <= 1):
        fail(f"{where}: anchor_y must be from 0 to 1")
    if not (number(layout["max_width"]) and 0 < layout["max_width"] <= 1):
        fail(f"{where}: max_width must be above 0 and at most 1")
    lines = layout["max_lines"]
    if not (isinstance(lines, int) and not isinstance(lines, bool) and 1 <= lines <= MAX_SUBTITLE_LINES):
        fail(f"{where}: max_lines must be from 1 to {MAX_SUBTITLE_LINES}")


def check_karaoke(where, karaoke):
    states = ("active", "spoken", "upcoming", "emphasis")
    check_fields(where, karaoke, ("mode",), states)
    if karaoke["mode"] not in KARAOKE_MODES:
        fail(f"{where}: mode must be one of {KARAOKE_MODES}")
    for state in states:
        if state not in karaoke:
            continue
        look = karaoke[state]
        check_fields(f"{where} {state}", look, (), ("color", "background", "scale", "opacity"))
        for name in ("color", "background"):
            if name in look:
                check_color(f"{where} {state}.{name}", look[name])
        if "scale" in look and not (number(look["scale"]) and 0 < look["scale"] <= MAX_KARAOKE_SCALE):
            fail(f"{where}: {state}.scale must be above 0 and at most {MAX_KARAOKE_SCALE}")
        if "opacity" in look and not (number(look["opacity"]) and 0 <= look["opacity"] <= 1):
            fail(f"{where}: {state}.opacity must be from 0 to 1")


def check_manifest(manifest, presets):
    check_fields("the manifest", manifest, ("format", "type", "id", "name", "version", "license", "items"))
    kind = manifest["type"]
    if manifest["format"] != 1 or kind not in TYPES:
        fail(f"format must be 1 and type one of {TYPES}")
    if not safe_id(manifest["id"]):
        fail("unsafe pack id")
    for name in ("name", "version"):
        if not isinstance(manifest[name], str) or not manifest[name].strip():
            fail(f"empty {name}")
    check_fields("license", manifest["license"], ("spdx", "files"))
    if not manifest["license"]["spdx"].strip() or not manifest["license"]["files"]:
        fail("license.spdx and license.files must not be empty")
    items = manifest["items"]
    if not items or len(items) > MAX_ITEMS:
        fail(f"items must hold 1 to {MAX_ITEMS} styles")
    seen = set()
    subtitle = kind == "subtitle-style"
    for item in items:
        optional = ("category", "preview_text", "animation") + (("karaoke",) if subtitle else ())
        required = ("id", "name", "style") + (("layout",) if subtitle else ())
        check_fields("an item", item, required, optional)
        where = f"item '{item['id']}'"
        if not safe_id(item["id"]):
            fail(f"{where}: the id may only hold letters, digits, '.', '-' and '_'")
        if item["id"].lower() in seen:
            fail(f"{where}: the id is used twice")
        seen.add(item["id"].lower())
        short_text(f"{where} name", item["name"])
        for name in ("category", "preview_text"):
            if name in item:
                short_text(f"{where} {name}", item[name])
        check_style(f"{where} style", item["style"])
        if "animation" in item:
            check_animation(f"{where} animation", item["animation"], presets)
        if subtitle:
            check_layout(f"{where} layout", item["layout"])
            if "karaoke" in item:
                check_karaoke(f"{where} karaoke", item["karaoke"])


def animation_presets():
    source = json.loads(ANIMATIONS.read_text(encoding="utf-8"))
    return {f"{source['id']}/{item['id']}": item["kind"] for item in source["items"]}


def build_manifest(folder):
    source = json.loads((folder / "pack.json").read_text(encoding="utf-8"))
    check_fields(f"{folder.name}/pack.json", source, ("type", "id", "name", "version", "items"))
    if source["id"] != folder.name:
        fail(f"{folder.name}/pack.json: the id '{source['id']}' is not the folder name")
    if source["id"] not in SPDX:
        fail(f"{folder.name}: no licence is known for this pack")
    return {
        "format": 1,
        "type": source["type"],
        "id": source["id"],
        "name": source["name"],
        "version": source["version"],
        "license": {"spdx": SPDX[source["id"]], "files": LICENSE_FILES},
        "items": source["items"],
    }


def write_zip(target, folder, manifest):
    entries = {
        "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        "LICENSE.txt": (folder / "LICENSE.txt").read_text(encoding="utf-8"),
        "NOTICE.txt": (folder / "NOTICE.txt").read_text(encoding="utf-8"),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w") as archive:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, entries[name].replace("\r\n", "\n").encode("utf-8"), compresslevel=9)
    temporary.replace(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "dist", help="output directory")
    parser.add_argument("--check", action="store_true", help="only validate the sources")
    args = parser.parse_args()
    presets = animation_presets()
    folders = sorted(p.parent for p in SOURCE.glob("*/pack.json"))
    if not folders:
        fail(f"no pack.json below {SOURCE}")
    for folder in folders:
        manifest = build_manifest(folder)
        check_manifest(manifest, presets)
        for name in LICENSE_FILES:
            if not (folder / name).is_file():
                fail(f"{folder.name}: missing {name}")
        if args.check:
            print(f"{manifest['id']}: {len(manifest['items'])} {manifest['type']} items ok")
            continue
        target = args.output / f"{manifest['id']}.zip"
        write_zip(target, folder, manifest)
        print(f"wrote {target} ({len(manifest['items'])} items)")


if __name__ == "__main__":
    main()
