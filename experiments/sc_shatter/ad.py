# Review helper (second pass, 2026-11-10). Used through execute_python_script:
#   exec(open(project.folder + '/experiments/sc_shatter/ad.py', encoding='utf-8').read()); r = live(...)
# Schedules live captures with run(delayFrames) and stores the feed read in the same frame.
import tdh

_HERE = project.folder + '/experiments/sc_shatter'  # the repository is where the open project is saved

_ONE = '''
import tdh
s = op('/project1/sc_shatter')
s.par.Take = {take}; s.par.Seed = {seed}; s.par.Subject = {subject}; s.par.Manual = {manual}; s.par.Phase = {phase}
if {cut}:
    s.par.Shotstart = absTime.seconds - {age}
s.op('out1').cook(force=True)
tdh.capture(s.op('out1').path, 'experiments/sc_shatter/captures/{name}', max_size={size})
h = s.op('hub')
d = s.fetch('seq', {{}})
e = dict((k, round(float(h[k]), 3)) for k in ('t', 'bar_pos', 'energy', 'section', 'beat', 'hit_low', 'hits_low', 'bass', 'vocals', 'hit_high', 'pulse'))
e['q'] = round(float(s.op('ctl')['q']), 3)
e['age'] = round(float(s.op('shot')['age']), 2)
e['subj'] = int(s.op('ctl')['subj'])
d['{name}'] = e
s.store('seq', d)
'''


def live(jobs, size=640):
    """jobs: [(delayFrames, take, seed, name, age_or_None, subject, manual_phase)]. age None keeps Shotstart."""
    s = op('/project1/sc_shatter')
    s.par.Preview = True
    s.store('seq', {})
    for j in jobs:
        d, take, seed, name = j[0], j[1], j[2], j[3]
        age = j[4] if len(j) > 4 else 10.0
        subject = j[5] if len(j) > 5 else -1
        phase = j[6] if len(j) > 6 else None
        run(_ONE.format(take=take, seed=seed, subject=subject, name=name, size=size,
                        manual=(phase is not None), phase=(phase if phase is not None else 0.3),
                        cut=(age is not None), age=(age if age is not None else 0)), delayFrames=d)
    return len(jobs)


def got():
    s = op('/project1/sc_shatter')
    d = s.fetch('seq', {})
    return '\n'.join('%s %s' % (k, v) for k, v in sorted(d.items()))


def rebuild():
    g = {'op': op, 'td': td, '__name__': 'build'}
    exec(open(_HERE + '/build.py', encoding='utf-8').read(), g)
    path = g['build']()
    s = op(path)
    s.op('out1').cook(force=True)
    return str({'path': path, 'baked': str(s.fetch('baked_now', None)), 'errors': str(tdh.errors(path))})


def perf():
    s = op('/project1/sc_shatter')
    rows = []
    tot = 0.0
    for o in s.findChildren(maxDepth=2):
        try:
            c = float(o.cpuCookTime); g = float(getattr(o, 'gpuCookTime', 0.0) or 0.0)
        except Exception:
            continue
        if absTime.frame - o.cookAbsFrame <= 2 and (c + g) > 0.01:
            rows.append((round(c + g, 3), o.path.replace(s.path + '/', ''), round(c, 3), round(g, 3)))
            tot += c + g
    rows.sort(reverse=True)
    return str({'total_ms': round(tot, 3), 'rows': rows[:14]})
