// Point-cloud shapeshifter: every point knows where it sits in shape A and shape B.
// The whole morph is stateless (a function of uMorph.x), so the scene can be cut to at any time.
// The take (build.py TAKES) chooses how the same cloud is laid out and drawn.
uniform sampler2D sA;      // atlas of the shape we leave: rows of position, colour, normal
uniform sampler2D sB;      // atlas of the shape we become
uniform vec4 uMorph;   // x morph progress 0..1, y evolve, z yaw of A, w yaw of B
uniform vec4 uAudio;   // x hit_low, y bass, z vocals, w pulse
uniform vec4 uAudio2;  // x hit_high, y energy, z hit_mid, w beat_pos
uniform vec4 uAccent;  // rgb hot accent of the shape we become (linear), w section_pos
uniform vec4 uLook;    // x point diameter in units of the shape's point spacing, y floor height, z word flag A, w word flag B
uniform vec4 uTake;    // x layout (0 one object, 1 catalogue grid, 2 duel), y colour mode (0 lit texture, 2 raster, 3 two inks, 4 contours), z world scale, w normal sign (-1: seen from inside)
uniform vec4 uShot;    // x age of the shot in seconds, y seed, z arrival burst amount, w focal length in pixels
uniform vec4 uSize;    // x size multiplier, y min px, z max px, w raster cell px
uniform vec4 uInk;     // rgb ink (linear), w how far the texture colour gives way to it
uniform vec4 uInk2;    // rgb second ink, w fog density
uniform vec4 uPaperM;  // rgb paper colour of the flat takes (linear), w 1 when the backdrop is paper
uniform vec4 uGrid;    // x columns, y rows, z fraction of points drawn, w cell under the beat cursor
uniform sampler2D sIn; // the Input picture (another scene's output); black and unread when Input is blank
uniform vec4 uPic;     // x shape A is the picture sheet, y shape B is, z how far objects wear the picture, w input mode (0 none, 1 sheet, 2 screen)
uniform vec4 uDesc;    // x 1 in Describe mode (the lettering explains the technique; no red mark), y how far across lettering its last mark turns red

out vec4 vCol;
out float vSoft;
out float vRad;
out vec3 vPaper;

const float PI = 3.14159265;
const vec3 LUM = vec3(0.2126, 0.7152, 0.0722);

float hash1(float n) { return fract(sin(n * 12.9898) * 43758.5453); }
vec3 hash3(float n) { return fract(sin(vec3(n * 12.9898, n * 78.233, n * 37.719)) * 43758.5453); }

// Divergence-free by construction: each component depends only on the other two axes.
vec3 flow(vec3 p, float t)
{
	vec3 v = vec3(
		sin(p.y * 2.1 + t) + cos(p.z * 1.7 - t * 0.7),
		sin(p.z * 2.3 - t * 0.8) + cos(p.x * 1.9 + t * 0.6),
		sin(p.x * 2.0 + t * 0.9) + cos(p.y * 2.2 - t));
	vec3 q = p * 2.7 + v * 0.6;
	v += 0.5 * vec3(
		sin(q.y * 2.1 - t) + cos(q.z * 1.7 + t),
		sin(q.z * 2.3 + t) + cos(q.x * 1.9 - t),
		sin(q.x * 2.0 - t) + cos(q.y * 2.2 + t));
	return v;
}

vec3 rotY(vec3 p, float a)
{
	float c = cos(a), s = sin(a);
	return vec3(c * p.x + s * p.z, p.y, -s * p.x + c * p.z);
}

// Word points have no texture: colour them from the ident palette across the word.
vec3 wordColour(vec3 p, float r)
{
	vec3 ivory = vec3(0.93, 0.89, 0.80);
	vec3 red = vec3(0.86, 0.34, 0.24);
	vec3 yellow = vec3(0.86, 0.71, 0.24);
	float x = p.x / 2.4 + 0.5;
	vec3 c = mix(ivory, yellow, smoothstep(0.55, 0.95, x + (r - 0.5) * 0.2));
	c = mix(c, red, step(uDesc.y, x) * (1.0 - uDesc.x));        // the last mark of the phrase
	return c;
}

