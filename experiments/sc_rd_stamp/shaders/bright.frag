// Glow source: only what is brighter than lit paper (the lamp on gold, enamel and tar).
out vec4 fragColor;
void main() {
    vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
    float l = max(c.r, max(c.g, c.b));
    c *= smoothstep(1.25, 2.6, l);
    fragColor = TDOutputSwizzle(vec4(min(c, vec3(10.0)), 1.0));
}
