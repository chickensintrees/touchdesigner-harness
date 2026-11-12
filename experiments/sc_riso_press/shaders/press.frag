// press.frag: the press bed seen from above. Sheets of paper travel along the feed;
// each plate of the separation is screened (dots / lines / grain, own angle) in paper
// space and overprinted, out of register. see: experiments/sc_riso_press/NOTES.md (2026-11-10)
// inputs: 0 sep (live sheet, plates in r,g,b,a)  1 hold (the previous sheet)  2 t_cap (Describe caption, sheet space)
uniform vec4 uView;    // centre x, y (sheet heights), view height, rotation
uniform vec4 uFeed;    // slide remaining 0..1, feed axis (0 x, 1 y), sheet counter, gap
uniform vec4 uLay;     // roller progress per plate on the live sheet
uniform vec4 uRegA;    // plate 0 xy, plate 1 xy register offset (sheet heights)
uniform vec4 uRegB;    // plate 2 xy, plate 3 xy
uniform vec4 uPl0, uPl1, uPl2, uPl3;   // ink index, screen (0 dot 1 line 2 grain 3 solid), angle, density
uniform vec4 uTone;    // screen frequency (cells per sheet height), dot gain, edge roughness, streaks
uniform vec4 uFm;      // per-plate frequency multiplier
uniform vec4 uPaper;   // rgb, opaque inks (1) or multiply (0)
uniform vec4 uBed;     // rgb, lanes (grid of sheets) on
uniform vec4 uMisc;    // marks on, margin, evolve, variant seed
uniform vec4 uFx;      // sheet skew, colourway chance, static misregister, flash
uniform vec4 uCam;     // perspective tilt (0 = straight down), pile mode, pile spread angle, pile spread offset
uniform vec4 uMode;    // reprint (new plates wipe over the old impression), negative on odd sheets, Describe (print the caption), -
uniform vec4 uInkB;    // per plate: second ink of a split fountain (below 0 = none)
out vec4 fragColor;

const vec2 SHEET = vec2(1.6, 1.0);

float h21(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, s, -s, c); }
float sdBox(vec2 p, vec2 b) { vec2 d = abs(p) - b; return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0); }

vec3 pal(float fi) {
    int i = int(fi + 0.5);
    if (i == 0) return vec3(1.00, 0.28, 0.55);   // fluorescent pink
    if (i == 1) return vec3(0.00, 0.60, 0.62);   // teal
    if (i == 2) return vec3(1.00, 0.84, 0.08);   // yellow
    if (i == 3) return vec3(0.098, 0.169, 0.231);// ident ink
    if (i == 4) return vec3(0.93, 0.30, 0.18);   // red
    if (i == 5) return vec3(0.12, 0.32, 0.80);   // blue
    if (i == 6) return vec3(0.40, 0.66, 0.26);   // green
    if (i == 7) return vec3(0.97, 0.95, 0.90);   // opaque white
    if (i == 8) return vec3(0.06, 0.06, 0.07);   // black
    if (i == 9) return vec3(1.00, 0.48, 0.12);   // fluorescent orange
    return vec3(0.46, 0.30, 0.76);               // violet
}
float altInk(float h) {
    int i = int(h * 8.0);
    if (i == 0) return 0.0; if (i == 1) return 1.0; if (i == 2) return 2.0; if (i == 3) return 4.0;
    if (i == 4) return 5.0; if (i == 5) return 6.0; if (i == 6) return 9.0; return 10.0;
}

float seg(vec2 p, vec2 c, vec2 hs) { vec2 d = abs(p - c) - hs; return step(max(d.x, d.y), 0.0); }

