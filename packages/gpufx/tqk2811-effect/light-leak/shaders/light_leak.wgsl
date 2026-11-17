// Integer hash (PCG output step): the same numbers on every GPU.
fn fx_hash(x: u32) -> u32 {
    let v = x * 747796405u + 2891336453u;
    let w = ((v >> ((v >> 28u) + 4u)) ^ v) * 277803737u;
    return (w >> 22u) ^ w;
}

// Random number in [0, 1) of three integers.
fn fx_rand(a: i32, b: i32, c: i32) -> f32 {
    let h = fx_hash(bitcast<u32>(a) ^ fx_hash(bitcast<u32>(b) ^ fx_hash(bitcast<u32>(c))));
    return f32(h >> 8u) / 16777216.0;
}
// Seconds of the timeline clock, from the exact whole seconds and fraction. It wraps once an
// hour so f32 keeps its precision; the picture jumps once at that point.
fn fx_clock() -> f32 {
    return f32(globals.time_int % 3600) + globals.time_frac;
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let aspect = globals.size.x / globals.size.y;
    let uv = gpufx_uv(id);
    let p = vec2f(uv.x * aspect, uv.y);
    let t = fx_clock() * params.speed;
    var leak = vec3f(0.0);
    // Four soft patches circling just inside the frame edges.
    for (var k = 0; k < 4; k++) {
        let r0 = fx_rand(params.seed, k, 1);
        let r1 = fx_rand(params.seed, k, 2);
        let r2 = fx_rand(params.seed, k, 3);
        let ang = r0 * 6.2831853 + t * (0.6 + r1) * select(-1.0, 1.0, r2 > 0.5);
        let center = vec2f(0.5 * aspect, 0.5) + vec2f(cos(ang) * 0.62 * aspect, sin(ang) * 0.62);
        let rad = params.size * (0.6 + 0.8 * r1);
        let d = length(p - center) / max(rad, 1e-3);
        let pulse = 0.65 + 0.35 * sin(t * 4.0 * (0.5 + r2) + r0 * 6.2831853);
        leak += mix(params.color1.rgb, params.color2.rgb, r2) * exp(-d * d * 2.0) * pulse;
    }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let g = clamp(leak * params.intensity, vec3f(0.0), vec3f(1.0));
    gpufx_write(id, vec4f(1.0 - (1.0 - c.rgb) * (1.0 - g), c.a));
}
