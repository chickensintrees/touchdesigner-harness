# Probe 1: does gl_VertexID / gl_VertexIndex address a faceted POP's vertices in a GLSL MAT?
REPO = td.project.folder

VS = '''
uniform sampler2D sP;
out vec3 vCol;
vec3 hash3(float n) { return fract(sin(vec3(n * 12.9898, n * 78.233, n * 37.719)) * 43758.5453); }
void main()
{
	int id = gl_VertexIndex;
	int W = textureSize(sP, 0).x;
	vec3 p = texelFetch(sP, ivec2(id % W, id / W), 0).xyz;
	int tri = id / 3;
	vCol = hash3(float(tri) + 1.0);
	p += (vCol - 0.5) * 0.05;
	gl_Position = TDWorldToProj(TDDeform(p));
}
'''
PS = '''
in vec3 vCol;
out vec4 oFragColor;
void main()
{
	TDCheckDiscard();
	oFragColor = TDOutputSwizzle(vec4(vCol, 1.0));
}
'''


def build():
    LIB = {'op': op}
    exec(open(REPO + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    scene = LIB['new_scene']('sc_shatter', 2000, -1100)
    src = scene.create(td.fileinPOP, 'src')
    src.par.file.expr = "mod.paths.model_file('marble_bust')"
    tri = scene.create(td.facetPOP, 'tri')
    tri.par.operation = 'unique'
    tri.par.computenormals = False
    src.outputConnectors[0].connect(tri)
    vp = scene.create(td.poptoTOP, 'vp')
    vp.par.pop = tri.path
    vp.par.rgbamode = 'custom'
    vp.par.extract = 'point'
    vp.par.layout = 'square'
    vp.par.attribscope = 'P'
    geo = scene.create(td.geometryCOMP, 'geo')
    for c in geo.children:
        c.destroy()
    g = geo.create(td.gridPOP, 'grid')
    g.par.rows = 101
    g.par.cols = 301
    f = geo.create(td.facetPOP, 'soup')
    f.par.operation = 'unique'
    f.par.computenormals = False
    g.outputConnectors[0].connect(f)
    f.render = True
    f.display = True
    vd = scene.create(td.textDAT, 'vs')
    vd.text = VS
    pd = scene.create(td.textDAT, 'ps')
    pd.text = PS
    mat = scene.create(td.glslMAT, 'mat')
    mat.par.vdat = vd.path
    mat.par.pdat = pd.path
    mat.seq.sampler.numBlocks = 1
    mat.par.sampler0name = 'sP'
    mat.par.sampler0top = vp.path
    mat.par.sampler0filter = 'nearest'
    mat.par.cullface = 'neither'
    geo.par.material = mat.path
    cam = scene.create(td.cameraCOMP, 'cam')
    cam.par.tz = 2.6
    cam.par.fov = 40
    render = scene.create(td.renderTOP, 'render')
    render.par.camera = cam.path
    render.par.geometry = geo.path
    render.par.lights = ''
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.outputConnectors[0].connect(scene.op('out1'))
    return scene.path
