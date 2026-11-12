# Execute DAT for sc_physarum: turns the feed's counters into one-frame events for the agent shader.
# Writes the Constant CHOP 'ev': boot, kick (share of agents to re-scatter this frame), sec, n, fr, flip.
# see: experiments/sc_physarum/NOTES.md (2026-11-10)
S = {'off': True, 't': 0.0, 'key': None, 'hl': None, 'hm': None, 'sec': None, 'n': 0, 'flip': 0.0}


def onFrameStart(frame):
    sc = parent()
    hubc = op('/project1/sw_hub')
    on = sc.par.Preview.eval()
    if hubc is not None:
        on = on or hubc.par.Solo.eval() or hubc.par.Scene.eval() == sc.name
    if not on:
        S['off'] = True
        return
    ev = op('ev')
    hub = op('hub')
    f = absTime.frame
    key = (int(sc.par.Take.eval()), round(float(sc.par.Seed.eval()), 5), round(float(sc.par.Shotstart.eval()), 3))
    # 'off' and not a frame gap: under load the frame counter jumps by dozens between cooks
    boot = S['off'] or key != S['key']
    now = absTime.seconds
    dt = min(0.1, max(0.0, now - S['t']))
    S['t'] = now
    S['off'] = False
    S['key'] = key
    try:
        hl, hm, sec = int(hub['hits_low']), int(hub['hits_mid']), int(hub['section'])
        sl, sm = float(hub['hit_low']), float(hub['hit_mid'])
    except Exception:
        return
    kick = 0.0
    secchg = 0.0
    S['flip'] *= 0.5 ** (dt / 0.22)
    if boot:
        S['n'] += 1
        S['flip'] = 0.0
    else:
        if S['hl'] is not None and hl != S['hl']:
            kick = min(1.0, max(0.25, sl))
            S['n'] += 1
        if S['hm'] is not None and hm != S['hm']:
            S['flip'] = max(S['flip'], min(1.0, 0.45 + sm))
        if S['sec'] is not None and sec != S['sec']:
            secchg = 1.0
            S['n'] += 1
    S['hl'], S['hm'], S['sec'] = hl, hm, sec
    ev.par.const0value = 1.0 if boot else 0.0
    ev.par.const1value = kick
    ev.par.const2value = secchg
    ev.par.const3value = S['n'] % 4000
    ev.par.const4value = f % 4096
    ev.par.const5value = S['flip']
    return
