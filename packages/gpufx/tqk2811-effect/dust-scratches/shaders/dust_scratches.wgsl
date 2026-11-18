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
    let c = textureLoad(src, vec2i(id.xy), 0);
    let uv = gpufx_uv(id);
    let aspect = globals.size.x / globals.size.y;
    let tick = i32(floor(fx_clock() * params.fps)) + params.seed * 7919;
    let p = vec2f(uv.x * aspect, uv.y);
    var m = 0.0;
    // Dust: a few round specks and short hairs per frame, from a coarse grid.
    let cells = 9.0;
    let q = p * cells;
    let base = floor(q);
    for (var dy = -1; dy <= 1; dy++) {
        for (var dx = -1; dx <= 1; dx++) {
            let cell = base + vec2f(f32(dx), f32(dy));
            let ci = vec2i(cell);
            if (fx_rand(ci.x, ci.y, tick) >= params.dust * 0.25) { continue; }
            let ctr = cell + vec2f(fx_rand(ci.x, ci.y, tick + 1), fx_rand(ci.x, ci.y, tick + 2));
            let r = mix(0.01, 0.05, fx_rand(ci.x, ci.y, tick + 3));
            var d = q - ctr;
            if (fx_rand(ci.x, ci.y, tick + 4) < 0.35) {
                // A hair: a thin bent line.
                let ang = fx_rand(ci.x, ci.y, tick + 5) * 6.2831853;
                let dir = vec2f(cos(ang), sin(ang));
                let along = dot(d, dir);
                let side = dot(d, vec2f(-dir.y, dir.x)) - along * along * 1.5;
                m = max(m, (1.0 - smoothstep(0.004, 0.012, abs(side))) * (1.0 - smoothstep(0.2, 0.35, abs(along))));
            } else {
                m = max(m, 1.0 - smoothstep(r * 0.5, r, length(d)));
            }
        }
    }
    // Scratches: up to three thin vertical lines, slightly slanted.
    for (var k = 0; k < 3; k++) {
        if (fx_rand(k, tick, 11) >= params.scratches * 0.6) { continue; }
        let x0 = fx_rand(k, tick, 12) * aspect;
        let x = x0 + (uv.y - 0.5) * (fx_rand(k, tick, 13) - 0.5) * 0.02;
        let wpx = mix(0.6, 1.8, fx_rand(k, tick, 14)) / globals.size.y;
        let fade = 0.5 + 0.5 * sin(uv.y * 9.0 + fx_rand(k, tick, 15) * 6.28);
        m = max(m, (1.0 - smoothstep(wpx * 0.5, wpx, abs(p.x - x))) * fade);
    }
    gpufx_write(id, vec4f(mix(c.rgb, params.color.rgb, m * params.opacity), c.a));
}
