// Frame-to-frame motion of the source: windowed Lucas-Kanade over RGB.
// (The Optical Flow TOP reports "not supported" on this GPU; see NOTES.md.)
// Inputs: 0 current small blurred source, 1 the previous frame of the same.
// Output: xy = motion in UV units per frame (where the picture moved to), z = confidence.
uniform vec4 uF;   // x max length in UV units, y regulariser, z unused, w unused
out vec4 fragColor;

void main()
{
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st;
    float sxx = 0.0, sxy = 0.0, syy = 0.0;
    vec2 sb = vec2(0.0);
    for (int j = -2; j <= 2; j++) {
        for (int i = -2; i <= 2; i++) {
            vec2 u = uv + vec2(i, j) * px * 1.5;
            vec3 c  = texture(sTD2DInputs[0], u).rgb;
            vec3 p  = texture(sTD2DInputs[1], u).rgb;
            vec3 cx = texture(sTD2DInputs[0], u + vec2(px.x, 0.0)).rgb + texture(sTD2DInputs[1], u + vec2(px.x, 0.0)).rgb
                    - texture(sTD2DInputs[0], u - vec2(px.x, 0.0)).rgb - texture(sTD2DInputs[1], u - vec2(px.x, 0.0)).rgb;
            vec3 cy = texture(sTD2DInputs[0], u + vec2(0.0, px.y)).rgb + texture(sTD2DInputs[1], u + vec2(0.0, px.y)).rgb
                    - texture(sTD2DInputs[0], u - vec2(0.0, px.y)).rgb - texture(sTD2DInputs[1], u - vec2(0.0, px.y)).rgb;
            vec3 gx = cx * 0.25, gy = cy * 0.25, gt = c - p;
            sxx += dot(gx, gx); sxy += dot(gx, gy); syy += dot(gy, gy);
            sb  -= vec2(dot(gx, gt), dot(gy, gt));
        }
    }
    float reg = uF.y;
    sxx += reg; syy += reg;
    float det = sxx * syy - sxy * sxy;
    vec2 f = vec2(syy * sb.x - sxy * sb.y, sxx * sb.y - sxy * sb.x) / max(det, 1e-9);   // in texels
    f *= px;                                                                           // to UV units
    float len = length(f);
    if (len > uF.x) f *= uF.x / len;
    float conf = clamp((sxx + syy - 2.0 * reg) * 4.0, 0.0, 1.0);
    fragColor = TDOutputSwizzle(vec4(f, conf, 1.0));
}
