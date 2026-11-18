fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }
const TAPS: i32 = 96;

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let r = vec2f(params.radius * globals.size.y / globals.size.x, params.radius);
    // A golden angle spiral covers the disc evenly. Bright samples are raised above 1 before
    // the plain average, as a lens spreads the full light of a point over its disc, so small
    // highlights come out as bright discs instead of being averaged away.
    var acc = vec3f(0.0);
    var asum = 0.0;
    let lod = max(log2(params.radius * globals.size.y / 24.0), 0.0);
    // Boost only against darker surroundings, so a bright sky or wall keeps its brightness.
    let around = fx_luma(clamp(textureSampleLevel(src, smp, uv, max(lod + 3.0, 5.0)).rgb, vec3f(0.0), vec3f(1.0)));
    let gain = params.highlights * 4.0 * (1.0 - smoothstep(0.15, 0.45, around));
    for (var k = 0; k < TAPS; k++) {
        let t = (f32(k) + 0.5) / f32(TAPS);
        let ang = f32(k) * 2.3999632;
        let p = uv + vec2f(cos(ang), sin(ang)) * sqrt(t) * r;
        let s = textureSampleLevel(src, smp, p, lod);
        let l = fx_luma(clamp(s.rgb, vec3f(0.0), vec3f(1.0)));
        let w = 1.0 + gain * smoothstep(params.threshold, 1.0, l);
        acc += s.rgb * w;
        asum += s.a;
    }
    gpufx_write(id, vec4f(clamp(acc / f32(TAPS), vec3f(0.0), vec3f(1.0)), asum / f32(TAPS)));
}
