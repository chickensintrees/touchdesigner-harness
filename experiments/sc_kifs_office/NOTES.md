# sc_kifs_office: ray-marched letter architecture, seven takes

## Intent

A nave you fly down forever, built from a folded (kaleidoscopic IFS, Menger-style) lattice whose walls are
embossed with sign lettering. What has to work for it to read:

- The lettering must be legible relief, lit from the side, not a decal: it is part of the distance function,
  so it casts and catches light.
- The space must read as architecture (a tall corridor with side cavities and depth), not as a fractal blob:
  a carved nave, fog with depth, a tube light along the axis, ambient occlusion in the recesses.
- A narrow palette: putty steel surfaces, fluorescent green light, CRT blue fog, warning-sign red as the accent.
- The music re-tunes the building: bass and vocal pitch turn the fold angles, the bar line opens the cavities,
  each kick sends a ring of light down the nave, and the camera never stops (evolve).

## Technique

One GLSL TOP (`kifs`, 1280x720, rgba16float) running `shaders/kifs.frag`, fed by a 1024x1024 text wall.

- **Text wall**: four Archivo Black Text TOPs (`row0..3`, 1024x256 each, the four `ROWS` of the scene's words: by default REAL TIME, DO NOT TOUCH in red,
  PLATE 07, EXHIBIT 12) stacked by a Layout TOP, blurred 5 px (the blur is the bevel), mipmapped, repeat-extended. Red channel =
  letter height; red minus green = "red ink" mask. The shader's `NROWS` and frieze row numbers follow that order.
- **Distance function**: a Menger-style kaleidoscopic IFS (4 iterations of abs fold, two rotations, axis sort,
  scale 3) repeated on a 4-unit lattice, with a pointed-arch nave carved along the camera path. The nave is a
  little wider than the lattice's own central shaft, so its walls are cut flat and the lettering has a face to sit on.
- **Lettering in the distance function**: stage 1 marches (64 steps) to a shell `base - RELIEF`; the base normal there
  fixes triplanar weights and mirror signs (so text is never back to front); stage 2 (16 steps, 80 in total) refines
  onto `base - RELIEF * height(text)`. The normal, and so the lighting, comes from that displaced field.
- **Inscription frieze** (2026-11-10, second pass): a 3.5 cm steel belt on both nave walls at eye height, part of the
  distance function. It does not use the triplanar read: each 2.16-unit stretch gets one whole row of the text wall,
  with ruled lines above and below and a tick between words, so rows 0, 1 and 2 of the wall are
  always whole and readable whatever the folds do to the lattice behind.
