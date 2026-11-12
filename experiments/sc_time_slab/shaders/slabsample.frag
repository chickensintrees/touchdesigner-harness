// Resample the slab (a ring of the last 64 plates, as a 2D texture array) per pixel.
// Array input 0: the slab. 2D input 0: the time map (0 = now, 1 = oldest).
// uHead.w picks how the slab is read; see TAKES in build.py.
//   0 map:    every pixel looks back as far as the time map says; R, G, B at
//             slightly different depths, layers blended
//   1 (unused here: the strip photograph is its own TOP, strip.frag)
//   2 panels: N tall panels, the same crop of the plate at N different moments
//   3 grid:   contact sheet, every cell the whole plate a little older
// Depths arrive in frames but are computed from seconds and the measured frame rate.
// Nothing reads further back than the frames stored since this shot's take was set
// (uHead.z), so a cut never shows plates from an earlier shot; the past opens up over
// the first second.
uniform vec4 uHead;   // ring index written this frame, slab length, frames stored this shot, mode
uniform vec4 uDepth;  // depth in frames for R, G, B; w = dither amount
uniform vec4 uS;      // panels or columns, rows, 1 in Describe mode (grid only), 0
uniform vec4 uK;      // s1, s2, kick count, hit_low
out vec4 fragColor;

float hash12(vec2 p)
{
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec3 layer(vec2 uv, float a)
{
    float n = uHead.y;
    return texture(sTD2DArrayInputs[0], vec3(uv, mod(uHead.x - a + n, n))).rgb;
}

vec3 slab(vec2 uv, float age)
{
    age = clamp(min(age, uHead.z), 0.0, uHead.y - 2.0);
    float a0 = floor(age);
    return mix(layer(uv, a0), layer(uv, a0 + 1.0), age - a0);
}

void main()
{
    vec2 uv = vUV.st;
    int mode = int(uHead.w + 0.5);
    float maxd = uDepth.x;
    vec3 col;

    if (mode == 2) {
        float n = uS.x;
        float i = floor(uv.x * n);
        float px = fract(uv.x * n);
        // every kick moves "now" one panel along
        float k = mod(i + uK.z, n);
        if (uK.x > 0.5) k = n - 1.0 - k;
        float a = k / max(n - 1.0, 1.0) * maxd;
        vec2 q = vec2(0.5 + (px - 0.5) / n, uv.y);
        col = slab(q, a);
        // gel per panel: ident red, yellow, blue, green, pink over an ivory key
        vec3 gel[5] = vec3[5](vec3(1.0, 0.33, 0.22), vec3(1.0, 0.80, 0.22), vec3(0.20, 0.62, 0.86),
                              vec3(0.62, 0.78, 0.30), vec3(0.86, 0.34, 0.56));
        vec3 g = gel[int(mod(i + floor(uK.y * 5.0), 5.0))];
        float l = dot(col, vec3(0.299, 0.587, 0.114));
        col = mix(g * l * 1.5, col * mix(vec3(1.0), g, 0.55), 0.35) + g * 0.035;
        col *= smoothstep(0.0, 0.012, px) * smoothstep(1.0, 0.988, px);
    } else if (mode == 3) {
        vec2 g = vec2(uS.x, uS.y);
        // Describe mode: the whole sheet is drawn at 85% above the caption band (108 px of 720),
        // so no row of cells is hidden under the words. Off: gv == uv, the picture is unchanged.
        vec2 gv = uS.z > 0.5 ? vec2((uv.x - 0.5) / 0.85 + 0.5, (uv.y - 0.15) / 0.85) : uv;
        vec2 c = floor(gv * g);
        vec2 q = fract(gv * g);
        float k = c.x + (g.y - 1.0 - c.y) * g.x;       // reading order, newest top left
        float a = k / (g.x * g.y - 1.0) * maxd;
        if (a > uHead.z) col = vec3(0.0);              // cells fill in after the cut
        else col = slab(q, a);
        vec2 e = smoothstep(vec2(0.0), vec2(0.03, 0.05), q) * smoothstep(vec2(1.0), vec2(0.97, 0.95), q);
        col *= e.x * e.y;
        if (gv.x < 0.0 || gv.x > 1.0 || gv.y < 0.0 || gv.y > 1.0) col = vec3(0.0);
    } else {
        float d = texture(sTD2DInputs[0], uv).r;
        d += (hash12(gl_FragCoord.xy) - 0.5) * uDepth.w;
        col.r = slab(uv, d * uDepth.x).r;
        col.g = slab(uv, d * uDepth.y).g;
        col.b = slab(uv, d * uDepth.z).b;
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
