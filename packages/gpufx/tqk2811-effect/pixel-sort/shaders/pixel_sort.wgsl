fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }
const STEPS: i32 = 48;

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let c = textureLoad(src, vec2i(id.xy), 0);
    let a = radians(params.angle);
    let aspect = globals.size.x / globals.size.y;
    let dir = vec2f(cos(a) / aspect, sin(a));
    let step = dir * params.length / f32(STEPS);
    // Walk back against the direction while the pixels stay bright, to the start of the run
    // (or as far as `length`). The streak carries the color of the run start and fades into the
    // pixel's own color along the run. No state, so this is a look-alike of a real sort.
    var best = c.rgb;
    let bl = fx_luma(clamp(c.rgb, vec3f(0.0), vec3f(1.0)));
    if (bl >= params.threshold) {
        var start = c.rgb;
        var n = 0;
        for (var k = 1; k <= STEPS; k++) {
            let p = uv - step * f32(k);
            if (any(p < vec2f(0.0)) || any(p > vec2f(1.0))) { break; }
            let s = textureSampleLevel(src, smp, p, 0.0).rgb;
            if (fx_luma(clamp(s, vec3f(0.0), vec3f(1.0))) < params.threshold) { break; }
            start = s;
            n = k;
        }
        best = mix(start, c.rgb, pow(f32(n) / f32(STEPS), 3.0));
    }
    let o = mix(c.rgb, best, params.amount);
    gpufx_write(id, vec4f(o, c.a));
}
