// The studio output chain: sync (tear, roll), keyer, colouriser, chroma bleed, phosphor glow,
// interlace, snow. Input 0: loop output. Input 1: blurred copy (glow). Input 2: source picture.
uniform vec4 uSync;   // x tear amount, y roll offset 0..1, z time, w flagging at the top
uniform vec4 uColz;   // x colouriser amount, y palette index, z band count, w key amount
uniform vec4 uLook;   // x negative amount, y interlace, z chroma bleed px, w snow
uniform vec4 uAud;    // x pulse, y hit_high, z energy, w frame counter (wrapped)
uniform vec4 uWall;   // x monitor-wall tiles across (1 = off), y seed, z glow gain, w exposure
out vec4 fragColor;

float hash(float n) { return fract(sin(n * 127.1) * 43758.5453); }
float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float ihash(uvec3 v)
{
    v = v * 1664525u + 1013904223u;
    v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
    v ^= v >> 16u;
    v.x += v.y * v.z;
    return float(v.x & 0x00ffffffu) / 16777216.0;
}
float vnoise(float x)
{
    float i = floor(x); float f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    return mix(hash(i), hash(i + 1.0), f);
}

const vec3 PAL[30] = vec3[30](
    // 0 Paik: hard video primaries
    vec3(0.02, 0.0, 0.12), vec3(0.1, 0.0, 0.9), vec3(0.95, 0.0, 0.55), vec3(1.0, 0.85, 0.0), vec3(0.0, 1.0, 0.9),
    // 1 ident
    vec3(0.03, 0.06, 0.09), vec3(0.16, 0.49, 0.61), vec3(0.86, 0.34, 0.24), vec3(0.86, 0.71, 0.24), vec3(0.93, 0.89, 0.8),
    // 2 thermal
    vec3(0.0, 0.0, 0.0), vec3(0.45, 0.0, 0.55), vec3(1.0, 0.1, 0.05), vec3(1.0, 0.6, 0.0), vec3(1.0, 1.0, 0.75),
    // 3 broadcast: beige and sickly green
    vec3(0.05, 0.07, 0.04), vec3(0.42, 0.47, 0.38), vec3(0.72, 0.42, 0.56), vec3(0.86, 0.89, 0.78), vec3(0.93, 0.89, 0.78),
    // 4 acid
    vec3(0.0, 0.02, 0.0), vec3(0.0, 0.55, 0.2), vec3(0.85, 1.0, 0.0), vec3(1.0, 0.1, 0.6), vec3(1.0, 1.0, 1.0),
    // 5 two-tone
    vec3(0.0, 0.0, 0.0), vec3(0.66, 0.2, 0.17), vec3(0.0, 0.0, 0.0), vec3(0.93, 0.89, 0.78), vec3(0.66, 0.2, 0.17));

vec3 pal(float l, float id, float bands)
{
    float b = clamp(floor(clamp(l, 0.0, 0.999) * bands), 0.0, 4.0);
    return PAL[int(clamp(id, 0.0, 5.0)) * 5 + int(b)];
}

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

