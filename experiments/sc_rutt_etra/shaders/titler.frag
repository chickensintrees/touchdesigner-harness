// Describe mode caption: a strip across the lower part of the frame with the take's caption on it.
// Input 0: the signal. Input 1: the caption (Text TOP, full width, strip height, transparent).
// Only in the signal path while Describe is on (a Switch TOP bypasses it otherwise).
uniform vec4 uT;    // x strip height (fraction of frame), y strip's lower edge, z how far the strip darkens the picture, w text gain
uniform vec4 uTc;   // text colour
out vec4 fragColor;

void main()
{
    vec2 uv = vUV.st;
    vec4 c = texture(sTD2DInputs[0], uv);
    float v = (uv.y - uT.y) / uT.x;
    if (v > 0.0 && v < 1.0) {
        float edge = smoothstep(0.0, 0.08, v) * (1.0 - smoothstep(0.92, 1.0, v));
        float a = texture(sTD2DInputs[1], vec2(uv.x, v)).a;
        c.rgb *= 1.0 - uT.z * edge;
        c.rgb = mix(c.rgb, uTc.rgb * uT.w, a);
    }
    fragColor = TDOutputSwizzle(c);
}
