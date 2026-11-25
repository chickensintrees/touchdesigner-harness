"""experiments/id_title_card/typeset.py: how a title card is set on its grid.

These are facts about the layout (margins, sizes, letterspacing, edges), never about
which words are on the card.
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("typeset", ROOT / "experiments" / "id_title_card" / "typeset.py")
typeset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(typeset)

FONTS = ROOT / "assets" / "fonts"
PHRASES = ["GO", "OPEN STUDIO", "STAY TUNED", "WE WILL BE RIGHT BACK", "A VERY LONG PROGRAMME TITLE THAT GOES ON",
           "Tonight At Nine On Channel Nine", "AVOCADO WAVE"]
SMALL = ["REEL 04", "A LIVE SESSION", "2026"]
W, H = typeset.FRAME


@pytest.fixture(scope="module")
def fonts():
    # the pack that ships with the repository answers the system face with its monospace
    return {"bold": typeset.font(str(FONTS / "BarlowCondensed-Bold.ttf")),
            "medium": typeset.font(str(FONTS / "BarlowCondensed-Medium.ttf")),
            "system": typeset.font(str(FONTS / "IBMPlexMono-Medium.ttf"))}


def every(fonts, margin=64.0, small=SMALL):
    for take, name in enumerate(typeset.TAKES):
        for phrase in PHRASES:
            yield name, phrase, typeset.layout(phrase, small, take, fonts, margin=margin)


def type_runs(runs):
    return [r for r in runs if r["kind"] in (typeset.TYPE, typeset.TILE)]


# ---- words ------------------------------------------------------------------
def test_lines_keep_every_word_in_order():
    for phrase in PHRASES:
        for k in (1, 2, 3):
            found = typeset.breaks(phrase, k)
            assert " ".join(found) == phrase and all(found) and len(found) <= k
        assert " ".join(typeset.lines(phrase)) == phrase


def test_long_phrases_break_evenly():
    for phrase in PHRASES[3:6]:
        lengths = [len(x) for x in typeset.lines(phrase)]
        assert max(lengths) <= 2.2 * min(lengths), (phrase, typeset.lines(phrase))


def test_every_take_gets_different_words():
    text = "ONE TWO | THREE ||  FOUR   FIVE "
    assert typeset.phrases(text) == ["ONE TWO", "THREE", "FOUR FIVE"]
    assert [typeset.pick(text, t) for t in range(4)] == ["ONE TWO", "THREE", "FOUR FIVE", "ONE TWO"]
    assert typeset.labels(" a / b //c/ d ") == ["a", "b", "c"]


# ---- the font file ----------------------------------------------------------
def test_font_file_is_read(fonts):
    bold = fonts["bold"]
    assert bold.cap == pytest.approx(0.7) and bold.desc == pytest.approx(0.2)
    assert bold.advance("HAMBURG") == pytest.approx(3.397)        # the sum of the file's own advance widths
    assert bold.lsb("H") == pytest.approx(0.044) and bold.rsb("G") == pytest.approx(0.034)
    assert bold.advance(" ") > 0 and bold.lsb(" ") == 0
    assert fonts["system"].advance("AB") == pytest.approx(2 * fonts["system"].advance("A"))  # a monospace
    plain = typeset.font(str(FONTS / "no-such-font.ttf"))
    assert plain.advance("ABCD") == 2.0                            # a missing file still sets type


# ---- the grid ---------------------------------------------------------------
def test_grid_has_twelve_columns_between_the_margins():
    for margin in (32.0, 64.0, 96.0):
        assert typeset.column(0, margin) == margin
        assert typeset.column(11, margin) + typeset.span(1, margin) == pytest.approx(W - margin)
        assert typeset.span(12, margin) == pytest.approx(W - 2 * margin)


def test_margins_are_respected(fonts):
    """No ink in the margin, on any side, unless the take is one that runs off the frame on purpose."""
    for margin in (40.0, 64.0, 100.0):
        for name, phrase, runs in every(fonts, margin):
            assert 0 < len(runs) <= typeset.MAX_RUNS
            for r in runs:
                if r["kind"] == typeset.TILE or (name == "bleed" and r["line"] == 0):
                    continue
                hang = 0.02 * r["size"]            # round and pointed letters may hang out a little
                assert r["x0"] >= margin - hang - 0.01, (name, phrase, r["text"])
                assert r["x1"] <= W - margin + hang + 0.01, (name, phrase, r["text"])
                assert r["y0"] >= margin - 0.01 and r["y1"] <= H - margin + 0.01, (name, phrase, r["text"])


def test_lines_never_overflow_or_overlap(fonts):
    for name, phrase, runs in every(fonts):
        lines = sorted((r for r in type_runs(runs) if r["line"] >= 0 and r["kind"] == typeset.TYPE and name != "bleed"),
                       key=lambda r: r["y0"])
        for a, b in zip(lines, lines[1:], strict=False):
            assert b["y0"] > a["y1"], (name, phrase)        # a line starts below the baseline of the one above
        small = [r for r in type_runs(runs) if r["line"] < 0]
        for a in small:                                      # small lines keep clear of the title
            for b in lines:
                apart = a["y1"] <= b["y0"] or a["y0"] >= b["y1"] or a["x1"] <= b["x0"] or a["x0"] >= b["x1"]
                assert apart, (name, phrase, a["text"], b["text"])


def test_at_most_two_sizes_and_two_faces_per_take(fonts):
    for name, phrase, runs in every(fonts):
        sizes = {round(r["size"], 2) for r in type_runs(runs)}
        faces = {r["font"] for r in type_runs(runs)}
        assert len(sizes) <= 2 and len(faces) <= 2, (name, phrase, sizes, faces)


def test_scale_is_never_in_between(fonts):
    """The title is either very large or small in a lot of space."""
    for name, phrase, runs in every(fonts):
        title = [r for r in type_runs(runs) if r["line"] >= 0]
        cap = max(r["y1"] - r["y0"] for r in title)
        if name == "credit":
            assert cap <= 0.06 * H, (phrase, cap)
        elif name == "bleed":
            assert cap == pytest.approx(H - 2 * 64.0)
        elif name == "poster" and len(phrase) <= 12:
            assert cap >= 0.25 * H, (phrase, cap)


def test_letterspacing_is_deliberate(fonts):
    for name, phrase, runs in every(fonts):
        for r in type_runs(runs):
            em = r["track"] / r["size"]
            if r["font"] == "bold" and r["size"] >= 100:
                assert em < 0, (name, phrase)               # large capitals are set tight
            if r["font"] == "medium":
                assert em >= 0.1, (name, phrase)            # small capitals are set open
            if name == "credit" and r["line"] >= 0:
                assert em >= 0.2 and r["dtr"] > 0            # and the credit's title opens further


def test_letterspacing_changes_the_width(fonts):
    s = typeset.Setter(fonts)
    tight = s.run("HAMBURG", "bold", 100.0, 0.0, 64.0, 300.0)
    loose = s.run("HAMBURG", "bold", 100.0, 0.1, 64.0, 300.0)
    assert loose["x1"] - loose["x0"] == pytest.approx(tight["x1"] - tight["x0"] + 6 * 10.0)   # six gaps of 0.1 em
    assert s.fit("bold", "HAMBURG", 0.0, 500.0) == pytest.approx(500.0 / (tight["x1"] - tight["x0"]) * 100.0)


def test_stacked_capitals_are_leaded_tight(fonts):
    runs = typeset.layout("WE WILL BE RIGHT BACK", SMALL, 0, fonts)
    lines = [r for r in runs if r["line"] >= 0]
    assert len(lines) >= 2
    cap = lines[0]["y1"] - lines[0]["y0"]
    for a, b in zip(lines, lines[1:], strict=False):
        assert b["y1"] - a["y1"] == pytest.approx(cap * typeset.LEAD)
        assert typeset.LEAD <= 1.2


def test_left_edges_are_optically_aligned(fonts):
    """The ink of every line starts on the margin, not the letter's box; a round letter hangs out slightly."""
    s = typeset.Setter(fonts)
    flat = s.run("HOME", "bold", 300.0, 0.0, 64.0, 400.0)
    round_ = s.run("OPEN", "bold", 300.0, 0.0, 64.0, 400.0)
    assert flat["x0"] == pytest.approx(64.0)
    assert flat["px"] == pytest.approx(64.0 - fonts["bold"].lsb("H") * 300.0)   # the pen starts left of the ink
    assert 0 < 64.0 - round_["x0"] <= 0.02 * 300.0
    right = s.run("2026", "medium", 24.0, 0.16, 1216.0, 80.0, align="right", hang=False)
    assert right["x1"] == pytest.approx(1216.0)
    centre = s.run("TITLE", "bold", 56.0, 0.3, 640.0, 300.0, align="center")
    assert 0.5 * (centre["x0"] + centre["x1"]) == pytest.approx(640.0)


