// sc_vector_scope: where the beam is. One texel = one beam sample; 4096 samples per gun,
// stored 1024 wide x 4 rows, up to 8 guns stacked. Output: x, y (screen units, y in -1..1),
// pen (0..1 brightness factor), gun-local parameter u.
// Input 0: baked shape paths (1024 x 4*ROWS: xyz + pen). Input 1: this frame's audio, 800 x 1 (r = left, g = right).
// Input 2: a small picture (text or a lit model) that the scan take displaces its raster with; black on other takes.
// Describe mode: the take's rows are swapped for baked rows of words that explain it, and takes with no
// words of their own get one more gun (the last) that draws a small label. Input: when the scene is given
// a picture, input 2 carries it (512 x 288) and uIn.x says how this take uses it.
// PATH_MARK_31
out vec4 fragColor;

uniform vec4 uGroup;   // first row, row count, stride between guns, number of guns
uniform vec4 uGroup2;  // alt group first row, alt count, use alt every n-th step (0 never), kind
uniform vec4 uStep;    // beats per shape, seed, shot age (s), beat_pos
uniform vec4 uXform;   // scale, offset x, offset y, roll
uniform vec4 uRot;     // yaw speed, tilt, perspective, section index
uniform vec4 uAud;     // gain, smoothing (samples), window span, level (live)
uniform vec4 uHit;     // spring low, spring mid, hit_high, pulse
uniform vec4 uTrace;   // drawn fraction (1 = whole path), head speed (laps per beat), dissolve beats, dissolve gain
uniform vec4 uTime;    // evolve, bar_pos, energy, section kick (1 at a section change, gone in about 0.4 s)
uniform vec4 uDesc;    // Describe label gun: first row, row count (0 = no label gun), size, brightness
uniform vec4 uDescB;   // Describe label gun: x, y; z = 1 when Describe is on; w = 1: the whole take holds still on hits
uniform vec4 uDescC;   // the gonio/timebase/waterfall label word: size x, brightness x, offset x and y multipliers (all 1 normally)
uniform vec4 uIn;      // x: 1 when there is an Input picture and this take uses it (scan, timebase, waterfall)

const float N = 4096.0;
const float PI = 3.14159265;
const float ASPECT = 1.7777778;

float hash1(float n) { return fract(sin(n * 127.1 + 3.7) * 43758.5453); }

vec4 shape(float row, float i)
{
	int ii = int(i);
	return texelFetch(sTD2DInputs[0], ivec2(ii & 1023, (ii >> 10) + 4 * int(row)), 0);
}

vec2 audioAt(float u, float smoothing)
{
	float w = float(textureSize(sTD2DInputs[1], 0).x);
	vec2 acc = vec2(0.0);
	float tot = 0.0;
	for (int j = -4; j <= 4; j++)
	{
		float k = exp(-float(j * j) / 6.0);
		float x = (u * (w - 1.0 - 8.0 * smoothing) + 4.0 * smoothing + float(j) * smoothing + 0.5) / w;
		acc += texture(sTD2DInputs[1], vec2(x, 0.5)).rg * k;
		tot += k;
	}
	return acc / tot;
}

vec2 stereoFigure(float u, float r)
{
	vec2 now = audioAt(u, 0.0), late = audioAt(u - 0.012 - 0.02 * r, 0.0);
	float mid = (now.x + now.y) * 0.5, side = (now.x - now.y) * 0.5, midLate = (late.x + late.y) * 0.5;
	return vec2(side * 3.5 + midLate * 1.15, mid);
}

float pmod(float a, float b) { return a - b * floor(a / b); }

// which baked row a gun shows at a given step
float rowFor(float step, float gun, float seedI)
{
	float alt = uGroup2.z;
	if (alt > 0.5 && pmod(step, alt) > alt - 1.5)
		return uGroup2.x + pmod(seedI + floor(step / alt) + gun * 3.0, uGroup2.y);
	return uGroup.x + pmod(seedI + step + gun * uGroup.z, uGroup.y);
}

vec3 rotY(vec3 p, float a) { float c = cos(a), s = sin(a); return vec3(c * p.x + s * p.z, p.y, -s * p.x + c * p.z); }
vec3 rotX(vec3 p, float a) { float c = cos(a), s = sin(a); return vec3(p.x, c * p.y - s * p.z, s * p.y + c * p.z); }
vec2 rot2(vec2 p, float a) { float c = cos(a), s = sin(a); return vec2(c * p.x - s * p.y, s * p.x + c * p.y); }

