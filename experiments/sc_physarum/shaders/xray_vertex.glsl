// X-ray of a model: brightness is how edge-on the surface is to the camera, summed through the whole object.
out vec3 vN;

void main()
{
	vec4 wp = TDDeform(TDPos());
	gl_Position = TDWorldToProj(wp);
	vec3 wn = TDDeformNorm(TDNormal());
	vN = (uTDMats[TDCameraIndex()].cam * vec4(wn, 0.0)).xyz;
}
