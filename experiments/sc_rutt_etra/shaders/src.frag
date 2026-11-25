// Source picture for the scan processor, 640x360. Never shown directly.
// Input 0: lit model render. Input 1: text (repeat-extended). Input 2: spectrum waterfall.
// R: luminance that deflects the beam.  G: text mask (for the keyer).  B: model alpha.
uniform vec4 uMix;   // x model weight, y text weight, z oscillator weight, w time (evolve)
uniform vec4 uTx;    // x text zoom, y text scroll x, z text scroll y, w oscillator frequency
uniform vec4 uMix2;  // x waterfall weight, y text weight in the key channel only
uniform vec4 uAud;   // x bass, y energy, z seed, w beat_pos
uniform vec4 uIn;    // x 1 = input 0 is another scene's picture (the COMP's Input), y its gain, z 1 = it scrolls with the text
out vec4 fragColor;

void main()
{
    vec2 uv = vUV.st;
    vec4 m = texture(sTD2DInputs[0], uv + vec2(uTx.y * uIn.z * step(0.5, uIn.x), 0.0));
    float lm = dot(m.rgb, vec3(0.299, 0.587, 0.114));
    vec2 tuv = (uv - 0.5) / uTx.x + 0.5 + uTx.yz;
    tuv.x = (tuv.x - 0.5) * (640.0 / 384.0) + 0.5;      // the text tile is 384 wide
    float tx = texture(sTD2DInputs[1], tuv).r;

    // voltage-controlled oscillators: two sweeping sines multiplied (ring modulation)
    vec2 p = (uv - 0.5) * vec2(1.7778, 1.0);
    float t = uMix.w;
    float f = uTx.w;
    vec2 c = 0.35 * vec2(sin(t * 0.7 + uAud.z * 6.0), cos(t * 0.5));
    float o1 = sin(length(p - c) * f * 6.2832 - t * 2.0 - uAud.x * 1.5);
    float o2 = sin(p.x * f * 2.5 + sin(p.y * 3.0 + t * 0.9) * 2.0 + uAud.z * 9.0);
    float o = 0.5 + 0.5 * o1 * o2;
    o = o * o;

    float wf = texture(sTD2DInputs[2], clamp(uv, 0.002, 0.998)).r;
    float l = lm * uMix.x + tx * uMix.y + o * uMix.z + wf * uMix2.x;
    float al = m.a * step(0.001, uMix.x);
    if (uIn.x > 0.5) {
        // Input: input 0 is another scene's picture. Its brightness is the whole deflection signal;
        // the oscillators and the spectrum waterfall stay on top at reduced strength, the text drops out.
        l = lm * uIn.y + o * uMix.z * 0.3 + wf * uMix2.x * 0.45;
        al = 1.0;
    }
    fragColor = TDOutputSwizzle(vec4(l, tx * uMix2.y, al, 1.0));
}
