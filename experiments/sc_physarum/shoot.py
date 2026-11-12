# Dev helper, run inside TouchDesigner: start a shot (Take, Seed, Shotstart) and capture it after each delay.
#   g = {'op': op, 'run': run, 'absTime': absTime, 'TAKE': 2, 'SEED': 0.3, 'NAME': 'take_2', 'DELAYS': [20, 240]}
#   exec(open('<this file>').read(), g)
# Captures land in captures/<NAME>_<delay>.png; the feed at each capture is stored on the COMP as 'cap_<NAME>_<delay>'.
_s = op('/project1/sc_physarum')
_s.par.Take = TAKE
_s.par.Seed = SEED
_s.par.Shotstart = absTime.seconds
_code = '''
s = op('/project1/sc_physarum')
if int(s.par.Take) == %d:
    g = {'op': op, 'NAME': '%s'}
    exec(open(project.folder + '/experiments/sc_physarum/cap.py', encoding='utf-8').read(), g)
    s.store('cap_%s', g['r'])
else:
    s.store('cap_%s', 'take was changed under us')
'''
for _d in DELAYS:
    _n = '%s_%d' % (NAME, _d) if len(DELAYS) > 1 else NAME
    run(_code % (TAKE, _n, _n, _n), delayFrames=_d)
r = 'scheduled'
