// Describe mode only: a caption along the bottom of the finished frame.
// Input 0: the graded picture. Input 1: the caption (Text TOP, transparent background).
out vec4 fragColor;

void main() {
    vec3 col = texture(sTD2DInputs[0], vUV.st).rgb;
    float t = texture(sTD2DInputs[1], vUV.st).a;
    // a dark band behind the two lines, fading out upward
    float band = smoothstep(0.170, 0.115, vUV.t);
    col = mix(col, vec3(0.020, 0.028, 0.026), 0.84 * band);
    col = mix(col, vec3(0.93, 0.89, 0.78), clamp(t, 0.0, 1.0));
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