def test_poster_fills_the_grid(fonts):
    """The poster's title is as large as fits: its widest line reaches the right margin or its stack the rule."""
    for phrase in PHRASES:
        runs = typeset.layout(phrase, SMALL, 0, fonts)
        lines = [r for r in runs if r["line"] >= 0]
        rule = next(r for r in runs if r["kind"] == typeset.BAR)
        wide = max(r["x1"] + 0.02 * r["size"] for r in lines) >= W - 64.0   # a line that hangs out left ends as much short
        tall = min(r["y0"] for r in lines) <= rule["y1"] + 28.0 + 1.0
        assert wide or tall, phrase
        assert max(r["y1"] for r in lines) == pytest.approx(H - 64.0)   # and it stands on the bottom margin


def test_rows_fill_the_frame_and_the_repeat_fits_one_picture(fonts):
    for phrase in PHRASES:
        (r,) = typeset.layout(phrase, SMALL, 4, fonts)
        pitch, period = r["order"], r["span"]
        assert H / pitch == pytest.approx(round(H / pitch))            # a whole number of rows
        assert r["x1"] - r["x0"] < period <= W or len(phrase) > 30


def test_table_has_a_row_for_every_run(fonts):
    rows = typeset.table(typeset.layout("OPEN STUDIO", SMALL, 0, fonts))
    assert len(rows) == typeset.MAX_RUNS + 1 and all(len(r) == len(rows[0]) for r in rows)
    kinds = [int(r[rows[0].index("kind")]) for r in rows[1:]]
    assert kinds.count(0) == typeset.MAX_RUNS - len(typeset.layout("OPEN STUDIO", SMALL, 0, fonts))


