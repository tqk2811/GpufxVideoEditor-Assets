// Shake: the frame shake of AI Video Studio (MIT), held at a constant amplitude so it needs no clip time.

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    if (params.amp <= 0.0) {
        gpufx_write(id, textureLoad(src, vec2i(id.xy), 0));
        return;
    }
    let size = globals.size;
    // Amplitude is in design pixels on a 1280 long side.
    let unit = max(size.x, size.y) / 1280.0;
    let beat = floor((f32(globals.time_int) + globals.time_frac) * params.rate);
    let offset = vec2f(sin(beat * 2.1), cos(beat * 1.7)) * params.amp * unit / size;
    let scale = 1.0 + params.amp / 300.0;
    let origin = vec2f(0.5, 0.45);
    let uv = origin + (gpufx_uv(id) - origin - offset) / scale;
    gpufx_write(id, textureSampleLevel(src, smp, uv, 0.0));
}
