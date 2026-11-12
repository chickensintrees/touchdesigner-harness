# sc_paper_storm: instanced paper storm

## Intent

A weather system made of paper: 6144 printed sheets (three different prints, mixed) and a couple of hundred objects, all instanced, all choreographed by one shader. Since the third pass (2026-11-10 evening) it is no longer one picture. The cutter comes back to this scene many times in a track and each visit is a different **take**: a different formation, camera, subject, scale and palette, on the same instance field.

What makes it work:
- Scale and order. Thousands of identical rectangles only look good when they are choreographed: every sheet has a home in each formation.
- The music is in the motion, not in a brightness knob: rotation locked to `bar_pos`, flips and pages locked to `beat_pos`, kicks throw things.
- One accent per take: red lettered reverses in the tunnel, yellow flaps on the board, the gold idol on red, ink on a pale sky.

## Words and shapes (2026-11-11)

Everything the scene shows that is content rather than technique sits in one dict, `DEFAULTS`, near the top of build.py, and `build()` reads it through `LIB['scene_words'](scene, DEFAULTS)`. An asset pack may hold `scenes/sc_paper_storm/words.json` with any of the same names; its values then replace the ones in build.py (same type required), so one source builds different-looking scenes on different packs. The values in build.py suit the pack that ships with the repository.

| Name | What it is | In build.py (the shipped pack) |
|---|---|---|
| `WORDMARK`, `WORDMARK_PX` | the two lines on the red reverses (tunnel, one_sheet) and their type size | REAL / TIME |
| `PAGES` | the board's eight pages, three lines each; at most 11 characters a line in the shipped face, so every line stays in frame at the closest crop | HERE. NOW. / DO NOT TOUCH / NOTHING IS PRERENDERED / SOUND IN. PICTURE OUT. / ... |
| `BACK_PHRASES`, `BACK_PHRASE_PX` | the oculus's blue reverses (the seed picks one) and their type size | NOW. / DO NOT TOUCH / SOUND IN. / PLATE 07 / NOT MADE / LOOP |
| `BOARD_CROP` | how far the seed may crop the board (0 = never), so all three lines of a page stay in frame in the pack's face | 0.16 |
| `BOARD_CROP_D` | how far the seed may crop the board in Describe mode, so the widest explaining line stays in frame in the pack's face | 0.08 |
| `RITUAL_LABEL` | Describe mode's caption for the ritual take (it names the props) | 196 objects; ducks hop, keys are thrown |
| `FORMS` | the three printed sheets: `model` (a flat sheet in the pack whose picture is printed), and the paper, ink and words of the stand-in drawn when that picture is missing | `blueprint`, `star_chart`, `ticket` |
| `PROPS` | the four instanced props in the order `field.frag` knows them: `model`, how many (`w` x `h`), `scale`, `rot` (turns the mesh before it is placed) and the stand-in teapot's colour | 40 `rubber_duck` (hop), 140 `skeleton_key` (dominoes), 8 `traffic_cone` (point at the idol), 8 `amphora` (outer guard) |
| `MONOLITH` | the one large object in the middle of the paper takes: model, scale, turn, height | `marble_bust` |
| `IDOL` | what the prop rings turn round in the ritual take: model, scale, height, turn, roughness, emission | `lander` |

Things to know when writing a pack's own rows:
- A prop's `scale` is the Geometry COMP's scale, which comes after the instance positions: it scales the ring's radius as well as the object. The rings sit at 4.3 and 5.3 (hoppers), 7.0 (dominoes), 2.5 (inner eight) and 3.45 (outer eight) times the scale.
- An instance's +Z points along the shader's facing vector and +Y along its up vector. The dominoes stand with their +Z up, +Y along the ring and +X towards the middle, so an upright model needs `rot` (the key uses 90, 0, 90; the cone uses -90, 0, 0 to point its tip at the idol).
- Triangles are `w` x `h` x the model's count (in its `info.json`). The shipped props are about 30000 triangles each, 196 instances, 5.9 million triangles in the takes that show them; measured cost is in the log.
- The Describe words (`DESCRIBE`, `PAGES_D`, `BACK_PHRASES_D`, `DFORMS`) describe the technique and are not replaceable, apart from `RITUAL_LABEL`.

## Takes (`TAKES` in build.py; the COMP's `Take` parameter picks `take % 8`, `Seed` varies it)

Described as they look on the shipped pack.

