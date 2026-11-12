in float vFly;
out vec4 oFragColor;

void main()
{
	TDCheckDiscard();
	// r: one unit of trail per walking agent (added up by the blend); g: agents in ballistic flight (rings,
	// bursts), which leave no trail, so a ring stays a thin circle instead of filling in as a disc
	oFragColor = TDOutputSwizzle(vec4(1.0 - vFly, vFly, 0.0, 1.0));
}
