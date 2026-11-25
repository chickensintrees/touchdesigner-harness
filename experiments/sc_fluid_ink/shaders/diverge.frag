// Divergence of the stepped velocity, in grid units, minus the blast source.
// out: r pressure guess (last frame's), g divergence
out vec4 fragColor;
void main() {
    vec2 uv = vUV.st;
    vec2 px = uTD2DInfos[0].res.xy;
    vec4 c = texture(sTD2DInputs[0], uv);
    float l = texture(sTD2DInputs[0], uv - vec2(px.x, 0.0)).x;
    float r = texture(sTD2DInputs[0], uv + vec2(px.x, 0.0)).x;
    float b = texture(sTD2DInputs[0], uv - vec2(0.0, px.y)).y;
    float t = texture(sTD2DInputs[0], uv + vec2(0.0, px.y)).y;
    // walls: no flow through the frame edge
    if (uv.x < px.x) l = -c.x;
    if (uv.x > 1.0 - px.x) r = -c.x;
    if (uv.y < px.y) b = -c.y;
    if (uv.y > 1.0 - px.y) t = -c.y;
    float div = 0.5 * (r - l + t - b) - c.a;
    fragColor = TDOutputSwizzle(vec4(c.b, div, 0.0, 1.0));
}
