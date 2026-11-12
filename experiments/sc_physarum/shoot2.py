# Dev helper, run inside TouchDesigner: play shots back to back with Describe / Input set, capture each.
#   g = {'op': op, 'run': run, 'absTime': absTime, 'SHOTS': [(take, seed, describe, input, name), ...], 'PER': 300, 'DELAY': 270}
#   exec(open('<this file>').read(), g)
# The capture call re-asserts nothing: if the cutter changed Take under us the result says so.
_start = '''
s = op('/project1/sc_physarum')
s.par.Preview = True
s.par.Take = %d
s.par.Seed = %f
s.par.Describe = %d
s.par.Input = %r
s.par.Shotstart = absTime.seconds
'''
_cap = '''
s = op('/project1/sc_physarum')
if int(s.par.Take) == %d and int(s.par.Describe) == %d:
    g = {'op': op, 'NAME': %r}
    exec(open(project.folder + '/experiments/sc_physarum/cap.py', encoding='utf-8').read(), g)
    s.store('cap_' + %r, g['r'])
else:
    s.store('cap_' + %r, 'take was changed under us')
'''
for _i, (_t, _sd, _de, _in, _nm) in enumerate(SHOTS):
    run(_start % (_t, _sd, _de, _in), delayFrames=1 + _i * PER)
    run(_cap % (_t, _de, _nm, _nm, _nm), delayFrames=1 + _i * PER + DELAY)
r = 'scheduled %d shots' % len(SHOTS)
