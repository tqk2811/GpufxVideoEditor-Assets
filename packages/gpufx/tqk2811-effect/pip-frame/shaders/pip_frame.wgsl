// Signed distance to a rounded box of half size b and corner radius r.
fn rbox(p: vec2f, b: vec2f, r: f32) -> f32 {
    let q = abs(p) - b + vec2f(r);
    return length(max(q, vec2f(0.0))) + min(max(q.x, q.y), 0.0) - r;
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let aspect = globals.size.x / globals.size.y;
    let uv = gpufx_uv(id);
    let sc = max(params.scale, 0.01);
    let half_size = vec2f(0.5 * aspect, 0.5) * sc;
    let p = (uv - params.position) * vec2f(aspect, 1.0);
    let r = min(params.radius, min(half_size.x, half_size.y));
    let d = rbox(p, half_size, r);
    let px = 1.0 / globals.size.y;
    // The whole clip, shrunk into the box.
    let q = 0.5 + (uv - params.position) / sc;
    let s = textureSampleLevel(src, smp, clamp(q, vec2f(0.0), vec2f(1.0)), log2(1.0 / sc));
    let inside = 1.0 - smoothstep(-px, px, d);
    let bw = params.border;
    let in_border = select(0.0, smoothstep(-bw - px, -bw + px, d), bw > 0.0);
    let col = mix(s.rgb, params.border_color.rgb, in_border * params.border_color.a);
    let ca = mix(s.a, 1.0, in_border * params.border_color.a) * inside;
    var acc = vec4f(col * ca, ca);
    // Drop shadow: the same box moved by the offset and blurred, under the clip.
    let ds = rbox(p - params.shadow_offset, half_size, r);
    let soft = max(params.shadow, px);
    let g = (1.0 - smoothstep(-soft, soft, ds)) * params.shadow_color.a;
    acc = acc + vec4f(params.shadow_color.rgb * g, g) * (1.0 - acc.a);
    let a = acc.a;
    gpufx_write(id, vec4f(select(vec3f(0.0), acc.rgb / max(a, 1e-6), a > 0.0), a));
}
