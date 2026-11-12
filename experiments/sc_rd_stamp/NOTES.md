# sc_rd_stamp: reaction-diffusion paperwork

## Intent
A rubber stamp that will not stay stamped. Short phrases are slammed onto a printed sheet
as a chemical in a Gray-Scott reaction-diffusion simulation, so every letter is crisp for an
instant and then starts to grow coral tendrils, hollow out, and get eaten until the next drum
hit stamps it back. It works when (1) you can read the phrase at the moment it lands, (2) the
ink reads as a physical material (gold leaf or wet red enamel standing proud of cream paper,
with a highlight that slides over it) and not as a simulation readout, and (3) the pattern
regime (beads, worms, maze, collapse) audibly follows the track.

## Describe mode and Input (fourth pass, 2026-11-11, for the website)
Two parameters on the COMP, both off/blank by default; with both at default every take is
as before (captures/sheet_final.png against the third pass's sheet_takes.png).

**Describe (toggle).** Every word on screen then explains the technique. Three layers, all
drawn at build time, so the toggle moves switches and nothing is rebuilt:
- what is stamped: each take's `describe` list in `TAKES` (appended to the `phrases` table,
  or an extra 12-cell atlas `datlas0..2` behind the `atlsw` Switch for the tiled takes);
- the paper: `sheet0..2` (Text TOPs, one per paper, `SHEETS` in build.py) replace the three papers on the `forms` Switch, so the page under the stamps is a printed
  explanation instead of the pack's own sheet;
- a two-line caption along the bottom of every take (`captext` -> `label.frag` -> `fin`
  Switch; with Describe off `fin` passes `grade` through and `label` never cooks).
The `takes` table holds a second copy of every row for Describe (`<name>_d`, with the row's
`dover` numbers applied); the `tk` CHOP reads row `take + 7 * describe`.
`preset.json` carries the same words per take: `python preset_words.py` writes them from
build.py, `python preset_words.py --check` fails if the two differ.

| Take | Stamped in Describe mode | Page | Caption, second line |
|---|---|---|---|
| 0 desk | one of 8 two-line phrases, e.g. "THE LETTERS / ARE THE SEED", "KICK DRUM = / FRESH STAMP", "10 SIM STEPS / PER FRAME" | sheet "REACTION-DIFFUSION": five numbered steps | "Stamped letters seed a Gray-Scott simulation. Each kick drum presses them solid again." |
| 1 macro | one of 5 phrases (too close to read, as in the take itself) | same sheet, seen as large blurred print | "The simulation is read as a height map, so the ink stands up and catches the light." |
| 2 field | nine of FEED KILL GROW WORMS SPOTS 1-BIT KICK INK GRAY-SCOTT 640 x 360 SEED DITHER, on a 3 x 3 grid (3 x 4 without Describe: bigger words) | none | "Short words dissolve into worms and spots, in 1-bit dither. Kick drums re-ink about half." |
| 3 approvals | six of KICK SNARE BASS HATS FEED KILL SEED GROW BURN GLINT 3 INKS STAMP, no word twice | sheet "SIX STAMPS, ONE SIMULATION" | "Six stamps in three inks, all one simulation. Each kick drum presses a third of them again." |
| 4 carbon | one of 5 two-line phrases, e.g. "WHITE INK / ON CARBON", at 1.25 size (1.7 without) | none | "The same simulation as white ink on dark carbon paper, seen from one end of the phrase." |
| 5 ticket | one of KICK = STAMP, ONE PER KICK, GRAY-SCOTT, LIVING INK, KICK DRUM | sheet "ONE KICK, ONE STAMP" | "Every kick drum lands a new stamp. The black ink keeps growing; red marks are old stamps." |
| 6 relic | TRI-PLANAR, 3D MODEL, NO UVS, GLSL MAT, SAME INK, GRAY-SCOTT, REACTION, DIFFUSION, KICK, FEED, KILL, SKIN; the flat impression is drawn on the model in this mode only, and the seed picks only among the models whose last column in `RELICS` is 1 | none | "The same living ink projected onto a 3D model from three sides. Kick drums re-ink it." |

**Input (path of a TOP).** The picture enters where the words did: `inp` (Select TOP on the
path) -> `inmask` (`inmask.frag`: a pixel is ink where it is brighter than a wide blur of
the picture, `inblur`) -> `insw` Switch -> third input of `stamp`. `stamp.frag` then uses
that mask in place of the text: the whole page in desk, macro, carbon and field, one small
copy in each of the six frames in approvals, one small framed copy per kick on the ticket, and through the same projection on the relic. Desk and macro (`inpaper=1`) also print
the picture itself on the page in its own colours (`forms` input 6), so the coloured
picture lies flat and its bright shapes stand up out of it as ink. All seven takes accept
it; none ignores it. The living ink is pressed from the picture at the cut, on section
changes and on kicks, as with words; the flat impression under it is re-inked from the
picture every frame with a short trail (`inject.frag`, `uBoot.y`; not on the ticket take),
and the relic draws that impression too, so the picture stays readable when the coral
runs wild. `mode/hasin` is 1 only when the path is a TOP outside this COMP
(reading our own out1 would be a cook loop). Changing Describe or Input fires `ctl/boot`,
so the loop starts clean both ways. With Input blank `insw` and `forms` do not pull `inp`,
`inblur` or `inmask`, so none of them cooks.

## Words and shapes (2026-11-11)
Everything the scene says or shows that belongs to an asset pack is one dict, `DEFAULTS`, at
the top of build.py, read once in `build()` through `scene_words()`:

