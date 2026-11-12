// Environment map for the models (equirectangular, 512x256): a paper-white studio
// ceiling, a hot horizon band and an ink floor, with two hard soft-box strips so
// glossy and metal surfaces get graphic highlights instead of rendering black.
out vec4 fragColor;

void main()
{
    vec2 uv = vUV.st;                      // x = longitude, y = 0 floor .. 1 ceiling
    vec3 ink   = vec3(0.03, 0.05, 0.08);
    vec3 ivory = vec3(0.933, 0.894, 0.800);
    vec3 hot   = vec3(0.95, 0.55, 0.20);
    vec3 blue  = vec3(0.157, 0.494, 0.608);
    vec3 c = mix(ink, blue * 0.6, smoothstep(0.0, 0.45, uv.y));
    c = mix(c, hot * 1.4, smoothstep(0.42, 0.50, uv.y) * (1.0 - smoothstep(0.52, 0.62, uv.y)));
    c = mix(c, ivory * 1.2, smoothstep(0.58, 0.9, uv.y));
    // soft boxes: one wide key strip, one narrow kicker on the other side
    float lon = fract(uv.x);
    float box1 = smoothstep(0.02, 0.0, abs(lon - 0.18) - 0.07) * smoothstep(0.02, 0.0, abs(uv.y - 0.70) - 0.12);
    float box2 = smoothstep(0.01, 0.0, abs(lon - 0.66) - 0.02) * smoothstep(0.02, 0.0, abs(uv.y - 0.55) - 0.22);
    c += vec3(5.0, 4.8, 4.2) * box1 + vec3(4.0, 2.2, 2.8) * box2;
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
