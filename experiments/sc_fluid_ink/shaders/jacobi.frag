// One Jacobi iteration of the pressure Poisson equation. Run with npasses = 20 or so:
// each pass reads the previous pass as input 0. r pressure, g divergence (carried through).
out vec4 fragColor;
void main() {
    vec2 uv = vUV.st;
    vec2 px = uTD2DInfos[0].res.xy;
    float div = texture(sTD2DInputs[0], uv).g;
    float l = texture(sTD2DInputs[0], uv - vec2(px.x, 0.0)).r;
    float r = texture(sTD2DInputs[0], uv + vec2(px.x, 0.0)).r;
    float b = texture(sTD2DInputs[0], uv - vec2(0.0, px.y)).r;
    float t = texture(sTD2DInputs[0], uv + vec2(0.0, px.y)).r;
    fragColor = TDOutputSwizzle(vec4((l + r + b + t - div) * 0.25, div, 0.0, 1.0));
}
