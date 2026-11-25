# Helper: capture every take in one call, in a given mode. exec this file's text inside TouchDesigner
# after setting PREFIX, DESCRIBE, INPUT (and optionally REBUILD, SEED, TAKES_TO_SHOOT) in the same namespace:
#   PREFIX='r'; DESCRIBE=1; INPUT=''; exec(open(project.folder + '/experiments/sc_paper_storm/allshots.py').read()); result
# Files land in captures/<PREFIX><take>.png. Leaves Describe/Input as set; say so in the same call if that matters.
exec(open(project.folder + '/experiments/sc_paper_storm/shot.py', encoding='utf-8').read())
if globals().get('REBUILD'):
    g = {'op': op, 'td': td, '__name__': 'build'}
    exec(open(project.folder + '/experiments/sc_paper_storm/build.py', encoding='utf-8').read(), g)
    g['build']()
result = {}
for i in globals().get('TAKES_TO_SHOOT', range(8)):
    d = shot('%s%d' % (PREFIX, i), take=i, seed=globals().get('SEED', 0.4), age=5.0, describe=DESCRIBE, inp=INPUT)
    result[i] = d['err']
    result['feed'] = d
