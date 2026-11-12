// Extruded word as a phosphor monolith: solid lit face cut by dark scan gaps that climb
// with the beat, hot top fading to a dim foot, ribbed sides, whole slab goes white on a kick.
uniform vec4 uCol;     // rgb colour, w flash 0..1+
uniform vec4 uFx;      // x beat_pos, y energy, z extrusion depth (local), w height of the word (local)
in vec3 vWP;
in vec3 vLP;
out vec4 fragColor;

void main()
{
    TDCheckDiscard();
    // face normal from derivatives; a degenerate triangle gives a zero cross product,
    // and normalize(0) is NaN, which the Bloom TOP then spreads over the whole frame
    vec3 cr = cross(dFdx(vLP), dFdy(vLP));
    float cl = length(cr);
    float face = cl > 1e-12 ? abs(cr.z) / cl : 1.0;     // 1 on the front/back faces, 0 on the extruded sides
    face = smoothstep(0.3, 0.7, face);
    float flash = uCol.w;
    float hgt = max(uFx.w, 0.01);
    float y01 = clamp(vLP.y / hgt, 0.0, 1.0);
    float grad = mix(0.22, 1.0, y01 * y01 * (3.0 - 2.0 * y01));
    // lit bands with thin dark gaps, climbing one band every two beats
    float band = fract(y01 * 15.0 - uFx.x * 0.5);
    float aa = fwidth(y01 * 15.0);
    float lit = smoothstep(0.0, aa, band) * (1.0 - smoothstep(0.74 - aa, 0.74, band));
    lit = mix(0.07, 1.0, lit);
    // one white bar sweeps up the face every four beats
    float sb = (fract(y01 - uFx.x * 0.25) - 0.5) * 7.0;
    float sweep = exp(-sb * sb);
    float body = face * (grad * lit * (0.85 + 0.6 * uFx.y));
    // the extruded sides: ribs along the depth, so the slab reads as a line drawing in 3D
    float ribs = step(0.5, fract(vLP.z / max(uFx.z, 1e-4) * 5.0 + 0.25));
    float sides = (1.0 - face) * (0.05 + 0.42 * ribs) * (0.5 + 0.6 * uFx.y) * mix(0.5, 1.0, y01);
    vec3 col = uCol.rgb * (body + sides);
    col += mix(uCol.rgb, vec3(1.0), 0.6) * face * lit * sweep * (0.25 + 0.6 * uFx.y);
    col += mix(uCol.rgb, vec3(1.0), 0.75) * flash * (face * (1.3 + 0.9 * lit) + (1.0 - face) * 0.9);
    // fade the foot into the ground
    col *= smoothstep(-0.1, 0.5, vWP.y);
    if (any(isnan(col)) || any(isinf(col))) col = vec3(0.0);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
