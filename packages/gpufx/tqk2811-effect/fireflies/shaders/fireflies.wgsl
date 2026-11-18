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
const CELLS: f32 = 7.0;   // cells per frame height

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let aspect = globals.size.x / globals.size.y;
    let uv = gpufx_uv(id);
    let t = fx_clock() * params.speed;
    let q = vec2f(uv.x * aspect, uv.y) * CELLS;
    let base = floor(q);
    var glow = 0.0;
    // Each firefly stays near its own cell, so the 3x3 neighbors hold every one that can reach.
    for (var dy = -1; dy <= 1; dy++) {
        for (var dx = -1; dx <= 1; dx++) {
            let cell = base + vec2f(f32(dx), f32(dy));
            let ci = vec2i(cell);
            let salt = params.seed * 104729;
            if (fx_rand(ci.x, ci.y, salt) >= params.density) { continue; }
            let r0 = fx_rand(ci.x, ci.y, salt + 1);
            let r1 = fx_rand(ci.x, ci.y, salt + 2);
            let r2 = fx_rand(ci.x, ci.y, salt + 3);
            let wander = vec2f(sin(t * (0.7 + r0) + r1 * 6.28) + 0.5 * sin(t * 1.9 * (0.5 + r2) + r0 * 3.0),
                               cos(t * (0.6 + r2) + r0 * 6.28) + 0.5 * cos(t * 1.7 * (0.5 + r1) + r2 * 3.0)) * 0.35;
            let ctr = cell + vec2f(0.5) + wander;
            let d = length(q - ctr) / (0.06 * params.size);
            let pulse = smoothstep(-0.2, 0.8, sin(fx_clock() * (1.0 + 2.0 * r1) + r0 * 6.28));
            glow += (exp(-d * d) + 0.25 * exp(-d * d * 0.08)) * pulse;
        }
    }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let g = clamp(params.color.rgb * glow * params.brightness, vec3f(0.0), vec3f(1.0));
    gpufx_write(id, vec4f(1.0 - (1.0 - c.rgb) * (1.0 - g), c.a));
}
