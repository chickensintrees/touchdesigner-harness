// Trail map: diffuse, decay, add this frame's deposit.
// inputs: 0 previous trail, 1 deposit render, 2 attractant map
// out: r trail, g slow memory of the trail (stain), b flight glow (rings), a agents on this pixel this frame
uniform vec4 uTrail;  // x diffuse 0..1, y decay on the attractant, z deposit gain, w decay off the attractant
uniform vec4 uTrail2; // x memory decay, y boot (clear), z deposit boost on the attractant, w wall kill
out vec4 fragColor;

void main()
{
	vec2 uv = vUV.st;
	vec2 px = uTD2DInfos[0].res.xy;
	vec4 c = texture(sTD2DInputs[0], uv);
	vec3 sum = vec3(0.0);
	for (int j = -1; j <= 1; j++)
		for (int i = -1; i <= 1; i++)
			sum += texture(sTD2DInputs[0], uv + vec2(i, j) * px).rgb;
	sum /= 9.0;
	vec4 dep = texture(sTD2DInputs[1], uv);
	vec4 a = texture(sTD2DInputs[2], uv);
	float on = clamp(a.r, 0.0, 1.0);
	float decay = mix(uTrail.w, uTrail.y, on) * (1.0 - uTrail2.w * clamp(a.g, 0.0, 1.0));
	float r = mix(c.r, sum.r, uTrail.x) * decay + dep.r * uTrail.z * (1.0 + uTrail2.z * on);
	r = min(r, 40.0);
	float g = max(c.g * uTrail2.x, 1.0 - exp(-r * 0.35));
	float b = sum.b * 0.62 + dep.g;
	if (uTrail2.y > 0.5)
	{
		r = 0.0; g = 0.0; b = 0.0;
	}
	fragColor = TDOutputSwizzle(vec4(r, g, b, dep.a));   // a: the agents themselves, this frame
}
