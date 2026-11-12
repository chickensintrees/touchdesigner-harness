# Review helper: rebuild the scene from build.py.  exec with {'op': op, 'td': td}; then g['go']()
# The repository is wherever the open project file is saved (td.project.folder).
def go():
    g = {'op': op, 'td': td, '__name__': 'build'}
    exec(open(td.project.folder + '/experiments/sc_kifs_office/build.py', encoding='utf-8').read(), g)
    return g['build']()
