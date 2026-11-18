// A straight soft edge sweeps across the picture in direction `angle` (degrees, 0 = to the right,
// 90 = down); behind it the picture shows, ahead of it it is transparent. At progress 1 the whole
// picture shows unchanged.
@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let a = radians(params.angle);
    let dir = vec2f(cos(a), sin(a));
    // Project the corners on the direction so the sweep starts and ends exactly at the picture.
    let lo = min(0.0, dir.x) + min(0.0, dir.y);
    let hi = max(0.0, dir.x) + max(0.0, dir.y);
    let d = (dot(uv, dir) - lo) / max(hi - lo, 1e-4);
    let s = max(params.softness, 1e-4);
    let p = clamp(params.progress, 0.0, 1.0);
    let edge = p * (1.0 + s);
    var m = 1.0 - smoothstep(edge - s, edge, d);
    if (p >= 1.0) { m = 1.0; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    gpufx_write(id, vec4f(c.rgb, c.a * m));
}
