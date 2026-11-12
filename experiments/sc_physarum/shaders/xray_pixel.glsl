in vec3 vN;
out vec4 oFragColor;

void main()
{
	TDCheckDiscard();
	float f = 1.0 - abs(normalize(vN + 1e-6).z);
	f = f * f * f;
	oFragColor = TDOutputSwizzle(vec4(vec3(0.012 + 0.7 * f), 1.0));
}
