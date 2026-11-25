out vec3 vWP;
out vec3 vLP;
void main()
{
    vec3 p = TDPos();
    vec4 wp = TDDeform(p);
    vWP = wp.xyz;
    vLP = p;
    gl_Position = TDWorldToProj(wp);
}
