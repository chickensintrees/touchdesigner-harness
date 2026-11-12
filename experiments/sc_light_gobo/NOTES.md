# sc_light_gobo: fluorescent fog and shadow type

## Intent

Light is the subject. A dark room at night, full of fog, with hard light sources: a projector, fluorescent tubes, one tungsten lamp. The fog is ray-marched, and at every step the shader asks whether the light reaches that point through a **gobo** (occluder mask): the scene's phrases, venetian blinds, a ruled sheet's grid, a spoked wheel, and the true shadow of a library model rendered from the light's point of view (a shadow map). Words and objects are written as beams and shadows hanging in the air, not drawn on a surface. It works when you can see the shafts as solid things in space, the blacks stay black, and the lights behave like real ballasts with the music.

## Inputs / outputs
- Inputs: hub audio feed (`hub`), `shot` (take, seed, age), and optionally the TOP named by the `Input` parameter (see "Describe and Input").
- Output TOP: `out1`, 1280x720.

## Technique

- `tk` (Constant CHOP): every per-take number, one channel each, picked by `parent().par.Take % 11` from the `TAKES` table in build.py. `rig`: camera and projector after drift, bar sweep and seed.
- Library models are Geometry COMPs placed per take. (With no model library each is the bundled teapot fitted to the model's box: see "Assets".) Two Render TOPs draw them with one override GLSL MAT (`shaders/gbuf_*.glsl`) that **projects with our own camera maths**, not TouchDesigner's: `gb_cam` from the camera (world normal + distance from the eye, 1280x720) and `gb_lgt` from the projector (distance from the light, 1024x1024: the shadow map). Because the vertex shader and the ray-march build their basis from the same eye/target/tan(half fov), mesh pixels and marched rays line up exactly with no matrix plumbing.
- `beam` (`shaders/beam.frag`, GLSL TOP, HDR): room = analytic box; solid hit = nearer of room and G-buffer; then at most 64 fog steps with a white-noise start offset per pixel per frame. Each step sums: projector (cone x gobo x shadow map x forward-scattering phase), up to 8 tubes (line lights with a louvre mask), the tungsten lamp (cone), a little ambient. Fog density is two octaves of simplex noise, the second warped by the first and both advected by `evolve`. Gobo modes: 0 open, 1 one phrase from the text atlas, 2 venetian blinds, 3 ruled grid, 4 tiled phrases, 5 spoked wheel, 6 comb of slits; any of 1 to 5 can be inverted.
- Slit planes (take 2): each of 5 thin planes of light is intersected analytically with the camera ray, like the sheets below but along the beam instead of across it, so the plane shows a crisp slice of the fog noise instead of a grainy slab. The main march skips the projector in this mode.
- Tubes light the fog in their own 12-sample loop (`tubeFog`, branch-free), not in the main march. Bare-tube takes mirror the tubes in the floor (one reflected ray against each segment).
- "Sheets" (take 0): besides the fog, up to 12 infinitely thin layers of smoke across the beam are intersected analytically, so each layer shows the whole gobo image crisply: the phrase hangs in the air several times over, and the shadow of whatever stands in the beam is cut out of each copy.
- `grade` (`shaders/grade.frag`): quarter-size blur added as glow, tone curve on the peak channel (keeps colour, blacks stay black), grain, vignette, optional 1-bit Bayer dither.

## Takes (`captures/take_<n>.png`, contact sheet `captures/takes_sheet.png`)

Eleven since the second pass (2026-11-10 evening). The first six visits are six different palettes and compositions. What stands in each take is the pack's choice (`DEFAULTS['MODELS']` in build.py, see "Content"); the table names the scene's own defaults.

| n | name | picture |
|---|---|---|
| 0 | WORDS IN AIR | blue projector beam seen at an angle; the phrase repeated on layers of smoke receding to the wall, an amphora in the beam, two dim green tubes |
| 1 | BLINDS | side-on: green venetian-blind shafts seen edge-on as hard diagonal blades, slat pattern on the carpet, backlit gramophone (hero) |
| 2 | RED PLANES | no beam: a comb of thin red light planes, each showing a swirling cross-section of the smoke like a red sky, five objects a black skyline, a laser line across the floor |
| 3 | LAMP CONE | close: one tungsten cone with smoke curling in it over an astrolabe and a stack of solids, everything else black |
| 4 | FLOOR TYPE | straight down: tiled phrases thrown across the carpet at a raking angle, streaked beams, the shadows of a pierced stone and a traffic cone |
| 5 | GRID WINDOW | wide and high: a ruled grid as planes of blue light over a big dark floor, a tiny lander under a warm lamp, a duck, an hourglass; ceiling tubes strike green |
| 6 | LEANING TUBES | bare tubes (green, blue, one warm) propped on a wall and mirrored in a polished floor, crystal cluster silhouette, no projector |
| 7 | ONE BIT | the whole machine dithered to black and white: a spoked wheel turning behind a bust's silhouette, its shadow volume coming at the camera |
| 8 | SHADOW PLAY | negative: a bright paper-coloured room printed with dark phrases over wall, floor and ceiling, a turning wire cage and its shadow |
| 9 | CORRIDOR | no projector: ceiling tubes receding down a narrow corridor, a pulse of light racing toward the camera every two beats, a stack of solids and a traffic cone in silhouette |
| 10 | FLOOR TUBE | macro at carpet level: one tube lying on the floor beside a small hourglass throws a looped ribbon's giant shadow up the wall |

`seed` changes inside a take: camera distance (0.84 to 1.16) and orbit phase, which phrase, gobo tilt, yaw of spinning models, tube colours and lengths (take 6).

## Channel to visual mapping

| Feed | Drives |
|---|---|
| `hit_low`, `hit_mid` (+ `hits_low`, `hits_mid`) | which tubes strike: about half the tubes, chosen afresh by each hit count, stutter at 24 Hz while the hit envelope is up, then hold bright on a 0.8 s tail (`slow` Lag CHOP) |
| `hit_mid`, `pulse` | projector intensity kick (+60% on a snare, +30% on the beat) |
| `hit_low` tail, `bass` | fog density breathes/puffs |
| `bar_pos` | projector target sweeps (period 4 bars; 2 bars vertically), blind slats open and close (2 bars) |
| `beat_pos` | smoke layers travel down the beam (take 0), tiled rows slide against each other (takes 4, 8), wheel turns (take 7), slit planes sweep (take 2), the corridor's pulse of light runs one length every two beats (take 9) |
| `hits_low`, `hits_mid` + slow tails | take 2: which slit planes flare; take 10: the floor tube and the light it throws strike together |
| `section` | which phrase, which grid boxes are filled, wheel spoke count, which tube is dead |
| `energy` | tube brightness |
| `vocals` | tungsten lamp slot brightness (take 5) |
| `evolve` | fog advection and swirl, camera drift, model spin |
| `shot.age` | first third of a second: projector and tubes stutter like a lamp catching, then hold |

## Assets (2026-11-11)

Nothing in this folder names a folder on a machine: every file parameter is an expression on the scaffold's `mod.paths`, and build.py finds the repository from `td.project.folder`. The scene reads only these from `<assets>/`, and each has a fallback:

| Uses | From | With no assets |
|---|---|---|
| Phrase and Describe atlases (`t0..7`, `d0_*`, `d4_*`, `d8_*`) | `<assets>/fonts/ArchivoBlack-Regular.ttf` via `mod.paths.font('archivo')` | the Text TOP's default face (Verdana here), with `bold` switched on by an expression |
| Describe caption (`caption`) | `<assets>/fonts/BarlowCondensed-Bold.ttf` via `mod.paths.font('barlow')` | the default face; the two lines shrink to fit the strip |
| Fifteen models (the names in `DEFAULTS['MODELS']`): amphora, gramophone, broken_column, lander, skeleton_key, traffic_cone, astrolabe, balanced_solids, pierced_stone, rubber_duck, hourglass, crystal_cluster, marble_bust, wire_cage, ribbon_loop | `<assets>/models/<slug>/model.obj` via `mod.paths.model_file` (textures are not used: the G-buffer material ignores them) | TouchDesigner's bundled teapot, stretched by the `fit` Transform POP in each Geometry COMP to the box the real model fills, standing on that box's floor |

- Committed data: none as files. The models' bounding boxes (`DEFAULTS['SIZES']` in build.py, copied from the library's `info.json`) replace the read of `info.json` at build time, and the teapot's bounds are measured at build time from the bundled sample (with the measured values recorded in build.py as a fallback).
- `fit` is driven by `mod.paths.have('models/<slug>/model.obj')`: scale 1 and no offset with the library, the stretch with the teapot. So the saved .tox works in either state without a rebuild.
- The shaders, the fog, the tubes, the gobo patterns, the Input picture and the feed need no assets at all, so takes 6 (leaning tubes) and 9 (corridor) and the fog in every take are the same picture either way.
- Trap: do not name a system face as the font fallback. A face the machine lacks puts two warnings on every Text TOP ("Failed to load font file ... Substituted with Verdana"), and "Arial Black" is not in this build's Font menu even on Windows.
- Trap: `pop.computeBounds()` on a File In POP created and cooked in the same script returned zeros for the teapot; `pop.bounds()` in a later call returned the real box. build.py uses `bounds()` and falls back to the recorded numbers.

