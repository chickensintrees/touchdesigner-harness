# sc_flow_mosh: optical-flow datamosh

## Intent
Datamosh made on purpose. A clean poster frame (a wordmark, a lit rotating library model, bold ident-palette colour fields) is shown only for an instant on the kick; between kicks the picture is never redrawn. Instead the motion of the hidden clean source pushes the pixels of the last output around, so the old poster melts along the new poster's movement.

It works when: on a hit you can read the wordmark or name the model at a glance; half a beat later the same colours are visibly torn and dragged in the direction the model is turning; and after several seconds without a hit it is still made of crisp palette colour, not grey mud or white.

## Words and models (2026-11-11)
Everything the scene shows that is content rather than technique sits in one dict, `DEFAULTS`, at the top of `build.py`: `PHRASES` (16 lines), `CARDS` (4), `MARKS` (the two wordmarks set in type when a pack has no lettering art), `HEROES` (4 rows: model, stand-in colour, PBR MAT parameters) and `WORLD` (11 rows: model, scale, cell count, fallback height, stand-in colour). `build()` reads it once through `LIB['scene_words']`, so a pack that holds `scenes/sc_flow_mosh/words.json` replaces any of those names whole; the Describe words (`DESCRIBE`) are not content and are not replaceable. The lettering is asked for as `art/stack_rgb.png` and `art/mark_rgb.png`.

On the pack that ships with the repository: the poster's wordmark is REAL / TIME or HARNESS; the heroes are the gramophone, space helmet, marble bust and hourglass; the field is broken columns, balanced solids, amphorae, traffic cones, astrolabes, rubber ducks, skeleton keys, landers, wire cages, crystal clusters and ribbon loops (pierced_stone is the one object not used); the phrase face is IBM Plex Mono (the pack's answer to the name `chicago`), wider and lighter than the face the rows were first set in.

