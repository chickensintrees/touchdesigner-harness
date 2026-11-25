// sc_exploded_view: places every part of every view. All layout lives in the views CHOP
// (logic.py); this shader only applies it. see: experiments/sc_exploded_view/NOTES.md
uniform vec4 uViewA[12];   // per view: pitch, yaw, roll (radians), scale
uniform vec4 uViewB[12];   // per view: offset x, offset y, explode amount, cursor (typing / sweep position 0..1)
uniform vec4 uObj;         // x mode (0 separate parts, 1 slabs, 2 sweep cut), y slabs, z axis 0/1/2, w views
uniform vec4 uExt;         // x lo, y hi of the model along the axis, z gap per slab at explode 1, w fan
uniform vec4 uMisc;        // x evolve, y hit_high, z seed, w beat_pos
uniform vec4 uKeys;        // x chaos 0..1, y spread, z lift, w row lift
uniform vec4 uKeys2;       // x how far the base sinks under the flying parts
uniform vec4 uParts;       // the parts file: x how many parts fly, y lowest part centre, z height range of the centres
uniform vec4 uPartsUV;     // Input picture on the parts: x width, y depth (z 0: laid on the x-z bed) or height (z 1: on the x-y face)

out Vertex {
	vec3 wN;
	vec3 wPos;
	float along;
	float glow;
	flat vec3 axisW;
	flat vec3 planeLo;
	flat vec3 planeHi;
	flat float pid;
	flat vec2 range;
	flat vec3 camPos;
	flat vec4 camFwd;      // xyz forward, w 1 when orthographic
	vec3 keyUV;            // Input picture: place on the parts object (xy 0..1), z 1 on a part, 0 on the base
	flat vec3 offW;        // Input picture: this slab's explosion offset in world units
	flat vec3 vOrg;        // Input picture: view offset xy, view scale
} oVert;

vec3 hash3(float n) { return fract(sin(vec3(n * 12.9898, n * 78.233, n * 37.719)) * 43758.5453); }

mat3 rotM(vec3 e)
{
	float cx = cos(e.x), sx = sin(e.x), cy = cos(e.y), sy = sin(e.y), cz = cos(e.z), sz = sin(e.z);
	mat3 rx = mat3(1, 0, 0, 0, cx, sx, 0, -sx, cx);
	mat3 ry = mat3(cy, 0, -sy, 0, 1, 0, sy, 0, cy);
	mat3 rz = mat3(cz, sz, 0, -sz, cz, 0, 0, 0, 1);
	return rx * ry * rz;
}

mat3 axisRot(vec3 a, float t)
{
	float c = cos(t), s = sin(t), k = 1.0 - c;
	return mat3(k * a.x * a.x + c, k * a.x * a.y + s * a.z, k * a.x * a.z - s * a.y,
	            k * a.x * a.y - s * a.z, k * a.y * a.y + c, k * a.y * a.z + s * a.x,
	            k * a.x * a.z + s * a.y, k * a.y * a.z - s * a.x, k * a.z * a.z + c);
}

float bound(int k, int n, float cut)
{
	if (uObj.x > 1.5)
		return k <= 0 ? uExt.x : (k == 1 ? mix(uExt.x, uExt.y, cut) : uExt.y);
	return mix(uExt.x, uExt.y, float(k) / float(n));
}