- **Shading**: fluorescent battens across the nave every 2 units (volumetric glow accumulated in the march; the two
  nearest light each surface point with inverse-square falloff and a 7-step soft shadow each), 4-tap ambient
  occlusion, a very faint cold fill and camera lamp, exponential fog toward near-black CRT blue, ACES-style curve,
  an extra contrast curve, blue-shadow / green-highlight split tone, vignette. Putty steel lattice, darker steel
  frieze, cream letters, red letters (the wall's red row) that are slightly emissive at all times.
- **Control CHOPs**: `sel_pitch -> pitch_hold (hold while a note sounds) -> tune (lag 0.18 s)` so the folds glide
  between notes and stay put through rests; `sel_kick -> ring` (Trigger CHOP, 1 at each kick, linear fall over 0.45 s).
- Nine uniforms: `uCam`, `uFold`, `uHit`, `uShot` (seed, age, take, arrival), `uTakeA..D` (see Takes) and `uIn`
  (Input wired, Describe on; see "Describe mode and Input").
- Second atlas `phrases` (1280x1280, eight rows, Barlow Condensed Bold, two rows red) on input 1.

## Channel to visual mapping

| Feed | Drives |
|---|---|
| `evolve` | camera travel down the nave (0.55 units per evolve unit), look sway, slow roll: never static |
| `bass_pitch` (held, lagged) | first fold angle, `0.16*sin(note*pi/6)`: each bass note re-tunes the lattice (same note in any octave = same building) |
| `pitch` (vocal, held, lagged) | second fold angle, `0.11*sin(note*pi/6)` |
| `bar_pulse` | cavities: nave half-width 0.72 -> 0.92 and every block shrinks 22 %, so gaps open on the bar line and close again |
| `hit_low` (via `ring`) | a pulse that leaves the camera and runs 14 units down the nave in 0.45 s: a thin pane of green light across the nave (a scan bar on every surface it crosses), the battens firing in sequence as it reaches them and dying away behind it, and a 10 % lurch wider of the lens |
| `hit_mid` | the red letters flare (they smoulder at a low level all the time) |
| `hit_high` | knocks a random 45 % of the battens out for the length of the hat; `beat_pos` re-deals which ones every half beat |
| `pulse` | all battens tick brighter on the beat |
| `energy` | batten level, fog colour and density, cold fill |
| `section` | jump cut of state: fold offsets (block proportions), camera roll bias and lane, which words sit where on the frieze, and **power**: about a third of the sections are a power cut (battens at 5 %), where the only light is the smouldering red lettering and whatever each kick fires |


## Takes (2026-11-10 evening: "too repetitive, needs more variety")

One shader, one folded lattice, seven ways of cutting into it and looking at it. `TAKES` in build.py is a table
(`takes` Table DAT in the scene); the row is `op('shot')['take'] % 7` and reaches the shader as the uniforms
`uTakeA..D` (architecture, camera, light, grade, fold bias, atlas, relief, speed, lens, fog, text scale, fold
iterations, block shrink). A cut changes numbers only; both text atlases are always loaded. `seed` re-rolls
everything listed after each take below. Contact sheet: `captures/takes_sheet.png` (plus `rb_sheet.png` on a kick,
`rc_sheet.png` on a snare, `arr_sheet.png` 0.12 s after a cut).

| Take | Name | What you see | Seed changes |
|---|---|---|---|
| 0 | nave | The original: flying down the arched corridor under fluorescent battens, steel frieze with the wall words, fluorescent green grade. About a fifth of shots are a power cut. | lane, roll, block proportions, frieze word order, power cut |
| 1 | block | Outside, daylight: a finite chunk of the lattice standing as a dark monolith on an endless cream sheet ruled and printed with the wall words; beige sky, soft sun shadow. | tower / slab / cube, orbit angle, distance (close to tiny-in-a-field), height, which side of frame |
| 2 | shaft | 1-bit black and white, ordered dither on doubled pixels: plunging down a square shaft lined with huge extruded phrase letters and square ring lights. No title word. | start roll, position in the shaft, block proportions |
| 3 | macro | Extreme close-up skimming sideways over a sliced plate: ink-blue and red letters (the phrase sheet) standing 3D off ivory tiles under a raking sun. Ink and ivory grade. No title word. | where on the plate, height, tilt, roll, direction of travel, sun start angle |
| 4 | rotunda | Inside a sphere carved out of a more strongly folded lattice, a glowing amber orb at the centre throwing radial shadows over a dome of wall words; amber on black. | orbit angle, eye height, orb left or right of frame, or lying on the floor looking straight up |
| 5 | cut | Orthographic, square onto a diagonal slice through the lattice: the cut face is flat warning red with the phrase sheet knocked out in white; white clay lit by ambient occlusion only shows through the holes. Full-frame poster. No title word. | cut direction (three), in-plane rotation, depth of cut, zoom 2 to 5 units, pan |
| 6 | strafe | Emergency lighting, red monochrome: travelling sideways along the nave wall like a train window, one phrase at a time passing on the frieze, alternate battens strobing. No title word. | which wall, eye height, how far the camera looks ahead, tilt, roll, phrase order |

Takes that do not show wall row 0 (the title word): 2, 3, 5, 6 (phrase atlas). Takes 1 and 4 carry it only as one of four small
repeated words; take 0 has it on the frieze, in perspective and off-centre.

**First half second of a shot** (`uShot.w` = 1 at the cut falling to 0 at 0.5 s): every take starts on a wider lens
and 2.4x hot and settles; nave/shaft/strafe rush 0.9 units forward and their tubes strike one after another away
from the camera; the block swings 40 degrees into place; macro letters rise out of the flat plate; the orb ignites;
the cut starts zoomed in and 0.8 units deeper and pulls back.

**Music per take** (on top of the shared mapping below): kick pulse is a pane down the nave/shaft (0, 2, 6), an
expanding green shell (1, 4), a yellow scan bar across the plate (3), a ring spreading over the section plus the
cut jumping 0.22 units deeper and easing back (5). Snare: red letters flare (0, 1, 3, 4, 6), the whole frame flips
to its negative (2), the red section heats to orange (5). Hats: battens knocked out (0), dimmed (6), random lattice
cells flash (1, 3, 4, 5). Beat: shaft snaps a quarter turn every 4 beats; the macro's raking sun turns once per
16 beats; strafe battens swap on every beat. Bass/vocal pitch still re-fold the lattice in every take.

## Words (2026-11-11)

- 2026-11-11: the words in build.py are generic defaults (`DEFAULTS`: four `ROWS` for the text wall, eight `PHRASES`
  for the condensed sheet, each `[text, is_red]`), read at build time through `LIB['scene_words']`. The words the
  scene was first made with live in a private pack's `scenes/sc_kifs_office/words.json` under the same two names;
  a build on that pack draws them instead. The counts are fixed at 4 and 8 (the shader reads that many rows).
  Captures, logs and the hero frame described below from before this date show the first words, not the defaults.
- Widths at build size, measured with the pack's fonts: wall rows 572 to 946 px of 1024 (110 px Archivo Black,
  not fitted), phrases 727 to 1220 px of 1280 (128 px Barlow Condensed, squeezed only if wider than the sheet).
