// sc_vector_scope: light left by a Gaussian beam that moved along one segment in one time step.
// It is the line integral of the beam spot along the segment, so joined segments add up
// seamlessly and brightness falls as the beam moves faster (after woscope, m1el 2014).
uniform vec4 uBeam;        // sigma, gain, retrace visibility, guns

in vec3 vLocal;
in vec4 vCol;
out vec4 oFragColor;

float erfApprox(float x)
{
	float s = sign(x), a = abs(x);
	float t = 1.0 + (0.278393 + (0.230389 + (0.000972 + 0.078108 * a) * a) * a) * a;
	t *= t;
	return s - s / (t * t);
}

void main()
{
	float sigma = vCol.a;      // uBeam.x, or the Describe label's own width
	float s = 1.41421356 * sigma;
	float L = vLocal.z;
	float x = vLocal.x, y = vLocal.y;
	float across = exp(-y * y / (s * s));
	float along;
	if (L < 1e-5)
		along = exp(-x * x / (s * s));
	else
		along = (erfApprox(x / s) - erfApprox((x - L) / s)) * s * 0.8862269 / L;   // sqrt(pi)/2
	float v = across * along;
	oFragColor = vec4(vCol.rgb * v, v);
}