void main()
{
	vec3 p = TDPos();
	vec3 n = TDNormal();
	int inst = TDInstanceID();
	int nViews = max(1, int(uObj.w + 0.5));
	int view = inst % nViews;
	int slab = inst / nViews;
	vec4 A = uViewA[view];
	vec4 B = uViewB[view];
	mat3 R = rotM(A.xyz);
	float E = B.z;
	float glow = 0.0;
	float pid = 1.0;
	vec3 ax = vec3(0, 1, 0);
	vec3 pLo = vec3(0), pHi = vec3(0);
	vec2 rng = vec2(-1e6, 1e6);
	float along = 0.0;
	vec3 keyUV = vec3(0.0);
	vec3 offW = vec3(0.0);

	if (uObj.x < 0.5) {
		// separate parts: the normal slot carries the part's centre (x, z), its place in the landing
		// order and, in the fraction, its height (prep_parts.py); 0 is a base, which only sinks a
		// little as the parts lift off
		vec3 t = n;
		float isKey = step(0.5, t.y);
		float whole = floor(t.y + 0.01);
		keyUV = uPartsUV.z < 0.5 ? vec3(p.x / uPartsUV.x + 0.5, 0.5 - p.z / uPartsUV.y, isKey)
		                         : vec3(p.x / uPartsUV.x + 0.5, p.y / uPartsUV.y + 0.5, isKey);
		float id = max(whole - 1.0, 0.0);
		vec3 c = vec3(t.x, uParts.y + clamp(t.y - whole, 0.0, 1.0) / 0.9 * uParts.z, t.z);
		vec3 h = hash3(id + 1.0 + floor(uMisc.z * 64.0));
		float ord = id / max(uParts.x, 1.0);
		float cur = B.w * 1.04;
		float seat = smoothstep(ord, ord + 0.02, cur);
		float fly = E * (1.0 - seat) * isKey;
		float row = floor((c.z + 0.11) / 0.048 + 0.5);
		vec3 q = p - c;
		vec3 raxis = normalize(h - 0.5 + vec3(1e-3));
		q = axisRot(raxis, uKeys.x * fly * (h.z - 0.5) * 9.0) * q;
		vec3 cc = c;
		cc.xz *= 1.0 + fly * uKeys.y;
		cc.y += (c.y - (uParts.y + 0.5 * uParts.z)) * fly * uKeys.y;     // nothing on a flat bed of parts
		cc.y += fly * (uKeys.z * (0.55 + 0.45 * mix(0.5, h.y, uKeys.x)) + uKeys.w * (2.0 - row));
		cc += uKeys.x * fly * (h - 0.5) * vec3(0.5, 0.2, 0.5);
		// the base sinks under the flying parts; the macro take has no base at all
		cc.y -= (1.0 - isKey) * (uKeys2.x > 10.0 ? uKeys2.x
		        : E * uKeys.z * uKeys2.x * (1.0 - smoothstep(0.85, 1.0, B.w)));
		// landing: a short dip and a flash of ink just after the part seats
		float since = max(cur - ord - 0.02, 0.0);
		float land = isKey * seat * exp(-since * 38.0) * step(0.02, E);
		cc.y -= 0.03 * land * sin(min(since * 60.0, 3.14159));
		// hats pop a few random parts out of place
		float pop = isKey * uMisc.y * step(0.86, hash3(id + floor(uMisc.w * 2.0) * 7.0).x);
		cc.y += 0.07 * pop;
		glow = max(land, pop);
		p = q + cc;
		n = vec3(0.0, 1.0, 0.0);      // the real normal comes from derivatives in the pixel shader
		pid = id + 1.0 + float(view) * 100.0;
	} else {
		int ns = max(1, int(uObj.y + 0.5));
		int a = int(uObj.z + 0.5);
		ax = a == 0 ? vec3(1, 0, 0) : (a == 1 ? vec3(0, 1, 0) : vec3(0, 0, 1));
		vec3 perp = ax.yzx;
		along = dot(p, ax);
		rng = vec2(bound(slab, ns, B.w), bound(slab + 1, ns, B.w));
		float k = float(slab) - float(ns - 1) * 0.5;
		vec3 off = ax * k * uExt.z * E + perp * uExt.w * E * (mod(float(slab), 2.0) - 0.5) * 2.0;
		p += off;
		offW = R * (off * A.w);
		pLo = R * ((ax * rng.x + off) * A.w) + vec3(B.xy, 0.0);
		pHi = R * ((ax * rng.y + off) * A.w) + vec3(B.xy, 0.0);
		pid = float(inst) + 1.0;
	}

	vec3 w = R * (p * A.w) + vec3(B.xy, 0.0);
	oVert.wN = R * n;
	oVert.wPos = w;
	oVert.along = along;
	oVert.glow = glow;
	oVert.axisW = R * ax;
	oVert.planeLo = pLo;
	oVert.planeHi = pHi;
	oVert.pid = pid;
	oVert.range = rng;
	oVert.keyUV = keyUV;
	oVert.offW = offW;
	oVert.vOrg = vec3(B.xy, A.w);
	mat4 camInv = uTDMats[TDCameraIndex()].camInverse;
	oVert.camPos = camInv[3].xyz;
	oVert.camFwd = vec4(normalize(-camInv[2].xyz), uTDMats[TDCameraIndex()].proj[3][3] > 0.5 ? 1.0 : 0.0);
	gl_Position = TDWorldToProj(vec4(w, 1.0));
}
