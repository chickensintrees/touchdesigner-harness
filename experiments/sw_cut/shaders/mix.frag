// sw_cut picture layer: one shot treatment, one transition, one optional second layer.
// Input 0 = A, the scene on screen. Input 1 = B: the outgoing scene's frozen last
// frame while a transition runs, then the layered scene (live) if the shot has one.
// Index order of treatments, transitions and layer modes is fixed by the lists in
// build.py (TREATMENTS, TRANSITIONS, LAYER_MODES); index 0 is "none" / "cut".
uniform vec4 uShot;   // x treatment, y transition, z layer mode, w seed 0..1
uniform vec4 uTime;   // x transition progress 0..1 (1 = done), y shot age s, z beat_pos, w bar_pos
uniform vec4 uAudio;  // x pulse, y hit_low, z hit_mid, w energy
out vec4 fragColor;

const float PI = 3.14159265;
const vec3 INK = vec3(0.098, 0.169, 0.231), IVORY = vec3(0.933, 0.894, 0.800), RED = vec3(0.863, 0.337, 0.239);
const vec3 YELLOW = vec3(0.863, 0.710, 0.239), BLUE = vec3(0.157, 0.494, 0.608), PINK = vec3(0.722, 0.341, 0.475);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
vec2 rot(vec2 p, float a) { float c = cos(a), s = sin(a); return vec2(c * p.x - s * p.y, s * p.x + c * p.y); }
vec2 mirrorUV(vec2 uv) { return 1.0 - abs(1.0 - mod(uv, 2.0)); }   // tile by reflection, no seams
vec3 A(vec2 uv) { return texture(sTD2DInputs[0], mirrorUV(uv)).rgb; }
vec3 B(vec2 uv) { return texture(sTD2DInputs[1], mirrorUV(uv)).rgb; }

vec3 pal(float i) {   // a seed-chosen trio from the ident palette
    int k = int(mod(i, 6.0));
    if (k == 0) return INK; if (k == 1) return IVORY; if (k == 2) return RED;
    if (k == 3) return YELLOW; if (k == 4) return BLUE; return PINK;
}

