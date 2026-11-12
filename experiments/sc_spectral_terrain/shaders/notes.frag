// Note history, 2 x rows, scrolling in step with the waterfall (row 0 newest).
// Column 0, the voice: R held pitch 0..1 (glides to each new note), G spark (1 when a
//   note is detected, decaying), B ribbon x (-1..1), A vocal stem loudness.
// Column 1, the bass: R held hue 0..1 (pitch class), G flare (1 on a note, decaying),
//   B bass stem loudness.
uniform vec4 uLive;   // x pitch 0..1 (0 = none this frame), y ribbon x, z vocals
uniform vec4 uBass;   // x hue 0..1, y 1 when a bass note is detected, z bass loudness
out vec4 fragColor;

void main()
{
    ivec2 px = ivec2(gl_FragCoord.xy);
    vec4 c;
    if (px.y == 0) {
        vec4 prev = texelFetch(sTD2DInputs[0], ivec2(px.x, 0), 0);
        if (px.x == 0) {
            float on = step(0.0005, uLive.x);
            float hgt = mix(prev.r, uLive.x, on * 0.4);
            float spark = max(on, prev.g * 0.90);
            c = vec4(hgt, spark, uLive.y, uLive.z);
        } else {
            float on = uBass.y;
            float hue = mix(prev.r, uBass.x, on * 0.5);
            float flare = max(on, prev.g * 0.955);
            c = vec4(hue, flare, uBass.z, 0.0);
        }
    } else {
        c = texelFetch(sTD2DInputs[0], px - ivec2(0, 1), 0);
    }
    fragColor = c;
}
