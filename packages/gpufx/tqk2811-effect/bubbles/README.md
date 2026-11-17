# Bubbles

Soap bubbles rise over the video, each with a thin rim and a highlight.

Every particle is computed from the timeline time and a hash of its grid cell, so the effect keeps no state: seeking, scrubbing and split renders give the same picture.

| Parameter | Default | Meaning |
|---|---|---|
| `density` | 0.35 | Part of the grid cells that hold a particle |
| `speed` | 0.08 | Speed, frame heights per second |
| `wind` | 0.0 | Sideways drift, frame heights per second (negative blows left) |
| `size` | 1.0 | Particle size; larger particles are also fewer |
| `opacity` | 0.9 | Opacity of the particles |
| `color` | "#dff3ff" | Bubble color |
| `seed` | 1 | Changes where the particles are |
