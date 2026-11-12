# sc_spectral_terrain: Spectrogram terrain

Built 2026-11-10 against TouchDesigner 2025.33230. Rebuild with `build.py` (idempotent).

## Words (generic pass, 2026-11-11)

Everything the scene says that is content, not technique, sits in one dict at the top of build.py:
`CONTENT = {'WORDS': [[operator name, text, width], ...8 rows], 'LABELS': {take name: [captions]}}`.
build() reads it once through `LIB['scene_words'](scene, CONTENT)`, so a pack that holds
`scenes/sc_spectral_terrain/words.json` replaces either name (same shape: eight WORDS rows, operator
names starting `w_`; build() asserts both). The Describe words (`DWORDS`, `dlabels`) are not in the dict:
they describe the technique and are the same on every pack. The scene loads no model, picture or baked
data, so words are all a pack can change here.

**Log, generic pass**
- 2026-11-11: the defaults in build.py are generic (real-time picture-making and catalogue-of-objects
  phrases, same line counts and close to the same line lengths as before so the monoliths keep their
  size). The originals live in a private pack's `scenes/sc_spectral_terrain/words.json`. Checked both
  ways: `gen_t<take>_s<seed>.png` and `gen_desc_t<take>.png` on the shipped pack (every take, every
  phrase and caption), `ref_t<take>_s<seed>.png` before and `priv_t<take>_s<seed>.png` after on the
  private pack. Weak on the shipped pack: the four-line valley phrase still loses part of its last
  line behind the ridges when the bass is loud, as the four-line phrase before it did.
- 2026-11-11, review: the pond take's second phrase had a ten-letter first line, which at 8 units
  wide stood too low and lost its top half behind the far ripples. The default is now a seven-letter
  line (`w_loud`), which stands clear of them. Tox and snapshot re-saved from the shipped pack.

## Assets (portability pass, 2026-11-11)

No file in this folder names a machine folder any more: `python -m pytest -q tests/test_portable.py
-k sc_spectral_terrain` checks it, including the saved .tox and the snapshot. build.py finds the
repository from `td.project.folder`; every file parameter is an expression on the scaffold's
`local/modules/paths` module; `sync_preset.py` finds its folder from its own location.

| The scene uses | Parameter (expression) | With no assets folder |
|---|---|---|
| `<assets>/fonts/ArchivoBlack-Regular.ttf` | `w_*/text` Text POP `fontfile` = `mod.paths.font('archivo')` | TouchDesigner's default face. The monoliths are sized from their measured bounds at build time, so they keep their width and place; the letters are thinner. |
| `<assets>/fonts/ChicagoFLF.ttf` | `label` Text TOP `fontfile` = `mod.paths.font('chicago')` | TouchDesigner's default face at the same pixel size. The longest two-line Describe caption still fits the frame. |
| `experiments/sc_spectral_terrain/shaders/*` (committed) | shader Text DATs `file` = `mod.paths.here('shaders/<name>')` | unchanged |

Nothing else is loaded: no model, no picture, no precomputed data. The terrain, sky, ribbon and
finishes are all generated from the hub's spectrum and feed, so no data file was added.

**Log, portability pass (newest first)**
- `p3_final_take_<n>.png`, `p3_final_sheet.png`: Assets blank again, after the last rebuild: the
  real fonts, same pictures as `p0_ref_sheet.png`. tdh.check: pending, fail (cook_budget alone,
  the known flap after a tox save), pass (3.19 ms, 24 active operators). Tox and snapshot saved
  with Preview off.
- `p2_noassets_take_<n>.png`, `p2_noassets_sheet.png`, `p2_noassets_modes_sheet.png`: the COMP's
  `Assets` parameter pointed at an empty folder, rebuilt. No errors. All eight takes draw and
  follow the music as before; the only difference is the typeface. Describe (takes 0, 2, 3, 4) and
  Input (takes 3, 7 with the test picture) work in this state.
- `p1_assets_take_<n>.png`, `p1_assets_sheet.png`, `p1_assets_modes_sheet.png`: after converting,
  with the real assets: every take, Describe on takes 0 and 5, Input on takes 3 and 5.
- `p0_ref_take_<n>.png`, `p0_ref_sheet.png`: every take before anything was changed.

**Weak with no assets, honestly**
- The default face is a light sans. The extruded monoliths lose their weight: the dark scan gaps
  of `word.frag` cut thin strokes into dashes, so the valley phrases and the small far-off dusk phrase
  are harder to read than in Archivo Black (`p2_noassets_take_0.png`, `p2_noassets_take_4.png`).
