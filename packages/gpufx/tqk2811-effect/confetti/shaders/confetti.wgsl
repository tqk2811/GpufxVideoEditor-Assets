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
fn fx_over(c: vec4f, acc: vec4f) -> vec4f {
    let a = acc.a + c.a * (1.0 - acc.a);
    if (a <= 0.0) { return vec4f(0.0); }
    return vec4f((acc.rgb + c.rgb * c.a * (1.0 - acc.a)) / a, a);
}

const LAYERS: i32 = 4;
const FAR_CELLS: f32 = 16.0;    // cells per frame height in the farthest layer
const NEAR_CELLS: f32 = 5.0;  // and in the nearest
const SWAY: f32 = 0.1;        // side-to-side swing, in cells

fn particle(q: vec2f, r: vec4f, t: f32, depth: f32) -> vec4f {
    var palette = array<vec3f, 6>(vec3f(1.0, 0.3, 0.3), vec3f(1.0, 0.82, 0.25), vec3f(0.25, 0.75, 1.0),
                                  vec3f(0.5, 0.95, 0.4), vec3f(1.0, 0.42, 0.84), vec3f(0.98, 0.98, 0.98));
    let s = params.spin;
    let ang = r.z * 6.2831853 + t * (1.0 + 2.0 * r.w) * s * select(-1.0, 1.0, r.x > 0.5);
    let flip = cos(t * (2.5 + 3.0 * r.y) * s + r.w * 6.2831853);
    var lq = vec2f(cos(ang) * q.x + sin(ang) * q.y, -sin(ang) * q.x + cos(ang) * q.y);
    lq.x /= max(abs(flip), 0.08);
    let half_size = vec2f(0.13, 0.07);
    let e = abs(lq) - half_size;
    let aa = 0.02;
    let a = (1.0 - smoothstep(-aa, 0.0, max(e.x * abs(flip), e.y))) * mix(0.75, 1.0, depth);
    let col = palette[min(u32(fract(r.x * 7.31 + r.y * 3.17) * 6.0), 5u)] * (0.55 + 0.45 * abs(flip));
    return vec4f(col * a, a);
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let aspect = globals.size.x / globals.size.y;
    let uv = gpufx_uv(id);
    let t = fx_clock();
    var c = textureLoad(src, vec2i(id.xy), 0);
    // no change to the picture
    var acc = vec4f(0.0);
    // Nearest layer first: it lies over the others.
    for (var layer = LAYERS - 1; layer >= 0; layer--) {
        let depth = f32(layer + 1) / f32(LAYERS);
        let cells = mix(FAR_CELLS, NEAR_CELLS, depth) / max(params.size, 0.1);
        var p = vec2f(uv.x * aspect, uv.y);
        // straight down
        p.y -= t * params.speed * mix(0.55, 1.0, depth) * 1.0;
        p.x -= t * params.wind * mix(0.6, 1.0, depth);
        p *= cells;
        let base = floor(p);
        let salt = layer * 7919 + params.seed * 104729;
        for (var dy = -1; dy <= 1; dy++) {
            for (var dx = -1; dx <= 1; dx++) {
                let cell = base + vec2f(f32(dx), f32(dy));
                let ci = vec2i(cell);
                if (fx_rand(ci.x, ci.y, salt) >= params.density) { continue; }
                let r = vec4f(fx_rand(ci.x, ci.y, salt + 1), fx_rand(ci.x, ci.y, salt + 2),
                              fx_rand(ci.x, ci.y, salt + 3), fx_rand(ci.x, ci.y, salt + 4));
                let swing = sin(t * (0.8 + r.z) * 2.0 + r.w * 6.2831853) * SWAY;
                let center = cell + 0.5 + (r.xy - 0.5) * 0.5 + vec2f(swing, 0.0);
                let col = particle(p - center, r, t, depth);
                acc += col * (1.0 - acc.a);
            }
        }
    }
    gpufx_write(id, fx_over(c, acc * clamp(params.opacity, 0.0, 1.0)));
}
