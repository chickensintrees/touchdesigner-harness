uniform vec4 uCol;     // rgb, w gain
uniform vec4 uFx;      // x fog density, y beat_pos
in vec2 vRC;
in float vSpark;       // 1 where a sung note was detected, decaying after
in float vVox;         // vocal stem loudness when the row was written
out vec4 fragColor;

void main()
{
    TDCheckDiscard();
    // a solid band with a hot core: the note itself (the strip is now a ribbon, not a curtain)
    float cx = (vRC.x - 0.35) * 3.4;
    float top = exp(-cx * cx) * 0.55 + exp(-cx * cx * 30.0);
    float veil = pow(1.0 - vRC.x, 2.2) * 0.30;        // the curtain hanging below it
    veil *= 0.55 + 0.45 * sin(vRC.y * 420.0 + uFx.y * 6.2832);
    // no curtain right in front of the lens: close up it reads as a sheet of glass
    veil *= smoothstep(0.03, 0.22, vRC.y) * 0.3;
    float head = exp(-vRC.y * 22.0);                   // the comet head at the newest end
    float fog = exp(-vRC.y * uFx.x);
    float vox = min(vVox, 1.3);
    // an ember line when nobody sings, a curtain when the stem is loud, white heat on a note
    float level = 0.10 + 1.1 * vox * vox + 0.6 * vox;
    // the veil only hangs while the stem is audible; the top line stays as an ember
    vec3 col = uCol.rgb * (veil * (level - 0.10) + top * (0.35 + 1.3 * level));
    col += vec3(1.0, 0.95, 0.85) * top * (2.6 * vSpark + 1.6 * head * (0.2 + vox));
    col += vec3(1.0, 0.95, 0.85) * veil * vSpark * 0.9;
    col *= fog * uCol.w;
    if (any(isnan(col)) || any(isinf(col))) col = vec3(0.0);
    fragColor = TDOutputSwizzle(vec4(col, 0.0));
}