| Name | What |
|---|---|
| `PHRASES` | the 19 framed phrases; the takes pick rows by number (`plist`), so a replacement keeps the count |
| `ATLAS` | the 12 short words of the tiled takes |
| `LABELS` | what each take is called (its name in the `takes` table, the heading of its Describe caption) |
| `PAPERS` | the three flat sheet models whose pictures are the pages, each with the share of its height that fits a 16:9 page |
| `BLANKS` | the plain sheets drawn from text when a paper's picture is missing |
| `RELICS` | the three models of the relic take: size, turn, lift, and whether it can carry a word in Describe mode |
| `TUNING` | numbers of a take that suit one pack only (take number -> columns of `TAKE_DEFAULTS`); here take 3 gets `chalk` 1, because the blueprint is dark |

The Describe words (`describe`, `caption`, `SHEETS`) are not in it: they explain the
technique and are the same on every pack. A pack that holds
`scenes/sc_rd_stamp/words.json` replaces any of these names with its own value of the same
shape. Why a dict and not parameters: the phrase list and the take table refer to each
other by row number, and the papers and models are loaded at build time.

## Takes (third pass, 2026-11-10 evening: "too repetitive")
The cutter counts this scene's visits in the COMP's `Take` parameter and sets `Seed` and
`Shotstart` for each shot. `TAKES` in build.py has seven rows; the row is
`Take % 7`. Every row is numbers in the `takes` table, read by the `tk` CHOP and passed to
the shaders as uniforms; the three papers, the word atlas and the three models stay loaded,
so a cut changes no file and no wiring. Captures: `captures/take_<n>.png`
(`take_<n>_in.png` is 0.1 s after the cut, `take_<n>_a.png` 2.5 s after),
`captures/sheet_takes.png` and `sheet_music.png` are the contact sheets.

| Take | Name | One line |
|---|---|---|
| 0 | desk | The original picture: tilted cream sheet carrying the first paper's print, one framed phrase, wide then dollying in; ink by section |
| 1 | macro | A few centimetres above the same paper with shallow focus: the ink edge as landscape, no word readable |
| 2 | field | No page at all. Top-down, the whole frame is twelve short words dissolving into worms, in 1-bit dithered black and white |
| 3 | approvals | The second paper from straight above with six small crooked stamps in three inks (gold, red, tar); each kick re-presses a third of them |
| 4 | carbon | Negative: white correction-fluid ink on carbon paper, an oversized unframed phrase seen from one end like road markings, shallow focus |
| 5 | ticket | The third paper (a pink ticket) from above; one small tar stamp that lands somewhere new on every kick and leaves its red impressions behind |
| 6 | relic | No paper. The chemistry is projected onto a library model (one of the three in `RELICS`, by seed) turning in the dark under tubes |

Only take 0 can show phrase 0, the title phrase, centred (5 of its 20 phrase slots). Takes 1, 4 and 5
draw from lists without it; 2, 3 and 6 use the atlas of short words.

What `Seed` changes inside a take: which phrase, the stamp's angle, offset and size, the ink
where the take does not fix it (`(section + int(seed*3)) % 3`), the phase of the light orbit;
macro: which stretch of the phrase and from which side; top-down takes: the roll direction
and where the view drifts; carbon: which end the camera stands at; approvals and field: which
word sits in which tile; ticket: where the stamps land; relic: which model, left or right
of centre, and how far.

What `age` does (first half second of every shot): the loop is wiped and the phrase pressed
solid for 0.22 s (`ctl/boot`, `ctl/hold`), the camera starts 55% further back and rolled
9 degrees and drops onto the page (`exp(-7 age)`), the exposure flashes (`exp(-9 age)`,
grade.frag); in the relic take the model spins 200 degrees into place and the camera comes
in from 2.5 units further away.

New operators for this pass: `takes`, `tsel`, `tdel`, `tk`, `pick` (the take as channels),
`atl_00..11` + `atlas` (word atlas), `form0..2` + `forms` (papers on a Switch TOP),
`relic0..2`, `skinmat` (GLSL MAT, `relic.vert/.frag`), `mcam`, `mrend`, `mbg`, and `pic`
(Switch TOP: page or relic; only the shown branch cooks). `grade.frag` gained a depth of
field (blur circle written by `shade.frag` into alpha) and the 1-bit dither.

Cost per take, steady state, summed cpuCookTime + gpuCookTime of the operators that cooked
in the last 3 frames (file loaders left out, they keep their load time): desk 1.71 ms,
macro 1.66, field 1.53, ticket 1.63, relic 2.12. Approvals and carbon were not read
cleanly (the cutter took the scene during both readings); they run the same operators as
field and macro. The first frame the relic was ever drawn cost 14.5 ms (shader compile);
build.py now draws it once ten frames after the build.

Helpers added: `take.py` / `tour.py` (start shots and capture them some frames later),
`sheet.py` (contact sheet, run in a shell).

## Technique
Everything is rebuilt by `build.py`; GLSL is in `shaders/`.

Second pass (art direction, 2026-11-10) changed three things; where the bullets below
disagree with this paragraph, this paragraph is current.
- The chemistry is zoned by the phrase. `near` (Blur TOP, 60 px, of the stamp at 640x360) is
  a cheap distance-to-letters field and `sim.frag` also reads the crisp stamp: inside the
  strokes the margin sits just above the flood edge and a kick pushes it below (solid
  letters), near the strokes is the worm band, and beyond a "reach" set by energy and bass
  everything dies. The impression no longer inhibits anything, and `inject.frag` presses
  the whole phrase on a kick (no noise patches).
- Three living inks in turn by `section % 3` (`ctl/mat`): 0 gold leaf on a red stamp,
  1 red enamel on a navy stamp, 2 black tar on a red stamp.
