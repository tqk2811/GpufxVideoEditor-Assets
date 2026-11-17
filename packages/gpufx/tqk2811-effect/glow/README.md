# Glow

Bloom: the bright parts of the picture bleed soft light around them.

Uses the mip chain of the input, so the glow costs six samples per pixel whatever its radius.

| Parameter | Default | Meaning |
|---|---|---|
| `intensity` | 1.0 | Strength of the glow |
| `threshold` | 0.55 | Brightness (0..1) a pixel needs before it glows |
| `radius` | 1.0 | Spread of the glow; 1 reaches about a tenth of the frame |
| `tint` | "#ffffff" | Color the glow is multiplied by |
