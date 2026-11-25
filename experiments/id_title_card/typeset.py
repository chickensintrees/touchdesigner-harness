"""Typesetting for title cards: a phrase laid out on a grid, one layout per take.

Every take is one idea set with two or three colours, at most two type sizes and
a 12-column grid with the same margin on all four sides:

    poster   the title as large as the grid allows, flush left, tight leading
    bleed    one line of capitals as tall as the grid, running off both sides
    credit   a small, widely spaced title between two hairlines, centred
    system   the title in the system face, flush left, on a ruled card
    rows     the title repeated in rows that fill the frame edge to edge

`layout(...)` returns the runs of a take: each run is one line of lettering (or
one solid bar) with its face, size, letterspacing, position and the box its ink
fills. Widths come from the font files themselves (`Font`), so a line can be
sized to a width and its ink, not its metrics box, put on the margin.

Pure Python: used by the title card inside TouchDesigner (layout_td.py) and
tested by tests/test_typeset.py.
"""
import math
import struct

FRAME = (1280, 720)
COLUMNS = 12
GUTTER = 16
MAX_RUNS = 8
MAX_LINES = 4
TAKES = ("poster", "bleed", "credit", "system", "rows")

# font key -> file in an asset pack
FONT_FILES = {
    "bold": "fonts/BarlowCondensed-Bold.ttf",
    "medium": "fonts/BarlowCondensed-Medium.ttf",
    "system": "fonts/ChicagoFLF.ttf",
}

# ground, type, accent (sRGB 0..1), one palette per take
PALETTES = {
    "poster": ((0.937, 0.922, 0.886), (0.067, 0.067, 0.071), (0.898, 0.212, 0.122)),
    "bleed": ((0.106, 0.208, 0.820), (0.949, 0.933, 0.902), (1.000, 0.824, 0.122)),
    "credit": ((0.051, 0.051, 0.059), (0.914, 0.894, 0.847), (0.560, 0.541, 0.494)),
    "system": ((0.957, 0.957, 0.941), (0.063, 0.063, 0.063), (0.063, 0.063, 0.063)),
    "rows": ((0.898, 0.212, 0.122), (0.067, 0.067, 0.071), (0.949, 0.933, 0.902)),
}

DISPLAY_TRACK = -0.012   # large capitals are set tight (em)
LABEL_TRACK = 0.16       # small capitals are set open (em)
SYSTEM_TRACK = -0.03     # the system face is spaced for 12 px; large, it is closed up (em)
LABEL_SIZE = 24
LEAD = 1.14              # baseline to baseline of stacked capitals, in cap heights
# letters whose left or right side is round or pointed hang a little outside the edge,
# so the edge looks straight (share of the type size)
HANG = {"O": 0.014, "C": 0.014, "G": 0.014, "Q": 0.014, "S": 0.008, "A": 0.016, "V": 0.016, "W": 0.014, "Y": 0.016}
SCROLL_STEP = 320.0      # the bleed take moves this far on every beat (px)

TYPE, BAR, TILE = 1, 2, 3  # kinds of run
COLUMNS_OUT = ("text", "font", "size", "track", "px", "py", "kind", "col", "order", "line",
               "x0", "y0", "x1", "y1", "dx", "dtr", "typeon", "span")


# ---- words ------------------------------------------------------------------
def phrases(text):
    """The phrases in a control's text: separated by |, blanks dropped."""
    found = [" ".join(p.split()) for p in str(text).split("|")]
    return [p for p in found if p] or [""]


def pick(text, take):
    """The phrase for a take: they go round in order, so every take has different words."""
    found = phrases(text)
    return found[int(take) % len(found)]


def labels(text):
    """The small lines: separated by /, blanks dropped, at most three."""
    found = [" ".join(p.split()) for p in str(text).split("/")]
    return [p for p in found if p][:3]


