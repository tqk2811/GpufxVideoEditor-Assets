"""Translations that travel inside the pack zips.

A pack may have `i18n/<language>.json` next to its manifest (for example `i18n/vi.json`). The zip
carries each of them at the same path, `i18n/<language>.json`. The file is optional and never changes
the original manifest or item files. Every field is optional:

    {
      "name": "...", "description": "...", "tags": ["..."],
      "params": {"<param name>": {"label": "...", "description": "..."}},   # effect packs
      "items": {"<item id>": {"name": "...", "description": "...", "category": "...", "tags": ["..."]}}
    }

`items` is keyed by the same id as the pack's own items (the file name of items/<id>.json for clip
animations, the `id` of an item in pack.json or manifest.json for the other kinds). Every pack zip holds one
item (see item_packs.py), so its file has the item's `name`, `description`, `tags` and `category` at the
top, `collection_name` (the translated name of the source collection) and `items` with that one item.
Standard library only.
"""

import json
import re
import sys
from pathlib import Path

LANGUAGE = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
TEXT_FIELDS = ("name", "description", "category", "label", "collection_name")


def fail(message):
    sys.exit(f"error: {message}")


def check_texts(where, obj, allowed):
    if not isinstance(obj, dict):
        fail(f"{where}: an object is expected")
    for key, value in obj.items():
        if key not in allowed:
            fail(f"{where}: unknown field '{key}'")
        if key == "tags":
            if not isinstance(value, list) or not all(isinstance(t, str) and t.strip() for t in value):
                fail(f"{where}.tags: a list of non-empty strings is expected")
        elif key in TEXT_FIELDS:
            if not isinstance(value, str) or not value.strip():
                fail(f"{where}.{key}: a non-empty string is expected")


def check_translation(where, data, item_ids=None, param_names=None):
    check_texts(where, {k: v for k, v in data.items() if k not in ("params", "items")}, ("name", "description", "tags", "category", "collection_name"))
    for section, allowed_keys, fields in (
        ("params", param_names, ("label", "description")),
        ("items", item_ids, ("name", "description", "category", "tags")),
    ):
        entries = data.get(section)
        if entries is None:
            continue
        if not isinstance(entries, dict):
            fail(f"{where}.{section}: an object is expected")
        for key, value in entries.items():
            if allowed_keys is not None and key not in allowed_keys:
                fail(f"{where}.{section}: '{key}' is not in the pack")
            check_texts(f"{where}.{section}.{key}", value, fields)


def i18n_entries(folder, item_ids=None, param_names=None):
    """{"i18n/<language>.json": text} for every i18n/*.json of the folder, checked against the pack."""
    entries = {}
    directory = Path(folder) / "i18n"
    if not directory.is_dir():
        return entries
    for path in sorted(directory.glob("*.json")):
        if not LANGUAGE.match(path.stem):
            fail(f"{path}: the file name must be a language code such as vi.json")
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        try:
            data = json.loads(text)
        except ValueError as error:
            fail(f"{path}: {error}")
        check_translation(str(path), data, item_ids, param_names)
        entries[f"i18n/{path.name}"] = text
    return entries
