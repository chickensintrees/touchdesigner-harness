# sc_droste_crt: the monitor that shows itself

## Intent
A monitor on a desk, lamp-lit, with five objects around it,
and its screen shows this very render: last frame of the camera's own picture is the screen texture,
so there is a tunnel of monitors inside monitors. Each level is one (or a few) frames older than the
one outside it, so a lamp flash on a kick or an object hopping on a snare travels inward as an echo, and
each level turns the hue a step so the tunnel is a rainbow of pasts. It works when you can read the
room, see at least five levels, and see a hit ripple down them. Takes change the room, the camera
and the kind of recursion.

## Technique
- Real feedback, not a drawn tunnel. `render_m` (master camera `cam_m`) -> `mast` -> Feedback TOP `fb`
  (target `mast`) -> optional per-level delay (`cache`, 16 frames at 1280x720, `csel`) -> `scr`
  (shaders/screen.frag: one "level step": hue turn, gain with soft clip, rotation, zoom, invert,
  phosphor tint, scanlines, terminal text, power-on flash) -> Constant MAT on the glass.
- The glass is a 13x9 grid inside `m_crt` (`m_crt/scrn`), bent to a quadratic fitted to the model's
  tube (half the model's real bulge), filling the recess of the bezel. The CRT is stretched 1.30x in
  x so that recess is exactly 16:9 and the glass can show the whole frame.
- A camera on the glass's axis at distance D1 = 1.282 sees the glass fill the frame exactly. From that:
  (a) the Droste dolly is a second render (`render_o`, `cam_o`) whose camera travels from the master
  pose to the fill pose, exponentially in distance, once every `bars` bars; at the end the frame is
  the screen texture, which is the master frame, so the wrap is seamless (post takes the hue step
  back out continuously and cross-fades to the flat texture over the last 4.5%).
  (b) the Escher take is shaders/escher.frag on the master image: log-polar map w -> alpha w,
  alpha = 1 - i n ln(s)/2pi, with the hue step made continuous in angle so there is no seam at the
  branch cut.
  (c) a camera closer than D1 makes every level bigger than the last: "words out".
- Nothing after `mast` is fed back: post.frag (fringing, glow, shoulder, vignette, grain, 1-bit dither).
- `tk` holds every per-take number (expressions indexed by the `Take` parameter, from the TAKES table
  in build.py); `lv`, `cam_a`, `camm`, `camo` derive the level transform and the camera poses.

## Takes (captures/take_<n>.png, sheet captures/takes_sheet.png)
0. desk at night: three-quarter establishing shot, blue room, warm lamp pool, rainbow tunnel on the glass.
1. droste dolly: on-axis daylight room, camera travels into the glass and re-emerges every 2 bars.
2. escher spiral: log-polar twist (2 levels per turn) of the on-axis picture, amber and blue light, zooming.
3. one-bit negative: every level inverts the last; output dithered to black and white; side-on from the left.
4. wall of monitors: no desk, 15 CRTs stacked, salmon-lit, every glass showing the wall.
5. terminal: close on a dark green-phosphor screen; one of the scene's terminal screens (`TERMS`) types out from the cut and echoes down the levels 8 frames apart.
6. spiral tunnel: screen fills 72% of frame, each level turned about 17 degrees (more with bass): a twisting corridor of bezels, pink and blue.
7. phosphor macro: no camera at all; the view is the screen texture itself seen through staggered RGB phosphor slots (shaders/macro.frag), slowly panning; full-frame pattern, the nested monitor only just readable.
8. words out: camera inside the fill distance, no room; one phrase (`PHRASES`) per beat drawn small in the centre flies outward, turning hue each step.

`Seed` moves camera azimuth (seedaz), hue step (x0.75 to x1.25), which terminal screen / which phrase.

## Channel -> visual
- hit_low: desk lamp flashes (cone light, and the `glow` object's emission), the `kick` object hops, the glass lights up, the camera pushes in; all of it then walks down the levels. hits_low parity: polarity of the 1-bit take. section parity: sign of the hue step.
- hit_mid: the `snare` object jumps and tips, overhead tube and rim light kick. hit_high: the `hat` object hops, the `rattle` object shakes, lens fringing.
- pulse: screen glow light and a lift on the glass. beat_pos: the `hat` object swings, the `glow` object sways. beat / beat_i: word changes (take 8).
- bar_pos: dolly phase (take 1), Escher zoom phase (take 2), level rotation swing (take 6). bass: extra level rotation (take 6).
- evolve: camera orbit drift, grain. energy: overhead tube level. shot age: power-on flash on the glass, typing (take 5).

## Describe and Input (2026-11-11, for the website)
An earlier agent started this and was cut off having written only shoot2.py; everything else here was
built and checked in one later pass. Words live in build.py beside each take (`describe=`), and
`python sync_preset.py` copies them into preset.json (`--check` fails if the two differ).

**Describe** (COMP toggle; no rebuild, the tables for both modes exist side by side):
- Takes 0, 1, 2, 3, 4, 6, 7 have no text of their own. Describe adds a caption strip over the bottom 142 px:
  an amber title and two lines in the scene's typeface (`caps` table -> `cap_title`, `cap_body` -> shaders/caption.frag ->
  `final` switch). It sits after post, so the loop never sees it. With Describe off `final` passes `post` untouched.
- Take 5 (terminal): six explanatory screens (`terms_d`) are typed on the glass in place of the scene's own screens;
  Seed picks the screen, as before.
- Take 8 (words out): sixteen short phrases (`phr_d`), one per beat, in list order so they read as sentences
  ("VIDEO FEEDBACK / A SCREEN / SHOWING / ITS OWN LAST FRAME / CAMERA TOO CLOSE / SO EACH COPY IS / BIGGER ...").
- build() measures every caption line with the real font and stores the ones wider than the frame in the COMP's
  storage as `describe_overflow` (empty = all fit). It caught six lines of the first draft.

**Input** (COMP text parameter naming a TOP; `inon` is 1 only for an existing TOP outside this scene, so the
scene cannot read its own out1). `insel` (Select TOP, reads only) -> `inlev` (gain). Two entry points, per take (`inp`):
- backdrop (takes 0, 1, 2): the back wall and floor are hidden, the renders' background goes transparent and each
  render is laid over the picture (`render_m_ov`, `render_o_ov`) before `mast`. The camera therefore films the desk
  in front of the picture and the loop nests it; the dolly and Escher maths hold because the picture is part of the
  master frame.
- on the glass (takes 3, 5, 6, 7, 8, and take 4 does both): screen.frag draws the picture on the outermost glass
  where the text is drawn (flat mix, or lighten in takes 5 and 6), so every deeper level gets it from the feed,
  older and transformed a step. In take 8 it is stamped small on each beat in place of the words and flies outward.
- Blank Input: `render_*_in` switches pass the renders straight through, the wall and floor come back, and the
  shader branch is skipped.

## Words and models (2026-11-11: generic defaults, a pack may replace them)
Everything the scene says and every model it stands on the desk is one dict, `DEFAULTS`, at the top of build.py,
read once in build() through `LIB['scene_words']`. A pack that holds `scenes/sc_droste_crt/words.json` replaces
any of its names (same type required), so the same build.py draws a different set on a different pack.

| Name | What it is | Default (the pack in this repository) |
|---|---|---|
| `TERMS` | six screens typed on the glass in take 5 | real-time picture-making and catalogue lines |
| `PHRASES` | sixteen stamps for take 8, one per beat | the same two veins, 8 characters a line at most |
| `MONITOR` | model name and flat colour | `''`: the monitor built of eight Box POPs (the pack has no monitor) |
| `DESK` | model name and flat colour | `''`: the desk built of four Box POPs |
| `PROPS` | five rows: role, model, scale, position, turn, teapot stand-in, colour | `kick` rubber_duck, `glow` astrolabe, `rattle` gramophone, `snare` amphora, `hat` lander |

The role fixes what the music does to the object (see "Channel -> visual"); the Geometry COMPs are named after
it (`m_kick`, `m_glow`, `m_rattle`, `m_snare`, `m_hat`). A model name of `''` for the monitor or the desk means
"always the boxes"; with a name, the boxes are only the fallback for a missing model, as before.
The typeface is still asked for as `chicago`; the repository's pack answers with IBM Plex Mono through its
aliases.json. Plex Mono is wider (36.8 px a character at the terminal's 46, 120 px at the stamps' 150), which is
why the default lines are at most 29 and 8 characters, and why build() shrinks the Describe caption body
(20 -> about 19) when the widest line would not fit the frame.

## Assets (2026-11-11: the scene is portable)
No file here names a folder. Every file parameter is an expression on the scaffold's `mod.paths`
(shaders: `mod.paths.here('shaders/...')`), and the choice between a real asset and its stand-in is also an
expression (`mod.paths.have(...)`), so one saved .tox works with or without the assets folder and the COMP's
`Assets` parameter switches it live. Nothing precomputed is read from disk and no data file was added.

| The scene uses | With no assets |
|---|---|
| the monitor model named in `MONITOR`, if any (also the 15 of take 4) | a monitor made of eight Box POPs (`m_crt/standin`, `w_crt/standin`: case, tube housing, base, four bezel bars, drive slot) laid out round the same measured 16:9 recess, in flat putty. Never a teapot: the loop needs a screen in a bezel, and the glass (`m_crt/scrn`) is unchanged. This is also what the default words ask for. |
| the desk model named in `DESK`, if any | a desk of four Box POPs (top, two pedestals, back panel) with the same top height, flat wood colour. Also the default. |
| the five models named in `PROPS` | TouchDesigner's bundled teapot (what `mod.paths.model_file` returns), five of them. `fit` (Transform POP) scales each and stands it on the desk where the object stood; build.py reads the teapot's bounds from its OBJ at build time. Each has a flat colour (`plain`) in place of its texture, and they still hop, rattle and sway with the drums. |
| the font asked for as `chicago` (terminal, words out, Describe captions) | Arial (`font` parameter, used when `fontfile` is empty). |

No pictures, music or feeds are loaded by this scene (the hub supplies the feed).
In each model's Geometry COMP: `mesh` -> `shape` (Switch POP: `mesh`, or `fit` / `standin`), and the PBR MAT's
base colour map is `tex` or `plain`.

## Checks
`tdh.check` PASS after the final rebuild (cook_budget read 1.5 ms on take 0 and 1.6 ms on take 4 in quiet
moments, 6.1 ms right after the tox save). The first run after a rebuild fails cook_budget (14.5 ms):
one-off model and texture loads.

## Second pass (art direction, 2026-11-10 evening)
What I saw before changing anything (captures/j_take_<n>_a/b.png, two moments per take): 0 handsome; 1 dolly
muddy grey-green and a sibling of 2; 3 one-bit was grey 2 px dither noise, same picture in both captures;
4 wall strong but identical in both captures; 5 and 6 good; 7 glass macro illegible; 8 soft but different.
Changed (all in build.py and shaders):
- Take 3 rebuilt as a hard-threshold 1-bit picture with a narrow 3 px dither band, closer camera, black wall;
  every kick flips the polarity of the whole frame and holds it (post.frag uB.y = hits_low parity).
  k_take_3_a.png, take_3.png, n_take_3_b.png.
- Take 7 replaced: phosphor macro (macro.frag, view 3). First version warped the slot grid with the barrel
  and gave ring moire at 4 px per slot (l-round take_7, see takes sheet history); slots now stay on the pixel
  grid at 15 to 21 px per triad and only the picture bulges. take_7.png, n_take_7_b.png.
- Take 1 dolly: red wall and brighter warm tube, so the levels go magenta, orange, green, cyan instead of mud.
- Every kick now adds light to the glass (`kick`, screen.frag uX.y) and pushes the master camera in (`punch`,
  0 for the on-axis takes 1, 2, 8); both are then seen a step later by each deeper level. Take 4 also turns
  its hue step on kicks (`hk`). m_kick0_sheet.png: take 0, 8 stills from a kick of 0.98.
- The hue step changes sign with the section's parity (`secflip`, off for takes 1 and 2 whose maths needs a
  constant step), so a section change sends a reversed rainbow down the tunnel.
