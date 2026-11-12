// "Relic" take: put the rendered model (input 0, premultiplied, linear HDR) into the void:
// a dark room with one pair of fluorescent tubes overhead and a pool of light on the floor.
uniform vec4 uBg;  // evolve, kick, seed, pulse
out vec4 fragColor;
void main() {
    vec2 scr = (vUV.st - 0.5) * vec2(16.0 / 9.0, 1.0);
    vec4 r = texture(sTD2DInputs[0], vUV.st);
    vec3 bg = mix(vec3(0.004, 0.007, 0.006), vec3(0.020, 0.030, 0.026), smoothstep(0.5, -0.5, scr.y));
    // tubes, seen in perspective above the model
    float y = scr.y - 0.36;
    float persp = 1.0 / max(0.25 + y * 1.6, 0.05);
    float x = (scr.x + 0.15 * sin(uBg.x * 0.05 + uBg.z * 6.28)) * persp;
    float pair = smoothstep(0.035, 0.012, abs(abs(fract(x * 0.9 + 0.5) - 0.5) / 0.9 - 0.06));
    bg += vec3(0.86, 0.95, 0.78) * pair * smoothstep(0.0, 0.10, y) * (0.8 + 0.5 * uBg.w);
    // light pool under the model
    vec2 d = scr - vec2(0.0, -0.42);
    bg += vec3(0.10, 0.12, 0.09) * exp(-(d.x * d.x * 3.0 + d.y * d.y * 40.0)) * (1.0 + uBg.y);
    vec3 col = r.rgb + bg * (1.0 - r.a);
    fragColor = TDOutputSwizzle(vec4(clamp(col, 0.0, 40.0), 0.0));
}
