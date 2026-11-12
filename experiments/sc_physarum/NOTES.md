# sc_physarum: slime mould

## Intent
A living network of veins that finds a subject, traces it, and abandons it when the music moves on.
230,400 Physarum agents live in a float texture; they smell a trail map and an attractant map (a phrase, the
X-ray of a turning 3D model, the printed lines of a sheet), steer toward the strongest smell, walk and leave
trail. It works when (a) the veins visibly organise around the attractant within the first second of a shot,
(b) the network visibly changes species with the stems (lace, arteries, rings), and (c) every take reads as a
physical thing (film on a lightbox, gold in marble, mould on paper), never as a data map.

## Technique
- Modes added by `uExtra` (drift heading, re-condense share) and kick mode 4 (blown off in place); see Takes.
- `agents` (GLSL TOP, 480x480 rgba32float, closed by `fb_a`): one texel per agent, xy position, z heading,
  w ballistic timer. Three sensors read `trail + gain * attractant - wall`; classic Jones turn rule.
  Spawn modes (uniform, on the attractant by rejection sampling, ring, burst from the subject, blots, frame
  edges, horizontal sheets) are used at the cut, on kicks and on section changes.
- `deposit_r` (Render TOP, additive GLSL MAT `deposit`): a 480x480 point grid whose vertex shader moves each
  point to its agent's pixel. r counts walking agents, g counts agents in ballistic flight.
- `trail` (GLSL TOP 1280x720 rgba16float, closed by `fb_t`): 3x3 diffuse, decay (slower on the attractant),
  add deposit. g keeps a slow memory (stain), b the flight glow.
- `amap` (GLSL TOP): the attractant for the take: slow noise, a Text TOP (`txt`, phrases from `words_json` through `textlib`), an
  additive rim-light "X-ray" render of one of six library models (`model_r`), a printed sheet's ink, or a tiling
  grid of culture dishes with walls.
- `shade` (GLSL TOP): eight looks and a view transform (zoom, rotation, pan, or a tilted perspective plane).
- `events` (Execute DAT, events.py) turns hub counters into one-frame events in the `ev` CHOP: boot (scene
  was off, or Take/Seed/Shotstart changed), kick, section change, and a decaying snare envelope `flip`.

## Takes (TAKES in build.py, played in ORDER; `take % 11`)
Three modes of the technique now, not one: vein network (0, 2, 4, 6, 7, 8, 9, 10), directional flow (1),
bare grains with no trail (3), and a mirrored blot (5).
0. xray: big prop off-centre (seed picks prop and side), fine lace, blue film on a lightbox. `take_0.png`
1. bleed: FLOW. A phrase at the top of a coloured sheet; its ink runs down in rivulets that merge (agents pulled
   toward "down", re-spawn on the letters when they leave the frame). Seed: pink + navy or goldenrod + red, slant. `take_1.png`
2. marble: no subject; gold veins in black marble as an endless floor at a low angle, camera travels. `take_2.png`
3. toner: GRAINS. No trail at all: the 230k agents drawn as toner specks on copier glass, packed onto a block of
   phrases; a scan bar crosses once per bar. Seed: zoom 1x to 2.6x, skew, and whether the snare prints a negative. `take_3.png`
4. dishes: many subjects, red cultures in walled petri dishes on a light table; seed picks 4x2 / 5x3 / 7x4. `take_4.png`
5. blot: MIRROR. A folded inkblot on a card on a green blotter; one half of the map printed twice. Seed: red or
   black ink, card angle; section changes the blot. `take_5.png` (hero)