// brightness of the Input picture at uv (0 outside it)
float inLum(vec2 uv)
{
	float inside = step(abs(uv.x - 0.5), 0.5) * step(abs(uv.y - 0.5), 0.5);
	return dot(texture(sTD2DInputs[2], uv).rgb, vec3(0.3, 0.6, 0.1)) * inside;
}

void main()
{
	ivec2 px = ivec2(gl_FragCoord.xy);
	float gun = float(px.y >> 2);
	float i = float(px.x + ((px.y & 3) << 10));
	float u = (i + 0.5) / N;
	int kind = int(uGroup2.w + 0.5);
	float K = uGroup.w;
	if (gun >= K) { fragColor = vec4(0.0, 0.0, 0.0, u); return; }
	float labelOn = step(0.5, uDesc.y);
	float Km = K - labelOn;                                   // guns that draw the picture
	bool isLabel = labelOn > 0.5 && gun > Km - 0.5;
	int inMode = int(uIn.x + 0.5);

	float seed = uStep.y;
	float seedI = floor(seed * 997.0);
	float g1 = hash1(gun * 7.3 + seedI), g2 = hash1(gun * 3.1 + seedI + 40.0), g3 = hash1(gun + seedI * 0.37 + 9.0);
	float s1 = hash1(seedI + 1.0), s2 = hash1(seedI + 2.0), s3 = hash1(seedI + 3.0);

	// ---- which shapes, and how far through the beat-locked morph
	float B = max(uStep.x, 0.25);
	float bp = uStep.w - gun * 0.5 * step(3.5, float(kind)) * step(float(kind), 4.5);   // arcade guns change in a stagger
	float stp = floor(bp / B);
	float tb = bp - stp * B;                                  // beats since the change
	float m = 1.0 - exp(-5.5 * tb) * cos(10.0 * tb);          // damped spring: overshoots, rings, settles
	float pick = seedI + uRot.w * 3.0;                        // a new section brings new shapes at once
	float rowA = rowFor(stp - 1.0, gun, pick);
	float rowB = rowFor(stp, gun, pick);
	if (isLabel)
	{
		rowA = uDesc.x + pmod(pick + stp - 1.0, uDesc.y);
		rowB = uDesc.x + pmod(pick + stp, uDesc.y);
	}
	// Describe: label words change cleanly (a short blank, then the next words), they do not morph
	bool snap = isLabel || (uDescB.z > 0.5 && ((kind == 1 && gun > 0.5) || (kind == 5 && gun > 1.5) || (kind == 10 && gun > 0.5)));
	if (snap) m = 1.0;
	vec4 a = shape(rowA, i), b = shape(rowB, i);
	vec3 p = mix(a.xyz, b.xyz, m);
	float pen = mix(a.w, b.w, clamp(m, 0.0, 1.0));
	// mid-morph the beam is travelling far per sample: let the scramble show a little
	if (snap) pen *= smoothstep(0.08, 0.3, tb);
	else pen = max(pen, 0.35 * (1.0 - smoothstep(0.0, 0.35, abs(m - 1.0))) * step(tb, 1.0));

	float evolve = uTime.x;
	float scale = uXform.x;
	vec2 off = uXform.yz;
	float roll = uXform.w;
	float yaw = uRot.x * evolve, tilt = uRot.y, persp = uRot.z;
	float audGain = uAud.x, audSmooth = uAud.y;
	float audU = u * uAud.z;
	float burst = clamp(uTime.w, 0.0, 1.0);
	audGain *= 1.0 + 5.0 * burst;                             // section change: the drawing arrives in a scribble
	float hitScale = 1.0 + 0.30 * uHit.x + 0.30 * burst;
	float traceFrac = uTrace.x;
	bool rawXY = false, sweep = false, direct = false;
	bool steady = uDescB.w > 0.5;                                      // words that must be read: hits do not shake them
	vec2 qd = vec2(0.0);
	vec2 audDir = vec2(1.0);

	// ---- per-kind composition
	if (isLabel)
	{	// DESCRIBE LABEL: a few plain words, small, flat and steady
		scale = uDesc.z; off = uDescB.xy; yaw = 0.0; tilt = 0.0; persp = 0.0; roll = 0.0;
		audGain = 0.004; steady = true; traceFrac = 1.0;
		pen *= uDesc.w;
	}
	else if (kind == 0)
	{	// WORD: one clean vector phrase, off-centre; the seed picks the side
		off *= vec2(s1 < 0.5 ? 1.0 : -1.0, s2 < 0.5 ? 1.0 : -1.0);
		tilt += 0.25 * sin(evolve * 0.31 + s3 * 6.0);
		scale *= 0.78 + 0.34 * s3;
		yaw = 0.35 * sin(evolve * 0.23 + s1 * 6.0);
	}
	else if (kind == 1)
	{	// GONIO: gun 0 is the stereo field itself, gun 1 a small label
		if (gun < 0.5) { rawXY = true; pen = 1.0; }
		else { scale = 0.34 * uDescC.x; off = vec2(-1.12, -0.80) * vec2(s1 < 0.5 ? 1.0 : -1.0, 1.0) * uDescC.zw; audGain *= 0.02; yaw = 0.0; tilt = 0.0; pen *= 0.3 * uDescC.y; steady = steady || uDescB.z > 0.5; }
	}
	else if (kind == 2)
	{	// WIRE: a model turning in space
		// laid out like a drawing sheet: the turning model large on one side, its front elevation
		// and plan small and still on the other
		float side = s1 < 0.5 ? 1.0 : -1.0;
		if (gun < 0.5)
		{
			off *= vec2(side, 1.0);
			yaw += s2 * 6.28;
			scale *= 0.9 + 0.3 * s3;
			tilt += (s3 - 0.5) * 0.4;
		}
		else
		{
			yaw = 0.0;
			tilt = gun < 1.5 ? 0.0 : 1.5708;
			persp = 0.0;
			scale *= 0.36;
			off = vec2(-side * (0.95 + 0.25 * s2), gun < 1.5 ? 0.46 : -0.46);
			audGain *= 0.4;
			hitScale = 1.0 + 0.10 * uHit.y;
			pen *= 0.3;
		}
	}
	else if (kind == 3)
	{	// MACRO: so close the outline leaves the frame
		off += 0.9 * vec2(sin(evolve * 0.21 + s1 * 6.28), 0.6 * cos(evolve * 0.17 + s2 * 6.28));
		roll += (s3 - 0.5) * 0.9;
	}
	else if (kind == 4)
	{	// ARCADE: eight different subjects on a 4 x 2 board
		float col = mod(gun, 4.0), rw = floor(gun / 4.0);
		// the board shuffles: each bar every subject hops one cell along
		float hop = floor(uTime.y) + (1.0 - exp(-6.0 * fract(uTime.y) * 4.0) * cos(11.0 * fract(uTime.y) * 4.0));
		float cc = pmod(col + (rw < 0.5 ? hop : -hop), 4.0);
		float wrap = smoothstep(3.0, 4.0, cc);          // slide out one side and in the other
		off = vec2((cc - 1.5 - 4.0 * wrap * step(0.5, wrap)) * 0.80 + (rw - 0.5) * 0.25, (rw - 0.5) * -0.92);
		yaw = evolve * (0.5 + g1) * (g2 < 0.5 ? 1.0 : -1.0) + g3 * 6.28;
		tilt = 0.35 + 0.3 * g2;
		scale *= 0.85 + 0.3 * g1;
		hitScale = 1.0 + 0.25 * uHit.x * step(0.5, g3) + 0.25 * uHit.y * step(g3, 0.5);
	}
	else if (kind == 5)
	{	// TIMEBASE: two traces swept left to right, plus a readout word
		if (gun < 1.5 && inMode == 1)
		{	// INPUT: 32 stacked traces. The waveform still moves each one; the picture sets how bright
			// the beam is as it crosses, the way a television draws.
			float li = floor(i / 256.0);
			float f = (i - li * 256.0 + 0.5) / 256.0;
			float line = gun * 16.0 + li;
			float v = (line + 0.5) / 32.0;
			float l = inLum(vec2(f, v));
			vec2 a0 = audioAt(f * 0.6 + 0.4 * hash1(line + seedI), 1.0);
			float wob = (mod(line, 2.0) < 0.5 ? a0.x : a0.y) * audGain * 0.3 * (0.35 + l);
			qd = vec2((f * 2.0 - 1.0) * ASPECT * 0.95, (v * 2.0 - 1.0) * 0.9 + wob);
			pen = (0.3 + 14.0 * l * l) * step(1.5, i - li * 256.0);     // 16 lines per gun: the beam is 16 times faster, so dimmer
			direct = true;
		}
		else if (gun < 1.5) { sweep = true; pen = 1.0; off = vec2(0.0, gun < 0.5 ? 0.42 : -0.38) * step(s2, 0.6); audGain *= 1.0 + 0.9 * step(0.6, s2); audDir = gun < 0.5 ? vec2(1.0, 0.0) : vec2(0.0, 1.0); }
		else { scale = 0.30 * uDescC.x; off = vec2(1.18 * (s1 < 0.5 ? 1.0 : -1.0), -0.84) * uDescC.zw; audGain *= 0.015; yaw = 0.0; tilt = 0.0; pen *= 0.5 * uDescC.y; steady = steady || uDescB.z > 0.5; }
	}
	else if (kind == 6)
	{	// LISSAJOUS: nested harmonic knots, ratios change with the seed and the step
		float A = 1.0 + floor(pmod(pick + stp, 4.0)), Bq = 2.0 + floor(pmod(pick * 3.0 + stp * 2.0, 5.0));
		float A0 = 1.0 + floor(pmod(pick + stp - 1.0, 4.0)), B0 = 2.0 + floor(pmod(pick * 3.0 + stp * 2.0 - 2.0, 5.0));
		float th = u * 2.0 * PI;
		float ph = evolve * 0.6 + gun * 0.22;
		vec3 qa = vec3(sin(A0 * th + ph), sin(B0 * th), cos((A0 + B0) * th + ph * 0.5));
		vec3 qb = vec3(sin(A * th + ph), sin(Bq * th), cos((A + Bq) * th + ph * 0.5));
		p = mix(qa, qb, m) * vec3(1.0, 1.0, 0.6);
		pen = 1.0;
		scale *= 1.0 - gun * 0.13;
		yaw += gun * 0.35;
		roll += gun * 0.1 * sin(evolve * 0.4);
	}
	else if (kind == 7)
	{	// WALL: text as texture, two columns of four blocks, written by a travelling head
		float col = mod(gun, 2.0), rw = floor(gun / 2.0);
		off = vec2((col - 0.5) * 1.72, (1.5 - rw) * 0.46) + vec2(0.0, 0.02 * sin(evolve + gun));
		yaw = 0.0; tilt = 0.0;
		hitScale = 1.0 + 0.05 * uHit.x;
	}
	else if (kind == 8)
	{	// DIAL: phrases bent round three concentric rings that tick round on the beat, like a rotary
		// dial seen close; the waveform is a small circle at the hub. Often larger than the frame.
		float side = s1 < 0.5 ? 1.0 : -1.0;
		off = vec2(side * (0.35 + 0.75 * s2), (s3 - 0.5) * 0.9);
		scale *= 0.95 + 0.9 * s3;
		tilt = (s2 - 0.5) * 1.3;
		yaw = side * -0.5 * s3;                                                   // a fixed lean, not a spin
		float bpf = fract(uStep.w), bpi = floor(uStep.w);
		float click = bpi + 1.0 - exp(-7.0 * bpf) * cos(15.0 * bpf);              // one notch per beat, ringing
		if (gun > 4.5)
		{
			vec2 a0 = audioAt(u, 1.0);
			float rr = 0.085 + clamp((a0.x + a0.y) * audGain * 1.1, -0.06, 0.10);
			float th = u * 2.0 * PI;
			p = vec3(rr * cos(th), rr * sin(th), 0.0);
			pen = 0.6;
		}
		else
		{
			float ring = gun < 1.5 ? 0.0 : (gun < 3.5 ? 1.0 : 2.0);
			float R = ring < 0.5 ? 0.80 : (ring < 1.5 ? 0.50 : 0.265);
			float span = ring < 1.5 ? PI * 0.5 : PI;                               // half the angle one phrase covers
			float second = ring < 1.5 ? mod(gun, 2.0) : 0.0;
			float dir = ring == 1.0 ? -1.0 : 1.0;
			float rot = dir * (click * 0.2618 * (1.0 + ring) + evolve * 0.25);
			float th = PI * 0.5 + second * PI - p.x * span * 0.93 + rot;
			vec2 ar = audioAt(fract(u + g1), audSmooth);
			float rad = R + p.y * R * span * 0.93 + (ar.x + ar.y) * audGain * 0.55
			          + 0.05 * uHit.x * (ring - 1.0);                              // kick: outer and inner rings part
			p = vec3(rad * cos(th), rad * sin(th), 0.0);
		}
		audGain *= 0.25;
		hitScale = 1.0 + 0.12 * uHit.x + 0.30 * burst;
	}
	else if (kind == 9)
	{	// SCAN: a raster of 64 lines pushed out of the screen by the brightness of a picture
		// (a phrase or a lit model), after the Rutt-Etra scan processor. Seen at a slant.
		float li = floor(i / 512.0);
		float f = (i - li * 512.0 + 0.5) / 512.0;
		float line = gun * 8.0 + li;
		float v = (line + 0.5) / (Km * 8.0);
		// a little vertical smoothing so the lines flow instead of stepping
		float lum = 0.0;
		for (int j = -1; j <= 1; j++)
			lum += dot(texture(sTD2DInputs[2], vec2(f, v + float(j) * 0.006)).rgb, vec3(0.3, 0.6, 0.1)) * (j == 0 ? 0.5 : 0.25);
		lum = clamp(lum, 0.0, 1.5);
		vec2 al = audioAt(fract(f * 0.6 + line * 0.137), audSmooth);
		float h = 0.34 * (1.0 + 0.6 * uHit.x) + 0.3 * burst;
		p = vec3((f * 2.0 - 1.0) * 1.62, (v * 2.0 - 1.0) * 0.92, lum * h + al.x * audGain * (0.3 + lum));
		pen = (0.17 + 1.5 * lum) * step(1.5, i - li * 512.0);
		tilt = -(0.30 + 0.40 * s2) + 0.1 * sin(evolve * 0.5);
		yaw = (s1 - 0.5) * 0.7 + 0.12 * sin(evolve * 0.37 + s3 * 6.0);
		off = vec2(0.0, -0.12);
		audGain = 0.0;
		hitScale = 1.0 + 0.04 * uHit.x;
	}
	else if (kind == 10)
	{	// WATERFALL: one trace that climbs away from the viewer in steps; the afterglow leaves the
		// earlier traces standing behind it as a ridged landscape of the last seconds.
		if (gun < 0.5)
		{
			float c = fract(uStep.w / B);
			float cq = floor(c * 30.0) / 30.0;
			float far = 1.0 - (1.0 - cq) * (1.0 - cq);                             // perspective: far lines crowd together
			float wd = mix(1.08, 0.42, far);
			vec2 a0 = audioAt(u, 0.0);
			float taper = 0.15 + 0.85 * exp(-pow((u - 0.5) * 3.0, 2.0));
			float amp = audGain * (1.0 + 0.8 * uHit.x) * taper * mix(1.0, 0.45, far);
			float vx = (s1 - 0.5) * 1.4;                                           // vanishing point
			qd = vec2(vx * far + (u * 2.0 - 1.0) * ASPECT * wd, -0.92 + 1.38 * far + abs(a0.x + a0.y) * amp);
			direct = true;
			pen = 1.0;
			if (inMode == 1)
			{	// INPUT: the landscape is the picture. 32 rows (bottom row nearest), each raised by the
				// picture's brightness along it; the climbing trace is a bright row that carries the waveform.
				// (One row per step with the afterglow holding the rest was tried first: the old rows had
				// faded to a fifth by the time the trace came round, in_10.png.)
				float li = floor(i / 128.0);
				float f = (i - li * 128.0 + 0.5) / 128.0;
				float rq = (li + 0.5) / 32.0;
				float farR = 1.0 - (1.0 - rq) * (1.0 - rq);
				float l = inLum(vec2(f, rq));
				float hd = abs(rq - cq);
				hd = min(hd, 1.0 - hd);
				float headK = exp(-hd * hd * 600.0);
				vec2 a1 = audioAt(f, 0.0);
				float tp = 0.15 + 0.85 * exp(-pow((f - 0.5) * 3.0, 2.0));
				float ampR = audGain / (1.0 + 5.0 * burst) * (1.0 + 0.8 * uHit.x) * tp * (0.025 + 0.3 * headK);
				qd = vec2(vx * farR + (f * 2.0 - 1.0) * ASPECT * mix(1.08, 0.42, farR),
				          -0.92 + 1.38 * farR + (l * 0.40 + abs(a1.x + a1.y) * ampR) * mix(1.0, 0.45, farR));
				pen = (0.7 + 26.0 * l) * (0.45 + 1.6 * headK) * step(1.5, i - li * 128.0);
			}
		}
		else { scale = 0.30 * uDescC.x; off = vec2(1.12 * (s1 < 0.5 ? 1.0 : -1.0), 0.82) * uDescC.zw; audGain *= 0.01; yaw = 0.0; tilt = 0.0; pen *= 0.22 * uDescC.y; hitScale = 1.0; steady = steady || uDescB.z > 0.5; }
	}

	vec2 q;
	float depth = 0.0;
	vec2 aud = audioAt(fract(audU + g1 * step(1.5, Km)), audSmooth);
	if (rawXY)
	{
		aud = audioAt(u, 0.0);
		// mid up, side across, like a goniometer
		// This track is close to mono, so the plain figure is a thin upright line. The side signal
		// is opened up and the mid is also plotted against itself a moment earlier (a phase portrait),
		// which turns every tone into a loop. Both are still nothing but the samples.
		float norm = audGain / (0.10 + 2.2 * uAud.w);          // ride the live level so quiet bars still fill the tube
		q = stereoFigure(u, s3) * norm;
		q = rot2(q, roll + (s2 < 0.5 ? 0.0 : -0.7854) + 0.12 * uHit.y);
		q *= 1.0 + 0.2 * uHit.x;
	}
	else if (sweep)
	{
		aud = audioAt(u, 0.0);
		q = vec2((u * 2.0 - 1.0) * ASPECT * 0.97, dot(aud, audDir) * audGain) + off;
		q.y += 0.06 * uHit.x * sin(u * 40.0 + uTime.x * 9.0) * (gun < 0.5 ? 1.0 : -1.0);
	}
	else if (direct)
	{
		q = qd;
	}
	else
	{
		p = rotY(p, yaw);
		p = rotX(p, tilt);
		depth = p.z;
		float w = 1.0 / (1.0 - persp * p.z * 0.45);
		q = p.xy * w;
		float snare = steady ? 0.0 : uHit.y;
		if (steady)
		{
			hitScale = 1.0;
			if (uDescB.w > 0.5) audGain /= 1.0 + 5.0 * burst;     // the whole take: keep the waveform, drop the section burst
			else audGain = min(audGain, 0.004);                   // a label
		}
		q = rot2(q, roll + 0.05 * snare);
		q *= scale * hitScale;
		q.x += 0.10 * snare * q.y;                        // snare: a shear that rings
		q += off;
		q += aud * audGain;                               // left to X, right to Y
		if (uTrace.z > 0.0)
		{	// the last beat before a change: the drawing lets go and becomes the raw stereo field,
			// then the next shape condenses out of it
			vec2 blob = off * 0.5 + stereoFigure(u, s3) * uTrace.w / (0.10 + 2.2 * uAud.w);
			float d = max(smoothstep(B - uTrace.z, B - 0.55 * uTrace.z, tb), exp(-9.0 * tb));
			q = mix(q, blob, d);
			pen = mix(pen, 2.5, d);
		}
	}

	// ---- beam blanking
	// the drawn window: a head runs round the path, the tail behind it is lit
	float arrive = clamp(uStep.z / 0.3, 0.0, 1.0);            // first third of a second: the picture is written on
	float frac = traceFrac * arrive;
	if (frac < 0.999)
	{
		float head = fract(uStep.w * uTrace.y + g1);
		float behind = fract(head - u);
		float lit = 1.0 - smoothstep(frac * 0.85, frac, behind);
		lit *= mix(1.0, 0.45 + 1.6 * exp(-behind / max(frac, 1e-3) * 5.0), step(traceFrac, 0.999));
		pen *= lit;
	}
	// nearer edges of a turning model are brighter
	pen *= clamp(1.0 + 0.9 * depth * persp, 0.25, 1.8);
	pen *= 1.0 + 1.5 * burst;
	fragColor = vec4(q, pen, u);
}