// ---- treatments: how the shot's own picture is re-seen --------------------
vec3 treated(vec2 uv) {
    int t = int(uShot.x + 0.5);
    float seed = uShot.w, age = uTime.y;
    float asp = uTD2DInfos[0].res.z / uTD2DInfos[0].res.w;
    if (t == 1) {                       // mirror: one half reflected onto the other
        bool flip = seed > 0.5;
        float x = flip ? 1.0 - uv.x : uv.x;
        x = 0.5 - abs(x - 0.5);
        x = mix(x, x + 0.18, step(0.66, fract(seed * 7.0)));   // sometimes mirror off-centre
        return A(vec2(flip ? 1.0 - x : x, uv.y));
    }
    if (t == 2) {                       // kaleidoscope: 3 to 8 wedges, turning with the bar
        float n = 3.0 + floor(seed * 6.0);
        vec2 p = (uv - 0.5) * vec2(asp, 1.0);
        float a = atan(p.y, p.x) + uTime.w * 0.5 * (seed > 0.5 ? 1.0 : -1.0), r = length(p);
        float w = PI / n;
        a = abs(mod(a, 2.0 * w) - w);
        vec2 q = vec2(cos(a), sin(a)) * r * (0.9 + 0.1 * uAudio.x);
        return A(q / vec2(asp, 1.0) + vec2(0.5, 0.35 + 0.3 * fract(seed * 3.0)));
    }
    if (t == 3) {                       // channel split, kicked apart by hits
        float d = 0.004 + 0.03 * uAudio.y + 0.012 * uAudio.z;
        vec2 dir = rot(vec2(1.0, 0.0), seed * 6.283);
        return vec3(A(uv + dir * d).r, A(uv).g, A(uv - dir * d).b);
    }
    if (t == 4) {                       // three-ink poster from the ident palette
        float l = luma(A(uv)), base = floor(seed * 6.0);
        float n = hash(floor(uv * vec2(640.0, 360.0))) * 0.06 - 0.03;
        // Low thresholds: many scenes are thin bright lines on black, and at 0.28 / 0.62
        // they posterised to a single flat ink (seen in cut_02, 2026-11-10).
        vec3 c = l + n < 0.07 ? pal(base) : (l + n < 0.34 ? pal(base + 2.0) : pal(base + 1.0));
        return c;
    }
    if (t == 5) {                       // punch in: 1.7x to 2.6x on a seed-chosen region, drifting
        float z = 1.7 + 0.9 * fract(seed * 5.0);
        vec2 c = vec2(0.25 + 0.5 * fract(seed * 11.0), 0.3 + 0.4 * fract(seed * 17.0));
        c += 0.02 * vec2(sin(age * 0.7), cos(age * 0.5));
        z *= 1.0 + 0.05 * uAudio.y - 0.02 * age;
        return A(c + (uv - 0.5) / max(z, 1.2));
    }
    if (t == 6) {                       // tiles: a grid of the picture, alternate tiles flipped or zoomed
        vec2 g = vec2(2.0 + floor(seed * 3.0), 2.0 + floor(fract(seed * 7.0) * 2.0));
        vec2 cell = floor(uv * g), f = fract(uv * g);
        float h = hash(cell + floor(seed * 100.0));
        if (mod(cell.x + cell.y, 2.0) > 0.5) f.x = 1.0 - f.x;
        float z = 1.0 + floor(h * 3.0) * 0.5;
        float lit = step(0.5, fract(h * 9.0 + floor(uTime.z))) * 0.25 * uAudio.x;   // tiles wink on beats
        return A(0.5 + (f - 0.5) / z) * (1.0 + lit);
    }
    if (t == 7) {                       // negative
        return 1.0 - A(uv);
    }
    if (t == 8) {                       // slices: horizontal bands sliding against each other on the beat
        float bands = 6.0 + floor(seed * 18.0);
        float b = floor(uv.y * bands);
        float off = (hash(vec2(b, floor(uTime.z))) - 0.5) * 0.35 * (uAudio.x * uAudio.x + 0.15 * uAudio.y);
        return A(vec2(uv.x + off, uv.y));
    }
    if (t == 9) {                       // triptych: three panels, three crops of the same moment
        float panel = floor(uv.x * 3.0), fx = fract(uv.x * 3.0);
        float gap = step(fx, 0.012) + step(0.988, fx);
        float z = 1.0 + panel * 0.7 + 0.5 * fract(seed * 3.0);
        vec2 c = vec2(0.5 + (panel - 1.0) * 0.12, 0.5 + (fract(seed * 13.0 + panel * 0.37) - 0.5) * 0.3);
        vec3 col = A(c + (vec2(fx / 3.0 + 1.0 / 3.0, uv.y) - 0.5) / z);
        if (panel == 1.0 && seed > 0.5) col = 1.0 - col;
        return mix(col, vec3(0.0), min(gap, 1.0));
    }
    if (t == 10) {                      // line art: edges only, in one ink on a ground
        vec2 px = 1.5 / uTD2DInfos[0].res.zw;
        float gx = luma(A(uv + vec2(px.x, 0.0))) - luma(A(uv - vec2(px.x, 0.0)));
        float gy = luma(A(uv + vec2(0.0, px.y))) - luma(A(uv - vec2(0.0, px.y)));
        float e = smoothstep(0.03, 0.16, length(vec2(gx, gy)));
        bool dark = fract(seed * 3.0) > 0.4;      // ink ground with a bright line, or ivory with a dark one
        vec3 ground = dark ? INK * 0.5 : IVORY;
        vec3 line = dark ? pal(1.0 + floor(seed * 5.0)) : (seed > 0.5 ? RED : INK);
        return mix(ground, line, e);
    }
    return A(uv);
}