- `shade` now writes linear HDR, lit by a warm desk lamp close to the page over a dim green
  fluorescent ambient; `bright` (threshold, 320x180) -> `glow` (Blur) -> `grade`
  (`grade.frag`: glow added before the tonemap, vignette, ACES-like shoulder, gamma). The
  camera starts each section wide on the whole form and dollies into a macro shot of the
  phrase (`section_pos`).

- `phrase` (Text TOP, Archivo Black, auto-fit) -> `stamp` (`stamp.frag`): the phrase inside a
  rounded stamp frame, at a per-section angle, offset and scale.
- Chemistry loop at 640x360, 16-bit float: `fb` (Feedback) -> `inject` (`inject.frag`, once per
  frame) -> `sim` (`sim.frag`, 10 passes per frame, each pass reads the last) -> back to `fb`.
  State: R = 1-U (so a black texture is the rest state and no init pass is needed), G = V,
  B = trace of where V has been, A = the flat stamp impression.
- `hmap` (Blur TOP, 3 px, upscaled to 1280x720) smooths the state so the normal is not faceted.
- `shade` (`shade.frag`): a ray-plane camera looking down at the page on a dark desk. Layers:
  cream paper with fibre noise and the first paper's print; the flat rubber-stamp
  impression (Beer-Lambert absorption, patchy: warning-label red under gold, navy under red
  enamel); a contact shadow; then the
  V field as a raised bead with a normal from its gradient, shaded either as gold leaf (metal,
  crinkled, tinted reflections) or wet red enamel (dielectric with Fresnel). Both reflect a
  procedural ceiling of paired fluorescent tubes plus an orbiting key light.
- The pattern band was measured, not remembered: `map.py` runs a copy of the simulation with F
  across and k up (captures/map_b.png). `sim.frag` steers k as a margin above the measured
  flood edge `kf(F)`.

## Mapping (feed channel -> what you see)
| Channel | Drives |
|---|---|
| `section` | New phrase; new stamp angle, offset, scale; ink by `section % 3`: gold leaf on a red stamp, red enamel on navy, black tar on red. For 0.3 s (`ctl/hold`) the old living ink is burned off (kill +0.02) and the old impression lifted while the new phrase is held down as solid V and as a fresh impression |
| `hit_low` | `ctl/kick`: presses the whole phrase into V (0.75 x kick) and drops the in-stroke margin below the flood edge, so the letters go solid and embossed on the hit and then hollow to outlines, worms and beads until the next one. Also re-inks the impression, punches the camera in 7.5% and lifts glow and exposure |
| `hit_mid` | "burn": kill +0.003 x hit outside the strokes (a third of that inside), coral retreats |
| `hit_high` | specular gain on the living ink (x1 to x3.5) |
| `energy` | regime and reach: feed 0.030 -> 0.048; margin outside the strokes 0.0026 -> 0.0013 and inside 0.0013 -> 0.0006; the reach threshold on `near` 0.20 -> 0.012 (quiet = ink only on the strokes, loud = rails and worms well outside the frame) |
| `bass` | reach threshold -0.08 x bass and margin -0.0007 x bass: the coral gets further and fatter |
| `section_pos` | camera dolly from the wide shot to the macro shot, with a small sideways track |
| `vocals` | feed +0.004 |
| `evolve` | wide-shot camera drift and roll, drift of the noise field that makes the regime differ across the page, drift of the tube reflections |
| `beat_pos` | key light orbit, one turn per 32 beats (the moving highlight) |
| `pulse` | key light intensity +30% on the beat |
| `bar_pulse` | camera moves 4% toward the page on the bar line |
| (cook gap) | `ctl/boot`: first frame after the scene was not cooking wipes the loop and stamps the current phrase, so a cut to the scene never shows a stale or empty sheet |

Not used: `spectrum`, `pitch`, `bass_pitch`, `onset`.

## Inputs / outputs
- Inputs: `hub` audio feed, and the library files listed under "Assets" below (three sheet pictures, three models, two fonts), each with a fallback.
- Output TOP: `out1`, 1280x720.
- Cost: steady-state per-operator times read live were sim 0.12 ms CPU + 0.22 ms GPU, shade
  0.04 + 0.11, hmap 0.02 + 0.08, the rest under 0.11 ms each; `tdh.check` cook_budget read
  0.86 ms (2026-11-10, eight scenes cooking).

## Assets (2026-11-11: what the scene loads, and what it shows without it)
No file is named by folder anywhere. Every file parameter is an expression on the `paths`
module the scaffold installs (`local/modules/paths`); `python -m pytest -q
tests/test_portable.py -k sc_rd_stamp` fails if a machine path comes back. Nothing was
added to the experiment folder as data: every fallback is drawn or fitted live.

| Used from `<assets>/` | Where | With no assets |
|---|---|---|
| `fonts/ArchivoBlack-Regular.ttf` | every stamped word (`phrase`, the atlases), sheet and stand-in headlines | TouchDesigner's default face (Verdana here) with Typeface set to Bold. Thinner and rounder than Archivo Black, so the stamps read less like rubber stamps. |
| `fonts/BarlowCondensed-Bold.ttf` | Describe sheets' body text, the Describe caption | the default face at 0.7 of the size (it is much wider than a condensed face) |
| `models/star_chart/basecolor.png`, `models/blueprint/basecolor.png`, `models/ticket/basecolor.png` (the `PAPERS` rows) | the printed page under the stamps (`form0..2`) | `blank0..2`: a plain sheet drawn from Text TOPs (`BLANKS` in build.py: PLATE 07, SHEET 12-B, ADMIT ONE, with ruled fields), behind `formsw0..2`. The Movie File In with no file is never cooked. |
| `models/amphora/model.obj`, `models/pierced_stone/model.obj`, `models/space_helmet/model.obj` (the `RELICS` rows) | the relic take (`relic0..2/mesh`) | TouchDesigner's bundled teapot for all three, so the seed no longer changes the object. `relicN/fit` (Transform POP, Align page) centres it and scales its longest side to 1.4 units; for a library model `fit` does nothing. |

