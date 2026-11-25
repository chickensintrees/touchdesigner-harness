# Compares where the layout says each line's ink is with where TouchDesigner drew it.
# Run inside TouchDesigner (never blocks: one take per call):
#     g = {'op': op}
#     exec(open(project.folder + '/experiments/id_title_card/measure_td.py', encoding='utf-8').read(), g)
#     g['measure'](take)   -> [{'run', 'text', 'want': [x0, y0, x1, y1], 'got': [...], 'off': worst edge in px}]
# Edges that lie outside the frame are compared with the frame edge.
import numpy as np


def measure(take, comp="/project1/id_title_card"):
    c = op(comp)  # noqa: F821
    keep = (c.par.Take.eval(), c.par.Cycle.eval())
    c.par.Take, c.par.Cycle = take, 0
    table = c.op("runs")
    table.cook(force=True)
    found = []
    for i in range(8):
        row = i + 1
        if int(float(table[row, "kind"].val)) not in (1, 3):
            continue
        top = c.op("run%d" % i)
        top.cook(force=True)
        a = top.numpyArray()[::-1, :, 3]          # row 0 = top of the frame
        ys, xs = np.where(a > 0.5)
        if not len(xs):
            found.append({"run": i, "text": table[row, "text"].val, "got": None, "off": 9999})
            continue
        h, w = a.shape
        got = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        want = [float(table[row, k].val) for k in ("x0", "y0", "x1", "y1")]
        if float(table[row, "dtr"].val):          # its box is for the letterspacing fully open; held still it is closed
            want[0] -= float(table[row, "dx"].val)
            want[2] += float(table[row, "dx"].val)
        clip = [min(max(want[0], 0), w), min(max(want[1], 0), h), min(max(want[2], 0), w), min(max(want[3], 0), h)]
        found.append({"run": i, "text": table[row, "text"].val, "want": [round(v, 1) for v in clip], "got": got,
                      "off": round(max(abs(g - v) for g, v in zip(got, clip)), 1)})
    c.par.Take, c.par.Cycle = keep
    return found
