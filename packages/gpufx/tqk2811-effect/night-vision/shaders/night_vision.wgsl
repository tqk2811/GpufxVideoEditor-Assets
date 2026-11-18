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
fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }
@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let uv = gpufx_uv(id);
    let aspect = globals.size.x / globals.size.y;
    let tick = i32(floor(fx_clock() * 24.0));
    let gid = vec2i(id.xy);
    var l = fx_luma(clamp(c.rgb, vec3f(0.0), vec3f(1.0)));
    l = 1.0 - exp(-l * params.gain * 1.5);
    l += (fx_rand(gid.x, gid.y, tick) - 0.5) * params.noise * 2.0;
    l *= 0.92 + 0.08 * sin(uv.y * globals.size.y * 1.6);
    let d = length((uv - 0.5) * vec2f(aspect, 1.0)) / 0.7;
    l *= mix(1.0, 1.0 - smoothstep(0.75, 1.05, d), params.vignette);
    let o = clamp(params.tint.rgb * l + vec3f(max(l - 0.85, 0.0)), vec3f(0.0), vec3f(1.0));
    gpufx_write(id, vec4f(mix(c.rgb, o, params.amount), c.a));
}
