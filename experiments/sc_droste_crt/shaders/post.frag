// Final grade. Nothing here is fed back: the loop takes the master render before this.
// input 0: the view (master, dolly camera or Escher)   input 1: blurred view   input 2: screen texture
uniform vec4 uComp;   // hue degrees, gain, blend-to-screen-texture, 1-bit mode
uniform vec4 uA;      // shot age, pulse, hit_high, evolve
uniform vec4 uG;      // saturation, contrast, vignette, grain
uniform vec4 uTintP;  // shadow tint rgb, bloom amount
uniform vec4 uB;      // hit_low, kick parity (1-bit polarity), -, -
out vec4 fragColor;

vec3 hueRot(vec3 c, float deg) {
    float a = radians(deg);
    float cs = cos(a), sn = sin(a);
    const vec3 k = vec3(0.57735);
    return c * cs + cross(k, c) * sn + k * dot(k, c) * (1.0 - cs);
}
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
float bayer(vec2 p) {
    ivec2 i = ivec2(mod(p, 4.0));
    int idx = i.x + i.y * 4;
    const float m[16] = float[16](0., 8., 2., 10., 12., 4., 14., 6., 3., 11., 1., 9., 15., 7., 13., 5.);
    return (m[idx] + 0.5) / 16.0;
}

vec3 view(vec2 uv) {
    vec3 c = texture(sTD2DInputs[0], uv).rgb;
    if (uComp.z > 0.001) c = mix(c, texture(sTD2DInputs[2], uv).rgb, uComp.z);
    return c;
}

void main() {
    vec2 uv = vUV.st;
    vec2 p = uv * 2.0 - 1.0;
    // a little lens colour fringing, more on hats
    float ca = 0.0012 + 0.004 * uA.z;
    vec3 c = vec3(view(uv + p * ca).r, view(uv).g, view(uv - p * ca).b);
    vec3 b = texture(sTD2DInputs[1], uv).rgb;
    c += uTintP.w * b * b;
    c = max(c, vec3(0.0));
    c = hueRot(c, uComp.x) * uComp.y;
    c = max(c, vec3(0.0));

    c += exp(-uA.x * 9.0) * 0.35;                       // arrival flash
    c = 1.0 - exp(-c * 1.25);                           // shoulder
    float l = dot(c, vec3(0.299, 0.587, 0.114));
    c = mix(vec3(l), c, uG.x);
    c = (c - 0.5) * uG.y + 0.5;
    c += uTintP.rgb * (1.0 - l) * 0.12;
    c *= 1.0 - uG.z * pow(length(p * vec2(0.9, 1.0)), 2.6) * 0.55;
    c += (hash(gl_FragCoord.xy + fract(uA.w) * 91.7) - 0.5) * uG.w;

    if (uComp.w > 0.5) {                                 // the game's 1-bit look
        float g = dot(max(c, vec3(0.0)), vec3(0.299, 0.587, 0.114));
        // mostly a hard threshold, with a narrow band of coarse dither at the edges of
        // shapes; each kick flips the polarity of the whole picture and holds it
        g = smoothstep(0.10, 0.62, g);
        float th = mix(0.5, bayer(floor(gl_FragCoord.xy / 3.0)), 0.42);
        float bit = step(th, g);
        if (uB.y > 0.5) bit = 1.0 - bit;
        c = mix(vec3(0.02, 0.02, 0.03), vec3(0.96, 0.95, 0.90), bit);
    }
    fragColor = TDOutputSwizzle(vec4(clamp(c, 0.0, 1.0), 1.0));
}
