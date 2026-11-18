fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }
@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let aspect = globals.size.x / globals.size.y;
    let a = radians(params.angle);
    let d = abs(dot((uv - vec2f(0.5, params.focus)) * vec2f(aspect, 1.0), vec2f(-sin(a), cos(a))));
    let k = smoothstep(params.width, params.width + params.falloff, d);
    let top = f32(textureNumLevels(src) - 1u);
    let lod = min(k * params.blur, top);
    // Two taps half a texel of that mip apart soften the blocky look of the mip levels.
    let px = vec2f(0.5) / globals.size * exp2(lod);
    var s = (textureSampleLevel(src, smp, uv + px, lod) + textureSampleLevel(src, smp, uv - px, lod)) * 0.5;
    if (lod < 0.05) { s = textureLoad(src, vec2i(id.xy), 0); }
    let l = fx_luma(s.rgb);
    gpufx_write(id, vec4f(clamp(mix(vec3f(l), s.rgb, params.saturation), vec3f(0.0), vec3f(1.0)), s.a));
}
