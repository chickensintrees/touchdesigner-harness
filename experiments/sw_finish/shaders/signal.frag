// sw_finish, pass 1: what happens to the SIGNAL before it reaches a display.
// Gate weave (film), then tape faults: line jitter, a travelling tracking bar,
// head-switch noise along the bottom edge, colour bleeding to the right, softness.
uniform vec4 uTape;  // x chroma bleed, y tracking error, z head switch, w softness
uniform vec4 uClock; // x seconds, y frame (wrapped), z gate weave, w unused
out vec4 fragColor;

float hash1(float x) { return fract(sin(x * 127.1) * 43758.5453); }
float hash2(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
float noise1(float x) {
    float i = floor(x), f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    return mix(hash1(i), hash1(i + 1.0), f);
}
vec3 toYiq(vec3 c) {
    return vec3(dot(c, vec3(0.299, 0.587, 0.114)), dot(c, vec3(0.596, -0.274, -0.322)), dot(c, vec3(0.211, -0.523, 0.312)));
}
vec3 toRgb(vec3 c) {
    return vec3(c.x + 0.956 * c.y + 0.621 * c.z, c.x - 0.272 * c.y - 0.647 * c.z, c.x - 1.106 * c.y + 1.703 * c.z);
}
vec3 src(vec2 uv) { return texture(sTD2DInputs[0], clamp(uv, vec2(0.001), vec2(0.999))).rgb; }

void main() {
    vec2 uv = vUV.st;
    float t = uClock.x;
    float fr = floor(uClock.y);
    vec2 px = uTDOutputInfo.res.xy;

    // Gate weave: the whole frame wanders slowly and twitches a little each frame.
    vec2 weave = (vec2(noise1(t * 1.3), noise1(t * 1.7 + 9.0)) - 0.5) * 0.005;
    weave += (vec2(hash1(fr), hash1(fr + 3.0)) - 0.5) * 0.0012;
    uv += weave * uClock.z;

    // Tape: every scan line sits slightly left or right of where it should.
    float line = floor(uv.y * 240.0);
    float jitter = (hash2(vec2(line, fr)) - 0.5) * 0.0018 * uTape.y;

    // Tracking bar: a band that travels up the picture and tears it sideways.
    float bandY = fract(t * 0.06 + noise1(t * 0.3) * 0.3);
    float d = abs(uv.y - bandY);
    d = min(d, 1.0 - d);
    float band = smoothstep(0.05, 0.0, d) * smoothstep(0.0, 0.15, uTape.y);
    float tear = band * (noise1(uv.y * 90.0 + t * 30.0) - 0.5) * 0.07 * uTape.y;

    // Head switch: the bottom few lines are skewed and noisy.
    float hs = smoothstep(0.04, 0.0, uv.y) * uTape.z;
    float skew = hs * (0.03 + 0.03 * noise1(t * 8.0 + uv.y * 300.0));

    uv.x += jitter + tear + skew;

    // Luma: a little soft. Chroma: averaged over a run of pixels to the left, so
    // colour arrives late and bleeds to the right of bright shapes.
    float soft = uTape.w * 1.6;
    vec3 c0 = src(uv);
    vec3 cl = src(uv - vec2(px.x * soft, 0.0));
    vec3 cr = src(uv + vec2(px.x * soft, 0.0));
    float y = toYiq(c0 * 0.5 + (cl + cr) * 0.25).x;
    vec2 iq = vec2(0.0);
    float wsum = 0.0;
    float reach = 2.5 * uTape.x;
    for (int i = 0; i < 9; i++) {
        float w = 1.0 - float(i) / 10.0;
        iq += toYiq(src(uv - vec2(px.x * float(i) * reach, 0.0))).yz * w;
        wsum += w;
    }
    iq /= wsum;
    vec3 col = toRgb(vec3(y, iq));
    col = mix(c0, col, clamp(max(uTape.x, uTape.w) * 4.0, 0.0, 1.0));

    // Dropouts inside the tracking bar and the head-switch band: short white streaks.
    float streak = step(0.965, hash2(vec2(floor(uv.x * 90.0 + hash1(line + fr) * 40.0), line + fr * 7.0)));
    col += streak * (band * 0.8 + hs * 0.6);
    col *= 1.0 - hs * 0.35;
    // Tape hiss: fine luma noise that scales with the tracking amount.
    col += (hash2(vec2(uv.x * 700.0 + fr, line * 3.0 + fr)) - 0.5) * 0.05 * uTape.y;

    fragColor = TDOutputSwizzle(vec4(max(col, 0.0), 1.0));
}
