// sc_light_gobo: volumetric light through gobos.
// March from the camera through fog; at each step ask whether each light reaches that point:
// the projector through its gobo (text atlas / blinds / ruled grid / wheel) and through the shadow
// map of the library models (rendered from the light), fluorescent tubes through their louvres,
// a tungsten lamp through its shade. Output is HDR; grade.frag tone-maps it.
// Inputs: 0 = G-buffer from the camera (normal, distance), 1 = G-buffer from the projector
// (alpha = distance: the shadow map), 2 = text atlas (2 x 4 cells of 512x256), or the Input picture when uIn.x is 1.
uniform vec4 uCamP;     // xyz eye, w tan(half hfov)
uniform vec4 uCamT;     // xyz target, w aspect
uniform vec4 uLgtP;     // projector xyz, w tan(half cone)
uniform vec4 uLgtT;     // projector target xyz, w gobo mode
uniform vec4 uLgtC;     // projector colour * intensity, w sheets amount
uniform vec4 uGobo;     // x phrase cell, y rotation, z beat_pos, w blind opening
uniform vec4 uGobo2;    // x invert, y sheet spacing, z gobo scale, w section
uniform vec4 uTube;     // x count, y layout, z intensity, w time
uniform vec4 uTube2;    // x idle level, y z of first tube, z spacing, w projector falloff
uniform vec4 uTubeHit;  // x hits_low, y hits_mid, z slow low env, w slow mid env
uniform vec4 uHit;      // hit_low, hit_mid, hit_high, pulse
uniform vec4 uLamp;     // tungsten lamp xyz, w intensity
uniform vec4 uFog;      // x density, y evolve, z noise amount, w ambient
uniform vec4 uMisc;     // x seed, y shot age, z exposure, w fog noise frequency
uniform vec4 uRoom;     // x half width, y height, z back wall z, w front wall z
uniform vec4 uIn;       // x 1 = input 2 is the Input picture (the projector's slide), y gain, z white balance

out vec4 fragColor;

#define STEPS 64
#define NT 8
#define NP 5
#define NTS 12
#define PI 3.14159265

vec3 Lp, Lf, Lr, Lu;
float Ltan;
vec3 LC;
vec3 tubeA[NT], tubeB[NT], tubeC[NT], tubeX[NT];
float tubeL[NT], tubeLen[NT];
int ntube;
bool gGobo = true;
vec3 PC = vec3(1.0);    // colour of the projector's slide at the last projVis point (1 unless an Input picture is on)

