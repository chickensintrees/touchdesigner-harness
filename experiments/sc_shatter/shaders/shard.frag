// sc_shatter: lit shards. Outer skin takes the model's basecolor; inner skin and fracture walls
// are gold or red. Light is a key lamp plus a procedural studio (softbox overhead, strip at the side).
uniform sampler2D sTex;
uniform vec4 uLight;    // xyz direction to the key light, w reflections on
uniform vec4 uKey;      // rgb key colour * intensity, w ambient
uniform vec4 uInner;    // rgb inner colour, w emissive amount
uniform vec4 uTint;     // rgb colour for untextured subjects (or multiplier), w 1 = use texture
uniform vec4 uLook;     // x roughness, y studio reflection strength, z 1 = unlit flat white (1-bit takes), w reflection alpha
uniform vec4 uHits;     // x hit_low, y hit_high, z pulse, w inner metalness
uniform vec4 uMode;     // x layout, y grid pitch, z skin metal (gold), w glass (additive)
uniform vec4 uEnv;      // rgb studio ambient tint, w burst glow
uniform vec4 uInput;    // x 1 = the subject is the slab carrying the scene's Input picture (sTex)

in vec3 vWorld;
in vec3 vN;
in vec2 vUV;
in vec4 vData;
in vec3 vObj;
in vec4 vCam;
out vec4 oFragColor;

vec3 studio(vec3 r)
{
	// a large softbox overhead, slightly in front; a narrow strip light at the left; dim room
	vec2 s = r.xz / max(r.y, 0.05);
	float box = (1.0 - smoothstep(0.75, 0.85, abs(s.x - 0.25))) * (1.0 - smoothstep(0.38, 0.46, abs(s.y - 0.35))) * step(0.0, r.y);
	float strip = (1.0 - smoothstep(0.10, 0.14, abs(r.y - 0.22))) * smoothstep(0.55, 0.62, -r.x);
	float room = mix(0.04, 0.42, smoothstep(-0.35, 0.6, r.y));
	return uEnv.rgb * room + vec3(1.0, 0.97, 0.92) * box * (9.0 + 8.0 * uHits.y) + vec3(0.75, 0.88, 1.0) * strip * 5.0;
}

