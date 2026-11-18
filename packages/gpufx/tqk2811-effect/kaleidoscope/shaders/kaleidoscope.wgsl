// Seconds of the timeline clock, from the exact whole seconds and fraction. It wraps once an
// hour so f32 keeps its precision; the picture jumps once at that point.
fn fx_clock() -> f32 {
    return f32(globals.time_int % 3600) + globals.time_frac;
}
@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let aspect = globals.size.x / globals.size.y;
    let d = (uv - params.center) * vec2f(aspect, 1.0);
    let r = length(d) / max(params.zoom, 0.01);
    let seg = 6.2831853 / f32(max(params.segments, 2));
    var ang = atan2(d.y, d.x) + radians(params.rotation + params.spin * fx_clock());
    ang = ang - seg * floor(ang / seg);
    ang = min(ang, seg - ang);    // mirror every other half slice
    // Sample around the frame center, folding back so it never leaves the picture.
    var p = vec2f(0.5) + vec2f(cos(ang) / aspect, sin(ang)) * r;
    p = 1.0 - abs(1.0 - abs(p) % 2.0);
    let s = textureSampleLevel(src, smp, p, 0.0);
    gpufx_write(id, s);
}
