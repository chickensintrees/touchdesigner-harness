// Subtract the pressure gradient: the field that leaves here is (nearly) divergence-free.
// in0: stepped velocity (rg), in1: solved pressure (r)
// out: rg velocity, b pressure, a shot id (vstep compares it to know when a new shot began)
uniform vec4 uTime;   // evolve, shot age, shot id, boot
out vec4 fragColor;
void main() {
    vec2 uv = vUV.st;
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 v = texture(sTD2DInputs[0], uv).xy;
    float p = texture(sTD2DInputs[1], uv).r;
    float l = texture(sTD2DInputs[1], uv - vec2(px.x, 0.0)).r;
    float r = texture(sTD2DInputs[1], uv + vec2(px.x, 0.0)).r;
    float b = texture(sTD2DInputs[1], uv - vec2(0.0, px.y)).r;
    float t = texture(sTD2DInputs[1], uv + vec2(0.0, px.y)).r;
    v -= 0.5 * vec2(r - l, t - b);
    if (uv.x < px.x || uv.x > 1.0 - px.x) v.x = 0.0;
    if (uv.y < px.y || uv.y > 1.0 - px.y) v.y = 0.0;
    // keep the pressure mean from drifting when a blast source is active
    fragColor = TDOutputSwizzle(vec4(v, p * 0.98, uTime.z));
}
