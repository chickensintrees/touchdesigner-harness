# sc_point_morph: point-cloud shapeshifter

## Intent

One cloud of 123,904 points (352 x 352) that is, in turn, each of nine 3D models from the
asset pack and three pieces of lettering, wearing each model's real
texture colours, and that migrates from one to the next when the music changes section.

What makes it work:

- **Each shape must read when it settles.** Points carry the basecolor sampled at their UV, and
  the settled cloud has to be dense and crisp enough to recognise the object, not a fog.
- **The migration is the show.** Not a lerp: each point leaves on its own delay, and is carried
  by a curl-noise wind whose strength peaks mid-flight, so the shape dissolves from one side,
  streams, and condenses into the next.
- **It is a sculpture in a room, not a sprite on black.** Depth-sized, depth-dimmed points, a
  reflecting floor, a slow orbit, bloom. Lit by its own colour.
- **The music is visible.** Section = which shape. Kick = the surface jumps along its normals.
  Bass = the whole body breathes. Vocals = shimmer. Evolve = orbit and wind drift.

## Takes (2026-11-10 evening, after "too repetitive")

The first cut showed this scene as one object in front of a halftone sun every time. It now has
eight takes in the `TAKES` table of `build.py`, picked by `op('shot')['take'] % 8`. All of them are
the same 123,904-point cloud and the same stateless morph; a take changes layout, camera, how a
point is drawn and the backdrop, through uniforms, one Switch index and the Render TOP's camera.
Nothing loads at a cut: all 14 atlases are baked at build. Contact sheet: `captures/takes_sheet.png`
(rows: take 0-3 seed set A, take 0-3 seed set B, take 4-7 A, take 4-7 B), thumbnails
`captures/takes_thumbs.png`, singles `captures/take_<n>.png` and `captures/takeb_<n>.png`.

| Take | Name | One line |
|---|---|---|
| 0 | sculpture | The first cut's picture: one object (or a phrase) on a reflecting floor in front of a halftone sun. |
| 1 | catalogue | Fifteen small clouds in a 5 x 3 grid on paper, a different model in each cell, each turning; the beat walks a cursor through the cells. Caption in a bottom corner. |
| 2 | inside | The camera stands inside a five-times model and looks out through its skin: a wall of coloured discs with radial echo. No object outline, no text. |
| 3 | plan | Straight down on the object, drawn as climbing contour lines in one ink on a drawing grid (navy, teal or warning red). A plate number in the corner. |
| 4 | streak | Long exposure: one point in forty, the model turning fast, seen from above; every point leaves its orbit as a line. |
| 5 | raster | The object as a print screen of flat discs in two inks on yellow, pink or ivory paper, cropped close and off-centre, with a line of caption type. |
| 6 | duel | Two objects side by side in two inks, seen from near the floor, a strand of points forever pulled out of one into the other. |
| 7 | phrase | A phrase as landscape: ivory letters on red, blue or green stock, the camera raking along them from one end, the far end lost in the paper. |

Only take 0 can show the short lettering (`word`) centred (one shape in twelve of its list); take 7
shows it one visit in three, raked and cropped. Takes 1 to 6 never show it.

`seed` chooses: where the walk through the take's shape list starts (so which objects), which of
three papers / inks / captions, which side the camera and the subject sit on, the orbit phase, the
plan view's rotation, the catalogue's turn.

`age`: every take arrives. All: the cloud falls into place from a burst in 0.4 s (`burst` column).
Take 0: the sun flares and springs wide. Take 1: cells pop in one after another over 0.4 s. Take 5:
the raster starts at 72 px cells, then 36, then 18 (two snaps in 0.22 s). The echo is emptied for the
first 0.07 s of a shot so the last visit's trail never shows. `captures/arrive_sheet.png`.

Review helper: `shoot.py` (Text DAT `shoot_code`) schedules Take / Seed / capture a few frames apart
and records the feed and whether the cutter changed Take in between (`take_ok`).

## Describe mode and Input (2026-11-11, for the public website)

Two agents did this: the first was cut off with the code written but nothing logged; the second
rebuilt, checked every step again, fixed what the captures showed (log 38 to 42) and wrote this.

### Describe

`Describe` on the scene COMP swaps every word for words about the technique. No rebuild, no hitch:
the Describe letterings are four more atlases baked at build (`word_d0` .. `word_d3`) and the
captions are a second tuple in the same Text TOP expression. The words live in `TAKES` in build.py
(`dshapes`, `dcaptions`) and are mirrored in preset.json `"words"`. Captions are in the caption face, 24 px
(40 px in the raster take), in the same bottom corner as the takes' own captions. All sheets:
`captures/desc_sheet.png` (one per take), `captures/desc_sheet_all.png` (every caption and word),
singles `captures/desc_take_<n><a|b|c>.png`.

