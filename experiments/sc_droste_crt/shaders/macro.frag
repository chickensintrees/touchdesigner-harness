// Macro of the tube: the lens is pressed against the glass, so the picture (the screen
// texture, which is the previous master frame) breaks into staggered RGB phosphor slots.
// input 0: the screen texture
uniform vec4 uP;    // centre x, centre y, zoom, slot cell size in pixels
uniform vec4 uQ;    // hit_low, hit_high, pulse, shot age
out vec4 fragColor;

void main() {
    vec2 res = vec2(1280.0, 720.0);
    vec2 q = vUV.st * 2.0 - 1.0;
    // the slots stay on the output's pixel grid (warping them gives ring moire at 4 px a
    // slot); only the picture behind them bulges
    vec2 px = vUV.st * res;
    float cw = max(uP.w, 3.0);
    float col = floor(px.x / cw);
    float yo = mod(col, 2.0) * 0.5;
    float row = floor(px.y / cw + yo);
    vec2 cc = vec2(col + 0.5, row + 0.5 - yo) * cw;  // slot centre: one sample per triad
    vec2 qc = cc / res * 2.0 - 1.0;
    qc *= 1.0 + 0.07 * dot(qc, qc);
    vec2 suv = clamp(uP.xy + qc * 0.5 / max(uP.z, 0.2), 0.002, 0.998);
    float ce = (0.006 + 0.03 * uQ.y) / max(uP.z, 0.2);   // convergence error, worse on hats
    vec3 s;
    s.r = textureLod(sTD2DInputs[0], suv + vec2(ce, 0.0), 0.0).r;
    s.g = textureLod(sTD2DInputs[0], suv, 0.0).g;
    s.b = textureLod(sTD2DInputs[0], suv - vec2(ce, 0.0), 0.0).b;
    s = max(s, vec3(0.0));
    vec2 f = vec2(fract(px.x / cw), fract(px.y / cw + yo));
    float sx = f.x * 3.0;
    float k = floor(sx);
    float fx = fract(sx);
    float m = smoothstep(0.06, 0.30, fx) * (1.0 - smoothstep(0.70, 0.94, fx));
    m *= smoothstep(0.03, 0.20, f.y) * (1.0 - smoothstep(0.80, 0.97, f.y));
    vec3 mask = vec3(float(k < 0.5), float(k > 0.5 && k < 1.5), float(k > 1.5)) * m;
    float drive = 4.0 * (1.0 + 0.45 * uQ.z + 0.8 * min(uQ.x, 1.2));
    vec3 c = pow(s, vec3(0.9)) * mask * drive;
    c += s * 0.16;                                  // halation between the slots
    // a soft window reflection on the glass
    float sheen = smoothstep(0.35, 1.25, dot(q, normalize(vec2(-0.55, 0.83))));
    c += vec3(0.05, 0.065, 0.08) * sheen;
    c += exp(-uQ.w * 10.0) * vec3(0.9, 1.0, 0.95) * mask * 2.0;   // every slot fires at the cut
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
