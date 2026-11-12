"""Decides which scene is on screen, one frame at a time. No TouchDesigner imports:
the Execute DAT in sw_cut feeds it the hub's channels, and tests feed it a baked feed.

A "cut key" names the current shot slot. It changes at every musical section,
inside loud passages every `bars_loud` bars, and inside quiet passages every
`bars_quiet` bars counted from the section's start (so a long quiet section is
not one long shot). When the key changes, the cut waits
for the next beat line, then shows the scene that fits the passage's energy and
has been off screen longest. The next scene is chosen before the cut so it can be
warmed up (cooked off screen) and feedback loops are alive when it appears.

Every shot also gets a plan, so that two visits to a scene do not look alike:
a take number (how many times that scene has been shown: the scene picks its
camera, palette, subject from it), a seed, a treatment (a picture effect held for
the shot), a transition into it, and sometimes a second scene layered over it.
"""

import zlib

DEFAULTS = {
    "loud": 0.75,  # energy at or above this is a loud passage
    "hysteresis": 0.03,  # loud switches off only below loud - hysteresis
    "bars_loud": 2,  # in a loud passage, cut every this many bars
    "bars_quiet": 0,  # in a quiet passage, cut every this many bars of a section; 0 = at sections only
    "quiet_last": 0.75,  # no cut inside a quiet section past this share of it: the section's end is near
    "min_bars": 1.0,  # shortest shot, in bars
    "warm_section_pos": 0.88,  # start warming the next scene this far through a section
    "warm_bar": 0.6,  # ...or this far through the last bar before a loud-passage cut
    "treatments": [],  # names of picture effects; "" (none) is always available
    "treat_chance": 0.45,  # share of shots that get a treatment
    "transitions": [],  # names of ways into a shot; "cut" is always available
    "trans_chance": 0.5,  # share of cuts that use a transition other than a hard cut
    "layer_chance": 0.15,  # share of shots with a second scene layered in
    "layer_modes": [],  # names of ways to combine two scenes
}


def new_state():
    return {
        "scene": "",
        "key": None,
        "next": "",
        "next_plan": None,
        "pending": False,
        "last_cut_bar": -999.0,
        "history": [],
        "last_shown": {},  # scene -> shot number it was last on screen
        "visits": {},  # scene -> how many shots it has had
        "shot": {"n": 0, "seed": 0.0, "take": 0, "treat": "", "trans": "cut", "layer": "", "layer_mode": ""},
        "loud": False,
        "loud_next": None,
        "bar_i": None,
        "beat_i": None,
        "section": None,
        "section_bar": 0,  # the bar the current section began in
    }


def _hash01(*parts):
    """A stable number in [0, 1) from any values: same inputs, same answer, every run."""
    return (zlib.crc32("|".join(str(p) for p in parts).encode()) % 100000) / 100000.0


def candidates(scenes, energy):
    """scenes: [(name, energy_min, energy_max)]. Names whose band holds this energy; all if none do."""
    fit = [n for n, lo, hi in scenes if lo <= energy <= hi]
    return fit or [n for n, _, _ in scenes]


def pick(scenes, key, energy, avoid, last_shown=None):
    """The fitting scene that has been off screen longest (never-shown first).

    Ties are broken by a stable hash of the key, so the same moment of the same
    track always picks the same scene, but every scene gets used before any
    returns.
    """
    names = candidates(scenes, energy)
    names = [n for n in names if n not in avoid] or names
    if not names:
        return ""
    last_shown = last_shown or {}
    return min(names, key=lambda n: (last_shown.get(n, -1), _hash01(key, n)))


def _choose(options, chance, last, *seed):
    """One of `options` with probability `chance`, never the one used last; else ''."""
    options = [o for o in options if o and o != last]
    if not options or _hash01("use", *seed) >= chance:
        return ""
    return options[int(_hash01("which", *seed) * len(options)) % len(options)]


def plan_shot(state, scene, scenes, cfg, key):
    """The look of the next shot of `scene`: take, seed, treatment, transition, layer."""
    n = state["shot"]["n"] + 1
    take = state["visits"].get(scene, 0)
    prev = state["shot"]
    treat = _choose(cfg["treatments"], cfg["treat_chance"], prev["treat"], "treat", key, n)
    trans = _choose(cfg["transitions"], cfg["trans_chance"], prev["trans"], "trans", key, n) or "cut"
    layer, layer_mode = "", ""
    others = [s for s, _, _ in scenes if s != scene and s != state["scene"]]
    if others and cfg["layer_modes"] and _hash01("layer", key, n) < cfg["layer_chance"]:
        layer = min(others, key=lambda s: (state["last_shown"].get(s, -1), _hash01("layer", key, s)))
        modes = cfg["layer_modes"]
        layer_mode = modes[int(_hash01("mode", key, n) * len(modes)) % len(modes)]
    return {
        "n": n,
        "seed": _hash01("seed", key, n, scene),
        "take": take,
        "treat": treat,
        "trans": trans,
        "layer": layer,
        "layer_mode": layer_mode,
    }


def _show(state, scene, plan, bar_now):
    state["scene"] = scene
    state["shot"] = plan
    state["visits"][scene] = state["visits"].get(scene, 0) + 1
    state["last_shown"][scene] = plan["n"]
    if plan["layer"]:
        state["last_shown"][plan["layer"]] = plan["n"]
    state["history"] = (state["history"] + [scene])[-8:]
    state["last_cut_bar"] = bar_now
    state["next"], state["next_plan"], state["pending"] = "", None, False


