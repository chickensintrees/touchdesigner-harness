// Light the chemistry. Three layers on a sheet of paper under fluorescent tubes:
//   1. the impression: flat rubber-stamp ink, always legible
//   2. the living ink: the reaction-diffusion field as a raised bead (gold leaf, red
//      enamel, black tar or white correction fluid)
//   3. the light: an orbiting key light and a ceiling of tubes in reflection
// The take picks the camera (uTake.x), the paper (uTake.z) and the ink (uSec.w).
// Inputs: 0 smoothed state (G = V for height, B trace, A impression),
//         1 stamp mask (full res), 2 form print.
// Output is linear HDR, alpha = blur circle for grade.frag's depth of field.
uniform vec4 uCam;   // evolve, beat_pos, bar_pulse, pulse
uniform vec4 uHit;   // hit_low, hit_mid, hit_high, energy
uniform vec4 uSec;   // section, kick, hold, ink (0 gold leaf, 1 red enamel, 2 black tar, 3 white, 4 by tile)
uniform vec4 uPose;  // stamp angle, stamp centre x, y, section_pos
uniform vec4 uTake;  // camera (0 desk dolly, 1 macro, 2 top-down, 3 raking), stamp mode, paper (0 cream + print, 1 the form's own colour, 2 flat, 3 flat with no edge), share of the form's height shown
uniform vec4 uShot;  // seed, age (s), tile columns, tile rows
uniform vec4 uPaper; // flat paper colour (linear), w = tiles are framed
uniform vec4 uCamP;  // top-down half height, roll, depth of field strength, key light gain
uniform vec4 uInk;   // impression strength, 1 = the impression is a pale transfer (for a dark paper), unused x2
out vec4 fragColor;

const vec3 CREAM = vec3(0.846, 0.767, 0.577);   // #EDE3C8, linear
const vec3 INK = vec3(0.47, 0.050, 0.045);      // multiplies cream to #A8322B
const vec3 NAVY = vec3(0.030, 0.052, 0.105);    // multiplies cream to about ident ink #192B3B
const vec3 DESK = vec3(0.016, 0.024, 0.022);
const vec3 GOLD = vec3(1.00, 0.62, 0.20);

float height(vec2 uv) {
    float v = texture(sTD2DInputs[0], uv).g;
    return smoothstep(0.12, 0.42, v);
}
float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

// what the ink reflects: a dim office ceiling with pairs of fluorescent tubes
vec3 ceiling(vec3 P, vec3 r, float drift) {
    float up = clamp(r.z, 0.0, 1.0);
    vec3 env = mix(vec3(0.045, 0.040, 0.032), vec3(0.15, 0.165, 0.13), up * up);
    if (r.z > 0.02) {
        vec3 c = P + r * ((2.2 - P.z) / r.z);
        float x = abs(fract(c.x / 1.5 + drift) - 0.5) * 1.5;
        float pair = smoothstep(0.085, 0.03, abs(x - 0.12));
        float seg = smoothstep(0.48, 0.42, abs(fract(c.y / 2.6 + 0.2) - 0.5));
        env += vec3(0.86, 0.95, 0.78) * pair * seg * 3.2;
    }
    return env;
}

