// sc_vector_scope: one instanced quad per beam segment (sample i to i+1 of one gun).
// The quad is stretched over the segment plus a margin of a few beam widths.
uniform sampler2D sPath;   // x, y, pen, u (1024 wide, 4 rows per gun)
uniform vec4 uBeam;        // sigma (screen units), gain, retrace visibility, number of guns
uniform vec4 uTintA;       // rgb colour of gun 0
uniform vec4 uTintB;       // rgb colour of the last gun; w = palette mode (1 = arcade palette)
uniform vec4 uLabel;       // x > 0: the last gun is the Describe label; y = its beam width; z > 0: the last gun is the take's own label, drawn at that width

out vec3 vLocal;           // x along the segment from its start, y across, z = segment length
out vec4 vCol;

const float ASPECT = 1.7777778;

vec4 fetchPath(int i, int gun)
{
	return texelFetch(sPath, ivec2(i & 1023, (i >> 10) + 4 * gun), 0);
}

vec3 arcade(float k)
{
	// ident palette, pushed towards a colour vector monitor
	vec3 c[6] = vec3[6](vec3(1.0, 0.22, 0.12), vec3(1.0, 0.78, 0.10), vec3(0.10, 0.75, 1.0),
	                    vec3(0.45, 1.0, 0.25), vec3(1.0, 0.25, 0.65), vec3(0.95, 0.92, 0.85));
	return c[int(mod(k, 6.0))];
}

void main()
{
	vec3 g = TDPos();
	int id = TDInstanceID();
	int seg = id & 4095;
	int gun = id >> 12;
	vec4 a = fetchPath(seg, gun);
	vec4 b = fetchPath(min(seg + 1, 4095), gun);
	float sigma = uBeam.x;
	bool isLabel = uLabel.x > 0.5 && gun == int(uBeam.w + 0.5) - 1;
	float guns = uBeam.w - step(0.5, uLabel.x);          // guns that draw the picture
	if (isLabel || (uLabel.z > 0.5 && gun == int(uBeam.w + 0.5) - 1))
		sigma = uLabel.y;
	float pen = min(a.z, b.z);
	float vis = mix(uBeam.z * max(a.z, b.z), 1.0, clamp(pen, 0.0, 1.0)) * max(pen, uBeam.z);
	vec2 d = b.xy - a.xy;
	float L = length(d);
	vec2 dir = L > 1e-6 ? d / L : vec2(1.0, 0.0);
	vec2 nrm = vec2(-dir.y, dir.x);
	float r = sigma * 3.5;
	// corner (g.x, g.y) in -0.5..0.5
	float along = (g.x + 0.5) * (L + 2.0 * r) - r;
	float across = g.y * 2.0 * r;
	vec2 p = a.xy + dir * along + nrm * across;
	vLocal = vec3(along, across, L);
	float kk = guns > 1.5 ? float(gun) / (guns - 1.0) : 0.0;
	vec3 tint = mix(uTintA.rgb, uTintB.rgb, kk);
	if (uTintB.w > 0.5)
		tint = arcade(float(gun) + uTintA.w);
	if (isLabel)
		tint = uTintB.w > 0.5 ? vec3(0.95, 0.92, 0.85) : uTintA.rgb;
	vCol = vec4(tint * uBeam.y * vis, sigma);              // alpha carries the beam width to the pixel shader
	bool dead = gun >= int(uBeam.w + 0.5) || seg >= 4095 || vis <= 0.0005;
	gl_Position = dead ? vec4(2.0, 2.0, 2.0, 1.0) : vec4(p.x / ASPECT, p.y, 0.0, 1.0);
}
