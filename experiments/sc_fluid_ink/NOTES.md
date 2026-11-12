# sc_fluid_ink: Ink in water

## Intent
A real 2D fluid (stable fluids with pressure projection and vorticity confinement) used as ink dropped
into water. Poster phrases, pages of small print and model silhouettes arrive as crisp ink and the
music tears them apart: kicks are blasts or jets that carry a drop of ink, snares are vortex pairs, bass
stirs the whole tank, the voice is a moving nozzle whose height follows pitch. It works when (a) the ink
reads as liquid (mushroom plumes, filaments, mixing colours, a lit wet surface over paper) and not as a
smeared blur, (b) a viewer can see the drums land, and (c) every return to the scene is a different
picture: top-down marbling, side-on plumes sinking, 1-bit bleeding page, luminous ink at night, macro
letter fragments.

## Technique
All in GLSL TOPs inside `/project1/sc_fluid_ink`, built by `build.py`, shaders in `shaders/`.

- Velocity and pressure at 320x180 (rgba32float), dye at 1280x720 (rgba16float): two Feedback TOPs.
- Per frame: `vstep` (semi-Lagrangian self-advection, vorticity confinement, forces) -> `diverge` ->
  `jacobi` (one GLSL TOP, `npasses` 22, warm-started from last frame's pressure kept in the velocity
  texture's blue channel) -> `proj` (subtract the pressure gradient, walls at the frame edge) -> `dye`
  (advect three inks along the projected field, add new ink).
- The dye texture holds three ink concentrations in r, g, b. `shade` turns them into a picture: each ink
  absorbs light like a filter (Beer-Lambert, so red over blue goes dark, yellow over blue goes green),
  the surface normal comes from the gradient of ink thickness plus the gradient of the pressure field
  (so a kick sends a ripple through the paper), the paper or the printed sheet is sampled through that normal
  (refraction), and there is a specular highlight, edge darkening and a lensing term. Style 1 is luminous
  ink in dark water, style 2 is a 1-bit ordered dither.
- `src` draws what is laid down as crisp ink (a phrase, the page of typewriter small print, model
  silhouettes from a Render TOP, marbling bands, three fat drops, a halftone of drops). `dye` presses it
  in with `max()` while `ctl/stamp` is 1: for the first 0.3 s of a shot and for 0.25 s at each new
  section (new phrase or model, at a new place).
- A new shot is detected without any state outside the loop: `ctl/id` is a number made from Take, Seed
  and Shotstart; both feedback loops store it in their alpha and start clean when it differs.
- `takes` (Table DAT) -> `tk` (Constant CHOP): one row of about 50 numbers per take; every uniform
  reads `tk` or `ctl`.

## Channel-to-visual mapping
| Feed | What it does |
|---|---|
| `hit_low` + `hits_low` | kick: a star of 3 to 6 jets out of a fresh drop of ink (kmode 0), a jet with ink from a frame edge (kmode 1), or a heavy drop falling from the top (kmode 2). Place and shape are a hash of the hit count and the seed, strength is the hit strength |
| `hit_mid` + `hits_mid` | snare: a vortex pair with a blob of ink between, which then travels |
| `hit_high` + `hits_high` | hat: a fine droplet somewhere |
| `bass` | slow global stir (a drifting divergence-free flow), stronger with the bass |
| `vocals`, `pitch` | a nozzle that sweeps left-right with `beat_pos`, squirts ink and a jet while the voice sounds, at a height set by the held, lagged pitch (MIDI 40 low to 64 high) |
| `section` | new phrase / model, stamped at a new place; alternates the stamp's ink |
| `evolve` | drift of the stir field and of the view |
| `pulse` | 7 % lift in the light on each beat |
| `shot/age` | the view punches in 22 % and settles in half a second; the stamp is held 0.3 s then released with a shove |
| `bar` | the page take prints its page again on each bar line |
| `shot/take`, `shot/seed` | which picture (below); seed moves the shape, picks phrase and model, rotates the marbling, flips the 1-bit take to white-on-black, places every drum hit |

## Controls added 2026-11-11
`Describe` (toggle): the words explain the technique (see the log entry of that date). `Input` (path of a TOP):
that picture becomes the ink, or the paper on the sheet take. Both off or blank: the scene as before.

## Assets
Every file parameter is an expression on `mod.paths` (the scaffold's `local/modules/paths`); nothing names a folder.
The shaders are `experiments/sc_fluid_ink/shaders/*.frag` (`mod.paths.here`). No precomputed data: nothing was
added to the folder.

The words, the six models and the sheet are `DEFAULTS` at the top of build.py, read once at build time through
`LIB['scene_words']`. A pack may replace any of its names (`PHRASES`, `PAGE_LINES`, `CAPTIONS`, `SHEET_STANDIN`,
`MODELS`, `SHEET`) with its own `scenes/sc_fluid_ink/words.json`. `MODELS` rows carry each model's tilt, turn and
size; `SHEET` carries the sheet model, its width / height (`aspect`), its height in frame heights (`size`) and the
sheet take's stamp position and view, because those suit one sheet. After changing packs, rebuild.

From the optional assets folder the scene uses, and falls back to:

| Asset | Used for | With no assets |
|---|---|---|
| `<assets>/fonts/ArchivoBlack-Regular.ttf`, `BarlowCondensed-Bold.ttf` | the ink phrases (takes 0, 5, 8, 9) | TouchDesigner's default face, with the Text TOP's `bold` switched on by expression |
| `<assets>/fonts/ChicagoFLF.ttf` (the shipped pack answers with IBM Plex Mono) | page, captions, Describe sheets | the default face; the Describe page sets smaller (23 px, line spacing -1) so its 16 lines fit |
| `<assets>/models/<slug>/model.obj` for the six `MODELS` (gramophone, amphora, lander, skeleton_key, rubber_duck, hourglass) | silhouettes in night, sinking, survey | the bundled teapot for all six, centred and scaled to 1 unit at build time (`_fit_unit`), each with a different tilt |
| `<assets>/models/<slug>/basecolor.png` for those six | the lit render the silhouette's density comes from | plain PBR material (`basecolormap` cleared at build time) |
| `<assets>/models/<SHEET model>/basecolor.png` (star_chart) | the sheet under the water in the sheet take | `form_gen`, a Text TOP that types a plain catalogue sheet from `SHEET_STANDIN` (Switch TOP `form`, by expression) |

The model fallbacks are decided when build.py runs (scale and material), so after adding or removing the
assets folder, rebuild. Fonts and the sheet switch follow the folder live.

## Takes (`TAKES` in build.py; the cutter's Take is taken modulo 10)
Second pass, 2026-11-10 evening. Captured 3.2 s into a shot with seed 0.41: `captures/take_<n>.png`, sheet
`captures/takes_sheet.png`. The same shots at 0.3 s: `captures/tk<n>_0.png`, sheet
`captures/takes_arrival_sheet.png`; at 6 s: `captures/f<n>_2.png`, sheet `captures/takes_late_sheet.png`.

0. phrase: a poster phrase in glossy black ink, off-centre in cream water; kicks are red stars.
1. marbling: the whole frame in red, yellow and blue bands (angle by seed), combed by jets from the edges. No word.
2. night: one model (which one by seed and section) as luminous ivory ink in navy water, pink edge jets, yellow snares.
3. inkblot: the left half of the tank shown folded down the middle, like a test plate. Black blots and one red on
   white card, a typed caption ("PLATE 9. ORIGIN: UNRECORDED."). All hits land in the shown half.
4. page: a full page of typewriter small print bleeding, 1-bit ordered dither; white-on-black for about half the seeds.
   The page is printed again on every bar line, so it never dissolves to an empty frame.
5. oil: a condensed phrase bigger than the frame as an oil film on black water. Colour is interference from film
   thickness (shade style 3), so the letters change colour as they thin and every edge and drop grows rings.
6. sinking: side-on. A row of three small model silhouettes at the top sinks as plumes; kicks are red drops from above.
7. survey: one model drawn as contour lines of ink thickness on green graph paper (shade style 4): no gloss, no
   fill beyond a wash, three draughtsman inks. Kicks are red line-drawn stars.
8. macro: letters three times the frame height, so only fragments show; thick ident colours that mix, strong surface.
9. sheet: a printed sheet (the star chart) seen through the water (refracted), a small red stamped phrase on it, black stars, blue voice.

Removed in the second pass: `jets` (at 6 s it was the same picture as `night`: neon swirls on dark) and `halftone`
(mud by 7 s). `src.frag` mode 4 and 5 are still there, unused.

## What is weak or unverified
- Late in a long shot (6 s and more) the ink-heavy takes (0 phrase, 6 sinking, 8 macro) drift toward "busy
  swirl": the compositions differ most in the first four seconds (`takes_late_sheet.png`).
- The scene was only ever watched as stills (sequences of 3 or 4 captures per shot). I have not seen it
  in motion or through the cutter, and frame rate on the shared machine was uneven, which changes how
  far the ink travels per second (the solver uses a fixed 1/60 s step).
- The voice nozzle is confirmed only indirectly: dashed trails of the nozzle ink appear where vocals are
  loud (`c0_2.png` red dashes, `b6_1.png` blue dashes) and the held pitch reads sensibly (49) after the
  gate fix, but I did not capture a clean before/after of height following pitch.
- Marbling band edges still show some saw-teeth where a jet shears them hard (velocity grid is 320x180).
- Night take: the model's own shading is mostly lost (it reads as a flat ivory silhouette).
- Soft haze from bilinear dye advection is hidden by the `crisp` curve in shade, not removed.
- `tdh.check` passed on the third run after the final rebuild (first pending, second counted model
  loads: 39 ms; third 2.2 ms).

## Next
- A MacCormack or bicubic dye advection step for sharper filaments; velocity at 480x270.
- Let the phrase itself push the water (force from the stamp's edges) so the arrival is a splash.
- A take where the dye is advected text that re-forms (reverse the stored flow) on the bar line.

## Log
(newest first)

- 2026-11-11 Generic defaults. The words, models and sheet in build.py are now generic (`DEFAULTS`: real-time
  picture-making phrases and a catalogue of unexplained objects; gramophone, amphora, lander, skeleton_key,
  rubber_duck, hourglass; the star chart as the sheet). The originals live in a private pack's
  `scenes/sc_fluid_ink/words.json`, and a build on that pack draws the scene as before. Take 9 is now called
  `sheet`; the sheet's shape and size are uniforms (`ctl2/shasp`, `ctl2/shsize`) because the star chart is square
  and is laid 1.62 frame heights high so it fills the frame. Sheets on the shipped pack: `g_sheet_a.png`,
  `g_sheet_b.png` (all ten takes, several seeds, 0.5 s and 2.5 s), Describe `gd_sheet.png`. An independent review the same day replaced four weak phrases, re-captured every take (`gv_sheet.png`, `gw_sheet.png`, Describe `gdv_sheet.png`) and re-saved the tox, snapshot and `hero.png` (= `hv3_2.png`, inkblot, seed 0.63, 4.5 s).
  - Weak on the shipped pack: on the sheet take a new section stamps the next phrase almost on top of the last
    (as it always did), and two two-line phrases overprinted are hard to read (`gb9_1.png`). The skeleton key is
    a thin stroke of ink in the sinking take (`g6_0.png`). IBM Plex Mono stands in for the bitmap face, so the
    1-bit page reads as typewriter print.
- 2026-11-11 Portability. build.py and the helpers no longer name any folder: the repository is
  `td.project.folder`, every file parameter is a `mod.paths` expression, and the scene builds with an empty
  assets folder (see "Assets"). Reference before the change `ref_sheet.png`; after, with assets `wa_sheet.png`
  and `wb_sheet.png` (all ten takes, seed 0.41, 3.2 s: the same pictures); with the COMP's Assets parameter on
  an empty folder `na_sheet.png` (first try: thin default type, teapots at odd tilts, sheet header cut off) and
  `nb_sheet.png` (bold type, milder tilts, header in frame), Describe `nd_sheet.png`, `ng_sheet.png`, Input
  `ni_sheet.png`. No errors in either state.
  - Weak with no assets: every model is a teapot, so night, sinking and survey always show the same subject
    (only its turn and tilt change); the default face is lighter than Archivo Black even emboldened, so the
    phrase and macro takes have thinner ink and tear up sooner; the 1-bit page loses its bitmap-face look;
    the stand-in sheet is one size of type with no box for the stamp, so the red stamp lands on blank paper.
- 2026-11-11 Describe mode and Input (two agents; the first was cut off, the second checked and finished it).
  Sheets: `describe_sheet.png` (all ten takes, Describe on, seed 0.41, 2.4 s), `off_sheet.png` (all ten with
  Describe off and Input blank, toggled with no rebuild: same pictures as `takes_sheet.png`), `n_in_sheet_a.png`
  and `n_in_sheet_b.png` (all ten with Input = /project1/sw_testcard/out1 at 1 s and 4 s), `p4_sheet.png`
  (page take in Describe, three seeds), `fin_d_sheet.png` (after the last clean rebuild).
  - Describe, what is on screen: every take except the page gets one caption sentence in the typewriter face on a strip
    along the bottom (pale strip, or dark on the night and oil takes), chosen from `caps` in its TAKES row by
    seed and section, e.g. "EVERY KICK DRUM COMBS THE BANDS WITH A JET FROM THE EDGE." Phrase, oil and macro
    also swap their big ink words for `describe` ("FLUID / SIMULATION", "KICKS FIRE / JETS", "OIL FILM",
    "VORTEX"). The page prints 16 lines of sentences (`PAGE_DESCRIBE`) from a second Text TOP, and the sheet take
    lies a filled-in sheet (`SHEET_DESCRIBE`, field and value) under the water in place of its own sheet.
    All of it exists at build time; the toggle only flips Switch TOPs and text expressions.
  - Page take in Describe: with the normal behaviour the sentences were mush within a second (`q4_1.png`), so
    `dfeed` presses 7 % of the page back in every frame and each bar-line reprint replaces the bled page.
    Captions were rewritten as whole sentences and measured with evalTextSize: the widest is 1123 px.
  - Input, where it enters: `src.frag` lays the picture down as ink instead of the take's own shape (what
    differs from the picture's average brightness becomes ink, hues split across the three inks) and `dye`
    presses it in again on every beat (`infeed`, `inbeat`), so it keeps re-forming while the drums tear it.
    The sheet take (`inmode` 2) instead puts the picture under the water as the paper and keeps its red stamp.
    `ctl/hasin` is 0 for a blank path, a missing TOP or this scene's own out1, and then every uniform is as before.
  - Weak: in Describe the page is easy to read in quiet passages and half-smeared in loud ones
    (`p4c_1.png`, `fin_d4_0.png`) until the next bar line. The big ink words on the phrase take are torn up
    within about 3 s, as they are meant to be; the caption carries the explanation. Marbling, night, sinking
    and survey have only the caption. The Describe sheet is labels, not sentences, and ink covers parts of it.
    With Input, phrase, marbling and macro give nearly the same picture (glossy letters in one ink over a
    haze; marbling loses its bands), and the picture's colours mostly turn to a soft tinted haze. Best with
    Input: survey (7), oil (5), sinking (6), inkblot (3), sheet (9). Input was only tested with the test card.
- 2026-11-10 second pass (art director), final: `takes_sheet.png`, `takes_arrival_sheet.png`,
  `takes_late_sheet.png` (seed 0.41, from a clean rebuild), `hero.png` = `f3_1.png` (inkblot). Ten takes.
  Still only judged from stills. Known weak: oil at 6 s is busy and shows stair-steps on sheared letter edges
  (`f5_2.png`); inkblot gets heavy by 6.5 s when kicks are dense (`k3_2.png`); the caption can sit over ink.
- 2026-11-10 second pass r2 `k_sheet.png` (seed 0.63, 0.3 / 3 / 6.5 s). Oil bands 2.4 -> 0.85: at 2.4 the
  haze became moire lines (`n5_2.png`). Page showed a ghost second print at the cut (`k4_0.png`): the feed's
  section ramps between integers (21.67 seen) and the stamp position followed it; position now uses int(section).
- 2026-11-10 second pass r1 `n_sheet.png` (seed 0.27). New: inkblot (mirror in shade, src mode 6, caption TOP
  into grade), oil film (shade style 3), survey contours on graph paper (shade style 4), page reprint on the
  bar line (restamp=2). All four worked first time.
- 2026-11-10 second pass r0 `judge_sheet.png` (seed 0.27, the first builder's nine takes at 0.3 / 2.5 / 6.5 s).
  Seen: nine different arrivals; by 6.5 s night and jets were the same picture, halftone was mud, and the page
  had dissolved to a nearly empty white frame with a few stars (`j4_2.png`). Marbling, sinking, sheet and macro
  were strong and left alone.
- 2026-11-10 r8 final: `takes_sheet.png`, `takes_arrival_sheet.png`, `take_0.png` .. `take_8.png`,
  `hero.png` (= take 1), `final_rebuild.png` (clean rebuild from build.py, take 3 seed 0.55, 5 s in:
  three sunk silhouettes in green, brass and red plumes). tox and snapshot written, Preview off.
- 2026-11-10 r7 `sheet_d.png` (seed 0.82, takes 0, 1, 2, 8 at 0.3, 2, 4, 7 s). Marbling smoother with
  less confinement; night no longer blown out; halftone drops finer (0.028) with some dissipation.

- 2026-11-10 r6 `sheet_c.png`, `sheet_c2.png` (seed 0.17). Restamps now land at a new place per section
  (before, the next phrase printed on top of the wreck of the last and read as clutter: `b0_2.png`).
  Jets take opens with three fat drops instead of a black frame. Found the held pitch was 15: the feed
  ramps between 0 and the note, so the gate is now "between MIDI 36 and 90". Marbling band edges show
  saw-teeth where jets shear them (`c1_1.png`): lowered vorticity confinement for that take.
- 2026-11-10 r5 `sheet_b.png`, `sheet_b2.png` (seed 0.63). Nine takes, reordered so the first visits
  differ most. Added the glow pass (bright -> blur -> grade), the arrival shove, a different ink per
  kick for the jets take, a per-seed inverted 1-bit page. Night take was blown out to a white blob.
- 2026-11-10 r4 `sheet_a.png`, `sheet_a2.png` (seed 0.3). First eight takes from the TAKES table. The
  page take turned to grey mush in 2 s (too much stir, no dissipation); halftone background too faint.
- 2026-11-10 r3 `sheet_05.png`, `05_4.png`. First good frames: a black phrase torn into mushroom
  plumes by red star blasts. Soft haze around sheared ink, so `shade` got a "crisp" curve.
- 2026-11-10 r2 `sheet_03.png`, `sheet_04.png`. The text vanished the moment the stamp let go. Cause:
  a "scene was not cooking" reset (`absTime.frame - proj.cookAbsFrame > 3`) fired on every long frame,
  and my own capture made long frames. Removed; the shot id in the loops' alpha is enough.
- 2026-11-10 r1 `sheet_02.png`. Kick as a divergence source ("true" radial blast): in a closed tank the
  solver turns it into outflow everywhere and the whole picture is pushed off and blurred. Replaced by a
  star of jets, which the projection turns into mushroom dipoles.
- 2026-11-10 r0 `01_first.png`. Pipeline runs first time, but forces were about 10x too strong
  (velocities at the clamp, picture shredded in a second). Rescaled.
