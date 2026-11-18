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
const CELLS: f32 = 10.0;

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let aspect = globals.size.x / globals.size.y;
    let uv = gpufx_uv(id);
    let t = fx_clock() * params.rate;
    let q = vec2f(uv.x * aspect, uv.y) * CELLS;
    let base = floor(q);
    var glow = 0.0;
    for (var dy = -1; dy <= 1; dy++) {
        for (var dx = -1; dx <= 1; dx++) {
            let cell = base + vec2f(f32(dx), f32(dy));
            let ci = vec2i(cell);
            // Each twinkle lives one period, then the cell picks a new place.
            let r0 = fx_rand(ci.x, ci.y, params.seed * 7919);
            let ph = t + r0;
            let life = i32(floor(ph));
            let salt = params.seed * 104729 + life * 31;
            if (fx_rand(ci.x, ci.y, salt) >= params.density) { continue; }
            let ctr = cell + vec2f(fx_rand(ci.x, ci.y, salt + 1), fx_rand(ci.x, ci.y, salt + 2));
            let at = clamp(ctr / CELLS / vec2f(aspect, 1.0), vec2f(0.0), vec2f(1.0));
            let l = fx_luma(clamp(textureSampleLevel(src, smp, at, 0.0).rgb, vec3f(0.0), vec3f(1.0)));
            let keep = mix(1.0, smoothstep(0.45, 0.85, l), params.follow);
            let env = sin(fract(ph) * 3.14159265);
            let s = 0.4 * params.size * mix(0.5, 1.0, fx_rand(ci.x, ci.y, salt + 3)) * env;
            let d = q - ctr;
            // Turn the star a little each life.
            let a = fx_rand(ci.x, ci.y, salt + 4) * 0.8;
            let rd = vec2f(d.x * cos(a) - d.y * sin(a), d.x * sin(a) + d.y * cos(a));
            let ad = abs(rd) / max(s, 1e-4);
            let rays = exp(-ad.x * 18.0) * exp(-ad.y * 1.5) + exp(-ad.y * 18.0) * exp(-ad.x * 1.5);
            let core = exp(-dot(ad, ad) * 6.0);
            glow += (rays + core) * env * keep;
        }
    }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let g = clamp(params.color.rgb * glow, vec3f(0.0), vec3f(1.0));
    gpufx_write(id, vec4f(1.0 - (1.0 - c.rgb) * (1.0 - g), c.a));
}
