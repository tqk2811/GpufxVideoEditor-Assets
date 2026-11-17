@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let r = clamp(params.radius, 1, 8);
    let p = vec2i(id.xy);
    let hi = vec2i(globals.size) - 1;
    var best_mean = vec3f(0.0);
    var best_var = 1e9;
    // The four overlapping squares around the pixel; the one with the least spread wins.
    for (var q = 0; q < 4; q++) {
        let sx = select(-1, 1, (q & 1) == 1);
        let sy = select(-1, 1, (q & 2) == 2);
        var sum = vec3f(0.0);
        var sq = vec3f(0.0);
        for (var y = 0; y <= r; y++) {
            for (var x = 0; x <= r; x++) {
                let s = textureLoad(src, clamp(p + vec2i(x * sx, y * sy), vec2i(0), hi), 0).rgb;
                sum += s;
                sq += s * s;
            }
        }
        let n = f32((r + 1) * (r + 1));
        let mean = sum / n;
        let v = sq / n - mean * mean;
        let total = v.r + v.g + v.b;
        if (total < best_var) {
            best_var = total;
            best_mean = mean;
        }
    }
    let c = textureLoad(src, p, 0);
    gpufx_write(id, vec4f(mix(c.rgb, best_mean, params.amount), c.a));
}
