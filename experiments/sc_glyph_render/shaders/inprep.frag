// inprep.frag: makes another scene's picture (the COMP's Input) look like what
// tone.frag expects from the model render: premultiplied luminance, with alpha 0
// where the picture is dark. Those dark parts become the void, so the picture
// keeps a silhouette, a keyline and a white rim, as a model does.
// input 0: the Input TOP (any resolution)
uniform vec4 uIn;    // x zoom, y roll (radians), z w centre offset (uv)
uniform vec4 uKey;   // x gamma (2 puts mid grey near the black/white line), y z luminance where the key opens
out vec4 fragColor;

void main()
{
    vec2 p = (vUV.st - 0.5) * vec2(1.7778, 1.0);
    float cs = cos(uIn.y), sn = sin(uIn.y);
    p = mat2(cs, -sn, sn, cs) * p / max(uIn.x, 0.05);
    vec2 uv = p / vec2(1.7778, 1.0) + 0.5 + uIn.zw;
    vec3 c = texture(sTD2DInputs[0], uv).rgb;
    float l = clamp(dot(c, vec3(0.30, 0.59, 0.11)), 0.0, 4.0);
    float a = smoothstep(uKey.y, uKey.z, l);
    float v = pow(l, uKey.x);
    fragColor = TDOutputSwizzle(vec4(vec3(v) * a, a));
}
