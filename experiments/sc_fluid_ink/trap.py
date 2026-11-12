# Dev helper, run inside TouchDesigner: for each (tag, take, seed) in SHOTS restart the shot, then
# capture out1 at each of AGES seconds into it (a temporary Execute DAT; a rebuild removes it).
# Captures are captures/<tag>_<i>.png. Log: op('/project1/sc_fluid_ink').fetch('traplog')
#   g = {'op': op, 'td': td, 'absTime': absTime, 'SHOTS': [('t0', 0, 0.3)], 'AGES': [0.2, 1, 3, 6]}
#   exec(open('<this file>').read(), g)
_s = op('/project1/sc_fluid_ink')
_old = _s.op('zz_trap')
if _old:
    _old.destroy()
_s.store('traplog', '')
_d = _s.create(td.executeDAT, 'zz_trap')
_d.text = '''import tdh
AGES = %r
SHOTS = %r
def start(st, k):
    tag, take, seed = SHOTS[k]
    parent().par.Take = take
    parent().par.Seed = seed
    parent().par.Shotstart = absTime.seconds
    st['k'] = k
    st['i'] = 0
def onFrameEnd(frame):
    st = me.storage
    k = st.get('k', -1)
    if k < 0:
        start(st, 0)
        return
    if k >= len(SHOTS):
        me.par.active = False
        return
    tag, take, seed = SHOTS[k]
    # the cutter may be driving this scene too: hold the shot we are testing
    if int(parent().par.Take.eval()) != take or abs(parent().par.Seed.eval() - seed) > 1e-6:
        start(st, k)
        return
    i = st['i']
    age = op('shot')['age'].eval()
    if age >= AGES[i]:
        h = op('hub')
        name = '%%s_%%d' %% (tag, i)
        tdh.capture(op('out1').path, 'experiments/sc_fluid_ink/captures/' + name + '.png', max_size=1280)
        line = name + ' age=%%.2f ' %% age + ', '.join('%%s=%%.2f' %% (c, float(h[c])) for c in ['t','energy','bass','vocals','section','beat','hit_low','hits_low','hit_mid','hit_high','pulse']) + ' phrase=' + op('phrase').par.text.eval().replace(chr(10), ' / ')
        parent().store('traplog', parent().fetch('traplog', '') + line + chr(10))
        st['i'] = i + 1
        if st['i'] >= len(AGES):
            if k + 1 < len(SHOTS):
                start(st, k + 1)
            else:
                st['k'] = k + 1
    return
''' % (AGES, SHOTS)
_d.par.frameend = True
_d.par.active = True
r = _d.path
