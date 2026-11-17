fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }

fn lum_at(p: vec2f) -> f32 {
    return fx_luma(textureSampleLevel(src, smp, p / globals.size, 0.0).rgb);
}

fn edge_at(px: vec2f, w: f32) -> f32 {
    let tl = lum_at(px + vec2f(-w, -w)); let tc = lum_at(px + vec2f(0.0, -w)); let tr = lum_at(px + vec2f(w, -w));
    let ml = lum_at(px + vec2f(-w, 0.0)); let mr = lum_at(px + vec2f(w, 0.0));
    let bl = lum_at(px + vec2f(-w, w)); let bc = lum_at(px + vec2f(0.0, w)); let br = lum_at(px + vec2f(w, w));
    let gx = (tr + 2.0 * mr + br) - (tl + 2.0 * ml + bl);
    let gy = (bl + 2.0 * bc + br) - (tl + 2.0 * tc + tr);
    return length(vec2f(gx, gy));
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let px = vec2f(id.xy) + 0.5;
    let c = textureLoad(src, vec2i(id.xy), 0);
    let l = fx_luma(textureSampleLevel(src, smp, gpufx_uv(id), 0.0).rgb);
    let e = max(edge_at(px, 1.0), edge_at(px, 2.0) * 0.7);
    var v = 1.0 - smoothstep(0.08, 0.5, e * params.strength);
    let sp = max(params.spacing, 2.0);
    let h1 = smoothstep(0.35, 0.65, abs(fract((px.x + px.y) / sp) - 0.5) * 2.0);
    let h2 = smoothstep(0.35, 0.65, abs(fract((px.x - px.y) / sp) - 0.5) * 2.0);
    v *= mix(1.0, h1, smoothstep(0.6, 0.3, l) * params.hatching);
    v *= mix(1.0, h2, smoothstep(0.35, 0.1, l) * params.hatching);
    v *= mix(1.0, l, 0.25);
    var rgb = mix(params.ink.rgb, params.paper.rgb, v);
    rgb = mix(rgb, rgb * (c.rgb / max(l, 0.1)), params.colored);
    gpufx_write(id, vec4f(mix(c.rgb, rgb, params.amount), c.a));
}
