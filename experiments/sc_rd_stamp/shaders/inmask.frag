// Input: turn another scene's picture into a stamp mask.
// Input 0: the picture (1280x720). Input 1: the same picture blurred wide (its local average).
// A pixel is "ink" where it is brighter than its surroundings: that follows the picture's
// shapes whatever its exposure, and gives strokes rather than big flat areas, which is what
// the chemistry needs (a flat flood of ink has nowhere to grow).
// Output: R = mask, G = luminance, B = local average, A = 1.
out vec4 fragColor;

void main() {
    vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
    vec3 b = texture(sTD2DInputs[1], vUV.st).rgb;
    const vec3 W = vec3(0.299, 0.587, 0.114);
    float l = dot(c, W);
    float lb = dot(b, W);
    float m = smoothstep(0.03, 0.11, l - lb);
    fragColor = TDOutputSwizzle(vec4(m, l, lb, 1.0));
}
