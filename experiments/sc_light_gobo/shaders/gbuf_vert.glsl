// G-buffer vertex shader. Projects with OUR camera (position, target, tan of half the horizontal
// field of view), not TouchDesigner's, so the ray-march in beam.frag lines up pixel for pixel.
uniform vec4 uRo;   // xyz eye, w tan(half hfov)
uniform vec4 uTa;   // xyz target, w aspect (w/h)
out vec3 vW;
out vec3 vN;
void main()
{
	vec4 wp = TDDeform(TDPos());
	vW = wp.xyz;
	vN = TDDeformNorm(TDNormal());
	vec3 f = normalize(uTa.xyz - uRo.xyz);
	vec3 up = abs(f.y) > 0.98 ? vec3(0.0, 0.0, -1.0) : vec3(0.0, 1.0, 0.0);
	vec3 r = normalize(cross(f, up));
	vec3 u = cross(r, f);
	vec3 d = wp.xyz - uRo.xyz;
	float z = dot(d, f);
	float n = 0.05, fa = 90.0;
	gl_Position = vec4(dot(d, r) / uRo.w, dot(d, u) * uTa.w / uRo.w, (z * (fa + n) - 2.0 * fa * n) / (fa - n), z);
}
