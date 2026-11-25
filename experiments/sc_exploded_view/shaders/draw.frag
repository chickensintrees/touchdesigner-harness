// sc_exploded_view: the draughtsman. Turns the G-buffer into line art on paper and adds the
// annotation geometry (dimension lines, leaders, borders) and the lettering.
// inputs: 0 normal.xyz + depth, 1 part id / cut flag / glow / coverage, 2 lettering,
//         3, 4 (the TOPs parameter) the Input picture as it sits on the parts, and the Input picture itself
uniform vec4 uPaper;    // rgb paper, w paper style (0 plain, 1 blueprint grid, 2 dot grid, 3 black, 4 ruled)
uniform vec4 uInk;      // rgb ink, w outline radius px
uniform vec4 uAccent;   // rgb second ink (cut faces, dimensions), w crease radius px
uniform vec4 uStyle;    // x hatch spacing px, y cut-face fill, z shading lines, w vignette
uniform vec4 uAudio;    // x pulse, y hit_mid, z age, w evolve
uniform vec4 uAudio2;   // x hit_low, y beat phase, z reveal 0..1, w depth edge threshold
uniform vec4 uStyle2;   // x contour rings along the axis (0 off), y solid fill 0..1, z part mode, w scan position 0..1
uniform vec4 uPic;      // x 1 when the Input picture is on the parts, y lettering knock-out (labels over line work),
                        // z 0..1 the Input picture drafted onto the sheet behind the parts
uniform vec4 uL0[40];   // segment x0 y0 x1 y1 in pixels
uniform vec4 uL1[40];   // kind, ink (0 ink, 1 accent), width px, spare

out vec4 fragColor;

const vec2 RES = vec2(1280.0, 720.0);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

// brightness of the Input picture: half way between luminance and the strongest channel, so a
// saturated colour reads as a mid tone and not as near black
float picLum(vec3 c) { return 0.5 * dot(c, vec3(0.299, 0.587, 0.114)) + 0.5 * max(c.r, max(c.g, c.b)); }

float sdSeg(vec2 p, vec2 a, vec2 b)
{
	vec2 pa = p - a, ba = b - a;
	float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0.0, 1.0);
	return length(pa - ba * h);
}

float arrowHead(vec2 p, vec2 tip, vec2 dir, float len)
{
	vec2 q = p - tip;
	float x = dot(q, dir);
	float y = abs(dot(q, vec2(-dir.y, dir.x)));
	return max(max(-x, x - len), y - x * 0.24);
}

// x: outline strength, y: crease strength
vec2 edges(vec2 uv, float r, vec4 G, vec4 D)
{
	vec2 texel = 1.0 / RES;
	float outl = 0.0, crease = 0.0;
	for (int i = 0; i < 4; i++) {
		vec2 dir = i == 0 ? vec2(1, 0) : (i == 1 ? vec2(0, 1) : (i == 2 ? vec2(0.707, 0.707) : vec2(-0.707, 0.707)));
		vec2 d = dir * r * texel;
		vec4 g1 = texture(sTD2DInputs[0], uv + d), g2 = texture(sTD2DInputs[0], uv - d);
		vec4 e1 = texture(sTD2DInputs[1], uv + d), e2 = texture(sTD2DInputs[1], uv - d);
		float both = e1.a * e2.a;
		outl = max(outl, abs(e1.a - e2.a));
		outl = max(outl, both * min(1.0, abs(e1.x - e2.x)));
		outl = max(outl, both * smoothstep(uAudio2.w, uAudio2.w * 2.0, abs(g1.a + g2.a - 2.0 * G.a)));
		outl = max(outl, both * abs(e1.y - e2.y));
		crease = max(crease, both * smoothstep(0.08, 0.35, 1.0 - dot(g1.xyz, g2.xyz)));
	}
	return vec2(outl, crease);
}

