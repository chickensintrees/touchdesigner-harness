# sc_exploded_view: exploded technical drawing

Built 2026-11-10 in TouchDesigner 2025.33230. Rebuild: run `build.py` (see `sw_hub/SCENE_BRIEF.md`).
Development helpers (rebuild, set a shot, capture every take, timed bursts): `dev.py`. Contact sheets: `sheet.py`.
The parts file: `prep_parts.py`.

## Intent

Engineering-drawing views of the asset pack's objects, drawn as line art and never as shaded surfaces.
The models are rendered to a normal/depth/part-id buffer and a GLSL pass extracts outline and
crease lines from the discontinuities, on blueprint blue, drafting-film cream, or black with one ink.

The objects come apart. One of them (the parts object: with the pack that ships, a lunar lander) is a
file of separate shapes: on the bar line the parts fly out into an exploded view and then re-seat one at
a time in landing order through the bar, like a typed sentence. The other models are sliced into slabs
along an axis; the slabs separate and close with the kicks and the cut faces are hatched. Around the
parts sit dimension lines whose numbers are live, leaders, catalogue numbers, a title block and a
rubber stamp.

Each visit is a different sheet. What it must do for a viewer: the explosion amount visibly snaps with
the kick, parts land through the bar, the object changes with the section, something is always turning.

## Words and models (2026-11-11)

Everything the sheets say and every model they draw is one dict, `DEFAULTS` at the top of `build.py`:
`MODELS` (name, size, triangles, drawing title, catalogue number, plain name), `POOLS` and `INPUT_POOLS`
(which models each take may draw), `CAP_INSIDE`, `PARTS` (the parts file and how takes 0, 2 and 7 frame
it), `PHRASES`, `STAMPS`, `TITLE`, `PARTS_LABELS`, `PARTS_WORDS` and `LABELS`. `build()` reads it through
`LIB['scene_words']`, so a pack's `scenes/sc_exploded_view/words.json` replaces any of those names, and
writes the result into the Text DAT `words`; `logic.setup` reads that DAT (again whenever its text
changes, so a value can be tried live). The defaults are generic: the pack's sixteen objects, catalogue
wording, phrases about real-time picture-making.

| # | Model | Used by takes |
|---|-------|---------------|
| 0 | the parts file (lander, 63 parts) | 0, 2, 7 |
| 1-15 | gramophone, space_helmet, skeleton_key, astrolabe, hourglass, ribbon_loop, balanced_solids, wire_cage, amphora, marble_bust, broken_column, rubber_duck, crystal_cluster, traffic_cone, pierced_stone | 1, 3, 4, 5, 6, 8, 9 by pool |

The parts file (`meshes/parts.obj`, `parts.json`) is made by `prep_parts.py` from one pack model: the
surface is split into its connected shapes and any shape with more than its share of triangles is cut
again into chunks of neighbouring triangles (k-means on triangle centres, then the borders straightened),
so every triangle is the model's own. Each part's centre and landing order ride in the normal slot (the
format is at the top of `prep_parts.py`). Tried before choosing the lander (`captures/g3A.png`): the
hourglass (23 real shapes plus chunks: reads as an assembly but is a thin column in a wide frame) and the
amphora (48 shards: the cleanest breaks, but one narrow pot). The lander fills the frame and has legs,
dishes and nozzles that read as parts. A pack may bring its own parts file: `PARTS['obj']` and
`PARTS['info']` are looked up with `mod.paths.scene_file`, and a flat bed of parts with no heights in
its .json gives them in `PARTS['bed']`.

