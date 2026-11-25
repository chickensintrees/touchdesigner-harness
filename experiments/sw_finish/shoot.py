# Captures a source TOP through every preset of /project1/sw_finish, for before
# and after sheets. Run inside TouchDesigner:
#
#     g = {'op': op, 'td': td, '__name__': 'shoot'}
#     exec(open(project.folder + '/experiments/sw_finish/shoot.py', encoding='utf-8').read(), g)
#     g['shoot']({'rutt': '/project1/sc_rutt_etra/out1'})
import json

import td


def shoot(sources, finish="/project1/sw_finish", restore="film35"):
    import tdh

    repo = td.project.folder.replace(chr(92), "/")
    with open(repo + "/experiments/sw_finish/presets.json", encoding="utf-8") as fh:
        presets = list(json.load(fh))
    c = op(finish)  # noqa: F821
    apply = c.op("preset_exec").module.apply
    files = []
    for short, top in sources.items():
        c.par.Input = top
        for p in presets:
            apply(c, p)
            r = tdh.capture(finish + "/out1", "experiments/sw_finish/captures/%s_%s.png" % (short, p), max_size=1280)
            files.append(r["file"].split("/")[-1])
    c.par.Preset = restore
    apply(c, restore)
    return files
