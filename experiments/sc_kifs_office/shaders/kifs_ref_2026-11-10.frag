// sc_kifs_office: ray-marched letter architecture, several takes of one folded lattice.
// Input 0: text wall, 4 rows (r = letter height, r-g = "red ink" mask), repeat extend, mipmapped.
// Input 1: phrase wall, 8 rows, same encoding.
// The take (build.py TAKES) picks architecture, camera, lighting and grade through uTakeA..D.
uniform vec4 uCam;   // evolve, beat_pos, section, energy
uniform vec4 uFold;  // bass fold angle, vocal fold angle, cavity (bar_pulse), beat pulse
uniform vec4 uHit;   // kick travel 0..1, kick strength, hit_mid, hit_high
uniform vec4 uShot;  // seed, age, take, arrival (1 at the cut, 0 half a second later)
uniform vec4 uTakeA; // arch, cam, light, grade
uniform vec4 uTakeB; // fold bias a, fold bias b, atlas (0 wall, 1 phrases), relief multiplier
uniform vec4 uTakeC; // travel speed, focal length, fog density, text scale
uniform vec4 uTakeD; // fold iterations, block shrink (opens gaps between the blocks), unused, unused

out vec4 fragColor;

const vec3 FLUO  = vec3(0.863, 0.894, 0.776);
const vec3 PUTTY = vec3(0.784, 0.749, 0.651);
const vec3 CRT   = vec3(0.494, 0.608, 0.690);
const vec3 RED   = vec3(0.659, 0.196, 0.169);
const vec3 PAPER = vec3(0.929, 0.890, 0.784);
const vec3 AMBER = vec3(0.784, 0.537, 0.184);
const vec3 INK   = vec3(0.098, 0.169, 0.231);
const vec3 IVORY = vec3(0.933, 0.894, 0.800);

const float CELL = 4.0;      // lattice period in world units
const float RELIEF = 0.03;   // letter emboss height
const float TS = 0.5;        // text tiles per world unit (lattice surfaces)
const float REACH = 14.0;    // how far a kick's pulse runs down the nave
const float TP = 2.0;        // tube spacing along the nave
const float TY = 0.74;       // tube height above the path
const float TW = 0.40;       // tube half length (across the nave)
const float FY = -0.17;      // inscription frieze: centre height and half height
const float FH = 0.27;
const float PLATE = 1.86;    // arch 3: the lattice is sliced at this z (just inside a cell face)
const float ROT_R = 2.6;     // arch 4: radius of the rotunda carved round the origin

// arch: 0 nave + frieze, 1 square shaft, 2 block standing on a floor, 3 sliced plate, 4 rotunda, 5 diagonal cut
// cam:  0 fly the nave, 1 plunge down the shaft, 2 orbit outside, 3 macro strafe, 4 inside the rotunda,
//       5 orthographic onto the cut, 6 sideways along the nave wall
// light: 0 battens, 1 ring lights, 2 sun, 3 orb at the origin, 4 ambient occlusion only
// grade: 0 fluorescent green, 1 one-bit dither, 2 beige daylight, 3 ink and ivory, 4 amber dark,
//        5 white clay, 6 emergency red
int gArch, gCamM, gLight, gGrade, gIter;
float gSeed, gArr, gRel;
vec3 gOff; float gRoll; float gLane; float gPow; float gCamz;
vec3 gBox;                       // arch 2: half size of the block
vec3 gCN, gCR, gCU; float gCH;   // arch 5: cut plane normal, in-plane axes, offset
vec3 gKickO;                     // where a kick's pulse starts (arch 3 and 5)
vec3 gSun;

mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
float hash(float n) { return fract(sin(n * 127.1) * 43758.5453); }
float h1(float k) { return hash(gSeed * 91.7 + k * 1.37); }    // per-shot random numbers

void sectionState() {
    float s = uCam.z + floor(gSeed * 61.0);
    gOff = vec3(1.0) + 0.14 * (vec3(hash(s + 1.0), hash(s + 2.0), hash(s + 3.0)) - 0.5);
    gRoll = (hash(s + 4.0) - 0.5) * 0.7;
    gLane = hash(s + 5.0);
    gPow = (gGrade == 0 && hash(s + 6.0) < 0.22) ? 0.05 : 1.0;   // nave take: some shots are a power cut
}

vec2 path(float z) {
    return vec2(sin(z * 0.21) * 0.30 + sin(z * 0.13) * 0.18, cos(z * 0.17) * 0.20);
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}

