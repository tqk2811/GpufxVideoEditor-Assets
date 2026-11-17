# Snow

Snowflakes drift down over the video in four layers of depth.

Near flakes are bigger, brighter and faster. Every particle is computed from the timeline time and a hash of its grid cell, so the effect keeps no state: seeking, scrubbing and split renders give the same picture.

| Parameter | Default | Meaning |
|---|---|---|
| `density` | 0.5 | Part of the grid cells that hold a particle |
| `speed` | 0.12 | Speed, frame heights per second |
| `wind` | 0.03 | Sideways drift, frame heights per second (negative blows left) |
| `size` | 1.0 | Particle size; larger particles are also fewer |
| `opacity` | 0.9 | Opacity of the particles |
| `color` | "#ffffff" | Snow color |
| `seed` | 1 | Changes where the particles are |