Not used: Chicago, the lettering art, the models' UVs (the relic is tri-planar). The music and
feed are the hub's business.

## Dev helpers (run inside TouchDesigner, see the header of each)
`rebuild.py` (run build.py), `cap.py` (capture + feed values), `trap.py` (captures at fixed
frame offsets after the next section change), `map.py` (F/k regime map), `dump.py` (one channel
of a TOP as a PNG), `tour2.py` (tour of takes with Describe and Input set), and in a shell
`sheet.py` (contact sheet) and `preset_words.py` (mirror the Describe words into
preset.json, or `--check` them). The helper nodes they add (`zz_*`, `zm_*`) are removed by a rebuild.

## Final state after the second pass (2026-11-10)
- Clean rebuild from `build.py` (33 ops). `tdh.errors` empty. `tdh.check`: run 1 after the
  rebuild FAIL on `moving` only (stale sample from the destroyed COMP, "cooks": -399), run 2
  PASS (moving delta 0.209 over 217 cooks, cook_budget 1.21 ms).
- Per operator, read live in steady state: sim 0.13 ms CPU + 0.20 GPU, near 0.05 + 0.13,
  shade 0.04 + 0.11, hmap 0.02 + 0.09, bright/glow/grade under 0.05 each. `form` showed
  9 + 11 ms right after the rebuild (the one-off texture load).
- captures/f4.png is from the final rebuild. `captures/hero.png` is a copy of captures/f2.png,
  taken one rebuild earlier with the same files. Tox and snapshot re-saved with Preview off.

## Final state of the first pass (2026-11-10)
- Clean rebuild from `build.py`, then captures/21a_final.png: red title-phrase stamp with gold
  beads and dashes (energy 0.43, snare burning), no helper nodes left in the COMP.
- `tdh.errors` empty. `tdh.check` PASS on the third run after a rebuild. The first two runs
  after a rebuild fail for reasons that are not the scene: run 1 compares against a motion
  sample from the destroyed COMP ("cooks": -690), run 2 counts the one-off load of the form
  texture (about 16 ms) as per-frame cost. Without a rebuild in between it passes on run 2.
- `sc_rd_stamp.tox`, `snapshot/network.json` (25 ops) written. `captures/hero.png` is a copy of
  captures/20_150.png (gold filigree growing out of a two-line phrase, same shader files as
  the final rebuild). Preview off; `sim.totalCooks` stopped rising.

## Log (newest first; 2026-11-10 unless dated)
- SIXTH PASS, 2026-11-11 (generic defaults). The words, papers and models in build.py are
  now generic and match the asset pack that ships with the repository: phrases about
  real-time picture-making and a catalogue of unexplained objects, the star chart,
  blueprint and ticket as papers, the amphora, pierced stone and space helmet as relics.
  The words and shapes the scene was first made with live in a private pack's
  `scenes/sc_rd_stamp/words.json`, and a build on that pack reads them from there. Take 5
  is now called `ticket`. Older entries below describe captures made with that private
  pack; their phrases are given here only as "a phrase" or "the title phrase".
- Seen on the generic pack (captures/gen_sheet.png, g2_sheet.png, gd_sheet.png): all seven
  takes plus Describe. The blueprint is dark, so on take 3 the flat impressions were
  dark-on-blue between kicks and could not be read (gen_3.png, gen_3b.png). Fixed in
  review the same day: a take column `chalk` (0 by default) makes the impression a pale
  transfer instead of absorbing ink (`shade.frag`, `uInk.y`), and the generic `TUNING`
  sets it for take 3 only. A pack whose `TUNING` is empty draws as before.
  The marble bust was tried as a relic and dropped: red enamel across its eyes read as
  blood (gen_6c.png). Tall models are drawn at 0.9 so they clear the frame.
  `tdh.check` on the generic pack: run 1 FAIL on `moving` only (first sample after the
  rebuild), run 2 PASS (moving delta 0.24 over 55 cooks). Tox, snapshot and
  captures/hero.png (take 3 on the blueprint) are from the generic build, saved with the
  COMP's Assets blank so no folder is stored.
- The same build.py on the private pack: `tdh.snapshot` of the rebuilt COMP differs from
  the snapshot committed before this pass in six parameter expressions only (the relic's
  turn and size now carry `0 +` and `1.0 *`); captures/prv_sheet.png against ref_sheet.png
  taken before the change shows the same papers, models, words and layouts.
- FIFTH PASS, 2026-11-11 (portability; nothing drawn differently). build.py, rebuild.py,
  dump.py and map.py no longer name a folder: the repository is `td.project.folder`, and
  every `file` / `fontfile` parameter is an expression on `mod.paths` (shaders
  `mod.paths.here(...)`, fonts `mod.paths.font(...)`, form pictures
  `mod.paths.model_texture(...)`, models `mod.paths.model_file(...)`). See "Assets" above
  for the fallbacks. Reference before the change: captures/sheet_ref.png (ref_take_0..6,
  seed 0.3).
- With assets after the change: captures/sheet_port.png (port_take_0..6, seed 0.3) against
  sheet_ref.png and the fourth pass's sheet_final.png: the same seven compositions, papers,
  faces, inks and (take 6) the model. Compared by eye in stills, not as a pixel diff (the
  picture follows the music). Describe on take 0 and Input on take 3:
  captures/port_describe_0.png, port_input_3.png.