void main()
{
	TDCheckDiscard();
	if (vCam.w > 0.5)
	{
		oFragColor = TDOutputSwizzle(vec4(0.0, 0.0, 0.0, 1.0));
		return;
	}
	float kind = vData.x;
	float A = vData.z;
	bool mirror = vData.w > 0.5;
	// while the object is whole its lining is hidden (it pokes through thin features otherwise)
	if (kind > 0.5 && A < 0.004)
		discard;
	if (uLook.z > 0.5)
	{
		// 1-bit: white chips, no light. Inner faces a shade darker so the post dither can use them.
		float v = kind > 0.5 ? 0.55 : 1.0;
		// Input: the chips carry the picture's brightness, which the post dither turns into dots
		if (uInput.x > 0.5 && kind < 0.5)
			v = clamp(dot(pow(max(texture(sTex, vUV).rgb, 0.0), vec3(2.2)), vec3(0.3, 0.6, 0.1)) * 1.5 + 0.04, 0.0, 1.0);
		oFragColor = TDOutputSwizzle(vec4(vec3(v) * uTint.rgb, 1.0));
		return;
	}
	vec3 V = normalize(vCam.xyz - vWorld);
	vec3 n = normalize(vN);
	if (dot(n, V) < 0.0)
		n = -n;
	vec3 L = normalize(uLight.xyz);
	float ndl = max(dot(n, L), 0.0);
	float ndv = max(dot(n, V), 1e-3);
	vec3 Hh = normalize(L + V);
	float ndh = max(dot(n, Hh), 0.0);

	vec3 base;
	vec3 F0 = vec3(0.045);
	float metal = 0.0;
	float rough = uLook.x;
	if (kind < 0.5)
	{
		vec3 tex = texture(sTex, vUV).rgb;
		base = mix(uTint.rgb, pow(max(tex, 0.0), vec3(2.2)) * uTint.rgb, uTint.w);
		// Input: the picture keeps its own colours (no take tint)
		if (uInput.x > 0.5)
			base = pow(max(tex, 0.0), vec3(2.2));
		if (uMode.z > 0.01)
		{
			// gilded: the texture only darkens the gold (eyes, mouth, base stay readable)
			float lum = dot(base, vec3(0.3, 0.6, 0.1));
			vec3 gold = vec3(1.0, 0.70, 0.22) * (0.25 + 0.75 * smoothstep(0.02, 0.45, lum));
			base = mix(base, gold, uMode.z);
			metal = uMode.z;
			F0 = mix(F0, gold, uMode.z);
		}
	}
	else
	{
		base = uInner.rgb;
		metal = uHits.w;
		F0 = mix(vec3(0.05), uInner.rgb, metal);
		rough = mix(rough, 0.32, 0.5);
		// walls catch a little more light at their outer edge
		if (kind > 1.5) base *= 1.15;
	}
	float a2 = max(rough * rough, 0.002);
	float a4 = a2 * a2;
	float dd = ndh * ndh * (a4 - 1.0) + 1.0;
	float D = a4 / (3.14159 * dd * dd);
	vec3 F = F0 + (1.0 - F0) * pow(1.0 - ndv, 5.0);
	vec3 spec = F * min(D, 60.0) * ndl * 0.25;
	vec3 R = reflect(-V, n);
	vec3 env = studio(R) * F * uLook.y * (1.0 - 0.6 * rough);
	// Input: a flat slab mirrors the whole softbox at once, which washes the picture out
	if (uInput.x > 0.5 && kind < 0.5 && uMode.z < 0.01)
		env *= 0.1;
	vec3 amb = uEnv.rgb * uKey.w * (0.55 + 0.45 * n.y);
	vec3 col = base * (1.0 - metal) * (uKey.rgb * ndl + amb) + uKey.rgb * spec + env;
	col += base * metal * (uKey.rgb * ndl * 0.16 + amb * 0.5);
	// inner faces glow: more while the object is open, and with every kick
	if (kind > 0.5)
		col += uInner.rgb * uInner.w * (0.35 + 0.65 * clamp(A * 2.0, 0.0, 1.0) + 1.2 * uHits.x);
	// freshly burst outer shards flash
	col += base * uEnv.w * smoothstep(0.0, 0.25, A) * uHits.z * 0.6;

	float alpha = 1.0;
	if (uMode.w > 0.5)
	{
		// glass: drawn additively without depth, so only rims, glints and reflections add up
		float fr = pow(1.0 - ndv, 2.2);
		vec3 tintc = kind < 0.5 ? uTint.rgb : uInner.rgb;
		col = tintc * (0.02 + 0.55 * fr) + (uKey.rgb * spec * 0.6 + env * 0.35) * mix(vec3(1.0), tintc, 0.5);
		if (kind > 0.5)
			col += uInner.rgb * uInner.w * (0.1 + 0.5 * clamp(A * 2.0, 0.0, 1.0) + 0.9 * uHits.x) * (0.3 + fr);
		col *= 1.0 + 0.5 * uHits.x;
		// Input: the picture glows on whichever face of each shard is turned to the camera
		if (uInput.x > 0.5 && kind < 0.5 && dot(vN, V) > 0.0)
			col += pow(max(texture(sTex, vUV).rgb, 0.0), vec3(2.2)) * mix(vec3(1.0), uTint.rgb, 0.3) * 1.3;
		oFragColor = TDOutputSwizzle(vec4(col, 0.0));
		return;
	}
	if (mirror)
	{
		float h = max(-vWorld.y, 0.0);
		alpha = uLook.w * exp(-h * 2.2);
		col *= alpha;
	}
	oFragColor = TDOutputSwizzle(vec4(col, alpha));
}
