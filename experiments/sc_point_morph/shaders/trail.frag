// input 0: this frame's cloud, input 1: last frame's trail.
// The echo is read slightly magnified about the sculpture, so every frame's light creeps
// outward: rays stand off the shape, and a drum hit throws a shell of it into the room.
uniform vec4 uTrail;   // x decay, y zoom per frame, z centre x, w centre y
out vec4 fragColor;

void main()
{
	vec2 uv = vUV.st;
	vec4 now = texture(sTD2DInputs[0], uv);
	vec2 c = uTrail.zw;
	vec4 old = texture(sTD2DInputs[1], (uv - c) / (1.0 + uTrail.y) + c);
	// the echo cools as it leaves
	old.rgb *= vec3(0.94, 0.985, 1.0);
	// maximum, not add: a decayed echo never brightens what is already there
	fragColor = TDOutputSwizzle(max(now, old * uTrail.x));
}
