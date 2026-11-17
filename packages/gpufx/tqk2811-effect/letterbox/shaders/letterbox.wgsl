@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let aspect = globals.size.x / globals.size.y;
    let ratio = max(params.ratio, 0.01);
    let p = clamp(params.progress, 0.0, 1.0);
    let uv = gpufx_uv(id);
    let s = max(params.softness, 1e-4);
    var m = 0.0;
    if (aspect < ratio) {
        // Bars at the top and bottom, in frame heights.
        let bar = (1.0 - aspect / ratio) * 0.5 * p;
        let y = uv.y - params.offset * bar;
        m = max(1.0 - smoothstep(bar - s, bar, y + s * 0.5), smoothstep(1.0 - bar, 1.0 - bar + s, y + s * 0.5));
    } else {
        // Bars at the sides, in frame widths.
        let bar = (1.0 - ratio / aspect) * 0.5 * p;
        let sx = s / aspect;
        let x = uv.x - params.offset * bar;
        m = max(1.0 - smoothstep(bar - sx, bar, x + sx * 0.5), smoothstep(1.0 - bar, 1.0 - bar + sx, x + sx * 0.5));
    }
    if (p <= 0.0) { m = 0.0; }
    let k = m * params.color.a;
    gpufx_write(id, vec4f(mix(c.rgb, params.color.rgb, k), max(c.a, k)));
}
