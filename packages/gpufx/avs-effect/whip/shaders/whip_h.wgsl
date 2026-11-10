// Whip, pass 1: horizontal part of the blur.

fn avs_k() -> f32 {
    // Progress of the motion: the clip's clock over `duration`, shortened to a clip that is shorter.
    let span = select(params.duration, min(params.duration, params.clip_duration), params.clip_duration > 0.0);
    if (span <= 0.0) { return 1.0; }
    return clamp(params.clip_time / span, 0.0, 1.0);
}

fn avs_out_cubic(k: f32) -> f32 { return 1.0 - pow(1.0 - k, 3.0); }
fn avs_in_cubic(k: f32) -> f32 { return k * k * k; }
fn avs_in_out_sine(k: f32) -> f32 { return -(cos(3.14159265 * k) - 1.0) * 0.5; }
// One-dimensional Gaussian on the texture `tex` around `uv`, 33 taps whatever the width.
fn avs_gauss(tex: texture_2d<f32>, uv: vec2f, step: vec2f) -> vec4f {
    var sum = vec4f(0.0);
    var total = 0.0;
    for (var i = -16; i <= 16; i++) {
        let x = f32(i) * 3.0 / 16.0;
        let weight = exp(-0.5 * x * x);
        sum += textureSampleLevel(tex, smp, uv + step * x, 0.0) * weight;
        total += weight;
    }
    return sum / total;
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let sigma = sin(3.14159265 * avs_k()) * params.blur * max(globals.size.x, globals.size.y) / 1280.0;
    if (sigma <= 0.0 || avs_k() >= 1.0) {
        gpufx_write(id, textureLoad(src, vec2i(id.xy), 0));
        return;
    }
    gpufx_write(id, avs_gauss(src, gpufx_uv(id), vec2f(sigma / globals.size.x, 0.0)));
}
