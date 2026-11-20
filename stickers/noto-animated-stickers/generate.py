"""Build the Animated Noto Emoji sticker pack (animated WebP) from the files Google publishes.

    py -I stickers/noto-animated-stickers/generate.py --source <folder> --download   fetch the originals once
    py -I stickers/noto-animated-stickers/generate.py --source <folder> -o dist-stickers

Binary images are never committed to this repository. Animated Noto Emoji
(https://googlefonts.github.io/noto-emoji-animation/) is licensed under CC BY 4.0: the FAQ of that page
answers "Can I use these animated assets commercially: for a video, for broadcast, apps, etc.?" with
"Animated Noto Emoji is licensed under CC BY 4.0. See the full license for all details." The originals
are the 512x512 animated WebP files at https://fonts.gstatic.com/s/e/notoemoji/latest/<code>/512.webp.
That URL is not versioned, so the script pins each original by its SHA-256 (SOURCES below) and stops on
any mismatch: re-download, look at the new files and update the hashes on purpose.

The files go into the zip unmodified (512x512, already small: libwebp keeps only what changes between
frames, and scaling them down and encoding again saved almost nothing), renamed after the Unicode name
of each emoji. Each sticker becomes its own pack, `sticker-packs/noto-animated-stickers-<id>.zip`, which has `manifest.json` (format 1, type "sticker",
items `{id, file, name, tags, category}`), `LICENSE.txt` and `NOTICE.txt` (stickers/noto-animated-stickers/)
and `images/<id>.webp`. It is reproducible byte for byte (sorted entries, fixed timestamps, WebP stored
as is). Standard library only; run it with `py -I`: the downloaded files are data.
"""

import argparse
import hashlib
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from pack_stickers import FORMAT, ID_PATTERN, fail, slugify, write_packs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = Path(__file__).resolve().parent
VERSION = "1.0.0"
PACK_ID = "noto-animated-stickers"
PACK_NAME = "Stickers: Animated Noto Emoji"
URL = "https://fonts.gstatic.com/s/e/notoemoji/latest/{code}/512.webp"
SIZE = 512

