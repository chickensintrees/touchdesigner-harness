// sc_vector_scope: phosphor persistence. Input 0 = this frame's beam light, input 1 = last frame's screen.
// The screen keeps the brighter of the new light and the fading old light; each colour channel
// fades at its own rate, so the afterglow drifts in hue the way a two-layer phosphor does.
// Alpha carries a stamp of the shot that drew the screen: when the stamp changes (a cut), the old
// screen is dropped. An age window was tried first and missed the cut whenever frames were dropped.
out vec4 fragColor;
uniform vec4 uDecay;   // rgb: fraction kept per 1/60 s, w: shot stamp (multiple of 1/255)
uniform vec4 uFrame;   // x: frame time in units of 1/60 s

void main()
{
	vec3 cur = max(texture(sTD2DInputs[0], vUV.st).rgb, 0.0);
	vec4 old = texture(sTD2DInputs[1], vUV.st);
	float same = step(abs(texture(sTD2DInputs[1], vec2(0.5)).a - uDecay.w), 0.4 / 255.0);
	vec3 keep = pow(clamp(uDecay.rgb, 0.0, 0.995), vec3(clamp(uFrame.x, 0.5, 6.0)));
	vec3 prev = clamp(old.rgb, 0.0, 40.0) * keep * same;
	vec3 c = max(cur, prev) + 0.15 * min(cur, prev);
	fragColor = TDOutputSwizzle(vec4(c, uDecay.w));
}
