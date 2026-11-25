// The lit picture plus its glow.
// in2: a caption (white on black), printed in dark ink when uGlow.z is on.
// Describe mode puts it on a strip along the bottom edge so it reads over any ink:
// uGlow.w 1 = dark type on a pale strip, 2 = pale type on a dark strip, 0 = no strip (the inkblot plate).
uniform vec4 uGlow;   // gain, threshold, caption, strip
out vec4 fragColor;
void main() {
    vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
    vec3 g = texture(sTD2DInputs[1], vUV.st).rgb;
    c += g * uGlow.x;
    vec3 capc = vec3(0.07, 0.07, 0.08);
    if (uGlow.w > 0.5) {
        vec3 pale = vec3(0.95, 0.93, 0.87);
        vec3 strip = uGlow.w > 1.5 ? capc : pale;
        capc = uGlow.w > 1.5 ? pale : capc;
        c = mix(c, strip, 0.9 * (1.0 - smoothstep(0.0700, 0.0715, vUV.t)) * uGlow.z);
    }
    c = mix(c, capc, texture(sTD2DInputs[2], vUV.st).r * uGlow.z);
    fragColor = TDOutputSwizzle(vec4(clamp(c, 0.0, 1.0), 1.0));
}
