// sc_exploded_view: writes the drawing's G-buffer, not a picture.
// buffer 0: world normal xyz, camera depth.  buffer 1: part id, cut-face flag, glow, coverage.
// buffer 2: the Input picture as it sits on the parts (rgb, a 1 where a part carries it); black when Input is blank.
uniform vec4 uObj;         // x mode (0 separate parts, 1 slabs, 2 sweep cut)
uniform vec4 uExt;         // x lo, y hi of the model along the axis
uniform vec4 uPicFit;      // x 1 when an Input picture is on, y z its width and height in model units, w 1: this model is a thin shell (below)
uniform sampler2D sPic;    // the Input picture (insel)

in Vertex {
	vec3 wN;
	vec3 wPos;
	float along;
	float glow;
	flat vec3 axisW;
	flat vec3 planeLo;
	flat vec3 planeHi;
	flat float pid;
	flat vec2 range;
	flat vec3 camPos;
	flat vec4 camFwd;
	vec3 keyUV;
	flat vec3 offW;
	flat vec3 vOrg;
} iVert;

layout(location = 0) out vec4 oFragColor;
layout(location = 1) out vec4 oData;
layout(location = 2) out vec4 oPic;

void main()
{
	TDCheckDiscard();
	if (iVert.along < iVert.range.x || iVert.along > iVert.range.y)
		discard;
	vec3 P = iVert.wPos;
	// the parts object's normal slot is spent on part data, so its faces get a geometric normal
	vec3 n = uObj.x < 0.5 ? normalize(cross(dFdx(P), dFdy(P))) : normalize(iVert.wN);
	float cut = 0.0;
	vec3 ray = iVert.camFwd.w > 0.5 ? iVert.camFwd.xyz : normalize(P - iVert.camPos);
	// A model that is a thin double-walled shell (a skin with a second skin just inside it) shows,
	// through a cut, the far inner skin, which faces the camera. Seen from outside a solid would show
	// its cut there, so a face that looks back at the slab's own centre line counts as the cut too.
	// (Only for the models named in CAP_INSIDE: on a hollowed or pierced shape it would hatch the outside.)
	bool inside = false;
	if (uPicFit.w > 0.5 && uObj.x > 0.5 && gl_FrontFacing) {
		vec3 a0 = normalize(iVert.axisW);
		vec3 rel = P - iVert.offW - vec3(iVert.vOrg.xy, 0.0);
		rel -= a0 * dot(rel, a0);
		inside = dot(n, rel) < -0.2 * length(rel);
	}
	if (!gl_FrontFacing || inside) {
		if (uObj.x > 0.5) {
			// looking into a sliced solid: what we see is the cut. Put the pixel on the cut plane.
			vec3 a = normalize(iVert.axisW);
			float facing = dot(a, ray);
			vec3 P0 = facing < 0.0 ? iVert.planeHi : iVert.planeLo;
			float den = abs(facing) < 1e-4 ? 1e-4 : facing;
			float t = dot(a, P0 - P) / den;
			P = P + ray * min(t, 0.0);
			n = facing < 0.0 ? a : -a;
			cut = 1.0;
		} else if (uObj.x > 0.5) {
			n = -n;
		}
	}
	if (uObj.x < 0.5 && dot(n, ray) > 0.0)
		n = -n;
	oFragColor = vec4(n, dot(P - iVert.camPos, iVert.camFwd.xyz));
	// third slot: landing glow for separate parts; for every sliced model, how far along its axis the pixel is (0..1)
	float third = uObj.x < 0.5 ? iVert.glow : clamp((iVert.along - uExt.x) / max(uExt.y - uExt.x, 1e-5), 0.0, 1.0);
	oData = vec4(iVert.pid, cut, third, 1.0);
	// The Input picture. On the parts object it is printed across the whole object, so every part carries its
	// own tile away with it. On every other part it is projected from the camera onto the part as it
	// was before it came apart, so the slabs carry their strips of it with them (cut faces included).
	oPic = vec4(0.0);
	if (uPicFit.x > 0.5) {
		vec2 puv;
		float ok = 1.0;
		if (uObj.x < 0.5) {
			puv = iVert.keyUV.xy;
			ok = step(0.5, iVert.keyUV.z);
		} else {
			vec3 rest = (P - iVert.offW - vec3(iVert.vOrg.xy, 0.0)) / max(iVert.vOrg.z, 1e-4);
			puv = 0.5 + rest.xy / uPicFit.yz;
		}
		// mirrored repeat, so a part larger than the picture is still covered
		puv = 1.0 - abs(1.0 - mod(puv, 2.0));
		oPic = vec4(texture(sPic, puv).rgb, ok);
	}
}
