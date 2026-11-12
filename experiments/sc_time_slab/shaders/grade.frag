// Input 0: the resampled slab (after bloom in the dark grades).
// Grades (uB.x): 0 stark dark studio, 1 daylight (paper white, no crush),
// 2 one-bit ordered dither, black and white (uB.y > 0.5 inverts it).
uniform vec4 uA;   // pulse, energy, hit_high, evolve
uniform vec4 uB;   // grade, s3, shot age in seconds, 0
out vec4 fragColor;

float bayer4(vec2 p)
{
    int x = int(mod(p.x, 4.0)), y = int(mod(p.y, 4.0));
    int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
    return (float(m[x + y * 4]) + 0.5) / 16.0;
}

void main()
{
    vec2 uv = vUV.st;
    float pulse = uA.x, energy = uA.y, hh = uA.z;
    int grade = int(uB.x + 0.5);
    vec3 col = max(texture(sTD2DInputs[0], uv).rgb, 0.0);
    vec2 q = uv - 0.5;
    // every shot arrives with a short flare
    float arrive = exp(-uB.z * 9.0);

    if (grade == 2) {
        float l = dot(col, vec3(0.299, 0.587, 0.114));
        l = pow(clamp(l * (1.25 + 0.25 * pulse) + 0.5 * arrive, 0.0, 1.0), 0.8);
        float b = step(bayer4(floor(gl_FragCoord.xy / 2.0)), l);
        if (uB.y > 0.5) b = 1.0 - b;
        col = vec3(b);
    } else if (grade == 1) {
        // daylight: gentle shoulder, warm paper white, a little cool in the shadows
        col = col * (1.0 + 0.10 * pulse + 0.6 * arrive);
        col = col / (1.0 + 0.18 * col) * 1.18;
        float l = dot(col, vec3(0.299, 0.587, 0.114));
        col = mix(col * vec3(0.90, 0.97, 1.04), col * vec3(1.03, 1.0, 0.93), smoothstep(0.1, 0.8, l));
        col *= 1.0 - 0.45 * dot(q, q);
    } else {
        // stark studio: an S-curve that holds the blacks down, a trace of ink-green in
        // the deepest shadows, cream highlights
        col = col * col * (3.0 - 2.0 * min(col, 1.0)) * 0.55 + col * 0.55;
        float l = dot(col, vec3(0.299, 0.587, 0.114));
        vec3 shadow = vec3(0.006, 0.012, 0.010);
        vec3 hi = vec3(1.04, 0.99, 0.86);
        col = shadow * (1.0 - min(l, 1.0)) + col * hi;
        col *= 1.0 + 0.10 * pulse + 0.9 * arrive;
        col *= 1.0 - 0.9 * dot(q, q);
        col *= 0.98 + 0.02 * sin(uv.y * 720.0 * 3.14159);
        col += hh * 0.02;
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
