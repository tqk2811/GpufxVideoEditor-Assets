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
    let uv = gpufx_uv(id);
    let c = textureLoad(src, vec2i(id.xy), 0);
    let tick = i32(floor(fx_clock() * params.rate));
    // Bursts: whole frames on or off, in runs decided per half second.
    let burst = fx_rand(i32(floor(fx_clock() * 2.0)), params.seed, 91) < params.bursts;
    if (!burst || params.amount <= 0.0) { gpufx_write(id, c); return; }
    let rows = max(1.0 / params.block, 1.0);
    let row = i32(floor(uv.y * rows));
    let cols = i32(floor(uv.x * mix(1.0, 6.0, fx_rand(row, tick, params.seed + 3))));
    let r0 = fx_rand(row, tick, params.seed);
    let r1 = fx_rand(row, cols + tick * 13, params.seed + 1);
    var o = c.rgb;
    if (r0 < params.amount * 0.5) {
        let dx = (r1 - 0.5) * 2.0 * params.shift;
        let split = params.shift * 0.25 * fx_rand(row, tick, params.seed + 2);
        o = vec3f(textureSampleLevel(src, smp, vec2f(uv.x + dx + split, uv.y), 0.0).r,
                  textureSampleLevel(src, smp, vec2f(uv.x + dx, uv.y), 0.0).g,
                  textureSampleLevel(src, smp, vec2f(uv.x + dx - split, uv.y), 0.0).b);
        if (r1 > 0.93) {
            // A block frozen into one flat, oversaturated color.
            let s = textureSampleLevel(src, smp, vec2f(fract(r1 * 7.0), uv.y), 0.0).rgb;
            o = clamp((s - 0.5) * 2.5 + 0.5, vec3f(0.0), vec3f(1.0));
        }
    }
    gpufx_write(id, vec4f(o, c.a));
}
