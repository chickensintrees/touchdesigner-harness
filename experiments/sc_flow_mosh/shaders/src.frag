// Clean source pictures, one per take mode (see TAKES in build.py). Never shown directly
// except on I-frames. The same shader also draws the transplant card (uMod.w = 1).
// Inputs: 0 3D render, premultiplied alpha (hero model 720x720, or the prop field 1280x720),
//         1 stack mask, 2 one-line mark mask, 3 phrase atlas (16 rows in the phrase face),
//         4 card atlas (2x2 Archivo Black cards).
uniform vec4 uTime;   // x beat_pos, y evolve, z pulse, w section index
uniform vec4 uMod;    // x bar_pulse, y energy, z hit_low, w role: 0 picture, 1 transplant card
uniform vec4 uShot;   // x source mode, y seed 0..1, z shot age (s), w arrival punch (1 at the cut, 0 after ~0.5 s)
uniform vec4 uCam;    // prop-field camera: xyz position, w pitch (radians)
uniform vec4 uCam2;   // x tan(half horizontal fov), y yaw (radians), z hit_high, w 1 = Describe mode
uniform float uPW[16];   // phrase widths as a fraction of the atlas width
out vec4 fragColor;

const vec3 INK    = vec3(0.098, 0.169, 0.231);
const vec3 IVORY  = vec3(0.933, 0.894, 0.800);
const vec3 RED    = vec3(0.863, 0.337, 0.239);
const vec3 YELLOW = vec3(0.863, 0.710, 0.239);
const vec3 BLUE   = vec3(0.157, 0.494, 0.608);
const vec3 GREEN  = vec3(0.600, 0.671, 0.329);
const vec3 PINK   = vec3(0.722, 0.341, 0.475);
const vec3 ORANGE = vec3(0.890, 0.480, 0.180);
const float PI = 3.14159265;
const float ASPECT = 16.0 / 9.0;

