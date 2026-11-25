// im_depth_relief: every photograph is a sheet of points pushed out by its depth
// map. Each point knows its place in the picture that is leaving and in the one
// that is arriving, and streams from one to the other on a curling wind.
uniform sampler2D sA;   // slot 0 picture
uniform sampler2D sB;   // slot 1 picture
uniform sampler2D sDA;  // slot 0 depth (white = near)
uniform sampler2D sDB;  // slot 1 depth
uniform vec4 uMorph;    // x 0 = slot 0 is up, 1 = slot 1; y seconds; z relief depth; w wander
uniform vec4 uShape;    // x aspect of slot 0, y aspect of slot 1, z point size multiplier, w focal length in pixels
uniform vec4 uGrid;     // x columns, y rows, z dust amount, w colour boost in flight
uniform vec4 uMusic;    // x kick 0..1, y bass 0..1, z snare 0..1, w hi-hat 0..1
uniform vec4 uLook;     // x 0 natural, 1 depth contours in two inks, 2 one row in three (scan lines); y kicks blow the points apart 0..1; z beat position; w depth curve (a power: below 1 spreads the far distance)

out vec4 vCol;

const float PI = 3.14159265;

vec3 hash3(float n) {
    vec3 p3 = fract(vec3(n) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xxy + p3.yzz) * p3.zyx);
}

// Divergence-free by construction: each component depends only on the other two axes.
vec3 flow(vec3 p, float t) {
    vec3 v = vec3(
        sin(p.y * 2.1 + t) + cos(p.z * 1.7 - t * 0.7),
        sin(p.z * 2.3 - t * 0.8) + cos(p.x * 1.9 + t * 0.6),
        sin(p.x * 2.0 + t * 0.9) + cos(p.y * 2.2 - t));
    vec3 q = p * 2.7 + v * 0.6;
    v += 0.5 * vec3(
        sin(q.y * 2.1 - t) + cos(q.z * 1.7 + t),
        sin(q.z * 2.3 + t) + cos(q.x * 1.9 - t),
        sin(q.x * 2.0 - t) + cos(q.y * 2.2 + t));
    return v;
}

// A picture of any shape, 1 unit tall, shrunk if it is too wide for the frame.
vec3 sheet(vec2 uv, float asp, float depth) {
    float fit = min(1.0, 1.72 / asp);
    // the relief breathes with the bass, and a kick throws the nearest parts at the lens
    float z = (depth - 0.45) * uMorph.z * (1.0 + 0.9 * uMusic.y) + 0.22 * uMusic.x * depth * depth;
    return vec3((uv.x - 0.5) * asp * fit, (uv.y - 0.5) * fit, z);
}

void main() {
    vec3 g = TDPos();
    vec2 uv = clamp(g.xy + 0.5, 0.0, 1.0);
    float id = floor(uv.x * (uGrid.x - 1.0) + 0.5) + floor(uv.y * (uGrid.y - 1.0) + 0.5) * uGrid.x;
    vec3 rnd = hash3(id + 1.0);

    vec3 cA = textureLod(sA, uv, 0.0).rgb;
    vec3 cB = textureLod(sB, uv, 0.0).rgb;
    // a depth map often gives one near object most of its range: the curve hands some back to the distance
    float curve = uLook.w > 0.0 ? uLook.w : 1.0;
    float dA = pow(textureLod(sDA, uv, 0.0).r, curve);
    float dB = pow(textureLod(sDB, uv, 0.0).r, curve);
    vec3 pA = sheet(uv, uShape.x, dA);
    vec3 pB = sheet(uv, uShape.y, dB);

    // Departure sweeps across the picture left to right (or right to left on the
    // way back), blurred by a delay of each point's own. Near points leave first.
    float m = uMorph.x;
    float sweep = mix(uv.x, 1.0 - uv.x, step(0.5, m) * 0.0);
    float delay = clamp(0.5 * sweep + 0.3 * rnd.y + 0.2 * (1.0 - dA), 0.0, 1.0);
    float s = clamp((m - delay * 0.7) / 0.3, 0.0, 1.0);
    s = s * s * s * (s * (s * 6.0 - 15.0) + 10.0);
    float mid = sin(PI * s);

    float t = uMorph.y * 0.35;
    vec3 pos = mix(pA, pB, s);
    // In flight the stream bows toward the camera and rides the wind.
    pos.z += mid * (0.2 + 0.35 * rnd.z);
    pos.y += mid * (rnd.x - 0.4) * 0.12;
    vec3 wind = flow(pos * 1.3 + rnd * 0.2, t);
    pos += wind * (0.004 + 0.07 * mid * mid + 0.035 * uMusic.z) * uMorph.w;   // a snare is a gust
    pos += (rnd - 0.5) * uLook.y * uMusic.x * 0.7 * (0.3 + rnd.z);              // some takes burst on every kick
    // One point in twenty-five never quite lands: dust in front of the picture.
    float dust = step(1.0 - uGrid.z * 0.04, rnd.x);
    pos += dust * (vec3(0.0, 0.0, 0.05 + 0.3 * rnd.y * rnd.y) + wind * 0.03 * uMorph.w);

    vec3 col = mix(cA, cB, s);
    float lum = dot(col, vec3(0.2126, 0.7152, 0.0722));
    col = max(mix(vec3(lum), col, 1.0 + uGrid.w * mid), 0.0);   // in flight the colours run richer
    col *= 1.0 + 0.5 * mid;
    col = mix(col, col * (1.3 + 2.0 * uMusic.w) + 0.08, dust);   // dust catches the light, and glints on hi-hats
    float depth = mix(dA, dB, s);
    if (uLook.x > 0.5 && uLook.x < 1.5) {
        // contours: bands of equal depth in two inks, walking toward the lens a band per two beats
        float band = step(0.5, fract(depth * 7.0 - uLook.z * 0.5));
        col = (0.25 + 1.2 * lum) * mix(vec3(0.95, 0.22, 0.16), vec3(0.16, 0.85, 0.95), band);
    }
    col *= 1.0 + 0.25 * uMusic.x;

    vec4 world = TDDeform(pos);
    gl_Position = TDWorldToProj(world);
    float w = max(gl_Position.w, 0.05);
    // a point is as wide as the gap to its neighbour, so a settled picture is solid
    float spacing = 1.0 / (uGrid.y - 1.0);
    float px = spacing * uShape.w / w * uShape.z * (1.0 - 0.45 * mid) * (1.0 - 0.4 * dust);
    if (uLook.x > 1.5) {
        // scan lines: only every third row is drawn, with fatter points
        float row = floor(uv.y * (uGrid.y - 1.0) + 0.5);
        if (mod(row, 3.0) > 0.5) gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
        px *= 1.7;
    }
    gl_PointSize = clamp(px * (1.0 + 0.3 * uMusic.x), 1.0, 14.0);
    vCol = vec4(col, 1.0);
}
