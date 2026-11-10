// Iris reveal. Rewritten in WGSL from the block iris-reveal (see NOTICE.txt).

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
    let e = ease_in_out(p, 2.0);
    let uv = gpufx_uv(id);
    let size = globals.size;
    let center = vec2f(params.x, params.y) * 0.01 * size;
    let full = length(max(center, size - center)) * 1.02 + 2.0;
    let radius = e * full;
    let d = length(uv * size - center);

    var a = textureSampleLevel(first, smp, uv, 0.0);
    if (params.style == 0) {
        // The "color" register: the clip being left is dimmed and desaturated, reached at the
        // start of the pass so progress 0 is the untouched clip.
        let gray = dot(a.rgb, vec3f(0.2126, 0.7152, 0.0722)) * 0.76;
        a = vec4f(mix(a.rgb, vec3f(gray), smoothstep(0.0, 0.18, p)), a.a);
    }
    let cover = clamp(radius - d + 0.5, 0.0, 1.0);
    var color = mix(a, textureSampleLevel(second, smp, uv, 0.0), cover);

    let rim_width = max(2.0, size.x * 0.0021);
    let rim = clamp(rim_width * 0.5 - abs(d - radius) + 0.5, 0.0, 1.0);
    let rim_in = smoothstep(0.0, 0.18 / 1.1, p);
    let rim_out = 1.0 - smoothstep(1.0 - 0.24 / 1.1, 1.0, p);
    color = vec4f(mix(color.rgb, params.accent.rgb, rim * rim_in * rim_out * params.accent.a), color.a);
    gpufx_write(id, color);
}
