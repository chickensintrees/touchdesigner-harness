// sw_images: shows the pictures of a prepared set one after another, as a plain
// 1280x720 picture that any scene can take as its Input.
// Inputs: 0 and 1 are the two picture slots, which take turns.
uniform vec4 uMix;    // x 0 = slot 0 up, 1 = slot 1 up; y change (0 dissolve, 1 cut, 2 static); z push amount; w phase 0..1 through this picture
uniform vec4 uShape;  // x aspect of slot 0, y aspect of slot 1, z 1 = fill the frame, 0 = show the whole picture; w seconds
uniform vec4 uGround; // rgb colour behind a picture that does not fill the frame
uniform vec4 uColour; // x which picture slot 0 holds, y which picture slot 1 holds, z how much of the colour treatment (0 = none)
out vec4 fragColor;

float hash2(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 place(float asp, vec2 uv, float zoom) {
    float oa = uTDOutputInfo.res.z / uTDOutputInfo.res.w;
    vec2 p = (uv - 0.5) / zoom;
    vec2 whole = asp > oa ? vec2(1.0, asp / oa) : vec2(oa / asp, 1.0);
    vec2 fill = asp > oa ? vec2(oa / asp, 1.0) : vec2(1.0, asp / oa);
    return p * mix(whole, fill, uShape.z) + 0.5;
}

vec3 hue(float h) { return clamp(abs(fract(h + vec3(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0, 0.0, 1.0); }

// Each picture gets its own colour treatment, chosen by its place in the set, so
// a run of similar photographs still changes colour from one to the next:
// as it is, two inks, hues turned a third round, a three-ink poster, a tinted negative.
vec3 treat(vec3 c, float idx) {
    if (uColour.z <= 0.0) return c;
    float kind = mod(idx, 5.0);
    float h = fract(idx * 0.381966 + 0.08);
    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    vec3 t = c;
    if (kind > 0.5 && kind < 1.5) {
        t = mix(hue(h) * 0.22, mix(hue(h + 0.45), vec3(1.0), 0.55), smoothstep(0.04, 0.9, l));
    } else if (kind < 2.5 && kind > 1.5) {
        t = mix(c.gbr, c.brg, step(0.5, fract(idx * 0.5 + 0.25)));
    } else if (kind < 3.5 && kind > 2.5) {
        vec3 dark = hue(h + 0.6) * 0.18, mid = hue(h), light = mix(hue(h + 0.12), vec3(1.0), 0.75);
        t = l < 0.33 ? dark : (l < 0.66 ? mid : light);
    } else if (kind > 3.5) {
        t = (1.0 - c) * mix(vec3(1.0), hue(h) + 0.35, 0.6);
    }
    return mix(c, t, clamp(uColour.z, 0.0, 1.0));
}

vec3 show(vec3 c, vec2 q) {
    float inside = step(0.0, q.x) * step(q.x, 1.0) * step(0.0, q.y) * step(q.y, 1.0);
    return mix(uGround.rgb, c, inside);
}

void main() {
    vec2 uv = vUV.st;
    float zoom = 1.0 + uMix.z * uMix.w;
    vec2 q0 = place(uShape.x, uv, zoom);
    vec2 q1 = place(uShape.y, uv, zoom);
    vec3 a = show(treat(texture(sTD2DInputs[0], q0).rgb, uColour.x), q0);
    vec3 b = show(treat(texture(sTD2DInputs[1], q1).rgb, uColour.y), q1);
    float m = uMix.x;
    int mode = int(uMix.y + 0.5);
    vec3 col;
    if (mode == 0) {
        col = mix(a, b, smoothstep(0.0, 1.0, m));
    } else {
        col = m < 0.5 ? a : b;
        if (mode == 2 && m > 0.001 && m < 0.999) {
            // between pictures the channel is empty: grey snow, with the old or new picture faintly under it
            float fr = floor(uShape.w * 60.0);
            float snow = hash2(floor(uv * vec2(427.0, 240.0)) + fr * 1.37);
            float roll = step(0.93, fract(uv.y * 1.7 + uShape.w * 2.3)) * 0.25;
            col = mix(vec3(snow * 0.75 + roll), col, 0.12);
        }
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