| # | Name | One line | What the seed changes |
|---|---|---|---|
| 0 | tunnel | The first cut's picture: flight down a tube of blueprints, star charts and pink tickets to the marble bust in an ink void, red REAL TIME reverses on the beat's flip ring, ducks, keys, cones and amphorae tumbling round the bust. | spin direction, where along the tube we are |
| 1 | board | Square-on wall of 96 x 64 sheets, long lens. Sheets turned to their yellow reverse spell a three-line page in pixel letters; a new page flaps in from the left every two beats. | which page comes first, how close the crop is (`BOARD_CROP`) |
| 2 | murmuration | Ink silhouettes of the whole flock folding in a pale cream sky, the bust a small dark shape under it. No readable text. | flock shape and phase, mirrored framing |
| 3 | ritual | No paper at all: two rings of hopping rubber ducks, a fence of brass keys falling like dominoes, eight traffic cones pointing inward and eight amphorae round the gold lander, on red, low and close with depth of field. No text. | camera height (eye level to high three-quarter), mirrored side, turn direction |
| 4 | rain | Locked camera in pale green haze; sheets fall past like leaves, one step per beat, near ones soft; the bust stands off to one side. | wind slant, mirrored framing, about one shot in five the rain falls up |
| 5 | floor | Straight down on a tidy floor of sheets in 1-bit dither at 640 x 360 fat pixels; a ring of sheets turning to their black reverse leaves the ripple origin every two beats. | floor rotation, camera height (7 to 12 units), ripple origin |
| 6 | one_sheet | One large sheet turning close to the lens, sharp and readable, left or right of centre; the whole galaxy of paper is a red and blue blur behind it. | which of the three prints, which side it hangs |
| 7 | oculus | Inside the dome looking up and off-axis through counter-turning rings of paper; reverses are blue with one of `BACK_PHRASES`. | number of rings (7 to 11), which phrase, mirrored framing |

No take has a centred mark. The two-line mark only exists as the small red reverses of take 0 (and blurred in the background of take 6).

First half second of a shot (`shot/age` -> `ctl/arr`, 1 falling to 0 over 0.7 s, plus a camera dolly-in): tunnel closes in round the lens; board starts all yellow and clears from the right; flock bursts out of a knot; prop rings snap shut from 2.6 times their radius while the idol spins round; rain drops 16 units in a rush; floor starts face down and turns over from the middle; the one sheet swoops in from the side; the dome falls shut.

## Technique

Geometry COMP instancing fed by tiny GLSL TOPs (TOP-to-instance). One fragment shader, `shaders/field.frag`, computes per pixel (= per instance) the position, facing vector and up vector for the take's formation. `uOut` picks which of the four a TOP carries (`*_p`, `*_n`, `*_u`, `*_c`). The Geometry COMP reads Translate from `_p`, orientation through Rotate to Vector + Up Vector from `_n`/`_u` (no Euler angles), colour from `_c`, and the texture index (which of the three prints) from the alpha of `_p`.

- Take switching costs nothing at the cut: `tk` (Constant CHOP, one channel per look value) holds each as `(v0, ..., v7)[take % 8]`; cameras, lights, fog, render flags, Switch TOPs, post uniforms and the `ctl` texture read it. Every model and texture is loaded at build time (force-cooked), including the ones hidden in the current take. Measured on the frame after a switch: 2.3 to 3.6 ms, the same as a steady frame.
- Sheets: two Geometry COMPs on the same 64 x 96 instance field, each a single-sided 2-triangle quad from `meshes/`: `sheets` (printed side, three 512 px pictures by instance) and `backs` (reverse side). The reverse is a Switch TOP: the red two-line mark (a Text TOP), a plain Constant TOP in the take's colour, or a Text TOP whose phrase the seed picks.
- Board: eight 96 x 48 Text TOPs (12 px, three lines) stacked by a Layout TOP into `pages`, input 1 of every field TOP. A sheet is turned over where the page's pixel is lit; `field.frag` mixes the previous and the current page with a delay by column, so pages flap in as a wave.
- Props: `prop0` to `prop3`, one Geometry COMP per row of `PROPS`. In the ritual take the same four instance fields put them in rings; `uSeed` (10 + row) tells the shader which prop it is. Each has a `fit` Transform POP that turns the mesh by the row's `rot`.
- `idol` and `hero` (one sheet, both sides, full-size pictures on a Switch TOP) are ordinary Geometry COMPs shown only in their takes; `monolith` is shown in the paper takes.
- Kick shockwave: `hitsel` (hits_low) -> `hitslope` -> `ringenv` (Trigger CHOP, restart, linear 1 -> 0 in 0.85 s) -> `ctl['ring']`. A ring leaves the middle; what it passes is thrown outward, tipped and tinted amber. Radius scale per take (0 = off).
- Music reaches the shaders as a texture: `ctl` (Constant CHOP, 24 rows, order fixed in build.py) -> `ctltex` (CHOP To TOP, 1 x 24) -> input 0 of every field TOP and input 1 of post.
- Look: PBR materials, exponential fog in the take's haze colour, headlamp at the camera, cone lamp above the middle, ambient, and two distant lights (from above and below) for the daylight takes. Every material writes camera depth to alpha; `shaders/post.frag` uses it for depth of field (far and near ranges per take), adds the void glow, grades with per-take shadow tint, saturation and vignette, and for the floor take quantises to 1-bit with a 4 x 4 Bayer matrix in 2 x 2 pixel blocks. Then a Bloom TOP (intensity per take, 0 in the pale and 1-bit takes).
- The old `Force` parameter and the section-driven hand-over between formations are gone: the take decides the formation. The hall formation was dropped (the board replaces it).
- Helpers: `shot.py` (set take/seed/age and capture in one call), `allshots.py` (every take in one call), `perf.py` (cost per take), `contact.py` (contact sheet, run in the shell), `sync_preset.py` (mirrors the Describe words into preset.json).

