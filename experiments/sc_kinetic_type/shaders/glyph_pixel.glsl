// Glyph coverage from the font atlases, written as palette weights:
// red = ink, green = accent, blue = third colour, black with alpha = knock-out to background.
uniform sampler2D sF0;   // Archivo Black
uniform sampler2D sF1;   // Barlow Condensed Bold
uniform sampler2D sF2;   // Chicago
uniform sampler2D sF3;   // Barlow Condensed numerals, large

in vec2 vUV;
in vec2 vRect;
in float vGate;
flat in vec2 vRectSize;
flat in vec4 vInfo;
out vec4 oFragColor;

float tap(int font, vec2 uv, vec2 dx, vec2 dy)
{
	if (font == 0) return textureGrad(sF0, uv, dx, dy).r;
	if (font == 1) return textureGrad(sF1, uv, dx, dy).r;
	if (font == 2) return textureGrad(sF2, uv, dx, dy).r;
	return textureGrad(sF3, uv, dx, dy).r;
}

void main()
{
	TDCheckDiscard();
	int font = int(floor(vInfo.x + 0.5));
	float a;
	if (font < 0) {
		vec2 d2 = min(vRect, vRectSize - vRect);
		a = clamp(min(d2.x, d2.y) + 0.5, 0.0, 1.0);
	} else {
		vec2 uv = vUV / 1280.0;
		vec2 dx = dFdx(uv), dy = dFdy(uv);
		// magnified: re-sharpen the edge at the 50% contour; minified: trust the mipmapped coverage
		float mag = 1.0 / max(1280.0 * min(length(dx), length(dy)), 1e-5);     // of the more magnified axis
		// four taps 0.6 texel out smooth the stair-steps the atlas has on diagonals (01_flash_first.png)
		float o = mag > 1.2 ? 0.6 / 1280.0 : 0.0;
		float t = 0.25 * (tap(font, uv + vec2(o, o), dx, dy) + tap(font, uv + vec2(-o, o), dx, dy)
			+ tap(font, uv + vec2(o, -o), dx, dy) + tap(font, uv + vec2(-o, -o), dx, dy));
		float w = max(abs(dFdx(t)) + abs(dFdy(t)), 1e-4);
		float sharp = clamp((t - 0.5) / w + 0.5, 0.0, 1.0);
		a = mix(t, sharp, smoothstep(0.8, 1.4, mag));
	}
	a *= vInfo.z;
	int c = int(vInfo.y + 0.5);
	if (vInfo.w > 0.5 && c == 1 && vGate > 0.0 && vGate < 1.0) c = 0;     // roll call: ink inside the gate is knocked out
	vec3 k = c == 1 ? vec3(1.0, 0.0, 0.0) : c == 2 ? vec3(0.0, 1.0, 0.0) : c == 3 ? vec3(0.0, 0.0, 1.0) : vec3(0.0);
	oFragColor = TDOutputSwizzle(vec4(k * a, a));
}