// ---- layers: a second live scene inside the shot ---------------------------
vec3 layered(vec2 uv, vec3 a) {
    int m = int(uShot.z + 0.5);
    float seed = uShot.w;
    if (m == 0) return a;
    vec3 b = B(uv);
    if (m == 1) {                       // matte: B's brightness chooses between A and A's negative
        float k = smoothstep(0.25, 0.55, luma(b));
        return mix(a, 1.0 - a, k);
    }
    if (m == 2) return abs(a - b);      // difference
    if (m == 3) {                       // split screen along a seed-chosen line, edge nudged by the beat
        float ang = floor(seed * 4.0) * PI * 0.25;
        float d = dot(uv - 0.5, vec2(cos(ang), sin(ang))) + 0.03 * (uAudio.x - 0.5);
        float line = smoothstep(0.004, 0.0, abs(d));
        return mix(d < 0.0 ? a : b, vec3(1.0), line);
    }
    if (m == 4) {                       // inset: B in a framed window
        vec2 c = vec2(seed > 0.5 ? 0.72 : 0.28, fract(seed * 5.0) > 0.5 ? 0.7 : 0.3), half_ = vec2(0.19, 0.19);
        vec2 q = (uv - c) / half_;
        float inside = step(max(abs(q.x), abs(q.y)), 1.0), frame = step(max(abs(q.x), abs(q.y)), 1.06);
        vec3 w = B(0.5 + q * 0.5);
        return mix(mix(a, vec3(0.0), frame), w, inside);
    }
    if (m == 5) return 1.0 - (1.0 - a) * (1.0 - b * 0.8);   // screen: double exposure
    // 6 interleave: stripes of A and B that swap on each beat
    float s = floor(uv.x * (4.0 + floor(seed * 12.0))) + floor(uTime.z);
    return mod(s, 2.0) < 0.5 ? a : b;
}

// ---- transitions: how the shot arrives over the last one --------------------
vec3 arrive(vec2 uv, vec3 now) {
    int t = int(uShot.y + 0.5);
    float p = clamp(uTime.x, 0.0, 1.0), seed = uShot.w;
    if (t == 0 || p >= 1.0) return now;
    vec3 old = B(uv);
    if (t == 1) return now + (1.0 - p) * (1.0 - p) * 1.4;                    // flash
    if (t == 2) {                                                            // whip: old pushed out, smeared
        vec2 dir = rot(vec2(1.0, 0.0), floor(seed * 4.0) * PI * 0.5);
        float e = p * p * (3.0 - 2.0 * p);
        vec2 sh = dir * e;
        vec2 ua = uv - sh + dir, ub = uv - sh;
        float blur = (1.0 - abs(2.0 * p - 1.0)) * 0.08;
        vec3 acc = vec3(0.0);
        for (int i = 0; i < 6; i++) {
            float o = (float(i) / 5.0 - 0.5) * blur;
            vec2 qa = ua + dir * o, qb = ub + dir * o;
            bool in_b = all(greaterThanEqual(qb, vec2(0.0))) && all(lessThanEqual(qb, vec2(1.0)));
            acc += in_b ? B(qb) : treated(qa);
        }
        return acc / 6.0;
    }
    if (t == 3) {                                                            // blocks: the new shot arrives in tiles
        vec2 g = vec2(16.0, 9.0) * (1.0 + floor(seed * 3.0));
        return hash(floor(uv * g) + seed) < p ? now : old;
    }
    if (t == 4) return mod(floor(p * 6.0), 2.0) < 0.5 ? old : now;            // strobe between the two
    if (t == 5) return luma(old) < p * 1.15 ? now : old;                      // dark parts of the old shot open first
    if (t == 6) {                                                            // fall through the old shot
        float z = 1.0 + p * p * 5.0;
        vec3 o = B(0.5 + (uv - 0.5) / z);
        return mix(o, now, smoothstep(0.35, 1.0, p));
    }
    if (t == 7) {                                                            // bands hand over one by one
        float bands = 5.0 + floor(seed * 9.0), b = floor(uv.y * bands);
        return hash(vec2(b, seed)) * 0.7 + 0.3 * (b / bands) < p ? now : old;
    }
    return p < 0.4 ? 1.0 - now : now;                                         // 8: arrives as a negative, then snaps
}

void main()
{
    vec2 uv = vUV.st;
    vec3 c = treated(uv);
    if (uTime.x >= 1.0) c = layered(uv, c);    // B is the old frame until the transition is over
    c = arrive(uv, c);
    fragColor = TDOutputSwizzle(vec4(clamp(c, 0.0, 4.0), 1.0));
}