## Assets (2026-11-11: what the scene loads, and what it shows without it)

Nothing in this folder names a folder on a machine. Every file parameter is an expression on the scene's `local/modules/paths` (`mod.paths.here(...)`, `.font(...)`, `.model_file(...)`, `.model_texture(...)`); `python -m pytest -q tests/test_portable.py -k sc_paper_storm` checks the sources, the snapshot and the .tox. The switches below are expressions too, so a saved .tox opened on a machine with no assets falls back without a rebuild.

| From `<assets>/` | Used for | Without it |
|---|---|---|
| font `chicago` (the shipped pack answers with IBM Plex Mono) | board pages (12 px), the lettered reverses, the Describe caption | TouchDesigner's default face (Verdana), same sizes |
| `fonts/BarlowCondensed-Bold.ttf` | the explaining sheets of Describe mode (`dform_*`) and the stand-in sheets | default face set at 0.6 of the size (`NOFONT_K`), so the lines still fit the sheet |
| `models/<FORMS[i].model>/basecolor.png` | the three prints on the 6144 sheets and on the one large sheet | `sform0..2`: stand-in sheets drawn with Text TOPs on the row's paper with the row's words, picked by the `pic0..2` Switch TOPs |
| `models/<PROPS[i].model>` (`model.obj`, `basecolor.png`) | the instanced props | TouchDesigner's teapot, brought to the library's size and centre by `fit` (Transform POP), painted the row's `teapot` colour |
| `models/<MONOLITH.model>` | the monolith | one large teapot |
| `models/<IDOL.model>` | the idol of the ritual take | one large gold teapot |
| `scenes/sc_paper_storm/words.json` (optional) | replaces names of `DEFAULTS` | the values in build.py |

Committed in this folder and always present: `meshes/sheet_front.obj`, `meshes/sheet_back.obj` (the two-triangle sheet), `shaders/*.frag`, and `data/white.png` (8 x 8 white, 78 bytes: what a Movie File In reads when its picture is missing, because an empty file name is a warning). Nothing is precomputed from a model or a font: the board's pages are Text TOPs read live by the shader.

## Channel -> visual

| Feed | Drives |
|---|---|
| `shot/take`, `shot/seed`, `shot/age` | which take, the variation inside it, the arrival in the first 0.7 s |
| `bar_pos` | tunnel and galaxy rotation, dome rings counter-turning, prop rings turning (1/16 turn per bar), the one sheet's slow roll |
| `beat_pos` | the travelling flip ring from the camera (tunnel, galaxy, dome); board: page number = beat / 2, flap wave across the columns; floor: ripple phase and a flip ring every two beats; rain: falls one 0.9 unit step per beat; ritual: the first prop hops in a wave that runs round the ring once a beat, dominoes tip and stand every two beats; flock: the turning field advances a quarter cycle per beat |
| `hit_low` (lagged 0.22 s release) | throws sheets outward (tunnel, galaxy, dome, flock +16 %), pops board sheets towards the lens, lifts the floor, holds the rain up, throws the dominoes off the floor and parts the hopping rings, the inner eight jab at the idol, the idol swells 7 %, the one sheet tips 22 degrees |
| `hits_low` (each step) | launches the amber shockwave ring: tunnel, galaxy, dome, board (wide), floor (small) |
| `hit_mid` | whole-frame lift of 22 % |
| `hit_high` | board: loose flaps chatter; flock: sheets scatter out of alignment |
| `bass` | flock fold amplitude, floor ripple height |
| `energy` | lamp above the middle, void glow, flip flash, prop hop height |
| `evolve` | flight down the tunnel, camera sway, prop tumble, rain fall and rocking, flock drift, floor sliding under the camera, idol turning |

## Cost

Third pass, measured per take with `perf.py` (sum of cpuCookTime + gpuCookTime over every operator of the scene that cooked in the last two frames, File In POPs and Movie File Ins left out because they keep their load-time value), 2026-11-10 with other scenes cooking:

| take | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| CPU ms | 1.7 | 1.6 | 1.2 | 1.6 | 1.4 | 1.3 | 2.0 | 1.5 |
| GPU ms | 1.2 | 0.8 | 0.8 | 1.4 | 0.9 | 0.8 | 1.5 | 0.9 |

All under 4 ms against the 8 ms budget. `tdh.check`: FAIL at 99 and 87 ms on the two runs straight after the rebuild (model and texture loads counted as per-frame cost, as before), PASS at 3.96 ms on the third (55 active operators).

## Traps found in the third pass

