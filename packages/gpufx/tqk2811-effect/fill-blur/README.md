# Fill Blur

Fills the empty sides around a video of another shape with a blurred, enlarged copy of itself, as for a vertical phone video in a wide frame.

With `aspect` above 0 the effect changes the size of the clip: a 1080x1920 clip comes out 3414x1920 at 16:9 (the width is capped at 8192). With `aspect` 0 the size stays and `scale` below 1 shows the background around a smaller picture. The output is opaque.

| Parameter | Default | Meaning |
|---|---|---|
| `aspect` | 1.7777778 | Width / height of the output (16:9 = 1.778); 0 keeps the size of the clip and shrinks the picture by `scale` |
| `scale` | 1 | Size of the sharp picture inside the frame |
| `blur` | 4 | Blur of the background, as a mip level (each step doubles it) |
| `dim` | 0.3 | Darkens the background |
| `zoom` | 1.1 | Extra enlargement of the background |
