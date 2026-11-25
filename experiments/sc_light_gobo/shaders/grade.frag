// Grade: glow, tone map to deep blacks, grain; optional 1-bit dither (the game's look).
// Inputs: 0 = HDR beam image, 1 = blurred quarter-size copy, 2 = caption strip (Describe mode only).
uniform vec4 uMisc;     // x seed, y shot age, z exposure, w 1-bit amount
uniform vec4 uTime;     // x time
uniform vec4 uDesc;     // x 1 = Describe on: draw the caption strip, y strip height, z left margin, w strip width, as fractions of the frame
out vec4 fragColor;

float hash21(vec2 p)
{
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float bayer4(vec2 p)
{
	ivec2 i = ivec2(mod(p, 4.0));
	int b[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
	return (float(b[i.y * 4 + i.x]) + 0.5) / 16.0;
}

void main()
{
	vec2 uv = vUV.st;
	vec3 c = texture(sTD2DInputs[0], uv).rgb;
	vec3 gl = texture(sTD2DInputs[1], uv).rgb;
	c += gl * 0.35;
	c *= uMisc.z;
	// filmic shoulder, toe pulled down so the blacks stay black
	float m = max(c.r, max(c.g, c.b)) + 1e-5;
	float mt = pow(m / (m + 0.6), 1.25);
	c = c / m * mt;                                   // curve on the peak channel: colour survives
	c = mix(c, vec3(mt), smoothstep(0.55, 1.0, mt) * 0.75);   // only the hottest cores bleach
	c = pow(c, vec3(1.0 / 2.2));
	c = max(c - 0.02, 0.0) * 1.03;
	vec2 q = uv - 0.5;
	c *= 1.0 - 0.55 * dot(q, q);
	c += (hash21(gl_FragCoord.xy + fract(uTime.x) * 91.7) - 0.5) * 0.018;
	if (uMisc.w > 0.5) {
		float l = dot(c, vec3(0.3, 0.55, 0.15));
		vec2 px = floor(gl_FragCoord.xy / 2.0);
		c = vec3(step(bayer4(px), pow(l, 1.7) * 1.25));
	}
	if (uDesc.x > 0.5) {                              // Describe: a caption along the bottom, on a darkened band
		float band = 1.0 - smoothstep(uDesc.y * 0.9, uDesc.y * 1.3, uv.y);
		if (uMisc.w > 0.5) band = step(uv.y, uDesc.y * 1.05) / 0.72;          // 1-bit take: a solid black band
		c *= 1.0 - 0.72 * band;
		float cx = (uv.x - uDesc.z) / uDesc.w;
		float a = (uv.y < uDesc.y && cx > 0.0 && cx < 1.0) ? texture(sTD2DInputs[2], vec2(cx, uv.y / uDesc.y)).r : 0.0;
		if (uMisc.w > 0.5) a = step(0.5, a);
		c = mix(c, uMisc.w > 0.5 ? vec3(1.0) : vec3(0.93, 0.92, 0.86), a);
	}
	fragColor = TDOutputSwizzle(vec4(max(c, 0.0), 1.0));
}
