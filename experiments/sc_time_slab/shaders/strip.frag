// Strip photograph (peripheral camera). The canvas scrolls sideways a few pixels a
// frame and the new columns are filled from one fixed vertical slit of the plate, so
// x is time: a prop turning on the slit is unrolled into a frieze, and anything that
// flashes becomes a vertical bar. Unlike the slab this keeps several seconds.
// Alpha is 1 where the strip has been exposed and 0 where it has not: build.py lays
// it over the live plate, so after a cut the strip wipes across the ordinary picture.
// Input 0: the plate (now). Input 1: this TOP's previous frame (Feedback TOP).
uniform vec4 uP;   // pixels scrolled per frame, direction (1: new columns enter on the left), slit x, slit width (uv)
out vec4 fragColor;

void main()
{
    vec2 uv = vUV.st;
    float W = uTD2DInfos[1].res.z;
    float S = max(1.0, floor(uP.x + 0.5));
    float dir = uP.y > 0.0 ? 1.0 : -1.0;
    float xe = dir > 0.0 ? gl_FragCoord.x : W - gl_FragCoord.x;   // pixels from the entering edge
    vec4 col = vec4(0.0, 0.0, 0.0, 1.0);
    if (xe < S) {
        float u = uP.z + (xe / S - 0.5) * uP.w;
        // R and B look through slits a little either side: edges of what turns split into colour
        col.r = texture(sTD2DInputs[0], vec2(u - 0.010, uv.y)).r;
        col.g = texture(sTD2DInputs[0], vec2(u, uv.y)).g;
        col.b = texture(sTD2DInputs[0], vec2(u + 0.010, uv.y)).b;
    } else {
        // whole-pixel shift with texelFetch: the strip never blurs however long it travels
        col = texelFetch(sTD2DInputs[1], ivec2(gl_FragCoord.xy) - ivec2(int(dir * S), 0), 0);
    }
    fragColor = TDOutputSwizzle(col);
}
