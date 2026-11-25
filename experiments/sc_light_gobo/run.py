# Review helpers, not part of the scene. Use from execute_python_script:
#     g = {'op': op, 'td': td, 'absTime': absTime, 'run': run}
#     exec(open(project.folder + '/experiments/sc_light_gobo/run.py', encoding='utf-8').read(), g)
#     r = g['rebuild']()   /  g['shot'](take, seed, 'name')  /  g['all_takes'](8)  /  g['info']()
import tdh

REPO = td.project.folder.replace(chr(92), "/")   # the repository is wherever the open project is saved
S = "/project1/sc_light_gobo"
NL = chr(10)


def rebuild():
    b = {"op": op, "td": td, "__name__": "build"}
    exec(open(REPO + "/experiments/sc_light_gobo/build.py", encoding="utf-8").read(), b)
    return b["build"]()


def info():
    """Compile messages of the shaders plus errors."""
    s = op(S)
    out = {"errors": str(tdh.errors(S))}
    for n in ("beam", "grade", "m_cam", "m_lgt"):
        o = s.op(n)
        i = s.op(n + "_info")
        if o is not None and i is not None and "rror" in i.text:
            out[n] = i.text[:1500]
    return out


def setshot(take, seed, age_back=5.0):
    s = op(S)
    s.par.Take = take
    s.par.Seed = seed
    s.par.Shotstart = absTime.seconds - age_back
    return take


def shot(take, seed, name, age_back=5.0, delay=1):
    """Set the take at +delay frames, capture 3 frames later, store the feed with it."""
    set_code = NL.join([
        "s = op('%s')" % S,
        "s.par.Take = %d; s.par.Seed = %g; s.par.Shotstart = absTime.seconds - %g" % (take, seed, age_back),
    ])
    cap_code = NL.join([
        "import tdh",
        "s = op('%s')" % S,
        "s.par.Take = %d; s.par.Seed = %g" % (take, seed),
        "tdh.capture('%s/out1', 'experiments/sc_light_gobo/captures/%s.png', max_size=1280)" % (S, name),
        "h = s.op('hub')",
        "d = s.fetch('shots', {})",
        "d['%s'] = str({k: round(float(h[k]), 3) for k in ('t','section','energy','beat','bass','vocals','bar_pos','hit_low','hits_low','hit_mid','pulse')})" % name,
        "s.store('shots', d)",
    ])
    run(set_code, delayFrames=delay)
    run(cap_code, delayFrames=delay + 3)
    return name


def all_takes(n, seed=0.3, prefix="take_", every=8):
    for k in range(n):
        shot(k, seed, "%s%d" % (prefix, k), delay=1 + every * k)
    return n


def some(takes, seed=0.3, prefix="x_", every=8):
    """Capture a chosen list of takes: files <prefix><take>.png."""
    for j, k in enumerate(takes):
        shot(k, seed, "%s%d" % (prefix, k), delay=1 + every * j)
    return len(takes)


def cost(takes, every=45, samples=3):
    """Store beam/grade/gbuffer cook times per take in COMP storage 'cost' (read it in a later call)."""
    op(S).store('cost', {})
    j = 0
    for k in takes:
        run("s = op('%s'); s.par.Take = %d; s.par.Seed = 0.3" % (S, k), delayFrames=1 + every * j)
        for m in range(samples):
            code = NL.join([
                "s = op('%s')" % S,
                "s.par.Take = %d" % k,
                "d = s.fetch('cost', {})",
                "row = [round(float(s.op(n).gpuCookTime), 2) for n in ('beam', 'grade', 'glow', 'gb_cam', 'gb_lgt')]",
                "row.append(round(sum(float(o.cpuCookTime) for o in s.findChildren(maxDepth=1) if absTime.frame - o.cookAbsFrame < 3), 2))",
                "d.setdefault(%d, []).append(row)" % k,
                "s.store('cost', d)",
            ])
            run(code, delayFrames=1 + every * j + every - 4 * (samples - m))
        j += 1
    return len(takes)
