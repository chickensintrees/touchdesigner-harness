# Where every card of the cut-out montage is on this frame, and what the camera
# and the ground do. Pure Python with no TouchDesigner in it, so tests/test_montage.py
# can check it; inside TouchDesigner a Script CHOP calls frame() once per frame.
#
# The camera looks down -z from about z = 4.3 with a 46 degree lens, so at z = 0 the
# frame is about 6.5 wide and 3.65 high. A card is 1 high before its size.
import math

CARDS = 12

# name, ground pattern, palette (two flat colours), finish preset
TAKES = [
    {"name": "Conveyor", "ground": "burst", "palette": ((0.949, 0.761, 0.0), (0.922, 0.541, 0.227)), "finish": "film35"},
    {"name": "Slam", "ground": "rings", "palette": ((0.086, 0.169, 0.451), (0.957, 0.455, 0.627)), "finish": "film35"},
    {"name": "Carousel", "ground": "stripes", "palette": ((0.925, 0.898, 0.816), (0.812, 0.176, 0.153)), "finish": "vhs"},
    {"name": "Speaker wall", "ground": "dots", "palette": ((0.059, 0.365, 0.314), (0.953, 0.816, 0.353)), "finish": "film35"},
    {"name": "Tunnel", "ground": "rings", "palette": ((0.043, 0.043, 0.051), (0.925, 0.2, 0.471)), "finish": "crt"},
    {"name": "Burst", "ground": "burst", "palette": ((0.176, 0.627, 0.851), (0.937, 0.925, 0.878)), "finish": "film35"},
    {"name": "Giant and chorus", "ground": "split", "palette": ((0.914, 0.322, 0.11), (0.129, 0.114, 0.196)), "finish": "film35"},
    {"name": "Cascade", "ground": "checker", "palette": ((0.537, 0.376, 0.769), (0.957, 0.890, 0.404)), "finish": "vhs"},
]
GROUNDS = ["burst", "rings", "stripes", "dots", "checker", "split"]
FINISHES = ["clean", "film35", "vhs", "crt", "onebit"]
FEED = ("beat_pos", "bar_pos", "hit_low", "hit_mid", "hit_high", "hits_low", "energy", "bass", "drums", "vocals", "other")


def _hash(i, k):
    return math.modf(abs(math.sin(i * 12.9898 + k * 78.233) * 43758.5453))[0]


def _punch(phase, amount, rate=7.0):
    """1 at rest, 1 + amount right on the beat, falling back fast."""
    return 1.0 + amount * math.exp(-rate * (phase % 1.0))


def _card(x, y, z, size, rz=0.0, pic=0):
    return {"x": x, "y": y, "z": z, "s": size, "rz": rz, "pic": int(pic)}


