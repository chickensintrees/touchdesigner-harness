// Three ways to draw the same history (uLook.x):
// 0 ridge lines on a black surface that writes depth (hidden-line drawing),
// 1 solid lit mountains in fog, 2 contour map in ink on paper.
uniform sampler2D sWF;
uniform vec4 uDim;     // x width, y depth, z height scale, w ridge lines
uniform vec4 uCol;     // line / light / ink colour rgb, w = overall gain
uniform vec4 uCol2;    // accent colour rgb (hits), w = pulse
uniform vec4 uFx;      // x fog density over depth, y energy, z beat_pos, w hit_high
uniform vec4 uLook;    // x look, y contours per unit height, z body (see terrain.vert), w arrival sweep position
uniform vec4 uBg;      // rgb fog or paper colour, w fog density over distance (solid look)
uniform vec4 uSun;     // xyz light direction
uniform vec4 uCamP;    // camera position
uniform sampler2D sIn; // Input picture (the scene's Input parameter); black when blank
uniform vec4 uIn;      // x 1 = a picture is given, w its gain
in vec3 vWP;
in vec2 vTC;
in vec2 vSC;
in float vFlat;
in float vH;
in vec3 vN;
in vec2 vPC;
out vec4 fragColor;

void main()
{
    TDCheckDiscard();
    vec4 wf = texture(sWF, vSC);
    float h = wf.r * vFlat;
    float flash = wf.a;
    int look = int(uLook.x + 0.5);
    int shp = int(uLook.z + 0.5);
    float lv = vTC.y * uDim.w;
    float w = fwidth(lv);
    float d = abs(fract(lv) - 0.5);
    float line = 1.0 - smoothstep(w * 0.9, w * 2.1, d);
    // where the lines get denser than pixels, fall back to their average
    line = mix(line, 0.24, smoothstep(0.35, 0.8, w));
    // the arrival: one bright row races from the live edge to the far end in the first half second
    float sd = (vTC.y - uLook.w) * 14.0;
    float sweep = exp(-sd * sd) * step(uLook.w, 1.25);
    bool pin = uIn.x > 0.5;
    vec3 pic = pin ? texture(sIn, vPC).rgb : vec3(0.0);
    float pl = smoothstep(0.12, 0.85, dot(pic, vec3(0.30, 0.59, 0.11)));   // the same contrast curve as the relief
    vec3 col;
    if (look == 1) {
        vec3 n = normalize(vN);
        vec3 L = normalize(uSun.xyz);
        float dif = max(dot(n, L), 0.0);
        float hh = clamp(vH / 1.1, 0.0, 1.0);
        // dark violet rock; only the loudest peaks carry pale caps
        vec3 alb = mix(vec3(0.07, 0.05, 0.13), vec3(0.30, 0.17, 0.22), smoothstep(0.1, 0.8, hh));
        alb = mix(alb, vec3(0.95, 0.84, 0.74), smoothstep(0.80, 1.05, hh) * 0.8);
        if (pin) alb = mix(alb, pic * uIn.w * 0.6, 0.85);      // Input: the picture is the rock's colour
        col = alb * (uBg.rgb * 0.35 + uCol.rgb * dif * 2.4) * uCol.w * 0.6;
        // light grazing the slopes that face the sun
        col += uCol.rgb * pow(dif, 3.0) * 0.35;
        // the rows are still there: thin warm strata, and kick rows glow as they roll away
        col += uCol2.rgb * line * (0.10 + 0.35 * hh);
        col += uCol2.rgb * flash * (0.25 + 1.2 * line) * (0.3 + hh);
        col += uCol2.rgb * sweep * 1.5;
        float dist = length(vWP - uCamP.xyz);
        float f = 1.0 - exp(-dist * uBg.w);
        // mist pools in the low ground
        f = clamp(f + 0.12 * exp(-max(vWP.y, 0.0) * 1.6) * smoothstep(4.0, 22.0, dist), 0.0, 1.0);
        col = mix(col, uBg.rgb, f);
    } else if (look == 2) {
        float c = vH * uDim.z * uLook.y;
        float cw = max(fwidth(c), 1e-4);
        float l1 = 1.0 - smoothstep(cw * 0.6, cw * 1.6, abs(fract(c) - 0.5));
        l1 *= 1.0 - smoothstep(0.45, 0.9, cw);
        float c5 = c / 5.0;
        float cw5 = max(fwidth(c5), 1e-4);
        float l5 = 1.0 - smoothstep(cw5 * 1.6, cw5 * 2.8, abs(fract(c5) - 0.5));
        float band = clamp(floor(c) / (uDim.z * 1.2 * uLook.y), 0.0, 1.0);
        vec3 n = normalize(vN);
        float shade = 0.90 + 0.16 * dot(n, normalize(uSun.xyz));
        vec3 paper = uBg.rgb;
        vec3 tint = mix(paper, uCol2.rgb, band * 0.75);
        if (pin) tint = paper * mix(vec3(1.0), pic, 0.45) * (1.0 - 0.30 * band);   // Input: printed as a wash under the ink
        col = tint * shade;
        // graticule: a faint survey grid, time one way and frequency the other
        float gu = vTC.x * 16.0, gv = vTC.y * 24.0;
        float gl = max(1.0 - smoothstep(0.0, fwidth(gu) * 1.3, abs(fract(gu) - 0.5)),
                       1.0 - smoothstep(0.0, fwidth(gv) * 1.3, abs(fract(gv) - 0.5)));
        col = mix(col, uCol.rgb, gl * 0.16);
        col = mix(col, uCol.rgb, max(l1 * 0.62, l5 * 0.95));
        // kick rows are stamped across the sheet in red hatch
        float hatch = step(0.5, fract((vWP.x + vWP.z) * 2.2));
        col = mix(col, vec3(0.66, 0.20, 0.17), clamp(flash * 0.85, 0.0, 1.0) * (0.35 + 0.65 * hatch) * 0.8);
        col = mix(col, vec3(0.66, 0.20, 0.17), sweep * 0.9);
    } else {
        // faint long lines along the flight direction, only on the high ground
        float lu = vTC.x * 64.0;
        float wu = fwidth(lu);
        float lineU = (1.0 - smoothstep(wu * 0.6, wu * 1.6, abs(fract(lu) - 0.5))) * (1.0 - smoothstep(0.3, 0.7, wu));
        float fog = exp(-vTC.y * uFx.x);
        float lift = 0.30 + 1.5 * h * h + 0.6 * h;
        // Input: every line takes the colour and brightness of the picture under it (lc), with a
        // little of the take's own colour left so the dark parts are still a drawing
        vec3 lc = uCol.rgb;
        if (pin) {
            lc = uCol.rgb * 0.10 + pic * uIn.w * (0.30 + 0.90 * pl);
            lift = 0.40 + 0.9 * pl + 0.4 * h;
        }
        col = lc * line * lift;
        col += uCol2.rgb * line * flash * (0.4 + 0.9 * h);
        col += lc * lineU * 0.10 * smoothstep(0.25, 0.9, h);
        // the live edge: the first rows burn hotter
        float edge = exp(-vTC.y * 90.0);
        col += mix(lc, vec3(1.0), 0.45) * line * edge * (0.6 + 1.2 * h);
        // peaks glow a little between the lines
        col += lc * 0.02 * h * h * h;
        if (pin) col += pic * 0.10;                          // a faint body between the lines
        col += mix(uCol2.rgb, vec3(1.0), 0.5) * sweep * (0.25 + 1.6 * line);
        // side fade so the open bodies have no hard left/right border
        float side = 1.0;
        if (shp == 0 || shp == 4) side = smoothstep(0.0, 0.04, vTC.x) * (1.0 - smoothstep(0.96, 1.0, vTC.x));
        col *= fog * side * uCol.w;
    }
    if (any(isnan(col)) || any(isinf(col))) col = vec3(0.0);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
