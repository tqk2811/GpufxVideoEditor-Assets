// Mask shape Rounded Rectangle, rewritten in WGSL from the shape table of AI Video Studio (MIT).
// x, y, w, h are percent of the frame (SVG viewBox 0..100); feather is the standard deviation of a
// Gaussian edge in viewBox units, approximated with a signed distance, so it is exact on straight edges.

const CORNER_STEPS = 16u;
const POINT_COUNT = 68u; // 4 corners of 17 points each

// A rounded rectangle in the 0..100 box of the shape; r is the corner radius, 0..50.
fn shape_point(index: u32) -> vec2f {
    let r = clamp(params.r, 0.0, 50.0);
    let corner = index / (CORNER_STEPS + 1u);
    let step_index = index % (CORNER_STEPS + 1u);
    let a = 1.5707963 * (f32(corner) + f32(step_index) / f32(CORNER_STEPS)) - 3.1415927;
    var center = vec2f(r, r);
    if (corner == 1u) { center = vec2f(100.0 - r, r); }
    if (corner == 2u) { center = vec2f(100.0 - r, 100.0 - r); }
    if (corner == 3u) { center = vec2f(r, 100.0 - r); }
    return center + vec2f(cos(a), sin(a)) * r;
}

// Signed distance in viewBox units from p to the shape placed by params: negative inside.
fn signed_distance(p: vec2f, origin: vec2f, scale: vec2f) -> f32 {
    var best = 1e20;
    var inside = false;
    var a = origin + shape_point(POINT_COUNT - 1u) * scale;
    for (var i = 0u; i < POINT_COUNT; i += 1u) {
        let b = origin + shape_point(i) * scale;
        let edge = b - a;
        let w = p - a;
        let t = clamp(dot(w, edge) / max(dot(edge, edge), 1e-9), 0.0, 1.0);
        let q = w - edge * t;
        best = min(best, dot(q, q));
        if (((a.y > p.y) != (b.y > p.y)) && (p.x < a.x + (p.y - a.y) / (b.y - a.y) * (b.x - a.x))) {
            inside = !inside;
        }
        a = b;
    }
    let d = sqrt(best);
    return select(d, -d, inside);
}

// Abramowitz and Stegun 7.1.27, |error| < 5e-4.
fn erf(x: f32) -> f32 {
    let v = abs(x);
    let d = 1.0 + v * (0.278393 + v * (0.230389 + v * (0.000972 + v * 0.078108)));
    let y = 1.0 - 1.0 / (d * d * d * d);
    return select(y, -y, x < 0.0);
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let c = textureLoad(src, vec2i(id.xy), 0);
    let p = gpufx_uv(id) * 100.0;
    let w = max(params.w, 1.0);
    let h = max(params.h, 1.0);
    let origin = vec2f(params.x - w * 0.5, params.y - h * 0.5);
    let d = signed_distance(p, origin, vec2f(w, h) * 0.01);
    // The feather keeps its width in viewBox units; a third of a pixel of antialiasing is added.
    let pixel = 50.0 / globals.size.x + 50.0 / globals.size.y;
    let sigma = sqrt(params.feather * params.feather + 0.11 * pixel * pixel);
    var m = 0.5 * (1.0 - erf(d / (sigma * 1.4142135)));
    if (params.invert != 0u) { m = 1.0 - m; }

    let source_alpha = c.a * m;
    let background_alpha = params.bg.a * (1.0 - m);
    let alpha = source_alpha + background_alpha;
    var rgb = c.rgb;
    if (background_alpha > 0.0) {
        rgb = (c.rgb * source_alpha + params.bg.rgb * background_alpha) / alpha;
    }
    gpufx_write(id, vec4f(rgb, alpha));
}