vec3 paper(vec2 px, vec2 uv)
{
	vec3 c = uPaper.rgb;
	float style = uPaper.w;
	float mott = TDSimplexNoise(px * 0.004) * 0.5 + TDSimplexNoise(px * 0.02 + 40.0) * 0.25;
	float grain = hash(floor(px)) - 0.5;
	if (style < 0.5) {
		c *= 1.0 + 0.035 * mott + 0.03 * grain;
	} else if (style < 1.5) {
		// blueprint: a fine and a coarse grid a little lighter than the ground
		vec2 f = abs(fract(px / 24.0 + 0.5) - 0.5) * 24.0;
		vec2 m = abs(fract(px / 120.0 + 0.5) - 0.5) * 120.0;
		float fine = 1.0 - smoothstep(0.0, 1.0, min(f.x, f.y));
		float major = 1.0 - smoothstep(0.3, 1.4, min(m.x, m.y));
		c *= 1.0 + 0.10 * mott + 0.05 * grain;
		c = mix(c, uInk.rgb, 0.07 * fine + 0.16 * major);
	} else if (style < 2.5) {
		vec2 f = fract(px / 20.0) - 0.5;
		float dotm = 1.0 - smoothstep(0.05, 0.09, length(f));
		c *= 1.0 + 0.03 * mott + 0.025 * grain;
		c = mix(c, uInk.rgb, 0.22 * dotm);
	} else if (style < 3.5) {
		c += 0.012 * grain;
	} else {
		float y = abs(fract(px.y / 36.0 + 0.5) - 0.5) * 36.0;
		c *= 1.0 + 0.04 * mott + 0.03 * grain;
		c = mix(c, uAccent.rgb, 0.18 * (1.0 - smoothstep(0.2, 1.0, y)));
	}
	vec2 q = uv - 0.5;
	c *= 1.0 - uStyle.w * dot(q, q) * 1.6;
	return c;
}

