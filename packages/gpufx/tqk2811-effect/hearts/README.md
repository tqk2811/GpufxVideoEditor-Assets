# Hearts

Hearts float up over the video, swaying and tilting.

Every particle is computed from the timeline time and a hash of its grid cell, so the effect keeps no state: seeking, scrubbing and split renders give the same picture.

| Parameter | Default | Meaning |
|---|---|---|
| `density` | 0.25 | Part of the grid cells that hold a particle |
| `speed` | 0.1 | Speed, frame heights per second |
| `wind` | 0.0 | Sideways drift, frame heights per second (negative blows left) |
| `size` | 1.0 | Particle size; larger particles are also fewer |
| `opacity` | 0.9 | Opacity of the particles |
| `rise` | true | Hearts rise; off makes them fall |
| `color` | "#ff4d6d" | First heart color |
| `color2` | "#ff9ebb" | Second heart color |
| `seed` | 1 | Changes where the particles are |
