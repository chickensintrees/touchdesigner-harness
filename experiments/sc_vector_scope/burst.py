# Burst helper for the MCP bridge: one take, several captures at given frame offsets after the cut.
# Before exec define TAKE, SEED, PREFIX and FRAMES = [4, 10, 16, ...]. Results in comp storage 'caps'.
SCENE = '/project1/sc_vector_scope'
_s = op(SCENE)
_s.store('caps', {})
run("s = op('%s'); s.par.Take = %d; s.par.Seed = %r; s.par.Shotstart = absTime.seconds; s.par.Preview = True"
    % (SCENE, TAKE, SEED), delayFrames=1)
_cap = ("import tdh\ns = op('%s'); h = s.op('hub')\n"
        "tdh.capture(s.op('out1').path, 'experiments/sc_vector_scope/captures/{file}', max_size=640)\n"
        "d = s.fetch('caps', {{}}); d['{file}'] = dict((k, round(float(h[k]), 3)) for k in "
        "('t', 'energy', 'hit_low', 'hit_mid', 'hit_high', 'pulse', 'beat_pos')); "
        "d['{file}']['age'] = round(float(s.op('shot')['age']), 3); "
        "d['{file}']['spring'] = round(float(s.op('spring')['hit_low']), 3); s.store('caps', d)" % SCENE)
for _f in FRAMES:
    run(_cap.format(file='%s_%03d.png' % (PREFIX, _f)), delayFrames=1 + _f)
queued = len(FRAMES)
