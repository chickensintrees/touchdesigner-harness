// Describe mode caption for the takes that have no text of their own: a dark strip along the
// bottom with the technique's name and two lines saying what this take does. Runs after post
// and is never fed back, so the loop does not see it.
// input 0: the graded picture   input 1: body text (alpha)   input 2: title text (alpha)
uniform vec4 uC;    // strip height (fraction of the frame), 1-bit take, -, -
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec3 c = texture(sTD2DInputs[0], uv).rgb;
    float body = texture(sTD2DInputs[1], uv).a;
    float title = texture(sTD2DInputs[2], uv).a;
    float strip = 1.0 - smoothstep(uC.x - 0.004, uC.x, uv.y);
    bool bit = uC.y > 0.5;
    c = mix(c, vec3(0.02, 0.02, 0.03), strip * (bit ? 1.0 : 0.93));
    vec3 paper = vec3(0.93, 0.89, 0.78);
    vec3 amber = bit ? vec3(0.96, 0.95, 0.90) : vec3(0.86, 0.62, 0.24);
    if (bit) paper = vec3(0.96, 0.95, 0.90);
    c = mix(c, paper, body);
    c = mix(c, amber, title);
    // a hairline on top of the strip
    float line = step(abs(uv.y - uC.x), 0.0015);
    c = mix(c, amber, line * 0.8);
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