void main()
{
	vec2 uv = vUV.st;
	vec2 px = uv * RES;
	vec4 G = texture(sTD2DInputs[0], uv);
	vec4 D = texture(sTD2DInputs[1], uv);
	vec3 col = paper(px, uv);
	vec3 pap = col;

	// the plotter draws the sheet left to right in the first moments of a shot
	float reveal = uAudio2.z;
	float front = reveal * 1.15 * RES.x;
	float shown = reveal >= 1.0 ? 1.0 : smoothstep(front, front - 30.0, px.x);

	float kick = min(uAudio.x, 1.0);
	float rO = uInk.w * (1.0 + 0.45 * kick);
	vec2 e = edges(uv, rO, G, D);
	vec2 e2 = edges(uv, uAccent.w, G, D);
	float lineInk = max(smoothstep(0.25, 0.6, e.x), 0.75 * step(0.05, uAccent.w) * smoothstep(0.3, 0.7, e2.y));

	// solid parts hide the grid: paper shows through a touch lighter
	float cov = D.a;
	float fill = uStyle2.y;
	vec3 body = mix(mix(col, uPaper.rgb, 0.85), uInk.rgb, fill);
	// on a solid part the lines are cut out of it in the paper colour
	vec3 lineCol = mix(uInk.rgb, uPaper.rgb, step(0.5, fill) * step(0.5, cov));
	// shading lines on the side away from the light, like a quick drafting tone; the darkest
	// faces get a second set across the first
	float shade = clamp(0.5 - dot(G.xyz, normalize(vec3(-0.45, 0.6, 0.66))), 0.0, 1.0);
	float sl = 1.0 - smoothstep(0.25, 0.75, abs(fract((px.x - px.y) / 5.0) - 0.5) * 2.0 + 1.0 - shade * 2.2);
	float sl2 = 1.0 - smoothstep(0.25, 0.75, abs(fract((px.x + px.y) / 5.0) - 0.5) * 2.0 + 1.0 - max(shade - 0.55, 0.0) * 3.5);
	body = mix(body, uInk.rgb, uStyle.z * max(sl, sl2) * 0.55);
	// contour rings: where evenly spaced cutting planes meet the surface. The ring count is set
	// by the kick, the rings crawl with evolve, and a scan band inks them heavy in the second ink.
	float nC = uStyle2.x;
	// The Input picture, drawn the way a draughtsman would tone it: hatching whose line weight
	// follows the picture. tone is 0 where the picture matches the face it is drawn on and 1 where
	// it is furthest from it, in the direction of the ink used (so the picture is never a negative).
	float pic = 0.0, tone = 0.0, toneCut = 0.0;
	if (uPic.x > 0.5) {
		vec4 Pc = texture(sTD2DInputs[3], uv);
		pic = step(0.5, Pc.a) * cov;
		// brightness half way between luminance and the strongest channel, so a saturated colour
		// reads as a mid tone and not as near black   [tone v4]
		float lum = picLum(Pc.rgb);
		const vec3 LW = vec3(0.299, 0.587, 0.114);
		vec3 hc = mix(uInk.rgb, uPaper.rgb, step(0.5, fill));
		tone = dot(hc, LW) < dot(body, LW) ? 1.0 - lum : lum;
		toneCut = dot(uAccent.rgb, LW) < dot(body, LW) ? 1.0 - lum : lum;
		tone = pow(smoothstep(0.10, 0.95, tone), 1.4);
		toneCut = pow(smoothstep(0.10, 0.95, toneCut), 1.4);
		if (nC < 0.5) {
			// two inks: the first carries light and dark (one diagonal, crossed in the darkest parts),
			// the second carries how strongly coloured the picture is (level lines)
			float sat = max(Pc.r, max(Pc.g, Pc.b)) - min(Pc.r, min(Pc.g, Pc.b));
			float h1 = abs(fract((px.x - px.y) / 6.0) - 0.5) * 2.0;
			float h2 = abs(fract((px.x + px.y) / 6.0 + 0.25) - 0.5) * 2.0;
			float h3 = abs(fract(px.y / 5.0) - 0.5) * 2.0;
			float a1 = (1.0 - smoothstep(-0.18, 0.18, h1 - tone * 0.74)) * step(0.03, tone);
			float a2 = (1.0 - smoothstep(-0.18, 0.18, h2 - (tone - 0.62) * 1.6)) * step(0.62, tone);
			float a3 = (1.0 - smoothstep(-0.2, 0.2, h3 - (sat - 0.25) * 0.8)) * step(0.3, sat) * (1.0 - step(0.5, fill));
			body = mix(body, uAccent.rgb, a3 * pic);
			body = mix(body, hc, max(a1, a2) * pic);
		}
	}
	if (nC > 0.5) {
		float v = D.z * nC - uAudio.w * 0.8;
		float fw = max(fwidth(D.z) * nC, 1e-4);
		float dpx = (0.5 - abs(fract(v) - 0.5)) / fw;
		float band = 1.0 - smoothstep(0.02, 0.10, abs(D.z - uStyle2.w));
		float wpx = 0.75 + 1.9 * band + 0.6 * kick;
		// with an Input picture the rings carry it: thin where it is light, swelling to touch where it is dark
		if (pic > 0.5) {
			wpx = mix(0.25, min(0.5 / fw * 0.72, 10.0), tone) + 1.2 * band;   // [tone v3] never quite touching
			// a face square to the axis has no rings to carry the picture (they are more than
			// about 25 px apart there), so it is hatched instead   [tone v2]
			float sq = 1.0 - smoothstep(0.02, 0.06, fw);
			float hh = abs(fract((px.x - px.y) / 6.0) - 0.5) * 2.0;
			body = mix(body, uInk.rgb, sq * (1.0 - smoothstep(-0.18, 0.18, hh - tone * 0.74)) * step(0.03, tone));
		}
		float ring = (1.0 - smoothstep(wpx - 0.5, wpx + 0.5, dpx)) * step(fw, 0.9);
		body = mix(body, uAccent.rgb, 0.16 * band);
		body = mix(body, mix(uInk.rgb, uAccent.rgb, band), ring);
	}
	// cut faces: tinted and hatched, direction alternating by slab
	float isCut = smoothstep(0.4, 0.6, D.y);
	float par = mod(floor(D.x + 0.5), 2.0) * 2.0 - 1.0;
	float hs = max(uStyle.x, 3.0);
	float hv = abs(fract((px.x + par * px.y) / hs + uAudio.w * 0.6) - 0.5) * hs;
	float hatch = 1.0 - smoothstep(0.5, 1.4, hv);
	// with an Input picture the cut-face hatching carries it in its line weight
	if (pic > 0.5) {
		float hp = min(hs, 7.0);
		float hq = abs(fract((px.x + par * px.y) / hp + uAudio.w * 0.6) - 0.5) * 2.0;
		hatch = (1.0 - smoothstep(-0.18, 0.18, hq - toneCut * 1.05)) * step(0.02, toneCut);
	}
	vec3 cutc = mix(body, uAccent.rgb, uStyle.y);
	cutc = mix(cutc, uAccent.rgb, hatch * 0.9);
	body = mix(body, cutc, isCut);
	// Input on the sheet: the picture is drafted onto the paper behind the parts, the way the parts
	// themselves are drawn: its edges traced as ink lines, its tones as hatching that swells on the
	// beat, its strong colours as level lines in the second ink. The parts stay clean on top of it.
	if (uPic.z > 0.001) {
		const vec3 LW2 = vec3(0.299, 0.587, 0.114);
		vec2 t = 1.5 / RES;
		vec3 I = texture(sTD2DInputs[4], uv).rgb;
		float l0 = picLum(I);
		float gx = picLum(texture(sTD2DInputs[4], uv + vec2(t.x, 0.0)).rgb) - picLum(texture(sTD2DInputs[4], uv - vec2(t.x, 0.0)).rgb);
		float gy = picLum(texture(sTD2DInputs[4], uv + vec2(0.0, t.y)).rgb) - picLum(texture(sTD2DInputs[4], uv - vec2(0.0, t.y)).rgb);
		float tn = dot(uInk.rgb, LW2) < dot(uPaper.rgb, LW2) ? 1.0 - l0 : l0;
		tn = pow(smoothstep(0.10, 0.95, tn), 1.4) * (0.85 + 0.25 * kick);
		float sat = max(I.r, max(I.g, I.b)) - min(I.r, min(I.g, I.b));
		float h1 = abs(fract((px.x - px.y) / 7.0) - 0.5) * 2.0;
		float h2 = abs(fract((px.x + px.y) / 7.0 + 0.25) - 0.5) * 2.0;
		float h3 = abs(fract(px.y / 6.0) - 0.5) * 2.0;
		float a1 = (1.0 - smoothstep(-0.16, 0.16, h1 - tn * 0.70)) * step(0.03, tn);
		float a2 = (1.0 - smoothstep(-0.16, 0.16, h2 - (tn - 0.62) * 1.5)) * step(0.62, tn);
		float a3 = (1.0 - smoothstep(-0.2, 0.2, h3 - (sat - 0.25) * 0.8)) * step(0.3, sat);
		float trace = smoothstep(0.10, 0.30, length(vec2(gx, gy)));
		col = mix(col, uAccent.rgb, a3 * 0.55 * uPic.z * shown);
		col = mix(col, uInk.rgb, max(max(a1, a2) * 0.62, trace) * uPic.z * shown);
	}
	// a key that has just landed is inked solid
	body = mix(body, uAccent.rgb, clamp(D.z, 0.0, 1.0) * 0.9 * step(uStyle2.z, 0.5));
	col = mix(col, body, cov * shown);
	col = mix(col, lineCol, lineInk * shown);

	// annotation geometry
	float aInk = 0.0, aAcc = 0.0;
	for (int i = 0; i < 40; i++) {
		vec4 s = uL0[i];
		vec4 k = uL1[i];
		if (k.x < 0.5) continue;
		float w = k.z;
		float d = 1e6;
		vec2 a = s.xy, b = s.zw;
		vec2 dir = normalize(b - a + vec2(1e-5, 0.0));
		if (k.x < 1.5) {
			d = sdSeg(px, a, b);
		} else if (k.x < 2.5) {
			float hl = min(13.0, 0.4 * length(b - a));
			d = sdSeg(px, a + dir * hl * 0.8, b - dir * hl * 0.8);
			d = min(d, arrowHead(px, a, dir, hl) + w);
			d = min(d, arrowHead(px, b, -dir, hl) + w);
		} else if (k.x < 3.5) {
			float t = dot(px - a, dir);
			float dash = step(fract(t / 14.0 - uAudio.w * 0.5), 0.6);
			d = sdSeg(px, a, b) + (1.0 - dash) * 10.0;
		} else if (k.x < 4.5) {
			d = min(sdSeg(px, a, b), length(px - a) - 3.5 + w);
		} else if (k.x < 5.5) {
			vec2 c = 0.5 * (a + b), hsz = 0.5 * abs(b - a);
			vec2 q = abs(px - c) - hsz;
			d = abs(length(max(q, 0.0)) + min(max(q.x, q.y), 0.0));
		} else if (k.x < 6.5) {
			d = abs(length(px - a) - s.z);
		} else {
			// tick: short cross stroke at a
			d = sdSeg(px, a - vec2(4.0, -4.0), a + vec2(4.0, -4.0));
		}
		float m = 1.0 - smoothstep(w - 0.6, w + 0.6, d);
		if (k.y < 0.5) aInk = max(aInk, m); else aAcc = max(aAcc, m);
	}
	col = mix(col, uAccent.rgb, aAcc * shown);
	col = mix(col, uInk.rgb, aInk * shown);

	// lettering: white text takes the ink, red text takes the second ink
	vec4 T = texture(sTD2DInputs[2], uv);
	// knock-out: clear the line work to bare paper just around the letters (Describe labels that sit on a drawing)
	if (uPic.y > 0.5) {
		float ko = T.a;
		for (int i = 0; i < 8; i++) {
			float an = float(i) * 0.7854;
			vec2 o = vec2(cos(an), sin(an)) / RES;
			ko = max(ko, texture(sTD2DInputs[2], uv + o * 3.0).a);
			ko = max(ko, 0.8 * texture(sTD2DInputs[2], uv + o * 6.0).a);
		}
		col = mix(col, pap, ko * shown);
	}
	vec3 tc = T.rgb / max(T.a, 1e-3);
	col = mix(col, tc.g > 0.5 ? uInk.rgb : uAccent.rgb, T.a * shown);

	// the plotter head
	if (reveal < 1.0)
		col = mix(col, uAccent.rgb, 0.8 * (1.0 - smoothstep(0.5, 2.5, abs(px.x - front))));

	fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
