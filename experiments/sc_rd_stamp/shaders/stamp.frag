// The rubber stamp mask. Three modes (uMode.x), chosen by the take:
//   0 one phrase (input 0, a Text TOP) in a rounded frame, at a per-shot pose
//   1 a sheet of tiles: every cell holds a different phrase from the atlas (input 1,
//     3 x 4 cells), framed (a sheet of approvals) or bare and brick-laid (a field of letters)
//   2 scatter: one small framed phrase that jumps to a new place and angle on every kick
// Output: R = mask, G = text, B = frame, A = which part a kick presses this time.
// With an Input picture (uIn.x = 1, input 2 = its mask from inmask.frag) the picture is
// what gets stamped: the whole page in mode 0 and in the bare tiles, one small copy per
// framed tile in mode 1, one small framed copy per kick in mode 2.
uniform vec4 uPose;   // angle (rad), offset x, offset y, scale
uniform vec4 uBox;    // half width, half height, frame thickness, padding
uniform vec4 uMode;   // mode, tile columns, tile rows, frame on
uniform vec4 uShot;   // seed, hits_low, share of tiles a kick presses, tile angle jitter
uniform vec4 uIn;     // x = 1 when an Input picture replaces the words, y = 1 in Describe mode
out vec4 fragColor;

const float ASPECT = 16.0 / 9.0;
const vec2 ATLAS = vec2(3.0, 4.0);
const float CELL_ASPECT = 426.0 / 240.0;

float sdRound(vec2 p, vec2 b, float r) {
    vec2 d = abs(p) - b + r;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - r;
}
float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, s, -s, c); }

void main() {
    vec2 p = (vUV.st - 0.5) * vec2(ASPECT, 1.0);
    int mode = int(uMode.x + 0.5);
    float txt = 0.0, frame = 0.0, gate = 1.0;
    float aa = 0.003;
    bool pic = uIn.x > 0.5;

    if (mode == 1) {
        vec2 grid = uMode.yz;
        vec2 g = vUV.st * grid;
        if (uMode.w < 0.5) g.x += 0.5 * mod(floor(g.y), 2.0);      // bare tiles are brick-laid
        vec2 id = floor(g);
        vec2 cs = vec2(ASPECT / grid.x, 1.0 / grid.y);
        vec2 lp = (fract(g) - 0.5) * cs;
        lp = rot((hash21(id + uShot.x * 17.0) - 0.5) * uShot.w) * lp;
        float hw = min(cs.x * 0.43, cs.y * 0.43 * CELL_ASPECT);
        vec2 box = vec2(hw, hw / CELL_ASPECT);
        float pad = uMode.w > 0.5 ? hw * 0.12 : 0.0;
        vec2 tuv = lp / (2.0 * (box - pad)) + 0.5;
        float n = mod(id.x * 5.0 + id.y * 7.0 + floor(uShot.x * 97.0), 12.0);   // neighbours never share a word
        // Describe mode: no word twice on a sheet of six, so every label gets read
        if (uIn.y > 0.5) n = mod(id.x + id.y * 3.0 + floor(uShot.x * 97.0), 12.0);
        vec2 cell = vec2(mod(n, ATLAS.x), floor(n / ATLAS.x));
        if (pic) {
            if (uMode.w < 0.5) txt = texture(sTD2DInputs[2], vUV.st).r;
            else if (tuv.x > 0.0 && tuv.x < 1.0 && tuv.y > 0.0 && tuv.y < 1.0)
                txt = texture(sTD2DInputs[2], tuv).r;
        } else
        if (tuv.x > 0.0 && tuv.x < 1.0 && tuv.y > 0.0 && tuv.y < 1.0)
            txt = textureLod(sTD2DInputs[1], (cell + tuv) / ATLAS, 0.0).r;
        if (uMode.w > 0.5) {
            float th = hw * 0.06;
            float d = sdRound(lp, box, hw * 0.10);
            frame = smoothstep(aa, 0.0, abs(d + th * 0.5) - th * 0.5);
        }
        gate = step(hash21(id + mod(uShot.y, 97.0) * 0.37), uShot.z);
    } else {
        vec4 pose = uPose;
        if (mode == 2) {
            // a new place on every kick
            vec2 k = vec2(mod(uShot.y, 97.0), uShot.x * 53.0);
            pose.x = (hash21(k) - 0.5) * 1.1;
            pose.y = (hash21(k + 3.7) - 0.5) * 1.25;
            pose.z = (hash21(k + 9.1) - 0.5) * 0.62;
        }
        p -= pose.yz;
        p = rot(pose.x) * p / pose.w;
        vec2 box = uBox.xy;
        if (pic && mode == 2) box = vec2(0.50, 0.50 / ASPECT + uBox.w);   // a 16:9 window
        vec2 inner = box - vec2(uBox.w);
        vec2 tuv = p / (2.0 * inner) + 0.5;
        if (pic && mode == 0)
            txt = texture(sTD2DInputs[2], vUV.st).r;        // the whole page
        else if (tuv.x > 0.0 && tuv.x < 1.0 && tuv.y > 0.0 && tuv.y < 1.0)
            txt = pic ? texture(sTD2DInputs[2], tuv).r : texture(sTD2DInputs[0], tuv).r;
        float d = sdRound(p, box, 0.035);
        frame = uMode.w * smoothstep(aa, 0.0, abs(d + uBox.z * 0.5) - uBox.z * 0.5);
        if (pic && mode == 0) frame = 0.0;
    }

    float m = max(txt, frame);
    fragColor = TDOutputSwizzle(vec4(m, txt, frame, gate));
}