def _cost(groups):
    # even line lengths read as one block; a lone short word at the end is the classic bad break
    lengths = [len(" ".join(g)) for g in groups]
    mean = sum(lengths) / len(lengths)
    widow = 3.0 if len(groups) > 1 and lengths[-1] < 0.45 * max(lengths) else 0.0
    return sum((n - mean) ** 2 for n in lengths) + widow * mean


def _splits(words, k):
    if k == 1:
        yield [words]
        return
    for i in range(1, len(words) - k + 2):
        for rest in _splits(words[i:], k - 1):
            yield [words[:i]] + rest


def breaks(phrase, k):
    """The phrase on exactly k lines of similar length (fewer when it has fewer words)."""
    words = str(phrase).split()
    if not words:
        return [""]
    k = max(1, min(k, len(words)))
    return [" ".join(g) for g in min(_splits(words, k), key=_cost)]


def lines(phrase, max_lines=MAX_LINES):
    """Break a phrase into at most max_lines lines of similar length, in reading order."""
    words = str(phrase).split()
    if not words:
        return [""]
    if len(words) <= 3:
        k = min(len(words), max_lines)
    else:
        k = min(max_lines, 3 if len(words) <= 6 else 4)
    return breaks(phrase, k)


def line(phrase, i, max_lines=MAX_LINES):
    """Line i of the stack, or an empty string when the stack is shorter."""
    found = lines(phrase, max_lines)
    return found[i] if 0 <= i < len(found) else ""