- The captions lose the 1-bit Chicago character; the one-bit chart take's caption is the most
  out of keeping.
- Judged from stills, not watched in motion.

## Fourth pass (Describe and Input, 2026-11-11): read this first

Two agents did this pass; the first was cut off, the second checked each step again from a rebuild
and finished it. With `Describe` off and `Input` blank every take is as in the third pass
(`final_sheet.png`, taken in the same call as row one of `describe_sheet.png`).

**Describe (`parent().par.Describe`)**: toggling it changes uniforms, the caption string and
which monolith renders. Nothing is built at the toggle: the eight Describe monoliths (`DWORDS`,
`w_d_*`) are cooked at build time beside the content ones.
- Every take gets a two-line Chicago caption (24 px, typed on at 150 characters a second) saying
  what the take does to the height map. On the CRT finish it has a dark outline (`uDesc.y` in
  crt.frag); on paper and one-bit the title strip grows from 10% to 12.5% of the height, and the
  one-bit caption is drawn at full resolution, not at 640x360.
- Takes 0, 4 and 7 swap their content monolith for a two-word statement (`dhero`), and stand it
  higher (`dwlift`, `dwscale`) because the content words' lower line sinks behind ridges.
- The words are `dhero` and `dlabels` in each TAKES row; `sync_preset.py` mirrors them into
  preset.json (`python sync_preset.py`, or `python sync_preset.py check` to prove they agree).

| Take | Monolith (seed picks one) | Caption (seed picks one) |
|---|---|---|
| 0 valley | SPECTRUM TERRAIN / LOUDER IS HIGHER / BASS BUILDS WALLS | EVERY FRAME THE SOUND SPECTRUM BECOMES THE FRONT ROW OF A HEIGHT MAP. OLDER ROWS SLIDE AWAY. BASS BUILDS THE WALLS, A KICK IS A WHITE RIDGE. |
| 1 skim | none | 256 BY 192 HEIGHT MAP OF THE SPECTRUM, ONE NEW ROW EVERY FRAME. THE HORIZON IS NOW... / EACH LINE RUSHING AT THE LENS IS ONE FRAME OF SOUND... THE RIBBON OVERHEAD HANGS AT THE PITCH OF THE VOICE. |
| 2 tunnel | none | THE SAME HEIGHT MAP ROLLED INTO A TUBE: FREQUENCY RUNS ROUND THE WALL, TIME RUNS DOWN THE BORE. KICKS ARE WHITE RINGS. THE BAR ROLLS THE CAMERA. |
| 3 map | none | CONTOUR MAP OF SOUND FROM STRAIGHT ABOVE: LINES JOIN EQUAL LOUDNESS, BLUER IS LOUDER... / THE SPECTRUM HISTORY PRINTED AS A SURVEY SHEET... A SNARE KNOCKS THE INK OUT OF REGISTER. |
| 4 dusk | HEIGHT IS LOUDNESS / ONE ROW PER FRAME / SHADED SOLID | THE SAME SPECTRUM HEIGHT MAP SHADED AS SOLID ROCK: ONE SUN, DISTANCE FOG. THE THIN STRATA ARE ITS ROWS. A KICK DRUM IS A GLOWING BAND ROLLING AWAY. |
| 5 chart | none | ONE TRACE PER FRAME OF SOUND, STACKED FLAT WITH NO PERSPECTIVE. BASS IS IN THE MIDDLE... / THE SPECTRUM HISTORY AS A SEISMOGRAPH IN PURE BLACK AND WHITE: ORDERED DITHER AT 640 BY 360. THE BEAT THICKENS THE DOTS. |
| 6 planet | none | THE HEIGHT MAP WRAPPED ON A SPHERE: FREQUENCY IS LONGITUDE, NEW SOUND ENTERS AT THE NORTH POLE AND TRAVELS SOUTH. A KICK SWELLS ONE LATITUDE. / SPECTRUM PLANET: A 256 BY 192 GRID... IT TURNS FASTER WHEN THE MUSIC IS LOUD. |
| 7 pond | NOW IS THE CENTRE / KICKS MAKE RINGS | THE HEIGHT MAP AS A SPIRAL DISC: FREQUENCY IS THE ANGLE, NEW SOUND STARTS AT THE CENTRE AND SPREADS OUT. EACH KICK DRUM LEAVES THE MIDDLE AS A RING. |

