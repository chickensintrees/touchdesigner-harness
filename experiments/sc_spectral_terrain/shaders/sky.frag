// Sky behind the terrain: horizon glow tinted by the bass note, stars, and a "sun" that is the
// same spectrogram as the ground drawn in polar form: angle = frequency (bass at the horizon on
// both sides, treble at the top), radius = time (now at the centre, expanding outward).
// Input 0: note history (2 x rows). Input 1: waterfall history (R height, A kick).
uniform vec4 uCam;     // x pitch deg (rx), y yaw deg (ry), z roll deg (rz), w tan(fovy/2)
uniform vec4 uFx;      // x bar_pulse, y hit_high, z evolve, w energy
uniform vec4 uCol;     // rgb phosphor
uniform vec4 uHit;     // x kick flash, y hit_mid
uniform vec4 uSkyM;    // x mode: 0 horizon sun, 1 flat colour, 2 dusk with a small sun, 3 stars only, 4 full-circle sun; y sun azimuth (rad)
uniform vec4 uBg;      // rgb paper / fog colour
out vec4 fragColor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

vec3 hue2rgb(float h)
{
    return clamp(abs(fract(h + vec3(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0, 0.0, 1.0);
}

void main()
{
    vec2 q = (vUV.st - 0.5) * vec2(1280.0 / 720.0, 1.0);
    float rz = radians(uCam.z);
    q = mat2(cos(rz), -sin(rz), sin(rz), cos(rz)) * q;
    float th = uCam.w;
    // view ray elevation and azimuth offsets on screen
    float hy = tan(radians(-uCam.x)) / (2.0 * th);       // horizon height above centre
    float hx = tan(radians(uCam.y)) / (2.0 * th);        // world -z direction, sideways
    float dy = q.y - hy;
    float dx = q.x - hx;
    vec3 col = vec3(0.0);
    int mode = int(uSkyM.x + 0.5);
    if (mode == 1) {
        fragColor = TDOutputSwizzle(vec4(uBg.rgb, 1.0));
        return;
    }
    if (mode == 2) {
        // dusk: the fog colour at the horizon, deepening upward, one small hard sun
        float up = max(dy, 0.0);
        col = mix(uBg.rgb, uBg.rgb * vec3(0.20, 0.26, 0.50), smoothstep(0.0, 0.75, up));
        vec2 sp2 = vec2(dx - tan(uSkyM.y) / (2.0 * th), dy - 0.085);
        float sr = length(sp2);
        float disc = 1.0 - smoothstep(0.070, 0.074, sr);
        // the sun is cut by slats that are the live spectrum's bass level
        col += uCol.rgb * (disc * 2.2 + exp(-sr * 9.0) * 0.55 + exp(-sr * 2.2) * 0.22) * (0.8 + 0.5 * uFx.x);
        if (any(isnan(col)) || any(isinf(col))) col = uBg.rgb;
        fragColor = TDOutputSwizzle(vec4(col, 1.0));
        return;
    }
    if (mode == 3) {
        // deep field: stars over the whole frame, no horizon
        vec2 g3 = q * 60.0 + vec2(uFx.z * 0.15, 0.0);
        vec2 id3 = floor(g3);
        float h3 = hash(id3);
        vec2 s3 = fract(g3) - 0.5 - (vec2(hash(id3 + 3.1), hash(id3 + 7.7)) - 0.5) * 0.7;
        float st = (1.0 - smoothstep(0.02, 0.08, length(s3))) * step(0.84, h3);
        st *= 0.3 + 0.7 * step(0.5, fract(h3 * 37.0 + uFx.z * 0.3)) + 3.0 * uFx.y * step(0.92, h3);
        col = mix(uCol.rgb, vec3(1.0), 0.5) * st * 0.6;
        fragColor = TDOutputSwizzle(vec4(col, 1.0));
        return;
    }
    float full = mode == 4 ? 1.0 : 0.0;
    // input 0 is the note history; texel (1, 0) is the bass right now:
    // R held hue (pitch class), G flare that decays after each detected note, B bass loudness
    vec4 bass = texelFetch(sTD2DInputs[0], ivec2(1, 0), 0);
    vec3 note = mix(vec3(1.0), hue2rgb(bass.r), 0.88);
    vec4 uTint;
    uTint.rgb = mix(uCol.rgb * 0.55, note, 0.30 + 0.70 * bass.g);
    uTint.w = 0.16 + 0.55 * min(bass.b, 1.2) + 0.55 * bass.g + 0.12 * uFx.w;
    float above = max(smoothstep(-0.002, 0.004, dy), full);
    // glow band
    float glow = (exp(-max(dy, 0.0) * 11.0) * 0.30 + exp(-max(dy, 0.0) * 45.0) * 0.55) * (1.0 - full);
    glow *= exp(-dx * dx * 1.4);
    col += uTint.rgb * glow * uTint.w * above;

    // polar spectrogram sun
    float r = length(vec2(dx, dy));
    float R = 0.44 + 0.03 * uFx.x + 0.05 * uHit.x;
    const float N = 22.0;
    float rn = r / R * N;
    float pxw = N / (720.0 * R);
    float ang = atan(mix(max(dy, 0.0), abs(dy), full), dx) / 3.14159265;     // 0 right horizon .. 1 left horizon
    float k0 = floor(rn);
    vec3 sun = vec3(0.0);
    float dome = 0.0;
    for (int i = -4; i <= 0; i++) {
        float k = k0 + float(i);
        if (k < 0.0 || k >= N) continue;
        float v = (k + 0.5) / N;
        vec4 w = texture(sTD2DInputs[1], vec2(ang, v * 0.92));
        float hh = min(w.r, 1.5);
        float rad = k + 0.5 + hh * 2.7;
        float d = abs(rn - rad);
        float line = 1.0 - smoothstep(pxw * 0.9, pxw * 2.4, d);
        float fade = 1.0 - 0.75 * v;
        vec3 lc = mix(uTint.rgb * 1.3, uCol.rgb, smoothstep(0.1, 0.8, v));
        sun += lc * line * (0.16 + 1.5 * hh * hh + 0.5 * hh) * fade;
        sun += vec3(1.0, 0.96, 0.86) * line * w.a * 0.9 * fade;
        dome = max(dome, (1.0 - smoothstep(rad - 0.2, rad, rn)) * step(float(i), -0.5));
    }
    // a faint filled core so the dome has a body behind the lines
    float core = exp(-r * r / (R * R) * 5.0);
    sun += uTint.rgb * core * (0.10 + 0.25 * min(bass.b, 1.2));
    col += sun * above * (0.55 + 0.6 * uFx.w + 0.35 * uFx.x);

    // stars
    vec2 g = vec2(dx, dy) * 46.0;
    vec2 id = floor(g);
    float hsh = hash(id);
    vec2 sp = fract(g) - 0.5 - (vec2(hash(id + 3.1), hash(id + 7.7)) - 0.5) * 0.7;
    float star = (1.0 - smoothstep(0.02, 0.07, length(sp))) * step(0.86, hsh);
    star *= 0.25 + 0.75 * step(0.5, fract(hsh * 37.0 + uFx.z * 0.3)) + 2.5 * uFx.y * step(0.93, hsh);
    col += uCol.rgb * star * above * max(smoothstep(0.02, 0.2, dy), full) * 0.55 * smoothstep(0.8, 1.3, r / R);
    if (any(isnan(col)) || any(isinf(col))) col = vec3(0.0);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
