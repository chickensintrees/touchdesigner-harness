// sc_shatter: every triangle corner is read from the fracture atlas (see bake.py) and moved with
// its cell as a rigid body. The whole motion is a function of one phase value, so it runs
// backwards exactly: the object is whole at phase 0 and again at phase 1.
uniform sampler2D sAtlas;
uniform vec4 uBurst;   // x phase 0..1, y power (units), z spin (turns), w level: 0 micro 1 fine 2 coarse 3 slabs
uniform vec4 uShape;   // x start stagger, y lock stagger, z gravity, w swirl
uniform vec4 uAudio;   // x kick jolt, y evolve, z arrival burst, w direction spread
uniform vec4 uGrid;    // x columns, y rows, z spacing x, w spacing z
uniform vec4 uWave;    // x instance wave span, y wave angle, z shot seed, w instance yaw jitter
uniform vec4 uLight;   // xyz direction to the key light, w 1 = floor reflections on
uniform vec4 uSlab;    // xyz slide direction, w slabs per unit (10: the planes baked into the atlas)
uniform vec4 uOrder;   // x stagger mode (0 random, 1 from impact point, 2 reading order, 3 height), yzw impact point 0..1 in the bounds
uniform vec4 uMode;    // x layout (0 burst, 1 knolling grid on the floor), y grid pitch, z skin metal, w glass
uniform vec4 uXform;   // x object scale, y object yaw, z hang drift, w floor clamp on

out vec3 vWorld;
out vec3 vN;
out vec2 vUV;
out vec4 vData;        // kind, random, local burst, mirror flag
out vec3 vObj;         // object-space rest position
out vec4 vCam;         // camera position, w 1 = shadow pass

const float TAU = 6.2831853;

vec3 hash3(float n) { return fract(sin(vec3(n * 12.9898, n * 78.233, n * 37.719)) * 43758.5453); }

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
		sin(q.x * 2.0 + t * 0.9) + cos(q.y * 2.2 + t));
	return v;
}

vec3 rotAxis(vec3 v, vec3 k, float a)
{
	float c = cos(a), s = sin(a);
	return v * c + cross(k, v) * s + k * dot(k, v) * (1.0 - c);
}

vec3 rotY(vec3 p, float a)
{
	float c = cos(a), s = sin(a);
	return vec3(c * p.x + s * p.z, p.y, -s * p.x + c * p.z);
}

// Out fast, hang, pulled back with the same curve reversed. 0 at q = 0 and q = 1.
float burstCurve(float q)
{
	float up = 1.0 - pow(1.0 - clamp(q / 0.13, 0.0, 1.0), 3.0);
	float down = 1.0 - pow(1.0 - clamp((1.0 - q) / 0.42, 0.0, 1.0), 3.0);
	return up * down * (1.0 + uXform.z * (q - 0.13));
}

