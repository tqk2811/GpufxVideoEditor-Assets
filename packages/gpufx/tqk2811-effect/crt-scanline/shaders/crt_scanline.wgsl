@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    var q = gpufx_uv(id) * 2.0 - 1.0;
    q *= 1.0 + params.curvature * (q.yx * q.yx);
    let uv = q * 0.5 + 0.5;
    let src_a = textureLoad(src, vec2i(id.xy), 0).a;
    if (any(uv < vec2f(0.0)) || any(uv > vec2f(1.0))) {
        gpufx_write(id, vec4f(params.border.rgb, max(src_a, params.border.a)));
        return;
    }
    var rgb = textureSampleLevel(src, smp, uv, 0.0).rgb;
    let lines = select(globals.size.y / 3.0, params.lines, params.lines > 0.0);
    let s = 0.5 + 0.5 * cos(uv.y * lines * 6.2831853);
    rgb *= mix(1.0, s, params.scanlines);
    let col = id.x % 3u;
    var m = vec3f(1.0, 0.0, 0.0);
    if (col == 1u) { m = vec3f(0.0, 1.0, 0.0); }
    if (col == 2u) { m = vec3f(0.0, 0.0, 1.0); }
    rgb *= mix(vec3f(1.0), m * 1.6 + 0.4, params.mask);
    let e = uv * (1.0 - uv);
    rgb *= mix(1.0, clamp(pow(e.x * e.y * 16.0, 0.35), 0.0, 1.0), params.vignette);
    rgb *= params.brightness;
    gpufx_write(id, vec4f(rgb, src_a));
}