6. sheet: top-down on a printed sheet (seed picks sheet, angle, crop); teal mould follows the printed lines. `take_6.png`
7. onebit: a word fragment bigger than the frame, 2 px 1-bit dither; seed picks polarity. `take_7.png`
8. poster: tiny yellow prop in a navy field, colony bursts out of it; three flat screenprint inks. `take_8.png`
9. crt: wall of Chicago text on a curved green CRT in a beige bezel, eaten into bone letters. `take_9.png`
10. rust: 3x macro, rust under blistering putty paint; letter strokes cross the frame. `take_10.png`
Contact sheets: `captures/sheet_takes.png` (5 s into each shot), `sheet_takes_2s.png`, `sheet_takes_arrival.png` (0.4 s).

## Channel to visual
- `bass` (lagged): sensor distance, so mesh size (thicker, sparser arteries when the bass is in).
- `vocals`: sensor angle (wider = more cellular). `other`: turn rate. `energy`, `drums`: step length (speed).
- `section`: new phrase / prop / printed sheet (the veins abandon the old one and re-find the new), a share of
  agents re-spawn on it, and the breed steps through lace / normal / artery (sensor distance x0.6, 1, 1.7).
- `hits_low` (kick, exactly once each): a share of agents re-scatters: flying rings (xray, marble, sheet, crt),
  dust (onebit), back onto the food (dishes, rust, bleed), a burst from the subject (poster, blot), blown off
  in place (toner). `hit_low` also flashes the light in marble
  and rust and widens the misregistration in the poster.
- `hits_mid` (snare): attract flips to repel for about 0.3 s (strength per take, `flipk`); the 1-bit take
  goes negative, the film goes warm.
- toner: `beat_pos` moves the scan bar (one pass per bar), `hit_low` flashes the glass, snare loosens the
  grains (and prints a negative when seed > 0.5). blot: `pulse` swells the ink mass. bleed: kick glints the wet ink.
- `pulse`: brightness pump. `hit_high`: tube buzz (sheet, dishes). `beat_pos`: scan bar on the film.
  `evolve`: prop rotation, light direction, camera travel over the marble floor, CRT hum bar.
- `shot.age`: tube flicker-on (xray), light flash (marble), negative flash (1-bit); the spawn mode itself is
  the arrival in the others (blots, sheets, burst).

## Words and models (2026-11-11)
Everything a pack may replace sits in `DEFAULTS` at the top of build.py and is read once, at build time, through
`LIB['scene_words']`: `PHRASES`, `FRAGMENTS`, `STANDIN_SHEETS`, `PROPS` (rows: model, scale, tilt, lift) and
`SHEETS` (rows: model, invert, white). A pack's `scenes/sc_physarum/words.json` gives its own values under the
same names. build.py writes the three word lists to the DAT `words_json`; `textlib.text/sheet` are handed its text.

## Assets (2026-11-11)
Nothing here names a folder: every file parameter is an expression on `mod.paths` (the scaffold's
`local/modules/paths`), and build.py finds the repository from `td.project.folder`. No precomputed data: nothing
is baked from a model or a font, so nothing was added to this folder.

| Used from `<assets>/` | Where | With no assets |
|---|---|---|
| `models/<the six PROPS>/model.obj` (gramophone, astrolabe, marble_bust, lander, hourglass, wire_cage) | X-ray prop (xray, poster) | TouchDesigner's bundled teapot in all six slots; each geo's `fit` Transform POP scales and centres it to the library's convention and holds it at a different tilt per slot |
| `models/<the three SHEETS>/basecolor.png` (star_chart, blueprint, ticket) | the sheet in the sheet take; a row with invert or white set gets a Level TOP `ink_<model>` (the blueprint is white on blue, and the mould eats dark ink) | `ssheet`, a Text TOP that types out one of three stand-in sheets (`textlib.sheet`) on cream paper; the `sheet` switch picks it, so the empty Movie File In TOPs never cook |
| `fonts/ArchivoBlack-Regular.ttf`, `ChicagoFLF.ttf`, `BarlowCondensed-Bold.ttf` | `txt`, `label`, `dsheet`, `ssheet` | TouchDesigner's default face |

