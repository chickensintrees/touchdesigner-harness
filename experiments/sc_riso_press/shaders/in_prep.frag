// in_prep.frag: makes a picture from another scene (COMP par Input) look like the
// three-light render that sep.frag expects: rgb = three "lightings", a = coverage.
// Green and red are swapped so the default pink plate (which reads channel 0 and inks the
// shade) prints where green is missing and the teal plate where red is missing: a rough
// magenta / cyan / yellow separation. Blacks are lifted so a dark picture prints as heavy
// dots, not as three solid floods. see: experiments/sc_riso_press/NOTES.md (2026-11-11)
uniform vec4 uPrep;    // black lift, gamma
out vec4 fragColor;
void main() {
    vec3 c = clamp(texture(sTD2DInputs[0], vUV.st).rgb, 0.0, 1.0).grb;
    c = uPrep.x + (1.0 - uPrep.x) * pow(c, vec3(max(uPrep.y, 0.05)));
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