- The driver also resets the feedback and the cache when `Take` changes, not only after an absence.
- Terminal font 54 -> 46: the longest line overflowed the glass (l_take_5_s90.png).
- Back wall colour is per take (wr, wg, wb).
Still weak: take 7 is a texture more than a picture; takes 1 and 2 are still both frontal CRTs (now very
different in colour); the kick's walk down the levels is clear in takes 4 and 6, modest in take 0; nothing
was watched in motion, only stills. Cost by cpuCookTime + gpuCookTime of operators cooked in the last frames:
take 0 1.6 ms, take 7 1.7 ms, take 1 (two renders) 2.8 ms.

## Log (newest first)
- 2026-11-11 Generic defaults. The words, the models and their tuning moved into `DEFAULTS` (build.py) and are
  read through `scene_words`; the defaults are now generic (see "Words and models") and the originals live in a
  private pack's scenes/sc_droste_crt/words.json, which reproduces the earlier pictures on that pack
  (captures/ref_*.png before, captures/pv_*.png after). On the repository's pack: captures/g*_take_*.png,
  g*_desc_*.png. Geometry COMPs of the five objects renamed after their roles.
- 2026-11-11 Portable. build.py and rebuild.py name no folder (repository = td.project.folder, files through
  mod.paths). With assets, after the change: captures/p1_take_0..8.png and, after the last rebuild,
  p2_take_0..8.png, p2_describe_take_0.png, p2_describe_take_5.png, p2_input_take_4.png: the same pictures as
  final_take_0..8.png. With the `Assets` parameter on an empty folder: na1_take_0..8.png (first try, Courier New),
  then na2_take_0/1/5/8.png, na2_describe_take_0/5/8.png, na2_input_take_0/4/6.png (Arial, monitor base stepped
  forward); errors empty in both states.
