// Environment map (equirectangular) for the props: a black studio with long
// fluorescent tubes and one overhead softbox, so glossy and metallic surfaces
// have something to reflect. The accent tube colour follows the room (section mod 4).
uniform vec4 uA;   // room, daylight (0 or 1), 0, 0
out vec4 fragColor;

float band(float x, float c, float w) { return smoothstep(w, w * 0.5, abs(x - c)); }

void main()
{
    vec2 uv = vUV.st;
    float mode = uA.x;                                         // the room, as in bg.frag
    vec3 accent = vec3(0.62, 1.0, 0.45);                       // fluorescent green
    if (mode > 4.5)      accent = vec3(1.0, 0.96, 0.84);       // empty black room: white only
    else if (mode > 2.5) accent = vec3(0.35, 0.65, 1.0);       // CRT blue
    else if (mode > 1.5) accent = vec3(1.0, 0.16, 0.10);       // warning red
    else if (mode > 0.5) accent = vec3(1.0, 0.62, 0.20);       // amber
    vec3 white = vec3(1.0, 0.96, 0.84);

    vec3 col = vec3(0.012, 0.016, 0.014);
    // floor bounce and a soft horizon
    col += vec3(0.05, 0.05, 0.04) * smoothstep(0.5, 0.0, uv.y);
    // tall tubes standing round the prop
    float vert = smoothstep(0.22, 0.30, uv.y) * smoothstep(0.92, 0.84, uv.y);
    col += white  * 7.0 * band(uv.x, 0.12, 0.012) * vert;
    col += accent * 8.0 * band(uv.x, 0.31, 0.018) * vert;
    col += white  * 5.0 * band(uv.x, 0.55, 0.008) * vert;
    col += accent * 8.0 * band(uv.x, 0.71, 0.022) * vert;
    col += white  * 6.0 * band(uv.x, 0.90, 0.012) * vert;
    // overhead softbox
    col += white * 2.2 * smoothstep(0.86, 0.95, uv.y);
    // daylight rooms (uA.y > 0.5): a white cyclorama with a darker floor and two black flags
    if (uA.y > 0.5) {
        col = mix(vec3(0.30, 0.29, 0.26), vec3(1.5, 1.45, 1.3), smoothstep(0.30, 0.55, uv.y));
        col *= 1.0 - 0.93 * band(uv.x, 0.31, 0.05) * vert;
        col *= 1.0 - 0.93 * band(uv.x, 0.71, 0.03) * vert;
        col += white * 3.0 * smoothstep(0.86, 0.95, uv.y);
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
