# exec'd inside TouchDesigner: rebuild (optional) then schedule take captures
import tdh
def go(prefix, rebuild=True, takes=range(8), seed=0.3, **kw):
    if rebuild:
        g = {'op': op, 'td': td, '__name__': 'build', 'absTime': absTime}
        exec(open(project.folder + '/experiments/sc_rutt_etra/build.py', encoding='utf-8').read(), g)
        g['build']()
    g2 = {'op': op, 'td': td, 'run': run, 'absTime': absTime}
    exec(open(project.folder + '/experiments/sc_rutt_etra/shots.py', encoding='utf-8').read(), g2)
    n = g2['shoot'](takes=takes, seed=seed, prefix=prefix, **kw)
    return str(tdh.errors('/project1/sc_rutt_etra')) + ' frames ' + str(n)
