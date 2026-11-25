// The Input picture printed on a sheet of paper: the whole 16:9 frame, inset with a paper
// margin, its colours multiplied into the stock like ink. The output texture is stretched over
// the sheet (1.29 times wider than tall), so the inset is worked out in sheet units.
// With uDuo.w = 1 it is the reverse side instead: the picture as a two-colour print in the
// take's reverse colour (uDuo.rgb), full width, on a card of that colour.
// Input 0: the Input picture (any size).
uniform vec3 uPaper;
uniform vec4 uDuo;
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    const float SHEET = 1.2917;              // sheet width / height
    float W = uDuo.w > 0.5 ? 1.0 : 0.90;     // picture width as a fraction of the sheet's width
    float H = W / 1.7778 * SHEET;            // its height as a fraction of the sheet's height
    vec2 p = (uv - 0.5) / vec2(W, H) + 0.5;
    vec3 pic = clamp(texture(sTD2DInputs[0], clamp(p, 0.0, 1.0)).rgb, 0.0, 1.0);
    // soft edge so the print does not alias when the sheet is small
    vec2 e = smoothstep(vec2(0.0), vec2(0.006), p) * (1.0 - smoothstep(vec2(0.994), vec2(1.0), p));
    float inside = e.x * e.y;
    vec3 col;
    if (uDuo.w > 0.5) {
        float l = dot(pic, vec3(0.3, 0.59, 0.11));
        vec3 duo = mix(uDuo.rgb * 0.34, uDuo.rgb, smoothstep(0.0, 0.42, l));
        duo = mix(duo, vec3(0.96, 0.90, 0.78), smoothstep(0.5, 0.95, l));    // highlights go to the lettering cream
        col = mix(uDuo.rgb, duo, inside);
    } else {
        col = mix(uPaper, uPaper * (pic * 0.94 + 0.05), inside);             // ink is never quite black
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
