// Kinetic type machine: one instance = one glyph quad (or one solid bar).
// Everything a glyph does is a function of the feed and the shot, so the scene is stateless.
// Layout data (baked by build.py) lives in sLay: 7 attributes x 3 rows of 1024 texels per layout.
uniform sampler2D sLay;   // per-glyph layout attributes
uniform sampler2D sTab;   // glyph table: row f = (x0, y0, cellw, advance) in atlas px; row NF+f = font constants
uniform sampler2D sPar;   // per-take parameters: transform, palette
uniform sampler2D sNum;   // the large numerals atlas (font 3), read here as the mosaic's mask
uniform vec4 uTime;    // beat_pos, bar_pos, beats since the beat of the cut, shot age (s)
uniform vec4 uHits;    // hit_low, hit_mid, hit_high, pulse
uniform vec4 uState;   // energy, section, seed, layout index
uniform vec4 uCount;   // bar_i, beat_i, hits_low, t
uniform vec4 uMisc;    // bar_pulse, evolve, hits_high, take
uniform sampler2D sInp;   // the Input picture (another scene's output), read per glyph
uniform vec4 uInp;     // 1 while the COMP's Input names a TOP, else 0 and nothing below reads sInp

out vec2 vUV;
out vec2 vRect;
out float vGate;
flat out vec2 vRectSize;
flat out vec4 vInfo;

const float PI = 3.14159265;
const int LW = 1024;
const int ROWS = 3;
const int NA = 7;
const int NF = 4;

vec4 attr(int i, int a)
{
	int li = int(uState.w + 0.5);
	return texelFetch(sLay, ivec2(i % LW, li * NA * ROWS + a * ROWS + i / LW), 0);
}

float hash1(float n) { return fract(sin(n * 12.9898) * 43758.5453); }
vec3 hash3(float n) { return fract(sin(vec3(n * 12.9898, n * 78.233, n * 37.719)) * 43758.5453); }
mat2 rot2(float a) { float c = cos(a), s = sin(a); return mat2(c, s, -s, c); }
float easeOutBack(float x) { float y = x - 1.0; return 1.0 + 2.70158 * y * y * y + 1.70158 * y * y; }
float easeOutCubic(float x) { float y = 1.0 - x; return 1.0 - y * y * y; }

// beat counter that lurches forward on each beat and then coasts
float stepped(float bp, float amount)
{
	float f = fract(bp);
	float st = floor(bp) + 1.0 - pow(1.0 - f, 5.0);
	return mix(bp, st, amount);
}

float counter(float id)
{
	int k = int(id + 0.5);
	if (k == 0) return max(uCount.x, 0.0) + 1.0;            // bar number
	if (k == 1) return max(uCount.y, 0.0);                  // beat number
	if (k == 2) return mod(max(uCount.y, 0.0), 4.0) + 1.0;  // beat in bar 1..4
	if (k == 3) return floor(max(uTime.x, 0.0) * 4.0);      // sixteenths
	if (k == 4) return uCount.z;                            // kicks so far
	if (k == 5) return floor(uCount.w * 100.0);             // centiseconds
	if (k == 6) return uState.y;                            // section
	return floor(uCount.w);                                 // seconds
}

// accordion: weight of row j of n; a bulge travels through the rows once per bar
float accW(float j, float n)
{
	float ph = uTime.x * 0.25 - j / n;
	float b = 0.5 + 0.5 * cos(2.0 * PI * ph);
	// quiet passages keep the rows nearly even; loud ones and kicks make the bulge extreme
	return 0.16 + pow(b, 3.0) * (0.5 + 1.4 * uState.x + 1.3 * min(uHits.x, 1.0)) + 0.25 * uHits.w;
}

