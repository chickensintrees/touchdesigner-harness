# Capture helper for the MCP bridge (nothing in the scene depends on it).
# Before exec, define SHOTS = [(take, seed, 'file.png'), ...] and optionally HOLD (frames per shot, default 60)
# and OVER = {(take_row_name, column): value} to try table values without a rebuild.
# Each shot: set Take/Seed/Shotstart, wait HOLD frames, capture out1, store the feed in comp storage 'caps'.
SCENE = '/project1/sc_vector_scope'
_s = op(SCENE)
_hold = globals().get('HOLD', 60)
for (_row, _col), _v in globals().get('OVER', {}).items():
    _s.op('takes')[_row, _col] = _v
_s.store('caps', {})
_set = ("s = op('%s'); s.par.Take = {take}; s.par.Seed = {seed}; s.par.Shotstart = absTime.seconds; s.par.Preview = True" % SCENE)
_cap = ("import tdh\ns = op('%s'); h = s.op('hub')\n"
        "s.par.Take = {take}; s.par.Seed = {seed}\n"
        "tdh.capture(s.op('out1').path, 'experiments/sc_vector_scope/captures/{file}', max_size={size})\n"
        "d = s.fetch('caps', {{}}); d['{file}'] = dict((k, round(float(h[k]), 3)) for k in "
        "('t', 'energy', 'rms', 'hit_low', 'hit_mid', 'hit_high', 'pulse', 'beat_pos', 'section', 'vocals', 'bass')); s.store('caps', d)" % SCENE)
for _i, (_take, _seed, _file) in enumerate(SHOTS):
    run(_set.format(take=_take, seed=_seed), delayFrames=1 + _i * _hold)
    run(_cap.format(take=_take, seed=_seed, file=_file, size=globals().get('SIZE', 1280)), delayFrames=_i * _hold + _hold - 1)
queued = len(SHOTS)
