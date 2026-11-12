// Once per frame: press the stamp into the chemistry and age the ink memory.
// State (input 0): R = 1-U (so black is the rest state), G = V,
// B = trace (where the living ink has recently been),
// A = impression (the flat stamped ink: set on a section change, re-inked by kicks, fades).
// Input 1: stamp mask (R), and in A which part of it a kick presses this time.
uniform vec4 uStamp;  // hold (0/1), kick amount, trace decay, impression decay
uniform vec4 uBoot;   // x = 1 on the first frames of a shot or after the scene was not cooking,
                      // y = 1 when an Input picture is the stamp: the impression then follows it every frame
out vec4 fragColor;

void main() {
    vec4 c = texture(sTD2DInputs[0], vUV.st);
    vec4 st = texture(sTD2DInputs[1], vUV.st);
    float m = st.r;
    // Cutting to the scene: whatever is in the loop is stale (or nothing), so start
    // a clean sheet and stamp the current phrase in this one frame.
    c *= 1.0 - uBoot.x;
    float hold = max(uStamp.x, uBoot.x);
    // A kick presses the phrase again, as hard as the hit. sim.frag keeps the
    // coral outside the strokes, so refilling the strokes no longer resets it.
    float kick = clamp(uStamp.y, 0.0, 1.0) * st.a;
    float press = m * max(hold, 0.75 * kick);

    c.g = max(c.g, press);            // V poured in
    c.r = max(c.r, press * 0.85);     // U displaced
    // impression: the old phrase is lifted off while the new one is held down
    float old = c.a * mix(uStamp.w, 0.80, uStamp.x);
    // a moving Input picture walks away from where it was stamped, and in a loud passage the
    // coral then buries it (captures/i5_2_loud.png): keep a flat print of where it is now,
    // with a short trail. Both lines change nothing when uBoot.y is 0.
    old *= mix(1.0, 0.93, uBoot.y);
    c.a = max(old, max(max(m * hold, m * kick * 0.9), m * uBoot.y * 0.85));
    c.b = max(c.b * uStamp.z, smoothstep(0.12, 0.3, c.g));
    fragColor = TDOutputSwizzle(c);
}