# Code (as in the URL) -> SHA-256 of the original 512.webp, by category, in the order the panel shows them.
SOURCES = {
    "Emotions": {
        "1f600": "99ae57c7ca271adaa211f2c3e599e996dcc2d962564e49bcd979671e5c73146f",
        "1f602": "281d5ceb7881fe9393c200ea16c73a4d53af58b4ff04d76a46c432e7e4dd0901",
        "1f923": "6dc164b225a4688da15a6642c366e9eb536a0bfb5fe5a475a75c94d2fe14eba5",
        "1f60a": "cd29299c0bfd6c49484c3e536208a81ba1473b80e7236ba7b6ca07c81a21dd6e",
        "1f60d": "f9a12dd0779299de1c77d8c6168be39ad0f5c579b7ac46f9c77d60be042bc3de",
        "1f970": "7734ab5ea4f0f8169df1f9d0faa00983d1d535b9d73b8d4243250531ea9ed898",
        "1f618": "acb27c59d0dc049d5b56dacee775e0a7b4049f226017e6ecd126cf3480199f3d",
        "1f60e": "16e9f241e5471c77bd94b3ff1fbdfd4a37e2056d6485256db41729165b57e66f",
        "1f929": "878a5c5ac1397cf4f79cb73bdb4d077e0eb19b633ebc46dbdf53ecb74223d2b6",
        "1f973": "fcf2af3bb9244afe32685f0293ff2ad3f4fb3575e93fec3054f59c052b82762f",
        "1f914": "4f8cbd8d563d8bf16d4d7043c3e91afcfe514389bd7e81cc5624f6097aa2053c",
        "1f92b": "86e9f17633ec9264b99dea4f7b2bc9893b27e8560f07246dd1987960c36d782e",
        "1f644": "324bde5da39264d5cbd61308aae42174fb03081349333e0467e144402e94f1a1",
        "1f62d": "13a7a4b7e6d920b83f899ca64312bed80280507e93c04bd6e2361764db975a50",
        "1f631": "960377ff1bbe23d763c32facd45654d1d3b38aaa9d4f5cc4b296bf3c79b9b007",
        "1f621": "0404e358adb2ed3bcefe415af7d5dfe3fd150946b1ffde7926337b34ce05ac3d",
        "1f92f": "9bda8e4f7c8941625b0ae64c2c3c85c794bbbe14f8e7bdd13b92b34c726ac59e",
        "1f634": "ca41f50126de30ef67ae2df42f17ae3fd2ffd7deb7b1bba6d2e4141b1ff2ce3f",
        "1f608": "bf5119c4aca66355ff2f0cf68688f6c89a8bd1665272cc20136c3cfaf8291c81",
        "1f440": "44da2fbd6e9ec1dee07808fef5216fb8393d78155c7f104be99525215961e07e",
    },
    "Hands": {
        "1f44d": "f456f329ec2457828e0511f31b855e1b3b21c91f53d7d465dc3a1aa7d3b73383",
        "1f44f": "424f978963357da085a444e1b659028a5f7ccd927d72158ef5c97c82d3ddfd20",
        "1f64c": "51accc877dc32ac4ecfbb5745b89afdf1f610c7e23c4fb292f4bea3dd603fa44",
        "1f64f": "648eb5ee603e776d4452ea78f2a89b7b08c3f4110d4afa7ed3954622a1499a68",
        "1f44b": "2209749c084f37f914e7878346b1285896f4ce9d1a3f5294db93779c00186fa9",
        "270c_fe0f": "116172b2c450bd61d99c844eba03d92bc16ca674e98ec6d76f927f409d5cf321",
        "1f4aa": "fdbf8494ad8c8235bcfec94e751b5570a398bb328020e5282f3923535389548e",
    },
    "Marks": {
        "2764_fe0f": "8f02722ca349a1b1a0c7a02d7ec3c716e09eccdbf696adf89c67afe2bb175b56",
        "1f494": "ccbcbf0f3e1fdb8307072f5f13794f7fa44234518c28bf426ef4f393c0a62cea",
        "1f496": "56a448bb667eab7573047a671f706782b757282e1b737b22abdb2c01fff3f36f",
        "1f525": "8c18972a71041700a1da4d9a1586640fb6d55eff4dc64efd29efde6a384a2ff5",
        "2728": "6f02d6b946908b6bb33452ff81f613928b0a30c09d51d0b43a85d35359e5d1cc",
        "1f4a5": "5db437158db94661f626069d3b68f87ca223108adccb5aa12467bbe003c584c3",
        "1f4af": "c9fdc6075233c9fbd1b77b4df0107187a543223b9ff566fd65a887f221b21008",
        "2b50": "b93aeff891b9601812738449efedab7085b0f6da74c2c39edd652ad523fc76b2",
        "1f31f": "0fe335effdfa7a35334ebd1f2c4b4ba12bfb7a21dd44a458080bc45b365a073d",
        "1f389": "aeff875df341bb7136fa4c84538000a3d4aea8a6dd16245ee8fa1c8bbfeb6ddc",
        "1f38a": "85ca810ff267af819a4025d934af583986ebb6efd1bef4e03be11e49a102cb88",
        "1f381": "14c1aa3148391097d2b90f60afb1acec91d971ffa995862dc50a3b91902e3a36",
        "1f382": "57084b37f4492e470880278badf4e434777982e3eec63fa278e75a16d853575e",
        "1f680": "304e710dde0b42b15673e10937623789adf72cae569c0e0defe7ec21c0bdf293",
        "1f4a1": "aae84c10307e31042dd9dc3d6c1b4561dd3965cde26343646d16a155119f408a",
        "1f514": "743b1168d677dd130f85bc748900d2ae57d9fb9b1549285be4800b666f9e4dfd",
        "2705": "21d3e05606b552902dc221e04c8144809ed650ee2c018a01249803d5ccf85bdb",
        "274c": "aebcaa7d5166f971503823d54df388f1f869288096aad3884f7c3ece5913f7e2",
        "1f4b8": "ecf133c9f706d9c0b64a59460c01e4a28fc5154987537790d3e4dfd7e65379cd",
    },
}

