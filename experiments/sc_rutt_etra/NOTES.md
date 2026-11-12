# sc_rutt_etra: scan-processor video synth

Built 2026-11-10 in TouchDesigner 2025.33230. COMP `/project1/sc_rutt_etra` at (1250, -1100).

## Intent

An analogue video synthesizer in the spirit of the Rutt-Etra scan processor. A low-resolution
source picture (a lit, slowly turning library model, short phrases in capitals, or plain
oscillators) is never shown directly. It is redrawn as a raster of 30 to 300 scan lines, each a
real ribbon in 3D whose deflection follows the source brightness along that line, so the picture
becomes a relief of glowing wires seen in perspective. Around that sit the other boxes of a 1970s
video studio: a colouriser (luminance bands to hard colours), a keyer, a camera-at-monitor
feedback loop, and a sync generator that tears and rolls. Everything is continuous voltage: no
blocks, no pixel glitches. Audio wobbulates the raster: bass bends it, snare hits tear sync,
the live spectrum rides on the line deflection, hats break the beam up.

## Technique

Signal path, left to right in the network:

1. **Source** (640x360, never shown). `srender` renders one of five library models (`m0`..`m4`,
   named in `DEFAULTS['MODELS']` in build.py; a teapot when there is no library, see Assets) with
   two lights. `text` is a 384x360 Text TOP holding two stacked phrases. `src` (`shaders/src.frag`) mixes model
   luminance, the repeated text tile and two ring-modulated sine oscillators by per-take weights;
   `srcblur` softens it.
2. **Raster** (`lines`, `shaders/raster.vert` + `raster.frag`). One Grid SOP ribbon (2 x 385
   points) instanced once per scan line (`numinstances` = line count, 8 to 300). The vertex shader
   uses `TDInstanceID()` as the line number, samples the source along the line, deflects the line
   in the raster plane (`dy`) and in depth (`dz`), then widens the ribbon in screen space
   perpendicular to its projected direction, so the beam has a width in pixels and a gaussian
   profile. Intensity follows source brightness, and a beam that travels fast (steep deflection)
   is dimmer, as on a real scan processor. Additive blending, 16-bit float. `vert=1` scans
   vertically. `solid` is a black hold-out sheet drawn by the same shader (`uRas.w = 1`) for the
   hidden-line take.
3. **Loop** (`loop`, `shaders/loop.frag` + `fbk`). Camera at its own monitor: last frame rotated,
   zoomed, optionally mirrored, hue-rotated, gain up to about 1, with a soft knee so it saturates
   instead of blowing out. Gain is 0 for the first quarter second of a shot so stale frames from
   before the cut do not show.
4. **Output chain** (`crt`, `shaders/crt.frag`, with `glow` = quarter-size blur). Vertical hold
   slip with a sync bar, flagging and tearing as smooth per-scan-line offsets, a keyer (source
   picture in flat palette bands behind the wires), a colouriser (luminance bands of the finished
   signal to one of six five-colour palettes), chroma smeared to the right, glow, soft
   saturation, negative, interlace, snow, hum bar, monitor-wall tiling with per-tube hold error
   and palette.

Every take is one row of the `TAKES` table in `build.py` (about 75 columns with defaults); the row for
`Take % 10` is read into the `tk` CHOP and combined with the feed in `ctl`.

## Takes (`captures/take_<n>.png`, sheet `captures/takes_sheet.png`)

Ten takes since the art-direction pass (2026-11-10 evening). Take = `Take % 10`.

