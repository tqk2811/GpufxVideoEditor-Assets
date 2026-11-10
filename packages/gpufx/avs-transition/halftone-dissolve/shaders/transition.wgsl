// Halftone dissolve. Rewritten in WGSL from the block halftone-dissolve (see NOTICE.txt).

// GSAP powerN.inOut: an exponent of N + 1.
fn ease_in_out(t: f32, power: f32) -> f32 {
    let e = power + 1.0;
    return select(1.0 - pow(2.0 * (1.0 - t), e) * 0.5, pow(2.0 * t, e) * 0.5, t < 0.5);
}

fn dot_random(col: i32, row: i32, salt: u32) -> f32 {
    var h = (u32(col) * 73856093u) ^ (u32(row) * 19349663u) ^ salt;
    h = (h ^ (h >> 13u)) * 1274126177u;
    h = h ^ (h >> 16u);
    return f32(h >> 8u) / 16777216.0;
}

fn smooth01(v: f32) -> f32 {
    return v * v * (3.0 - 2.0 * v);
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let p = clamp(params.progress, 0.0, 1.0);
    if (p <= 0.0) {
        gpufx_write(id, textureLoad(first, vec2i(id.xy), 0));
        return;
    }
    if (p >= 1.0) {
        gpufx_write(id, textureLoad(second, vec2i(id.xy), 0));
        return;
    }
    let e = ease_in_out(p, 1.0);
    let uv = gpufx_uv(id);
    let size = globals.size;
    let pos = uv * size;
    var pitch = 1.0 / 30.0;
    if (params.dot_size == 0) { pitch = 1.0 / 44.0; }
    if (params.dot_size == 2) { pitch = 1.0 / 20.0; }
    let cell = max(8.0, size.x * pitch);
    let r_max = cell * 0.78;
    let max_dist = length(size * 0.5);

    var window = 0.0;
    var ink = 0.0;
    let row0 = i32(floor(pos.y / cell));
    for (var row = row0 - 1; row <= row0 + 1; row += 1) {
        let offset = select(0.75, 0.25, ((row % 2) + 2) % 2 == 0);
        let col0 = i32(floor(pos.x / cell - offset));
        for (var col = col0 - 1; col <= col0 + 1; col += 1) {
            let centre = vec2f((f32(col) + offset) * cell, (f32(row) + 0.5) * cell);
            var base = centre.x / size.x;
            if (params.direction == 1) { base = length(centre - size * 0.5) / max_dist; }
            if (params.direction == 2) { base = dot_random(col, row, 0x4a17f03du); }
            let jitter = select((dot_random(col, row, 0x9e3779b9u) - 0.5) * 0.22, 0.0, params.direction == 2);
            let threshold = clamp(base + jitter, 0.0, 1.0) * 0.62;
            let d = distance(pos, centre);
            let rw = r_max * smooth01(clamp((e - threshold) / 0.38, 0.0, 1.0));
            let ri = r_max * smooth01(clamp((e + 0.07 - threshold) / 0.38, 0.0, 1.0));
            if (rw > 0.25) { window = max(window, clamp(rw - d + 0.5, 0.0, 1.0)); }
            if (ri > 0.25) { ink = max(ink, clamp(ri - d + 0.5, 0.0, 1.0)); }
        }
    }

    // First clip, then the ink dots, then the second clip through the windows.
    var color = textureSampleLevel(first, smp, uv, 0.0);
    color = vec4f(mix(color.rgb, params.accent.rgb, ink * params.accent.a), color.a);
    color = mix(color, textureSampleLevel(second, smp, uv, 0.0), window);
    gpufx_write(id, color);
}