def _conveyor(i, f, seed, n):
    # two rows running opposite ways, one bar per third of the frame; kicks swell the near row
    row = i % 2
    way = 1.0 if row == 0 else -1.0
    per = n // 2
    run = (i // 2) / per + way * f["bar_pos"] * 0.2 + seed
    u = run % 1.0
    lap = int(math.floor(run)) * (1 if row == 0 else -1)  # a card that leaves one side comes back as a new picture
    x = (u - 0.5) * 9.5
    y = 0.85 if row else -0.8
    z = -1.2 if row else 0.6
    size = (1.25 if row else 1.55) * (1.0 + (0.3 * f["hit_low"] if row == 0 else 0.22 * f["hit_mid"]))
    rz = 9.0 * math.sin(f["beat_pos"] * math.pi + i) * (0.3 + f["hit_high"])
    return _card(x, y, z, size, rz, i + lap * n + int(seed * 97))


def _slam(i, f, seed, n):
    # card 0 is a new picture slammed down on every beat; the earlier ones lie under it, pushed back
    beat = int(math.floor(f["beat_pos"]))
    k = beat - i
    spread = min(1.0, i / 3.0)
    x = (_hash(k, 1) - 0.5) * 3.6 * spread
    y = (_hash(k, 2) - 0.5) * 1.5 * spread
    rz = (_hash(k, 3) - 0.5) * 50.0
    size = 1.9 - 0.09 * i
    if i == 0:
        size *= _punch(f["beat_pos"], 0.55)
        rz *= 0.4
    else:  # the pile under it jumps on kicks and shivers on hi-hats
        size *= 1.0 + 0.18 * f["hit_low"]
        rz += 16.0 * f["hit_high"] * math.sin(i * 2.3)
        y += 0.2 * f["hit_low"] * (1 if i % 2 else -1)
    return _card(x, y, 1.0 - 0.22 * i, size, rz, k + int(seed * 97))


def _carousel(i, f, seed, n):
    # a ring that turns a quarter per bar; the card at the front is biggest, drums shake them
    a = (i / n + f["bar_pos"] * 0.25 + seed) * math.tau
    x = 2.7 * math.sin(a)
    z = 1.5 * math.cos(a) - 0.6
    y = 0.25 * math.sin(a * 2.0) + 0.45 * f["drums"] * math.sin(i * 2.4 + f["beat_pos"] * math.tau)
    size = (1.1 + 0.5 * (math.cos(a) * 0.5 + 0.5)) * (1.0 + 0.25 * f["hit_low"])
    return _card(x, y, z, size, 14.0 * f["hit_mid"] * math.sin(i * 1.7), i + int(seed * 97))


def _wall(i, f, seed, n):
    # a tight wall, four across: each column is the size of one part of the music,
    # and a kick swaps the pictures of one row
    col, row = i % 4, i // 4
    stem = (f["bass"], f["drums"], f["other"], f["vocals"])[col]
    size = 0.62 + 1.05 * min(1.0, stem) + 0.2 * f["hit_low"] * (row == int(f["hits_low"]) % 3)
    x = (col - 1.5) * 1.55
    y = (1 - row) * 1.15 + 0.14 * math.sin(f["beat_pos"] * math.pi + col * 1.6)  # the columns nod in turn on the beat
    pic = i + int(seed * 97) + n * ((int(f["hits_low"]) + 2 - row) // 3)  # how many times this row has been swapped
    return _card(x, y, 0.02 * i, size, 0.0, pic)


def _tunnel(i, f, seed, n):
    # cards fly out of the distance past the lens, one card per beat, on a spiral
    u = (i / n + f["beat_pos"] / n) % 1.0
    lap = int(math.floor(i / n + f["beat_pos"] / n))
    a = (i * 0.61 + seed) * math.tau
    r = 0.45 + 1.5 * u
    z = -9.0 + 12.6 * u
    return _card(r * math.cos(a), r * math.sin(a) * 0.62, z, 1.5 * (1.0 + 0.3 * f["hit_low"]), (a * 57.3) % 360.0 * 0.15 + 20.0 * f["hit_high"], i + lap * n + int(seed * 97))


def _burst(i, f, seed, n):
    # gathered in the middle, thrown outward by every kick, turned by the count of kicks
    a = (i / n + 0.07 * int(f["hits_low"]) + 0.125 * f["bar_pos"] + seed) * math.tau  # the wheel also turns with the bar
    r = 0.6 + 2.3 * f["hit_low"] * (0.6 + 0.4 * _hash(i, 5)) + 0.5 * f["energy"]
    size = 0.7 + 0.4 * _hash(i, 6) + 0.3 * f["hit_mid"]
    return _card(r * math.cos(a) * 1.35, r * math.sin(a) * 0.8, -0.8 + 0.14 * i, size, a * 57.3 + 90.0 * f["hit_low"], i + int(seed * 97))


def _giant(i, f, seed, n):
    # one picture as large as the frame, new every bar; the rest hop along the bottom in time
    if i == 0:
        bar = int(math.floor(f["bar_pos"]))
        x = (f["bar_pos"] % 1.0 - 0.5) * 0.9 * (1 if bar % 2 else -1)
        return _card(x, 0.25, -0.6, 3.3 * _punch(f["bar_pos"], 0.18, 9.0), 0.0, -1 - bar - int(seed * 97))
    u = (i - 1) / (n - 2)
    hop = abs(math.sin((f["beat_pos"] + 0.5 * (i % 2)) * math.pi))
    return _card((u - 0.5) * 6.2, -1.3 + 0.38 * hop * (0.4 + f["drums"]), 0.9, 0.62 + 0.1 * f["hit_mid"], 12.0 * math.sin(f["beat_pos"] * math.pi + i), i + int(seed * 97))


def _cascade(i, f, seed, n):
    # four columns of falling cards, a beat per fall, tumbling; hi-hats kick them sideways
    col = i % 4
    u = (i // 4 / 3.0 + f["beat_pos"] * 0.33 + _hash(col, 7)) % 1.0
    lap = int(math.floor(i // 4 / 3.0 + f["beat_pos"] * 0.33 + _hash(col, 7)))
    x = (col - 1.5) * 1.6 + 0.3 * f["hit_high"] * math.sin(i * 3.1)
    return _card(x, 2.6 - 5.2 * u, 0.3 * col - 0.4, 1.2 + 0.3 * f["hit_low"], (u * 200.0 + i * 40.0) * (1 if col % 2 else -1), i + lap * n + int(seed * 97))


def new_deal():
    """The state deal() keeps between frames: which picture each card holds, and the pictures not yet shown."""
    return {"held": {}, "deck": [], "round": 0, "count": 0}


def deal(state, take, pics, count):
    """Which picture of the set (0..count-1) each card shows on this frame.

    `pics` are the cards' own picture numbers from frame() (any integers, one per
    card). A number that was on screen last frame keeps its picture. A new number
    takes the next picture from a shuffled deck of the whole set, and the deck is
    only shuffled again once it is empty: no subject comes back until every one
    has been shown, whatever the takes, the cuts or the music do.
    """
    count = max(1, int(count))
    if state["count"] != count:
        state.update(new_deal(), count=count)
    keys = [(int(take), int(p)) for p in pics]
    held = {k: state["held"][k] for k in keys if k in state["held"]}
    for k in keys:
        if k in held:
            continue
        if not state["deck"]:
            state["deck"] = sorted(range(count), key=lambda j: _hash(j + 1, state["round"] + 11))
            state["round"] += 1
        on_screen = set(held.values())
        at = next((j for j, p in enumerate(state["deck"]) if p not in on_screen), 0)
        held[k] = state["deck"].pop(at)
    state["held"] = held
    return [held[k] for k in keys]


_LAYOUTS = [_conveyor, _slam, _carousel, _wall, _tunnel, _burst, _giant, _cascade]


def frame(take, seed, age, feed, n=CARDS):
    """Everything the network needs for one frame.

    take, seed, age: the shot (age in seconds since the cut).
    feed: the hub's channels by name; missing ones read as 0.
    Returns {"cards": [n x {x, y, z, s, rz, pic}], "cam": {x, y, z, roll},
             "ground": {"mode": index into GROUNDS, "a": rgb, "b": rgb, "beat", "kick", "bass"},
             "finish": index into FINISHES, "name": the take's name}
    """
    f = {k: float(feed.get(k, 0.0) or 0.0) for k in FEED}
    which = int(take) % len(TAKES)
    spec = TAKES[which]
    layout = _LAYOUTS[which]
    arrive = 1.0 + 0.5 * math.exp(-9.0 * max(0.0, age)) * math.cos(age * 22.0) - math.exp(-14.0 * max(0.0, age))
    cards = []
    for i in range(n):
        c = layout(i, f, float(seed), n)
        c["s"] *= max(0.0, arrive)
        cards.append(c)
    # the camera leans with the bar, steps in on kicks and tilts on snares
    cam = {
        "x": 0.55 * math.sin(f["bar_pos"] * math.pi * 0.5),
        "y": 0.14 * math.sin(f["bar_pos"] * math.pi * 0.25 + 0.7),
        "z": 4.3 - 0.45 * f["hit_low"] - 0.25 * f["energy"],
        "roll": 2.5 * f["hit_mid"] * (1 if int(f["beat_pos"]) % 2 else -1),
    }
    a, b = spec["palette"]
    if int(f["bar_pos"]) % 2 and which in (1, 3, 6):  # these grounds trade their two colours every bar
        a, b = b, a
    ground = {"mode": GROUNDS.index(spec["ground"]), "a": a, "b": b, "beat": f["beat_pos"], "kick": f["hit_low"], "bass": f["bass"]}
    return {"cards": cards, "cam": cam, "ground": ground, "finish": FINISHES.index(spec["finish"]), "name": spec["name"]}
