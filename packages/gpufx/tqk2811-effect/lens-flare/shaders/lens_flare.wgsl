const TAU: f32 = 6.2831853;

fn hue(h: f32) -> vec3f {
    return clamp(abs(fract(h + vec3f(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0, vec3f(0.0), vec3f(1.0));
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let aspect = globals.size.x / globals.size.y;
    let uv = gpufx_uv(id);
    let p = vec2f(uv.x * aspect, uv.y);
    let l = vec2f(params.center.x * aspect, params.center.y);
    let mid = vec2f(0.5 * aspect, 0.5);
    let d = p - l;
    let r = length(d);
    let ang = atan2(d.y, d.x);
    var flare = params.color.rgb * (exp(-r * 9.0) * 0.6 + exp(-r * r * 900.0) * 1.5);
    flare += params.color.rgb * exp(-abs(d.y) * 160.0) * exp(-abs(d.x) * 2.5) * 0.6 * params.streak;
    let rays = pow(abs(sin(ang * 6.0)), 24.0) + pow(abs(sin(ang * 4.0 + 0.7)), 40.0) * 0.6;
    flare += params.color.rgb * rays * exp(-r * 6.0) * 0.35;
    // A thin rainbow halo around the light.
    for (var k = 0; k < 3; k++) {
        let rr = 0.33 + f32(k) * 0.012;
        let w = (r - rr) * 70.0;
        flare[k] += exp(-w * w) * 0.08;
    }
    // Ghosts on the line from the light through the middle of the frame.
    let axis = mid - l;
    var ats = array<f32, 6>(0.45, 0.7, 1.15, 1.4, 1.75, 2.3);
    var szs = array<f32, 6>(0.05, 0.12, 0.03, 0.18, 0.07, 0.25);
    for (var k = 0; k < 6; k++) {
        let fk = f32(k);
        let at = ats[k];
        let sz = szs[k];
        let g = l + axis * at;
        let dg = length(p - g) / sz;
        let disc = (1.0 - smoothstep(0.75, 1.0, dg)) * (0.35 + 0.65 * smoothstep(0.2, 1.0, dg));
        flare += hue(0.08 + fk * 0.17) * disc * 0.12 * params.ghosts;
    }
    let c = textureLoad(src, vec2i(id.xy), 0);
    gpufx_write(id, vec4f(c.rgb + flare * params.intensity, c.a));
}