## Describe and Input (2026-11-11)

- **Describe** (`parent().par.Describe`). Two kinds of words, both in build.py (`DESCRIBE`, `CAPTIONS`, `CAPTIONS_IN`) and mirrored in preset.json (`words`, `words_with_input`):
  - The three takes whose gobo is text (0, 4, 8) each have their own atlas of eight two-line phrases (`atlas_d0`, `atlas_d4`, `atlas_d8`, built once beside the phrase `atlas`). The Switch TOP `slide` in front of `beam` input 2 picks the phrase atlas or a Describe atlas, so the toggle recompiles and rebuilds nothing. The tiled takes (4, 8) use 432 px cells centred in the 512 px tile so neighbouring phrases do not run together.
  - Every take gets a two-line caption along the bottom (`caption`, Barlow Condensed Bold 27 px, 1216x96, drawn by `grade.frag` on a darkened band only while `uDesc.x` is 1; solid black band and white text on the 1-bit take). The eight takes with no readable text carry only this caption.
- **Input** (`parent().par.Input`). The picture enters as the **projector's slide**: `slide`'s last input is `in_pic` (Select TOP), and `uIn.x` tells `beam.frag` that input 2 is a picture, not the atlas. `goboIn()` fits the whole 16:9 frame inside the cone and passes its colour out through `PC`, which multiplies the lamp colour wherever the projector lights fog, smoke layers or surfaces; the lamp moves 70% toward white (`inw`) so the picture keeps its colours. The shadow map, fog, sheets and sweep all still apply. `inp` (Constant CHOP) holds `valid` (Input names a TOP that is not our own `out1`) and `on` (valid and the take uses it); a bad path, a CHOP or our own output falls back to the scene's own source with no error.
  - Uses it: 0 (picture repeated on the smoke layers), 4 (thrown across the carpet from above), 5 (replaces the ruled grid, thrown across the big floor), 8 (its negative on the paper room), 10 (up the wall behind the shadow caster), 1 (behind the blinds: colour in the shafts only), 3 (the lamp cone).
  - Ignores it (`inp=0`, no projector image to replace): 2 RED PLANES, 6 LEANING TUBES, 7 ONE BIT, 9 CORRIDOR.
  - While an Input is on, the text takes show no words of their own (the picture replaced them), so their caption switches to `CAPTIONS_IN`.

