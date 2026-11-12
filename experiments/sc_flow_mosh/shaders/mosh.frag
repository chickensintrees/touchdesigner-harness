// Datamosh step. The previous output is pushed along the source's motion; the
// I-frame picture is let through only on I-frames.
// Inputs: 0 previous output (feedback), 1 motion source, 2 flow (xy, in UV units per frame),
//         3 the motion source's previous frame, 4 the I-frame picture (the motion source
//         itself in most takes; a different picture in the transplant take).
uniform vec4 uA;   // x flow gain, y macroblock size in px (1 = per pixel), z I-frame strength 0..1, w 1 = full I-frame
uniform vec4 uB;   // x unused, y streak amount 0..2 (above 1 = sort-dominant), z frame counter, w ambient drift gain
uniform vec4 uC;   // x evolve, y hit seed, z heal rate, w residual gain (section bloom, transplant stamp)
uniform vec4 uD;   // x reveal pattern (0 clusters, 1 rising columns, 2 scan from the top), y share of streak columns that rise
out vec4 fragColor;

float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float lum(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

vec2 RES;

vec2 flowAt(vec2 uv)
{
    vec2 b = max(uA.y, 1.0) / RES;
    vec2 q = (floor(uv / b) + 0.5) * b;
    vec2 f = texture(sTD2DInputs[2], q).xy;
    // a slow swirl so flat fields creep too; also block-quantised
    vec2 c = (q - 0.5) * vec2(16.0 / 9.0, 1.0);
    float a = uC.x * 0.23;
    vec2 sw = vec2(sin(c.y * 5.0 + a) + 0.6 * sin(c.x * 3.1 - a * 1.3),
                   sin(c.x * 4.3 - a * 0.8) + 0.6 * sin(c.y * 2.7 + a * 1.1));
    f = f * uA.x + sw * uB.w;
    // whole-pixel motion per block, like a codec's motion vectors: the block is copied
    // rigidly, so nothing is resampled into mush. The fraction is kept by random rounding.
    vec2 fp = f * RES;
    vec2 blk = floor(uv / b);
    fp = floor(fp + vec2(hash2(blk + uB.z * 0.37), hash2(blk.yx + 7.3 + uB.z * 0.51)));
    return fp / RES;
}

vec3 adv(vec2 uv)
{
    vec2 lo = 0.5 / RES, hi = 1.0 - 0.5 / RES;
    return texture(sTD2DInputs[0], clamp(uv - flowAt(uv), lo, hi)).rgb;
}

void main()
{
    RES = uTD2DInfos[0].res.zw;
    vec2 uv = vUV.st;
    vec3 isrc = texture(sTD2DInputs[4], uv).rgb;
    vec3 col = adv(uv);

    // residual (P-frame look): what changed in the motion source since its last frame is
    // added onto the pushed-around old picture, so a new subject prints itself in the old
    // picture's colours.
    if (uC.w > 0.001)
        col = clamp(col + (texture(sTD2DInputs[1], uv).rgb - texture(sTD2DInputs[3], uv).rgb) * uC.w, 0.0, 1.0);

    // streaks (the pixel-sort look, made in the loop): in some columns light grows upward
    // (the brighter of a pixel and the one a few rows below wins), in others dark drips
    // downward. Which columns take part changes a few times a second.
    if (uB.y > 0.001) {
        float amt = min(uB.y, 1.0);
        float colid = floor(gl_FragCoord.x / 3.0);
        float gate = hash2(vec2(colid, floor(uB.z / 9.0)));
        if (gate < uB.y * 0.5) {
            float stepPx = (2.0 + floor(3.0 * hash2(vec2(colid, 3.0)))) * (uB.y > 1.0 ? 2.0 : 1.0);
            bool up = hash2(vec2(colid, 11.0)) < uD.y;
            vec2 puv = uv + vec2(0.0, (up ? -stepPx : stepPx) / RES.y);
            if (puv.y > 0.0 && puv.y < 1.0) {
                vec3 oth = adv(puv);
                float la = lum(col), lb = lum(oth);
                if (up) { if (lb > la + 0.03 && lb > 1.0 - 0.7 * amt) col = oth; }
                else    { if (lb < la - 0.03 && lb < 0.7 * amt) col = oth; }
            }
        }
    }

    // I-frames: whole frame, or part of it on weaker hits and while a shot arrives
    float k = uA.z;
    if (uA.w > 0.5) {
        col = isrc;
    } else {
        float h;
        if (uD.x < 0.5) {
            // ragged clusters of 40 px blocks (a coarse 160 px lottery decides the
            // neighbourhood, a fine one frays its edge)
            h = 0.55 * hash2(floor(gl_FragCoord.xy / 160.0) + uC.y * 1.731)
              + 0.45 * hash2(floor(gl_FragCoord.xy / 40.0) + uC.y * 0.917);
            h = clamp((h - 0.2) / 0.6, 0.0, 1.0);
        } else if (uD.x < 1.5) {
            // columns filling from the floor up
            h = 0.55 * hash2(vec2(floor(gl_FragCoord.x / 24.0), uC.y * 1.31)) + 0.45 * uv.y;
        } else {
            // a scan from the top in 16 px bands, a few bands ahead or behind
            h = 0.85 * (1.0 - floor(uv.y * 45.0) / 45.0) + 0.15 * hash2(vec2(floor(uv.y * 45.0), floor(gl_FragCoord.x / 160.0) + uC.y));
        }
        if (h < k) col = isrc;
        // slow healing: now and then one small block is refreshed
        vec2 sb = floor(gl_FragCoord.xy / 16.0);
        if (hash2(sb * 1.37 + uB.z * 0.113) < uC.z) col = isrc;
    }

    fragColor = TDOutputSwizzle(vec4(clamp(col, 0.0, 1.0), 1.0));
}
