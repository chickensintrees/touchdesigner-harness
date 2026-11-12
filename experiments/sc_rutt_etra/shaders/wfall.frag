// Spectrum waterfall: a history of the live spectrum as a picture the scan processor can scan.
// Row 0 is now; every cook the older rows step up by exactly one row (whole rows: a fractional
// slide averages neighbouring rows every frame and flattens the history within a second; stepping
// on alternate frames by absTime.frame parity stalls when TouchDesigner drops every other frame).
// Input 0: the hub's full spectrum (log frequency). Input 1: last frame of this pass.
uniform vec4 uW;   // x 1 = clear the history (the scene was not cooking), y unused, z gain
out vec4 fragColor;

float sp(float x)
{
    float s = 0.0;
    for (int i = 0; i < 4; i++)
        s = max(s, texture(sTD2DInputs[0], vec2(0.21 + 0.6 * x + float(i) * 0.0007, 0.5)).r);
    return pow(clamp(s * 5.0, 0.0, 4.0), 0.6);
}

void main()
{
    vec2 uv = vUV.st;
    float rows = uTDOutputInfo.res.w;
    float v;
    if (uv.y * rows < 1.0) {
        float x = abs(uv.x - 0.5) * 2.0;                 // low notes in the middle, mirrored
        v = sp(x) * (1.0 - smoothstep(0.7, 1.0, x)) * uW.z;
        v = mix(texture(sTD2DInputs[1], uv).r, v, 0.6);   // a little lag: the meter needle, not the raw FFT
    } else {
        v = texture(sTD2DInputs[1], uv - vec2(0.0, 1.0 / rows)).r * (1.0 - uW.x) * 0.993;   // far ridges settle
    }
    if (isnan(v) || isinf(v)) v = 0.0;
    fragColor = TDOutputSwizzle(vec4(v, v, v, 1.0));
}