- With the Render TOP's background alpha at 0 (needed here, alpha carries depth), the background you see is the camera's **fog colour x Fog Alpha** (`fogalpha`, default 0.5), not the Render TOP's `bgcolor`. Asking for 1.2 gave 0.6 whatever bgcolor said; fog off gave black. A pale sky needs `fogalpha` 1.
- Layout TOP: the default `fit` (fitbest) squeezed 96 x 48 inputs into square cells; `fit='fill'` is right. With twelve inputs it laid out only the first eight (both `vertbt` and `gridcols`), with no warning. Eight pages it is.
- Text TOP `fontsizexunit` defaults to points: 12 gives 16 px glyphs. Set 'pixels' for crisp 12 px type.
- The ambient light alone leaves a sheet that faces away from the lamps nearly black, even at dimmer 0.95. Daylight takes need real lights from above and below.
- A two-sided card made of two coplanar single-sided meshes shows the wrong (mirrored) side unless the material culls back faces.
- Returning a parameter that holds operators (`par.tops.eval()`) from execute_python_script dumps every parameter of every one of them into the reply.
- A loop that sets `Take`, force-cooks `out1` and calls `tdh.capture` gives a different picture per iteration inside one call (unlike time, which does not advance), so all takes can be captured at the same musical instant.
- Bash heredocs with apostrophes in the text still break in Git Bash (trap 15 of the first pass, paid for again).

## Log (newest first)

Sixth pass (generic words and shapes, for the public repository), 2026-11-11. The defaults in build.py are now generic and suit the shipped pack; the words, models and tuning the scene was first made with live in a private pack's `scenes/sc_paper_storm/words.json`, and a build on that pack looks as it did before. See "Words and shapes".

- build.py: one `DEFAULTS` dict read through `LIB['scene_words']`; `model()` takes a mesh rotation and a teapot colour; operators are named by role, not by model (`prop0..3`, `idol`, `monolith`, `tex`/`tex1`/`tex2`, `sform0..2`, `pic0..2`); take 6 is `one_sheet`; the look channel that shows the idol is `idol`.
- Shipped pack, chosen and tuned by looking: bust as the monolith (scale 5, turned 24 degrees: it faces the tunnel camera); lander as the idol at scale 2.2 (at 2.7 its legs covered the inner rings); 40 ducks at scale 0.45 (140 overlapped into a yellow band); 140 keys as the dominoes, turned to stand upright in the ring; cones turned to point at the lander; amphorae at 0.8 so they stand clear of the duck rings.
- Lettering in IBM Plex Mono: the red mark at 96 pt (124 clipped the second line), reverses' phrases at 90 pt (110 touched the top edge; a seven-letter line still fills the width), Describe board crop limited to 8 % (12 characters are 86 of the 96 columns).
- Review, same day: the board's longest lines (11 characters) were cut by the frame at the seed's closer crops (`rv_h1a`, `rv_h1b`). The crop limit became a word, `BOARD_CROP` (0.16 here; the private pack keeps 0.42). At 0.26 the lines fitted across but the face's line spacing cut the top and bottom lines (`rv_k2a`). Captures `rv_g*` (seed 0.4), `rv_h*`, `rv_d*` (Describe), `rv_k*` (board after the change), `rv_p*` (private pack).
- Captures (shipped pack): `g5a0..7` (seed 0.4), `g4b0..7` (seed 0.71), `g4c*` (seed 0.55), `g4d*`, `g5d*`, `g5e1` (Describe), `g4i1`, `g4i6` (test picture), `g4_phrase0..5`, `g4_backtex`, `g3_sform0..2` (stand-in sheets), contact sheets `_g4a`, `_g4b`, `_g4cd`, `_g5`. Before and after on the private pack: `before_*`, `after_*`.
- Cost on the shipped pack, `perf.py`, CPU / GPU ms per take 0 to 7: 3.1 / 12.7 (the Bloom TOP read 12.3 in that sample against its usual 0.35: contention), 1.9 / 0.7, 1.8 / 0.7, 2.6 / 0.8, 2.3 / 1.3, 1.9 / 0.7, 2.2 / 2.7, 2.0 / 0.8. `tdh.check`: FAIL at 18.7 ms on the two runs straight after the rebuild (loads), then PASS at 5.2 ms (ritual) and 6.9 ms (tunnel).
- Weak, shipped pack: the blueprint is dark blue paper, so in the one_sheet take a blueprint under the low key light is dim beside the star chart and the ticket; the star chart (square) and the ticket (2:1) are stretched to the sheet's 1.29:1; the ducks face outward and do not turn with their ring's direction. Judged from stills.

Fifth pass (portability, for the public repository), 2026-11-11. Only where files are found changed; no take, word or shader did. Captures: `ref_0..7`, `_sheet_ref.png` (before), `port_0..7`, `port_d0`, `port_d6`, `port_i1`, `port_i6`, `_sheet_port.png` (after, real assets, final build), `na_0..7`, `_sheet_na.png` (empty assets folder), `na_d0/1/3/6`, `na_i0/1/6`, `na_di4`, `_sheet_na_modes.png` (empty assets, Describe and Input), `_sheet_na_static.png` (the stand-in and explaining sheets in the default face).