Not used: art, music, feeds (the hub's feed arrives through the `hub` CHOP).

## Describe and Input (2026-11-11)
- `Describe`: every take's words live in its TAKES row (`describe` = words that replace the phrases in the
  `txt` Text TOP, `label` = a caption card composited bottom-left/right by `label` -> `cap` -> `fin`). build.py
  writes them to the DAT `describe_json`; `textlib.words/label` read it, so the toggle is only an expression
  switch (no rebuild, nothing baked). The sheet take prints its words on a blank sheet (`dsheet`, 4th input of
  the `sheet` switch). shade.frag `uView2.w` = Describe: the three long-text takes keep their print readable
  (toner: letters printed under the grains; sheet: ink drawn over the mould; crt: text lit, veins 40% dimmer).
- `Input`: `in_sel` (Select TOP) -> `src0` (Switch, replaces the text in amap's slot 0) and `uIn.x`. amap.frag
  `pic()` turns the picture into food: 0.40 brightness + 0.45 brighter-than-surroundings + 0.45 edges. It stands
  where the take's own food stood (text, prop, sheet ink, noise, island). `textlib.inp` returns '' for a blank,
  missing or non-TOP path and for anything inside this scene, so the scene cannot read itself.
- Mirrored in preset.json: `words` per take (text words first, caption last), `accepts_input`, `as_processor`.

## Log
Newest first. 2026-11-10 unless dated. Entries before the generic-defaults one use the names of that time
(the take `form`, the operators `form`, `dform`, `sform`).
- 2026-11-11, generic defaults. The phrases, fragments, stand-in sheets, the six X-ray models and the three
  printed sheets are now `DEFAULTS` in build.py and are generic (real-time picture-making and a catalogue of
  unexplained objects; models and sheets from the pack that ships with the repository). The originals live in a
  private pack's `scenes/sc_physarum/words.json`, so that pack builds the scene as it was. The take `form` is
  now `sheet` (operators `sheet`, `dsheet`, `ssheet`); textlib.py holds no words.
  - Before, private pack: `before_<take>_a.png` (seed 0.23), `_b` (0.71). Generic: `g1_*` (all takes),
    `g2_*`, `g3_*`, `g4_*` (every model, every sheet, Describe on xray / crt / sheet).
  - Tall models were cut off top and bottom at the take's scale, so each PROPS row carries its own scale.
    The blueprint is white lines on blue: without `invert` the whole sheet was ink.
  - Weak: the wire cage reads as a lattice only at some angles (seen from above it is a ring of light); on the
    star chart the mould was still four separate blots 4.3 s into the shot (`g2_6_2.png`). Sections changed
    every few seconds while these were shot, so several X-ray stills hold the ghost of the previous model.
  - tdh.check on the generic pack: fail 42.7 ms (other agents building), then PASS 2.38 ms.
- 2026-11-11, portability. build.py and the helper scripts name no folder; file parameters are `mod.paths`
  expressions. Same seed (0.23) and delay (4.5 s) throughout, 11 takes each time.
  - Before: `ref_0,1,6,9.png` (`sheet_ref.png`). Converted, real assets: `pa_0..10.png`
    (`sheet_portable_assets.png`), and again after the no-assets trial: `pb_0..10.png` (`sheet_portable_back.png`).
    Same looks as `sheet_final_off.png`; phrases and props differ only because the section differs.
  - Assets parameter pointed at the empty `captures/_noassets`, rebuilt: `na_0..10.png` (`sheet_noassets.png`),
    no errors. Describe on (crt) and Input set (xray): `na_desc_9.png`, `na_input_0.png`; with assets
    `pb_desc_9.png`, `pb_input_0.png`.
  - tdh.check after the last rebuild: pending, fail 47.5 ms (model loads counted), PASS 3.08 ms with 17 other
    agents building. `tests/test_portable.py -k sc_physarum`: failed before (12 hits), 1 passed after the tox
    and snapshot were rewritten. Tox saved with Assets blank, Describe off, Input blank, Preview off.
  - Weak with no assets: one prop instead of six (the teapot, told apart only by its tilt); the default face is a
    light sans, so the bleed and rust takes lose their heavy letters and the 1-bit and CRT takes lose Chicago; the
    stand-in forms are typed text and dotted rules, not a designed sheet with boxes.
- 2026-11-11, Describe and Input (finishing a pass another agent started and was cut off in: its build.py,
  amap.frag and textlib.py edits were sound and are kept; nothing of it had been verified or logged).
  - Rebuilt on the new scaffold, Describe off / Input blank, all 11 takes at seed 0.23: `sheet_b1_off.png`,
    and again at the end: `sheet_final_off.png` (`final_off_0..10.png`). Same looks as `sheet_takes.png`.
  - Describe, first look `sheet_d1.png`: caption cards fine, but the three long texts did not read: toner was
    grey-on-grey after a kick, the form's sentences were buried under mould, and the CRT's Chicago letters
    were traced into wobbly veins ("NODODY ORLW TIESOUEINS"). Fixed in shade.frag with `uView2.w` (above):
    `sheet_d2.png`, `sheet_d2b.png`. Final, every take: `desc_0..10.png`, `sheet_describe.png`.
  - Input with /project1/sw_testcard/out1, all takes: `sheet_i1.png`. A bright figure on a bright ground (white
    type on the lit disc) was uniform food, so onebit, marble and dishes showed only mesh. Added the
    brighter-than-surroundings term to `pic()`: `sheet_i2.png` (onebit now reads INPU). Final six:
    `input_0,1,3,6,7,9.png`, `sheet_input.png`.
  - Weak: see "Weak or unverified" (first four bullets).
- Second builder pass (art direction). Judged all 8 original takes at 0.33 s, 2 s and 5 s with fresh seeds: all
  eight differ at a glance and none went black or white, but six of them settle into the same closed-cell
  mesh after about 4 s, so the scene had one mode in eight costumes. Added three takes that use the agents
  differently and re-ordered the list so neighbours are unlike:
  - bleed: agents.frag `uExtra.x/y` pulls headings toward one direction; leaving the frame re-spawns on the shape.
    First try (sd 7, doff 0.972) filled the whole pink sheet with navy streaks and buried the phrase; sd 13,
    doff 0.955 and spawning with the drift heading gave separate drips. `sheet_takes*.png` column 2.
  - blot: amap mode 5 (noise island, wall outside), shade mirrors p.x. Worked first time.
  - toner: trail.frag now writes this frame's agent count to alpha; shade draws that. With any deposit at all
    (0.04, then 0.004) the grains collapse onto the letters' centre lines within 3 s; dep 0.0 keeps letters
    filled. Kicks blow grains off in place (kick mode 4), strays re-condense 6% per frame (`uExtra.z`).
    `sheet_toner_kick_snare.png`: 16 frames over 1.3 s, a weak kick (0.25) then a snare: letters soften, then
    dissolve to dust while the snare envelope is up. The kick alone was small in that capture.
  - X-ray flight glow halved and made blue (was a white disc), CRT flight glow made phosphor green (was grey).
  - onShape() rejection tries 10 -> 24 (fewer strays).
  Final rebuild then all 11 takes shot back to back: `take_0..10.png`. tdh.check: fail 18.4 ms (GLSL TOPs
  reading 4-5 ms CPU each, i.e. contention), then PASS 1.78 ms. GPU sum of the scene's operators 0.58-0.60 ms.
- Final rebuild from build.py, take 5 seed 0.23: `final_rebuild.png` (artery breed, bass 0.56; compare
  `take_5.png`, same take in a lace passage). tdh.check: fail 78 ms right after rebuild, fail 13.1 ms,
  then PASS at 1.75 ms. Tox, snapshot, hero (`hero.png` = take_5) written. Preview off.
- All eight takes captured 4.5 s into a shot: `take_0..7.png`, `sheet_takes.png`.
- Added the per-section breed, because in the passage I tested (t 205-224 s) bass was 0.006 and the species
  barely moved: `sheet_r4.png` (4 moments of marble and 1-bit; rings on kicks, scatter on a kick frame,
  fragment change on a section change are visible; mesh size is not).
- Poster take failed twice as "tiny subject in a big field": spawning everywhere, then rejection sampling on
  a small scent (10 tries is not enough for 3% of the frame) both filled the frame with an even net
  (`06_poster_240.png`, `sheet_r2.png`). Fixed by bursting every agent out of the subject's own position and
  giving the subject a wide scent to crawl back along: `sheet_r3.png` rows 2-3.
- X-ray went brown and blown out (`sheet_r2.png`): the snare tint was on half the time and agents piled on
  the prop. Tint cut to 0.3, deposit and boost lowered: `sheet_r3.png` row 1 (one prop's ghost at 0.25 s, traced
  by 1.5 s, replaced by the next prop at the section change).
- Rings rendered as filled white discs (`01_core.png`, `07_crt_240.png`): flying agents were leaving trail
  the whole way out. They now deposit only into the flight channel.
- First pass of all looks: `02_marble_*`, `03_form_*`, `04_onebit_*`, `05_dishes_240`, `07_crt_*`,
  `08_rust_240`. Marble stone used hash noise (faceted blocks) and a grey polish; replaced with simplex.
- Core mechanism, first build: veins formed on the first run. A lit prop was a uniform blob as attractant;
  an additive rim-light render (edges and overlapping parts bright) made the veins trace structure:
  `01_core.png`.

## Weak or unverified
- Describe, sheet take: mould still strikes through the printed sentences; lines 1 and 4 are partly covered by
  the blots at 4.5 s (`desc_6.png`). Readable with effort, not at a glance.
- Describe, dishes / rust / onebit: the big words are fragments by design (letters in dishes, strokes at 3x,
  a cropped word); only the caption card explains. Rust at some seeds shows no letter at all.
- Describe + Input together: the given picture replaces the text, so only takes with a caption card still
  carry words (toner, bleed, crt and sheet show none).
- Input: strong on xray, bleed, toner, sheet, crt; usable on onebit, poster, blot (half the picture, mirrored);
  marble (lost in the tilted floor), dishes (barely steers the cultures) and rust (3x crop) do not show a
  recognisable picture. Only the test card was tried, never another scene's out1; a dark, low-contrast input
  will give little food. The picture is only food and a ghost: its colours are never shown.
- Still only stills (sequences of stills for toner). Nobody has watched it in motion.
- Kick reaction is the weakest link in the network takes: fuzzy wreath rings (0, 2, 6, 9), small. Toner's kick
  puff was only captured at strength 0.25 and was slight; a strong kick was not caught. Bleed's kick (45% of
  agents back onto the letters) was not isolated at all. Blot spatter is small.
- The six older network takes still converge on a similar closed-cell mesh after 4-5 s; in shots over 5 s
  xray, sheet and onebit lose their subject under it.
- Bass was 0.01 in every passage either builder captured (t 163-224 s), so bass -> mesh size is unseen.
- Dishes show stray letter shapes in some dishes (text is half-strength food there); intended, not tuned.
- Bleed puts a readable phrase large at the top of frame: closest thing here to "a slogan in the frame".
- Simulation speed is per cooked frame, so everything converges more slowly when the instance drops frames.
- Cook cost under load unknown: CPU reads 4-5 ms per GLSL TOP during contention, 0.1 ms when quiet.
- build.py (the scaffold) leaves Preview on after a rebuild; turn it off by hand. The tox has it off.

## Next
- Two sim steps per frame for faster convergence at low frame rates.
- One letter of a phrase per dish; a depth-of-field pass on the marble floor.