- No assets, first try: Courier New as the fallback face was spindly at 150 px in take 8 and three caption lines
  overflowed (`describe_overflow`); Arial fits. The box monitor's base was flush with the bezel and read as one
  slab (na1_take_0.png); it now stands a step proud.
- 2026-11-11 Describe + Input. Final rebuild from build.py, then: Describe on every take captures/describe_take_0..8.png
  (sheet describe_sheet.png); Input = /project1/sw_testcard/out1 on every take captures/input_take_0..8.png
  (sheet input_sheet.png); both off captures/final_take_0..8.png (sheet final_sheet.png) against the pre-change
  rebuild captures/q0_take_0..8.png (q0_sheet.png): same pictures.
- Input, take 6: a 0.85 mix with a luma key pasted the picture over the tunnel (i2_sheet_a.png, bottom right);
  lighten blend lets the turned copies show through (i3_take_6.png). Take 5 uses lighten too.
- Input, backdrop takes: with the floor left in, a dark band cut the picture in half (i1_take_0.png); the floor
  now hides with the wall (i2_sheet_a.png).
- Input, takes 3, 6, 7 first tried as backdrop (i1_sheet.png): only slivers of the picture showed. Moved to the glass.
- Describe captions: first draft had the title overlapping the body and six lines too wide (d1_take_0.png,
  d1_take_3.png); sizes 26/20, lines rewritten (d2_sheet.png).
