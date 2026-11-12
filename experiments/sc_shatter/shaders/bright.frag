// highlights only, for the glow
uniform vec4 uThr;   // x threshold
out vec4 fragColor;
void main()
{
	vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
	c = max(c - uThr.x, 0.0);
	c = min(c, vec3(8.0));
	fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
