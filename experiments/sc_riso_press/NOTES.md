# sc_riso_press: misregistered print shop

## Intent (written before building, 2026-11-10)

A risograph / screen-print press seen from above. The picture should read as printed matter being made in time with the music, not as a halftone filter over a 3D render. What makes that difference:

- **Plates are separate things.** A 3D render of a library model is lit by three pure-colour lights (red, green, blue) from different directions, so each colour channel is its own lighting of the form. Each channel becomes one spot-colour plate; a fourth key plate takes deep shadow, a contour line and line-art type.
- **Plates are printed at different times.** Each plate's separation is latched (held) and only re-exposed on its own trigger (kick, snare, hat, roller pass). The model keeps turning, so the plates disagree in pose as well as position: misregistration in time.
- **Each plate has its own screen** (dots, lines or stochastic grain) at its own angle, computed analytically in paper space so a macro take shows crisp giant rosettes.
- **Ink is rolled on.** After a cut and after every paper advance the sheet arrives blank and each plate is swept on by a roller, one after another.
- **Paper moves.** On each bar (or beat, per take) the sheet advances; the previous print slides out and a blank sheet slides in. Earlier sheets are an edition: same latched image, different ink density, colourway and register.
- **Print artefacts**: multiply overprint on fibrous paper, rough dot edges, ink starvation streaks along the feed, dry-ink speckle, registration crosses and colour bars printed per plate (so the crosses split when the plates are out of register), a slug line in Chicago.

Takes must be different pictures: proof sheet, loupe macro, delivery grid of many sheets, two-colour line moire, full-bleed type sheet, poster corner with marks, opaque ink on dark stock, makeready ghosts, gang sheet.

## Technique (as built)

```
m_<model>, one per model named in the words (16 on the shipped pack) (mesh -> fit; one rendered at a time; grey lifted texture) + cam + light0/1/2 (pure R, G, B)
   -> render 1024x600 (rgb = three lightings, a = coverage)
in_sel (COMP par Input, else black) -> in_prep 1024x600 ; render | in_prep -> src_sw   (2026-11-11)
t_big (Archivo Black) + t_slug (Chicago 24 px) + t_rows (Barlow Condensed) -> typepack (r, g, b)
src_sw + typepack + fb_sep -> sep 1024x640   plates 0..3 in r,g,b,a, each HELD until its latch fires
sep + fb_hold -> hold                         copy of sep taken at each paper advance = the previous sheet
sep + hold + t_cap -> press 1280x720 -> out1  bed, sheets, screens, overprint, marks, roller, Describe caption
cook_driver (press_driver.py) -> every uniform, camera, lights, text, fontsel (which face the big word uses), and ctl (readout CHOP)
```

