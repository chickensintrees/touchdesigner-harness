// Prepares a picture given through the COMP's Input parameter (another scene's output)
// to stand in for this scene's clean source. Most takes take it as it is; the 1-bit take
// gets it Bayer-dithered (so the mosh pushes dither dots around and the final threshold
// keeps a picture), and the void take gets it crushed to near black in the shot's one hot
// colour (so only its lights grow into rising columns).
// Input: 0 the given picture, any size.
uniform vec4 uI;   // x source mode of the take (see TAKES in build.py), y seed 0..1
out vec4 fragColor;

float hash(float n) { return fract(sin(n * 12.9898 + 4.1414) * 43758.5453); }
float lum(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

float bayer4(vec2 f)
{
    int x = int(mod(f.x, 4.0)), y = int(mod(f.y, 4.0));
    int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
    return (float(m[y * 4 + x]) + 0.5) / 16.0;
}

void main()
{
    vec3 c = clamp(texture(sTD2DInputs[0], vUV.st).rgb, 0.0, 1.0);
    int mode = int(uI.x + 0.5);
    float sd = uI.y;
    if (mode == 4) {
        float v = step(bayer4(floor(gl_FragCoord.xy / 3.0)), pow(lum(c), 0.8) * 1.1);
        if (hash(sd * 19.0) < 0.4) v = 1.0 - v;          // the same whole-frame inversion the take uses
        c = vec3(v);
    } else if (mode == 5) {
        int hk = int(mod(floor(sd * 25.0), 5.0));         // the take's hot colour
        vec3 H = hk == 0 ? vec3(1.0, 0.72, 0.22) : hk == 1 ? vec3(0.55, 0.80, 1.0) : hk == 2 ? vec3(1.0, 0.25, 0.18)
               : hk == 3 ? vec3(0.80, 1.0, 0.62) : vec3(1.0, 0.96, 0.86);
        float l = lum(c);
        float k = smoothstep(0.30, 0.80, l);
        c = vec3(0.012, 0.018, 0.030) + mix(H * l, c, 0.35) * k;
    }
    fragColor = TDOutputSwizzle(vec4(clamp(c, 0.0, 1.0), 1.0));
}
