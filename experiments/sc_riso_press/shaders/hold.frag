// hold.frag: the previous sheet. Copies input 0 (the live separation, less any plate
// that was never rolled onto that sheet) when uLatch.x
// fires (paper advance), otherwise keeps its own previous frame (input 1).
uniform vec4 uLatch;
uniform vec4 uLaid;    // plates that actually reached the paper before it moved on
out vec4 fragColor;
void main() {
    vec4 a = texture(sTD2DInputs[0], vUV.st) * uLaid;
    vec4 b = texture(sTD2DInputs[1], vUV.st);
    fragColor = TDOutputSwizzle(uLatch.x > 0.5 ? a : b);
}