- Checked on the generic pack: `captures/sheet_gen.png` (all seven takes, twelve shots), Describe on takes 0, 2, 5.

## Assets

The scene loads three font files and one shader, nothing else (no model, no picture, no data baked from either).
Every file parameter is an expression on `mod.paths`; build.py names no folder.

| Used | Where | With no assets folder |
|---|---|---|
| `<assets>/fonts/ArchivoBlack-Regular.ttf` | the four-row text wall and the four-row Describe sheets (takes 0, 1, 4) | the system face Impact (`STANDIN` in build.py), or TouchDesigner's default face where Impact is not installed |
| `<assets>/fonts/BarlowCondensed-Bold.ttf` | the eight-row phrase sheet and the eight-row Describe sheets (takes 2, 3, 5, 6) | the same |
| `<assets>/fonts/ChicagoFLF.ttf` | the shaft's Describe caption (`label2`) | TouchDesigner's default face (Verdana here), shrunk if a line would overrun the panel |
| `experiments/sc_kifs_office/shaders/kifs.frag` | the shader, `mod.paths.here('shaders/kifs.frag')` | always there (in the repository) |

Row sizes that were fitted at build time (`maxfrac`, the caption width) are measured with whatever face is loaded,
so the sheets fit with the stand-in too. Contact sheet of the scene with no assets: `captures/noassets_sheet.png`.

## Describe mode and Input (2026-11-11, for the public website)

**Describe** (COMP toggle). Each take has its own sheet of words that say what the picture is, built at build time
in the same shape as the atlas that take already uses (`DESCRIBE` in build.py, mirrored to preset.json `words`).
Two Switch TOPs (`wall_sw`, `phr_sw`) sit between the text walls and the shader and pick the take's sheet when
Describe is on; nothing is loaded at the toggle. What each take shows:

| Take | How it carries words | Words |
|---|---|---|
| 0 nave | frieze, whole words | RAY MARCHING / NO POLYGONS (red) / ONE SHADER; 80 STEPS MAX only as lattice fragments |
| 1 block | list printed on the floor, small on the block | FRACTAL BLOCK / SOFT SHADOW / FOLDED 3 TIMES / RAY MARCHED |
| 2 shaft | caption panel (Chicago, 1-bit, bottom left) | 1-BIT RAY MARCH / EACH DOT IS BLACK OR WHITE. / 4 BY 4 ORDERED DITHER, DOTS DOUBLED. / THE SNARE SWAPS BLACK AND WHITE. The wall letters (1-BIT, DITHER, RAY MARCH, BLACK WHITE, NO GREY) stay as unreadable giant fragments |
| 3 macro | two-word labels at 90 px, three to a row, so a whole label fits the window | RAISED TYPE / HEIGHT MAP / SIDE LIGHT / NO MESH / RAY MARCH / RAKING SUN / MACRO |
| 4 rotunda | small repeated words on the dome | CARVED SPHERE / ONE ORB LIGHT / FOLDED 4 TIMES / RAY MARCHED |
| 5 cut | one paragraph on the cut face, set once as a column the height of the frame | THIS IS NOT A 3D MODEL. ONE SHADER MEASURES THE DISTANCE TO A FOLDED BOX FOR EVERY PIXEL. THIS IS A FLAT SLICE THROUGH THAT FRACTAL. EACH KICK DRUM PUSHES THE SLICE DEEPER. |
| 6 strafe | one line at a time on the frieze | ONE SHADER. / NO POLYGONS. / UP TO 80 STEPS. / NOTES BEND WALLS. / KICK FIRES TUBES. / BEAT SWAPS LIGHTS. / TEXT IS THE WALL. / EMERGENCY RED. |

