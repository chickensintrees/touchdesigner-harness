# sc_shatter: Shatter and reassemble

## Intent
Solid things breaking and un-breaking in time with the music. A library model or an
extruded phrase is cut into rigid shards (small chips, Voronoi cells, a few big pieces, or
horizontal slabs). On the bar line it is whole for an instant; the downbeat bursts it outward with
spin, it hangs as a lit cloud of shards showing gold, red, blue or ink insides, then it is pulled
back and locks together exactly on a bar or beat line, like footage run backwards. It works when
the shards read as solid, lit pieces of a recognisable thing, when the reassembly lands on the
line, and when each return of the scene (take) is a different picture.

## Technique (as built)
- **Bake** (`bake.py`, pure numpy, about 0.5 to 3 s per subject; run in system Python or, when a
  cache file is missing or was baked from something else, inside TouchDesigner by `build.py`). Each subject (library OBJ, or a Text
  POP's triangles dumped once to `cache/raw_<name>.npy`) becomes a float atlas
  `cache/<name>.npy`, 1280 wide: one texel per triangle corner for position + fine cell id,
  normal + micro cell id, uv + kind + slab height, then small tables of cell pivots.
  - Low-poly sources are subdivided (longest-edge bisection) and heavy ones decimated (vertex
    clustering) to a budget.
  - Fine cells are true Voronoi regions of seed points on the surface, and **every triangle that
    straddles two cells is cut on the bisector plane**, so fracture lines are straight. The same
    cut is made on horizontal planes every 0.1 units for the slab mode.
  - Micro cells nest inside fine cells; coarse cells are unions of fine cells (farthest-point
    seeds), so one set of walls serves all three levels.
  - Thickness: an inset copy of the skin (the lining) plus wall quads along every fine-cell border.
    Lining and walls are flagged so the shader can colour them (gold, red, blue, ink).
- **Draw**: one generic triangle soup (a Grid POP, triangles, Facet unique) per size: `big`
  176,000 triangles for single objects, `small` 14,400 for instanced grids. A GLSL MAT vertex
  shader (`shaders/shard.vert`) ignores the grid, reads corner `gl_VertexIndex` from the atlas and
  applies the cell's rigid motion: pivot + rotation about a random axis + travel along the
  outward direction, all functions of one burst value, so the motion reverses exactly.
- **Timing** is stateless: phase = bar_pos / cycle length, per-cell and per-instance staggered
  (random, from an impact point, reading order, top first; instance wave across a grid).
- **Light** (`shaders/shard.frag`): key lamp with GGX highlight, a procedural studio reflection
  (overhead softbox, side strip), ambient; no light COMPs.
- **Shadows**: the same geometry is drawn a second time by an orthographic camera looking straight
  down; the vertex shader recognises that pass (`proj[3][3] == 1`) and flattens every shard onto
  the floor along the light direction. Blurred, then read by the backdrop shader in world space.
- **Reflection**: odd instances are the mirror image below the floor, drawn premultiplied.
- **Backdrop** (`shaders/comp.frag`): ray-plane floor with a pool of light, optional tile or ruled
  pattern, seamless wall. **Post** (`shaders/post.frag`): glow, filmic curve, or 1-bit Bayer dither.

## Takes (`TAKES` in build.py; `Take % 10`)
| n | name | picture |
|---|------|---------|
| 0 | porcelain | one statuette (marble bust, amphora, pierced stone) mid close, dark blue room; a few big pieces drift apart from an impact point and close on every bar line, gold lining glows |
| 1 | mat | forty rubber ducks, or forty amphorae lying on their sides, on a green cutting mat seen from straight above; a detonation wave crosses the grid, hard shadows, red lining |
| 2 | knoll | knolling, not an explosion: one object (gramophone, space helmet, lander, astrolabe, hourglass, traffic cone) takes itself apart into a full-frame tidy grid of its own 260 pieces, each lying skin up and scaled to its slot, on ink blue with hard shadows; the grid fills row by row and flies home |
| 3 | murmur | a sentence as thousands of white chips on black, 1-bit dithered; the flock rides a flow field and locks in left to right, whole for one bar |
| 4 | chorus | a receding line of seven gilded busts on brick red with floor reflections; they crack open one after another down the line, plaster-white insides |
| 5 | slabs | broken column, stack of painted solids, traffic cone or hourglass sliced into horizontal slabs that slide apart, top first; flat ident yellow, blue lining, long lens, subject left of centre |
| 6 | glass | the object (amphora, hourglass, space helmet, crystal cluster, pierced stone) as a ghost of green glass in the dark, drawn additively without depth: only rims, glints and overlaps show; shards drift apart and back |
| 7 | collapse | a red phrase (DO NOT / TOUCH, HERE. / NOW., FOUND, / NOT MADE.) seen low and close from one end falls top first into red and ink blocks on cream, then un-falls |
| 8 | cloud | camera inside a slow (4 bar) burst of chunky shards of a lander, gramophone, crystal cluster or space helmet; black room, red lining, wide lens |
| 9 | onebit | one lit object and its shadow on white paper, dithered to pure black and white, moving in twelve steps per cycle like stop motion |

The subjects named in this table are the defaults (`WORDS` in build.py, the generic pack); a pack
with its own `scenes/sc_shatter/words.json` shows its own. `Seed` changes the subject (with
`section`), the camera azimuth, the impact point and every shard's direction. Captures:
`captures/g8_sheet_a.png`, `_b`, `_c` (every take with every subject, whole and burst).

## Channel to visual
| Feed | Drives |
|------|--------|
| `bar_pos` | the burst phase: out on the line, back on a line (cycle 1, 2 or 4 bars per take) |
| `hit_low` | kick jolt: cracks open for a moment even while whole; lining flashes; exposure +10% |
| `hit_high` | the softbox reflection flares (crisp speculars on hats) |
| `pulse` | pool of light on the floor breathes, camera dollies 2.5% (plus 3% on `hit_low`) |
| `energy` | burst distance (72% to 122% of the take's power) |
| `vocals` | lining glow (up to 2.2x) |
| `section` | subject swap (with the shot seed); `section_pos` under 0.07 replays the arrival burst at 75%, so the new subject closes in from shards |
| `evolve` | camera swing and orbit, flow field of the murmuration |
| `shot.age` | arrival: a burst that closes in the first half second, with a dolly-in |
| `shot.take`, `shot.seed` | which picture, and its variation |

## Describe mode and Input (2026-11-11)
Both are parameters the scaffold adds. With Describe off and Input blank every expression takes
its old branch, so the takes are as before (`off_sheet.png` against `takes_sheet.png`).

**Describe** (`TAKES[n]['label']`, `['describe']`, `['label_in']` in build.py; mirrored to
preset.json as `words`). Two things change, with no rebuild:
- Every take gets a two-line caption on a dark plate, bottom left (Barlow Condensed Bold 27 px):
  line one names what is on screen, line two says how it moves and what the music does. The
  twenty strips (ten for the take's own subject, ten for the take shattering an Input picture) are
  Text TOPs drawn once at build time; a Switch TOP hands `post.frag` the right one, or a 16 px
  blank while Describe is off. On the two 1-bit takes the caption is pure white on black.
- The two text takes swap the pack's phrases for baked phrases about the technique (seven more
  atlases, `x_*` in bake.py): murmur shows ONE MESH CUT / INTO CHIPS., CHIPS FLOCK, / THEN LOCK
  IN., WHOLE AGAIN / EVERY 2 BARS., NO SIMULATION. / ONE FORMULA.; collapse shows CUT INTO /
  BLOCKS, FALL. / UN-FALL., SHATTER / IN REVERSE. All atlases load at build time, so the toggle
  only moves a switch index (checked: no `label*` or `atlas_*` operator cooked on the toggle).

**Input** (`TAKES[n]['input']`, `inscale`, `inyaw`). The picture enters as the thing that gets
shattered: four more subjects, `panel*` in bake.py, are 16:9 slabs whose two faces carry the TOP
named by `Input` (a Select TOP, `input_pic`, wired into the texture switch; it is only read while
Input is usable). Each take names the slab it uses, so all ten takes accept a picture:
porcelain, slabs, collapse, cloud and onebit the upright slab; knoll a slab lying face up; mat
forty small face-up slabs; chorus seven gilded ones turned side-on in a fanned row; murmur the
slab as chips carrying the picture's brightness into the 1-bit dither; glass the picture glowing
additively on whichever face of each shard is turned to the camera. Input is ignored (the scene
runs as if blank) when the path is empty, missing, not a TOP, or inside this scene. While a
picture is in, the camera keeps to the slab's front (no orbit, swing and seed range capped) and
the take's tint is not applied to it.


- Custom parameters for inspection: `Manual` + `Phase` freeze the burst phase, `Subject` forces a
  subject index (-1 = automatic). Leave Manual off and Subject at -1.
- Output TOP: `out1`, 1280x720.
- `cache/` (about 450 MB of baked atlases, plus about 320 MB in `cache/noassets/` once the
  stand-ins have been baked) is git-ignored and regenerated by `build.py` or `python bake.py all`.

## Assets (2026-11-11)
Nothing here names a folder. `build.py` takes the repository from `td.project.folder`; every file
parameter is an expression on `mod.paths`; the atlas loader reads
`mod.paths.here(<file relative to this folder>)` from the COMP's `atlas_files` storage; `bake.py`
run in a shell finds the repository from its own location. No data file is committed: everything
derived from a model or a font is baked again from whatever `mod.paths` returns.

| The scene uses | From | With that missing |
|---|---|---|
| 14 models: `marble_bust`, `amphora`, `pierced_stone`, `gramophone`, `space_helmet`, `lander`, `astrolabe`, `hourglass`, `traffic_cone`, `broken_column`, `balanced_solids`, `crystal_cluster`, `wire_cage`, `rubber_duck` (`model.obj`, baked into 16 fracture atlases; the rows are `WORDS['MODELS']` in build.py) | `<assets>/models/<slug>/model.obj` | TouchDesigner's bundled teapot, baked with the same subject settings into `cache/noassets/<subject>.npy`: 1.45 units long for the single-object subjects, 1 unit for the three marked `instanced` (`duck_s`, `amphora_s`, `bust_m`), subdivided so the cracks can be fine |
| their pictures (`tex_<subject>`, Movie File In) | `<assets>/models/<slug>/basecolor.png` | a 16 px Constant TOP of one flat colour per subject (`standin` in its `WORDS['MODELS']` row), so a section change still changes the picture |
| Archivo Black, for the 14 extruded phrases | `<assets>/fonts/ArchivoBlack-Regular.ttf` | the Text POP's default face; the phrase meshes are dumped and baked again into `cache/noassets/` (the bake rescales each phrase to its set width, and bakes coarser if a face passes the triangle budget) |
| Barlow Condensed Bold, for the Describe captions | `<assets>/fonts/BarlowCondensed-Bold.ttf` | the Text TOP's default face, with the font size reduced per caption until it fits the 1232 px strip (27 px down to 20 px here) |

The Input slabs (`panel*`) and all shaders need no assets. Each subject is decided on its own, so a
library with only some of the models gives teapots for the rest. The stand-in atlases live apart
from the real ones, so switching the `Assets` parameter and rebuilding never bakes over them.
Every atlas has a `<name>.sig` beside it that says what it was baked from (the subject's settings,
the model's folder name and file size, the font file); `build.py` reuses an atlas only when that
matches what the pack asks for now, so another pack, model or phrase under the same subject name
is baked again instead of shown stale.

On a clone with no cache, the first `build.py` run dumps 14 phrases and bakes 34 atlases inside
TouchDesigner (0.1 to 3 s each in system Python, so roughly a minute of blocked main thread,
once; estimated, not timed). To avoid the wait, build once so the COMP exists, run `dump_texts()` from
build.py, then
`python bake.py --noassets --teapot <TouchDesigner>/Samples/Geo/UtahTeapot.obj all` in a shell.

## Log
(newest first; files are in `captures/`)

- **23 Generic defaults** (2026-11-11). The defaults in the source are generic: models of the
  pack that ships with the repository, phrases about real-time pictures and a catalogue of
  unexplained objects. The originals live in a private pack's `scenes/sc_shatter/words.json`
  (same four names as `WORDS` in build.py: `MODELS`, `PHRASES`, `TAKES`, `LABELS`), so a build on
  that pack is as before: its 29 atlases were re-baked from that file in a shell and are
  byte-identical to the ones already in `cache/`.
  - Before, on the private pack: `ref_sheet_a.png`, `_b`, `_c` (ten takes; whole at seed 0.3,
    phase 0.3 at seed 0.3, whole at seed 0.7). After, same pack, same takes, seeds and subjects:
    `aft_sheet_a.png`, `_b`, `_c`: same subjects, words, palettes and framing (shard directions
    and the orbiting cameras of glass and cloud differ: they follow `evolve`).
  - Generic pack, first look (`g1_sheet_a.png`, `_b`): every model turned solid gold, red or blue
    as soon as it opened (`g3_bust_q15.png`). The pack's generated models are thin double walls:
    an outer sheet and, 0.002 units inside it, a second sheet facing the hollow (the bust is two
    closed components of +0.111 and -0.108 signed volume). The lining is the skin moved inward,
    so the second sheet's lining landed outside the object. `bake.py` now keeps only the outer
    sheet for rows marked `shell` (`_outer_skin`: a voxel flood fill says which side of a
    back-to-back pair is nearer the open air). Tried first and dropped: removing connected
    components of negative volume (the column and the crystals are one component, both sheets
    joined); a flood fill alone (vases, cones and horns are open, so their inside is outside too:
    `g6_sheet.png`, the amphora still gold). `g7_sheet.png`: all sixteen subjects open into
    pieces of themselves with the lining in the cracks. Rows without `shell` bake as before.
  - Mat: keys and traffic cones were thin lines and dots from above (`g1_sheet_a.png`); ducks and
    amphorae on their sides fill their cells (`g8_sheet_a.png`). Chorus: gilded ducks were lumps
    (`g1_sheet_a.png`); gilded busts read at once. Glass: 1 unit tall subjects touched the top
    of the frame, so the generic `TAKES` row pulls that camera back. Two phrases were narrowed
    after touching the frame edge at the ends of the seed's azimuth range (`g9_sheet_a.png`).
  - `build.py` stops with a list when a take's subject has more triangles than the soup that
    draws it (`_check_budgets`): the first small ducks and amphorae were over by a few hundred.
  - Generic pack: `g8_sheet_a.png`, `_b`, `_c` (every take, every subject, whole and burst),
    `g9_sheet_a.png` (Describe on four takes, phrases at both ends of the azimuth range),
    `g9_sheet_b.png` (all ten takes live). `tdh.errors` empty; `tdh.check`: run 1 FAIL (moving:
    stale sample from before the rebuild), run 2 FAIL on cook_budget only (29 ms, read seconds
    after a capture batch), run 3 PASS (moving delta 0.105, cook 1.72 ms). Tox, snapshot and
    `hero.png` (the gilded busts) are from the generic build. Left built on the private pack,
    Assets blank, Describe off, Input blank, Manual off, Subject -1, Preview off.

- **22 Portable** (2026-11-11). No picture change intended. Before: `pre_sheet.png` (ten takes at
  phase 0.3 with a fixed subject each, Describe on murmur, Input on slabs). After converting, on
  the real assets: `port_sheet.png`, same subjects, faces, textures and palettes (the shard
  directions and camera swing differ because they follow `evolve`). With the COMP's `Assets`
  parameter on an empty folder (`captures/_noassets`): `na_sheet.png`, rows 1 to 3 the same
  twelve states, row 4 live takes 0, 5, 8, 9 (q 0.83, 0.91, 0.57, 0.08 from `bar_pos`):
  teapots in every model take, phrases in the default face, captions fitted; `tdh.errors` empty.
  23 stand-in atlases were baked in a shell, one model and `x_rev` inside TouchDesigner by the
  rebuild, to prove that path. First stand-in bake had the teapot 1 unit long: 0.47 high, small
  and low in the single-object takes (first `na_sheet.png`), so those are baked at 1.45.
  Assets blanked and rebuilt: `back_sheet.png`, as `port_sheet.png`. Tox and snapshot saved from
  that rebuild; `python -m pytest -q tests/test_portable.py -k sc_shatter`: 1 passed (it failed
  with 12 hits before the conversion). `tdh.check`: run 1 pending, run 2 FAIL on cook_budget only
  (33 ms, read seconds after the capture batch), run 3 PASS (moving delta 0.164, cook 2.01 ms).
  Left with Assets blank, Describe off, Input blank, Manual off, Subject -1, Preview off.

- **21 Describe and Input, done list** (2026-11-11). Clean rebuild from `build.py`, then
  `describe_sheet.png` (every take live with Describe on, plus each baked phrase whole),
  `input_sheet.png` (every take with `/project1/sw_testcard/out1`), `off_sheet.png` (every take
  with both off, phase 0.3). `tdh.errors` empty. `tdh.check`: run 1 pending (first motion sample),
  run 2 FAIL on cook_budget only (29 ms, read seconds after a batch of take changes), run 3 PASS
  (moving delta 0.145, cook 2.06 ms, 19 active operators). Tox and snapshot saved; Describe off,
  Input blank, Preview off. `preset.json` has `words` per take, `accepts_input`, `as_processor`.
- **20 Input tuned.** `i1_sheet.png` first try (each take at phase 0.3 and 0.93): it worked at
  once on porcelain, mat, murmur and slabs. Fixed after looking: collapse tinted the picture red
  (the take's text tint; the picture now keeps its own colours); the face-up slabs on mat and
  knoll were washed pale because a flat slab mirrors the whole softbox (studio reflection on the
  picture cut to 10%, `i2_sheet.png`); chorus slabs were small and coplanar (now 1.5x, turned 90
  degrees so they fan out down the line); glass barely showed the picture (glow raised);
  `i3_sheet.png` showed glass and cloud edge-on as a sliver, because those takes pick any azimuth
  (camera now stays in front of the slab, `i4_sheet.png`); porcelain, collapse and onebit slabs
  rescaled to sit inside the frame.
- **19b Describe built.** `d1_sheet.png`: captions on all ten takes, legible at half size.
  `d2_sheet.png`: the baked phrases whole. SHATTER / IN REVERSE touched the top of the frame at
  width 3.2, rebaked at 2.8. Captions that claimed "a 3D model" were untrue with a picture in, so
  a second caption set (`label_in`) is shown when Describe and Input are both on (`i3_sheet.png`).
- **19a Start of the Describe / Input pass.** `git diff 08710bf` for this folder was empty and
  the live COMP had no Describe or Input parameter: the earlier attempt left nothing behind.
  Rebuilt from the unchanged `build.py` on the new scaffold: `base_sheet.png` matches
  `takes_sheet.png` in kind (different subjects and phases).

- **19 second pass, done list.** `tdh.errors` empty; `tdh.check` run 1 FAIL on cook_budget only
  (196 ms: atlas loads of the rebuild counted), run 2 PASS (moving delta 0.081, cook 1.88 ms, 19
  active ops). Quiet per-frame cost read one call after setting the take: chorus 1.66 ms, mat
  3.15 ms, glass 1.45 ms (CPU+GPU summed). Tox and snapshot saved, `hero.png` is the chorus.
  `take_6.png`, `take_7.png` and `hero.png` are from the last rebuild; the other take captures are
  from the rebuild before it (their settings did not change in between).
- **18 glass and collapse tuned.** `takes_sheet.png` first version: a thin glass subject flew out of
  frame (thin subject, off-centre, drift 0.7) and the collapse heap left the frame empty. Glass
  now uses solid subjects, power 0.4, drift 0.4; collapse has gravity 1.0, power 0.85 and a closer
  camera. `g3_sheet.png`: row 2 is a live glass subject at q 1.0, 0.09, 0.22, 0.35; row 3 is the
  phrase rising live (q 0.61 to 1.0, section 28).
- **17 three new modes, field dropped** (second builder, same day). Looking at `r1_sheet.png`
  (all eight takes live, twice): every take was an outward burst of loose shards, three of them on
  cream or white, and `field` read as gold confetti with no subject. Added, all in the same
  shader pair: `lay=1` knolling (cells hop to grid slots, turn their mean normal up, scale to the
  slot), `skinmetal` (gilded skin), `glass` (additive blending, depth off, fresnel only; the MAT's
  blending and depth test follow the take), a third `mid` soup of 54,000 triangles and a 49,562
  triangle mid-weight atlas for the line of seven. `n1_sheet.png` first stills (knoll pieces far too
  small), `n2_sheet.png` after scaling pieces to slots (the dark blob in the middle of those
  stills is a stale shadow map: several states captured in one call), `k2_sheet.png` a live
  2-bar knoll cycle (q 1.0, 0.05, 0.21, 0.35, 0.50, 0.64, 0.79, 0.94) over the chorus cut
  arrival (age 0.08 burst open, 0.28 closing, 0.58 whole, 1.58 wave running), `r2_sheet.png` all
  ten takes live twice. Also: section change replays the arrival burst, kick jolts raised on
  every take, `onebit` steps its phase, cloud rests one half bar instead of one bar, top-down
  cameras aim 0.25 to 0.3 units up-screen (the pictures sat high in frame).
- **16 review of the first build.** `r1_sheet.png` with the feed (t 5 to 11 s, energy 0.13 to
  0.42): porcelain, mat, slabs and murmur strong; cloud's rest bar is a dim object on black;
  field and collapse mostly empty frame.

- **15 final.** Clean rebuild from `build.py` (it re-baked one small subject inside TouchDesigner because I
  had deleted that cache file: the in-TD bake path works for models as well as text), `hero.png`
  re-captured from it, `tdh.errors` empty, `tdh.check` PASS on the second run (moving delta 0.109,
  cook 1.25 ms), tox and snapshot saved, Preview off, Manual off, Subject -1.
- **14 cloud exposure.** `final2_sheet.png` (live, take 2): white subjects clipped under a 3.4
  key with glow 0.9; key 2.3, glow 0.6, exposure 0.9 (`m_sheet.png`, `take_2.png`).
- **13 live sequences.** Captures scheduled with `run(..., delayFrames=n)` so one call holds several
  moments. `live1_sheet.png` (take 1): q 0.63 all out; q 0.79 left columns locked, right still out;
  q 1 whole with hit_low 0.25, every copy cracked open by the kick; q 1 with hit_low 0.06, faint
  cracks; q 0.14 the next wave starting at the left; q 0.37 wave three quarters across.
  `live6_sheet.png` (take 6): age 0.12 arrival burst closing on HERE. NOW.; whole with kick cracks;
  collapse; section 5 -> 6 swaps the phrase mid-heap; it rises.
  `final2_sheet.png` (take 2): bar_pos 46.989 gives q 0.996 (last shard landing on bar line 47),
  bar_pos 47.58 whole with hit_low 0.33 and vocals 1.09 (red cracks glowing), bar_pos 48.026 gives
  q 0.009 with the section change swapping one subject for the next on the bar line.
- **12 perf.** Steady state about 1.5 to 2 ms CPU+GPU for the nine per-frame operators (take 0,
  146k triangles drawn twice plus the shadow pass; take 1 similar). A reading taken in the same call
  as a rebuild or a take change shows 20+ ms: stale first-cook values, not the running cost.
- **11 mat take, subjects.** Long thin objects are plain bars and slabs from above: unreadable
  (`k_t1_q000.png`, `k3_t1_q050.png`, `k4_sheet.png`). Round objects with a face read at once.
  Cream on a cream sheet had no contrast, so the floor became a green cutting mat with a tile
  grid. `k5_t1_round.png`: the strongest wide picture so far.
- **10 clean slabs.** Slab mode first sliced by micro-cell centre: torn sawtooth edges
  (`take_4.png` at that time, `e_sheet.png` row 2). The bake now cuts triangles on the slab planes and
  stores each triangle's centre height: straight cuts (`h_sheet.png`).
- **09 live.** With Manual off the phase follows `bar_pos`; kick jolt visibly opens cracks on a whole
  subject (`g_sheet.png`, bottom right, hit_low 0.08) and on the phrase (top right, hit_low 0.23).
  Rest fractions were then set so every lock-in lands on a bar or beat line.
- **08 take polish.** `e_sheet.png`, `f_sheet.png`, `i_sheet.png`: cloud switched from micro chips
  (red confetti, `a_sheet.png`) to fine cells (chunky shards with walls); field given a bigger
  object and impact-ordered stagger; collapse lining changed from gold (the heap turned yellow) to
  ink; `negative` (flat silhouettes) replaced by `onebit` (lit object + shadow, dithered); murmur
  lock order reversed to reading order (negative `d1`).
- **07 straight fractures.** Cells first followed the mesh's own triangle edges: staircase cracks
  (`c`-less captures `s02`, `b_t0.png`). Cutting triangles on the Voronoi bisectors gives clean
  polygonal shards (`c_t0_cut.png`). A second cut pass doubled the triangle count with slivers
  (cut corners sit exactly on the border): one pass only.
- **06 eight takes roughed in.** `a_sheet.png`: all eight differ at a glance from the first try.
- **05 shadows.** Shadow map was empty in the composite: a new Camera COMP sits at z = 5, so the
  top-down view was off the map. Zeroed. `s04_sheet_shadow.png`.
- **04 instancing + top-down.** 40 instances with a travelling wave, `s03_sheet_q45.png`.
- **03 first burst.** `s02_coarse_q30.png`: a statuette in big pieces, lining far too bright (emissive
  1.5 plus matte yellow); toned down and made metallic. Lining poked through thin features while
  whole (`s01_whole.png`): lining and walls are now discarded while a cell is closed.
- **02 atlas + GLSL MAT.** Pixel shaders have no `TDCameraIndex()`; camera position and the shadow
  flag are passed from the vertex shader.
- **01 probe.** `gl_VertexIndex` works in a GLSL MAT vertex shader on a Facet-unique POP: three
  consecutive ids are one triangle. A default Grid POP gives quads (four corners per primitive:
  long streaks); `surftype = 'triangles'` fixes it. (viewed with get_top_image, not saved)

## What is weak or unverified
- Generic defaults (log 23): seen as stills only. `_outer_skin` was judged by eye on the sixteen
  subjects here (`g7_sheet.png`), not measured; on rods and rings thinner than about 0.02 units
  (astrolabe, wire cage, lander legs) flecks of lining still show through the skin when open, as
  on any thin feature. The amphorae on the mat are dark on the green and read less well than the
  ducks. The stand-in (no assets) state was not rebuilt with the new subject names: its atlases
  will be baked inside TouchDesigner the first time an empty Assets folder is tried.
- No assets (log 22): every model take shows the same teapot, told apart only by a flat colour and
  the crack pattern, so a section change is a colour change; the forty on the mat and the seven in
  the chorus are teapots too. The teapot has no picture on it, so porcelain, slabs and onebit are
  plainer than with the library. The default face is lighter than Archivo Black, so the murmur
  chips and the collapse blocks are thinner. The stand-in state was seen only on this machine
  (Windows default face) and as stills; the "bake coarser if over budget" retry never fired here.
  The first build on a clean clone blocks TouchDesigner for the bake (estimated, not timed whole).
- Describe: the captions are static text; they carry no live numbers from the feed. On collapse
  the baked phrases are seen low from one end, as that take is designed, so they are strongly
  foreshortened: CUT INTO / BLOCKS is the hardest to read, and the caption does the explaining.
  The baked phrases are readable only while whole (half of murmur's cycle, a quarter of
  collapse's). The first Describe toggle after a build was not timed; "no hitch" rests on the
  check that no caption or atlas operator cooks on the toggle.
- Input: the picture is recognisable only while the slab is whole or nearly whole. Mid-burst it is
  coloured confetti; that is weakest on cloud (one whole moment in four bars, and the lit side
  can face away from the key lamp, so the picture is dim), onebit (dark pictures give black chips)
  and knoll's grid stage (pieces are scaled to their slots, so the picture does not survive
  there). Chorus shows the picture only as gold relief, each slab half hidden by the next. The
  slab is always 16:9 and samples the input as it is (no aspect fitting). Tested only with the
  test card, as stills; no other scene's out1 was tried, and nothing was watched as video.
- 29 float atlases are now held on the GPU (the eleven new ones are about 175 MB as files).
  `cache/` is git-ignored: on a fresh clone `build.py` bakes the eleven inside TouchDesigner
  (roughly 10 s of blocked main thread). That path was not re-run in this pass; the new atlases
  were baked with `dump_texts()` and system Python.
- Seen only as stills and scheduled still sequences, never as running video. Lock-in on the bar
  line is read from phase numbers beside captures (logs 13, 17), not from a frame-exact film.
- knoll: the whole-object moment is a small thing in a big blue field; pieces
  are scaled to their slots, so sizes are not true; pieces cross each other in flight. With thin
  subjects the yellow lining shows through and the tray reads as coloured chips.
- chorus has one subject; its seed only changes the camera azimuth and crack pattern.
- glass and cloud are both shards in a dark room; they differ in material and colour, not layout.
- collapse is still the emptiest frame while the heap is down.
- onebit's stepped motion has only been seen as stills.
- `tdh.check` cook_budget counts one-off loads after a rebuild (196 ms once here); run it twice.
- Triangles are cut only where they span exactly two cells; three-cell corners and the micro level
  (murmur chips) still follow mesh edges. Slab cuts have no wall faces.
- No self-shadowing between shards and no depth of field; shadows fall on the floor only.
- A section change swaps the subject instantly; the arrival burst covers it but it is still a swap.
- 18 float atlases are about 290 MB of GPU texture. They cook once, but they are held.
- Capturing several manual states in one call shows a stale shadow map; set, wait a few frames,
  then capture (`ad.py` does this with two scheduled jobs).

## Next
- Cut the micro level too (or bake a second, finer Voronoi level) so the murmuration chips are
  clean polygons; add wall faces on slab cuts.
- Depth of field for the cloud take (camera depth is easy to write to alpha).
- Cross-fade subjects at a section change by bursting the old one out and the new one in.
- Half-float atlases (ids packed in two channels) to halve the texture memory.

## Files
- `dx.py` Describe / Input pass helper: `shots([...])` schedules set-then-capture pairs with
  Describe, Input, phase and subject per shot. `build.py` also has `dump_texts()`, which writes the
  raw mesh of any new text subject from the live COMP so `python bake.py <name>` can bake it
  outside TouchDesigner.
- `ad.py` second-pass helper (scheduled live captures with the feed, quiet cost reading).
- `build.py` builder (WORDS, TAKES, DEFAULTS), `bake.py` fracture bake, `shaders/` GLSL, `run.py` and
  `sheet.py` development helpers (rebuild, stills, live sequences, contact sheets), `probe1.py`
  the first `gl_VertexIndex` probe (it rebuilds the COMP as the probe: do not run it casually).

## Keepers
(the orchestrator commits)
