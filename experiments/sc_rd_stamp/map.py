# Dev helper, run inside TouchDesigner: a second copy of the simulation where feed F runs
# 0.010..0.070 left to right and kill k runs 0.050..0.070 bottom to top, seeded with a grid
# of blobs. After about 15 s it shows where patterns can live on this discretisation.
# A rebuild removes it.   g = {'op': op, 'td': td, 'absTime': absTime}; exec(open('<this file>').read(), g)
_s = op('/project1/sc_rd_stamp')
for _n in ['zm_drv', 'zm_sim', 'zm_fb', 'zm_frag']:
    if _s.op(_n):
        _s.op(_n).destroy()
_src = open(td.project.folder + '/experiments/sc_rd_stamp/shaders/sim.frag', encoding='utf-8').read()
_a = _src.index('    float F = mix(')
_b = _src.index('    float U = 1.0 - c.r;')
_src = _src[:_a] + '''    float F = mix(0.010, 0.070, uv.x);
    float k = mix(0.050, 0.070, uv.y);
    vec2 cell = fract(uv * vec2(32.0, 18.0)) - 0.5;
    float seed = step(max(abs(cell.x), abs(cell.y)), 0.22) * uDrift.z;
    c.g = max(c.g, seed); c.r = max(c.r, seed * 0.85);
''' + _src[_b:]
_d = _s.create(td.textDAT, 'zm_frag')
_d.text = _src
_fb = _s.create(td.feedbackTOP, 'zm_fb')
_fb.par.format = 'rgba16float'
_s.op('zero').outputConnectors[0].connect(_fb)
_g = _s.create(td.glslTOP, 'zm_sim')
_g.par.pixeldat = 'zm_frag'
_g.par.outputresolution = 'custom'
_g.par.resolutionw, _g.par.resolutionh = 640, 360
_g.par.format = 'rgba16float'
_g.par.npasses = 8
_fb.outputConnectors[0].connect(_g)
_g.seq.vec.numBlocks = 2
_g.par.vec0name = 'uAudio'
_g.par.vec1name = 'uDrift'
_g.par.vec1valuez.expr = "1 if absTime.frame < %d else 0" % (int(absTime.frame) + 20)
_fb.par.top = 'zm_sim'
_fb.par.resetpulse.pulse()
_e = _s.create(td.executeDAT, 'zm_drv')
_e.text = "def onFrameStart(frame):\n    op('zm_sim').cook(force=True)\n    return\n"
_e.par.framestart = True
_e.par.active = True
for _i, _o in enumerate([_d, _fb, _g, _e]):
    _o.nodeX, _o.nodeY = 200 * _i, 500
r = 'ok'
