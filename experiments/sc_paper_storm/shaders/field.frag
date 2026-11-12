// Instance field for the paper storm. One pixel = one instance.
// uOut picks what this TOP carries: 0 position (a = texture index), 1 facing vector,
// 2 up vector, 3 colour multiplier.
// Input 0 is the control texture (one row per channel of the 'ctl' CHOP, order = CTL in build.py).
// Input 1 is the board's page atlas (96 x 48 per page, pages stacked); the everyday or the Describe pages.
// Input 2 is the scene's Input picture at 96 x 54 (only read while control row 23 is 1).
// The take picks ONE formation (row 5); nothing here follows the section any more.
uniform float uOut;
uniform float uProp;   // 0 sheets, 1 solid props
uniform float uSeed;   // per field: 1 sheets, 10 to 13 the four props in the order of PROPS in build.py
uniform float uPages;  // number of pages in the board atlas
out vec4 fragColor;

#define TAU 6.2831853
#define PI 3.14159265

float C(int i) { return texelFetch(sTD2DInputs[0], ivec2(0, i), 0).r; }

vec4 hash4(float n) {
    vec4 p = fract(vec4(n + uSeed * 17.31) * vec4(.1031, .1030, .0973, .1099));
    p += dot(p, p.wzxy + 33.33);
    return fract((p.xxyz + p.yzzw) * p.zywx);
}

vec3 rotAx(vec3 v, vec3 k, float a) {
    return v * cos(a) + cross(k, v) * sin(a) + k * dot(k, v) * (1.0 - cos(a));
}

struct Fr { vec3 p; vec3 n; vec3 u; };

float gB, gBeat, gKick, gE, gArr, gSeed, gBass, gHat, gEnergy;
float s1, s2, s3;      // three numbers from the shot seed
float gExtra;          // per-formation extra turn of the sheet about its up axis (board, floor arrival)
float gS;              // 0..1 through a formation's own flip, for the flash
float gFlat;           // 1 = turn about the sheet's horizontal axis instead (split-flap)
vec2 gRes;
float gIn;             // 1 while an Input picture is in use (control row 23)
vec3 gInCol;           // the Input's colour for this sheet (board), -1 = none

// 0: tunnel the camera flies down
Fr tunnel(float id, vec2 cell, vec4 h) {
    Fr f;
    float L = 80.0;
    float z = mod(h.y * L + gE * 5.0 + s1 * L, L) - L + 17.0;
    float lay = h.z;
    float r = uProp > 0.5 ? mix(1.7, 3.1, lay) : mix(3.3, 8.5, pow(lay, 1.4));
    float dir = s2 < 0.5 ? 1.0 : -1.0;
    float a = h.x * TAU + dir * gB * (TAU / 8.0) * (1.6 - lay) + z * 0.07 + gArr * 1.6;
    r += gKick * (0.3 + 1.5 * h.w);
    r += gArr * 7.0 * (0.4 + h.w);          // arrival: the tunnel closes in round the lens
    vec3 rad = vec3(cos(a), sin(a), 0.0);
    f.p = rad * r + vec3(0.0, 0.0, z);
    f.n = normalize(-rad * 0.6 + vec3(0.0, 0.0, 0.8));
    f.u = vec3(-rad.y, rad.x, 0.0);
    return f;
}

// 1: dome of paper, seen from inside looking up (the oculus)
Fr dome(float id, vec2 cell, vec4 h) {
    Fr f;
    float NB = 7.0 + floor(s1 * 5.0);
    float band = floor(h.x * NB);
    float dir = mod(band, 2.0) < 0.5 ? 1.0 : -1.0;
    float y = (band + 0.5 + (h.y - 0.5) * 0.42) / NB * 2.0 - 1.0;
    if (uProp > 0.5) {
        float pa = h.x * TAU + gB * (TAU / 8.0) * (0.6 + 0.8 * h.z);
        float pr = 3.6 + 3.4 * h.z + gKick * (0.4 + 1.6 * h.w);
        vec3 pp = rotAx(vec3(pr * cos(pa), (h.w - 0.5) * 0.9, pr * sin(pa)), vec3(1.0, 0.0, 0.0), 0.5);
        f.p = rotAx(pp, vec3(0.0, 0.0, 1.0), 0.22);
        f.n = vec3(0.0, 0.0, 1.0); f.u = vec3(0.0, 1.0, 0.0);
        return f;
    }
    float rr = sqrt(max(0.0, 1.0 - y * y));
    float a = fract(h.z * 31.7 + h.w * 5.3) * TAU + (gB * (TAU / 8.0) + gArr * 2.2) * dir * (1.0 + mod(band, 3.0) * 0.5);
    vec3 d = vec3(rr * cos(a), y, rr * sin(a));
    float R = 10.0 + 1.2 * h.z * h.z;
    R += gKick * (0.4 + 2.2 * h.w);
    R *= 1.0 + gArr * 0.9;                  // arrival: the dome falls shut
    f.p = d * R;
    f.n = -d;
    f.u = normalize(cross(d, vec3(0.0, 1.0, 0.0)) + vec3(1e-4, 0.0, 0.0));
    return f;
}