| n | name | what you see |
|---|---|---|
| 0 | portrait | green wire relief of a model on a tilted raster plane, three-quarter view, 110 lines |
| 1 | colouriser | 230 lines face-on, close on the model's head, hard cyan/violet/orange bands on deep blue; the head rocks instead of spinning, so the face stays towards camera; rolls on the bar line |
| 2 | mandala | 24 oscillator lines into the feedback loop, rotation per pass 360/n (n = 3 to 8 by seed), mirror-extended so it fills the frame with no border |
| 3 | landscape | no model: phrases as embossed amber wire lettering filling the frame, raster laid back |
| 4 | waterfall | no picture: about two seconds of live spectra as a white hidden-line mountain range (low notes in the middle, newest row at the front) |
| 5 | negative | black wires of a model on a lit beige field, a phrase printed flat behind in warning red, off-centre |
| 6 | macro | 46 fat vertical red lines, hidden-line, extreme close-up; abstract |
| 7 | wall | 4, 9 or 16 small tubes (by seed); tubes differ in palette, gain, hold error, mirror, zoom and polarity |
| 8 | rings | the raster re-patched to concentric circles scanning the model, each ring its own hue (rainbow relief on black) |
| 9 | drum | phrases embossed round a solid cylinder of 130 rings, cyan with pink lettering, off-centre and tilted |

From the eleventh visit on, the model steps on by two each time round the table
(`captures/takes_sheet_seed2.png`, takes 10 to 19 at seed 0.71). Seed also changes: line count
(+-15%), which way the raster is turned and by how much, model yaw, phrase, oscillator frequency,
feedback symmetry and hue step, monitor-wall size and layout, ring hue offset.

## Channel to visual mapping

| Feed | Drives |
|---|---|
| `shot.age` | arrival: raster opens from a single horizontal line with deflection overshoot, 0.35 s; feedback gain fades in |
| `bass` | bends the whole raster sideways (two slow sines down the frame); flagging at the top; turns the feedback angle |
| `hit_mid` | sync tear: bands of lines shear sideways for the length of the hit, in the raster and again in the output chain |
| `hit_low` | deflection height +80% (was +50%), beam flash, camera punch-in, feedback zoom kick |
| `hit_high` | beam break-up: lines drop out in smooth gaps |
| live spectrum (`specraw`) | added to line deflection, mirrored about the centre, fanned by line number (takes 2 and 4 mainly) |
| `energy` (remapped 0.33..0.65) | deflection amount, beam gain, feedback gain |
| `evolve` | raster sway, model spin, text scroll, oscillator sweep |
| `bar_pos`, `bar_pulse` | raster roll angle; vertical hold slip on the bar line (take 1) |
| `pulse` | exposure and beam pulse on the beat |
| `section` | which phrase is on the text tile; the raster jumps to a new yaw; the picture rolls once through (vertical hold) in the first 3.5% of each section |
| live spectrum history | take 4: the whole picture is the last two seconds of spectra |

## Assets (2026-11-11)

No file is named by a folder on a machine. Every file parameter is an expression on the scene's
`local/modules/paths` (shaders: `mod.paths.here('shaders/...')`). From `<assets>/` the scene uses:

