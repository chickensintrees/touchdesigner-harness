// input 0: cloud with its outward echo (linear light), input 1: quarter-size blur of it for the
// glow, input 2: this frame's cloud alone, whose alpha says where a point was drawn.
// Adds the room and grades.
uniform vec4 uRoom;    // x height of the floor contact in uv, y energy, z pulse, w evolve
uniform vec4 uRoom2;   // x hit_high, y vocals, z where the sculpture stands across the frame (uv)
uniform vec4 uTint;    // rgb accent of the current shape, w hit_low
uniform vec4 uSec;     // x section_pos, y 1 when the shape is the word, z beat_pos
uniform vec4 uPost;    // x backdrop (0 room and sun, 1 flat paper, 2 void, 3 drawing grid), y glow, z vignette, w echo
uniform vec4 uPaper;   // rgb paper colour (linear), w age of the shot in seconds
uniform vec4 uCap;     // x strength of the dark band behind a Describe caption (0 outside Describe mode)
out vec4 fragColor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

// A sparse layer of soft out-of-focus motes hanging in the room, drifting upward.
float motes(vec2 uv, float scale, float t, float seed)
{
	vec2 p = uv * vec2(1.78, 1.0) * scale + vec2(sin(t * 0.21 + seed) * 0.3, -t * 0.12);
	vec2 cell = floor(p);
	vec2 f = fract(p) - 0.5;
	float r = hash(cell + seed);
	if (r > 0.34)
		return 0.0;
	vec2 o = (vec2(hash(cell + seed + 3.1), hash(cell + seed + 7.7)) - 0.5) * 0.6;
	float rad = 0.05 + 0.10 * hash(cell + seed + 11.3);
	float d = length(f - o);
	float tw = 0.55 + 0.45 * sin(t * 1.3 + r * 60.0);
	return smoothstep(rad, rad * 0.55, d) * tw * (0.4 + 1.8 * r);
}

// The backdrop: a halftone sun in the shape's accent colour, standing behind the sculpture.
// Solid at its heart, breaking into print dots at the rim. It cuts colour on the section change,
// flares and springs outward at that instant, and swells on kicks.
float sun(vec2 uv, float cx, float flare)
{
	vec2 dc = (uv - vec2(cx, 0.56)) * vec2(1.78, 1.0);
	float R = 0.40 * (1.0 + 0.05 * uRoom.z + 0.14 * uTint.w + 0.35 * flare);
	mat2 rot = mat2(0.866, -0.5, 0.5, 0.866);
	vec2 hp = rot * dc * 46.0;
	vec2 hc = fract(hp) - 0.5;
	vec2 cc = transpose(rot) * ((floor(hp) + 0.5) / 46.0);
	// the word is wide: its sun is a lozenge (the dots stay round)
	cc.x /= 1.0 + 1.1 * uSec.y;
	float dcell = length(cc);
	float shade = clamp((R - dcell) / (R * 0.62), 0.0, 1.0);
	// every beat the sun throws off a ring of dots that crosses the room and thins out
	float ph = fract(uSec.z);
	float ring = exp(-pow((dcell - R - 0.05 - ph * 0.85) / 0.05, 2.0)) * pow(1.0 - ph, 1.5);
	shade = max(shade, ring * 0.30 * (smoothstep(0.12, 0.45, uRoom.y) + 0.6 * uTint.w));
	float r = 0.76 * sqrt(shade);
	return smoothstep(r + 0.05, r - 0.05, length(hc)) * step(0.001, shade);
}

