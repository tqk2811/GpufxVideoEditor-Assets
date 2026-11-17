# Confetti

Colored paper confetti tumbles down over the video.

Each piece turns and flips at its own speed. Every particle is computed from the timeline time and a hash of its grid cell, so the effect keeps no state: seeking, scrubbing and split renders give the same picture.

| Parameter | Default | Meaning |
|---|---|---|
| `density` | 0.55 | Part of the grid cells that hold a particle |
| `speed` | 0.22 | Speed, frame heights per second |
| `wind` | 0.0 | Sideways drift, frame heights per second (negative blows left) |
| `size` | 1.0 | Particle size; larger particles are also fewer |
| `opacity` | 1.0 | Opacity of the particles |
| `spin` | 1.0 | How fast the pieces turn and flip |
| `seed` | 1 | Changes where the particles are |
