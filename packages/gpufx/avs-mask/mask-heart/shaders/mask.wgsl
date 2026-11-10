// Mask shape Heart, rewritten in WGSL from the shape table of AI Video Studio (MIT).
// x, y, w, h are percent of the frame (SVG viewBox 0..100); feather is the standard deviation of a
// Gaussian edge in viewBox units, approximated with a signed distance, so it is exact on straight edges.

const POINT_COUNT = 96u;
var<private> POINTS: array<vec2f, 96> = array<vec2f, 96>(
    vec2f(50.000, 96.000), vec2f(44.824, 91.919), vec2f(39.812, 87.914), vec2f(34.988, 83.968), vec2f(30.375, 80.062), vec2f(25.996, 76.181), vec2f(21.875, 72.305), vec2f(18.035, 68.417), vec2f(14.500, 64.500), vec2f(11.293, 60.536), vec2f(8.438, 56.508), vec2f(5.957, 52.397), vec2f(3.875, 48.188), vec2f(2.215, 43.860), vec2f(1.000, 39.398), vec2f(0.254, 34.784), vec2f(0.000, 30.000), vec2f(0.150, 26.697), vec2f(0.588, 23.543), vec2f(1.299, 20.547), vec2f(2.266, 17.719), vec2f(3.473, 15.066), vec2f(4.904, 12.598), vec2f(6.544, 10.323), vec2f(8.375, 8.250), vec2f(10.382, 6.388), vec2f(12.549, 4.746), vec2f(14.859, 3.333), vec2f(17.297, 2.156), vec2f(19.846, 1.226), vec2f(22.490, 0.551), vec2f(25.214, 0.139), vec2f(28.000, 0.000), vec2f(29.851, 0.070), vec2f(31.652, 0.275), vec2f(33.401, 0.613), vec2f(35.094, 1.078), vec2f(36.728, 1.666), vec2f(38.301, 2.373), vec2f(39.809, 3.194), vec2f(41.250, 4.125), vec2f(42.621, 5.161), vec2f(43.918, 6.299), vec2f(45.139, 7.533), vec2f(46.281, 8.859), vec2f(47.341, 10.274), vec2f(48.316, 11.771), vec2f(49.204, 13.348), vec2f(50.000, 15.000), vec2f(50.796, 13.348), vec2f(51.684, 11.771), vec2f(52.659, 10.274), vec2f(53.719, 8.859), vec2f(54.861, 7.533), vec2f(56.082, 6.299), vec2f(57.379, 5.161), vec2f(58.750, 4.125), vec2f(60.191, 3.194), vec2f(61.699, 2.373), vec2f(63.272, 1.666), vec2f(64.906, 1.078), vec2f(66.599, 0.613), vec2f(68.348, 0.275), vec2f(70.149, 0.070), vec2f(72.000, 0.000), vec2f(74.786, 0.139), vec2f(77.510, 0.551), vec2f(80.154, 1.226), vec2f(82.703, 2.156), vec2f(85.141, 3.333), vec2f(87.451, 4.746), vec2f(89.618, 6.388), vec2f(91.625, 8.250), vec2f(93.456, 10.323), vec2f(95.096, 12.598), vec2f(96.527, 15.066), vec2f(97.734, 17.719), vec2f(98.701, 20.547), vec2f(99.412, 23.543), vec2f(99.850, 26.697), vec2f(100.000, 30.000), vec2f(99.746, 34.784), vec2f(99.000, 39.398), vec2f(97.785, 43.860), vec2f(96.125, 48.188), vec2f(94.043, 52.397), vec2f(91.562, 56.508), vec2f(88.707, 60.536), vec2f(85.500, 64.500), vec2f(81.965, 68.417), vec2f(78.125, 72.305), vec2f(74.004, 76.181), vec2f(69.625, 80.062), vec2f(65.012, 83.968), vec2f(60.188, 87.914), vec2f(55.176, 91.919)
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