- With no assets (the COMP's `Assets` parameter pointed at the empty folder
  captures/_noassets, then a rebuild): `tdh.errors` empty, captures/sheet_noassets.png
  (na_take_0..6), Describe captures/na_describe_0/3/6.png, Input captures/na_input_0/3.png.
  Every take moves and stamps on the kick as before. Weak points: the default face is
  lighter than Archivo Black; the three papers are plain ruled sheets with none of the pack's print; the relic is always the teapot.
- Traps: (1) the Text TOP's Bold toggle does nothing unless Legacy Font Selection is on;
  the `typeface` menu ('Regular' / 'Bold') is what selects the weight. (2)
  `computeBounds()` on a File In POP or an undisplayed Transform POP returned zeros;
  `pop.bounds()` returned the real box. (3) Transform POP's Align page (`aligntx/y/z` =
  'origin', `alignscale` = 'unity') centres a mesh and makes its longest side 1 with no
  Python; `alignxformorder` = 'aligntransform' lets `scale` apply after that. (4) Menu
  parameters take expressions that return the menu name, so one network serves both the
  library model and the stand-in.
- FOURTH PASS, 2026-11-11 (Describe and Input). Done by two agents: the first was cut off
  part-way and left build.py, the shaders and the live COMP changed but NOTES.md and
  preset.json untouched; the second (this entry) re-checked every step from a rebuild.
- Rebuild on the new scaffold with Describe off and Input blank: captures/sheet_final.png
  (final_0..6.png, seed 0.3) against the third pass's take_0..6.png: same seven
  compositions, papers, inks and word layouts. sim.frag is identical to the third pass
  again (the first agent's every-frame press of the chemical `INPRESS` and in-stroke margin
  `uZone.z` were both left at 0 and are removed). stamp.frag, inject.frag, shade's
  uniforms and relic.frag differ only behind `uIn` / `uBoot.y` / `mode` values that are 0
  by default. This is argued from the code and seen in stills; it is not a pixel diff (the
  picture depends on the music, so two captures never match).
- Describe, every take captured and read at 1280x720: captures/describe_0..6.png, contact
  sheet captures/sheet_describe.png. Seen and changed by the second agent:
  field at 2 x 3 showed three words and a lot of white (d3_2.png), now 3 x 3 at the same
  word size (FEED and KILL fill the middle, d4_2.png); carbon's one-line words were letters
  the height of the frame, unreadable (d3_4.png: "REACT"), now two-line phrases at 1.25
  size (d4_4a.png: WHITE INK / ON CARBON, readable with the head tilted); the relic showed
  no word at all 2.6 s into a shot (d3_6.png: gold rings on red), so in Describe mode the
  flat impression is drawn on the model (ivory on lacquer, navy on cream, red on putty) and
  a model with no wide face is left out (describe_6.png: KILL, TRI-PLANAR, 3D MODEL, SAME INK
  in grey-navy with red enamel outlines on a boxy model).
- Input with /project1/sw_testcard/out1, all seven takes: captures/sheet_input.png,
  input_0..6.png, i4_*.png. Desk (i4_0.png): the colour picture printed on the page and
  TEST INPUT standing out of it in crinkled gold, lagging the moving picture by a beat so a
  ghost of the letters shows beside the ink. Field (i4_2.png): TEST INPUT in 1-bit tar,
  dripping. Relic (i4_6a.png): the words wrapped round the model in gold on red.
  Approvals and ticket show small framed copies; carbon the whole picture in white from
  one end; macro is colour and enamel edges with nothing recognisable (as the take is).
  Then a tour in a loud passage (energy about 0.6) lost the picture: field, approvals and
  relic were all maze with no TEST INPUT (captures/i5_2_loud.png, i5_3_loud.png,
  i5_6_loud.png), because the test picture moves away from where it was stamped and the
  impression stayed behind. Now the impression follows the picture every frame
  (sheet_input.png, energy 0.59: input_0.png gold coral round a red TEST INPUT on the colour
  print, input_2.png TEST INPUT in dripping 1-bit tar, input_4.png clean white on carbon).
  Approvals and relic are readable at the cut (input_3a.png, input_6a.png) and still mostly
  coral 2.5 s later in that passage (input_3.png, input_6.png).
  Describe and Input together: the caption's second line becomes "The bright shapes of
  another picture are the stamp. Each kick drum presses them again." and the first gains
  "+ INPUT" (captures/describe_input_0.png; the first wording ran off the right edge).
- Cost, take 0, sum of cpu+gpu of what cooked in the last 2 frames: 2.2 to 2.9 ms plain,
  2.5 to 3.2 ms with Describe and Input both on (label 0.05, captext 0.15, inmask 0.08,
  inblur 0.07). With both off `label`, `captext`, `inp`, `inmask` stop (totalCooks held at
  297 across three readings). `label` cost 6.45 ms on its first ever cook (compile), so
  build.py now draws `label` and `inmask` once after the build.
- tdh.check after a rebuild: run 1 pending (first samples), run 2 FAIL on cook_budget only
  (35.4 ms with every GLSL TOP reading about 4 ms, `stamp` included: other agents
  compiling), run 3 PASS (cook_budget 3.3 ms, moving delta 0.094 over 60 cooks). After the
  last rebuild: run 1 FAIL on cook_budget only (57.6 ms), run 2 PASS (2.88 ms, moving
  delta 0.085 over 366 cooks).
