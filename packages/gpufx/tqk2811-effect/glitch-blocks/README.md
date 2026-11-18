# Glitch Blocks

Digital glitch: blocks of the picture jump sideways, split their colors or freeze into flat color for a few frames at a time.

The pattern changes `rate` times a second on the timeline clock, and glitches come in bursts so that the clean picture shows between them.

| Parameter | Default | Meaning |
|---|---|---|
| `amount` | 0.5 | How many blocks glitch |
| `shift` | 0.06 | Largest sideways jump, part of the frame width |
| `block` | 0.08 | Block height, part of the frame height |
| `rate` | 8 | Glitch changes per second |
| `bursts` | 0.5 | Part of the time that glitches (0 = never, 1 = always) |
| `seed` | 1 | Changes the pattern |
