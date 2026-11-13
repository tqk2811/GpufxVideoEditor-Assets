# GpufxVideoEditor-Assets

Shader packages for [GpufxVideoEditor](https://github.com/tqk2811/GpufxVideoEditor), in the
[gpufx package format](https://github.com/tqk2811/FFmpegGpuFilter/blob/master/docs/EFFECT_FORMAT.md).

Based on AI Video Studio by Nguyễn Tất Kiểm
(<https://github.com/nguyentatkiem/ai-video-studio>). The masks, looks, transitions and the shake effect
are rewritten in WGSL from its formulas. `punch`, `zoom-in`, `whip`, `blur-in` and `push` read the `clip_time` and `clip_duration` parameters, which the editor fills in; a tool that does not leaves them at 0. No code, image or preview of the original project is copied.

## Packages

| Folder | Packages |
|--------|----------|
| `packages/gpufx/avs-mask/` | `mask-circle`, `mask-rounded`, `mask-rect`, `mask-heart`, `mask-star`, `mask-diamond`, `mask-blob` |
| `packages/gpufx/avs-look/` | `look-warm`, `look-cool`, `look-vivid`, `look-bw`, `look-film`, `look-fade`, `look-night`, `look-pop` |
| `packages/gpufx/avs-transition/` | `chromatic-aberration-wipe`, `curtain-reveal`, `directional-wipe`, `grid-pixelate-wipe`, `halftone-dissolve`, `iris-reveal`, `whip-pan-cut`, `zoom-through-transition` |
| `packages/gpufx/avs-effect/` | `shake`, `punch`, `zoom-in`, `whip`, `blur-in`, `push` |

Masks keep alpha: the area outside the shape is transparent, so they work on a clip placed over another
one. The `bg` parameter fills it with a color instead.

## Build

```sh
py scripts/pack.py                  # every package -> dist/<slug>.zip
py scripts/pack.py -o out look-warm # chosen packages into out/
py scripts/pack.py --notices        # rewrite THIRD_PARTY_NOTICES.md
```

`scripts/pack.py` uses only the Python standard library. Each zip has `manifest.json` at its root and is
reproducible byte for byte (sorted entries, fixed timestamps). Zips are build output and are not committed.

## Audio packs

Sound effects and music from AI Video Studio are shipped as release zips, but the audio is not in this
repository. `scripts/pack_audio.py` builds them from a checkout of that project:

```sh
py scripts/pack_audio.py --source <ai-video-studio>/assets -o dist-audio
```

It writes `sfx-<category>.zip` for every category of `sfx/catalog.json` and `music.zip` (16 zips, 339
audio files), plus `audio-packs.zip`, a plain zip holding those 16 for a single download (unpack it,
then install each inner zip). Each pack zip has `manifest.json` (format 1), `LICENSE.txt`, `NOTICE.txt` and `audio/<file>`;
audio is stored without recompression and the zips are reproducible byte for byte. Names, tags and loop
come from the catalogs; FLAC durations are read from the file header, MP3 durations from the catalog.
The licence and attribution of these packs are the MIT licence of AI Video Studio, listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Sticker pack

107 emoji as 3D PNG images, from [Fluent Emoji](https://github.com/microsoft/fluentui-emoji) by Microsoft
(MIT). The images are not in this repository. `scripts/pack_stickers.py` builds the zip from a checkout of
that project, which must be at the commit pinned in the script (`FLUENT_COMMIT`):

```sh
py -I scripts/pack_stickers.py --source <fluentui-emoji> -o dist-stickers
```

It writes `stickers.zip` with `manifest.json` (format 1, type `sticker`; items have `id`, `file`, `name`,
`tags`, `category`), `LICENSE.txt` (the Microsoft licence), `NOTICE.txt` and `images/<id>.png`. Names, tags
and categories come from the `metadata.json` of each emoji, and the zip is reproducible byte for byte. The
list of 107 emoji follows the sticker panel of AI Video Studio. Only the files in the checkout are used:
a sparse checkout of the `LICENSE` and of the 107 `assets/<Name>/` folders is enough.

## License

The repository is [MIT](LICENSE). Each package carries `LICENSE.txt` with the full text of every licence
that applies and `NOTICE.txt` with its attribution; the packages derived from the HyperFrames blocks bundled
in AI Video Studio also carry the Apache License 2.0. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) collects them.