## Content (2026-11-11)

Everything a pack may replace sits in one dict, `DEFAULTS` in build.py, read once at build time through `LIB['scene_words'](scene, DEFAULTS)`. A pack replaces any of the five names with its `scenes/sc_light_gobo/words.json`:

- `PHRASES`: the eight two-line phrases of the text atlas (the count is fixed; a line of about 9 characters or more fills its cell's width).
- `CELL`: how many of a cell's 512 pixels the widest line may fill. The default 432 leaves a gap between neighbouring phrases in the tiled takes (4, 8), as the Describe atlases already did; 512 fills the cell.
- `MODELS`: rows `[take, model, x, z, yaw, scale, spin, y of base]`. The cameras and lights are the scene's and stay put; a pack fits its models to them.
- `SIZES`: the bounding box of each model named in `MODELS`.
- `NOUNS`: what the Describe captions call the things in the takes (`{name}` in `CAPTIONS`, `CAPTIONS_IN`, `DESCRIBE`), so a caption never names a model the pack did not put there.

preset.json's `words` are the defaults run through `NOUNS`; `python sync_preset.py` rewrites them and `python sync_preset.py --check` fails when they differ.

## Log (newest first)

- **Generic defaults (2026-11-11).** The defaults in build.py are now generic: phrases about real-time picture-making and a catalogue of objects, and fifteen models of the shipped pack by their own names. The originals (phrases, model rows, sizes, caption nouns) live in a private pack's `scenes/sc_light_gobo/words.json`. Three takes were renamed for what they show: 2 RED PLANES, 3 LAMP CONE, 5 GRID WINDOW.
  - Private pack, before and after the restructure: `tdh.snapshot` of the rebuilt scene is byte-identical to the one taken before any change (`captures/ref_network.json`, `priv1_network.json`), so every expression, text and placement is the same.
  - Generic pack: first build `g1_sheet.png`. Changed after looking: the gramophone turned to profile in BLINDS (horn-on it was a blob); ONE BIT got the bust at 1.35 (a duck at 1.8 was an unreadable mass); LAMP CONE took three tries, since nothing in the pack is a table: floor-standing things about 1.25 high under the cone, an astrolabe and the sphere on top of the stack of solids (an hourglass showed only its lit top cap, like a saucer); the crystal cluster moved into frame in LEANING TUBES. Final: `g5a_*.png`, `g5b_*.png` (seeds 0.3, 0.7), Describe `g5d_*.png`.
  - Review the same day: in the tiled takes two long lines met with no gap ("NOT MADE.PICTURE OUT.", `rvg_t4_s30.png`), so the cell width became a pack value, `CELL` (432 by default: `rvh_t4_s30.png`, `rvh_t8_s30.png`). A marble bust was tried three ways in place of the stack of solids in LAMP CONE (`rvh_t3`, `rvi_t3`, `rvj_t3`, `rvk_t3`): only its crown catches the cone or it blocks the cone, so the stack of solids stayed. LAMP CONE is still the weakest generic take. Two caption nouns changed: "printed grid", "looped ribbon".

- **Portability pass (2026-11-11).** build.py, run.py and sheet.py converted: no literal folders, file parameters are `mod.paths` expressions, model sizes come from `SIZES` in build.py. Reference before any change: `p0_0..10.png`, `p0_sheet.png` (seed 0.3).
  - With assets after the conversion: `p1_sheet.png`, then after the final rebuild `take_0..10.png`, `takes_sheet.png`, `hero.png` (take 1); Describe and Input on takes 0, 5 and 0, 4: `p2_modes_sheet.png`. Same eleven pictures as `p0_sheet.png` and the earlier take captures; the differences are the phrase (section) and model spin (evolve).
  - With no assets (`Assets` pointed at the empty `captures/_noassets`, rebuilt): first try named "Arial Black" as the fallback face and got 48 warnings (`n0_sheet.png`, thin Verdana); now the default face in bold, zero errors: `n1_0..10.png`, `n1_sheet.png`, Describe and Input `n1_modes_sheet.png`. Every model is a teapot stretched to the model's box: tall models become tall coffee pots, a wide low one a wide low teapot, a thin one a thin teapot. Light, fog, shadows, tubes and words all work.
  - Then `Assets` blanked, rebuilt, tox and snapshot saved (96 ops), `python -m pytest -q tests/test_portable.py -k sc_light_gobo`: 1 passed.
  - `tdh.check`: pending, then cook_budget fail at 59.8 ms (model loads), then fail at 18.8 and 19.1 ms with every other check passing. `beam.gpuCookTime` read 17.7 ms and, seconds later, 6.2 ms on the same take (take 5) with seventeen other agents building; CPU for the whole scene was under 1 ms and the `fit` POPs do not cook per frame. The shaders were not touched in this pass. A fifth run a minute later: PASS, cook_budget 7.0 ms on take 5.

- **Describe and Input pass (2026-11-11).** The earlier agent on this task left nothing: `git diff 08710bf` for this folder was empty and the live COMP was the old one, so this started clean. Rebuilt on the new scaffold unchanged first (`d0_0..10.png`, `d0_sheet.png` against the old `take_*.png`: same eleven pictures).
  - Describe: first try had the caption flush to the left edge and dithered into noise on the 1-bit take (first `desc_7.png`); now a 32 px margin and a solid band. Tiled phrases ran together ("PROJECTEDSEEN FROM"), fixed with the narrower cells. Final: `desc_0..10.png`, `describe_sheet.png`.
  - Input with `/project1/sw_testcard/out1`: worked on the first build (`in_0..10.png`, `input_sheet.png`, seed 0.62). The ruled grid in front of the picture made take 5 unreadable, so the grid now gives way to the picture; the wheel take saw nothing recognisable and now ignores the input. With Describe as well: `ind_*.png`, `input_describe_sheet.png`.
  - Blank Input, Describe off, after the final rebuild: `take_0..10.png`, `takes_sheet.png`, `hero.png` recaptured; they match the old sheet. With `uIn.x` 0, `PC` is exactly 1 and `slide` passes `atlas` through, so the shader does the same arithmetic as before.
  - Cost unchanged: `beam` 4.4 to 4.6 ms on takes 0 and 4 and 6.2 to 6.7 ms on take 5, with or without Input and Describe (single readings of 15 to 17 ms and one of 43 ms appear while other agents cook). `tdh.check`: pending, then cook_budget 86 ms fail, then PASS at 7.8 ms on take 5.

- Second pass closed with a clean rebuild from build.py: all eleven takes recaptured at seed 0.3 (`take_0..10.png`, `takes_sheet.png`), `hero.png` = take 1 again, tox and snapshot (53 ops) saved with Preview off.
- **Second pass (art direction, 2026-11-10 evening).** Judged first from `r1a_sheet.png` / `r1b_sheet.png` (all nine takes at two seeds with the feed stored): nine takes did differ at a glance; weakest were CORRIDOR (murky grey-green, nothing happening), LEANING TUBES (milky), and ONE BIT lost its figure at some seeds.
- New take 2 RED PLANES (then called COPIER) (`r2a_2.png` first try: one blown-out pink plane filling the frame, "lava"; `r3a_2.png` after lowering gain 6 -> 2.2, tilting the comb 0.35 rad and dropping the camera: red smoke sky over a black skyline). Kick flares seen in `r7_c_sheet.png` (the frames at hit_low 0.53 and at a new hits_low count are the bright ones).
- New take 10 FLOOR TUBE (`r2a_10.png` milky; fog 0.1 -> 0.05 and tube fog light halved: `r3a_sheet.png`). Tube and its light now strike together, with a floor of 0.2 so it never reads as a black frame (`r8_f_sheet.png`; before the floor three of six captures were black).
- CORRIDOR moved to take 9, gets a beat chase and a second object far down; idle level 0.12 -> 0.03, fog 0.07 -> 0.04 (`r4_k_sheet.png`, `take_9.png`). Still the plainest picture.
- LEANING TUBES: fog 0.12 -> 0.03, tube fog light x0.6, floor reflections (`take_6.png`). The glass of a tube is now as bright as the tube whatever `tint` gives the fog.
- ONE BIT: at seed 0.4 the camera drifted off the line from the lamp through the figure and the frame was white glare with no figure (`r2a_7.png`); camera moved onto the lamp-figure line (x 0.1 -> -0.25) and drift cut to 0.05 (`r3a_sheet.png`).
- WORDS IN AIR: camera target raised so the beam sits lower in the frame.
- **Cost.** Measured with 40 frames of dwell per take and three samples (`run.py` `cost()`): with all tubes struck, take 5 was 21 ms and the corridor 10 to 17 ms in `beam` (the first builder's 4.8 ms was a moment with the tubes idle, because the old loop skipped unlit tubes). Sampling the tubes on every 4th step inside the main loop saved nothing. Moving them to their own 12-sample loop with no branches and a constant count did: see "Cost" below.

- (First builder) Final clean rebuild from build.py, all nine takes recaptured (`take_0..8.png`, `takes_sheet.png`, `hero.png`), tox and snapshot saved, Preview off.
- Cost: take 0 measured 6 ms GPU in `beam` (64 steps + 12 layers + 4 tubes), takes 2 and 6 about 7 ms (the per-step tube loop is the expensive part). Sheet takes now march 36 fog steps, tube-only takes 40 and skip the projector test, and a tube only lights fog within about 6 units. No visible change in `takes_sheet.png`. See "Weak" for the measurements.
- The model's own texture and PBR MAT are deleted at build (the override material makes them dead weight: 9 to 15 ms of load each).
- Fog puff moved from `bass` alone to `bass` + kick tail: `bass` read about 0.01 in every sample I took between t=110 and t=241, so the breath was invisible.
- Final takes: `captures/take_0..8.png`, `takes_sheet.png`; hero = take 1 (`hero.png`).
- Take 8 first tried as "CARVED" (staring into a red lamp with the phrase inverted): pink soup, no blacks, unreadable (`w11_take8.png`). Replaced by SHADOW PLAY: camera beside the projector looking at the lit wall, inverted tiled text (`w12_take8.png`). Much stronger and the only bright take.
- Moments: `m1/m2/m3_take0.png`, `m*_take5.png` (`moments_sheet.png`): phrase changes with section, layers move with the beat, tubes differ, grid boxes change.
- Arrival: `w10_arr_sheet.png`: six captures in the first 0.3 s; projector drops out on two of them, leaving the tube-lit figure.
- Dither: interleaved gradient noise gave a visible cross-hatch moire near the beam apex (`w09_take5.png`); white noise per pixel per frame reads as grain (`w10_take5.png`). Steps 56 -> 64.
- Tube strikes: `w08_sheet.png`, eight captures 7 frames apart in take 2 with the feed stored: at hit_mid 0.57 tubes drop and the nearest goes grey, next capture all bright.
- Take 3: light as a wide cone filled the frame with flat orange (`w05_take3.png`); a narrow cone from above with inverse-square falloff and fog noise at 5x frequency gives a cone with curling smoke and black around it (`w07_take3.png`).
- Take 7: the figure was invisible at first (`w04_take7.png`): camera rays missed its shadow volume and lit fog veiled it. Putting light, figure and camera nearly in line makes the shadow volume come at the lens (`w05_sheet.png`).
- Take 1: looking into the light washed out to a green burst (`w01_take1.png`, `w04_sheet.png`). Moving the camera to look along the slat planes makes each shaft a hard blade (`w05_take1.png`).
- Tone map: per-channel curve bleached the blue to white (`w01`); curve on the peak channel keeps colour.
- First build (`w01_take0.png`): G-buffer with custom projection lined up first time; text reads the right way round.

## Cost (steady, per take, 2026-11-10 after the second pass)

`beam.gpuCookTime` after 40 frames on each take, three samples each, two sweeps, other agents building at the time: take 0 4.4 to 4.8, 1 4.0, 2 2.5 to 2.9, 3 4.0, 4 4.5 to 5.2, 5 6.0, 6 3.8 to 4.2, 7 4.3 to 4.8, 8 4.4, 9 3.9, 10 5.2 to 5.5 ms. `grade` + `glow` + both G-buffers add about 0.2 ms GPU. CPU for everything that cooks each frame: 0.7 to 1.3 ms. Worst case about 7.3 ms (take 5). Takes without tubes read about 1 ms higher than at the start of the session (take 1: 3.0 then 4.0); I could not tell whether that is the larger shader or other agents' load.

## Weak / unverified

- No assets: the default face is light even in bold, so the words in takes 0, 4 and 8 are thinner and read less well as stencils than Archivo Black; the caption in the default face is wider and shrinks. The stretched teapots are plainly teapots (every shadow becomes a coffee-pot shadow), in RED PLANES they are only bumps on the skyline, and in LEANING TUBES the silhouette is a dim teapot at the frame edge. The captions and descriptions still name the models (`NOUNS`), which is untrue of the stand-ins. Judged from stills only.
- Describe: the caption is an ordinary subtitle, not light in fog; on eight of eleven takes it is the only text. In take 0 the long phrases ("36 FOG STEPS PER PIXEL") shrink to fit the cell and the overlapping smoke layers garble all but the nearest copy. In take 4 the words lie at steep angles and are cropped by the frame; you read fragments. No live feed numbers are shown anywhere. Describe was judged from stills only.
- Input: takes 1 (blinds) and 3 (lamp cone) only take the picture's colours, you cannot recognise it there; four takes ignore it. Tested with the test card only, never with another scene's output: a dark picture will give a dark room (`ing` is the per-take gain, 1.25 on take 0, 1 elsewhere). Take 8 shows the negative, which may surprise. With Input on, takes 0, 4 and 8 lose their words even in Describe mode (caption only).
- "Exactly as before" with Input blank was checked by eye against the old captures and by reading the shader; the picture is noisy and feed-driven, so no pixel comparison was possible.
- Everything was judged from stills and 6 to 8 frame capture sequences. Nobody has watched it play. Sweep speeds, the corridor chase and the red planes' travel are unseen as motion.
- The shared instance was dropping frames while I captured (the feed's `t` repeated between captures 7 frames apart), so strike and stutter rhythms may look different at a clean 60 fps.
- `tdh.check` passes on the third and fourth run after a rebuild (cook_budget 6.9 and 7.4 ms on take 5, the dearest take) with `cook_budget` listed first. The first run fails (stale `moving` sample) and the second failed cook_budget at 37 ms (model loads counted).
- Fog is grainy by design (white-noise offset, no temporal filter). The corridor is the grainiest since its tube glow has only 12 samples a pixel.
- CORRIDOR (9) is still the plainest take; GRID WINDOW (5) has a flat blue haze over its upper half; WORDS IN AIR (0) still overlaps its layers into mush at the right edge at some seeds.
- In RED PLANES the objects read as a skyline of silhouettes, not as recognisable models; the contour lines the planes draw on them are thin and mostly lost. The snare flare (`hits_mid`) was added after the capture sequence and is not separately seen.
- Models are shaded with one putty albedo; mesh edges in the G-buffer are not anti-aliased. Only the projector casts model shadows.
- `bass` read near zero in most samples but 1.2 to 2.5 in a few (t = 177 to 181); its part of the fog breath is still not something I saw.
- Takes 1, 4, 9 and 10 are all fluorescent green. They differ in composition, not in colour.

## Next

- Temporal accumulation of the fog (one feedback pass) to trade grain for smoothness.
- A second shadow-mapped light so the tubes cast model shadows.
- Model albedo in a second colour buffer.
