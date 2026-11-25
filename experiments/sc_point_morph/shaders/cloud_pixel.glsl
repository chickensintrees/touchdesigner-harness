in vec4 vCol;
in float vSoft;       // 1: a whole raster cell (paper with one ink disc), 0: a shaded disc
in float vRad;        // raster: radius of the ink disc as a fraction of the cell
in vec3 vPaper;
uniform vec4 uGain;   // x overall point gain
out vec4 oFragColor;

void main()
{
	TDCheckDiscard();
	float d = length(gl_PointCoord - 0.5) * 2.0;
	if (vSoft > 0.5)
	{
		float ink = 1.0 - smoothstep(vRad - 0.08, vRad + 0.08, d);
		oFragColor = TDOutputSwizzle(vec4(mix(vPaper, vCol.rgb, ink), 1.0));
		return;
	}
	if (d > 1.0)
		discard;
	// opaque, depth-tested discs with a slightly darker edge so neighbours stay distinct
	oFragColor = TDOutputSwizzle(vec4(vCol.rgb * uGain.x * (1.0 - 0.35 * d * d), 1.0));
}
