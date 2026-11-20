#!/usr/bin/env python3
"""Build the clip animation packs: AI Video Studio's text animations and the tqk2811 animations.

    py -I scripts/pack_animations.py            # -> dist/clip-animation-packs/<pack id>-<item id>.zip
                                                #    and dist/clip-animation-packs.zip
    py -I scripts/pack_animations.py -o out     # into out/
    py -I scripts/pack_animations.py --check    # only validate the sources

Source: animations/<pack>/pack.json (id, name, version, items: the item ids in order), one
animations/<pack>/items/<id>.json per item, LICENSE.txt and NOTICE.txt. An item may carry a
"description", which stays in the source and is left out of the item file. Every item is its own pack
(see item_packs.py): each zip has, at its root, manifest.json (format 1, type "clip-animation", items =
[the item id], collection and collection_name = the pack.json id and name, name and description of the
item), items/<id>.json, LICENSE.txt, NOTICE.txt and i18n/<code>.json; clip-animation-packs.zip bundles
them all. It is reproducible byte for byte (sorted entries, fixed timestamps). Standard library only.

Before writing, the manifest is checked with the rules of the editor's strict reader
(crates/d3d12-backend/src/clip_animation_pack.rs and engine::check_curve): known fields only, safe
ids, kinds in/out/loop, 0 < default_duration <= 60, applies_to kinds, curve tracks with keyframes in
rising t within 0..1 and finite values, known easings (with the ranges of power, elastic, bounce,
steps and wave), the item files matching pack.json (id = file name, none missing, none unlisted,
no duplicate), an effect's package id and static parameters,
and per_unit (engine::per_unit::check_per_unit: only on text items, stagger or selector, no blur).
"""

import argparse
import json
import math
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from item_packs import item_i18n_entries, item_manifest, remove_collection, type_folder, write_bundle  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "animations"
SPDX = {
    "avs-clip-animation": "MIT",
    "tqk2811-clip-animation": "MIT",
}
UNITS = ("char", "word", "line")
ORDERS = ("forward", "backward", "center", "random")
SHAPES = ("square", "ramp_up", "ramp_down", "triangle", "round", "smooth")
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
KIND = "clip-animation"  # -> clip-animation-packs/ and clip-animation-packs.zip
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
KINDS = ("in", "out", "loop")
CLIP_KINDS = ("text", "image", "video", "sticker")
PROPERTIES = ("dx", "dy", "scale", "scaleX", "scaleY", "rotation", "opacity", "blur")
UNIT_EASES = ("linear", "hold", "easeIn", "easeOut", "easeInOut", "inCubic", "outCubic", "inSine",
              "outSine", "inOutSine", "outExpo", "elastic", "bounce")
MAX_DEFAULT_DURATION = 60.0
POWER_MODES = ("in", "out", "inOut")
STEP_POSITIONS = ("start", "end", "both", "none")


def fail(message):
    sys.exit(f"error: {message}")


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check_fields(where, obj, required, optional=()):
    if not isinstance(obj, dict):
        fail(f"{where} is not an object")
    for name in required:
        if name not in obj:
            fail(f"{where} lacks '{name}'")
    for name in obj:
        if name not in required and name not in optional:
            fail(f"{where} has the unknown field '{name}'")


def check_whole(where, name, value, low, high):
    if not (isinstance(value, int) and not isinstance(value, bool) and low <= value <= high):
        fail(f"{where}: {name} must be a whole number in {low}..{high}")


