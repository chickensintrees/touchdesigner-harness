# Helper: rebuild the scene from build.py. exec this file's text inside TouchDesigner.
g = {'op': op, 'td': td, '__name__': 'build'}
exec(open(project.folder + '/experiments/sc_paper_storm/build.py', encoding='utf-8').read(), g)
built = g['build']()