- Final rebuild from build.py: captures/final_rebuild_take6.png (= hero.png), final_rebuild_take0.png. Errors empty.
- All takes: captures/take_0..8.png, takes_sheet.png; seeds and second moments: seeds_sheet.png.
- Arrival: captures/g_cut6_sheet.png. Faked a cut on take 6: the glass flashes white, then the tunnel digs
  in one level per 3 cooks, the white rectangle travelling down it. Reads well.
- Kick echo: captures/f_kick0_sheet.png (take 0, 8 stills after a kick of 0.83). Lamp flash on the desk
  in still 0, gone outside by still 1 while the first glass still shows it, then deeper. Visible but
  modest at this camera distance (only 3 to 4 levels are big enough to read).
- Escher twist 2 and amber light so it stops resembling the dolly in a thumbnail (e_sheet.png -> takes_sheet.png).
- Flattened the glass bulge to half and re-measured the plane: Escher seam at the left gone (d_sheet.png).
- "words out" replaced a weak "mirror hall" take (a_sheet.png, bottom right: just another desk shot).
  First version drew white text: hue rotation does nothing to grey (c_sheet.png). Amber text cycles (d_sheet.png).
- Escher first try had a hue seam along the negative x axis: sign of the angle term (a_sheet.png, take 2).
- Spiral tunnel looked like a black hole (b_sheet.png): not a bug, the loop fills one level per (delay+1)
  cooks and the shared instance was cooking this scene at 7 to 30 fps. Also raised the driver's "was I away"
  reset from 4 to 30 frames, because stutter was resetting the loop.
