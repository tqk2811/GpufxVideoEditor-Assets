fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }
@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let rgb = clamp(c.rgb, vec3f(0.0), vec3f(1.0));
    let l = fx_luma(rgb);
    // Overlay blend of the picture with its own gray: the silver kept on the film.
    let lo = 2.0 * rgb * l;
    let hi = 1.0 - 2.0 * (1.0 - rgb) * (1.0 - l);
    let ov = mix(lo, hi, step(vec3f(0.5), vec3f(l)));
    let mixd = mix(rgb, ov, 0.7);
    var o = mix(vec3f(fx_luma(mixd)), mixd, params.saturation);
    o = (o - 0.5) * params.contrast + 0.5;
    gpufx_write(id, vec4f(mix(rgb, clamp(o, vec3f(0.0), vec3f(1.0)), params.amount), c.a));
}
