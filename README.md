# GpufxVideoEditor-Assets

Shader packages for [GpufxVideoEditor](https://github.com/tqk2811/GpufxVideoEditor), in the
[gpufx package format](https://github.com/tqk2811/FFmpegGpuFilter/blob/master/docs/EFFECT_FORMAT.md).

Based on AI Video Studio by Nguyễn Tất Kiểm
(<https://github.com/nguyentatkiem/ai-video-studio>). The masks, looks, transitions and the shake effect
are rewritten in WGSL from its formulas. No code, image or preview of the original project is copied.

## Packages

| Folder | Packages |
|--------|----------|
| `packages/gpufx/avs-mask/` | `mask-circle`, `mask-rounded`, `mask-rect`, `mask-heart`, `mask-star`, `mask-diamond`, `mask-blob` |
| `packages/gpufx/avs-look/` | `look-warm`, `look-cool`, `look-vivid`, `look-bw`, `look-film`, `look-fade`, `look-night`, `look-pop` |
| `packages/gpufx/avs-transition/` | `chromatic-aberration-wipe`, `curtain-reveal`, `directional-wipe`, `grid-pixelate-wipe`, `halftone-dissolve`, `iris-reveal`, `whip-pan-cut`, `zoom-through-transition` |
| `packages/gpufx/avs-effect/` | `shake` |

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

## License

The repository is [MIT](LICENSE). Each package carries `LICENSE.txt` with the full text of every licence
that applies and `NOTICE.txt` with its attribution; the packages derived from the HyperFrames blocks bundled
in AI Video Studio also carry the Apache License 2.0. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) collects them.
