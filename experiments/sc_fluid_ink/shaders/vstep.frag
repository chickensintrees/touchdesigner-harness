// Velocity step: self-advection, then forces. Output is NOT yet divergence-free.
// in0: last frame's projected field  (rg velocity in frame-heights per second, b pressure, a shot id)
// in1: last frame's dye (rgb = three inks), for buoyancy
// out: rg velocity, b pressure (warm start for the solver), a divergence source (kick blast)
uniform vec4 uTime;   // evolve, shot age, shot id, boot
uniform vec4 uHits;   // hit_low, hit_mid, hit_high, bass
uniform vec4 uK;      // kick hashes k1 k2 k3, kick mode (0 blast, 1 jet from an edge, 2 drop from the top)
uniform vec4 uS;      // snare hashes s1 s2 s3, vocals
uniform vec4 uNoz;    // nozzle x (aspect units), y, strength, angle
uniform vec4 uTake;   // stir, buoyancy, vorticity confinement, damping per second
uniform vec4 uGain;   // kick, snare, nozzle, arrival shove
out vec4 fragColor;

const float ASP = 16.0 / 9.0;
const float DT = 1.0 / 60.0;

vec2 V(vec2 uv) { return texture(sTD2DInputs[0], uv).xy; }

float curlAt(vec2 uv, vec2 px) {
    return 0.5 * (V(uv + vec2(px.x, 0.0)).y - V(uv - vec2(px.x, 0.0)).y
                - V(uv + vec2(0.0, px.y)).x + V(uv - vec2(0.0, px.y)).x);
}

// where a kick lands and which way it pushes; the same code is in dye.frag
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
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 p = uv * vec2(ASP, 1.0);
    vec4 c = texture(sTD2DInputs[0], uv);
    bool reset = abs(c.a - uTime.z) > 0.002 || uTime.w > 0.5;

    // semi-Lagrangian self-advection
    vec2 back = uv - DT * c.xy / vec2(ASP, 1.0);
    vec4 a = texture(sTD2DInputs[0], back);
    vec2 vel = a.xy;
    float pr = c.b;

    // vorticity confinement: push along the gradient of |curl| so small eddies survive the grid
    float w  = curlAt(uv, px);
    float wl = abs(curlAt(uv - vec2(px.x, 0.0), px));
    float wr = abs(curlAt(uv + vec2(px.x, 0.0), px));
    float wb = abs(curlAt(uv - vec2(0.0, px.y), px));
    float wt = abs(curlAt(uv + vec2(0.0, px.y), px));
    vec2 eta = 0.5 * vec2(wr - wl, wt - wb);
    eta /= (length(eta) + 1e-5);
    vel += uTake.z * 0.1 * vec2(eta.y, -eta.x) * w;

    float t = uTime.x;
    float bass = clamp(uHits.w, 0.0, 1.6);

    // bass: slow global stir, the curl of a drifting stream function (divergence-free by construction)
    vec2 q = p * 2.2;
    vec2 stir = vec2(
         cos(q.y * 1.3 + t * 0.21) * sin(q.x * 0.9 - t * 0.13) + 0.6 * cos(q.y * 2.9 - t * 0.17 + 1.7),
        -cos(q.x * 1.1 - t * 0.19) * sin(q.y * 1.2 + t * 0.11) - 0.6 * cos(q.x * 2.3 + t * 0.23 + 0.4));
    // ... and a shove as the stamp lets go, so the ink starts to tear even in a quiet bar
    float arrive = smoothstep(0.25, 0.4, uTime.y) * (1.0 - smoothstep(0.6, 1.1, uTime.y));
    vel += DT * uTake.x * 0.1 * (0.3 + bass + 5.0 * arrive * uGain.w) * stir;

    // kick
    vec2 kc, kd;
    kickGeo(uK.xyz, uK.w, kc, kd);
    vec2 d = p - kc;
    float kick = clamp(uHits.x, 0.0, 1.2) * uGain.x;
    float divsrc = 0.0;
    float h3 = uK.z;
    if (uK.w < 0.5) {
        // a blast: a star of 3 to 6 jets out of the drop. (A true divergence source was tried
        // first: in a closed tank it pushes the whole frame outward and wipes the picture.)
        float r = length(d);
        float lobes = 3.0 + floor(h3 * 3.99);
        float star = pow(max(0.0, cos(atan(d.y, d.x) * lobes + uK.x * 20.0)), 3.0);
        vel += (d / (r + 1e-4)) * kick * 0.16 * star * exp(-r * r / 0.012) * smoothstep(0.0, 0.03, r);
    } else {
        float along = dot(d, kd);
        float across = dot(d, vec2(-kd.y, kd.x));
        float g = exp(-across * across / 0.0022) * exp(-along * along / 0.03);
        vel += kd * kick * 0.13 * g;
    }

    // snare: a vortex pair, which then travels on its own
    vec2 sc = vec2(mix(0.3, ASP - 0.3, uS.x), mix(0.22, 0.78, uS.y));
    float sa = uS.z * 6.2832;
    vec2 sdir = vec2(cos(sa), sin(sa));
    vec2 sn = vec2(-sdir.y, sdir.x);
    float snare = clamp(uHits.y, 0.0, 1.2) * uGain.y;
    for (int i = 0; i < 2; i++) {
        float sgn = i == 0 ? 1.0 : -1.0;
        vec2 dd = p - (sc + sn * 0.07 * sgn);
        float g = exp(-dot(dd, dd) / 0.006);
        vel += sgn * snare * 1.0 * g * vec2(-dd.y, dd.x);
    }

    // voice: a nozzle
    vec2 nd = vec2(cos(uNoz.w), sin(uNoz.w));
    vec2 dn = p - uNoz.xy;
    vel += nd * uNoz.z * uGain.z * 0.06 * exp(-dot(dn, dn) / 0.0016);

    // ink is heavier than water (side-on takes)
    vec3 dye = texture(sTD2DInputs[1], uv).rgb;
    vel.y -= DT * uTake.y * dot(dye, vec3(1.0, 0.9, 0.8));

    vel *= 1.0 - uTake.w * DT;
    vel = clamp(vel, vec2(-4.0), vec2(4.0));

    if (reset) {
        vel = 0.2 * uTake.x * stir;
        pr = 0.0;
    }
    fragColor = TDOutputSwizzle(vec4(vel, pr, divsrc));
}