float hash(float n) { return fract(sin(n * 12.9898 + 4.1414) * 43758.5453); }
mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
float lum(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
bool inside(vec2 u) { return u.x > 0.0 && u.x < 1.0 && u.y > 0.0 && u.y < 1.0; }

void palette(int k, out vec3 A, out vec3 B, out vec3 C, out vec3 W, out vec3 S, out vec3 D)
{
    if (k == 0)      { A = INK;    B = RED;    C = YELLOW; W = IVORY; S = INK; D = BLUE; }
    else if (k == 1) { A = YELLOW; B = BLUE;   C = RED;    W = INK;   S = IVORY; D = ORANGE; }
    else if (k == 2) { A = PINK;   B = INK;    C = YELLOW; W = IVORY; S = INK; D = RED; }
    else if (k == 3) { A = BLUE;   B = IVORY;  C = RED;    W = INK;   S = YELLOW; D = GREEN; }
    else if (k == 4) { A = GREEN;  B = INK;    C = PINK;   W = IVORY; S = INK; D = YELLOW; }
    else if (k == 5) { A = RED;    B = IVORY;  C = BLUE;   W = INK;   S = YELLOW; D = ORANGE; }
    else             { A = IVORY;  B = RED;    C = BLUE;   W = INK;   S = YELLOW; D = YELLOW; }
}

// coverage of a wordmark mask (4:3 canvas) placed at centre c, canvas height s, angle a
float word(int idx, vec2 p, vec2 c, float s, float a)
{
    vec2 q = rot(a) * (p - c) / s;
    vec2 muv = q * vec2(0.75, 1.0) + 0.5;
    if (!inside(muv)) return 0.0;
    return texture(sTD2DInputs[idx], muv).r;
}

// coverage of phrase i; q is 0..1 across the phrase's own width and its row's height
float phrase(int i, vec2 q)
{
    if (!inside(q)) return 0.0;
    vec2 a = vec2((10.0 + q.x * uPW[i] * 1280.0) / 1280.0, (float(i) + q.y) / 16.0);
    return textureLod(sTD2DInputs[3], a, 0.0).r;
}
float phraseAspect(int i) { return uPW[i] * 16.0; }   // width / height of the phrase's quad

// hero model (square render, 1 unit high at scale 1) with an optional ink sticker shadow
vec3 hero(vec3 col, vec2 p, vec2 mc, float msc, float shadow, float boost)
{
    vec2 muv = (p - mc) / msc + 0.5;
    vec2 suv = muv - vec2(0.028, -0.028);
    if (shadow > 0.0 && inside(suv))
        col = mix(col, INK, texture(sTD2DInputs[0], suv).a * shadow);
    if (inside(muv)) {
        vec4 m = texture(sTD2DInputs[0], muv);
        col = col * (1.0 - m.a) + m.rgb * boost;
    }
    return col;
}

// ---------------------------------------------------------------- mode 0 / 3: poster
vec3 poster(vec2 p)
{
    float bp = uTime.x, ev = uTime.y, pulse = uTime.z, punch = uShot.w;
    float sec = uTime.w + floor(uShot.y * 53.0);
    float seed = hash(sec + 0.37);
    int k = int(mod(sec, 7.0));
    int lay = int(mod(sec, 3.0));
    vec3 A, B, C, W, S, D;
    palette(k, A, B, C, W, S, D);

    float ang = mix(-0.9, 0.9, seed) + 0.12 * sin(bp * PI / 4.0);
    vec2 n = vec2(cos(ang), sin(ang));
    vec2 t = vec2(-n.y, n.x);
    float d = dot(p, n) + 0.22 * sin(bp * PI / 2.0 + seed * 6.0);
    float aa = 1.5 / 720.0;
    float inB = smoothstep(-aa, aa, d);
    float st = fract(dot(p, t) * 5.0 + ev * 0.35);
    float stripe = smoothstep(0.5 - 0.02, 0.5, st) * (1.0 - smoothstep(1.0 - 0.02, 1.0, st));
    vec3 colA = mix(A, D, stripe);
    vec2 g = rot(0.5) * p * 9.0 + vec2(-ev * 0.4, bp * 0.25);
    float dots = 1.0 - smoothstep(0.22, 0.26, length(fract(g) - 0.5));
    vec3 colB = mix(B, mix(B, A, 0.5), dots);
    vec3 col = mix(colA, colB, inB);

    vec2 mc = (lay == 0) ? vec2(0.42, 0.0) : (lay == 1) ? vec2(-0.45, 0.02) : vec2(0.0, 0.15);
    vec2 dc = mc + 0.07 * vec2(cos(bp * PI / 2.0), sin(bp * PI / 2.0));
    float rad = 0.40 + 0.05 * pulse + 0.03 * uMod.x + 0.5 * punch;
    float disc = 1.0 - smoothstep(rad - aa, rad + aa, length(p - dc));
    col = mix(col, C, disc);

    int idx; vec2 wc; float ws; float wa;
    if (lay == 0)      { idx = 1; wc = vec2(-0.20, 0.02); ws = 1.18; wa = 0.06; }
    else if (lay == 1) { idx = 1; wc = vec2(0.22, -0.03); ws = 1.15; wa = -0.05; }
    else               { idx = 2; wc = vec2(0.0, -0.31);  ws = 1.58; wa = 0.0; }
    wc += vec2((lay == 2 ? 0.03 : 0.06) * sin(bp * PI / 2.0 + seed * 3.0), 0.035 * sin(bp * PI));
    ws *= 1.0 + 0.07 * pulse + 0.6 * punch;        // the wordmark slams in from oversize
    wa += 0.05 * sin(bp * PI / 4.0) + 0.25 * punch;
    vec2 so = vec2(0.022, -0.022);
    float wsh = word(idx, p - so, wc, ws, wa);
    float wm = word(idx, p, wc, ws, wa);
    col = mix(col, S, wsh);
    col = mix(col, W, wm);

    float msc = (lay == 2) ? 0.98 : 1.12;
    msc *= 1.0 + 0.05 * pulse - 0.45 * punch;      // while the model grows into place
    return hero(col, p, mc, msc, 0.85, 1.0);
}

// ---------------------------------------------------------------- prop field camera ray
vec3 camRay(vec2 p)
{
    float k = 2.0 * uCam2.x / ASPECT;
    vec3 d = normalize(vec3(p.x * k, p.y * k, -1.0));
    float cx = cos(uCam.w), sx = sin(uCam.w);
    d = vec3(d.x, cx * d.y - sx * d.z, sx * d.y + cx * d.z);
    float cy = cos(uCam2.y), sy = sin(uCam2.y);
    return vec3(cy * d.x + sy * d.z, d.y, -sy * d.x + cy * d.z);
}

// ---------------------------------------------------------------- mode 1: the aisle
// A sideways tracking shot down rows of props. Carpet tiles, ceiling panels and
// fluorescent tubes are drawn here by ray-plane hits so they match the Render TOP's camera.
vec3 aisle(vec2 p, vec2 uv)
{
    vec3 ro = uCam.xyz, d = camRay(p);
    vec3 WALL = vec3(0.839, 0.804, 0.710), CARP = vec3(0.490, 0.494, 0.467), CARP2 = vec3(0.424, 0.471, 0.376);
    vec3 TUBE = vec3(0.92, 1.0, 0.82);
    vec3 fogc = WALL * vec3(0.84, 0.88, 0.78);
    vec3 col = fogc; float t = 1e3;
    if (d.y < -1e-4) {
        t = -ro.y / d.y;
        vec3 h = ro + t * d;
        vec2 c = floor(h.xz / 0.8);
        col = mix(CARP, CARP2, mod(c.x + c.y, 2.0));
        vec2 e = abs(fract(h.xz / 0.8) - 0.5);
        col *= 1.0 - 0.4 * smoothstep(0.46, 0.5, max(e.x, e.y));
    } else if (d.y > 1e-4) {
        t = (2.6 - ro.y) / d.y;
        vec3 h = ro + t * d;
        col = vec3(0.60, 0.58, 0.50);
        vec2 e = abs(fract(h.xz) - 0.5);
        col *= 1.0 - 0.3 * smoothstep(0.46, 0.5, max(e.x, e.y));
        vec2 f = abs(fract(h.xz / 2.0) - 0.5);
        float tb = step(f.x, 0.05) * step(f.y, 0.36);
        col = mix(col, TUBE * (1.5 + 0.5 * uTime.z + 0.6 * uShot.w), tb);
    }
    col = mix(col, fogc, 1.0 - exp(-t * 0.06));
    float hot = smoothstep(1.0, 1.2, lum(col));          // only the tubes are brighter than paper
    vec4 m = texture(sTD2DInputs[0], uv);
    col = col * (1.0 - m.a) + m.rgb * 0.8;
    int g = int(mod(floor(uShot.y * 30.0), 3.0));
    if (g == 1) col = pow(col, vec3(1.25)) * vec3(0.70, 1.0, 0.60);                   // sickly green
    if (g == 2) col = col * (0.3 + 0.7 * col) * vec3(0.22, 0.34, 0.56) + hot * vec3(0.75, 1.0, 0.70);   // lights out
    return col;
}

// ---------------------------------------------------------------- mode 6: the floor plan
// The same props seen from straight above on ident-palette tiles, with a phrase painted
// across the floor.
vec3 plan(vec2 p, vec2 uv)
{
    vec3 A, B, C, W, S, D;
    int k = int(mod(floor(uShot.y * 70.0) + uTime.w, 7.0));
    palette(k, A, B, C, W, S, D);
    vec3 ro = uCam.xyz, d = camRay(p);
    float t = -ro.y / min(d.y, -1e-4);
    vec3 h = ro + t * d;
    vec2 g = h.xz / 1.6;
    vec2 c = floor(g);
    vec3 col = mix(A, B, mod(c.x + c.y, 2.0));
    float aa = 0.012 * ro.y / 13.0;
    col = mix(col, C, 1.0 - smoothstep(0.34 - aa, 0.34 + aa, length(fract(g) - 0.5)));
    int pi = int(mod(floor(uShot.y * 16.0) + uTime.w, 16.0));
    float hgt = 16.0 / phraseAspect(pi);              // the phrase spans exactly one 16-unit period
    float zc = -4.0;
    float tx = phrase(pi, vec2(fract(h.x / 16.0), (zc - h.z) / hgt + 0.5));
    col = mix(col, W, smoothstep(0.35, 0.65, tx));
    col = mix(col, INK, texture(sTD2DInputs[0], uv - vec2(0.010, -0.018)).a * 0.8);
    vec4 m = texture(sTD2DInputs[0], uv);
    return col * (1.0 - m.a) + m.rgb * 0.85;
}

// ---------------------------------------------------------------- mode 2: transplant
// The motion donor: a huge turning model on loud stripes. It is never shown; only its
// motion (and, on kicks, its frame difference) reaches the screen.
vec3 donor(vec2 p)
{
    float bp = uTime.x, ev = uTime.y;
    vec3 A, B, C, W, S, D;
    palette(int(mod(uTime.w, 7.0)), A, B, C, W, S, D);
    vec2 t = vec2(cos(0.6), sin(0.6));
    float st = step(0.5, fract(dot(p, t) * 3.0 + ev * 0.5));
    vec3 col = mix(A, D, st);
    vec2 mc = vec2(mix(-0.35, 0.35, hash(uShot.y * 13.0)), -0.03) + 0.12 * vec2(cos(bp * PI / 2.0), sin(bp * PI / 2.0));
    return hero(col, p, mc, 1.85 * (1.0 + 0.10 * uTime.z + 0.5 * uShot.w), 0.85, 1.0);
}

// The I-frame picture: one big off-centre phrase card, flat and still.
vec3 card(vec2 p)
{
    float sd = uShot.y;
    int ci = int(mod(floor(sd * 4.0) + uTime.w, 4.0));
    int pk = int(mod(floor(sd * 16.0), 4.0));
    vec3 bg, fg, sh;
    if (pk == 0)      { bg = vec3(0.929, 0.890, 0.784); fg = vec3(0.659, 0.196, 0.169); sh = INK; }
    else if (pk == 1) { bg = INK;    fg = YELLOW; sh = RED; }
    else if (pk == 2) { bg = PINK;   fg = IVORY;  sh = INK; }
    else              { bg = YELLOW; fg = INK;    sh = IVORY; }
    float s = mix(1.15, 1.6, hash(sd * 7.7));
    vec2 c = vec2(mix(-0.30, 0.30, hash(sd * 5.1)), mix(-0.10, 0.10, hash(sd * 9.7)));
    float a = mix(-0.10, 0.10, hash(sd * 3.3));
    if (uCam2.w > 0.5) {
        // Describe mode: the card's words must be readable whole, so it stays inside the
        // frame (the Describe cards are set smaller in their cells to match) and above the label
        s = mix(1.0, 1.18, hash(sd * 7.7));
        c = c * vec2(0.4, 0.4) + vec2(0.0, 0.035);
        a *= 0.6;
    }
    vec2 cell = vec2(mod(float(ci), 2.0), floor(float(ci) / 2.0));
    vec3 col = bg;
    for (int i = 0; i < 2; i++) {
        vec2 q = rot(a) * (p - c - (i == 0 ? vec2(0.03, -0.03) : vec2(0.0))) / s;
        vec2 cuv = q * vec2(1.0 / ASPECT, 1.0) + 0.5;
        if (inside(cuv)) {
            float v = smoothstep(0.35, 0.65, textureLod(sTD2DInputs[4], (cell + cuv) / 2.0, 0.0).r);
            col = mix(col, i == 0 ? sh : fg, v);
        }
    }
    // a rule and a small line in the phrase face, like a sheet's header, pinned to a corner
    float ry = 0.5 - 0.085;
    col = mix(col, fg, step(abs(p.y - ry), 0.004) * step(abs(p.x), 0.8));
    int pi = int(mod(floor(sd * 16.0) + 9.0, 16.0));
    float ph = 0.045;
    col = mix(col, fg, step(0.5, phrase(pi, (p - vec2(-0.80, ry + 0.012)) / vec2(ph * phraseAspect(pi), ph))));
    return col;
}

// ---------------------------------------------------------------- mode 4: 1-bit wall
float bayer4(vec2 f)
{
    int x = int(mod(f.x, 4.0)), y = int(mod(f.y, 4.0));
    int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
    return (float(m[y * 4 + x]) + 0.5) / 16.0;
}

vec3 wall(vec2 p, vec2 uv)
{
    float bp = uTime.x, ev = uTime.y, sd = uShot.y;
    float hr0 = hash(sd * 3.7);
    float rows = hr0 < 0.33 ? 5.0 : (hr0 < 0.66 ? 8.0 : 13.0);
    float y = uv.y * rows, r = floor(y), fy = fract(y);
    float hr = hash(r * 7.3 + floor(sd * 31.0) + uTime.w * 1.7);
    int pi = int(mod(floor(hr * 16.0), 16.0));
    float hrow = 1.0 / rows;
    float wid = hrow * 0.8 * phraseAspect(pi);
    float period = wid + hrow * 0.9;
    float dir = mod(r, 2.0) < 0.5 ? 1.0 : -1.0;
    float beatstep = floor(bp) + smoothstep(0.0, 0.3, fract(bp));
    float x = p.x + dir * (ev * 0.30 * (0.5 + hr) + 0.05 * beatstep) + hr * 3.0;
    float tx = step(0.5, phrase(pi, vec2(mod(x, period) / wid, (fy - 0.1) / 0.8)));
    float inv = step(0.62, hash(r * 3.1 + uTime.w + floor(sd * 13.0)));      // some rows are white bars
    float v = mix(tx, 1.0 - tx, inv);
    // the model, dithered, punched through the text
    vec2 mc = vec2(mix(-0.5, 0.5, hash(sd * 11.0)), 0.0);
    float msc = 1.5 * (1.0 + 0.06 * uTime.z + 0.5 * uShot.w);
    vec2 muv = (p - mc) / msc + 0.5;
    if (inside(muv)) {
        vec4 m = texture(sTD2DInputs[0], muv);
        float edge = texture(sTD2DInputs[0], muv + vec2(0.006, 0.0)).a + texture(sTD2DInputs[0], muv - vec2(0.006, 0.0)).a
                   + texture(sTD2DInputs[0], muv + vec2(0.0, 0.006)).a + texture(sTD2DInputs[0], muv - vec2(0.0, 0.006)).a;
        if (edge > 0.2) v = 0.0;                                   // black keyline
        if (m.a > 0.5) v = step(bayer4(floor(gl_FragCoord.xy / 3.0)), pow(lum(m.rgb), 0.7) * 1.25);
    }
    if (hash(sd * 19.0) < 0.4) v = 1.0 - v;
    return vec3(v);
}

// ---------------------------------------------------------------- mode 5: the void
// Nearly nothing: a small prop, a caption and a few floating tubes in the dark. The
// mosh pass turns every light thing into a rising column (vertical sort).
vec3 voidm(vec2 p)
{
    float ev = uTime.y, sd = uShot.y, aa = 1.5 / 720.0;
    int hk = int(mod(floor(sd * 25.0), 5.0));
    vec3 H = hk == 0 ? vec3(1.0, 0.72, 0.22) : hk == 1 ? vec3(0.55, 0.80, 1.0) : hk == 2 ? vec3(1.0, 0.25, 0.18)
           : hk == 3 ? vec3(0.80, 1.0, 0.62) : vec3(1.0, 0.96, 0.86);
    vec3 col = vec3(0.012, 0.018, 0.030) + 0.02 * H * smoothstep(0.5, -0.5, p.y);
    float si = floor(sd * 17.0);
    for (int i = 0; i < 5; i++) {
        float fi = float(i);
        float y = mix(-0.42, 0.40, hash(fi * 3.1 + si));
        float x0 = mix(-0.8, 0.8, hash(fi * 5.7 + si)) + 0.3 * sin(ev * 0.35 + fi * 2.1);
        float len = 0.08 + 0.16 * hash(fi * 9.3 + si);
        float bar = (1.0 - smoothstep(len - aa, len + aa, abs(p.x - x0))) * (1.0 - smoothstep(0.005 - aa, 0.005 + aa, abs(p.y - y)));
        float flick = 0.55 + 0.45 * step(0.3, hash(fi + floor(uTime.x * 2.0))) + 0.6 * uCam2.z + uShot.w;
        col = mix(col, H * min(1.0, flick), bar);
    }
    vec2 mc = vec2(mix(-0.6, 0.6, hash(sd * 11.0)), mix(-0.30, -0.12, hash(sd * 23.0)));
    col = hero(col, p, mc, 0.46 * (1.0 + 0.10 * uTime.z + 1.2 * uShot.w), 0.0, 1.35);
    int pi = int(mod(floor(sd * 16.0) + uTime.w, 16.0));
    float ph = 0.038;
    float wd = ph * phraseAspect(pi);
    vec2 pc = vec2(clamp(mc.x - wd * 0.5, -0.86, 0.86 - wd), mc.y - 0.25);
    col = mix(col, H, step(0.5, phrase(pi, (p - pc) / vec2(wd, ph))));
    return col;
}

void main()
{
    vec2 uv = vUV.st;
    vec2 p = (uv - 0.5) * vec2(ASPECT, 1.0);
    int mode = int(uShot.x + 0.5);
    vec3 col;
    if (uMod.w > 0.5)   col = card(p);
    else if (mode == 1) col = aisle(p, uv);
    else if (mode == 2) col = donor(p);
    else if (mode == 4) col = wall(p, uv);
    else if (mode == 5) col = voidm(p);
    else if (mode == 6) col = plan(p, uv);
    else                col = poster(p);
    fragColor = TDOutputSwizzle(vec4(clamp(col, 0.0, 1.0), 1.0));
}
