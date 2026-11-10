// Cool look: the CSS filter chain `saturate(1.05) hue-rotate(12deg) brightness(1.02)` of AI Video Studio (MIT), step by step in sRGB
// as the CSS filter functions work, with the matrices of the Filter Effects specification.
// `amount` moves every filter argument between its identity (0) and the look (1).

fn saturate_color(c: vec3f, s: f32) -> vec3f {
    return clamp(vec3f(
        dot(c, vec3f(0.213 + 0.787 * s, 0.715 - 0.715 * s, 0.072 - 0.072 * s)),
        dot(c, vec3f(0.213 - 0.213 * s, 0.715 + 0.285 * s, 0.072 - 0.072 * s)),
        dot(c, vec3f(0.213 - 0.213 * s, 0.715 - 0.715 * s, 0.072 + 0.928 * s))), vec3f(0.0), vec3f(1.0));
}

fn hue_rotate(c: vec3f, degrees: f32) -> vec3f {
    let a = radians(degrees);
    let k = cos(a);
    let n = sin(a);
    return clamp(vec3f(
        dot(c, vec3f(0.213 + k * 0.787 - n * 0.213, 0.715 - k * 0.715 - n * 0.715, 0.072 - k * 0.072 + n * 0.928)),
        dot(c, vec3f(0.213 - k * 0.213 + n * 0.143, 0.715 + k * 0.285 + n * 0.140, 0.072 - k * 0.072 - n * 0.283)),
        dot(c, vec3f(0.213 - k * 0.213 - n * 0.787, 0.715 - k * 0.715 + n * 0.715, 0.072 + k * 0.928 + n * 0.072))), vec3f(0.0), vec3f(1.0));
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
    rgb = saturate_color(rgb, mix(1.0, 1.0500, a));
    rgb = hue_rotate(rgb, mix(0.0, 12.0000, a));
    rgb = brightness(rgb, mix(1.0, 1.0200, a));
    gpufx_write(id, vec4f(rgb, c.a));
}
