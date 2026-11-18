fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }
fn heat(x: f32) -> vec3f {
    // Piecewise palette: black-blue, purple, red, orange, yellow, white.
    let k = array<vec3f, 6>(vec3f(0.0, 0.0, 0.15), vec3f(0.35, 0.0, 0.6), vec3f(0.85, 0.05, 0.3),
                            vec3f(1.0, 0.45, 0.0), vec3f(1.0, 0.9, 0.1), vec3f(1.0, 1.0, 1.0));
    let p = clamp(x, 0.0, 1.0) * 5.0;
    let i = min(i32(floor(p)), 4);
    return mix(k[i], k[i + 1], p - f32(i));
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let s = textureSampleLevel(src, smp, gpufx_uv(id), params.blur).rgb;
    let l = (fx_luma(clamp(s, vec3f(0.0), vec3f(1.0))) - 0.5) * params.contrast + 0.5;
    gpufx_write(id, vec4f(mix(c.rgb, heat(l), params.amount), c.a));
}
