# Test (2026-11-11): with Describe off and Input blank, every take is pixel-identical to the shader as it stood
# before Describe and Input were added (shaders/kifs_ref_2026-11-10.frag, the committed file of 2026-11-10).
# It builds a second GLSL TOP beside the live one, on the scene's own text walls with the same uniform expressions,
# cooks both in the same frame for each take, and returns the largest pixel difference (expected 0.0).
# The 'describe_on' and 'input_on' rows prove the comparison can fail: they must be greater than 0.
#     g = {'op': op, 'td': td, 'absTime': absTime, 'project': project}
#     exec(open(project.folder + '/experiments/sc_kifs_office/ab_test.py', encoding='utf-8').read(), g); r = g['run']()
# If the look is changed on purpose later, replace the reference file with the new shader and say so in NOTES.md.
import numpy as np

S = '/project1/sc_kifs_office'
REF = 'experiments/sc_kifs_office/shaders/kifs_ref_2026-11-10.frag'   # under the repository (project.folder)
JOBS = [(0, 0.3), (1, 0.3), (2, 0.8), (3, 0.1), (4, 0.3), (5, 0.3), (6, 0.7)]


def run(testcard='/project1/sw_testcard/out1'):
    s = op(S)
    keep = (s.par.Preview.eval(), s.par.Describe.eval(), s.par.Input.eval(), s.par.Take.eval(), s.par.Seed.eval())
    s.par.Preview = True
    s.par.Describe = False
    s.par.Input = ''
    k = s.op('kifs')
    for n in ('ab_frag', 'ab_ref'):
        if s.op(n):
            s.op(n).destroy()
    d = s.create(td.textDAT, 'ab_frag')
    d.text = open(project.folder + '/' + REF, encoding='utf-8').read()
    a = s.create(td.glslTOP, 'ab_ref')
    a.par.pixeldat = d.name
    a.par.outputresolution = 'custom'
    a.par.resolutionw, a.par.resolutionh = 1280, 720
    a.par.format = 'rgba16float'
    a.par.inputextenduv = 'repeat'
    a.par.inputfiltertype = k.par.inputfiltertype.eval()
    a.inputConnectors[0].connect(s.op('wall'))
    a.inputConnectors[1].connect(s.op('phrases'))
    a.seq.vec.numBlocks = 8
    for i in range(8):
        getattr(a.par, 'vec%dname' % i).val = getattr(k.par, 'vec%dname' % i).eval()
        for ax in 'xyzw':
            getattr(a.par, 'vec%dvalue%s' % (i, ax)).expr = getattr(k.par, 'vec%dvalue%s' % (i, ax)).expr

    def diff(take, seed):
        s.par.Take, s.par.Seed = take, seed
        s.par.Shotstart = absTime.seconds - 5
        k.cook(force=True)
        a.cook(force=True)
        s.op('out1').cook(force=True)
        x, y = s.op('out1').numpyArray(), a.numpyArray()
        return float(np.abs(x - y).max()), float(x[..., :3].mean())

    r = {}
    worst = 0.0
    for take, seed in JOBS:
        m, mean = diff(take, seed)
        worst = max(worst, m)
        r['take%d' % take] = 'maxdiff %.6f (frame mean %.4f)' % (m, mean)
    s.par.Describe = True
    r['describe_on'] = 'maxdiff %.6f (must be > 0)' % diff(0, 0.3)[0]
    s.par.Describe = False
    s.par.Input = testcard
    r['input_on'] = 'maxdiff %.6f (must be > 0)' % diff(5, 0.3)[0]
    s.par.Input = ''
    r['ref_errors'] = str(a.warnings()) + str(a.errors())
    r['PASS'] = worst == 0.0 and not r['ref_errors'] and '0.000000' not in r['describe_on'] + r['input_on']
    a.destroy()
    d.destroy()
    s.par.Preview, s.par.Describe, s.par.Input, s.par.Take, s.par.Seed = keep
    return r
