// Palette pass: the render holds weights (r ink, g accent, b third); the take's colours come from sPar.
uniform vec4 uTime;    // beat_pos, bar_pos, local beats, age
uniform vec4 uHits;    // hit_low, hit_mid, hit_high, pulse
uniform vec4 uState;   // energy, section, seed, layout index
uniform vec4 uMisc;    // bar_pulse, evolve, hits_high, take
uniform vec4 uInp;     // 1 while the COMP's Input names a TOP (input 2), else 0 and the colours below are untouched
out vec4 fragColor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }

const vec3 LUMA = vec3(0.299, 0.587, 0.114);
// two flat colours and a line coverage: the lighter colour takes the lines, so a bright picture stays bright
vec3 tone(vec3 a, vec3 b, float line) { return dot(b, LUMA) > dot(a, LUMA) ? mix(a, b, line) : mix(b, a, line); }

void main()
{
	vec2 uv = vUV.st;
	vec4 r = texture(sTD2DInputs[0], uv);
	int take = int(uMisc.w + 0.5);
	int po = fract(uState.z * 3.0) > 0.5 ? 6 : 1;                 // the seed picks the take's first or second palette
	vec3 bg = texelFetch(sTD2DInputs[1], ivec2(po, take), 0).rgb;
	vec3 ink = texelFetch(sTD2DInputs[1], ivec2(po + 1, take), 0).rgb;
	vec3 acc = texelFetch(sTD2DInputs[1], ivec2(po + 2, take), 0).rgb;
	vec3 third = texelFetch(sTD2DInputs[1], ivec2(po + 3, take), 0).rgb;
	vec4 fx = texelFetch(sTD2DInputs[1], ivec2(5, take), 0);

	float wI = r.r, wA = r.g, wT = r.b;
	float wB = clamp(1.0 - wI - wA - wT, 0.0, 1.0);

	// inversions: ink and ground change places
	float inv = 0.0;
	int st = int(fx.y + 0.5);
	if (st == 1) {
		// a band sweeps across the frame once per bar
		float f = fract(uTime.y);
		float x0 = -0.3 + 1.6 * f;
		inv = step(x0, uv.x) * step(uv.x, x0 + 0.22);
	} else if (st == 2) {
		// snare: the whole card flips for the length of the hit
		inv = step(0.45, uHits.y);
	} else if (st == 3) {
		// the frame below a line that rises through the bar
		inv = step(uv.y, fract(uTime.y * 0.5) * 1.02 - 0.01);
	}
	if (fx.z > 0.5 && fract(uState.z * 5.0) > 0.55) inv = 1.0 - inv;      // some shots are negatives
	if (inv > 0.5) { float tmp = wI; wI = wB; wB = tmp; }

	// Input, takes of kind 1 and 2 (sPar column 11): the picture is printed inside the type as a line screen in two
	// of the take's flat colours. Lines thicken where the picture is bright, hop one period a beat, swell on kicks.
	// IN.x says where: 1 in the ink, 2 in the third colour (the big numerals), 5 in the accent (echo's front word),
	// 6 nowhere in the type. IN.y is the line period. IN.w is how strongly the same screen also tints the ground.
	vec4 IN = texelFetch(sTD2DInputs[1], ivec2(11, take), 0);
	if (uInp.x > 0.5 && IN.x > 0.5) {
		int kind = int(IN.x + 0.5);
		vec3 pic = texture(sTD2DInputs[2], uv).rgb;
		float l = smoothstep(0.04, 0.7, dot(pic, LUMA));
		float per = max(IN.y, 2.0);
		float bf = fract(uTime.x);
		float y = uv.y * 720.0 + per * (floor(uTime.x) + 1.0 - pow(1.0 - bf, 5.0));
		float d = abs(fract(y / per) - 0.5) * per;
		float line = clamp(0.5 * l * per * (1.0 + 0.35 * min(uHits.x, 1.0)) - d + 0.5, 0.0, 1.0) * smoothstep(0.0, 0.12, l);
		// the ground's tint is whichever of ink and accent stands further from it
		vec3 tint = distance(bg, acc) > distance(bg, ink) ? acc : ink;
		vec3 ink0 = ink, acc0 = acc;
		if (kind == 1) ink = tone(ink0, acc0, line);
		if (kind == 2) third = tone(third, acc0, line);
		if (kind == 5) acc = tone(acc0, ink0, line);
		if (IN.w > 0.0) {
			bg = tone(bg, mix(bg, tint, IN.w), line);
			if (kind == 1) third = tone(third, mix(third, tint, IN.w), line);
		}
	}

	vec3 c = bg * wB + ink * wI + acc * wA + third * wT;
	c += (hash(uv * vec2(1280.0, 720.0) + fract(uTime.x) * 91.0) - 0.5) * 0.018;   // a little tooth
	fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