void main()
{
	int id = gl_VertexIndex;
	ivec2 sz = textureSize(sAtlas, 0);
	int Wd = sz.x;
	int H = (sz.y - 8) / 3;
	int B = 3 * H;
	vec4 meta = texelFetch(sAtlas, ivec2(0, B + 7), 0);
	int inst = TDInstanceID();
	bool mirror = (inst & 1) == 1;
	int k = inst >> 1;
	bool shadowPass = uTDMats[TDCameraIndex()].proj[3][3] > 0.5;   // the shadow camera is orthographic
	if (float(id) >= meta.x || (mirror && (uLight.w < 0.5 || shadowPass)))
	{
		gl_Position = vec4(0.0, 0.0, 2.0, 1.0);
		vWorld = vec3(0.0); vN = vec3(0.0, 1.0, 0.0); vUV = vec2(0.0); vData = vec4(0.0); vObj = vec3(0.0); vCam = vec4(0.0);
		return;
	}
	ivec2 tc = ivec2(id % Wd, id / Wd);
	vec4 t0 = texelFetch(sAtlas, tc, 0);
	vec4 t1 = texelFetch(sAtlas, tc + ivec2(0, H), 0);
	vec4 t2 = texelFetch(sAtlas, tc + ivec2(0, 2 * H), 0);
	vec3 P = t0.xyz;
	vec3 N = t1.xyz;
	int fine = int(t0.w + 0.5);
	int micro = int(t1.w + 0.5);
	vec3 lo = texelFetch(sAtlas, ivec2(1, B + 7), 0).xyz;
	vec3 hi = texelFetch(sAtlas, ivec2(2, B + 7), 0).xyz;
	vec3 centre = texelFetch(sAtlas, ivec2(3, B + 7), 0).xyz;

	vec4 mT = texelFetch(sAtlas, ivec2(micro % Wd, B + micro / Wd), 0);
	vec4 fT = texelFetch(sAtlas, ivec2(fine, B + 4), 0);
	int level = int(uBurst.w + 0.5);
	vec3 pivot = mT.xyz;
	float cid = float(micro);
	float rad = 0.03;
	float cellIdx = float(micro);
	float ncell = meta.y;
	vec3 cellN = vec3(0.0, 1.0, 0.0);
	vec3 centre0 = texelFetch(sAtlas, ivec2(3, B + 7), 0).xyz;
	if (level == 1)
	{
		cellIdx = float(fine);
		ncell = meta.z;
		cellN = texelFetch(sAtlas, ivec2(fine, B + 5), 0).xyz;
		pivot = fT.xyz;
		cid = float(fine) + 7000.0;
		rad = texelFetch(sAtlas, ivec2(fine, B + 5), 0).w;
	}
	else if (level == 2)
	{
		int coarse = int(fT.w + 0.5);
		vec4 cT = texelFetch(sAtlas, ivec2(coarse, B + 6), 0);
		pivot = cT.xyz;
		cellIdx = float(coarse);
		ncell = meta.w;
		cellN = normalize(cT.xyz - centre0 + vec3(0.0, 1e-3, 0.0));
		cid = float(coarse) + 9000.0;
		rad = cT.w;
	}
	float slab = 0.0;
	if (level == 3)
	{
		// the bake cut every triangle on the y planes (10 per unit) and stored its centre height
		slab = floor(t2.w * uSlab.w);
		cid = slab + 12000.0;
		pivot = vec3(centre.x, (slab + 0.5) / uSlab.w, centre.z);
		rad = 0.2;
	}
	vec3 rnd = hash3(cid + 1.0 + floor(uWave.z * 64.0) * 0.37);
	vec3 rnd2 = hash3(cid * 1.31 + 5.0);

	// instance layout
	float nx = max(uGrid.x, 1.0), nz = max(uGrid.y, 1.0);
	float ix = mod(float(k), nx), iz = floor(float(k) / nx);
	vec3 instOff = vec3((ix - (nx - 1.0) * 0.5) * uGrid.z, 0.0, (iz - (nz - 1.0) * 0.5) * uGrid.w);
	vec3 irnd = hash3(float(k) * 3.7 + 11.0 + uWave.z * 9.0);
	vec2 wdir = vec2(cos(uWave.y), sin(uWave.y));
	float ext = max(0.5 * ((nx - 1.0) * uGrid.z * abs(wdir.x) + (nz - 1.0) * uGrid.w * abs(wdir.y)), 1e-3);
	float iu = clamp(0.5 + 0.5 * dot(instOff.xz, wdir) / ext + (irnd.x - 0.5) * 0.08, 0.0, 1.0);
	float span = (nx * nz > 1.5) ? uWave.x : 0.0;
	float qg = clamp((uBurst.x - iu * span) / max(1.0 - span, 1e-3), 0.0, 1.0);

	// per-cell stagger: first out is last back, like footage reversed
	vec3 rel = (pivot - lo) / max(hi - lo, vec3(1e-3));
	float d0 = rnd2.x;
	int omode = int(uOrder.x + 0.5);
	if (omode == 1) d0 = clamp(length((rel - uOrder.yzw) * (hi - lo)) / length(hi - lo) * 1.4, 0.0, 1.0);
	else if (omode == 2) d0 = clamp(rel.x * 0.85 + (1.0 - rel.y) * 0.15, 0.0, 1.0);
	else if (omode == 3) d0 = 1.0 - rel.y;
	if (omode > 0) d0 = clamp(d0 * 0.88 + rnd2.x * 0.12, 0.0, 1.0);
	// lock stagger: positive = first out is last back (true reversal); negative = first out is first back (reading order)
	float pscale = 1.0;
	bool knoll = uMode.x > 0.5 && (level == 1 || level == 2);
	if (knoll) d0 = clamp(cellIdx / max(ncell, 1.0) * 0.9 + rnd2.x * 0.1, 0.0, 1.0);
	float e1 = uShape.y >= 0.0 ? d0 * uShape.y : (1.0 - d0) * -uShape.y;
	float q = clamp((qg - d0 * uShape.x) / max(1.0 - d0 * uShape.x - e1, 1e-3), 0.0, 1.0);
	float A = burstCurve(q);
	float A0 = A;
	// kicks open the cracks a little, even while whole; the arrival burst closes in the first half second
	A += uAudio.x * (0.25 + rnd.x) + uAudio.z * (0.5 + rnd.y);

	vec3 dirOut = pivot - centre;
	dirOut.y *= 0.8;
	vec3 dir = normalize(normalize(dirOut + 1e-4) + (rnd - 0.5) * 2.0 * uAudio.w);
	float speed = 0.35 + 1.3 * rnd2.y * rnd2.y;
	vec3 off = dir * A * uBurst.y * speed;
	vec3 axis = normalize(rnd2 - 0.5 + 1e-3);
	float ang = TAU * uBurst.z * A * (0.3 + rnd.y) * (1.0 + 1.3 * q) * (rnd.z < 0.5 ? -1.0 : 1.0);
	if (level == 3)
	{
		// slabs slide sideways, alternating, and turn a little about the vertical
		vec3 side = normalize(uSlab.xyz + vec3(1e-4, 0.0, 0.0));
		off = side * A * uBurst.y * (mod(slab, 2.0) < 0.5 ? -1.0 : 1.0) * (0.5 + rnd.x);
		ang = TAU * uBurst.z * A * (rnd.y - 0.5);
		axis = vec3(0.0, 1.0, 0.0);
	}
	// murmuration: the cloud rides a moving flow field while it hangs
	if (uShape.w > 0.0)
		off += flow((pivot + instOff) * 0.9 + rnd * 0.2, uAudio.y * 0.6) * uShape.w * A * 0.5;
	off.y -= uShape.z * A * A * (0.5 + rnd2.z);
	if (knoll)
	{
		// knolling: every piece hops to its own slot in a tidy grid on the floor and lies skin up
		float m = smoothstep(0.0, 1.0, clamp(A0, 0.0, 1.0));
		float cols = ceil(sqrt(ncell * 1.9));
		float rws = ceil(ncell / cols);
		vec3 slot = vec3((mod(cellIdx, cols) - (cols - 1.0) * 0.5) * uMode.y, rad * 0.22 + 0.01,
			(floor(cellIdx / cols) - (rws - 1.0) * 0.5) * uMode.y);
		off = dir * (A - A0) * uBurst.y * speed + (slot - pivot) * m
			+ vec3(0.0, sin(3.14159 * m) * (0.25 + 0.5 * rnd.x), 0.0);
		vec3 ax = cross(cellN, vec3(0.0, 1.0, 0.0));
		float al = length(ax);
		axis = al > 1e-3 ? ax / al : vec3(1.0, 0.0, 0.0);
		ang = acos(clamp(cellN.y, -1.0, 1.0)) * m + (A - A0) * (rnd.y - 0.5) * 2.0;
		// every piece grows or shrinks to fill its slot: a specimen tray
		pscale = mix(1.0, clamp(0.62 * uMode.y / max(rad, 0.01), 0.4, 5.0), m);
	}
	if (uXform.w > 0.5)
		off.y = max(off.y, min(0.0, rad * 0.35 - pivot.y));    // shards come to rest on the floor

	vec3 pos = pivot + rotAxis(P - pivot, axis, ang) * pscale + off;
	vec3 nrm = rotAxis(N, axis, ang);
	if (uXform.w > 0.5)
		pos.y = max(pos.y, 0.002);

	float yaw = uXform.y + (irnd.y - 0.5) * uWave.w;
	pos = rotY(pos * uXform.x, yaw) + instOff;
	nrm = rotY(nrm, yaw);
	if (mirror)
	{
		pos.y = -pos.y;
		nrm.y = -nrm.y;
	}
	if (shadowPass)
	{
		pos.xz -= uLight.xz / max(uLight.y, 0.05) * pos.y;
		pos.y = 0.0;
	}
	vec4 world = TDDeform(pos);
	vWorld = world.xyz;
	vN = nrm;
	vUV = t2.xy;
	vData = vec4(t2.z, t2.w, A, mirror ? 1.0 : 0.0);
	vObj = P;
	vCam = vec4(uTDMats[TDCameraIndex()].camInverse[3].xyz, shadowPass ? 1.0 : 0.0);
	gl_Position = TDWorldToProj(world);
}
