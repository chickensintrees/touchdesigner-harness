// sc_vector_scope: the glass. Input 0 = phosphor screen, 1 = tight glow, 2 = wide glow.
// POST_MARK_01
out vec4 fragColor;
uniform vec4 uGlow;    // tight amount, wide amount, exposure, white-hot core amount
uniform vec4 uGrat;    // graticule mode (0 none, 1 grid, 2 polar), brightness, invert (0/1), bezel (0/1)
uniform vec4 uGratCol; // rgb graticule / screen tint
uniform vec4 uLive;    // pulse, hit_high, energy, time

const float ASPECT = 1.7777778;

float lineAt(float v, float w) { return 1.0 - smoothstep(0.0, w, abs(v)); }

float graticule(vec2 p, int mode)
{
	// p: x in -ASPECT..ASPECT, y in -1..1
	float px = 2.0 / 720.0;
	float g = 0.0;
	if (mode == 1)
	{
		float div = 0.25;                                   // 8 divisions high
		vec2 c = (fract(p / div + 0.5) - 0.5) * div;
		g = max(lineAt(c.x, px), lineAt(c.y, px)) * 0.55;
		// ticks on the centre lines
		vec2 t = (fract(p / (div * 0.2) + 0.5) - 0.5) * div * 0.2;
		g = max(g, lineAt(t.x, px) * step(abs(p.y), 0.022));
		g = max(g, lineAt(t.y, px) * step(abs(p.x), 0.022));
		g = max(g, max(lineAt(p.x, px * 1.3), lineAt(p.y, px * 1.3)) * 0.9);
	}
	else if (mode == 2)
	{
		float r = length(p);
		float ring = (fract(r / 0.3 + 0.5) - 0.5) * 0.3;
		g = lineAt(ring, px) * 0.6 * step(r, 0.95);
		float a = atan(p.y, p.x);
		float sp = (fract(a / (3.14159265 / 4.0) + 0.5) - 0.5) * (3.14159265 / 4.0) * r;
		g = max(g, lineAt(sp, px) * 0.6 * step(0.05, r) * step(r, 0.95));
		float tk = (fract(a / (3.14159265 / 36.0) + 0.5) - 0.5) * (3.14159265 / 36.0) * r;
		g = max(g, lineAt(tk, px) * step(0.86, r) * step(r, 0.9));
	}
	return g;
}

void main()
{
	vec2 uv = vUV.st;
	vec2 p = (uv * 2.0 - 1.0) * vec2(ASPECT, 1.0);
	vec3 scr = texture(sTD2DInputs[0], uv).rgb;
	vec3 g1 = texture(sTD2DInputs[1], uv).rgb;
	vec3 g2 = texture(sTD2DInputs[2], uv).rgb;
	vec3 light = scr + g1 * uGlow.x + g2 * uGlow.y;
	light *= uGlow.z * (1.0 + 0.25 * uLive.x);
	// a saturated phosphor still goes white where the beam dwells
	float peak = max(light.r, max(light.g, light.b));
	light += vec3(max(peak - 1.0, 0.0)) * uGlow.w;
	vec3 col = 1.0 - exp(-light);

	int mode = int(uGrat.x + 0.5);
	float gr = graticule(p, mode);
	// the graticule is etched in the glass: dim on its own, lit by the glow passing behind it
	float lum2 = dot(g2, vec3(0.3, 0.6, 0.1)) * uGlow.z;
	col += uGratCol.rgb * gr * uGrat.y * (0.35 + 2.5 * min(lum2, 1.0));
	// a breath of the tube's own colour, strongest in the middle
	col += uGratCol.rgb * 0.018 * (1.0 - 0.6 * dot(p, p) / 4.0) * (0.6 + uLive.z);

	if (uGrat.z > 0.5)
	{	// negative: a lit screen with the beam cut out of it
		float l = max(col.r, max(col.g, col.b));
		vec3 paper = uGratCol.rgb * (0.82 - 0.25 * dot(p, p) / 4.0);
		col = paper * (1.0 - smoothstep(0.08, 0.75, l)) + col * 0.06;
	}
	if (uGrat.w > 0.5)
	{	// rounded tube face
		vec2 d = abs(p) - vec2(ASPECT - 0.16, 1.0 - 0.16);
		float sd = length(max(d, 0.0)) - 0.12;
		col *= 1.0 - smoothstep(-0.01, 0.02, sd);
	}
	// fine grain so the black is not dead
	float n = fract(sin(dot(gl_FragCoord.xy + uLive.w * 60.0, vec2(12.9898, 78.233))) * 43758.5453);
	col += (n - 0.5) * 0.012;
	fragColor = TDOutputSwizzle(vec4(max(col, 0.0), 1.0));
}
