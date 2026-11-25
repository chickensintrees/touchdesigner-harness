// im_montage: the flat two-colour printed ground behind the cut-outs. Six patterns,
// all hard-edged, all moved by the music.
uniform vec4 uA;    // rgb first colour, w pattern: 0 burst 1 rings 2 stripes 3 dots 4 checker 5 split
uniform vec4 uB;    // rgb second colour, w beat position (counts up one per beat)
uniform vec4 uAim;  // x kick 0..1, y bass 0..1, z seconds, w number of rays
out vec4 fragColor;

float edge(float v, float w) { return smoothstep(0.5 - w, 0.5 + w, v); }

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 p = (vUV.st - vec2(0.5, 0.46)) * vec2(res.x / res.y, 1.0);
    int mode = int(uA.w + 0.5);
    float beat = uB.w;
    float kick = uAim.x;
    float bass = uAim.y;
    float k = 0.0;
    if (mode == 0) {            // sunburst: steps round one ray per beat, opens on kicks
        float rays = max(2.0, floor(uAim.w + 0.5));
        float a = atan(p.y, p.x) / 6.2831853 * rays + floor(beat) * 0.5 + 0.5 * smoothstep(0.0, 0.25, fract(beat));
        float w = fwidth(a) * 1.2;
        k = edge(abs(fract(a) - 0.5) * 2.0 * (1.0 - 0.3 * kick), w);
    } else if (mode == 1) {     // rings that travel outward, a ring per beat
        float r = length(p) * 5.0 - beat * 1.0 - bass * 0.6;
        k = edge(abs(fract(r) - 0.5) * 2.0, fwidth(r) * 1.5);
    } else if (mode == 2) {     // slanted stripes that slide with the beat and thicken with the bass
        float s = (p.x + p.y * 0.6) * 5.0 + beat * 0.5;
        k = edge(abs(fract(s) - 0.5) * 2.0 + (bass - 0.4) * 0.5, fwidth(s) * 1.5);
    } else if (mode == 3) {     // halftone dots whose size is the bass, popping on kicks
        vec2 g = p * 9.0;
        g.x += 0.5 * floor(g.y);
        float d = length(fract(g) - 0.5);
        float rad = 0.16 + 0.22 * bass + 0.12 * kick;
        k = 1.0 - smoothstep(rad - 0.02, rad + 0.02, d);
    } else if (mode == 4) {     // checkerboard that swaps on every beat
        vec2 g = floor(p * 4.0 + vec2(0.0, 0.5));
        k = mod(g.x + g.y + floor(beat), 2.0);
        float pulse = kick * 0.35;
        vec2 f = abs(fract(p * 4.0 + vec2(0.0, 0.5)) - 0.5);
        if (max(f.x, f.y) > 0.5 - pulse * 0.5) k = 1.0 - k;
    } else {                    // split field: a diagonal that swings on the beat
        float lean = 0.5 * sin(beat * 3.14159265);
        float s = p.x + p.y * lean + (kick - 0.3) * 0.15;
        k = edge(s * 8.0 + 0.5, fwidth(s * 8.0) * 1.5);
    }
    vec3 col = mix(uA.rgb, uB.rgb, clamp(k, 0.0, 1.0));
    col *= 1.0 - 0.18 * smoothstep(0.3, 1.2, length(p));   // printed, not lit
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
