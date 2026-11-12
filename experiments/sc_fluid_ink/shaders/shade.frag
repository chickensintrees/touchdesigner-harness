// Render the dye as liquid over paper.
// in0: dye (rgb = inks 0..2), in1: velocity field (rg velocity, b pressure), in2: paper / sheet texture
// style 0: absorbing ink in clear water over paper (Beer-Lambert), lit from the density gradient
// style 1: luminous ink in dark water
// style 2: 1-bit, ordered dither
// style 3: oil film on dark water (interference colours from thickness)
// style 4: survey drawing (contour lines of ink thickness on graph paper)
uniform vec4 uView;    // zoom, centre x, centre y (frame heights from centre), rotation
uniform vec4 uStyle;   // style, paper (0 plain, 1 sheet), refraction, bump
uniform vec4 uPaper;   // rgb; w = the sheet's width / height
uniform vec4 uInk0;    // rgb: the colour of a thick layer of ink 0; w = the sheet's height in frame heights
uniform vec4 uInk1;
uniform vec4 uInk2;
uniform vec4 uMore;    // invert (1-bit), sharpen, mirror (inkblot), bands (oil film / contour count)
uniform vec4 uFx;      // pulse, hit_low, hit_high, energy
uniform vec4 uTime;    // evolve, shot age, beat_pos, seed
out vec4 fragColor;

const float ASP = 16.0 / 9.0;

float hash(vec2 q) { return fract(sin(dot(q, vec2(127.1, 311.7))) * 43758.5453); }

// bilinear advection leaves a soft haze around sheared ink; this pulls thin ink down so edges stay edges
vec3 crisp(vec3 d) { return mix(d, d * smoothstep(vec3(0.0), vec3(0.5), d) * 1.15, uMore.y); }

float thick(vec3 d) { float h = d.r + d.g + d.b; return 1.0 - exp(-1.6 * h); }

float bayer4(ivec2 c) {
    int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
    return (float(m[(c.x & 3) + ((c.y & 3) << 2)]) + 0.5) / 16.0;
}

vec3 paperAt(vec2 duv) {
    vec2 p = (duv - 0.5) * vec2(ASP, 1.0);
    vec3 col = uPaper.rgb;
    if (uStyle.y > 2.5) {
        // the Input picture lies under the water, filling the frame
        return texture(sTD2DInputs[2], clamp(duv, vec2(0.001), vec2(0.999))).rgb;
    } else if (uStyle.y > 1.5) {
        // graph paper
        vec2 g1 = abs(fract(p / 0.05 + 0.5) - 0.5) * 0.05;
        vec2 g2 = abs(fract(p / 0.25 + 0.5) - 0.5) * 0.25;
        float l1 = 1.0 - smoothstep(0.0006, 0.0016, min(g1.x, g1.y));
        float l2 = 1.0 - smoothstep(0.0012, 0.0026, min(g2.x, g2.y));
        col = mix(col, col * vec3(0.66, 0.80, 0.70), max(l1 * 0.45, l2 * 0.9));
    } else if (uStyle.y > 0.5) {
        // the sheet (uPaper.w : 1, uInk0.w frame heights high): a little larger than the frame, slightly askew
        float a = 0.05 + (uTime.w - 0.5) * 0.12;
        vec2 q = mat2(cos(a), sin(a), -sin(a), cos(a)) * (p - vec2(0.05, -0.02));
        vec2 fuv = q / vec2(uPaper.w * uInk0.w, uInk0.w) + 0.5;
        vec3 f = texture(sTD2DInputs[2], fuv).rgb;
        float on = step(0.0, fuv.x) * step(fuv.x, 1.0) * step(0.0, fuv.y) * step(fuv.y, 1.0);
        col = mix(col * 0.62, col * f / 0.955, on);
    }
    // fibres
    float g = TDSimplexNoise(p * vec2(60.0, 240.0)) * 0.5 + TDSimplexNoise(p * 420.0) * 0.5;
    col *= 1.0 + 0.035 * g;
    return col;
}

