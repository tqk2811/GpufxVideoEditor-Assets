fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }
@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let rgb = clamp(c.rgb, vec3f(0.0), vec3f(1.0));
    let l = fx_luma(rgb);
    let w = smoothstep(0.1, 0.9, l);
    // Tint toward the shadow or highlight color while keeping the brightness.
    let tint = mix(params.shadow.rgb, params.highlight.rgb, w);
    var o = mix(rgb, tint * (l / max(fx_luma(tint), 1e-3)), params.strength * 0.5);
    o = (o - 0.5) * params.contrast + 0.5;
    gpufx_write(id, vec4f(mix(rgb, clamp(o, vec3f(0.0), vec3f(1.0)), params.amount), c.a));
}
