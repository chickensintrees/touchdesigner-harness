// Gray-Scott step. Run with several passes per frame (each pass reads the last).
// R = 1-U, G = V, B and A pass through.
// Inputs: 0 state, 1 "near" (the stamp mask blurred wide: a cheap distance-to-letters
// field), 2 the crisp stamp mask.
// The chemistry is zoned by the phrase, so the living ink itself stays letter-shaped:
//   inside the strokes  - close to the flood edge: solid on a kick, then it hollows to
//                         outlines and worms that run along the strokes
//   near the strokes    - the worm band: coral fingers outward from the letters
//   beyond the "reach"  - too much kill: everything dies
// The reach is what the music moves most.
uniform vec4 uAudio;  // energy, bass, vocals, burn (hit_mid)
uniform vec4 uDrift;  // evolve, section hold, kick, unused
uniform vec4 uZone;   // per take: floor on "alive" (1 = coral may live anywhere), margin bias outside the strokes
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec2 px = uTD2DInfos[0].res.xy;
    vec4 c = texture(sTD2DInputs[0], uv);

    vec2 lap = -c.rg;
    lap += 0.2 * (texture(sTD2DInputs[0], uv + vec2(px.x, 0.0)).rg
                + texture(sTD2DInputs[0], uv - vec2(px.x, 0.0)).rg
                + texture(sTD2DInputs[0], uv + vec2(0.0, px.y)).rg
                + texture(sTD2DInputs[0], uv - vec2(0.0, px.y)).rg);
    lap += 0.05 * (texture(sTD2DInputs[0], uv + px).rg
                 + texture(sTD2DInputs[0], uv - px).rg
                 + texture(sTD2DInputs[0], uv + vec2(px.x, -px.y)).rg
                 + texture(sTD2DInputs[0], uv + vec2(-px.x, px.y)).rg);

    float e = smoothstep(0.33, 0.65, uAudio.x);
    float bass = clamp(uAudio.y, 0.0, 1.5);
    float near = texture(sTD2DInputs[1], uv).r;
    float inside = smoothstep(0.35, 0.65, texture(sTD2DInputs[2], uv).r);

    // the regime drifts across the page so different corners live in different chemistry
    vec2 q = (uv - 0.5) * vec2(16.0 / 9.0, 1.0);
    float n1 = TDSimplexNoise(vec3(q * 1.3, uDrift.x * 0.05));
    float n2 = TDSimplexNoise(vec3(q * 1.1 + 7.3, uDrift.x * 0.04 + 3.0));

    // Patterns only live in a curved band of (F, k). kf(F) is its lower edge, below which
    // V floods the page; it was measured on this discretisation (captures/map_b.png).
    // m is the margin above that edge: ~0.001 fat fast mazes, ~0.002 worms that finger
    // outward, ~0.004 slow spots, ~0.007 everything dies.
    float F = min(mix(0.030, 0.048, e) + 0.004 * clamp(uAudio.z, 0.0, 1.0) + 0.003 * n1, 0.054);
    float f = F - 0.04;
    float kf = 0.0587 + 0.25 * f - 13.0 * f * f;

    // outside the strokes: worms, as far from the letters as the music reaches
    float reach = clamp(mix(0.20, 0.012, e) - 0.08 * bass + 0.03 * n2, 0.006, 0.5);
    float alive = max(smoothstep(reach * 0.6, reach * 1.5 + 0.01, near), uZone.x);
    float mOut = mix(0.0026, 0.0013, e) - 0.0007 * bass + 0.0005 * n2 + uZone.y;
    mOut = max(mOut, 0.0006) + 0.012 * (1.0 - alive);
    // inside the strokes: a kick floods them solid, then they crack
    // (quiet margin 0.0020 plus the full snare burn killed the strokes outright in a
    // quiet section, captures/r4_d.png: the strokes get a lower margin and a third of the burn)
    float mIn = mix(0.0013, 0.0006, e) - 0.0060 * uDrift.z;
    float m = mix(mOut, mIn, inside);
    // snare burns the coral back, a section change burns everything that is not held down
    m += 0.003 * uAudio.w * mix(1.0, 0.3, inside) + 0.020 * uDrift.y;
    float k = kf + m;

    float U = 1.0 - c.r;
    float V = c.g;
    float uvv = U * V * V;
    // in 1-U form: d(1-U) = Du*lap(1-U) + uvv - F*(1-U)
    float r = c.r + (1.0 * lap.r + uvv - F * c.r);
    float g = c.g + (0.5 * lap.g + uvv - (F + k) * V);
    fragColor = TDOutputSwizzle(vec4(clamp(r, 0.0, 1.0), clamp(g, 0.0, 1.0), c.b, c.a));
}