void main()
{
    vec2 uv = vUV.st;
    float t = uSync.z;

    // monitor wall: the same signal on a bank of tubes, each with its own hold error
    float tiles = max(uWall.x, 1.0);
    vec2 cell = floor(uv * tiles);
    float cid = hash2(cell + uWall.y * 17.0);
    vec2 border = vec2(1.0);
    float tileGain = 1.0;
    float palId = uColz.y;
    float czAmt = uColz.x;
    float tubeNeg = 0.0;
    if (tiles > 1.5) {
        vec2 f = fract(uv * tiles);
        vec2 q = (f - 0.5) * 1.12;
        q *= 1.0 + 0.18 * dot(q, q);                       // tube curvature
        border = smoothstep(vec2(0.5), vec2(0.47), abs(q));
        uv = q + 0.5;
        // no two tubes are set up alike: some are mirrored, some zoomed in, some wired in negative
        uv.x = mix(uv.x, 1.0 - uv.x, step(0.5, fract(cid * 5.0)));
        uv = (uv - 0.5) * (fract(cid * 3.7) > 0.6 ? 0.42 : 1.0) + 0.5;
        tubeNeg = step(0.8, fract(cid * 11.0));
        tileGain = 0.75 + 0.6 * cid;
        palId = mod(uColz.y + floor(fract(cid * 13.0) * 3.0), 6.0);
        czAmt = uColz.x * step(0.35, fract(cid * 29.0));
    }

    // vertical hold: the picture slips and a sync bar travels through
    float roll = uSync.y + (tiles > 1.5 ? step(0.6, cid) * fract(cid * 7.0 + t * 0.15 * (cid - 0.3)) : 0.0);
    float y = fract(uv.y + roll);
    float bar = smoothstep(0.0, 0.012, abs(fract(uv.y + roll + 0.5) - 0.5)) ;
    bar = mix(1.0, bar, step(0.0005, abs(roll)));

    // horizontal sync: flagging at the top of the frame, and tearing on hits
    float flag = uSync.w * exp(-(1.0 - y) * 9.0) * sin(t * 5.0 + y * 30.0);
    float band = smoothstep(0.4, 0.7, vnoise(y * 4.0 + floor(t * 15.0) * 3.7 + cid * 9.0));
    float tear = uSync.x * band * (vnoise(y * 60.0 + t * 50.0) - 0.35) * 0.14;
    tear += uSync.x * 0.0015 * sin(y * 400.0 + t * 90.0);
    float x = uv.x + flag * 0.08 + tear;
    vec2 suv = vec2(x, y);

    // luminance sharp, chrominance smeared to the right (narrow chroma bandwidth)
    vec2 px = vec2(1.0 / 1280.0, 0.0);
    vec3 c0 = texture(sTD2DInputs[0], suv).rgb;
    vec3 cs = c0 * 0.34;
    cs += texture(sTD2DInputs[0], suv - px * uLook.z).rgb * 0.26;
    cs += texture(sTD2DInputs[0], suv - px * uLook.z * 2.0).rgb * 0.2;
    cs += texture(sTD2DInputs[0], suv - px * uLook.z * 3.5).rgb * 0.12;
    cs += texture(sTD2DInputs[0], suv - px * uLook.z * 5.5).rgb * 0.08;
    float l0 = luma(c0), ls = luma(cs);
    vec3 c = cs + vec3(l0 - ls);
    c = max(c, 0.0);
    vec3 glow = texture(sTD2DInputs[1], suv).rgb;

    // keyer: the source picture, colourised in flat bands, keyed in behind the wires
    vec4 src = texture(sTD2DInputs[2], suv);
    float negAmt = max(uLook.x, tubeNeg);
    float key = smoothstep(0.25, 0.55, src.g) * uColz.w;
    vec3 layer = PAL[int(clamp(palId, 0.0, 5.0)) * 5 + 2];
    c = mix(c, layer * 0.75 + c, key * (1.0 - negAmt));

    // colouriser: luminance bands of the finished signal to hard colours
    float lc = luma(c + glow * 0.5);
    vec3 cz = pal(1.0 - exp(-lc * 1.6), palId, uColz.z);
    c = mix(c, cz, czAmt);

    c += glow * uWall.z * (1.0 - 0.6 * czAmt);
    c *= uWall.w * (1.0 + 0.25 * uAud.x) * tileGain;

    // tone: phosphor saturates softly
    c = 1.0 - exp(-c);

    // negative: dark wires on a lit field
    vec3 paper = PAL[int(clamp(palId, 0.0, 5.0)) * 5 + 4];
    vec3 ink = mix(vec3(1.0), vec3(0.74, 0.2, 0.15), key);     // the keyed layer prints in DO NOT OPEN red
    vec3 neg = paper * ink * (1.0 - 0.95 * clamp(luma(c) * 1.3, 0.0, 1.0)) + 0.15 * c * (1.0 - paper);
    c = mix(c, neg, negAmt);

    // interlace: alternate fields, with the off field dimmed
    float ln = floor(vUV.t * 360.0);
    float field = mod(ln + uAud.w, 2.0);
    c *= 1.0 - uLook.y * 0.25 * field;
    // snow and a faint hum bar
    // noise on a video line is smeared along the line, not a grid of dots
    float nx = vUV.s * 260.0 + ihash(uvec3(uint(ln), 7u, uint(uAud.w))) * 9.0;
    float nf = fract(nx); nf = nf * nf * (3.0 - 2.0 * nf);
    float n = mix(ihash(uvec3(uint(nx), uint(ln), uint(uAud.w))), ihash(uvec3(uint(nx) + 1u, uint(ln), uint(uAud.w))), nf);
    float streak = vnoise(vUV.s * 90.0 + ln * 37.0 + t * 400.0);
    c += uLook.w * (n - 0.5) * 0.12 * (0.5 + streak);
    c *= 0.94 + 0.06 * sin(vUV.t * 6.2832 - t * 1.7);

    c *= bar * border.x * border.y;
    // tube corners
    vec2 vq = vUV.st - 0.5;
    c *= 1.0 - 0.9 * dot(vq, vq) * dot(vq, vq) * 4.0;
    c = max(c, 0.0);
    if (any(isnan(c)) || any(isinf(c))) c = vec3(0.0);
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
