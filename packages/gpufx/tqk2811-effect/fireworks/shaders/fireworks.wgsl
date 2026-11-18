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
const SLOTS: i32 = 4;      // bursts that can be alive at the same time
const SPARKS: i32 = 48;
const LIFE: f32 = 2.0;     // seconds a burst lasts

fn hue(h: f32) -> vec3f {
    return clamp(abs(fract(h + vec3f(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0, vec3f(0.0), vec3f(1.0));
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let aspect = globals.size.x / globals.size.y;
    let uv = gpufx_uv(id);
    let p = vec2f(uv.x * aspect, uv.y);
    let now = fx_clock();
    let period = LIFE / f32(SLOTS);
    var light = vec3f(0.0);
    let spark_r = 2.2 / globals.size.y;
    for (var k = 0; k < SLOTS; k++) {
        // Slot k starts a burst every LIFE seconds, offset so slots take turns.
        let shifted = now - f32(k) * period;
        let n = i32(floor(shifted / LIFE));
        let age = shifted - f32(n) * LIFE;
        let salt = params.seed * 104729 + k * 7919;
        // `rate` thins the bursts: skip some starts when fewer are wanted.
        if (fx_rand(n, k, salt) >= params.rate * period) { continue; }
        let ctr = vec2f((0.15 + 0.7 * fx_rand(n, k, salt + 1)) * aspect, 0.1 + (params.height - 0.1) * fx_rand(n, k, salt + 2));
        let col = mix(hue(fx_rand(n, k, salt + 3)), vec3f(1.0), 0.25);
        let u = age / LIFE;
        let fade = (1.0 - u) * (1.0 - u);
        // Sparks fly out and slow down, then sag under gravity.
        let reach = params.size * (1.0 - exp(-age * 3.0));
        let sag = 0.08 * age * age;
        let local = p - ctr - vec2f(0.0, sag);
        if (length(local) > reach + 0.05) { continue; }
        for (var s = 0; s < SPARKS; s++) {
            let a = (f32(s) + fx_rand(n, s, salt + 4) * 0.6) * 6.2831853 / f32(SPARKS);
            let sp = mix(0.75, 1.0, fx_rand(n, s, salt + 5));
            let dir = vec2f(cos(a), sin(a));
            let pos = dir * reach * sp;
            // A short trail behind each spark.
            let rel = local - pos;
            let along = clamp(dot(rel, -dir), 0.0, 0.035 * (1.0 - u));
            let d = length(rel + dir * along);
            let twinkle = 0.7 + 0.3 * fx_rand(n * 97 + s, i32(floor(now * 20.0)), salt + 6);
            light += col * exp(-d * d / (spark_r * spark_r)) * fade * twinkle;
        }
        // A flash at the burst center in the first moment.
        let fl = 0.3 * exp(-age * 14.0) * exp(-dot(local, local) / (params.size * params.size * 0.01));
        light += vec3f(1.0, 0.95, 0.85) * fl;
    }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let g = clamp(light * params.brightness, vec3f(0.0), vec3f(1.0));
    gpufx_write(id, vec4f(1.0 - (1.0 - c.rgb) * (1.0 - g), c.a));
}
