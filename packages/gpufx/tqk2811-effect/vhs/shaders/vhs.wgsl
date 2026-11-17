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

fn tape(x: f32, y: f32, dx: f32) -> vec3f {
    // A little horizontal smear: the bandwidth of the tape is low.
    let a = textureSampleLevel(src, smp, vec2f(x - dx, y), 0.0).rgb;
    let b = textureSampleLevel(src, smp, vec2f(x, y), 0.0).rgb;
    let c = textureSampleLevel(src, smp, vec2f(x + dx, y), 0.0).rgb;
    return (a + 2.0 * b + c) * 0.25;
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let t = fx_clock();
    let uv = gpufx_uv(id);
    let row = uv.y;
    let line = i32(floor(row * 240.0));
    let tick = i32(floor(t * 30.0));
    var x = uv.x + (sin(row * 90.0 + t * 13.0) * 0.5 + sin(row * 17.0 - t * 7.0)) * 0.0012 * params.wobble;
    let band_y = fract(t * 0.11);
    let d = min(abs(row - band_y), 1.0 - abs(row - band_y));
    let band = exp(-d * d * 900.0) * params.tracking;
    x += band * 0.03 * (fx_rand(line, tick, 1) - 0.5);
    let px = 1.5 / globals.size.x;
    let ch = params.chroma;
    var rgb = vec3f(tape(x + ch, row, px).r, tape(x, row, px).g, tape(x - ch, row, px).b);
    let l = fx_luma(rgb);
    rgb = mix(vec3f(l), rgb, params.saturation);
    let gid = vec2i(id.xy);
    rgb += (fx_rand(gid.x, gid.y, tick) - 0.5) * 2.0 * params.noise;
    rgb = mix(rgb, vec3f(fx_rand(gid.x / 3, line, tick)), band * 0.45);
    if ((id.y & 1u) == 1u) { rgb *= 1.0 - 0.25 * params.scanlines; }
    let c = textureLoad(src, gid, 0);
    gpufx_write(id, vec4f(rgb, c.a));
}
