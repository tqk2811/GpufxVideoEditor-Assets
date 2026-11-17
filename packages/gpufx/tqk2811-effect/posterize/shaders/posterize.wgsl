@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let n = f32(max(params.levels, 2) - 1);
    let g = max(params.gamma, 0.01);
    let v = pow(clamp(c.rgb, vec3f(0.0), vec3f(1.0)), vec3f(1.0 / g));
    let q = pow(floor(v * n + 0.5) / n, vec3f(g));
    gpufx_write(id, vec4f(mix(c.rgb, q, params.amount), c.a));
}
