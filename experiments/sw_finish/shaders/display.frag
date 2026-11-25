// sw_finish, pass 2: what the DISPLAY or the film stock does to the picture.
// Inputs: 0 the signal, 1 highlights blurred small (bloom), 2 highlights blurred wide (halation).
uniform vec4 uTube;  // x curvature, y scan lines, z aperture mask, w corner rounding
uniform vec4 uGlow;  // x bloom, y halation, z misregistration, w grain
uniform vec4 uFrame; // x letterbox aspect (0 = none), y 4:3 picture (0/1), z dither amount, w dither pixel size
uniform vec4 uTint;  // rgb colour the blacks lean toward, w strength
uniform vec4 uCast;  // rgb colour cast (multiplies the picture), w vignette
uniform vec4 uClock; // x seconds, y frame (wrapped)
out vec4 fragColor;

float hash2(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
float bayer2(vec2 a) { a = floor(a); return fract(a.x / 2.0 + a.y * a.y * 0.75); }
float bayer8(vec2 a) { return bayer2(0.25 * a) * 0.0625 + bayer2(0.5 * a) * 0.25 + bayer2(a); }
float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 frag = vUV.st * res;
    vec2 uv = vUV.st;
    float fr = floor(uClock.y);

    // 1-bit: work on a coarse pixel grid so every dot is a hard square.
    float pix = max(1.0, floor(uFrame.w + 0.5));
    vec2 cell = floor(frag / pix);
    if (uFrame.z > 0.0) uv = (cell + 0.5) * pix / res;

    // Tube geometry. q is the picture in -1..1; beyond 1 is the dark around the tube.
    float asp = res.x / res.y;
    float picAsp = mix(asp, 4.0 / 3.0, uFrame.y);
    vec2 p = uv * 2.0 - 1.0;
    p.x *= asp / picAsp;
    float k = uTube.x * 0.22;
    vec2 q = p * (1.0 + k * dot(p, p)) / (1.0 + k);
    float r = uTube.w * 0.14;
    vec2 dd = abs(q) - (1.0 - r);
    float sd = length(max(dd, 0.0)) + min(max(dd.x, dd.y), 0.0) - r;
    float inside = smoothstep(0.006, -0.006, sd);
    if (uTube.w <= 0.0 && uFrame.y <= 0.0 && uTube.x <= 0.0) inside = 1.0;

    vec2 suv = vec2(0.5 + q.x * 0.5 * picAsp / asp, 0.5 + q.y * 0.5);

    // Misregistration: the three guns do not land in quite the same place.
    vec2 off = q * uGlow.z * 0.004 + vec2(uGlow.z * 0.0012, 0.0);
    vec3 col;
    col.r = texture(sTD2DInputs[0], suv + off).r;
    col.g = texture(sTD2DInputs[0], suv).g;
    col.b = texture(sTD2DInputs[0], suv - off).b;

    // Bloom is neutral and tight. Halation is the red-orange halo film makes when
    // bright light scatters back through the base.
    vec3 bloom = texture(sTD2DInputs[1], suv).rgb;
    vec3 hal = texture(sTD2DInputs[2], suv).rgb;
    col += bloom * uGlow.x * 0.8;
    col += luma(hal) * vec3(1.0, 0.32, 0.12) * uGlow.y * 1.1;

    float l = luma(col);

    // Scan lines follow the glass. Bright lines swell and close the gaps.
    float lines = 0.5 + 0.5 * cos(q.y * 3.14159265 * 240.0);
    float gap = mix(0.45, 0.9, clamp(l, 0.0, 1.0));
    col *= mix(1.0, (gap + (1.0 - gap) * lines) * 1.22, uTube.y);

    // Aperture grille: vertical stripes of red, green and blue phosphor.
    float tri = mod(floor(frag.x), 3.0);
    vec3 mask = vec3(tri == 0.0 ? 1.0 : 0.72, tri == 1.0 ? 1.0 : 0.72, tri == 2.0 ? 1.0 : 0.72);
    col *= mix(vec3(1.0), mask * 1.2, uTube.z);

    // Vignette, colour cast, and blacks that are never neutral.
    float v = dot(q * vec2(0.85, 1.0), q * vec2(0.85, 1.0));
    col *= 1.0 - uCast.w * 0.45 * smoothstep(0.2, 1.9, v);
    col *= uCast.rgb;
    col += uTint.rgb * uTint.w * (1.0 - clamp(luma(col) * 1.6, 0.0, 1.0));

    // Grain: two sizes, stronger in the mid-tones and shadows, slightly coloured.
    float g1 = hash2(floor(frag / 1.5) + fr * 1.7);
    float g2 = hash2(floor(frag / 3.0) + fr * 2.3 + 40.0);
    float g = (g1 * 0.65 + g2 * 0.35) - 0.5;
    vec3 gc = vec3(g) + (vec3(hash2(frag + fr), hash2(frag + fr + 11.0), hash2(frag + fr + 23.0)) - 0.5) * 0.35;
    col += gc * uGlow.w * 0.22 * (1.0 - 0.55 * clamp(l, 0.0, 1.0));

    col *= inside;

    // Letterbox bars are true black: they are the edge of the film frame.
    if (uFrame.x > 0.0) {
        float half_h = 0.5 * asp / uFrame.x;
        col *= step(abs(vUV.t - 0.5), half_h);
    }

    // 1-bit ordered dither: pure black or pure white, tone from the pattern.
    if (uFrame.z > 0.0) {
        float tone = smoothstep(0.07, 0.92, luma(col));
        float bw = step(bayer8(cell) + 0.02, tone);
        col = mix(col, vec3(bw), uFrame.z);
    }

    fragColor = TDOutputSwizzle(vec4(max(col, 0.0), 1.0));
}
