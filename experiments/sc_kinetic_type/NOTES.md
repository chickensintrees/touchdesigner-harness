# sc_kinetic_type: kinetic type machine

Built 2026-11-10 in TouchDesigner 2025.33230. COMP `/project1/sc_kinetic_type`, builder `build.py`.

## Intent

A typographic engine in the Swiss poster / broadcast kinetic type tradition. No 3D models, no
centred wordmark. Every glyph is its own instanced quad cut from a font atlas, so letters can be
typed one per sixteenth, slammed in per beat, scrolled per line, stretched, scattered and
re-assembled. Rules, bars and cursors are the same instances with a "solid" flag. Two or three
flat colours per take. Archivo Black and Barlow Condensed against Chicago. The layout system
itself changes between takes, each one a different picture from the same machine.

Everything is stateless: a glyph's position is a function of the feed (`beat_pos`, hits, counters)
and of the shot (`take`, `seed`, `age`), so the cutter can cut to it at any time.

## Technique

- **Atlases.** Four Text TOPs (1280 x 1280, mono) drawn from a `specdat` table: Archivo Black,
  Barlow Condensed Bold, Chicago (50 characters each) and a numerals-only Barlow at 462 px. Cells are
  packed by advance width at the largest font size that fits (186 / 240 / 200 / 462 px). Advances,
  kerning pairs and cap heights are measured from the Text TOP (`evalTextSize`, `numpyArray`) and kept in
  the `glyphs`, `kern` and `fonts` tables.
- **Layouts.** `build.py` holds a small layout engine (`Lay`: `text`, `rect`, `marquee`, `wrap`,
  `digits`) and one function per take. Each glyph or bar is a row of 28 floats (position, size,
  rotation, character, font, colour index, animation mode, line / word / index, mode parameters,
  stretch, arrival, kick). All takes x 4 variants are baked by a Script TOP into one 1024 x 756
  float texture (`lay`). `gtab` holds the glyph rectangles, `par` the per-take palettes and transform.
