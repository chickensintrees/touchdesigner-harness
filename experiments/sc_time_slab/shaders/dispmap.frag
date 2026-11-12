// The time map: 0 = now, 1 = the oldest frame in the slab.
// Input 0: big soft-edged text (white on black). Input 1: a wall of small Chicago phrases.
// uT.x picks the kind of map; see TAKES in build.py.
uniform vec4 uA;   // bar phase, bass, energy, evolve
uniform vec4 uB;   // pulse, section (integer), hit_low, beat phase
uniform vec4 uC;   // kick count, hit_mid, bar_pos, beat_pos
uniform vec4 uT;   // map mode, flip, s1, s2 (seed-derived 0-1 numbers)
out vec4 fragColor;

float hash(float n) { return fract(sin(n * 127.1) * 43758.5453); }

void main()
{
    vec2 uv = vUV.st;
    float bar = uA.x, bass = min(uA.y, 1.3), energy = uA.z, ev = uA.w;
    float pulse = uB.x, sec = uB.y, kick = min(uB.z, 1.0);
    int mode = int(uT.x + 0.5);
    float s1 = uT.z, s2 = uT.w;
    vec2 p = (uv - 0.5) * vec2(16.0 / 9.0, 1.0);
    float d = 0.0;
    float t = 0.0;
    bool quake = true;

    if (mode == 0) {
        // WORD TEAR: sweeping gradient (one triangle wave up the frame per bar) plus a
        // hard step into the past inside giant letters
        t = texture(sTD2DInputs[0], uv).r;
        float dir = s2 < 0.5 ? 1.0 : -1.0;
        float g = abs(fract(uv.y * 1.25 + dir * uv.x * 0.45 - bar) * 2.0 - 1.0);
        g = smoothstep(0.0, 1.0, g);
        float swell = smoothstep(0.9, 0.0, length(p)) * bass;
        d = g * (0.26 + 0.38 * energy) + swell * 0.25;
        d += t * (0.30 + 0.28 * energy + 0.30 * bass + 0.12 * pulse);
    } else if (mode == 1) {
        // TWIST: one clean ramp along the spin axis, full depth. A spinning prop
        // becomes a helix. s2 > 0.5: the ramp runs sideways (the prop tumbles on X).
        float c = s2 > 0.5 ? uv.x : uv.y;
        if (s1 > 0.5) c = 1.0 - c;
        // cut into slices (10 to 27 of them): each slice is one moment, so the prop
        // becomes a stack of discs turned by different amounts, not a blur
        float N = 10.0 + floor(fract(s1 * 7.0) * 18.0);
        c = (floor(c * N) + 0.5) / N;
        d = c * (0.72 + 0.28 * energy + 0.10 * pulse);
    } else if (mode == 2) {
        // RINGS OF PAST: stepped rings round an off-centre point; the newest ring
        // leaves the centre on every beat and travels out
        vec2 c = vec2(0.5 * (s1 - 0.5), 0.3 * (s2 - 0.5));
        float r = length(p - c);
        float ph = fract(r * 2.0 - uB.w);
        float steps = 5.0;
        d = floor(ph * steps + 0.5) / steps;
        d *= 0.55 + 0.45 * energy;
        d += 0.25 * bass * smoothstep(0.5, 0.0, r);
        quake = false;
        // kicks throw alternate rings further back
        d += kick * 0.35 * mod(floor(r * 2.0 * steps - uB.w * steps), 2.0);
    } else if (mode == 3) {
        // VENETIAN: slanted blades, each at one of four depths, reshuffled by every kick
        float a = radians(mix(-65.0, 65.0, s1));
        float n = 7.0 + floor(s2 * 16.0);
        float x = (p.x * cos(a) + p.y * sin(a)) * n + ev * 0.6;
        float id = floor(x);
        float lvl = floor(hash(id * 1.7 + uC.x * 3.1) * 4.0) / 3.0;
        float edge = smoothstep(0.0, 0.04, fract(x)) * smoothstep(1.0, 0.96, fract(x));
        d = lvl * edge * (0.45 + 0.40 * energy + 0.25 * bass);
        d += 0.20 * kick * hash(id * 9.1 + uC.x);
        quake = false;
    } else if (mode == 5) {
        // PHRASE CRAWL: lines of small text crawl up the frame; every letter is a
        // window into the past. Alternate lines look back further.
        vec2 q = vec2(uv.x * 0.9 + s1, uv.y * 0.9 + uC.z * 0.125 + s2);
        t = texture(sTD2DInputs[1], q).r;
        float row = floor(q.y * 12.0);
        float deep = 0.55 + 0.45 * hash(row);
        d = t * deep * (0.50 + 0.30 * energy + 0.25 * bass + 0.12 * pulse);
        d += 0.10 * energy * abs(fract(uv.x * 0.7 - bar) * 2.0 - 1.0);
    } else {
        d = 0.0;
        quake = false;
    }

    if (quake) {
        // time-quake: each kick drops a fresh random set of horizontal strips into the
        // past for as long as the hit envelope lasts (about 0.15 s)
        float rows = 7.0 + 9.0 * hash(uC.x * 1.3);
        float strip = floor(uv.y * rows + hash(uC.x) * 5.0);
        float pick = step(0.55, hash(strip * 3.7 + uC.x * 11.0));
        d += pick * kick * 0.45 * (t > 0.5 ? -1.0 : 1.0);
    }

    d = clamp(d, 0.0, 1.0);
    // flipped: the letters are "now", the room is the past
    if (uT.y > 0.5) d = clamp(0.7 - d, 0.0, 1.0);
    fragColor = TDOutputSwizzle(vec4(vec3(d), 1.0));
}
