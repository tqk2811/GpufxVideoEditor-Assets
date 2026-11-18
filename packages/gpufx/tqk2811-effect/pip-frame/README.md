# PiP Frame

Picture in picture: shrinks the clip into a framed box with rounded corners, a border and a drop shadow, placed anywhere in the frame.

Outside the box the picture is transparent, so the tracks below show through. Unlike `rounded-corners`, the box can be any size and sit anywhere.

| Parameter | Default | Meaning |
|---|---|---|
| `position` | [0.72, 0.28] | Center of the box, 0..1 of the frame ([0, 0] = top-left) |
| `scale` | 0.4 | Box size, part of the frame |
| `radius` | 0.03 | Corner radius, part of the frame height |
| `border` | 0.006 | Border width, part of the frame height |
| `border_color` | "#ffffff" | Border color |
| `shadow` | 0.03 | Softness of the drop shadow |
| `shadow_offset` | [0.008, 0.012] | Shadow offset, part of the frame height |
| `shadow_color` | "#000000a0" | Shadow color (alpha sets its strength) |
