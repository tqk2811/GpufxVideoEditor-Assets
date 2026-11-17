fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let size = max(params.size, 2.0);
    let a = radians(params.angle);
    let rot = mat2x2f(cos(a), sin(a), -sin(a), cos(a));
    let px = vec2f(id.xy) + 0.5;
    let p = transpose(rot) * px / size;
    let cell = floor(p) + 0.5;
    let center = rot * (cell * size);
    // The mean color of the cell, from the mip level about the size of a cell.
    let lod = clamp(log2(size) - 0.5, 0.0, f32(textureNumLevels(src) - 1u));
    let cc = textureSampleLevel(src, smp, center / globals.size, lod).rgb;
    let l = fx_luma(cc);
    let r = sqrt(clamp(1.0 - l, 0.0, 1.0)) * 0.72;
    let aa = 1.0 / size;
    let m = 1.0 - smoothstep(r - aa, r + aa, length(p - cell));
    let ink = select(params.ink.rgb, cc / max(max(cc.r, max(cc.g, cc.b)), 0.05) * 0.85, params.colored != 0u);
    let c = textureLoad(src, vec2i(id.xy), 0);
    let ht = mix(params.paper.rgb, ink, m);
    gpufx_write(id, vec4f(mix(c.rgb, ht, params.amount), c.a));
}