def check_ease(where, ease):
    if isinstance(ease, str):
        if ease not in UNIT_EASES:
            fail(f"{where}: unknown ease '{ease}'")
        return
    if not isinstance(ease, dict) or len(ease) != 1:
        fail(f"{where}: bad ease {ease!r}")
    name, value = next(iter(ease.items()))
    if name in ("backIn", "backOut"):
        check_fields(f"{where} {name}", value, ("amplitude",))
        if not finite(value["amplitude"]):
            fail(f"{where}: amplitude is not finite")
    elif name == "cubicBezier":
        if not (isinstance(value, list) and len(value) == 4 and all(finite(v) for v in value)):
            fail(f"{where}: cubicBezier needs 4 finite numbers")
    elif name == "power":
        # exponent > 0 (default 3), mode in / out / inOut (default in)
        check_fields(f"{where} power", value, (), ("exponent", "mode"))
        if "exponent" in value and not (finite(value["exponent"]) and value["exponent"] > 0):
            fail(f"{where}: power exponent must be finite and > 0")
        if value.get("mode", "in") not in POWER_MODES:
            fail(f"{where}: power mode must be in, out or inOut")
    elif name == "elastic":
        # amplitude >= 1 (default 1), period > 0 (default 0.3); the bare string "elastic" takes the defaults
        check_fields(f"{where} elastic", value, (), ("amplitude", "period"))
        if "amplitude" in value and not (finite(value["amplitude"]) and value["amplitude"] >= 1):
            fail(f"{where}: elastic amplitude must be finite and >= 1")
        if "period" in value and not (finite(value["period"]) and value["period"] > 0):
            fail(f"{where}: elastic period must be finite and > 0")
    elif name == "bounce":
        # bounces 1..20 (default 4), decay in (0, 1) (default 0.5); the bare string "bounce" takes the defaults
        check_fields(f"{where} bounce", value, (), ("bounces", "decay"))
        if "bounces" in value:
            check_whole(where, "bounce bounces", value["bounces"], 1, 20)
        if "decay" in value and not (finite(value["decay"]) and 0 < value["decay"] < 1):
            fail(f"{where}: bounce decay must be finite and in (0, 1)")
    elif name == "steps":
        # count 1..1000 (default 4), position start / end / both / none (default end)
        check_fields(f"{where} steps", value, (), ("count", "position"))
        if "count" in value:
            check_whole(where, "steps count", value["count"], 1, 1000)
        if value.get("position", "end") not in STEP_POSITIONS:
            fail(f"{where}: steps position must be start, end, both or none")
    elif name == "wave":
        # amplitude finite (default 0.1), cycles > 0 finite (default 2), decay >= 0 finite (default 0)
        check_fields(f"{where} wave", value, (), ("amplitude", "cycles", "decay"))
        if "amplitude" in value and not finite(value["amplitude"]):
            fail(f"{where}: wave amplitude is not finite")
        if "cycles" in value and not (finite(value["cycles"]) and value["cycles"] > 0):
            fail(f"{where}: wave cycles must be finite and > 0")
        if "decay" in value and not (finite(value["decay"]) and value["decay"] >= 0):
            fail(f"{where}: wave decay must be finite and >= 0")
    else:
        fail(f"{where}: unknown ease '{name}'")


def check_keys(where, keys):
    last = 0.0
    for key in keys:
        check_fields(f"{where} keyframe", key, ("t", "value"), ("ease",))
        t = key["t"]
        if not (finite(t) and 0 <= t <= 1 and finite(key["value"])):
            fail(f"{where}: a keyframe is not finite or its t is not in 0..1")
        if t < last:
            fail(f"{where}: the keyframes are not in rising t")
        last = t
        if "ease" in key:
            check_ease(where, key["ease"])


def check_curve(where, curve):
    check_fields(f"{where} curve", curve, ("tracks",))
    tracks = curve["tracks"]
    if not isinstance(tracks, dict) or not tracks:
        fail(f"{where}: the curve has no track")
    for prop, keys in tracks.items():
        if prop not in PROPERTIES:
            fail(f"{where}: unknown property '{prop}'")
        if not isinstance(keys, list) or not keys:
            fail(f"{where}: the {prop} track has no keyframe")
        check_keys(f"{where} {prop}", keys)


def check_effect(where, effect):
    check_fields(f"{where} effect", effect, ("package",), ("progress", "params"))
    if not isinstance(effect["package"], str) or not SAFE_ID.match(effect["package"]):
        fail(f"{where}: the effect package is not a package id")
    progress = effect.get("progress", "progress")
    if not isinstance(progress, str) or not progress.strip():
        fail(f"{where}: the effect has an empty progress")
    params = effect.get("params", {})
    if not isinstance(params, dict) or len(params) > 64 or progress in params:
        fail(f"{where}: bad effect params")
    for name, value in params.items():
        simple = finite(value) or isinstance(value, bool) or (isinstance(value, str) and value.strip()) or (
            isinstance(value, list) and 2 <= len(value) <= 4 and all(finite(v) for v in value))
        if not name.strip() or not simple:
            fail(f"{where}: the effect parameter '{name}' must be a number, a bool, 2 to 4 numbers or an enum choice")


