// glyph.frag: redraws the luminance plane as running bitmap text, 1-bit.
// input 0: tone.frag (r luminance, g poster letter mask, b model plus keyline, a rim + 2 * tile parity)
// input 1: all glyph atlases stacked (build.py PACK_CB): 16x4 cells each, ASCII 32..95
// input 2: the running texts, one row each, one texel per character, value = ASCII code - 32
//          (row 0 the scene's phrases; the other rows are the Describe texts, build.py CODES_CB)
uniform vec4 uCell;   // x atlas index (cell size), y screen pixels per bitmap pixel, z page reveal 0..1, w reveal style
uniform vec4 uText;   // x scroll in characters (unfloored), y strip length, z phrase start, w glitch 0..1
uniform vec4 uFx;     // x frame invert 0/1, y time (frames), z edge dither width, w poster flash 0/1
uniform vec4 uMode;   // x poster 0 none / 1 grey block / 2 keyhole, y quadtree 0/1, z ticker rows 0/1, w quadtree split threshold
uniform vec4 uRow;    // x which row of input 2 the text is read from (uText.y is that row's length)
out vec4 fragColor;

// cell width, cell height, y origin in the stacked atlas. build.py refuses to
// build if this line differs from its CELLS.
const ivec3 ATL[6] = ivec3[6](ivec3(48, 64, 0), ivec3(36, 48, 256), ivec3(24, 32, 448), ivec3(18, 24, 576), ivec3(15, 20, 672), ivec3(12, 16, 752));

float bayer4(ivec2 p)
{
    const float m[16] = float[16](0., 8., 2., 10., 12., 4., 14., 6.,
                                  3., 11., 1., 9., 15., 7., 13., 5.);
    return (m[(p.x & 3) + ((p.y & 3) << 2)] + 0.5) / 16.0;
}