float naveA() { return 0.72 + 0.20 * uFold.z; }

// the nave: a pointed arch over a box, following the camera path (negative inside)
float naveC(vec2 c) {
    float a = naveA();
    float arch = length(vec2(abs(c.x) + a, c.y)) - 2.0 * a;
    float box = max(abs(c.x) - a, -c.y - 0.62);
    return c.y > 0.0 ? arch : box;
}

float lattice(vec3 p) {
    vec3 q = p / (CELL * 0.5);
    q = mod(q + 1.0, 2.0) - 1.0;
    float s = 1.0;
    float S = 3.0;
    mat2 ra = rot(uFold.x + uTakeB.x), rb = rot(uFold.y + uTakeB.y);
    for (int i = 0; i < 4; i++) {
        if (i >= gIter) break;
        q = abs(q);
        q.xy *= ra;
        q.yz *= rb;
        if (q.x < q.y) q.xy = q.yx;
        if (q.x < q.z) q.xz = q.zx;
        if (q.y < q.z) q.yz = q.zy;
        q = q * S - gOff * (S - 1.0);
        if (q.z < -0.5 * gOff.z * (S - 1.0)) q.z += gOff.z * (S - 1.0);
        s *= S;
    }
    return sdBox(q, vec3(1.0 - 0.22 * uFold.z - uTakeD.y)) / s * (CELL * 0.5);
}

float base(vec3 p) {
    float d = lattice(p);
    if (gArch == 0) {
        vec2 c = p.xy - path(p.z);
        float nv = naveC(c);
        d = max(d, -nv);                                         // carve the nave
        // the inscription frieze: an unbroken steel belt at eye height on both walls
        float fr = max(abs(nv) - 0.035, abs(c.y - FY) - FH);
        return min(d, fr);
    }
    if (gArch == 1) {
        vec2 c = abs(p.xy - path(p.z));
        return max(d, naveA() - max(c.x, c.y));
    }
    if (gArch == 2) return min(max(d, sdBox(p, gBox)), p.y + gBox.y);
    if (gArch == 3) return max(d, p.z - PLATE);
    if (gArch == 4) return max(d, ROT_R - length(p));
    return max(d, dot(p, gCN) - gCH);
}

// signed distance from the front of the kick's pulse
float frontD(vec3 p) {
    if (gArch <= 1) return p.z - (gCamz + uHit.x * REACH);
    if (gArch == 3) return p.x - (gKickO.x - 2.2 + uHit.x * 4.4);
    if (gArch == 5) return length(p - gKickO) - uHit.x * 6.0;
    return length(p) - (0.3 + uHit.x * 8.0);
}

// brightness of the tube whose centre is at zc
float tubeB(float zc) {
    float id = floor(zc / TP);
    float b = gPow * (0.45 + 0.75 * uCam.w) * (0.75 + 0.45 * uFold.w);
    // hats knock random tubes out for a moment (a new set every half beat)
    if (gGrade == 0) b *= 1.0 - 0.85 * min(uHit.w, 1.0) * step(0.55, hash(id * 3.7 + floor(uCam.y * 2.0)));
    // emergency take: alternate tubes strobe, swapping on every beat
    if (gGrade == 6) b *= mix(0.14, 1.9, mod(id + floor(uCam.y), 2.0)) * (1.0 - 0.5 * min(uHit.w, 1.0));
    // the kick: tubes fire in sequence down the nave and die away behind the front
    float dz = zc - (gCamz + uHit.x * REACH);
    b += 1.9 * uHit.y * (dz > 0.0 ? exp(-dz * dz * 0.9) : exp(dz * 0.45));
    // arrival: the tubes strike one after another away from the camera
    b *= smoothstep(0.0, 0.25, (1.0 - gArr) * 1.25 - abs(zc - gCamz) / 16.0);
    return b;
}

// fluorescent battens across the nave (or square rings round the shaft); returns (distance, brightness)
vec2 tube(vec3 p) {
    float zc = (floor(p.z / TP) + 0.5) * TP;
    vec2 c = p.xy - path(zc);
    vec3 q;
    if (gArch == 1) q = vec3(max(abs(c.x), abs(c.y)) - naveA() * 0.93, 0.0, p.z - zc);
    else q = vec3(max(abs(c.x) - TW, 0.0), c.y - TY, p.z - zc);
    return vec2(length(q) - 0.02, tubeB(zc));
}

