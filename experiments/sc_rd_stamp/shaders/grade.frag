// Finish: depth of field (blur circle in input 0's alpha), add the blurred highlights
// (input 1) to the HDR picture, vignette, filmic shoulder, gamma, and for the 1-bit take an
// ordered dither to pure black and white. The glow is taken before the tonemap, so the paper
// never blooms (the Bloom TOP on the tonemapped image washed it white, captures/09_220.png).
uniform vec4 uGrade;  // glow gain, kick, hit_high, shot age (s)
uniform vec4 uFx;     // depth of field radius (px, 0 = off), 1-bit (0/1), exposure, vignette
out vec4 fragColor;

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
                                  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

void main() {
    vec2 scr = (vUV.st - 0.5) * vec2(16.0 / 9.0, 1.0);
    vec4 c0 = texture(sTD2DInputs[0], vUV.st);
    vec3 col = c0.rgb;
    if (uFx.x > 0.0) {
        float rad = c0.a * uFx.x;
        if (rad > 0.6) {
            vec2 px = uTD2DInfos[0].res.xy;
            vec3 acc = col;
            float wsum = 1.0;
            // the spiral is turned by a different amount at every pixel: a fixed spiral
            // drew moire over the blurred highlights (captures/a1.png)
            float turn = 6.2832 * fract(52.9829189 * fract(dot(gl_FragCoord.xy, vec2(0.06711056, 0.00583715))));
            for (int i = 0; i < 22; i++) {
                float fi = float(i) + 0.5;
                float r = sqrt(fi / 22.0) * rad;
                float a = fi * 2.39996 + turn;
                vec4 s = texture(sTD2DInputs[0], vUV.st + vec2(cos(a), sin(a)) * r * px);
                // a sharp neighbour does not smear into a blurred pixel's disc as much
                float w = 0.25 + 0.75 * smoothstep(0.0, 1.0, s.a * uFx.x / max(r, 1.0));
                acc += min(s.rgb, vec3(4.0)) * w;   // an unclamped glint scatters as salt (captures/take_1_in.png)
                wsum += w;
            }
            col = acc / wsum;
        }
    }
    vec3 glow = texture(sTD2DInputs[1], vUV.st).rgb;
    col += glow * uGrade.x * (1.0 + 0.8 * uGrade.y);
    col *= 1.0 - uFx.w * dot(scr, scr);
    // the cut lands like a flashbulb
    float flash = exp(-uGrade.w * 9.0);
    col *= uFx.z * (1.0 + 0.10 * uGrade.y + 1.3 * flash);
    // ACES-like shoulder (Narkowicz fit)
    col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
    col = clamp(pow(max(col, 0.0), vec3(1.0 / 2.2)), 0.0, 1.0);
    if (uFx.y > 0.5) {
        ivec2 q = ivec2(gl_FragCoord.xy / 2.0) & 3;
        float th = (BAYER[q.y * 4 + q.x] + 0.5) / 16.0;
        float l = dot(col, vec3(0.299, 0.587, 0.114));
        l = smoothstep(0.08, 0.92, l);
        col = vec3(step(th, l));
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
