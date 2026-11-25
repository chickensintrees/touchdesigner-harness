# id_title_card

## Intent
A title card: a phrase from a control, set on a grid a different way on every take. It works when each take, frozen on any frame, would pass as a piece of title design: one idea, a clear grid, two or three colours, type that is either very large or small in a lot of space.

## How it is built
- `typeset.py` (pure Python, tested by `tests/test_typeset.py`) does the typesetting. It reads advance widths, side bearings and cap height from the font files, and lays each take out on a 12-column grid with the same margin on all four sides. Its result is a list of runs: one line of lettering (or one solid bar) with face, size, letterspacing, position and the box its ink fills.
- The takes, in order:
  - 0 `poster`: the title as large as the grid allows, flush left, leading 1.14 cap heights, standing on the bottom margin; three small lines on a ruled top row. Paper, ink, one red rule.
  - 1 `bleed`: one line of capitals exactly as tall as the grid, wider than the frame, moving one step on every beat; the small lines in a yellow block. Cobalt, paper, yellow.
  - 2 `credit`: a small, widely spaced title between two hairlines, centred a little above the middle; its letterspacing opens slowly over the cycle. Near black, warm white, grey. This is the one take with fades and the film finish.
  - 3 `system`: the title in the system face in mixed case, hanging from a rule, typed on a letter every sixteenth note; from the second bar one line is selected (reversed out of a bar). Two colours.
  - 4 `rows`: the title repeated in rows that fill the frame edge to edge; the rows slide against each other on the beat and one row is picked out. Red, ink, paper.
- At most two type sizes and two faces per take. Large capitals are set tight (-0.012 em), small capitals open (0.16 em, a control). Left edges are aligned by ink, not by the letter's box, and round or pointed letters hang out by up to 0.016 em.
- Faces: Barlow Condensed Bold for titles, Barlow Condensed Medium for small lines, the pack's `chicago` for the system take (the pack that ships with the repository answers that name with IBM Plex Mono).
- In TouchDesigner the layout is the Script DAT `runs` (`layout_td.py`), one row per run. Eight Text TOPs draw the rows full frame; `shaders/card.frag` composes them. A card builds, holds and clears once every `Cycle` bars: lines arrive by masks, wipes and cuts counted in beats, never by wobble.
- Widths are asked of TouchDesigner itself (`evalTextSize` on one small Text TOP per face), so kerning is included.
- `measure_td.py` compares the box the layout predicts for each line with the ink TouchDesigner drew.

## Inputs / outputs
- Output TOP: `out1`, 1280x720.
- Controls: Titles, Small Lines, Take, Bars Until The Card Clears And Builds Again, Margin, Small Line Letter Spacing, Preview.
- Source of truth: `build.py` (rebuilding destroys and recreates the COMP).

## Log
2026-11-23: typography rebuilt after three notes that it looked amateur. What was wrong with the six old takes: every line of the stack was scaled to the block width, so a three-line title had three type sizes and size was an accident of word length; default letterspacing and loose leading; everything centred with nothing to align to and no margins; four faces across six takes, one of them a system serif with faux bold; saturated backgrounds (confetti, sunburst, starburst, tunnel) standing in for composition; the small line mis-lettered on purpose, unreadable on two takes and overrunning its shape on a third. All six were removed, with the mis-lettering.
Measured in TouchDesigner (`measure_td.py`, held still): every small line and every system-face line is drawn within 0.5 px of where the layout puts it; large capitals within 3 px, the difference being the overshoot of round letters above and below flat ones (7 px at the bleed size).
Cook cost 1.3 to 1.7 ms. Not a hub scene (no Shotstart, Describe or Input), so the cutter cannot use it.
Weak: the cycle is counted from the bar count of the track, not from when a take begins, so a take that starts mid-cycle shows a built card until the next cycle. The system take has no cursor. The bleed take needs a title of four letters or more to keep the frame full.
2026-11-19: built. captures/sheet_takes.png.

## Keepers