def check_per_unit(where, per_unit):
    check_fields(f"{where} per_unit", per_unit, ("curve",), ("unit", "order", "seed", "stagger", "selector"))
    if per_unit.get("unit", "char") not in UNITS or per_unit.get("order", "forward") not in ORDERS:
        fail(f"{where}: per_unit unit or order is unknown")
    seed = per_unit.get("seed", 0)
    if not (isinstance(seed, int) and not isinstance(seed, bool) and seed >= 0):
        fail(f"{where}: per_unit seed must be a whole number")
    if ("stagger" in per_unit) == ("selector" in per_unit):
        fail(f"{where}: per_unit needs exactly one of stagger and selector")
    if "stagger" in per_unit and not (finite(per_unit["stagger"]) and 0 <= per_unit["stagger"] <= 1):
        fail(f"{where}: the stagger of per_unit must be in 0..1")
    if "selector" in per_unit:
        selector = per_unit["selector"]
        check_fields(f"{where} selector", selector, (), ("start", "end", "offset", "shape"))
        if selector.get("shape", "square") not in SHAPES:
            fail(f"{where}: unknown selector shape")
        for name in ("start", "end", "offset"):
            check_keys(f"{where} selector {name}", selector.get(name, []))
    check_curve(f"{where} per_unit", per_unit["curve"])
    if "blur" in per_unit["curve"]["tracks"]:
        fail(f"{where}: the per_unit curve cannot blur a unit")


def check_item(item):
    check_fields("an item", item, ("id", "name", "kind", "default_duration"), ("description", "curve", "applies_to", "effect", "per_unit"))
    where = f"item '{item['id']}'"
    if not isinstance(item["id"], str) or not SAFE_ID.match(item["id"]) or item["id"] in (".", ".."):
        fail(f"{where}: unsafe id")
    if not isinstance(item["name"], str) or not item["name"].strip():
        fail(f"{where}: empty name")
    if "description" in item and not isinstance(item["description"], str):
        fail(f"{where}: description must be a string")
    if item["kind"] not in KINDS:
        fail(f"{where}: kind '{item['kind']}' is not in, out or loop")
    duration = item["default_duration"]
    if not (finite(duration) and 0 < duration <= MAX_DEFAULT_DURATION):
        fail(f"{where}: default_duration must be in (0, {MAX_DEFAULT_DURATION}]")
    if "applies_to" in item:
        kinds = item["applies_to"]
        if not kinds or len(set(kinds)) != len(kinds) or any(k not in CLIP_KINDS for k in kinds):
            fail(f"{where}: bad applies_to")
    if "per_unit" in item:
        if item.get("applies_to") != ["text"]:
            fail(f"{where}: an item with per_unit must have applies_to ['text']")
        check_per_unit(where, item["per_unit"])
    if "effect" in item:
        check_effect(where, item["effect"])
    if "curve" in item:
        check_curve(where, item["curve"])
    elif "effect" not in item and "per_unit" not in item:
        fail(f"{where}: an item without an effect or per_unit needs a curve")


def check_manifest(manifest, items):
    check_fields("the manifest", manifest, ("format", "type", "id", "name", "version", "license", "items",
                                            "collection", "collection_name"), ("description",))
    if manifest["format"] != 1 or manifest["type"] != "clip-animation":
        fail("format must be 1 and type 'clip-animation'")
    if not SAFE_ID.match(manifest["id"]):
        fail("unsafe pack id")
    for name in ("name", "version", "collection", "collection_name"):
        if not isinstance(manifest[name], str) or not manifest[name].strip():
            fail(f"empty {name}")
    check_fields("license", manifest["license"], ("spdx", "files"))
    if not manifest["license"]["spdx"].strip() or not manifest["license"]["files"]:
        fail("license.spdx and license.files must not be empty")
    if len(items) != 1 or [item["id"] for item in items] != manifest["items"]:
        fail("a pack holds exactly one item, matching the manifest")
    if not SAFE_ID.match(manifest["collection"]) or manifest["id"] != f"{manifest['collection']}-{manifest['items'][0]}":
        fail(f"pack id '{manifest['id']}' is not '<collection>-<item id>'")
    for item in items:
        check_item(item)


