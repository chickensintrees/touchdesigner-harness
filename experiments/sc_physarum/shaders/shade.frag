// Display: turns the trail map into a physical picture. One look per take.
// inputs: 0 trail (r trail, g stain, b flight glow), 1 attractant map (r attract, g wall, b aux), 2 quarter-size blur of the trail
// looks: 0 film on a lightbox, 1 gold in black marble, 2 mould on a paper sheet, 3 1-bit, 4 culture dishes on a
//        light table, 5 screenprint poster, 6 CRT phosphor, 7 rust under filing-cabinet paint
uniform vec4 uLook;   // x look, y evolve, z seed, w shot age (s)
uniform vec4 uAudio;  // x pulse, y hit_low, z hit_high, w energy
uniform vec4 uAudio2; // x beat_pos, y flip, z bass, w vocals
uniform vec4 uView;   // x zoom, y rotation, z pan x, w pan y
uniform vec4 uView2;  // x pitch of a tilted view (0 = straight down), y camera height, z invert (1-bit), w 1 in Describe mode (the words are kept readable)
out vec4 fragColor;

const float ASPECT = 16.0 / 9.0;
const float TAU = 6.2831853;
const vec2 PX = vec2(1.0 / 1280.0, 1.0 / 720.0);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float vnoise(vec2 p)
{
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

float fbm(vec2 p)
{
	float s = 0.0, a = 0.5;
	for (int i = 0; i < 4; i++) { s += a * vnoise(p); p = p * 2.03 + 17.0; a *= 0.5; }
	return s;
}

// ---- view: screen uv -> position on the trail map ----
float gDist = 1.0;   // distance along the view ray, in frame heights (1 when looking straight down)
float gSky = 0.0;    // 1 above the horizon of a tilted view
vec3 gRay = vec3(0.0, 0.0, -1.0);

vec2 viewMap(vec2 uv)
{
	vec2 s = (uv - 0.5) * vec2(ASPECT, 1.0);
	float c = cos(uView.y), sn = sin(uView.y);
	if (uView2.x < 0.001)
	{
		vec2 q = mat2(c, -sn, sn, c) * s / uView.x;
		return q / vec2(ASPECT, 1.0) + 0.5 + uView.zw;
	}
	float th = uView2.x;
	vec3 fwd = vec3(0.0, -sin(th), -cos(th));
	vec3 up = vec3(0.0, cos(th), -sin(th));
	vec3 rd = normalize(s.x * vec3(1, 0, 0) + s.y * up + 1.5 * fwd);
	gRay = rd;
	if (rd.y > -0.004)
	{
		gSky = 1.0;
		gDist = 99.0;
		return vec2(0.5);
	}
	float t = uView2.y / -rd.y;
	gDist = t;
	vec2 pl = vec2(rd.x * t, -rd.z * t);
	pl = mat2(c, -sn, sn, c) * pl / uView.x;
	return pl / vec2(ASPECT, 1.0) + 0.5 + uView.zw;
}

float gLod = 0.0;    // 0 near, 1 far: far away the quarter-size blur stands in for mipmaps

vec4 trailAt(vec2 p)
{
	vec2 o = PX * 0.75;
	vec4 t = 0.25 * (texture(sTD2DInputs[0], p + o) + texture(sTD2DInputs[0], p - o)
		+ texture(sTD2DInputs[0], p + vec2(o.x, -o.y)) + texture(sTD2DInputs[0], p + vec2(-o.x, o.y)));
	return mix(t, texture(sTD2DInputs[2], p), gLod);
}

float heightAt(vec2 p, float k) { return 1.0 - exp(-trailAt(p).r * k); }

vec3 normalAt(vec2 p, float k, float relief)
{
	vec2 e = PX * (1.5 + 3.0 * gLod);
	float hx = heightAt(p + vec2(e.x, 0.0), k) - heightAt(p - vec2(e.x, 0.0), k);
	float hy = heightAt(p + vec2(0.0, e.y), k) - heightAt(p - vec2(0.0, e.y), k);
	return normalize(vec3(-hx * relief, -hy * relief, 1.0));
}

void main()
{
	vec2 uv = vUV.st;
	float look = uLook.x;
	float age = uLook.w;
	float seed = uLook.z;
	vec2 scr = (uv - 0.5) * vec2(ASPECT, 1.0);
	float bezel = 0.0;

	if (look > 2.5 && look < 3.5)
		uv = (floor(uv / (PX * 2.0)) + 0.5) * PX * 2.0;        // fat pixels for the 1-bit look
	if (look > 5.5 && look < 6.5)
	{
		// a curved tube
		vec2 c = uv - 0.5;
		c *= 1.0 + 0.16 * dot(c, c) + 0.10 * c.yx * c.yx;
		c *= 1.045;
		bezel = max(smoothstep(0.485, 0.5, abs(c.x)), smoothstep(0.48, 0.5, abs(c.y)));
		uv = c + 0.5;
	}

	vec2 p = viewMap(uv);
	vec2 pc = p;                                             // unmirrored: the card the blot is printed on
	if (look > 8.5 && look < 9.5)
		p.x = 0.5 - abs(p.x - 0.5);                          // a folded inkblot: one half, printed twice
	gLod = clamp((gDist - 1.6) / 4.0, 0.0, 1.0);
	vec4 t = trailAt(p);
	vec4 a = texture(sTD2DInputs[1], p);
	vec4 g = texture(sTD2DInputs[2], p);
	float v = 1.0 - exp(-t.r * 0.22);
	float halo = 1.0 - exp(-g.r * 0.25);
	float fly = 1.0 - exp(-t.b * 0.5);
	float grain = hash(uv * 911.0 + fract(uLook.y * 3.7)) - 0.5;
	vec3 col = vec3(0.0);

	if (look > 9.5)
	{
		// 10: toner on photocopier glass. No veins: the agents themselves, as grains.
		float cnt = texture(sTD2DInputs[0], p).a;
		float dens = 1.0 - exp(-cnt * mix(0.7, 2.6, smoothstep(0.2, 0.6, a.r)));
		float smudge = 1.0 - exp(-g.a * 1.6);
		float bx = fract(uAudio2.x * 0.25) * 1.3 - 0.15;                    // the scan bar crosses once per bar
		float bar = exp(-pow((uv.x - bx) / 0.035, 2.0));
		float wake = smoothstep(bx - 0.5, bx, uv.x) * step(uv.x, bx);       // glass still glowing behind the bar
		vec3 glass = vec3(0.60, 0.66, 0.58) * (0.92 + 0.08 * fbm(uv * vec2(ASPECT, 1.0) * 3.0));
		glass *= 0.62 + 0.38 * wake + 1.5 * bar + 0.9 * uAudio.y + 0.5 * exp(-age * 6.0);
		col = glass * (1.0 - 0.45 * smudge);
		col = mix(col, vec3(0.012, 0.012, 0.016), dens);
		col = mix(col, vec3(0.02), min(1.0, fly * 0.7));                   // grains in flight smear
		col = mix(col, col * 0.30, uView2.w * 0.75 * smoothstep(0.35, 0.65, a.r));   // Describe: the letters stay printed under the grains
		col += vec3(0.75, 1.0, 0.7) * bar * 0.25;
		col = mix(col, vec3(0.80, 0.86, 0.78) * (1.0 - dot(col, vec3(0.33))), step(0.5, uAudio2.y) * step(0.5, seed));   // some shots: the snare prints a negative
		col *= 1.0 - 0.55 * dot(scr, scr);
		col += grain * 0.02;
	}
	else if (look > 8.5)
	{
		// 9: a folded inkblot on a card, on a desk blotter
		vec2 cq = (pc - 0.5) * vec2(ASPECT, 1.0);
		vec2 cd = abs(cq) - vec2(0.66, 0.46);
		float card = 1.0 - smoothstep(0.0, 0.004, max(cd.x, cd.y));
		vec2 sq = abs(cq + vec2(-0.012, 0.016)) - vec2(0.66, 0.46);
		float shadow = 1.0 - smoothstep(-0.01, 0.035, max(sq.x, sq.y));
		vec3 desk = vec3(0.045, 0.085, 0.065) * (0.8 + 0.4 * fbm(pc * vec2(ASPECT, 1.0) * 90.0));
		desk *= 1.0 - 0.7 * shadow;
		float fibre = fbm(pc * vec2(ASPECT, 1.0) * 260.0);
		vec3 paper = vec3(0.90, 0.87, 0.78) * (0.93 + 0.07 * fibre);
		paper *= 1.0 - 0.10 * exp(-abs(cq.x) / 0.004);                       // the fold
		bool redInk = fract(seed * 5.37) < 0.35;
		vec3 inkc = redInk ? vec3(0.27, 0.016, 0.012) : vec3(0.012, 0.014, 0.024);
		float fuzz = fbm(p * vec2(ASPECT, 1.0) * 150.0);
		float stain = min(1.0, t.g * 1.2);
		float wash = smoothstep(0.05, 0.5, halo + 0.25 * (fuzz - 0.5));
		float mass = smoothstep(0.30, 0.42, halo * 1.25 + 0.55 * v + 0.12 * (fuzz - 0.5) + 0.10 * uAudio.x);
		float veins = smoothstep(0.16, 0.30, v + 0.10 * (fuzz - 0.5));
		col = paper;
		col = mix(col, mix(paper, inkc, 0.30) * vec3(0.96, 0.97, 1.05), stain * 0.55);   // where the water went
		col = mix(col, mix(paper, inkc, 0.62), wash * 0.75);
		col = mix(col, inkc, max(mass, veins));
		col = mix(col, inkc, step(0.25 + 0.7 * hash(floor(uv * vec2(640.0, 360.0))), fly));   // spatter
		col += vec3(0.25) * pow(max(0.0, mass * (fuzz - 0.55) * 2.2), 2.0) * (1.0 + 2.0 * uAudio.y);  // wet sheen
		col = mix(desk, col, card);
		col *= (0.92 + 0.10 * uAudio.x) * (1.0 - 0.40 * dot(scr, scr));
		col += grain * 0.015;
	}
	else if (look > 7.5)
	{
		// 8: the ink of a notice runs down the sheet
		bool gold = fract(seed * 3.71) < 0.45;
		float fibre = fbm(p * vec2(ASPECT, 1.0) * 240.0);
		vec3 paper = (gold ? vec3(0.80, 0.56, 0.10) : vec3(0.84, 0.36, 0.46)) * (0.90 + 0.10 * fibre);
		vec3 inkc = gold ? vec3(0.21, 0.012, 0.010) : vec3(0.010, 0.022, 0.050);
		float glyph = smoothstep(0.35, 0.65, a.r);
		float run = smoothstep(0.10, 0.28, v);
		float feather = smoothstep(0.03, 0.35, halo + 0.2 * (fibre - 0.5));
		float stain = min(1.0, t.g * 1.2);
		col = paper;
		col = mix(col, mix(paper, inkc, 0.35), stain * 0.35);
		col = mix(col, mix(paper, inkc, 0.55), feather * 0.55);
		col = mix(col, mix(paper, inkc, 0.82), run);
		col = mix(col, inkc * 0.6, glyph * 0.95);
		vec3 n = normalAt(p, 0.22, 6.0);
		float spec = pow(max(dot(n, normalize(vec3(0.25, 0.55, 0.8))), 0.0), 30.0);
		col += vec3(1.0, 0.95, 0.9) * spec * run * (0.10 + 0.55 * uAudio.y);      // wet ink catches the tube on a kick
		float tube = 0.90 + 0.12 * uAudio.x - 0.07 * uAudio.z * step(0.5, fract(uLook.y * 31.0));
		col *= tube * (1.0 - 0.40 * dot(scr, scr));
		col *= 0.25 + 0.75 * smoothstep(0.0, 0.25, age);
		col += grain * 0.015;
	}
	else if (look < 0.5)
	{
		// 0: X-ray film on a lightbox. The tube flickers on at the cut.
		float lit = age < 0.36 ? smoothstep(0.0, 0.05, age) * (0.35 + 0.65 * step(0.45, fract(age * 14.0 + seed))) : 1.0;
		vec3 film = vec3(0.010, 0.022, 0.040);
		col = film;
		col += vec3(0.05, 0.16, 0.24) * a.b * 0.42;                        // the object itself, a ghost
		col += vec3(0.08, 0.30, 0.48) * halo;
		col += vec3(0.55, 0.86, 1.0) * v * v * 1.05;
		col += vec3(0.75, 0.92, 1.0) * fly * 0.45;
		float bar = exp(-pow((uv.y - fract(uAudio2.x * 0.25)) / 0.05, 2.0));  // a slow scan, one pass per bar
		col *= 1.0 + 0.30 * uAudio.x + 0.25 * bar;
		col = mix(col, col.bgr * vec3(1.3, 0.9, 0.6), 0.3 * uAudio2.y);    // snare: the film goes warm
		col *= lit * (1.0 - 0.50 * dot(scr, scr));
		col += grain * 0.022;
	}
	else if (look < 1.5 || look > 6.5)
	{
		// 1: gold veins in black marble.  7: rust creeping under putty filing-cabinet paint.
		bool rust = look > 6.5;
		float k = rust ? 0.30 : 0.16;
		float h = heightAt(p, k);
		vec3 n = normalAt(p, k, rust ? 5.0 : 9.0);
		float la = uLook.y * 0.5 + seed * TAU;
		vec3 L = normalize(vec3(cos(la), sin(la) * 0.6 + 0.5, 0.55));
		vec3 V = uView2.x < 0.001 ? vec3(0.0, 0.0, 1.0) : normalize(vec3(-gRay.x, gRay.z, -gRay.y));
		vec3 Hh = normalize(L + V);
		float diff = max(dot(n, L), 0.0);
		float kickLight = 1.0 + 1.6 * uAudio.y + 0.4 * uAudio.x + 3.0 * exp(-age * 7.0);   // and a flash at the cut
		if (!rust)
		{
			float m = smoothstep(0.10, 0.28, h);
			vec2 sp = p * vec2(ASPECT, 1.0);
			float w1 = TDSimplexNoise(sp * 1.7 + seed * 9.0);
			float w2 = TDSimplexNoise(sp * 4.0 + w1 * 1.3 + 5.0);
			float vein = pow(1.0 - abs(w2), 14.0) * (1.0 - gLod);
			vec3 stone = vec3(0.010, 0.011, 0.014) + vec3(0.16, 0.17, 0.19) * vein * (0.5 + 0.5 * w1) + 0.006 * w1;
			stone += vec3(0.9, 0.95, 1.0) * pow(max(dot(vec3(0, 0, 1), Hh), 0.0), 160.0) * 0.10 * kickLight;   // polish
			float spec = pow(max(dot(n, Hh), 0.0), 38.0);
			vec3 gold = vec3(1.0, 0.72, 0.30) * (0.10 + 0.95 * diff) + vec3(1.0, 0.93, 0.70) * spec * 1.8 * kickLight;
			gold *= 0.55 + 0.6 * h;
			col = mix(stone, gold, m);
			col += vec3(0.25, 0.14, 0.03) * halo * (1.0 - m) * 0.5;       // gold light spilling into the stone
			col += vec3(1.0, 0.9, 0.6) * fly * 1.2;
			vec3 fog = vec3(0.020, 0.016, 0.012);
			col = mix(col, fog, 1.0 - exp(-max(gDist - 1.0, 0.0) * 0.16));
			if (gSky > 0.5)
				col = fog;
			col += vec3(0.42, 0.27, 0.10) * exp(-abs(gRay.y) * 16.0) * (0.35 + 0.25 * uAudio.x);   // glow along the horizon
			col *= 1.0 - 0.35 * dot(scr, scr);
		}
		else
		{
			float eaten = smoothstep(0.16, 0.34, h);
			float blister = smoothstep(0.02, 0.16, h) * (1.0 - eaten);
			float peel = fbm(p * vec2(ASPECT, 1.0) * 60.0);
			vec3 paint = vec3(0.60, 0.55, 0.42) * (0.86 + 0.10 * peel);
			paint *= 0.40 + 0.62 * diff;
			paint += vec3(1.0) * pow(max(dot(n, Hh), 0.0), 24.0) * 0.35 * blister * kickLight;
			float pit = fbm(p * vec2(ASPECT, 1.0) * 220.0);
			vec3 ox = mix(vec3(0.42, 0.16, 0.04), vec3(0.10, 0.045, 0.03), smoothstep(0.35, 0.8, h + 0.3 * (pit - 0.5)));
			ox += vec3(0.5, 0.28, 0.08) * step(0.78, pit) * 0.5;
			ox *= 0.6 + 0.5 * diff;
			col = mix(paint, ox, eaten);
			col = mix(col, col * vec3(0.93, 0.80, 0.62), min(1.0, t.g * 1.3) * (1.0 - eaten));   // the stain it leaves
			col += vec3(1.0, 0.6, 0.2) * fly * 0.5;
			col *= 1.0 + 0.10 * uAudio.x;
			col *= 1.0 - 0.45 * dot(scr, scr);
			col += grain * 0.02;
		}
	}
	else if (look < 2.5)
	{
		// 2: mould on a cream paper sheet
		float fibre = fbm(p * vec2(ASPECT, 1.0) * 240.0);
		vec3 paper = vec3(0.93, 0.89, 0.78) * (0.90 + 0.10 * fibre);
		float ink = 1.0 - smoothstep(0.30, 0.80, a.b);
		paper = mix(paper, vec3(0.10, 0.10, 0.12), ink * (1.0 - a.g));
		paper = mix(paper, vec3(0.30, 0.31, 0.29), a.g);                    // the desk beyond the sheet
		float stain = min(1.0, t.g * 1.2);
		float sh = 1.0 - exp(-trailAt(p + vec2(-2.5, 3.0) * PX).r * 0.22);  // a little relief shadow
		float fuzz = fbm(p * vec2(ASPECT, 1.0) * 420.0 + 3.0);
		col = paper;
		col *= mix(vec3(1.0), vec3(0.84, 0.74, 0.42), stain * 0.85);         // yellow tide mark where it has been
		float bloom = smoothstep(0.06, 0.55, halo + 0.35 * (fuzz - 0.5) * halo);
		col = mix(col, vec3(0.42, 0.52, 0.40), bloom * 0.80);                // grey-green fuzz around the veins
		col *= 1.0 - 0.30 * max(sh - v, 0.0);
		vec3 mould = mix(vec3(0.16, 0.32, 0.24), vec3(0.02, 0.07, 0.06), smoothstep(0.2, 0.75, v + 0.25 * (fuzz - 0.5)));
		col = mix(col, mould, smoothstep(0.10, 0.40, v + 0.18 * (fuzz - 0.5)));
		col += vec3(0.5, 0.6, 0.45) * step(0.93, fuzz) * bloom * 0.25;          // spore specks
		col = mix(col, vec3(0.05, 0.05, 0.06), uView2.w * 0.9 * ink * (1.0 - a.g));   // Describe: the print stays on top of the mould
		col = mix(col, vec3(0.80, 0.86, 0.70), fly * 0.8);                  // spores in flight
		// a fluorescent tube overhead: it buzzes with the hats and pumps a little on the beat
		float tube = 0.90 + 0.10 * uAudio.x - 0.07 * uAudio.z * step(0.5, fract(uLook.y * 31.0));
		col *= tube * vec3(0.97, 1.0, 0.93) * (1.0 - 0.38 * dot(scr, scr));
		col += grain * 0.015;
	}
	else if (look < 3.5)
	{
		// 3: 1-bit, ordered dither
		ivec2 ip = ivec2(floor(gl_FragCoord.xy / 2.0)) & 3;
		int bi = ip.x + ip.y * 4;
		const float bayer[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
		float th = (bayer[bi] + 0.5) / 16.0;
		float val = 1.6 * v * v + 0.85 * halo + 0.22 * a.r + fly;
		val *= 0.75 + 0.5 * uAudio.x;
		float bit = step(th * 0.9 + 0.06, val);
		float inv = uView2.z;
		if (age < 0.10) inv = 1.0 - inv;                                    // the cut lands as a negative flash
		inv = abs(inv - step(0.5, uAudio2.y));                               // snare: negative
		bit = abs(bit - inv);
		col = vec3(bit);
	}
	else if (look < 4.5)
	{
		// 4: culture dishes on a fluorescent light table
		float d = a.b;                                                      // 0 centre .. 1 rim of the dish
		float inDish = 1.0 - a.g;
		vec3 table = vec3(0.80, 0.87, 0.72) * (0.92 + 0.08 * fbm(p * vec2(ASPECT, 1.0) * 40.0));
		table *= 1.0 - 0.35 * (1.0 - smoothstep(1.0, 1.22, d));              // the dish's shadow on the table
		vec3 agar = vec3(0.93, 0.80, 0.50) * (1.0 - 0.18 * d * d);
		col = mix(table, agar, inDish);
		float stain = min(1.0, t.g * 1.3);
		col = mix(col, col * vec3(1.0, 0.62, 0.38), stain * 0.7 * inDish);
		vec3 culture = mix(vec3(0.72, 0.16, 0.10), vec3(0.20, 0.02, 0.03), smoothstep(0.25, 0.8, v));
		col = mix(col, culture, smoothstep(0.08, 0.35, v) * inDish);
		float rim = exp(-pow((d - 1.02) / 0.035, 2.0));
		col = mix(col, vec3(1.0, 1.0, 0.96), rim * 0.75);                   // glass rim catching the light
		col += vec3(1.0, 0.9, 0.7) * fly * 0.4;
		float tube = 0.92 + 0.10 * uAudio.x - 0.06 * uAudio.z * step(0.5, fract(uLook.y * 29.0));
		vec3 far = vec3(0.60, 0.68, 0.55);
		col = mix(col, far, 1.0 - exp(-max(gDist - 1.0, 0.0) * 0.10));
		if (gSky > 0.5)
			col = vec3(0.08, 0.10, 0.08);
		col *= tube * (1.0 - 0.30 * dot(scr, scr));
		col += grain * 0.012;
	}
	else if (look < 5.5)
	{
		// 5: three-colour screenprint, the red screen printed a little out of register
		vec3 inkc = pow(vec3(0.098, 0.169, 0.231), vec3(2.2)), ivory = pow(vec3(0.93, 0.89, 0.80), vec3(2.2));
		vec3 red = pow(vec3(0.86, 0.34, 0.24), vec3(2.2)), yellow = pow(vec3(0.86, 0.71, 0.24), vec3(2.2));
		float tooth = fbm(uv * vec2(ASPECT, 1.0) * 300.0);
		float e = fwidth(v) * 1.2 + 0.01;
		vec2 off = vec2(7.0, -5.0) * PX * (1.0 + 1.5 * uAudio.y);
		float v2 = 1.0 - exp(-trailAt(p + off).r * 0.22);
		col = inkc * (0.90 + 0.16 * tooth);
		col = mix(col, red, smoothstep(0.16 - e, 0.16 + e, v2 + 0.08 * (tooth - 0.5)) * 0.95);
		float subj = smoothstep(0.30, 0.36, a.b + 0.25 * uAudio.x * a.b);
		col = mix(col, yellow, subj * 0.95);
		col = mix(col, ivory, smoothstep(0.30 - e, 0.30 + e, v + 0.06 * (tooth - 0.5)));
		col = mix(col, ivory, step(0.12 + 0.8 * hash(floor(uv * vec2(640.0, 360.0))), fly));   // spores in flight, stippled
		col *= 0.92 + 0.14 * uAudio.x;
		col *= 1.0 - 0.18 * dot(scr, scr);
	}
	else
	{
		// 6: green phosphor on a beige monitor
		float scan = 0.78 + 0.22 * sin(uv.y * 720.0 * 3.14159 / 1.5);
		float glyph = a.r;
		vec3 ph = vec3(0.22, 1.0, 0.30);
		col = vec3(0.012, 0.030, 0.016);
		col += ph * 0.045 * glyph;                                           // the text the mould is eating, dim
		col += ph * (0.55 * v * v + 0.16 * halo) * (1.0 - 0.4 * uView2.w);
		col += ph * 0.55 * smoothstep(0.3, 0.7, glyph) * uView2.w;           // Describe: the text itself stays lit, the veins dimmer
		col += ph * fly * 0.9;
		col *= scan * (0.90 + 0.25 * uAudio.x);
		float roll = exp(-pow((uv.y - fract(uLook.y * 0.9)) / 0.06, 2.0));    // a hum bar rolling up the tube
		col *= 1.0 + 0.35 * roll;
		col *= 1.0 - 0.9 * dot(uv - 0.5, uv - 0.5);
		col = mix(col, col.grb, 0.6 * uAudio2.y);
		col += grain * 0.03;
		vec3 plastic = vec3(0.70, 0.66, 0.55) * (0.55 + 0.3 * uv.y);
		col = mix(col, plastic, bezel);
	}

	col = max(col, 0.0);
	col = col / (1.0 + 0.30 * col) * 1.30;
	fragColor = TDOutputSwizzle(vec4(pow(col, vec3(1.0 / 2.2)), 1.0));
}
