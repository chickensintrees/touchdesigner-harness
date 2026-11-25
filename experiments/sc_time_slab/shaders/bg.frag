// Studio backdrop that is never still: a few drifting fluorescent tubes and faint
// blind-slats on a wall, so the time map has something to tear everywhere in
// frame, without out-shouting the prop.
// Rooms (uB.z): 0 green-black studio, 1 beige wall, 2 red-black, 3 CRT-blue
// dark, 4 daylight cyclorama (bright, soft shadows instead of tubes), 5 empty (black,
// thin white tubes, no slats).
uniform vec4 uA;   // evolve, energy, pulse, section (integer)
uniform vec4 uB;   // bar_pos, hit_mid, room, prop side (-1, 0, 1)
out vec4 fragColor;

float hash(float n) { return fract(sin(n * 127.1) * 43758.5453); }

void main()
{
    vec2 uv = vUV.st;
    float ev = uA.x, energy = uA.y, pulse = uA.z, sec = uA.w;
    vec2 p = uv - 0.5;
    p.x *= 16.0 / 9.0;

    int room = int(uB.z + 0.5);
    vec3 wa = vec3(0.006, 0.012, 0.009), wb = vec3(0.045, 0.070, 0.050);
    vec3 accent = vec3(0.45, 1.0, 0.30), base = vec3(0.86, 0.92, 0.76);
    float slatSign = 1.0, tubeGain = 1.0, pool = 1.0;
    if (room == 3)      { wa = vec3(0.004, 0.010, 0.022); wb = vec3(0.035, 0.065, 0.11);
                          accent = vec3(1.0, 0.60, 0.16); base = vec3(0.55, 0.78, 1.0); }
    else if (room == 2) { wa = vec3(0.020, 0.004, 0.003); wb = vec3(0.11, 0.022, 0.016);
                          accent = vec3(1.0, 0.14, 0.09); base = vec3(1.0, 0.93, 0.80); }
    else if (room == 1) { wa = vec3(0.20, 0.17, 0.115);   wb = vec3(0.46, 0.40, 0.27);
                          accent = vec3(0.30, 0.85, 0.25); base = vec3(1.0, 0.95, 0.78);
                          slatSign = -1.6; pool = 0.0; }
    else if (room == 4) { wa = vec3(0.50, 0.48, 0.41);    wb = vec3(0.80, 0.78, 0.69);
                          accent = vec3(0.86, 0.34, 0.24); base = vec3(-0.9, -0.85, -0.75);
                          slatSign = -1.8; tubeGain = 0.45; pool = 0.0; }
    else if (room == 5) { wa = vec3(0.0); wb = vec3(0.012, 0.012, 0.014);
                          accent = vec3(1.0, 0.97, 0.88); base = vec3(1.0, 0.97, 0.88);
                          slatSign = 0.0; tubeGain = 0.8; pool = 0.35; }
    vec3 wall = mix(wa, wb, smoothstep(-0.7, 0.7, p.y + 0.35 * p.x));
    // a pool of accent light on the wall behind the prop, so it has a silhouette in the dark rooms
    vec2 pp = p - vec2(0.23 * uB.w, 0.0);
    wall += pool * accent * (0.07 + 0.06 * energy) * exp(-dot(pp, pp) * 3.5);

    // slanted, drifting tubes; the slant and the lit set change with the section
    float ang = 0.35 * sin(sec * 1.7);
    float c = p.x * cos(ang) + p.y * sin(ang);
    float x = c * 3.0 + ev * 0.55;
    float id = floor(x);
    float f = fract(x);
    float w = 0.03 + 0.05 * hash(id + sec * 13.0);
    float tube = smoothstep(w, w * 0.4, abs(f - 0.5));
    float on = step(0.30, hash(id * 3.1 + sec));
    float glow = exp(-abs(f - 0.5) * 5.0);
    float pick = hash(id * 7.7 + sec * 2.0);
    vec3 tubeCol = pick > 0.55 ? accent : base;
    vec3 col = wall;
    col += tubeGain * on * tube * tubeCol * (0.35 + 0.45 * energy + 0.6 * pulse);
    col += tubeGain * on * glow * tubeCol * 0.10 * (0.4 + energy);

    // blind slats: thin horizontal lines sliding down, two steps per bar
    float y = uv.y * 9.0 + uB.x * 2.0;
    float slat = smoothstep(0.06, 0.02, abs(fract(y) - 0.5));
    col += slatSign * slat * vec3(0.080, 0.095, 0.078) * (0.5 + 0.8 * energy);
    col = max(col, 0.0);

    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
