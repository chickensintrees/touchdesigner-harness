// Log-polar Escher twist of the master image. The master camera sits on the screen's
// axis, so the screen is the whole frame scaled by s about the frame centre, and the
// image obeys I(s z) = T(I(z)). Mapping w -> alpha w in the log plane with
// alpha = 1 - i ln(s) / 2pi turns the nested rectangles into one continuous spiral.
// input 0: master image
uniform vec4 uE;    // s (screen/frame ratio), zoom phase 0..1, hue step degrees, gain per level
uniform vec4 uE2;   // twist amount, centre x, centre y, extra rotation (radians)
out vec4 fragColor;

vec3 hueRot(vec3 c, float deg) {
    float a = radians(deg);
    float cs = cos(a), sn = sin(a);
    const vec3 k = vec3(0.57735);
    return c * cs + cross(k, c) * sn + k * dot(k, c) * (1.0 - cs);
}

void main() {
    vec2 asp = vec2(16.0 / 9.0, 1.0);
    vec2 z = (vUV.st * 2.0 - 1.0 - vec2(uE2.y, uE2.z)) * asp;
    float s = clamp(uE.x, 0.05, 0.95);
    float ls = log(s);
    float r = max(length(z), 1e-5);
    float th = atan(z.y, z.x);
    vec2 W = vec2(log(r), th + uE2.w);
    float beta = -ls / 6.2831853 * uE2.x;
    vec2 w = vec2(W.x - W.y * beta, W.x * beta + W.y);
    w.x += uE.y * ls;
    vec2 zp = exp(w.x) * vec2(cos(w.y), sin(w.y));
    float m = max(abs(zp.x) / asp.x, abs(zp.y));
    float k = floor(log(max(m, 1e-6)) / ls);
    vec2 zs = zp * pow(s, -k);
    vec2 uv = zs / asp * 0.5 + 0.5;
    vec3 c = texture(sTD2DInputs[0], clamp(uv, 0.001, 0.999)).rgb;
    // T^k, made continuous: the zoom phase and the angle each stand for a fraction of a level
    float lev = k - uE.y - uE2.x * th / 6.2831853;
    c = hueRot(max(c, vec3(0.0)), uE.z * lev);
    c *= pow(uE.w, clamp(lev, -2.0, 6.0));
    fragColor = TDOutputSwizzle(vec4(max(c, vec3(0.0)), 1.0));
}