# ---- the font file ----------------------------------------------------------
class Font:
    """What a layout needs from a TrueType file: advance widths, side bearings,
    cap height and descent, all as shares of the type size."""

    def __init__(self, path):
        with open(path, "rb") as fh:
            data = fh.read()
        count = struct.unpack(">H", data[4:6])[0]
        tables = {}
        for i in range(count):
            tag, _, off, length = struct.unpack(">4sIII", data[12 + 16 * i:28 + 16 * i])
            tables[tag.decode("latin-1")] = data[off:off + length]
        head = tables["head"]
        self.upm = struct.unpack(">H", head[18:20])[0]
        long_loca = struct.unpack(">h", head[50:52])[0]
        hhea = tables["hhea"]
        self.desc = -struct.unpack(">h", hhea[6:8])[0] / self.upm
        n_metrics = struct.unpack(">H", hhea[34:36])[0]
        hmtx = tables["hmtx"]
        self._adv = [struct.unpack(">H", hmtx[4 * g:4 * g + 2])[0] for g in range(n_metrics)]
        self._cmap = self._read_cmap(tables["cmap"])
        loca, self._glyf = tables.get("loca", b""), tables.get("glyf", b"")
        if long_loca:
            self._loca = struct.unpack(">%dI" % (len(loca) // 4), loca)
        else:
            self._loca = [2 * v for v in struct.unpack(">%dH" % (len(loca) // 2), loca)]
        os2 = tables.get("OS/2", b"")
        cap = struct.unpack(">h", os2[88:90])[0] if len(os2) >= 90 and struct.unpack(">H", os2[0:2])[0] >= 2 else 0
        if cap <= 0:
            box = self._box("H")
            cap = box[3] if box else 0.7 * self.upm
        self.cap = cap / self.upm

    @staticmethod
    def _read_cmap(cmap):
        found = {}
        n = struct.unpack(">H", cmap[2:4])[0]
        for i in range(n):
            platform, _, off = struct.unpack(">HHI", cmap[4 + 8 * i:12 + 8 * i])
            if platform not in (0, 3) or struct.unpack(">H", cmap[off:off + 2])[0] != 4:
                continue
            seg = struct.unpack(">H", cmap[off + 6:off + 8])[0] // 2
            ends = off + 14
            starts = ends + 2 * seg + 2
            deltas = starts + 2 * seg
            ranges = deltas + 2 * seg
            for s in range(seg):
                end = struct.unpack(">H", cmap[ends + 2 * s:ends + 2 * s + 2])[0]
                start = struct.unpack(">H", cmap[starts + 2 * s:starts + 2 * s + 2])[0]
                delta = struct.unpack(">h", cmap[deltas + 2 * s:deltas + 2 * s + 2])[0]
                rng = struct.unpack(">H", cmap[ranges + 2 * s:ranges + 2 * s + 2])[0]
                for code in range(start, min(end, 0x2122) + 1):
                    if rng == 0:
                        gid = (code + delta) & 0xFFFF
                    else:
                        at = ranges + 2 * s + rng + 2 * (code - start)
                        gid = struct.unpack(">H", cmap[at:at + 2])[0]
                        gid = (gid + delta) & 0xFFFF if gid else 0
                    found.setdefault(code, gid)
            break
        return found

    def _gid(self, ch):
        return self._cmap.get(ord(ch), 0)

    def _box(self, ch):
        g = self._gid(ch)
        if g + 1 >= len(self._loca) or self._loca[g + 1] == self._loca[g]:
            return None  # no outline (a space)
        at = self._loca[g]
        return struct.unpack(">hhhh", self._glyf[at + 2:at + 10])

    def _advance(self, ch):
        g = self._gid(ch)
        return self._adv[min(g, len(self._adv) - 1)]

    def advance(self, text):
        """Width of the text from pen start to pen end, without kerning."""
        return sum(self._advance(ch) for ch in text) / self.upm

    def lsb(self, ch):
        """From the pen to the left edge of the letter's ink."""
        box = self._box(ch)
        return box[0] / self.upm if box else 0.0

    def rsb(self, ch):
        """From the right edge of the letter's ink to where the pen ends up."""
        box = self._box(ch)
        return (self._advance(ch) - box[2]) / self.upm if box else 0.0


class PlainFont:
    """Stands in when a font file is missing: every letter half an em wide."""

    cap, desc = 0.7, 0.2

    def advance(self, text):
        return 0.5 * len(text)

    def lsb(self, ch):
        return 0.0

    def rsb(self, ch):
        return 0.0


_FONTS = {}


def font(path):
    """The Font for a file (read once), or a PlainFont when it cannot be read."""
    if path not in _FONTS:
        try:
            _FONTS[path] = Font(path)
        except (OSError, KeyError, struct.error, IndexError):
            _FONTS[path] = PlainFont()
    return _FONTS[path]


# ---- the grid ---------------------------------------------------------------
def column(i, margin):
    """Left edge of column i (0..11) of the 12-column grid."""
    width = (FRAME[0] - 2 * margin - (COLUMNS - 1) * GUTTER) / COLUMNS
    return margin + i * (width + GUTTER)


def span(n, margin):
    """Width of n columns with the gutters between them."""
    width = (FRAME[0] - 2 * margin - (COLUMNS - 1) * GUTTER) / COLUMNS
    return n * width + (n - 1) * GUTTER


class Setter:
    """Sets lines of type: knows the fonts and how wide a text really comes out."""

    def __init__(self, fonts, measure=None):
        self.fonts = fonts                      # key -> Font
        self._measure = measure                 # (key, text) -> width in em, kerning included

    def pen(self, key, text):
        if not text:
            return 0.0
        if self._measure is not None:
            got = self._measure(key, text)
            if got and got > 0:
                return got
        return self.fonts[key].advance(text)

    def ink(self, key, text, track):
        """(width of the ink, left bearing, right bearing) in em, for a letterspacing in em."""
        if not text:
            return 0.0, 0.0, 0.0
        f = self.fonts[key]
        left, right = f.lsb(text[0]), f.rsb(text[-1])
        return self.pen(key, text) + track * (len(text) - 1) - left - right, left, right

    def fit(self, key, text, track, width):
        """The type size at which the ink of the text is exactly `width` wide."""
        ink = self.ink(key, text, track)[0]
        return width / ink if ink > 0 else 0.0

    def run(self, text, key, size, track, x, base, align="left", col=1, order=0.0, line=-1, hang=True, **more):
        """One line of type. x is where its ink starts (left), ends (right) or is centred."""
        f = self.fonts[key]
        ink, left, right = self.ink(key, text, track)
        width = ink * size
        if align == "right":
            x0 = x - width + (HANG.get(text[-1:], 0.0) * size if hang else 0.0)
        elif align == "center":
            x0 = x - 0.5 * width
        else:
            x0 = x - (HANG.get(text[:1], 0.0) * size if hang else 0.0)
        r = {
            "text": text, "font": key, "size": size, "track": track * size,
            "px": x0 - left * size, "py": FRAME[1] - base - f.desc * size,
            "kind": TYPE, "col": col, "order": order, "line": line,
            "x0": x0, "y0": base - f.cap * size, "x1": x0 + width, "y1": base,
            "dx": 0.0, "dtr": 0.0, "typeon": -1, "span": 0.0,
        }
        r.update(more)
        return r


def bar(x0, y0, x1, y1, col=1, order=0.0, **more):
    """A solid bar: a hairline or a block of colour."""
    r = {"text": "", "font": "", "size": 0.0, "track": 0.0, "px": 0.0, "py": 0.0, "kind": BAR, "col": col,
         "order": order, "line": -1, "x0": x0, "y0": y0, "x1": x1, "y1": y1, "dx": 0.0, "dtr": 0.0,
         "typeon": -1, "span": 0.0}
    r.update(more)
    return r


# ---- the takes --------------------------------------------------------------
def _poster(s, title, small, margin, label_track):
    """The title as large as the grid allows: flush left, tight, standing on the bottom margin."""
    w, h = FRAME
    f = s.fonts["bold"]
    lf = s.fonts["medium"]
    label_base = margin + lf.cap * LABEL_SIZE
    rule_y = label_base + 14
    room = (h - margin) - (rule_y + 4 + 28)
    best = None
    for k in (1, 2, 3):
        rows = breaks(title, k)
        by_width = min(s.fit("bold", t, DISPLAY_TRACK, w - 2 * margin) for t in rows)
        by_height = room / (f.cap * (1 + (len(rows) - 1) * LEAD))
        size = min(by_width, by_height)
        if best is None or size > best[0] * 1.02:
            best = (size, rows)
    size, rows = best
    runs = [bar(margin, rule_y, w - margin, rule_y + 4, col=2, order=0.0)]
    pitch = f.cap * size * LEAD
    for i, t in enumerate(rows):
        base = (h - margin) - (len(rows) - 1 - i) * pitch
        runs.append(s.run(t, "bold", size, DISPLAY_TRACK, margin, base, line=i, order=float(i)))
    for j, t in enumerate(small):
        if j == len(small) - 1 and j > 0:
            runs.append(s.run(t, "medium", LABEL_SIZE, label_track, w - margin, label_base, align="right", order=1.0 + j, hang=False))
        else:
            runs.append(s.run(t, "medium", LABEL_SIZE, label_track, column(4 * j, margin), label_base, order=1.0 + j, hang=False))
    return runs


def _bleed(s, title, small, margin, label_track):
    """One line of capitals as tall as the grid; it is wider than the frame and travels through it."""
    w, h = FRAME
    f = s.fonts["bold"]
    lf = s.fonts["medium"]
    text = " ".join(title.split())
    size = (h - 2 * margin) / f.cap
    width = s.pen("bold", text) * size + DISPLAY_TRACK * size * len(text)
    period = max(width + 0.5 * size, float(w))   # two copies follow each other this far apart
    runs = []
    for n in range(2):
        r = s.run(text, "bold", size, DISPLAY_TRACK, margin + n * period, h - margin, line=0, hang=False)
        r["dx"], r["span"] = -1.0, period
        runs.append(r)
    if small:
        note = "   /   ".join(small)
        pad = 14.0
        cap = lf.cap * LABEL_SIZE
        ink = s.ink("medium", note, label_track)[0] * LABEL_SIZE
        y1 = h - margin
        runs.append(bar(margin, y1 - cap - 2 * pad, margin + ink + 2 * pad, y1, col=2))
        runs.append(s.run(note, "medium", LABEL_SIZE, label_track, margin + pad, y1 - pad, col=0, hang=False))
    return runs


def _credit(s, title, small, margin, label_track):
    """A small title, widely spaced, between two hairlines in the middle of a lot of space."""
    w, h = FRAME
    f = s.fonts["bold"]
    lf = s.fonts["medium"]
    track0, track1 = 0.26, 0.36                 # the letterspacing opens slowly while the card is up
    rows = breaks(title, 1 if len(title) <= 16 else 2)
    size = min([56.0] + [s.fit("bold", t, track1, span(8, margin)) for t in rows])
    cap = f.cap * size
    pitch = cap * 1.9
    block = cap + (len(rows) - 1) * pitch
    cy = 0.47 * h                                # the optical centre sits a little above the middle
    top = cy - 0.5 * block
    gap = 36.0
    half = 0.5 * span(4, margin)
    runs = [bar(0.5 * w - half, top - gap - 2, 0.5 * w + half, top - gap, col=2, order=0.0),
            bar(0.5 * w - half, top + block + gap, 0.5 * w + half, top + block + gap + 2, col=2, order=0.0)]
    for i, t in enumerate(rows):
        r = s.run(t, "bold", size, track0, 0.5 * w, top + cap + i * pitch, align="center", line=i, order=1.0, hang=False)
        grow = (track1 - track0) * size
        r["dtr"] = grow
        r["dx"] = -0.5 * grow * (len(t) - 1)
        r["x0"] -= 0.5 * grow * (len(t) - 1)     # the box it fills when fully open
        r["x1"] += 0.5 * grow * (len(t) - 1)
        runs.append(r)
    lcap = lf.cap * LABEL_SIZE
    spots = [top - gap - 2 - 18, top + block + gap + 2 + 18 + lcap, h - margin]
    for j, t in enumerate(small):
        runs.append(s.run(t, "medium", LABEL_SIZE, max(label_track, 0.3), 0.5 * w, spots[j], align="center", order=2.0 + j, hang=False))
    return runs


def _system(s, title, small, margin, label_track):
    """The title in the system face, flush left on a ruled card, typed on a letter at a time."""
    w, h = FRAME
    f = s.fonts["system"]
    small_size = 26.0
    lead = 1.36                                  # mixed case needs room for its descenders
    rows = [t.title() for t in breaks(title, 3)]
    label_base = margin + f.cap * small_size
    rule_y = label_base + 14
    top = rule_y + 2 + 44                        # the title hangs from the rule; the space is left below it
    room = (h - margin - 60) - top
    size = min([168.0] + [s.fit("system", t, SYSTEM_TRACK, span(9, margin)) for t in rows])
    size = min(size, room / (f.cap * (1 + (len(rows) - 1) * lead) + f.desc))
    size = max(8.0, math.floor(size / 8.0) * 8.0)   # this face is drawn on a pixel grid: whole steps only
    runs = [bar(margin, rule_y, w - margin, rule_y + 2, col=1)]
    pitch = f.cap * size * lead
    typed = 0
    for i, t in enumerate(rows):
        runs.append(s.run(t, "system", size, SYSTEM_TRACK, margin, top + f.cap * size + i * pitch, line=i, typeon=typed, hang=False))
        typed += len(t)
    for j, t in enumerate(small):
        t = t.title()
        if j == 0:
            runs.append(s.run(t, "system", small_size, 0.0, margin, label_base, hang=False))
        elif j == 1:
            runs.append(s.run(t, "system", small_size, 0.0, w - margin, label_base, align="right", hang=False))
        else:
            runs.append(s.run(t, "system", small_size, 0.0, margin, h - margin, hang=False))
    return runs


def _rows(s, title, small, margin, label_track):
    """The title repeated in rows that fill the frame; the rows slide against each other on the beat."""
    w, h = FRAME
    f = s.fonts["bold"]
    text = " ".join(title.split())
    for count in (4, 5, 6, 7, 8, 9, 10, 12):
        pitch = h / count
        size = 0.80 * pitch / f.cap
        period = (s.pen("bold", text) + DISPLAY_TRACK * len(text)) * size + 0.42 * size
        if period <= w:
            break
    base = 0.5 * pitch + 0.5 * f.cap * size
    r = s.run(text, "bold", size, DISPLAY_TRACK, 0.21 * size, base, line=0, hang=False)
    # a tiled run has no beat to arrive on and is no single line: those two columns carry
    # the height of a row and the distance from one repeat to the next
    r["kind"], r["order"], r["line"], r["span"] = TILE, pitch, period, period
    return [r]


_LAYOUTS = {"poster": _poster, "bleed": _bleed, "credit": _credit, "system": _system, "rows": _rows}


def take_name(take):
    return TAKES[int(take) % len(TAKES)]


def layout(title, small, take, fonts, measure=None, margin=64.0, label_track=LABEL_TRACK):
    """The runs of a take. `fonts` maps 'bold', 'medium' and 'system' to a Font; `measure`
    (key, text) -> em, when given, is a truer width than the font's own advances (kerning)."""
    s = Setter(fonts, measure)
    words = " ".join(str(title).upper().split()) or " "
    notes = [t.upper() for t in small]
    margin = max(16.0, min(160.0, float(margin)))
    return _LAYOUTS[take_name(take)](s, words, notes, margin, float(label_track))[:MAX_RUNS]


def table(runs):
    """The runs as rows of text for a table: a header, then MAX_RUNS rows (unused ones are blank)."""
    rows = [list(COLUMNS_OUT)]
    blank = bar(0, 0, 0, 0, col=0)
    blank["kind"] = 0
    for i in range(MAX_RUNS):
        r = runs[i] if i < len(runs) else blank
        rows.append([r[c] if isinstance(r[c], str) else ("%d" % r[c] if isinstance(r[c], int) else "%.3f" % r[c]) for c in COLUMNS_OUT])
    return rows


# ---- time -------------------------------------------------------------------
def _ease(x):
    x = min(1.0, max(0.0, x))
    return 1.0 - (1.0 - x) ** 3


def cycle_beats(beat_pos, bars):
    """How many beats into its cycle a card is. A card builds, holds and clears once
    every `bars` bars (four beats each); with 0 bars it stays built: beat 8 of a cycle with no end."""
    if bars <= 0:
        return 8.0
    return float(beat_pos) % (4.0 * bars)


def motion(name, beat_pos, bars, period):
    """The one moving number of a take.

    bleed: how far the line has travelled (px): a step on every beat, eased, done by the half beat.
    credit: how far the letterspacing has opened, 0..1 across the cycle.
    """
    if bars <= 0:
        return 0.0
    if name == "bleed":
        b = float(beat_pos) % (4.0 * bars)        # every cycle starts with the line's first letter on the margin
        return (SCROLL_STEP * (math.floor(b) + _ease((b % 1.0) / 0.5))) % max(float(period), 1.0)
    if name == "credit":
        x = (float(beat_pos) % (4.0 * bars)) / (4.0 * bars)
        return x * x * (3.0 - 2.0 * x)
    return 0.0


def typed(text, start, chars):
    """The part of a line that has been typed so far. start < 0: the line is not typed on."""
    if start < 0:
        return text
    return text[:max(0, int(chars) - int(start))]


def typed_chars(cycle_beat, total_beats):
    """Letters typed so far: one every sixteenth note; the card clears half a beat before its cycle ends."""
    if total_beats <= 0:
        return 9999
    if cycle_beat >= total_beats - 0.5:
        return 0
    return int(cycle_beat * 4.0) + 1


def contrast(a, b):
    """Contrast ratio of two sRGB colours (1..21)."""
    def lum(c):
        lin = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)