def read_pack(folder):
    """Read animations/<pack>/pack.json and items/<id>.json; return (manifest, items) with the strict layout checks."""
    where = f"{folder.name}/pack.json"
    source = json.loads((folder / "pack.json").read_text(encoding="utf-8"))
    check_fields(where, source, ("id", "name", "version", "items"))
    if source["id"] not in SPDX:
        fail(f"{folder.name}: no licence is known for the pack '{source['id']}'")
    ids = source["items"]
    if not isinstance(ids, list) or not ids:
        fail(f"{where}: items must be a non-empty array of item ids")
    for item_id in ids:
        if not isinstance(item_id, str) or not SAFE_ID.match(item_id) or item_id in (".", ".."):
            fail(f"{where}: {item_id!r} is not a safe item id")
    if len({item_id.lower() for item_id in ids}) != len(ids):
        fail(f"{where}: an item id is listed twice")
    items_dir = folder / "items"
    if not items_dir.is_dir():
        fail(f"{folder.name}: missing the items folder")
    for entry in items_dir.iterdir():
        if not entry.is_file() or entry.suffix != ".json" or entry.stem not in ids:
            fail(f"{folder.name}/items/{entry.name} is not listed in pack.json (or is not an <id>.json file)")
    items = []
    for item_id in ids:
        file = items_dir / f"{item_id}.json"
        if not file.is_file():
            fail(f"{folder.name}: item '{item_id}' has no items/{item_id}.json")
        item = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(item, dict) or item.get("id") != item_id:
            fail(f"{folder.name}/items/{item_id}.json: the id field must equal the file name")
        items.append(item)

    manifest = {
        "format": 1,
        "type": "clip-animation",
        "id": source["id"],
        "name": source["name"],
        "version": source["version"],
        "license": {"spdx": SPDX[source["id"]], "files": ["LICENSE.txt", "NOTICE.txt"]},
        "items": ids,
    }
    return manifest, items


def pack_folders():
    """Every folder of animations/ with a pack.json, in name order."""
    return sorted(p.parent for p in SOURCE.glob("*/pack.json"))


def write_zip(target, folder, manifest, items, collection_ids):
    entries = {
        "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        "LICENSE.txt": (folder / "LICENSE.txt").read_text(encoding="utf-8"),
        "NOTICE.txt": (folder / "NOTICE.txt").read_text(encoding="utf-8"),
    }
    for item in items:
        shipped = {name: value for name, value in item.items() if name != "description"}
        entries[f"items/{item['id']}.json"] = json.dumps(shipped, ensure_ascii=False, indent=2) + "\n"
    # i18n/<language>.json next to pack.json, cut down to this pack's one item.
    entries.update(item_i18n_entries(folder, manifest["items"][0], collection_ids))
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
    parser.add_argument("--check", action="store_true", help="only validate the source")
    args = parser.parse_args()
    folders = pack_folders()
    if not folders:
        fail(f"no pack.json below {SOURCE}")
    ids = set()
    output = type_folder(args.output, KIND)
    for folder in folders:
        for name in ("LICENSE.txt", "NOTICE.txt"):
            if not (folder / name).is_file():
                fail(f"{folder.name}: missing {name}")
        collection, items = read_pack(folder)
        packs = [(item_manifest(collection, item, item["id"]), item) for item in items]
        for manifest, item in packs:
            check_manifest(manifest, [item])
            if manifest["id"].lower() in ids:
                fail(f"the pack id '{manifest['id']}' is used twice")
            ids.add(manifest["id"].lower())
        if args.check:
            print(f"{collection['id']}: {len(packs)} packs ok")
            continue
        output.mkdir(parents=True, exist_ok=True)
        remove_collection(output, collection["id"])
        for manifest, item in packs:
            write_zip(output / f"{manifest['id']}.zip", folder, manifest, [item], set(collection["items"]))
        print(f"{collection['id']}: wrote {len(packs)} packs into {output}")
    if not args.check:
        write_bundle(args.output, KIND)

if __name__ == "__main__":
    main()
