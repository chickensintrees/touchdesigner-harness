// The scan processor. One instance = one scan line, drawn as a camera-facing ribbon.
// The line's deflection follows the source brightness along it.
// The same shader also draws the solid black hold-out surface (uRas.w > 0.5) used by the
// hidden-line takes: there the grid's own rows give v and nothing is expanded.
uniform sampler2D sSrc;
uniform sampler2D sSpec;
uniform vec4 uRas;    // x line count, y segments per line, z beam width px, w 1 = solid surface
uniform vec4 uDisp;   // x deflection in the raster plane, y deflection in depth, z spectrum amount, w arrival 0..1
uniform vec4 uWob;    // x bass bend, y sync tear, z time, w oscillator wobble
uniform vec4 uSrcXf;  // x source zoom, y offset x, z offset y, w scan: 0 horizontal, 1 vertical, 2 disc (rings), 3 drum (cylinder)
uniform vec4 uGeo;    // x raster width, y raster height, z camera distance, w seed
out float vSide;
out float vLum;
out float vU;
out float vLine;
out float vSpeed;
out float vFade;
out vec2 vSuv;      // where on the source picture this point of the line is looking

vec2 gSuv = vec2(0.5);
float gLen0 = 1.0;   // undeflected length of one unit of u, set by rpos

float hash(float n) { return fract(sin(n * 127.1) * 43758.5453); }
float vnoise(float x)
{
    float i = floor(x); float f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    return mix(hash(i), hash(i + 1.0), f);
}

// the hub's full spectrum is log-frequency; the music sits in about 14%..80% of it
float spec(float x)
{
    float s = textureLod(sSpec, vec2(0.15 + 0.6 * clamp(x, 0.0, 1.0), 0.5), 0.0).r;
    return pow(clamp(s * 5.0, 0.0, 4.0), 0.6);
}

vec3 rpos(float u, float v, out float lum, out float fade)
{
    float t = uWob.z;
    float a = uDisp.w;
    // wobbulation along the scan direction: bass bends the raster, a hit shears lines sideways
    float bend = uWob.x * sin(v * 4.2 + t * 1.3) + uWob.x * 0.5 * sin(v * 11.0 - t * 2.1);
    float band = smoothstep(0.45, 0.75, vnoise(v * 3.1 + floor(t * 14.0) * 7.3));
    float tear = uWob.y * band * (vnoise(v * 23.0 + t * 37.0) - 0.3);
    float us = u + bend + tear;

    float mode = uSrcXf.w;
    float ang = us * 6.2832;
    vec2 cs = vec2(cos(ang), sin(ang));
    float rad = 0.06 + 0.94 * v;
    vec2 sc = mode > 0.5 ? vec2(v, us) : vec2(us, v);
    if (mode > 2.5) sc = vec2(fract(1.0 - us), v);                            // drum: the picture wraps round
    else if (mode > 1.5) sc = 0.5 + rad * 0.5 * cs * vec2(0.5625, 1.0);  // disc: rings scan an upright picture
    vec2 suv = (sc - 0.5) / uSrcXf.x + 0.5 + uSrcXf.yz;
    if (mode > 2.5) suv.x = fract(suv.x);
    gSuv = suv;
    vec4 s = textureLod(sSrc, suv, 0.0);
    lum = s.r;
    vec2 e = smoothstep(vec2(0.0), vec2(0.04), sc) * (1.0 - smoothstep(vec2(0.96), vec2(1.0), sc));
    fade = e.x * e.y;
    if (mode > 2.5) fade = e.y;
    else if (mode > 1.5) fade = 1.0 - smoothstep(0.94, 1.0, v);

    float sp = spec(abs(u - 0.5) * 2.0 * (0.55 + 0.9 * v)) * (0.35 + 0.65 * sin(v * 3.1416));
    float osc = uWob.w * sin(u * 31.0 + v * 9.0 + t * 3.0) * sin(u * 3.0 - t);
    float d = lum + sp * uDisp.z + osc;
    d *= 1.0 + 2.5 * (1.0 - a) * (1.0 - a);          // deflection overshoots as the tube warms up

    float across = (v - 0.5) * (0.02 + 0.98 * a);    // the raster opens from a single line
    float along = u - 0.5;
    vec3 p;
    if (mode > 2.5) {
        // drum: rings stacked on a cylinder, deflected outward
        float R = 0.5 * uGeo.y * (0.02 + 0.98 * a) + d * uDisp.y;
        p = vec3(R * cs.x, across * uGeo.y * 1.4 + d * uDisp.x, R * cs.y);
        gLen0 = 3.1416 * uGeo.y;
    } else if (mode > 1.5) {
        // disc: concentric rings, deflected radially and in depth
        float R = rad * 0.62 * uGeo.y * (0.02 + 0.98 * a) + d * uDisp.x;
        p = vec3(R * cs.x, R * cs.y, d * uDisp.y);
        gLen0 = 6.2832 * rad * 0.62 * uGeo.y;
    } else if (mode > 0.5) {
        p = vec3(across * uGeo.x - d * uDisp.x, along * uGeo.y, d * uDisp.y);
        gLen0 = uGeo.y;
    } else {
        p = vec3(along * uGeo.x, across * uGeo.y + d * uDisp.x, d * uDisp.y);
        gLen0 = uGeo.x;
    }
    return p;
}

void main()
{
    vec3 P = TDPos();
    float u = P.x + 0.5;
    float du = 1.0 / uRas.y;
    float lum, lum2, fade, fade2;

    if (uRas.w > 0.5) {
        // solid hold-out surface
        float v = P.y + 0.5;
        vec3 a = rpos(u, v, lum, fade);
        vec4 c = TDWorldToProj(TDDeform(a));
        c.z += 0.004 * c.w;
        vSide = 0.0; vLum = lum; vU = u; vLine = 0.0; vSpeed = 1.0; vFade = fade; vSuv = gSuv;
        gl_Position = c;
        return;
    }

    float line = float(TDInstanceID());
    float v = (line + 0.5) / uRas.x;
    float side = P.y * 2.0;
    vec3 a = rpos(u, v, lum, fade);
    vSuv = gSuv;
    vec3 b = rpos(u + du, v, lum2, fade2);
    vec4 ca = TDWorldToProj(TDDeform(a));
    vec4 cb = TDWorldToProj(TDDeform(b));
    vec2 asp = vec2(1280.0 / 720.0, 1.0);
    vec2 dir = (cb.xy / max(cb.w, 1e-4) - ca.xy / max(ca.w, 1e-4)) * asp;
    float dl = length(dir);
    dir = dl > 1e-7 ? dir / dl : vec2(1.0, 0.0);
    vec2 n = vec2(-dir.y, dir.x);
    float wpx = uRas.z * clamp(uGeo.z / max(ca.w, 0.05), 0.5, 4.0);
    ca.xy += n / asp * side * wpx * (2.0 / 720.0) * ca.w;

    float len0 = gLen0 * du;
    vSpeed = clamp(len0 / max(length(b - a), 1e-6), 0.0, 1.0);   // a fast beam is a dim beam
    vSide = side;
    vLum = lum;
    vU = u;
    vLine = line;
    vFade = fade;
    gl_Position = ca;
}
