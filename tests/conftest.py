import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "td"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fake_td


@pytest.fixture
def td(monkeypatch):
    """A fresh fake `td` module with a small network under /project1:

    noise1 (TOP, mid-gray) -> level1 (TOP) -> out1 (TOP)
    lfo1 (CHOP, values in 0..1), notes (Text DAT), info1 (Info DAT),
    TDMCP (COMP, must be excluded), broken (TOP with an error)
    """
    mod = fake_td.make_module()
    monkeypatch.setitem(sys.modules, "td", mod)
    import tdh

    tdh.reload()
    r = mod._registry
    P = fake_td.Par
    fake_td.OP(r, "/project1", "containerCOMP")
    gray = np.full((64, 96, 4), 0.5, np.float32)
    noise = fake_td.TOP(r, "/project1/noise1", "noiseTOP", pixels=gray,
                        pars=[P("period", 4.0, default=1.0), P("seed", 1, default=1)], x=0, y=0)
    level = fake_td.TOP(r, "/project1/level1", "levelTOP", pixels=gray,
                        pars=[P("brightness1", 1.0, default=1.0, mode=fake_td.ParMode.EXPRESSION,
                                expr="absTime.seconds % 1")], x=200)
    out = fake_td.TOP(r, "/project1/out1", "outTOP", pixels=gray, x=400)
    fake_td.wire(noise, level)
    fake_td.wire(level, out)
    fake_td.CHOP(r, "/project1/lfo1", "lfoCHOP", channels={"chan1": [0.0, 0.5, 1.0]}, n_inputs=0)
    fake_td.DAT(r, "/project1/notes", "textDAT", text="hello\nworld", n_inputs=0,
                pars=[P("file", "", default="")])
    fake_td.DAT(r, "/project1/info1", "infoDAT", text="changes every frame", n_inputs=0)
    fake_td.OP(r, "/project1/TDMCP", "baseCOMP", errors="should never be seen")
    fake_td.OP(r, "/project1/TDMCP/inner", "textDAT", errors="should never be seen")
    return mod


@pytest.fixture
def broken(td):
    fake_td.TOP(td._registry, "/project1/broken", "glslTOP", errors="Compile error line 3")
    return td