void main()
{
	int id = TDInstanceID();
	vec4 A = attr(id, 0), B = attr(id, 1), C = attr(id, 2), D = attr(id, 3);
	vec4 E = attr(id, 4), F = attr(id, 5), G = attr(id, 6);
	vec2 uv = TDPos().xy + 0.5;
	float bp = uTime.x, barp = uTime.y, lb = uTime.z, age = uTime.w;
	int take = int(uMisc.w + 0.5);

	vec2 pen = A.xy;
	float s = A.z, rot = A.w;
	float ch = B.x;
	int font = int(floor(B.y + 0.5));
	float col = B.z;
	int mode = int(B.w + 0.5);
	float rnd = C.w;
	vec2 scl = E.xy;
	float alpha = 1.0, rx = 0.0, pop = 1.0, xE = 0.0;
	vec3 gate = vec3(0.0);
	vec2 xTgt = vec2(0.0);
	bool solid = font < 0;
	vec2 dir = vec2(cos(rot), sin(rot));
	if (scl.x == 0.0 && scl.y == 0.0) alpha = 0.0;      // unused slot

	if (mode == 1) {
		// line scrolls along its baseline, locked to the beat
		pen += dir * mod(D.x * stepped(bp, D.z), D.y);
	} else if (mode == 2) {
		// flash card: one word per D.y beats, letters land one after another
		float k = floor(lb / D.y);
		float cur = mod(k, D.x);
		float f = lb - k * D.y;
		if (abs(C.y - cur) > 0.5) alpha = 0.0;
		// fast: the first letter is already half way in on the beat itself (feed_flash_snare.png showed an empty card)
		float g = clamp((f - F.w * 0.02) / 0.13 + 0.35, 0.0, 1.0);
		if (f < F.w * 0.02) alpha = 0.0;
		float e = easeOutBack(g);
		pen.y -= (1.0 - e) * 0.3 * s;
		pop *= mix(0.75, 1.0, e);
	} else if (mode == 3 || mode == 9) {
		// typed: one glyph per sixteenth (D.z per beat), then hold D.y steps; 9 is the cursor
		float cnt = mod(floor(lb * D.z) + D.w, D.x + D.y);      // D.w glyphs are already typed at the cut
		if (mode == 3) {
			if (C.z >= cnt) alpha = 0.0;
			else if (C.z >= cnt - 1.0) { float f = fract(lb * D.z); pop *= 1.0 + 0.45 * (1.0 - f) * (1.0 - f); }
		} else {
			float at = min(cnt, D.x);
			if (abs(C.z - at) > 0.5) alpha = 0.0;
			else if (cnt >= D.x && fract(lb * 2.0) > 0.5) alpha = 0.0;
		}
	} else if (mode == 4) {
		// roll call: the list steps up one line per D.w beats; the line in the gate is knocked out and enlarged
		float qv = lb / D.w;
		float off = D.x * (floor(qv) + easeOutBack(clamp(fract(qv) * 2.4, 0.0, 1.0)));
		float lo = D.z - 0.5 * D.y;
		float y = mod(pen.y + off - lo, D.y) + lo;
		float d = abs(y + 0.36 * s - D.z);
		float hl = 1.0 - smoothstep(0.35 * D.x, 0.75 * D.x, d);
		float k = 1.0 + G.y * hl;
		pen.x = F.x + (pen.x - F.x) * k;
		pen.x += G.z * min(uHits.x, 1.2) * (1.0 - hl);      // kick: lines outside the gate jolt apart, odd against even
		pen.y = y - 0.36 * s * (k - 1.0);
		s *= k;
		gate = vec3(1.0, D.z - 0.5 * D.x, D.x);       // knocked out per pixel inside the gate (take_3.png, mid-step)
	} else if (mode == 5) {
		// exploded letters: assembled for one bar, scattered on a grid for the next
		float cy = barp * 0.5 + D.x;
		float cyc = fract(cy);
		float e = smoothstep(0.5, 0.53, cyc) * (1.0 - smoothstep(0.84 + 0.1 * rnd, 0.9 + 0.1 * rnd, cyc));
		e = max(e, 1.0 - smoothstep(0.0, 0.35, age - 0.25 * rnd));
		// every letter gets its own cell of an 8 x 4 specimen grid; the permutation changes each cycle
		float cyi = floor(cy + 0.5);
		vec3 hc = hash3(cyi * 7.31 + uState.z * 37.0);
		vec3 h = hash3(rnd * 91.7 + cyi * 3.7);
		float kk = 5.0 + 8.0 * floor(hc.x * 4.0);                  // 5, 13, 21, 29: all coprime with 32
		float cellI = mod(C.z * kk + floor(hc.y * 32.0), 32.0);
		xTgt = vec2((mod(cellI, 8.0) + 0.5) * 160.0, 64.0 + (floor(cellI / 8.0) + 0.5) * 164.0);
		xTgt += 6.0 * vec2(sin(uMisc.y * 2.0 + rnd * 40.0), cos(uMisc.y * 1.7 + rnd * 23.0));
		float r2 = (floor(h.z * 4.0) - 1.0) * PI * 0.5 * step(0.6, fract(h.z * 13.0));
		float s2 = 190.0 * (h.x > 0.86 ? 2.3 : 1.0);
		xE = e;
		rx += r2 * e;
		s = mix(s, s2, e);
		vec2 kd = hash3(rnd * 17.3 + uCount.z * 0.91).xy - 0.5;
		pen += kd * min(uHits.x, 1.2) * (1.0 - e) * D.y;
		rx += kd.x * min(uHits.x, 1.2) * (1.0 - e) * D.z;
	} else if (mode == 6) {
		// numeral taken from a feed counter: D.x which counter, D.y decimal place
		float v = counter(D.x);
		ch = 48.0 + mod(floor(v / pow(10.0, D.y) + 1e-3), 10.0);
		if (D.y < 0.5) pop *= 1.0 + D.z * uHits.w;
	} else if (mode == 7) {
		// accordion: row heights are redistributed every frame, type is stretched to fit its row
		float n = D.y, tot = 0.0, y0 = 0.0, hr = 0.0;
		for (int j = 0; j < 16; j++) {
			if (float(j) >= n) break;
			float w = accW(float(j), n);
			if (float(j) < D.x - 0.5) y0 += w;
			if (abs(float(j) - D.x) < 0.5) hr = w;
			tot += w;
		}
		float k = 720.0 * hr / tot / D.z;
		scl.y *= k;
		pen.y = 720.0 * y0 / tot + pen.y * k;
		pen.x += mod(G.z * stepped(bp, 0.7), G.y);
	} else if (mode == 8) {
		// solid bar whose length follows the feed
		int st = int(D.x + 0.5);
		float k = 1.0;
		if (st == 1) k = fract(barp);
		else if (st == 2) k = uHits.w;
		else if (st == 3) k = fract(bp);
		else if (st == 4) k = uState.x;
		else if (st == 5) k = min(uHits.x, 1.0);
		else if (st == 6) k = fract(barp * 0.25);
		scl.x *= max(k, D.y);
	} else if (mode == 10) {
		// beat lamp: lit when the beat in a cycle of D.y equals D.x
		col = abs(mod(max(uCount.y, 0.0), D.y) - D.x) < 0.5 ? 2.0 : 3.0;
	} else if (mode == 11) {
		// mosaic: a field of small glyphs with text streaming through it; the cells under a giant feed
		// numeral (D.x counter, D.y digits, D.z size, origin D.w / G.y) swell and take the ink
		float cw = G.w;
		vec2 cc = A.xy + vec2(0.5 * cw);
		vec4 fc3 = texelFetch(sTab, ivec2(0, NF + 3), 0);
		float adv0 = texelFetch(sTab, ivec2(16, 3), 0).w * D.z / fc3.x;
		vec2 q = cc - vec2(D.w, G.y);
		float di = floor(q.x / adv0);
		float m = 0.0;
		if (di >= 0.0 && di < D.y) {
			float dg = mod(floor(counter(D.x) / pow(10.0, D.y - 1.0 - di) + 1e-3), 10.0);
			vec4 tb = texelFetch(sTab, ivec2(16 + int(dg + 0.5), 3), 0);
			vec2 lp = vec2(q.x - di * adv0, q.y) * fc3.x / D.z + vec2(fc3.z, fc3.w);
			if (lp.x > 0.0 && lp.x < tb.z && lp.y > 0.0 && lp.y < fc3.y)
				m = textureLod(sNum, (tb.xy + lp) / 1280.0, log2(max(cw * fc3.x / D.z, 1.0))).r;
		}
		m = smoothstep(0.25, 0.75, m);
		// Input: a glyph halftone. Every cell's size follows the brightness of the picture under it; the numeral
		// only turns the bright cells it covers to the accent and shakes them on kicks.
		// Tried and dropped: luminance alone with a cut at 0.3 (a saturated disc vanished), and letting the numeral
		// swell its cells as well (it hid the picture).
		bool pic = uInp.x > 0.5;
		float mn = m, mp = 0.0;
		if (pic) {
			vec3 pc = textureLod(sInp, cc / vec2(1280.0, 720.0), log2(max(cw, 2.0)) - 1.0).rgb;
			float pv = mix(dot(pc, vec3(0.299, 0.587, 0.114)), max(pc.r, max(pc.g, pc.b)), 0.25);
			mp = smoothstep(0.12, 0.7, pv);
			m = mp;
		}
		// the text runs along its row a cell per eighth note, odd rows against even
		float sh = floor(bp * 2.0) * (mod(C.x, 2.0) < 0.5 ? 1.0 : -1.0);
		ch = attr(int(C.x * C.y + mod(C.z + sh, C.y) + 0.5), 1).x;
		col = m > 0.5 ? 1.0 : 3.0;
		if (pic) col = mp > 0.25 ? (mn > 0.5 ? 2.0 : 1.0) : 3.0;
		// arrival: a shock ring of swollen glyphs runs out from the centre (feed_mosaic_kick.png, first version:
		// growing the field from nothing left the frame empty for 0.4 s at every section change)
		float rr = length(cc - vec2(640.0, 360.0)) / 740.0 - age * 2.2;
		float arrive = 1.0 + 0.6 * exp(-rr * rr * 30.0);
		if (pic) {
			s *= mix(0.4, 1.3, mp) * (1.0 + 0.25 * uHits.w * mp) * arrive;
			rx += (rnd - 0.5) * 2.6 * min(uHits.x, 1.2) * mn * mp;
		} else {
			s *= mix(0.55, 1.35, m) * (1.0 + 0.25 * uHits.w * m) * arrive;
			rx += (rnd - 0.5) * 2.6 * min(uHits.x, 1.2) * m;
		}
		xTgt = cc;
		xE = 1.0;
		// r2_dbg.png: the word spaces left holes in the numeral. Inside it a space is drawn as a solid block.
		if (ch < 32.5 && m > 0.5) { solid = true; scl = vec2(cw * 0.84 * arrive * (1.0 + 0.2 * uHits.w)); }
	} else if (mode == 12) {
		// ring: the glyph rides a circle round A.xy (D.x radius, D.y angle, D.z radians a beat, D.w direction)
		float a0 = clamp((age - E.z) / 0.45, 0.0, 1.0);
		float th = D.y + D.z * stepped(bp, 0.75) - D.w * 0.9 * (1.0 - easeOutCubic(a0));
		// kick: neighbouring rings breathe against each other and lurch along their circles. In pixels, not as a
		// share of the radius: at 4.5% the outer rings ran into each other (feed_rings_kick.png, first version)
		float R = D.x + D.w * (13.0 * min(uHits.x, 1.2) + 4.0 * uHits.w);
		th += D.w * 46.0 * min(uHits.x, 1.2) / D.x;
		pen = A.xy + R * vec2(cos(th), sin(th));
		rot = th - 0.5 * PI;
		dir = vec2(cos(rot), sin(rot));
	} else if (mode == 13) {
		// echo: copy C.x of a word, offset along a swinging direction; the stack is tight in quiet beats and
		// shoots out on kicks (D.x angle, D.y swing, D.z pixels per copy)
		float ang = D.x + D.y * sin(bp * PI * 0.25);
		float open = easeOutBack(clamp(age / 0.35, 0.0, 1.0));
		float spread = D.z * open * (0.3 + 0.5 * uState.x + 1.0 * min(uHits.x, 1.2) + 0.3 * uHits.w);
		pen += C.x * spread * vec2(cos(ang), sin(ang));
	}

	// shared modifiers --------------------------------------------------------
	pen.x += (A.x - F.x) * F.y * uHits.w;                               // tracking opens on the beat
	vec3 hk = hash3(rnd * 53.1 + uCount.z * 0.731);
	pen += (hk.xy - 0.5) * F.z * min(uHits.x, 1.2);                     // kick scatter
	int fl = int(E.w + 0.5);
	if (fl == 1 && uHits.z > 0.05 && hash1(rnd * 7.7 + uMisc.z * 0.37) > 0.84) col = 2.0;   // hats light single glyphs
	if (fl == 2 && hash1(rnd * 3.1 + floor(bp * 4.0) * 0.173) > 0.5) alpha = 0.0;         // sixteenth flicker
	if (fl == 3) scl.y *= smoothstep(0.12, 0.5, uState.x);                                 // row closes in quiet passages

	int ar = int(G.x + 0.5);                                            // arrival after the cut
	float a = clamp((age - E.z) / 0.28, 0.0, 1.0);
	if (ar == 1) { pop *= easeOutBack(a); if (a <= 0.0) alpha = 0.0; }
	else if (ar == 2) { pen -= dir * (1.0 - easeOutCubic(a)) * 500.0; }
	else if (ar == 3) { pen.y -= (1.0 - easeOutCubic(a)) * 140.0; if (a <= 0.0) alpha = 0.0; }
	else if (ar == 4) { scl.x *= easeOutCubic(a); }
	else if (ar == 5) { if (a <= 0.0) alpha = 0.0; }
	else if (ar == 6) {                                               // decode: random capitals until it settles
		if (a <= 0.0) alpha = 0.0;
		else if (a < 1.0 && !solid) ch = 65.0 + floor(hash1(rnd * 9.1 + floor(age * 24.0) * 0.37) * 26.0);
	}

	// geometry -----------------------------------------------------------------
	vec2 local, centre;
	vUV = vec2(0.0);
	if (solid) {
		local = uv * scl;
		centre = 0.5 * scl;
	} else {
		vec4 tab = texelFetch(sTab, ivec2(int(ch + 0.5) - 32, font), 0);
		vec4 fc = texelFetch(sTab, ivec2(0, NF + font), 0);       // FS, row height, pad, baseline offset
		float cap = texelFetch(sTab, ivec2(1, NF + font), 0).x;
		vec2 k = s / fc.x * scl;
		vec2 cell = vec2(tab.z, fc.y);
		local = (uv * cell - vec2(fc.z, fc.w)) * k;
		centre = vec2(tab.w * 0.5, cap * fc.x * 0.5) * k;
		vUV = tab.xy + uv * cell;
		if (tab.z <= 0.0) alpha = 0.0;
	}
	if (mode == 5 || mode == 11) pen = mix(pen, xTgt - centre, xE);          // exploded letters sit centred in their cells
	vec2 v = centre + rot2(rx) * ((local - centre) * pop);
	vec2 world = pen + rot2(rot) * v;
	vGate = gate.x > 0.5 ? (world.y - gate.y) / gate.z : -1.0;

	vec4 X = texelFetch(sPar, ivec2(0, take), 0);                 // angle, scale, offset
	vec4 FX = texelFetch(sPar, ivec2(5, take), 0);
	vec4 FX2 = texelFetch(sPar, ivec2(10, take), 0);              // zoom range, snare jolt
	float ang = X.x * ((FX.x > 0.5 && fract(uState.z * 7.0) > 0.5) ? -1.0 : 1.0);
	ang += FX2.y * min(uHits.y, 1.0) * (hash1(uCount.z * 0.37 + 2.0) > 0.5 ? 1.0 : -1.0);
	float zoom = X.y * (1.0 + FX2.x * pow(fract(uState.z * 13.0), 2.0));
	world = vec2(640.0, 360.0) + X.zw + rot2(ang) * ((world - vec2(640.0, 360.0)) * zoom);

	// Input, takes whose glyph kind is 1 (sPar column 11, z): every glyph is sized and coloured by the picture
	// under its centre
	vec4 IN = texelFetch(sPar, ivec2(11, take), 0);
	if (uInp.x > 0.5 && IN.z > 0.5 && IN.z < 1.5 && !solid && alpha > 0.0) {
		vec2 wc = pen + rot2(rot) * centre;
		wc = vec2(640.0, 360.0) + X.zw + rot2(ang) * ((wc - vec2(640.0, 360.0)) * zoom);
		float lum = dot(textureLod(sInp, wc / vec2(1280.0, 720.0), log2(max(0.3 * s * zoom, 1.0))).rgb,
			vec3(0.299, 0.587, 0.114));
		float l = smoothstep(0.05, 0.8, lum);
		world = wc + (world - wc) * mix(0.4, 1.0, l);
		if (lum > 0.78 && col > 0.5) col = 2.0;
		else if (l < 0.15 && col > 0.5) col = 3.0;
	}

	vRect = uv * scl * pop * zoom;
	vRectSize = scl * pop * zoom;
	vInfo = vec4(solid ? -1.0 : float(font), col, alpha, gate.x);
	if (alpha <= 0.0) world = vec2(-99999.0);
	gl_Position = TDWorldToProj(vec4(world, 0.0, 1.0));
}
