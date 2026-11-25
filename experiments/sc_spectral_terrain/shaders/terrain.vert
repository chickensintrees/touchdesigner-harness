// Grid in x,z in [-0.5, 0.5]; z = +0.5 is the front (newest) edge.
// One history texture, five bodies (uShape.x): 0 plane, 1 tunnel, 2 planet, 3 disc, 4 flat stack.
uniform sampler2D sWF;
uniform vec4 uDim;     // x width, y depth, z height scale, w ridge lines
uniform vec4 uMono0;   // x, z, half width of the word footprint, w valley floor height factor
uniform vec4 uShape;   // x body, y radius / size, z twist, w spin angle
uniform vec4 uMap;     // x 1 = ridge (bass in the middle), y arrival 0..1 with overshoot, z height spring
uniform sampler2D sInH; // Input picture, softened (the scene's Input parameter); black when blank
uniform vec4 uIn;      // x 1 = a picture is given, y relief from its brightness, z spectrum relief kept in its dark parts, w gain
uniform vec4 uInM;     // picture u = dot(xy, grid uv) + uInO.x, v = dot(zw, grid uv) + uInO.y
uniform vec4 uInO;     // xy offset, z spectrum relief kept in the picture's bright parts, w 1 = planar on the disc
out vec3 vWP;
out vec2 vTC;
out vec2 vSC;          // where this vertex samples the history
out float vFlat;
out float vH;
out vec3 vN;
out vec2 vPC;          // where this vertex samples the Input picture

vec2 picUV(vec2 tc)
{
    if (uInO.w > 0.5) {
        // the disc: the picture lies flat in world x,z (the same angle and radius as main() below)
        float ang = tc.x * 6.2831853 + uShape.w + uShape.z * tc.y;
        float rad = uMono0.z + tc.y * uShape.y * uMap.y;
        return vec2(rad * cos(ang) * uInM.x, rad * sin(ang) * uInM.w) + uInO.xy;
    }
    return vec2(dot(uInM.xy, tc), dot(uInM.zw, tc)) + uInO.xy;
}

float foot(vec2 p, vec4 m)
{
    vec2 d = max(abs(p - m.xy) - vec2(m.z, 0.25), 0.0);
    return length(d);
}

vec2 mapTC(vec2 tc)
{
    if (uMap.x > 0.5) tc.x = abs(tc.x - 0.5);     // fold: bass (texture edge) lands in the middle
    return tc;
}

float hgt(vec2 tc, out float flat_)
{
    vec2 sc = mapTC(tc);
    vec4 wfs = texture(sWF, sc);
    float h = wfs.r;
    float kick = wfs.a;
    float d = 10.0;
    if (uShape.x < 0.5) {
        vec2 xz = vec2((tc.x - 0.5) * uDim.x, -tc.y * uDim.y);
        d = foot(xz, uMono0);
    }
    float open = smoothstep(0.15, 1.6, d);
    // a low berm pushed up around the footprint so the ground reads as flowing round it
    float bd = (d - 0.9) / 0.45;      // pow(negative, 2.0) is NaN in GLSL: square by hand
    float berm = exp(-bd * bd) * 0.22;
    // profile: the treble is kept low (factor uMono0.w) so the camera has a corridor
    float a = abs(sc.x - 0.5) * 2.0;
    float env = mix(uMono0.w, 1.0, pow(a, 1.4));
    flat_ = open * env;
    // a kick is a physical swell on the rows written during it
    if (uIn.x > 0.5) {
        // Input: the picture's brightness is relief (a scan processor), and it gates the spectrum:
        // bright parts carry the full moving terrain, dark parts lie nearly flat
        float l = dot(texture(sInH, picUV(tc)).rgb, vec3(0.30, 0.59, 0.11));
        l = smoothstep(0.12, 0.85, l);     // a little contrast, so a mid-grey background lies flat
        float g = mix(uIn.z, uInO.z, l);
        return (h * flat_ * g * (1.0 + 0.5 * kick) + berm + (kick * 0.15 + l * uIn.y) * open) * uMap.z;
    }
    return (h * flat_ * (1.0 + 0.5 * kick) + berm + kick * 0.15 * open) * uMap.z;
}

void main()
{
    vec3 p = TDPos();
    vec2 tc = vec2(p.x + 0.5, 0.5 - p.z);
    float fl;
    float h = hgt(tc, fl);
    float A = uDim.z;
    float arr = uMap.y;
    int shp = int(uShape.x + 0.5);
    vec3 pos;
    vec3 n = vec3(0.0, 1.0, 0.0);
    if (shp == 1) {
        // tunnel: frequency round the wall (bass on the floor), time down the bore
        float R = uShape.y * (1.0 + 1.6 * (1.0 - min(arr, 1.0)));
        float ang = tc.x * 6.2831853 - 1.5707963 + uShape.z * tc.y + uShape.w;
        float r = max(R - h * A, 0.3);
        pos = vec3(r * cos(ang), r * sin(ang), -tc.y * uDim.y);
    } else if (shp == 2) {
        // planet: frequency is longitude, time runs from the north pole to the south
        float lat = 1.5707963 - (0.015 + 0.97 * tc.y) * 3.14159265;
        float lon = tc.x * 6.2831853 + uShape.w;
        float r = (uShape.y + h * A) * arr;
        pos = r * vec3(cos(lat) * cos(lon), sin(lat), cos(lat) * sin(lon));
    } else if (shp == 3) {
        // disc: frequency is the angle, now is the inner rim, the past spreads outward
        float ang = tc.x * 6.2831853 + uShape.w + uShape.z * tc.y;
        float rad = uMono0.z + tc.y * uShape.y * arr;
        float ramp = smoothstep(0.0, 0.22, tc.y);
        pos = vec3(rad * cos(ang), h * A * ramp, rad * sin(ang));
    } else if (shp == 4) {
        // flat stack: every row is a trace on a chart, nearer rows hide the ones above
        pos = vec3((tc.x - 0.5) * uDim.x, (tc.y - 0.5) * uShape.y * arr + h * A, -tc.y * 3.0);
    } else {
        pos = vec3((tc.x - 0.5) * uDim.x, h * A, -tc.y * uDim.y);
        float e = 1.0 / 256.0;
        float f2;
        float hx = hgt(tc + vec2(e, 0.0), f2) - hgt(tc - vec2(e, 0.0), f2);
        float hz = hgt(tc + vec2(0.0, e), f2) - hgt(tc - vec2(0.0, e), f2);
        n = normalize(vec3(-hx * A / (2.0 * e * uDim.x), 1.0, hz * A / (2.0 * e * uDim.y)));
    }
    vec4 wp = TDDeform(pos);
    vWP = wp.xyz;
    vTC = tc;
    vSC = mapTC(tc);
    vFlat = fl * uMap.z;
    vH = h;
    vN = n;
    vPC = picUV(tc);
    gl_Position = TDWorldToProj(wp);
}