vec3 baseNormal(vec3 p, float e) {
    vec2 k = vec2(1.0, -1.0);
    return normalize(k.xyy * base(p + k.xyy * e) + k.yyx * base(p + k.yyx * e) +
                     k.yxy * base(p + k.yxy * e) + k.xxx * base(p + k.xxx * e));
}

vec2 smp(vec2 uv, float lod) {
    vec4 t = uTakeB.z > 0.5 ? textureLod(sTD2DInputs[1], uv, lod) : textureLod(sTD2DInputs[0], uv, lod);
    return vec2(t.r, t.r - t.g);
}

// 1 on the inner face of the frieze
float onFrieze(vec3 p, vec3 w) {
    if (gArch != 0) return 0.0;
    vec2 c = p.xy - path(p.z);
    return (w.x > 0.5 && abs(c.y - FY) < FH + 0.01 && abs(abs(c.x) - naveA()) < 0.09) ? 1.0 : 0.0;
}

// text height and red mask; the frieze gets one clean row of big words, everything else is triplanar
vec2 txt(vec3 p, vec3 n, vec3 w, float lod) {
    vec3 sg = sign(n);
    if (onFrieze(p, w) > 0.5) {
        float nr = uTakeB.z > 0.5 ? 8.0 : 4.0;                  // rows in the chosen atlas
        float fu = 2.0 * FH * nr;                               // world units per row, letters kept square
        float cy = p.y - path(p.z).y;
        float u = sg.x * p.z / fu + 0.25 * sg.x;
        float wi = floor(u);
        float row = mod(wi + sg.x + uCam.z, 3.0) < 0.5 ? 1.0 : (mod(wi, 5.0) < 0.5 ? 2.0 : 0.0);
        if (nr > 5.0) row = floor(hash(wi * 1.7 + sg.x + floor(gSeed * 53.0)) * 7.999);
        float vr = (cy - (FY - FH)) / (2.0 * FH);
        float vb = clamp(vr, 0.04, 0.96);
        vec2 r = smp(vec2(u, (nr - 1.0 - row + vb) / nr), max(lod - 0.6, 0.0));
        // ruled lines above and below the words, and a tick between them, like a field on a printed sheet
        float rule = 1.0 - smoothstep(0.012, 0.03, min(abs(vr - 0.07), abs(vr - 0.93)));
        float tick = (1.0 - smoothstep(0.004, 0.012, abs(fract(u) - 0.5) - 0.488)) * step(abs(vr - 0.5), 0.43);
        r.x = max(r.x, 0.62 * max(rule, tick));
        return r;
    }
    float ts = TS * uTakeC.w;
    if (gArch == 5 && abs(dot(p, gCN) - gCH) < 0.012 + RELIEF * gRel) {
        // the cut face: one big sheet of type lying in the plane of the cut
        return smp(vec2(dot(p, gCR), dot(p, gCU)) * ts, lod);
    }
    vec2 r = vec2(0.0);
    if (w.x > 0.02) r += w.x * smp(vec2(sg.x * p.z, p.y) * ts, lod);
    if (w.y > 0.02) r += w.y * smp(vec2(p.x, sg.y * p.z) * ts, lod);
    if (w.z > 0.02) r += w.z * smp(vec2(-sg.z * p.x, p.y) * ts + 0.37, lod);
    return r;
}

float relief(vec3 p, vec3 n, vec3 w, float lod) {
    return base(p) - RELIEF * gRel * txt(p, n, w, lod).x;
}

float softShadow(vec3 p, vec3 l, float maxd, float k, int steps) {
    float sh = 1.0; float st = 0.04;
    for (int i = 0; i < 12; i++) {
        if (i >= steps) break;
        float d = base(p + l * st);
        sh = min(sh, k * d / st);
        st += clamp(d, 0.03, 0.35);
        if (st > maxd || sh < 0.02) break;
    }
    return clamp(sh, 0.0, 1.0);
}

// light arriving at p from the batten at zc: diffuse * falloff * soft shadow (xyz = direction, w = amount)
vec4 tubeLight(vec3 p, vec3 n, float zc) {
    vec2 pc = path(zc);
    vec3 lp = vec3(pc.x + clamp(p.x - pc.x, -TW, TW), pc.y + TY - 0.04, zc);
    if (gArch == 1) lp = vec3(pc + 0.35 * (p.xy - pc), zc);
    vec3 l = lp - p; float ld = length(l); l /= ld;
    float dif = max(dot(n, l), 0.0);
    float att = 1.0 / (0.2 + ld * ld * 1.6);
    float amt = dif * att * tubeB(zc);
    if (amt < 0.004) return vec4(l, 0.0);
    return vec4(l, amt * softShadow(p, l, ld, 9.0, 7));
}