Five things exist only in Describe mode: the cut's paragraph is a single column fitted to the frame height and
placed off-centre by the seed (off, the phrase sheet tiles the face at the take's own scale); the block's floor list
is set 1.67 times larger; the shaft's caption (`label2` over the frame through `post_sw`; index 0 of
that switch is the shader untouched), smaller type on the strafe sheet (100 px, so a line fits the frame), and in
the block take the floor print is turned in quarter turns to face the camera (off, the scene's own floor words are upside
down from half the orbit, as before).

**Input** (COMP text parameter: a TOP path). `in_sel` (Select TOP) reads that TOP, or the black `in_blank` when the
parameter is blank, missing, not a TOP, or one of this scene's own TOPs; it is the shader's third input and
`uIn.x` says whether to use it. When it is on, the picture replaces both text walls everywhere the shader reads
them: its brightness is the emboss height (so the picture stands off the surface as relief and casts shadows) and
its colour is the paint. Per take: nave and strafe turn the frieze into a strip of film, one whole 16:9 frame
after another, faintly back-lit, with the lattice wallpapered in fragments; block prints it on the paper floor
(8 units a picture) and wraps the block; shaft lines the walls with it, dithered to 1 bit; macro skims over it
as a relief plate in a half ink-and-ivory duotone; rotunda tiles the dome with it under the orb; cut shows it flat
and in full colour on the cut face with the clay showing through the holes. Red parts of the picture take the
place of the red ink (they flare on the snare). Input wins over Describe: with a picture wired there are no words
except the shaft caption.

`ab_test.py` is the test that Describe off + Input blank is unchanged: it renders the committed 2026-11-10 shader
(`shaders/kifs_ref_2026-11-10.frag`) beside the live one in the same frame for all seven takes and returns the
largest pixel difference (0.0), and proves it can fail with Describe on and with Input on.

## Log (newest first)

### Sixth pass (portability), 2026-11-11

Where the scene finds files changed; what it draws did not.

- build.py and the helpers name no folder: the repository is `td.project.folder`, fonts are
  `mod.paths.font('archivo' / 'barlow' / 'chicago')` expressions, the shader is `mod.paths.here(...)`.
  ab_test.py, rebuild.py and take_shot.py read from `project.folder`; sheet.py finds `captures/` from its own location.
- Proof that nothing drawn changed: the ten text sheets (`wall`, `phrases`, `d0..d6`, `label2`) were saved as arrays
  before the change and compared after each rebuild with assets: largest difference 0.000000 on all ten. ab_test
  PASS (0.000000 on seven takes; 0.88 with Describe on, 0.86 with Input on). **p0_sheet.png** (before),
  **p1_sheet.png**, **port_sheet.png** (after the last rebuild; includes Describe on the shaft and the test card
  as Input on the nave): the same seven pictures at different moments of the track.
- With the COMP's `Assets` parameter on an empty folder: tdh.errors empty, all seven takes drawn and cooking.
  First try (**na_sheet.png**) used TouchDesigner's default face: thin strokes, weak relief (the Text TOP's Bold
  toggle did nothing to Verdana or Arial here). Second (**nb_take_0..6, nb_desc_*, nb_in_* / noassets_sheet.png**)
  names Impact as the stand-in: heavy, condensed, close to the real picture.
- Weak with no assets: one face does the work of two, so the wall takes and the phrase takes lose their contrast
  of wide and condensed type; an eleven-letter word in Impact fills 60 % of its row where Archivo Black fills it, so the frieze
  words are smaller with more bare steel; the shaft caption is in a plain face, not the bitmap one.
  Impact was only seen on this Windows machine; a machine without it gets the thin default face of na_sheet.png.

### Fifth pass (Describe and Input finished by a second agent), 2026-11-11

The fourth-pass agent was cut off; everything below was re-checked from a rebuild, not taken on trust.

- Rebuild from build.py, then ab_test: PASS, max difference 0.000000 on all seven takes against the committed
  2026-11-10 shader (0.87 with Describe on, 0.86 with Input on, so the test can fail). **x_off_sheet.png** beside
  takes_sheet.png: the same seven pictures.