STOP_WORDS = {"with", "and", "of", "the", "a", "in", "face"}


def read_text(name):
    return (SOURCE_DIR / name).read_text(encoding="utf-8").replace("\r\n", "\n")


def emoji_name(code):
    chars = [chr(int(part, 16)) for part in code.split("_") if part != "fe0f"]
    if len(chars) != 1:
        fail(f"{code}: one code point expected")
    name = unicodedata.name(chars[0], "")
    if not name:
        fail(f"{code} has no Unicode name")
    return name


def download(source):
    source.mkdir(parents=True, exist_ok=True)
    for codes in SOURCES.values():
        for code in codes:
            target = source / f"{code}.webp"
            if target.is_file():
                continue
            request = urllib.request.Request(URL.format(code=code), headers={"User-Agent": "asset-packer"})
            with urllib.request.urlopen(request, timeout=60) as response:
                target.write_bytes(response.read())
            print(f"downloaded {target.name}")


def check_webp(data, code):
    """An animated WebP (RIFF, VP8X with the animation flag, an ANIM chunk) of SIZE x SIZE."""
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP" or data[12:16] != b"VP8X":
        fail(f"{code}: not an extended WebP")
    flags = data[20]
    width = int.from_bytes(data[24:27], "little") + 1
    height = int.from_bytes(data[27:30], "little") + 1
    if not flags & 0x02 or b"ANIM" not in data[30:64]:
        fail(f"{code}: not an animated WebP")
    if (width, height) != (SIZE, SIZE):
        fail(f"{code}: {width}x{height}, {SIZE}x{SIZE} expected")
    return data


def load_items(source):
    items = []  # (item, webp bytes)
    ids = set()
    for category, codes in SOURCES.items():
        for code, digest in codes.items():
            path = source / f"{code}.webp"
            if not path.is_file():
                fail(f"{path} not found: run with --download first")
            data = path.read_bytes()
            actual = hashlib.sha256(data).hexdigest()
            if actual != digest:
                fail(f"{path.name}: SHA-256 {actual} differs from the pinned {digest}")
            name = emoji_name(code)
            slug = slugify(name)
            if not ID_PATTERN.match(slug) or slug in ids:
                fail(f"bad or duplicate id '{slug}'")
            ids.add(slug)
            words = [w for w in re.split(r"[^a-z0-9]+", name.lower()) if w and w not in STOP_WORDS]
            tags = [name.lower()] + [w for i, w in enumerate(words) if w not in words[:i]] + ["animated"]
            item = {"id": slug, "file": f"images/{slug}.webp", "name": name.capitalize(), "tags": tags,
                    "category": category}
            items.append((item, check_webp(data, code)))
    return items


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, required=True, help="folder of the original <code>.webp files")
    parser.add_argument("--download", action="store_true", help="download the missing originals into --source")
    parser.add_argument("-o", "--output", type=Path, help="output directory")
    args = parser.parse_args()

    if args.download:
        download(args.source)
        if not args.output:
            return
    if not args.output:
        parser.error("-o is needed to build the zip")
    items = load_items(args.source)
    manifest = {
        "format": FORMAT,
        "type": "sticker",
        "id": PACK_ID,
        "name": PACK_NAME,
        "version": VERSION,
        "license": {"spdx": "CC-BY-4.0", "files": ["LICENSE.txt", "NOTICE.txt"]},
        "items": [item for item, _ in items],
    }
    write_packs(args.output, manifest, items, read_text("LICENSE.txt"), read_text("NOTICE.txt"))
    for category, codes in SOURCES.items():
        print(f"  {category}\t{len(codes)}")


if __name__ == "__main__":
    main()
