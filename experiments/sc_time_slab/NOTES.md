# sc_time_slab: time-slab objects

## Intent

A real, textured object from the asset pack (on the pack that ships: gramophone, space helmet, hourglass, bronze ribbon knot, lander) tumbles in studio light. We never show it "now": every pixel shows the prop at a different moment of the last second. Which moment is decided by a map made of giant letters (SIGNAL / NOISE, DO NOT / TOUCH) plus a sweeping gradient. So the words are never drawn; they appear only as a tear in time across the object, a region where the prop is a few frames older and therefore rotated differently.

What makes it work:
- The prop must move enough, all the time, that "half a second ago" looks clearly different from "now". Continuous spin from `evolve`, plus kick-driven jolts that travel through the slab as a visible ripple.
- The background must move too (drifting tube bands), otherwise letters only exist where the prop is.
- The resample happens at 1280x720 with a sharp full-resolution map, so letter edges are crisp even though the history is 640x360.
- Red, green and blue read slightly different depths of the past, so moving edges split into colour fringes: time made visible as colour.
- Lighting with a warm key and a fluorescent green rim so the smear has shape, not a grey blob.

## Assets (portability pass, 2026-11-11)

Nothing in this folder names a folder on a machine. `build.py` finds the repository from `td.project.folder`, and every file parameter is an expression on the scaffold's paths module (`mod.paths`, source `experiments/sw_hub/paths_module.py`). The scene commits no precomputed data: it reads only its own shaders and the files below, and nothing is derived from a model or a font ahead of time.

