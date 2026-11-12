// sep.frag: colour separation. Turns the three-light render + type into four
// continuous-tone plates (R,G,B,A = plates 0..3, 0 = no ink, 1 = solid) covering the
// whole sheet, and HOLDS each plate until its latch fires (plates are exposed at
// different times). see: experiments/sc_riso_press/NOTES.md (2026-11-10)
// inputs: 0 src_sw: render (premultiplied rgb = three lightings, a = coverage) or in_prep (Input picture)
//         1 typepack (r = big type, g = slug line, b = rows of phrases), sheet space
//         2 this TOP's previous frame
uniform vec4 uLatch;   // per plate: 1 = expose now
uniform vec4 uImg;     // margin (sheet heights), tiles x, tiles y, variant seed
uniform vec4 uAmt;     // per plate: object tone multiplier (below 0.86 keeps it out of the solid range)
uniform vec4 uSun;     // gradient centre x, y (image uv), radius, key outline weight
uniform vec4 uPa0, uPa1, uPa2, uPa3;   // source channel (0..2 light, 3 luma), mode (0 shade, 1 light, 2 none), big type, rows type
uniform vec4 uPb0, uPb1, uPb2, uPb3;   // flood amount, gradient kind, plate scale, type knocks out of flood (1) / adds (0)
uniform vec4 uPc0, uPc1, uPc2, uPc3;   // plate offset x, y (image uv), plate rotation, tone gamma
uniform vec4 uIn;      // x = 1 while input 0 is another scene's picture (COMP par Input), not the render; y = 1 in Describe mode
out vec4 fragColor;

const vec2 SHEET = vec2(1.6, 1.0);

float h21(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }

float grad(float kind, vec2 iuv) {
    vec2 d = (iuv - uSun.xy) * vec2(1.7, 1.0);
    if (kind < 0.5) return 1.0;                                   // flat
    if (kind < 1.5) return clamp(1.15 - iuv.y * 1.2, 0.0, 1.0);    // heavy at the bottom
    if (kind < 2.5) return 1.0 - smoothstep(0.0, uSun.z, length(d)); // soft sun
    if (kind < 3.5) return step(length(d), uSun.z) * (0.35 + 0.65 * clamp(0.5 + (uSun.y - iuv.y) / uSun.z * 0.5, 0.0, 1.0)); // hard disc, graded
    if (kind < 4.5) return step(0.5, fract(iuv.y * 9.0 + 0.25)) ;  // bands
    return clamp(iuv.x * 0.9 + iuv.y * 0.5 - 0.1, 0.0, 1.0);        // diagonal ramp
}

float plate(int i, vec4 pa, vec4 pb, vec4 pc, vec2 iuv, vec2 suv, vec3 typ) {
    float amt = i == 0 ? uAmt.x : i == 1 ? uAmt.y : i == 2 ? uAmt.z : uAmt.w;
    if (pa.y > 2.5) return 0.0;
    // this plate's own view of the artwork (scale, rotate, offset about the image centre)
    vec2 c = (iuv - 0.5) * vec2(1.7, 1.0);
    float cs = cos(pc.z), sn = sin(pc.z);
    c = mat2(cs, -sn, sn, cs) * c / max(pb.z, 0.05);
    vec2 ruv = c / vec2(1.7, 1.0) + 0.5 - pc.xy;
    vec4 r = texture(sTD2DInputs[0], ruv);
    float inb = step(0.0, ruv.x) * step(ruv.x, 1.0) * step(0.0, ruv.y) * step(ruv.y, 1.0);
    r *= inb;
    float a = r.a;
    float lum = max(r.r, max(r.g, r.b));
    float L = pa.x < 0.5 ? r.r : pa.x < 1.5 ? r.g : pa.x < 2.5 ? r.b : lum;
    L = a > 0.001 ? clamp(L / a, 0.0, 1.0) : 0.0;
    float obj = 0.0;
    if (pa.y < 0.5) obj = pow(1.0 - L, pc.w);          // ink in the shade
    else if (pa.y < 1.5) obj = pow(L, pc.w);           // ink in the light
    obj *= amt;
    if (i == 3) {
        // key plate: deep shadow plus a contour line
        float l3 = a > 0.001 ? lum / a : 1.0;
        obj = pa.y < 1.5 ? smoothstep(0.34, 0.08, l3) * 0.92 : 0.0;
        vec2 px = 1.6 / vec2(textureSize(sTD2DInputs[0], 0));
        float e = abs(texture(sTD2DInputs[0], ruv + vec2(px.x, 0.0)).a - texture(sTD2DInputs[0], ruv - vec2(px.x, 0.0)).a)
                + abs(texture(sTD2DInputs[0], ruv + vec2(0.0, px.y)).a - texture(sTD2DInputs[0], ruv - vec2(0.0, px.y)).a);
        obj = max(obj, smoothstep(0.25, 0.7, e) * uSun.w);
        a = max(a, smoothstep(0.25, 0.7, e) * uSun.w);
    }
    float bg = pb.x * grad(pb.y, iuv);
    float ty = max(typ.r * pa.z, typ.b * pa.w);
    bg = pb.w > 0.5 ? bg * (1.0 - step(0.5, max(typ.r * step(0.01, pa.z), typ.b * step(0.01, pa.w)))) : max(bg, ty);
    if (pa.y > 1.5) return bg;
    // an Input picture covers the whole image area, and in Describe mode the words must be whole:
    // in both cases type overprints the object instead of hiding behind it
    if (uIn.x > 0.5 || uIn.y > 0.5) return max(mix(bg, obj, a), ty);
    return mix(bg, obj, a);
}