The pack's models (all but the helmet) are thin double-walled shells, not solids: signed volume about
0.005 of a unit cube, half the surface facing inward (measured 2026-11-11). Through a cut the camera
sees the far inner skin, which faces it, so the back-face test that caps a solid finds only the thin
rim. For the models named in `CAP_INSIDE` the pixel shader also counts a front face that looks back at
the slab's own centre line as the cut (`shaders/part_pixel.glsl`). That is right for convex shapes and
wrong for pierced or hollowed ones (`captures/g8A.png`, second tile: the pierced stone's holes hatched),
which are left out and show their cuts as rims.

## Technique

- `logic.py` is the whole brain, run once per frame from three Script CHOPs and four Script DATs
  (`ctl`, `views`, `lines`, `lab_*`). It holds `TAKES` and the palettes, takes the words and models from
  the Text DAT `words`, and returns the frame's scalars, one transform per view, the annotation segments and the lettering.
- `part_mat` (GLSL MAT, `shaders/part_vertex.glsl`, `part_pixel.glsl`) places every part. Geometry
  instancing is `views x slabs`; each instance picks its view transform from a uniform array, and in
  slab mode discards everything outside its slab's range along the axis. Back faces seen through the
  cut are pushed onto the cut plane and flagged, which gives a capped, hatchable cut face with no
  extra geometry. The camera is orthographic and fixed (2 units high), so Python can project any
  object point to pixels and hang dimension lines and leaders on the real parts.
- The parts object is `meshes/parts.obj`, written by `prep_parts.py`: one pack model cut into separate
  shapes, each vertex carrying its part's centre and landing-order index.
- `gbuffer` (Render TOP, three 32-bit colour buffers, 4x AA): world normal + camera depth; part id /
  cut flag / landing glow / coverage; and the Input picture as it sits on the parts (black when unused).
- `draw` (`shaders/draw.frag`): outline from coverage, id, cut-flag and depth-curvature steps; thinner
  crease lines from normal steps; hatching and tint on cut faces; paper (five grounds); up to 40
  annotation segments (plain, dimension with arrowheads, dashed, leader, box, circle) from a CHOP
  uniform array; lettering from four Text TOPs fed by `specdat` tables.
- `final`: a quarter-size blur added back as a halo on the dark sheets only.

Measured cost with the scene cooking: 1.7 to 2.2 ms (`tdh.check` cook_budget, second run), of which
`gbuffer` is 0.3 to 0.85 ms GPU depending on the take (1.44 M triangles in the three-view of a 60k model).

## Takes (`TAKES` in logic.py, `Take % 10`)

| # | Name | What you see |
|---|------|--------------|
| 0 | iso_keys | Blueprint blue, white line. The parts object in isometric, parts exploding and landing again; live width dimension, leader to the part that is landing, title block, the phrase typed along the top. Seed flips the side. |
| 1 | three_view | Cream film, dark ink, red second ink. Front, plan and side elevations left; exploded isometric of the sliced part right with hatched cut faces; title block. |
| 2 | macro_keys | Black, amber ink with halo, no lettering at all. Perspective camera close in among the parts; they lift and land, the landing part lit solid. |
| 3 | contour_scan | Yellow, black ink, red second ink. No drawing of edges: one huge cropped part drawn only as the rings where cutting planes meet its surface. The kick sets the ring count (18 to 78), a red band scans the part once a bar, big red plane count. Seed picks the ring axis (long axis or vertical) and the side. |
| 4 | parts_sheet | Green dot-grid paper, cross-hatched tone. Twelve small views of one part in a turntable grid, cells opening and closing with the beat, balloon numbers. |
| 5 | section_sweep | Deep red, ivory line, black hatch, body tinted lighter than the ground. One huge part with its near end cut away; the cut plane jumps on each kick. "SECTION A-A" set large in a corner. |
| 6 | rosette | Ink navy, parts as solid pink shapes with navy lines cut out of them, yellow cut faces. Twelve copies of one sliced part on a wheel, off-centre and cropped by the frame; the wheel clicks one station per beat and the spokes burst outward with the kick. |
| 7 | plan_typed | Pink ruled slip, navy ink. The parts object square on, filling the frame (from the front for the lander; from above for a flat bed of parts), parts scattered and set back over two bars, phrase in large type along the bottom. |
| 8 | slab_strip | Carpet grey, white line, yellow hatch. One part cut into up to 14 slabs laid out across the frame, numbered, one long dimension. |
| 9 | bill_of_materials | Black, green phosphor. Parts list as the picture, a huge live number, a tall exploded stack at one side with leaders. |

Captures of all ten after the final rebuild: `captures/take_0.png` ... `take_9.png`, sheet `captures/takes_sheet.png`.
Seed changes: which side the composition sits on (0, 3, 5, 6, 9), which model (section + seed), which phrase,
tumble phase, the ring axis (3), the parts object turned end for end (7), stamp wording.

## Describe (the scene's `Describe` toggle, added 2026-11-11)

With Describe on, every word on the sheet says what the viewer is looking at; with it off nothing changes.
The words are in `WORDS`, `TITLE_D` and `STAMPS_D` at the top of `logic.py`, one entry per take; the lines
that name the parts object (`PARTS_WORDS`) and each model's plain name (`MODELS`) are in `build.py`. All
are mirrored into `preset.json` (`words`). The lettering is rebuilt from Python every frame, so the toggle
swaps the words on the next frame with nothing baked and no rebuild. Captures: `describe_take_0..9.png`,
sheet `describe_sheet.png`; other side of each layout and the stamps: `f_sheet_0..2.png`.

| # | What Describe shows |
|---|---------------------|
| 0 | Typed along the top, one of four sentences ("THE BAR SETS THE PARTS BACK IN."); leader "PART 61 OF 63 LANDING"; dimension "SPREAD X 1.00"; title block "EXPLODED VIEW   LINE ART TRACED FROM A 3D MODEL / MODEL: LANDER / 29095 TRIANGLES / SONG SECTION 19 OF 43 / BAR 053 / BEAT 4"; stamp "ON THE SNARE". |
| 1 | "FRONT VIEW", "TOP VIEW", "SIDE VIEW"; "EXPLODED VIEW: SLICED IN 6, THE KICK SETS THE GAP" / "A SHADER CAPS AND HATCHES THE CUT FACES"; dimensions "BASS 0.01", "H 1.00", "EXPLODE 0.36"; the same title block and stamp. |
| 2 | The take has no lettering; Describe adds two lines bottom left in a cleared strip: "EXPLODED VIEW: 63 PARTS, EACH A SEPARATE SHAPE." / "A SHADER TRACES THE EDGES. THE BAR SETS THE PARTS BACK IN." |
| 3 | "NO OUTLINES. / ONLY THE RINGS WHERE / PLANES CUT THE SURFACE."; under the big live ring count "CUTTING PLANES, COUNT SET BY THE KICK"; scan label "PLANE 007". |
| 4 | Cell 12 "ONE MODEL, 12 ANGLES"; footer "CELLS OPEN AND CLOSE WITH THE BEAT.  PINK = OPEN.  THE SLICES ARE CUT IN THE SHADER, NOT IN THE MODEL."; the cell numbers and angles stay (they are true). |
| 5 | Large "SECTION CUT"; "EACH KICK MOVES THE CUT PLANE.  NOW AT 35% OF THE LENGTH"; leader "HATCHED CUT FACE". |
| 6 | "WHEEL STEP 07 OF 12" / "ONE CLICK PER BEAT" / "THE KICK WIDENS THE WHEEL" / "12 COPIES OF ONE SPACE HELMET". |
| 7 | Typed large along the bottom, one of three sentences ("HI-HATS POP PARTS OUT OF PLACE."); "FRONT VIEW.  63 PARTS SCATTER, THEN LAND FROM THE GROUND UP"; "NOTE ONSETS 00732". |
| 8 | "BROKEN COLUMN CUT INTO 14 SLABS.  THE KICK SETS THE SPACING."; "BAR 056"; dimension "EXPLODE 0.60"; stamp. |
| 9 | The list becomes eight facts ("RENDER: NORMAL, DEPTH, PART ID", "SHADER: A JUMP IN ANY IS A LINE", "NO LIGHTS: ONLY EDGES AND HATCHING", "SLABS ARE CUT IN THE SHADER", "CUT FACES GET CAPPED AND HATCHED", "KICK: SETS THE GAP, NOW 0.13", "BEAT: THICKENS THE OUTLINE", "NEW SONG SECTION: NEW MODEL"); the big number is the bass level times 100, labelled "BASS LEVEL X 100, LIVE"; leaders "SLAB 01". |

## Input (the scene's `Input` parameter, added 2026-11-11)

`insel` (Select TOP) reads the TOP named by `Input`; `logic.input_path` returns nothing for a blank,
missing or non-TOP path and for any TOP inside this scene (a cook loop), and then `insel` shows a 16 px
black constant and the three uniforms `pic`, `sheet`, `knock` in `ctl` are 0, which leaves every shader
path as it was. A take uses the picture in one of two ways (`inp=` in its settings):

- `parts` (takes 1, 3, 5, 7): the picture is wrapped round the parts. `part_pixel.glsl` writes it to a
  third G-buffer (`gpic`): projected from the camera onto the part as it sat before it came apart, so each
  slab carries its strip away; on the parts object it is printed across the whole object, so each part
  carries its tile. `draw.frag` then draws it as hatching whose weight follows the tone (second ink for strong colour),
  as the weight of the contour rings on take 3, and as the cut-face hatching on take 5. These takes pick
  their part from `INPUT_POOLS` (broad-faced models only).
- `sheet` (takes 0, 2, 4, 6, 8, 9): the picture is drafted onto the paper behind the parts: edges traced
  as ink lines, tones as hatching that swells on the beat, strong colour as level lines in the second ink.
  The parts stay clean on top, and lettering clears a small halo of paper round itself (`knock`).

Captures with `/project1/sw_testcard/out1`: `input_take_0..9.png`, sheet `input_sheet.png`; with Describe as
well `m_take_big_0.png`, `m_take_big_1.png`, `n3_2.png`.

## Assets (added 2026-11-11)

No file in this folder names a folder on a machine. `build.py` finds the repository from `td.project.folder`
and every file parameter is an expression on `mod.paths` (`experiments/sw_hub/paths_module.py`).

| The scene uses | From | With no assets |
|---|---|---|
| The parts object (a lander cut into 63 parts) | `experiments/sc_exploded_view/meshes/parts.obj`, `parts.json` (committed, 1.6 MB; made by `prep_parts.py` from `<assets>/models/lander/model.obj`), or the pack's own `scenes/sc_exploded_view/meshes/...` when its words name one | The same: takes 0, 2 and 7 do not change. |
| Fifteen models (the table under "Words and models") | `<assets>/models/<name>/model.obj` (no textures are used) | TouchDesigner's teapot for every one. `build.py` reads the file `mod.paths.model_file` returns, adds a Transform POP `fit` that centres it and makes its longest side 1 unit, and lists its size and triangle count in the table `model_info`; `logic.use_standins` takes them from there and names the part TEAPOT, UTAH (TEAPOT in Describe). |
| Small lettering | `<assets>/fonts/BarlowCondensed-Bold.ttf` | The default face at 13 px in place of 17 px, so the title block still fits. |
| Large lettering | the fonts `mod.paths.font` gives for `chicago` (IBM Plex Mono in the pack that ships), `archivo` and `barlow` (by take) | The default face at the take's size. |

The fit and the table are made at build time, so after the assets folder appears or disappears the scene
must be rebuilt from `build.py`; the saved `.tox` is the with-assets build. Captures with an empty assets
folder: `captures/noassets_take_0..9.png`, sheet `captures/noassets_sheet.png`.

## Channel to visual

| Feed | Drives |
|------|--------|
| `hits_low` (count) | Each kick picks a new explosion level from a table; the amount moves there with a 0.07 s lag. Slab gaps, the strip length, the stack height, the dimension numbers, the ring count (take 3), the wheel radius (take 6) and the cut depth (take 5) all follow. |
| `hit_low` (envelope) | A small extra push on the explosion on top of the level. |
| `bar` / `bar_pos` | Landing cursor: at the bar line every part is out; they seat in landing order through 80% of the bar (takes 0, 2) or over two bars (take 7). A part is inked solid as it lands. The typed phrase grows with it. |
| `hit_high` | Pops a random handful of parts out of place. |
| `hits_mid` | Rubber stamp (`STAMPS`: DO NOT TOUCH, PLATE 07, LOOP...) lands for 0.3 s on each snare (takes 0, 1, 8). |
| `pulse` | Outline weight swells on the beat; halo breathes on the dark sheets. |
| `beat_i` | Title block BEAT field, highlighted row of the parts list, highlighted slab number, which cells are open on the parts sheet. |
| `bar_i` | REV number, BAR field, quantities in the parts list. |
| `bass` | The huge number on take 9; front-elevation dimension on take 1. |
| `section` | Swaps the part (pool per take), the phrase, the sheet number, the parts-list window. |
| `energy` | Slow zoom of every view (0.93 to 1.07). |
| `evolve` | Tumble and sway of the isometrics, turntable, hatch scroll, dashed-line crawl. |
| `shot.age` | First 0.4 s: the sheet is plotted left to right behind a moving line, and the explosion starts nearly closed and opens. |
| `section` change | The plotter draws the new sheet again (last three quarters of the wipe, 0.25 s). |
| `beat_i`, no kick for 1 s | Picks the explosion level instead of the kick, so a breakdown does not freeze the parts. Also the rosette's ratchet (one station per beat). |
| `bar` | Take 3: position of the red scan band and the PLANE readout. |

`pitch` is not used (it is non-zero only 7% of the track; a dimension that flickers reads as a bug).

## Log (newest first)

- 22 Review of 21, 2026-11-11 (second agent). `prep_parts.py` with no arguments now makes the committed
  file (its default was the hourglass; `lander --parts 60` reproduces `parts.obj` and `parts.json` byte
  for byte). Tox and snapshot saved again from the generic build; both packs captured again
  (`captures/rv_gen*.png`, `rv_priv*.png`). `tdh.check` on the generic pack: PASS at 3.5 ms once the
  meshes had loaded. Older log entries reworded so they name no object of the first pack. A pack's
  words.json must not repeat the `LABELS` defaults: tests/test_generic.py then reads them as private phrases.
- 21 Generic defaults, 2026-11-11. The words and models in the source are now generic (the asset pack's
  objects, catalogue wording, phrases about real-time pictures) and sit in `DEFAULTS` in `build.py`; the
  originals live in a private pack's `scenes/sc_exploded_view/words.json`, with that pack's parts file
  and its baker beside it, and that pack still draws what it drew. Checked two ways: offline, HEAD's
  `logic.py` and the new one fed that words file gave identical frames (views, lines, labels, uniforms)
  for 400 random feed states with Describe off and 400 with it on; in TouchDesigner, twenty captures on
  that pack before and after (`captures/ref_*.png`, `priv_*.png`). `logic.py` no longer holds any words
  or model names but the Describe sentences; `part_vertex.glsl` takes the part count, the height of the
  part centres and the picture plane from uniforms (`uParts`, `uPartsUV`) where it had the first parts file's
  numbers. On the generic pack every take was captured (`captures/gen_*.png`, Describe `desc_*.png`),
  each pool model by model (`g4*.png`, `g5*.png`, `g8*.png`). Dropped after looking: the skeleton key in
  the slab strip and parts sheet (slivers), the balanced solids and hourglass on the wheel (stations
  overlap), the pierced stone and broken column in the section sweep. First generic look of take 0 had
  the typed phrase running through the lander's flying parts on the mirrored layout; the lander sits
  lower now. `tdh.check`: 40.8 ms twice while captures and mesh loads were counted, then PASS at 2.88 ms.
Entries 20 to 01, and the weak points written before 2026-11-11, describe the scene on the pack it was
first built with: its parts object was a flat bed of 78 small parts on a base, set back row by row, there
were twelve models, and the baker was `prep_keys.py` (now in that pack).

- 20 Portable, 2026-11-11 (fifth agent). Paths only: no folder named in `build.py`, `logic.py`, `dev.py` or
  the baker; file parameters are `mod.paths` expressions; see "Assets". With assets all ten takes,
  Describe (takes 1, 8) and Input (takes 3, 4) compared with captures taken before the change
  (`ref_sheet.png` before, `final_sheet.png` and `final_di_sheet.png` after). With the scene's `Assets`
  parameter on an empty folder: `tdh.errors` empty, ten takes captured twice at different moments
  (`noassets_sheet.png`), Describe (`noassets_d_sheet.png`) and Input (`noassets_i_sheet.png`).
  First no-assets look had the default face at 17 px running out of the title block; now 13 px.
  A File In POP's `computeBounds()` returned zeros for the teapot in the calls after creating it, so the
  builder reads the OBJ's bounds as text.
  With the mesh files as expressions each mesh loaded a second time (25 to 50 ms) on the cut that first
  showed its part, which the forced cook in the builder used to prevent; a second forced cook 1.5 s after
  the build stops it (checked: every part shown, `totalCooks` of the meshes unchanged). Tried and
  dropped: the second cook four frames after the build (too soon), and switching every part on for a
  frame (did not load them). `tdh.check`: pending, 131 ms and 49 ms while those loads were counted, then
  PASS at 3.12 ms. `python -m pytest -q tests/test_portable.py -k sc_exploded_view`: 1 passed.
- 19 Describe and Input finished, 2026-11-11 (fourth agent; the third was cut off part-way with the words
  written and the parts-mode Input working but nothing recorded). Final clean rebuild, then all ten takes
  captured three ways in the same frames: plain (`take_*.png`, `takes_sheet.png`: unchanged from before,
  and `pic`, `sheet`, `knock` asserted 0 on every take), Describe (`describe_sheet.png`) and Input
  (`input_sheet.png`); the three side by side in `final_three_ways.png`. `tdh.errors` empty; `tdh.check`
  pending, then 39.9 ms (first sample after the rebuild), then PASS at 2.83 ms (it was 1.7 to 2.2 before the
  third G-buffer; other scenes were cooking). Tox and snapshot written with Preview off, Describe off,
  Input blank. The captures `d_*`, `i_*`, `i7_*`, `s1_*` are the third agent's and are not referred to.
- 18 Input on the sheet. With the picture only on the parts, six takes showed a few stripes of it or mush
  (`j_take_big_0..2.png`: the parts of take 0, the twelve small views, the wheel, the slab strip, the stack)
  and take 2 ignored it. Those takes now draft the picture onto the paper behind the parts
  (`k_take_big_0.png`, `k_take_big_1.png`). Tried and dropped: the picture on the part faces of take 2
  (`k_take_big_1.png`, second tile: solid yellow parts, nothing recognisable). The parts list (take 9) has
  the sheet at 0.38 so the list still reads.
- 17 Describe checked take by take at 1280x720, both sides of each layout (`e_take_*.png`, `f_sheet_*.png`).
  Two fixes: on take 3 the three lines moved 100 px clear of the ruler, because the scan label crossed them
  for an eighth of every bar (`describe_sheet.png` first version, `n3_0.png` after), and they clear the
  rings round themselves when a large part sits under them (`n3_2.png`).

- 16 Second pass (art direction), final clean rebuild: ten takes captured (`takes_sheet.png`), hero is
  take 3 (`hero.png`). `tdh.check` passes at 1.7 to 2.1 ms; it reads 30 ms on the first run after a
  rebuild or a tox save (the meshes did not recook: `cookAbsFrame` unchanged). The tox is saved with Preview off.
- 15 Take 2 (macro) was one cube on black for the first part of every bar at a loud moment (`n2_sheet.png`,
  third tile): the parts flew out of the frame. Lift 0.24 to 0.13, spread 0.5 to 0.12, scale 4 to 5.2, drift
  0.9 to 0.3. Six yaws checked in `q2_sheet.png`, one bar in `p2_sheet.png`: the frame stays full.
- 14 The explosion froze in a breakdown (`m3_sheet.png`: E 0.1 for six frames, no kick for seconds). The
  beat count now picks the level when there has been no kick for a second.
- 13 New take 6, rosette (`m6_sheet.png` arrival, `n2_sheet.png` second version). Solid fill is one
  number in draw.frag (`uStyle2.y`): the body takes the ink and the lines are drawn in the paper colour.
  First version was a small wheel in a big empty field (`k1_sheet.png`); now it is cropped by the frame.
- 12b New take 3, contour scan (`k1_sheet.png`, `h3_sheet.png`). The G-buffer's third data slot carries
  the position along the part's axis (the parts object still uses it for the landing glow); draw.frag inks
  `fract(along * N)` at a constant pixel width using `fwidth`.
- 12a Seen first (`j1_sheet.png`, `j2_sheet.png`, the builder's eight takes at two moments): all eight
  differ in ground colour and layout, but all are the same thin outline on a flat field, several have a
  small subject in a large empty sheet (takes 4 and 6), the parts sheet's tall parts ran
  into the row below, and the macro take was half black. Fixes: section sweep fitted to the cross-section
  and tinted, parts sheet fitted to its exploded length, two thin-stemmed models out of the strip pool,
  cross-hatch on the darkest faces.

- 12 Final clean rebuild, all eight takes captured and compared (`takes_sheet.png`); `tdh.check` PASS on
  the third run (first pending, second 33 ms right after the rebuild, third 2.16 ms); tox and snapshot
  written; hero is `moment_0.png`. Preview off.
- 11 Added the halo pass for the dark sheets (`final`). Take 2 and 7 gained depth; 0.3 on blueprint.
- 10 Take 4 rebuilt: it was two halves sliding apart with a small cut visible (`f_sheet.png`). Now the
  near half is simply not drawn and the kick moves the cut plane, so the hatched face fills the part
  (`g_sweep_sheet.png`, then a hollow vessel in `takes_sheet.png`, which shows its wall thickness). Two
  thin-stemmed models left that pool: a thin stem gives a dot of hatch (`h_take_4.png`).
- 09 Burst of take 1 from age 0 (`e_three_sheet.png`): plotter wipe at 0, 0.08, 0.28 s; explosion opening
  0.11 to 0.5; stamps on the snares.
- 08 Take 2 was the parts object seen edge-on at the top of a black frame (`d_macro_sheet.png` first version):
  at scale 5 and 33 degrees of tilt the plane passed behind the camera. Scale 4, camera at 1.7, pitch
  near plan; the base is removed in this take because it filled half the frame with a black panel.
- 07 Take 5 seed above 0.66 showed an empty base (`b_sheet.png`): I flipped the parts object with roll, which
  in plan view turns it face down. The flip is a yaw.
- 06 All eight takes first seen together (`a_sheet.png`). Fixes after it: three-view isometric fitted to
  its exploded length, strip labels follow the projected slabs, explosion levels raised.
- 05 Slab mode first look (`05_three.png`): hatched caps worked first time.
- 04 Parts exploding and landing (`03_keys.png`, `04_keys_b.png`).
- 03 The base was part 37 in the landing order and flew about with the parts; the baker now marks the
  largest shape as the base.
- 02 Nothing drew (`01_first.png`: annotations only). A GLSL MAT on a POP draws nothing once the vertex
  shader reads `uv[0]`, or a custom attribute declared on the Attributes page (vertex class or converted
  to point class), although it compiles; the only sign is a warning on the Render TOP. `TDNormal()`
  arrives unnormalised, so the part data rides in the normal slot and the parts object's normals come from
  `dFdx/dFdy` in the pixel shader. Also `TDCameraIndex()` does not exist in the pixel shader.
- 01 Scaffold, logic module, annotation layer.

## Weak points (honest)

- I have only seen stills and bursts 0.2 to 0.4 s apart, never the scene in motion. The 0.07 s lag on the
  explosion and the 0.3 s stamp are judged from numbers and stills.
- The kick is on most beats, so the explosion level changes about twice a second; in a busy passage it
  may read as jitter rather than a snap. `LEVELS` and the lag in `logic.py` are the two knobs.
- Take 4 (parts sheet): each part is cut into at most 4 slabs and the cells are small, so
  the open and closed states differ less than I wanted. Take 8 (slab strip) varies by model: a hollow box is a row of
  frames (good); thin-stemmed models are heaps of slivers and are kept out of its pool.
- Lines are extracted in screen space at one radius, so line weight is the same near and far and thin
  parts (stems, cords, wires) get blobby. The library meshes are shells with some stray interior
  faces, so a few short ticks appear inside flat faces (visible on a boxy model's side elevation).
- Lettering is Barlow Condensed and a display or mono face, not a real drafting hand. Label widths are estimated from
  character counts, so right-aligned text can sit a few pixels off.
- Generic pack (2026-11-11): seen only as stills. The lander's parts are chunks of one skin, so their
  borders are ragged where a chunk boundary crosses fine detail; in the close-up (take 2) they read as
  torn foil more than as machined parts. Cut faces are hatched in full only on the models in
  `CAP_INSIDE` and the helmet; the others show a hatched rim. In the section sweep a model cut across
  its height shows the inner floor unhatched. On the mirrored blueprint layout the stamp can sit on the
  end of the dimension line. SHEET and SONG SECTION still count "OF 43" whatever the track.

- Second pass: still never seen in continuous motion. The rosette's solid parts have ragged navy marks
  where crease lines are cut out of the pink (worst on finely detailed models), and at the lowest explosion level
  neighbouring stations touch. The contour take's rings break up where the surface is nearly flat to the
  axis (the top of a rounded head). Takes 0, 1, 4 and 8 are still thin line on a flat field: at thumbnail
  size they differ by ground colour and layout more than by drawing technique.
- The section-change re-plot hides part of the sheet for a quarter of a second; if the cutter also cuts on
  sections it will rarely be seen.

- Describe and Input (2026-11-11): seen only as stills. Describe: on take 1 the side-view height label
  ("H 0.42") sits on the drawing, as the number it replaces did, and "BASS 0.01" on a width dimension is
  true but odd; on take 5 the leader "HATCHED CUT FACE" points at the middle of the cut, which on a hollow
  part is not hatched; the small labels are 17 px Barlow, readable at 1280x720 but not at
  thumbnail size. Input: take 7 is a mosaic on the separate parts: large shapes survive, words in
  the picture do not, and it is stretched to the parts object's own proportions. Take 3 on a rounded figure shows tone
  but not shapes; on broad-faced models it is the best of the ten. The sheet takes show the picture
  whole but flat: it does not come apart with the parts, the parts only cover it. A dark, low-contrast
  input gives little on light paper with dark ink beyond its traced edges. The Select TOP pulls the other
  scene's output, so that scene cooks while this one is on.

- No assets (2026-11-11): every part that is not the parts object is the same teapot, so a new song section
  no longer brings a new object on seven of the ten takes, and the parts list (take 9) is seven rows of
  TEAPOT, UTAH. The default face is plainer and wider than the real ones: in the title block SHEET and REV
  nearly touch, and the big headings lose their display face.

## Next

- Hidden lines dashed (render back faces to a third buffer), and line weight by depth.
- A catalogue take showing every model at once, each in its own cell.
- Hold the explosion level for a bar on some takes so the snap is rarer and bigger.
