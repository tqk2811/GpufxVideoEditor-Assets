# Rain

Rain: thin slanted streaks fall fast over a slightly darker picture.

`angle` turns the whole rain; `wind` adds drift on top. Every particle is computed from the timeline time and a hash of its grid cell, so the effect keeps no state: seeking, scrubbing and split renders give the same picture.

| Parameter | Default | Meaning |
|---|---|---|
| `density` | 0.6 | Part of the grid cells that hold a particle |
| `speed` | 1.8 | Speed, frame heights per second |
| `wind` | 0.0 | Sideways drift, frame heights per second (negative blows left) |
| `size` | 1.0 | Particle size; larger particles are also fewer |
| `opacity` | 0.5 | Opacity of the particles |
| `angle` | 12 | Slant of the rain in degrees (positive falls to the right) |
| `dim` | 0.15 | Darkens the picture under the rain |
| `color` | "#c8d6e6" | Rain color |
| `seed` | 1 | Changes where the particles are |