float hash21(vec2 p)
{
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

void basis(vec3 ro, vec3 ta, out vec3 f, out vec3 r, out vec3 u)
{
	f = normalize(ta - ro);
	vec3 up = abs(f.y) > 0.98 ? vec3(0.0, 0.0, -1.0) : vec3(0.0, 1.0, 0.0);
	r = normalize(cross(f, up));
	u = cross(r, f);
}

// ---------------------------------------------------------------- gobos
// mode 6: a comb of thin light planes (a copier's scan bar, a laser level). Where each sits, how bright.
float slitY(int k)
{
	return -0.8 + 1.6 * fract((float(k) + 0.5) / float(NP) + uGobo.z * 0.03125);
}
float slitI(int k)
{
	float y = slitY(k);
	float sel = step(0.5, hash21(vec2(float(k) + 3.0, uTubeHit.x)));       // each kick picks the planes that flare
	float selM = step(0.5, hash21(vec2(float(k) + 11.0, uTubeHit.y)));     // and each snare
	return (0.4 + 1.8 * sel * min(uTubeHit.z, 1.2) + 1.4 * selM * min(uTubeHit.w, 1.2)) * smoothstep(0.0, 0.14, 0.8 - abs(y));
}
float textCell(vec2 q, float idx)
{
	if (q.x < 0.0 || q.x > 1.0 || q.y < 0.0 || q.y > 1.0) return 0.0;
	idx = mod(idx, 8.0);
	float c = mod(idx, 2.0), r = floor(idx / 2.0);
	return textureLod(sTD2DInputs[2], (vec2(c, 3.0 - r) + q) / vec2(2.0, 4.0), 0.0).r;
}

float gobo(vec2 l)
{
	int mode = int(uLgtT.w + 0.5);
	float ca = cos(uGobo.y), sa = sin(uGobo.y);
	l = mat2(ca, -sa, sa, ca) * l;
	l *= uGobo2.z;
	float m = 1.0;
	if (mode == 1) {                                  // one phrase, big
		m = textCell(l * vec2(0.56, 1.12) + 0.5, uGobo.x);
	} else if (mode == 2) {                           // venetian blinds in a window frame
		float s = abs(fract(l.y * 6.5 + 0.5) - 0.5) * 2.0;
		m = 1.0 - smoothstep(uGobo.w - 0.07, uGobo.w + 0.07, s);
		m *= smoothstep(0.015, 0.035, abs(l.x)) * smoothstep(0.015, 0.035, abs(abs(l.x) - 0.47));
		m *= step(abs(l.x), 0.92) * step(abs(l.y), 0.8);
	} else if (mode == 3) {                           // a ruled sheet's grid: rules and filled boxes as light
		vec2 g = l * 3.5 + vec2(0.5, 0.0);
		vec2 c = floor(g), f = fract(g);
		float ln = max(1.0 - smoothstep(0.045, 0.07, min(f.x, 1.0 - f.x)), 1.0 - smoothstep(0.045, 0.07, min(f.y, 1.0 - f.y)));
		float h = hash21(c + floor(uGobo2.w) * 7.3);
		float box = step(0.8, h) * step(0.2, f.x) * step(f.x, 0.8) * step(0.2, f.y) * step(f.y, 0.8);
		float tick = step(h, 0.16) * step(abs(f.x - 0.5), 0.3) * step(abs(f.y - 0.3), 0.035);
		float head = step(0.72, l.y) * step(l.y, 0.9) * step(abs(l.x), 0.8);
		m = max(max(ln * 0.9, box), max(tick, head));
		m *= step(abs(l.x), 0.95) * step(abs(l.y), 0.95);
	} else if (mode == 4) {                           // text as texture: tiled phrases, rows sliding against each other
		vec2 q = l * vec2(1.7, 3.4);
		float row = floor(q.y);
		q.x += row * 0.37 + (mod(row, 2.0) < 0.5 ? 1.0 : -1.0) * uGobo.z * 0.125;
		m = textCell(fract(q), row * 3.0 + floor(q.x) + uGobo.x);
	} else if (mode == 5) {                           // spoked gobo wheel
		float a = atan(l.y, l.x) + uGobo.z * 0.39;
		float r = length(l);
		m = smoothstep(-0.1, 0.1, sin(a * (5.0 + 2.0 * mod(floor(uGobo2.w), 3.0)))) * step(0.16, r);
		m = max(m, step(r, 0.07));
		m *= 1.0 - step(0.55, r) * step(r, 0.6);
	} else if (mode == 6) {                           // comb of slits: contour lines where the planes meet solid things
		m = 0.0;
		for (int k = 0; k < NP; k++)
			m = max(m, (1.0 - smoothstep(0.012, 0.026, abs(l.y - slitY(k)))) * slitI(k));
		return m;
	}
	return mix(m, 1.0 - m, uGobo2.x);
}

// Input picture as the projector's slide: the whole 16:9 frame inside the cone, in colour.
// The blinds and the wheel stay in front of it; the text gobos and the ruled grid are replaced by it.
float goboIn(vec2 l)
{
	int mode = int(uLgtT.w + 0.5);
	float pat = (mode == 2 || mode == 5) ? gobo(l) : 1.0;
	float ca = cos(uGobo.y), sa = sin(uGobo.y);
	vec2 q = (mat2(ca, -sa, sa, ca) * l) * uGobo2.z * vec2(0.58, 1.031) + 0.5;
	bool inside = q.x > 0.0 && q.x < 1.0 && q.y > 0.0 && q.y < 1.0;
	vec3 c = inside ? textureLod(sTD2DInputs[2], q, 0.0).rgb : vec3(0.0);
	c = clamp(c, 0.0, 1.0);
	if (uGobo2.x > 0.5 && (mode == 1 || mode == 4)) c = 1.0 - c;      // the negative take prints the picture's negative
	PC = c * uIn.y;
	return pat;
}

// How much projector light reaches p (gobo x cone x model shadow). fo = distance falloff.
float projVis(vec3 p, out float fo)
{
	fo = 0.0;
	PC = vec3(1.0);
	vec3 d = p - Lp;
	float z = dot(d, Lf);
	if (z < 0.08) return 0.0;
	vec2 l = vec2(dot(d, Lr), dot(d, Lu)) / (z * Ltan);
	float r2 = dot(l, l);
	if (r2 > 1.0) return 0.0;
	float cone = 1.0 - smoothstep(0.86, 1.0, r2);
	float dist = length(d);
	float sd = textureLod(sTD2DInputs[1], l * 0.5 + 0.5, 0.0).a;
	if (sd > 0.0 && sd < dist - 0.05) return 0.0;
	fo = 1.0 / (1.0 + uTube2.w * dist * dist);
	if (!gGobo) return cone;
	if (uIn.x > 0.5) return cone * goboIn(l);
	return cone * gobo(l);
}

// ---------------------------------------------------------------- tubes
vec3 closestOnSeg(vec3 p, vec3 a, vec3 b)
{
	vec3 ab = b - a;
	return a + ab * clamp(dot(p - a, ab) / dot(ab, ab), 0.0, 1.0);
}

void setupTubes()
{
	ntube = int(uTube.x + 0.5);
	int lay = int(uTube.y + 0.5);
	float tm = uTube.w;
	float arrive = uMisc.y < 0.4 ? step(0.45, hash21(vec2(floor(uMisc.y * 24.0), 9.0))) : 1.0;
	for (int i = 0; i < NT; i++) {
		float fi = float(i);
		vec3 a, b, c = vec3(0.72, 1.0, 0.58);
		if (lay == 0) {                               // crosswise on the ceiling, receding
			float z = uTube2.y - fi * uTube2.z;
			a = vec3(-0.8, uRoom.y - 0.1, z); b = vec3(0.8, uRoom.y - 0.1, z);
		} else if (lay == 1) {                        // two rows running away from the camera
			float x = (mod(fi, 2.0) * 2.0 - 1.0) * 2.4;
			float z = uTube2.y - floor(fi / 2.0) * uTube2.z;
			a = vec3(x, uRoom.y - 0.1, z - 0.7); b = vec3(x, uRoom.y - 0.1, z + 0.7);
		} else if (lay == 3) {                        // lying on the floor
			a = vec3(-1.0 + fi * 1.3, 0.035, uTube2.y - fi * 0.8);
			b = a + vec3(1.0, 0.0, 0.55);
		} else {                                      // bare tubes leaning on the back wall
			float x = (fi - 0.5 * float(ntube - 1)) * uTube2.z + (hash21(vec2(fi, 3.0)) - 0.5) * 0.3;
			float zz = uTube2.y + hash21(vec2(fi, 5.0)) * 0.5;
			float len = 1.2 + 0.9 * hash21(vec2(fi, 11.0 + floor(uMisc.x * 8.0)));
			a = vec3(x, 0.03, zz);
			b = a + vec3((hash21(vec2(fi, 8.0)) - 0.5) * 0.5, len, -0.12);
			float k = mod(fi + floor(uMisc.x * 5.0), 5.0);
			c = k < 0.5 ? vec3(0.72, 1.0, 0.58) : k < 1.5 ? vec3(0.38, 0.62, 1.0) : k < 2.5 ? vec3(0.72, 1.0, 0.58) : k < 3.5 ? vec3(1.0, 0.5, 0.2) : vec3(0.38, 0.62, 1.0);
		}
		float selL = step(0.45, hash21(vec2(fi, uTubeHit.x)));
		float selM = step(0.45, hash21(vec2(fi + 7.0, uTubeHit.y)));
		float envS = max(selL * uTubeHit.z, selM * uTubeHit.w);
		float envF = max(selL * uHit.x, selM * uHit.y);
		float stut = step(0.5, hash21(vec2(fi, floor(tm * 24.0))));       // a ballast catching
		float strike = envF > 0.22 ? stut : 1.0;
		float hum = 0.93 + 0.07 * sin(tm * 97.0 + fi * 2.1);
		float dead = lay == 3 ? 1.0 : step(0.12, hash21(vec2(fi, 21.0 + floor(uGobo2.w))));  // one tube in eight is out this section
		// corridor: a pulse of light runs down the row toward the camera every two beats
		float chase = lay == 0 ? exp(-9.0 * fract(uGobo.z * 0.5 + fi / float(max(ntube, 1)))) : 0.0;
		float lv = ((uTube2.x + chase * 1.1) * dead + envS * 1.25) * strike * hum * arrive;
		tubeA[i] = a; tubeB[i] = b; tubeC[i] = c; tubeX[i] = normalize(b - a); tubeLen[i] = length(b - a);
		tubeL[i] = i < ntube ? lv * uTube.z : 0.0;
	}
}

// Light from the tubes at p (surf = 1: on a surface with normal n; 0: in the fog). Written without
// branches or a variable loop count: a version with early-outs and "i < ntube" cost about 0.1 ms
// per call per lit tube at 1280x720 (20 ms for 8 tubes on 64 steps).
vec3 tubeFog(vec3 p, vec3 n, float surf)
{
	vec3 c = vec3(0.0);
	float louv = uTube.y < 1.5 ? 1.0 : 0.0;
	for (int i = 0; i < NT; i++) {
		vec3 pa = p - tubeA[i];
		float along = dot(pa, tubeX[i]);
		vec3 d = tubeX[i] * clamp(along, 0.0, tubeLen[i]) - pa;
		float d2 = dot(d, d);
		float I = tubeL[i] / (d2 + 0.06) * (1.0 - smoothstep(13.0, 26.0, d2));
		float s = abs(fract(dot(p, tubeX[i]) * 3.0) - 0.5) * 2.0;
		float lv = smoothstep(0.25, 0.75, d.y * inversesqrt(d2 + 1e-4)) * (0.25 + 0.75 * smoothstep(0.35, 0.6, s));
		I *= mix(1.0, max(dot(n, d) * inversesqrt(d2 + 1e-4), 0.0), surf);
		c += tubeC[i] * (I * mix(1.0, lv, louv));
	}
	return c;
}

vec3 lampLight(vec3 p, vec3 n, bool surf)
{
	if (uLamp.w <= 0.0) return vec3(0.0);
	vec3 d = p - uLamp.xyz;
	float d2 = dot(d, d);
	float dl = sqrt(d2 + 1e-5);
	float cone = smoothstep(0.45, 0.8, -d.y / dl);
	float I = uLamp.w * cone / (d2 + 0.04);
	if (surf) I *= max(dot(n, -d) / dl, 0.0);
	return vec3(1.0, 0.56, 0.2) * I;
}

// ---------------------------------------------------------------- fog
float fogD(vec3 p)
{
	float e = uFog.y;
	float n = TDSimplexNoise(p * 0.42 * uMisc.w + vec3(e * 0.33, -e * 0.1, e * 0.21));
	float n2 = TDSimplexNoise(p * 1.15 * uMisc.w + vec3(-e * 0.5 + n * 0.8, n * 0.9, e * 0.3));   // warped by the first: swirl
	float d = 1.0 + uFog.z * (0.75 * n + 0.5 * n2);
	d *= 0.55 + 0.9 * exp(-max(p.y, 0.0) * 0.45);                                       // heavier near the floor
	return uFog.x * max(d, 0.04);
}

float phase(float c)
{
	float g = 0.55;
	return (1.0 - g * g) / pow(1.0 + g * g - 2.0 * g * c, 1.5);
}

// ---------------------------------------------------------------- surfaces
float roomHit(vec3 ro, vec3 rd, out vec3 n)
{
	vec3 lo = vec3(-uRoom.x, 0.0, uRoom.z), hi = vec3(uRoom.x, uRoom.y, uRoom.w);
	vec3 t1 = (lo - ro) / rd, t2 = (hi - ro) / rd;
	vec3 tm = max(t1, t2);
	float t = min(tm.x, min(tm.y, tm.z));
	n = t == tm.x ? vec3(-sign(rd.x), 0.0, 0.0) : (t == tm.y ? vec3(0.0, -sign(rd.y), 0.0) : vec3(0.0, 0.0, -sign(rd.z)));
	return t;
}

vec3 roomAlbedo(vec3 p, vec3 n)
{
	if (n.y > 0.5) {                                 // carpet tiles
		vec2 g = abs(fract(p.xz / 0.6) - 0.5);
		float seam = smoothstep(0.47, 0.5, max(g.x, g.y));
		float sp = hash21(floor(p.xz * 90.0));
		return vec3(0.20, 0.21, 0.19) * (0.8 + 0.3 * sp) * (1.0 - 0.45 * seam);
	}
	if (n.y < -0.5) {                                // ceiling tiles
		vec2 g = abs(fract(p.xz / 1.2) - 0.5);
		return vec3(0.34, 0.33, 0.29) * (1.0 - 0.6 * smoothstep(0.47, 0.5, max(g.x, g.y)));
	}
	float skirt = step(p.y, 0.12);
	return mix(vec3(0.42, 0.40, 0.35), vec3(0.08), skirt);
}

vec3 shade(vec3 p, vec3 n, vec3 alb)
{
	vec3 c = vec3(0.0);
	vec3 L = Lp - p;
	float dl = length(L);
	float fo;
	float v = projVis(p + n * 0.03, fo);
	c += LC * PC * v * fo * max(dot(n, L / dl), 0.0);
	if (ntube > 0) c += tubeFog(p, n, 1.0) * 0.6;
	c += lampLight(p, n, true);
	c += vec3(0.6, 0.8, 1.0) * uFog.w * 0.6;
	return c * alb;
}

float segRayDist(vec3 ro, vec3 rd, float tmax, vec3 a, vec3 b)
{
	vec3 ab = b - a, ao = ro - a;
	float A = dot(ab, ab), B = dot(ab, rd), C = dot(ab, ao), D = dot(rd, ao);
	float den = A - B * B;
	float s = den > 1e-5 ? clamp((C - B * D) / den, 0.0, 1.0) : 0.0;
	float t = clamp(B * s - D, 0.0, tmax);
	s = clamp((C + B * t) / A, 0.0, 1.0);
	return length(ro + rd * t - (a + ab * s));
}

void main()
{
	vec2 uv = vUV.st;
	vec2 sc = uv * 2.0 - 1.0;
	vec3 ro = uCamP.xyz, cf, cr, cu;
	basis(ro, uCamT.xyz, cf, cr, cu);
	vec3 rd = normalize(cf + cr * sc.x * uCamP.w + cu * sc.y * uCamP.w / uCamT.w);

	Lp = uLgtP.xyz; Ltan = uLgtP.w;
	// a new shot: the lamp catches for a third of a second before it holds
	LC = uLgtC.rgb * (uMisc.y < 0.33 ? 0.9 * step(0.42, hash21(vec2(floor(uMisc.y * 30.0), 4.0))) : 1.0);
	if (uIn.x > 0.5) LC = mix(LC, vec3(max(LC.r, max(LC.g, LC.b))), uIn.z);   // a picture needs a whiter lamp to keep its colours
	basis(Lp, uLgtT.xyz, Lf, Lr, Lu);
	setupTubes();
	// the tube lying on the floor IS the projector: when its ballast stutters or a hit strikes it, so does the light
	if (uTube.y > 2.5) LC *= clamp(tubeL[0] / max(uTube.z * uTube2.x, 1e-3), 0.2, 1.6);   // never fully dark: the shot must not read as a black frame

	// ---- what solid thing is behind this pixel: a library model (G-buffer) or the room
	vec3 n;
	float tS = roomHit(ro, rd, n);
	vec3 pS = ro + rd * tS;
	vec3 alb = roomAlbedo(pS, n);
	vec4 g = texture(sTD2DInputs[0], uv);
	if (g.a > 0.0 && g.a < tS) {
		tS = g.a;
		pS = ro + rd * tS;
		n = normalize(g.rgb);
		if (dot(n, rd) > 0.0) n = -n;
		alb = vec3(0.50, 0.47, 0.40);
	}
	bool floorHit = !(g.a > 0.0 && g.a <= tS) && n.y > 0.5;
	int gmode = int(uLgtT.w + 0.5);
	vec3 col = shade(pS, n, alb);

	// ---- the fog
	float tmax = min(tS, 40.0);
	float sheets = uLgtC.w;
	bool projOn = dot(uLgtC.rgb, vec3(1.0)) > 0.0;
	// sheet takes carry their image on the layers, tube-only takes have no fine gobo detail: fewer fog steps
	int ns = sheets > 0.0 ? 36 : (projOn && gmode != 6 ? STEPS : 40);
	float dt = tmax / float(ns);
	float fr = mod(floor(uTube.w * 60.0), 64.0);
	float dith = hash21(gl_FragCoord.xy * 0.7071 + fr * vec2(3.71, 7.13));      // white: reads as film grain, no moire
	float t = dt * dith;
	float T = 1.0;
	vec3 acc = vec3(0.0);
	float thin = mix(1.0, 0.8, min(sheets, 1.0));    // sheet takes: clear air, light caught on thin layers
	vec3 amb = vec3(0.55, 0.8, 1.0) * uFog.w;
	for (int i = 0; i < STEPS; i++) {
		if (i >= ns) break;
		vec3 p = ro + rd * t;
		float dens = fogD(p);
		float fo;
		float v = projOn && gmode != 6 ? projVis(p, fo) : 0.0;
		vec3 Li = vec3(0.0);
		if (v > 0.0) Li += LC * PC * v * fo * phase(dot(normalize(p - Lp), -rd)) * thin;
		Li += lampLight(p, vec3(0.0), false);
		Li += amb;
		acc += T * Li * dens * dt;
		T *= exp(-dens * dt * 0.9);
		t += dt;
	}

	// ---- the tubes' glow in the fog: soft, so it gets its own short loop (NTS samples, denser near the eye)
	// instead of riding the main march: 8 line lights on each of 64 steps cost 20 ms.
	if (ntube > 0) {
		float sig = uFog.x * 0.7;
		for (int j = 0; j < NTS; j++) {
			float u = (float(j) + fract(dith + 0.618 * float(j))) / float(NTS);
			float tb = tmax * u * (0.5 + 0.5 * u);
			vec3 p = ro + rd * tb;
			acc += exp(-sig * tb) * tubeFog(p, vec3(0.0), 0.0) * fogD(p) * ((0.5 + u) * tmax / float(NTS));
		}
	}

	// ---- sheets: thin layers of smoke across the beam, each catching the whole gobo image
	if (sheets > 0.0) {
		float sp = uGobo2.y;
		float o0 = dot(ro - Lp, Lf), dn = dot(rd, Lf);
		float ph = fract(uGobo.z * 0.25);
		for (int k = 0; k < 12; k++) {
			float zk = (float(k) + ph) * sp + 0.6;
			float tk = (zk - o0) / dn;
			if (tk <= 0.02 || tk >= tS) continue;
			vec3 p = ro + rd * tk;
			float fo;
			float v = projVis(p, fo);
			float edge = smoothstep(0.0, 0.6, zk - 0.6);
			acc += LC * PC * v * fo * sheets * 0.3 * edge * exp(-uFog.x * tk * 0.9) * (0.7 + 0.5 * fogD(p) / max(uFog.x, 1e-4));
		}
	}
	// ---- slit planes: each plane of light is cut analytically, so it shows a crisp cross-section of the smoke
	if (gmode == 6 && projOn) {
		float ca = cos(uGobo.y), sa = sin(uGobo.y);
		vec3 Lu2 = (-sa * Lr + ca * Lu) * uGobo2.z;
		gGobo = false;
		for (int k = 0; k < NP; k++) {
			vec3 nk = normalize(Lu2 - slitY(k) * Ltan * Lf);
			float dn = dot(rd, nk);
			if (abs(dn) < 1e-4) continue;
			float tk = -dot(ro - Lp, nk) / dn;
			if (tk <= 0.02 || tk >= tS) continue;
			vec3 p = ro + rd * tk;
			float fo;
			float v = projVis(p, fo);
			if (v <= 0.0) continue;
			float thick = 0.03 * dot(p - Lp, Lf) * Ltan;
			float s = fogD(p) / max(uFog.x, 1e-4);
			acc += LC * v * fo * slitI(k) * s * s * uFog.x * thick / max(abs(dn), 0.07) * exp(-uFog.x * tk * 0.9) * 2.2;
		}
		gGobo = true;
	}
	col = col * T + acc;

	// ---- the sources themselves
	for (int i = 0; i < ntube; i++) {
		float d = segRayDist(ro, rd, tS, tubeA[i], tubeB[i]);
		col += tubeC[i] * tubeL[i] * (3.0 / max(uTube.z, 0.05) * (1.0 - smoothstep(0.018, 0.03, d)) + 0.004 / (d * d + 0.004));   // the glass is as bright as the tube, whatever the fog gets
		col += vec3(0.1) * (1.0 - smoothstep(0.018, 0.03, d)) * step(float(i), uTube.x - 0.5);   // a dead tube is still a grey glass stick
	}
	if (floorHit && uTube.y > 1.5) {                 // bare tubes mirror in a polished floor
		vec3 r2 = reflect(rd, vec3(0.0, 1.0, 0.0));
		for (int i = 0; i < ntube; i++) {
			float d = segRayDist(pS, r2, 30.0, tubeA[i], tubeB[i]);
			col += tubeC[i] * tubeL[i] * T * (0.6 * (1.0 - smoothstep(0.02, 0.09, d)) + 0.0012 / (d * d + 0.004));
		}
	}
	vec3 toL = Lp - ro;
	float dL = length(toL);
	if (dL < tS) {                                   // looking into the projector
		float fo;
		float v = projVis(ro, fo);
		float ca = dot(rd, toL / dL);
		col += LC * v * (0.0009 / (1.0009 - ca)) * 0.6;
	}
	if (uLamp.w > 0.0) {
		vec3 tw = uLamp.xyz - ro;
		float dw = length(tw);
		if (dw < tS) col += vec3(1.0, 0.56, 0.2) * uLamp.w * 0.0006 / (1.0006 - dot(rd, tw / dw));
	}
	fragColor = TDOutputSwizzle(vec4(max(col, 0.0), 1.0));
}
