// Camera pointed at its own monitor. Input 0: the raster. Input 1: last frame of this pass.
// The loop gain may pass 1; a soft knee (the camera tube saturating) keeps it finite.
uniform vec4 uFb;    // x loop gain, y rotation (radians), z zoom, w hue rotation per pass (radians)
uniform vec4 uFb2;   // x black level cut per pass, y unused, z raster gain into the loop, w mirror 0/1
out vec4 fragColor;

vec3 hueRot(vec3 c, float a)
{
    const vec3 k = vec3(0.57735);
    float ca = cos(a), sa = sin(a);
    return c * ca + cross(k, c) * sa + k * dot(k, c) * (1.0 - ca);
}

void main()
{
    vec2 uv = vUV.st;
    vec3 r = texture(sTD2DInputs[0], uv).rgb;
    vec2 asp = vec2(1.7778, 1.0);
    vec2 p = (uv - 0.5) * asp;
    float c = cos(uFb.y), s = sin(uFb.y);
    p = mat2(c, -s, s, c) * p / max(uFb.z, 0.01);
    if (uFb2.w > 0.5) p.x = abs(p.x);
    vec2 fuv = p / asp + 0.5;
    vec3 f = texture(sTD2DInputs[1], fuv).rgb;
    // the input is mirror-extended, so a turned frame has no edge; only the far corners fade
    f *= 1.0 - smoothstep(0.85, 1.25, length(p));
    f = max(hueRot(f, uFb.w) - uFb2.x, 0.0);   // black level: faint haze does not go round again
    float fl = dot(f, vec3(0.299, 0.587, 0.114));
    f = max(mix(vec3(fl), f, 1.18), 0.0);     // a camera loop gains chroma as well as level
    vec3 o = r * uFb2.z + f * uFb.x;
    o = o / (1.0 + 0.22 * o);                 // tube saturation
    o = mix(r, o, step(0.001, uFb.x));        // loop off: pass the raster untouched
    if (any(isnan(o)) || any(isinf(o))) o = vec3(0.0);
    fragColor = TDOutputSwizzle(vec4(o, 1.0));
}