// printer's marks, per plate: register crosses (all plates), crop marks (key), colour bar
float marks(vec2 P, int i) {
    if (uMisc.x < 0.5) return 0.0;
    float m = uMisc.y, th = 0.0011, t = 0.0;
    for (int n = 0; n < 4; n++) {
        vec2 c = n == 0 ? vec2(-(0.8 - m * 0.5), 0.0) : n == 1 ? vec2(0.8 - m * 0.5, 0.0) : n == 2 ? vec2(0.0, 0.5 - m * 0.5) : vec2(0.0, -(0.5 - m * 0.5));
        vec2 d = P - c;
        t = max(t, seg(d, vec2(0.0), vec2(m * 0.36, th)));
        t = max(t, seg(d, vec2(0.0), vec2(th, m * 0.36)));
        t = max(t, step(abs(length(d) - m * 0.2), th));
    }
    if (i == 3) {
        vec2 a = abs(P), c = SHEET * 0.5 - m;
        t = max(t, seg(a, vec2(c.x + m * 0.5, c.y), vec2(m * 0.3, th)));
        t = max(t, seg(a, vec2(c.x, c.y + m * 0.5), vec2(th, m * 0.3)));
    }
    float w = m * 0.44;
    vec2 b = (P - vec2(-0.8 + m + 0.01, -(0.5 - m * 0.5) - w * 0.5)) / w;
    if (b.y > 0.0 && b.y < 1.0 && b.x > 0.0 && b.x < 12.0) {
        float n = floor(b.x);
        if (int(n / 3.0) == i) { float j = n - 3.0 * floor(n / 3.0); t = max(t, j < 0.5 ? 1.0 : j < 1.5 ? 0.6 : 0.3); }
    }
    return t;
}

vec4 sepAt(vec2 P, float usePrev) {
    vec2 uv = P / SHEET + 0.5;
    float inb = step(0.0, uv.x) * step(uv.x, 1.0) * step(0.0, uv.y) * step(uv.y, 1.0);
    return mix(texture(sTD2DInputs[0], uv), texture(sTD2DInputs[1], uv), usePrev) * inb;
}
float ch(vec4 v, int i) { return i == 0 ? v.r : i == 1 ? v.g : i == 2 ? v.b : v.a; }