void main() {
    vec2 suv = vUV.st;                       // sheet uv
    vec2 P = (suv - 0.5) * SHEET;            // sheet-height units
    float m = uImg.x;
    vec2 ihalf = SHEET * 0.5 - m;
    vec2 iuv = P / (2.0 * ihalf) + 0.5;      // image-area uv
    float inimg = step(abs(P.x), ihalf.x) * step(abs(P.y), ihalf.y);
    vec3 typ = texture(sTD2DInputs[1], suv).rgb;

    // gang sheet: step-and-repeat the artwork, each tile with its own plate order
    vec2 tiles = max(uImg.yz, vec2(1.0));
    vec2 tid = floor(iuv * tiles);
    vec2 tuv = fract(iuv * tiles);
    float many = step(1.5, tiles.x * tiles.y);
    vec2 auv = mix(iuv, tuv, many);

    vec4 t;
    t.r = plate(0, uPa0, uPb0, uPc0, auv, suv, typ);
    t.g = plate(1, uPa1, uPb1, uPc1, auv, suv, typ);
    t.b = plate(2, uPa2, uPb2, uPc2, auv, suv, typ);
    t.a = plate(3, uPa3, uPb3, uPc3, auv, suv, typ);
    if (many > 0.5) {
        float h = h21(tid + uImg.w * 7.3);
        if (h > 0.66) t.rgb = t.gbr; else if (h > 0.33) t.rgb = t.brg;
        float d = h21(tid * 1.7 + 3.1 + uImg.w);
        if (d < 0.2) t.r = 0.0; else if (d < 0.4) t.g = 0.0; else if (d < 0.55) t.b = 0.0;
        float fl = h21(tid * 2.3 + 9.2 + uImg.w);     // some tiles get a flat tint behind
        vec4 r0 = texture(sTD2DInputs[0], tuv);
        if (fl < 0.3) t.r = max(t.r, 0.55 * (1.0 - r0.a)); else if (fl < 0.55) t.b = max(t.b, 0.7 * (1.0 - r0.a)); else if (fl < 0.7) t.g = max(t.g, 0.45 * (1.0 - r0.a));
        // gutters between tiles stay paper
        vec2 gz = smoothstep(vec2(0.0), vec2(0.035), tuv) * smoothstep(vec2(0.0), vec2(0.035), 1.0 - tuv);
        t *= step(0.99, gz.x * gz.y);
    }
    t *= inimg;
    t.a = max(t.a, typ.g);                   // slug line prints in the key, margins included

    vec4 prev = texture(sTD2DInputs[2], suv);
    fragColor = TDOutputSwizzle(mix(prev, clamp(t, 0.0, 1.0), step(0.5, uLatch)));
}