float bayer4(vec2 p) {
    ivec2 i = ivec2(mod(p, 4.0));
    int idx = i.x + i.y * 4;
    int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
    return (float(m[idx]) + 0.5) / 16.0;
}

void lookAt(vec3 ro, vec3 ta, vec3 upv, out vec3 f, out vec3 rgt, out vec3 up) {
    f = normalize(ta - ro);
    rgt = normalize(cross(upv, f));
    up = cross(f, rgt);
}

void main() {
    gArch = int(uTakeA.x + 0.5); gCamM = int(uTakeA.y + 0.5); gLight = int(uTakeA.z + 0.5); gGrade = int(uTakeA.w + 0.5);
    gIter = int(uTakeD.x + 0.5);
    gSeed = uShot.x; gArr = clamp(uShot.w, 0.0, 1.0);
    float arr2 = gArr * gArr;
    gRel = uTakeB.w;
    sectionState();
    vec2 uv = (vUV.st - 0.5) * vec2(uTDOutputInfo.res.z / uTDOutputInfo.res.w, 1.0);

    float ev = uCam.x * uTakeC.x;
    float camz = ev * 0.55 - arr2 * 0.9;                       // every shot arrives with a short rush forward
    gCamz = camz;
    float focal = uTakeC.y - 0.07 * uHit.y - 0.22 * arr2;      // each kick shoves the lens wider
    vec3 ro, rd, f, rgt, up;
    float roll = 0.0; float tfar = 24.0; float t = 0.02; bool ortho = false;
    gBox = vec3(4.0); gCN = vec3(0.0, 0.0, 1.0); gCR = vec3(1.0, 0.0, 0.0); gCU = vec3(0.0, 1.0, 0.0); gCH = 0.0;
    gKickO = vec3(0.0); gSun = normalize(vec3(0.5, 0.6, 0.4));

    if (gCamM == 0) {                                          // flying the nave
        ro = vec3(path(camz) + vec2((gLane - 0.5) * 0.3, -0.14 + 0.05 * sin(uCam.x * 0.11)), camz);
        float az = camz + 1.6;
        vec3 ta = vec3(path(az) + vec2(0.12 * sin(uCam.x * 0.09), 0.02 + 0.12 * sin(uCam.x * 0.07)), az);
        lookAt(ro, ta, vec3(0, 1, 0), f, rgt, up);
        roll = gRoll + 0.3 * sin(uCam.x * 0.05);
    } else if (gCamM == 1) {                                   // plunging down the shaft
        float a0 = h1(1.0) * 6.283;
        ro = vec3(path(camz) + 0.28 * naveA() * vec2(cos(a0), sin(a0)), camz);
        vec3 ta = vec3(path(camz + 3.0) - 0.1 * vec2(cos(a0), sin(a0)), camz + 3.0);
        lookAt(ro, ta, vec3(0, 1, 0), f, rgt, up);
        float q = uCam.y * 0.25;                               // a quarter turn snapped on every bar
        roll = h1(2.0) * 6.283 + 1.5708 * (floor(q) + smoothstep(0.0, 0.18, fract(q)));
    } else if (gCamM == 6) {                                   // sideways along the nave wall
        float side = h1(1.0) < 0.5 ? -1.0 : 1.0;
        ro = vec3(path(camz) + vec2(-side * 0.5 * naveA(), FY + mix(-0.05, 0.22, h1(2.0))), camz);
        vec3 fw = normalize(vec3(side, mix(-0.18, 0.05, h1(3.0)), mix(0.15, 0.75, h1(4.0))));
        lookAt(ro, ro + fw, vec3(0, 1, 0), f, rgt, up);
        roll = (h1(5.0) - 0.5) * 0.24;
    } else if (gCamM == 2) {                                   // outside, orbiting the block
        float k = h1(7.0);
        gBox = k < 0.34 ? vec3(2.0, 6.0, 2.0) : (k < 0.67 ? vec3(6.0, 2.0, 6.0) : vec3(4.0, 4.0, 4.0));
        float ang = gSeed * 6.283 + ev * 0.06 + arr2 * 0.7;
        float dist = mix(2.3, 4.6, h1(3.0)) * max(gBox.x, gBox.y);
        ro = vec3(cos(ang) * dist, -gBox.y + mix(0.5, 1.6, h1(4.0)) * gBox.y + 0.4, sin(ang) * dist);
        lookAt(ro, vec3(0.0, -0.25 * gBox.y, 0.0), vec3(0, 1, 0), f, rgt, up);
        uv += vec2((h1(5.0) - 0.5) * 0.7, (h1(6.0) - 0.5) * 0.2);    // the subject sits off-centre
        tfar = 70.0;
        gSun = normalize(vec3(cos(ang + 2.1), 0.5, sin(ang + 2.1)));
    } else if (gCamM == 3) {                                   // macro: skimming the sliced plate
        float dir = h1(7.0) < 0.5 ? -1.0 : 1.0;
        ro = vec3(h1(1.0) * 40.0 + dir * ev * 0.3, h1(2.0) * 40.0 + 0.05 * sin(uCam.x * 0.2), PLATE + mix(0.42, 0.85, h1(3.0)));
        vec3 fw = normalize(vec3(0.7 * (h1(4.0) - 0.5), 0.4 * (h1(5.0) - 0.5), -1.0));
        lookAt(ro, ro + fw, vec3(0, 1, 0), f, rgt, up);
        roll = (h1(6.0) - 0.5) * 0.6;
        gKickO = ro;
        float th = h1(8.0) * 6.283 + uCam.y * 0.3927;          // the raking light turns once every 16 beats
        gSun = normalize(vec3(cos(th), sin(th), 0.30));
        gRel *= 1.0 - arr2;                                    // the letters rise out of the plate
    } else if (gCamM == 4) {                                   // inside the rotunda
        float ang = gSeed * 6.283 + ev * 0.1 + arr2 * 0.6;
        vec2 cs = vec2(cos(ang), sin(ang));
        if (h1(1.0) < 0.55) {
            ro = vec3(cs.x * ROT_R * 0.68, mix(-0.9, 0.5, h1(2.0)), cs.y * ROT_R * 0.68);
            lookAt(ro, vec3(0.0, 0.1, 0.0), vec3(0, 1, 0), f, rgt, up);
            uv.x += (h1(3.0) < 0.5 ? -1.0 : 1.0) * mix(0.3, 0.62, h1(4.0));    // the orb sits to one side
        } else {                                               // lying on the floor looking straight up
            ro = vec3(cs.x * 0.7, -ROT_R * 0.72, cs.y * 0.7);
            lookAt(ro, vec3(0.0, ROT_R, 0.0), vec3(cs.y, 0.0, -cs.x), f, rgt, up);
            uv.y -= 0.2;
        }
        roll = 0.15 * sin(uCam.x * 0.07);
    } else {                                                   // orthographic, square onto a diagonal cut
        float k = h1(1.0);
        gCN = normalize(k < 0.5 ? vec3(1.0, 1.0, 1.0) : (k < 0.75 ? vec3(1.0, 2.0, 3.0) : vec3(2.0, 1.0, 1.0)));
        gCR = normalize(cross(vec3(0.0, 1.0, 0.0), gCN));
        gCU = cross(gCN, gCR);
        float a = h1(2.0) * 6.283 + uCam.x * 0.02;
        vec3 r2 = gCR * cos(a) + gCU * sin(a); gCU = cross(gCN, r2); gCR = r2;
        gCH = h1(3.0) * 8.0 + ev * 0.1 + 0.22 * uHit.y * uHit.y + arr2 * 0.8;   // each kick pushes the cut deeper
        float zoom = mix(2.0, 5.0, h1(4.0)) * (1.0 - 0.35 * arr2) * (1.0 - 0.04 * uHit.y);
        vec2 pan = vec2(h1(5.0), h1(6.0)) * 12.0 + vec2(ev * 0.12, 0.0);
        vec3 c0 = gCN * gCH + gCR * pan.x + gCU * pan.y;
        gKickO = c0;
        ro = c0 + gCR * uv.x * zoom + gCU * uv.y * zoom + gCN * 0.12;
        rd = -gCN; f = rd; rgt = gCR; up = gCU;
        ortho = true; tfar = 9.0;
    }
    if (!ortho) {
        vec2 suv = rot(roll) * uv;
        rd = normalize(f * focal + rgt * suv.x + up * suv.y);
    }

    bool tubes = gLight <= 1;
    float orbB = (0.55 + 1.0 * uCam.w) * (0.7 + 0.7 * uFold.w) * (1.0 - arr2) + 1.2 * uHit.y * (1.0 - uHit.x);

    // stage 1: march to the shell that encloses the embossed letters
    float glow = 0.0; float tubeAcc = 0.0; bool hit = false;
    float shell = RELIEF * gRel;
    for (int i = 0; i < 64; i++) {
        vec3 p = ro + rd * t;
        float d = base(p) - shell;
        float stp = min(d, 0.2);
        float dzf = frontD(p);
        glow += uHit.y * exp(-dzf * dzf * 30.0) * stp;
        if (tubes) {
            vec2 tb = tube(p);
            tubeAcc += tb.y * 0.0016 / (0.0009 + tb.x * tb.x) * stp;
            if (d < 0.0012 * t) { hit = true; break; }
            d = min(d, abs(tb.x) + 0.012);                    // slow down beside a tube, never stop on it
        } else {
            if (gLight == 3) {
                float od = length(p) - 0.16;
                tubeAcc += orbB * 0.012 / (0.004 + od * od) * stp;
                if (d < 0.0012 * t) { hit = true; break; }
                d = min(d, abs(od) + 0.02);
            } else if (d < 0.0012 * t) { hit = true; break; }
        }
        t += d * 0.85;
        if (t > tfar) break;
    }

    // what is behind everything, and what the fog fades to
    vec3 fogc = mix(vec3(0.004, 0.008, 0.012), CRT * CRT * 0.22, (0.15 + 0.6 * uCam.w) * (0.4 + 0.6 * gPow));
    if (gGrade == 1) fogc = vec3(0.0);
    else if (gGrade == 2) fogc = mix(PAPER * PAPER * 0.95, FLUO * FLUO * 0.8, clamp(uv.y + 0.4, 0.0, 1.0)) * (0.75 + 0.3 * uCam.w);
    else if (gGrade == 3) fogc = INK * INK * 0.5;
    else if (gGrade == 4) fogc = vec3(0.010, 0.006, 0.004);
    else if (gGrade == 5) fogc = vec3(0.035);
    else if (gGrade == 6) fogc = vec3(0.004);
    vec3 col = fogc;
    if (hit) {
        vec3 p = ro + rd * t;
        vec3 nb = baseNormal(p, 0.002 + 0.001 * t);
        vec3 w = pow(abs(nb), vec3(8.0)); w /= (w.x + w.y + w.z);
        float lod = clamp(log2(t * 1.2 * uTakeC.w), 0.0, 6.0);
        if (ortho) lod = clamp(log2(4.0 * uTakeC.w), 0.0, 6.0);
        // stage 2: refine onto the lettering (16 steps; 80 in total)
        for (int i = 0; i < 16; i++) {
            float d = relief(ro + rd * t, nb, w, lod);
            if (d < 0.0006 * t) break;
            t += d * 0.6;
        }
        p = ro + rd * t;
        vec2 tx = txt(p, nb, w, lod);
        float frz = onFrieze(p, w);
        float e = 0.0025 + 0.0012 * t;
        vec2 k = vec2(1.0, -1.0);
        vec3 n = normalize(k.xyy * relief(p + k.xyy * e, nb, w, lod) + k.yyx * relief(p + k.yyx * e, nb, w, lod) +
                           k.yxy * relief(p + k.yxy * e, nb, w, lod) + k.xxx * relief(p + k.xxx * e, nb, w, lod));

        // ambient occlusion from the march (the clay take reaches further)
        float aoR = gLight == 4 ? 2.6 : 1.0;
        float ao = 0.0, sc = 1.0;
        for (int i = 1; i <= 4; i++) {
            float h = (0.03 + 0.09 * float(i)) * aoR;
            ao += (h - base(p + nb * h)) * sc / aoR; sc *= 0.7;
        }
        ao = clamp(1.0 - 1.4 * ao, 0.0, 1.0);

        float face = smoothstep(0.35, 0.75, tx.x);
        float red = clamp(tx.y * 1.6, 0.0, 1.0);
        vec3 steel = mix(PUTTY * PUTTY * 0.62, PUTTY * PUTTY * 0.30 + CRT * 0.04, frz);   // the frieze is darker steel
        vec3 alb = mix(steel, mix(PAPER, RED * RED * 1.6, red), face);
        bool floorHit = gArch == 2 && p.y < -gBox.y + 0.05 + shell;
        if (gGrade == 3) alb = mix(IVORY * IVORY * 0.8, mix(INK * INK * 1.2, vec3(0.74, 0.11, 0.05), red), face);
        bool cutFace = gArch == 5 && abs(dot(p, gCN) - gCH) < 0.012 + shell;
        if (gGrade == 5) alb = cutFace ? mix(vec3(0.80, 0.05, 0.03), vec3(0.9), face) : vec3(0.86);
        if (floorHit) {
            // the floor is a printed sheet: cream paper, ruled, printed in ink
            vec2 g2 = abs(fract(p.xz * 0.5) - 0.5);
            float rule = 1.0 - smoothstep(0.004, 0.012, min(g2.x, g2.y));
            alb = mix(PAPER * PAPER, mix(INK * INK * 2.0, RED * RED * 1.6, red), max(face, 0.55 * rule));
        }

        vec3 light = vec3(0.0); float spec = 0.0;
        // random lattice cells flash on the hats (the takes without tubes)
        vec3 cid = floor(p / (CELL / 3.0) + 0.5);
        float win = step(0.82, hash(dot(cid, vec3(1.0, 7.3, 13.7)) + floor(uCam.y * 2.0))) * min(uHit.w, 1.0);
        if (tubes) {
            // the two nearest battens, each with its own soft shadow
            float z0 = (floor(p.z / TP) + 0.5) * TP;
            float z1 = z0 + (p.z > z0 ? TP : -TP);
            vec4 la = tubeLight(p, n, z0);
            vec4 lb = tubeLight(p, n, z1);
            float key = la.w + lb.w;
            spec = pow(max(dot(reflect(rd, n), la.xyz), 0.0), 32.0) * la.w
                 + pow(max(dot(reflect(rd, n), lb.xyz), 0.0), 32.0) * lb.w;
            light = FLUO * FLUO * 2.4 * key;
            light += CRT * CRT * (0.035 + 0.05 * uCam.w) * ao * ao * (0.6 + 0.4 * n.y);           // cold fill, only in the open
            light += CRT * 0.10 * ao * max(dot(n, -rd), 0.0) / (1.0 + t * t * 0.8);               // faint lamp on the camera
        } else if (gLight == 2) {
            float dif = max(dot(n, gSun), 0.0);
            float sh = dif > 0.001 ? softShadow(p, gSun, gArch == 3 ? 1.2 : 14.0, gArch == 3 ? 5.0 : 10.0, 12) : 0.0;
            float sunB = (0.75 + 0.9 * uCam.w) * (0.8 + 0.35 * uFold.w);
            vec3 sunC = gGrade == 3 ? IVORY * vec3(1.0, 0.93, 0.78) : vec3(1.0, 0.95, 0.84);
            vec3 skyC = gGrade == 3 ? INK * 0.55 + vec3(0.0, 0.01, 0.03) : FLUO * 0.22;
            light = sunC * 1.5 * sunB * dif * sh + skyC * ao * (0.55 + 0.45 * n.y);
            spec = pow(max(dot(reflect(rd, n), gSun), 0.0), 24.0) * sh * 0.5;
            light += FLUO * 2.0 * win * face;
        } else if (gLight == 3) {
            vec3 l = -p; float ld = length(l); l /= ld;
            float dif = max(dot(n, l), 0.0);
            float sh = dif > 0.001 ? softShadow(p, l, ld - 0.2, 8.0, 10) : 0.0;
            float att = 1.0 / (0.25 + ld * ld * 0.42);
            light = AMBER * vec3(1.25, 1.0, 0.7) * 3.2 * orbB * dif * att * sh;
            light += CRT * CRT * 0.03 * ao;
            spec = pow(max(dot(reflect(rd, n), l), 0.0), 24.0) * sh * att * orbB;
            light += AMBER * 3.0 * win * face;
        } else {
            light = vec3(0.05 + 1.05 * pow(ao, 2.6)) * (0.85 + 0.25 * uCam.w + 0.12 * uFold.w);
            if (cutFace) light = vec3(0.8 + 0.3 * uFold.w + 1.2 * min(uHit.z, 1.2));     // the section is flat ink; the snare heats it
            light += vec3(1.2) * win * step(0.5, 1.0 - face);
        }
        col = alb * light + (gGrade == 4 ? AMBER : FLUO) * spec * 1.2;
        if (gLight != 4) col *= mix(0.25, 1.0, ao);
        // red ink smoulders in the dark and flares on the snare
        if (gGrade != 5) col += vec3(0.9, 0.06, 0.04) * red * face * (0.10 + 0.25 * (1.0 - gPow) + 1.5 * min(uHit.z, 1.2));
        // the kick's scan bar: a thin line of light crossing every surface as the pulse passes
        float dzf = frontD(p);
        float bar = uHit.y * exp(-dzf * dzf / (0.006 + 0.0006 * t * t));
        vec3 barC = gGrade == 5 ? vec3(0.9, 0.05, 0.03) : (gGrade == 3 ? vec3(0.86, 0.71, 0.24) : FLUO * vec3(0.75, 1.0, 0.7));
        col += barC * bar * 1.6 * (0.25 + 0.75 * ao) * (0.5 + 0.5 * face + 0.3 * frz);
        float fog = 1.0 - exp(-t * uTakeC.z * (1.0 + 0.3 * uCam.w));
        col = mix(col, fogc, fog);
    }
    vec3 glowC = gGrade == 5 ? vec3(0.0) : (gGrade == 3 ? vec3(0.86, 0.71, 0.24) * 0.5 : FLUO * vec3(0.75, 1.0, 0.7));
    col += glowC * glow * 0.45 * smoothstep(0.04, 0.3, uHit.x);
    col += (gLight == 3 ? AMBER * vec3(1.4, 1.0, 0.55) : FLUO * vec3(0.9, 1.0, 0.82)) * min(tubeAcc, 6.0);
    col *= 1.0 + 1.4 * arr2 * arr2;                            // the cut lands a touch hot

    // grade
    col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
    col = pow(clamp(col, 0.0, 1.0), vec3(0.4545));
    float vig = 1.0 - 0.45 * dot(uv, uv);
    if (gGrade == 0) {
        col = mix(col, col * col * (3.0 - 2.0 * col), 0.55);                 // contrast
        float lum = dot(col, vec3(0.3, 0.6, 0.1));
        col = mix(col + CRT * 0.035 * (1.0 - lum), col * FLUO / 0.86, lum);  // blue in the shadows, green in the lights
        col *= vig;
    } else if (gGrade == 1) {
        // pure black and white, ordered dither on doubled pixels
        float lum = dot(col, vec3(0.3, 0.6, 0.1)) * vig;
        lum = smoothstep(0.16, 0.80, lum); lum *= lum;
        col = vec3(step(bayer4(floor(gl_FragCoord.xy * 0.5)), lum));
        if (uHit.z > 0.45) col = 1.0 - col;                                  // the snare flips it to its negative
    } else if (gGrade == 2) {
        col = mix(col, col * col * (3.0 - 2.0 * col), 0.35);
        float lum = dot(col, vec3(0.3, 0.6, 0.1));
        col = mix(col * vec3(0.92, 1.0, 0.93) + vec3(0.02, 0.035, 0.02), col * PAPER / 0.89, lum);   // sickly green shadows
        col *= mix(1.0, vig, 0.5);
    } else if (gGrade == 3) {
        col = mix(col, col * col * (3.0 - 2.0 * col), 0.6);
        float lum = dot(col, vec3(0.3, 0.6, 0.1));
        col = mix(INK * 0.35 + col * 0.75, col, smoothstep(0.0, 0.5, lum));
        col *= vig;
    } else if (gGrade == 4) {
        col = mix(col, col * col * (3.0 - 2.0 * col), 0.6);
        float lum = dot(col, vec3(0.3, 0.6, 0.1));
        col = mix(col + vec3(0.0, 0.012, 0.03) * (1.0 - lum), col * vec3(1.06, 0.97, 0.84), lum);
        col *= vig;
    } else if (gGrade == 5) {
        col = mix(col, col * col * (3.0 - 2.0 * col), 0.3);
        col *= mix(1.0, vig, 0.35);
    } else {
        // emergency lighting: one red channel of information
        float lum = dot(col, vec3(0.3, 0.6, 0.1));
        lum = lum * lum * (3.0 - 2.0 * lum);
        col = mix(vec3(0.015, 0.0, 0.0), vec3(1.0, 0.07, 0.04), lum) + vec3(0.0, 0.55, 0.38) * smoothstep(0.78, 1.0, lum);
        col *= vig;
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