| Take | What Describe shows |
|---|---|
| 0 sculpture | The lettering shapes become POINT CLOUD, 123,904 POINTS and ONE CLOUD / MANY SHAPES (no red last mark); three 3-line captions explain the sampling, the section morph and the beat band, kicks and vocals. |
| 1 catalogue | One line: how the cloud is dealt into 15 cells, how many points each, the beat cursor. |
| 2 inside | INSIDE THE CLOUD plus two lines: the camera inside a five-times model, discs are surface points, kicks and feedback rays. |
| 3 plan | Three lines on how points near a height level make contour lines, 15 levels per unit, the beat contour. |
| 4 streak | LONG EXPOSURE plus two lines: 1 point in 40, each frame keeps about 99 % of the last, trails are feedback. |
| 5 raster | Two short lines at 40 px, top corner: A HALFTONE / MADE OF POINTS., DARKER SURFACE, / BIGGER DOT., THE NEAREST POINT / WINS EACH CELL. |
| 6 duel | Two or three lines: half the points each, the strand, ink change over four beats, 6 % in transit, a hard kick pulls a quarter. |
| 7 phrase | The lettering becomes MADE OF / POINTS, POINT CLOUD or ONE CLOUD / MANY SHAPES; one caption for all seeds. The camera is less raked and further back than with Describe off (`dang`, `ddfix`, `dtgtx`, `dtgty`), because the take's own rake left these words unreadable. |

A dark band (`capplate`, `uCap` in post.frag) sits behind the caption in takes 0, 2, 3, 4, 6 and 7,
only in Describe mode.

### Input

`Input` names a TOP outside this scene; `ctl['inon']` is 1 only then (a missing path, a CHOP, or
this scene's own out1 all give 0). `in_sel` (Select TOP) reads it and is the GLSL MAT's third
sampler `sIn`; blank selects a 16 x 16 black constant that no shader path reads. The picture enters
where the cloud gets its positions and colours:

| Take | `inmode` | What it does with the picture |
|---|---|---|
| 0 sculpture | 1 | A new shape, the picture sheet (`picture.py`, atlas `word_pic`: 123,904 points on a 2.4 x 1.35 sheet), takes each point's colour from the picture and stands it forward by brightness. The take's list alternates sheet and models, so the picture streams off into a model and back; the models wear the picture as a front projection at 55 %. |
| 2 inside | 2 | Every disc takes the picture's colour at its own place on screen: the picture seen through the wall of discs. |
| 3 plan | 3 | The sheet lies flat under the top camera with brightness as height, so the contour lines trace the picture's tones. The strongest of the five. |
| 5 raster | 1 | The sheet printed as the two-ink halftone, in 12 px cells, pulled back so the whole picture shows under the caption. |
| 7 phrase | 1 | The sheet raked in one ink; bright parts stand forward of their own holes. |
| 1, 4, 6 | 0 | Ignore the input: fifteen tiny clouds, one point in forty, and two-shapes-in-two-inks have nowhere a picture would read. |

Captures with `/project1/sw_testcard/out1`: `captures/in_sheet.png`, singles `captures/in_take_*.png`.
Blank Input: `captures/final_off_sheet.png` (all eight takes, two seeds, Describe off).

## Assets (2026-11-11, portability)

No file here names a folder. Every file parameter is an expression on the scene's paths module
(`mod.paths`, installed by the scaffold); the builder finds the repository from `td.project.folder`.

| The scene uses | From | With no assets folder |
|---|---|---|
| Nine models, named in the `MODELS` rows of the scene's words (build.py `DEFAULTS`, or a pack's own file): `model.obj` and `basecolor.png` | `<assets>/models/<slug>/` | `stand_in.py` bakes a stand-in for each slot at build: TouchDesigner's bundled teapot (the file `mod.paths.model_file` returns, read and triangulated in numpy) for the first and the last slot, and seven solids drawn in numpy for the rest (tower, ring, ball, spring, eight-sided gem, trefoil knot, cone). Each is fitted to 1 unit like a library model and coloured in bands of two ident-palette colours. The File In POPs still load the teapot and the texture operators a flat ivory tile (`stand_in.png`, 78 bytes), so nothing warns; the bake does not read them. |
| Archivo Black (the lettering shapes) | `<assets>/fonts/ArchivoBlack-Regular.ttf` | TouchDesigner's default face. `sample_surface.py` fits any lettering to 2.4 x 1.05 units, so the phrases still fill their place. |
| The caption face (`mod.paths.font('chicago')`; the shipped pack answers with IBM Plex Mono) | `<assets>/fonts/`, by that name or the pack's alias for it | TouchDesigner's default face, same sizes and corners. |

