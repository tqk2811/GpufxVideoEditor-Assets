// Black and White look: the CSS filter chain `grayscale(1) contrast(1.15)` of AI Video Studio (MIT), step by step in sRGB
// as the CSS filter functions work, with the matrices of the Filter Effects specification.
// `amount` moves every filter argument between its identity (0) and the look (1).

fn grayscale(c: vec3f, amount: f32) -> vec3f {
    let s = 1.0 - clamp(amount, 0.0, 1.0);
    return clamp(vec3f(
        dot(c, vec3f(0.2126 + 0.7874 * s, 0.7152 - 0.7152 * s, 0.0722 - 0.0722 * s)),
        dot(c, vec3f(0.2126 - 0.2126 * s, 0.7152 + 0.2848 * s, 0.0722 - 0.0722 * s)),
        dot(c, vec3f(0.2126 - 0.2126 * s, 0.7152 - 0.7152 * s, 0.0722 + 0.9278 * s))), vec3f(0.0), vec3f(1.0));
}

fn contrast(c: vec3f, k: f32) -> vec3f {
    return clamp((c - vec3f(0.5)) * k + vec3f(0.5), vec3f(0.0), vec3f(1.0));
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
    rgb = grayscale(rgb, mix(0.0, 1.0000, a));
    rgb = contrast(rgb, mix(1.0, 1.1500, a));
    gpufx_write(id, vec4f(rgb, c.a));
}