// Input picture. The sheet (picture.py) is 2.4 wide by 1.35 tall and hangs 0.22 above the floor.
vec2 sheetUV(vec3 p) { return vec2(p.x / 2.4 + 0.5, (p.y + 0.28) / 1.35); }
// An object wears the picture as a front projection in its own frame (models are 1 unit tall at most).
vec2 wearUV(vec3 p) { return vec2(0.5 + p.x * 0.5625, p.y + 0.5); }
vec3 picture(vec2 uv) { return textureLod(sIn, clamp(uv, 0.0, 1.0), 0.0).rgb; }

void main()
{
	vec3 g = TDPos();
	float SIDE = float(textureSize(sA, 0).x);
	ivec2 tc = ivec2(clamp(floor((g.xy + 0.5) * (SIDE - 1.0) + 0.5), 0.0, SIDE - 1.0));
	float id = float(tc.x) + float(tc.y) * SIDE;
	vec3 rnd = hash3(id + 1.0);
	float r4 = hash1(id + 7.31);
	int lay = int(uTake.x + 0.5);
	int cmode = int(uTake.y + 0.5);
	float nsign = uTake.w;

	ivec2 tcC = tc + ivec2(0, int(SIDE));
	ivec2 tcN = tc + ivec2(0, 2 * int(SIDE));
	vec4 pA4 = texelFetch(sA, tc, 0);
	vec4 pB4 = texelFetch(sB, tc, 0);
	vec3 pA = pA4.xyz;
	vec3 pB = pB4.xyz;
	vec3 nA = texelFetch(sA, tcN, 0).xyz;
	vec3 nB = texelFetch(sB, tcN, 0).xyz;
	vec3 cA = mix(texelFetch(sA, tcC, 0).rgb, wordColour(pA, rnd.x), uLook.z);
	vec3 cB = mix(texelFetch(sB, tcC, 0).rgb, wordColour(pB, rnd.x), uLook.w);

	int inmode = int(uPic.w + 0.5);
	float yawA = uMorph.z, yawB = uMorph.w;
	if (inmode == 1 || inmode == 3)
	{
		// The cloud is given a picture. As the sheet, each point takes the picture's colour at its
		// place and stands forward by its brightness, so the picture is a relief of points; as an
		// object, it can wear the picture like a slide projected from the front.
		vec2 uvA = sheetUV(pA), uvB = sheetUV(pB);
		vec3 iA = picture(uvA), iB = picture(uvB);
		cA = mix(mix(cA, picture(wearUV(pA)), uPic.z), iA, uPic.x);
		cB = mix(mix(cB, picture(wearUV(pB)), uPic.z), iB, uPic.y);
		if (inmode == 3)
		{
			// plan view: the sheet lies on the floor, the right way up for the camera above it, and
			// brightness is height, so the contour lines of the take trace the picture's tones
			if (uPic.x > 0.5) { pA = vec3((uvA.x - 0.5) * 1.6, -0.5 + 0.5 * dot(iA, LUM), (0.5 - uvA.y) * 0.9); nA = vec3(0.0, 1.0, 0.0); yawA = 0.0; }
			if (uPic.y > 0.5) { pB = vec3((uvB.x - 0.5) * 1.6, -0.5 + 0.5 * dot(iB, LUM), (0.5 - uvB.y) * 0.9); nB = vec3(0.0, 1.0, 0.0); yawB = 0.0; }
		}
		else
		{
			pA.z += uPic.x * (dot(iA, LUM) - 0.4) * 0.22;
			pB.z += uPic.y * (dot(iB, LUM) - 0.4) * 0.22;
		}
	}

	pA = rotY(pA, yawA); nA = rotY(nA, yawA);
	pB = rotY(pB, yawB); nB = rotY(nB, yawB);

	float s;
	float swirlAmt = 1.0;
	if (lay == 2)
	{
		// Duel: the two shapes stand side by side, half the points each, and a strand of points
		// is forever being pulled out of one and into the other. Kicks tear more of them loose.
		float strand = step(r4, 0.06 + 0.22 * min(uAudio.x, 1.0) + 0.04 * uAudio.w);
		float travel = fract(rnd.y + uAudio2.w * 0.25);
		s = mix(step(0.5, fract(id * 0.5)), travel, strand);
		pA.x -= 0.82;
		pB.x += 0.82;
		swirlAmt = 0.45;
	}
	else
	{
		// Staggered departure: a front sweeps up through shape A, blurred by a per-point random delay.
		float delay = clamp(0.55 * (pA.y + 0.5) + 0.45 * rnd.y, 0.0, 1.0);
		s = clamp((uMorph.x - delay * 0.55) / 0.45, 0.0, 1.0);
		s = s * s * s * (s * (s * 6.0 - 15.0) + 10.0);
	}
	float mid = sin(PI * s);

	float t = uMorph.y * 0.35;
	vec3 base = mix(pA, pB, s);
	// Mid-flight the path bows outward into a vortex about the vertical axis and rides the wind.
	vec3 swirl = rotY(base, swirlAmt * mid * (1.6 + 2.0 * rnd.z)) * (1.0 + 0.22 * mid * rnd.x);
	swirl.y += mid * (rnd.z - 0.3) * 0.28;
	vec3 wind = flow(swirl * 1.3 + rnd * 0.15, t);
	vec3 pos = swirl + wind * (0.003 + 0.10 * mid * mid);

	vec3 nrm = normalize(mix(nA, nB, s) + 1e-5) * nsign;
	// One point in nine never lands: it hangs off the surface as dust and drifts on the wind,
	// so a settled shape still has an atmosphere and is never still.
	float dust = step(0.89, rnd.x);
	pos += dust * (nrm * (0.03 + 0.16 * rnd.y * rnd.y) + wind * 0.035);
	// Beat: a scan front rises from the floor through the sculpture once per beat. Where it passes,
	// the surface lifts off along its normals and burns in the accent colour. Kicks make it hot.
	float front = uLook.y - 0.12 + fract(uAudio2.w) * 1.55;
	float band = exp(-pow((pos.y - front) / 0.055, 2.0));
	float amp = 0.40 * smoothstep(0.12, 0.45, uAudio2.y) + 0.9 * uAudio.x + 0.35 * uAudio.w;
	pos += nrm * band * amp * (0.5 + rnd.z) * 0.045;
	// Kick: the whole surface jumps a little, dust is thrown far.
	pos += nrm * uAudio.x * (0.4 + rnd.z) * mix(0.012, 0.13, dust);
	// Snare: a fine fizz.
	pos += (rnd - 0.5) * uAudio2.z * 0.018;
	// Bass: the body breathes.
	pos *= 1.0 + 0.04 * min(uAudio.y, 1.5);
	// Arrival: in the first half second of a shot the cloud falls into place from a burst.
	float arr = 1.0 - smoothstep(0.0, 0.42, uShot.x - 0.12 * rnd.y);
	pos += (nrm * 0.25 + (rnd - 0.5) * 0.9) * arr * arr * uShot.z;
	float h0 = pos.y + 0.5;                    // height above the floor, before any layout

	// the take's own scale (the inside take stands the camera within a five-times model)
	float wscale = uTake.z;
	pos = vec3(pos.x, pos.y + 0.5, pos.z) * wscale - vec3(0.0, 0.5, 0.0);
	float onCell = 0.0;
	if (lay == 1)
	{
		// Catalogue: point i belongs to cell (i mod cells); each cell turns on its own and the
		// beat cursor swells one cell at a time.
		float K = uGrid.x * uGrid.y;
		float c = mod(id, K);
		float cx = mod(c, uGrid.x), cy = floor(c / uGrid.x);
		onCell = step(abs(c - uGrid.w), 0.5);
		float pop = smoothstep(0.0, 0.10, uShot.x - c * 0.028);
		pop *= 1.0 + 0.35 * (1.0 - smoothstep(0.10, 0.30, uShot.x - c * 0.028));
		float cs = 0.84 * pop * (1.0 + 0.30 * onCell * (0.35 + uAudio.w));
		float a = uMorph.y * 0.45 + c * 1.7 + uShot.y * 6.283;
		pos = rotY(pos, a) * cs;
		nrm = rotY(nrm, a);
		pos += vec3((cx - 0.5 * (uGrid.x - 1.0)) * 1.32, (0.5 * (uGrid.y - 1.0) - cy) * 1.25 + 0.05, 0.0);
		wscale *= cs;
	}

	vec3 col = mix(cA, cB, s);
	col = pow(max(col, 0.0), vec3(2.2));       // texture bytes are sRGB; work in linear light
	// in flight the colours run richer, so the stream is confetti of the two objects, not grey grit
	float lum0 = dot(col, LUM);
	float chroma = max(col.r, max(col.g, col.b)) - min(col.r, min(col.g, col.b));
	col = max(mix(vec3(lum0), col, 1.0 + 0.9 * mid), 0.0);
	// white plastic keeps its detail instead of clipping under the key light
	float wordness = mix(uLook.z, uLook.w, s);
	col *= mix(1.0 / (1.0 + 0.7 * max(lum0 - 0.35, 0.0)), 1.0, wordness);

	bool mirror = TDInstanceID() == 1;
	float floorY = uLook.y;
	float h = max(pos.y - floorY, 0.0);
	if (mirror)
		pos.y = floorY - h;

	vec4 world = TDDeform(pos);
	if (inmode == 2)
	{
		// The picture is laid over the screen and every point takes the colour it finds under itself:
		// the cloud becomes a moving screen of discs that the picture shows through.
		vec4 cp = TDWorldToProj(world);
		vec3 ip = pow(picture(cp.xy / max(cp.w, 0.05) * 0.5 + 0.5), vec3(2.2));
		// (a tenth of the model's own colour was left in at first: the saturation boost of the inside
		// take turned that into a pink wash over the whole picture, NOTES log 41)
		col = ip * (0.6 + 0.8 * dot(col, LUM));
	}
	vec3 camPos = uTDMats[TDCameraIndex()].camInverse[3].xyz;
	vec3 toCam = normalize(camPos - world.xyz);
	vec3 wn = normalize(mirror ? nrm * vec3(1.0, -1.0, 1.0) : nrm);
	float facing = dot(wn, toCam);
	// Lit like an object on a desk: warm key from upper left, cool fill from the right, a rim.
	float key = max(dot(wn, normalize(vec3(-0.55, 0.75, 0.5))), 0.0);
	float fill = max(dot(wn, normalize(vec3(0.8, 0.1, 0.4))), 0.0);
	float rim = pow(1.0 - abs(facing), 3.0);
	vec3 light = vec3(0.10, 0.10, 0.12)
		+ vec3(0.80, 0.70, 0.57) * key
		+ vec3(0.08, 0.15, 0.22) * fill
		+ vec3(0.25, 0.40, 0.50) * rim * 0.4;
	light = mix(light, vec3(1.05), mid * 0.8);
	// the word is a lit sign, not a lump of plastic: its faces glow
	light = mix(light, light * 0.9 + vec3(0.48), wordness);  // in flight every mote is its own light
	// seen from inside there is no key light to face: light the wall by how squarely it faces us
	if (nsign < 0.0)
	{
		light = vec3(0.22) + vec3(0.85, 0.80, 0.72) * max(facing, 0.0);
		if (inmode != 2)
			col = max(mix(vec3(dot(col, LUM)), col, 1.7), 0.0);
	}

	// Vocals: shimmer, a rolling population of points flares.
	float tw = pow(fract(rnd.y * 17.0 + uMorph.y * 0.9 + pos.y * 0.7), 24.0);
	float voc = min(uAudio.z, 1.0);
	float shimmer = tw * (0.03 + 2.0 * voc * voc);
	float hat = step(0.975, rnd.z) * uAudio2.x * 1.5;

	gl_Position = TDWorldToProj(world);
	float w = max(gl_Position.w, 0.05);
	float dist = length(camPos - world.xyz);
	// nearer is brighter and bigger: the cloud has a front and a back
	float depthGain = clamp(1.0 - 0.6 * (dist - length(camPos)), 0.4, 1.4);
	if (lay == 1 || nsign < 0.0)
		depthGain = 1.0;

	float size = uLook.x * mix(pA4.w, pB4.w, s) * wscale * uSize.x * (1.0 - 0.5 * dust) * (1.0 - 0.5 * mid)
		* (1.0 + 1.2 * band * amp + 0.8 * tw * voc + uAudio.w * 0.12);
	float px = size * uShot.w / w;

	vec3 lit = col * light * depthGain * (0.85 + 0.3 * uAudio2.y);
	vec3 c = lit;
	c += (col + vec3(0.25, 0.22, 0.18)) * (shimmer + hat);
	c += vec3(0.10, 0.17, 0.22) * rim * depthGain * (1.0 - uInk.w);   // a cool edge even on black parts
	vec3 hot = mix(vec3(1.0, 0.86, 0.62), uAccent.rgb * 1.6, 0.55) * band * amp * 1.1;
	c += hot * (lay == 1 ? 0.0 : 1.0);
	c *= 1.0 + 0.55 * onCell;
	// one ink instead of the texture colours
	c = mix(c, uInk.rgb * (0.04 + 1.7 * dot(c, LUM)), uInk.w);
	float soft = 0.0;
	vRad = 1.0;
	vPaper = uPaperM.rgb * (0.95 + 0.05 * uAudio.w);

	if (cmode == 3)
	{
		// two inks: whose point is it?
		vec3 two = mix(uInk.rgb, uInk2.rgb, s);
		two = mix(two, vec3(1.0, 0.93, 0.80), 0.25 * mid);
		c = two * (0.10 + 1.9 * dot(lit, LUM) + 0.35 * mid) + two * (shimmer + hat) + hot * 0.25;
	}
	else if (cmode == 4)
	{
		// contours: only points near a height level are inked, and the levels climb
		float ph = h0 * 15.0 - uMorph.y * 1.1;
		float line = smoothstep(0.38, 0.48, abs(fract(ph) - 0.5));
		c = uInk.rgb * (0.02 + line * (0.35 + 0.9 * h0) + 0.6 * (shimmer + hat)) + uInk2.rgb * band * amp * 1.6;
		px *= 1.0 + 0.5 * line;
		// a picture laid flat (Input, plan view) also fills softly by its tone, so it stays readable between the lines
		if (inmode == 3)
			c += uInk.rgb * 0.5 * dot(col, LUM) * mix(uPic.x, uPic.y, s);
	}
	// depth fog: into the dark, or into the paper when the take is printed on paper
	c = mix(vPaper * uPaperM.w, c, exp(-uInk2.w * max(dist - 0.9, 0.0)));
	if (mirror)
		c *= 0.2 * exp(-h * 3.2);

	if (cmode == 2)
	{
		// Raster: every point is moved to the middle of its screen cell and drawn as a whole cell:
		// paper with one disc of ink on it, the darker the surface the bigger the disc. The nearest
		// point wins the cell, so the object becomes a print screen of what the camera can see.
		// (Sizing each cell by its darkest point was tried: every cell had one, b_raster_dbg3.png.)
		float cell = uSize.w * (uShot.x < 0.10 ? 4.0 : (uShot.x < 0.22 ? 2.0 : 1.0));
		vec2 res = vec2(1280.0, 720.0);
		vec2 pxy = (gl_Position.xy / w * 0.5 + 0.5) * res;
		float row = floor(pxy.y / cell);
		float off = mod(row, 2.0) * 0.5 * cell;
		vec2 sn = vec2((floor((pxy.x - off) / cell) + 0.5) * cell + off, (row + 0.5) * cell);
		float dark = 1.0 - smoothstep(0.02, 0.50, dot(lit, LUM));
		float f = sqrt(0.05 + 0.95 * dark) * (0.80 + 0.20 * uAudio.w) + 0.5 * band * amp;
		bool second = chroma > 0.22 && lum0 > 0.05;
		c = second ? uInk2.rgb : uInk.rgb;
		soft = 1.0;
		vRad = clamp(f, 0.12, 1.0) * 0.96;
		bool cull = facing < 0.0 || gl_Position.w < 0.05 || dust > 0.5;
		gl_Position = cull ? vec4(2.0, 2.0, 2.0, 1.0) : vec4(sn / res * 2.0 - 1.0, gl_Position.z / w, 1.0);
		gl_PointSize = cell;
	}
	else
	{
		gl_PointSize = clamp(px, uSize.y, uSize.z);
	}
	// thinned takes draw only some of the points
	if (hash1(id + 3.7) > uGrid.z)
		gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
	vCol = vec4(c, 1.0);
	vSoft = soft;
}