def step(state, feed, scenes, cfg=None):
    """Advance one frame. Returns True when a cut happened on this frame.

    feed needs: energy, section, section_pos, bar_i, bar, beat_i.
    state['scene'] and state['shot'] are what to show; state['next'] and
    state['next_plan'] are what to warm up (may be '' / None).

    Cuts land on beat lines only. Whether a passage counts as loud is decided late
    in each bar and applied at the bar line, so energy wobbling around the
    threshold cannot fire a cut mid-bar, and the next scene is always known at
    least a frame before it appears.
    """
    cfg = {**DEFAULTS, **(cfg or {})}
    if not scenes:
        return False
    bar_i, beat_i = int(feed["bar_i"]), int(feed["beat_i"])
    bar_now = bar_i + feed["bar"]  # continuous, so a shot length is a real duration
    energy = feed["energy"]
    every = max(1, int(cfg["bars_loud"]))
    new_beat = state["beat_i"] is not None and beat_i != state["beat_i"]

    # The track looped or was re-cued: bar time ran backwards. Without this the
    # shortest-shot rule would block every cut until the old bar count came round.
    if bar_now < state["last_cut_bar"] - 1.0 and state["last_cut_bar"] > -900:
        state["last_cut_bar"] = bar_now - cfg["min_bars"]
        state["key"] = None if not state["scene"] else state["key"]
        state["pending"] = True

    if state["bar_i"] is not None and bar_i != state["bar_i"] and state["loud_next"] is not None:
        state["loud"], state["loud_next"] = state["loud_next"], None
    if state["loud_next"] is None and feed["bar"] > cfg["warm_bar"]:
        floor = cfg["loud"] - (cfg["hysteresis"] if state["loud"] else 0.0)
        state["loud_next"] = energy >= floor
    state["bar_i"], state["beat_i"] = bar_i, beat_i

    section = int(feed["section"])
    if section != state.get("section") or bar_i < state.get("section_bar", 0):
        state["section"], state["section_bar"] = section, bar_i
    quiet_every = max(0, int(cfg["bars_quiet"]))
    in_section = bar_i - state["section_bar"]
    if state["loud"]:
        slot = bar_i // every
    elif quiet_every and feed["section_pos"] <= cfg["quiet_last"]:
        slot = ("q", in_section // quiet_every)
    elif quiet_every:
        slot = state["key"][1] if state["key"] and state["key"][0] == section else ("q", in_section // quiet_every)
    else:
        slot = 0
    key = (section, slot)
    avoid = state["history"][-2:]

    if not state["scene"]:
        state["key"] = key
        scene = pick(scenes, key, energy, [], state["last_shown"])
        _show(state, scene, plan_shot(state, scene, scenes, cfg, key), bar_now)
        return True

    cut = False
    if state["pending"] and new_beat and bar_now - state["last_cut_bar"] >= cfg["min_bars"]:
        scene, plan = state["next"], state["next_plan"]
        if not scene:
            scene = pick(scenes, key, energy, avoid, state["last_shown"])
            plan = plan_shot(state, scene, scenes, cfg, key)
        state["key"] = key
        _show(state, scene, plan, bar_now)
        cut = True
    elif key != state["key"]:
        state["pending"] = True

    if not state["next"]:
        loud_soon = state["loud_next"] if state["loud_next"] is not None else state["loud"]
        crosses = (bar_i + 1) // every != bar_i // every or not state["loud"]
        bar_cut_soon = feed["bar"] > cfg["warm_bar"] and loud_soon and crosses
        if quiet_every and not loud_soon and feed["bar"] > cfg["warm_bar"] and feed["section_pos"] <= cfg["quiet_last"]:
            bar_cut_soon = bar_cut_soon or (in_section + 1) // quiet_every != in_section // quiet_every
        if state["pending"] or feed["section_pos"] > cfg["warm_section_pos"] or bar_cut_soon:
            next_key = ("next", int(feed["section"]), bar_i)
            state["next"] = pick(scenes, next_key, energy, avoid, state["last_shown"])
            state["next_plan"] = plan_shot(state, state["next"], scenes, cfg, next_key)
    return cut


def simulate(rows, names, scenes, cfg=None, fps=60.0, rate=100.0, loops=1):
    """Run the cutter over a baked feed, `loops` times end to end.

    rows: feed.chan rows; names: its channel names. Returns (shots, cold): shots is
    [(time_s, scene, plan)] for every cut, with time counted across loops; cold is
    the times of cuts to a scene that was not announced as state['next'] on the
    frame before.
    """
    col = {n: i for i, n in enumerate(names)}
    state = new_state()
    shots, cold = [], []
    duration = rows[-1][col["t"]]
    for loop in range(loops):
        frame = 0
        while frame / fps <= duration:
            t = frame / fps
            row = rows[min(len(rows) - 1, int(t * rate))]
            feed = {
                "energy": row[col["energy"]],
                "section": row[col["section"]],
                "section_pos": row[col["section_pos"]],
                "bar_i": int(row[col["bar_pos"]] // 1),
                "bar": row[col["bar_pos"]] % 1,
                "beat_i": int(row[col["beat_pos"]] // 1),
            }
            warmed = state["next"]
            if step(state, feed, scenes, cfg):
                shots.append((round(loop * duration + t, 3), state["scene"], dict(state["shot"])))
                if len(shots) > 1 and warmed != state["scene"]:
                    cold.append(round(loop * duration + t, 3))
            frame += 1
    return shots, cold
