fn fx_luma(c: vec3f) -> f32 { return dot(c, vec3f(0.2126, 0.7152, 0.0722)); }

fn lum_at(p: vec2f) -> f32 {
    return fx_luma(textureSampleLevel(src, smp, p / globals.size, 0.0).rgb);
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let px = vec2f(id.xy) + 0.5;
    let c = textureLoad(src, vec2i(id.xy), 0);
    // A small blur first, so grain does not break the bands or draw lines.
    var sm = vec3f(0.0);
    for (var y = -1; y <= 1; y++) {
        for (var x = -1; x <= 1; x++) {
            sm += textureSampleLevel(src, smp, (px + vec2f(f32(x), f32(y))) / globals.size, 0.0).rgb;
        }
    }
    sm /= 9.0;
    let l = fx_luma(sm);
    let n = f32(max(params.levels, 2));
    let lq = (floor(l * n) + 0.5) / n;
    var flat_c = sm * (lq / max(l, 1e-3));
    flat_c = mix(vec3f(fx_luma(flat_c)), flat_c, params.saturation);
    let w = max(params.edge_width, 0.5);
    let tl = lum_at(px + vec2f(-w, -w)); let tc = lum_at(px + vec2f(0.0, -w)); let tr = lum_at(px + vec2f(w, -w));
    let ml = lum_at(px + vec2f(-w, 0.0)); let mr = lum_at(px + vec2f(w, 0.0));
    let bl = lum_at(px + vec2f(-w, w)); let bc = lum_at(px + vec2f(0.0, w)); let br = lum_at(px + vec2f(w, w));
    let gx = (tr + 2.0 * mr + br) - (tl + 2.0 * ml + bl);
    let gy = (bl + 2.0 * bc + br) - (tl + 2.0 * tc + tr);
    let e = length(vec2f(gx, gy));
    let m = smoothstep(params.edge, params.edge * 1.6 + 0.02, e);
    let toon = mix(flat_c, params.edge_color.rgb, m * params.edge_color.a);
    gpufx_write(id, vec4f(mix(c.rgb, toon, params.amount), c.a));
}
