// "Relic" take: the living ink as the skin of a library model. The simulation is projected
// onto the model from three sides (object space) and lit like the ink on the page:
// a raised bead of gold leaf, red enamel or tar on a lacquered body.
uniform sampler2D sSim;   // smoothed state, G = V
uniform vec4 uInk;        // ink (0 gold on red lacquer, 1 red enamel on cream, 2 tar on putty), kick, hit_high, pulse
uniform vec4 uLight;      // beat_pos, evolve, seed, 1 in Describe mode or with an Input
in vec3 vWP;
in vec3 vLP;
in vec3 vWN;
in vec3 vLN;
in vec3 vCam;
flat in mat3 vToWorld;
out vec4 fragColor;

const vec3 GOLD = vec3(1.00, 0.62, 0.20);
const vec3 LAMP = vec3(1.0, 0.84, 0.62);

vec2 simuv(vec2 c) { return vec2(c.x * 0.5625 * 0.9 + 0.5, c.y * 0.9 + 0.5); }
// the flat impression (state A): drawn in Describe mode and with an Input only, so the words
// or the picture stay readable
float impr(vec2 c) { return texture(sSim, simuv(c)).a; }
float hgt(vec2 c) { return smoothstep(0.12, 0.42, texture(sSim, simuv(c)).g); }
// height and its gradient along the two axes of one projection
vec3 proj(vec2 c) {
    float e = 0.004;
    float h = hgt(c);
    return vec3(h, hgt(c + vec2(e, 0.0)) - hgt(c - vec2(e, 0.0)), hgt(c + vec2(0.0, e)) - hgt(c - vec2(0.0, e)));
}

vec3 room(vec3 r, float drift) {
    float up = clamp(r.y, 0.0, 1.0);
    vec3 env = mix(vec3(0.030, 0.034, 0.028), vec3(0.13, 0.15, 0.12), up * up);
    if (r.y > 0.05) {
        vec2 c = r.xz / r.y * 2.0;
        float x = abs(fract(c.x / 1.5 + drift) - 0.5) * 1.5;
        float pair = smoothstep(0.11, 0.04, abs(x - 0.14));
        float seg = smoothstep(0.48, 0.42, abs(fract(c.y / 2.6 + 0.2) - 0.5));
        env += vec3(0.86, 0.95, 0.78) * pair * seg * 3.2;
    }
    return env;
}

void main()
{
    TDCheckDiscard();
    vec3 ln = normalize(vLN);
    vec3 w = pow(abs(ln), vec3(4.0));
    w /= (w.x + w.y + w.z);
    // flip each projection on its back-facing side, or the words read mirrored there
    vec3 sg = vec3(ln.x < 0.0 ? 1.0 : -1.0, 1.0, ln.z < 0.0 ? -1.0 : 1.0);
    vec3 px = proj(vec2(vLP.z * sg.x, vLP.y)), py = proj(vLP.xz), pz = proj(vec2(vLP.x * sg.z, vLP.y));
    float h = px.x * w.x + py.x * w.y + pz.x * w.z;
    // gradient of the height in object space
    vec3 g = w.x * vec3(0.0, px.z, px.y * sg.x) + w.y * vec3(py.y, 0.0, py.z) + w.z * vec3(pz.y * sg.z, pz.z, 0.0);
    vec3 N = normalize(vWN);
    vec3 gw = vToWorld * g;
    gw -= N * dot(gw, N);
    float gold = 1.0 - step(0.5, uInk.x);
    float tar = step(1.5, uInk.x);
    vec3 Ni = normalize(N - gw * mix(2.6, 2.0, gold));

    vec3 V = normalize(vCam - vWP);
    float la = uLight.x * 0.19635 + uLight.z * 6.28;
    vec3 Lp = vec3(2.2 * cos(la), 1.9, 2.4 + 0.8 * sin(la));
    vec3 L = normalize(Lp - vWP);
    vec3 Hh = normalize(L + V);
    float key = 1.5 + 0.5 * uInk.w;
    float drift = uLight.y * 0.012;
    vec3 AMB = vec3(0.050, 0.068, 0.056) * 2.2;
    // a green fluorescent rim from behind
    float rim = pow(1.0 - max(dot(N, V), 0.0), 3.0);

    // body: lacquer under gold, cream paper under enamel, putty steel under tar
    vec3 body = vec3(0.38, 0.030, 0.026);
    if (uInk.x > 0.5) body = vec3(0.846, 0.767, 0.577);
    if (uInk.x > 1.5) body = vec3(0.58, 0.52, 0.38);
    float inkmask = smoothstep(0.10, 0.32, h);
    if (uLight.w > 0.5) {
        float im = impr(vec2(vLP.z * sg.x, vLP.y)) * w.x + impr(vLP.xz) * w.y + impr(vec2(vLP.x * sg.z, vLP.y)) * w.z;
        // ivory on the red lacquer, navy on cream, red on putty (dark red on lacquer could not be read, captures/d4_6.png)
        vec3 dye = vec3(0.80, 0.72, 0.52);
        if (uInk.x > 0.5) dye = vec3(0.030, 0.045, 0.10);
        if (uInk.x > 1.5) dye = vec3(0.30, 0.020, 0.018);
        body = mix(body, dye, 0.9 * smoothstep(0.25, 0.6, im));
    }
    // contact shadow where the bead meets the body
    body *= 1.0 - 0.6 * smoothstep(0.0, 0.2, h) * (1.0 - inkmask);
    vec3 bcol = body * (AMB + LAMP * key * max(dot(N, L), 0.0));
    bcol += LAMP * pow(max(dot(N, Hh), 0.0), 40.0) * 0.25 * key;
    bcol += room(reflect(-V, N), drift) * 0.05;
    bcol += vec3(0.50, 0.70, 0.45) * rim * 0.35;

    float ndl = max(dot(Ni, L), 0.0);
    float ndv = max(dot(Ni, V), 0.0);
    vec3 env = room(reflect(-V, Ni), drift);
    float sparkle = 1.0 + 2.5 * uInk.z;
    float fres = 0.04 + 0.96 * pow(1.0 - ndv, 5.0);
    vec3 eb = mix(vec3(0.50, 0.030, 0.020), vec3(0.22, 0.006, 0.006), smoothstep(0.3, 1.0, h));
    eb = mix(eb, vec3(0.006, 0.006, 0.008), tar);
    vec3 enamel = eb * (AMB + LAMP * 1.6 * ndl * key);
    enamel += LAMP * pow(max(dot(Ni, Hh), 0.0), 180.0) * 7.0 * sparkle * key;
    enamel += env * fres * mix(1.3, 2.2, tar);
    vec3 fm = GOLD + (1.0 - GOLD) * pow(1.0 - ndv, 5.0);
    vec3 leaf = fm * env * 0.9;   // 1.5 with the kick boost glowed like a lamp (captures/take_6_a.png)
    leaf += fm * LAMP * pow(max(dot(Ni, Hh), 0.0), 120.0) * 3.0 * sparkle * key;
    leaf += GOLD * vec3(0.46, 0.26, 0.07) * (0.22 + 1.1 * ndl * key);
    vec3 icol = mix(enamel, leaf, gold) * (1.0 + 0.25 * uInk.y);

    vec3 col = mix(bcol, icol, inkmask);
    if (any(isnan(col)) || any(isinf(col))) col = vec3(0.0);
    fragColor = TDOutputSwizzle(vec4(clamp(col, 0.0, 40.0), 1.0));
}
