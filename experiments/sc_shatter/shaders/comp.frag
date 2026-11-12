// sc_shatter: studio backdrop (floor with a pool of light and the shards' projected shadows, a
// seamless wall) under the render. Input 0: render (premultiplied), input 1: blurred shadow map.
uniform vec4 uCamPos;   // xyz, w tan(half horizontal fov)
uniform vec4 uCamTgt;   // xyz, w unused
uniform vec4 uFloorA;   // rgb floor in the light pool, w pool radius
uniform vec4 uFloorB;   // rgb floor far away, w shadow strength
uniform vec4 uWallA;    // rgb wall at the horizon, w floor pattern (0 none, 1 carpet tiles, 2 ruled sheet)
uniform vec4 uWallB;    // rgb wall at the top, w shadow map half extent
uniform vec4 uFx;       // x pulse, y hit_low, z evolve, w pool centre x
out vec4 fragColor;

void main()
{
	vec2 uv = vUV.st;
	vec3 fwd = normalize(uCamTgt.xyz - uCamPos.xyz);
	vec3 right = normalize(cross(fwd, vec3(0.0, 1.0, 0.0)));
	vec3 up = cross(right, fwd);
	vec2 ndc = uv * 2.0 - 1.0;
	float th = uCamPos.w;
	vec3 rd = normalize(fwd + right * ndc.x * th + up * ndc.y * th * 720.0 / 1280.0);

	vec3 wall = mix(uWallA.rgb, uWallB.rgb, smoothstep(0.0, 0.55, rd.y));
	// a soft glow on the wall behind the subject
	vec3 col = wall;
	if (rd.y < -1e-4)
	{
		float t = -uCamPos.y / rd.y;
		vec3 p = uCamPos.xyz + rd * t;
		float r = length(p.xz - vec2(uFx.w, 0.0));
		float pool = 1.0 - smoothstep(uFloorA.w * 0.25, uFloorA.w, r);
		vec3 fl = mix(uFloorB.rgb, uFloorA.rgb, pool * (0.85 + 0.25 * uFx.x));
		int pat = int(uWallA.w + 0.5);
		if (pat == 1)
		{
			vec2 g = abs(fract(p.xz * 1.0 + 0.5) - 0.5);
			float w = fwidth(p.x) + fwidth(p.z);
			float line = 1.0 - smoothstep(0.0, 0.012 + w, min(g.x, g.y));
			fl *= 1.0 - 0.35 * line;
		}
		else if (pat == 2)
		{
			float g = abs(fract(p.z * 4.0) - 0.5);
			float w = fwidth(p.z) * 4.0;
			float line = 1.0 - smoothstep(0.0, 0.03 + w, g);
			fl = mix(fl, fl * vec3(0.45, 0.62, 0.78), 0.55 * line);
		}
		float R = uWallB.w;
		vec2 suv = vec2(p.x / (2.0 * R) + 0.5, -p.z / (2.0 * R) + 0.5);
		float sh = 0.0;
		if (suv.x > 0.0 && suv.x < 1.0 && suv.y > 0.0 && suv.y < 1.0)
			sh = texture(sTD2DInputs[1], suv).a;
		fl *= 1.0 - uFloorB.w * sh;
		// the floor runs up into the wall without a seam
		float far = smoothstep(0.0, 0.16, -rd.y);
		col = mix(wall, fl, far);
	}
	vec4 ren = texture(sTD2DInputs[0], uv);
	col = ren.rgb + col * (1.0 - clamp(ren.a, 0.0, 1.0));
	fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
