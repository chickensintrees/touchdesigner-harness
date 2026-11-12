# Builder for /project1/sc_kinetic_type. Run inside TouchDesigner (see sw_hub/SCENE_BRIEF.md).
# Idempotent: destroys and rebuilds the whole scene.
# see: experiments/sc_kinetic_type/NOTES.md (2026-11-10)
import json
import math
import random

import td

SLUG = 'sc_kinetic_type'
# Nothing here names a folder: files are found through the scene's local/modules/paths (mod.paths).
# see: experiments/sw_hub/SCENE_BRIEF.md "Portability" (2026-11-11)

CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.!-:',?/&#()+>"
# (name, font key for mod.paths.font, characters, row height / font size, baseline offset / font size,
#  cap-height probe, installed family used when <assets>/fonts does not hold the file)
ATLASES = [
    ('archivo', 'archivo', CHARS, 1.06, 0.22, 'H', 'Arial Black'),
    ('barlow', 'barlow', CHARS, 1.06, 0.22, 'H', 'Impact'),
    ('chicago', 'chicago', CHARS, 1.06, 0.22, 'H', 'Tahoma'),
    ('numerals', 'barlow', '0123456789:-.', 0.92, 0.10, '0', 'Impact'),
]
NF = len(ATLASES)
AR, BA, CH, NU = 0, 1, 2, 3
ASIZE = 1280
PAD = 10

W, H = 1280, 720
LW, ROWS, NA = 1024, 3, 7        # layout texture: 3 rows of 1024 texels per attribute, 7 attributes
MAXG = LW * ROWS
NV = 4                           # layout variants per take, chosen by the shot seed

# The words the takes show. An asset pack may replace any of these names with its own
# scenes/sc_kinetic_type/words.json (same names, same kinds of value); build() reads them once through
# LIB['scene_words'] and keeps them in the scene's `words` DAT, which the layout bake reads.
# Capitals only: the atlases hold CHARS. Keep the counts: takes pick PHRASES by index.
DEFAULTS = {
    # the pool the ticker wall, marquee, roll call, counter columns, rings, mosaic and small lists draw from
    "PHRASES": [
        "REAL TIME!", "HERE. NOW. REAL TIME!", "SIGNAL ACQUIRED...", "FEEDBACK LOOP ..... OPEN",
        "PLATE 07: ORIGIN UNRECORDED.", "EVERY FRAME IS MADE NOW. THEN GONE.", "LISTEN WITH YOUR EYES.",
        "NOTHING HERE IS PRERENDERED.", "SOUND IN. PICTURE OUT.", "THE KICK MOVES THE TYPE.", "DO NOT TOUCH",
        "FOUND, NOT MADE.", "PLATE 07", "PLATE 12-B", "CATALOGUE 0047", "SIXTY FRAMES A SECOND, EVERY SECOND.",
        "THIS PICTURE IS RUNNING IN REAL TIME", "THIS PICTURE IS MADE OF SOUND.", "HANDLE WITH BOTH HANDS.",
        "EVERYTHING IS SIGNAL", "OBJECT OF UNKNOWN USE", "PAST. PRESENT. LATER.",
        "CATALOGUE OF UNEXPLAINED OBJECTS", "LOUD. LOUDER. BRIGHT.",
    ],
    # flash cards: one card per variant, shown a word per beat; the two small labels on the rule
    "FLASH_CARDS": ["SOUND IN. PICTURE OUT. HERE. NOW.", "DO NOT TOUCH", "LOUD. LOUDER. BRIGHT.",
                    "LISTEN WITH YOUR EYES."],
    "FLASH_LEFT": "PLATE 07",
    "FLASH_RIGHT": "CATALOGUE 0047",
    # accordion: one word per row, bottom row first, per variant
    "ACCORDION_ROWS": [
        ["NOW."] * 6,
        ["EVERYTHING", "IS", "SIGNAL", "EVERYTHING", "IS", "SIGNAL"],
        ["HERE.", "NOW.", "FEEDBACK!", "HERE.", "NOW.", "FEEDBACK!", "HERE."],
        ["OUT.", "PICTURE", "IN.", "SOUND", "OUT.", "PICTURE", "IN.", "SOUND"],
    ],
    # swiss columns: [typed headline, small header] per variant, and the label right of the header
    "COLUMNS": [
        ["EVERY FRAME IS MADE NOW. THEN GONE.", "FOUND, NOT MADE."],
        ["SIXTY FRAMES A SECOND, EVERY SECOND.", "CATALOGUE OF UNEXPLAINED OBJECTS"],
        ["THIS PICTURE IS RUNNING IN REAL TIME", "PAST. PRESENT. LATER."],
        ["PLATE 07: ORIGIN UNRECORDED.", "FEEDBACK LOOP ..... OPEN"],
    ],
    "COLUMNS_RIGHT": "EXHIBIT 12-B",
    # exploded letters: the sentence per variant, and the footer
    "EXPLODE_SENT": ["HANDLE WITH BOTH HANDS.", "THIS PICTURE IS MADE OF SOUND.", "EVERYTHING IS SIGNAL",
                     "LISTEN WITH YOUR EYES."],
    "EXPLODE_FOOT": "EVERY FRAME IS MADE NOW. THEN GONE.",
    # typewriter: the typed sentence per variant, the huge cropped line scrolling behind, the header
    "TYPE_SENT": ["EVERY FRAME IS MADE NOW. THEN GONE.", "SIXTY FRAMES A SECOND, EVERY SECOND.",
                  "SIGNAL ACQUIRED... FEEDBACK LOOP ..... OPEN", "PLATE 07: ORIGIN UNRECORDED."],
    "TYPE_BACK": "CATALOGUE 0047",
    "TYPE_FOOT": "SIGNAL ACQUIRED...",
    # echo, per variant: [lines, x of the left edge, y of the top, width to fit, stack angle, swing]
    "ECHO": [
        [["LOOP."], -30, 420, 1180, 0.62, 0.5],
        [["DO NOT", "TOUCH"], 250, 580, 1000, 2.6, 0.4],
        [["NOW"], 400, 580, 800, -2.4, 0.6],
        [["REAL", "TIME."], 50, 640, 900, -0.5, 0.45],
    ],
}


def _strings(x):
    """Every text in a words value (numbers, such as the echo tuning, are skipped)."""
    if isinstance(x, str):
        return [x]
    return [z for y in x for z in _strings(y)] if isinstance(x, list) else []


for _k in sorted(DEFAULTS):
    for _s in _strings(DEFAULTS[_k]):
        _bad = [c for c in _s if c != ' ' and c not in CHARS]
        assert not _bad, 'default words use glyphs the atlases do not hold: %r in %r' % (_bad, _s)