| Used from assets | Where | With no assets |
|---|---|---|
| `<assets>/models/<slug>/model.obj` for the five models named in `DEFAULTS["MODELS"]` | `m_<slug>/mesh` | TouchDesigner's bundled teapot for all five. `build.py` adds a Transform POP (`m_<slug>/fit`) that centres it and makes its longest side 1 unit, as the library's models are. |
| `<assets>/models/<slug>/basecolor.png` for the same five | `m_<slug>/tex`, the material's base colour map | No `tex`, no map: a plain glossy colour per model (cream, blue, red, gold as real metal, green; the last two columns of `MODELS`), so the seed's choice of model still changes the picture. |
| `<assets>/fonts/ArchivoBlack-Regular.ttf` | `words` (take 0's giant phrase), `cap_title` | TouchDesigner's default face. `fitiffat` still fits the phrase to the frame. |
| `<assets>/fonts/ChicagoFLF.ttf` | `wall`, `wall_d` (take 7's crawl) | Default face, same 44 px on the same twelve lines. The pack that ships answers this name with a monospaced face (its `aliases.json`): wider letters, same lines. |
| `<assets>/fonts/BarlowCondensed-Bold.ttf` | `cap_body` (Describe caption sentence) | Default face; it is wider, so `fitiffat` draws the sentence smaller. |

No art, music or feed file is read by the scene itself (the hub supplies the feed).

With no assets (captures `na_take_0.png` to `na_take_7.png`, all on `na_sheet.png`; Describe `na_describe_0.png`, `na_describe_7.png`; Input `na_input_0.png`, `na_input_3.png`): every take works and is plainly the same technique on a spinning glossy teapot. Weak: it is a teapot five times over, told apart only by colour; the teapot is squat (0.47 units tall against 1 wide), so the twist (take 1) and the panels (take 4) have a small subject in a lot of black; the default face is lighter than Archivo Black and Chicago, so take 0's phrase tears thinner strokes and take 7's wall reads as ordinary sans-serif, not as the game's type; the teapot has no texture detail, so the blades macro (take 6) is smooth bands of colour with less to cut.

State at hand-off (05:55): `tdh.errors` empty in both states; `tdh.check` PASS on its third run (first pending, second 37 ms on cook_budget straight after the rebuild, third 7.6 ms); `python -m pytest -q tests/test_portable.py -k sc_time_slab` passes; tox and snapshot written from the last rebuild with Assets blank, Describe off, Input blank, Preview off.

The stand-in is decided when `build.py` runs (it asks the installed module, which sees the COMP's `Assets` parameter): after changing `Assets`, rebuild.

## Fifth pass (Describe and Input finished, 2026-11-11 05:20 to 05:40): read this first

The fourth builder was cut off before saving. A fifth one rebuilt from `build.py`, re-checked every step below with its own captures, and found the fourth pass sound: nothing was removed. Three changes, all inert with Describe off and Input blank:

- **The given picture moves with the music** (`in_move`, a Transform TOP after `in_fit`, mirrored at the edges). The technique shows only what moves, and with an Input the prop's spin, kick and arrival were gone, so a slow picture came through the twist nearly untouched (`i5_take_1` in the fourth-pass state). Now the Input sways sideways with the beat (`inmove` in `TAKES`: 1.5% of its width by default, 10% in the twist, 30% in the strip photograph so the slit scans across it), swells 7% on each kick (`hit_low`) and arrives 25% oversized. `input_sheet.png`: the twist now cuts TEST INPUT into offset slices; the strip is a frieze of squeezed, mirrored letters.
- **Contact sheet in Describe mode sits above the caption** (`slabsample.frag`, `uS.z`): the grid is drawn at 85% so no row is under the words (`describe_take_5.png`). The dither is applied afterwards at full size, so it stays crisp.
- **Twist caption**: "anything that turns" became "anything that moves", which is also true of an Input.

Verified this pass (captures viewed): `p5_take_0` to `7` (rebuild, nothing set: same takes as `take_0` to `7`), `describe_take_0` to `7` and `describe_sheet.png` (seed 0), `input_take_0` to `7` and `input_sheet.png` (test picture, seed 0.37, 3 s after the cut; top left of the sheet is the test picture itself), `di_take_0/2/5/7` and `di_sheet.png` (both, seed 0.62), `off_take_0` to `7` and `off_sheet.png` (Describe off, Input blank, after the last rebuild).

State at hand-off (05:32): `tdh.errors` empty; `tdh.check` PASS on its second run (cook_budget 7.8 ms, 30 active operators, with the instance at 27 fps); `sc_time_slab.tox` and `snapshot/network.json` written from the last rebuild; Describe off, Input blank, Preview off. Turning Describe on cost 0.78 + 0.42 ms for the two caption texts and 0.12 ms for the big phrase, once.

Where Input is strongest: word tear (0), rings (3), blades (6), crawl (7), panels (4), then twist (1). Weakest: the grid at 8x8 (64 cells of 160x90, texture more than picture) and the strip on a short shot. Real frame rate during this pass was 20 to 35 fps.

## Fourth pass (Describe and Input, 2026-11-11)

For the public site (SCENE_BRIEF.md, "Describe mode and Input"). With `Describe` off and `Input` blank the picture goes through three Switch TOPs at index 0 (`plate_sw`, `wall_sw`, `desc_sw`) and one unchanged expression, so every take is as the third pass left it. Nothing was retuned.

### Describe (`parent().par.Describe`)

- **Every take gets a two-line caption along the bottom**: a title (Archivo Black 25 px, yellow) and one sentence (Barlow Condensed Bold 30 px, ivory) over a dark band that fades out upward. In the one-bit take the band is solid black and the text pure white. The words are the take's `describe` row in `TAKES`; `{n}`, `{nn}` and `{slices}` are filled from the shot's seed (panel count, grid cells, twist slices: checked against `dispmap`, 11 levels where the caption said 11). `cap_title`, `cap_body`, `label.frag`, `desc_sw`. The texts read the COMP's Take and Seed directly, so they are drawn once per shot.
- **Take 0** also swaps its giant phrase for one of `D_PHRASES` (SLIT SCAN, TIME SLAB, THE PAST, OLDER HERE, 64 FRAMES, TIME TEAR, NOT NOW, TIME MAP, LATE; the seed picks, same index as the pack's list). Same Text TOP, new string: 0.11 ms.
- **Take 7** crawls `D_WALL` (eighteen short sentences about the mechanism) in place of the pack's wall. Both sheets are made at build time (`wall`, `wall_d`), `wall_sw` picks one.
- Nothing in the Describe words names the prop, because with an Input the prop is not in the picture.
- Captures: `describe_take_0.png` to `describe_take_7.png`, all on `describe_sheet.png` (seed 0); with an Input, `di_sheet.png`.

### Input (`parent().par.Input`)

- **The Input takes the plate's place.** `in_sel` (Select TOP) reads it, `in_fit` makes it 640x360, `plate_sw` feeds it to the slab and the strip canvas in place of prop-over-room. The prop, room, lights and camera do not cook while an Input is set. Everything after the plate is the same: the time maps, the resample, the panels, the grid, the strip, the grade.
- `inp` (Constant CHOP, channel `on`) is 1 only when Input names an existing TOP outside this COMP; anything else (blank, a typo, our own `out1`) leaves the scene on its own plate with no error.
- The Bloom TOP is skipped while an Input is set: another scene's picture is already graded, and the second bloom washed the test picture to cream (`i1_sheet.png` with, `i3_sheet.png` without).
- `head_driver` counts the Input in the shot key, so changing it restarts the look-back and no prop plates show through.
- All eight takes use it. Captures with `/project1/sw_testcard/out1`: `i3_sheet.png` (seed 0.37, 0.8 s after the cut), `di_sheet.png` (with Describe).

### A fault found on the way (fixed, not a look change)

`head_driver` advanced the slab only if `absTime.frame - out1.cookAbsFrame <= 1`. With eighteen agents in the instance the real rate fell to 8 to 17 fps and TouchDesigner skipped frame numbers (7 at a time), so the test never held: the slab stood still, no take could look back, and every take showed the plain plate (`i2_sheet.png`: no letters in takes 0 and 7, 20 of 64 grid cells). It now compares with the last frame the driver itself ran. At a steady 60 fps the two tests are the same.

### Weak, honestly

- **The technique shows only what moves.** (Fourth-pass state; the fifth pass gave the Input its own sway and kick, see above.) A slow or still Input came out nearly untouched in the map takes: the test picture turns slowly, and the twist (take 1) showed only small steps on the letters (`i3_take_1.png`). A fast scene will be cut up far more than the test picture suggests, which nobody has seen.
- **The Input is stored at 640x360**, so fine text in another scene goes soft, most in the regions that are "now" where there is nothing to hide it.
- **Panels (take 4) show only the middle third to fifth of the Input**, and the grid's cells at 8x8 are 160x90: the Input is recognisable as texture, not readable.
- **Strip photograph on a short shot**: as before, the strip needs 3.5 s at 60 fps to cross. At 8 fps it had moved 40 px in 2.5 s (`describe_take_2.png`), because it scrolls per frame.
- **Take 0's big Describe words read only where something moves**: on the prop you get "SLI / SCA" (`describe_take_0.png`), as with the pack's phrases. The caption carries the explanation.
- **The caption covers the bottom 100 px**, including the foot of the crawl and of the panels (the contact sheet now moves up out of its way, fifth pass).
- A Select TOP pulls its source: reading another scene's `out1` cooks that scene's output once a frame if nothing else is. I do not force-cook it.
- All Describe and Input captures were taken at 8 to 17 fps real, not 60: look-back is in seconds so depths are right, but everything stored is coarser in time than it will be on a quiet machine.
- Still judged from stills.

## Third pass (takes, 2026-11-10 evening)

The first cut was too repetitive. This scene's part in that: every time the cutter came back it showed one chrome prop mid-frame with a word cut into it. A third builder gave it eight takes. Where this section and the older text below disagree, this section is current.

The technique is unchanged in kind: a plate (prop over a moving room) is stored over time and the picture is put together from different moments of it. What changes between takes is **how the past is laid out across the frame**, plus camera, prop, room and grade. All of it is in the `TAKES` table at the top of `build.py`; the row used is `op('shot')['take'] % 8`. A tuple in a row means the shot's seed picks one.

### The takes (captures `take_0.png` to `take_7.png`, seed 0; all on `contact_sheet.png`)

| Take | Name | What you see |
|---|---|---|
| 0 | word_tear | The earlier look: prop off centre in a dark room, a giant phrase cut into it as a tear in time. Seed: phrase (nine), model, room (green, red, blue), side. |
| 1 | twist | Empty black room, white tubes, low camera. A clean ramp of time cut into 10 to 27 slices: the prop spins 150 degrees a beat and becomes a stack of discs each turned a different amount. Seed: slice count, ramp up or down, or sideways (vertical slices). No text. |
| 2 | strip_photo | A strip photograph. A canvas scrolls 6 px a frame and is fed from one vertical slit of the plate, so x is time: the turning prop is unrolled into a chrome frieze across the whole frame. Each shot opens on the ordinary prop and the strip wipes across it in about 3.5 s (`take_2_wipe.png` at 1.6 s, `take_2.png` at 4.6 s). No text. |
| 3 | rings | Camera 58 degrees above, big prop, red room. Stepped rings of past round an off-centre point; a new ring leaves the centre on every beat, kicks throw alternate rings further back. No text. |
| 4 | triptych | 3, 4 or 5 tall panels (seed), the same crop of the plate at evenly spaced moments of the last second, each under its own gel (red, yellow, blue, green, pink). Every kick moves "now" one panel along. No text. |
| 5 | contact_sheet | 4x4, 6x6 or 8x8 grid (seed), every cell the whole plate a little older, reading order from top left; one-bit ordered dither, black and white (seed: empty black or daylight room, inverted or not). After a cut the cells fill in one by one. No text. |
| 6 | blades_macro | Long lens (17 degrees) on a part of the prop, widest colour split. Slanted blades of time (seed: angle, 7 to 22 of them), each at one of four depths, reshuffled by every kick. Reads as abstract chrome and rainbow. No text. |
| 7 | phrase_crawl | Beige wall, daylight grade, no bloom. Twelve lines of small Chicago phrases crawl up the frame as the time map: text as texture, lines start mid-phrase, alternate lines look back further. Prop large and off to one side. |

Only take 0 has centred words (one of nine two-line phrases).

Seed inside a take: four unrelated numbers are derived from it (`sd` CHOP: s1 to s4) and pick the room, model, phrase, panel or grid count, slice count, blade angle, ring centre, side, and the macro camera's aim. The model choice is also shifted by the take number so that two takes with similar seeds start on different props. `arr_sheet.png` and `g_sheet.png` show all takes at seed 0.37 against `contact_sheet.png` at seed 0.

### The first half second (`op('shot')['age']`)

- The prop arrives 45% oversized and 200 degrees round, and settles in about half a second (`tk` channel `arrive` = exp(-6 age)); the camera swings in 14 degrees; the grade flares.
- The past is rationed by the shot: the sampler never reads further back than the number of plates stored since this shot's Take and Seed were set (`head` channel `since`). So a cut never shows plates from an earlier take, and the time map opens up over the first second: words tear open, grid cells fill, slices start to turn. If the cutter warmed the scene before the cut, that history is already there and only the pop, whip and flare remain.
- `arr_sheet.png`: every take 0.25 s after a cut from a different take.

### What else changed

- `head_driver` now advances the slab whenever `out1` cooked this frame or last, whoever asked. Before, it only ran with Preview on or as the hub's scene, so when the cutter warmed the scene or used it as a layer (it cooks `out1` directly) the slab stood still.
- `strip.frag`, `strip_fb`, `strip_over`: the strip photograph. It is a feedback canvas, not the slab, because 62 frames across 1280 px is 20 px a frame and looked like mush (c_take_2_s00); the canvas keeps 3.5 s at full sharpness (whole-pixel shift with texelFetch).
- Rooms are chosen by the take and seed, not the section: two new ones in `bg.frag`, 4 daylight cyclorama and 5 empty black. `env.frag` has a matching white cyclorama.
- `grade.frag` has three grades: dark studio, daylight, one-bit dither. Bright and one-bit takes skip the Bloom TOP through a Switch.
- Model and phrase are held for the shot (seed), no longer swapped by the section mid-shot. The section still sets the tube layout and slant.
- Flipped maps (letters are "now") are gone: the words stop reading (r15, g_take_0_s37).
- `sweep_takes.py` captures takes without blocking TouchDesigner: it cuts to each take as the cutter does, waits, captures, and records the feed and the cook cost.

### Does it follow the music

`pairs_sheet.png` puts each take at two moments side by side (`take_N` and `take_bN`, same seed). What differs and why:
- take 0: letter depth follows `energy` and `bass` (take_0: 0.41 and 0.53; take_b0: 0.58 and 0.01), and the prop is at a different turn.
- take 1: take_b1 was caught on a kick (`hit_low` 0.60): the kick strips cut model 4's base; take_1 (no kick) has only the slices.
- take 3: `h_sheet.png` is four captures two seconds apart. With `bass` 1.25 and `energy` 0.75 (h_take_3_s001, the hero) the rings are deep and separate into rainbow bands; with `bass` 0.01 and `energy` 0.46 (s003) model 0 is nearly whole with one ring through it.
- take 4: every kick moves which panel is "now", so the three copies of model 0 sit at different turns in the two captures.
- take 6: blades reshuffle on kicks; take 7: letters cut deeper with `pulse` (0.12 against 0.69) and the crawl has moved with `bar_pos`.
- take 2: the strip is the music written out sideways: anything that pulses in the plate becomes a vertical bar. Not checked against the feed column by column.
- Everything in the table under "What drives what" below still applies to the plate, except that model, phrase and room no longer follow `section`.

### Cost (measured by `sweep_takes.py` from the operators that cooked that frame)

Per take, quiet readings: CPU 1.0 to 1.5 ms. GPU without the `slab` TOP's own reading: 0.4 to 0.7 ms. The strip take does not cook the slab at all: 0.6 ms GPU.

The Texture 3D TOP `slab` then adds a `gpuCookTime` that is usually 5.4 to 5.7 ms, which is why `tdh.check` reads 7 to 10 ms. That number is not this scene's cost, as far as I can show:
- it is the same with 16 layers as with 64 (5.47 against 5.68 ms) and with the Render TOP disconnected (5.61 ms), so it is neither the size of the array nor the render;
- in one sweep it was under 0.4 ms in three takes running (take_4, take_5, take_6 at 20:00), with nothing changed;
- later it read 39 and 96 ms while the measured frame rate stayed at 60.2 fps, which a blocking 39 ms cook cannot do.
So it follows what the whole GPU is doing (about twenty scene COMPs in this instance tonight, six with Preview on when I looked), not what this TOP does. What it really costs alone could not be measured without stopping other agents' scenes. The earlier passes' "5.4 to 6.0 ms, not explained" is this.

`tdh.check`: passed at 9.7 ms before the last rebuild and at 7.7 ms after it; the four runs after that failed on cook_budget only (44, 51, 98, 41 ms), each time with `slab` reporting nearly all of it and every other check passing. `checks.json` still has the earlier builders' 12 ms limit. CPU readings also jump to 3 to 4 ms per GLSL TOP while other agents rebuild (one sweep read 24 ms).

Small waste left in: `sd` and `tk` read the `shot` CHOP, which cooks every frame because of `age`, so they, `words`, `words_soft` and `envmap` re-cook every frame (about 0.4 ms together) though they only change at a cut. Reading the COMP's Take and Seed parameters directly would stop that. A new phrase at a cut costs 0.11 ms (measured), so there is no hitch from the text.

### Weak, honestly

- **Still judged from stills.** Nobody has watched any take move. The strip photograph scrolls at 360 px a second; the twist turns 310 degrees a second. Both may be too busy or just right; I cannot tell from frames.
- **Take 1 (twist) is the weakest.** It reads as model 4 with its parts sliced and offset, not as the helix I wanted; with model 0 or model 1 it is less clear still. It is also the emptiest frame.
- **Take 6 (blades_macro)** is handsome but abstract: you cannot tell which prop it is.
- **Take 7** is busy and a little muddy in beige; the words read, the prop less so.
- **Take 2 on a short shot**: the strip needs 3.5 s to cross the frame, so a 2 s shot is mostly the plain prop with a band of strip at one edge (unless the cutter warmed it).
- **Seed 0 favours model 0** less than before (model shifts with the take) but takes 0, 4 and 5 still start on it.
- Take 5 at 8x8 is texture more than picture: 64 cells of 160x90.
- Daylight is only in take 7 (beige) and one seed option of take 5. A bright strip-photograph was tried and looked like beige mush (b_take_2, c_take_2_s10), so that take went back to a dark room.
- The cutter fights a sweep: when it cuts to this scene or layers it during a sweep, the capture shows its take, not the one under test (take_b5 has one model 0 cell and thirteen of model 4 for that reason). `take_held` in the sweep's record catches most of it, not all.

## Second pass (art direction, 2026-11-10)

A second builder judged the scene from six captures (r01 to r06) and changed it. Where this section and the older text below disagree, this section is current (and the third pass above is newer still).

What was wrong: the tubes were the hero and the prop was a small, flat-lit beige blob (r04_plate); the letters read as dim patches in a busy wall; rainbow fringes everywhere; the prop tumbled onto its underside so it was often unrecognisable; bass sat near zero so the letters rarely moved with the music.

What changed:
- **The prop is the hero.** About 1.3x larger, just off centre (tx 0.5, was 0.8). It no longer accumulates X rotation from snares: it stays upright enough to recognise, spins on Y, and nods 30 degrees on each snare (`hit_mid`) and springs back.
- **Real reflections.** `shaders/env.frag` draws an equirectangular black studio with tall tubes and a softbox; an Environment Light (`light_env`) uses it, rotating slowly with `evolve`. Materials are glossy (metallic 0.35, roughness 0.26); model 3 is real metal (0.95, 0.2). Key light down to 2.0, fill to 0.5, so there is contrast.
- **Stark rooms with one accent each.** Walls are near black (the beige room stays beige), fewer and thinner tubes, each room has a pale base tube colour and one accent (green, amber-on-blue, red). A pool of accent light sits on the wall behind the prop in the dark rooms. Grade has an S-curve and much less shadow lift.
- **Kicks are visible.** Time-quake in `dispmap.frag`: each kick drops a new random set of horizontal strips 0.45 of the slab into the past for as long as `hit_low` lasts (inside letters they jump toward now instead). Letter depth now follows `energy` as well as `bass`.
- **Loop-safe hits.** `head_driver` accumulates `hits_low`/`hits_mid` into the `acc` Constant CHOP and ignores the backwards step at the track loop. Checked across the loop: feed `hits_low` went 443 to 7, `acc` kept rising (22), no whip (r10).
- **No first-showing hitch.** `build()` force-cooks every model's mesh, texture and material, so models no longer load (25 to 60 ms) the first time their section comes up.
- Colour split narrowed (R, G, B at 1.0, 0.955, 0.91 s); section index is passed to shaders as an integer (the feed's `section` is briefly fractional at a change: 16.667 was read).

Second-pass captures (all viewed): r01 to r06 before; r07 to r23 after. Best: `r16_out` (now `hero.png`: model 4, beige room, phrase 4, kick 0.64 just after a section change, so the quake strips show the previous dark room), `r20_out` (model 1, phrase 2, beige), `r11_out`/`r12_out`/`r23_out` (model 3), `r07_out` (model 1). Weakest: `r19_out` (blue room, model 4 shredded by a kick, sparse and dark), `r15_out` (flipped map, words hard to read).

Still weak after the second pass:
- Still judged from stills only. Nobody has watched it move.
- Flipped-map sections (section mod 3 == 2) are the weakest: the words are hard to read (r15) and the prop outside the letters can vanish (r10).
- In the dark rooms the words exist almost only on the prop; across the wall they are a faint offset of slats and tubes. That is a choice (prop over wall) but the phrase is not always legible.
- model 3's highlights clip to white with bloom (r11); the beige room is hazy under bloom (r17).
- model 0's dark back or underside faces the camera for part of each turn (r14).
- Cook: `tdh.check` passes at 7.1 to 7.9 ms, of which `slab` reports 5.4 to 6.0 ms GPU. That reading did not change with the environment map locked or the environment light removed from the render, so it is not from this pass's additions; the first builder measured 2.3 ms total earlier in the day with fewer scenes running. Not explained.
- `tdh.check` straight after a rebuild still fails cook_budget once (78 ms: the forced model loads); the next two runs pass.

## Technique (as first built, 2026-11-10, TouchDesigner 2025.33230)

`build.py` builds everything; GLSL is in `shaders/`.

1. **Plate, 640x360.** Five pack models (the five models named in `DEFAULTS["MODELS"]`), one rendered at a time, PBR with a warm key, a fluorescent green rim and a blue fill. Rendered over `bg.frag`: drifting slanted tubes and sliding blind slats on a wall whose colour scheme changes with the section.
2. **Slab.** `slab` is a Texture 3D TOP in 2D-array mode, 64 layers of 640x360 8-bit. It runs as our own ring: `replacesingle` on, `replaceindex` = the `head` CHOP, which `head_driver` advances once per frame. The same DAT measures the real frame rate.
3. **Time map, 1280x720.** `dispmap.frag`: a triangle-wave gradient that sweeps up the frame once per bar, a bass swell from the centre, plus the big Archivo Black words (Text TOP, slightly blurred) as a step into the past. Every third section the map is flipped, so the letters are "now" and the room is the past.
4. **Resample, 1280x720.** `slabsample.frag` reads the array directly (`sTD2DArrayInputs[0]`), blends the two nearest layers, and reads R, G and B at 1.0 s, 0.94 s and 0.88 s of maximum look-back. Doing this at output resolution is the "clean upscale": letter edges are full-resolution even though the history is half-resolution.
5. **Bloom TOP, then `grade.frag`**: ink-green shadows, cream highlights, vignette, faint scanlines.

## What drives what

| Feed channel | Visual |
|---|---|
| `evolve` | steady Y spin of the prop (70 degrees per unit), drift of the tubes, slow turn of the reflected environment |
| `hits_low` (through a 0.07 s Lag) | each kick snaps the prop 38 degrees round Y; the snap then travels through the letters and gradient as they catch up |
| `hit_mid` | each snare nods the prop 30 degrees in X, then it springs back |
| `hit_low` | prop scale kick (+10%); time-quake: random horizontal strips drop 0.45 of the slab into the past while the hit lasts |
| `hit_mid`, `pulse` | rim light brightness |
| `beat_pos` | vertical bounce (one per two beats) and Z roll |
| `bar_pos`, `bar` | X tumble; slats slide two spacings per bar; the time gradient sweeps the frame once per bar |
| `bass` | how far into the past the letters reach, and a central swell |
| `energy` | letter depth, gradient depth, tube and slat brightness, wall pool |
| `pulse` | tube flash, letter depth kick, overall +10% exposure. Because the flash is stored in the slab, the letters flash late: they show the previous beat |
| `section` | model (mod 5), phrase (mod 5), room palette (mod 4), map flip (mod 3), which side the prop sits on (mod 2), tube layout and gradient direction |
| `hit_high` | tiny exposure lift (barely visible) |

## State at hand-off

- `tdh.errors`: empty. `tdh.check`: PASS on the run after the build settled (cook_budget 2.3 ms, 20 active ops). The run that immediately follows a rebuild reports 30 ms because it counts the one-off model and texture loads; while other scenes were compiling, every GLSL TOP in the project (not only ours) also showed about 3 ms of CPU each.
- `captures/hero.png` was `25_out.png` after the first build; it is now `r16_out.png` (see the second-pass section).
- `Preview` is off. `sc_time_slab.tox` and `snapshot/network.json` were written from the final build.

## What is weak or unverified

- **Never seen in motion.** Everything was judged from stills. The kick jolt was caught mid-flight once (22: `jolt` at 357.77 on its way to 358), but whether the ripple through the letters reads as a ripple at speed is not verified.
- **Bass was near zero in most captures** (0.01 to 0.04; 0.45, 0.81 and 1.02 in three). The letters' depth therefore sat at its floor most of the time. Capture 11 (bass 1.02) shows the deep end: inside the letters the prop becomes an unreadable rainbow smear.
- **The prop is often hard to recognise.** With a 1 s slab and this much spin, large parts of it are smeared; in flipped sections the whole room is the past and only the letters are sharp. That is the idea, but in some frames (10, 16, 20) the object is just coloured streaks.
- **Track loop.** `hits_low` and `hits_mid` reset at the loop, so the Lag whips the prop back hundreds of turns in a few frames (26 was taken just after the loop). A one-off flash per 249 s; not fixed.
- **Thin moving lines dim in the past**: the slats and tube cores lose contrast inside deep-time regions because R, G and B read different moments and two layers are blended. I chased this as a suspected sampling bug; per-mask medians of sampler output and the stored layers agree, so it is inherent, not a fault.
- **Model 3 (the metal one)** renders dull (no environment map; metallic lowered to 0.25 so it is not a black silhouette). Seen once after that change only in the beige room before it (21), not re-captured after.
- The beige room was retuned twice (23 was blown out); only 24 shows the final values.
- `spectrum`, `vocals` and `pitch` are unused.

## Log (newest first)

Generic defaults (2026-11-11 06:55 to 07:15). Sheets: ref_a_, ref_b_ (before, private pack), gen_, g2_ (generic pack), pv_a_, pv_b_ (after, private pack).

- **2026-11-11** The defaults in `build.py` are generic: the models, which models each take may show, the nine big phrases and the eighteen wall lines now sit in one dict, `DEFAULTS`, read through `scene_words()`. The originals live in a private pack's `scenes/sc_time_slab/words.json` under the same names (`MODELS`, `TAKE_MODELS`, `PHRASES`, `WALL`), so a build on that pack is as it was. In log entries older than this one, "model 0" to "model 4" and "phrase 1" to "phrase 9" are rows of that pack's lists, not of the defaults.
- **gen_a_take_0 to 7, gen_take_N_sNNN** first generic build (gramophone, space helmet, hourglass, ribbon knot, lander). The hourglass at 2.3 was cut off top and bottom in the strip photograph (gen_take_2_s370), the lander at 2.1 lost its dish in the twist (gen_take_1_s370), and the helmet is wider than a panel in the five-panel triptych (gen_take_4_s710). Scales to 2.0, 1.9, 1.9, 2.1, 1.9; the triptych shows the lander in place of the helmet. From above the helmet is a blown-out white dome (g2_take_3_s900): the rings show the ribbon knot instead.
- `import_model` (scene_lib) decides whether to wire the base colour map by asking the default pack, not the scene's own `Assets` pack; `build.py` wires it again from the scene's paths module. Without that, a scene pointed at another pack by its `Assets` parameter would be untextured.
- The big phrases hold real line breaks now (they held a backslash and an n, replaced in the expression).

Portability pass (2026-11-11 05:50 to 06:00). Sheets: ref_, pa_, na_, pb_.

- **pb_take_0 to 7, pb_sheet** Assets blank again, rebuilt: as ref_sheet. **pb_describe_0, pb_input_3** Describe and Input on the real assets. Tox and snapshot saved from this build.
- **na_take_0 to 7, na_sheet, na_describe_0, na_describe_7, na_input_0, na_input_3, na_di_sheet** `Assets` pointed at the empty folder `captures/_noassets`, rebuilt: teapots in five colours, default face, `tdh.errors` empty. See "Assets" above.
- **pa_take_0 to 7, pa_sheet** rebuilt from the converted `build.py` with the real assets: same models, rooms, phrases and type as ref_sheet (the moments of the track differ).
- **ref_take_0 to 7, ref_sheet** the scene as found, seed 0, 2 s after each cut, before anything was changed.
- Changed: `build.py` (no literal folders; `mod.paths` expressions for shader files, fonts, models; teapot fit and colours when the library is absent), the usage comment in `sweep_takes.py`. No shader, take or look was changed.


Fifth pass (Describe and Input finished, 2026-11-11). Sheets: describe_, input_, di_, off_ (these replace the fourth pass's files of the same name).

- **off_take_0 to off_take_7, off_sheet** after the last rebuild, Describe off, Input blank: the takes as in take_0 to take_7. Tox and snapshot saved from this build. Preview off.
- **di_take_0, 2, 5, 7, di_sheet** Describe with the test picture, seed 0.62: TIME SLAB torn through TEST INPUT, 16 dithered cells above the caption, the crawl's sentences across it.
- **input_take_0 to 7, input_sheet** the Input with `in_move`: every take cuts the test picture; twist and strip now do too.
- **i6_take_0 to 7** first sweep with `in_move`. **i5_take_0 to 7** the fourth pass's Input as found: twist nearly untouched.
- **describe_take_0 to 7, describe_sheet** final words; contact sheet above its caption (d5_take_5: bottom row was under the band).
- **d5_take_0 to 7** the fourth pass's Describe as found: all captions legible at 1280x720.
- **p5_take_0 to 7** rebuilt from build.py as found, nothing set: same eight takes.

Fourth pass (Describe and Input, 2026-11-11). Sheets: s1_, d1_, i1_ to i3_.

- **off_take_0 to off_take_7, off_sheet** final rebuild from build.py, Describe off, Input blank: the takes as before.
- **di_sheet** Describe and Input together: SLIT SCAN torn through TEST INPUT (take 0), the crawl's sentences over it (take 7), 16 dithered cells (take 5), rings, strip.
- **describe_take_0 to 7, describe_sheet** final Describe words, seed 0. Sentences cut to under about 100 characters so they stay at 30 px (d1_sheet: the longer ones had shrunk to about 22 px).
- **i3_sheet** Input after the `head_driver` fix: word tear, rings, blades and crawl all cut the test picture; twist barely.
- **i2_sheet** Input with captions, slab standing still (see the fault above): the picture came through untouched.
- **i1_sheet** first Input sweep, with bloom: washed out. Bloom now skipped with an Input.
- **d1_take_0 to 7, d1_sheet** first Describe sweep. The first Describe frame after a rebuild cost 63 ms (the caption shader compiling); build.py now cooks `label` five frames after building.
- **s1_sheet** rebuilt on the new scaffold with nothing else changed: takes 0, 3, 5, 7 as in contact_sheet.png.

Third pass (takes). Sheets: a_ to h_, arr_, contact_sheet, pairs_sheet.

- **final_rebuild_take6_s52** clean rebuild from build.py, take 6 at seed 0.52: red room, upright blades, full rainbow. Tox and snapshot saved from this build. Preview off.
- **h_take_3_s000 to s003, h_sheet** four rings captures two seconds apart; s001 (bass 1.25) is `hero.png` and `take_3.png`. The first take_3 of this sweep was the cutter's own shot (it layered this scene at that moment).
- **take_0 to take_7, take_b0 to take_b7, pairs_sheet** final takes at seed 0, twice. take_b5 is spoiled by the cutter (see Weak).
- `head_driver` driven by `out1` cooking, not by Preview or the hub's scene, after reading the cutter's driver: it cooks `out1` directly when warming or layering, and the slab stood still.
- **take_3, take_4 of 19:57** rings without model 3 (from above it is its dark base), triptych without model 4 (dim under gels). Model choice shifted by take number.
- **late_take_2** strip after 4.6 s: full frieze. Two earlier tries showed 18% of it: the cutter had cut to this scene mid-capture and reset the canvas (its log confirmed 117.71 s).
- **g_sheet** (seed 0.37) twist was a plain model 4: the frame count per shot reset whenever more than 3 frames were dropped, so nothing could look back. Threshold now 30 frames. Then twist to 150 degrees a beat, scale 1.3.
- **arr_sheet** first version: 0.25 s after a cut the left three quarters of the twist was still the previous take's red room (arr_take_1). Shot age times frame rate overshoots when frames drop; now counted in stored plates (`head` channel `since`). Second version: clean.
- **d_take_2_s00** strip photograph as a scrolling feedback canvas: the first frame of the round that looked new. Then: unexposed canvas shows the live plate, reset per shot, so the strip wipes in.
- **c_sheet** strip photograph read from the slab: conveyor of props drawn whole was beige mush in daylight (c_take_2_s10), unrolled prop was 20 px blocks (c_take_2_s00). Tumble on X for the sideways ramp showed model 0's black underside (d_take_1_s31): removed.
- **b_sheet** all eight takes for the first time. Twist barely twisted (spin too slow): tempo-locked spin and slices added. Rings: bigger prop, tighter rings.
- **a_sheet** first sweep; takes 5 to 7 were the cutter's take, not mine (it had cut to the scene). Added the lock to `sweep_takes.py`.
- **v00_a, v00_b, v00_c** the scene as found; **v01_rebuilt** rebuilt on the new scaffold with nothing else changed: same look (model 3, phrase 1, green room).

- **r22, r23** final rebuild from build.py. r22: model 3, blue room, rainbow coil. r23: model 3, green studio, kick 0.56, quake strips. Checks pass twice (7.3, 7.9 ms).
- **r20, r21** accent pool on the wall behind the prop in dark rooms (r19 was sparse). r20: model 1, beige, phrase 2. r21: model 2, red room, phrase 3.
- **r16 to r19** models preloaded in build() (each first showing had cost a 25 to 60 ms cook and failed the check at every new model). r16 is the hero.
- **r15** key light 2.6 to 2.0 and environment 1.0 to 0.85 (r14: model 0 blown out in the beige room).
- **r10 to r13** more tubes lit (0.30 threshold, was 0.45) and brighter slats, because in r08/r09 the wall was so dark the words existed only on the prop. r10 crosses the track loop: no whip. r13: model 4, kick strips in the O.
- **r07 to r09** second-pass rebuild: env map + environment light, glossy materials, bigger centred prop, nod instead of tumble, dark rooms with accents, time-quake, loop-safe hit accumulator, S-curve grade. r07: model 1 reads clearly with phrase 2 cut into it.
- **r01 to r06** second builder's look at the first build before changing anything: tubes dominate, prop is a flat beige blob (r04_plate), letters are dim patches.

- **24, 25, 26** final build. 24: beige room after dimming, model 1, phrase 2 (section 41, flipped map). 25: red-black room, model 2 clearly readable, phrase 3 cut into it (section 42). 26: just after the track loop, hits counters reset, prop whipped into a smear.
- **23** beige room first values: washed out (mean 0.6), bloom lifted the whole wall. Dimmed wall to 0.17..0.40.
- **22** caught on a kick (hit_low 0.6): model 1 with phrase 2, letters hold the pre-kick pose.
- **21** added room palettes by section (green-black, beige, red-black, CRT blue) and lit more tubes, because quiet sections with two lit tubes looked empty (19, 20). Model 3 was a black silhouette on beige.
- **17 to 20** motion set back to moderate (spin 95, tumble over two bars). 17: model 0 readable inside phrase 1. 19, 20: model 4, flipped map, room nearly empty.
- **14 to 16** look-back made seconds-based (`head` CHOP carries measured fps; depth = seconds x fps, capped at 62 frames) after I misread the frame rate as 20 fps from the track time; the measured rate is 60. I had doubled the motion speeds on that wrong reading: 16 shows the result, model 0 is a white streak. 15 (model 1, phrase 2, green room) is the best single frame of the session but belongs to those faster settings.
- **11 to 13** bloom threshold measured (0.3 adds nothing, 0.01 adds 60% to the mean; using 0.05), colour split narrowed from 14 frames to about 7 because the prop turned to pure rainbow (10).
- **07 to 10** bloom added (07 at default: haze), flipped-map sections added, text auto-fit (WORLD! was clipped in 05).
- **04 to 06** more motion (bounce, faster tubes), wider camera. 06: first frame that looked like the goal.
- **03** camera was 38 degrees horizontal, so the prop overflowed the frame (02_plate); set 60 and rescaled. Background got slats so the map tears in both directions.
- **02** replaced three Time Machine TOPs with one GLSL pass reading the array, layers blended. Fringes appear, stair-steps go.
- **01** first version with Texture 3D + Time Machine TOP: works, but the Time Machine picks the nearest layer, which gives blocky stair-steps along the gradient (01_out), and one map cannot give different depths per colour.

## Next

- Watch every take at speed, twist and strip first.
- Twist: try a prop built for it (something long and asymmetric upright), or drop the slices to 6 and double the look-back.
- A bright take that works: the daylight room needs props with colour, not chrome on cream.
- Read Take and Seed from the COMP parameters in `sd` and `tk` to stop the per-frame re-cooks.
- Find out what the slab's GPU reading is with the other scenes stopped.
- Watch it at speed and tune jolt size and Lag against what the eye catches.
- Make the hit counters loop-safe (accumulate deltas, ignore negative steps).
- Give the props an environment map so the metal and glass models have something to reflect.
- Let `vocals` or `pitch` bend the time map (for example a horizontal band at a height set by pitch).
- Try the slab as depth as well as time: use the same map to offset UV slightly, so letters also refract in space.
