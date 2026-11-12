// Describe mode only: a caption along the bottom of the graded picture.
// Input 0: the graded picture. Input 1: the title (1280x40). Input 2: the sentence (1280x44).
// Both are white text on a clear ground; their alpha is the ink.
uniform vec4 uL;   // grade (2 = one-bit: the caption stays pure black and white), 0, 0, 0
out vec4 fragColor;

void main()
{
    vec3 col = texture(sTD2DInputs[0], vUV.st).rgb;
    ivec2 px = ivec2(gl_FragCoord.xy);
    float title = (px.y >= 58 && px.y < 98) ? texelFetch(sTD2DInputs[1], px - ivec2(0, 58), 0).a : 0.0;
    float body = (px.y >= 14 && px.y < 58) ? texelFetch(sTD2DInputs[2], px - ivec2(0, 14), 0).a : 0.0;
    float y = gl_FragCoord.y;
    if (uL.x > 1.5) {
        col = y < 108.0 ? vec3(0.0) : col;
        col = max(col, vec3(step(0.5, max(title, body))));
    } else {
        // a dark band that fades out upward, so the words read over any picture
        col *= 1.0 - 0.86 * (1.0 - smoothstep(96.0, 150.0, y));
        col = mix(col, vec3(0.86, 0.71, 0.24), title);   // ident yellow
        col = mix(col, vec3(0.93, 0.89, 0.80), body);    // ident ivory
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