// 2: a tidy floor of sheets seen from straight above; rings of height travel out on the beat
Fr floorf(float id, vec2 cell, vec4 h) {
    Fr f;
    vec2 pitch = vec2(1.08, 0.86);
    vec2 size = gRes * pitch;
    vec2 g = (cell + 0.5) * pitch;
    g = mod(g + vec2(gE * 0.7, gE * 0.25) , size) - size * 0.5;     // the floor slides under the camera
    vec2 o = (vec2(s2, s3) - 0.5) * 9.0;                            // where the ripples start
    float r = length(g - o);
    float amp = (0.22 + 0.5 * gBass * 0.5 + 0.55 * gKick) * exp(-r * 0.045);
    float ph = r * 0.75 - gBeat * TAU;
    float y = amp * sin(ph);
    float dy = amp * 0.75 * cos(ph);                               // slope along the radius
    vec2 rd = (g - o) / max(r, 1e-3);
    vec3 n = normalize(vec3(-dy * rd.x, 1.0, -dy * rd.y));
    vec3 u = normalize(vec3(0.0, 0.0, -1.0) + n * n.z);
    // arrival: every sheet starts face down and they turn over from the middle outward
    float tl = clamp(gArr * 3.0 - (1.0 - r / 20.0) * 2.0, 0.0, 1.0);
    // the beat's flip is a narrow ring on the floor, leaving the ripple origin every two beats
    gS = smoothstep(0.0, 0.26, fract(gBeat * 0.5 - r / 15.0));
    gExtra = PI * smoothstep(0.0, 1.0, tl) + TAU * gS;
    float yaw = s1 * TAU;
    vec3 p = vec3(g.x, y + gKick * 0.5 * h.w, g.y);
    vec3 ax = vec3(0.0, 1.0, 0.0);
    f.p = rotAx(p, ax, yaw);
    f.n = rotAx(n, ax, yaw);
    f.u = rotAx(u, ax, yaw);
    return f;
}

// 3: spiral galaxy with the monolith as its core
Fr galaxy(float id, vec2 cell, vec4 h) {
    Fr f;
    float arm = floor(h.x * 3.0);
    float rr = uProp > 0.5 ? 1.8 + 4.5 * h.y : 2.2 + 17.0 * pow(h.y, 0.75);
    float a = arm * TAU / 3.0 + log(rr) * 2.6 + (h.z - 0.5) * (h.z - 0.5) * 3.0 * sign(h.z - 0.5) + gB * (TAU / 16.0) + s1 * TAU + gArr * 1.3;
    rr += gKick * (0.3 + 1.6 * h.w);
    rr *= 1.0 + gArr * 0.7;
    float y = (h.w - 0.5) * 2.2 * exp(-rr * 0.12);
    vec3 p = vec3(rr * cos(a), y, rr * sin(a));
    float tilt = 0.42;
    p = rotAx(p, vec3(1.0, 0.0, 0.0), tilt);
    f.p = p;
    vec3 ax = normalize(h.xyz - 0.5);
    float sp = gE * 0.9 + h.w * TAU;
    f.n = rotAx(normalize(vec3(0.0, 1.0, 0.35)), ax, sp);
    f.u = rotAx(vec3(1.0, 0.0, 0.0), ax, sp);
    return f;
}

