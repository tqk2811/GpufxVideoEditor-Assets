// Punch: the clip starts zoomed in and settles to rest, from the punch accent of AI Video Studio (MIT).

fn avs_k() -> f32 {
    // Progress of the motion: the clip's clock over `duration`, shortened to a clip that is shorter.
    let span = select(params.duration, min(params.duration, params.clip_duration), params.clip_duration > 0.0);
    if (span <= 0.0) { return 1.0; }
    return clamp(params.clip_time / span, 0.0, 1.0);
}

fn avs_out_cubic(k: f32) -> f32 { return 1.0 - pow(1.0 - k, 3.0); }
fn avs_in_cubic(k: f32) -> f32 { return k * k * k; }
fn avs_in_out_sine(k: f32) -> f32 { return -(cos(3.14159265 * k) - 1.0) * 0.5; }

fn avs_scale() -> f32 {
    return 1.0 + params.amp * (1.0 - avs_out_cubic(avs_k()));
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let scale = avs_scale();
    if (scale == 1.0) {
        gpufx_write(id, textureLoad(src, vec2i(id.xy), 0));
        return;
    }
    let origin = vec2f(0.5, 0.45);
    let uv = origin + (gpufx_uv(id) - origin) / scale;
    gpufx_write(id, textureSampleLevel(src, smp, uv, 0.0));
}
