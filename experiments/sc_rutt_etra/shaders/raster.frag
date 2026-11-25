// Beam profile and intensity modulation for one scan line (or black for the hold-out surface).
uniform vec4 uRas;    // w 1 = solid surface
uniform vec4 uCol;    // phosphor colour rgb, w gain
uniform vec4 uCol2;   // colour of the brightest parts rgb, w flash (hit_low)
uniform vec4 uHue;    // x hue spread across the lines (turns), y hue offset, z amount: a chroma oscillator on the line counter
uniform sampler2D sIn;   // the Input picture in colour (black when there is none)
uniform vec4 uIn;     // x how far the beam takes the Input picture's colour (0 with no Input)
uniform vec4 uInt;    // x base intensity, y intensity from source brightness, z beam break-up, w time
in float vSide;
in float vLum;
in float vU;
in float vLine;
in float vSpeed;
in float vFade;
in vec2 vSuv;
out vec4 fragColor;

float hash(float n) { return fract(sin(n * 127.1) * 43758.5453); }
float vnoise(float x)
{
    float i = floor(x); float f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    return mix(hash(i), hash(i + 1.0), f);
}

void main()
{
    TDCheckDiscard();
    if (uRas.w > 0.5) { fragColor = TDOutputSwizzle(vec4(0.0, 0.0, 0.0, 1.0)); return; }
    float prof = exp(-vSide * vSide * 3.2);
    float lum = clamp(vLum, 0.0, 1.5);
    float I = (uInt.x + uInt.y * lum) * mix(1.0, vSpeed, 0.55);
    // break-up: the beam current drops out along the line, smoothly, never in blocks
    float g = vnoise(vU * 34.0 + vLine * 13.7 + uInt.w * 9.0) * vnoise(vU * 7.0 - vLine * 3.1 - uInt.w * 4.0);
    I *= mix(1.0, smoothstep(0.12, 0.38, g) * 1.5, clamp(uInt.z, 0.0, 1.0));
    I *= 1.0 + uCol2.w;
    vec3 ph = uCol.rgb;
    if (uHue.z > 0.001) {
        float h = vLine / max(uRas.x, 1.0) * uHue.x + uHue.y;
        vec3 rb = 0.5 + 0.5 * cos(6.2832 * (h + vec3(0.0, 0.33, 0.67)));
        ph = mix(ph, rb * rb * 1.3 + 0.03, uHue.z);
    }
    float hold = uHue.z;
    if (uIn.x > 0.001) {
        // Input: the beam takes the hue of the picture under it, kept bright (a colour camera on the scan processor)
        vec3 ic = max(textureLod(sIn, vSuv, 0.0).rgb, 0.0);
        vec3 tint = ic / max(max(ic.r, max(ic.g, ic.b)), 0.08);
        ph = mix(ph, tint * tint * 1.15 + 0.03, uIn.x);
        hold = max(hold, uIn.x);
    }
    vec3 col = mix(ph, uCol2.rgb, smoothstep(0.25, 0.95, lum) * (1.0 - 0.65 * hold)) * I * prof * uCol.w * vFade;
    if (any(isnan(col)) || any(isinf(col))) col = vec3(0.0);
    fragColor = TDOutputSwizzle(vec4(col, prof));
}
