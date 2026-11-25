// G-buffer pixel shader: world normal in rgb, distance from the eye in alpha (0 = nothing here).
uniform vec4 uRo;
in vec3 vW;
in vec3 vN;
out vec4 oFragColor;
void main()
{
	TDCheckDiscard();
	oFragColor = vec4(normalize(vN), length(vW - uRo.xyz));
}
