// Grid pixelate wipe. Rewritten in WGSL from the block grid-pixelate-wipe (see NOTICE.txt).
// The cells cover the first clip from the center of the cell list and reveal the second from its ends.

// GSAP powerN.inOut: an exponent of N + 1.
fn ease_in_out(t: f32, power: f32) -> f32 {
    let e = power + 1.0;
    return select(1.0 - pow(2.0 * (1.0 - t), e) * 0.5, pow(2.0 * t, e) * 0.5, t < 0.5);
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
    let uv = gpufx_uv(id);
    let cols = max(params.cols, 1);
    let rows = max(params.rows, 1);
    let grid = vec2f(f32(cols), f32(rows));
    let cell_uv = uv * grid;
    let cell = min(vec2i(cell_uv), vec2i(cols - 1, rows - 1));
    let local = cell_uv - vec2f(cell);
    let count = f32(cols * rows);
    let index = f32(cell.y * cols + cell.x);
    // GSAP stagger distance over the list of cells, as the source has no grid option.
    let middle = (count - 1.0) * 0.5;
    let from_center = abs(index - middle) / max(middle, 1.0);

    var scale = 0.0;
    if (p < 0.5) {
        let t = clamp((p * 2.0 - from_center * 0.5) / 0.5, 0.0, 1.0);
        scale = ease_in_out(t, 2.0);
    } else {
        let t = clamp(((p - 0.5) * 2.0 - (1.0 - from_center) * 0.5) / 0.5, 0.0, 1.0);
        scale = 1.0 - ease_in_out(t, 2.0);
    }

    let pixels = globals.size / grid;
    let edge = (vec2f(scale * 0.5) - abs(local - vec2f(0.5))) * pixels;
    let cover = clamp(min(edge.x, edge.y) + 0.5, 0.0, 1.0);
    var color: vec4f;
    if (p < 0.5) {
        color = textureSampleLevel(first, smp, uv, 0.0);
    } else {
        color = textureSampleLevel(second, smp, uv, 0.0);
    }
    gpufx_write(id, mix(color, vec4f(params.color.rgb, 1.0), cover * params.color.a));
}
