// The output may have another shape than the clip: the size comes from `aspect`, at the clip's height.
fn gpufx_output_size(out_index: u32) -> vec2u {
    let s = gpufx_input_size(0u);
    if (params.aspect <= 0.0) { return s; }
    let w = u32(round(f32(s.y) * params.aspect * 0.5)) * 2u;
    return vec2u(clamp(w, 2u, 8192u), s.y);
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let in_size = vec2f(textureDimensions(src));
    let a_in = in_size.x / in_size.y;
    let a_out = globals.size.x / globals.size.y;
    // Background: the clip enlarged to cover the frame, blurred with nine taps of a small mip level.
    let cover = vec2f(min(1.0, a_out / a_in), min(1.0, a_in / a_out)) / max(params.zoom, 1.0);
    let ub = 0.5 + (uv - 0.5) * cover;
    let lod = clamp(params.blur, 0.0, f32(textureNumLevels(src) - 1u));
    let tap = exp2(lod) / in_size;
    var bg = vec4f(0.0);
    for (var y = -1; y <= 1; y++) {
        for (var x = -1; x <= 1; x++) {
            let w = select(1.0, 2.0, x == 0) * select(1.0, 2.0, y == 0);
            bg += textureSampleLevel(src, smp, ub + vec2f(f32(x), f32(y)) * tap, lod) * w;
        }
    }
    bg /= 16.0;
    bg = vec4f(bg.rgb * (1.0 - params.dim), 1.0);
    // Foreground: the clip fitted inside the frame.
    let fit = vec2f(min(1.0, a_in / a_out), min(1.0, a_out / a_in)) * clamp(params.scale, 0.01, 1.0);
    let uf = (uv - 0.5) / fit + 0.5;
    let edge = min(min(uf.x, 1.0 - uf.x) * fit.x * globals.size.x, min(uf.y, 1.0 - uf.y) * fit.y * globals.size.y);
    let m = clamp(edge + 0.5, 0.0, 1.0);
    var fg = textureSampleLevel(src, smp, clamp(uf, vec2f(0.0), vec2f(1.0)), 0.0);
    let k = fg.a * m;
    gpufx_write(id, vec4f(mix(bg.rgb, fg.rgb, k), 1.0));
}
