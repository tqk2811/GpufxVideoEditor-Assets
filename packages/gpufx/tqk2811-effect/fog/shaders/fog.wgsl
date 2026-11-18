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
fn vnoise(p: vec2f, salt: i32) -> f32 {
    let i = floor(p);
    let f = p - i;
    let u = f * f * (3.0 - 2.0 * f);
    let ii = vec2i(i);
    let a = fx_rand(ii.x, ii.y, salt);
    let b = fx_rand(ii.x + 1, ii.y, salt);
    let c = fx_rand(ii.x, ii.y + 1, salt);
    let d = fx_rand(ii.x + 1, ii.y + 1, salt);
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let aspect = globals.size.x / globals.size.y;
    let t = fx_clock();
    var p = vec2f(uv.x * aspect, uv.y) * 3.0 / params.scale;
    // Five octaves, each drifting a little faster than the one below.
    var n = 0.0;
    var amp = 0.5;
    for (var k = 0; k < 5; k++) {
        let q = p + vec2f(-t * params.speed * 3.0 / params.scale * (1.0 + f32(k) * 0.35), t * 0.01 * f32(k));
        n += vnoise(q, params.seed * 31 + k) * amp;
        p = p * 2.03 + vec2f(1.7, 9.2);
        amp *= 0.5;
    }
    let h = mix(smoothstep(1.0 - params.height - 0.25, 1.0, uv.y), 1.0, params.height * params.height);
    let fog = clamp(smoothstep(0.3, 0.8, n) * params.density * h * 1.4, 0.0, 1.0);
    let c = textureLoad(src, vec2i(id.xy), 0);
    gpufx_write(id, vec4f(mix(c.rgb, params.color.rgb, fog), c.a));
}
