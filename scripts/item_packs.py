"""One item per pack: the shared part of the content pack scripts.

Every content pack (sound, music, sticker, clip animation, text or subtitle style) holds exactly one
item. The scripts still read their sources as collections (one AI Video Studio category, one
pack.json...) and split each collection here:

- manifest `id` = `<collection id>-<item id>`; `items` = the one item, its id unchanged;
- `collection` = the collection id, `collection_name` = the collection's display name;
- `name`, `description`, `tags`, `category` of the manifest come from the item;
- i18n/<code>.json: `name`, `description`, `tags`, `category` = the item's translation,
  `collection_name` = the collection's translated name, `items` = only that item.

Pack zips of one type go to <output>/<type>-packs/, and <output>/<type>-packs.zip bundles every zip of
that folder (stored, fixed timestamps), so a single download holds them all. Standard library only.
"""

import json
import zipfile
from pathlib import Path

from pack_i18n import i18n_entries

FIXED_TIME = (1980, 1, 1, 0, 0, 0)
ITEM_FIELDS = ("description", "tags", "category")


def pack_id(collection_id, item_id):
    return f"{collection_id}-{item_id}"


def item_manifest(collection, item, entry=None):
    """The manifest of the pack holding `item` alone. `collection` is the manifest of the whole
    collection; `entry` is what goes into `items` (default: the item itself)."""
    manifest = {}
    for key, value in collection.items():
        if key == "id":
            manifest["id"] = pack_id(collection["id"], item["id"])
        elif key == "name":
            manifest["name"] = item["name"]
            for field in ITEM_FIELDS:
                if field in item:
                    manifest[field] = item[field]
            manifest["collection"] = collection["id"]
            manifest["collection_name"] = collection["name"]
        elif key == "items":
            manifest["items"] = [item if entry is None else entry]
        elif key not in ITEM_FIELDS:
            manifest[key] = value
    return manifest


def item_i18n_entries(folder, item_id, item_ids):
    """{"i18n/<language>.json": text} for the pack of one item, from the collection's i18n/*.json
    (checked against every item of the collection first)."""
    entries = {}
    for name, text in i18n_entries(folder, item_ids=item_ids).items():
        data = json.loads(text)
        translated = (data.get("items") or {}).get(item_id)
        out = {}
        if translated:
            for field in ("name", "description", "tags", "category"):
                if field in translated:
                    out[field] = translated[field]
        if "name" in data:
            out["collection_name"] = data["name"]
        if translated:
            out["items"] = {item_id: translated}
        if out:
            entries[name] = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    return entries


def type_folder(output, kind):
    return Path(output) / f"{kind}-packs"


def remove_collection(folder, collection_id):
    """Delete the zips of an earlier run of the same collection, so a removed item does not linger."""
    if not folder.is_dir():
        return
    for path in folder.glob("*.zip"):
        try:
            with zipfile.ZipFile(path) as archive:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        except (KeyError, ValueError, zipfile.BadZipFile):
            continue
        if manifest.get("collection") == collection_id:
            path.unlink()


def write_bundle(output, kind):
    """<output>/<kind>-packs.zip holding every zip of <output>/<kind>-packs/, stored."""
    folder = type_folder(output, kind)
    zips = sorted(folder.glob("*.zip"))
    bundle = Path(output) / f"{kind}-packs.zip"
    temporary = bundle.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w") as archive:
        for path in zips:
            info = zipfile.ZipInfo(path.name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, path.read_bytes())
    temporary.replace(bundle)
    print(f"{bundle.name}\t{len(zips)} zips\t{bundle.stat().st_size} bytes")
    return len(zips)
