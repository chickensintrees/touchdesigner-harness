// im_depth_relief: each point is an opaque, depth-tested disc.
in vec4 vCol;
out vec4 oFragColor;

void main() {
    TDCheckDiscard();
    float d = length(gl_PointCoord - 0.5) * 2.0;
    if (d > 1.0)
        discard;
    oFragColor = TDOutputSwizzle(vec4(vCol.rgb * (1.0 - 0.25 * d * d), 1.0));
}