- build.py, run.py, allshots.py: no literal folder; file parameters are `mod.paths` expressions (see "Assets"). New in the network: `fit` (Transform POP) in each prop, the monolith and the idol; stand-in sheets and their switches in `sheets` and `hero`; `data/white.png`.
- With assets: ten static TOPs (pages, pages_d, reverses, explaining sheets, sheet pictures, caption) captured before and after are pixel-identical; all eight takes match the reference in composition, palette and subject (the music was at another moment).
- Without assets (the COMP's `Assets` parameter on an empty folder, rebuilt): `tdh.errors` empty in all eight takes, in Describe on four and with the test picture on four. What it looks like: paper takes are close to the real ones, with plainer sheets in Verdana; the board reads in Verdana pixels; every model is a teapot (a ring of 140 blue teapots, 140 cream ones, a large gold teapot for the idol, a large putty teapot for the monolith).
- Traps: a Movie File In with an empty file name warns "File not found", so its expression falls back to `data/white.png`. The scaffold's `import_model` decides whether to wire the texture from the process-wide assets folder, not the COMP's `Assets` parameter, so `model()` in build.py wires it itself and tints the material by expression. Text TOP `bold` did nothing to the default face here (same width and look), so it is not used.
- The saved .tox is compressed: the committed one from the fourth pass, which did hold literal folders, contains no readable path either, so the portable test's scan of the .tox cannot fail. What shows the .tox is clean is the snapshot (157 `mod.paths` expressions, no folder) and a scan of all 18933 parameters and every DAT's text in the live COMP for a constant holding a drive or a home folder: none.
- `tdh.check`, portable test: see "Checks (fifth pass)" at the end.

Weak, without assets:
- The ritual take is teapots round a teapot: it shows the choreography, not the objects. The dominoes become a bead chain of teapots and lose the domino fall.
- The rain and murmuration takes have a teapot where the monolith stood; in the rain it is large in frame.
- The stand-in sheets are sparse (a title, four ruled rows) and their type is light; at tunnel distance only the titles read.
- Board letters in Verdana are thinner than the pack's face, since they are 12 px antialiased text thresholded per sheet.
- Judged from stills, like everything else here.

Fourth pass (Describe mode and Input, for the public website), 2026-11-11. Two agents: the first was cut off after writing build.py, print.frag, the field.frag change and sync_preset.py; the second rebuilt from build.py, looked at every take in every mode, added the tunnel and oculus captions, and wrote this entry. Captures: `p*_base` (before), `final_0..7`, `final_contact.png` (after: Describe off, Input blank), `describe_0..7`, `describe_contact.png`, `i0..7`, `_sheet_i.png` (test picture, Describe off), `di0..7`, `_sheet_di.png` (test picture and Describe).

**Describe (`parent().par.Describe` -> `mode['describe']`).** Every lettered surface has a Describe twin built at build time, picked by a Switch TOP, so the toggle needs no rebuild: `pages_d` beside `pages` (`pagesw`), `backtex_d` / `backphrase_d` beside the reverses (`backtexsw`, `backphrasesw`), three explaining sheets `dform_a/b/c` beside the three printed sheets (`face0..2`), `dform_hero` on the one large sheet, and a two-line caption `cap` composited over the picture by `capover` / `capsw` (index 0 = the untouched bloom output). Words live in `DESCRIBE`, `PAGES_D`, `BACK_PHRASES_D`, `DFORMS` in build.py; `python sync_preset.py` mirrors them to preset.json and `--check` fails on drift.
- 0 tunnel: sheets read INSTANCING / ONE SHADER / ON THE BEAT (titles legible, the small rows only on the nearest sheets), red reverses "6144 COPIES", caption "INSTANCING: 6144 COPIES OF ONE PAPER SHEET, EACH PLACED BY A SHADER. / THE BAR TURNS THE TUNNEL. THE BEAT FLIPS A RING OF SHEETS TO RED."
- 1 board: eight pages in sheet-pixels, e.g. "INSTANCING / 6144 / SHEETS", "ONE SHADER / PLACES / THEM ALL". No caption: the wall is the text. The seed's crop is limited to 20 % in this mode (`zvard`) so all three lines stay in frame.
- 2 murmuration, 3 ritual, 5 floor: caption only ("THREE SINE WAVES FOLD THE FLOCK. BASS DEEPENS THE FOLDS."; the ritual's caption counts the props and says which hop and which are thrown; "A FLOOR OF 6144 SHEETS, DRAWN IN 1-BIT DITHER. / EVERY 2 BEATS A RING OF SHEETS TURNS OVER TO BLACK.").
- 4 rain: explaining sheets on the falling paper plus caption "THEY FALL ONE STEP PER BEAT. NEAR SHEETS GO OUT OF FOCUS."
- 6 one_sheet: the large sheet carries six real sentences ("This sheet is one flat model: two triangles. The blur behind it is 6144 copies of the model, arranged in a spiral by one shader. ..."), all legible at 1280 x 720. No caption needed.
- 7 oculus: blue reverses carry a seed-picked pair ("6144 SHEETS", "FLIP ON BEAT", ...), caption "RINGS OF PAPER TURN WITH THE BAR. THE BEAT FLIPS A RING TO BLUE."

**Input (`parent().par.Input` -> `inp` Select TOP -> `mode['inp']`, `ctl` row 23).** A blank, missing, non-TOP or own-scene path falls back to `inblank` (tested: all three give inp 0 and no errors), so nothing can loop. The picture enters in three places:
- the printed side of every sheet: `print0..2` (shaders/print.frag) print the whole 16:9 frame on each paper stock with a margin, colours multiplied into the paper; the `face*` switches pick them. Tunnel, rain, floor, one_sheet (1024 px print on the hero sheet), oculus.
- the reverse of the sheets where the take sets `backin`: `backprint`, a two-colour print in the take's reverse colour (red in the tunnel).
- the board: `inlum` (96 x 54) is input 2 of the field shader. Each sheet takes its pixel's colour and turns to its yellow reverse against a 4 x 4 ordered-dither threshold: a flip-dot display of the picture. This is the best one (`i1`: TEST INPUT in yellow flaps on a coloured wall).
- Murmuration (ink silhouettes) and ritual (no paper) ignore the Input. With Describe also on, captions switch to `label_input` and the reverses keep their words.

Checks: `tdh.errors` empty; `tdh.check` FAIL 206 ms straight after the rebuild (loads), a missed reading of 0.0 ms / 0 operators, then PASS at 3.44 ms (34 active operators, 299 idle: the Describe and Input twins do not cook while switched out).

Weak, fourth pass:
- Tunnel, rain and oculus in Describe: only the sheet titles are readable in a still; the rows of facts on the sheets are too small except on the two or three nearest. The caption carries the explanation.
- Oculus with an Input (`i7`): hundreds of small dark prints; the picture is recognisable only on the nearer sheets and the take loses its blue. A dark input makes dark paper everywhere (ink is multiplied into the stock).
- Floor with an Input: 1-bit dither of a small print; the test words are just legible, a busy picture would be noise.
- Board with an Input: 96 x 54 sheets, so fine detail is gone, and a hard kick's shockwave disc breaks the middle of the picture for a moment, as it does the letters.
- The caption is a flat band over the bottom 80 px of the frame; it hides that strip of the picture.
- Describe and Input were judged from stills only, like everything else here.

Third pass (variety: takes), 2026-11-10 evening. Before: `g01_before`, `g02_before` (galaxy -> tunnel hand-over), `g03_before` (tunnel), and `g04_rebuilt_new_scaffold` (old build.py on the new scaffold: same tunnel, Take/Seed/Shotstart and `shot` present).

- `take_0.png` to `take_7.png`, `takes_contact.png`: every take after the last shader change. `hero.png` = the first `take_3.png` (ritual at kick 0.73: dominoes thrown off the floor, idol facing the lens).
- `n0_final_rebuild` to `n7_final_rebuild`, `_sheet_n.png`: all eight after the final clean rebuild from build.py.
- `m*_a` against `m*_b`, `_sheet_m.png`: every take twice with the same seed, 13 s apart. a: kick 0.08, ring 0.57, energy 0.42. b: kick 0.72, ring 0.78, energy 0.67 (caught with a temporary Execute DAT waiting for kick > 0.55). Tunnel wider and redder; board on another page with the shockwave disc on it; flock spread and refolded; floor torn open round a black hole of reverses; one sheet tipped back; dome rings wider. The ritual pair differed least (ring phases only), so the kick now throws the dominoes and parts the hopping rings (`take_3`).
- `k2`, `k4`, `k5`, `k7`: after the fog-alpha fix the sky is cream and the rain haze is pale green; before it (`i02`, `i04`, `j*`) both were a dull khaki at half the brightness asked for.
- `j*_s7`, `j*_arr`, `_sheet_j.png`: seed 0.71, and every take 0.15 s after the cut. Board all yellow, flock a knot, prop rings wide open, floor face down.
- `i05`: floor nearly black: the camera-distance flip ring (8.8 units wide) covered the whole view from 8.5 units up. The floor now has its own narrow ring from the ripple origin.
- `i06`: the one sheet showed mirrored and upside down (two coplanar sides, no culling). Fixed.
- `i04`, `h04`: rain as dark olive polygons on mud. Volume made 3.7 times larger (84 x 40 x 80), distant lights added.
- `h01`: board text squeezed into a three-column stripe (Layout TOP fit). Fixed in `i01`.
- `h00` to `h07`, `_sheet_h.png`: first look at all eight.

Second pass (art direction), 2026-11-10. Before: `a01` to `a07`. The first build was competent but one colour (sepia and olive mud), its kick response was invisible in stills (galaxy at kick 0.22 and at 0 looked the same, `a03`/`a04`), and in the tunnel most near sheets showed their print mirrored (`a05`, `a07`).

- `f01_final_rebuild_tunnel.png` (= `hero.png`): clean rebuild, tunnel, beat 0.82: the red ring of lettered reverses is near the lens, cream and pink sheets behind it, monolith and props at the far end.
- `e01`, `e02`: headlamp moved close to the lens (offset -1.1, +1.4, +0.6 instead of -2.5, +3.0, +1.0) and sheets given a faint ink emission. Before that a sheet 3 units away could face the camera with its back to the lamp and draw a pure black polygon across the monolith (`d05`).
- `d01` to `d04`: auto mode after rebuild. `d02` is a dome -> hall hand-over at beat 0.15 with the flip wave at the lens: a storm of red leaflets. `d03` is the hall at ring 0.80: an amber disc of lifted sheets on the wall round the monolith.
- `c03`: hand-over drew two black wedges over a third of the frame (sheets within a unit of the lens). Added a 2.8 unit keep-out sphere round the camera in `field.frag`. Not seen again in `d02`, `d05`.
- `c02`: tunnel at ring 0.92: the shockwave is an amber band of sheets just round the monolith, with the red flip ring further out. Font size 124 clipped the mark; 84 fits.
- `b06`: shockwave first seen (galaxy, ring 0.90), far too hot: x2.8 white on the lamp pool. Changed to an amber tint (x2.0 red, x1.55 green, x1.12 blue at the peak) and bloom intensity 0.45 -> 0.35.
- `b05`: Trigger CHOP fed from the `hit_low` envelope read ring 0.137 on a fresh hit of 1.1: the envelope had not fallen under the threshold since the previous kick, so the ramp did not restart. Now triggered from the slope of the `hits_low` counter.
- `b01` to `b04`: red reverses in all four formations. Prints read the right way round everywhere. Dome props moved from a clump in front of the monolith to a tilted belt round it (`b03`).
- Grade: olive shadows replaced by ink blue (ambient 0.26, 0.42, 0.60), saturation 1.12 -> 1.3, and a tanh shoulder above 0.72 so the lamp pool rolls off instead of clipping. Lamp dimmer 3.5 + 4.0 energy -> 2.6 + 2.6 energy.

First build:

- `14_final_rebuild.png`: clean rebuild from build.py, tunnel at kick 0.42: gaps open between sheets, monolith and props in the middle, readable prints near the lens. The two heavy props' counts halved to 8 each for cost.
- `13_rebuild.png`: rebuild reproduces the tunnel.
- `12_auto.png` (= `hero.png`): the hall after a dome -> hall hand-over. Back wall, floor and ceiling of sheets, monolith in the middle, props in a lattice, and the beat's flip wave visible as a dark ring of edge-on sheets around the monolith.
- `10_auto.png`, `11_auto.png`: dome at kick 0.72 against kick 0.12: rings visibly looser and further out on the kick.
- `09_tunnel_dof.png`: depth of field added (materials write depth to alpha, post mixes a blur). Centre depth read back as 12.6 units, which matches the camera distance. The handwriting on a pink sheet is readable at the right edge.
- `08_dome_rings3.png`: dome reworked from an even Fibonacci shell (read as flat wallpaper, `06`) into nine latitude rings turning against each other, with dark gaps. Much better.
- `07_dome_rings2.png`: caught the hand-over arc by accident: two sheets fill a third of the frame. Kept the arc for real section changes, disabled it when the formation does not change.
- `05_galaxy.png`: spiral arms of paper round the monolith under the lamp. The strongest still. Taken before depth of field was added.
- `03_auto_a.png`, `04_auto_b.png`: first looks in auto mode after widening the field of view (the Camera COMP `fov` is horizontal; 58 gave a 34 degree vertical view and hid the hall's floor and ceiling).
- Before that (no file kept): beige-fog version. Paper on luminous beige haze was pale on pale, and the Bloom TOP at defaults (threshold 0.01) whited out the centre. Switched to the dark void with a hard lamp: cream and pink against ink gives the contrast.
- `01_tunnel.png`: the blown-out beige attempt.
- First build: `half` is a reserved word in GLSL; a Constant CHOP expression reading `me['fa']` is a cook loop.

## Weak points

Third pass:
- Everything was judged from stills, the arrivals from one frame each at 0.15 s. Nobody has watched a take in motion; the board's flap wave, the dominoes and the rain steps are the ones most likely to surprise.
- Murmuration: the fold is three sine warps, not a flock simulation. It reads as a murmuration in a still; in motion it may look like a rubber sheet. Its kick response (16 % swell) is the subtlest of the eight.
- Ritual (first pack): the hopping props lay on their sides and sat close together, so the ring read as a pale band with pegs rather than as objects. Nothing casts a shadow and there is no floor.
- Rain: a near, soft sheet is a plain grey rectangle when it shows its reverse; the take depends on a printed side happening to face the lens. The monolith is large in frame, so in subject this is take 0's nearest relative, though not in picture.
- Board: at a hard kick the shockwave disc and the pop towards the lens break the letters up for a moment (first `take_1`, kick 0.73). Toned down afterwards (ring 2.2 -> 1.5, pop 3.5 -> 2.0) and not re-checked at a kick that hard. Letters are about 20 % wide for their height, since the pitch is square but the sheets are not.
- Floor: in 1-bit the printed sheets are near-plain tiles; nothing on them is readable. It is a graphic pattern, not print.
- Oculus: between flip rings, with the blue reverses hidden, it is cream and pink rings on navy and close in feeling to take 0's palette.
- Takes 0, 6 and 7 share the ink-void look and a monolith or a hole in the middle more than the other five do.
- The seed gives each take two or three variations (mirror, height, crop, phrase), not an endless supply.

## Weak points of the first two passes (tunnel, dome, galaxy; the hall no longer exists)

After the second pass:
- The hall at rest (`e02`) is still the dullest formation: a grey brick wall. It only comes alive when the flip wave or a shockwave crosses it.
- The dome between beats is beige and static (`d01`); its red moment is short because most visible sheets sit at the same distance from the camera.
- The monolith is dim in the tunnel when `energy` is low (`e01`): the headlamp barely reaches it and the cone lamp follows energy.
- The galaxy carries more red than the others because its sheets also tumble on their own; the ring reads less cleanly there.
- Motion was judged from stills a few seconds apart, never from a recording.
- Still no cast shadows; props still read as pale lumps at distance.

From the first build (those marked fixed were addressed above):

- The hand-over between formations was seen only in one accidental frame (`07`) and one settled frame; I did not watch it in motion.
- (fixed) Dome: the prop swarm clumps in front of the monolith and partly hides it.
- Props read as grey lumps at distance; their textures are low-contrast. No shadows anywhere (shadow maps were not tried), so the lamp pool is not grounded by cast shadows.
- (mostly fixed: shoulder in post.frag; the bloom can still lift the dome's bottom rows to near white) The lamp pool at the bottom of the frame still clips to white in the dome and galaxy when energy is high.
- The hall wastes about two thirds of its sheets off-screen (the grid is 69 units wide).
- Sheets are lit single-sided: mid-flip and back-facing sheets go nearly black. It reads as the flip wave, but it also makes random dark tiles in the tunnel.
- (fixed: shockwave ring) Kick response is a radius change only; at low `hit_low` values it is subtle.
- (fixed: red reverses) No lettering beyond what is printed on the sheets.

## Next

- Record each take for a few bars and watch the arrivals and the kicks in motion.
- Shadow map on the cone lamp for the ritual; a floor disc under the rings; stand the hopping props upright (done by `rot` in the sixth pass).
- A ninth take: sheets leaving the monolith in a single stream.

## Next (from the first two passes)

- Shadow map on the cone light for the monolith and props.
- A fifth formation that spells the mark out of sheets (sample a Text TOP for homes).
- Use `hits_low` to launch a one-shot ripple from the monolith instead of a plain radius kick.
- Decimate the two heavy props so they can be instanced in the hundreds.

## Checks (first and second pass)

Second pass: `tdh.check` PASS at 2.8 ms and 5.1 ms (42 active operators); FAIL at 83 and 80 ms on the runs straight after a rebuild, for the reason below; one run reported 0.0 ms with 0 active operators, which is a missed measurement, not a result. Own per-frame operators: render 0.3 to 2.0 ms CPU + 0.5 GPU, bloom 0.34 GPU, back text 0.4.

First build: `tdh.check`: PASS, cook_budget 4.1 ms (38 to 81 active operators). It FAILS (19 to 86 ms reported) when run straight after a rebuild or a `save_tox`, because the one-off model loads (File In POP for the two 60000-triangle props, about 45 ms each) are counted as per-frame cost, and it read 19 to 29 ms while seven other scenes were cooking and GPU timings were inflated about ten-fold (Bloom TOP alone read 4.2 ms against its usual 0.35). Quiet reading: render 0.55 to 1.2 ms GPU, bloom 0.4, total about 1.3 ms CPU + 1.5 to 2.2 ms GPU.

## Checks (fifth pass, portability, 2026-11-11)

After the final rebuild on the real assets: `tdh.errors` empty. `tdh.check`: PASS with a missed reading (0.0 ms, 0 active operators), FAIL at 289 ms (the loads of the rebuild counted as per-frame cost), then PASS at 4.86 ms (52 active operators, 338 idle). `python -m pytest -q tests/test_portable.py -k sc_paper_storm`: 1 passed. `python sync_preset.py --check`: preset.json matches build.py.
