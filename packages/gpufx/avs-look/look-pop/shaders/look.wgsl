// Pop look: the CSS filter chain `saturate(1.6) contrast(1.15) brightness(1.04)` of AI Video Studio (MIT), step by step in sRGB
// as the CSS filter functions work, with the matrices of the Filter Effects specification.
// `amount` moves every filter argument between its identity (0) and the look (1).

fn saturate_color(c: vec3f, s: f32) -> vec3f {
    return clamp(vec3f(
        dot(c, vec3f(0.213 + 0.787 * s, 0.715 - 0.715 * s, 0.072 - 0.072 * s)),
        dot(c, vec3f(0.213 - 0.213 * s, 0.715 + 0.285 * s, 0.072 - 0.072 * s)),
        dot(c, vec3f(0.213 - 0.213 * s, 0.715 - 0.715 * s, 0.072 + 0.928 * s))), vec3f(0.0), vec3f(1.0));
}

fn contrast(c: vec3f, k: f32) -> vec3f {
    return clamp((c - vec3f(0.5)) * k + vec3f(0.5), vec3f(0.0), vec3f(1.0));
}

fn brightness(c: vec3f, b: f32) -> vec3f {
    return clamp(c * b, vec3f(0.0), vec3f(1.0));
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
    rgb = saturate_color(rgb, mix(1.0, 1.6000, a));
    rgb = contrast(rgb, mix(1.0, 1.1500, a));
    rgb = brightness(rgb, mix(1.0, 1.0400, a));
    gpufx_write(id, vec4f(rgb, c.a));
}
