fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let a = radians(params.angle);
    let dir = vec2f(cos(a), -sin(a)) * params.distance / globals.size;
    let uv = gpufx_uv(id);
    let d = fx_luma(textureSampleLevel(src, smp, uv - dir, 0.0).rgb) - fx_luma(textureSampleLevel(src, smp, uv + dir, 0.0).rgb);
    let c = textureLoad(src, vec2i(id.xy), 0);
    let relief = mix(vec3f(0.5 + d * params.strength), c.rgb + d * params.strength, params.color);
    gpufx_write(id, vec4f(mix(c.rgb, relief, params.amount), c.a));
}
