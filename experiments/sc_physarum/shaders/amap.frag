// Attractant map: what the mould is looking for in this take.
// inputs: 0 text, or the scene's Input picture when uIn.x is 1; 1 X-ray render of a library model; 2 printed sheet
// out: r attract 0..1, g wall (agents avoid, trail dies), b auxiliary picture for the display (paper tone, ghost)
uniform vec4 uMap;  // x source (0 noise, 1 text, 2 model, 3 sheet, 4 dishes, 5 mirrored island), y evolve, z seed, w section
uniform vec4 uCtr;  // xy subject centre (uv), z strength of its far scent, w reach
uniform vec4 uXf;   // x zoom, y rotation, z offset x, w offset y
uniform vec4 uIn;   // x 1 when input 0 is a picture from another scene, y size of that picture where a prop was
out vec4 fragColor;

const float ASPECT = 16.0 / 9.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

vec2 xf(vec2 uv)
{
	vec2 q = (uv - 0.5) * vec2(ASPECT, 1.0);
	float c = cos(uXf.y), s = sin(uXf.y);
	q = mat2(c, -s, s, c) * q / uXf.x;
	return q / vec2(ASPECT, 1.0) + 0.5 + uXf.zw;
}

float inside(vec2 p)
{
	vec2 d = step(vec2(0.0), p) * step(p, vec2(1.0));
	return d.x * d.y;
}

// ---- a picture given through the scene's Input parameter, as food ----
float lumAt(vec2 p) { return dot(texture(sTD2DInputs[0], p).rgb, vec3(0.299, 0.587, 0.114)); }

// bright parts are food and edges are richer food, so the veins draw the picture's outlines first
float pic(vec2 p)
{
	vec2 e = vec2(2.0 / 1280.0, 2.0 / 720.0);
	float l = lumAt(p);
	float gx = lumAt(p + vec2(e.x, 0.0)) - lumAt(p - vec2(e.x, 0.0));
	float gy = lumAt(p + vec2(0.0, e.y)) - lumAt(p - vec2(0.0, e.y));
	float edge = smoothstep(0.04, 0.30, length(vec2(gx, gy)));
	// brighter than its surroundings counts for more than plain brightness, so a bright figure on a
	// bright ground (white type on a lit disc) still stands out as food
	vec2 w = e * 14.0;
	float mean = 0.25 * (lumAt(p + vec2(w.x, w.y)) + lumAt(p - vec2(w.x, w.y)) + lumAt(p + vec2(w.x, -w.y)) + lumAt(p + vec2(-w.x, w.y)));
	float local = smoothstep(0.03, 0.30, l - mean);
	return clamp(0.40 * smoothstep(0.10, 0.80, l) + 0.45 * local + 0.45 * edge, 0.0, 1.0) * inside(p);
}

