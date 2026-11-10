// Curtain reveal. Rewritten in WGSL from the block curtain-reveal (see NOTICE.txt).
// The curtains close over the first clip and open onto the second. The source only opens; at both
// ends the gathered curtains and the pelmet slide off the frame.

// GSAP powerN.inOut: an exponent of N + 1.
fn ease_in_out(t: f32, power: f32) -> f32 {
    let e = power + 1.0;
    return select(1.0 - pow(2.0 * (1.0 - t), e) * 0.5, pow(2.0 * t, e) * 0.5, t < 0.5);
}

const FOLDS = 11u;
var<private> LEFT_WIDTHS: array<f32, 11> = array<f32, 11>(88.0, 124.0, 70.0, 106.0, 136.0, 80.0, 112.0, 62.0, 98.0, 130.0, 69.0);
var<private> RIGHT_WIDTHS: array<f32, 11> = array<f32, 11>(104.0, 66.0, 128.0, 84.0, 120.0, 62.0, 100.0, 134.0, 76.0, 112.0, 89.0);
const PX = 0.052083332; // percent of the width of one pixel at 1920

struct Palette { dark: vec3f, mid: vec3f, light: vec3f, sheen: vec3f, pelmet: vec3f };

fn hex(v: u32) -> vec3f {
    return vec3f(f32((v >> 16u) & 255u), f32((v >> 8u) & 255u), f32(v & 255u)) / 255.0;
}

fn palette(tone: i32) -> Palette {
    if (tone == 0) { return Palette(hex(0x3d0810u), hex(0x8a1a26u), hex(0xb23345u), hex(0xcc5c6eu), hex(0x4a0e1au)); }
    if (tone == 2) { return Palette(hex(0x070d1fu), hex(0x152a5cu), hex(0x274a8fu), hex(0x4f72b4u), hex(0x0c1836u)); }
    if (tone == 3) { return Palette(hex(0x0c1f13u), hex(0x1f4a2bu), hex(0x356b3fu), hex(0x5c9166u), hex(0x12291au)); }
    return Palette(hex(0x2b0912u), hex(0x5c1a2cu), hex(0x7d2c42u), hex(0xa04c62u), hex(0x3a0f1eu));
}

fn fold_color(t: f32, crest: f32, pal: Palette) -> vec3f {
    let stops = array<f32, 7>(0.0, 0.2, crest - 0.14, crest, crest + 0.10, 0.8, 1.0);
    let colors = array<vec3f, 7>(pal.dark, pal.mid, pal.light, pal.sheen, pal.light, pal.mid, pal.dark);
    var i = 0;
    while (i < 5 && t > stops[i + 1]) { i += 1; }
    return mix(colors[i], colors[i + 1], clamp((t - stops[i]) / max(stops[i + 1] - stops[i], 1e-5), 0.0, 1.0));
}

// One curtain: rgb, coverage. x is percent from the outer edge of the curtain, y percent of the height.
fn curtain(x: f32, y: f32, draw: f32, hide: f32, right: bool, pal: Palette) -> vec4f {
    var total = 0.0;
    var gathered = 0.0;
    for (var i = 0u; i < FOLDS; i += 1u) {
        let w = select(LEFT_WIDTHS[i], RIGHT_WIDTHS[i], right) * PX;
        let u = f32(i) / f32(FOLDS - 1u);
        total += w;
        gathered += w * (1.0 - (0.86 - 0.16 * u));
    }
    let anchor = 51.0 - total;
    var cursor = anchor - hide * (anchor + gathered + 1.0);
    var result = vec4f(0.0);
    for (var i = 0u; i < FOLDS; i += 1u) {
        let w = select(LEFT_WIDTHS[i], RIGHT_WIDTHS[i], right) * PX;
        let u = f32(i) / f32(FOLDS - 1u);
        let sx = 1.0 - draw * (0.86 - 0.16 * u);
        let sy = 1.0 - draw * 0.07 * u * u;
        let width = w * sx;
        if (x >= cursor && x < cursor + width + 0.2) {
            let t = clamp((x - cursor) / max(width, 1e-5), 0.0, 1.0);
            let hem_arc = 1.6 * (1.0 - sqrt(max(0.0, 1.0 - (2.0 * t - 1.0) * (2.0 * t - 1.0))));
            if (y <= sy * 100.0 - hem_arc) {
                let crest = (44.0 + f32((i * 5u) % 13u)) * 0.01;
                let local = y / (sy * 100.0);
                var c = fold_color(select(t, 1.0 - t, right), crest, pal);
                var black = 0.0;
                if (local < 0.16) { black = 0.45 * (1.0 - local / 0.16); }
                if (local > 0.82) { black = 0.5 * (local - 0.82) / 0.18; }
                c = mix(c, vec3f(0.0), black);
                c = mix(c, vec3f(0.0), 0.34 * (1.0 - sx));
                result = vec4f(c, 1.0);
            }
        }
        cursor += width;
    }
    return result;
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) id: vec3u) {
    if (!gpufx_in_bounds(id)) { return; }
    let p = clamp(params.progress, 0.0, 1.0);
    if (p <= 0.0) {
        gpufx_write(id, textureLoad(first, vec2i(id.xy), 0));
        return;
    }
    if (p >= 1.0) {
        gpufx_write(id, textureLoad(second, vec2i(id.xy), 0));
        return;
    }
    let uv = gpufx_uv(id);
    let x = uv.x * 100.0;
    let y = uv.y * 100.0;
    let s = abs(2.0 * p - 1.0);
    let draw = ease_in_out(s, 2.0);
    let hide = smoothstep(0.8, 1.0, s);
    let pal = palette(params.tone);

    var color: vec4f;
    if (p < 0.5) {
        color = textureSampleLevel(first, smp, uv, 0.0);
    } else {
        color = textureSampleLevel(second, smp, uv, 0.0);
        if (params.spotlight != 0u) {
            let opening = (p - 0.5) * 2.0;
            let ellipse = (vec2f(x, y) - vec2f(50.0, 44.0)) / vec2f(34.0, 52.0);
            let glow = 0.42 * max(0.0, 1.0 - length(ellipse) / 0.72);
            let envelope = 0.9 * smoothstep(0.25, 0.7, opening) * (1.0 - smoothstep(0.85, 1.0, opening));
            let a = glow * envelope;
            color = vec4f(color.rgb + a * vec3f(1.0, 0.769, 0.502) * (vec3f(1.0) - color.rgb), color.a);
        }
    }

    let left = curtain(x, y, draw, hide, false, pal);
    let right = curtain(100.0 - x, y, draw, hide, true, pal);
    color = vec4f(mix(color.rgb, left.rgb, left.a), color.a);
    color = vec4f(mix(color.rgb, right.rgb, right.a), color.a);

    if (params.pelmet != 0u) {
        let wave = 78.0 + 14.0 * sin((1.0 - uv.x) * 15.707964);
        let hem = 11.0 * wave * 0.01 - hide * 11.0;
        if (y <= hem) { color = vec4f(pal.pelmet, color.a); }
    }
    gpufx_write(id, color);
}
