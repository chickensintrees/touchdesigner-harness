# Dev helper, run inside TouchDesigner: adds a temporary Execute DAT that captures out1
# at fixed frame offsets after the next section change (the stamp moment), then
# switches itself off. A rebuild removes it.
#   g = {'op': op, 'td': td, 'TAG': '06'}; exec(open('<this file>').read(), g)
_s = op('/project1/sc_rd_stamp')
_old = _s.op('zz_trap')
if _old:
    _old.destroy()
_d = _s.create(td.executeDAT, 'zz_trap')
_d.text = '''import tdh
OFFS = [12, 100, 220, 330]
def onFrameStart(frame):
    frame = absTime.frame   # the timeline frame wraps
    st = me.storage
    hold = op('ctl')['hold'].eval()
    if st.get('t0') is None:
        if hold > 0.5 and st.get('prev', 1) < 0.5:
            st['t0'] = frame
            st['i'] = 0
        st['prev'] = hold
        return
    i = st['i']
    if i >= len(OFFS):
        me.par.active = False
        return
    if frame - st['t0'] >= OFFS[i]:
        h = op('hub')
        name = 'TAG_%d' % OFFS[i]
        tdh.capture(op('out1').path, 'experiments/sc_rd_stamp/captures/' + name + '.png', max_size=1280)
        st['log'] = st.get('log', '') + name + ': ' + ', '.join('%s=%.3f' % (k, float(h[k])) for k in ['t','energy','bass','vocals','section','hit_low','hit_mid','hit_high','pulse']) + ' kick=%.2f' % op('ctl')['kick'].eval() + ' phrase=' + op('phrase').par.text.eval().replace(chr(10), ' / ') + chr(10)
        st['i'] = i + 1
    return
'''.replace('TAG', TAG)
_d.par.framestart = True
_d.par.active = True
r = _d.path
