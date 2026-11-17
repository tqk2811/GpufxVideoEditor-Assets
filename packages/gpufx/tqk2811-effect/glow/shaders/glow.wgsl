fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }

// The input has mipmaps: each level is the picture blurred twice as wide. The glow sums the
// bright part of six levels and lays it over the picture with a screen blend.
@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let c = textureLoad(src, vec2i(id.xy), 0);
    let top = f32(textureNumLevels(src) - 1u);
    let thr = clamp(params.threshold, 0.0, 0.99);
    var acc = vec3f(0.0);
    for (var k = 1; k <= 6; k++) {
        let lod = min(f32(k) * params.radius + 0.5, top);
        let s = textureSampleLevel(src, smp, uv, lod).rgb;
        let l = fx_luma(s);
        acc += s * (max(l - thr, 0.0) / (max(l, 1e-4) * (1.0 - thr)));
    }
    let g = clamp(acc / 6.0 * params.intensity * 1.5 * params.tint.rgb, vec3f(0.0), vec3f(1.0));
    gpufx_write(id, vec4f(1.0 - (1.0 - c.rgb) * (1.0 - g), c.a));
}
