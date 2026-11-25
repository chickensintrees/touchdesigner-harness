// Puts the render over the take's background, adds depth of field, then grades it.
// Input 0: render, alpha = camera depth in units (0 where nothing was drawn).
// Input 1: control texture. Input 2: blurred render, mixed in by depth.
// Every look value comes from the take (the 'tk' CHOP in build.py).
uniform vec3 uHaze;     // background / fog colour of the take
uniform vec3 uShadow;   // what the shadows are multiplied by (ink blue, sick green, nothing)
uniform vec4 uP1;       // x void glow, y vignette, z saturation, w 1-bit dither
uniform vec4 uP2;       // x far blur starts this far behind focus, y is full by here, z near blur begins inside this distance (0 = none), w sky gradient
out vec4 fragColor;

float C(int i) { return texelFetch(sTD2DInputs[1], ivec2(0, i), 0).r; }

float bayer4(vec2 p) {
    ivec2 i = ivec2(mod(p, 4.0));
    int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
    return (float(m[i.x + i.y * 4]) + 0.5) / 16.0;
}

void main() {
    vec2 uv = vUV.st;
    // the 1-bit take is drawn in fat pixels, like the game
    if (uP1.w > 0.5) uv = (floor(uv * vec2(640.0, 360.0)) + 0.5) / vec2(640.0, 360.0);
    vec4 r = texture(sTD2DInputs[0], uv);
    float energy = C(4), snare = C(9);
    vec2 q = (uv - 0.5) * vec2(1.7778, 1.0);
    float d = length(q);
    vec4 b = texture(sTD2DInputs[2], uv);
    float depth = r.a, focus = C(8);
    float far = depth < 0.01 ? 1.0 : smoothstep(focus + uP2.x, focus + uP2.y, depth);
    float near = (depth < 0.01 || uP2.z < 0.01) ? 0.0 : 1.0 - smoothstep(uP2.z * 0.4, uP2.z, depth);
    float coc = max(far, near);
    vec3 col = mix(r.rgb, b.rgb, coc);
    // the void glows faintly behind everything, more when the passage is loud
    col += uHaze * uP1.x * (0.2 + 1.6 * energy) * mix(1.3, 0.0, smoothstep(0.0, 0.9, d)) * far;
    // a sky is lighter at the top
    col *= mix(1.0, mix(0.8, 1.12, uv.y), uP2.w * (depth < 0.01 ? 1.0 : 0.3));
    // snare lifts the whole room for an instant, like a tube striking
    col *= 1.0 + 0.22 * snare;
    col = 1.25 * col / (1.0 + 0.5 * col);
    // shoulder: everything above 0.72 rolls off towards 1 instead of clipping (the lamp pool)
    col = mix(col, 0.72 + 0.28 * tanh((col - 0.72) / 0.28), step(0.72, col));
    float l = dot(col, vec3(0.3, 0.59, 0.11));
    col = mix(col, col * uShadow, 1.0 - smoothstep(0.03, 0.5, l));
    col = mix(vec3(l), col, uP1.z);
    col = pow(max(col, 0.0), vec3(1.18));
    float vig = 1.0 - smoothstep(0.35, 1.15, d);
    col *= mix(1.0 - uP1.y, 1.0, vig);
    if (uP1.w > 0.5) {
        float lum = dot(col, vec3(0.3, 0.59, 0.11));
        lum = pow(clamp(lum * 1.25, 0.0, 1.0), 0.8);
        col = vec3(step(bayer4(floor(vUV.st * vec2(640.0, 360.0))), lum));
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
