@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let rgb = clamp(c.rgb, vec3f(0.0), vec3f(1.0));
    // A different S-curve per channel: red and green steepened, blue flattened and lifted.
    let s = params.strength;
    let r = mix(rgb.r, smoothstep(0.0, 1.0, rgb.r), 0.8 * s);
    let g = mix(rgb.g, smoothstep(0.05, 0.95, rgb.g), 0.6 * s);
    let b = mix(rgb.b, rgb.b * 0.6 + 0.2, 0.7 * s);
    var o = vec3f(r, g, b) + vec3f(0.03, 0.04, -0.02) * s;
    gpufx_write(id, vec4f(mix(rgb, clamp(o, vec3f(0.0), vec3f(1.0)), params.amount), c.a));
}