**Input (`parent().par.Input`)**: the picture is laid on the body and becomes part of the height
map. `in_pic` (Select TOP, 640x360) reads the named TOP, or the black `in_none` when the path is
blank, missing, not a TOP or this scene's own out1 (`tk/inon`); `in_soft` is a blurred 320x180
copy. terrain.vert reads `in_soft`: brightness adds relief (`inamp`) and gates how much of the
spectrum's relief survives (`inmix` in dark parts, `inpk` in bright). terrain.frag reads `in_pic`:
it colours the ridge lines, the rock, or washes the paper under the ink. Each take says where the
picture sits on its grid (`inua` .. `invo`); the pond lays it flat in world x,z (`inplanar`), and
the chart's turned-on-its-side variant turns the picture with it (`ingate`, `gub`, `gva`, `gvo`).
With `inon` 0 the shaders take their old branch, so blank restores the scene.

Seen with /project1/sw_testcard/out1 (`input_sheet.png`, `in_take_<n>_s30.png`, `_s70.png`):
- **Strong**: 3 map (TEST INPUT embossed in contour ink with the card's colours as a wash),
  5 chart (the words drawn in one-bit traces, both upright and turned), 7 pond (the words lie on
  the disc as raised ring lines, the content word stands in the hole), 6 planet whole-globe variant
  (letters wrapped round it, only part readable).
- **Usable**: 1 skim (letters stand up as stepped rows that rush at the lens; the valley variant
  shows less), 6 planet close-limb variant (one huge letter).
- **Weak**: 0 valley (colour and a raised plateau at a grazing angle, no shape you could name),
  2 tunnel (colour bands and broken relief, tiled 2 x 3 on the wall, unreadable), 4 dusk (a mesa
  and a faint tint; the pink fog eats the colour).
- Cost with a picture given: one tdh.check reading of 7.7 ms (2.8 ms without), while seventeen
  other scenes were cooking.

**Traps found this pass**
- Swapping u and v to turn a picture 90 degrees is a mirror, not a turn: one of the two needs its
  sign flipped (the chart's turned variant read backwards twice before it read right).
- A capture taken in the same call as a rebuild shows a flat plain: the history is empty. Capture
  in a later call.
- The scratchpad folder is shared by every agent in the run: a helper called `cap.py` or
  `sheet.py` gets overwritten by another agent within a minute. Use a folder of your own.

**Weak, honestly**
- In Describe mode the vocal ribbon still crosses the take 0 monolith and can hide its second line
  (`describe_take_0_s90.png`: BASS BUILDS is clear, WALLS is half covered). NOW IS THE CENTRE
  keeps its lower line partly behind the inner ridges when they are tall.
- The captions are small (24 px Chicago capitals, two lines of about 70 characters). They read at
  1280x720 but not in a thumbnail.
- Take 6's caption sits on bright lines; the outline keeps it readable but it is the busiest.
- Describe and Input were judged from stills, not watched in motion; the caption typing on was
  not seen.

**Log, fourth pass (newest first)**
- `final_take_0.png` .. `final_take_7.png`, `final_sheet.png`: Describe off, Input blank, after the
  last rebuild. Same pictures as the third pass. tdh.check: pending, fail (cook_budget 54.7 ms,
  24 active operators, the known flap), pass (2.85 ms).
- `describe_take_<n>_s30.png`, `_s90.png`, `describe_sheet.png`: every take in Describe mode, two
  seeds each.
- `in_take_<n>_s30.png`, `_s70.png`, `input_sheet.png`: every take with the test picture.
- `f6_sheet.png`, `f5_sheet.png`: pond changed from a polar wrap (letters upside down on the far
  side, `f4_sheet_a.png`) to a flat projection; chart's turned variant turned to match.
- `f3_sheet.png`: monoliths lifted in Describe mode. `f2_sheet_0.png`: before, TERRAIN, HIGHER and
  WALLS were half sunk.
- `f1_sheet.png` against `f1_old.png`: rebuild on the new scaffold, unchanged.
- First agent (cut off): `e2_*` Describe trials, `e3_*` .. `e8_*` Input trials.

## Third pass (takes, 2026-11-10 evening)

The first cut was too repetitive. This scene was always a word in a valley from the
same height. It now has **eight takes**, chosen by `op('shot')['take'] % 8` from the `TAKES` table
in build.py. One waterfall history feeds all of them; a take is a row of numbers (body, look, sky,
finish, camera, palette, word), so a cut changes uniforms and render flags only. Nothing loads at
a cut: all eight phrase meshes and their materials are cooked at build time.

| Take | Name | What you see | Seed varies |
|---|---|---|---|
| 0 | valley | The original: phrase monolith in a line-drawn valley, spectrogram sun, CRT | which of 3 phrases, green/amber swap, camera side and height |
| 1 | skim | No word. Head-height forward flight in ice blue, live edge at the horizon, rows rush at the lens. Small Chicago readout top left | valley or central ridge, side, height, readout phrase |
| 2 | tunnel | Terrain rolled into a bore, red phosphor, camera inside rolling with the bar, spectrogram sun at the far end. No text | twist direction and amount, camera offset |
| 3 | map | Daylight: straight down on cream paper, ink contours, blue height tint, survey grid, kick rows stamped in red hatch, Chicago title block | wide sheet or close crop, title phrase |
| 4 | dusk | Solid lit mountains in pink fog under a small sun, gold strata lines; a phrase stands small and far off | which of 3 phrases and where, sun azimuth, camera height |
| 5 | chart | No perspective: rows stacked flat like a seismograph, one-bit black and white dither, Chicago caption | white-on-black or black-on-white, upright or turned 90 degrees and cropped, caption |
| 6 | planet | Terrain wrapped on a globe turning in a star field, amber | whole globe or close limb, side, caption |
| 7 | pond | Spiral disc of ripples spreading from a red phrase at its centre, cream lines | which of 2 phrases, camera elevation and side |

Takes 1, 2, 3, 5 and 6 have no wordmark in the picture (1, 3, 5, 6 carry a small Chicago caption
from `CONTENT['LABELS']`; 2 has no text). The first phrase of `CONTENT['WORDS']` appears only in
take 0, one seed in three.

**How it is built**
- `tk` (Constant CHOP): one channel per key of `DEFAULTS`, each a tuple indexed by the take, plus
  the seed split into `s1`, `s2`, `s3` and a gate `g` (1 when s3 > 0.6) for either/or variations.
- `terrain.vert` `uShape.x`: 0 plane, 1 tunnel, 2 planet, 3 disc, 4 flat stack. `uMap.x` folds the
  history so the bass is in the middle (ridge) instead of at the edges (valley).
- `terrain.frag` `uLook.x`: 0 ridge lines, 1 solid lit rock with distance fog, 2 contour map.
- `sky.frag` `uSkyM.x`: 0 horizon spectrogram sun, 1 flat colour, 2 dusk gradient and small sun,
  3 stars, 4 full-circle sun (tunnel end).
- `crt.frag` `uPost.x`: 0 CRT tube, 1 paper (no glow, fibre, snare knocks the plates out of
  register), 2 one-bit ordered dither at 640x360.
- `label` (Text TOP, Chicago): caption typed on at 50 characters a second from the shot's age.

**Arrival (first half second, from `op('shot')['age']`)**: the terrain springs up from 35% height
with an overshoot; one white row sweeps from the live edge to the far end; the camera dollies in;
the word rises out of the ground in 0.4 s; the tunnel irises down from 2.6x radius; the planet
pops from nothing; the disc's rings shoot outward; the chart fans open from a single line; the
caption types on. Seen in stills at ages 0.05 to 0.4 s (`w_d1.png` .. `w_d7.png`), not in motion.

**What follows the music in the new takes** (all of them are the same history, so the spectrum is
the shape in every take): `hit_low` writes a kick row that is a white ring travelling down the
tunnel, a red hatch band crossing the map, a glowing stratum on the dusk mountains, a swollen
latitude on the planet and a ripple leaving the pond's centre; it also punches the camera and
flashes the word. `hit_mid` splits the CRT colours and knocks the paper plates out of register.
`bar_pos` rolls the tunnel camera 16 degrees. `evolve` spins the planet, pond and tunnel.
`pulse` lifts brightness (and the one-bit exposure, so the dither thickens on the beat).

**Cost** (sum of cpuCookTime + gpuCookTime of operators cooked in the last 2 frames, one reading
per take while other scenes were cooking): take 0 2.1 ms, 1 2.4, 2 2.4, 3 2.7, 4 2.1, 5 2.3,
6 2.1, 7 2.1. `tk` is 0.3 ms of that (about 80 Python expressions). One reading of 35 ms came
straight after a batch of forced cooks (every GLSL operator showed ~3 ms); the next read 2.4.

**Traps found this pass**
- Camera rotate order is xyz: with rx -90 (looking down), rz no longer spins the picture, it tips
  the view to the horizon and the render comes back empty (alpha mean 0). Spin with ry.
- A Constant CHOP channel that reads another channel of the same CHOP is a cook dependency loop
  (already in TRAPS.md; I hit it again with `cx` reading `xmap`). Repeat the expression.
- A bright full-frame picture (the pink dusk) makes the bloom-only pass lift every dark area:
  mountains meant to be dark came out pale until bloom gain went from 0.45 to 0.10.
- Several `out1.cook(force=True)` in one script, each after setting Take/Seed/Shotstart, do give
  different pictures (parameters changed), so one call can capture all takes at the same instant
  of the music. The history does not advance between them.
- The cutter writes this COMP's Take while you work (I read Take 64 once): set it in the same
  call as the capture.
- A word's GLSL MAT cost 4.3 ms of CPU the first time it rendered; build.py now force-cooks every
  word material once. I did not measure whether that removes the first-use cost.
- Bash heredocs holding Python with apostrophes inside triple quotes break in Git Bash; write the
  script with the Write tool.

**Weak, honestly**
- Take 4 (dusk) is the least sure: it is pink on pink, the phrase's bottom line sinks behind
  ridges when the floor swells, and it is the take furthest from "this technique".
- Take 1 valley variant has a dim flat band at the horizon where the treble floor is flattened;
  the ridge variant is the better half.
- Take 0 and take 1 are the closest pair (both line terrain in perspective); colour, word and
  direction of travel separate them.
- Take 3 gets busy in loud passages (contours of every row). The red hatch covers a lot when
  kicks come fast.
- The vocal ribbon is shown only in takes 0 and 1.
- Nothing here was watched in motion: arrivals, the tunnel's roll and the planet's spin were
  judged from stills.

**Log, third pass (newest first)**
- `take_0.png` .. `take_7.png` and `take_0_b.png` .. `take_7_b.png`: every take at two moments
  with different seeds; sheets `contact_sheet.png`, `contact_sheet_b.png`. `hero.png` = take 6.
- `w_e1.png`: skim valley variant had a black foreground hump: fog 0.75 -> 0.35, camera 1.25 -> 1.5.
- `w_d0.png` .. `w_d7.png`: arrival frames. d1-d3 valley at 0.05 / 0.2 / 0.4 s: white sweep row,
  the phrase rising, first line then second. d4 tunnel irising. d5 planet popping. d6 chart fanning, caption part typed.
- `w_c0.png`, `w_c1.png`: dusk pale and washed: bloom was lifting it (see traps).
- `w_b0.png` .. `w_b7.png` (bass 2.17, energy 0.73): map reads once contours went 2.4 -> 1.5 per
  unit and hillshade was halved; red hatch bands are the kick rows. Dusk ridge variant put the
  camera inside the ridge: dusk no longer takes the ridge fold. Pond word lifted out of the hole.
- `w_a0.png` .. `w_a7.png`: map camera fixed. Map too noisy, caption unreadable under ink (title
  block added), dusk a pink mush, pond word hidden behind the near rim.
- `w_t0.png` .. `w_t7.png`, `w_sheet1.png`: first look at all eight. Map blank (camera, see traps).
- `v0_a.png`, `v0_b.png`, `v0_c.png`: the scene as found, three moments: word in valley each time.
  `v0_rebuild.png`: clean rebuild on the new scaffold (Take, Seed, Shotstart, `shot`), unchanged.

**Next**
- Scroll the history by track time, not by cooked frame (the planet and pond slow with frame rate).
- Give the dusk take a second light and darker rock, or replace it with a point-sprite terrain.
- Let the chart take draw the vocal pitch as one heavy trace.

The sections below describe the first two passes; where they speak of `section` choosing the word,
palette or camera, the take and seed now do that.

## Intent

A landscape that is literally the last few seconds of the track. The hub's live spectrum is written
as the front row of a small history texture every frame and the older rows shift back one step, so
the texture is a waterfall spectrogram. That texture displaces a dense grid drawn as glowing ridge
lines with hidden-line removal (the "Unknown Pleasures" drawing, but live and in perspective).

What has to work for the picture to land:

- **A valley, not a wall.** The spectrum is mirrored with the bass at both outer edges and the highs
  in the middle, so the loud lows build two mountain ranges and the camera flies down the valley
  between them. The front edge of the terrain is the live spectrum, large in frame, so the music is
  seen the instant it happens and then recedes to the horizon.
- **Hits travel.** Each row stores how hard the kick was when it was written, so a kick is a white
  ridge line that rolls away from the viewer.
- **Words as monoliths.** Extruded phrases stand in the valley; the terrain is pressed
  flat around their footprints, and they flash on `hit_low`.
- **The voice is a curtain of light.** A ribbon hangs over the valley at the height of the sung note
  and recedes with the terrain.
- **CRT phosphor, real depth.** Green and amber on black, bloom, scanlines, slight barrel distortion;
  the horizon glow takes its hue from the bass note.

## Technique

- `wf` (GLSL TOP 256x192 rgba16float) + `wf_fb` (Feedback TOP): `shaders/waterfall.frag` writes the
  live spectrum into row 0 and copies every other row from the row before it in last frame's image.
  R = height, A = kick strength when the row was written. One row per cooked frame, so 192 rows is
  about 3.2 s at 60 fps (longer when the frame rate dips).
- `notes` + `notes_fb` (2x192): the same scroll for the voice (column 0: held pitch, spark, ribbon x,
  vocal loudness) and the bass (column 1: held hue, flare, loudness). See "Traps" for why it holds.
- `terrain`: a 256x192 Grid SOP with a GLSL MAT. `terrain.vert` lifts each vertex by the history
  texture, applies a valley profile (the middle is scaled to 18%) and flattens the ground around the
  three word footprints with a small berm. `terrain.frag` paints the surface black and draws the
  ridge lines from the depth coordinate with `fwidth` anti-aliasing; because the black surface writes
  depth, near ridges hide far ones. No lights.
- `w_*`: Text POPs (Archivo Black, extruded), sized from `computeBounds()`,
  with `word.frag`: scanned face, ribbed sides, flash uniform.
- `comet`: a 2x192 strip whose vertices are placed by the notes texture; additive, depth-tested, no
  depth write.
- `sky` (GLSL TOP): horizon glow, slatted sun and stars, placed from the camera's rotation so they
  stay on the horizon. `over` puts the render on it, `bloom` (Bloom TOP, bloom-only output) and
  `crt.frag` finish: barrel, chromatic split, scanlines, hum bar, vignette, soft shoulder.
- `ctl` (Constant CHOP) holds every expression that turns the feed into a control value.

Steady cost measured live: about 1.8 ms CPU+GPU for the 19 operators that cook each frame.

## Channel mapping

| Feed | What you see |
|---|---|
| hub spectrum (full log-frequency `specraw`) | the terrain itself: front row is now, it recedes at one row per frame |
| `bass` (through the spectrum) | height of the two outer mountain walls |
| `hit_low` | white-hot ridge line written at the front that travels away; one word flashes (which one cycles with `hits_low % 3`), the other two flash faintly |
| `pitch` / `pitch_conf` | height of the ribbon (held at the last sung note, glides to the next); a white spark on the ribbon where a note was detected |
| `vocals` | brightness and drop of the ribbon's curtain |
| `bass_pitch` | hue of the horizon glow and the lower half of the sun (pitch class round the colour wheel, held), with a flare on each detected note |
| `energy` | line brightness, sun brightness, sweep on the word faces |
| `section` | palette swap (green ground / amber words, or the reverse) and one of four camera positions |
| `evolve` | camera drift, ribbon weave, sun slats, star flicker |
| `beat_pos` | scanlines climbing the word faces, ribbon weave, curtain stripes |
| `bar_pos`, `bar_pulse` | camera roll, sun radius and brightness |
| `pulse` | camera bob, overall CRT brightness |
| `hit_mid` | chromatic split in the CRT pass |
| `hit_high` | star flare |

## Traps found (worth adding to the brief)

- **The scaffold's `spectrum` TOP is not a usable spectrum.** `/project1/sw_hub/spectex` is the first
  20% of a 24000-sample log-frequency spectrum (Audio Spectrum CHOP, `frequencylog` 1). That part is
  below the music: it reads as a smooth ramp with no peaks, and its level swings 100x between
  passages (0.0005 to 0.2 seen). The real content sits in roughly 14% to 95% of `sw_hub/specraw`,
  with peaks of 0.05 to 0.25. This scene points its own `spectrum` Select TOP at `specraw`.
- **`pitch` is on about 7% of the time and `bass_pitch` about 10%**, in bursts averaging 50 ms (read
  from `sw_hub/feedin`; vocal range MIDI 40 to 64). Anything drawn only "while pitch > 0" flickers
  for a frame or two. Hold the last note and decay a marker instead.
- `pow(x, 2.0)` with negative `x` is NaN in GLSL. Three shaders had it; one NaN pixel in the render
  makes the Bloom TOP output NaN everywhere and the final frame black.
- `normalize(cross(dFdx(p), dFdy(p)))` is NaN on degenerate triangles of an extruded Text POP.
- `smoothstep(a, b, x)` with `a > b` returned 0 here (it is undefined): write `1.0 - smoothstep(b, a, x)`.
- GLSL MAT works with both Grid SOP and Text POP geometry using `TDPos()`; POP bounds are
  `pop.computeBounds()` (`pop.bounds` is a method, not a value).
- `tdh.check` cook_budget read 53.9 ms on a run a few seconds after a rebuild and 1.76 ms on the
  next: sample it twice after the network has settled.

## Second pass (art direction, 2026-11-10): what changed

The sections above describe the first build. These three changes supersede them where they differ:

- **One hero monolith, not three.** `section % 3` picks one of the first three phrases of
  `CONTENT['WORDS']`; it stands alone in the middle of the valley (x 0, z -12.5, 9.2 / 7.0 / 6.0 units wide,
  extrusion 11% of its width) and rises out of the black ground over the first tenth of each section
  (`ctl/rise`). `word.frag` is now a solid lit face cut by dark scan gaps (hot top, dim foot, ribbed
  sides) instead of dim scanlines. On a kick the whole slab goes white and scales 5%.
  `hits_low % 3` no longer chooses anything.
- **The sun is the spectrogram.** `sky.frag` takes the waterfall as input 1 and draws it in polar
  form: angle = frequency (bass at the horizon both sides, treble at the top), radius = time (now at
  the centre). 22 displaced rings, tinted by the bass note inside, white on kick rows. It replaces
  the slatted synthwave disc, which was the most stock-looking thing in the frame, and it shows the
  treble that the valley profile flattens on the ground.
- **A kick is a swell, not just a colour.** `terrain.vert` raises rows by their stored kick value
  (walls 50% taller, valley floor +0.45 units), so each kick is a physical wave rolling to the
  horizon. `flash` gain is 1.9 x `hit_low`; the camera punches in 0.45 units on it.
- Smaller: the vocal strip is a 0.45-unit ribbon with a hot core (its curtain is cut to 30%), bloom
  gain 0.8 -> 0.6, side cameras re-aimed so the word is not cut by the top of frame.

`tdh.check` cook_budget flapping, cause found: after a rebuild the shader Text DATs (4 to 8 ms each,
`totalCooks` 1) and the Grid SOP / Text POPs (2 to 5 ms, cooked once) still count as active
operators. Read 43.9 ms twelve seconds after a rebuild, then 1.54 and 1.54 ms (PASS, PASS) once
they aged out. Steady per-frame cost is about 1.5 ms.

## Log (newest first)

- **Second pass, final** (`r5_a.png` = `hero.png`, `r5_b.png`, `r5_c.png`): after the last rebuild.
  r5_a low centre camera, the first phrase in amber in front of the polar sun, green valley. r5_b kick 0.33:
  the second phrase white, front ridges white. r5_c vocals 0.66: ribbon streaks across the word.
- `r4_a.png` .. `r4_f.png`: r4_a caught a section change on a kick (0.56): the phrase half risen out of
  the ground, white. r4_b snare 0.58: red/blue split over everything. r4_e kick 0.59 on the low
  right camera showed black below the terrain's front edge (camera jolt went backward): jolt now
  goes forward and that camera sits at z 3.5. r4_d: vocal curtain hung as a glass pane in front of
  the third phrase: curtain cut to 30%.
- `r3_c.png`: left camera looked down (pitch -11) and cut the word's top; kick rows washed the frame
  milky. Pitch -5.5, word lifted 0.7, white kick lines reduced.
- `r2_a.png` .. `r2_d.png`: first look at the hero word and polar sun. Words 9.4/8.0/6.6 wide were
  too big for the side cameras.
- `r1_a.png` .. `r1_g.png`: the first build as found, seven frames over 25 s. Terrain good; the three
  words were dim flat scan-lined stickers at mid-height that overlapped each other and the frame
  edge; no visible word flash in any of the seven; the slatted sun read as stock synthwave.

- **Final rebuild** (`19_final_t233.png`, copied to `hero.png`): low centre camera, green ground,
  amber words, full valley, ribbon crossing in front of the phrase's second line. Tox and snapshot saved from this
  build; Preview off.
- `18_final_t225.png`: right-hand low camera on a kick (0.33): front ridges white, the right word
  flashed white. Words re-spaced (the first narrower and further back) because `17_final_t208.png`
  had the second overlapping the first.
- `17_final_t208.png`: snare 0.94 and pulse 0.95: clear red/blue split on the lines.
- `16_final_t198.png`: the newest end of the curtain hung right in front of the low right camera as
  a sheet of amber glass over the words. The veil now fades in over the first 20% of the depth.
- `15_rebuild_t185.png`: clean rebuild reproduces the scene. High camera cut the phrase's first line off the top:
  pitch changed to -12.
- `14_t174.png`: vocals 1.3: bright green striped curtain across the valley, amber ground.
- `13_t162.png`: high camera after the fix, snare split visible.
- `12_t143.png`: sky glow washed the top of the frame yellow when the horizon sat high: glow halved.
- `tdh.check`: nine runs in all, two of them the "pending" first samples. Passed 3 times with
  cook_budget at 1.5, 1.8 and 4.9 ms (the last run was a pass).
  Failed 3 times on cook_budget alone, reading 54 to 67 ms, each within a few seconds of a
  rebuild or a tox save, and once on `moving` with a stale sample from before a rebuild (cooks -30).
  Per-operator readings taken in between sum to about 1.5 ms; I did not catch which operator
  reports the spike.
- `11_t069.png`: high camera (section % 4 = 3) showed the terrain as a floating slab with black
  round it. Lowered and moved that camera forward (y 4.2, pitch -15, z 6).
- `10_t048.png`: bass 1.34, tall walls; ribbon as a thin amber line with a striped curtain by the
  right word. Removed the curtain's idle glow: at `09_t031.png` it read as a big translucent sheet
  across the words when nobody was singing.
- `08_t023.png`: bass note held (hue 0.86): horizon and sun base turn violet against green ground.
  Words moved inward and lifted so the lower lines clear the ridges.
- `07_b.png`: bass note C, cyan sun; the ribbon passed over the camera and left the top of frame, so
  its height range was reduced (1.5 to 3.4 units) and the weave made faster (4-beat period).
- `06_a.png`: first look at the curtain with vocals 0.79; ribbon was nearly straight.
- `05_notes.png`: note history texture added. Kick at 0.58: front ridge lines white, right word
  flashed.
- `04_words.png`: amber section, bass 0.8. Found the pitch channel lights 2 rows in 192: the ribbon
  was a single shard. Read the analysis table to see how sparse it is, then switched to hold + spark.
- `03_lift.png`, `02_valley.png`: valley profile, smoothing across frequency, camera moved so the
  live edge is at the bottom of frame, bloom reduced (the first version was a green haze).
- `01_first.png`: black. Causes, in the order found: reversed `smoothstep`, NaN from `pow`, NaN from
  `normalize`, and a terrain saturated at full height because the scaffold spectrum is the wrong
  slice (see Traps).

## What is weak

- (Second pass) The hero word sits in front of the middle of the polar sun, so the sun's centre,
  where "now" is, is mostly hidden; you see its outer, older rings. The last line of each phrase is
  partly behind ridges when the valley floor swells. `hit_high` star flare still unconfirmed.
  The rise at a section change was caught in one still (`r4_a.png`), not watched.
- The ribbon is the weakest part. With a pitch channel this sparse it is mostly a held line whose
  brightness follows the vocal stem; it does not trace a melody the way the concept imagined.
- The word furthest back overlaps the left word from the two side cameras, and lower text lines are
  still partly behind ridges when the bass is loud.
- The scroll speed is one row per cooked frame, so it slows if the frame rate drops.
- The high camera is the least composed of the four.
- Words flash on the kick but do not otherwise move.
- Not seen in motion by a person: judged from stills taken seconds apart.

## Next

- Scroll by track time instead of by frame (write `t` per row, sample by time) so speed is tempo-true.
- Let `section` choose which phrases stand in the valley from a longer list.
- Give the words a wireframe edge pass so they belong to the line drawing.
- Replace the ribbon's source with a continuous pitch track if the hub ever publishes one.
