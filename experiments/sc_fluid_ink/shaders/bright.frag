// Highlights only, at low resolution, for the glow.
uniform vec4 uGlow;   // gain, threshold, unused, unused
out vec4 fragColor;
void main() {
    vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
    float l = max(c.r, max(c.g, c.b));
    fragColor = TDOutputSwizzle(vec4(c * smoothstep(uGlow.y, uGlow.y + 0.3, l), 1.0));
}
