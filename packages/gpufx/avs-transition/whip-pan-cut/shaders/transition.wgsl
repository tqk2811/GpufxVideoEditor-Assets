// Whip pan cut. Rewritten in WGSL from the block whip-pan-cut (see NOTICE.txt).

// GSAP powerN.inOut: an exponent of N + 1.
fn ease_in_out(t: f32, power: f32) -> f32 {
    let e = power + 1.0;
    return select(1.0 - pow(2.0 * (1.0 - t), e) * 0.5, pow(2.0 * t, e) * 0.5, t < 0.5);
}

// The strip holding both clips side by side; the first clip is 0..1 and the second follows.
fn strip(x: f32, y: f32, right: bool) -> vec4f {
    if (right) {
        if (x < 0.0) { return textureSampleLevel(second, smp, vec2f(x + 1.0, y), 0.0); }
        return textureSampleLevel(first, smp, vec2f(x, y), 0.0);
    }
    if (x < 1.0) { return textureSampleLevel(first, smp, vec2f(x, y), 0.0); }
    return textureSampleLevel(second, smp, vec2f(x - 1.0, y), 0.0);
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
    let e = ease_in_out(p, 3.0);
    let uv = gpufx_uv(id);
    let right = params.direction == 1;
    let x = uv.x + select(e, -e, right);

    // Horizontal blur: 16 px of standard deviation at the middle of the whip, at 1920 wide.
    let half = select((1.0 - (p - 0.5) * 2.0), p * 2.0, p < 0.5);
    let sigma = 16.0 * half * half * half * half / 1920.0;
    var color = vec4f(0.0);
    var total = 0.0;
    for (var i = -7; i <= 7; i += 1) {
        let r = f32(i) / 7.0 * 2.5;
        let weight = exp(-0.5 * r * r);
        color += strip(x + r * sigma, uv.y, right) * weight;
        total += weight;
    }
    color /= total;

    // The hairline seam on the boundary between the clips, while the whip runs.
    let seam_x = select(1.0 - e, e, right);
    let half_width = 0.35 * 0.01 * 0.5;
    let seam = clamp((half_width - abs(uv.x - seam_x)) * globals.size.x + 0.5, 0.0, 1.0);
    let seam_in = clamp(p / (0.1 / 0.55), 0.0, 1.0);
    let seam_out = 1.0 - clamp((p - (1.0 - 0.15 / 0.55)) / (0.15 / 0.55), 0.0, 1.0);
    color = vec4f(mix(color.rgb, params.accent.rgb, seam * seam_in * seam_out * params.accent.a), color.a);
    gpufx_write(id, color);
}