Log:
- 2026-11-11: the defaults in `build.py` are generic (words about real-time picture-making and a catalogue of unexplained objects; the shipped pack's models by their real names). The originals live in a private pack's `scenes/sc_flow_mosh/words.json`; built on that pack the scene is as it was (same words, models, per-model looks). Older entries below describe pictures made with that pack, with its content named in neutral terms.
- 2026-11-11, seen on the shipped pack (rebuilt from `build.py`, every take at seeds 0.37, 0.81 and 0.13, 26 and 85 frames into the shot: `gen_sheet.png`, `gen81_sheet.png`, `gen13_sheet.png`; Describe on takes 0, 2, 4, 5: `gend_*.png`). Changed after looking: the space helmet and the marble bust were white blobs in the void and 1-bit takes, so their rows darken the base colour (0.5 and 0.6); broken columns at scale 1.6 filled the aisle frame and burned out, now 1.25 and darker; two phrases ran off the end of their atlas row (IBM Plex Mono is 32 px a character at 40 px, so 38 characters is the limit; `sync_words.py --check` now counts them). `hero.png` is the poster take, REAL / TIME with the hourglass, 40 frames into a shot.
- 2026-11-11, private pack after the change: its snapshot differs from the one committed before only in the two art names and the live `ctl` values (20 lines of a sorted diff); takes at seeds 0.37 and 0.81 show the same words, models and layouts as before (`before_sheet.png`, `after_sheet.png` and the `81` pair).

Weak, honest (shipped pack):
- The void caption is thin in Plex Mono at about 27 px and is the first thing the vertical sort eats; it reads in the first quarter second only.
- The floor-plan paint is mostly under the objects, as before; a word or two shows.
- The cutter was live and changed `Take` during some captures, so a few sheet tiles show a different take from their label; every take was still seen at least twice. Nothing was watched in motion.
- The tox and snapshot were saved from the build on the shipped pack with `Assets` blanked for the save (a set `Assets` is a folder on this machine). Opening that tox on a machine whose default pack is another one keeps the shipped pack's words and instance tables until a rebuild.

## Assets (portability pass, 2026-11-11)
Nothing in this folder names a folder on a machine. `build.py` finds the repository through `td.project.folder`; every file parameter is an expression on the scaffold's module DAT (`mod.paths.here`, `font`, `model_file`, `model_texture`, `asset`), so the .tox and the snapshot hold expressions. The fallbacks are decided by expressions too, not at build, except where noted.

| Used from `<assets>/` | Where | When it is missing |
|---|---|---|
| `models/<slug>/model.obj` for the four heroes and the 11 props of the field (named in `HEROES` and `WORLD` of `DEFAULTS` in `build.py`, or by the pack's own `words.json`) | `m_*/mesh`, `w_*/mesh` | TouchDesigner's bundled teapot. `fit` (a Transform POP after `mesh`, identity while the file exists) scales it to the library's 1-unit size, centres a hero, and stands a prop on the floor where the library mesh's base was. |
| `models/<slug>/basecolor.png` | `m_*/tex`, `w_*/tex` | `flat`, a plain colour per model (`HEROES` and `WORLD` in `build.py`); a hero whose row sets metal parameters is still metal as a stand-in. |
| `models/<slug>/info.json` | at build, `_world` reads each prop's height (`size_units[1]`) so it stands on the floor | the height written in that prop's `WORLD` row |
| `art/stack_rgb.png`, `art/mark_rgb.png` | `mask0`, `mask1` | `mask0_f`, `mask1_f`: the two `MARKS` of `DEFAULTS` set in type on the same canvas (third input of `mask0_sw`, `mask1_sw`). |
| `fonts/ArchivoBlack-Regular.ttf` | cards, Describe wordmarks, the stand-in wordmarks | TouchDesigner's default face (Verdana here) in bold; Legacy Font Selection is switched on by the same expression because Bold does nothing without it. |
| `fonts/ChicagoFLF.ttf` | phrase atlases `phr*`, the Describe label `lab` | The default face, regular. It is wider than Chicago, so at build an atlas whose widest row would not fit is set a little smaller (40 px became 39.6 for the scene's own phrases, 24 px became 23.2 for the label). Row widths (`pw*`, `lab_w`) are measured at build with whichever face is there: **built-time data**, so after adding or removing fonts, rebuild. |

Not used: music and feeds (the hub's business). No data file was added to this folder; the only precomputed data is the 11 prop heights, now literals in `WORLD`.

**What it looks like with no assets** (`noassets_takes_sheet.png`, takes `noassets_take_<n>_a.png` and `noassets_take_<n>.png`; Describe and Input in `noassets_describe_input_sheet.png`): the same seven takes with the same motion, palettes, mosh and music mapping, but every model is the Utah teapot. Poster: a coloured or gold teapot beside the wordmark in bold sans. Aisle and plan: a field of 162 teapots in flat palette colours on the same tiles. Transplant: the card in bold Verdana, carved into the shape of a turning teapot. 1-bit: rows of regular Verdana with a dithered teapot. Void: a small pale teapot, caption and tubes.

**Weak with no assets, honest.**
- One model everywhere: a section change no longer changes the hero's shape, only its colour; the aisle is rows of lumps, far less of a place than the real models, and near teapots are dim blue-green blobs in the dark grade (`noassets_take_1.png`).
- The 1-bit rows lose the Chicago look entirely; regular Verdana is thin when thresholded and smears to nothing sooner (`noassets_take_4.png`).
- The stand-in wordmark is plain bold Verdana, not lettering; the void caption is hard to read (it was small already).
- Flat-coloured teapots in the plan take wash towards white under the lights; their colours are closer together than the real props' textures.
- A .tox saved with fonts and opened without them keeps Chicago's row widths (see the table): rows may overlap or leave gaps until a rebuild. Not tried.
- The no-assets state was only tried through the COMP's `Assets` parameter pointed at an empty folder on this machine, not on a second machine or a fresh clone.

**Checks (portability pass).** `tdh.errors` empty with assets and with none (also with Describe on and with Input set, in both states). `python -m pytest -q tests/test_portable.py -k sc_flow_mosh`: 1 passed (it failed before on `build.py` and the snapshot). `tdh.check` after the final rebuild, three calls: pending, fail on cook_budget alone at 22.3 ms (the call after the tox save), PASS at 2.75 ms. `python sync_words.py --check` passes. Tox and snapshot (266 operators) saved with Assets blank, Describe off, Input blank, Preview off.

Log, portability pass (newest first):
- Final state, real assets, rebuilt from `build.py`: `take_<n>_a.png`, `take_<n>.png` (sheet `takes_pairs_sheet_v6.png`), Describe on takes 0 and 4 (`port_describe_*.png`), Input on take 2 (`port_input_2*.png`). Compared with `ref_sheet.png` (before any change) and `takes_pairs_sheet_v5.png`: same pictures.
- No assets, Describe on (takes 4, 0, 2) and Input set to the test picture (takes 2, 4): `noassets_describe_input_sheet.png`. Label and rows fit; the input is moshed as with assets.
- No assets, second build: `noassets_takes_sheet.png`. Bold wordmark and cards after turning Legacy Font Selection on in the fallback.
- No assets, first build: `na_sheet.png`. Worked first time, but the wordmark and cards were thin regular Verdana: the Text TOP's Bold toggle did nothing (text width 838 px with and without it; 926 px with Legacy Font Selection on).
- With assets after converting: `pa_sheet.png` against `ref_sheet.png`.
- `ref_sheet.png` (`ref_<n>_a.png`, `ref_<n>.png`): all seven takes before anything was changed.

## Describe mode and Input (fourth pass, 2026-11-11)
Two agents did this: the first wrote most of it and was cut off before logging or final checks; the second re-read every step, rebuilt, looked at every take again, fixed what is listed under "Changed by the second agent", and finished. With `Describe` off and `Input` blank the scene is as before (`take_0.png` to `take_6.png` and `takes_pairs_sheet_v5.png`, captured after the Describe and Input runs on the same build).

**Describe (`parent().par.Describe`).** The words live in `DESCRIBE` in `build.py`, keyed by take name, and `sync_words.py` mirrors them into `preset.json` (`python sync_words.py --check` fails on drift). Everything is baked at build next to the scene's own version and picked by Switch operators (`mask0_sw`, `mask1_sw`, `phr_sw`, `pw_sw`, `cards_sw`) or a uniform, so the toggle costs no rebuild and no load. Two kinds of words:
- *In the picture* (they get moshed like the scene's own words): the poster's wordmark becomes DATA / MOSH or DATAMOSH (`mask0_d`, `mask1_d`); the transplant cards become THIS TYPE IS A KEYFRAME. / BORROWED MOTION / MOTION TRANSPLANT / A HIDDEN MODEL MOVES THIS. (`cards_d`); the Chicago phrase rows of the transplant header, 1-bit wall, void caption and floor-plan paint come from per-take atlases `phr_d2`, `phr_d4`, `phr_d5`, `phr_d6`.
- *A label outside the loop* (`lab`, drawn 1:1 by `post.frag` on an ink plate, 24 px Chicago, yellow title and ivory sentence, so it never rots): every take has one. `_label` raises at build if a line is wider than 1210 px, `_phrase_atlas(strict=True)` if a phrase row does not fit, `_world` if the prop count stops being the 162 the words state.

| Take | Label seen in `describe_take_<n>_a.png` | In-picture words |
|---|---|---|
| 0 poster | OPTICAL-FLOW DATAMOSH / A KICK REDRAWS THE POSTER. THEN ITS OWN MOTION DRAGS IT APART. (top) | DATA MOSH or DATAMOSH as the wordmark |
| 1 aisle | DATAMOSH, TRACKING SHOT / THE CAMERA SLIDES PAST 162 PROPS. NEAR ONES SMEAR FASTER. | none (the take has no text) |
| 2 transplant | DATAMOSH TRANSPLANT / THE TYPE IS THE CLEAN FRAME. A HIDDEN 3D MODEL MOVES IT. | one of the four cards; header line such as KEYFRAME: TYPE. MOTION: 3D MODEL. |
| 3 macro | DATAMOSH, ZOOMED IN 5X / EACH SQUARE IS ONE BLOCK. ITS LINE IS THE MOTION IT COPIES. | fragments of the poster's DATAMOSH, if the zoom lands on it |
| 4 onebit | 1-BIT DATAMOSH / PURE BLACK AND WHITE. KICKS REDRAW IT. MOTION SMEARS IT. | 16 sliding rows: OPTICAL FLOW MOVES OLD PIXELS. / THE KICK DRUM REDRAWS THE FRAME. / MOTION IS MEASURED AT 320 X 180. / ... |
| 5 void | DATAMOSH WITH A VERTICAL SORT / BRIGHT PIXELS COPY UPWARD EACH FRAME. A HARD KICK CLEARS THEM. (top) | caption under the prop, e.g. A HARD KICK WIPES THE COLUMNS. |
| 6 plan | DATAMOSH, SEEN FROM ABOVE / 162 PROPS ON TILES. THE CAMERA SWINGS IN TIME WITH THE MUSIC. | floor paint, e.g. TOP-DOWN DATAMOSH OF 162 PROPS. (mostly hidden by props) |

**Input (`parent().par.Input`).** The picture enters where the clean source did. `inp_on` is 1 when the parameter names a TOP that is not inside this COMP (blank, missing, not a TOP and this scene's own operators all count as no input). `inp` (Select TOP) reads it, `inprep` (`shaders/inprep.frag`) fits it to 1280x720, and two Switches route it: `msrc` (the picture whose motion is measured and whose last frame feeds the residual) and `isrc` (the picture I-frames are made of). So the kick shows the other scene clean and its own motion then drags blocks of it apart. Per take, with the test picture (`input_take_<n>_a.png`, `input_take_<n>.png`, sheet `input_takes_sheet.png`):
- 0 poster and 6 plan: the same treatment (frequent clean frames, 8 px blocks); the take's own picture is not used at all. Recognisable always; between close kicks only the edges fray.
- 1 aisle: fewer clean frames and 16 px blocks: the deepest melt of a given picture.
- 2 transplant: the input replaces the type card; the motion still comes from the hidden turning model, and each kick stamps the model's frame difference into it. The strongest combination: the other scene carved into the shape of the hidden model.
- 3 macro: the analyser overlay over the input, zoom capped at 2.2x (5x of an unknown picture was a flat field too often).
- 4 onebit: `inprep` Bayer-dithers the input first (3 px dots), so the mosh pushes dither dots and the final threshold keeps a picture.
- 5 void: `inprep` crushes the input to near black and tints its lights with the shot's hot colour, so only its bright parts grow into rising columns.
While an input is given, Describe shows a second set of labels (sets 7 to 13 of `lab`, `label_input` in `DESCRIBE`, `words_with_input` in `preset.json`), because the takes' own sentences would be untrue: e.g. DATAMOSH OF ANOTHER SCENE / A KICK SHOWS THE INPUT CLEAN. ITS OWN MOTION DRAGS IT APART.; DATAMOSH TRANSPLANT / THE INPUT IS THE CLEAN FRAME. A HIDDEN 3D MODEL MOVES IT.; 1-BIT DATAMOSH OF ANOTHER SCENE / THE INPUT IS DITHERED TO BLACK AND WHITE, THEN SMEARED. The in-picture Describe words are not drawn then: the input is the picture.

**Changed by the second agent** (each seen in a capture):
- `dB_sheet.png`: the Describe cards were cropped by the frame ("A HIDDEN MODEL MOVES THIS." read "A HIDDEN / MODEL / OVES THI"). `src.frag` now gets the Describe flag in `uCam2.w` and keeps the card inside the frame (scale 1.0 to 1.18, 40% of the offset, less tilt, lifted clear of the label); `_card_atlas(fit=(425, 205))` sets the type as large as fits. After: `dx_sheet.png`. With Describe off that branch is not taken.
- Same sheet: DATA / MOSH ran under the model and off the left edge ("DAT / MOS"). The stack word is now at most 800 px of its 1280 px canvas. After: `dx_sheet.png` tiles 0 and 1.
- The 1-bit take had no label; 1.4 s into a shot its rows were smeared past reading (`describe_takes_sheet.png` before the change), so it has one now.
- Words made true: WEAK KICKS REDRAW ONLY PATCHES. became WEAK KICKS REDRAW ONLY THE TOP. (that take's partial refresh is a scan from the top); THE CAMERA SWINGS WITH THE BEAT became IN TIME WITH THE MUSIC (the swing takes eight beats); LONG ROT (jargon) became LEFT TO ROT / FEWER CLEAN FRAMES: 16 PX BLOCKS SLIDE ALONG THE INPUT'S MOTION.
- This file said 173 prop instances; the build counts 162 and now refuses to build otherwise.

**Weak, honest.**
- In-picture Describe words rot like everything else. 85 frames into a kick-less stretch the transplant card read "MOT / TRANSP" and the void caption was gone (`describe_takes_sheet.png`, which is the late capture on purpose); only the label is always readable. `describe_takes_sheet_a.png` is the same takes 30 frames in.
- The poster's label sits top left and in the centred layout covers the model's head (`dA_0_a.png`). The floor-plan paint is fragments under the props; that take is explained by its label alone. Macro shows a word only if the zoom lands on one.
- The void caption is small (about 14 px capitals), as the scene's own caption is.
- Input: takes 0 and 6 are one treatment, not two. With a slow-moving input (the test picture drifts slowly) and a kick on every beat, takes 0 and 6 are close to the input pasted in with frayed edges; takes 1, 2, 4 and 5 are the ones to use as the second half of a combination. Only the test picture was tried, never another scene's `out1`.
- "Blank restores the scene exactly" is shown by structure (all three Switches at index 0, Describe uniforms 0) and by eye in the final captures, not by a pixel comparison: the picture depends on the music, so no two captures match.
- Describe was toggled only between shots in the tests, not mid-shot; mid-shot the in-picture words change at the next I-frame, the label at once.
- Cost of the additions was not measured separately; `inprep` and the unused atlases cook only when selected.

**Checks (fourth pass).** `tdh.errors` empty, also with `Input` set to a missing path, to this scene's own `out1`, to a COMP and to spaces (all read as no input). `tdh.check` run three times after the final rebuild, each in its own call: pending (first sample), fail on cook_budget alone at 24.2 ms (the call after forced cooks and captures), then PASS at 1.05 ms. Tox and snapshot (231 operators) saved with Describe off, Input blank, Preview off. `python sync_words.py --check` passes.

Log, fourth pass (newest first):
- Final rebuild from `build.py`: `describe_take_<n>_a.png` / `describe_take_<n>.png` (30 and 85 frames), `input_take_<n>_a.png` / `input_take_<n>.png` (test picture, Describe on), then `take_<n>_a.png` / `take_<n>.png` with Describe off and Input blank. Sheets `describe_takes_sheet_a.png`, `describe_takes_sheet.png`, `input_takes_sheet.png`, `takes_pairs_sheet_v5.png`.
- `dx_sheet.png`: both stack layouts and the centred layout of the Describe poster, two fitted cards.
- `in_sheet.png` (Describe off) and `ind_sheet.png` (Describe on, seed 0.81): first look at the test picture through all seven takes.
- `dA_<n>_a.png` (full size, each read), `dB_sheet.png`, `d2_sheet.png`: Describe on every take at two seeds; found the cropped cards and the hidden DATA / MOSH.
- `r1_sheet.png`: rebuild on the current scaffold with Describe off and Input blank: same pictures as `takes_sheet.png` from the third pass.
- First agent (not logged by it; file names only): `dn_*`, `d3_*`, `describe_sheet.png`, `i1_mask1_d.png`.

## Takes (third pass, 2026-11-10 evening): the scene no longer repeats
The cutter kept returning to one picture (the wordmark and a model on a disc). There are now seven takes in the `TAKES` table in `build.py`, picked by `op('shot')['take'] % 7`. A take is a row of numbers read through the `tk` CHOP by expressions and uniforms; every model, atlas and render a take needs is loaded at build, and Switch TOPs (`r3d`, `isrc`) cook only the branch in use, so a cut costs no load. `seed` varies each take from inside.

| Take | Name | One line | What `seed` changes |
|---|---|---|---|
| 0 | poster | The original: wordmark, one hero model on a disc, ident-palette fields; kick = I-frame. | palette, layout, model, model heading |
| 1 | aisle | No text. Sideways tracking shot through rows of props on carpet tiles under fluorescent tubes; the flow is parallax, near props smear faster than far ones. | direction of travel, camera height, yaw (-20/0/20), grade (washed beige, sickly green, lights out) |
| 2 | transplant | Classic datamosh transplant: I-frames are a big off-centre Archivo card (the four `CARDS`), the motion comes from a huge turning model that is never shown; each kick stamps the model's frame difference into the type. | card, card colours, scale, position, tilt, donor model |
| 3 | macro | Crash zoom 5x into the buffer (nearest), with a codec-analyser overlay: 16 px block grid and one motion vector per block. Letters and dots become huge torn shapes. | where the zoom lands, underlying poster |
| 4 | onebit | Pure black and white: rows of Chicago phrases sliding in opposite directions, some rows inverted, a Bayer-dithered model punched through; output thresholded to 1-bit. | 5, 8 or 13 rows, which phrases, model side, whole-frame inversion |
| 5 | void | Nearly black: a small prop, a caption, five floating tubes in one hot colour. Vertical sort dominant: every light thing grows into a rising column until a strong kick or two beats clears it. | hot colour (amber, CRT blue, red, green, white), tube layout, prop position, phrase |
| 6 | plan | The prop field from straight above on ident-palette checker tiles with a disc under each prop and a phrase painted across the floor; the camera yaws with the bar and drops in. Many small subjects. | palette, camera height (9.5 to 14.5), heading, phrase |

No centred wordmark in takes 1, 2, 4, 5, 6; take 3 shows fragments of it; takes 1 and 5 (after a second of sort) have no readable text.

**Arrival (first half second).** The driver sees a new `Take`/`Seed`/`Shotstart` and, for `arrive` seconds (0.2 to 0.35), prints the new picture over whatever the last shot left in the feedback buffer (clusters, rising columns in the void, a top-down scan in 1-bit), carried by the new picture's motion, then snaps the clean frame in. On top: the poster's wordmark slams in from oversize, the aisle camera pushes in 2.5 units, the plan camera drops from 9 units higher, the macro zoom ramps 1x to 5x in 0.4 s, void tubes flash. Sequence: `g3_sheet.png` (columns at about 3, 8, 14, 22, 70 frames).

**New parts.** `takes` (Table DAT) and `tk`; `phr` (16 phrases, Chicago, one per 80 px row, drawn by one Text TOP from `phr_spec`) with widths in `pw` (uniform array `uPW`); `cards` (2x2 Archivo cards); `w_*` (11 instanced library props, 162 instances, a grid that repeats every 16 units so the camera wraps without a seam), `cam_aisle`, `cam_plan`, `wrender`; floor, ceiling and tubes are ray-plane hits in `src.frag` matched to the active camera (`uCam`, `uCam2`); `cardsrc` (same shader, role 1) and `isrc`; `mosh` input 4 is the I-frame picture; `post` has zoom, analyser overlay and 1-bit. `Fullhit`, `Rotbeat`, `Maxrot` moved from COMP parameters into the table. Tools: `capture_takes.py`, `measure_takes.py` (both schedule with `run(delayFrames)`, nothing blocks), `contact_sheet.py`.

**Follows the music (per take, from the capture log).** All takes: `hits_low` I-frame or partial refresh, `hits_mid` 30% refresh and block-size jump, `energy` flow gain, `vocals` red/blue split and streaks, section change bloom. `take_1_a.png` (hit_low 0, 0.07 s after an I-frame) against `take_1.png` (hit_low 0.77, I-frame that frame: clean, new section); `take_6_a.png` (0.22 s of rot, torn tiles) against `take_6.png` (pulse 0.99, hit_mid 0.58, vocals 0.99: clean, wide colour split); `take_5_a.png` (0.22 s: short flames) against `take_5.png` (1.48 s without a strong kick: columns to the top of the frame); `take_2_a.png` (0.23 s: card legible) against `take_2.png` = `hero.png` (1.5 s: the type carved into the shape of the turning model). Void sort amount also rises with `rms`; aisle tubes and plan camera height kick with `pulse`.

**Cost** (`measure_takes.py`, cpu + gpu of operators that cooked in the last 3 frames, steady samples): take 0 about 1.0 ms, 1 about 1.5, 2 about 1.1, 3 about 1.1, 4 about 1.0, 5 about 1.0, 6 about 1.4 to 1.75. `wrender` (162 instances; the triangle count quoted here earlier went with a wrong instance count and was not re-measured) is 0.6 to 0.8 ms. First cook after a shader edit was 4 to 20 ms once.

**Checks.** `tdh.errors` empty. `tdh.check`: first run after the rebuild failed cook_budget at 502 ms (it sums the load-time cook of 15 File In POPs and their textures); second run passed at 1.18 ms.

**Weak, honest.**
- Take 3 depends on where the zoom lands: on letters or dots it is the best "macroblock" picture (`g3_sheet.png` row 2), on a chrome model it is grey noise with needles (`take_3_a.png`).
- Take 1 is pale. In the neutral and green grades the near props are close to white, and the mosh is subtle for the first 0.3 s after each I-frame; it needs about half a second of rot to show the parallax smear (`g2_sheet.png` rows 1 and 2). The lights-out grade was last seen in a contact-sheet tile (`g3_sheet.png` row 5), very dark; it was lifted afterwards and not looked at again.
- Take 2's card is still; between kicks all the life is in the rot.
- The plan phrase is mostly covered by props and reads as fragments. I did not check whether it is mirrored at every heading.
- The cutter was live while I worked and took the scene over twice mid-capture (it set Take 43); the captures named here were checked against the log for the right take. I never watched the takes in motion, only stills and sequences of stills.
- One path in the cutter sets `Take = int(seed * 997) % 6` (sw_cut/build.py line 109), which never reaches take 6. Not mine to change.
- (Fixed 2026-11-11: `build.py` now ends with `Preview` off.) Was: `build.py` still leaves `Preview` on (scaffold default); it was turned off by hand before saving the tox.

Log, third pass (newest first):
- Final rebuild from `build.py`, then `take_0.png` to `take_6.png` and `take_<n>_a.png` (34 and 110 frames into each shot), sheets `takes_sheet.png` and `takes_pairs_sheet.png`. `hero.png` = `take_2.png`.
- `g3_sheet.png`: arrival sequences for aisle, macro, plan, transplant. Then fog 0.085 to 0.06 and darker, ceiling darker, tubes brighter, night grade rewritten twice (the first version multiplied the room up to white: `g1_sheet.png` rows 2 and 5).
- `g2_sheet.png`: aisle in three grades, 1-bit, void in two colours. Void model 0.36 to 0.46.
- `g1_sheet.png`: first look at all seven. Phrase atlas font 44 to 40 (one phrase was clipped: `f02_phr.png`), card type smaller (`f02_cards.png` touched the cell edges).
- `f01_rebuild_scaffold.png`: build.py run unchanged on the new scaffold: same look as `f00_before_sheet.png` (three captures of the old scene); `Take`/`Seed`/`Shotstart` and `shot` present.

## Technique
All in `build.py` (idempotent; `build(True)` also adds `dbg/sheet`, a contact sheet of the last 48 frames, which is how the hit-to-rot sequence was looked at in stills).

1. `src` (`shaders/src.frag`): the clean poster, never shown directly except on I-frames. Diagonal colour split, sliding stripes, drifting dots and a disc in the ident palette; the stack or one-line wordmark mask (1024x768) with a hard offset shadow; one of four library models (Render TOP 720x720, key + pink rim + blue fill + ambient) with an ink sticker shadow. Palette (7 sets), layout (3) and field angle change with `section`.
2. `small -> soft -> flow` (`shaders/flow.frag`): motion of the source between this frame and the last (`prev`, a Feedback TOP targeting `soft`), by windowed Lucas-Kanade over RGB at 320x180, blurred (`flowsoft`). The Optical Flow TOP was tried first and is not usable here (see traps).
3. `fb -> mosh` (`shaders/mosh.frag`): the loop. The previous output is copied from `uv - flow`, with the flow read once per macroblock and rounded to whole pixels (random rounding keeps the fraction), nearest filtering. So blocks are moved rigidly like codec motion vectors and nothing is resampled: colours stay the palette's, which is what keeps it from turning to mud. The source is let through only on I-frames.
4. `post` (`shaders/post.frag`): outside the loop. Channel drift and a mild corner falloff.
5. `cook_driver` (replaces the scaffold's text, same gate): each frame it compares `hits_low`, `hits_mid`, `section`, `beat_i` with the last frame and writes the I-frame decision to the `ctl` Constant CHOP.

## Channel -> visual
- `hits_low` step: I-frame. Strength (`hit_low`) above `Fullhit` (0.62): the whole clean poster for `Hold`+1 frames, after which the rot eases back in over `Ease` (0.13 s). Weaker: ragged clusters of 40 px blocks come back clean, roughly in proportion to the strength.
- `hits_mid` step: 30% of blocks come back clean; `hit_mid` envelope: macroblock size jumps 8 -> 16/32/64 px, so the smear breaks into big tiles for about 0.15 s.
- `section` step: the model (section % 4 of the four heroes), palette and layout change in the hidden source and a bloom starts (residual of the new picture over the old one); the full I-frame follows on the next beat.
- `beat_i` step with more than `Rotbeat` (0.3 s) of rot (passages with no kick): full I-frame on the beat. `Maxrot` (4 s) is a last resort.
- `energy`: flow gain (0.5 + 1.8*energy) and the strength of a slow swirl that makes flat fields creep. `hit_low` envelope: up to 2x gain on weak kicks (after a full I-frame the ease overrides it).
- `vocals`: above 0.25, columns streak (light grows up, dark drips down; the in-loop stand-in for pixel sort); above 0.15, red/blue split in `post`.
- `beat_pos`: model rotation, wordmark slide and tilt, field edge swing. `pulse`: wordmark, model and disc size kick (which itself makes a radial burst of flow). `evolve`: stripe and dot drift, swirl phase.

## Second pass (art direction, 2026-11-10): what changed
- **The rot has a shape in time.** `ctl['ease']` (driver) holds the flow gain near 0.08 for the first 0.03 s after a full I-frame and lets go over `Ease` (0.13 s); the old 2.5x gain jolt on the kick is gone. Before, the poster was torn within 2 frames of the hit and unreadable by 27 frames (`a02.png`, `a06.png`); now it reads for about a tenth of a second and is still decipherable at 0.58 s (`e02.png`, same track position as `a02.png`). All timing is in seconds (`age`, `Rotbeat`, `Maxrot`), and the ambient swirl is scaled by frame time (`dt60`), so the look depends less on frame rate. `Gain` default 1.3.
- **Section change is a P-frame bloom, not a cut.** On a section step no I-frame is sent. The model, palette and layout change in the hidden source; for the first 0.2 s the source's frame difference (`src - psrc`, the residual) is added to the old picture, so the new wordmark and model print themselves as embossed ghosts in the old poster's colours, carried by the new motion. The clean poster snaps in on the next beat (at least 0.12 s later, at most `Bloom` = 0.5 s). `Bloom` 0 gives the old clean cut. Sheets: `b03_bloom_sheet.png`, `c02_bloom_sheet.png`.
- **A better source.** Environment Light with a GLSL map (`shaders/env.frag`), a rim light on every PBR MAT, one hero metallic with a gold base colour, another as lacquer (per-model looks; since 2026-11-11 the third item of a `HEROES` row). Models about 20% larger. Stripes are a pure second colour `D` per palette instead of a 55% mix (which read as mauve mud). The wordmark fits the frame in all three layouts, including the "!". Masks loaded at 1280x960.
- Partial refreshes (weak kick, snare) come back as ragged clusters of 40 px blocks, not a grid of 80 px squares. The vocal red/blue split has a 1.5 px base offset instead of 5. `Fullhit` 0.62. The scene starts with an I-frame when it is cut to (a gap of more than 0.25 s since its last cooked frame).
- `ctl` channels added: `age`, `ease`, `dt60`, `bloom` (0.5 on the cut frame, then 1), `resid`. `mosh` is now a GLSL Multi TOP (4 inputs).

## Log (newest first)
- 2026-11-10, second pass, final rebuild from `build.py` (no debug sheet): `e01_rebuild.png` (hit_low 1.09, age 0: clean poster, third hero, the full wordmark), `e02.png` = `hero.png` (t 208, age 0.58, vocals 0.17: first hero melting off a red disc, the wordmark torn but legible on orange/yellow stripes), `e03.png` (late in a bloom, 0.85 s since the last I-frame: molten gold hero, fully abstract, the most rotted the scene gets), `e04.png` (vocals 0.87, age 0.13: centred layout, whole wordmark with streaks and fringe).
- `d01.png`: caught on a real snare (hit_mid 1.0, age 0.3): stripes and dots broken into large rectangular tiles, wordmark and model intact. `d02.png` (hit_low 0.88, age 0): clean fourth-hero poster. `d03.png` (age 0.07, vocals 0.35): first-hero poster, every edge dripping. `d04.png`, `d05.png`: gold hero, gold.
- Bloom, third try (`c02_bloom_sheet.png`): residual fades over 0.2 s, flow gain 0.7x during the bloom, ends on the next beat: old poster with the new model and wordmark ghosted over it, then the snap. Second try (`c01_bloom_sheet.png`): bloom up to 0.9 s at 1.3x gain was 30 frames of unreadable white/magenta mush. First try (`b03_bloom_sheet.png`, `b08_bloom_sheet.png`): constant residual 0.85 gave a good first 4 frames and rainbow noise after 8. Before any of that (`b01.png`): the flow on the cut frame itself compares two unrelated pictures and shattered the frame into camouflage in one frame; gain is now 0 on that frame.
- `b04.png` to `b07.png` (Ease 0.13, Gain 1.3, before the layout fixes): `b06.png` (age 0.27) model and wordmark readable and melting; `b04.png` (0.55) molten gold hero, half the wordmark; `b07.png` (0.85, kick-less passage) model and wordmark gone to strata, which is why `Rotbeat` went 0.5 -> 0.3.
- First look, nothing changed: `a01.png` to `a07.png`. Clean frame good (`a05.png`), but 13 frames after a hit already torn with a loud RGB fringe (`a01.png`), 27 frames after illegible (`a02.png`, `a06.png`); one hero a black hole; stripes mauve; the one-line mark cropped (no "!").
- First pass, below:
- 2026-11-10: final rebuild from `build.py`, looked at `captures/15_rebuild.png` (second hero, vocals 0.64: torn ivory wordmark with red/cyan fringes on red dots) and `16_final.png` (first hero, vocals 0.81, 31 frames after the last I-frame: ink wordmark dripping, yellow shadow pulled into streaks). Tox and snapshot written, Preview off.
- Snare now refreshes 30% of blocks, and the no-kick fallback moved from the bar line (after 45 frames) to the beat (after 30). Reason: `12.png` (72 frames of rot in a kick-less section, hit_mid 0.23, vocals 0.35) was palette-coloured but no longer readable as anything.
- `13.png` (vocals 0.72, 50 frames of rot): streak columns visible on the wordmark and disc, model in red still nameable. A yellow line at the left edge was `post` sampling outside the frame; clamped. `14.png` caught a partial I-frame (strength 0.49): clean 80 px blocks of stripes and dots beside rotted ones.
- `11.png` = `hero.png` (section 14, energy 0.49, vocals 0.05, 30 frames after an I-frame): hero model smeared mid-turn on a yellow disc, dots dragged into commas, wordmark melting at the bottom. The best frame.
- Vocal pass, third try (`08_sheet_streaks2.png`, `10.png`): streaks in both directions (light up, dark down) so neither tone eats the frame; drift moved to `post`. Second try (`07_streaks.png`): light-only streaks let an ivory field swallow an ink wordmark, and drift at 5x flow gave anaglyph triple images. First try (`06.png`): per-channel flow inside the loop plus an odd-even sort; within 30 frames it was rainbow noise with horizontal scan lines. In-loop channel separation accumulates and is the fastest route to mud.
- `09_block48_forced.png`: macroblock size forced to 48 to see it (the real hit_mid envelope is too short to catch by hand): big torn tiles, heavy.
- `04_sheet_blockcopy.png`, `05_rot_blur8.png`: whole-pixel block copy and a wider flow blur (4 -> 8). Before that (`02_mosh_first.png`, `03_sheet.png`) the loop sampled at sub-pixel offsets per pixel: scan-line striations, black creeping in from the edges (no clamp), wordmark shredded to noise in 2 s.
- `01_src.png`: source poster alone. First render had the model near black; key 1.6 -> 3.2, fill 0.7 -> 1.6, ambient 0.45 added.

## Checks
Second pass: `tdh.errors` empty. `tdh.check` run alone passed twice (cook_budget 8.08 ms on the first run after the rebuild, 0.81 ms later). Run in the same call right after a `tdh.capture` it failed once at 13.0 ms and, repeated in that same call, read 0.0: the failing reading coincides with the capture's readback. Own operators sum to about 0.7 ms (render 0.26, mosh 0.10, src 0.09, flow 0.07, post 0.06); masks and envmap cook once.

First pass:
`tdh.check` run four times: every check but `cook_budget` passed each time. `cook_budget` gave 0.149 pass, 29.1 fail, 0.98 pass, 13.4 fail. The fails coincide with calls that also captured or read pixels back and with other scenes loading; the scene's own operators sum to about 0.65 ms (render 0.22, src 0.09, mosh 0.09, flow 0.08, post 0.06). I did not get two clean passes in a row.

## Weak, unverified
Second pass:
- Late in a bloom that follows a long rot (`e03.png`) the frame is pure abstraction for up to half a second: colourful, not mud, but nothing is nameable until the snap.
- In passages with a strong kick every beat or faster, the picture never gets past light fraying (`d03`-`d05`): the deep melt only shows in sparser passages.
- The bloom was looked at in 320x180 and 640x360 contact-sheet tiles only, apart from one late frame (`e03.png`).
- The effect of `energy` on gain is still not isolated in a pair of captures. `dt60` scaling was not tested at a low frame rate.
- The wordmark art itself is stair-stepped (about 4 px steps in the PNG), so clean frames show jagged letter edges.
- (Fixed 2026-11-11: `build.py` now ends with `Preview` off.) Was: `build.py` still leaves `Preview` on; it was turned off by hand before the tox was saved.

First pass (frame-rate dependence, the unseen snare jump, the missing full-size I-frame, the loud split, the black model, the beige model and the square blocks are addressed above):
- The whole effect is per frame, so it depends on frame rate. TouchDesigner dropped to about 1 fps for some seconds during the build (shared machine); at that rate there is almost no rot between hits.
- The macroblock jump on `hit_mid` was only seen forced, not caught on a real snare. The effect of `energy` on gain was not isolated in a pair of captures.
- A clean full I-frame appears in the contact sheets and as `src`, not as a full-size capture of `out1`.
- The vocal red/blue split is loud and a little cheap next to the rest; one hero is a black shape with little modelling; the one meant to be gold is beige (no environment map).
- 80 px refresh blocks are plain squares.

## Next
- Done in the second pass: timing in seconds, residual (as the section bloom), environment map, clustered refresh blocks.
- Let `energy` raise `Fullhit` so loud passages keep more rot between kicks.
- A different wordmark phrase per section (a pack may hold more lettering art).
- (Fixed 2026-11-11: `build.py` now ends with `Preview` off.) Was: `build.py` leaves `Preview` on (scaffold default); it was turned off by hand before saving the tox.

## Traps found (2026-11-10, TouchDesigner 2025.33230)
- The plain GLSL TOP has 3 input connectors: `connect(dst.inputConnectors[3])` raises IndexError and the append form `connect(dst)` silently replaces input 0. Use a GLSL Multi TOP (`td.glslmultiTOP`, same parameters) for 4 or more inputs.
- Optical flow across a hard cut is noise at full clamp length: mute the flow on the cut frame.
- A residual (`src - previous src`) added inside the loop every frame turns to rainbow noise in about 8 frames; fade it out within 0.2 s.
- `tdh.check` in the same call as `tdh.capture` read 13 ms cook_budget here; run it in its own call.
- To look at an event in stills: an Execute DAT that sets the debug Cache TOP's `active` off a few frames after the event (`dbg/freeze` in `build(True)`; arm with `op('dbg').store('arm', 'bloom')`, release with `'go'`).
- Environment Light `envlightmap` takes a 2D equirect TOP; with it PBR `metallic` 1 renders as metal instead of black.
- Optical Flow TOP exists but errors on this machine: "The GPU or driver is reporting that Optical Flow is not supported", and passes its input through unchanged. Compute flow in GLSL.
- `layout` is a reserved word in GLSL: a variable of that name gives "unexpected LAYOUT".
- A Feedback TOP whose target is its own input gives that input's previous frame (used for `prev`).
- Layout TOP `align = 'gridrows'` with `numcols`/`numrows` makes a contact sheet; Cache Select TOP's parameter is `cachetop`, index 0 newest, negative older.
- A GLSL TOP created from Python brings docked `<name>_pixel`, `_info`, `_compute` DATs with it.
