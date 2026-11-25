// Output pass, outside the loop so nothing here accumulates.
// Zoom into the buffer (nearest, so macroblocks stay square), an optional codec-analyser
// overlay (block grid and motion vectors), channel drift on vocals, optional 1-bit.
// In Describe mode, a two-line label that says what the take is doing.
// Inputs: 0 moshed frame, 1 flow, 2 label atlas (24 px Chicago, 32 px rows, label set n at rows 2n, 2n+1).
uniform vec4 uP;   // x drift 0..1 (vocals), y hit_high, z pulse, w 1 = 1-bit black and white
uniform vec4 uZ;   // x zoom (1 = none), y z zoom centre in UV, w overlay amount
uniform vec4 uG;   // x macroblock size in px, y vector length gain, z unused, w unused
uniform vec4 uL;   // x label: 0 none, 1 bottom left, 2 top left; y label set; z w widths of its two lines in px
out vec4 fragColor;

void main()
{
    vec2 res = uTD2DInfos[0].res.zw;
    float zoom = max(uZ.x, 1.0);
    vec2 cen = clamp(uZ.yz, vec2(0.5 / zoom), vec2(1.0 - 0.5 / zoom));
    vec2 uv = (vUV.st - 0.5) / zoom + cen;
    // snap to the buffer's pixel centres so a zoomed pixel is one flat square
    uv = (floor(uv * res) + 0.5) / res;
    vec2 f = texture(sTD2DInputs[1], uv).xy;
    vec2 fd = f * 1.5;
    float fl = length(fd * res);
    if (fl > 10.0) fd *= 10.0 / fl;
    vec2 d = (vec2(1.5, 0.0) / res + fd) * uP.x + vec2(2.0, 0.0) / res * uP.y;
    d = floor(d * res + 0.5) / res;
    vec3 c;
    vec2 lo = 0.5 / res, hi = 1.0 - 0.5 / res;
    c.r = texture(sTD2DInputs[0], clamp(uv + d, lo, hi)).r;
    c.g = texture(sTD2DInputs[0], uv).g;
    c.b = texture(sTD2DInputs[0], clamp(uv - d, lo, hi)).b;

    if (uZ.w > 0.001) {
        // analyser overlay, drawn in buffer pixels
        float B = max(uG.x, 4.0);
        vec2 bp = ((vUV.st - 0.5) / zoom + cen) * res;
        vec2 bc = (floor(bp / B) + 0.5) * B;
        vec2 v = texture(sTD2DInputs[1], bc / res).xy * res * uG.y;
        float vl = length(v);
        if (vl > B * 1.6) v *= B * 1.6 / vl;
        vec2 pa = bp - bc;
        float hh = clamp(dot(pa, v) / max(dot(v, v), 1e-4), 0.0, 1.0);
        float dl = length(pa - v * hh);
        float px = 1.0 / zoom;                                  // one screen pixel in buffer pixels
        float line = (1.0 - smoothstep(0.8 * px, 1.6 * px, dl)) * step(0.6, vl);
        float dotm = 1.0 - smoothstep(2.0 * px, 3.0 * px, length(pa));
        vec2 ge = B * 0.5 - abs(pa);
        float grid = 1.0 - smoothstep(0.5 * px, 1.2 * px, min(ge.x, ge.y));
        float l = dot(c, vec3(0.299, 0.587, 0.114));
        vec3 mark = l > 0.55 ? vec3(0.06, 0.09, 0.13) : vec3(0.98, 0.95, 0.86);
        c = mix(c, mark, 0.28 * grid * uZ.w);
        c = mix(c, mark, max(line, dotm) * uZ.w);
    }

    if (uP.w > 0.5) {
        c = vec3(step(0.5, dot(c, vec3(0.299, 0.587, 0.114))));
    } else {
        // gentle corner falloff so the fields do not read as flat vector art
        vec2 q = vUV.st - 0.5;
        c *= 1.0 - 0.28 * dot(q, q) * 2.0;
    }
    if (uL.x > 0.5) {
        // drawn 1:1 in screen pixels on an ink plate so it reads over anything
        vec2 o = vUV.st * res - vec2(34.0, uL.x > 1.5 ? res.y - 92.0 : 30.0);
        float wmax = max(uL.z, uL.w);
        if (o.x > -14.0 && o.x < wmax + 14.0 && o.y > -10.0 && o.y < 72.0) {
            bool mono = uP.w > 0.5;                            // the 1-bit take keeps a 1-bit label
            c = mono ? vec3(0.0) : mix(c, vec3(0.06, 0.09, 0.13), 0.9);
            int li = o.y >= 32.0 ? 0 : 1;                      // line 0 is the upper one
            float ty = o.y - (li == 0 ? 32.0 : 0.0);
            if (o.x >= 0.0 && o.x < 1264.0 && ty >= 0.0 && ty < 32.0) {
                float v = texelFetch(sTD2DInputs[2], ivec2(int(o.x) + 8, (int(uL.y) * 2 + li) * 32 + int(ty)), 0).r;
                if (mono) c = vec3(step(0.5, v));
                else c = mix(c, li == 0 ? vec3(0.863, 0.710, 0.239) : vec3(0.933, 0.894, 0.800), v);
            }
        }
    }
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
