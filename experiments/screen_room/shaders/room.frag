// screen_room: a picture inlaid on the switched-off screen of a photographed room.
// Nothing of the room is drawn here: the room, its set and its glass are a picture
// (assets/rooms). This shader only places another picture on the glass, keeps
// the room's own reflections on top of it, lets the screen light what is next
// to it, and pushes the camera in.
// Input 0: the room.  Input 1: its glass mask (white = glass).
// Input 2: the picture as the tube shows it.  Input 3: the same, heavily blurred (the light it throws).
uniform vec4 uRow0;   // the room's matrix: (s, t, w) = M * (x, y, 1), x y in the picture, y down
uniform vec4 uRow1;
uniform vec4 uRow2;   // w how bright the switched-off glass is in the photograph (0..1)
uniform vec4 uScreen; // x y middle of the screen in the picture (y down), z the screen's shape (width / height), w 1 when there is no input
uniform vec4 uShot;   // x push amount, y seconds since the shot began, z seconds the push takes, w seconds (for snow)
uniform vec4 uLight;  // x glow into the room, y room light, z reflections kept on the glass, w screen brightness
out vec4 fragColor;

float hash2(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

void main() {
    // the camera: a slow push toward the screen, eased, never past the edge of the photograph
    float k = clamp(uShot.y / max(0.1, uShot.z), 0.0, 1.0);
    k = 1.0 - (1.0 - k) * (1.0 - k);
    float zoom = 1.0 + uShot.x * k;
    vec2 aim = mix(vec2(0.5), uScreen.xy, 0.85);
    vec2 p = vec2(vUV.s, 1.0 - vUV.t);
    p = aim + (p - aim) / zoom;
    vec2 ruv = vec2(p.x, 1.0 - p.y);
    vec3 room = texture(sTD2DInputs[0], ruv).rgb;
    float glass = texture(sTD2DInputs[1], ruv).r;

    // where this pixel is on the screen (0..1 across, 0..1 down)
    vec3 h = vec3(dot(uRow0.xyz, vec3(p, 1.0)), dot(uRow1.xyz, vec3(p, 1.0)), dot(uRow2.xyz, vec3(p, 1.0)));
    vec2 st = h.xy / h.z;
    // the picture is 16:9 and the tube is not: keep the middle, lose the sides
    float keep = clamp(uScreen.z / (16.0 / 9.0), 0.2, 1.0);
    vec2 suv = vec2(0.5 + (st.x - 0.5) * keep, 1.0 - st.y);
    vec3 pic = texture(sTD2DInputs[2], clamp(suv, 0.0, 1.0)).rgb;
    if (uScreen.w > 0.5) {
        float snow = hash2(floor(st * vec2(200.0, 150.0)) + floor(uShot.w * 60.0) * 1.37);
        pic = vec3(snow * 0.6);
    }
    // a tube is dimmer toward its edge, and the glass keeps what the room reflects in it
    vec2 e = abs(st - 0.5) * 2.0;
    float fall = 1.0 - 0.35 * pow(max(e.x, e.y), 4.0);
    // only what is brighter than the glass itself is a reflection; the rest is the tube's own grey
    vec3 shine = max(room - uRow2.w * 1.15 - 0.02, 0.0) * uLight.z;
    vec3 screen = pic * uLight.w * fall + shine;

    // the light the screen throws: on the bezel next to it and, more faintly, into the room
    vec3 spill = texture(sTD2DInputs[3], clamp(suv, 0.02, 0.98)).rgb;
    float d = length(max(abs(st - 0.5) - 0.5, 0.0));
    float near = exp(-d * 9.0), far = exp(-d * 1.6);
    float lum = dot(room, vec3(0.2126, 0.7152, 0.0722));
    vec3 lit = room * uLight.y;
    lit += spill * uLight.x * (0.4 * near + 0.2 * far) * (0.25 + 0.75 * lum);

    vec3 col = mix(lit, screen, glass);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
