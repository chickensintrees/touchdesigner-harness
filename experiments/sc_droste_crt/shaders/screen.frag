// What the CRT's glass shows: last frame of the master camera, turned one step
// (hue, gain, rotation, zoom, invert, phosphor tint), so every level of the tunnel
// is one more application of this shader.
// input 0: the feed (previous master frame, possibly delayed)   input 1: terminal text
// input 2: the scene's Input picture (black when there is none)
uniform vec4 uT;     // hue degrees, gain, rotation degrees, zoom
uniform vec4 uM;     // invert, mono, flip x, scanline strength
uniform vec4 uS;     // shot age (s), text amount, pulse, rounded-edge amount
uniform vec4 uTint;  // phosphor colour rgb, saturation
uniform vec4 uX;     // text scale about the centre, kick flash amount, Input lighten blend
uniform vec4 uI;     // Input picture on the glass: on, mix, scale about the centre, luma key amount
out vec4 fragColor;

vec3 hueRot(vec3 c, float deg) {
    float a = radians(deg);
    float cs = cos(a), sn = sin(a);
    const vec3 k = vec3(0.57735);
    return c * cs + cross(k, c) * sn + k * dot(k, c) * (1.0 - cs);
}

void main() {
    vec2 uv = vUV.st;
    vec2 asp = vec2(16.0 / 9.0, 1.0);
    vec2 p = uv * 2.0 - 1.0;

    // per-level transform about the screen centre
    float a = radians(uT.z);
    vec2 z = p * asp;
    z = mat2(cos(a), -sin(a), sin(a), cos(a)) * z / max(uT.w, 0.05);
    z /= asp;
    if (uM.z > 0.5) z.x = -z.x;
    vec2 suv = z * 0.5 + 0.5;
    vec3 c = texture(sTD2DInputs[0], suv).rgb;
    float inside = step(0.0, suv.x) * step(suv.x, 1.0) * step(0.0, suv.y) * step(suv.y, 1.0);
    c *= inside;
    c = max(c, vec3(0.0));

    c = hueRot(c, uT.x);
    float l = dot(c, vec3(0.299, 0.587, 0.114));
    c = max(mix(vec3(l), c, uTint.w), vec3(0.0));
    c = mix(c, l * uTint.rgb * 1.6, uM.y);
    c = mix(c, 1.0 - min(c, vec3(1.0)), uM.x);
    c *= uT.y;
    c = c / (1.0 + 0.22 * c);          // soft clip: the loop cannot run away

    // a picture given through the scene's Input, drawn on this level the way the text is: it
    // takes this take's phosphor, and the deeper levels get it from the feed, older each step
    if (uI.x > 0.5) {
        vec2 iuv = (uv - 0.5) / max(uI.z, 0.05) + 0.5;
        float iin = step(0.0, iuv.x) * step(iuv.x, 1.0) * step(0.0, iuv.y) * step(iuv.y, 1.0);
        vec3 ic = max(texture(sTD2DInputs[2], iuv).rgb, vec3(0.0));
        float il = dot(ic, vec3(0.299, 0.587, 0.114));
        float key = mix(1.0, 0.3 + 0.7 * smoothstep(0.05, 0.55, il), uI.w);
        ic = mix(ic, il * uTint.rgb * 1.6, uM.y);
        vec3 lit = max(c, ic * uI.y * key);
        c = mix(c, mix(mix(c, ic, uI.y * key), lit, uX.z), iin);
    }

    // terminal text drawn on this level; deeper levels get it from the feed
    vec2 tuv = (uv - 0.5) / max(uX.x, 0.05) + 0.5;
    vec4 t = texture(sTD2DInputs[1], tuv);
    t *= step(0.0, tuv.x) * step(tuv.x, 1.0) * step(0.0, tuv.y) * step(tuv.y, 1.0);
    c = mix(c, uTint.rgb * 1.5, t.a * uS.y);

    // the tube: scanlines, edge falloff, rounded corners
    float sl = 0.5 + 0.5 * sin(uv.y * 3.14159 * 2.0 * 180.0);
    c *= 1.0 - uM.w * 0.55 * sl;
    c *= 1.0 - 0.22 * uM.w * pow(length(p), 4.0);
    float rr = 0.085 * uS.w;
    vec2 d = abs(p * asp) - (asp - vec2(0.10 * uS.w + 0.0001));
    float sd = length(max(d, vec2(0.0))) - rr;
    c *= 1.0 - smoothstep(-0.012, 0.004, sd) * step(0.01, uS.w);

    // power-on flash at the start of a shot; it then travels down the levels
    float f = exp(-uS.x * 14.0);
    c = mix(c, vec3(0.85, 1.0, 0.92) * 1.5, f * 0.85);
    c += 0.05 * uS.z * uTint.rgb;
    // each kick lights the glass; the next level sees that a step later, so it walks inward
    c += uX.y * mix(vec3(1.0), uTint.rgb, 0.5);

    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
