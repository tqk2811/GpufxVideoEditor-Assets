fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }

// Radial blur of the bright parts towards the light, from a blurred mip level to hide the steps.
@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let n = clamp(params.samples, 8, 128);
    let step = (uv - params.center) * params.length / f32(n);
    let thr = clamp(params.threshold, 0.0, 0.99);
    let lod = min(2.0, f32(textureNumLevels(src) - 1u));
    var coord = uv;
    var fall = 1.0;
    var acc = vec3f(0.0);
    for (var k = 0; k < n; k++) {
        coord -= step;
        let s = textureSampleLevel(src, smp, coord, lod).rgb;
        let l = fx_luma(s);
        acc += s * (max(l - thr, 0.0) / (1.0 - thr)) * fall;
        fall *= params.decay;
    }
    let rays = clamp(acc / f32(n) * params.intensity * 4.0 * params.tint.rgb, vec3f(0.0), vec3f(1.0));
    let c = textureLoad(src, vec2i(id.xy), 0);
    gpufx_write(id, vec4f(1.0 - (1.0 - c.rgb) * (1.0 - rays), c.a));
}
