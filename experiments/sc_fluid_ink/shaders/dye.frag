// Dye step at full resolution: carry three inks along the velocity field, then add new ink.
// in0: last frame's dye (rgb = inks 0..2, a = shot id), in1: velocity (rg), in2: src (rgb = ink to stamp)
uniform vec4 uTime;   // evolve, shot age, shot id, boot
uniform vec4 uStamp;  // stamp (1 while the shape is held down), dissipation per second, kick ink amount, hat ink amount
uniform vec4 uHits;   // hit_low, hit_mid, hit_high, bass
uniform vec4 uK;      // kick hashes k1 k2 k3, kick mode
uniform vec4 uS;      // snare hashes s1 s2 s3, vocals
uniform vec4 uNoz;    // nozzle x, y, strength, angle
uniform vec4 uInk;    // ink index for kick, snare, nozzle, hat (0..2; 3 = all, <0 none)
uniform vec4 uH;      // hat hashes h1 h2 h3, snare ink amount
uniform vec4 uIn;     // Input feed: share of the Input picture's ink pressed in each frame (0 = no Input); 1 = stamp replaces
out vec4 fragColor;

const float ASP = 16.0 / 9.0;
const float DT = 1.0 / 60.0;

vec3 ink(float i) {
    if (i < -0.5) return vec3(0.0);
    if (i < 0.5) return vec3(1.0, 0.0, 0.0);
    if (i < 1.5) return vec3(0.0, 1.0, 0.0);
    if (i < 2.5) return vec3(0.0, 0.0, 1.0);
    return vec3(0.6);
}

// the same code is in vstep.frag
void kickGeo(vec3 h, float mode, out vec2 c, out vec2 dir) {
    if (mode < 0.5) {
        c = vec2(mix(0.22, ASP - 0.22, h.x), mix(0.2, 0.8, h.y));
        dir = vec2(0.0);
    } else if (mode < 1.5) {
        float side = floor(h.z * 4.0);
        if (side < 1.0)      { c = vec2(0.02, mix(0.2, 0.8, h.x));        dir = vec2(1.0, (h.y - 0.5) * 0.7); }
        else if (side < 2.0) { c = vec2(ASP - 0.02, mix(0.2, 0.8, h.x));  dir = vec2(-1.0, (h.y - 0.5) * 0.7); }
        else if (side < 3.0) { c = vec2(mix(0.3, ASP - 0.3, h.x), 0.02);  dir = vec2((h.y - 0.5) * 0.7, 1.0); }
        else                 { c = vec2(mix(0.3, ASP - 0.3, h.x), 0.98);  dir = vec2((h.y - 0.5) * 0.7, -1.0); }
        dir = normalize(dir);
    } else {
        c = vec2(mix(0.15, ASP - 0.15, h.x), 0.97);
        dir = normalize(vec2((h.y - 0.5) * 0.25, -1.0));
    }
}

void main() {
    vec2 uv = vUV.st;
    vec2 p = uv * vec2(ASP, 1.0);
    float pid = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0).a;
    bool reset = abs(pid - uTime.z) > 0.002 || uTime.w > 0.5;

    vec2 v = texture(sTD2DInputs[1], uv).xy;
    vec2 back = uv - DT * v / vec2(ASP, 1.0);
    vec3 d = texture(sTD2DInputs[0], clamp(back, vec2(0.0005), vec2(0.9995))).rgb;
    d *= 1.0 - uStamp.y * DT;
    if (reset) d = vec3(0.0);

    // kick: a drop of ink where the blast or jet is
    vec2 kc, kd;
    kickGeo(uK.xyz, uK.w, kc, kd);
    vec2 dk = p - (kc + kd * 0.05);
    float kr = uK.w < 0.5 ? 0.0011 : 0.0018;
    float ki = uInk.x > 3.5 ? floor(uK.y * 2.999) : uInk.x;     // 4: a different ink each kick
    d += ink(ki) * clamp(uHits.x, 0.0, 1.2) * uStamp.z * exp(-dot(dk, dk) / kr);

    // snare: a blob between the two vortices, which they carry off
    vec2 sc = vec2(mix(0.3, ASP - 0.3, uS.x), mix(0.22, 0.78, uS.y));
    vec2 ds = p - sc;
    d += ink(uInk.y) * clamp(uHits.y, 0.0, 1.2) * uH.w * exp(-dot(ds, ds) / 0.0016);

    // hat: a fine droplet
    vec2 hc = vec2(mix(0.1, ASP - 0.1, uH.x), mix(0.1, 0.9, uH.y));
    vec2 dh = p - hc;
    d += ink(uInk.w) * clamp(uHits.z, 0.0, 1.2) * uStamp.w * exp(-dot(dh, dh) / mix(0.00006, 0.0003, uH.z));

    // voice: the nozzle
    vec2 dn = p - uNoz.xy;
    d += ink(uInk.z) * uNoz.z * 0.5 * exp(-dot(dn, dn) / 0.0005);

    // the shape, held down crisp while stamp is on
    vec3 s = texture(sTD2DInputs[2], uv).rgb;
    d = max(d, s * uStamp.x);
    // Describe mode, page take: the reprint replaces what is there, so the sentences can be read
    if (uIn.y > 0.5 && uStamp.x > 0.5) d = s;
    // Input: a moving picture is pressed in a little every frame, so it keeps re-forming while
    // the water carries it off. 0 (no Input) leaves this step out.
    if (uIn.x > 0.0) d = mix(d, s, uIn.x);

    d = clamp(d, vec3(0.0), vec3(1.6));
    fragColor = TDOutputSwizzle(vec4(d, uTime.z));
}
