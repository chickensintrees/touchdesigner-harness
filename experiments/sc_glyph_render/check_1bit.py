# Asserts the scene's promise: the final image holds only #000 and #FFF.
# Run inside TouchDesigner:
#   g = {'op': op}; exec(open('<this file>', encoding='utf-8').read(), g); r = g['check']()
import numpy as np


def check(path='/project1/sc_glyph_render/out1'):
    a = op(path).numpyArray()[:, :, :3]
    other = int(np.count_nonzero((a != 0.0) & (a != 1.0)))
    white = float((a[:, :, 0] == 1.0).mean())
    grey = int(np.count_nonzero((a[:, :, 0] != a[:, :, 1]) | (a[:, :, 1] != a[:, :, 2])))
    return {'pass': other == 0 and grey == 0, 'pixels_not_0_or_1': other,
            'pixels_not_neutral': grey, 'white_fraction': round(white, 4),
            'size': [int(a.shape[1]), int(a.shape[0])]}