# ---- colour and time --------------------------------------------------------
def test_palettes_have_three_colours_that_read():
    assert set(typeset.PALETTES) == set(typeset.TAKES)
    for name, (ground, ink, _accent) in typeset.PALETTES.items():
        assert typeset.contrast(ground, ink) >= 4.0, name


def test_motion_is_locked_to_the_beat():
    assert typeset.cycle_beats(37.5, 4) == pytest.approx(5.5)
    assert typeset.cycle_beats(37.5, 0) == 8.0                           # held still: built, never clearing
    # the bleed line steps on each beat and has arrived by the half beat
    assert typeset.motion("bleed", 3.0, 4, 5000.0) == pytest.approx(3 * typeset.SCROLL_STEP)
    assert typeset.motion("bleed", 3.5, 4, 5000.0) == pytest.approx(4 * typeset.SCROLL_STEP)
    assert typeset.motion("bleed", 3.9, 4, 5000.0) == pytest.approx(4 * typeset.SCROLL_STEP)
    assert typeset.motion("bleed", 3.9, 0, 5000.0) == 0.0
    assert typeset.motion("bleed", 16.0, 4, 5000.0) == 0.0                # a new cycle starts from the margin again
    assert typeset.motion("credit", 0.0, 4, 0) == 0.0 and typeset.motion("credit", 15.99, 4, 0) > 0.99
    # typing: a letter every sixteenth, cleared half a beat before the cycle ends
    assert typeset.typed_chars(0.0, 16) == 1 and typeset.typed_chars(1.0, 16) == 5 and typeset.typed_chars(15.6, 16) == 0
    assert typeset.typed("Field", 0, 3) == "Fie" and typeset.typed("Notes", 5, 3) == "" and typeset.typed("Notes", -1, 0) == "Notes"
