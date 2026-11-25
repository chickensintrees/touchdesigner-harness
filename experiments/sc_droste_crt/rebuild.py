# Runs the builder inside TouchDesigner: exec(open(this).read()) then read `result`.
import traceback
g = {'op': op, 'td': td, '__name__': 'build', 'absTime': absTime, 'tdu': tdu}
try:
    exec(open(project.folder + '/experiments/sc_droste_crt/build.py', encoding='utf-8').read(), g)
    result = g['build']()
except Exception:
    result = traceback.format_exc()
