# Dev helper, run inside TouchDesigner: write one channel of a TOP as a grey PNG.
#   g = {'op': op, 'TOP': 'zm_sim', 'CH': 1, 'NAME': 'map_a'}; exec(open('<this file>').read(), g)
import numpy as np
import tdh
from td import project
_a = op('/project1/sc_rd_stamp').op(TOP).numpyArray()
_g = np.clip(_a[..., CH], 0, 1)
_img = np.dstack([_g, _g, _g]).astype(np.float32)
open(project.folder + '/experiments/sc_rd_stamp/captures/%s.png' % NAME, 'wb').write(
    tdh.imaging.encode_png(tdh.imaging.to_uint8(_img[::-1])))
r = 'ok'