Nothing precomputed is committed: every atlas is baked at build from whatever `mod.paths` returns.
`sample_surface.py` asks the module at cook time (`have('models/<slug>/model.obj')`), so the choice
follows the COMP's `Assets` parameter; changing that parameter needs a rebuild (the bakes cook once).
Captures with an empty assets folder: `captures/p2_none_sheet.png` (eight takes live, then eight held
on one shape), `captures/p3_none_sheet.png` (Describe on takes 0, 5, 7; Input on takes 0, 3, 5; three
live). With assets after the conversion: `captures/p4_with_sheet.png`; before it: `captures/p0_ref_sheet.png`.

## Words and models (2026-11-11)

Everything the scene says and shows that belongs to an asset pack sits in one dict, `DEFAULTS`, at
the top of build.py, and is read once at build through `LIB['scene_words'](scene, DEFAULTS)`:

| Name | What it holds |
|---|---|
| `MODELS` | Nine rows, one per model slot: the pack's model name and its tuning (`front` yaw, `high` camera height, `back` distance factor, `tint` of its sun). |
| `PHRASES` | The three letterings (`word`, `word_made`, `word_out`). |
| `RED_FROM` | How far across a lettering its last mark turns red (`uDesc.y`; 0.96 puts it on a closing full stop). |
| `CAPTIONS` | Three corner lines each for the catalogue, plan, raster and duel takes. |
| `TAKE_SHAPES` | Which models and letterings each take walks through, by name. |

The defaults are generic: nine objects of the shipped pack (ribbon_loop, marble_bust, gramophone,
space_helmet, skeleton_key, astrolabe, amphora, hourglass, lander) and plain words about real-time
pictures and a catalogue of objects. A pack replaces any of the five names with its own
`scenes/sc_point_morph/words.json`; the same build then draws that pack's models, words and tuning.
The slots have fixed places in `LAYOUT` (`model0` .. `model8` between the letterings), so shape
indices, the Describe letterings and the picture sheet are the same whatever the pack. The Describe
words are not in `DEFAULTS`: they describe the technique and stay in `TAKES`.
`stand_in.py` goes by slot number, not by model name, so the no-assets picture is unchanged.

Chosen by looking (captures `g0_*` .. `g5_*`, generic pack): the key turned 1.57 so its flat side
faces the camera, the gramophone 0.5; the helmet and lander step back (1.15, 1.1). The plan take
leaves out the hourglass and amphora (plain discs from above), the inside take the open shapes
(ribbon, astrolabe, key, hourglass, gramophone: half the frame or more is empty from within,
captures `rv_g4_t2_*`, `rv_g5_t2_*`), the streak take the pale ones (bust, hourglass, helmet: white blobs at gain 5),
the raster take the ribbon (wide enough to run under the caption) and the bust and hourglass
(one ink only: a silhouette with nothing inside it, captures `rv_g2_t5_*`). The dark crystal cluster is not
used: black points on the dark room.

## Technique

Built by `build.py` (idempotent). 123,904 points (352 x 352), drawn twice (the second instance is
the floor reflection) = 247,808 drawn points, under the 250k cap.

1. **Bake, once.** Each shape (File In POP of the library OBJ, or a Text POP of a phrase in
   Archivo Black) goes through a Facet POP (unique points) and POP to TOPs, so triangle corners
   reach `sample_surface.py`, a Script TOP callback. It samples the surface area-weighted with
   numpy, reads the basecolor at each point's UV, sorts the points by height, and writes one
   atlas per shape: position rows (alpha = mean point spacing), colour rows, normal rows.
   Texel i is point i in every atlas. The bakes cook once (about 0.1 to 0.3 s each at build).
2. **Pick a pair.** Two Switch TOPs choose the atlas we leave (section-1) and the one we become
   (section), walking the take's own list.
3. **Morph in the vertex shader** (`shaders/cloud_vertex.glsl`, GLSL MAT on a Grid POP of points
   whose xy is the texel address). Stateless: progress = section_pos / 0.5. Each point leaves on
   a delay (a front sweeping up shape A, blurred by a per-point random), bows outward round the
   vertical axis, and rides a divergence-free sine wind whose strength is sin(pi s) squared.
   One point in nine never lands and drifts as dust.