- **Drawing.** One Geometry COMP, one unit quad, 3072 instances, GLSL MAT. The vertex shader
  (`shaders/glyph_vertex.glsl`) reads its instance's row with `texelFetch` and applies the animation
  mode: scroll, flash card, typed, roll, exploded, counter numeral, accordion, feed bar, cursor, beat
  lamp, plus shared modifiers (tracking on the beat, kick scatter, hat sparkle, arrival after the cut,
  the take's rotation / zoom). An orthographic camera maps pixels 1:1. The pixel shader
  (`glyph_pixel.glsl`) writes palette weights (red ink, green accent, blue third, black-with-alpha
  knock-out) with premultiplied blending, and re-sharpens magnified glyphs at the 50% contour.
- **Palette pass.** `shaders/post.frag` turns weights into the take's colours and does the
  inversions (snare flip, sweeping band, rising split).
- Cost: render about 0.16 ms CPU, post 0.08 ms, GPU under 0.1 ms. The bakes (31 ms) run once.

## Channel-to-visual mapping

| Feed | What it does |
|---|---|
| `beat_pos` | every scroll (lines lurch forward on the beat, then coast), the roll-call step, flash-card word index, typing (4 glyphs a beat), accordion bulge position, red beat-progress bars |
| `beat_pos` (added takes) | ring rotation (lurch and coast), mosaic text stream (a cell per eighth note), echo direction swing (eight beats) |
| `beat_i`, `bar_i`, sixteenths, `t`, `hits_low` | the numerals: giant counters, bar numbers, beat lamps |
| `pulse` | numerals and tracking pop on the beat; accordion rows swell |
| `hit_low` (kick) | letters jolt and turn (flash cards, marquee, exploded sentence, typewriter); accordion bulge deepens; echo stack shoots out; mosaic numeral's glyphs are thrown about; rings breathe against each other and lurch; roll-call lines jolt apart |
| `hit_mid` (snare) | flash card flips to its negative for the hit; marquee angle jolts |
| `hit_high` (hat) + `hits_high` | single glyphs light up in the accent colour (flash cards, ticker wall) |
| `bar_pos` | rule that grows through the bar; inverted band sweeping the ticker wall; exploded letters assemble for a bar and scatter for the next; counter's inversion line rises over two bars |
| `energy` (remapped 0.33 to 0.65) | ticker rows close in quiet passages and open in loud ones; accordion contrast |
| `section` | moves every take on to its next layout variant (another phrase / arrangement) and replays the arrival |
| `evolve` | slow drift of the exploded letters |
| `shot.take` | which of the twelve layouts |
| `shot.seed` | variant (phrase), second palette, negative, mirrored angle, zoom |
| `shot.age` | arrivals in the first 0.3 s: rows slide in, numerals rise, lists decode from random capitals, letters assemble |

## Takes (`TAKES` in build.py; `take % 12`)

Numbering changed in the review pass (2026-11-10 19:35): three takes were added and the order reshuffled so
that neighbours differ most.

0. **Flash cards**: one Archivo Black word per beat, stretched upward to fill the whole frame or two thirds of it; the snare flips it to its negative.
1. **Mosaic**: a full-frame field of small glyphs with text streaming through it; the cells under a giant feed numeral swell and take the ink, and kicks shake the numeral to rubble. No headline.
2. **Echo**: one or two words with 25 copies stacked behind, alternately ink and ground (a striped extrusion); the stack is tight in quiet beats and shoots out on kicks.
3. **Diagonal marquee**: tilted bands of Archivo on the ground and Barlow on paper, zoom and tilt from the seed.
4. **Roll call**: the scene's 24 phrases in 1-bit Chicago stepping through a white gate, a line a beat; kicks jolt odd and even lines apart.
5. **Counter**: three numerals of a feed counter edge to edge, columns of text running up between them.
6. **Accordion**: rows of one repeated word, heights redistributed every frame, type stretched to fit.
7. **Rings**: phrases set round concentric circles, each ring its own size, face, speed and direction, centre off the frame (or in it, or far below it so the type arches).
8. **Swiss columns**: a frame-high bar number against a typed Barlow headline, rule, numbered list.
9. **Exploded letters**: a sentence holds for a bar, then every letter jumps to its own cell of a specimen grid.
10. **Ticker wall**: 9 to 18 rows of Chicago and Barlow at opposed speeds over one huge beat numeral.
11. **Typewriter**: a sentence typed a glyph per sixteenth in 150 px Chicago with a block cursor, filling the frame, over a huge cropped catalogue number.

Each has a second palette (seed), four layout variants (seed + section), and some have a mirrored or
zoomed form. Captures: `captures/take_<n>.png` and `captures/take_<n>_alt.png` (another seed: other
palette and variant), sheets `captures/takes_sheet.png` and `captures/takes_alt_sheet.png`.

## Describe mode and Input (2026-11-11)

Both are parameters on the COMP (the scaffold adds them). Off and blank, the scene is as it was: the scene's own
layouts baked by this build.py are equal, glyph for glyph, to those of the build before this work (compared in
TouchDesigner against commit 08710bf for all 12 takes x 4 variants), and both shaders skip the Input code
unless `uInp` is 1.

**Describe.** `DESCRIBE` in build.py holds each take's explaining words beside `TAKES`; `Lay.d` hands them to
the take's layout function, which uses them wherever it used one of the scene's own phrases. They are baked into a second
layout texture `layd`, and `lay_sw` (Switch TOP, index = Describe) feeds the shader, so the toggle needs no
rebuild (0.05 ms). Capitals only, because the atlases hold 50 characters; an assert at import rejects any
other glyph. `python words.py` mirrors them into preset.json (`--check` says whether it is in step). What each
take shows (captures `describe_take_<n>.png`, sheet `describe_sheet.png`):

0. Flash cards: a sentence a word per beat ("ONE WORD PER BEAT.", "EACH LETTER IS ONE QUAD.", "SNARE FLIPS THE
   CARD.", or "KINETIC TYPE"), labels "FLASH CARDS" and "KICK JOLTS. SNARE INVERTS.".
1. Mosaic: eight short sentences looping in the rows ("EVERY CELL IS ONE GLYPH QUAD.", "TEXT STEPS A CELL PER
   EIGHTH." ...) and a caption "MOSAIC: 920 GLYPH CELLS. THE ONES UNDER THE BIG NUMERAL SWELL." with the
   variant's true cell count (asserted).
2. Echo: "ECHO." / "26 COPIES" / "KICK" / "TYPE ECHO", footer "26 COPIES OF ONE WORD. KICKS PUSH THE STACK OUT.".
3. Diagonal marquee: nine facts, one per band ("LURCH ON THE BEAT, THEN COAST", "SNARE JOLTS THE ANGLE" ...).
4. Roll call: eighteen facts about the machine, read from the top in the order written.
5. Counter: label says which counter the numerals show ("COUNTING BEATS", "COUNTING SIXTEENTH NOTES", "COUNTING
   BARS", "COUNTING TIME, 1/100 S"); the vertical columns carry four facts.
6. Accordion: one word a row, read down the rows ("ONE BULGE TRAVELS THE ROWS EACH BAR.").
7. Rings: twelve facts, one per ring.
8. Swiss columns: a typed headline ("ONE LETTER PER SIXTEENTH NOTE." ...), header "SWISS COLUMNS / 12-COLUMN
   GRID", a six-line list of specifics set at 18 px instead of 15, lamps labelled "BEAT IN BAR".
9. Exploded letters: a sentence ("LETTERS JUMP TO A GRID." ...), footer "32 CELLS, 8 X 4. A NEW ORDER EVERY CYCLE.".
10. Ticker wall: sixteen facts, one per row.
11. Typewriter: a typed sentence ("THE CURSOR IS A QUAD TOO." ...), "TYPEWRITER" behind, a footer of specifics.

**Input.** `inp_sel` (Select TOP) reads the TOP named by `Input`, or the black `inp_none` when the parameter is
blank, names nothing, names something that is not a TOP, or names an operator inside this COMP (a cook loop).
`uInp` is 1 only in the first case. `INPUT_USE` in build.py says what each take does with the picture (baked
into `par`, column 11):

- **Line screen** (`post.frag`): the picture is printed as horizontal lines in two of the take's flat colours,
  thicker where it is bright, hopping one line a beat and swelling on kicks. Inside the ink for flash cards,
  marquee, counter, accordion, rings, exploded letters and typewriter; inside the big numerals for Swiss
  columns; inside the front word for echo; and behind the type, fainter, in all of those and in roll call and
  ticker wall.
- **Per glyph** (`glyph_vertex.glsl`, sampler `sInp`): rings and ticker wall shrink and recolour every letter
  by the picture under it. Mosaic becomes a halftone made of letters: each cell's size follows the picture,
  and the numeral only turns the bright cells it covers to the accent and shakes them on kicks.

Every take accepts the input. Captures with `/project1/sw_testcard/out1`: `input_take_<n>.png`, sheet
`input_sheet.png`. Strongest: counter, flash cards, exploded letters, marquee, typewriter, Swiss columns.

## Assets (2026-11-11)

Nothing in this folder names a folder on a machine. The scene's own files are found with
`mod.paths.here(...)` (the three shader DATs; `bake_cb` reads `build.py` through `project.folder`); the fonts with
`mod.paths.font(...)`. It uses no models, pictures or music of its own. From `<assets>/`:

| File | Used for | Without it |
|---|---|---|
| `<assets>/fonts/ArchivoBlack-Regular.ttf` | atlas `atlas_archivo` (the heavy display face) | Arial Black, if installed |
| `<assets>/fonts/BarlowCondensed-Bold.ttf` | `atlas_barlow` and `atlas_numerals` (condensed face, big numerals) | Impact, if installed |
| `<assets>/fonts/ChicagoFLF.ttf` | `atlas_chicago` (lists, labels, typewriter, roll call) | Tahoma Bold, if installed |

If the stand-in face is not installed either, the atlas is drawn in TouchDesigner's default face (Verdana
here), regular weight. Nothing precomputed is committed: `build.py` draws the four atlases and measures
advances, kerning pairs and cap heights from whatever face the Text TOP ends up with, then bakes the layouts
from those measurements, so the layouts fit the stand-in faces too. That measuring happens at build time:
after changing the `Assets` parameter (or adding or removing the fonts), run `build.py` again. The saved
`.tox` holds the measurements of the faces it was built with.

## Words (2026-11-11)

Everything the takes say with Describe off sits in one dict, `DEFAULTS`, at the top of build.py: the 24
`PHRASES` the pooled takes draw from, the flash cards and their two labels, the accordion rows, the Swiss
headlines and headers, the exploded and typed sentences, the typewriter's back line and header, and the echo
rows (words with their placement and angle, because that tuning follows the words). `build()` reads it once
through `LIB['scene_words']` and writes the result as JSON into the scene's `words` DAT; the Script TOP bake
reads that DAT, so the baked layouts are those of the pack the scene was built on. An asset pack replaces any
of the names with its own `scenes/sc_kinetic_type/words.json` (same names, same kinds of value, same counts:
takes pick phrases by index). An assert at import rejects default words that use a glyph outside `CHARS`.
Describe words are not part of this: they describe the machine and stay in `DESCRIBE`.

## Log (newest first)

- **23 Generic words** (2026-11-11). The defaults in build.py are now generic (real-time picture-making and
  a catalogue of unexplained objects); the words the scene was first made with live in a private pack's
  `scenes/sc_kinetic_type/words.json`. With that file, all 12 takes x 4 variants, Describe off and on, lay
  out glyph for glyph as the build.py of the commit before (96 of 96 layouts equal, 49664 rows, compared in
  TouchDesigner with the same font tables; the same comparison with the generic defaults differs, so it can
  fail). The echo row "NOW" is set narrower than the three-letter word it replaces (fit width 800, was 900):
  at 900 its W left the frame (`gen_t02_s1.png`). Captures: `ref_t<take>_s<k>.png` before, `gen_*`, `g2_*`
  and `g3_*` on the shipped pack, `prv_t<take>_v<variant>.png` after on the private pack.
  The scene as found was stale: its glyph tables were those of the shipped pack's mono face while its atlas
  showed the private pack's Chicago (the Assets parameter had been changed without a rebuild), so Chicago's
  wide letters were cut off (`ref_t04_s0.png`). Changing `Assets` needs a rebuild: the font tables and both
  layout textures are measured at build time.
- **22 Portability** (2026-11-11 05:57). No folder literals left in build.py, rebuild.py, the snapshot or
  the .tox: file parameters are `mod.paths` expressions. With the real fonts the rebuilt scene is the same
  data as before the change: the four atlases, `lay`, `layd`, `gtab`, `par` and the `glyphs`, `kern` and
  `fonts` tables have the same MD5 as in the scene built by the previous build.py (compared in
  TouchDesigner). Captures: `p0_take_<n>.png` before, `p1_take_<n>.png` and `p3_take_<n>.png` after (sheets
  `p0_sheet.png`, `p1_sheet.png`, `p3_sheet.png`, the last two with Describe on take 8 and the test card as
  Input on take 5). With `Assets` pointed at the empty `captures/_noassets`: no errors, all twelve takes,
  Describe and Input captured (`p2_noassets_take_<n>.png`, `p2_noassets_sheet.png`). First try used the
  Text TOP's `bold` toggle on Verdana and Tahoma: it does nothing unless `legacyfontselection` is on, and
  the heavy display takes came out in thin Verdana. Legacy selection also offers Arial Black by name, but
  warns when a named face is not installed, so build.py looks in the menu first.
- **21 Finish of the Describe / Input work** (fourth builder, 2026-11-11 05:15). The third builder was cut off
  part-way and left no notes; its Describe words and the line screen were sound and are kept. Fixed or
  finished here: roll call listed its facts bottom to top (now top to bottom); "CHICAGO, 34 PIXELS" was not
  true once the seed zooms the take (now "SET IN CHICAGO, BLACK AND WHITE ONLY"); words.py still expected the
  old one-number Input table and would have raised KeyError; an Input naming the scene's own out1 was
  accepted (now refused). Final sets after a clean rebuild: `describe_take_<n>.png`, `input_take_<n>.png`,
  `off_take_<n>.png` (Describe off, Input blank) and their three sheets.
- **20 Input.** Mosaic as found used the picture as a hard mask (luminance cut at 0.3): of the test card only
  a few cells along the letters showed, and its saturated disc vanished. Tried the numeral swelling its cells
  on top of the picture: the numeral hid the picture. Now cell size follows the picture continuously
  (luminance mixed with a quarter of the brightest channel) and the numeral only colours bright cells. The
  ground tint became a per-take number: marquee 0.45 (at 0.26 the card was a ghost behind the bands), Swiss
  columns 0.16 (it had none, so only the slice of picture inside the two numerals showed).
- **19 Describe.** All 12 takes x 4 variants captured and read at 1280 x 720. The 20 px Chicago footers and
  the 18 px list are legible. Typed takes need about two bars before the whole sentence is on screen.

- **18 Review pass hand-off** (second builder, 2026-11-10 19:35). Final rebuild from build.py, all 12
  takes captured twice with different seeds (`takes_sheet.png`, `takes_alt_sheet.png`), hero is
  `feed_echo_kick.png` (echo, hit_low 0.96). The first pass of those captures ran across the track's loop
  point (t 245 to 0): nothing broke, counters read 000 before the first beat.
- **17 Echo take** (new, mode 13). 26 copies of a word drawn back to front, alternately ink and
  ground, offset along a direction that swings over eight beats; spread follows energy, pulse and
  kick. `r4_sheet.png` first version (word too small, mid-frame), `take_2.png`, `r5_echo_1.png`,
  `feed_echo_kick.png` (hit_low 0.96: trail three times as long as in `take_2.png`).
- **16 Rings take** (new, mode 12, `Lay.ring`). `r2_ring_1.png`: 150 px letters on a 170 px circle
  collided, so size is capped at 0.42 R. `r4_ring_1_a.png`: a phrase longer than its circle was squeezed
  until letters overlapped, so type is resized for a whole number of repeats. `feed_rings_kick.png`
  first version: kick radius change of 4.5% made outer rings run into each other; now 13 px plus a
  lurch along the circle.
- **15 Mosaic take** (new, mode 11). The vertex shader samples the numerals atlas at each cell centre
  (sampler `sNum`), reads its character from a neighbouring instance so text streams along the rows,
  and draws word spaces inside the numeral as solid blocks (`r2_dbg.png` had holes there).
  `feed_mosaic_kick.png` (bar 41, hit_low 0.9: the numeral's glyphs thrown about, hats red).
  First arrival grew the field from nothing, which left the frame empty for 0.4 s at every section
  change (seen in the first `feed_mosaic_kick.png`); it is now a shock ring of swollen glyphs
  (`feed_mosaic_section.png`).
- **14 Section changes replay the arrival.** `sect_watch` (CHOP Execute on the hub's `section`) stamps
  `shot0.sect0`; the shader's age is the smaller of shot age and time since that stamp. The mid-shot
  layout swap now arrives instead of popping.
- **13 Review of the nine takes as found** (`r1_sheet.png`, two captures each). Flash cards were the
  weakest: a long word was a sliver at the frame edge with 80% empty cream (`r1_take_0_a.png`). Words
  are now stretched upward to fill (`r3_take_0_b.png`). Typewriter was one 112 px line on an empty
  frame for seconds (`r1_take_8_a.png`): now 150 px, four lines, eight glyphs present at the cut.
  Roll call was cropped by its zoom (`r1_take_3_b.png`): zoom range halved, kick jolt added.

- **12 Final rebuild from build.py**, checks, tox, snapshot, hero (`captures/hero.png`, counter in its
  navy / yellow palette). See "State at hand-off" below for the exact check output.
- **11 Faster slam.** `feed_flash_snare.png` caught the flash card on the beat itself: frame flipped
  by the snare but still empty, because every letter started below the frame. The first letter now
  starts 35% in and the stagger is 0.02 beats. Roll-call lines decode from random capitals
  (`feed_roll_arrival.png`); the gate's enlargement is capped so long lines stay inside the frame.
- **10 Feed evidence** (`captures/feed_sheet.png`): snare flips the card (`feed_flash_snare.png`,
  hit_mid 0.89); a hat turns the Y red (`feed_flash_hat.png`, hit_high 0.52); a kick knocks the
  sentence about (`feed_explode_kick.png`, hit_low 0.79); the off bar is the grid
  (`feed_explode_grid.png`); rows sliding in 0.14 s after the cut (`feed_ticker_arrival.png`).
- **09 All takes captured** in both palettes (`takes_sheet.png`, `takes_alt_sheet.png`). They differ at a
  glance. Seen: roll-call gate line ran off both edges (fixed in 11).
- **08 Kerning, anisotropy.** `d_5.png`: squashed accordion rows were blurred (mipmap level chosen by
  the squashed axis). Sampler anisotropy 16x and a sharpening test on the more magnified axis fixed it.
  `d_3.png`: roll-call letters looked badly spaced; the cause was my own kick scatter on 34 px text, not
  the font (Chicago has no kerning pairs). Removed the scatter there. Archivo and Barlow do have
  kerning (T. is -0.15 em): measured all pairs and applied them.
- **07 Exploded letters to a grid.** First version scattered to hashed positions: a heap in the middle
  (`a_take_7.png` and a direct view). Now each letter takes its own cell of an 8 x 4 grid through a
  permutation that changes every cycle, a few at 2.3x (`c_explode_grid.png`). Reads as a type specimen.
- **06 Second palettes, zoom, jolt, section variants, energy rows** added; `sheet_b.png`, `sheet_b2.png`.
- **05 Edge quality.** Magnified Archivo had stair-steps on diagonals (the W in a direct view).
  Four taps 0.6 texel apart before the threshold smooth them; corners round by about a texel.
- **04 Nine takes** written in one go (`a_take_0..8.png`). All drew first time. Ticker numeral too faint.
- **03 Blending.** Small red text punched cream boxes out of the black letters: `destblend` menu name
  is `omsa`, not `oneminussrcalpha`, and `postmultalpha` must be off for premultiplied output.
- **02 Sampler filter** menu name is `mipmaplinear`; `mipmap` silently left it at nearest and the
  magnified S was blocky.
- **01 Core mechanism**: atlas, baked layout texture, instanced quads, flash-card take
  (`01_flash_first.png`).

## State at hand-off (2026-11-10 19:35, review pass)

- `tdh.errors`: `[]`.
- `tdh.check('experiments/sc_kinetic_type/checks.json')` after the final rebuild: run 1 FAIL on cook_budget
  only (15.3 ms, the one-off bakes), run 2 **PASS** (0.53 ms), run 3 **PASS** (0.47 ms).
- Steady cost read from the operators with the mosaic (densest take) showing: render 0.17 to 0.24 ms CPU,
  glyph_mat 0.09, post 0.08 to 0.09; GPU render 0.04 to 0.3, post 0.03 to 0.04. One-off: lay 44 ms.
- `sc_kinetic_type.tox` and `snapshot/network.json` written; `Preview` off; Take 0, Seed 0.
- Not tested: the scene under the cutter (Take, Seed and Shotstart were set by hand).

## State at hand-off (2026-11-11 05:16, Describe / Input)

- `tdh.errors`: `[]`, also with Describe on and Input set.
- `tdh.check`: run 1 pending (first sample), run 2 FAIL on cook_budget only (17.9 ms while other scenes were
  cooking: render and post read 6 and 5 ms CPU for that sample), run 3 **PASS** (0.64 ms).
- Steady cost with Describe on and the test card as Input: render 0.24 ms CPU, post 0.14, glyph_mat 0.12,
  inp_sel 0.03, lay_sw 0.01; GPU 0.05 each. One-off: lay and layd about 50 ms each at build.
- tox and snapshot rewritten; Describe off, Input blank, Preview off.
- Captures `d1_*`, `i1_*`, `i2_*`, `s1_*` are the cut-off builder's working files, kept but superseded.

## State at hand-off (2026-11-11 05:59, portability)

- `tdh.errors`: `[]` with the real fonts and with `Assets` pointed at an empty folder, also with Describe on
  and Input set in both states.
- `python -m pytest -q tests/test_portable.py -k sc_kinetic_type`: `1 passed, 47 deselected`.
- `tdh.check` after the final rebuild: run 1 **PASS** (0.18 ms, but only 1 operator was active in that
  sample), run 2 FAIL on cook_budget only (16.4 ms, 8 operators active, none of them a bake: other scenes
  were building), run 3 **PASS** (0.60 ms, 8 operators active).
- An earlier check failed at 78 ms because the shared `experiments/sw_hub/paths_module.py` was edited at
  that moment and `bake_cb` then reached build.py through `mod.paths`, so the layouts re-baked. `bake_cb`
  now uses `project.folder` and does not depend on that module.
- tox and snapshot rewritten; Assets blank, Describe off, Input blank, Preview off, Take 0, Seed 0.

## What is weak, honestly

- Without the font files: Arial Black, Impact and Tahoma Bold stand in. It is still a poster machine and
  every take works, but the contrast between a pixel face (Chicago) and two poster faces is gone: Tahoma
  Bold is an ordinary sans, so roll call and the typewriter lose their 1-bit character, and Impact's
  numerals are narrower and blunter than Barlow's. The case where those three are not installed either
  (everything in regular Verdana) was not built or captured; the nearest thing seen was the first try in
  log 22, with regular Verdana and Tahoma beside Impact: thin, readable, dull.
- The .tox opened on a machine without the fonts, and not rebuilt, draws stand-in faces into cells measured
  for the real ones: letters will be spaced for the wrong widths until build.py is run.
- Describe: flash cards and the typed takes show a sentence over time, so a still holds one word or half a
  sentence. Marquee, rings and ticker lines are cropped by the frame at any instant and are read as they pass.
  Mosaic's row sentences are scrambled where rows run against each other inside the numeral; only its caption
  reads cleanly in a still. Accordion's squashed rows are unreadable until the bulge reaches them.
- Describe with Input together: mosaic's words still say the cells under the numeral swell, but with an Input
  it is the picture that sizes them.
- Describe after a section change: the Swiss list and the roll call decode from random capitals for up to
  0.6 s, so a capture taken then shows gibberish in the last lines.
- Input: mosaic is a coarse halftone (26 to 40 px cells): the test card's disc and the mass of its words show,
  the words are not readable in the 32-column variant. Roll call only carries the picture as a faint screen
  behind the list. Echo's screen fights its own stripes. The screen follows brightness only; the picture's
  colours are replaced by the take's palette, by design.
- Input was tested with the test card only, not with another scene's out1.
- Magnified type is reconstructed from a 186 px atlas by thresholding, not a true distance field.
  At 4x and more corners are slightly rounded. Fine in motion, visible in a still.
- Chicago is drawn from the vector font, so it is not the pixel-exact bitmap, and at 15 px (the list in
  Swiss columns) it is soft.
- The snare flip on flash cards is a full-frame inversion, several times a bar in busy passages: a
  strobe. Set that take's `fx` to 0 if it is too much.
- The flash card's small red furniture is hard to read where it crosses the letters.
- Roll call is still the quietest take (1-bit, no accent).
- Exploded letters in its grid state overlaps its 2.3x letters into a heap (`take_9.png`); it reads as
  collage, not as a specimen sheet.
- Echo is a word in the middle of the frame, large and cropped in two variants but still one subject.
- Mosaic in its 32-column Archivo variant swells into a blob for 0.3 s when the shock ring passes.
- Section-change arrivals blank parts of Swiss columns and the lists for up to 0.3 s (decode, rise).
- Motion was judged from stills and event-triggered captures, never from a recorded clip.

## Next

- A real distance-field atlas (jump flood in a GLSL TOP at build time) for the big letters.
- Per-word colour and word-level choreography in the marquee (a word that stops while its line runs).
- A take built on tracking alone (one line breathing from tight to full-frame letterspacing).
- Odometer roll for the numerals instead of a hard change.

## Dev helpers

`words.py` (mirror the Describe words and Input notes into preset.json; `--check`), `shots3.py` (scheduled
captures with Describe and Input set per shot), `rebuild.py` (rebuild + set take; finds the repository from `td.project.folder`), `shots2.py` (two captures per shot with the full feed), `shots.py` (scheduled captures of several takes), `watch.py`
(capture on a feed condition), `sheet.py` (contact sheet, outside TouchDesigner).