float hash(vec2 p)
{
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

// luminance of the tone plane at a page position (pixels, top-left origin)
vec4 toneAt(vec2 q, vec2 res)
{
    return textureLod(sTD2DInputs[0], vec2(q.x, res.y - q.y) / res, 0.0);
}

void main()
{
    vec2 res = uTDOutputInfo.res.zw;
    vec2 px = vec2(vUV.s * res.x, (1.0 - vUV.t) * res.y);   // top-left origin, like a page

    // ---- which cell: size, origin, atlas ----
    int ak = clamp(int(uCell.x + 0.5), 0, 5);
    float sc = max(1.0, floor(uCell.y + 0.5));      // screen pixels per bitmap pixel
    float pm = sc;                                  // ...and per picture pixel (fat pixels in the macro take)
    vec2 cs = vec2(ATL[ak].xy) * sc;
    vec2 org;
    if (uMode.y > 0.5) {
        // quadtree: start from 96x128 blocks and split a block in four wherever
        // the picture inside it has contrast, down to 12x16
        pm = 1.0;
        ak = 0; sc = 2.0; cs = vec2(96.0, 128.0);
        org = floor(-0.5 * (ceil(res / cs) * cs - res));
        for (int lev = 0; lev < 3; lev++) {
            vec2 b0 = floor((px - org) / cs) * cs + org;
            float mn = 9.0, mx = -9.0;
            for (int i = 0; i < 16; i++) {
                vec2 o = (vec2(float(i & 3), float(i >> 2)) + 0.5) * 0.25;
                float v = toneAt(b0 + o * cs, res).r;
                mn = min(mn, v);
                mx = max(mx, v);
            }
            if (mx - mn < uMode.w * (1.0 + 0.5 * float(lev))) break;
            cs *= 0.5;
            if (lev == 0) { ak = 0; sc = 1.0; }
            else if (lev == 1) { ak = 2; }
            else { ak = 5; }
        }
    } else {
        // centre the grid so the cropped cells are shared by both edges
        org = floor(-0.5 * (ceil(res / cs) * cs - res) / sc) * sc;
    }
    vec2 g = (px - org) / cs;
    ivec2 cell = ivec2(floor(g));
    vec2 f = fract(g);
    int ncols = int(ceil(res.x / cs.x));
    float nrows = ceil(res.y / cs.y);

    // luminance: one value for the whole cell (4 taps), one for this pixel
    float lc = 0.0;
    for (int i = 0; i < 4; i++) {
        vec2 o = vec2(float(i & 1), float(i >> 1)) * 0.5 + 0.25;
        lc += toneAt((vec2(cell) + o) * cs + org, res).r;
    }
    lc *= 0.25;
    vec2 qp = (floor(px / pm) + 0.5) * pm;
    vec4 here = texelFetch(sTD2DInputs[0], ivec2(clamp(vec2(qp.x, res.y - qp.y), vec2(0.0), res - 1.0)), 0);
    float lp = here.r;
    bool rim = mod(here.a, 2.0) > 0.5;
    bool flip = here.a > 1.5;                       // odd wallpaper tile

    // the page arrives: cells not yet typed show the bare picture (silhouette, no
    // letters). Rows from the top, columns from the left, random cells, or centre out.
    float m;
    int style = int(uCell.w + 0.5);
    if (style == 1) m = (float(cell.x) + 0.8 * hash(vec2(float(cell.y), 3.0))) / float(ncols);
    else if (style == 2) m = hash(vec2(cell) + 11.0);
    else if (style == 3) m = length((vec2(cell) + 0.5) * cs + org - 0.5 * res) / (0.6 * res.x);
    else m = (float(cell.y) + 0.8 * hash(vec2(float(cell.x), 7.0))) / nrows;
    bool typed = uCell.z >= 1.0 || m < uCell.z;

    // the poster word is cut per pixel from the font's outline (NOTES.md log 15);
    // the model and its keyline cut it, or the model's shadow side turns white
    // with the poster (NOTES.md log 09)
    int pmode = int(uMode.x + 0.5);
    bool poster = pmode == 1 && here.g > 0.5 && here.b < 0.5 && typed;

    // which character: the phrases run on, row after row, like a page of type;
    // or every row is its own ticker and alternate rows run opposite ways
    float n = uText.y;
    float idx;
    if (uMode.z > 0.5) {
        float rh = hash(vec2(float(cell.y), 3.0));
        float spd = 1.0 + floor(rh * 3.0);
        float dir = (cell.y & 1) == 0 ? 1.0 : -1.0;
        idx = float(cell.x) + floor(hash(vec2(float(cell.y), 5.0)) * n) + dir * floor(uText.x * spd);
    } else {
        idx = float(cell.y * ncols + cell.x) + floor(uText.x) + uText.z;
    }
    idx = mod(mod(idx, n) + n, n);
    float code = texelFetch(sTD2DInputs[2], ivec2(int(idx), int(uRow.x + 0.5)), 0).r;
    float tick = mod(floor(uFx.y / 3.0), 251.0);   // keep it small: a huge frame number flattens hash() to 0
    if (hash(vec2(cell) + tick * 0.37) < (uText.w - 0.12) * 0.15)
        code = floor(hash(vec2(cell.yx) * 1.7 + tick) * 59.0) + 1.0;   // hat: stray characters

    // pixel-exact fetch: each atlas was rasterised at exactly its cell size, so
    // one atlas texel is one bitmap pixel (crisp), drawn sc pixels wide
    ivec2 ics = ATL[ak].xy;
    ivec2 ip = clamp(ivec2(floor(f * cs / sc)), ivec2(0), ics - 1);
    ivec2 base = ivec2(int(mod(code, 16.0)), 3 - int(floor(code / 16.0))) * ics + ivec2(0, ATL[ak].z);
    ivec2 tp = base + ivec2(ip.x, ics.y - 1 - ip.y);
    int smear = max(1, ics.x / 9);
    float a0 = texelFetch(sTD2DInputs[1], tp, 0).r;
    float a1 = ip.x >= smear ? texelFetch(sTD2DInputs[1], tp - ivec2(smear, 0), 0).r : 0.0;
    const float thr = 0.5;
    bool reg = typed && a0 > thr;
    bool bold = reg || (typed && a1 > thr);                    // classic bitmap bold: smear right
    ivec2 ipx = ivec2(floor(px / pm));
    bool checker = ((ipx.x + ipx.y) & 1) == 0;
    bool grey = reg && checker;                                // classic Mac "greyed out" stipple

    // brightness decides the inking, never the letter
    float d = bayer4(cell);                                    // ordered dither between weights
    bool lit = lp + (bayer4(ipx) - 0.5) * uFx.z > 0.5;         // per-pixel: crisp, dithered edge
    int lvl;
    if (lit) {
        // the lit body is a page of regular black type you can read; only a
        // kick (tone.frag lifts luminance past 1) thins it to greyed, then bare
        float t = max(0.0, (lc - 0.5) / 0.5);
        t += (d - 0.5) * 0.12;                                 // bold black -> regular -> greyed -> bare white
        lvl = 3 - int(step(0.25, t) + step(1.07, t) + step(1.17, t));
        // a lit speck in a dark cell is drawing, not page: leave it solid
        if (lc < 0.42) lvl = 0;
    } else {
        float t = clamp(lc / 0.5, 0.0, 1.0);
        lvl = int(floor(t * 3.0 + 0.5 + (d - 0.5) * 0.4));     // nothing -> greyed -> regular -> bold white
        // a dark line through a lit cell (the cat's smile, a bezel, a dial hole)
        // is drawing: solid black, no letters breaking it up (NOTES.md log 14)
        if (lc > 0.58) lvl = 0;
    }
    lvl = clamp(lvl, 0, 3);
    bool ink = lvl == 3 ? bold : (lvl == 2 ? reg : (lvl == 1 ? grey : false));
    bool white = lit ? !ink : ink;

    // white outline just inside the silhouette wherever the model is dark
    if (!lit && rim) white = true;

    // poster: at rest a block of classic 50% grey carrying bold white type, so it
    // reads as a word from across the room and sits between the black void and
    // the white model; on the kick it snaps to a white block with black type
    if (poster && !lit && !rim)
        white = uFx.w > 0.5 ? !bold : (bold || checker);

    // keyhole: the picture exists only inside the letters of the word; outside
    // is the void, which shows greyed type for the length of a kick or beat, and
    // the model's outline
    if (pmode == 2 && here.g <= 0.5)
        white = rim || (uFx.w > 0.5 && grey);

    if (flip) white = !white;
    if (uFx.x > 0.5) white = !white;
    float v = white ? 1.0 : 0.0;
    fragColor = TDOutputSwizzle(vec4(v, v, v, 1.0));
}
