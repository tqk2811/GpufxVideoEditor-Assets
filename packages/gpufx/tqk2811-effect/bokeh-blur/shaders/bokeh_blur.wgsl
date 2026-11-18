fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }
const TAPS: i32 = 96;

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let r = vec2f(params.radius * globals.size.y / globals.size.x, params.radius);
    // A golden angle spiral covers the disc evenly; bright samples weigh more, so highlights
    // bloom into discs instead of being averaged away.
    var acc = vec3f(0.0);
    var wsum = 0.0;
    var asum = 0.0;
    let lod = max(log2(params.radius * globals.size.y / 8.0), 0.0);
    for (var k = 0; k < TAPS; k++) {
        let t = (f32(k) + 0.5) / f32(TAPS);
        let ang = f32(k) * 2.3999632;
        let p = uv + vec2f(cos(ang), sin(ang)) * sqrt(t) * r;
        let s = textureSampleLevel(src, smp, p, lod);
        let l = fx_luma(clamp(s.rgb, vec3f(0.0), vec3f(1.0)));
        let w = 1.0 + params.highlights * smoothstep(params.threshold, 1.0, l) * 4.0;
        acc += s.rgb * w;
        wsum += w;
        asum += s.a;
    }
    gpufx_write(id, vec4f(clamp(acc / wsum, vec3f(0.0), vec3f(1.0)), asum / f32(TAPS)));
}
