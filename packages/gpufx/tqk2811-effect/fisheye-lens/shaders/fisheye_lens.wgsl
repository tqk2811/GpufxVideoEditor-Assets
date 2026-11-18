@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let aspect = globals.size.x / globals.size.y;
    let d = (uv - params.center) * vec2f(aspect, 1.0);
    let half_diag = 0.5 * length(vec2f(aspect, 1.0));
    let r = length(d) / half_diag;
    // Barrel mapping: the radius read from the picture shrinks near the middle.
    let k = params.strength;
    let rr = r * (1.0 - k * 0.5 + k * 0.5 * r * r) / max(params.zoom, 0.01);
    let q = params.center + select(vec2f(0.0), d / max(r, 1e-6) * rr * half_diag / vec2f(aspect, 1.0), r > 1e-6);
    var s = textureSampleLevel(src, smp, clamp(q, vec2f(0.0), vec2f(1.0)), 0.0);
    let rim = 1.0 - params.rim * smoothstep(0.55, 1.0, r);
    gpufx_write(id, vec4f(s.rgb * rim, s.a));
}
