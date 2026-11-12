// tone.frag: makes the luminance plane glyph.frag reads. 0.5 is the line between
// "white letters on black" and "black letters on white".
// input 0: render (premultiplied rgba), or another scene's picture prepared to look
//          like one by inprep.frag when the COMP's Input is set (uVoid.y = 1)
// input 1: poster word (white on black)
// The mode (build.py TAKES) decides what the plane holds:
//   0 lit model over the void   1 ghost: flat inverse silhouette on a wall of type
//   2 corridor, no model        3 keyhole: a lit page with the model as its shadow
uniform vec4 uTone;   // x kick pump, y model side (-1 left, +1 right), z evolve, w mode
uniform vec4 uPost;   // x,y poster centre (uv), z poster scale, w beat_pos
uniform vec4 uShot;   // x seconds since the cut, y z w three seeds 0..1
uniform vec4 uVoid;   // x least luminance of the void (the quadtree take fills it with regular type), y 1 = input 0 is an Input picture,
                      // z the same floor in Describe mode, kept clear of the poster word's box so the word still reads
uniform vec4 uMod;    // x model offset from centre (signed), y tiles now, z tiles of this take, w beat parity
out vec4 fragColor;

// Input picture as a luminance for a flat surface in the corridor: the same curve
// the model gets, void where the picture was keyed out.
float pic(vec2 uv)
{
    vec4 c = textureLod(sTD2DInputs[0], clamp(uv, 0.0, 1.0), 0.0);
    float a = clamp(c.a, 0.0, 1.0);
    float l = dot(c.rgb / max(a, 1e-4), vec3(0.30, 0.59, 0.11));
    return mix(0.05, 0.27 + 0.73 * smoothstep(0.03, 0.50, l), a);
}

// A corridor seen from inside: fluorescent tubes on the ceiling, checker carpet,
// doors down both walls, a dark end wall that carries the poster word.
// Returns luminance; k is 1/depth.
float corridor(vec2 uv, out float k)
{
    vec2 q = (uv - uPost.xy) * vec2(1.7778, 1.0);
    float ang = 0.09 * sin(uTone.z * 0.5 + 6.283 * uShot.w);
    q = mat2(cos(ang), -sin(ang), sin(ang), cos(ang)) * q;
    const vec2 hs = vec2(0.60, 0.34);                 // half width, half height at depth 1
    float kx = abs(q.x) / hs.x, ky = abs(q.y) / hs.y;
    k = max(kx, ky);
    float z = 1.0 / max(k, 1e-3);
    // travel: half a tube per beat, plus a lunge that dies in the first half second
    float zz = z * 2.2 + uPost.w * 0.5 - 2.5 * exp(-7.0 * uShot.x);
    float lum;
    if (kx > ky) {
        float h = q.y / k / hs.y;                     // -1 floor .. +1 ceiling
        float c = fract(zz * 0.5 + (q.x < 0.0 ? 0.0 : 0.5));
        bool door = c > 0.22 && c < 0.62 && h < 0.42;
        bool knob = c > 0.52 && c < 0.56 && abs(h + 0.25) < 0.07;
        lum = door ? (knob ? 0.05 : 0.80) : 0.09;
        if (door && uVoid.y > 0.5) {
            // Input: every door is the picture, read left to right on both walls
            float u = (c - 0.22) / 0.40;
            lum = pic(vec2(q.x < 0.0 ? u : 1.0 - u, (h + 0.86) / 1.28));
        }
        if (h < -0.86) lum = 0.04;                    // skirting
    } else if (q.y > 0.0) {
        float x = q.x / k / hs.x;
        float c = fract(zz);
        lum = (abs(x) < 0.26 && c > 0.18 && c < 0.82) ? 1.0 : 0.04;
    } else {
        float x = q.x / k / hs.x;
        lum = mod(floor(x * 2.0 + 4.0) + floor(zz * 2.0), 2.0) > 0.5 ? 0.66 : 0.05;
    }
    lum *= 0.25 + 0.75 * smoothstep(0.26, 0.75, k);   // it gets dark down there
    lum *= 1.0 + 0.30 * uTone.x;                      // kick: the tubes surge
    if (k < 0.30) lum = 0.05;                         // the end wall
    // Input: the end wall is nearer and is a screen showing the picture
    if (uVoid.y > 0.5 && k < 0.55) lum = pic(q / (0.55 * hs) * 0.5 + 0.5);
    return lum;
}