- Cache moved from 640x360x32 to 1280x720x16 (same memory): delayed levels were soft.
- tk CHOP read op('shot')['take'], which recooked 50 expressions every frame (age changes): reads the parameter now.
- First tunnel: captures/01_first_tunnel.png. Dolly phases: captures/02_dolly_sheet.png.

## Weak / unverified
- With no assets (see "Assets"): the monitor is plainly a stack of boxes with hard edges and one flat colour, and
  the props are teapots, so takes 0 and 3 read as a demo set. Takes 1, 2, 4, 6 lose the bezel's
  moulding and are flatter. Takes 5, 7 and 8 are nearly as good as the real ones apart from the typeface: Arial
  has none of the character of the intended face, and its bold is not visibly heavier. Only seen in stills.
- Describe: the caption strip covers the bottom fifth of the picture in seven takes (in take 0 it hides the
  objects at the front of the desk). In take 5 the echo of the text overlaps lines 2 to 4 of the outer text, as it does with
  the scene's own screens: readable, not clean. In take 8 a phrase is on screen for one beat (0.48 s), so the sentences
  are caught in pieces. Lines are typed at 26 characters a second, so a shot under 4 s cuts a screen short.
- Input: in the backdrop takes (0, 1, 2) the monitor stands in front of the middle of the picture, so a picture
  whose subject is centred (the test card's words) shows mostly its outer parts; take 2 is the weakest for
  recognising the input. In take 5 the result is mostly the picture in green phosphor with one faint echo.
  The backdrop is not lit by the room and does not move with the camera (it is a flat plate, not a wall).
  Only tested with the test card, never with another scene's out1, and only in stills.
- Describe and Input together: in take 8 the words are drawn over the stamped picture and the two fight
  (captures/describe_input_take_8.png); in the caption takes they sit together well (describe_input_take_0.png).
- "Text typed on the innermost screen that propagates outward" is not literally done: text is drawn on the
  outermost glass and echoes inward (take 5), or flies outward only in the no-room take 8.
- The loop is frame-based, so ripple speed and the words-out speed scale with frame rate. Tuned by eye on an
  instance running 15 to 45 fps under ten agents; at a steady 60 everything is faster than what was seen.
  Never seen in motion at full rate.
- Dolly wrap: checked in stills (p=0.995 against p=0), not in motion. The glass's rounded picture edge is off
  in takes 1 and 2 so nothing pops; the flat-texture cross-fade over the last 4.5% may show as a slight breathing.
- Take 7 is the least clear picture: it reads as a scanlined image more than as glass.
- Takes 1 and 2 are both frontal CRTs; they differ by twist, palette and motion, less by composition.
- No shadows: props do not cast onto the desk.
- A cut to the scene shows up to `delay` stale frames from the cache before the reset black arrives.

## Next
Shadow map on the lamp; a reflection sheen on the glass; set delay in seconds from a measured frame rate;
an outward text loop inside the screen texture (second feedback) for the room takes.

## Test helpers (run inside TouchDesigner)
rebuild.py (runs the builder), shoot.py (take/seed stills), shoot2.py (the same with Describe and Input per shot), evcap.py (stills after a hit or a faked cut),
sheet.py (contact sheet, plain Python).
