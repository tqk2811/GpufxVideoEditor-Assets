// Film look: the CSS filter chain `sepia(.3) contrast(1.08) saturate(.85)` of AI Video Studio (MIT), step by step in sRGB
// as the CSS filter functions work, with the matrices of the Filter Effects specification.
// `amount` moves every filter argument between its identity (0) and the look (1).

fn sepia(c: vec3f, amount: f32) -> vec3f {
    let s = 1.0 - clamp(amount, 0.0, 1.0);
    return clamp(vec3f(
        dot(c, vec3f(0.393 + 0.607 * s, 0.769 - 0.769 * s, 0.189 - 0.189 * s)),
        dot(c, vec3f(0.349 - 0.349 * s, 0.686 + 0.314 * s, 0.168 - 0.168 * s)),
        dot(c, vec3f(0.272 - 0.272 * s, 0.534 - 0.534 * s, 0.131 + 0.869 * s))), vec3f(0.0), vec3f(1.0));
}

fn contrast(c: vec3f, k: f32) -> vec3f {
    return clamp((c - vec3f(0.5)) * k + vec3f(0.5), vec3f(0.0), vec3f(1.0));
}

fn saturate_color(c: vec3f, s: f32) -> vec3f {
    return clamp(vec3f(
        dot(c, vec3f(0.213 + 0.787 * s, 0.715 - 0.715 * s, 0.072 - 0.072 * s)),
        dot(c, vec3f(0.213 - 0.213 * s, 0.715 + 0.285 * s, 0.072 - 0.072 * s)),
        dot(c, vec3f(0.213 - 0.213 * s, 0.715 - 0.715 * s, 0.072 + 0.928 * s))), vec3f(0.0), vec3f(1.0));
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let a = clamp(params.amount, 0.0, 1.0);
    if (a <= 0.0) {
        gpufx_write(id, c);
        return;
    }
    var rgb = c.rgb;
    rgb = sepia(rgb, mix(0.0, 0.3000, a));
    rgb = contrast(rgb, mix(1.0, 1.0800, a));
    rgb = saturate_color(rgb, mix(1.0, 0.8500, a));
    gpufx_write(id, vec4f(rgb, c.a));
}
