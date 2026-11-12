// sc_exploded_view: phosphor halo for the dark sheets (0 on paper), breathing with the beat.
// inputs: 0 the drawing, 1 the drawing blurred at quarter size
uniform vec4 uGlow;     // x amount, y pulse, z hit_mid
out vec4 fragColor;
void main()
{
	vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
	vec3 g = texture(sTD2DInputs[1], vUV.st).rgb;
	c += uGlow.x * (0.75 + 0.6 * uGlow.y + 0.5 * uGlow.z) * g;
	fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