- Final state: clean rebuild from build.py (132 ops), then captures/sheet_describe.png,
  sheet_input.png and sheet_final.png were all taken from that build. `tdh.errors` empty.
  Tox and snapshot (136 ops) saved with Describe off, Input blank, Preview off.
  `python preset_words.py --check` passes (101 lines of words). `captures/hero.png` is
  unchanged from the third pass.
- Weak, honestly. Describe: the macro take shows no readable stamped word (only its
  caption and blurred sheet print explain it); carbon reads sideways; on the page takes the
  stamp sits on top of the sheet's body text, so some of its lines are covered at any
  moment; desk's stamp sometimes repeats the sheet's own headline (REACTION-DIFFUSION
  twice); the field's bottom row of words is under the caption band; the caption is the
  same on every visit to a take. Relic words break up within a few seconds between kicks
  and only the flat impression stays. Input: only the test picture was tried, never a real
  scene; the mask is "brighter than its surroundings", so a dark-on-light picture stamps
  its background and a low-contrast one stamps little; the picture's colours survive only
  in desk and macro, the other five takes use its shape alone; the ink follows motion only
  through kicks and the zoned chemistry, so fast motion leaves the ink a beat behind; with
  Input set, approvals' sheet in Describe mode still says "stamps" where pictures are
  stamped. All judged from stills again.
- THIRD PASS (takes). Where this entry or the Takes section disagrees with older text
  below or with the Mapping table, this is current: ink is `(section + int(seed*3)) % 3`
  only in takes 0, 1 and 6; the phrase comes from the take's list; `ctl/hold` is also 1 for
  the first 0.22 s of a shot; `ctl/boot` also fires when Take or Seed changes.
- Starting point, three captures a few seconds apart (captures/s0_a.png, s0_b.png, and
  s1_rebuilt.png after rebuilding the untouched build.py on the new scaffold): the same
  tilted sheet with the framed title phrase in the middle each time, tar then gold. The
  rebuild on the new scaffold needed no change and looked the same.
- First tour of six takes worked on the first compile (captures/a1.png .. a5.png). Seen
  and changed: the macro's blur drew moire over highlights (a1.png), fixed by turning the
  sample spiral per pixel and clamping samples to 4.0 (take_1_a.png: grain instead); the
  carbon take at camera height 0.17 was a white streak nobody could read (a4.png), raised
  to 0.30 and the white ink darkened so the bead shows (take_4_a.png, take_4.png); the
  sheet of approvals repeated one word four times with a random word per tile
  (captures/a3.png and the first take_3), now neighbours never share a word.
