# Convenience for the MCP bridge: exec this file inside TouchDesigner to rebuild the scene.
#   exec(open(project.folder + '/experiments/sc_vector_scope/rebuild.py').read())
g = {'op': op, 'td': td, '__name__': 'build'}
exec(open(project.folder + '/experiments/sc_vector_scope/build.py', encoding='utf-8').read(), g)
built = g['build']()
