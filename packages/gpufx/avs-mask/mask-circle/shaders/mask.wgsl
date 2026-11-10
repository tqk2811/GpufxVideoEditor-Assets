// Mask shape Circle, rewritten in WGSL from the shape table of AI Video Studio (MIT).
// x, y, w, h are percent of the frame (SVG viewBox 0..100); feather is the standard deviation of a
// Gaussian edge in viewBox units, approximated with a signed distance, so it is exact on straight edges.

const POINT_COUNT = 96u;
var<private> POINTS: array<vec2f, 96> = array<vec2f, 96>(
    vec2f(100.000, 50.000), vec2f(99.893, 53.270), vec2f(99.572, 56.526), vec2f(99.039, 59.755), vec2f(98.296, 62.941), vec2f(97.347, 66.072), vec2f(96.194, 69.134), vec2f(94.844, 72.114), vec2f(93.301, 75.000), vec2f(91.573, 77.779), vec2f(89.668, 80.438), vec2f(87.592, 82.967), vec2f(85.355, 85.355), vec2f(82.967, 87.592), vec2f(80.438, 89.668), vec2f(77.779, 91.573), vec2f(75.000, 93.301), vec2f(72.114, 94.844), vec2f(69.134, 96.194), vec2f(66.072, 97.347), vec2f(62.941, 98.296), vec2f(59.755, 99.039), vec2f(56.526, 99.572), vec2f(53.270, 99.893), vec2f(50.000, 100.000), vec2f(46.730, 99.893), vec2f(43.474, 99.572), vec2f(40.245, 99.039), vec2f(37.059, 98.296), vec2f(33.928, 97.347), vec2f(30.866, 96.194), vec2f(27.886, 94.844), vec2f(25.000, 93.301), vec2f(22.221, 91.573), vec2f(19.562, 89.668), vec2f(17.033, 87.592), vec2f(14.645, 85.355), vec2f(12.408, 82.967), vec2f(10.332, 80.438), vec2f(8.427, 77.779), vec2f(6.699, 75.000), vec2f(5.156, 72.114), vec2f(3.806, 69.134), vec2f(2.653, 66.072), vec2f(1.704, 62.941), vec2f(0.961, 59.755), vec2f(0.428, 56.526), vec2f(0.107, 53.270), vec2f(0.000, 50.000), vec2f(0.107, 46.730), vec2f(0.428, 43.474), vec2f(0.961, 40.245), vec2f(1.704, 37.059), vec2f(2.653, 33.928), vec2f(3.806, 30.866), vec2f(5.156, 27.886), vec2f(6.699, 25.000), vec2f(8.427, 22.221), vec2f(10.332, 19.562), vec2f(12.408, 17.033), vec2f(14.645, 14.645), vec2f(17.033, 12.408), vec2f(19.562, 10.332), vec2f(22.221, 8.427), vec2f(25.000, 6.699), vec2f(27.886, 5.156), vec2f(30.866, 3.806), vec2f(33.928, 2.653), vec2f(37.059, 1.704), vec2f(40.245, 0.961), vec2f(43.474, 0.428), vec2f(46.730, 0.107), vec2f(50.000, 0.000), vec2f(53.270, 0.107), vec2f(56.526, 0.428), vec2f(59.755, 0.961), vec2f(62.941, 1.704), vec2f(66.072, 2.653), vec2f(69.134, 3.806), vec2f(72.114, 5.156), vec2f(75.000, 6.699), vec2f(77.779, 8.427), vec2f(80.438, 10.332), vec2f(82.967, 12.408), vec2f(85.355, 14.645), vec2f(87.592, 17.033), vec2f(89.668, 19.562), vec2f(91.573, 22.221), vec2f(93.301, 25.000), vec2f(94.844, 27.886), vec2f(96.194, 30.866), vec2f(97.347, 33.928), vec2f(98.296, 37.059), vec2f(99.039, 40.245), vec2f(99.572, 43.474), vec2f(99.893, 46.730)
);

fn shape_point(index: u32) -> vec2f {
    return POINTS[index];
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
