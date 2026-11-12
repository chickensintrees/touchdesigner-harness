// A strip along z: x in [-0.5, 0.5] is across the ribbon, z = +0.5 the newest end.
// The ribbon hangs as a curtain: its top edge sits at the sung note.
uniform sampler2D sNotes;
uniform vec4 uDim;     // x width, y depth, z rows, w curtain drop
uniform vec4 uRib;     // x base height, y height range, z x range, w unused
out vec2 vRC;          // x: 0 top .. 1 bottom, y: 0 newest .. 1 oldest
out float vSpark;
out float vVox;

void main()
{
    vec3 p = TDPos();
    float v = 0.5 - p.z;
    float row = floor(v * (uDim.z - 1.0) + 0.5);
    vec4 s = texelFetch(sNotes, ivec2(0, int(row)), 0);
    float across = p.x + 0.5;
    float y = uRib.x + s.r * uRib.y - across * uDim.w * (0.35 + 0.65 * min(s.a, 1.0));
    vec3 wp3 = vec3(s.b * uRib.z, y, -v * uDim.y);
    vec4 wp = TDDeform(wp3);
    vRC = vec2(across, v);
    vSpark = s.g;
    vVox = s.a;
    gl_Position = TDWorldToProj(wp);
}