void main()
{
    vec2 uv = vUV.st;
    int mode = int(uTone.w + 0.5);

    // wallpaper: the render repeated as a grid, every other tile mirrored and
    // (in glyph.frag) of opposite polarity
    vec2 tuv = uv;
    float N = 1.0, par = 0.0, lod = 0.0;
    if (uMod.z > 1.5) {
        N = uMod.y;
        vec2 t = (uv - 0.5) * N + 0.5 + vec2(uTone.z * 0.05, 0.0);
        vec2 ti = floor(t);
        tuv = fract(t);
        if (mod(ti.x, 2.0) > 0.5) tuv.x = 1.0 - tuv.x;
        par = mod(ti.x + ti.y + uMod.w, 2.0);
        lod = log2(N);
    }
    vec4 c = textureLod(sTD2DInputs[0], tuv, lod);    // Lod: tuv jumps at tile borders
    float a = clamp(c.a, 0.0, 1.0);
    vec3 rgb = c.rgb / max(a, 1e-4);
    float l = dot(rgb, vec3(0.30, 0.59, 0.11));
    // The model keeps a real shadow side (NOTES.md log 14): below about 0.25 it is
    // black carrying white type, above it a white page carrying black type. The
    // floor of 0.27 keeps the shadow side one weight heavier than the void.
    float lo = 0.27 + 0.73 * smoothstep(0.03, 0.50, l);
    lo *= 1.0 + 0.25 * uTone.x;

    // void: slow diagonal bands of nothing / greyed type, so the dark part of
    // the frame is never still, and a lamp pool of regular type behind the model
    vec2 p = (uv - vec2(0.5 + 0.385 * uMod.x, 0.48)) * vec2(1.7778, 1.0);
    float pool = exp(-dot(p, p) * 4.5) * (N > 1.5 ? 0.0 : 1.0);
    float sweep = 0.5 + 0.5 * sin((uv.x * 1.1 + uv.y * 0.7) * 6.2832 - uTone.z * 0.8);
    float bg = 0.17 * smoothstep(0.55, 0.92, sweep) + 0.14 * pool;
    // at rest the void is at most greyed type, so the poster and the
    // model stand clear of it; a kick lifts the whole field one weight
    bg = min(bg, 0.20) * (1.0 + 0.6 * uTone.x);
    bg = max(bg, uVoid.x);

    // r: luminance   g: poster letter mask   b: model plus keyline (no poster here)
    // a: rim (the band just inside the silhouette; glyph.frag draws it as a white
    //    outline where the model is dark) + 2 * tile parity
    vec2 texel = uTD2DInfos[0].res.xy * N;
    float near = a, inner = a;
    for (int i = 0; i < 8; i++) {
        float ang = 0.7854 * float(i);
        vec2 dir = vec2(cos(ang), sin(ang)) * texel;
        near = max(near, textureLod(sTD2DInputs[0], clamp(tuv + dir * 14.0, 0.0, 1.0), lod).a);
        inner = min(inner, textureLod(sTD2DInputs[0], clamp(tuv + dir * 2.5, 0.0, 1.0), lod).a);
    }
    float rim = step(0.5, a) * (1.0 - step(0.5, inner));
    float key = step(0.5, near);

    vec2 puv = (uv - uPost.xy) / uPost.z + 0.5;
    float word = 0.0;
    if (puv.x > 0.0 && puv.x < 1.0 && puv.y > 0.0 && puv.y < 1.0)
        word = textureLod(sTD2DInputs[1], puv, max(0.0, -log2(uPost.z))).r;

    if (puv.x < 0.0 || puv.x > 1.0 || puv.y < 0.0 || puv.y > 1.0) bg = max(bg, uVoid.z);

    float lum = mix(bg, lo, a);
    if (mode == 1) {
        // ghost: the whole frame is a wall of regular type; the model's lit side is
        // the same wall in inverse video, its shadow side is just the wall
        float wall = 0.33 * (1.0 + 0.30 * uTone.x);
        lum = mix(wall, 0.80, step(0.5, a) * smoothstep(0.05, 0.22, l));
        rim = 0.0;
        key = 0.0;
    } else if (mode == 2) {
        float k;
        lum = corridor(uv, k);
        rim = 0.0;
        key = k < 0.30 ? 0.0 : 1.0;                   // the word lives on the end wall only
        if (uVoid.y > 0.5) key = 1.0;                 // Input: the end wall is the picture, no word
    } else if (mode == 3) {
        // keyhole: inside the word (glyph.frag) there is a lit page; the model is
        // a solid black hole in it, outlined in white (the rim) where it leaves the letters
        float page = 0.78 + 0.12 * (sweep - 0.5);
        lum = mix(page, 0.03, a);
        // Input: the picture itself is what the word is a window onto
        if (uVoid.y > 0.5) lum = mix(0.10, lo, a);
        key = 0.0;
    }
    fragColor = TDOutputSwizzle(vec4(lum, word, key, rim + 2.0 * par));
}
