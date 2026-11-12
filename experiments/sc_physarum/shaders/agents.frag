// Physarum agent update. One texel = one agent: xy position (0..1 of the trail map), z heading (radians),
// w ballistic timer (frames left of flying straight, used by rings and bursts).
// inputs: 0 previous agents, 1 previous trail, 2 attractant map (r attract, g wall)
uniform vec4 uSpecies; // x sensor angle (rad), y sensor distance (px), z turn per step (rad), w step (px)
uniform vec4 uField;   // x attract gain, y wall gain, z wander, w kick mode (0 uniform, 1 ring, 2 on shape, 3 burst from centre)
uniform vec4 uEvent;   // x boot, y kick share, z section share, w event counter
uniform vec4 uShot;    // x seed, y frame counter, z spawn mode, w flip (1 = attract becomes repel)
uniform vec4 uCtr;     // xy the subject's centre (uv): where bursts start
uniform vec4 uExtra;  // x drift strength (heading pulled toward y), y drift angle, z share per frame of stray agents that re-condense on the shape
uniform vec4 uRes;     // xy trail resolution in px, z ballistic speed multiplier, w ring start radius px
out vec4 fragColor;

const float TAU = 6.2831853;

uint pcg(uint v)
{
	uint s = v * 747796405u + 2891336453u;
	uint w = ((s >> ((s >> 28u) + 4u)) ^ s) * 277803737u;
	return (w >> 22u) ^ w;
}
float rnd(uint a, uint b) { return float(pcg(a ^ pcg(b))) / 4294967295.0; }

float smell(vec2 p, float gain)
{
	float t = texture(sTD2DInputs[1], p).r;
	vec4 a = texture(sTD2DInputs[2], p);
	return t + gain * a.r * (0.6 + t) - uField.y * a.g * 50.0;
}

// a point where the attractant is strong (rejection sampling), else anywhere
vec2 onShape(uint id, uint salt)
{
	vec2 p = vec2(0.5);
	for (uint k = 0u; k < 24u; k++)
	{
		p = vec2(rnd(id, salt + k * 2u + 11u), rnd(id, salt + k * 2u + 12u));
		vec4 a = texture(sTD2DInputs[2], p);
		if (a.r - a.g > 0.25 + 0.5 * rnd(id, salt + k + 77u))
			break;
	}
	return p;
}

vec4 spawn(float mode, uint id, uint salt)
{
	float r1 = rnd(id, salt + 1u), r2 = rnd(id, salt + 2u), r3 = rnd(id, salt + 3u), r4 = rnd(id, salt + 4u);
	vec2 px = 1.0 / uRes.xy;
	if (mode < 0.5)                       // 0: everywhere
		return vec4(r1, r2, r3 * TAU, 0.0);
	if (mode < 1.5)                       // 1: on the attractant
		return vec4(onShape(id, salt), uExtra.x > 0.0 ? uExtra.y + (r3 - 0.5) * 1.2 : r3 * TAU, 0.0);
	if (mode < 2.5)                       // 2: a ring around a point chosen by the event, flying outward
	{
		vec2 c = vec2(rnd(salt, 5u), rnd(salt, 6u));
		for (uint k = 0u; k < 6u; k++)    // prefer a centre on the shape
		{
			vec2 q = vec2(rnd(salt, 20u + k), rnd(salt, 40u + k));
			if (texture(sTD2DInputs[2], q).r > 0.3) { c = q; break; }
		}
		float a = r1 * TAU;
		vec2 p = c + vec2(cos(a), sin(a)) * uRes.w * (0.9 + 0.2 * r2) * px;
		return vec4(fract(p), a + (r3 - 0.5) * 0.05, 26.0 + 22.0 * r4);
	}
	if (mode < 3.5)                       // 3: a burst from the subject
	{
		float a = r1 * TAU;
		vec2 p = uCtr.xy + vec2(cos(a), sin(a)) * sqrt(r2) * 30.0 * px;
		return vec4(fract(p), a, 8.0 + 100.0 * r4 * r4);
	}
	if (mode < 4.5)                       // 4: a few blots, growing outward
	{
		uint b = uint(r4 * 5.0);
		uint ss = uint(uShot.x * 9973.0);
		vec2 c = vec2(0.12 + 0.76 * rnd(b, ss + 91u), 0.15 + 0.7 * rnd(b, ss + 92u));
		float a = r1 * TAU;
		vec2 p = c + vec2(cos(a), sin(a)) * sqrt(r2) * 22.0 * px;
		return vec4(fract(p), a, 0.0);
	}
	if (mode < 5.5)                       // 5: the frame edges, walking inward
	{
		float side = floor(r4 * 4.0);
		vec2 p = side < 1.0 ? vec2(r1, 0.004) : side < 2.0 ? vec2(r1, 0.996) : side < 3.0 ? vec2(0.003, r1) : vec2(0.997, r1);
		float a = atan(0.5 - p.y, 0.5 - p.x) + (r3 - 0.5) * 1.4;
		return vec4(p, a, 0.0);
	}
	// 6: horizontal sheets (lines of agents marching up and down)
	float row = (floor(r4 * 9.0) + 0.5) / 9.0;
	return vec4(r1, row, (r3 < 0.5 ? 0.25 : 0.75) * TAU, 12.0 * r2);
}