void main() {
    vec2 scr = (vUV.st - 0.5) * vec2(16.0 / 9.0, 1.0);
    float ev = uCam.x;
    int cam = int(uTake.x + 0.5);
    int pm = int(uTake.z + 0.5);
    float seed = uShot.x;
    float side = fract(seed * 13.7) > 0.5 ? 1.0 : -1.0;
    float arr = exp(-uShot.y * 7.0);            // 1 at the cut, gone in half a second
    float sp = clamp(uPose.w, 0.0, 1.0);

    vec3 ro, ta;
    vec3 upH = vec3(0.0, 0.0, 1.0);
    float foc = 1.22;
    float roll = 0.05 * sin(ev * 0.06);
    if (cam == 1) {
        // macro: a few centimetres above the paper, riding along the phrase
        float trav = (fract(seed * 7.3) - 0.5) * 0.55 + side * (sp - 0.5) * 0.22 + 0.02 * sin(ev * 0.3);
        ta = vec3(uPose.y + trav, uPose.z + (fract(seed * 3.1) - 0.5) * 0.16, 0.0);
        ro = ta + vec3(side * 0.13, -0.21, 0.055 + 0.015 * sin(ev * 0.11));
        foc = 1.5;
        roll = side * 0.10 + 0.04 * sin(ev * 0.07);
    } else if (cam == 2) {
        // top-down
        float Z = uCamP.x;
        vec2 room = 0.8 * max(vec2(8.0 / 9.0, 0.5) - Z * vec2(16.0 / 9.0, 1.0), 0.0);
        vec2 c = room * vec2(sin(ev * 0.11 + seed * 6.28), cos(ev * 0.08 + seed * 9.0));
        ro = vec3(c, Z * 2.0 * foc);
        ta = vec3(c, 0.0);
        upH = vec3(0.0, 1.0, 0.0);
        roll = uCamP.y * side + 0.03 * sin(ev * 0.06 + seed * 5.0);
    } else if (cam == 3) {
        // raking: from one end of the phrase, almost along the paper
        ta = vec3(side * (0.05 + 0.25 * sp) + 0.05 * sin(ev * 0.1), (fract(seed * 5.7) - 0.5) * 0.14, 0.0);
        ro = vec3(side * (-0.90 + 0.30 * sp), -0.30 + 0.20 * (fract(seed * 9.3) - 0.5), 0.30);
        foc = 1.35;
        roll = -side * 0.07;
    } else {
        // desk: every section starts wide on the whole form (the stamp lands, readable)
        // and dollies down into a macro shot tracking along the phrase.
        float push = 0.62 * (1.0 - (1.0 - sp) * (1.0 - sp));
        float dir = mod(floor(uSec.x + 0.5), 2.0) * 2.0 - 1.0;
        vec3 roW = vec3(0.13 * sin(ev * 0.09), -0.66 + 0.08 * sin(ev * 0.13), 1.04);
        vec3 taW = vec3(0.07 * sin(ev * 0.07 + 1.0), -0.03 + 0.04 * cos(ev * 0.05), 0.0);
        vec3 taC = vec3(uPose.y + dir * (sp - 0.5) * 0.12, uPose.z, 0.0);
        vec3 roC = taC + vec3(dir * 0.16, -0.50, 0.46);
        ro = mix(roW, roC, push);
        ta = mix(taW, taC, push);
    }
    // arrival: the camera comes down onto the page with the stamp; kicks punch in
    float d0 = length(ta - ro);
    ro += normalize(ta - ro) * d0 * (0.04 * uCam.z + 0.075 * uSec.y - 0.55 * arr);
    roll += 0.16 * arr * side;
    vec3 fw = normalize(ta - ro);
    vec3 rt = normalize(cross(fw, upH));
    vec3 up = cross(rt, fw);
    vec2 spr = mat2(cos(roll), sin(roll), -sin(roll), cos(roll)) * scr;
    vec3 rd = normalize(fw * foc + rt * spr.x + up * spr.y);

    float t = -ro.z / rd.z;
    if (rd.z > -1e-4) t = 50.0;
    vec3 P = ro + rd * t;
    vec2 uv = P.xy / vec2(16.0 / 9.0, 1.0) + 0.5;
    vec2 edge = abs(P.xy) - vec2(8.0 / 9.0, 0.5);
    float outside = max(edge.x, edge.y);
    if (pm == 3) {
        outside = -1.0;
        uv = 1.0 - abs(1.0 - mod(uv, 2.0));      // no page edge: mirror the field
    }
    float tf = length(ta - ro);
    float coc = clamp(abs(t - tf) / tf * uCamP.z, 0.0, 1.0);

    // key light: one orbit per 32 beats, breathing on the beat
    float la = uCam.y * 0.19635 + seed * 6.28;
    vec3 Lp = vec3(uPose.y * 0.5 + 0.62 * cos(la), 0.12 + 0.42 * sin(la), 0.42);
    if (cam == 1) Lp = vec3(ta.x + 0.30 * cos(la), ta.y + 0.12 + 0.22 * sin(la), 0.24);
    if (cam == 3) Lp = vec3(ta.x * 0.5 + 0.50 * cos(la), ta.y + 0.2 + 0.35 * sin(la), 0.36);
    vec3 L = normalize(Lp - P);
    float ld = length(Lp - P);
    float atten = 1.0 / (0.30 + 2.8 * ld * ld);
    const vec3 LAMP = vec3(1.0, 0.84, 0.62);        // desk lamp
    const vec3 AMB = vec3(0.050, 0.068, 0.056);     // fluorescent spill
    vec3 V = normalize(ro - P);
    float key = (0.80 + 0.30 * uCam.w) * uCamP.w;
    float drift = ev * 0.012;

    vec3 col;
    if (outside > 0.0) {
        // desk blotter with the page's shadow
        float sh = smoothstep(0.0, 0.10, outside);
        col = DESK * (0.5 + 1.6 * LAMP * max(L.z, 0.0) * atten * key) * mix(0.2, 1.0, sh);
        col += 0.028 * ceiling(P, reflect(-V, vec3(0.0, 0.0, 1.0)), drift);
    } else {
        vec4 raw = texture(sTD2DInputs[0], uv);
        float mask = texture(sTD2DInputs[1], uv).r;
        float e1 = 1.0 / 640.0;
        float h = height(uv);
        float hx = height(uv + vec2(e1, 0.0)) - height(uv - vec2(e1, 0.0));
        float hy = height(uv + vec2(0.0, e1 * 16.0 / 9.0)) - height(uv - vec2(0.0, e1 * 16.0 / 9.0));

        // which ink: one for the shot, or one per tile on a sheet of approvals
        float matv = uSec.w;
        if (matv > 3.5) {
            vec2 g = uv * uShot.zw;
            if (uPaper.w < 0.5) g.x += 0.5 * mod(floor(g.y), 2.0);
            matv = floor(hash21(floor(g) * 2.3 + seed * 7.0) * 3.0);
        }
        float gold = 1.0 - step(0.5, matv);
        float white = step(2.5, matv);
        float tar = step(1.5, matv) * (1.0 - white);

        // ---- paper and print ----
        float fib = TDSimplexNoise(P.xy * vec2(90.0, 260.0)) * 0.5 + TDSimplexNoise(P.xy * 420.0) * 0.5;
        vec2 gn = vec2(TDSimplexNoise(P.xy * 300.0), TDSimplexNoise(P.xy * 300.0 + 9.0));
        vec3 Np = normalize(vec3(0.05 * gn, 1.0));
        vec2 fuv = vec2(uv.x, 1.0 - (1.0 - uv.y) * uTake.w);
        vec3 ftex = texture(sTD2DInputs[2], fuv).rgb;
        vec3 paper;
        if (pm == 0) {
            paper = CREAM * (1.0 + 0.035 * fib);
            paper = mix(paper, vec3(0.10, 0.10, 0.13), smoothstep(0.1, 0.7, 1.0 - ftex.g) * 0.36);
        } else if (pm == 1) {
            paper = pow(ftex, vec3(2.2)) * (1.0 + 0.035 * fib);
        } else {
            paper = uPaper.rgb * (1.0 + 0.06 * fib);
        }

        // ---- the impression: flat stamp ink, patchy like a real rubber stamp ----
        float age = raw.a;
        float imp = max(mask * min(1.0, age * 2.2), (1.0 - mask) * age * age);
        float patchy = 0.90 + 0.12 * TDSimplexNoise(P.xy * 34.0) + 0.08 * fib;
        float drop = smoothstep(-0.75, -0.35, TDSimplexNoise(P.xy * 11.0 + 3.0));
        imp = clamp(imp * patchy * mix(0.72, 1.0, drop), 0.0, 1.0) * uInk.x;
        float wet = mask * uSec.y * uInk.x;              // a kick re-inks it: wet for a moment
        // ink absorbs (Beer-Lambert). Under gold the stamp is warning-label red; under red
        // enamel it is navy, because red beads on a red stamp could not be read (16_360.png).
        // White ink on carbon paper cannot absorb: it is a chalky transfer instead.
        vec3 dyed = paper * pow(mix(NAVY, INK, max(gold, tar)), vec3(clamp(imp * 0.95 + wet * 0.35, 0.0, 1.3)));
        vec3 chalk = mix(paper, vec3(0.42, 0.50, 0.58), clamp(imp * 0.8 + wet * 0.3, 0.0, 1.0));
        paper = mix(dyed, chalk, max(white, uInk.y));
        // where the living ink has been, a faint blot stays behind
        paper = mix(paper, paper * vec3(0.95, 0.70, 0.62), smoothstep(0.05, 1.0, raw.b) * 0.5 * (1.0 - white));

        // contact shadow thrown by the raised ink
        float hs = height(uv + normalize(L.xy + 1e-4) * vec2(0.5625, 1.0) * 0.008);
        float shadow = 1.0 - 0.78 * clamp((hs - h) * 1.8, 0.0, 1.0);

        float ndlp = max(dot(Np, L), 0.0);
        vec3 pcol = paper * (AMB * 1.6 + LAMP * 1.75 * ndlp * atten * key) * shadow;
        vec3 Hh = normalize(L + V);
        pcol += vec3(1.0, 0.92, 0.88) * pow(max(dot(Np, Hh), 0.0), 30.0) * (wet * 1.2 + imp * 0.10) * atten * key;
        // carbon paper has a waxy sheen
        if (pm == 2) pcol += 0.05 * ceiling(P, reflect(-V, Np), drift);

        // ---- the living ink ----
        float bump = mix(1.7, 1.35, gold);
        // gold leaf is crinkled; enamel is glass smooth
        vec2 crinkle = vec2(TDSimplexNoise(P.xy * 55.0), TDSimplexNoise(P.xy * 55.0 + 5.0)) * 0.07 * gold;
        vec3 Ni = normalize(vec3(-hx * bump + crinkle.x, -hy * bump + crinkle.y, 1.0));
        float ndl = max(dot(Ni, L), 0.0);
        float ndv = max(dot(Ni, V), 0.0);
        vec3 R = reflect(-V, Ni);
        vec3 env = ceiling(P, R, drift);
        float sparkle = 1.0 + 2.5 * uHit.z;

        // enamel: dielectric, deep red body, clear-coat reflections
        float fres = 0.04 + 0.96 * pow(1.0 - ndv, 5.0);
        vec3 body = mix(vec3(0.50, 0.030, 0.020), vec3(0.22, 0.006, 0.006), smoothstep(0.3, 1.0, h));
        body = mix(body, vec3(0.006, 0.006, 0.008), tar);
        body = mix(body, vec3(0.50, 0.54, 0.53), white);
        vec3 enamel = body * (AMB * 2.0 + LAMP * 2.2 * ndl * atten * key);
        enamel += LAMP * pow(max(dot(Ni, Hh), 0.0), 220.0) * 11.0 * sparkle * atten * key;
        enamel += env * fres * mix(1.3, 2.2, tar);

        // gold leaf: metal, everything it shows is a tinted reflection
        vec3 f0 = GOLD;
        vec3 fm = f0 + (1.0 - f0) * pow(1.0 - ndv, 5.0);
        vec3 leaf = fm * env * 1.5;
        leaf += fm * LAMP * pow(max(dot(Ni, Hh), 0.0), 150.0) * 8.0 * sparkle * atten * key;
        leaf += GOLD * vec3(0.46, 0.26, 0.07) * (0.22 + 2.4 * ndl * atten * key);

        vec3 icol = mix(enamel, leaf, gold);
        float inkmask = smoothstep(0.10, 0.32, h);
        col = mix(pcol, icol, inkmask);
        col *= mix(0.8, 1.0, smoothstep(0.0, -0.004, outside));
    }

    col = clamp(col, 0.0, 40.0);
    fragColor = TDOutputSwizzle(vec4(col, coc));
}
