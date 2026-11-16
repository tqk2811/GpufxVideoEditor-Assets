// A circle (round on screen, whatever the aspect) grows from `center` until it covers the farthest
// corner at progress 1; outside it the picture is transparent.
@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let uv = gpufx_uv(id);
    let aspect = vec2f(globals.size.x / globals.size.y, 1.0);
    let d = length((uv - params.center) * aspect);
    let far = max(max(length(params.center * aspect), length((vec2f(1.0, 0.0) - params.center) * aspect)),
                  max(length((vec2f(0.0, 1.0) - params.center) * aspect), length((1.0 - params.center) * aspect)));
    let s = max(params.softness, 1e-4);
    let p = clamp(params.progress, 0.0, 1.0);
    let r = p * (far + s);
    var m = 1.0 - smoothstep(r - s, r, d);
    if (p >= 1.0) { m = 1.0; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    gpufx_write(id, vec4f(c.rgb, c.a * m));
}