void main()
{
	ivec2 tc = ivec2(gl_FragCoord.xy);
	ivec2 size = textureSize(sTD2DInputs[0], 0);
	uint id = uint(tc.x + tc.y * size.x);
	uint fr = uint(uShot.y);
	uint evn = uint(uEvent.w) * 7919u + 13u;
	vec4 s = texelFetch(sTD2DInputs[0], tc, 0);
	vec2 px = 1.0 / uRes.xy;

	if (uEvent.x > 0.5)
	{
		fragColor = spawn(uShot.z, id, evn);
		return;
	}
	if (uEvent.y > 0.0 && rnd(id, evn + 500u) < uEvent.y)
	{
		float m = uField.w;
		if (m > 3.5)                      // 4: blown off where it lies, in a random direction
		{
			fragColor = vec4(s.xy, rnd(id, evn + 1u) * TAU, 6.0 + 26.0 * rnd(id, evn + 2u));
			return;
		}
		fragColor = spawn(m < 0.5 ? 0.0 : m < 1.5 ? 2.0 : m < 2.5 ? 1.0 : 3.0, id, evn);
		return;
	}
	if (uEvent.z > 0.0 && rnd(id, evn + 900u) < uEvent.z)
	{
		fragColor = spawn(1.0, id, evn);
		return;
	}

	vec2 p = s.xy;
	float ang = s.z;
	float timer = s.w;
	float step_ = uSpecies.w * (0.8 + 0.4 * rnd(id, 3u));
	if (timer > 0.5)
	{
		timer -= 1.0;
		step_ *= uRes.z;
	}
	else
	{
		float gain = uField.x * (1.0 - 2.0 * uShot.w);
		float sd = uSpecies.y * (0.75 + 0.5 * rnd(id, 7u));
		float sa = uSpecies.x;
		vec2 dF = vec2(cos(ang), sin(ang));
		vec2 dL = vec2(cos(ang + sa), sin(ang + sa));
		vec2 dR = vec2(cos(ang - sa), sin(ang - sa));
		float F = smell(p + dF * sd * px, gain);
		float L = smell(p + dL * sd * px, gain);
		float R = smell(p + dR * sd * px, gain);
		float r = rnd(id, fr + 100u);
		float turn = uSpecies.z;
		if (F >= L && F >= R) { }
		else if (F < L && F < R) ang += (r < 0.5 ? turn : -turn);
		else if (L > R) ang += turn;
		else ang -= turn;
		ang += (r - 0.5) * uField.z;
		ang += uExtra.x * sin(uExtra.y - ang);
		if (uExtra.z > 0.0 && rnd(id, fr + 300u) < uExtra.z && texture(sTD2DInputs[2], p).r < 0.2)
		{
			fragColor = spawn(1.0, id, fr * 31u + 5u);
			return;
		}
	}
	p += vec2(cos(ang), sin(ang)) * step_ * px;
	if (uExtra.x > 0.0 && p != fract(p))      // a drifting agent that leaves the frame starts again on the shape
	{
		fragColor = spawn(1.0, id, fr * 31u + 7u);
		return;
	}
	p = fract(p);
	fragColor = vec4(p, mod(ang, TAU), timer);
}