// 4: rain. The camera stands still; sheets fall past it like leaves, one step per beat
Fr rain(float id, vec2 cell, vec4 h) {
    Fr f;
    float L = 40.0;
    float dir = s2 < 0.22 ? -1.0 : 1.0;                 // now and then the rain falls up
    float fall = gE * 7.0 * (0.5 + h.w) + (floor(gBeat) + smoothstep(0.0, 0.3, fract(gBeat))) * 0.9;
    float y = mod(h.y * L - dir * (fall + gArr * gArr * 16.0), L) - L * 0.5;
    y += gKick * 1.4 * h.w * dir;                       // a kick holds the rain up for an instant
    float x = (h.x - 0.5) * 84.0;
    float z = mix(9.6, -70.0, pow(h.z, 1.15));
    float rock = gE * 3.0 * (0.6 + h.z) + h.x * 40.0;
    float ang = 0.35 + sin(rock) * 1.05;
    float ya = h.w * TAU + gE * 0.4;
    vec3 ax = vec3(cos(ya), 0.0, sin(ya));
    x += sin(rock) * 0.7 * cos(ya + 1.57) + y * (s1 - 0.5) * 0.9;   // falling-leaf slide, and the wind
    z += sin(rock) * 0.7 * sin(ya + 1.57);
    f.p = vec3(x, y, z);
    f.n = rotAx(vec3(0.0, 1.0, 0.0), ax, ang);
    f.u = rotAx(vec3(-ax.z, 0.0, ax.x), ax, ang);
    return f;
}

// 5: murmuration. A folded cloud of sheets that turns together
Fr flock(float id, vec2 cell, vec4 h) {
    Fr f;
    float t = gE * 1.3 + s1 * 40.0;
    vec3 b = normalize(h.xyz - 0.5 + 1e-3) * pow(h.w, 0.45);
    vec3 p = b * vec3(17.0, 6.0, 9.0);
    float A = 1.0 + 0.5 * min(gBass, 1.5);
    p += A * 5.0 * sin(p.yzx * 0.11 + t * 0.9 + s2 * 6.0);
    p += A * 3.4 * sin(p.zxy * 0.19 - t * 1.3);
    p += A * 2.0 * sin(p.yzx * 0.33 + t * 1.7);
    p *= (1.0 - 0.8 * gArr) * (1.0 + 0.16 * gKick);   // arrival: bursts out of a knot
    vec3 c = vec3(sin(t * 0.31) * 9.0, 17.0 + sin(t * 0.23) * 3.0, cos(t * 0.27) * 6.0);
    f.p = p + c;
    // one field turns them all: where it points at the camera the flock goes dark, elsewhere thin
    vec3 n = sin(p * 0.14 + t * vec3(0.7, 0.9, 0.6) + gBeat * TAU * 0.25) + (h.xyz - 0.5) * (0.35 + 1.5 * gHat);
    f.n = normalize(n + 1e-3);
    f.u = normalize(cross(f.n, vec3(0.31, 0.9, 0.2)) + 1e-3);
    return f;
}

// 6: the ritual. No paper: rings of the four props round the idol
Fr ringf(float id, vec2 cell, vec4 h) {
    Fr f;
    float N = gRes.x * gRes.y;
    float kind = uSeed - 10.0;
    float dir = s1 < 0.5 ? 1.0 : -1.0;
    float turn = dir * gB * (TAU / 16.0) + gArr * 2.4;
    float a, R, y = 0.0;
    vec3 n, u = vec3(0.0, 1.0, 0.0);
    if (kind < 0.5) {            // prop 0: two rings, hopping in a wave that runs round once a beat
        float ringi = mod(id, 2.0);
        float k = floor(id * 0.5), M = N * 0.5;
        a = k / M * TAU + ringi * PI / M - turn * (ringi < 0.5 ? 1.0 : -1.0);
        R = 4.3 + ringi * 1.0;
        float ph = fract(gBeat * (ringi < 0.5 ? 1.0 : 0.5) - k / M * 4.0);
        y = 0.75 * pow(sin(ph * PI), 2.0) * (0.5 + gEnergy) + gKick * 0.35;
        R -= gKick * 0.45 * (ringi < 0.5 ? 1.0 : -1.0);   // the two rings part on the kick
        n = vec3(cos(a), 0.0, sin(a));
    } else if (kind < 1.5) {     // prop 1: a ring of dominoes that tips and stands again
        a = id / N * TAU + turn * 0.5;
        R = 7.0;
        float ph = fract(gBeat * 0.5 - id / N * 3.0);
        float tip = sin(ph * PI); tip = tip * tip * tip * 1.15;
        vec3 rad = vec3(cos(a), 0.0, sin(a));
        vec3 tang = vec3(-rad.z, 0.0, rad.x);
        // stand on edge with the thin side along the ring, tip about the radius
        n = rotAx(vec3(0.0, 1.0, 0.0), rad, tip * dir);
        u = rotAx(tang, rad, tip * dir);
        y = 0.16 + gKick * 0.7 * (0.3 + h.w);      // every kick throws the dominoes off the floor
        f.p = rad * ((R + gKick * 0.5) * (1.0 + gArr * 1.6)) + vec3(0.0, y, 0.0);
        f.n = n; f.u = u;
        return f;
    } else if (kind < 2.5) {     // prop 2: close to the idol, jabbing at it on the kick
        a = id / N * TAU - turn * 2.0;
        R = 2.5 - gKick * 0.35;
        y = 0.25 + 0.2 * sin(gBeat * TAU + id);
        n = -vec3(cos(a), -0.25 - gKick * 0.5, sin(a));
    } else {                     // prop 3: slow outer guard between the rings
        a = (id + 0.5) / N * TAU + turn * 1.5;
        R = 3.45;
        y = 0.1 + 0.25 * gKick;
        n = vec3(cos(a + 1.2), 0.0, sin(a + 1.2));
    }
    R *= 1.0 + gArr * 1.6;                  // arrival: the rings snap shut
    f.p = vec3(cos(a) * R, y, sin(a) * R);
    f.n = normalize(n);
    f.u = u;
    return f;
}

