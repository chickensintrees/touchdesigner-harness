// id_title_card: composes a title card from its runs.
// Inputs 0..7: one run each (a line of lettering drawn full frame, shape in alpha).
// The layout (typeset.py) says where each run's ink is and what it is; this file
// only decides when it is on screen and in which of the take's three colours.
// Nothing fades or drifts except on the credit take: runs arrive by masks, wipes
// and cuts timed in beats.
uniform vec4 uCard;   // x take style 0..4, y beats into the cycle, z beats in a cycle (0 = hold still), w beat position
uniform vec4 uGrid;   // x margin in px
uniform vec4 uCol0;   // ground
uniform vec4 uCol1;   // type
uniform vec4 uCol2;   // accent
// the box each run's ink fills, in px from the top left: x0, y0, x1, y1
uniform vec4 uRect0, uRect1, uRect2, uRect3, uRect4, uRect5, uRect6, uRect7;
// x kind (0 none, 1 type, 2 bar, 3 tiled rows), y colour 0..2, z the beat it arrives on, w line of the title (-1 = small line)
// for tiled rows z is the height of a row and w the distance from one repeat to the next
uniform vec4 uRole0, uRole1, uRole2, uRole3, uRole4, uRole5, uRole6, uRole7;
out vec4 fragColor;

const int POSTER = 0, BLEED = 1, CREDIT = 2, SYSTEM = 3, ROWS = 4;

float sat(float x) { return clamp(x, 0.0, 1.0); }
float easeOut(float x) { x = sat(x); return 1.0 - pow(1.0 - x, 3.0); }
float easeIn(float x) { x = sat(x); return x * x * x; }
float easeBoth(float x) { x = sat(x); return x * x * (3.0 - 2.0 * x); }

float tex(int i, vec2 uv) {
    if (i == 0) return texture(sTD2DInputs[0], uv).a;
    if (i == 1) return texture(sTD2DInputs[1], uv).a;
    if (i == 2) return texture(sTD2DInputs[2], uv).a;
    if (i == 3) return texture(sTD2DInputs[3], uv).a;
    if (i == 4) return texture(sTD2DInputs[4], uv).a;
    if (i == 5) return texture(sTD2DInputs[5], uv).a;
    if (i == 6) return texture(sTD2DInputs[6], uv).a;
    return texture(sTD2DInputs[7], uv).a;
}

// the ink of run i at p (px from the top left)
float ink(int i, vec2 p, vec2 res) {
    if (p.x < 0.0 || p.y < 0.0 || p.x > res.x || p.y > res.y) return 0.0;
    return tex(i, vec2(p.x / res.x, 1.0 - p.y / res.y));
}

float inside(vec2 p, vec4 r) { return step(r.x, p.x) * step(p.x, r.z) * step(r.y, p.y) * step(p.y, r.w); }

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 p = vec2(vUV.s * res.x, (1.0 - vUV.t) * res.y);
    vec4 rect[8] = vec4[8](uRect0, uRect1, uRect2, uRect3, uRect4, uRect5, uRect6, uRect7);
    vec4 role[8] = vec4[8](uRole0, uRole1, uRole2, uRole3, uRole4, uRole5, uRole6, uRole7);
    vec3 col[3] = vec3[3](uCol0.rgb, uCol1.rgb, uCol2.rgb);
    int style = int(uCard.x + 0.5);
    float cb = uCard.y, total = uCard.z, beat = uCard.w;
    bool hold = total < 0.5;
    float leave = hold ? 1e6 : total - 1.0;      // the beat on which a card starts to clear
    float M = uGrid.x;

    float nlines = 0.0;
    for (int i = 0; i < 8; i++) if (role[i].x > 0.5 && role[i].x < 1.5 && role[i].w > -0.5) nlines = max(nlines, role[i].w + 1.0);

    // poster: ground and type change places on every other bar
    if (style == POSTER && !hold && mod(floor(cb / 4.0), 2.0) > 0.5) { vec3 t = col[0]; col[0] = col[1]; col[1] = t; }
    // system: from the second bar on, one line of the title is selected: reversed out of a bar across the grid
    float selected = (style == SYSTEM && !hold && cb >= 4.0 && cb < leave + 0.5) ? mod(floor(cb / 4.0) - 1.0, max(nlines, 1.0)) : -1.0;

    vec3 c = col[0];
    for (int i = 0; i < 8; i++) {
        vec4 r = rect[i];
        int kind = int(role[i].x + 0.5);
        if (kind == 0) continue;
        int ci = int(role[i].y + 0.5);
        float order = role[i].z, line = role[i].w;
        float a = 0.0;
        vec3 paint = col[ci];

        if (kind == 3) {                          // tiled rows
            float pitch = max(order, 1.0), period = max(line, 1.0);
            float count = floor(res.y / pitch + 0.5);
            float row = min(floor(p.y / pitch), count - 1.0);
            float dir = mod(row, 2.0) < 0.5 ? 1.0 : -1.0;
            float travel = 0.25 * period * (floor(beat) + easeOut(fract(beat) / 0.5));
            float x = mod(p.x - dir * travel - row * 0.18 * period, period);   // each row starts a step further along: a diagonal
            a = ink(i, vec2(x, p.y - row * pitch), res);
            if (!hold && row == mod(floor(beat), count)) paint = col[2];
        } else if (kind == 2) {                   // bar
            vec4 b = r;
            if (style == POSTER) {
                b.z = r.x + (r.z - r.x) * easeOut(cb / 1.0);
                b.x = r.x + (r.z - r.x) * easeIn((cb - leave) / 0.75);
            } else if (style == CREDIT) {
                float mid = 0.5 * (r.x + r.z), reach = 0.5 * (r.z - r.x) * easeBoth(cb / 2.0) * (1.0 - easeBoth((cb - leave) / 1.0));
                b.x = mid - reach; b.z = mid + reach;
            }
            a = inside(p, b);
        } else {                                  // type
            a = ink(i, p, res);
            if (style == POSTER) {
                if (line > -0.5) {
                    // each line of the title rises into place from behind its own baseline, a beat apart,
                    // and is wiped off from the left when the card clears
                    float h = r.w - r.y + 4.0;
                    float d = (1.0 - easeOut((cb - order) / 0.6)) * h;
                    float q = easeIn((cb - leave - 0.25 * line) / 0.5);
                    vec4 m = vec4(r.x - 40.0 + q * (r.z - r.x + 80.0), r.y - 2.0, r.z + 40.0, r.w + 1.0);
                    a = ink(i, p - vec2(0.0, d), res) * inside(p, m);
                } else {
                    a *= step(order, cb) * step(cb, leave + 0.5);
                }
            } else if (style == CREDIT) {
                a *= sat(cb - order) * (1.0 - sat(cb - leave));
            } else if (style == SYSTEM) {
                if (line > -0.5 && abs(line - selected) < 0.5) {
                    float pad = 0.16 * (r.w - r.y);
                    vec4 band = vec4(M, r.y - pad, res.x - M, r.w + pad);
                    c = mix(c, col[1], inside(p, band));
                    paint = col[0];
                }
            }
        }
        c = mix(c, paint, sat(a));
    }
    fragColor = vec4(c, 1.0);
}
