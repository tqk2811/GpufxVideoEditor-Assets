"""Zip every package of this repository, and write THIRD_PARTY_NOTICES.md.

    py scripts/pack.py                  all packages -> dist/<slug>.zip
    py scripts/pack.py -o out a b       only the packages a and b, into out/
    py scripts/pack.py --notices        rewrite THIRD_PARTY_NOTICES.md
    py scripts/pack.py --check-notices  fail if THIRD_PARTY_NOTICES.md is out of date
    py scripts/pack.py --wrappers <inner zips root> [-o out] [names]
                                        gpufx/<group>/<name>/ -> out/gpufx/<group>/<name>.zip.gpufxpack

A package is a folder below packages/ with a manifest.json; its folder name is the slug. Zips hold
manifest.json at the root and are byte for byte reproducible: entries are sorted, deflated, and use
a fixed timestamp. 
--wrappers builds the editor wrapper zips of the gpufx effect packages. <inner zips root> holds the
inner packages as produced by `gpufx pack`, laid out <root>/<group>/<name>.zip. A wrapper pack is a zip
named <name>.zip.gpufxpack (the editor tells it by its content, not its name) holding
manifest.json, i18n/<code>.json and the inner zip as <name>.zip; it fails if the inner zip is missing
or its manifest id differs from the wrapper id
(ignoring case), and checks the wrapper manifest and file names exactly as the editor does. Standard library only; run it with the `py` launcher on Windows.
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pack_audio import LICENSE_TEXT as AUDIO_LICENSE, NOTICE_TEXT as AUDIO_NOTICE  # noqa: E402
from pack_stickers import LICENSE_TEXT as STICKER_LICENSE, NOTICE_TEXT as STICKER_NOTICE  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ROOT / "packages"
NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
ANIMATION_DIR = ROOT / "animations"
TEXT_STYLE_DIR = ROOT / "text-styles"
STICKER_DIR = ROOT / "stickers"
WRAPPERS = ROOT / "gpufx"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
REQUIRED = ("manifest.json", "LICENSE.txt", "NOTICE.txt")


def discover():
    found = {}
    for manifest in sorted(PACKAGES.rglob("manifest.json")):
        folder = manifest.parent
        slug = folder.name
        if slug in found:
            sys.exit(f"duplicate package name {slug}: {folder} and {found[slug]}")
        found[slug] = folder
    return found


def validate(slug, folder):
    for name in REQUIRED:
        if not (folder / name).is_file():
            sys.exit(f"{slug}: missing {name}")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    for group in manifest.get("groups", []):
        for each_pass in group.get("passes", []):
            if not (folder / each_pass["shader"]).is_file():
                sys.exit(f"{slug}: missing {each_pass['shader']}")


def files_of(folder):
    names = [p for p in folder.rglob("*") if p.is_file()]
    # manifest.json first, then the rest in path order.
    return sorted(names, key=lambda p: (p.relative_to(folder).as_posix() != "manifest.json", p.relative_to(folder).as_posix()))


def pack(folder, target):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files_of(folder):
            info = zipfile.ZipInfo(path.relative_to(folder).as_posix(), FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def wrapper_sources():
    """gpufx/<group>/<name>/ folders: (group, name, folder), sorted."""
    found = []
    for manifest in sorted(WRAPPERS.rglob("manifest.json")):
        folder = manifest.parent
        found.append((folder.parent.relative_to(WRAPPERS).as_posix(), folder.name, folder))
    return found


def read_text_lf(path):
    # Line endings follow the checkout; the zip always holds LF so it stays reproducible.
    return path.read_bytes().replace(b"\r\n", b"\n")


WRAPPER_EXTENSION = ".zip.gpufxpack"
WRAPPER_KEYS = {"format", "type", "id", "version", "package", "tags"}
WRAPPER_REQUIRED = WRAPPER_KEYS - {"tags"}
MAX_ID_LENGTH = 128
DEVICE_NAMES = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}


def is_safe_id(text):
    # As is_safe_id in crates/d3d12-backend/src/paths.rs of the editor.
    if not text or len(text) > MAX_ID_LENGTH or text in (".", "..") or text.endswith("."):
        return False
    if not all(c.isascii() and (c.isalnum() or c in ".-_") for c in text):
        return False
    stem = text.split(".")[0].upper()
    numbered = any(stem.startswith(prefix) and stem[3:] in tuple("123456789") + ("0",) for prefix in ("COM", "LPT"))
    return stem not in DEVICE_NAMES and not numbered


def language_code(file_name):
    # As language_file_code in crates/gpufx-editor/src/i18n/pack.rs: <code>.json, the extension in
    # any case, the code 1 to 32 ASCII letters, digits, '-' or '_'.
    if len(file_name) < 5 or file_name[-5:].lower() != ".json":
        return None
    code = file_name[:-5]
    ok = 0 < len(code) <= 32 and all(c.isascii() and (c.isalnum() or c in "-_") for c in code)
    return code if ok else None


def check_wrapper_manifest(where, manifest):
    """Checks a wrapper manifest exactly as parse_wrapper_manifest of the editor does."""
    if not isinstance(manifest, dict):
        sys.exit(f"{where}: the manifest is not a JSON object")
    keys = set(manifest)
    if keys - WRAPPER_KEYS:
        sys.exit(f"{where}: unknown field(s) {', '.join(sorted(keys - WRAPPER_KEYS))}")
    if WRAPPER_REQUIRED - keys:
        sys.exit(f"{where}: missing field(s) {', '.join(sorted(WRAPPER_REQUIRED - keys))}")
    if type(manifest["format"]) is not int or manifest["format"] != 1:
        sys.exit(f"{where}: format must be 1")
    for key in ("type", "id", "version", "package"):
        if not isinstance(manifest[key], str):
            sys.exit(f"{where}: {key} must be a string")
    if manifest["type"] != "gpufx":
        sys.exit(f"{where}: type must be \"gpufx\"")
    if not manifest["id"].strip():
        sys.exit(f"{where}: the id is empty")
    tags = manifest.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        sys.exit(f"{where}: tags must be a list of strings")
    package = manifest["package"]
    if not package.lower().endswith(".zip") or not is_safe_id(package[:-4]):
        sys.exit(f"{where}: \"{package}\" is not the file name of a .zip beside the manifest")


def pack_wrapper(group, name, folder, inner_root, target):
    where = f"{group}/{name}"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8-sig"))
    check_wrapper_manifest(where, manifest)
    if manifest["package"] != f"{name}.zip":
        sys.exit(f"{where}: package must be {name}.zip")
    languages = []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        relative = path.relative_to(folder).as_posix()
        if relative == "manifest.json":
            continue
        file_name = relative[len("i18n/"):] if relative.startswith("i18n/") else None
        if file_name is None or "/" in file_name or language_code(file_name) is None:
            sys.exit(f"{where}: stray file {relative}: a wrapper holds only manifest.json and i18n/<code>.json")
        languages.append(path)
    inner = inner_root / group / f"{name}.zip"
    if not inner.is_file():
        sys.exit(f"{where}: missing inner zip {inner}")
    with zipfile.ZipFile(inner) as archive:
        try:
            inner_id = json.loads(archive.read("manifest.json").decode("utf-8-sig")).get("id")
        except KeyError:
            sys.exit(f"{where}: {inner} has no manifest.json")
    if not isinstance(inner_id, str) or inner_id.lower() != manifest["id"].lower():
        sys.exit(f"{where}: wrapper id {manifest['id']} differs from inner id {inner_id}")
    entries = [("manifest.json", read_text_lf(folder / "manifest.json"), zipfile.ZIP_DEFLATED)]
    for file in languages:
        entries.append((f"i18n/{file.name}", read_text_lf(file), zipfile.ZIP_DEFLATED))
    entries.append((f"{name}.zip", inner.read_bytes(), zipfile.ZIP_STORED))
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for entry, data, method in entries:
            info = zipfile.ZipInfo(entry, FIXED_TIME)
            info.compress_type = method
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)


def build_wrappers(inner_root, output, names):
    sources = wrapper_sources()
    if not sources:
        sys.exit(f"no wrapper sources in {WRAPPERS}")
    unknown = set(names) - {name for _, name, _ in sources}
    if unknown:
        sys.exit("unknown wrapper(s): " + ", ".join(sorted(unknown)))
    count = 0
    for group, name, folder in sources:
        if names and name not in names:
            continue
        target = output / "gpufx" / group / f"{name}{WRAPPER_EXTENSION}"
        pack_wrapper(group, name, folder, inner_root, target)
        count += 1
    print(f"packed {count} wrapper(s) into {output / 'gpufx'}")


def notices_text(packages):
    out = [
        "# Third-party notices",
        "",
        "Generated by `py scripts/pack.py --notices` from the `NOTICE.txt` and `LICENSE.txt` of every package, of the audio packs, of the sticker packs, of the clip animation packs and of the text and subtitle style packs (by collection: each pack zip holds one item of a collection).",
        "Each package zip carries its own `NOTICE.txt` and `LICENSE.txt` with the full licence texts.",
        "",
        "## Licence texts used",
        "",
    ]
    by_licence = {}
    for slug, folder in sorted(packages.items()):
        licence = (folder / "LICENSE.txt").read_text(encoding="utf-8")
        by_licence.setdefault(licence, []).append(slug)
    # The audio zips are built by scripts/pack_audio.py and share one licence and one notice.
    by_licence.setdefault(AUDIO_LICENSE, []).extend(["avs-sfx-<category>", "avs-music"])
    # The sticker zip is built by scripts/pack_stickers.py; its licence is Microsoft's, not AI Video Studio's.
    by_licence.setdefault(STICKER_LICENSE, []).append("avs-stickers")
    # The other sticker zips (stickers/noto-stickers/generate.py, stickers/noto-animated-stickers/generate.py,
    # stickers/tqk2811-stickers/generate.py, stickers/tqk2811-animated-stickers/generate.py) keep their LICENSE.txt and
    # NOTICE.txt in stickers/<zip name>/.
    sticker_packs = {folder.name: folder for folder in sorted(STICKER_DIR.iterdir()) if (folder / "LICENSE.txt").is_file()}
    for slug, folder in sticker_packs.items():
        by_licence.setdefault((folder / "LICENSE.txt").read_text(encoding="utf-8"), []).append(slug)
    # The clip animation zips are built by scripts/pack_animations.py from animations/<pack>/, each named after
    # the id in its pack.json.
    animations = {}
    for folder in sorted(ANIMATION_DIR.iterdir()):
        if (folder / "pack.json").is_file():
            animations[json.loads((folder / "pack.json").read_text(encoding="utf-8"))["id"]] = folder
    for slug, folder in animations.items():
        by_licence.setdefault((folder / "LICENSE.txt").read_text(encoding="utf-8"), []).append(slug)
    # The text and subtitle style zips are built by scripts/pack_text_styles.py from text-styles/<pack>/.
    styles = {folder.name: folder for folder in sorted(TEXT_STYLE_DIR.iterdir()) if (folder / "pack.json").is_file()}
    for slug, folder in styles.items():
        by_licence.setdefault((folder / "LICENSE.txt").read_text(encoding="utf-8"), []).append(slug)
    for index, (licence, slugs) in enumerate(by_licence.items(), start=1):
        out += [f"### Licence {index}", "", "Packages: " + ", ".join(f"`{s}`" for s in slugs), "", "```text", licence.rstrip("\n"), "```", ""]
    out += ["## Package notices", ""]
    for slug, folder in sorted(packages.items()):
        out += [f"### `{slug}`", "", "```text", (folder / "NOTICE.txt").read_text(encoding="utf-8").rstrip("\n"), "```", ""]
    out += ["### `avs-stickers`", "", "```text", STICKER_NOTICE.rstrip("\n"), "```", ""]
    for slug, folder in list(sticker_packs.items()) + list(animations.items()):
        out += [f"### `{slug}`", "", "```text", (folder / "NOTICE.txt").read_text(encoding="utf-8").rstrip("\n"), "```", ""]
    for slug, folder in styles.items():
        out += [f"### `{slug}`", "", "```text", (folder / "NOTICE.txt").read_text(encoding="utf-8").rstrip("\n"), "```", ""]
    return "\n".join(out).rstrip("\n") + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "dist", help="output directory (default: dist)")
    parser.add_argument("--notices", action="store_true", help="rewrite THIRD_PARTY_NOTICES.md")
    parser.add_argument("--check-notices", action="store_true", help="fail if THIRD_PARTY_NOTICES.md is out of date")
    parser.add_argument("--wrappers", type=Path, metavar="INNER_ROOT", help="build gpufx wrapper zips from inner zips laid out <root>/<group>/<name>.zip")
    parser.add_argument("slugs", nargs="*", help="package names (default: all)")
    args = parser.parse_args()

    if args.wrappers:
        build_wrappers(args.wrappers, args.output, set(args.slugs))
        return

    packages = discover()
    if not packages:
        sys.exit("no packages found")
    for slug, folder in packages.items():
        validate(slug, folder)

    if args.notices or args.check_notices:
        text = notices_text(packages)
        if args.check_notices:
            current = NOTICES.read_text(encoding="utf-8") if NOTICES.is_file() else ""
            if current.replace("\r\n", "\n") != text:
                sys.exit("THIRD_PARTY_NOTICES.md is out of date: run py scripts/pack.py --notices")
            print("THIRD_PARTY_NOTICES.md is up to date")
            return
        with open(NOTICES, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {NOTICES}")
        return

    selected = args.slugs or sorted(packages)
    for slug in selected:
        if slug not in packages:
            sys.exit(f"unknown package {slug}")
    args.output.mkdir(parents=True, exist_ok=True)
    for slug in selected:
        target = args.output / f"{slug}.zip"
        pack(packages[slug], target)
        print(target)
    print(f"packed {len(selected)} package(s)")


if __name__ == "__main__":
    main()
