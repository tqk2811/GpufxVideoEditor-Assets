# CRT Scanlines

Old CRT screen: curved glass, scanlines, an RGB phosphor mask and dark corners.

The corners outside the curved glass take the `border` color.

| Parameter | Default | Meaning |
|---|---|---|
| `curvature` | 0.15 | Bulge of the glass |
| `lines` | 0 | Number of scanlines; 0 is one every 3 pixels |
| `scanlines` | 0.5 | Darkness of the gaps between scanlines |
| `mask` | 0.3 | Strength of the RGB phosphor stripes |
| `vignette` | 0.4 | Darkening of the corners |
| `brightness` | 1.15 | Brightness, to make up for the dark gaps |
| `border` | "#000000" | Color outside the curved screen |