def _hex(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# ----------------------------------------------------------------------------------------------
# Layout engine: appends one row of 28 floats per glyph / bar. Columns, in fours:
#   A x, y, size, rot      B char, font, colour, mode     C line, word, idx, rnd     D p0..p3
#   E sx, sy, delay, flags F line centre x, tracking, kick, index in word           G arrival, g1, g2, 0
# Colours: 0 knock-out (ground), 1 ink, 2 accent, 3 third.
# Modes (glyph_vertex.glsl): 0 still, 1 scroll, 2 flash card, 3 typed, 4 roll, 5 exploded, 6 counter
# numeral, 7 accordion, 8 feed bar, 9 cursor, 10 beat lamp, 11 mosaic cell, 12 ring.
# ----------------------------------------------------------------------------------------------
class Lay:
    def __init__(self, adv, cap, seed, kern=None, desc=None, words=None):
        self.adv, self.cap, self.g = adv, cap, []
        self.d = desc                  # the take's Describe words, or None for the scene's own words
        self.w = words or DEFAULTS     # the scene's words (DEFAULTS, or the asset pack's)
        self.kern = kern or [dict() for _ in adv]
        self.rng = random.Random(seed)

    def pool(self):
        """The phrase list a take draws its lines from, and the order to use them in."""
        if self.d:
            return self.d['pool'], list(range(len(self.d['pool'])))     # Describe: in the order written
        order = list(range(len(self.w['PHRASES'])))
        self.rng.shuffle(order)
        return self.w['PHRASES'], order

    def width(self, txt, size, f, track=0.0):
        a, k = self.adv[f], self.kern[f]
        w = sum(a.get(c, a[' ']) for c in txt) + sum(k.get(txt[i:i + 2], 0.0) for i in range(len(txt) - 1))
        return w * size + track * size * max(0, len(txt) - 1)

    def text(self, txt, x, y, size, f=AR, col=1, mode=0, p=(0, 0, 0, 0), align='l', rot=0.0, track=0.0,
             line=0, word=0, idx=0, delay=0.0, ddelay=0.0, flags=0, arr=0, sx=1.0, sy=1.0, twt=0.0,
             kick=0.0, g1=0.0, g2=0.0, cx=None):
        a = self.adv[f]
        w = self.width(txt, size, f, track) * sx
        dx, dy = math.cos(rot), math.sin(rot)
        if align == 'c':
            x, y = x - dx * w / 2, y - dy * w / 2
        elif align == 'r':
            x, y = x - dx * w, y - dy * w
        if cx is None:
            cx = x + w / 2
        iw = 0
        kern = self.kern[f]
        for ci, c in enumerate(txt):
            ad = (a.get(c, a[' ']) + kern.get(txt[ci:ci + 2], 0.0)) * size * sx
            if c == ' ':
                word += 1
                iw = 0
            elif c in a:
                self.g.append([x, y, size, rot, ord(c), f, col, mode, line, word, idx, self.rng.random(),
                               p[0], p[1], p[2], p[3], sx, sy, delay, flags, cx, twt, kick, iw,
                               arr, g1, g2, 0])
                iw += 1
            delay += ddelay
            idx += 1
            x += dx * (ad + track * size * sx)
            y += dy * (ad + track * size * sx)
        return x, word, idx

    def rect(self, x, y, w, h, col=1, mode=0, p=(0, 0, 0, 0), rot=0.0, line=0, word=0, idx=0, delay=0.0,
             flags=0, arr=0, kick=0.0, g1=0.0, g2=0.0):
        self.g.append([x, y, 1, rot, 0, -1, col, mode, line, word, idx, self.rng.random(),
                       p[0], p[1], p[2], p[3], w, h, delay, flags, x + w / 2, 0, kick, 0, arr, g1, g2, 0])

    def marquee(self, txt, x, y, size, f, col, speed, span, rot=0.0, step=0.6, sep='   ', mode=1, p=None, **kw):
        unit = txt + sep
        per = self.width(unit, size, f, kw.get('track', 0.0)) * kw.get('sx', 1.0)
        n = int(math.ceil(span / per)) + 1
        pp = p if p is not None else (speed, per, step, 0)
        kw.setdefault('g1', per)       # the accordion reads its scroll period and speed from g1, g2
        kw.setdefault('g2', speed)
        for k in range(-1, n):
            self.text(unit, x + math.cos(rot) * k * per, y + math.sin(rot) * k * per, size, f, col=col,
                      mode=mode, p=pp, rot=rot, **kw)
        return per

    def ring(self, txt, cx, cy, R, size, f, col, omega, sgn, sep='  +  ', line=0, delay=0.0, flags=0):
        """txt repeated round a circle of radius R (baseline), reading clockwise, turning omega radians a beat."""
        unit = txt + sep
        per = self.width(unit, size, f)
        n = max(1, int(round(2 * math.pi * R / per)))
        # r4_ring_1_a.png: a phrase longer than its circle was squeezed until the letters overlapped. The type
        # is resized so that n repeats close the circle exactly at normal spacing.
        fit = 2 * math.pi * R / (n * per)
        size, per = size * fit, per * fit
        k = 2 * math.pi / (n * per)
        a, kern = self.adv[f], self.kern[f]
        for rep_i in range(n):
            x = rep_i * per
            for ci, c in enumerate(unit):
                if c != ' ' and c in a:
                    self.g.append([cx, cy, size, 0, ord(c), f, col, 12, line, 0, ci, self.rng.random(),
                                   R, -x * k, omega, sgn, 1, 1, delay, flags, cx, 0, 0, 0, 0, 0, 0, 0])
                x += (a.get(c, a[' ']) + kern.get(unit[ci:ci + 2], 0.0)) * size
        return size

    def wrap(self, txt, size, f, maxw):
        lines, cur = [], ''
        for wd in txt.split(' '):
            t = (cur + ' ' + wd) if cur else wd
            if cur and self.width(t, size, f) > maxw:
                lines.append(cur)
                cur = wd
            else:
                cur = t
        if cur:
            lines.append(cur)
        return lines

    def digits(self, x, y, size, counter, n, f=NU, col=1, popk=0.0, **kw):
        """n numerals reading a feed counter, most significant first. Returns the end x."""
        d0 = kw.pop('delay', 0.0)
        for i in range(n):
            x, _, _ = self.text('0', x, y, size, f, col=col, mode=6, p=(counter, n - 1 - i, popk, 0),
                                delay=d0 + 0.07 * i, **kw)
        return x


def col_x(i):
    """Left edge of column i of a 12-column grid with 40 px margins and 16 px gutters."""
    return 40 + i * (1200 + 16) / 12.0


# ------------------------------------ the takes ------------------------------------------------
def t_flash(L, v):
    """Full-bleed flash cards: one word per beat, sized to run off the frame."""
    D = L.d
    ph = (D['cards'] if D else L.w['FLASH_CARDS'])[v]
    words = ph.split()
    n = len(words)
    cap = L.cap[AR]
    for wi, wd in enumerate(words):
        em = L.width(wd, 1, AR)
        size = min(1350.0 / em, 1500.0)
        capx = cap * size
        # r1_take_0_a.png: a long word was a sliver at the frame edge and the card 80% empty. Words are now
        # stretched upward to fill: the whole frame, or two thirds of it from the top or the bottom.
        target = (760.0, 520.0, 760.0, 470.0)[(wi + v) % 4]
        sy = max(1.0, target / capx)
        capy = capx * sy
        if capy >= 700:
            y = 360 - capy / 2
        else:
            y = -0.04 * capy if (wi + v) % 4 == 1 else 720 - 0.96 * capy
        L.text(wd, 640 - em * size / 2, y, size, AR, col=1, mode=2, p=(n, 1, 0, 0), word=wi, kick=36, flags=1,
               twt=0.04, sy=sy)
    L.rect(40, 356, 1200, 5, col=2, mode=8, p=(3, 0.0, 0, 0))
    L.text(D['left'] if D else L.w['FLASH_LEFT'], 40, 372, 30, BA, col=2, track=0.08)
    L.text(D['right'] if D else L.w['FLASH_RIGHT'], 1240, 372, 30, BA, col=2, align='r', track=0.08)
    x = L.digits(40, 318, 30, 0, 3, f=BA, col=2)
    L.text(".", x, 318, 30, BA, col=2)
    L.digits(x + 8, 318, 30, 2, 1, f=BA, col=2)


def t_ticker(L, v):
    """Ticker wall: every row a different phrase, speed and direction, over one huge beat numeral."""
    size = 980.0
    L.digits(640 - 0.5 * L.adv[NU]['0'] * size, 360 - 0.5 * L.cap[NU] * size, size, 2, 1, f=NU, col=3, popk=0.05)
    rows = [16, 9, 12, 18][v]
    rh = 720.0 / rows
    P, order = L.pool()
    for i in range(rows):
        y = i * rh
        f = CH if i % 2 == 0 else BA
        size = rh * (0.60 if f == CH else 0.80)
        sp = L.rng.choice([-1, 1]) * L.rng.choice([40, 70, 110, 160, 240])
        col = 2 if i % 5 == 2 else 1
        if i % 7 == 3:
            L.rect(0, y + 2, 1280, rh - 4, col=1, arr=4, delay=0.02 * i)
            col = 0
        L.marquee(P[order[i % len(order)]], 0, y + rh * 0.27, size, f, col, sp, 1280, sep='  /  ',
                  step=0.8, flags=(3 if i % 3 == 1 else 1) if col == 1 else 0, arr=2, delay=0.02 * i)


def t_marquee(L, v):
    """Diagonal marquee: alternating bands of Archivo on the ground and Barlow on paper, opposed speeds."""
    P, order = L.pool()
    bh, y0 = 132.0, -230.0
    speeds = [170, -240, 90, -130, 300, -80, 210, -170, 120]
    for i in range(9):
        y = y0 + i * bh
        ph = P[order[i]]
        sp = speeds[(i + 2 * v) % 9]
        if i % 2 == 0:
            L.marquee(ph, -100, y + 22, 128, AR, 2 if i == 4 else 1, sp, 1480, sep='  +  ', kick=18, arr=2,
                      delay=0.03 * i)
        else:
            L.rect(-300, y, 1900, bh, col=3, arr=4, delay=0.03 * i)
            L.marquee(ph, -100, y + 24, 122, BA, 0 if i % 4 == 3 else 1, sp, 1480, sep='  /  ', track=0.02,
                      kick=18, arr=2, delay=0.03 * i)


def t_roll(L, v):
    """Roll call: the whole phrase list steps up one line a beat through a white gate."""
    step, size, cy = 62.0, 34.0, 360.0
    n = len(L.d['pool']) if L.d else len(L.w['PHRASES'])
    tot = n * step
    L.rect(0, cy - step / 2, 1280, step, col=1)
    align = ['c', 'l', 'c', 'r'][v]
    x = [640, 150, 640, 1130][v]
    P, order = L.pool()
    if L.d:
        order = order[::-1]      # line 0 is the lowest on screen; Describe reads from the top in the order written
    for i in range(n):
        ph = P[order[i]]
        grow = min(0.6, 1180.0 / L.width(ph, size, CH) - 1.0)      # the gate enlarges a line, but never past the frame
        L.text(ph, x, cy - 0.36 * size + (i - n // 2) * step, size, CH, col=1, mode=4,
               p=(step, tot, cy, 1), align=align, line=i, g1=grow, g2=(70 if i % 2 else -70), cx=x, arr=6,
               delay=0.3 * L.rng.random())
    # the furniture keeps to the side the list leaves empty
    if v == 3:
        L.text(L.d["label"] if L.d else "ROLL CALL", 40, 676, 20, CH, col=1)
        L.digits(40, 30, 20, 1, 4, f=CH, col=1)
        for i in range(4):
            L.rect(40 + i * 26, 640, 18, 18, col=3, mode=10, p=(i, 4, 0, 0))
    else:
        L.text(L.d["label"] if L.d else "ROLL CALL", 1240, 676, 20, CH, col=1, align="r")
        L.digits(1240 - 4 * L.adv[CH]['0'] * 20, 30, 20, 1, 4, f=CH, col=1)
        for i in range(4):
            L.rect(1240 - 96 + i * 26, 640, 18, 18, col=3, mode=10, p=(i, 4, 0, 0))


def t_counter(L, v):
    """Numerals edge to edge: three digits of a feed counter, with red columns of text running up between them."""
    size = 770.0 / L.cap[NU]
    adv = L.adv[NU]['0'] * size
    x0 = 640 - 1.5 * adv
    L.digits(x0, 360 - 385, size, [1, 3, 0, 5][v], 3, f=NU, col=1, popk=0.03, arr=3)
    D = L.d
    P, order = L.pool()
    for k in range(4):
        xb = x0 + k * adv
        if 0 < xb < 1280:
            L.rect(xb - 2, 0, 4, 720, col=2)
        sp = [130, -90, 180, -150][k]
        L.marquee(P[order[k]], xb + 44, 0, 34, BA, 2, sp, 720, rot=math.pi / 2, sep='   /   ', track=0.06)
    L.rect(0, 0, 1280, 16, col=2, mode=8, p=(3, 0, 0, 0))
    L.text((D['label'] if D else ["BEAT", "SIXTEENTH", "BAR", "TIME"])[v], 40, 676, 22, CH, col=2)


def t_accordion(L, v):
    """Accordion: rows of one repeated word; a bulge of height travels through the rows once a bar."""
    sets = L.w['ACCORDION_ROWS']
    if L.d:
        sets = [list(reversed(rows)) for rows in L.d['rows']]      # written top row first; row 0 is the bottom one
    words = sets[v]
    n = len(words)
    D = 120.0
    size = 0.90 * D / L.cap[AR]
    for r, wd in enumerate(words):
        sp = (80 + 35 * r) * (1 if r % 2 == 0 else -1)
        L.marquee(wd, 0, 0.05 * D, size, AR, 2 if r == n // 2 else 1, sp, 1280, sep=' ', mode=7, p=(r, n, D, 0),
                  arr=2, delay=0.04 * r)


def t_columns(L, v):
    """Swiss columns: a two-digit bar number the height of the frame against a typed column of Barlow."""
    main, head = L.w['COLUMNS'][v]
    D = L.d
    if D:
        main, head = D['main'][v], D['head']
    mirror = v % 2 == 1
    size = 650.0 / L.cap[NU]
    dw = 2 * L.adv[NU]['0'] * size
    L.digits((1280 - dw + 96) if mirror else -64, -48, size, 0, 2, f=NU, col=3, popk=0.04, arr=3)
    tx = 40 if mirror else col_x(6)
    tw = 1240 - col_x(6)
    L.rect(tx, 648, tw, 4, col=2, mode=8, p=(1, 0.02, 0, 0))
    L.text(head, tx, 664, 18, CH, col=1)
    L.text(D['right'] if D else L.w['COLUMNS_RIGHT'], tx + tw, 664, 18, CH, col=2, align='r')
    ts = 104.0
    lines = L.wrap(main, ts, BA, tw)
    ntot = sum(len(ln) + 1 for ln in lines) - 1
    idx = 0
    for li, ln in enumerate(lines):
        L.text(ln, tx, 536 - li * ts * 0.92, ts, BA, col=1, mode=3, p=(ntot, 10, 4, 0), idx=idx, line=li)
        idx += len(ln) + 1
    yb = 536 - len(lines) * ts * 0.92 + 40
    L.rect(tx, yb, tw, 2, col=1, arr=4, delay=0.1)
    ls, lstep = (18, 27) if D else (15, 24)      # Describe: the list is there to be read, so it is set larger
    for i in range(6):
        ph = D['list'][i] if D else L.w['PHRASES'][(v * 5 + i * 3 + 1) % len(L.w['PHRASES'])]
        y = yb - 30 - i * lstep
        if y < 84:
            break
        L.text("%02d" % (i + 1), tx, y, ls, CH, col=2, arr=5, delay=0.1 + 0.06 * i)
        L.text(ph, tx + 44, y, ls, CH, col=1, arr=6, delay=0.1 + 0.06 * i, flags=2 if (i == 2 and not D) else 0)
    for i in range(4):
        L.rect(tx + i * 28, 40, 20, 20, col=3, mode=10, p=(i, 4, 0, 0))
    L.text(D["lamps"] if D else "BAR", tx + tw, 40, 22, BA, col=2, align="r", track=0.1)


def t_explode(L, v):
    """Exploded letters: a sentence holds for a bar, then its letters jump to a coarse grid, turned and rescaled."""
    D = L.d
    ph = (D['sent'] if D else L.w['EXPLODE_SENT'])[v]
    size = 150.0
    lines = L.wrap(ph, size, AR, 1130)
    lh = 152.0
    y = 360 + (len(lines) - 1) * lh / 2 - 0.35 * size
    nwords = len(ph.split())
    word = 0
    idx = 0
    sp = L.adv[AR][' '] * size
    for li, ln in enumerate(lines):
        x = 70.0
        for wd in ln.split():
            x, _, idx = L.text(wd, x, y - li * lh, size, AR, col=2 if word == nwords - 1 else 1, mode=5,
                               p=(0, 70, 0.5, 0), line=li, word=word, idx=idx)
            x += sp
            word += 1
    L.text(D['foot'] if D else L.w['EXPLODE_FOOT'], 40, 30, 20 if D else 16, CH, col=1)
    L.digits(1240 - 3 * L.adv[CH]['0'] * 16, 30, 16, 0, 3, f=CH, col=1)


def t_type(L, v):
    """Typewriter: a sentence typed one glyph per sixteenth in Chicago, with a block cursor."""
    D = L.d
    ph = (D['sent'] if D else L.w['TYPE_SENT'])[v]
    L.marquee(D['back'] if D else L.w['TYPE_BACK'], 0, -74, 300, AR, 3, -90, 1280, sep='   ', step=0.3)
    # r1_take_8_a.png: one 112 px line on an empty frame for the first seconds. Now 150 px, filling the
    # frame top to bottom, and the first eight glyphs are already there at the cut.
    size, lh = 150.0, 164.0
    lines = L.wrap(ph, size, CH, 1190)
    ntot = sum(len(ln) + 1 for ln in lines) - 1
    idx = 0
    for li, ln in enumerate(lines):
        y = 560 - li * lh
        L.text(ln, 50, y, size, CH, col=1, mode=3, p=(ntot, 10, 4, 8), idx=idx, line=li, kick=10)
        for j in range(len(ln) + 1):
            L.rect(50 + L.width(ln[:j], size, CH) + 5, y - 0.08 * size, 0.5 * size, 0.9 * size, col=2,
                   mode=9, p=(ntot, 10, 4, 8), idx=idx + j)
        idx += len(ln) + 1
    L.text(D['foot'] if D else L.w['TYPE_FOOT'], 50, 690, 20 if D else 16, CH, col=1)
    L.digits(1230 - 4 * L.adv[CH]['0'] * 16, 690, 16, 3, 4, f=CH, col=1)


def t_mosaic(L, v):
    """Mosaic: a full-frame field of small glyphs, text streaming through it; the cells under a giant feed
    numeral swell and take the ink. No readable headline: text as texture."""
    cols, rows, f, counter, nd, caph, dx, dy = [(48, 27, CH, 2, 1, 770.0, 0, -25), (64, 36, BA, 0, 2, 700.0, 0, 10),
                                                (32, 18, AR, 2, 1, 1500.0, -90, -420), (40, 23, CH, 3, 3, 600.0, 0, 60)][v]
    cell = 1280.0 / cols
    S = caph / L.cap[NU]
    adv = L.adv[NU]['0'] * S
    ox, oy = 640 - 0.5 * nd * adv + dx, dy
    size = cell * {CH: 0.92, BA: 1.25, AR: 0.78}[f]
    stream = '  '.join(L.w['PHRASES']) + '  '
    for r in range(rows):
        if L.d:
            # Describe: each row loops one sentence (a row's text circulates inside the row), top row first
            unit = L.d['rows'][(rows - 1 - r) % len(L.d['rows'])] + '  '
            rowtxt = (unit * max(1, cols // len(unit))).ljust(cols)[:cols]
        for c in range(cols):
            chv = rowtxt[c] if L.d else stream[(r * 13 + c) % len(stream)]
            L.g.append([c * cell, r * cell, size, 0, ord(chv), f, 3, 11, r, cols, c, L.rng.random(),
                        counter, nd, S, ox, 1, 1, 0, 1, c * cell, 0, 0, 0, 0, oy, 0, cell])
    if L.d:
        # d1_take_1.png: the field's small pale letters are hard to read in a still, so Describe adds a caption
        label = L.d['label'][v]
        assert str(cols * rows) in label, 'the mosaic caption states the wrong cell count'
        L.rect(24, 18, L.width(label, 20, CH) + 32, 40, col=0)
        L.text(label, 40, 31, 20, CH, col=1)


def t_rings(L, v):
    """Rings: phrases set round concentric circles, each ring its own size, face and speed, the centre off
    the frame so the type crosses it in arcs."""
    cx, cy = [(1010.0, -40.0), (150.0, 790.0), (640.0, 360.0), (640.0, -1500.0)][v]
    far = max(math.hypot(cx - x, cy - y) for x in (0, 1280) for y in (0, 720))
    near = 1500.0 if v == 3 else (150.0 if v == 2 else 110.0)
    sizes = [58, 150, 40, 100, 214, 64, 124, 36, 176]
    faces = [BA, AR, CH, AR, BA, CH, BA, CH, AR]
    P, order = L.pool()
    R, i = near, 0
    while R < far and len(L.g) < MAXG - 400:
        size, f = sizes[i % 9] * (1.25 if v == 3 else 1.0), faces[i % 9]
        size = min(size, 0.42 * R)                        # r2_ring_1.png: 150 px letters on a 170 px circle collided
        sgn = 1 if i % 2 == 0 else -1
        px = L.rng.choice([70, 110, 160, 230])            # travel along the ring per beat, in pixels
        col = 2 if i % 4 == 1 else (3 if f == CH else 1)
        size = L.ring(P[order[i % len(order)]], cx, cy, R, size, f, col, sgn * px / R, sgn,
                      sep='  /  ' if f != AR else '  +  ', line=i, delay=0.03 * i, flags=1 if col == 1 else 0)
        R += L.cap[f] * size + max(32.0, 0.34 * size)     # room for the kick: neighbours close by 26 px
        i += 1
    if v == 2:
        s0 = 190.0
        L.digits(cx - 0.5 * L.adv[NU]['0'] * s0, cy - 0.5 * L.cap[NU] * s0, s0, 2, 1, f=NU, col=2, popk=0.25)


def t_echo(L, v):
    """Echo: one or two words with a stack of copies behind them, alternately ink and ground, so the offset
    reads as a striped extrusion. The stack is drawn back to front (draw order follows instance id)."""
    lines, x0, ytop, wid, ang, swing = L.w['ECHO'][v]
    D = L.d
    if D:
        lines = D['lines'][v]
    size = min(wid / max(L.width(ln, 1, AR) for ln in lines), 480.0)
    lh = L.cap[AR] * size * 1.16
    n = 26
    for k in range(n - 1, -1, -1):
        col = 2 if k == 0 else (1 if k % 2 == 1 else 0)
        for li, ln in enumerate(lines):
            L.text(ln, x0, ytop - L.cap[AR] * size - li * lh, size, AR, col=col, mode=13, p=(ang, swing, 11.0, 0),
                   line=k, flags=1 if k == 0 else 0)
    L.text(D['foot'] if D else L.w['PHRASES'][(v * 7 + 4) % len(L.w['PHRASES'])], 40, 30, 20 if D else 16, CH, col=1)
    L.digits(1240 - 3 * L.adv[CH]['0'] * 16, 30, 16, 4, 3, f=CH, col=1)


# The cutter counts a scene's visits: take = visit % len(TAKES). Neighbours are chosen to differ most.
# fx: 0 none, 1 an inverted band sweeps each bar, 2 snare flips the card, 3 inversion rises through two bars.
# flip: the seed may mirror the angle. neg: some seeds show the take as a negative.
TAKES = [
    dict(name='flash cards', fn=t_flash, bg='#EDE3C8', ink='#0E0E0E', acc='#DC563D', third='#287E9B', fx=2, neg=1,
         alt=('#287E9B', '#EEE4CC', '#DCB53D', '#192B3B')),
    dict(name='mosaic', fn=t_mosaic, bg='#DCE4C6', ink='#192B3B', acc='#DC563D', third='#8E9C78',
         alt=('#A8322B', '#EEE4CC', '#111111', '#C8594A')),
    dict(name='echo', fn=t_echo, bg='#C8892F', ink='#111111', acc='#EEE4CC', third='#192B3B',
         alt=('#EEE4CC', '#DC563D', '#111111', '#192B3B')),
    dict(name='diagonal marquee', fn=t_marquee, bg='#DC563D', ink='#111111', acc='#DCB53D', third='#EEE4CC',
         angle=-0.2, flip=1, zoom=0.7, jolt=0.035, alt=('#192B3B', '#EEE4CC', '#DCB53D', '#287E9B')),
    dict(name='roll call', fn=t_roll, bg='#000000', ink='#FFFFFF', acc='#FFFFFF', third='#4A4A4A', zoom=0.25,
         alt=('#FFFFFF', '#000000', '#000000', '#BBBBBB')),
    dict(name='counter', fn=t_counter, bg='#EEE4CC', ink='#287E9B', acc='#DC563D', third='#192B3B', fx=3,
         alt=('#192B3B', '#DCB53D', '#EEE4CC', '#287E9B')),
    dict(name='accordion', fn=t_accordion, bg='#0E0E0E', ink='#EDE3C8', acc='#B85779', third='#DCB53D',
         alt=('#EDE3C8', '#0E0E0E', '#DC563D', '#287E9B')),
    dict(name='rings', fn=t_rings, bg='#99AB54', ink='#111111', acc='#EEE4CC', third='#192B3B', jolt=0.02,
         alt=('#0C0C0C', '#DCE4C6', '#DC563D', '#6C7860')),
    dict(name='swiss columns', fn=t_columns, bg='#192B3B', ink='#EEE4CC', acc='#DCB53D', third='#24607A',
         alt=('#EEE4CC', '#192B3B', '#DC563D', '#DDCFAE')),
    dict(name='exploded letters', fn=t_explode, bg='#DCB53D', ink='#111111', acc='#F6F0DC', third='#A8322B',
         alt=('#B85779', '#111111', '#F6F0DC', '#192B3B')),
    dict(name='ticker wall', fn=t_ticker, bg='#10140E', ink='#DCE4C6', acc='#C8892F', third='#34482C', fx=1,
         alt=('#EDE3C8', '#111111', '#DC563D', '#DDD2B4')),
    dict(name='typewriter', fn=t_type, bg='#7E9BB0', ink='#192B3B', acc='#FFFFFF', third='#7190A6',
         alt=('#000000', '#FFFFFF', '#DC563D', '#161616')),
]
NT = len(TAKES)

# Describe mode (SCENE_BRIEF.md "Describe mode and Input", 2026-11-11): the words each take shows when the
# COMP's Describe toggle is on. They say what the viewer is looking at, and every statement is true of the
# scene as built. Capitals only: the atlases hold CHARS. Baked into a second layout texture (layd), so the
# toggle is a Switch TOP and needs no rebuild. describe_words() flattens them for preset.json.
GENERAL = ["EVERY LETTER IS ITS OWN QUAD", "3072 QUADS, ONE VERTEX SHADER", "POSITION IS A FUNCTION OF THE BEAT",
           "NO KEYFRAMES", "28 NUMBERS PER GLYPH, BAKED INTO A TEXTURE", "FOUR FONT ATLASES, 1280 X 1280",
           "TWO OR THREE FLAT COLOURS", "KINETIC TYPE MACHINE"]
DESCRIBE = {
    'flash cards': dict(
        cards=["ONE WORD PER BEAT.", "KINETIC TYPE", "EACH LETTER IS ONE QUAD.", "SNARE FLIPS THE CARD."],
        left="FLASH CARDS", right="KICK JOLTS. SNARE INVERTS."),
    'mosaic': dict(
        rows=["EVERY CELL IS ONE GLYPH QUAD.", "THE NUMERAL COUNTS THE MUSIC.", "CELLS UNDER IT SWELL.",
              "TEXT STEPS A CELL PER EIGHTH.", "KICKS SHAKE THE NUMERAL.", "HI-HATS LIGHT SINGLE CELLS.",
              "NO HEADLINE. TEXT AS TEXTURE.", "ODD ROWS RUN AGAINST EVEN."],
        label=["MOSAIC: %d GLYPH CELLS. THE ONES UNDER THE BIG NUMERAL SWELL." % n for n in (1296, 2304, 576, 920)]),
    'echo': dict(
        lines=[["ECHO."], ["26", "COPIES"], ["KICK"], ["TYPE", "ECHO"]],
        foot="26 COPIES OF ONE WORD. KICKS PUSH THE STACK OUT."),
    'diagonal marquee': dict(
        pool=["KINETIC TYPE", "EVERY LETTER IS A QUAD", "LURCH ON THE BEAT, THEN COAST", "KICKS SCATTER LETTERS",
              "DIAGONAL MARQUEE", "SNARE JOLTS THE ANGLE", "TWO TYPEFACES", "NO KEYFRAMES", "3072 QUADS, ONE SHADER"]),
    'roll call': dict(
        pool=["KINETIC TYPE MACHINE", "ONE LINE STEPS UP PER BEAT", "THE WHITE GATE ENLARGES ITS LINE",
              "INK INSIDE THE GATE IS KNOCKED OUT", "KICKS JOLT ODD AND EVEN LINES APART",
              "EVERY LETTER IS ITS OWN QUAD", "3072 INSTANCES OF ONE RECTANGLE", "ONE VERTEX SHADER PLACES THEM ALL",
              "28 NUMBERS PER GLYPH", "LAYOUTS BAKED INTO A FLOAT TEXTURE", "FOUR FONT ATLASES, 1280 X 1280",
              "SET IN ONE FACE, BLACK AND WHITE ONLY", "ORTHOGRAPHIC CAMERA, ONE UNIT PER PIXEL",
              "POSITION IS A FUNCTION OF THE BEAT", "NO KEYFRAMES", "LINES DECODE FROM RANDOM CAPITALS",
              "TWELVE LAYOUTS, FOUR VARIANTS EACH", "BUILT IN TOUCHDESIGNER"],
        label="ROLL CALL"),
    'counter': dict(
        pool=["THE BAR AT THE FOOT FILLS EACH BEAT", "THREE DIGITS OF A LIVE COUNTER",
              "THE INVERSION LINE RISES OVER TWO BARS", "NUMERALS CUT FROM A 462 PIXEL ATLAS"],
        label=["COUNTING BEATS", "COUNTING SIXTEENTH NOTES", "COUNTING BARS", "COUNTING TIME, 1/100 S"]),
    'accordion': dict(
        rows=[["ACCORDION"] * 6, ["STRETCH", "TO", "FIT", "STRETCH", "TO", "FIT"],
              ["ONE", "BULGE", "TRAVELS", "THE", "ROWS", "EACH", "BAR."],
              ["LOUDER", "MUSIC,", "DEEPER", "BULGE.", "KICKS", "DEEPEN", "IT", "MORE."]]),
    'rings': dict(
        pool=["TYPE SET ON CIRCLES", "EACH RING HAS ITS OWN SIZE, FACE AND SPEED",
              "NEIGHBOURS TURN IN OPPOSITE DIRECTIONS", "RINGS LURCH ON THE BEAT, THEN COAST",
              "KICKS MAKE THE RINGS BREATHE", "EVERY LETTER IS ITS OWN QUAD", "EACH GLYPH RIDES ITS CIRCLE BY ANGLE",
              "TYPE RESIZED SO THE PHRASE CLOSES THE RING", "NO KEYFRAMES", "3072 QUADS, ONE VERTEX SHADER",
              "KINETIC TYPE MACHINE", "ARCHIVO BLACK, BARLOW CONDENSED AND A MONO"]),
    'swiss columns': dict(
        main=["ONE LETTER PER SIXTEENTH NOTE.", "THE BIG NUMBER IS THE BAR.", "A GRID, A RULE, A NUMBER, A LIST.",
              "EVERY LETTER IS ITS OWN QUAD."],
        head="SWISS COLUMNS", right="12-COLUMN GRID", lamps="BEAT IN BAR",
        list=["HEADLINE: BARLOW CONDENSED, 104 PX", "TYPED 4 GLYPHS PER BEAT", "RULE GROWS THROUGH THE BAR",
              "LAMPS: BEAT 1 TO 4", "BIG NUMERALS: BAR NUMBER", "3072 QUADS, ONE SHADER"]),
    'exploded letters': dict(
        sent=["ONE BAR A SENTENCE, NEXT BAR A GRID.", "EVERY LETTER IS ITS OWN QUAD.", "LETTERS JUMP TO A GRID.",
              "KICKS KNOCK THE LETTERS ABOUT."],
        foot="32 CELLS, 8 X 4. A NEW ORDER EVERY CYCLE."),
    'ticker wall': dict(
        pool=["TICKER WALL", "EVERY ROW HAS ITS OWN SPEED AND DIRECTION", "ROWS LURCH ON THE BEAT, THEN COAST",
              "THE BIG NUMERAL IS THE BEAT IN THE BAR", "AN INVERTED BAND SWEEPS ONCE A BAR",
              "HI-HATS LIGHT SINGLE LETTERS", "SOME ROWS CLOSE WHEN THE MUSIC IS QUIET", "A MONO FACE AND BARLOW CONDENSED"]
        + GENERAL),
    'typewriter': dict(
        sent=["TYPED ONE GLYPH PER SIXTEENTH NOTE.", "THE CURSOR IS A QUAD TOO.", "KICKS NUDGE THE TYPED LETTERS.",
              "A SENTENCE, THEN A HOLD, THEN AGAIN."],
        back="TYPEWRITER", foot="TYPEWRITER: 4 GLYPHS A BEAT, BLOCK CURSOR, 150 PX TYPE"),
}

# Input (same section of the brief): what a take does with the picture named by the COMP's Input parameter.
# (screen, line period in pixels, glyph, ground):
#   screen (post.frag): the picture printed as a line screen in two of the take's flat colours, lines thickening
#     where it is bright. 1 inside the ink; 2 inside the third colour (the big numerals); 5 inside the accent
#     (echo's front word); 6 not in the type at all; 0 no screen.
#   glyph (glyph_vertex.glsl): 1 every glyph is sized and coloured by the picture under it; 2 mosaic, a glyph
#     halftone: every cell is sized by the picture under it and the numeral is printed over it in the accent; 0 none.
#   ground: how strongly the same line screen also tints the ground (0 to 1).
INPUT_USE = {
    'flash cards': (1, 9, 0, 0.26), 'mosaic': (0, 0, 2, 0), 'echo': (5, 8, 0, 0.26),
    'diagonal marquee': (1, 8, 0, 0.45), 'roll call': (6, 8, 0, 0.26), 'counter': (1, 9, 0, 0.26),
    'accordion': (1, 8, 0, 0.26), 'rings': (1, 8, 1, 0.26), 'swiss columns': (2, 9, 0, 0.16),
    'exploded letters': (1, 8, 0, 0.26), 'ticker wall': (6, 8, 1, 0.26), 'typewriter': (1, 8, 0, 0.26),
}
for _t in TAKES:
    _t['describe'] = DESCRIBE[_t['name']]
    _t['inp'] = INPUT_USE[_t['name']]


def _flat(x):
    if isinstance(x, str):
        return [x]
    out = []
    for y in (x.values() if isinstance(x, dict) else x):
        out += _flat(y)
    return out


def describe_words(t):
    """A take's Describe words as one flat list, in the order written (for preset.json)."""
    seen, out = set(), []
    for w in _flat(t['describe']):
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


for _t in TAKES:
    for _w in describe_words(_t):
        _bad = [c for c in _w if c != ' ' and c not in CHARS]
        assert not _bad, 'Describe words use glyphs the atlases do not hold: %r in %r' % (_bad, _w)


# ------------------------------------ baking ---------------------------------------------------
def _metrics(scene):
    adv = [dict() for _ in range(NF)]
    kern = [dict() for _ in range(NF)]
    cap = [0.7] * NF
    for r in scene.op('kern').rows()[1:]:
        kern[int(r[0].val)][chr(int(r[1].val)) + chr(int(r[2].val))] = float(r[3].val)
    for r in scene.op('glyphs').rows()[1:]:
        adv[int(r[0].val)][chr(int(r[1].val))] = float(r[2].val)
    for r in scene.op('fonts').rows()[1:]:
        cap[int(r[0].val)] = float(r[5].val)
    return adv, cap, kern


def bake(script_op):
    """Fill one of the Script TOPs ('lay', 'gtab', 'par') from the tables and the TAKES list."""
    import numpy as np
    scene = script_op.parent()
    name = script_op.name
    if name == 'gtab':
        arr = np.zeros((2 * NF, 96, 4), np.float32)
        for r in scene.op('glyphs').rows()[1:]:
            f, code = int(r[0].val), int(r[1].val)
            arr[f, code - 32] = (float(r[3].val), float(r[4].val), float(r[5].val), float(r[6].val))
        for r in scene.op('fonts').rows()[1:]:
            f = int(r[0].val)
            arr[NF + f, 0] = (float(r[1].val), float(r[2].val), float(r[3].val), float(r[4].val))
            arr[NF + f, 1] = (float(r[5].val), 0, 0, 0)
    elif name == 'par':
        arr = np.zeros((NT, 12, 4), np.float32)
        for i, t in enumerate(TAKES):
            arr[i, 0] = (t.get('angle', 0.0), t.get('scale', 1.0), 0, 0)
            alt = t.get('alt', (t['bg'], t['ink'], t['acc'], t['third']))
            for j, k in enumerate(('bg', 'ink', 'acc', 'third')):
                arr[i, 1 + j] = _hex(t[k]) + (1.0,)
                arr[i, 6 + j] = _hex(alt[j]) + (1.0,)
            arr[i, 5] = (t.get('flip', 0), t.get('fx', 0), t.get('neg', 0), 0)
            arr[i, 10] = (t.get('zoom', 0.0), t.get('jolt', 0.0), 0, 0)
            arr[i, 11] = t['inp']
    else:
        describe = name == 'layd'
        adv, cap, kern = _metrics(scene)
        wd = scene.op('words')         # written by build() from DEFAULTS and the asset pack
        words = json.loads(wd.text) if wd is not None and wd.text.strip() else DEFAULTS
        arr = np.zeros((NT * NV * NA * ROWS, LW, 4), np.float32)
        counts = []
        for i, t in enumerate(TAKES):
            for v in range(NV):
                L = Lay(adv, cap, 1000 + i * 17 + v, kern, t['describe'] if describe else None, words)
                t['fn'](L, v)
                counts.append(len(L.g))
                assert len(L.g) <= MAXG, '%s variant %d has %d glyphs, room for %d' % (t['name'], v, len(L.g), MAXG)
                g = np.array(L.g[:MAXG], np.float32).reshape(-1, NA * 4)
                li = i * NV + v
                for a in range(NA):
                    block = np.zeros((MAXG, 4), np.float32)
                    block[:len(g)] = g[:, a * 4:a * 4 + 4]
                    r0 = li * NA * ROWS + a * ROWS
                    arr[r0:r0 + ROWS] = block.reshape(ROWS, LW, 4)
        scene.store('glyph_counts_describe' if describe else 'glyph_counts', counts)
    script_op.copyNumpyArray(arr)


BAKE_CB = '''# Bakes layout / glyph / take tables from build.py (TAKES and the layout functions live there).
def onCook(scriptOp):
    g = {'op': op, 'td': td, '__name__': 'bake'}
    # project.folder, not mod.paths: an edit to the shared paths module must not trigger a 55 ms re-bake
    exec(open(project.folder + '/experiments/' + parent().name + '/build.py', encoding='utf-8').read(), g)
    g['bake'](scriptOp)
    return
'''

SECT_CB = '''# Remembers when the musical section last changed while the scene was cooking: arrivals replay on it.
def onValueChange(channel, sampleIndex, val, prev):
    op('shot0').par.value1 = absTime.seconds
    return
'''

SHOT_CB = '''# Remembers the beat on which the shot began, so typing and flash cards start with the cut.
def onValueChange(par, prev):
    f = op('/project1/sw_hub/feed')
    try:
        b = float(f['beat_pos'].eval())
    except Exception:
        b = 0.0
    import math
    op('shot0').par.value0 = math.floor(b)
    return
'''


def _paths(scene):
    """The paths module the scaffold installed in the scene (it sees the COMP's Assets parameter)."""
    return scene.op('local/modules/paths').module


def _shader(scene, name, fname, x, y):
    d = scene.create(td.textDAT, name)
    d.par.file.expr = "mod.paths.here('shaders/%s')" % fname
    d.par.syncfile = True
    d.text = open(_paths(scene).here('shaders/' + fname), encoding='utf-8').read()
    d.nodeX, d.nodeY = x, y
    return d


def _vecs(o, rows):
    o.seq.vec.numBlocks = len(rows)
    for i, (name, vals) in enumerate(rows):
        getattr(o.par, 'vec%dname' % i).val = name
        for c, v in zip('xyzw', vals):
            p = getattr(o.par, 'vec%dvalue%s' % (i, c))
            if isinstance(v, str):
                p.expr = v
            else:
                p.val = v


def _atlas(scene, k, spec_row):
    """One font atlas: glyph cells packed by advance width at the largest size that fits 1280 x 1280."""
    name, fontkey, chars, rh_k, bo_k, probe, family = spec_row
    t = scene.create(td.textTOP, 'atlas_' + name)
    t.nodeX, t.nodeY = -1500, 600 - k * 150
    # The font file wins when it is there. Without it the atlas is drawn in an installed face, bold
    # (TouchDesigner's default face if that one is missing too), and measured the same way. Bold and
    # names such as Arial Black only work with legacy font selection, so that is switched on with it.
    # A face that is not installed raises a warning in legacy mode, so it is looked for first.
    t.par.fontfile.expr = "mod.paths.font(%r)" % fontkey
    t.par.legacyfontselection = True
    installed = family in t.par.font.menuNames
    t.par.legacyfontselection = False
    if installed:
        t.par.legacyfontselection.expr = "0 if mod.paths.font(%r) else 1" % fontkey
        t.par.bold.expr = "0 if mod.paths.font(%r) else 1" % fontkey
        t.par.font = family
    t.par.legacyparsing = False
    t.par.wordwrap = False
    t.par.smartpunct = False
    t.par.outputresolution = 'custom'
    t.par.resolutionw, t.par.resolutionh = ASIZE, ASIZE
    t.par.fontautosize = 'nofit'
    t.par.fontsizexunit = 'pixels'
    t.par.fontsizex = 100
    t.par.alignx = 'left'
    t.par.aligny = 'bottom'
    t.par.bgalpha = 1
    t.par.format = 'mono8fixed'
    t.par.filtertype = 'mipmap'
    adv = {c: float(t.evalTextSize(c)[0]) / 100.0 for c in chars}
    adv[' '] = float(t.evalTextSize('A A')[0] - t.evalTextSize('AA')[0]) / 100.0
    # kerning pairs (Archivo and Barlow have them, Chicago has none): evalTextSize costs about 7 microseconds
    kern = {}
    for c1 in chars:
        for c2 in chars:
            k = float(t.evalTextSize(c1 + c2)[0]) / 100.0 - adv[c1] - adv[c2]
            if abs(k) > 0.004:
                kern[c1 + c2] = k
    best = None
    fs = 520
    while fs > 40:
        rh = int(math.ceil(fs * rh_k))
        x, row, cells = 0, 0, {}
        for c in chars:
            cw = int(math.ceil(adv[c] * fs)) + 2 * PAD
            if x + cw > ASIZE:
                row += 1
                x = 0
            cells[c] = (x, row * rh, cw)
            x += cw
        if (row + 1) * rh <= ASIZE:
            best = (fs, rh, cells)
            break
        fs -= 2
    fs, rh, cells = best
    bo = int(round(fs * bo_k))
    t.par.fontsizex = fs
    spec = scene.create(td.tableDAT, 'atlas_' + name + '_spec')
    spec.nodeX, spec.nodeY = -1700, 600 - k * 150
    spec.clear()
    spec.appendRow(['x', 'y', 'text'])
    for c in chars:
        x0, y0, cw = cells[c]
        spec.appendRow([x0 + PAD, y0 + bo, c])
    t.par.specdat = spec
    t.cook(force=True)
    # cap height, measured from the rasterised probe glyph
    a = t.numpyArray()
    x0, y0, cw = cells[probe]
    cell = a[y0:y0 + rh, x0:x0 + cw, 0]
    rows = [j for j in range(cell.shape[0]) if cell[j].max() > 0.5]
    cap = (max(rows) + 1 - bo) / float(fs) if rows else 0.7
    return t, adv, cells, (fs, rh, PAD, bo, cap), kern


def build():
    LIB = {'op': op}
    exec(open(td.project.folder + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    scene = LIB['new_scene'](SLUG, 750, -1100)
    pm = scene.op('local/modules/paths')
    if not pm.text.strip():        # a file DAT loads a frame after it is pointed at its file
        pm.text = open(LIB['experiment']('sw_hub', 'paths_module.py'), encoding='utf-8').read()

    # ---- the scene's words: DEFAULTS, with any name the asset pack replaces (read once, here) ----
    W_ = LIB['scene_words'](scene, DEFAULTS)
    words = scene.create(td.textDAT, 'words')
    words.text = json.dumps(W_, indent=1)
    words.nodeX, words.nodeY = -1500, 950

    # ---- font atlases and their tables ----
    glyphs = scene.create(td.tableDAT, 'glyphs')
    glyphs.nodeX, glyphs.nodeY = -1300, 800
    glyphs.clear()
    glyphs.appendRow(['font', 'code', 'adv_em', 'x0', 'y0', 'cellw', 'adv_px'])
    fonts = scene.create(td.tableDAT, 'fonts')
    fonts.nodeX, fonts.nodeY = -1100, 800
    fonts.clear()
    fonts.appendRow(['font', 'fs', 'rowh', 'pad', 'baseoff', 'cap_em', 'name'])
    kerns = scene.create(td.tableDAT, 'kern')
    kerns.nodeX, kerns.nodeY = -1100, 950
    kerns.clear()
    kerns.appendRow(['font', 'a', 'b', 'kern_em'])
    atlases = []
    for k, row in enumerate(ATLASES):
        t, adv, cells, (fs, rh, pad, bo, cap), kern = _atlas(scene, k, row)
        for pair, kv in kern.items():
            kerns.appendRow([k, ord(pair[0]), ord(pair[1]), kv])
        atlases.append(t)
        fonts.appendRow([k, fs, rh, pad, bo, cap, row[0]])
        glyphs.appendRow([k, 32, adv[' '], 0, 0, 0, adv[' '] * fs])
        for c in row[2]:
            x0, y0, cw = cells[c]
            glyphs.appendRow([k, ord(c), adv[c], x0, y0, cw, adv[c] * fs])

    cb = scene.create(td.textDAT, 'bake_cb')
    cb.text = BAKE_CB
    cb.nodeX, cb.nodeY = -1300, 950
    baked = {}
    for j, name in enumerate(('gtab', 'par', 'lay', 'layd')):
        s = scene.create(td.scriptTOP, name)
        for d in list(s.docked):
            d.destroy()
        s.par.callbacks = cb.path
        s.nodeX, s.nodeY = -900 + j * 150, 800
        s.cook(force=True)
        baked[name] = s
    # Describe: the same machine reads a second baked layout texture holding the explaining words
    lay_sw = scene.create(td.switchTOP, 'lay_sw')
    baked['lay'].outputConnectors[0].connect(lay_sw.inputConnectors[0])
    baked['layd'].outputConnectors[0].connect(lay_sw.inputConnectors[1])
    lay_sw.par.index.expr = "int(parent().par.Describe)"
    lay_sw.nodeX, lay_sw.nodeY = -450, 650
    lay_sw.cook(force=True)

    # Input: the picture another scene hands over (blank Input = a black constant that nothing reads)
    inp_none = scene.create(td.constantTOP, 'inp_none')
    inp_none.par.colorr = inp_none.par.colorg = inp_none.par.colorb = 0
    inp_none.par.outputresolution = 'custom'
    inp_none.par.resolutionw, inp_none.par.resolutionh = 16, 16
    inp_none.nodeX, inp_none.nodeY = 0, -300
    # a TOP outside this COMP: reading the scene's own operators would be a cook loop
    INP_OK = ("(lambda o: bool(o) and getattr(o, 'isTOP', False) and not o.path.startswith(parent().path + '/'))"
              "(op(parent().par.Input.eval()) if parent().par.Input.eval() else None)")
    inp_sel = scene.create(td.selectTOP, 'inp_sel')
    inp_sel.par.top.expr = "parent().par.Input.eval() if " + INP_OK + " else 'inp_none'"
    inp_sel.nodeX, inp_sel.nodeY = 150, -300

    # ---- the beat on which the shot began ----
    shot0 = scene.create(td.constantCHOP, 'shot0')
    shot0.par.name0 = 'beat0'
    shot0.par.value0 = 0
    shot0.par.name1 = 'sect0'
    shot0.par.value1 = 0
    ce = scene.create(td.chopexecuteDAT, 'sect_watch')
    ce.par.chop = 'hub'
    ce.par.channel = 'section'
    ce.par.valuechange = True
    ce.par.active = True
    ce.text = SECT_CB
    ce.nodeX, ce.nodeY = 0, 460
    shot0.nodeX, shot0.nodeY = -200, 330
    pe = scene.create(td.parameterexecuteDAT, 'shot_watch')
    pe.par.op = scene.path
    pe.par.pars = 'Shotstart Take Seed'
    pe.par.valuechange = True
    pe.par.active = True
    pe.text = SHOT_CB
    pe.nodeX, pe.nodeY = -200, 460

    # ---- glyph instances ----
    geo = scene.create(td.geometryCOMP, 'glyph_geo')
    for c in geo.children:
        c.destroy()
    quad = geo.create(td.rectangleSOP, 'quad')
    quad.par.sizex, quad.par.sizey = 1, 1
    quad.render = True
    quad.display = True
    geo.par.instancing = True
    geo.par.instancecountmode = 'manual'
    geo.par.numinstances = MAXG
    geo.nodeX, geo.nodeY = -400, 300

    mat = scene.create(td.glslMAT, 'glyph_mat')
    for d in list(mat.docked):
        d.destroy()
    mat.par.vdat = _shader(scene, 'glyph_vertex', 'glyph_vertex.glsl', -600, -300).path
    mat.par.pdat = _shader(scene, 'glyph_pixel', 'glyph_pixel.glsl', -600, -420).path
    samplers = [('sLay', lay_sw, 'nearest'), ('sTab', baked['gtab'], 'nearest'), ('sPar', baked['par'], 'nearest')]
    samplers += [('sF%d' % i, a, 'mipmaplinear') for i, a in enumerate(atlases)]
    samplers.append(('sNum', atlases[NU], 'mipmaplinear'))      # the vertex shader reads the numerals for the mosaic
    samplers.append(('sInp', inp_sel, 'mipmaplinear'))          # and the Input picture, per glyph
    mat.seq.sampler.numBlocks = len(samplers)
    for i, (nm, top, flt) in enumerate(samplers):
        getattr(mat.par, 'sampler%dname' % i).val = nm
        getattr(mat.par, 'sampler%dtop' % i).val = top.path
        getattr(mat.par, 'sampler%dfilter' % i).val = flt
        if flt != 'nearest':
            getattr(mat.par, 'sampler%danisotropy' % i).val = '16x'   # the accordion squashes type to a fifth of its height
    Hb = "op('hub')"
    BP = Hb + "['beat_pos']"
    LB = "(lambda b, b0: b - b0 if b >= b0 else b)(" + BP + ", op('shot0')['beat0'])"
    TAKE = "int(op('shot')['take']) % " + str(NT)
    # the seed picks a layout variant (phrase), and each new musical section moves on to the next one
    LAYI = ("(" + TAKE + ")*" + str(NV) + " + (int(op('shot')['seed']*" + str(NV) + ") + int(" + Hb
            + "['section'])) % " + str(NV))
    ENERGY = "(lambda e: e*e*(3-2*e))(min(1, max(0, (" + Hb + "['energy']-0.33)/0.32)))"
    # arrivals replay when the section changes mid-shot (the layout variant swaps then)
    AGE = "min(op('shot')['age'], absTime.seconds - op('shot0')['sect0'])"
    uniforms = [
        ('uTime', (BP, Hb + "['bar_pos']", LB, AGE)),
        ('uHits', (Hb + "['hit_low']", Hb + "['hit_mid']", Hb + "['hit_high']", Hb + "['pulse']")),
        ('uState', (ENERGY, Hb + "['section']", "op('shot')['seed']", LAYI)),
        ('uCount', (Hb + "['bar_i']", Hb + "['beat_i']", Hb + "['hits_low']", Hb + "['t']")),
        ('uMisc', (Hb + "['bar_pulse']", Hb + "['evolve']", Hb + "['hits_high']", TAKE)),
        ('uInp', ("int(" + INP_OK + ")", 0, 0, 0)),               # 1 while Input names a TOP
    ]
    _vecs(mat, uniforms)
    mat.par.blending = True
    mat.par.srcblend = 'one'
    mat.par.destblend = 'omsa'
    mat.par.postmultalpha = False      # the pixel shader already writes premultiplied weights
    mat.par.depthtest = False
    mat.par.depthwriting = False
    mat.par.cullface = 'neither'
    mat.nodeX, mat.nodeY = -400, -300
    geo.par.material = mat.path

    cam = scene.create(td.cameraCOMP, 'cam')
    cam.par.projection = 'ortho'
    cam.par.orthowidth = W
    cam.par.tx, cam.par.ty, cam.par.tz = W / 2, H / 2, 10
    cam.par.near, cam.par.far = 0.1, 100
    cam.nodeX, cam.nodeY = -400, 0

    render = scene.create(td.renderTOP, 'render')
    render.par.camera = cam.path
    render.par.geometry = geo.path
    render.par.lights = ''
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = W, H
    render.par.format = 'rgba8fixed'
    render.par.antialias = '1x'
    render.par.bgcolorr = render.par.bgcolorg = render.par.bgcolorb = 0
    render.par.bgcolora = 0
    render.nodeX, render.nodeY = 0, 0

    post = scene.create(td.glslTOP, 'post')
    for d in list(post.docked):
        d.destroy()
    post.par.pixeldat = _shader(scene, 'post_frag', 'post.frag', 400, -300).path
    post.par.format = 'rgba8fixed'
    post.par.outputresolution = 'custom'
    post.par.resolutionw, post.par.resolutionh = W, H
    render.outputConnectors[0].connect(post.inputConnectors[0])
    baked['par'].outputConnectors[0].connect(post.inputConnectors[1])
    inp_sel.outputConnectors[0].connect(post.inputConnectors[2])
    _vecs(post, [uniforms[0], uniforms[1], uniforms[2], uniforms[4], uniforms[5]])
    post.nodeX, post.nodeY = 400, 0
    post.outputConnectors[0].connect(scene.op('out1'))
    return scene.path