- **x_desc_*.png**: the fourth pass's Describe as found. Three takes were weak: the cut showed "FOR EVERY PIXEL /
  HIS IS A FLAT SLI / OUGH THAT / K DRUM PUSHES" (a quarter of the paragraph, starting anywhere); the macro showed
  one word ("HEIGHT", "RAISE"); the block's floor list was about 12 px high.
- Fixed, all in Describe-only branches: cut paragraph as one column fitted to the frame (**y_d5a/b/c.png**, three
  seeds, all eight lines in frame every time); macro labels at 90 px, three to a row (**y_d3a/b/c.png**: "RAISED
  TYPE" and "HEIGHT MAP" whole at all three camera heights); floor list 1.67x (**y_d1a/b.png**).
- "CAST SHADOW" removed from the macro words: the soft shadow marches the lattice without the lettering, so the
  letters shade their own sides but cast nothing. Replaced with SIDE LIGHT.
- Input: the shaft with a dark picture was a black frame with a few letters (**x_in_2.png**). In the 1-bit take
  the picture is now tone on steel rather than the only paint, so the shaft stays visible (**in_take_2.png**).
  The other six were left as the fourth pass built them.
- Input edge cases checked by setting the parameter: a path that does not exist, this scene's own out1, and a CHOP
  all fall back to `in_blank` with uIn.x = 0; the test card gives uIn.x = 1.
- Toggling Describe and changing take recooked none of the sheets (totalCooks of d0..d6, label2, wall, phrases
  unchanged), so the toggle loads nothing.
- Final set after the last clean rebuild (t=179.2, section 30; seeds 0.3 0.3 0.8 0.9 0.3 0.3 0.7):
  **desc_take_0..6 / describe_sheet.png**, **in_take_0..6 / input_sheet.png**, **in_b_take_0,1,5,6 / in_b_sheet.png**
  (other seeds), **final_take_0..6 / final_sheet.png** (Describe off, Input blank). Read on screen in Describe:
  0 "RAY MARC(HING)" and "(N)O POLYGONS" on the frieze; 1 "FRACTAL BLOCK / RAY MARCHED / FOLDED 3 TIMES / SOFT
  SHADOW" on the floor; 2 the caption, whole; 3 "RAISED TY(PE)" over "MAP HEIGHT"; 4 "RAY MARCHED", "CARVED",
  "FOLDED" round the dome; 5 "NOT A 3D MODE / ER MEASURES TH / TO A ..DED / ..VERY PIXEL / ..S IS A FLAT SL /
  THROUGH THAT / EACH KICK DRU / THE SLICE D..ER" (the lattice was holey at that moment); 6 "NOTES BEND WALLS."
- tdh.errors empty. tdh.check: first run pending (first samples), second run PASS (cook_budget 8.5 ms with other
  scenes cooking; GLSL TOP gpuCookTime 1.2 to 3.2 ms across takes, single readings of 13 ms are contention).

Weak, honestly (this pass):
- Cut (5): the paragraph is always whole in the frame now, but the holes of the cut still eat letters; how many
  depends on the fold at that moment (y_d5a reads nearly clean, desc_take_5 loses about a third of the letters).
- Rotunda (4) and the nave's lattice lettering are still fragments; only the nave frieze reads whole.
- Nave (0) and rotunda (4) name the technique but do not explain it; the explaining is in takes 2, 5 and 6.
- Still only stills, still only the test card as Input.

### Fourth pass (Describe and Input), 2026-11-11

- Rebuilt unchanged on the new scaffold first: **s1_take0..6 / s1_sheet.png** (t=53.9, seed 0.3): the seven takes
  as before (take 0 happened to be a power cut).
- **desc_take_0..6.png / describe_sheet.png** (t=240, section 40; seeds 0.3 0.3 0.8 0.1 0.3 0.3 0.7): final
  Describe captures after the last clean rebuild. Read on screen: take 0 "RAY MARC(HING)" and "(NO POLY)GONS" on
  the frieze; take 1 the floor list, small; take 2 the caption, whole; take 3 "(RAISED) TYPE RAISE(D)" / "MAP HEIG(HT)";
  take 4 "RAY MARCHED", "CARVED SPHERE" round the dome; take 5 "(FOR EVERY) PIXEL / (FLAT) SLICE / FRACTAL. /
  (KICK DRU)M PUSHES"; take 6 "BEAT SWAPS LIGHTS." whole, "UP TO 80 STEPS" below it.
- **in_take_0..6.png / input_sheet.png**: the same seven with Input = /project1/sw_testcard/out1. TEST INPUT is
  readable in all seven and looks different in each.
- **final_take_0..6.png / final_sheet.png**: Describe off, Input blank, same frame. ab_test PASS (max difference
  0.000000 on every take; 0.85 with Describe on, 0.86 with Input on). checks: first run fails `moving` (cooks -507)
  and cook_budget (31 ms, the rebuild); second run PASS (cook_budget 2.8 ms). GLSL TOP gpuCookTime 2.4-2.6 ms on the
  nave with or without an input.
- **d1_take0..6.png**: first Describe words. Long sentences failed in the macro ("NS IN 16 B" was all that fitted),
  rows set to fill the sheet ran into their own repeats on the floor and dome ("TIMESFOLDED"), and the shaft showed
  no readable letter at all. Fixes: short labels repeated across the row (macro), a margin kept on every Describe row
  (`maxfrac`), a caption for the shaft. 96 px type in the shaft (**d3_t2a/b.png**) was no more legible than 128, so
  the shaft sheet stays at 128.
- **d3_t6a/b.png**: strafe lines shortened and set at 100 px so a whole line sits in the frame ("TEXT IS THE WALL.",
  "NO POLYGONS."); at 128 px the frame held "A CORRIDOR FROM ONE SHADE".
- **e_t1a..d / e_sheet.png**: block floor print facing the camera from four orbit angles. Before, desc_take_1 showed
  it upside down.
- The first caption read "EUERY PIXEL" and "NEGATIUE": Chicago at 24 px draws V like U. Reworded without V or X.
- **in1_sheet.png, in2_take*.png**: first Input pass. The frieze showed the picture's relief but no colour: the
  frieze's `tick` term is 1 across the whole panel (it is the raised panel, not a tick), so the line that blanked
  the colour on the ruled lines blanked it everywhere. Removed. Floor picture enlarged from 4 to 8 units and turned
  to face the camera.
- Trap: the session scratchpad is shared between the agents of one workflow. A patch script saved there under a
  plain name (patch3.py) was overwritten by another agent before it ran. Use a folder of your own.

Weak, honestly:
- Shaft (2): its own lettering is still unreadable in Describe mode; the caption does all the explaining and it
  does not flip with the snare negative.
- (Fixed in the fifth pass: cut paragraph cropped by close zooms; block floor words 12 px high.)
- Nave (0): "80 STEPS MAX" never appears on the frieze (the frieze uses rows 0-2), only as broken lattice lettering.
- Strafe (6) between strobes and nave in a power cut are dark; the frieze words are there but dim.
- Input: on the lattice (as against the frieze, floor and cut face) the picture is fragments, as the text was.
  Macro (3) with a dark picture is a dark frame (the shaft had the same fault; fixed in the fifth pass). Input and Describe together show no words (except the shaft caption).
  The Select TOP reads the other scene's out1, so that scene cooks while this one is on screen.
- Describe and Input were looked at as stills only, with the test picture only; no real scene has been fed in yet,
  and the cost of the first Describe cut after loading the .tox (the sheets cook once) was not measured.

### Third pass (takes), 2026-11-10 evening

Starting point (v2_before_a/c.png, t=45 and 50): the same corridor both times, differing only in fold and lane.
build.py rebuilt cleanly on the new scaffold unchanged (Take/Seed/Shotstart + `shot` CHOP appeared).

- **take_0..6.png, takes_sheet.png** (t=154, section 26, bar_pulse 0.82, hit_high 0.62, folds 0.09/0.10): final clean
  rebuild from build.py, one capture per take. Seven pictures that do not share a palette, a camera or a subject.
  **hero.png = take_5.png**. checks: first run fails `moving` (stale sample, cooks -44), second run PASS.
- **rb_take0..6 / rb_sheet.png** (t=113.2, ring 0.59): all takes in the same frame of one kick. Pane mid-nave (0),
  green shell on the monolith (1), yellow scan bar top right of the plate (3), pink ring on the section (5).
- **rc_take0..6 / rc_sheet.png** (t=123.1, hit_mid 0.95, fold -0.09): same on a snare. Shaft is in negative, red
  letters hot in 0/1/3, section orange in 5. Captured with take_shot.py (one-shot Execute DAT on a feed condition).
- **arr_take0..6 / arr_sheet.png**: 0.12 s after a cut. Nave is still dark (tubes not struck yet), macro is bare tiles
  with no letters yet, cut is zoomed in.
- **w5_take2_0..2.png**: shaft fixed by dropping to 2 fold iterations and doubling the text size: big flat faces
  and whole letters instead of dither soup (ra_take2.png is the soup).
- **w4_take1_0..2.png**: block take with the new `shrink` column (0.22): gaps open between the blocks, so it reads
  as stacked cabinets with streets instead of a solid lump (w3_take1.png is the lump).
- **w2_take5_0/1.png**: cut face painted red with white type. Before (w1_take5.png) it was white clay on white
  clay under AO-only light, where embossed white letters are invisible. The (1,1,0) cut direction was dropped:
  walls parallel to the view smear.
- **w2_take3_0/1.png**: macro at 2 fold iterations. At 4 (w1_take3.png) the slice was a grid of small tiles and
  holes with no face big enough to carry a letter.
- **w1_sheet.png**: first sight of all seven, straight from the first compile.
- Cost per take, GLSL TOP gpuCookTime averaged over 16 frames each (max in brackets), other scenes cooking:
  nave 2.5 (2.9), block 1.7 (2.0), shaft 1.5 (1.9), macro 1.0 (1.2), rotunda 1.8 (2.3), cut 1.5 (1.9),
  strafe 2.5 (2.8) ms; cpuCookTime 0.13 ms. Still 64 + 16 march steps. Measured on the final
  shader and table, one rebuild before the last.

Weak, honestly:
- Seen only as stills. The arrival moves, the quarter-turn snap, the strobe and the 1-bit negative flip have not
  been watched in motion; the flip on every snare may be too much.
- Rotunda (4) is the busiest and least legible take and at a glance its seeds look alike apart from where the orb
  sits; the grey lens-shaped voids in it are unexplained.
- The clay in the cut take is soft and a little smeared on surfaces nearly parallel to the view.
- Macro letters have stair-stepped sides (relief 2.5x on a 16-step refine), visible in w2_take3_1.png.
- Nave and strafe share an architecture; the difference is camera, text and colour, not space.
- Take 0 in a power cut and take 6 between strobes are both very dark frames.
- In the 1-bit shaft, exposure depends on fixed thresholds; a quiet passage may go mostly black.

### Second pass (art director), 2026-11-10

What I saw first (ad_01..ad_06, t=124-215, sections 21-37): not the dark cathedral the first log describes. An evenly
lit olive-grey brick tunnel, no real blacks, two blown white blobs for tubes (they ran along the view axis, so they
foreshortened to dots), lettering mostly as fragments (only the red row on the floor read nearly whole), and two frames
0.2 s apart across a kick (ad_03 ring 0.52, ad_04 ring 0.07) that were almost the same picture. The text wall itself
was wrong: `wall_comp` showed only four of the six rows, cut off at the tile edges.

- **ad_30_rebuild_a.png / ad_31_rebuild_b.png** (t=197 section 33 lit; t=208 section 36 power cut, ring 0.48): final
  clean rebuild from build.py. Both states reproduce. checks: first run fails only `moving` (stale sample, cooks -202),
  second run PASS.
- **hero.png = ad_25_cut_kick.png** (t=177.6, ring 0.78, section uniform forced to 3 for the shot to see a power cut):
  dark nave, the kick's pane of light a third of the way down, only the battens it has passed are lit, the title word
  whole on both friezes, red letters glowing on the floor. **ad_26_cut_rest.png** is the same state between kicks:
  near-black with red lettering only. Never fully black.
- **ad_20_kick_start / ad_21_kick_mid / ad_22_kick_late / ad_23_cut_kick** (ring 1.0, 0.59, 0.30, 0.78): the kick in
  a lit section. Near battens flare at the start, the pane is visible mid-nave in ad_23, the far battens are the
  bright ones late. Captured with `ad_shot.py` (one-shot Execute DAT armed on a feed condition).
- **ad_13.png** (ring 0.96): first try of the kick was a pale green whiteout of the whole frame, because every ray
  starts inside the pane at the moment of the kick. Fixed: the volumetric part fades in over the first 30 % of the
  travel and is half as strong; batten boost 2.6 -> 1.9.
- **ad_12.png**: text wall rebuilt (one Text TOP per row, Layout TOP). First whole words on the frieze.
- **ad_11.png**: battens turned across the nave: they now read as tubes receding into the distance. Text tiny because
  the Text TOP's font size unit defaults to points; set `fontsizexunit='pixels'`. Layout TOP `fit` defaults to
  `fitbest`, which squeezed each 1024x256 row into a square cell; `fill` is right.
- **ad_10.png**: new lighting, frieze, kick pulse, power-cut sections. Old six-row wall still in, so the frieze showed
  the wrong rows.
- Dropped: the old camera-carried lamp at 0.55 and the 0.16 ambient (they were what flattened the picture); the
  single along-the-nave tube per 4-unit cell.

### First build

- **09_rebuild_a.png / 09_rebuild_b.png / hero.png** (t=55.5 and 61.8, section 9): final clean rebuild from build.py.
  Clean tiled Menger vault (folds near 0 right after the rebuild because no bass note had sounded yet), tubes, legible
  red sign lettering on the floor slab. checks PASS on the second run.
- **08_final_a.png** (t=44.3, ring 0.78, folds 0.15/-0.08): kick just fired; the near half of the frame is washed pale
  green. Too much whiteout, so the volumetric part of the ring was cut again (0.5 -> 0.3) and faded in over the first
  third of its travel. With folds this large the tiles smear into melted panels and the lettering breaks up.
- **08_final_b.png** (t=47.5, section 8, folds 0.01/-0.10): dark blue cavern with lit vault, red lettering readable.
- **07_ring_0/1/2.png** (t=25.6-25.8, one kick, ring 0.89 -> 0.67 -> 0.44): the pale-green wash starts on the camera
  and by the third frame sits as a glow far down the nave. This is the proof the ring travels.
- **06_a/b/c.png** (t=1.6, 11.1, 16.5; folds -0.06, 0.07, -0.16): split-tone grade added. 06_a is a clean square
  lattice, 06_c has skewed, windowed walls: the bass fold visibly re-shapes the building.
- **05_snare_red2.png** (hit_mid 0.90): red letters glow hot red-orange. Before this (04_snare_red.png, hit_mid 1.0)
  the glow tone-mapped to salmon pink; fixed with a more saturated emissive colour and a clamp.
- **04_snare_red.png** also shows bar_pulse = 1: thinner tiles, wider nave.
- **03_ring.png**: first sight of the kick light, a white bloom filling the far nave. Trap found on the way: the
  Trigger CHOP's `threshold` parameter is a toggle; the levels are `threshup`/`threshdown`. With those at 0 it never fired.
- **02_arch_tubes.png**: pointed-arch nave, fluorescent tubes, inverse-square light, ACES curve, text mirror signs
  fixed. Big step up from step 1: dark cavern, bright tubes, the red row readable.
- Step 1 (viewed with get_top_image, no file kept): round tunnel of grey tiles, fragments of mirrored letters, flat
  grey fog. Worked first time but dull: no contrast, text back to front on two of three axes, Reinhard washing it out.

## Honest weak points

- Still only seen as stills (about 20 this pass), never in motion. The kick pulse is verified at ring 1.0, 0.78, 0.59,
  0.48, 0.30 in different kicks, not as one sequence.
- Near the camera the frieze is a large plain steel panel; at some roll angles it fills a quarter of the frame with
  little on it but one word.
- Which sections are power cuts is a hash of the section index, not a reading of the music; several dark sections
  can come in a row. A Python copy of the hash did not agree with the GPU's, so the exact list is unknown
  (seen dark: 3, 36).
- The lattice lettering (triplanar) still fragments at large fold angles and doubles on oblique faces; the frieze is
  what carries legibility now.
- `bass_pitch` read 0 in every sample I took (t=21-215), so the first fold angle only moved when a held note changed;
  the vocal fold is the one I saw change (0.02 to 0.11).
- Distant text shimmers a little (mip level from ray distance only).
- Cost: GLSL TOP gpuCookTime 1.04-1.38 ms, cpuCookTime 0.1 ms by TouchDesigner's counters; tdh cook_budget 0.9 and
  6.4 ms on two runs with other scenes cooking. Not cross-checked against frame rate.
- Section jump cuts change lane and block proportions; not checked in all 43 sections (seen this pass: 3, 10, 16,
  20, 24, 25, 28-30, 33, 36).

## Next

- Watch a recording of the cutter going through all seven takes; tune the arrivals and the snare flip from that.
- A library model as a ray-marched silhouette is still the missing subject: every take is letters and blocks.
- Give the rotunda a clear second subject (a doorway, a ring of tubes) so its seeds differ more.
- Tie the power cut to the music (low `energy`, or the bar before a drop) instead of a hash.
- Detail on the frieze near the camera: small serial numbers, rivets, a second line of small type.
- One sequence of four frames through a single kick to confirm the pulse reads as travel.