4. **Opaque, depth-tested discs**, sized from the shape's own point spacing, lit by a warm key,
   cool fill and rim. Instance 1 is mirrored in the floor.
5. **Echo** (`shaders/trail.frag`): the feedback is read slightly magnified about the sculpture,
   so light creeps outward as rays; drum hits widen the step. `post.frag` keeps the echo behind
   the crisp cloud (using the render's alpha), adds a quarter-size blur glow, the room (floor
   pool, key shaft, drifting motes), luminance tone map, vignette.
6. **Halftone sun** (second pass, `post.frag` `sun()`): a disc of print dots in an accent colour
   chosen against the object (the `tint` of its `MODELS` row; lettering on a dark pink lozenge) stands behind the sculpture and is mirrored in the
   floor. The cloud's alpha masks it, so black parts of a model read as silhouette.
7. **Scan front** (second pass, vertex shader): once per beat a thin band rises from the floor
   through the sculpture; where it passes, points lift along their normals, swell and burn in the
   accent colour.

8. **Takes** (third pass). `ctl` (Constant CHOP) holds one channel per column of `TAKES`; `sel` picks
   the shape pair from the take's own list; `camctl` the orbit camera. The vertex shader lays the
   cloud out (one object, grid by `id mod 15`, or two objects with a travelling strand) and draws
   it (lit texture, one ink with fog, two inks, contour lines, or raster cells). Three cameras
   (`cam` orbit, `cam_top`, `cam_in`); the Render TOP's camera parameter is an expression.
   `post.frag` has four backdrops (room and sun, flat paper, void, drawing grid). A Text TOP
   (`caption`, the caption face) is laid over the result.
   - Catalogue atlases (`mosaic.py`): point i takes its texel from model (i mod 15) of nine models,
     so a "shape" can be fifteen small clouds and still morph like any other.
   - Raster: each point moves to the centre of its 18 px screen cell (odd rows offset half a cell)
     and is drawn as the whole cell, paper with one ink disc sized by how dark the lit surface is.
     Depth test keeps the nearest point, so each cell shows the visible surface.
   - Phrases are Text POPs fitted to 2.4 x 1.05 units inside `sample_surface.py`.