- `shaders/sep.frag`: per plate a recipe (which light, ink in the shade or in the light, type weights, flood and gradient kind, the plate's own scale / rotation / offset of the artwork, tone gamma and amount). Gang sheets tile the artwork and permute plates per tile. The key plate is deep shadow plus an alpha-edge contour plus the slug.
- `shaders/press.frag`: view transform, then which sheet is under the pixel (feed axis, optional lanes running in alternate directions), per-sheet hash for skew, density, colourway swap or dropout and static misregister. For each plate: register offset, screen in paper space (dot radius from the tone at the cell centre; line width; simplex grain), solid line art above tone 0.86, streaks along the feed, mottle, pinholes, the roller edge on the live sheet, then multiply (or opaque mix on dark stock). Printer's marks are generated per plate.
- `press_driver.py` is the press state machine in Python (measured about 0.36 ms a frame): shot detection, paper advance, roller timing, plate latches, register springs, view, model, lights, type. It replaces the scaffold's cook driver so the uniforms are always set before the one forced cook of `out1`.
- No feedback of the picture itself: only the two latches (`sep`, `hold`) at 1024x640 rgba8.

## Feed to picture

| Channel | What it does |
|---|---|
| `beat_pos` | paper advance every `adv` beats (4 = each bar by default, 1 in delivery, pile and conveyor, 2 in xerox and gang, 8 in loupe); roller passes follow at `lay` beat spacing |
| `section` | forces a paper advance; picks the model, the big word, the rows of phrases and the ink set (INKSETS); reseeds colourway swaps, gang-sheet plate order and ring-screen centres |
| `vocals` (smoothed) | sun / flood radius up to 22% larger; second plate up to 35% thinner |
| `hits_low` / `hit_low` | re-exposes plates 0 and key and kicks them out of register (jump, then an under-damped spring back); view punches in 3%, model thumps, work light flashes |
| `hits_mid` / `hit_mid` | same for plate 1 |
| `hits_high` / `hit_high` | same for plate 2 |
| `bass` (smoothed) | dot gain: dots, lines and grain swell from 0.70 to about 1.6 times |
| `energy` (remapped 0.33..0.65) | size of register kicks, strength of ink starvation streaks, sun radius |
| `evolve` | model spin (110 degrees per unit, so plates latched at different hits disagree in pose), light rig swing, view drift, row scroll, plate wobble in the type and makeready takes, streak wander |
| `shot.take`, `shot.seed` | take from the TAKES table; seed moves view centre and rotation, model, word, phrase order, light rig, sun position |
| shot start (first frame on screen, or Take/Seed/Shotstart change) | sheet arrives blank, the plates roll on within about 0.45 s, view snaps in from 22% wider and 7 degrees off |

## Second pass (art direction, 2026-11-10 evening)

What I saw before touching it (captures/j0a..j8b.png, two per take a few seconds apart): nine takes that did differ, but four of them (proof, corner, night, gang) were the same composition, one sheet slightly tilted on a dark bed; every take was straight-down dots, lines or grain; `j4b` (type take) was a full frame of blank cream paper and `j0b`, `j5b`, `j6b` were mostly blank sheets mid-roll; `j1a` (loupe) was dark green-brown mud.

Changed:
- Five new takes with new techniques (9 to 13 below): a heap of sheets, a tilted conveyor view, guilloche security printing, 1-bit photocopy with negatives, concentric-ring screens.
- `press.frag`: perspective tilt (`uCam.x`), pile mode (`uCam.y`), screens 4 rings / 5 guilloche waves / 6 cross-hatch, split-fountain inks (`uInkB`), reprint mode (`uMode.x`: new plates wipe over the old impression, so full-bleed takes never show blank paper after the arrival), negative on odd sheets (`uMode.y`), and screens finer than the pixel grid print as their average tone instead of aliasing.
- Driver: `INKSETS` (plates on default inks take a new ink triple per section and seed, so a returning take changes palette), roll-on starts during the paper slide and is faster (sheet complete about 0.5 s into a 1.92 s bar, was about 0.85 s), kick size up a third, kick also punches the zoom 3% and flashes the work light, vocals swell the sun and thin the second plate, big word can be set in Chicago.
- Fixed: a beat line falling inside the arrival masked the held sheet, which blanked every sheet in the delivery and conveyor lanes (seen in an early `m8_conv`); the first sheet after a cut is no longer masked.
- Loupe plates lightened (no more mud at seed 0.71; the violet/green/orange ink set at `b_1.png` is still heavy).

Still weak after this pass: the gang take is thin when the model is small or edge-on (`take_8.png`, `b_8.png`); sheet takes still show a blank sheet sliding in for about a quarter of each bar (`m6_slide.png`); pile and lane takes show one held image in many colourways, not a history; motion was again judged from stills and a six-frame arrival sequence (`p_03..p_60.png`), not a recording.

## Describe mode and Input (2026-11-11, for the public website)

Two agents worked on this. The first was cut off part-way; it left the `describe` entries in TAKES, the fitted big word, the caption Text TOP, `in_sel` / `in_prep` / `src_sw` and the batch helper's DESCRIBE / INPUT options, none of it logged or checked. The second (this entry) rebuilt, looked at every take, and changed what is listed under "fixed" below.

**Describe (COMP par `Describe`).** The words live in build.py beside each take (`describe=dict(...)`) and are mirrored into preset.json `"words"` by `sync_preset.py` (it reads the live TAKES, so the two cannot drift by hand). The driver treats Describe as part of the shot, so toggling it re-exposes every plate at once: no rebuild. Text TOPs re-rasterise only when their text changes, as they already did at every section change; string widths for fitting are measured once at build time (`DW` in the COMP's storage). Driver cost measured 0.41 to 0.51 ms with Describe on or off.

| Take | What Describe shows (captures/describe_<n>.png, describe_sheet.png) |
|---|---|
| 0 proof | big word, one of RISOGRAPH / SPOT COLOUR / OVERPRINT / HALFTONE, fitted whole across the top; caption "A 3D MODEL UNDER RED, GREEN AND BLUE LIGHTS. EACH LIGHT PRINTS AS ONE PLATE OF INK."; the slug still reads PROOF SHEET nnnn |
| 1 loupe | caption "HALFTONE DOTS" in the middle of the macro; the pink dot-tint word behind is DOTS (not readable at this scale, as before) |
| 2 delivery | EDITION / 1 PER BEAT / COPIES on every sheet, above a smaller model |
| 3 duotone | caption "2 INKS, 2 LINE SCREENS / RED AT 32 DEG, BLUE AT -28 / WHERE THEY CROSS: MOIRE" |
| 4 type | eleven short sentences, one per line, set where the view sees them (THIS SHEET HAS NO 3D MODEL. / SAME WORDS ON TWO INK PLATES. / ONE PRINTS SOLID, ONE AS GRAIN. / THEY NEVER QUITE LINE UP. / A KICK KNOCKS THE SOLID PLATE. / A SNARE KNOCKS THE GRAIN PLATE. / BOTH SPRING BACK INTO REGISTER. / BASS THICKENS THE GRAIN. / EACH BAR A ROLLER PRINTS AGAIN. / THE DISC IS A PLATE OF BIG DOTS. / THE STRIPES ARE ONE HUGE WORD.); the striped fragment is TWO PLATES / TYPE ONLY / OVERPRINT |
| 5 corner | caption "REGISTER CROSSES AND COLOUR BAR: EACH INK PLATE PRINTS ITS OWN. A DRUM HIT SPLITS THEM APART." |
| 6 night | OPAQUE INK / DARK STOCK / WHITE INK; caption "OPAQUE WHITE, PINK AND YELLOW PRINT WHERE THE LIGHT FALLS." |
| 7 makeready | MAKEREADY / TEST SHEET / WASTE SHEET printed solid; caption "EVERY PLATE HOLDS THE MODEL AT ITS OWN SIZE AND ANGLE."; the sheet is turned the right way up so it can be read |
| 8 gang | slug only: "STEP AND REPEAT 4 X 3 nnnn" |
| 9 pile | STACK / EDITION / 1 PER BEAT above a smaller model |
| 10 conveyor | PRESS RUN / EDITION / 1 PER BEAT above a smaller model |
| 11 bond | GUILLOCHE / WAVE LINES / ENGRAVED in wave lines; caption "LINE WIDTH CARRIES THE TONE AS ON A BANKNOTE" |
| 12 xerox | PHOTOCOPY / 1-BIT / NEGATIVE / CROSS-HATCH; caption "BLACK INK ONLY, CROSS-HATCHED / EVERY 2ND COPY IS A NEGATIVE" |
| 13 target | caption "RING SCREENS: 2 INKS, 2 CENTRES / WHERE RINGS CROSS: BULLSEYE MOIRE" |

Fixed in the second agent's pass (seen in its first captures, since deleted):
- Captions went through the separation on the key plate. Chicago at 22 to 24 px broke up there: letters lost strokes under the 0.86 line-art threshold and grew blobs from the dot screen ("RED" read as "AED"). The caption Text TOP `t_cap` now goes straight to the press (input 2), which prints it in the key ink, in register with the key plate, with no screen and no streaks, and knocks every plate out in a 3-texel halo around the letters so it reads over any amount of ink. `typepack` is wired as it was before this work.
- A sheet can drop a plate (colourway chance); in Describe that could drop the plate carrying the word (seen on proof). No dropped plates while Describe is on.
- Big words hidden behind the model (delivery, pile, conveyor, proof): in Describe the word sits in a band at the top (`bigmax`) and the model is smaller and lower (`mscale`, `mpos`).
- Makeready's word was a thin line tint under the blue plate: `bigamt=1.0` prints it solid. Bond's word is at 0.84 (just under solid) so it stays engraved but reads.
- Type take: the old flowing rows showed about 20 characters of each 45-character sentence. Now one sentence of at most 32 characters per line, sized so the widest fits the view (about 31 px in the sheet texture, 62 px on screen), starting at the view's left edge, with the scroll phase restarting at the shot. Two sentences were untrue and were rewritten (the type does not drift between plates; only register kicks and static misregister move it).
- "3 PLATES" (proof has three colour plates and a key) became SPOT COLOUR; "ONE BLACK PLATE" (xerox prints two black plates) became BLACK INK ONLY.

**Input (COMP par `Input`).** The picture enters where the three-light render did: `in_sel` (a Select TOP the driver points at the Input TOP) -> `in_prep` (green and red swapped so the default plates give a rough magenta / cyan / yellow separation, blacks lifted to 0.16, gamma 0.8) -> `src_sw` index 1 -> `sep`. Its three channels stand in for the three lights, so everything downstream applies: per-plate latches on kick, snare and hat (a moving input is frozen at a different moment on each plate), screens, misregister, editions, roller. Dark areas take the most ink. Blank Input, a path that is not a TOP, or a TOP inside this COMP all give index 0 and `in_sel` back on `black`; `in_prep` did not cook once in 650 frames with Input blank.
- With an Input: type prints over the picture instead of behind it; night, bond and xerox drop their big word (`inbig=0`); bond, xerox and target print the picture at scale 1 with no plate offset (`inscale=1`), because their own 1.5 to 1.7 crop left half a word of the test picture.
- Tested with /project1/sw_testcard/out1 on all 14 takes at seed 0.37 (captures/input_<n>.png, input_sheet.png) and nine at seed 0.83. Best: 3 duotone, 13 target, 12 xerox, 11 bond (full-bleed, the words TEST INPUT drawn in crossing lines, rings, hatching, guilloche), 2 delivery, 6 night. Good: 0 proof, 8 gang, 9 pile, 10 conveyor. Weak: 5 corner (coarse dots and a crop: "TEST INP"), 7 makeready (upside down, four copies at four sizes: a texture, barely readable), 1 loupe (a macro of dots: the input only steers dot sizes, it is not recognisable). Ignores Input: 4 type (no picture plate).
- With Describe and Input both on, proof and makeready swap to captions that say "PICTURE" instead of "3D MODEL" (`intext`).

## Assets (2026-11-11)

No file in this folder names a machine folder. Every file parameter is an expression on the scene's paths module (`local/modules/paths`, from `experiments/sw_hub/paths_module.py`): shaders and `press_driver.py` through `mod.paths.here(...)`, the rest as below. `tests/test_portable.py -k sc_riso_press` checks it, including the saved .tox and the snapshot.

| The scene uses | From | With no assets folder |
|---|---|---|
| the models named in build.py `DEFAULTS["MODELS"]` (on the shipped pack all 16 objects: gramophone, space_helmet, astrolabe, hourglass, ribbon_loop, pierced_stone, rubber_duck, marble_bust, lander, amphora, traffic_cone, crystal_cluster, wire_cage, broken_column, balanced_solids, skeleton_key) | `<assets>/models/<slug>/model.obj` | TouchDesigner's bundled teapot for every one. Each model has a `fit` Transform POP after `mesh`: identity for a library model, and for the teapot the centre and 1-unit scale the library uses (the teapot is measured at build time; the expressions switch on `mod.paths.have(...)`) |
| their base colour images (used only as a grey, lifted texture) | `<assets>/models/<slug>/basecolor.png` | `data/blank.png`, an 8 x 8 flat grey committed here (78 bytes), so the Movie File In always has a file |
| Archivo Black (big word), Barlow Condensed Bold (rows of phrases), the face the pack gives for `chicago` (IBM Plex Mono Medium on the shipped pack: slug line, Describe captions, the xerox take's big word) | `<assets>/fonts/` | TouchDesigner's default face (Verdana here) with `bold` on. The Describe fitting widths (`DW`) are measured at build time in whatever face is in use |

Nothing is precomputed from a model or a font except `DW`, which the builder measures again on every build. No art, music or feed files are read by this scene.

What it looks like with no assets (captures/port_n_0..13.png, port_n_sheet1.png, port_n_sheet2.png): the same press, sheets, screens, inks, marks and motion, printing a teapot on every take, with the words in bold Verdana. Weak: every section's "new model" is the same teapot, so the picture changes less over a track; Verdana is wider and lighter than Archivo Black and has none of Barlow's condensed weight, so the type take (4) has fewer, larger letters per line and looks plainer; the xerox take loses its 1-bit Chicago look; the slug line is ordinary small type.

## Takes (build.py TAKES; captures/take_<n>.png, captures/takes_sheet.png, second seeds in captures/b_<n>.png and takes_sheet_b.png)

0. proof: one sheet nearly filling the frame, model right, huge cropped yellow word, marks and slug.
1. loupe: 5x macro of the screens; giant dots, line and grain, register fringes; no readable word.
2. delivery: high above the bed, lanes of small sheets running in opposite directions, new sheet every beat, each sheet its own colourway.
3. duotone: red and blue line screens crossing into moire on pink stock, full bleed, model seen from above.
4. type: no model; rows of phrases on pink and teal (grain) sliding past each other, a coarse yellow disc, a striped key fragment.
5. corner: bottom-left corner of a poster; coarse-dot sun, tiny model, register crosses and colour bar large in frame.
6. night: opaque white, pink and yellow on navy stock, ink where the light falls (negative of the others), white line-art word.
7. makeready: waste sheet upside down on kraft; each plate carries the model at a different size and angle.
8. gang: the artwork stepped and repeated 4 x 3, each tile with its own plate order, dropout and tint.
9. pile: a heap on a brown bed; every beat a printed sheet is slapped on top at its own angle (it lands from 1.8x with a wide shadow).
10. conveyor: low tilted view down the bed, lanes of sheets stepping toward and away from the camera each beat, receding to haze.
11. bond: security printing on green-grey stock; green and ink guilloche wave lines engrave the model and a big word, faint pink ring screen.
12. xerox: 1-bit black cross-hatch model and Chicago word, heavy streaks, every second copy a negative (white on black).
13. target: orange and blue concentric-ring screens with different centres, bullseye moire on yellow stock, model enlarged.

## Checks (2026-11-10, after the final rebuild)

- `tdh.errors('/project1/sc_riso_press')`: `[]`.
- `tdh.check('experiments/sc_riso_press/checks.json')`: first run PENDING (moving, cook_budget need two samples), second and third PASS. moving delta 0.139 over 152 cooks; cook_budget 1.727 ms.
- Per-operator times read while other scenes were cooking: press gpu 0.33 to 0.39 ms, sep 0.03, render 0.04 to 0.06; cpu readings of 3 to 4 ms on every GLSL TOP (including the one-uniform `typepack`) are the shared-instance contention described in TRAPS.md, not this scene.
- `sc_riso_press.tox`, `snapshot/network.json`, `captures/hero.png` written. Preview left off.

## Log (newest first)

- **Generic defaults, review (2026-11-11)**: on the shipped pack the key also left makeready (at the plates' 1.5x and 2.1x sizes it printed as bare diagonal bars, `rv_g_7_0.png`) for the crystal cluster; it stays in xerox. Every take seen again at five seeds (`rv_g_<take>_<n>.png`), Describe on takes 0, 4, 6, 11 (`rv_d_<take>.png`); tdh.errors `[]`; tdh.check FAIL, FAIL (cook_budget, contention), PASS (cook_budget 2.68 ms). Tox and snapshot saved again from that build; hero is now proof with the astrolabe (`rv_hero_b.png`). Private pack rebuilt after: stored words and model rows equal the private file, `rv_p_<take>.png`.
- **Generic defaults (2026-11-11)**: the words and the models are generic by default and the originals live in a private pack's `scenes/sc_riso_press/words.json`. Everything a pack may replace sits in one dict, `DEFAULTS` in build.py: `BIG` (14 big words), `PHRASES` (22 rows of small type) and `MODELS` (per take, rows of `[model, size]`; size multiplies the take's `mscale`). build() reads it with `LIB['scene_words'](scene, DEFAULTS)`, puts each take's rows into the stored `TAKES` and the two word lists into the COMP's storage as `WORDS`; press_driver.py holds no words any more and reads `parent().fetch('WORDS')`. The model COMPs are made for the union of the rows, in order of first use. Describe words are not part of `DEFAULTS`. Nothing in this folder is baked from a model or a font, so no data files moved. Before the change, on the private pack: `captures/ref_<take>_a.png` (all 14 takes, seed 0.37) and `ref_<take>_b.png` (six takes, seed 0.83). On the shipped pack (COMP par Assets set to the repository's assets folder): every take at seeds 0.37, 0.83, 0.11 and 0.62 (`g_<take>_a..d.png`, sheets `g_sheet_*.png`); after those, the helmet was made smaller in proof (0.85) and night (0.8), the column smaller in duotone (0.85), and the key left the gang sheet (edge-on it was a thin line in every tile) for the astrolabe: `h_<take>_a..d.png` for takes 0, 1, 3, 6, 8. Describe on takes 0, 4, 7, 12: `gd_<take>.png`. tdh.errors `[]`; tdh.check FAIL (stale motion sample after the rebuild), FAIL (cook_budget 23.5 ms, contention while other scenes rebuilt), PASS (cook_budget 0.98 ms, moving delta 0.053 over 73 cooks, driver 0.46 ms). Tox, snapshot and hero (pile, ribbon_loop) saved from the generic build with Preview off and Assets blank. Then rebuilt on the private pack: stored `WORDS` and every take's rows equal the lists in git HEAD, and `p_<take>_a/b.png` were compared by eye with the `ref_` set. Weak on the shipped pack: the loupe goes almost solid with a bulky model and a heavy ink set (`g_1_c.png`), as it did before; the helmet seen from behind is a plain ball (`g_0_b.png`); a cropped big word can read as another word (TOUCH as OUCH in `g_2_b.png`).
- **Portable (2026-11-11)**: build.py, press_driver.py, rebuild.py and sync_preset.py no longer name any folder (see "Assets"). The driver used to write the big word's font file into the Text TOP from a table of paths kept in the COMP's storage; now `t_big`'s font file is an expression that reads a one-channel CHOP, `fontsel`, which the driver sets per take. (First try read the channel from `ctl`: that re-rasterised the word every frame, 196 cooks in 10 s, because `ctl` cooks every frame. With `fontsel`: 6 cooks.) Each model gained a `fit` Transform POP and the fallback texture. Reference before the change: `port_ref_0/3/6/9/12.png`. With assets after it: `port_a_0..13.png` (`port_a_sheet1.png`, `port_a_sheet2.png`), compared by eye with the reference and with `plain_sheet.png`: same compositions, faces, screens and marks. With the COMP's Assets parameter on an empty folder (`captures/_noassets`): `port_n_0..13.png`, tdh.errors `[]`. Describe and Input checked on one take in both states: `port_a_describe.png`, `port_a_input.png`, `port_n_describe.png`, `port_n_input.png` (sheets `port_a_io.png`, `port_n_io.png`). In the no-assets state tdh.check's `moving` passed (delta 0.195 over 207 cooks). Back on the real assets after the last rebuild: tdh.errors `[]`; tdh.check FAIL (stale motion sample from before the rebuild), FAIL (cook_budget 34 ms, contention), PASS (cook_budget 1.76 ms, moving delta 0.148 over 181 cooks); driver 0.44 ms; over 431 frames the `fit`, `mesh` and `tex` operators did not cook. Tox and snapshot saved with Preview off, Describe off, Input and Assets blank; `python -m pytest -q tests/test_portable.py -k sc_riso_press`: 1 passed.
- **Describe and Input, final rebuild (2026-11-11)**: rebuilt from build.py, then captured every take three ways at seed 0.37: `describe_0..13.png` + `describe_sheet.png` (Describe on), `input_0..13.png` + `input_sheet.png` (Input = the test picture), `plain_0..13.png` + `plain_sheet.png` (Describe off, Input blank; compared by eye with `take_0..13.png` from 2026-11-10: same compositions, type, screens and marks; the music and section differ, so models, words and inks differ as they always do). tdh.errors `[]`. tdh.check: PENDING, FAIL (cook_budget 23.3 ms while every GLSL TOP in the project read 4.2 to 4.7 ms CPU, the shared-instance contention), PASS (cook_budget 1.95 ms, moving delta 0.135 over 493 cooks). press gpu 0.38 ms, driver 0.41 to 0.51 ms. Tox and snapshot saved with Preview off, Describe off, Input blank. Left in captures/ from the first agent, unreferenced: `d_0..13.png`, `s1_t*.png`, `describe_wip.png`, and a `pre` folder of 15 files.
- With Describe off and Input blank the only code-path differences from 2026-11-10 are: `sep` reads the render through a Switch TOP at index 0, the press has a third input it does not sample, and `a *= 1.0 - halo` with halo 0.

- **Second pass final rebuild**: `final_rebuild.png` (= hero, conveyor), `final_rebuild_take13.png`; `take_0..13.png`, `b_0..13.png`; moments `m3_kick` (proof, snare 0.6: plates split into colour fringes), `m4_kick` (target), `m5_kick` (xerox negative), `m6_slide` (corner: blank sheet arriving), `m7_pile_land` (sheet landing on the heap), `m8_conv`, `m9_roll` (type: roller wiping the new impression over the old), `p_03..p_60` (duotone arrival, frames 3 to 60 after a cut: blank, red roller, blue roller, complete by frame 22); `moments_sheet.png`. The first-pass m1..m9 files were overwritten by these. tdh.check: FAIL once (cook_budget 25.6 ms, every GLSL TOP reading 4 to 6 ms CPU while other scenes rebuilt), then PASS twice (1.27 and 2.24 ms). Quiet per-operator cost: press gpu 0.38 to 0.47 ms, cpu 0.04; sep 0.06 / 0.05; render 0.21 / 0.06; text TOPs 0.65 in total; driver 0.40 to 0.43 ms.
- Xerox was washed out at low bass (thin lines) and by the kick flash: take gain 1.3, gamma 0.75, flash 0.4.
- Arrival of reprint takes: after a cut the first pass still rolls onto blank paper (the reveal); only later passes overprint.
- **First pass final rebuild** from build.py (those two files have since been overwritten): `final_rebuild.png` (proof, teal and yellow plates visibly holding different poses), `final_rebuild_take5.png`.
- **Take and moment captures**: `take_0..8.png`, `takes_sheet.png`; `m1_arrive` (0.2 s after a cut: pink down, teal roller crossing), `m2_roll`, `m3_slide` (bar line: printed sheet leaving at the top, blank arriving), `m4_kick` (snare 1.02: teal plate 0.034 sheet-heights off, fringe on every edge), `m5_delivery_slide`, `m6_loupe_roll` (roller band crossing the macro view), `m7_corner_kick` (= hero: register crosses split into three colours), `m8_type`, `m9_night`; `moments_sheet.png`.
- Loupe could land on blank paper for some seeds: smaller view jitter, and the take now has a pink dot tint of the big word and soft teal and yellow floods behind the model, so the macro is never empty.
- Register kick was 0.011 sheet-heights (3 px): invisible. Now 0.03 scaled by hit strength and energy. Model spin 30 to 110 degrees per evolve unit so held plates differ in pose. Dot gain range widened.
- An unfinished sheet (section change before all plates were rolled) left the press showing stale plates from an older model: `hold.frag` now masks plates that never reached the paper (`uLaid`).
- Default cadence changed from 8 beats / 1 beat per plate to 4 beats / a third of a beat: with the slow build the sheet was incomplete most of the time. Loupe keeps the slow build.
- Night take: white plate went solid (tone above 0.86 is line art). Added a per-plate tone amount (`uAmt`) to keep it in the dot range. Models over scale 1 overflow the image area and get a hard rectangular crop: all takes now 0.8 to 0.95.
- Slug line and crop marks were unreadable: tones at cell centres near line art printed stray dots. Margins are now pure line art, and dots are suppressed where the cell-centre tone is solid.
- First light rig orbited the model, so one light often dominated and the print went a single muddy green. Lights are now laid out relative to the camera (left-front, right, top-back) and only swing; tone gamma 2 leaves paper in the highlights.
- First build worked on the first run (no compile errors); lights at dimmer 1.6 gave a near-black render and so an all-ink print: dimmer 3.6 and texture lifted to 0.62..1.

Earlier working captures (a*, b*, c*, d*, e* series) were deleted when the final set was taken; what they showed is described above.

## Weak, unverified, next

- Describe (2026-11-11): judged from stills at two seeds (0.37, 0.83), not every seed and not in motion. On a kick the type take's two plates jump apart and every sentence doubles for about a third of a second (`describe_4.png` caught it); that is the technique, but it costs legibility. Delivery, pile, conveyor and gang carry only two or three words or a slug, so they name the idea and explain little. The loupe caption can drift partly out of frame with the view's pan. After a section change the live sheet and the older sheets can show different words for a bar. Captions are in Chicago at 24 to 26 px in the sheet: readable at 1280x720, small on a phone. Big-word options are picked by section and seed, so a given shot shows one of them, not all.
- Input (2026-11-11): tested only with the test picture, never with another scene's out1, and not in motion. Colours are not faithful (the section's ink set decides them) and a dark picture prints heavy. The type take ignores Input; loupe, corner and makeready use it but do not keep it recognisable. A Select TOP pulls on the Input TOP, so if that TOP's scene is not being cooked by its own driver the picture is whatever it last rendered.
- I judged motion from stills and short still sequences only, never from a recording at speed. The roller, slide, kick and plate re-exposure all appear in captures, but whether the 4-beat cadence feels right at 125 bpm is unverified.
- The live sheet's already-printed ink jumps on a hit and springs back. That is what the brief asks for, but it is not physical; the edition sheets (previous prints) keep only their static misregister.
- The press bed is plain dark blanket with faint rails. The wide takes carry it; the proof take's border is dull.
- Key-plate contour lines break into beads at coarse screens (corner take), and thin model parts (cords, legs, wire) get lost in the two-colour line take.
- Some seeds push the sheet partly out of frame in proof and night; I accepted that as variety and did not check every seed. Checked seeds: 0.11, 0.15, 0.2, 0.3, 0.37, 0.45, 0.5, 0.55, 0.6, 0.62, 0.77, 0.8, 0.83, 0.9 across various takes, not every seed on every take.
- Sheets older than the previous one all reuse the one held separation (an edition of copies with different inks), so the delivery grid shows one image in many colourways, not a history of different prints.
- `pitch` and the spectrum are unused.
- If the cutter sets Take and Scene after frame start, the first frame can show the old take; the driver runs at frame start.
- Next: a recording pass to tune cadence; grippers, lay marks and an ink duct on the bed; a third latch so the delivery lanes show two different past prints; vocals driving one plate's density.

## Dev helpers

`rebuild.py` (exec build.py), `batch.py` (queue of captures that wait, frame by frame, for a press state: full, roll, slide, kick, arrive, keep:<s>; optional globals DESCRIBE and INPUT set those parameters for the whole queue, and it leaves Preview on), `sheet.py` (contact sheet, plain Python with Pillow), `sync_preset.py` (run in TouchDesigner after a rebuild: writes each take's Describe words, `accepts_input` and `as_processor` into preset.json).
