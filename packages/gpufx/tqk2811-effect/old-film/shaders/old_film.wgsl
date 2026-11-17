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

fn sepia_tone(c: vec3f) -> vec3f {
    return vec3f(dot(c, vec3f(0.393, 0.769, 0.189)), dot(c, vec3f(0.349, 0.686, 0.168)), dot(c, vec3f(0.272, 0.534, 0.131)));
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let size = globals.size;
    let px = vec2f(id.xy) + 0.5;
    let ft = i32(floor(fx_clock() * max(params.fps, 1.0)));   // film frame number
    var uv = gpufx_uv(id);
    uv.y += (fx_rand(ft, 1, 0) - 0.5) * 0.006 * params.weave;
    let c = textureSampleLevel(src, smp, uv, 0.0);
    var rgb = mix(c.rgb, min(sepia_tone(vec3f(fx_luma(c.rgb))), vec3f(1.0)), clamp(params.sepia, 0.0, 1.0));
    rgb *= 1.0 + (fx_rand(ft, 2, 0) - 0.5) * 2.0 * params.flicker;
    // Scratches: up to three thin vertical lines per film frame, broken along their length.
    for (var k = 0; k < 3; k++) {
        if (fx_rand(ft, 10, k) < params.scratches * 0.6) {
            let x = fx_rand(ft, 11, k) * size.x;
            let w = 0.6 + fx_rand(ft, 12, k) * 1.2;
            let dx = (px.x - x) / w;
            let seg = fx_rand(ft * 7 + k, i32(px.y / size.y * 6.0), 13);
            let dark = select(0.0, 0.5, seg > 0.25) * exp(-dx * dx);
            rgb = mix(rgb, select(vec3f(0.05), vec3f(0.95), fx_rand(ft, 14, k) > 0.6), dark);
        }
    }
    // Dust: small dark or light blots.
    let specks = i32(params.dust * 8.0);
    for (var k = 0; k < specks; k++) {
        let p = vec2f(fx_rand(ft, 20, k), fx_rand(ft, 21, k)) * size;
        let r = (1.0 + fx_rand(ft, 22, k) * 3.0) * size.y / 720.0;
        let d = length((px - p) / vec2f(1.0, 0.6 + fx_rand(ft, 23, k)));
        let m = 1.0 - smoothstep(r * 0.6, r, d);
        rgb = mix(rgb, select(vec3f(0.08), vec3f(0.9), fx_rand(ft, 24, k) > 0.7), m * 0.8);
    }
    let gid = vec2i(id.xy);
    rgb += (fx_rand(gid.x, gid.y, ft) - 0.5) * 2.0 * params.grain;
    let q = (gpufx_uv(id) - 0.5) * vec2f(size.x / size.y, 1.0);
    rgb *= 1.0 - params.vignette * pow(clamp(length(q) * 1.2, 0.0, 1.5), 2.5);
    gpufx_write(id, vec4f(rgb, c.a));
}
