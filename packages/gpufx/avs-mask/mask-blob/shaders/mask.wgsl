// Mask shape Blob, rewritten in WGSL from the shape table of AI Video Studio (MIT).
// x, y, w, h are percent of the frame (SVG viewBox 0..100); feather is the standard deviation of a
// Gaussian edge in viewBox units, approximated with a signed distance, so it is exact on straight edges.

const POINT_COUNT = 80u;
var<private> POINTS: array<vec2f, 80> = array<vec2f, 80>(
    vec2f(52.000, 1.000), vec2f(56.120, 1.328), vec2f(60.213, 1.936), vec2f(64.250, 2.822), vec2f(68.203, 3.984), vec2f(72.045, 5.423), vec2f(75.748, 7.135), vec2f(79.284, 9.119), vec2f(82.625, 11.375), vec2f(85.743, 13.900), vec2f(88.611, 16.693), vec2f(91.201, 19.753), vec2f(93.484, 23.078), vec2f(95.434, 26.667), vec2f(97.021, 30.518), vec2f(98.219, 34.629), vec2f(99.000, 39.000), vec2f(99.377, 43.133), vec2f(99.393, 47.270), vec2f(99.059, 51.388), vec2f(98.391, 55.469), vec2f(97.400, 59.491), vec2f(96.100, 63.434), vec2f(94.504, 67.277), vec2f(92.625, 71.000), vec2f(90.477, 74.583), vec2f(88.072, 78.004), vec2f(85.425, 81.244), vec2f(82.547, 84.281), vec2f(79.452, 87.096), vec2f(76.154, 89.668), vec2f(72.666, 91.976), vec2f(69.000, 94.000), vec2f(65.184, 95.677), vec2f(61.256, 96.965), vec2f(57.242, 97.872), vec2f(53.172, 98.406), vec2f(49.072, 98.578), vec2f(44.971, 98.395), vec2f(40.896, 97.866), vec2f(36.875, 97.000), vec2f(32.936, 95.806), vec2f(29.107, 94.293), vec2f(25.416, 92.469), vec2f(21.891, 90.344), vec2f(18.558, 87.925), vec2f(15.447, 85.223), vec2f(12.585, 82.245), vec2f(10.000, 79.000), vec2f(7.562, 75.348), vec2f(5.494, 71.537), vec2f(3.793, 67.594), vec2f(2.453, 63.547), vec2f(1.471, 59.424), vec2f(0.842, 55.252), vec2f(0.561, 51.060), vec2f(0.625, 46.875), vec2f(1.029, 42.725), vec2f(1.768, 38.639), vec2f(2.838, 34.643), vec2f(4.234, 30.766), vec2f(5.953, 27.035), vec2f(7.990, 23.479), vec2f(10.341, 20.124), vec2f(13.000, 17.000), vec2f(14.921, 14.997), vec2f(16.932, 13.113), vec2f(19.027, 11.353), vec2f(21.203, 9.719), vec2f(23.455, 8.213), vec2f(25.779, 6.840), vec2f(28.171, 5.601), vec2f(30.625, 4.500), vec2f(33.138, 3.540), vec2f(35.705, 2.723), vec2f(38.322, 2.052), vec2f(40.984, 1.531), vec2f(43.688, 1.163), vec2f(46.428, 0.949), vec2f(49.200, 0.894)
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