void main()
{
	vec2 uv = vUV.st;
	vec3 rays = texture(sTD2DInputs[0], uv).rgb;
	vec4 crisp = texture(sTD2DInputs[2], uv);
	// the echo lives behind and around the sculpture, never on top of it
	int bgm = int(uPost.x + 0.5);
	vec3 cloud = mix(rays * uPost.w, crisp.rgb, clamp(crisp.a, 0.0, 1.0));
	vec3 glow = texture(sTD2DInputs[1], uv).rgb;

	// The room: an ink void. A pool of the shape's own colour lies on the floor under it and a
	// faint column of fluorescent haze stands behind it.
	float fy = uRoom.x;
	vec3 ink = vec3(0.0035, 0.0065, 0.0105);
	vec3 bg = ink * (0.35 + 1.1 * smoothstep(0.0, 1.0, uv.y));
	float shaft = 0.0, back = 0.0;
	if (bgm == 0)
	{
	vec2 p = (uv - vec2(uRoom2.z, fy)) * vec2(1.78, 1.0);
	float pool = exp(-(p.x * p.x * 3.0 + p.y * p.y * 60.0));
	bg += mix(vec3(0.30, 0.42, 0.50), uTint.rgb, 0.45) * pool * (0.06 + 0.10 * uRoom.y + 0.08 * uRoom.z);
	vec2 q = (uv - vec2(uRoom2.z, fy + 0.28)) * vec2(1.78, 1.0);
	back = exp(-(q.x * q.x * 2.2 + q.y * q.y * 3.0));
	bg += mix(vec3(0.42, 0.50, 0.38), uTint.rgb, 0.35) * back * (0.012 + 0.03 * uRoom.y);

	// a shaft from the key light, upper left, falling on the shape
	vec2 sp = uv - vec2(uRoom2.z, fy + 0.22);
	vec2 dir = normalize(vec2(-0.62, 0.78));
	float along = dot(sp * vec2(1.78, 1.0), dir);
	float across = dot(sp * vec2(1.78, 1.0), vec2(dir.y, -dir.x));
	shaft = exp(-across * across / (0.012 + 0.05 * max(along, 0.0))) * smoothstep(-0.15, 0.25, along);
	bg += vec3(0.50, 0.46, 0.36) * shaft * (0.02 + 0.04 * uRoom.y);
	float flare = max(exp(-uSec.x * 30.0), exp(-uPaper.w * 7.0));
	float sunGain = (1.0 - 0.45 * uSec.y) * 0.19 + 0.16 * uRoom.y + 0.10 * uRoom.z + 0.25 * uTint.w + 1.3 * flare;
	float s0 = sun(uv, uRoom2.z, flare);
	// its reflection lies in the floor
	float s1 = sun(vec2(uv.x, 2.0 * fy - uv.y), uRoom2.z, flare) * 0.22 * smoothstep(fy, fy - 0.03, uv.y)
		* smoothstep(0.0, fy, uv.y);
	bg += mix(uTint.rgb, vec3(1.0, 0.92, 0.78), 0.6 * flare) * (s0 * smoothstep(fy - 0.01, fy + 0.01, uv.y) + s1) * sunGain;
	}
	float m = motes(uv, 7.0, uRoom.w, 1.0) * 0.6 + motes(uv, 13.0, uRoom.w * 1.3, 5.0);
	bg += mix(vec3(0.40, 0.48, 0.55), uTint.rgb, 0.3) * m * (0.03 + 0.06 * uRoom2.x + 0.03 * uRoom.y) * (0.4 + shaft * 2.0 + back);
	if (bgm == 1 || bgm == 3)
	{
		// flat stock: the cloud is printed on it
		bg = uPaper.rgb * (0.95 + 0.05 * uRoom.z);
		if (bgm == 3)
		{
			vec2 gp = uv * vec2(1280.0, 720.0);
			float fine = max(step(mod(gp.x, 40.0), 1.0), step(mod(gp.y, 40.0), 1.0));
			float major = max(step(mod(gp.x + 1.0, 160.0), 2.0), step(mod(gp.y + 1.0, 160.0), 2.0));
			vec3 lineCol = dot(bg, vec3(0.33)) > 0.3 ? vec3(0.0) : vec3(1.0);
			bg = mix(bg, lineCol, (0.05 * fine + 0.09 * major) * (1.0 + 1.5 * uTint.w + 0.6 * uRoom.z));
		}
	}

	// the sculpture stands in front of the room: black parts read as silhouette against the sun
	bg *= 1.0 - (bgm == 1 || bgm == 3 ? 1.0 : 0.94) * clamp(crisp.a, 0.0, 1.0);
	vec3 col = bg + cloud + max(glow - 0.04, 0.0) * (0.30 + 0.35 * uRoom.z) * uPost.y;

	// Tone map on luminance so bright regions keep their texture colour instead of going white.
	float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
	float lm = 1.0 - exp(-l * 1.7);
	col *= lm / max(l, 1e-4);
	col = mix(col, vec3(lm), smoothstep(0.85, 1.0, lm) * 0.4);
	// a little extra saturation and a filmic toe
	col = mix(vec3(dot(col, vec3(0.2126, 0.7152, 0.0722))), col, 1.18);
	col = max(col, 0.0);
	col = col * col * (3.0 - 2.0 * col) * 0.35 + col * 0.65;

	float vig = smoothstep(1.3, 0.35, length((uv - vec2(0.5, 0.45)) * vec2(1.5, 1.0)) * 1.45);
	col *= mix(1.0 - 0.45 * uPost.z, 1.0, vig);
	col = pow(col, vec3(1.0 / 2.2));
	// Describe mode: a dark band along the bottom so the caption reads over a busy picture (0: untouched)
	col = mix(col, vec3(0.06, 0.09, 0.12), uCap.x * (1.0 - smoothstep(0.17, 0.25, uv.y)));
	col +=(hash(uv * vec2(1280.0, 720.0) + uRoom.w) - 0.5) / 255.0 * 1.5;
	fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
