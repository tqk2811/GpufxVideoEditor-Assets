"""Generate the gpufx wrapper sources gpufx/<group>/<name>/ from the inner gpufx packages.

    py -I scripts/migrate_gpufx_wrappers.py --ffmpeg-gpu-filter <packages/gpufx> --assets <packages/gpufx> --capcut <src>

Each source folder holds the editor manifest.json (format 1, type gpufx; id and version of the inner
manifest, tags empty) and a byte for byte copy of every i18n/<code>.json of the inner package. The
inner packages are not touched. Group is the path of the package below its root (ffmpeg, gpl3/openshot,
...); the capcut root gives group `capcut`. Re-running rewrites the same files; an existing manifest's
tags are kept. Names must be unique within a group.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "gpufx"


def inner_packages(root, fixed_group=None):
    for manifest in sorted(root.rglob("manifest.json")):
        folder = manifest.parent
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        if "gpufx" not in data.get("used_for", []):
            print(f"skip (not gpufx): {folder}", file=sys.stderr)
            continue
        if fixed_group:
            group = fixed_group
        else:
            group = folder.parent.relative_to(root).as_posix()
        yield group, folder.name, folder, data


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ffmpeg-gpu-filter", type=Path, required=True, help="FFmpegGpuFilter/packages/gpufx")
    parser.add_argument("--assets", type=Path, required=True, help="packages/gpufx of this repository")
    parser.add_argument("--capcut", type=Path, required=True, help="src folder of FFmpegGpuFilter-packages-capcut")
    args = parser.parse_args()

    seen = {}
    counts = {}
    sources = [(args.ffmpeg_gpu_filter, None), (args.assets, None), (args.capcut, "capcut")]
    for root, fixed in sources:
        for group, name, folder, data in inner_packages(root.resolve(), fixed):
            key = (group, name)
            if key in seen:
                sys.exit(f"collision in group {group}: {name}: {seen[key]} and {folder}")
            seen[key] = folder
            target = OUT / group / name
            tags = []
            old = target / "manifest.json"
            if old.is_file():
                tags = json.loads(old.read_text(encoding="utf-8")).get("tags", [])
            wrapper = {"format": 1, "type": "gpufx", "id": data["id"], "version": data["version"], "package": f"{name}.zip", "tags": tags}
            target.mkdir(parents=True, exist_ok=True)
            with open(old, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(json.dumps(wrapper, ensure_ascii=False, indent=2) + "\n")
            i18n = folder / "i18n"
            if i18n.is_dir():
                (target / "i18n").mkdir(exist_ok=True)
                for file in sorted(i18n.glob("*.json")):
                    shutil.copyfile(file, target / "i18n" / file.name)
            counts[group] = counts.get(group, 0) + 1
    for group in sorted(counts):
        print(f"{group}: {counts[group]}")
    print(f"total: {sum(counts.values())}")


if __name__ == "__main__":
    main()