// 7: the board. 96 x 64 sheets square-on; the ones turned over spell a page of text,
// and a new page flaps in from the left every two beats.
float pageBit(float page, vec2 rc) {
    if (rc.y < 8.0 || rc.y >= 56.0) return 0.0;
    float pg = mod(page, uPages);
    return step(0.5, texelFetch(sTD2DInputs[1], ivec2(int(rc.x), int(pg * 48.0 + rc.y - 8.0)), 0).r);
}
Fr board(float id, vec2 cell, vec4 h) {
    Fr f;
    vec2 rc = vec2(cell.y, cell.x);          // the field is 64 wide x 96 tall; the board is 96 x 64
    float pitch = 1.06;
    f.p = vec3((rc.x - 47.5) * pitch, (rc.y - 31.5) * pitch, gKick * 2.0 * h.w * h.w);
    f.n = vec3(0.0, 0.0, 1.0);
    f.u = vec3(0.0, 1.0, 0.0);
    float pg = floor(gBeat * 0.5) + floor(gSeed * 97.0);
    float q = fract(gBeat * 0.5) * 2.0;      // beats since this page began
    float tl = clamp((q - rc.x / 96.0 * 0.8 - h.x * 0.12) / 0.3, 0.0, 1.0);
    float st = mix(pageBit(pg - 1.0, rc), pageBit(pg, rc), smoothstep(0.0, 1.0, tl));
    if (gIn > 0.5) {
        // Input: the board shows the picture instead of a page. 96 x 54 sheets carry it (16:9,
        // five blank rows above and below); a sheet turns towards its yellow reverse as its
        // pixel gets brighter, against a 4 x 4 ordered-dither threshold, and takes the pixel's colour.
        st = 0.0;
        if (rc.y >= 5.0 && rc.y < 59.0) {
            vec3 c = texelFetch(sTD2DInputs[2], ivec2(int(rc.x), int(rc.y) - 5), 0).rgb;
            float lum = dot(clamp(c, 0.0, 1.0), vec3(0.3, 0.59, 0.11));
            int bi = int(mod(rc.x, 4.0)) + int(mod(rc.y, 4.0)) * 4;
            int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
            float th = 0.20 + 0.72 * (float(m[bi]) + 0.5) / 16.0;   // only near-white turns every sheet
            st = smoothstep(-0.07, 0.07, lum - th);
            gInCol = c;
        }
    }
    // hats make loose flaps chatter
    st += gHat * 0.25 * step(0.93, fract(h.z * 91.0 + floor(gBeat * 4.0) * 0.37));
    // arrival: the whole board shows its reverse, then clears from the right
    float al = clamp(gArr * 2.4 - (1.0 - rc.x / 96.0), 0.0, 1.0);
    st = mix(st, 1.0, smoothstep(0.0, 1.0, al));
    gExtra = PI * st;
    gFlat = 1.0;
    return f;
}

