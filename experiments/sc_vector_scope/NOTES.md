# sc_vector_scope

## Intent
Everything on screen is drawn by one glowing beam, as on an XY oscilloscope or a vector arcade monitor: short phrases as outlines, the asset pack's models as wireframes, Lissajous figures. The beam is honest physics: it spends equal time per sample, so slow parts glow, corners where it dwells burn as dots, and fast jumps between strokes are faint. The music is in the beam itself: the real left and right audio samples are added to X and Y, so a word shivers and fattens with the waveform, becomes the raw stereo field on some takes, and snaps back clean. It works when a viewer believes there is a tube behind the glass and can see the track in the line.

## Technique
- `bake_paths.py` (plain python, outside TouchDesigner) turns 39 shapes into beam paths of 4096 samples each and writes `paths.npz` / `paths.json` (both committed; the baker reads `<assets>/fonts` and `<assets>/models`, the scene does not): 8 words and 8 two-line blocks (outlines of the pack's `chicago` face, which in the shipped pack is IBM Plex Mono, via matplotlib TextPath), 6 big glyphs (Barlow Condensed), one drawn catalogue card, and 16 models. What is baked is `DEFAULTS` in build.py. Samples are spaced in equal time: the beam dwells on corners and crosses gaps between strokes in two samples with the pen down-weighted. Each model row of `DEFAULTS['MODELS']` says how it is drawn: as contour slices (most of them: the generated meshes are lumpy, and their cross-sections are clean closed curves) or as feature edges of a vertex-clustered copy (the lander and the wire cage, whose legs and rods slice into confetti).
- `shapes` (Script TOP, callbacks in `load_paths.py`) loads the paths as a 1024 x 364 float texture (39 picture rows + 52 Describe rows). `audtex` is this frame's 800 stereo samples from a read-only Select of `/project1/sw_hub/audio`.
- `path` (GLSL TOP, 1024 x 36, `shaders/path.frag`) computes where the beam is: up to 8 "guns" of 4096 samples, plus a ninth for the Describe label. It blends two baked rows with a beat-locked damped-spring morph, rotates and projects them, lays the guns out per take, adds the audio samples to X and Y, and sets the pen (draw-on at the cut, travelling write head, depth cue).
- `beam` + `beam_mat` (GLSL MAT, additive): one instanced quad per segment. The pixel shader is the line integral of a Gaussian spot along the segment (after woscope), so joined segments add up seamlessly and brightness falls with beam speed with no special cases.
- `phos` (GLSL TOP + Feedback): persistence. Keeps the brighter of new light and the fading screen, with a separate decay per colour channel so the afterglow shifts hue (P7: blue-white flash, yellow tail; amber: red tail). Alpha carries a stamp of the shot so the screen is wiped at a cut.
- `scan_src` (added by the second builder): a 512 x 288 picture for the scan take only, either a phrase in Archivo Black (`scan_text`) or a lit, turning model (`scan_render` of `sm0..2`, the rows of `DEFAULTS['SCAN_MODELS']`: marble bust, rubber duck, space helmet). It is the third input of `path`; a Switch TOP feeds black on every other take so the render does not cook.
- `sec` / `seclag`: the hub's section index minus a lagged copy of itself is a section kick, 1 at a change and gone in under a second.
- Two reduced-size blurs for glow, then `post`: exposure, white-hot core, graticule (grid or polar, lit by the glow behind it), tube tint, negative mode, rounded tube face, grain.

## Takes (`TAKES` in build.py; `Take % 11`)
| # | name | what you see | capture |
|---|---|---|---|
| 0 | word | one phrase as a green P31 outline, low and off-centre on a grid graticule; on the last beat of every 4 it lets go into the raw stereo figure and the next phrase condenses out of it | take_0.png |
| 1 | gonio | the stereo field itself as a full-frame amber cloud on a polar graticule, with a small label word in a corner | take_1.png |
| 2 | wire | a drawing sheet, blue-white: one model turning in 3D, large, on one side; its still front elevation and plan small on the other; morphs to the next model every 8 beats | take_2.png |
| 3 | macro | extreme close-up of a giant glyph outline: fat defocused ribbons crossing the frame, written by a travelling head, P7 blue flash and yellow afterglow, no graticule | take_3.png |
| 4 | arcade | colour vector monitor: eight different models, each its own colour, spinning on a 4 x 2 board that shuffles each bar | take_4.png |
| 5 | timebase | swept dual-trace scope: left channel above, right below (or overlaid, by seed), with a readout word | take_5.png |
| 6 | lissajous | four nested 3D Lissajous knots, amber to red, ratios change with seed and every 8 beats | take_6.png |
| 7 | wall | negative: a lit green screen with eight text blocks cut out of it in black, written in fragments by travelling heads | take_7.png |
| 8 | dial | aqua: phrases bent round three concentric rings that tick round one notch per beat (outer and inner one way, middle the other), a small circular waveform at the hub; larger than the frame and pushed to one side, tilted by seed | take_8.png |
| 9 | scan | hot pink: a raster of 64 scan lines pushed out of the screen by the brightness of a picture, seen at a slant (Rutt-Etra). Three shots in five the picture is a lit turning model (marble bust, rubber duck, space helmet), two in five a two-line phrase | take_9.png |
| 10 | waterfall | violet: one waveform trace climbing away in steps, the long afterglow leaving the last seconds behind it as a ridged trapezoid landscape; small readout word | take_10.png |

Contact sheets: `captures/takes_sheet.png` and `captures/takes_sheet_b.png` (the same shots 2.4 s later); the first builder's eight are in `captures/before_takes_sheet.png`. Seed varies inside a take: which phrase/model/glyph comes first, side of frame, scale, tilt, starting yaw, the gonio's axis (mid/side or rotated 45 degrees), traces split or overlaid, Lissajous ratios, arcade palette order, and where the write heads start.

## Describe mode (2026-11-11)
With the scene's `Describe` toggle on, every word on screen explains the take. The words are the `describe` entry of each row of `TAKES` in build.py, baked into `paths.npz` as extra rows (groups `d_<take>`; `python bake_paths.py --describe`, which leaves the 39 picture rows byte for byte) and mirrored to preset.json by `python sync_preset.py`. The `takes` table has every column twice (`x` and `d_x`); `tk` reads the `d_` set when Describe is on, so the toggle only changes uniforms: no rebuild, nothing loaded. build.py refuses to build if the baked words differ from TAKES.
| # | take | where the words go | words seen (capture) |
|---|---|---|---|
| 0 | word | replace the phrase | VECTOR SCOPE / ONE BEAM DRAWS THIS / AUDIO SHAKES THE LINE / SLOW BEAM = BRIGHT LINE / EVERY 4 BEATS IT LETS GO / THE GLOW IS FADING PHOSPHOR (`desc_0.png`, `desc_0b.png`) |
| 1 | gonio | the corner label, 1.5x larger, thin beam | STEREO FIELD / RAW AUDIO SAMPLES / LEFT AGAINST RIGHT / 800 SAMPLES PER FRAME (`desc_1.png`) |
| 2 | wire | an extra label gun, bottom left | A 3D MODEL TRACED BY THE BEAM / ONE TURNING VIEW FRONT AND TOP / NEW MODEL EVERY 8 BEATS (`desc_2.png`) |
| 3 | macro | giant letters become X, Y, XY, S, O; extra label gun with its own thin beam | MACRO: ONE LETTER OUTLINE, VERY CLOSE / A WIDE BEAM OUT OF FOCUS / BLUE FLASH YELLOW AFTERGLOW (`desc_3.png`) |
| 4 | arcade | extra label gun (the ninth) between the two rows | EIGHT BEAMS, EIGHT 3D MODELS / THE BOARD SHUFFLES EVERY BAR / 4096 POINTS PER MODEL (`desc_4.png`) |
| 5 | timebase | the readout label, larger | LEFT AND RIGHT WAVEFORMS / TIME RUNS LEFT TO RIGHT / ONE FRAME OF AUDIO (`desc_5.png`) |
| 6 | lissajous | extra label gun, bottom left | LISSAJOUS KNOTS / SINE WAVES ON X, Y AND Z / NEW RATIOS EVERY 8 BEATS (`desc_6.png`) |
| 7 | wall | replace the eight blocks; whole blocks, smaller, held still | ONE BEAM DRAWS IT ALL. / SLOW BEAM: BRIGHT LINE. / CORNERS BURN AS DOTS. / THE SCREEN IS INVERTED. / 4096 POINTS PER BLOCK. / LEFT AUDIO MOVES X. / RIGHT AUDIO MOVES Y. / EIGHT BLOCKS, EIGHT BEAMS. (`desc_7.png`) |
| 8 | dial | replace the ring phrases | TEXT BENT ROUND A RING / ONE NOTCH PER BEAT / THREE RINGS / KICKS PART THE RINGS / WAVEFORM AT THE HUB / POLAR COORDINATES / SIX BEAMS / MIDDLE RING TURNS BACK (`desc_8.png`, `desc_8b.png`) |
| 9 | scan | phrase shots: the big words; model shots: an extra label gun, top left | SCAN LINES / 64 LINES / BRIGHT LIFTS / RUTT- ETRA (`desc_9_text.png`); PICTURE BRIGHTNESS LIFTS 64 SCAN LINES / A RUTT-ETRA SCAN SEEN AT A SLANT (`desc_9.png`) |
| 10 | waterfall | the readout label, larger | WATERFALL / ONE TRACE CLIMBS / AFTERGLOW KEEPS THE PAST / 30 STEPS PER 4 BEATS (`desc_10.png`) |

Contact sheet: `captures/describe_sheet.png`. Labels do not morph or shake: they blank for a quarter of a beat and the next words appear.

## Input (2026-11-11)
`Input` names a TOP (another scene's `out1`). `inp` is 1 when it names a TOP other than this scene's own output; `in_sel` (Select TOP, 512 x 288, only reads) and `in_soft` feed the fourth input of the `scan_src` switch, which is the picture input of `path`. Blank or wrong path: the switch and `uIn` are exactly as before. Takes with `inmode=1` use it:
- 9 scan: the picture replaces the phrase or model: 64 scan lines lifted and brightened by its brightness (`in_9.png`, `i2_9b.png`). The strong one.
- 5 timebase: 32 stacked traces, each still moved by the left or right waveform, lit where the picture is bright (`in_5.png`, `i2_5b.png`).
- 10 waterfall: the landscape becomes the picture, 32 rows raised by brightness in the same trapezoid, with the climbing trace as a bright row (`in_10.png`, `in_10b.png`).
- The other eight takes ignore Input and play as normal (`in_2_ignored.png`).
Sheet: `captures/input_sheet.png`, `captures/i4_sheet.png`.

## Packs (2026-11-11)
Everything the scene says and every model it shows is one dict, `DEFAULTS`, at the top of build.py: `WORDS`, `BLOCKS`, `GLYPHS`, `FORM` and `MODELS` (what `bake_paths.py` bakes, in row order) and `SCAN_WORDS`, `SCAN_MODELS` (the scan take's pictures). build() reads it through `scene_words`, so a pack that holds `scenes/sc_vector_scope/words.json` replaces any of those names. Because the outlines are baked, such a pack also holds its own `paths.npz` and `paths.json`; `load_paths.py` and build.py find them with `mod.paths.scene_file`. build() compares the row names of the loaded `paths.json` with the words and refuses to build when they differ. Takes name their group of rows (`'word'`, `'model'`, ...); first row and count come from the loaded `paths.json`, so nothing assumes a row number.
`python bake_paths.py` bakes the shipped pack (`<repo>/assets`, or `TDH_ASSETS`; it does not follow `assets.local.txt`). If that pack has a `scenes/sc_vector_scope/words.json`, it bakes those words and models and writes the two files beside it, never into this folder.

## Assets (2026-11-11)
Nothing in the scene names a folder: every file parameter is a `mod.paths` expression, and the builder finds the repository from `td.project.folder`. What it takes from `<assets>/`, and what happens without it:
| Used | By | With no assets |
|---|---|---|
| nothing | words, blocks, glyphs, the drawn card and all 16 wireframe models on ten of the eleven takes | the same pictures: their beam paths are committed in `paths.npz` (448 KB), baked from the fonts and models beforehand |
| `<assets>/fonts/ArchivoBlack-Regular.ttf` | `scan_text`, the phrase the scan take lifts its raster with | TouchDesigner's default face: thinner letters, same words (`p2_na_9t.png`, `p2_na_9td.png`) |
| `<assets>/models/marble_bust`, `rubber_duck`, `space_helmet` (`model.obj`, `basecolor.png`) | `sm0..2`, the lit turning model of the scan take | TouchDesigner's bundled teapot for all three, untextured, scaled 0.5 and lowered 0.23 by `fit` so it fills the frame like a library model (`p2_na_9m.png`, `p2_na_9m_b.png`) |
| the pack's `chicago` and `barlow` faces (a file, or the stand-in its `aliases.json` names), 16 x `<assets>/models/<slug>/model.obj` | `bake_paths.py` only (plain python) | the baker stops with a message naming what is missing; the scene is unaffected |

Without assets: `captures/p2_na_sheet.png`. With: `captures/p1_sheet.png`.

## Channel to visual
| Feed | Drives |
|---|---|
| raw audio samples (hub `audio`, 800 per frame) | added to beam X (left) and Y (right) on every shape; the whole picture on gonio and timebase |
| `energy` | how much waveform gets into the beam (quiet = clean vector drawing, loud = fat shivering one); tube ambient glow |
| `level` | normalises the stereo figure so quiet bars still fill the tube |
| `beat_pos` | shape changes every 4 or 8 beats with a spring morph that overshoots and rings; the word take's dissolve on the last beat; write-head position |
| `bar_pos` | the arcade board's shuffle |
| `hit_low` -> Spring CHOP | scale kick that rings (about 5 Hz); beam brightness |
| `hit_mid` -> Spring CHOP | a shear and small roll that ring |
| `hit_high` | beam fattens for an instant |
| `pulse` | exposure breathes on the beat |
| `evolve` | model rotation, word sway, macro pan, Lissajous phase |
| `shot age` | the picture is written on over the first 0.3 s of a shot |
| `shot seed` | see above |
| `section` | index: every take picks different shapes (rows shift by 3 per section; scan phrase too). Change: a kick that for about half a second multiplies the waveform in the beam by up to 6, swells the drawing 30% and brightens it (`sec6_sheet.png`) |
| scan take only | picture brightness lifts the raster and brightens the line; `hit_low` spring deepens the relief and swells the model; `beat_pos` swings the model |
| dial take only | `beat_pos` ticks the rings round; `hit_low` spring parts the outer and inner rings |
| waterfall take only | `beat_pos` is the climb (one pass per 4 beats); `hit_low` spring raises the trace |

`pitch`, `vocals`, `bass` and the `spectrum` TOP are not used.

## Log (newest first)
- 2026-11-11 Generic defaults (sixth builder). The words, models and baked paths in this folder are now generic ones made from the shipped asset pack; the originals live in a private pack's `scenes/sc_vector_scope/words.json`, with that pack's own `paths.npz` and `paths.json` beside it.
  - build.py: one `DEFAULTS` dict read through `scene_words`; `paths.json` and `paths.npz` found with `scene_file`; groups by name; a check that the loaded paths were baked from the loaded words. See Packs above.
  - bake_paths.py: bakes `DEFAULTS`; fonts and models are found the way the engine finds them (file, else the pack's alias), so the `chicago` rows of the shipped pack are IBM Plex Mono.
  - Models, judged from `captures/vs_models_preview.png` and `vs_var1.png`: all sixteen as contour slices first. The gramophone's horn only read when cut front to back; the space helmet front to back with fewer cuts; the crystal cluster and the ribbon loop side to side; lander and wire cage were confetti as slices and read as feature edges.
  - Shipped pack (`Assets` set to `<repo>/assets`, rebuilt): all eleven takes, scan with phrase and with each of its three models, Describe on four takes (`g_sheet_a.png`, `g_sheet_b.png`, `g2_sheet.png`). At size 1.25 the space helmet overflowed the scan frame and the bust was cropped -> sizes 0.95, 1.1, 1.2 beside the model names. tdh.errors empty; tdh.check FAIL, FAIL (cook_budget 32 ms: the three model loads counted as per-frame cost), PASS (1.7 ms). Tox, snapshot and hero (the arcade board) saved from this build, with `Assets` blanked for the save so no folder is stored.
  - Private pack (`Assets` blank on a machine whose `assets.local.txt` names one, rebuilt): the same takes and seeds as captured before the change (`ref_sheet_a.png`, `ref_sheet_b.png` against `pv_sheet_a.png`, `pv_sheet_b.png`) show the original words, face and models in the same layouts.
  - Review, same day: both packs rebuilt and captured again (`rv_g_sheet_a.png`, `rv_g_sheet_b.png` shipped; `rv_p_sheet.png`, `rv_end_sheet.png` private). Tox and snapshot saved again from the shipped-pack build, without the capture helper's storage. tdh.check on the shipped pack: FAIL (cook_budget 22 ms, model loads), PASS (2.6 ms).
  - Not done: the thin skeleton key is a bare line when the drawing sheet shows it edge on (`g_2b.png`). The Describe rows of a pack's own `paths.json` must match `TAKES`: changing a Describe word means re-baking every pack that has its own paths.
- 2026-11-11 Portability (fifth builder). No picture was meant to change. Reference before touching anything: `p0_ref_sheet.png`.
  - build.py, rebuild.py and bake_paths.py name no folder: the repository is `td.project.folder` inside TouchDesigner and `Path(__file__).resolve().parents[2]` in plain python; shader DATs, the Script TOP's callbacks, the font, meshes and textures are `mod.paths` expressions.
  - `paths.npy` (6.0 MB of float32) replaced by `paths.npz` (328 KB): coordinates as int16 steps of 1/32767, each sample stored as its difference from the one before, pen bits packed (`load_paths.py`). Largest difference from the old file 0.000015 units, about a hundredth of a pixel. `python bake_paths.py --describe` run against `<assets>/fonts` reproduced the file bit for bit, so the gathered fonts are the ones the paths were baked from. Plain compressed float32 was 2.15 MB, over the 2 MB allowance.
  - With assets, rebuilt: all eleven takes, scan with model and with phrase, Describe and Input (`p1_sheet.png`) match `p0_ref_sheet.png` and `takes_sheet.png` in kind.
  - Without assets (`Assets` pointed at the empty `captures/_noassets`, rebuilt): first build left three warnings, File not found (""), on the unused `sm*/tex` Movie File Ins -> they keep the operator's own default picture when there is no texture, and the material's map is an expression that is empty then. The teapot is 2 units wide and stands on the floor, so at the library's scale it overflowed the frame -> `fit` (Transform POP, expressions on `mod.paths.have`). Then tdh.errors empty; `p2_na_sheet.png`: word, wire, arcade, wall, waterfall as with assets; scan shows the teapot or the phrase in the default face; Describe and Input work.
  - Blanked `Assets`, rebuilt, `p4_sheet.png` as `p1_sheet.png`.
  - Final: one more clean rebuild (`p5_sheet.png`), tdh.errors empty; tdh.check PASS (1.7 ms), FAIL (cook_budget 28.5 ms: the three model loads counted as per-frame cost), PASS (2.8 ms). Tox and snapshot saved with Assets blank, Describe off, Input blank, Preview off. `python -m pytest -q tests/test_portable.py -k sc_vector_scope`: 1 passed.
- 2026-11-11 Describe and Input (fourth builder; an earlier attempt at this left no changes in the files or the COMP). Rebuilt on the new scaffold first and checked three takes against yesterday's (`s1_take0.png`, `s1_take9.png`).
  - Describe: words per take as in the table above. First pass (`d1_sheet.png`): the gonio label was a smear (fat 0.0045 beam, shaken by hits) -> its own 0.0024 beam width and `steady`; wall was still fragments at trace 0.88 -> whole blocks; "CONTOUR LINES" was untrue for the four feature-edge models -> "TRACED BY THE BEAM". Second (`d2_sheet.png`, `d3_sheet.png`): wall at full pen was black blots and the two-line blocks overlapped -> scale 0.44, gain 0.4, held still on hits. Labels caught mid-morph were unreadable (`describe_sheet.png` take 4) -> labels snap. Scan label sat on top of the big Describe words (`input_sheet.png` desc_9_text) -> label off while the words are the picture.
  - Input: tried the picture as beam brightness (Z axis) on gonio, wall and macro: unrecognisable (`i1_sheet.png`), removed. Timebase first pass was far too dim because 16 lines per gun means a 16 times faster beam (`i1_sheet.png`) -> pen x8. Waterfall first read one picture row per step and let the afterglow hold the rest: old rows had faded to a fifth (`input_sheet.png` in_10) -> all 32 rows every frame.
  - MAXGUNS 8 -> 9 (the arcade label). Beam width now reaches the pixel shader in vCol.a so one gun can be thinner.
  - Describe off and Input blank after the final rebuild: `off_0..10.png`, `off_sheet.png`, same pictures as `takes_sheet.png`.
  - Final: tdh.errors empty; tdh.check pending, then FAIL (cook_budget 24 ms just after the rebuild, 17 other scenes building), then PASS (1.0 ms). Tox and snapshot saved with Describe off and Input blank. Cost of Describe: one more gun of 4096 segments on five takes; of Input: a 512 x 288 Select and Blur, cooked only on the three takes that use it.
- 2026-11-10 second builder (art direction pass). Judged first from `j_sheet.png` (8 takes x 2 moments, feed logged): all eight already differed at a glance; weakest were wire (one small abstract model in a black frame), timebase (a stock scope picture) and the unused `section`. Changes, each kept after viewing captures:
  - Three new takes, each a different way of using the beam: dial (`k_8_b.png`, `m8_sheet.png`), scan (`l_sheet.png`: two models and a phrase) and waterfall (`k_sheet.png`). Eleven takes now, eleven different thumbnails (`takes_sheet.png`).
  - Wire became a drawing sheet with two still orthographic views (`m_sheet.png`). Scale 1.62 cropped tall models (`takes_sheet` of that round), back to 1.36.
  - Section change now does something (`sec6_sheet.png`, 8 consecutive captures from a change: the Lissajous knot bursts into a scribble and settles). Lag 0.3 gave a kick that was already 0.2 one 0.2 s frame later; 1.0 was still 0.24 after 0.6 s; 0.7 kept.
  - Kick: beam gain swing 0.5 -> 0.8 and scale 0.22 -> 0.30 of the spring.
  - Scan: ivory with a red tail read as amber, too close to gonio and lissajous: now hot pink. Waveform gain 0.25 turned a phrase into scribble at energy 0.69 (`l_9_t2.png`): 0.11. Tilt reduced so models are not seen from above.
  - Dial: radial waveform gain 1.5 made the lettering a wheel of spokes (`m_sheet.png` take_8): 0.55, smoothing 3. Hub waveform clamped (it was a white starburst at energy 0.63).
  - `cap2.py` (waits in seconds, not frames: the instance swung between 5 and 60 cooked frames a second during this pass) and `cap_section.py` (captures the frames after the next section change).
  - Final: clean rebuild, 22 captures (`take_N.png`, `take_N_b.png`), tdh.errors empty, tdh.check FAIL on the first run (cook_budget 438 ms: the three model loads) and PASS on the second (1.4 ms, scan take up). Steady cost from the operators: scan take 2.7 ms CPU + 0.4 ms GPU (1.7 ms of it the 512 x 288 model render), arcade take 0.7 + 0.3. Hero = take 9.
- 2026-11-10 final: clean rebuild from build.py, eight takes captured (`take_0..7.png`, `takes_sheet.png`), six moments with feed (`moments_sheet.png`), arrival burst (`final_arrive_sheet.png`: black at age 0, partial outlines at 0.2 s, whole board by 0.38 s). tdh.check PASS on the second run (cook_budget 6.2 ms measured while about ten other scenes were cooking). Hero = take 0 mid-dissolve.
- Arrival changed from 0.45 s eased to 0.3 s linear: at age 0.2 s the eased version had drawn a fifth of the path, which read as a blink of black.
- One boxy model re-sliced front to back so its recess shows; one open-frame model back to feature edges (its slices were confetti); one dropped (a bare ring) and five added so the arcade's eight guns (stride 2 over 16 models) never show the same model twice.
- Spring CHOP switched from method 'disp' to 'force' on a light mass: 'disp' only followed the hit envelope (minimum -0.05, no ring). Read sample by sample from the CHOP: bounded, swings to about 0.5 on a 0.55 hit and oscillates. The ring was NOT seen in motion: every burst I took ran at about 5 cooked frames a second on the shared machine (`sheet_h.png`).
- Generated models as contour slices instead of feature edges (`f_wire_a.png`: a figurine reads as a lathe drawing; before, `02_wire.png`, `e_arcade.png`, it was a tangle).
- Cut wipe: an age window (wipe while age < 0.04, then 0.1) missed the cut whenever frames dropped and left the previous take's picture on the tube (`sheet_c.png`: a green phrase under a blue model). Replaced by a shot stamp in the feedback's alpha. Decay now uses `absTime.stepSeconds` so persistence lasts the same time at any frame rate.
- `tk` (take row as channels) cooked every frame at 0.6 ms because its expressions read `op('shot')`, whose age channel is time dependent; reading `parent().par.Take` instead cooks it only on a take change (12 cooks in 800 frames).
- Gonio: the track is close to mono, so the true mid/side figure was a thin upright line (`sheet_a.png` take 1). Now side x3.5 plus mid plotted against itself about 0.3 ms earlier (a phase portrait), gain riding `level`: a galaxy that fills the tube (`e_gonio.png`). Still nothing but the samples, but it is not a calibrated goniometer.
- Word take dissolve added (`sheet_d.png`, 16 frames across a step).
- All eight kinds first working (`sheet_a.png`); exposure was far too hot in the first frame (`01_first.png`, every line white) and the graticule invisible (gratlum 0.1 -> 0.4-0.6).
- First build: path shader, instanced beam, phosphor feedback and post worked on the first run apart from a `N` redefinition in the vertex shader.

## Weak points
- No assets: the scan take's three models are one teapot, so its model shots differ only by rotation and the music; its phrases are in a thin default face that the 64 lines resolve less boldly than Archivo Black. Everything else is unchanged, but only because the outlines are committed: new words or models cannot be baked without the fonts and the library.
- `fit` knows the teapot's size as two constants in build.py (`TEAPOT_FIT`); a different fallback mesh would need new ones.
- Describe: the wall's blocks still morph into the next blocks every 8 beats, and for about a beat the negative screen is black smears (`d5_7.png`). The dial is dense: at any moment two or three of its five phrases read and the rest are off-frame or upside down. Timebase with seed above 0.6 overlays the traces on the label (`d3_5.png`). The word take's phrase is unreadable for the last beat of every four (that is the take). Macro's X/Y/XY letters are no more readable than the usual ones; only the label explains.
- Describe labels on wire and lissajous can sit over the drawing when the seed puts the model on the left.
- Input: only three of eleven takes use it. Waterfall crowds the top third of the picture into the far rows, so text there is lost (`in_10.png`: INPUT reads, TEST does not). Timebase has 32 lines: big shapes and large type only. All three use brightness only; colour is discarded.
- Input was tested with the test card only, not with another scene's out1.
- The spring ring on hits is verified in numbers only, not seen in motion.
- Machine load: most captures were taken at 5 to 20 cooked frames a second, so the stepped ghosts on spinning models (`f_arcade_a.png`) are frame-rate artefacts; at 60 fps they should be a smooth afterglow. Not confirmed.
- The first cooked frame of every shot is black (the tube is wiped and the beam has not started). One frame at 60 fps; a visible blink if the frame rate is low.
- Some models are abstract from some angles (ribbon loop, space helmet, wire cage); the eye needs the rotation to read them.
- The macro take has no readable subject by design, but at a quiet moment it can be three static stripes.
- Labels on gonio and timebase are soft: the beam is as wide as their strokes.
- The arcade board hides its grid for about a beat per bar while the subjects slide; mid-slide stills look chaotic (seen in an earlier capture, not kept).
- The gonio take with the 45 degree axis (seed 0.77) in a vocal passage was a dim brown full-frame haze (`take_1.png`); the other axis is a bright galaxy (`take_1_b.png`).
- A section change on the wall take smears the cut-out text into blots for half a second (`take_7_b.png`); on timebase it throws the traces across the whole tube (`take_5_b.png`). Left in on purpose, but nobody has watched it at speed.
- Dial: all three test seeds put the rings on the left with the right third of the frame empty; the lettering is dense and only the middle ring reads easily.
- Scan: the model render costs 1.7 ms CPU, and a dark or boxy model reads less clearly than a pale rounded one (`l_9_a.png`).
- Waterfall depends on frame rate: the ridges are one per cooked frame, so at 5 frames a second there are few of them.
- The new takes were judged from stills only; the dial's tick and the waterfall's climb were not watched in motion.

## Next
- Capture a hit at a real 60 fps and tune the spring by eye.
- Depth-sort nothing, but dim back-facing contour slices more so models read without rotation.
- A ninth take: a word written once, slowly, by a single visible dot with a long P7 tail.
- Use `section` to pick the phosphor in the word take.

## Files
`build.py` (builder, TAKES), `bake_paths.py` (offline path baker), `load_paths.py` (the packed format of `paths.npz`, and the Script TOP's callbacks), `paths.npz`, `paths.json`, `shaders/` (path.frag, beam_vertex.glsl, beam_pixel.glsl, phosphor.frag, post.frag), `rebuild.py`, `sync_preset.py` (build.py -> preset.json; `--check`), `cap.py`, `cap2.py`, `cap3.py` (cap2 with Describe and Input per shot), `cap_section.py`, `burst.py`, `sheet.py` (capture helpers), `checks.json`, `sc_vector_scope.tox`, `snapshot/network.json`.
