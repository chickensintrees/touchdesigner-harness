# Test helper, exec'd inside TouchDesigner with SHOTS = [(take, seed, file, fresh)] and WAIT = frames.
# Sets Take/Seed, waits WAIT frames (the loop needs time to fill), captures, moves on.
# fresh=True also sets Shotstart to now, so the capture shows the arrival at WAIT frames of age.
# State lives in the scene COMP's storage; scene.fetch('shoot_done') turns 1 at the end.
CODE = '''
import tdh
s = op('/project1/sc_droste_crt')
shots = s.fetch('shoot_list'); i = s.fetch('shoot_i'); wait = s.fetch('shoot_wait')
if i > 0:
    t, sd, f, fresh = shots[i - 1]
    s.par.Take = t; s.par.Seed = sd
    tdh.capture(s.path + '/out1', 'experiments/sc_droste_crt/captures/' + f, max_size=1280)
    h = s.op('hub')
    s.fetch('shoot_log').append('%s t=%.2f en=%.2f sec=%d beat=%.2f hl=%.2f hits=%d hm=%.2f bass=%.2f voc=%.2f pulse=%.2f bar=%.2f' % (f, float(h['t']), float(h['energy']), int(h['section']), float(h['beat']), float(h['hit_low']), int(h['hits_low']), float(h['hit_mid']), float(h['bass']), float(h['vocals']), float(h['pulse']), float(h['bar'])))
if i < len(shots):
    t, sd, f, fresh = shots[i]
    s.par.Take = t; s.par.Seed = sd
    s.par.Shotstart = absTime.seconds if fresh else 0
    s.store('shoot_i', i + 1)
    run(s.fetch('shoot_code'), delayFrames=wait)
else:
    s.store('shoot_done', 1)
'''
s = op('/project1/sc_droste_crt')
s.par.Preview = True
s.store('shoot_list', SHOTS); s.store('shoot_i', 0); s.store('shoot_wait', WAIT)
s.store('shoot_code', CODE); s.store('shoot_done', 0); s.store('shoot_log', [])
run(CODE, delayFrames=1)
