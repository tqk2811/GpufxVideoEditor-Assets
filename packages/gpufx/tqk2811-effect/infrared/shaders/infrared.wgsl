fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }
@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let rgb = clamp(c.rgb, vec3f(0.0), vec3f(1.0));
    // Green carries most of the infrared light, blue almost none.
    let ir = clamp(rgb.g * 1.1 + rgb.r * 0.3 - rgb.b * 0.4, 0.0, 1.0);
    let uv = gpufx_uv(id);
    let s = textureSampleLevel(src, smp, uv, 4.0).rgb;
    let irs = clamp(s.g * 1.1 + s.r * 0.3 - s.b * 0.4, 0.0, 1.0);
    let bw = 1.0 - (1.0 - ir) * (1.0 - irs * params.glow);
    let fc = vec3f(clamp(ir * 1.1 + 0.1, 0.0, 1.0), rgb.r * 0.8, rgb.g * 0.9 + 0.1 * bw);
    var o = mix(vec3f(bw), mix(fc, fc + bw * 0.3, params.glow), params.color);
    gpufx_write(id, vec4f(mix(rgb, clamp(o, vec3f(0.0), vec3f(1.0)), params.amount), c.a));
}