- Relic take, three tries. (1) PBR MAT with the simulation as base colour through the
  model's own UVs: the UVs are an atlas of shards, so the pattern was confetti and the
  letters wall-sized (captures/b6x.png, c6x_in.png). (2) GLSL MAT projecting the simulation
  from three sides in object space (relic.frag): letters and worms wrap the model
  coherently (captures/c6x.png tar on cream, mirrored words on back faces, fixed by flipping
  the projection by the normal's sign). (3) Gold on red lacquer glowed like a lamp on a
  kick (take_6_a.png); leaf reflection and kick boost cut (take_6_s7.png).
  `TDCameraIndex()` does not exist in a GLSL MAT pixel shader: camera position and the
  world matrix are passed from the vertex shader.
- Ticket take: at stamp size 0.40 with two-line phrases the strokes were thinner than the
  pattern and the tar died to a few dashes in a quiet section (first take_5.png: the longest two-line phrase). Size 0.52 and one-line phrases (take_5_a.png: three red impressions of one phrase and the live tar one, 2.5 s into a shot).
- Field: with the impression layer off the words were gone 3 s into a shot (first
  take_2.png, energy 0.40: all worms). Impression back at 0.6, which the dither shows as
  grey under the tar. take_2_a.png (energy 0.46, no kick) is worms and rings; take_2.png,
  2.5 s later and 0.07 into a new section (the section burn and re-stamp), is clean
  words again.
- Follows the music, per take (feed values read in the same call as each capture):
  desk take_0_a.png (0.06 into section 10, snare 0.68: a flat solid phrase)
  against take_0.png 2.5 s later (no kick: tar beads on every letter); macro take_1_a.png
  and take_1.png both on kicks of 0.29 and 0.40 (letters flooded solid, camera has
  travelled along the phrase); approvals take_3_a.png (energy 0.38, kick 0.03: thin
  outlines) against take_3.png (energy 0.64, kick 0.45: fat flooded frames and letters);
  carbon take_4_a.png (bass 0.64: outlined, hollowing phrase) against take_4.png
  (0.08 into the next section: new phrase, solid); ticket
  take_5_in.png (one stamp) against take_5_a.png (four, one per kick since the cut).
  The relic pair (take_6_in.png gold words on red at the cut, take_6.png red enamel coral
  3.7 s later after a section change) was captured before the feed values of the last
  tour were kept, so its numbers are not in this log.
- The cutter was running the whole time and took the scene about every 35 s, setting Take
  to its own count (73 to 78 seen). tour.py records `take_held` per capture; captures where
  it was False were retaken (take_0 three times, take_3 twice).
- `captures/hero.png` is a copy of take_6.png (a model in red enamel coral). It predates
  the last change to relic.frag, which only touched the gold ink.
- Final state: clean rebuild from build.py (70 ops), `tdh.errors` empty, `tdh.check` FAIL
  on run 1 (cook_budget 347 ms: the load time of the three papers and three models, still
  on their operators), PASS on run 2 (cook_budget 1.77 ms, moving delta 0.17 over 484
  cooks). Tox and snapshot (74 ops) saved with Preview off.
- Weak, honestly: still judged from stills, including every arrival (seen only as single
  frames at 0.0 to 0.28 s: take_0_in.png wide and rolled, take_1_in.png flash). Take 0 and
  take 1 share paper and inks, so in a small thumbnail they differ by framing and blur
  only. The relic's boxy model is often seen from the back and reads as a box (take_6_s4.png).
  Carbon is legible only when the phrase is short; long ones are texture. Field loses its
  words within about 3 s of a section change. The depth of field is a 22-tap gather and is
  grainy up close. Approvals at 3 x 2 has letters near the smallest size the chemistry
  can hold. `spectrum`, `pitch` and `onset` are still unused. What Seed does was looked
  at for the relic (three seeds) and seen in passing for carbon and macro (two seeds
  each), not for the other takes.
- Next: watch it under the cutter; give carbon and macro a slow focus pull on `bass`;
  let the field's words drift so they drag trails; a second relic camera (close on the model); pick the relic's facing per model.
- SECOND PASS, what was seen first (captures/r1_a..r1_f.png, six captures over 20 s, first
  build): competent render, but the living ink had nothing to do with the letters most of
  the time. r1_b: two gold coral patches on a red title phrase. r1_c: a quiet section with one
  red worm on a flat navy phrase. r1_d, 3 s later: the page carpeted with red droplets
  (reads as measles or blood). r1_e: a kick at 0.42 as gold lumps over a short phrase plus the
  leftover droplets, hard to read. Flat lighting, cream everywhere, camera near static.
- Zoned chemistry (see Technique). captures/r2_a.png: a phrase in solid gold at a kick
  of 0.94; r3_a.png (kick 0.83) a phrase in solid red enamel; r3_b.png (kick
  0.13) black tar hollowed to outlines around a red phrase. So a kick reads as
  solid letters and the gap between kicks as outlines.
- Reach was too short at first (threshold 0.34 -> 0.035 on a 34 px blur): nothing grew
  outside the strokes (r3_a, r3_b). With 0.20 -> 0.012 on a 60 px blur: captures/r4_a.png,
  red enamel rails along the frame and drips off the title phrase; r5_c.png, tar worms over a red title phrase at bass 1.0 (section 8, one of the sustained-bass sections the first pass
  never saw: it does not carpet the page).
- Quiet sections: captures/r4_c.png (energy 0.20) letters dissolved into worms that stay on
  the strokes. But r4_d.png, 4.5 s later with a snare at 0.6: only a dozen droplets left,
  dead. In-stroke margin lowered (0.0020 -> 0.0013 quiet) and the snare burn cut to a third
  inside the strokes. After: captures/f4.png (energy 0.37, snare 0.33) tar beads still on
  every letter of a two-line phrase. The quietest sections (0 and 1) were not seen
  again after this change.
- HDR shade + glow + grade, lamp close to the page. First try blew out (r2_a.png, r2_b.png:
  white pool, pink haze); lamp gain 5.2 -> 1.75 and speculars cut by about half fixed it
  (r3_a.png).
- Black tar added as a third ink: captures/r6_b.png (a two-line phrase at the stamp),
  f1.png (the title phrase at the stamp, kick 0.83) and f2.png 3 s later in the same section
  with no kick: broken into beads and rails on the red stamp, camera pushed in. This pair
  is the clearest evidence of kick and section_pos.
- Dotted contour lines and glitter in every reflection (zoom of r5_c.png) were the Blur
  TOP's `dither`, not the shader. Off on hmap, near and glow; hmap blur 3 -> 7. Clean in
  r6_b.png.
- Gold read as custard (r7_b.png): ceiling ambient too bright and a wide specular. Darker
  ceiling, deeper gold, tighter highlight: r7_c.png (a two-line phrase, legible, foil
  glints), f3.png (gold outlining a red phrase at bass 0.84).
- Camera push reduced twice (0.86 -> 0.62) because wide phrases were cut off late in the
  section (r4_a.png, r4_d.png). It still crops the widest ones a little at the end (f2.png).
- The trace layer now shows the previous section's coral as a pale stain under the new
  stamp (r4_b.png, f1.png). Not designed, kept.
- Impression made a weak inhibitor of the reaction (kill margin +0.0012 x impression), growth
  eased (10 passes, loud margin 0.0019, bass 0.0009). captures/20_150.png: gold filigree
  through and around a phrase 2.4 s after the stamp; 20_270.png: 2 s later the gold
  has drawn back to outline every letter; 20_600.png: red enamel outlining a navy phrase;
  20_1000.png: a phrase filled solid in red enamel by a full-strength kick, worms around it.
  All four are readable.
- The same inhibitor at 0.0045 killed everything within a second of the stamp
  (captures/19_60.png: one bead). 19_270.png is a full kick in that build, solid gold.
- Why an inhibitor: with 12 passes the coral carpeted the page in about 4 s and buried the
  phrase (captures/18b.png: a phrase under red worms; 17_600.png: a full gold
  labyrinth over the title phrase, striking but unreadable).
- Navy impression under red enamel. Red beads on a red stamp could not be read
  (captures/16_360.png). captures/17_120.png: lumpy red enamel over a navy phrase;
  17_840.png: a navy phrase under red worms, readable.
- Kicks re-ink in patches instead of refilling the letters solid, and passes 8 -> 12. In a
  section with 16 kicks the solid refill reset the coral every half second
  (captures/15_440.png: always solid letters). After: captures/16_90.png, 16_270.png,
  16_360.png show one kick-heavy section going from solid letters to beads to coral.
- Output clamped to 0..1 (specular had reached 1.47 after the tonemap).
- Cut-in reset (`ctl/boot`, `uBoot`). Before this a rebuild or a cut left a blank sheet until
  the next kick or section. Tested once by turning Preview off for 5 s and capturing:
  captures/13b_resume.png shows a clean sheet with the current phrase freshly stamped.
  captures/13a.png is a kick moment in gold: a short phrase, solid and embossed.
- Chemistry re-anchored on the measured flood edge (captures/map_b.png). captures/12_100.png:
  1.5 s after the stamp the gold has collapsed to beads on the letters; captures/12_330.png:
  5 s after, gold worms have fingered out from the frame and letters over a legible red title phrase. This is the look I was after. captures/14_150.png (red beads on a two-line phrase) and captures/14_420.png (gold outlining another) are the same build.
- Before that the living ink died within 1.5 s in most sections (captures/11_100.png,
  11_330.png: a few beads). I had fitted the centre of the pattern band by eye from
  captures/map_a.png and steered around it; growth from a stamped shape is only fast near the
  flood edge, so the centre was the wrong anchor. Measured the band with numpy instead.
- Bloom TOP tried (preblacklevel 0.82, intensity 0.55) and removed: it washed the cream paper to
  white (captures/09_12.png, 09_220.png). Only that one setting was tried.
- Stamp box made smaller and camera widened so the whole frame of the stamp fits
  (captures/08_20.png had it cut off at the left). captures/10_12.png: a two-line phrase, red enamel, fully legible. Kick now also punches the camera.
- Quiet section 1 (energy 0.2): enamel is solid at the stamp (08_20.png), gone 3 s later leaving
  only the flat impression (08_180.png), back as solid enamel with beads after a
  kick (08_330.png).
- Impression made nearly opaque with Beer-Lambert absorption; with a linear mix it was pink
  (captures/06_180.png).
- Split the ink into two layers: a flat impression that stays legible for the whole section and
  the living reaction-diffusion bead on top; added gold leaf. captures/05a.png (gold piping on a
  pale red title phrase), 07_3.png (a phrase embossed in gold at the stamp), 07_75.png
  (gold reduced to beads at the letter corners 1.2 s later).
  Why: with one layer the phrase was unreadable 2 s after the stamp (captures/03a.png: lines and
  dots only).
- captures/04a.png: gold slab. Two mistakes at once: kill too low so V flooded the whole stamp,
  and the camera swung 0.34 sideways, which reads as a 30 degree rotation of the page. Camera
  swing cut to 0.13.
- captures/02a.png, 03a.png: first lit version, red enamel worms on the form. Paper blown out
  in the light pool, red too salmon.
- First build failed to compile: wiring a second input with `src.outputConnectors[0].connect(dst)`
  did not append on a GLSL TOP, and a GLSL TOP has only 3 input connectors. Now wired by index,
  and the shade pass takes 3 inputs.

## Weak points after the second pass (honest)
- Still judged from stills. The kick pulse (solid, then hollow) is inferred from captures at
  different kick values, not watched.
- With kicks every half second the letters may strobe between solid and outline; it could
  be too busy in motion.
- Coral outside the letters is mostly rails parallel to the frame and strokes, less often
  free branching coral. It is tidy rather than wild.
- Gold is the weakest of the three inks: honey foil, not leaf. Red enamel still reads as
  blood or ketchup.
- Late in a section the macro camera crops the widest phrases, and a cut to the scene late
  in a section lands on the macro view of a freshly stamped phrase (captures/r7_a.png).
- hit_high sparkle, pulse, bar_pulse, vocals and the light orbit are still not isolated.
- One section in three has a navy stamp, which is off the palette the scene was first made for.
- Simulation speed is still per frame, not per second.
- The first-pass points below about the patchy kick, the inhibitor and the missing bloom no
  longer apply.

## Weak points of the first pass
- Legibility is carried by the flat impression layer, which is not simulated. The chemistry
  itself is only letter-shaped for about a second after each stamp or kick.
- After a stamp the solid letters collapse within about a second and the coral takes 2 to 4 s
  to grow back, so in short or quiet sections without kicks you mostly see beads on a stamp
  (captures/21a_final.png).
- The balance between "coral buries the phrase" and "coral dies" was tuned over about ten
  sections of one track. I did not see every section, and sustained bass (sections 5, 8, 25)
  after the last change is unseen: it may still carpet the page.
- I am not sure the 0.3 s burn on a section change clears the old coral. Worms surround the
  new stamp 2 to 3 s into a section in captures/17_840.png and 20_1000.png; I did not check
  whether they are leftovers or fast new growth.
- The red enamel can read as blood rather than enamel when it is all droplets (06_180.png).
- `hit_mid` burn, `hit_high` sparkle, `pulse` and `bar_pulse` are wired but I never isolated
  them in a capture; only section, kick, energy/bass regime and the resume reset were seen
  to do their job.
- Judged from stills only. I never watched it in motion, so the feel of the kick punch and
  the highlight travel is unverified.
- Simulation speed is per frame (10 steps), not per second: a slower frame rate grows slower.
- The desk is plain: a dark surface with tube reflections. No depth of field, no bloom.
- Gold crinkle noise sparkles a little on wide flat areas (the frame bar in 13a.png).
- Only Archivo Black and only the first paper are used; Chicago was never tried (thinner strokes may
  not seed the chemistry).

## Next
- Watch it in motion and tune the kick decay inside the strokes.
- Let the reach breathe with `bass` more, so the coral visibly advances and retreats.
- Speed up regrowth after a stamp without burying the phrase: pour a seeded edge rather than a
  solid fill, and make the inhibitor follow the letters' interior only.
- Let the old coral survive a section change as a ghost in a third material instead of being
  burned off.
- Alternate the paper (the second and third) and try Chicago for short phrases.
- An HDR output plus a threshold glow pass, so highlights can bloom without lifting the paper.
