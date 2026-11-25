// Waterfall history. Input 0: last frame (feedback). Input 1: the hub's full log-frequency spectrum (24000x1).
// Row 0 (v = 0) is the newest; every frame the rest shift one row away.
// R: terrain height 0..~1.5   A: drum flash at the time the row was written
uniform vec4 uLive;   // z flash, w spectrum gain
uniform vec4 uRes;    // x = 1 / rows, y = smoothing mix, z = treble tilt
out vec4 fragColor;

float spec(float x) { return texture(sTD2DInputs[1], vec2(clamp(x, 0.002, 0.998), 0.5)).r; }

void main()
{
    vec2 uv = vUV.st;
    float dv = uRes.x;
    vec4 c;
    if (uv.t < dv) {
        float a = abs(uv.s - 0.5) * 2.0;      // 0 centre, 1 edge
        float f = 1.0 - a;                    // bass at the edges, treble in the middle
        // the hub's full spectrum is log-frequency; the music lives in 14%..95% of it
        float x = 0.14 + 0.81 * f;
        float w = 0.81 / 256.0;               // one column's span, sampled with 7 taps
        float av = 0.0, mx = 0.0;
        for (int i = -3; i <= 3; i++) {
            float v = spec(x + float(i) * w * 0.6);
            av += v; mx = max(mx, v);
        }
        float s = mix(av / 7.0, mx, 0.3);
        s *= 1.0 + uRes.z * f;                // lift the treble a little
        float h = pow(s * uLive.w, 0.62);
        h = clamp(h, 0.0, 1.5);
        vec4 prev = texture(sTD2DInputs[0], vec2(uv.s, dv * 0.5));
        h = mix(prev.r, h, uRes.y);
        c = vec4(h, 0.0, 0.0, uLive.z);
    } else {
        c = texture(sTD2DInputs[0], uv - vec2(0.0, dv));
    }
    fragColor = c;
}
