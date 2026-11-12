// typepack.frag: three Text TOPs into one texture (r = big type, g = slug, b = rows).
uniform vec4 uScroll;   // rows scroll x, y; big type scroll x, y (uv)
out vec4 fragColor;
void main() {
    vec2 uv = vUV.st;
    float big = texture(sTD2DInputs[0], uv - uScroll.zw).r;
    float slug = texture(sTD2DInputs[1], uv).r;
    float rows = texture(sTD2DInputs[2], fract(uv - uScroll.xy)).r;
    fragColor = TDOutputSwizzle(vec4(big, slug, rows, 1.0));
}
