// What gets laid down as crisp ink: a phrase, a page of small print, model silhouettes,
// marbling stripes or halftone drops. rgb = amount of inks 0..2.
// in0: the shape (Text TOP, page of text, or model render; chosen by a Switch TOP)
uniform vec4 uSrc;   // mode, scale, rotation, copies
uniform vec4 uPos;   // x, y offset from centre in frame heights, seed, section
uniform vec4 uSel;   // ink A, ink B, evolve, unused
// in1: the Input picture (another scene's output), in2: its average colour (1x1)
uniform vec4 uIn;    // 1 = lay the Input picture down instead of the shape, hue split, ink amount, unused
uniform vec4 uInR;   // tone range: ink starts at lo, is full at hi (distance from the picture's average brightness)
out vec4 fragColor;

const float ASP = 16.0 / 9.0;

vec3 ink(float i) {
    if (i < 0.5) return vec3(1.0, 0.0, 0.0);
    if (i < 1.5) return vec3(0.0, 1.0, 0.0);
    if (i < 2.5) return vec3(0.0, 0.0, 1.0);
    return vec3(0.6);
}
float hash(vec2 q) { return fract(sin(dot(q, vec2(127.1, 311.7))) * 43758.5453); }
float inside(vec2 uv) { return step(0.0, uv.x) * step(uv.x, 1.0) * step(0.0, uv.y) * step(uv.y, 1.0); }

void main() {
    vec2 uv = vUV.st;
    vec2 p = (uv - 0.5) * vec2(ASP, 1.0);
    float cr = cos(uSrc.z), sr = sin(uSrc.z);
    vec2 q = mat2(cr, sr, -sr, cr) * (p - uPos.xy) / uSrc.y;
    float mode = uSrc.x;
    vec3 col = vec3(0.0);
    // the shape alternates between two inks section by section
    float which = mod(floor(uPos.w), 2.0) < 0.5 ? uSel.x : uSel.y;

    if (uIn.x > 0.5) {
        // Input: the picture becomes ink. Whatever stands out from its average brightness is the
        // subject (bright things on a dark picture, dark things on a pale one); neutral tones go to
        // this take's own ink, and the picture's hues are split across the three inks.
        vec3 c = texture(sTD2DInputs[1], uv).rgb;
        float lum = dot(c, vec3(0.3, 0.6, 0.1));
        float mean = dot(texture(sTD2DInputs[2], vec2(0.5)).rgb, vec3(0.3, 0.6, 0.1));
        float t = abs(lum - mean) / max(max(mean, 1.0 - mean), 0.25);
        t = smoothstep(uInR.x, uInR.y, t);
        float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b));
        float sat = (mx - mn) / max(mx, 1e-3);
        vec3 hw = (c - mn) / max(mx - mn, 1e-3);
        hw /= max(hw.r + hw.g + hw.b, 1e-3);
        col = mix(ink(which), hw, clamp(sat * uIn.y, 0.0, 1.0)) * t * uIn.z;
    } else if (mode < 0.5) {               // phrase
        vec2 suv = q / vec2(ASP, 1.0) + 0.5;
        float m = smoothstep(0.38, 0.62, texture(sTD2DInputs[0], suv).r) * inside(suv);
        col = ink(which) * m;
    } else if (mode < 1.5) {               // model silhouettes, in a row
        float n = max(1.0, uSrc.w);
        float cw = 1.15;
        float x = q.x + cw * n * 0.5;
        float cell = floor(x / cw);
        vec2 g = vec2(mod(x, cw) - cw * 0.5, q.y);
        vec2 suv = g + 0.5;
        vec4 t = texture(sTD2DInputs[0], suv);
        float lum = dot(t.rgb, vec3(0.3, 0.6, 0.1));
        float m = smoothstep(0.3, 0.7, t.a) * mix(1.0, 0.35, smoothstep(0.05, 0.75, lum));
        m *= inside(suv) * step(0.0, cell) * step(cell, n - 0.5);
        col = ink(mod(which + cell, 3.0)) * m;
    } else if (mode < 2.5) {               // page of small print
        vec2 suv = q / vec2(ASP, 1.0) + 0.5;
        float m = smoothstep(0.3, 0.6, texture(sTD2DInputs[0], suv).r) * inside(suv);
        col = ink(which) * m;
    } else if (mode < 3.5) {               // marbling: bands of the three inks, slightly wavy
        float s = q.y * 9.0 + 0.35 * sin(q.x * 5.0 + uPos.z * 40.0) + uPos.z * 7.0;
        float band = floor(s);
        float f = fract(s);
        float m = smoothstep(0.0, 0.06, f) * (1.0 - smoothstep(0.62, 0.68, f));
        float k = mod(band, 4.0);
        col = k < 2.5 ? ink(k) * m : vec3(0.0);
    } else if (mode < 4.5) {               // three fat drops, one of each ink; the drums bring the rest
        for (int i = 0; i < 3; i++) {
            float fi = float(i);
            vec2 c = vec2(hash(vec2(uPos.z * 91.0, fi)) - 0.5, hash(vec2(fi + 3.0, uPos.z * 57.0)) - 0.5) * vec2(1.3, 0.6);
            float rr = mix(0.06, 0.13, hash(vec2(fi * 7.0, uPos.z * 13.0)));
            col += ink(fi) * (1.0 - smoothstep(rr - 0.004, rr, length(p - c)));
        }
    } else if (mode > 5.5) {               // inkblot: ragged blots left of the fold, new ones each section
        for (int i = 0; i < 5; i++) {
            float fi = float(i);
            vec2 hs = vec2(uPos.z * 91.0 + uPos.w * 3.7, fi * 5.3);
            vec2 c = vec2(-0.04 - 0.5 * hash(hs), (hash(hs + 7.1) - 0.5) * 0.66);
            vec2 dd = p - c;
            float ang = atan(dd.y, dd.x);
            float rr = mix(0.035, 0.12, hash(hs + 2.3)) * (1.0 + 0.3 * sin(ang * 3.0 + fi * 2.0) + 0.18 * sin(ang * 7.0 + uPos.z * 30.0));
            float m = 1.0 - smoothstep(rr - 0.004, rr, length(dd));
            col = max(col, (i == 3 ? ink(uSel.y) : ink(uSel.x)) * m);
        }
    } else {                               // halftone: drops whose size is the phrase
        float sp = 0.028;
        vec2 cellp = floor(p / sp + 0.5);
        vec2 cc = cellp * sp;
        cr = cos(uSrc.z); sr = sin(uSrc.z);
        vec2 cq = mat2(cr, sr, -sr, cr) * (cc - uPos.xy) / uSrc.y;
        vec2 suv = cq / vec2(ASP, 1.0) + 0.5;
        float m = texture(sTD2DInputs[0], suv).r * inside(suv);
        float r = sp * mix(0.24, 0.52, m);
        float dd = length(p - cc);
        float dot_ = 1.0 - smoothstep(r - 0.0025, r + 0.0005, dd);
        float k = m > 0.5 ? which : mod(which + 1.0 + mod(cellp.x + cellp.y, 2.0), 3.0);
        col = ink(k) * dot_;
    }
    fragColor = TDOutputSwizzle(vec4(col, max(col.r, max(col.g, col.b))));
}
