// sw_finish: keeps only the highlights, as the source for bloom and halation.
uniform vec4 uKnee; // x threshold, y unused
out vec4 fragColor;
void main() {
    vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
    float l = dot(c, vec3(0.299, 0.587, 0.114));
    float k = smoothstep(uKnee.x, 1.0, l);
    fragColor = TDOutputSwizzle(vec4(c * k, 1.0));
}