void main()
{
	vec2 uv = vUV.st;
	float mode = uMap.x;
	bool given = uIn.x > 0.5;
	float attract = 0.0, wall = 0.0, aux = 0.0;
	if (mode < 0.5)
	{
		// slow ridged noise: just enough to give the network a grain to follow
		vec2 q = (uv - 0.5) * vec2(ASPECT, 1.0) * 2.2 + uMap.z * 17.0;
		float n = TDSimplexNoise(vec3(q, uMap.y * 0.05));
		n += 0.5 * TDSimplexNoise(vec3(q * 2.3 + 5.0, uMap.y * 0.07));
		attract = 0.55 * (1.0 - smoothstep(0.0, 0.25, abs(n)));
		aux = n;
		if (given)
			attract = pic(uv);
	}
	else if (mode < 1.5)
	{
		vec2 p = xf(uv);
		attract = given ? pic(p) : texture(sTD2DInputs[0], p).r * inside(p);
		aux = attract;
	}
	else if (mode < 2.5)
	{
		float x = texture(sTD2DInputs[1], uv).r;
		attract = 1.0 - exp(-x * 1.6);
		if (given)
		{
			// the picture stands where the prop stood: full frame, or small and off-centre like the prop
			vec2 c = uIn.y < 0.99 ? uCtr.xy : vec2(0.5);
			attract = pic((uv - c) / uIn.y + 0.5);
		}
		aux = attract;
		// a scent that reaches across the frame, so a small subject can be found from far away
		vec2 d = (uv - uCtr.xy) * vec2(ASPECT, 1.0);
		attract = max(attract, uCtr.z / (1.0 + dot(d, d) / (uCtr.w * uCtr.w)));
	}
	else if (mode < 3.5)
	{
		// the sheet covers the frame; its ink is the food
		vec2 q = (uv - 0.5) * vec2(ASPECT, 1.0);
		float c = cos(uXf.y), s = sin(uXf.y);
		q = mat2(c, -s, s, c) * q / uXf.x;
		vec2 p = q / vec2(given ? ASPECT : 1.2917, 1.0) + 0.5 + uXf.zw;
		p.y = 1.0 - p.y;
		vec3 f = texture(sTD2DInputs[2], vec2(p.x, 1.0 - p.y)).rgb;
		float lum = dot(f, vec3(0.299, 0.587, 0.114));
		float in_ = inside(p);
		if (given)
			lum = 1.0 - pic(vec2(p.x, 1.0 - p.y));   // the picture photocopied onto the sheet: its bright parts are the ink
		attract = (1.0 - smoothstep(0.30, 0.78, lum)) * in_;
		wall = 1.0 - in_;
		aux = mix(0.0, lum, in_);
	}
	else if (mode > 4.5)
	{
		// an island of blotchy food, the same on both sides of the centre line (the display mirrors it)
		vec2 q = (uv - 0.5) * vec2(ASPECT, 1.0);
		q.x = abs(q.x);
		float d = length(q * vec2(0.72, 1.0));
		float n = TDSimplexNoise(vec3(q * 3.2 + uMap.z * 17.0 + uMap.w * 3.1, uMap.y * 0.04));
		n += 0.5 * TDSimplexNoise(vec3(q * 7.0 + 9.0 + uMap.w, uMap.y * 0.05));
		attract = smoothstep(-0.25, 0.45, n) * (1.0 - smoothstep(0.24, 0.40, d));
		if (given)
			attract = pic(uv) * (1.0 - smoothstep(0.24, 0.40, d));
		wall = smoothstep(0.40, 0.44, d);
		aux = n;
	}
	else
	{
		// culture dishes in a grid that tiles the frame; the mould cannot leave its dish
		float pick = floor(fract(uMap.z * 7.31) * 3.0);
		vec2 n = pick < 0.5 ? vec2(4.0, 2.0) : pick < 1.5 ? vec2(5.0, 3.0) : vec2(7.0, 4.0);
		vec2 g = uv * n;
		vec2 id = mod(floor(g), n);
		vec2 f = (fract(g) - 0.5) * vec2(ASPECT / n.x, 1.0 / n.y);
		float r0 = 0.5 * min(ASPECT / n.x, 1.0 / n.y);
		float kind = hash(id + floor(uMap.z * 91.0) + uMap.w * 3.0);
		float rad = 0.84 + 0.08 * hash(id + 3.0);
		float d = length(f) / r0;
		float in_ = 1.0 - smoothstep(rad - 0.03, rad, d);
		wall = 1.0 - in_;
		// what was inoculated: one dot, two dots, a streak, or nothing (a sterile dish)
		vec2 o = (vec2(hash(id + 7.0), hash(id + 9.0)) - 0.5) * 0.5 * r0;
		float dot1 = (1.0 - smoothstep(0.05, 0.13, length(f - o) / r0));
		float dot2 = (1.0 - smoothstep(0.04, 0.11, length(f + o * 1.4) / r0));
		float streak = (1.0 - smoothstep(0.02, 0.05, abs(f.y * 0.8 + f.x * (kind - 0.5)) / r0)) * step(d, 0.6);
		float food = kind < 0.4 ? dot1 : kind < 0.62 ? max(dot1, dot2) : kind < 0.85 ? streak : 0.0;
		float t = given ? 2.0 * pic(xf(uv)) : texture(sTD2DInputs[0], xf(uv)).r;
		attract = in_ * max(food, 0.5 * t);
		aux = d / rad;
	}
	fragColor = TDOutputSwizzle(vec4(attract, wall, aux, 1.0));
}
