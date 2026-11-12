# Dev helper, run inside TouchDesigner: play a list of shots back to back and capture each one.
#   g = {'op': op, 'run': run, 'absTime': absTime, 'SHOTS': [(take, seed, name), ...], 'PER': 300, 'DELAYS': [270]}
#   exec(open('<this file>').read(), g)
# Shot i starts at frame i*PER and is captured DELAYS frames into it (captures/<name>[_<delay>].png).
_start = '''
s = op('/project1/sc_physarum')
s.par.Take = %d
s.par.Seed = %f
s.par.Shotstart = absTime.seconds
'''
_cap = '''
s = op('/project1/sc_physarum')
if int(s.par.Take) == %d:
    g = {'op': op, 'NAME': '%s'}
    exec(open(project.folder + '/experiments/sc_physarum/cap.py', encoding='utf-8').read(), g)
    s.store('cap_%s', g['r'])
else:
    s.store('cap_%s', 'take was changed under us')
'''
for _i, (_t, _sd, _nm) in enumerate(SHOTS):
    run(_start % (_t, _sd), delayFrames=1 + _i * PER)
    for _d in DELAYS:
        _n = '%s_%d' % (_nm, _d) if len(DELAYS) > 1 else _nm
        run(_cap % (_t, _n, _n, _n), delayFrames=1 + _i * PER + _d)
r = 'scheduled %d shots' % len(SHOTS)