void main() {
    vec2 uv = vUV.st;
    vec2 p = (uv - 0.5) * vec2(ASP, 1.0);
    float cr = cos(uView.w), sr = sin(uView.w);
    p = mat2(cr, sr, -sr, cr) * p / uView.x + uView.yz;
    vec2 duv = p / vec2(ASP, 1.0) + 0.5;
    vec2 puv = duv;                      // the paper is never mirrored
    float sx = 1.0;
    if (uMore.z > 0.5) {                 // inkblot: the left half of the tank, folded
        sx = duv.x > 0.5 ? -1.0 : 1.0;
        duv.x = 0.5 - abs(duv.x - 0.5);
    }

    vec2 e = 1.3 * uTD2DInfos[0].res.xy;
    vec3 d  = crisp(texture(sTD2DInputs[0], duv).rgb);
    vec3 dl = crisp(texture(sTD2DInputs[0], duv - vec2(e.x, 0.0)).rgb);
    vec3 dr = crisp(texture(sTD2DInputs[0], duv + vec2(e.x, 0.0)).rgb);
    vec3 db = crisp(texture(sTD2DInputs[0], duv - vec2(0.0, e.y)).rgb);
    vec3 dt = crisp(texture(sTD2DInputs[0], duv + vec2(0.0, e.y)).rgb);
    float h = thick(d);
    float hl = thick(dl), hr = thick(dr), hb = thick(db), ht = thick(dt);
    vec2 grad = vec2((hr - hl) * sx, ht - hb);
    float lap = hl + hr + hb + ht - 4.0 * h;

    // the water surface itself: pressure is its height, so a kick sends a ripple through the page
    vec2 ve = uTD2DInfos[1].res.xy;
    float pl = texture(sTD2DInputs[1], duv - vec2(ve.x, 0.0)).b;
    float prr = texture(sTD2DInputs[1], duv + vec2(ve.x, 0.0)).b;
    float pb = texture(sTD2DInputs[1], duv - vec2(0.0, ve.y)).b;
    float pt = texture(sTD2DInputs[1], duv + vec2(0.0, ve.y)).b;
    vec2 pgrad = clamp(vec2((prr - pl) * sx, pt - pb), vec2(-0.25), vec2(0.25));

    vec2 slope = grad * uStyle.w + pgrad * 2.2;
    vec3 n = normalize(vec3(-slope, 1.0));

    // paper seen through the water, bent by the surface
    vec3 paper = paperAt(puv + n.xy * uStyle.z);

    vec3 col;
    float style = uStyle.x;
    vec3 L = normalize(vec3(-0.45, 0.6, 0.66));
    vec3 Hh = normalize(L + vec3(0.0, 0.0, 1.0));
    float spec = pow(max(dot(n, Hh), 0.0), 90.0);
    float diff = dot(n, L) / L.z;      // 1 on flat water
    float wet = smoothstep(0.02, 0.35, h);

    if (style < 0.5) {
        vec3 k0 = -log(max(uInk0.rgb, vec3(0.02)));
        vec3 k1 = -log(max(uInk1.rgb, vec3(0.02)));
        vec3 k2 = -log(max(uInk2.rgb, vec3(0.02)));
        // pigment gathers at the edge of a drop
        float edge = clamp(length(grad) * 3.0, 0.0, 1.0);
        vec3 T = exp(-(k0 * d.r + k1 * d.g + k2 * d.b) * (1.25 + 0.9 * edge));
        col = paper * T;
        col *= mix(1.0, clamp(diff, 0.55, 1.5), 0.55 * wet + 0.12);
        col *= 1.0 - 0.9 * clamp(lap, -0.25, 0.25);          // lensing: thick ink bulges, thin edges brighten
        col += vec3(1.0, 0.98, 0.94) * spec * (0.10 + 0.75 * wet);
    } else if (style < 1.5) {
        vec3 em = uInk0.rgb * d.r + uInk1.rgb * d.g + uInk2.rgb * d.b;
        float edge = clamp(length(grad) * 2.5, 0.0, 1.0);
        col = paper * exp(-1.2 * h);
        col += em * (1.0 + 1.0 * edge) * clamp(diff, 0.5, 1.6);
        col += vec3(1.0, 0.95, 0.85) * spec * (0.05 + 0.6 * wet);
        col = 1.0 - exp(-1.35 * col);
    } else if (style > 3.5) {
        // survey: contour lines of thickness, every fourth one heavy, a light wash under them
        float t = d.r + d.g + d.b;
        float f = t * uMore.w + 0.5;
        float fw = fwidth(f) + 1e-4;
        float line = 1.0 - smoothstep(0.7, 1.5, abs(fract(f + 0.5) - 0.5) / fw);
        float idx = 1.0 - smoothstep(1.4, 2.6, abs(fract(f * 0.25 + 0.5) - 0.5) * 4.0 / fw);
        line = max(line, idx) * smoothstep(0.03, 0.08, t);
        vec3 inkc = (uInk0.rgb * d.r + uInk1.rgb * d.g + uInk2.rgb * d.b) / max(t, 1e-3);
        col = paper * mix(vec3(1.0), mix(vec3(1.0), inkc, 0.45), smoothstep(0.0, 0.9, t));
        col = mix(col, inkc * 0.75, line);
    } else if (style > 2.5) {
        // oil film: colour is interference, set by thickness and by the tilt of the surface
        float t = d.r + d.g * 1.6 + d.b * 2.3;
        float film = smoothstep(0.01, 0.14, t);
        float ph = t * uMore.w + 0.5 * dot(n.xy, vec2(1.0, 0.6));
        vec3 irid = 0.5 + 0.5 * cos(6.2832 * (ph * vec3(1.0, 1.15, 1.32) + vec3(0.0, 0.33, 0.67)));
        irid = mix(vec3(dot(irid, vec3(0.333))), irid, 1.25);
        col = paper * (1.0 - 0.6 * film) + irid * film * 0.8 * clamp(diff, 0.5, 1.6);
        col += vec3(1.0, 0.97, 0.9) * spec * (0.08 + 0.8 * film);
        col = 1.0 - exp(-1.5 * max(col, vec3(0.0)));
    } else {
        // 1-bit: tone from ink thickness and the lit surface, then an ordered dither on 2 px cells
        float tone = 1.0 - smoothstep(0.08, 0.75, h) * 1.05;
        tone *= mix(1.0, clamp(diff, 0.4, 1.6), 0.6 * wet);
        tone += spec * 1.5 * wet;
        tone = mix(tone, tone * dot(paper, vec3(0.333)) / max(dot(uPaper.rgb, vec3(0.333)), 0.01), 0.8);
        float th = bayer4(ivec2(gl_FragCoord.xy) / 2);
        float bit = step(th, clamp(tone, 0.0, 1.0));
        col = vec3(uMore.x > 0.5 ? 1.0 - bit : bit);
    }

    if (style < 1.5 || style > 2.5) {
        // drums in the light, a vignette
        col *= 1.0 + 0.07 * uFx.x;
        vec2 vq = (uv - 0.5) * vec2(1.0, 0.85);
        col *= 1.0 - 0.55 * dot(vq, vq);
        col += (hash(gl_FragCoord.xy + fract(uTime.x) * 91.0) - 0.5) * 0.012;
    }
    fragColor = TDOutputSwizzle(vec4(clamp(col, 0.0, 1.0), 1.0));
}
