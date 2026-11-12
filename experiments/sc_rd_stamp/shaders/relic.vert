// "Relic" take: pass object and world position to relic.frag, which projects the
// chemistry onto the model from three sides (the library UVs are an atlas of shards:
// captures/c6x_in.png shows the pattern chopped to confetti through them).
out vec3 vWP;
out vec3 vLP;
out vec3 vWN;
out vec3 vLN;
out vec3 vCam;
flat out mat3 vToWorld;   // TDCameraIndex() only exists in the vertex shader
void main()
{
    vec3 p = TDPos();
    vec4 wp = TDDeform(p);
    vWP = wp.xyz;
    vLP = p;
    vLN = TDNormal();
    vWN = TDDeformNorm(TDNormal());
    vCam = uTDMats[TDCameraIndex()].camInverse[3].xyz;
    vToWorld = mat3(uTDMats[TDCameraIndex()].world);
    gl_Position = TDWorldToProj(wp);
}