Scene custom page: `Manual`, `Shape`, `Morph`, `Yaw` freeze a state for inspection (Manual also
switches off a take's spin and seeded yaw).

## Channel to visual

| Channel | Drives |
|---|---|
| `section` | which pair of shapes (A = section-1, B = section, mod 6); sun and room accent colour (hard cut) |
| `section_pos` | morph progress (first half of the section travels, second half holds); camera distance and height blend between the two shapes' framings, and a 32 % step back mid-flight; at 0 the sun flares ivory and springs 35 % wider, settling in about 0.1 of the section |
| `hit_low` | whole surface jumps a little along normals, dust is thrown about 10x further; heats the scan band; sun swells 14 % and brightens; echo zoom step, so rays leap outward |
| `hit_mid` | fine fizz of every point |
| `hit_high` | one point in forty flashes; background motes brighten |
| `bass` | whole body scales up to 6 % |
| `vocals` | shimmer: a rolling 3 % of points flare and swell |
| `pulse` | point size +12 %, glow gain, floor pool, echo zoom |
| `energy` | camera pushes in 8 %, overall brightness, echo length (decay 0.80 to 0.90), room light, sun brightness, base strength of the scan band and beat ring (both fade out below about 0.12) |
| `evolve` | wind phase, shape sway (yaw), camera swing and bob, sideways drift of the subject, shimmer roll, mote drift |
| `beat_pos` | height of the scan front (floor to above the head in about 0.7 beat); radius of the ring of dots the sun throws across the room each beat (ring strength from `energy` and `hit_low`) |

| `shot.take` | which row of `TAKES` (layout, drawing mode, camera, backdrop, shape list) |
| `shot.seed` | start of the walk through the shape list, palette / caption choice (thirds of 0-1), camera side (above or below 0.5), orbit phase, plan rotation |
| `shot.age` | arrival burst, sun flare, catalogue cells popping in, raster cell size snapping 72 / 36 / 18 px, echo emptied below 0.07 s |
| `beat_i` | catalogue: which of the fifteen cells is swollen and brightened (one step per beat) |
| `beat_pos` | duel: the strand's travel (a point crosses in four beats); plan: the scan front is a bright contour climbing the object |
| `hit_low` | duel: how many points are torn into the strand (6 % to 28 %); plan: grid lines brighten; raster: the scan band swells the discs |
| `pulse` | raster: disc size +20 %; flat takes: paper brightness 5 %; catalogue: the cursor cell's swell |

## Weak points (honest)

With no assets (2026-11-11):

- It is a different picture, not a lesser copy: striped teapots and toy solids instead of the pack's
  models. The technique reads (sampling, morph, every take's drawing mode); the objects are lost.
- The stand-in colours are two flat bands, so the takes that live on texture detail are plainer:
  the inside take is a wall of two colours, and the plan take of a ball or ring is concentric rings.
- The tower and the gem have 12 and 16 flat faces: lit as flat slabs, with hard band edges.
- Describe take 0 says EACH IN ITS TEXTURE COLOUR; a stand-in has no texture, only bands.
- The default face is narrower and lighter than Archivo Black and the caption face: lettering shapes are
  thinner, and the raster take's 40 px caption can run onto the subject
  (`captures/p2_none_sheet.png`, row 4 column 2).
- Framing tables (`FRONT`, `HIGH`, the step-back factors) were tuned for the real models; the
  stand-ins sit in frame but nobody chose their best side.
- Judged from stills only, at one passage of the track (sections 11 to 12).

Describe and Input (2026-11-11):

- Describe captions are 24 px caption type in a corner. They read at 1280 x 720 but will be small in a
  thumbnail; only take 5 (40 px) and the lettering of takes 0 and 7 read at gallery size.
- Take 0's and take 7's Describe lettering only shows when the section walk lands on a word: take 0
  shows a model nine visits in twelve, with the caption alone carrying the explanation.
- Take 7 in Describe mode is a different camera (less rake, further back), so it is not quite the
  take's own picture with new words. MADE OF / POINTS still loses a little of its second line
  behind the caption band on one camera side.
- Take 4's caption sits on the long-exposure glow when the subject is on the caption's side; the
  band keeps it readable but covers the foot of the picture.
- Captions are fixed sentences: no live numbers from the feed.
- Input, take 0: models wearing the picture at 55 % barely show it (`in_take_0_obj.png`: a few
  stripes on a figure). The sheet and the migration carry it.
- Input, take 2: the picture is recognisable only because it is laid over the screen; the model
  you are inside no longer matters. Dark pictures leave dark discs on a dark void.
- Input, takes 5 and 7 with Describe on: the caption can touch a corner of the sheet.
- Input, take 5: fine detail is lost at 12 px cells (the test card's letters read, small text will
  not), and the second ink follows saturation, so a grey picture prints in one ink.
- Input takes hold the sheet for the whole shot in takes 3, 5 and 7: the section morph that is
  this scene's signature only happens in take 0.
- The Select TOP reads the other scene's out1; if that scene is not cooking, the picture is a
  still. Nothing here cooks it on purpose.
- Input was judged with the test card only, never with another scene's output, and in stills.
- Describe and Input together were looked at for takes 0, 5 and 7 only.

Third pass (takes):

- Take 2 (inside) is the weakest. It is vivid and unlike the others, but it is an abstract field of
  discs; you cannot tell which model you are inside, and mid-migration it turns beige-grey
  (`captures/takeb_2.png`).
- Takes that land mid-migration lose their subject for up to half a section: the plan view becomes a
  round swarm (`a_sheet.png`-style frames), the raster a stack of dots (`captures/take_5.png`). Take
  7 migrates in 0.22 of a section and take 2 in 0.3 for this reason; the others still take 0.5.
- Take 4 (streak) is a small subject in a large dark frame, and it looks much the same for every
  seed except for the model. Streak length depends on frame rate (decay is per frame).
- Takes 0, 4 and 6 share the dark void; they differ in subject count and drawing, not in palette.
- Raster captions can touch the subject (an earlier hero frame had a caption's first letter on the model).
- Catalogue: nine models in fifteen cells, so six repeat; low boxy models read as lumps
  at that size.
- The beat scan front is still drawn in every take; in the duel it shows as a peach band near the
  floor.
- The build now stalls TouchDesigner for about 2 to 3 s (twelve bakes of about 0.25 s each).
- Still judged from stills only. The arrivals and the beat cursor were seen as single frames.
- Music-following was checked from two stills per take with the feed recorded, not from motion; in
  the flat takes (1, 5, 7) the music shows mostly through the migration, the cursor and disc size,
  which is quieter than take 0's sun and rays.

Earlier passes:

- The weakest shape of the first model set was a low cream box whose detail only just read, even from above.
- The floor line of the sun (a fixed 0.33 of the frame height) does not follow the camera; with the
  high camera of a low model the sun's horizon and the object's foot do not agree.
- The scan front runs on every beat whether or not there is a kick (its strength follows energy and
  hit_low), so it shows tempo more than drum pattern.
- With the subject drifted to one side, the other half of the frame holds only the beat ring.
- Each kick puffs the dust; on busy drum passages the shape rarely sits fully still.
- Dark specks on bright models are gaps between discs showing the far side, not texture.
- `bass` in this feed flips between about 0.01 and 1 to 2, so the breathing is a twitch more than
  a breath.
- Sprinkle POP and Lookup Texture POP are not in the final network (see log 02).
- The build stalls TouchDesigner for roughly 1.3 s in total while the six Script TOPs bake.
- `tdh.check` cook_budget read 18.7 ms on one run and 0.85 ms on the next with nothing changed;
  per-operator times of the 13 cooking operators sum to about 1 ms in a quiet sample and about
  13 ms (render 5.8, trail 3.5, post 3.8 CPU) in a contended one. Seven other scenes were cooking.
  I could not measure it alone.
- Not seen in motion by a person; judged from stills taken 0.8 to 2.8 s apart.

## Next

- Give the word its own echo setting (shorter, vertical only) and cap shimmer on it.
- Per-shape sway range (narrow for long, low models).
- Smooth `bass` with a Lag before it scales the body.
- Try a second, coarser population (bigger soft additive points) for the in-flight phase only.

## Log (newest first)

- **44 generic defaults (2026-11-11)** The defaults in build.py are now generic words and the
  shipped pack's models; the originals live in a private pack's `scenes/sc_point_morph/words.json`
  and a build on that pack draws them as before (held takes compared with captures taken before the
  change: same models, words, palettes and framing). New `DEFAULTS`, `LAYOUT`, `_configure()`;
  two lettering slots renamed `word_made` / `word_out` (same name lengths, so the sampler's
  seed is unchanged); the red last mark is `RED_FROM`, not a constant in the shader; stand-ins go
  by slot. Generic pack: all eight takes and Describe looked at, errors empty. Older entries below
  were written about the first model set and are worded neutrally.

- **43 portable (2026-11-11)** `p0_ref_sheet.png` (before), `p1_with_sheet.png` and
  `p4_with_sheet.png` (after, with assets: the eight held takes match the reference; the live rows
  differ only by which section the music was in), `p2_none_sheet.png`, `p3_none_sheet.png` (empty
  assets folder). build.py lost its five folder constants: file parameters are `mod.paths`
  expressions, shader and callback DATs use `mod.paths.here(...)`. New `stand_in.py` (Text DAT
  `stand_in`) and `stand_in.png`. Traps: the bundled teapot is mostly quads (1617 faces, 6440
  corners), so the three-corners-per-triangle bake cannot read it through the Facet POP, hence the
  numpy OBJ reader; a Movie File In with an empty file warns "File not found" once it cooks, hence
  the tile. Nine teapots would have made the morph invisible, hence the drawn solids. With the
  Assets parameter on an empty folder: errors empty, all takes drawn, Describe and Input work.
  Blanked and rebuilt: errors empty, tdh.check run 1 pending, run 2 PASS (cook_ms 1.78, 21 active
  ops). Portable test for this slug: 1 passed. No test covers stand_in.py itself.

- **42 Describe and Input, handed back** `captures/fin_sheet.png` (final build: eight takes with
  Describe on, five with the test card, three with Input blank), `final_off_sheet.png` (all takes,
  two seeds, Describe off, Input blank: as `takes_thumbs.png` and `v1_sheet_off.png`). Errors
  empty. tdh.check run 1 pending (first cook sample), runs 2 and 3 PASS, cook_ms 1.82 and 1.46 with
  21 to 23 active ops; render 0.21 CPU + 0.10 GPU, in_sel 0.01 ms. Build stalls TouchDesigner for
  about 2.9 s (19 bakes). Tox and snapshot saved; Describe off, Input blank, Preview off.
- **41 inside take with a picture** `i5_sheet_a.png` (cell 5: nearly empty, caught mid-arrival),
  then seen live: the picture was under a pink wash. A tenth of the model's colour was left in and
  the inside take's 1.7 x saturation boost blew it up. Now the disc takes the picture's colour
  outright, scaled by the model's brightness, and the boost is skipped. `in_take_2.png`.
- **40 Describe words fixed after reading them** `d1_sheet_*.png`, `d2_sheet_words.png`,
  `d3_sheet.png`, `d4_sheet.png`, `desc_sheet_all.png`. Raster captions were one 40 px line that ran
  across the subject (d1_sheet_45): broken into two lines. Take 7's lettering TEXT SAMPLED / INTO
  POINTS. and 123,904 POINTS were unreadable raked from one end (d2_sheet_words): replaced by MADE
  OF / POINTS, shorter list, and a Describe camera (angle 0.45, distance 2.7). Its caption said
  SEEN FROM ONE END, no longer true with that camera: now IN ONE INK. Duel caption claimed a kick
  pulls more than a quarter of the points; the shader gives 6 % + 22 % x kick strength, so only a
  full-strength kick reaches 28 %: now A HARD KICK PULLS A QUARTER. Caption band added to takes 0,
  4 and 6, where the glow or the floor reflection ran under the text.
- **39 Input checked take by take** `i5_sheet_a.png`, `i5_sheet_b.png`, `i6_sheet.png`,
  `in_sheet.png`. The first agent's sheet, plan relief, halftone and raked sheet all worked as
  written. Raster with a picture had the take's caption lying on the halftone: pulled back
  (`indmul` 1.25) and lowered (`intgty` 0.27).
- **38 picked up a cut-off session** `v1_sheet_off.png`. build.py, the shaders, picture.py,
  shoot.py and preset.json already held Describe and Input code with no log entry. Rebuilt on the
  scaffold with Describe and Input parameters: errors empty, all eight takes as before with both
  off. Nothing of the first agent's was assumed checked.

- **37 third pass, handed back** `captures/takes_sheet.png`, `takes_thumbs.png`, hero `hero.png`
  (= `takeb_5.png`, take 5 seed 0.8: a leafy model as a navy and blue raster on ivory). Errors empty.
  tdh.check run 1 FAIL (cook_budget 2015 ms: it summed the one-off bake cooks), run 2 PASS, cook_ms
  2.73 with 20 active ops. Per take, everything that cooked in the frame (CPU + GPU, from shoot.py):
  1.1 to 2.7 ms; render 0.15-0.37 CPU + 0.07-0.14 GPU. Samples right after a rebuild read 23 to
  29 ms (render 5.0, trail 3.4, post 4.3 CPU): first cooks, not the steady frame. Preview off.
- **36 phrase on coloured stock** `g_sheet.png`, `h_sheet.png`, `takes_sheet.png`. Take 7 was a
  fifth dark-void take; moved to flat paper with fog into the paper. Navy ink made the letters
  flat grey slabs (h_sheet top row): ivory ink on red / blue / green keeps the face shading.
- **35 phrase take** `c_sheet.png` (bottom right: amber mush, discs up to 40 px, camera 0.6 from the
  letters), `d_phrase.png`, `e_sheet.png` (contour-line drawing tried: unreadable), `f_phrase.png`.
- **34 streak** `e_sheet.png` (6 % of points: a fog ball), `f_streak.png`, `g_sheet.png` top right
  (2.5 % of points, spin 14 x evolve, decay 0.988, camera 0.8 above: orbits read as lines).
- **33 raster** `b_raster_dbg.png` .. `b_raster_dbg3.png`. First try: nothing drew (clip-space z
  below 0 is clipped here). Second: biggest disc in front, so every cell showed its darkest point
  and all discs were the same size. Final: each point draws its whole cell (paper plus disc) and
  ordinary depth picks the nearest point.
- **32 first eight takes** `a_sheet.png`, `c_sheet.png`. The cutter was showing the scene and set
  Take while I was capturing (c_sheet: five cells show take 2), hence `take_ok` in shoot.py.
- **31 rebuilt on the new scaffold, nothing else changed** `31_rebuilt_scaffold.png` (a boxy model in its
  amber sun, as before); the COMP has Take, Seed, Shotstart and the `shot` CHOP.
- **30 starting point** `30_before_0.png` .. `30_before_2.png`: the word in its pink lozenge, a
  figure arriving in a yellow sun, the figure settled in the same sun. Same composition in all three.

- **25 second pass, handed back** `25_word_manual.png`, `25_final_live.png`, hero `hero.png`
  (= `24_final_toword.png`: a model pouring into the word on the pink lozenge). Word glow cut from
  0.75 to 0.48 (24_final_word had the letters blooming shut). Final rebuild from build.py, errors
  empty. tdh.check: run 1 PASS but cook_budget read 0.0 ms with 0 active ops (its first sample, not
  a measurement); run 2 PASS with cook_ms 0.955, 13 active ops. Per-operator in the same call:
  render 0.20 CPU + 0.11 GPU, trail 0.12 + 0.04, post 0.11 + 0.05 ms. A call a few seconds earlier
  read render 4.9, post 3.8, trail 3.3 ms (CPU + GPU) with other scenes cooking, so the contended
  figure in the weak points still stands. Preview off.
- **24 second pass, final** `24_final_*.png`. Rebuilt from build.py after the changes below.
- **23 beat ring, word as a lit sign, framing** `23_ring_*.png`. The sun throws a ring of dots
  outward each beat (fills the dead sides of the frame with something on the beat). Word faces
  glow instead of being lit like plastic, its sun is a darker lozenge with round dots (22_live_6/7
  had dull grey letters on mid pink and stretched dots). Two boxy models step back (23_ring_4 had
  one touching top and bottom). Sideways drift of the subject cut from 0.36 to 0.28.
- **22 a low model seen from above, white compression** `22_live_*.png`. A low model from eye height is a
  cream brick; from 0.85 above its middle its top shows. Bright albedos are
  compressed before lighting so pale models keep surface detail (20_review_2 was a white
  slab). Sway about the front cut from 0.7 to 0.4 rad (word 0.42 to 0.24).
- **21 halftone sun, scan front, flight look** `21_sun_*.png`. First viewing as art director
  (`20_review_*.png`): the first model was lovely, but every frame was at least half empty ink, the
  mid-flight cloud was grey confetti that overflowed the frame (20_review_0), the word was dim and
  half in the vignette (20_review_6), and the kick's 1.4 % surface jump could not be seen in a
  still. Added the sun, the per-beat scan front (replaces the kick patches), richer and smaller
  in-flight points, camera step-back mid-flight, softer vignette (0.35 to 0.55 at the corners).

- **14 final rebuild** `captures/14_final_sheet.png`, hero `captures/hero.png` (= 13_thirds_4).
  Fresh rebuild from build.py: one model dissolving, the same with rays, another with a kick band, then
  flowing into the word. Checks pass on the third run (second run failed cook_budget at 18.7 ms).
- **13 thirds** `13_thirds_sheet.png`. Look-at target drifts sideways so the subject moves between
  the thirds; echo centre and room lights follow it. Word stays centred.
- **12 echo behind** `12_behind_sheet.png`. Post now uses the render alpha to keep the echo behind
  the cloud: 11 had rays painted over a model's dark face. Camera distance now allows for the
  object's depth (11 had two models cropped).
- **11 rays** `11_rays_sheet.png`. Feedback read magnified about the sculpture: light creeps
  outward as cool rays, kicks throw them further. Much more presence than plain trails.
- **10 / 09 live** `10_live_sheet.png`, `09_live_sheet.png`. First full sequences: model to word to
  model to model. Vocals pass 1.2 and blew out the shimmer, so it is clamped. Point diameter went
  from 1.35 to 1.8 spacings to close holes.
- **08 sized** `08_sized_sheet.png`. Point size from each shape's own spacing (atlas alpha): the
  one model was porous and another solid at one fixed size. All six shapes recognisable.
- **07 dust** `07_dust_sheet.png`. One point in nine hangs off the surface. Dimming them made
  dark specks, so they are smaller instead. Kick displacement cut from 0.085 to 0.014 on the
  surface (it tore the shape apart), 0.11 on dust.
- **06 fronts** `06_front_sheet.png`. Each shape at yaw 0; chose front offsets; camera distance
  and height per shape from info.json. Ghosts in this sheet are trails from switching shape by hand.
- **05 live** `05_live_a.png`, `05_live_b.png`. First live frames; a pale model overexposed.
- **04 Bloom TOP dropped.** It lifted the whole frame to grey. Replaced by a 320x180 Blur TOP
  added in post.
- **03 additive dropped** `03_settled_sheet.png` (all six cells show the same model: forcing cooks inside
  one script does not advance the frame). Additive points made a pretty glass figure but white models
  summed front and back into a blank slab. Switched to opaque depth-tested discs.
- **02 Sprinkle POP dropped** `02_area_weighted.png`. Sprinkle POP "Per Primitive" puts the same
  number of points on every primitive regardless of area (measured: a 0.1-unit patch of 800
  triangles beside a 1-unit quad of 2 took 99.7 % of the points). One model's thin cord glowed and its
  body was bare (`01_first.png`). Replaced by numpy area-weighted sampling in a Script TOP, which
  also made the height sort and the gutter fix possible.
- **01 first** `01_first.png`. Sprinkle + Lookup Texture + POP to TOP atlases, additive GLSL MAT.
