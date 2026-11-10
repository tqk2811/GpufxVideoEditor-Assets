// Chromatic aberration wipe. Rewritten in WGSL from the timing and formulas of the block chromatic-aberration-wipe (see NOTICE.txt).
// A 0.9 s push in the source timeline; all pixel offsets are at a 1920 wide frame.

// GSAP powerN.inOut: an exponent of N + 1.
fn ease_in_out(t: f32, power: f32) -> f32 {
    let e = power + 1.0;
    return select(1.0 - pow(2.0 * (1.0 - t), e) * 0.5, pow(2.0 * t, e) * 0.5, t < 0.5);
}

fn blur_first(uv: vec2f, sigma: f32) -> vec4f {
    if (sigma < 0.25) { return textureSampleLevel(first, smp, uv, 0.0); }
    var sum = vec4f(0.0);
    var total = 0.0;
    for (var i = 0u; i < 16u; i += 1u) {
        let r = sqrt((f32(i) + 0.5) / 16.0) * 2.5;
        let angle = f32(i) * 2.3999632;
        let offset = vec2f(cos(angle), sin(angle)) * r * sigma / globals.size;
        let weight = exp(-0.5 * r * r);
        sum += textureSampleLevel(first, smp, uv + offset, 0.0) * weight;
        total += weight;
    }
    return sum / total;
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
    let t = p * 0.9;
    let e = ease_in_out(p, 3.0);
    let uv = gpufx_uv(id);
    let to_uv_scale = vec2f(1.0 / 1920.0, globals.size.x / (1920.0 * globals.size.y));
    let mode = params.direction;
    var axis = vec2f(1.0, 0.0);
    if (mode == 1) { axis = vec2f(-1.0, 0.0); }
    if (mode == 2) { axis = vec2f(0.0, 1.0); }
    if (mode == 3) { axis = vec2f(0.0, -1.0); }
    let depth = 1.0;

    let from_offset = axis * (-70.0 * e * depth) * to_uv_scale;
    let from_scale = 1.0 - 0.04 * e;
    let from_uv = vec2f(0.5) + (uv - vec2f(0.5) - from_offset) / from_scale;
    var color = blur_first(from_uv, 5.0 * e * depth * globals.size.x / 1920.0);

    let to_offset = axis * (60.0 * (1.0 - e) * depth) * to_uv_scale;
    let to_scale = 1.04 - 0.04 * e;
    let local = vec2f(0.5) + (uv - vec2f(0.5) - to_offset) / to_scale;
    // The inset clip of the incoming clip, moving with its own transform.
    var reveal = 0.0;
    if (mode == 0) { reveal = (e - local.x) * globals.size.x / to_scale; }
    if (mode == 1) { reveal = (local.x - (1.0 - e)) * globals.size.x / to_scale; }
    if (mode == 2) { reveal = (local.y - (1.0 - e)) * globals.size.y / to_scale; }
    if (mode == 3) { reveal = (e - local.y) * globals.size.y / to_scale; }
    let cover = clamp(reveal + 0.5, 0.0, 1.0);
    if (cover > 0.0) {
        color = mix(color, textureSampleLevel(second, smp, local, 0.0), cover);
    }

    // The bright band sweeping across, as `mix-blend-mode: screen` with white.
    let band_time = clamp((t - 0.18) / 0.58, 0.0, 1.0);
    let band_start = -1.1 + 2.2 * ease_in_out(band_time, 2.0);
    let band_u = uv.x - band_start;
    let band = 0.75 * max(0.0, 1.0 - abs(2.0 * band_u - 1.0));
    color = vec4f(color.rgb + band * (vec3f(1.0) - color.rgb), color.a);

    // The red/cyan strobe: on twice, 0.07 s each, as `steps(1)` with yoyo gives.
    let strobe = (t >= 0.355 && t < 0.425) || (t >= 0.495 && t < 0.565);
    if (strobe) {
        let strength = params.aberration;
        let u = uv.x - 16.0 * strength / 1920.0;
        if (u >= 0.0 && u <= 1.0) {
            let opacity = min(strength, 1.0);
            let a = opacity * 0.35 * abs(1.0 - 2.0 * u);
            let tint = select(vec3f(0.133, 0.827, 0.933), vec3f(0.937, 0.267, 0.267), u < 0.5);
            color = vec4f(mix(color.rgb, tint, a), color.a);
        }
    }
    gpufx_write(id, color);
}