void main() {
    vec2 sc = (vUV.st - 0.5) * vec2(16.0 / 9.0, 1.0);
    // optional tilt: the top of the frame recedes down the bed
    float wp = 1.0;
    vec2 scv = sc;
    if (uCam.x > 0.001) {
        wp = max(0.05, 1.0 - uCam.x * (sc.y + 0.5));
        scv = vec2(sc.x, sc.y + 0.5) / wp - vec2(0.0, 0.5);
    }
    vec2 p = rot(uView.w) * (scv * uView.z) + uView.xy;
    float pix = uView.z / 720.0 / (wp * wp);

    // ---- which sheet is under this pixel ----
    vec2 fd = uFeed.y < 0.5 ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec2 cd = vec2(fd.y, fd.x);
    float sf = dot(SHEET, fd), sx = dot(SHEET, cd);
    float pitch = sf + uFeed.w, lanep = sx + uFeed.w;
    float lanes = uBed.a;
    float j = lanes > 0.5 ? floor(dot(p, cd) / lanep + 0.5) : 0.0;
    float sgn = mod(abs(j), 2.0) > 0.5 ? -1.0 : 1.0;
    float f = sgn * dot(p, fd) + uFeed.x * pitch + (j == 0.0 ? 0.0 : h21(vec2(j, 3.3)) * pitch);
    float k = floor(f / pitch + 0.5);
    vec2 q = fd * (sgn * (f - k * pitch)) + cd * (dot(p, cd) - j * lanep);
    float sid = uFeed.z - k + j * 37.0;
    float live = (j == 0.0 && k == 0.0) ? 1.0 : 0.0;
    float blank = (j == 0.0 && k < 0.0) ? 1.0 : 0.0;
    float shAbove = 0.0;
    bool pile = uCam.y > 0.5;
    if (pile) {
        // a heap: the newest sheet is slapped on top at its own angle, older ones show underneath
        q = vec2(10.0);
        k = 9.0;
        for (int kk = 0; kk < 7; kk++) {
            float sk = uFeed.z - float(kk);
            float ang = (h21(vec2(sk, 5.5)) - 0.5) * uCam.z;
            vec2 off = (vec2(h21(vec2(sk, 6.1)), h21(vec2(sk, 9.4))) - 0.5) * uCam.w * SHEET;
            float scl = 1.0, land = 0.0;
            if (kk == 0) { land = uFeed.x; scl = 1.0 + 0.8 * land; ang += 0.5 * land * (h21(vec2(sk, 2.9)) - 0.5); }
            vec2 qk = rot(ang) * (p - off) / scl;
            if (sdBox(qk, SHEET * 0.5) < 0.0) { q = qk; k = float(kk); break; }
            float so = 0.024 + 0.25 * land;
            shAbove = max(shAbove, (1.0 - smoothstep(-0.02, 0.07 + 0.3 * land, sdBox(qk - vec2(0.75, -1.0) * so, SHEET * 0.5))) * (1.0 - 0.5 * land));
        }
        sid = uFeed.z - k;
        live = k == 0.0 ? 1.0 : 0.0;
        blank = 0.0;
    } else {
        q = rot((h21(vec2(sid, 1.7)) - 0.5) * uFx.x) * q + (vec2(h21(vec2(sid, 4.1)), h21(vec2(sid, 8.9))) - 0.5) * uFx.x * 0.25;
    }

    float edge = TDSimplexNoise(q * 40.0 + sid) * 0.0016;
    float dBox = sdBox(q, SHEET * 0.5) + edge;
    float onSheet = 1.0 - smoothstep(-pix, pix, dBox);

    // ---- bed ----
    vec3 bed = uBed.rgb * (0.82 + 0.10 * TDSimplexNoise(p * vec2(3.0, 60.0)) + 0.08 * TDSimplexNoise(p * 90.0));
    float rail = smoothstep(0.012, 0.0, abs(fract(dot(p, cd) * 2.5 + 0.5) - 0.5) * 0.4);
    bed += uBed.rgb * 0.5 * rail;
    float sh = 1.0 - smoothstep(-0.02, 0.07, sdBox(q - vec2(0.018, -0.024), SHEET * 0.5));
    bed *= 1.0 - 0.6 * (pile ? shAbove : sh);

    // ---- paper ----
    vec2 P = q;
    vec2 s = P / SHEET + 0.5;
    float fib = TDSimplexNoise(P * vec2(70.0, 240.0)) * 0.5 + TDSimplexNoise(P * 430.0) * 0.5;
    vec3 col = uPaper.rgb * (1.0 + 0.04 * fib) * (0.97 + 0.05 * h21(vec2(sid, 2.2)));
    col *= 1.0 - 0.10 * smoothstep(-0.012, 0.0, dBox);
    col *= 1.0 - 0.5 * shAbove;
    float rp0 = 0.0;

    float along = dot(P, fd), across = dot(P, cd);
    float opaque = uPaper.a;
    vec4 PL[4] = vec4[4](uPl0, uPl1, uPl2, uPl3);
    vec2 REG[4] = vec2[4](uRegA.xy, uRegA.zw, uRegB.xy, uRegB.zw);
    float gain = uTone.y;
    vec3 bar = vec3(0.0);
    float barA = 0.0;
    // Describe caption: every plate is knocked out in a thin halo around the letters, so the
    // caption reads over any amount of ink
    float halo = 0.0;
    if (uMode.z > 0.5) {
        vec2 cuv0 = P / SHEET + 0.5;
        halo = texture(sTD2DInputs[2], cuv0).r;
        for (int n = 0; n < 8; n++) {
            float an = float(n) * 0.7854;
            halo = max(halo, texture(sTD2DInputs[2], cuv0 + vec2(cos(an), sin(an)) * 3.0 / vec2(1024.0, 640.0)).r);
        }
        halo = smoothstep(0.2, 0.5, halo) * step(abs(P.x), 0.8) * step(abs(P.y), 0.5);
    }
    if (blank < 0.5) {
        for (int i = 0; i < 4; i++) {
            vec4 pl = PL[i];
            float fi = float(i);
            float inkidx = pl.x, dens = pl.w;
            // roller edge on the live sheet; in reprint mode the old impression stays ahead of it
            float e = uLay[i] * 1.25 - 0.12;
            float x = s.x + 0.006 * TDSimplexNoise(vec2(P.y * 25.0, fi));
            float rp = (live > 0.5 && uMode.x > 0.5) ? step(e, x) : 0.0;
            if (i == 0) rp0 = rp;
            float usePrev = live > 0.5 ? rp : 1.0;
            float sidI = sid - rp;
            float hv = h21(vec2(sidI * 0.37 + fi * 3.1, uMisc.w * 1.3 + fi));
            if (i < 3 && hv < uFx.y) inkidx = altInk(h21(vec2(sidI + fi, 7.7 + uMisc.w)));
            if (i < 3 && hv > 1.0 - uFx.y * 0.3 && uMode.z < 0.5) dens = 0.0;   // (no dropped plates in Describe: one may carry the word)
            dens *= 0.80 + 0.28 * h21(vec2(sidI * 1.3, fi * 5.7));
            vec2 reg = live * (1.0 - rp) * REG[i] + (vec2(h21(vec2(sidI, fi * 2.0 + 0.3)), h21(vec2(sidI * 1.7, fi * 2.0 + 1.1))) - 0.5) * uFx.z;
            vec2 Pi = P - reg;
            // in the margins the separation only carries the slug line: pure line art, no screen
            float inMargin = 1.0 - step(abs(Pi.x), 0.8 - uMisc.y) * step(abs(Pi.y), 0.5 - uMisc.y);
            float tx = ch(sepAt(Pi, usePrev), i);
            tx = mix(tx, smoothstep(0.3, 0.55, tx), inMargin);
            float tp = max(tx, marks(Pi, i));
            float freq = uTone.x * uFm[i];
            float aa = max(freq * pix * 0.8, 0.02);
            mat2 R = rot(pl.z);
            vec2 g = R * Pi * freq;
            float n = TDSimplexNoise(Pi * freq * 2.3 + fi * 17.0) * uTone.z;
            float ink;
            if (pl.y < 0.5) {
                vec2 cell = floor(g) + 0.5;
                vec2 Pc = (transpose(R) * cell) / freq;
                float tc = max(ch(sepAt(Pc, usePrev), i) * (1.0 - inMargin), marks(Pc, i));
                float r = sqrt(tc) * 0.74 * gain;
                ink = (1.0 - smoothstep(r - aa, r + aa, length(g - cell) + n * 0.16)) * step(0.01, tc) * (1.0 - smoothstep(0.86, 0.95, tc));
            } else if (pl.y < 1.5 || pl.y > 3.5) {
                // line family: 1 straight, 4 concentric rings, 5 guilloche waves, 6 cross-hatch
                float w = tp * 0.52 * gain;
                float gl = g.y;
                if (pl.y > 3.5 && pl.y < 4.5) {
                    vec2 c = (vec2(h21(vec2(fi + 0.7, floor(uMisc.w) + 1.0)), h21(vec2(fi + 3.0, floor(uMisc.w)))) - 0.5) * SHEET * 0.8
                           + 0.035 * vec2(sin(uMisc.z * 0.6 + fi * 2.0), cos(uMisc.z * 0.47 + fi));
                    gl = length(Pi - c) * freq;
                } else if (pl.y > 4.5 && pl.y < 5.5) {
                    gl = g.y + 1.5 * sin(g.x * 0.19 + fi * 1.7) + 0.7 * sin(g.x * 0.57 - fi * 2.0 + uMisc.z * 0.25);
                }
                ink = (1.0 - smoothstep(w - aa, w + aa, abs(fract(gl) - 0.5) + n * 0.10)) * step(0.01, tp);
                if (pl.y > 5.5) {
                    float w2 = (tp - 0.42) * 0.8 * gain;
                    ink = max(ink, (1.0 - smoothstep(w2 - aa, w2 + aa, abs(fract(g.x) - 0.5) + n * 0.10)) * step(0.42, tp));
                }
            } else if (pl.y < 2.5) {
                float nn = 0.5 + 0.35 * TDSimplexNoise(Pi * freq * 1.7 + fi * 31.0) + 0.3 * (h21(floor(Pi * freq * 4.0) + fi) - 0.5);
                ink = smoothstep(-0.05, 0.05, tp * gain * 1.05 - nn) * step(0.01, tp);
            } else {
                ink = tp;
            }
            // screens too fine for the pixel grid print as their average tone instead of aliasing
            if (pl.y < 2.5 || pl.y > 3.5) ink = mix(ink, clamp(tp * gain * 1.25, 0.0, 1.0), smoothstep(0.3, 0.6, aa));
            ink = max(ink, smoothstep(0.86, 0.96, tp + n * 0.25));   // line art stays solid, with a rough edge

            float st = TDSimplexNoise(vec2(across * 13.0 + sidI * 3.1 + fi * 9.0, along * 0.45 + uMisc.z * 0.15));
            float streak = 1.0 - uTone.w * smoothstep(0.2, 0.75, st) * (0.55 + 0.45 * TDSimplexNoise(vec2(across * 120.0, along * 1.5 + fi)));
            float mott = 0.86 + 0.14 * TDSimplexNoise(P * 250.0 + fi * 11.0);
            float speck = smoothstep(0.66, 0.74, TDSimplexNoise(P * 150.0 + fi * 4.0 + sid));
            float a = ink * clamp(dens * streak * mott, 0.0, 1.0) * (1.0 - 0.75 * speck);
            a *= 1.0 - halo;
            if (i == 3 && uMode.z > 0.5) {
                // Describe caption: key ink, clean line art (no screen, no streaks), in register with the key
                vec2 cuv = Pi / SHEET + 0.5;
                float cin = step(0.0, cuv.x) * step(cuv.x, 1.0) * step(0.0, cuv.y) * step(cuv.y, 1.0);
                a = max(a, smoothstep(0.3, 0.55, texture(sTD2DInputs[2], cuv).r) * cin * (0.86 + 0.10 * mott) * (1.0 - 0.4 * speck));
            }
            vec3 inkc = pal(inkidx);
            if (uInkB[i] > -0.5) inkc = mix(inkc, pal(uInkB[i]), smoothstep(0.15, 0.85, s.y + 0.10 * TDSimplexNoise(vec2(s.x * 3.0, fi + sidI))));
            if (live > 0.5) {
                if (uMode.x < 0.5) a *= step(x, e);
                if (uLay[i] > 0.0 && uLay[i] < 1.0) {
                    float bb = exp(-pow((x - e - 0.012) / 0.014, 2.0));
                    bar = mix(bar, inkc * 0.55, bb);
                    barA = max(barA, bb);
                    a = min(1.0, a * (1.0 + 0.6 * exp(-(e - x) * 16.0)));
                }
            }
            col = opaque > 0.5 ? mix(col, inkc, a) : col * mix(vec3(1.0), inkc, a);
        }
    }
    if (uMode.y > 0.5 && mod(sid - rp0, 2.0) > 0.5) col = clamp(vec3(1.0) - col, 0.0, 1.0);
    col = mix(col, bar, barA * 0.85);
    col = mix(bed, col, onSheet);
    if (uCam.x > 0.001) col = mix(col, uBed.rgb * 1.5 + 0.02, smoothstep(0.45, 0.05, wp) * 0.9);

    // overhead work light, flash on impression
    float v = dot(sc, sc);
    col *= 1.06 - 0.30 * v;
    col += uFx.w * vec3(0.10, 0.09, 0.07) * (1.0 - v);
    col += (h21(vUV.st * 913.0 + uMisc.z) - 0.5) * 0.012;
    fragColor = TDOutputSwizzle(vec4(max(col, 0.0), 1.0));
}
