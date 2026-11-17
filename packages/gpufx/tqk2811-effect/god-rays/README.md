# God Rays

God rays: shafts of light stream out from a point through the bright parts of the picture.

Works best with a bright sky or window: dark pictures cast no rays. Lower `threshold` for more rays.

| Parameter | Default | Meaning |
|---|---|---|
| `center` | [0.5, 0.15] | Where the rays come from, 0..1 of the frame ([0, 0] = top-left) |
| `intensity` | 1.0 | Brightness of the rays |
| `length` | 0.8 | Length of the rays, part of the way to the light |
| `decay` | 0.975 | How fast the rays fade along their length |
| `threshold` | 0.5 | Brightness (0..1) a pixel needs to cast rays |
| `samples` | 64 | Samples along each ray; more is smoother and slower |
| `tint` | "#fff1d6" | Color of the rays |
