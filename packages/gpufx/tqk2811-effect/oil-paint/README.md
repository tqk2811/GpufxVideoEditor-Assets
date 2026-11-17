# Oil Paint

Oil painting: a Kuwahara filter flattens the picture into brush-like patches while keeping the edges.

Costs 4 x (radius + 1)^2 reads per pixel: radius 8 is 324.

| Parameter | Default | Meaning |
|---|---|---|
| `radius` | 5 | Brush size in pixels; larger is slower |
| `amount` | 1 | Strength: 0 is the original picture, 1 the full effect |
