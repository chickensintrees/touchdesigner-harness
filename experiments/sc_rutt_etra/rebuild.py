# Paste into execute_python_script: rebuilds the scene and reports errors.
import tdh
g = {'op': op, 'td': td, '__name__': 'build', 'absTime': absTime}
exec(open(project.folder + '/experiments/sc_rutt_etra/build.py', encoding='utf-8').read(), g)
path = g['build']()
r = str(path)
