// sc_shatter: glow, tone map, grade. Input 0: comp (linear), input 1: blurred highlights.
uniform vec4 uPost;    // x exposure, y glow amount, z vignette, w mode (0 colour, 1 one-bit dither, 2 one-bit inverted)
uniform vec4 uBeat;    // x hit_low, y pulse, z t (for grain), w saturation
uniform vec4 uDesc;    // x 1 = Describe on, y caption width (px), zw caption strip size (px)
out vec4 fragColor;

// Describe caption: a dark plate bottom left with the take's two lines (input 2) in white.
// Returns the picture unchanged when Describe is off.
vec3 caption(vec3 c, bool onebit)
{
	if (uDesc.x < 0.5)
		return c;
	vec2 p = gl_FragCoord.xy;
	vec2 org = vec2(24.0, 22.0);                       // plate corner
	vec2 pad = vec2(14.0, 4.0);
	vec2 q = p - org;
	vec2 size = vec2(uDesc.y + 2.0 * pad.x, uDesc.w + 2.0 * pad.y);
	if (q.x < 0.0 || q.y < 0.0 || q.x > size.x || q.y > size.y)
		return c;
	vec2 tuv = (q - pad) / uDesc.zw;
	float a = 0.0;
	if (tuv.x > 0.0 && tuv.x < 1.0 && tuv.y > 0.0 && tuv.y < 1.0)
		a = texture(sTD2DInputs[2], tuv).a;
	if (onebit)
		return vec3(step(0.45, a));
	return mix(mix(c, vec3(0.035, 0.04, 0.05), 0.86), vec3(0.97, 0.95, 0.9), a);
}

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }

float bayer4(ivec2 p)
{
	int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
	return (float(m[(p.x & 3) + ((p.y & 3) << 2)]) + 0.5) / 16.0;
}

vec3 filmic(vec3 x)
{
	// Hable-style curve applied on luminance-preserving mix so saturated reds stay red
	vec3 a = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14);
	return clamp(a, 0.0, 1.0);
}

void main()
{
	vec2 uv = vUV.st;
	vec3 c = texture(sTD2DInputs[0], uv).rgb;
	vec3 g = texture(sTD2DInputs[1], uv).rgb;
	c += g * uPost.y;
	c *= uPost.x * (1.0 + 0.10 * uBeat.x);
	vec2 d = uv - 0.5;
	c *= 1.0 - uPost.z * dot(d, d) * 1.6;
	int mode = int(uPost.w + 0.5);
	if (mode >= 1)
	{
		float l = dot(c, vec3(0.3, 0.6, 0.1));
		ivec2 px = ivec2(gl_FragCoord.xy) / 2;
		float b = step(bayer4(px), clamp(l, 0.0, 1.0) * 0.98 + 0.01);
		if (mode == 2) b = 1.0 - b;
		fragColor = TDOutputSwizzle(vec4(caption(vec3(b), true), 1.0));
		return;
	}
	float l0 = dot(c, vec3(0.2126, 0.7152, 0.0722));
	vec3 t = filmic(c);
	// keep hue: tone map the luminance too and mix
	vec3 t2 = c * (filmic(vec3(l0)).x / max(l0, 1e-4));
	t = mix(t, clamp(t2, 0.0, 1.0), 0.35);
	float l1 = dot(t, vec3(0.2126, 0.7152, 0.0722));
	t = mix(vec3(l1), t, uBeat.w);
	t = pow(max(t, 0.0), vec3(1.0 / 2.2));
	t += (hash(uv * vec2(1280.0, 720.0) + fract(uBeat.z) * 91.0) - 0.5) * 0.018;
	fragColor = TDOutputSwizzle(vec4(caption(t, false), 1.0));
}
