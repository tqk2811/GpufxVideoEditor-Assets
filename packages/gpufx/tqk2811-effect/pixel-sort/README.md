# Pixel Sort

Pixel sorting look: bright runs of pixels melt into streaks along one direction, as in glitch art.

Only pixels at least as bright as `threshold` are moved; dark parts stay as they are.

| Parameter | Default | Meaning |
|---|---|---|
| `threshold` | 0.3 | Brightness where streaks start |
| `length` | 0.35 | Longest streak, part of the frame |
| `angle` | 90 | Direction of the streaks in degrees (90 = down) |
| `amount` | 1 | Strength of the effect |
