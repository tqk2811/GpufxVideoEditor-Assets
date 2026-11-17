# Halftone

Printed halftone: the picture becomes a grid of ink dots on paper.

With `colored` on, each dot takes the most saturated version of its cell's color.

| Parameter | Default | Meaning |
|---|---|---|
| `size` | 8 | Dot spacing in pixels |
| `angle` | 45 | Angle of the dot grid in degrees |
| `ink` | "#1a1a1a" | Ink color |
| `paper` | "#f4efe4" | Paper color |
| `colored` | false | Draw each dot in the picture's own color instead of the ink |
| `amount` | 1 | Strength: 0 is the original picture, 1 the full effect |
