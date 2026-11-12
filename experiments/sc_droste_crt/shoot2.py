# Test helper like shoot.py, with Describe and Input per shot.
# exec'd inside TouchDesigner with SHOTS = [(take, seed, file, age, describe, input)] and WAIT = frames.
# age: None leaves Shotstart at 0 (old shot); a number sets Shotstart so the capture is at about that age (s).
# scene.fetch('shoot_done') turns 1 at the end; Describe and Input are put back to off / blank.
CODE = '''
import tdh
s = op('/project1/sc_droste_crt')
shots = s.fetch('shoot_list'); i = s.fetch('shoot_i'); wait = s.fetch('shoot_wait')
if i > 0:
    t, sd, f, age, d, inp = shots[i - 1]
    s.par.Take = t; s.par.Seed = sd; s.par.Describe = d; s.par.Input = inp
    tdh.capture(s.path + '/out1', 'experiments/sc_droste_crt/captures/' + f, max_size=1280)
    h = s.op('hub')
    s.fetch('shoot_log').append('%s t=%.2f sec=%d beat=%.2f hl=%.2f age=%.2f' % (f, float(h['t']), int(h['section']), float(h['beat']), float(h['hit_low']), float(s.op('shot')['age'])))
if i < len(shots):
    t, sd, f, age, d, inp = shots[i]
    s.par.Take = t; s.par.Seed = sd; s.par.Describe = d; s.par.Input = inp
    s.par.Shotstart = 0 if age is None else absTime.seconds + wait / 60.0 - age
    s.store('shoot_i', i + 1)
    run(s.fetch('shoot_code'), delayFrames=wait)
else:
    s.par.Describe = False; s.par.Input = ''; s.par.Shotstart = 0
    s.store('shoot_done', 1)
'''
s = op('/project1/sc_droste_crt')
s.par.Preview = True
s.store('shoot_list', SHOTS); s.store('shoot_i', 0); s.store('shoot_wait', WAIT)
s.store('shoot_code', CODE); s.store('shoot_done', 0); s.store('shoot_log', [])
run(CODE, delayFrames=1)
