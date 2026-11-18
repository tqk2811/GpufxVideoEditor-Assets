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
// Value noise on a pixel grid of `size`, smooth between the grid points.
fn grain(p: vec2f, tick: i32, ch: i32) -> f32 {
    let i = floor(p);
    let f = p - i;
    let u = f * f * (3.0 - 2.0 * f);
    let ii = vec2i(i);
    let a = fx_rand(ii.x, ii.y, tick * 3 + ch);
    let b = fx_rand(ii.x + 1, ii.y, tick * 3 + ch);
    let c = fx_rand(ii.x, ii.y + 1, tick * 3 + ch);
    let d = fx_rand(ii.x + 1, ii.y + 1, tick * 3 + ch);
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y) - 0.5;
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let tick = i32(floor(fx_clock() * params.fps));
    let p = vec2f(id.xy) / max(params.size, 1.0);
    let g = grain(p, tick, 0);
    let gc = vec3f(grain(p, tick, 1), grain(p + 17.0, tick, 2), grain(p + 41.0, tick, 0));
    let n = mix(vec3f(g), gc, params.color) * 2.4;
    let l = fx_luma(clamp(c.rgb, vec3f(0.0), vec3f(1.0)));
    let w = 4.0 * l * (1.0 - l) * 0.75 + 0.25;
    gpufx_write(id, vec4f(clamp(c.rgb + n * params.strength * w, vec3f(0.0), vec3f(1.0)), c.a));
}
