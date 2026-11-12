// Scatter: every grid point looks up its agent and lands on that agent's pixel of the trail map.
uniform sampler2D sAgents;
out float vFly;

void main()
{
	vec3 g = TDPos();
	float SIDE = float(textureSize(sAgents, 0).x);
	ivec2 tc = ivec2(clamp(floor((g.xy + 0.5) * (SIDE - 1.0) + 0.5), 0.0, SIDE - 1.0));
	vec4 a = texelFetch(sAgents, tc, 0);
	gl_Position = vec4(a.xy * 2.0 - 1.0, 0.0, 1.0);
	gl_PointSize = 1.0;
	vFly = step(0.5, a.w);
}