Fr form(float k, float id, vec2 cell, vec4 h) {
    if (k < 0.5) return tunnel(id, cell, h);
    if (k < 1.5) return dome(id, cell, h);
    if (k < 2.5) return floorf(id, cell, h);
    if (k < 3.5) return galaxy(id, cell, h);
    if (k < 4.5) return rain(id, cell, h);
    if (k < 5.5) return flock(id, cell, h);
    if (k < 6.5) return ringf(id, cell, h);
    return board(id, cell, h);
}

void main() {
    gRes = uTDOutputInfo.res.zw;
    vec2 cell = floor(vUV.st * gRes);
    float id = cell.x + cell.y * gRes.x;
    vec4 h = hash4(id + 1.0);

    gB = C(0); gBeat = C(1); gKick = C(2); gE = C(3); gEnergy = C(4);
    float mode = C(5);
    gSeed = C(6); gArr = C(7);
    gHat = min(C(16), 1.5); gBass = C(17);
    float flipAmt = C(18), ringScale = C(19);
    vec3 cam = vec3(C(12), C(13), C(14));
    s1 = fract(gSeed * 7.13 + 0.11); s2 = fract(gSeed * 13.7 + 0.37); s3 = fract(gSeed * 29.3 + 0.71);
    gExtra = 0.0; gFlat = 0.0; gS = 0.0;
    gIn = C(23); gInCol = vec3(-1.0);

    Fr f = form(mode, id, cell, h);
    f.n = normalize(f.n + 1e-5);
    f.u = normalize(f.u + 1e-5);

    // kick shockwave: a ring leaves the middle at every kick and throws what it passes
    // outward and off its surface. env runs 1 -> 0 over 0.85 s after the hit.
    float env = C(11);
    float dm = length(f.p);
    float ringR = ((1.0 - env) * 30.0 + 1.5) * ringScale;
    float band = ringScale < 0.01 ? 0.0 : exp(-pow((dm - ringR) / (2.4 * ringScale), 2.0)) * smoothstep(0.0, 0.25, env);
    f.p += (normalize(f.p + 1e-4) * 1.3 + f.n * 1.1) * band;
    // nothing comes closer to the lens than the take's keep-out: a sheet on the lens is one polygon over a third of the frame
    vec3 fromCam = f.p - cam;
    f.p += normalize(fromCam + 1e-4) * max(0.0, C(15) - length(fromCam));

    float s = 0.0;
    if (uProp > 0.5) {
        if (mode < 5.5) {
            // props tumble continuously (not in the ritual, where they stand in their rings)
            vec3 ax = normalize(hash4(id + 77.0).xyz - 0.5);
            float sp = gE * (0.6 + h.x) + gBeat * 0.25 + h.y * TAU;
            f.n = rotAx(f.n, ax, sp);
            f.u = rotAx(f.u, ax, sp);
        }
    } else {
        // travelling flip: a ring of turning sheets leaves the camera once per beat
        float d = length(f.p - cam);
        float ph = fract(gBeat - d / 16.0);
        s = smoothstep(0.0, 0.55, ph) * flipAmt;
        float turn = TAU * s + gExtra;
        s = max(s, gS);   // a whole turn, so the printed side comes back
        if (gFlat > 0.5) {
            vec3 side = cross(f.u, f.n);
            f.n = rotAx(f.n, side, turn);
            f.u = rotAx(f.u, side, turn);
        } else {
            f.n = rotAx(f.n, f.u, turn);
        }
        // the shockwave tips sheets back as it lifts them
        f.n = rotAx(f.n, f.u, band * 0.9 * (h.y - 0.3));
    }

    vec4 o;
    if (uOut < 0.5)      o = vec4(f.p, floor(fract(h.x * 7.13 + h.w * 3.71) * 2.9999));
    else if (uOut < 1.5) o = vec4(f.n, 1.0);
    else if (uOut < 2.5) o = vec4(f.u, 1.0);
    else {
        float flash = sin(s * PI);
        vec3 tint = mix(vec3(0.93, 0.92, 0.88), vec3(1.0), h.x) * vec3(C(20), C(21), C(22));
        if (gInCol.x >= 0.0) tint *= 0.22 + 1.5 * clamp(gInCol, 0.0, 1.0);   // board: the sheet takes its pixel's colour
        o = vec4(tint * (1.0 + flash * (0.25 + 0.6 * gEnergy)) * (1.0 + band * vec3(1.0, 0.55, 0.12)), 1.0);   // the shockwave passes as amber heat
    }
    fragColor = TDOutputSwizzle(o);
}