| Asset | Used for | With no assets |
|---|---|---|
| `<assets>/models/{amphora,gramophone,marble_bust,space_helmet,lander}/model.obj` (or the pack's own five, see Words and models) | the five model slots `m0`..`m4` | TouchDesigner's bundled teapot in all five slots, centred and scaled to 1 unit by `m<i>/fit` (`fit_module.py` reads the OBJ's bounds), each slot posed differently (`TEAPOT_POSE` in build.py) |
| `<assets>/models/<slug>/basecolor.png` | the models' base colour | plain white material; `tex` reads TouchDesigner's bundled `Map/GreyWedge.tif` only so it has a file, and the material ignores it |
| `<assets>/fonts/ArchivoBlack-Regular.ttf` (`DEFAULTS['FONT']`) | the text tile and the Describe caption | TouchDesigner's default face |

Nothing is precomputed from a model or a font, and no data file was added: `fit_module.py` (1.5 kB
of code) is the only new file. A library model goes through `m<i>/pick` input 0 untouched.
With no assets: takes 2, 3, 4 and 9 are the same apart from the typeface; takes 0, 5, 6, 7, 8
show the teapot as wire relief (`captures/p2_none_sheet.png`, `p3_none_sheet.png`,
`p4_none_sheet.png`). See the weak points.

## Words and models (2026-11-11)

Everything a pack may replace sits in `DEFAULTS` at the top of build.py and is read once per build
through `LIB['scene_words'](scene, DEFAULTS)`:

| Name | What it is |
|---|---|
| `PHRASES` | the 14 phrases of the text tile (takes 2, 3, 5, 9), with their line breaks |
| `FONT` | the paths module's name for the typeface of the tile and the caption |
| `MODELS` | the five model slots `m0`..`m4` |
| `FRAMING` | per model take: which slot it starts on and the takes-table columns that fit the take to that model (`FRAMING_COLS`: scale, lift, gain, yaw range, spin, rocking, source zoom and offset) |

A pack's `scenes/sc_rutt_etra/words.json` replaces any of the four whole. The Describe words and
captions (`TAKES[n]['words']`, `label`) are not in it: they describe the technique. As shipped:
amphora (portrait, rings), gramophone (negative), marble_bust (colouriser, close on the head),
space_helmet (macro), lander (wall), in Archivo Black. Why these: the colouriser's framing was made
for a head, and the bust has one; the amphora's bands read as a relief and as rings.

## Describe mode and Input (2026-11-11)

**Describe** (`parent().par.Describe`). Two things change, both live expressions, no rebuild:
- A caption: `label` (24 px, three lines, 1280x132) laid on a darkened strip at the bottom
  by `title_b` (`shaders/titler.frag`), after the output chain so it is never torn or coloured.
  The `fin` Switch TOP passes `crt` straight through when Describe is off, so the off picture is
  the old signal path untouched. Captions live in `TAKES[n]['label']` (and `label_in`, used when an
  Input is set); `{n}` is the live line count, `{sym}` the feedback symmetry, `{tiles}` the tube
  count, `{src}`/`{page}` change to "another picture" with an Input.
- The text tile: takes that put words into the picture (2 mandala, 3 landscape, 5 negative,
  9 drum) read `TAKES[n]['words']` from the `dwords` table instead of the `phrases` table
  (KEYER, FLAT RED BEHIND, DRUM SCAN, KICK = TALLER and so on). Takes 0, 1, 4, 6, 7, 8 have no
  text in the picture and carry the caption only.
- `python mirror_words.py` writes the words into preset.json; `--check` exits 1 if they differ.

**Input** (`parent().par.Input`). The picture enters at `srcsw`, a Switch TOP in front of `src`:
input 0 is the model render, input 1 is `insel` (a Select TOP on the Input path, 640x360). With an
Input, `src.frag` uses its brightness as the whole deflection signal (text drops out of the
deflection; oscillators and the waterfall stay at reduced strength), `raster.frag` tints the beam
with the picture's colour by the take's `icol`, and the raster scans the whole picture (`iz`)
instead of the take's model framing. `ctl['inp']` is 1 only if the path is a TOP and is not this
scene's own `out1`. Blank Input: `srcsw` index 0, `uIn` 0, picture as before.
- Strong with the test picture: 0 portrait, 1 colouriser, 3 landscape, 4 waterfall, 7 wall
  (`captures/input_<n>.png`, `input_sheet.png`). TEST INPUT stands up as wire lettering.
- Usable: 9 drum (picture wrapped twice round so a whole one faces camera), 2 mandala (the
  picture is recognisable only in the first pass; the loop smears it), 5 negative (the keyed red
  words still print over it, which is busy).
- Weak: 6 macro (46 fat vertical lines in extreme close-up: abstract, the input is not
  recognisable), 8 rings (the rings scan only the centre of the picture and deflection turns it
  into a rainbow lump; letters can be made out, the picture as a whole cannot).

## Log (newest first)

- **Generic defaults (2026-11-11 07:00).** The phrases, typeface, models and model framing in
  build.py are now generic (the repository's own asset pack: catalogue and real-time phrases,
  Archivo Black, five of its sixteen objects). The originals live in a private pack's
  `scenes/sc_rutt_etra/words.json`, and a build on that pack draws the scene as before
  (`captures/ref_*_sheet.png` before, `priv_*_sheet.png` after). Log entries below this one were
  written on the first pack: model names in them are that pack's.
  - `g1_*_sheet.png`: first generic build, old framing, typeface by alias (a mono face). The
    colouriser on a helmet was an abstract dome and the portrait bust was cut off at the top.
  - `g2_*_sheet.png`: bust moved to the colouriser slot, amphora to portrait and rings, Archivo
    Black named outright (fatter strokes lift better than the mono face's). `g3_*`: final framing.
    Describe on the generic pack: `g3_d0.png`, `g3_d3.png`, `g3_d5.png`.
  - tdh.errors empty on both packs. tdh.check on the generic pack: PASS (8.36 ms), fail
    (cook_budget 46.4 ms, other scenes rebuilding in the same session), PASS (2.30 ms). Tox,
    snapshot and `hero.png` (take 1, the bust in the colouriser) saved on the generic pack; scene
    left built on the local pack, Preview off.

- **Portability pass (2026-11-11 05:50 to 06:05).** build.py and the helpers name no folder; the
  repository is `td.project.folder`, files go through `mod.paths`. Order of proof:
  - Reference before any change: `p0_ref_<n>.png` / `p0_ref_sheet.png`.
  - Converted, real assets: `p1_with_<n>.png` / `p1_with_sheet.png` match the reference and
    `final_off_sheet.png` take for take (differences are the music, yaw and phrase). Describe and
    Input: `p1_with_di_sheet.png`.
  - Assets parameter at an empty folder, rebuilt: errors empty, `p2_none_sheet.png` (all ten).
    First try scaled the teapot by a million: `computeBounds()` on the teapot's File In POP
    returns zeros (it returned real sizes for a library model), so `fit_module.py` reads the
    bounds from the OBJ instead. An empty Movie File In path is a warning, so `tex` falls back
    to a bundled image. Take 1 framed empty sky above the teapot (its framing is for the
    head of a tall model): slot 2's teapot is lifted 0.27 (`p3_none_sheet.png` before,
    `p4_none_sheet.png` after). Describe and Input with no assets: `p3_none_sheet.png`.
  - Assets blanked, rebuilt: `take_<n>.png` / `takes_sheet.png` recaptured on this final build.
    Describe and Input again: `p5_final_sheet.png`. `hero.png` recaptured (take 8).
  - tdh.errors empty; tdh.check: pending, fail (cook_budget 39.1 ms straight after the save and
    snapshot), fail (13.3 ms), then PASS at 3.02 ms. Portable test for this scene: 1 passed.
    Tox and snapshot saved; Assets blank, Describe off, Input blank, Preview off.

- **Describe and Input pass (fourth builder, 2026-11-11 05:20 to 05:40).** An earlier agent was
  cut off part-way through this task; its edits were in build.py and the shaders with nothing in
  NOTES.md or preset.json. Rebuilt and checked each step rather than trusting it.
  - `v1_off_<n>.png`: all ten takes, Describe off, Input blank, against `take_<n>.png`: same
    pictures (differences are the music and the phrase).
  - `v2_desc_<n>.png`: Describe on. Captions legible at full size and on a quarter-size sheet.
    Fixed: the mandala caption said its lines were "drawn from sine waves" although the text tile
    is also in that source at half weight (now "sine waves and words"); with an Input the portrait
    caption read "A hidden picture of another picture" (now its own `label_in`). Caption Text TOP
    set to `fitiffat` so a long line shrinks instead of being cut off.
  - `v3_in_<n>.png`, `v3_ind_*.png`: test picture into all ten takes. Drum showed one giant
    letter (picture once round a drum we see a third of); `iz` 0.5 wraps it twice (`v4_in_9.png`).
  - Final rebuild, then `describe_<n>.png` / `describe_sheet.png`, `input_<n>.png` /
    `input_sheet.png`, `final_off_<n>.png` / `final_off_sheet.png`.
  - Input guards checked live: own `out1`, a missing path and a CHOP path all leave `inp` 0 with
    no errors. tdh.errors empty; tdh.check: pending, fail (cook_budget 45.6 ms straight after
    forced cooks), then PASS at 3.19 ms. Tox and snapshot saved; Preview off.
  - Tried by the earlier agent and dropped (its comment in build.py): keying the caption into the
    signal before the output chain so it tore and glowed with the picture; unreadable at 22 px.

- **Art-direction pass (second builder, 2026-11-10 19:14 to 19:30).** Judged first: `ad1_a<n>.png`
  and `ad1_b<n>.png` (all eight takes at seeds 0.3 and 0.62). All eight differed at a glance, but
  the mandala was a muddy green disc with a polygonal edge, the negative take was a tangle (text
  both deflecting the wires and keyed behind them), the wall was nine dim copies of one picture,
  and a 2 px canvas-weave lay over every frame (snow drawn as a dot grid on top of interlace).
  Changes, all in build.py and the shaders:
  - Two new scan modes in `raster.vert` (`vert` column: 2 = disc of rings, 3 = drum) and a chroma
    oscillator on the line counter in `raster.frag` (`hspread/hoff/hamt`): takes 8 and 9.
  - `wfall` + `wfb`: a 256x128 one-row-per-cook history of the spectrum, mixed into the source
    (`ww`): take 4 replaces the old edge-on scope. `ad4_sheet.png`, `ad5_b4.png`.
  - Mandala: rotation 360/n, black-level cut per pass, loop input mirror-extended, corner fade
    only. `ad3_2.png`, `fin_2.png`.
  - Negative: text goes only to the key channel (`wk`), printed in red under the black wires.
  - Wall: tile count by seed, tubes mirrored / zoomed / negative, brighter.
  - Snow is now smooth along the line (integer hash, interpolated in x); interlace dim 0.35 to 0.25.
  - Section change: yaw step and one vertical roll (`fin_4.png`, `fin_1b.png` caught mid-roll).
  - Kick deflection +50% to +80%. Hit sequence viewed: `ad6_hits.png` (take 8: frames at hit_low
    0.56 and 0.64 taller and brighter; frames at hit_mid 0.24 and 0.27 torn).
  - Tried and dropped: sliding the waterfall half a row per frame (bilinear averaging flattened the
    history, `ad3_4.png`); stepping it on alternate frames by `absTime.frame % 2` (stalls when
    frames drop in pairs); clearing the history on a cut back in (two seconds of flat field);
    a see-through drum (back lettering reads mirrored through the front, `ad2_9.png`).
  Final rebuild then `fin_*.png` / `sheet_fin.png`; `hero.png` is `fin_8.png` (rings).
  `take_0..9.png` are from one tuning step before the final build except takes 4 and 9, which
  were recaptured on it.

- **Final rebuild** from `build.py`, then `final_a/b/c.png` (take 1, seed 0.3, 0.67 s apart):
  torn and rolling on a snare at the bar line, clean, and bent by bass 1.3. `hero.png` is
  `final_b.png`. `take_<n>.png` were captured one small tuning step earlier (before the tear
  reduction and take 1's bend 2.0 to 1.5); the takes table is otherwise identical.
  tdh.check: fail on the first run after the rebuild (cook_budget 37.5 ms, model loads), then
  PASS three times (1.86, 0.33, 2.11 ms).
- **s08** `sheet_s08.png`: second-cycle takes. Colouriser on a low, wide model left the frame
  nearly empty (its framing is for a tall subject), so that model was swapped for another and the
  model order per take changed; portrait source zoom 1.3 so narrow models are not slivers.
  Feedback hue step now scaled by seed: mandalas go orange/blue, green/violet, pastel.
- **s07** `sheet_s07.png`: text tile narrowed to 384 px with two phrases stacked and repeated,
  raster tilt reduced to -32 degrees, depth deflection 0.11: the phrases read. Before that (s04 to s06) the landscape take was a row of
  unreadable towers with half the frame empty.
- **s05** `sheet_s05_audio.png`: take 0 and take 4 at four moments each. Tear on hit_mid 0.42
  and 0.30, taller and brighter on hit_low 0.71, scope ridges move with the spectrum.
- **s04** `sheet_s04_arrival.png`: one shot from frame 3 to 90: raster opens from one line.
  (The first three captures are identical because TouchDesigner dropped frames after the rebuild.)
- **s03** `sheet_s03.png`: colouriser gain up (face reaches the top bands), scope turned to 48
  degrees, macro source blur up to remove stair-steps, output-chain tear reduced.
- **s02** `sheet_s02.png`: a regular 11 px zigzag on every line turned out to be my own
  `sin(y*400)` ripple in the tear at 25 px amplitude; cut to 2 px. Mandala: mirror on, gain
  0.96, less hue step. Monitor wall: palette and colouriser amount per tube.
- **s01** `sheet_s01.png`: first run of all eight takes. Mechanism worked first time; source
  too dark (luminance about 0.3), lines dim. Added source gain 2.4 and beam gain 2.6.

## Honest weak points

- **With no assets the model takes are a teapot.** All five slots are the same teapot in different
  poses, so the variety between models is gone. Take 1 (colouriser) is the weakest: a smooth
  untextured teapot falls into one or two colour bands, so at some yaws it is a flat teal
  silhouette (`p4_none_1b.png`). Take 6 (macro) is abstract lines as it always was. The default
  typeface is plainer than the pack's, and with it the Describe caption is a little smaller.
- **Describe is a caption strip, not part of the technique** in six of ten takes: plain subtitle
  text over the bottom 18% of the frame, covering that part of the picture. It reads, but it is
  the least inventive answer. The words inside the picture (takes 3, 5, 9) are cropped by the
  frame as the phrases are, and in the mandala (take 2) they are not readable at all.
- **Describe numbers are live but nominal in preset.json** (line count varies +-15% by seed).
- **Input on takes 6 and 8 is weak** (see above). An Input replaces the model, so the model-only
  variety (which model, yaw) is lost; a dark input gives a nearly flat raster.
- **A Select TOP on another scene's out1 pulls that scene's cook** while this one is showing; that
  is what "read the TOP" costs. Not measured with a real second scene, only the test picture.

- **Take 9 (drum) depends on the phrase.** With a short phrase most of the visible face is bare
  cyan rings with lettering at the edges (`take_9.png`); with a long one it reads well
  (`ad5_b9.png`). It is the weakest of the ten.
- **Take 4 (waterfall) is only as full as the last two seconds were loud**: in a quiet passage it is
  a nearly flat field with a few ridges (`take_4.png`); far rows show some herringbone aliasing.
- **Take 2 (mandala) is busy rather than clean**; no longer muddy or boxed, but at high bass it is
  a scribble (`seed2_take_12.png`, bass 2.0).
- Still judged from stills and short frame sequences only, never watched at speed in the cutter.
  The section roll and the yaw step in particular are unwatched in motion.

- **Take 6 (macro) depends on the subject.** With a thin model most of the frame is
  parallel red lines with one or two hot wires. It reads as abstract, not as an object.
- **Take 3 text is readable only at a moderate tilt**; depth deflection turns strokes into walls,
  so this is a compromise between relief and legibility. Phrases are cropped by the frame.
- **Tear strength is high.** On a strong snare the picture is hard to read for about 0.15 s. That
  is the brief, but a viewer may find it frequent; `tear` column scales it per take. A frame
  viewed after the final rebuild (take 1 mid-roll on a snare) was torn past recognition, so the
  raster tear was cut by a third and take 1's to 0.6. After that, `final_a.png` (hit_mid 0.54 with
  bar_pulse 0.77, so tear and roll together) keeps the face recognisable (`sheet_final.png`).
- **Hidden-line is approximate**: the hold-out sheet is a 160x256 grid pushed back in depth, so
  lines very near a silhouette can be clipped or show through.
- **Not seen in motion.** Everything was judged from stills; roll, interlace flicker and feedback
  drift have not been watched at speed. Interlace alternates per frame and may flicker too much
  at 60 fps.
- The pack's lettering art is not used at all; text is typeset phrases only.
- `tk` and `ctl` hold about 75 Python expressions (about 0.45 ms CPU per frame together).

## Next

- Watch it in the cutter and tune tear, roll and interlace by eye.
- Per-model framing columns so every take frames every model well.
- Drum: build the text tile from three or four phrases so the face is always full.
- A take with two rasters keyed over each other (model over text) using the model alpha in
  `src`'s blue channel, which is already written but unused.
