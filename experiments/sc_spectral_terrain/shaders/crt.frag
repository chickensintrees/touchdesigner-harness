// Finish. Input 0: scene, input 1: bloom of the scene, input 2: Chicago label (alpha).
// uPost.x: 0 CRT phosphor tube, 1 printed paper, 2 one-bit dither (the game's look).
uniform vec4 uFx;      // x pulse, y hit_mid, z t, w energy
uniform vec4 uAmt;     // x bloom gain, y scanline depth, z barrel, w aberration
uniform vec4 uPost;    // x mode, y invert (one-bit), z label strength, w exposure for one-bit
uniform vec4 uLab;     // rgb label colour
uniform vec4 uPaper;   // rgb paper colour (the caption strip)
uniform vec4 uDesc;    // x caption strip height (0.100 normally, taller in Describe mode), y halo behind the caption (Describe mode on the tube)
out vec4 fragColor;

vec2 barrel(vec2 uv, float k)
{
    vec2 c = uv - 0.5;
    float r2 = dot(c, c);
    return 0.5 + c * (1.0 + k * r2) / (1.0 + k * 0.25);
}

vec3 scene(vec2 uv)
{
    return texture(sTD2DInputs[0], uv).rgb + texture(sTD2DInputs[1], uv).rgb * uAmt.x;
}

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }

float bayer(ivec2 p)
{
    const float m[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
    return (m[(p.x & 3) + (p.y & 3) * 4] + 0.5) / 16.0;
}

void main()
{
    int mode = int(uPost.x + 0.5);
    vec3 col;
    if (mode == 1) {
        // paper: no tube, no glow. A snare knocks the plates out of register.
        vec2 uv = vUV.st;
        vec2 off = vec2(0.0020, -0.0009) * uFx.y;
        vec3 a = texture(sTD2DInputs[0], uv).rgb;
        vec3 b = texture(sTD2DInputs[0], uv + off).rgb;
        col = vec3(a.r, min(a.g, b.g), b.b);
        // a title block along the bottom edge, ruled off like a drawing sheet
        float strip = 1.0 - smoothstep(uDesc.x - 0.002, uDesc.x, uv.y);
        col = mix(col, uPaper.rgb, strip * uPost.z);
        col = mix(col, uLab.rgb, (1.0 - smoothstep(0.0012, 0.0024, abs(uv.y - uDesc.x - 0.004))) * uPost.z);
        float lab = texture(sTD2DInputs[2], uv).a * uPost.z;
        col = mix(col, uLab.rgb, lab);
        // fibre and a soft fold of shadow
        float fib = hash(floor(uv * vec2(1280.0, 720.0))) - 0.5;
        float fib2 = hash(floor(uv * vec2(160.0, 720.0)) + 7.0) - 0.5;
        col *= 1.0 + fib * 0.045 + fib2 * 0.025;
        vec2 e = abs(uv - 0.5) * 2.0;
        col *= 1.0 - 0.16 * pow(dot(e, e) * 0.5, 1.6);
        col *= 0.97 + 0.03 * uFx.x;
        fragColor = TDOutputSwizzle(vec4(clamp(col, 0.0, 1.0), 1.0));
        return;
    }
    if (mode == 2) {
        // one-bit: 640x360 fat pixels, ordered dither, pure black and white
        ivec2 ip = ivec2(gl_FragCoord.xy) / 2;
        vec2 uv = (vec2(ip) * 2.0 + 1.0) / vec2(1280.0, 720.0);
        vec3 s = scene(uv);
        float l = dot(s, vec3(0.30, 0.59, 0.11)) * uPost.w * (1.0 + 0.25 * uFx.x);
        // caption strip: cleared, ruled, then the Chicago text
        if (uPost.z > 0.0 && uv.y < uDesc.x) l = (uv.y > uDesc.x - 0.006) ? 1.0 : 0.0;
        l = max(l, texture(sTD2DInputs[2], uv).a * uPost.z);
        float bit = step(bayer(ip), l);
        // Describe mode: the caption is drawn at full resolution so two lines of small type stay readable
        if (uDesc.y > 0.0) bit = max(bit * step(uDesc.x, uv.y), step(0.5, texture(sTD2DInputs[2], vUV.st).a * uPost.z));
        bit = mix(bit, 1.0 - bit, uPost.y);
        fragColor = TDOutputSwizzle(vec4(vec3(bit), 1.0));
        return;
    }
    vec2 uv = barrel(vUV.st, uAmt.z);
    float ab = uAmt.w * (0.4 + 2.0 * uFx.y);
    vec2 dir = (uv - 0.5) * ab;
    col.r = scene(uv + dir).r;
    col.g = scene(uv).g;
    col.b = scene(uv - dir).b;
    if (uDesc.y > 0.0) {
        // Describe mode: a dark outline behind the caption so it reads over bright lines
        float m = 0.0;
        for (int i = 0; i < 8; i++) {
            float a = float(i) * 0.7853982;
            vec2 o = vec2(cos(a), sin(a)) / vec2(1280.0, 720.0);
            m = max(m, texture(sTD2DInputs[2], uv + o * 2.5).a);
            m = max(m, texture(sTD2DInputs[2], uv + o * 5.0).a * 0.8);
        }
        col *= 1.0 - uDesc.y * m;
    }
    col += uLab.rgb * texture(sTD2DInputs[2], uv).a * uPost.z;
    // scanlines: 360 line pairs, slowly rolling
    float sl = 0.5 + 0.5 * sin((uv.y * 360.0 + uFx.z * 0.6) * 6.2832);
    col *= 1.0 - uAmt.y * sl * (1.0 - 0.5 * clamp(dot(col, vec3(0.333)), 0.0, 1.0));
    // a soft hum bar drifting up the tube
    float hb = (fract(uv.y - uFx.z * 0.07) - 0.5) * 6.0;
    float hum = exp(-hb * hb);
    col *= 1.0 + 0.07 * hum;
    col *= 1.0 + 0.10 * uFx.x;
    // vignette and tube edge
    vec2 e = abs(uv - 0.5) * 2.0;
    float vig = 1.0 - 0.38 * pow(dot(e, e) * 0.5, 1.4);
    float edge = 1.0 - smoothstep(0.985, 1.0, max(e.x, e.y));
    col *= vig * edge;
    col += (hash(vUV.st * vec2(1280.0, 720.0) + uFx.z * 60.0) - 0.5) * 0.012;
    // soft shoulder so hot phosphor rolls off instead of clipping
    col = 1.0 - exp(-max(col, 0.0) * 1.25);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
