# Scene brief: how to build a scene for the audio engine

Written 2026-11-10 against TouchDesigner 2025.33230 and the hub built by `experiments/sw_hub/build.py`, and revised 2026-11-11 for the asset pack that ships with the repository. Every fact below was checked live; if one turns out wrong, trust TouchDesigner and fix this file.

## What the engine is

An audio-reactive engine that cuts between many scene networks in time with the music. Each scene is one self-contained network using a different technique. The hub (`/project1/sw_hub`) plays the track and publishes the analysis; the cutter (`/project1/sw_cut`) shows one scene at a time. This brief is the contract for building **one scene**. A scene should be beautiful, new and strange rather than safe. It uses text and/or 3D models from the asset pack, and it must visibly follow the music.

The repository ships a generic asset pack in `assets/` (section "The asset pack" below). A scene's source carries generic words and asks that pack for its models by their real names. Anybody may keep a second pack of their own with other words, models and baked data, and every scene must pick those up without a change to its source (section "Words, models and tuning belong to the pack").

## Variety is the brief

The first cut of eight scenes was too repetitive, and it needed more variety and more exploration of techniques. The repetition had three causes, and every scene must work against them:

1. **A scene looked the same every time it came back.** The cutter returns to a scene many times in a track. Each return is a new **take**: the cutter sets the scene COMP's `Take` parameter (0, 1, 2, ... counting that scene's visits) and `Seed` (0 to 1, different every shot) *before* the scene appears, and they hold for the shot. Read them from the `shot` CHOP the scaffold makes: `op('shot')['take']`, `op('shot')['seed']`, `op('shot')['age']` (seconds since the cut). A scene must have **at least six takes that differ at a glance**: not a hue shift, but a different composition, camera distance and angle, subject, palette, scale, or mode of the technique (macro detail against wide establishing shot, top-down against side-on, positive against negative, one object against many). Keep them in a `TAKES` table in build.py, select with `take % len(TAKES)`, and use `seed` for further variation inside a take (offsets, rotation, which phrase, which model) so that even the seventh visit is new. Test by setting the COMP's `Take` and `Seed` parameters by hand and capturing each take.
2. **Almost every scene put one big wordmark in the middle of the frame.** The centred wordmark must not be the default image. Use the scene's whole word list, use text as texture, structure, fragments and edges, let some takes have no readable word at all, and compose off-centre.
3. **Every scene was "one subject, mid-shot".** Vary scale and density between takes: extreme close-up, full-frame pattern, tiny subject in a big field, many subjects.

A shot lasts about 2 to 9 seconds. Something should happen in its first half second (use `op('shot')['age']`): an arrival, a snap, a reveal.

Scenes that already exist (do not rebuild their technique under another name):

| Scene | Technique |
|---|---|
| `sc_rd_stamp` | reaction-diffusion ink growing from stamped lettering on a printed sheet |
| `sc_time_slab` | slit-scan time displacement of a spinning 3D object |
| `sc_point_morph` | a point cloud sampled from models, morphing between them |
| `sc_glyph_render` | a 3D scene redrawn in 1-bit bitmap type |
| `sc_kifs_office` | a ray-marched folded fractal building with lettering in relief |
| `sc_paper_storm` | thousands of instanced printed sheets flying in formations |
| `sc_spectral_terrain` | a landscape whose height is the recent spectrum, with extruded words |
| `sc_flow_mosh` | optical-flow datamosh of posters |
| `sc_droste_crt` | real video feedback: a screen that shows its own camera |
| `sc_exploded_view` | models drawn as exploded engineering line art |
| `sc_fluid_ink` | a 2D fluid simulation of inks laid down as words and silhouettes |
| `sc_kinetic_type` | moving poster typography, one rectangle per letter |
| `sc_light_gobo` | patterned light and shadows as shafts in fog |
| `sc_physarum` | a slime-mould agent simulation growing veins over shapes |
| `sc_riso_press` | spot-colour plates screened and overprinted out of register |
| `sc_rutt_etra` | a picture redrawn as displaced scan lines in 3D |
| `sc_shatter` | models pre-cut into shards that burst and reassemble |
| `sc_vector_scope` | an oscilloscope beam tracing outlines, wireframes and waveforms |

## Describe mode and Input

The scenes are also shown on a public web gallery of techniques, with a sample of each and combinations of presets. Every scene therefore carries two more parameters (the scaffold adds them on rebuild).

**`Describe` (toggle).** When `parent().par.Describe` is on, every word the scene shows must describe what the viewer is looking at: the technique, how it works, what this take is doing, what the music is driving. No phrase from the scene's word bank or from a pack's words appears in this mode, and no jokes. With it off the scene behaves exactly as before.
- Write the words per take, to suit how that take uses text. A take that shows one big word needs one or two strong words (the technique's name). A take that runs long text needs real sentences that explain the mechanism in plain language a designer who has never used TouchDesigner would follow. Lists, tickers and labels should carry true specifics: operator and shader facts, counts, and live values from the feed where the scene already shows numbers.
- Every statement must be true of this scene as built. Do not claim an operator, a number or a behaviour that is not there. Plain words, no hype, no "AI" boasting. Upper or lower case as the take's design needs. Straight quotes and plain hyphens only.
- Keep the words in build.py beside the take (for example a `describe` entry in each TAKES row), and mirror them into `experiments/<slug>/preset.json` as `"words": [...]` on each take, in the order they are used. Describe words belong to the scene, not to a pack, so they stay out of the defaults dict described below.
- Takes with no readable text need no words (`"words": []`), but if a take could carry a small label naming the technique without hurting the picture, add one in Describe mode.
- Anything baked at build time from the word list (atlases, outlines, pre-rendered sheets, tables) must also exist for the Describe words, so switching the toggle needs no rebuild and causes no hitch.

**`Input` (text: the path of a TOP).** Combining presets: when `parent().par.Input` names a TOP (normally another scene's `out1`, 1280x720), the scene uses that moving picture as its raw material in place of (or wrapped around) its own source, and applies its technique to it. Blank means the scene's own source, exactly as before. Find the place in the network where a picture enters the technique and put a Switch there: the image a shader re-draws, the texture on a model or sheet, the attractant or dye or gobo mask, the screen inside the monitor, the thing that gets shattered, printed, scanned, moshed or time-sliced. If the scene has no picture input at all, give it one that makes sense (a texture on its surfaces, a mask, a displacement source) so that it can still be the second half of a combination. A scene must never read its own out1 (a cook loop), and must not cook the other scene: only read the TOP.
- Test with the shared test picture `/project1/sw_testcard/out1` (an always-cooking moving image with the words TEST INPUT, built by `experiments/sw_hub/testcard.py`): set `Input` to it, capture at least three takes, and check that the input is recognisably there and the technique is recognisably applied. Then blank it and confirm the scene is as before.
- Record in preset.json: `"accepts_input": true`, and `"as_processor"`: one plain sentence saying what the scene does to a picture it is given.

## Portability

Nothing in the repository may name a folder on somebody's machine: not in a builder, a shader loader, a note, a snapshot or a saved .tox. `python -m pytest -q tests/test_portable.py -k <slug>` fails if an experiment's tracked files contain one, including inside the binary .tox.

- **Where the repository is.** The repository is wherever the open project file is saved. In a builder script use `td.project.folder` (or the scaffold's `LIB['repo']()`); never a literal path.
- **Every parameter that names a file is an expression.** The scaffold installs a module DAT in the scene COMP at `local/modules/paths` (source: `experiments/sw_hub/paths_module.py`), reachable from any operator inside the COMP as `mod.paths`. Set file parameters like this, through execute-python:
  - a file in the experiment's folder: `dat.par.file.expr = "mod.paths.here('shaders/sim.frag')"`
  - a baked data file that a pack may replace: `"mod.paths.scene_file('paths.npz')"` (see "Baked files load through `scene_file`")
  - a font: `text.par.fontfile.expr = "mod.paths.font('chicago')"` (also `'archivo'`, `'barlow'`)
  - a model or its texture: `mesh.par.file.expr = "mod.paths.model_file('gramophone')"`, `tex.par.file.expr = "mod.paths.model_texture('gramophone')"`
  - any other asset: `"mod.paths.asset('art/mark_alpha.png')"`
  A constant value would bake one machine's folder into the .tox and the snapshot, so constants are not allowed for file parameters. Inside DAT scripts and callbacks use `mod.paths...` or `project.folder` the same way.
- **Which pack answers.** `mod.paths.assets()` is, in order: the scene COMP's own `Assets` parameter if it is set, then the `TDH_ASSETS` environment variable, then the folder named on the first line of `assets.local.txt` in the repository root (a file git ignores, for a pack kept to oneself), then `<repo>/assets`, the pack that ships with the repository. Every pack has the same layout: `models/<name>/model.obj` and `basecolor.png`, `fonts/`, `art/`, `music/`, `feeds/`, and optionally `scenes/<slug>/` and `aliases.json`.
- **Assets are optional.** A scene must **build with zero errors and show a sensible, moving picture when the assets folder is empty**: `mod.paths.model_file` then returns TouchDesigner's bundled teapot, `mod.paths.font` returns an empty string (TouchDesigner's default face), `mod.paths.asset` returns an empty string. Handle each: a Movie File In with an empty file must not leave an error or a black hole in the picture (switch to a generated stand-in: a flat colour, a ramp, a Text TOP), a texture that is missing must not break the material, and data precomputed from a model or a font (outlines, point sets, atlases, key layouts) must either be committed in the experiment folder as a small data file or be regenerated from whatever `mod.paths` returns.
- **Precomputed data and helper scripts.** Anything a builder reads from disk is either inside `experiments/<slug>/` (committed, addressed with `mod.paths.here(...)`, `mod.paths.scene_file(...)` or `LIB['experiment'](slug, rel)`) or under assets with a fallback. Helper scripts in the folder follow the same rule.
- **Notes and cards.** NOTES.md, preset.json and comments may mention files only by repo-relative path (`experiments/<slug>/captures/x.png`) or as `<assets>/...`.
- **The hub.** With no music in any pack the hub plays TouchDesigner's bundled sample track, whose feed ships in `experiments/sw_hub/sample_feed/`. The feed's channels are the same, so a scene needs no change for that.

How to prove it, in this order:
1. With the shipped pack: set the scene's `Assets` parameter to the repository's `assets` folder (an absolute path built from `project.folder`), rebuild, and capture every take. This is what a stranger who clones the repository sees, so it is the picture that matters most.
2. With assets absent: set `Assets` to an empty folder created under the experiment's `captures/` (for example `captures/_noassets`, again built from `project.folder`), rebuild from build.py (the scaffold keeps the parameter across the rebuild), and check `tdh.errors` is empty and at least three takes show a moving picture (capture and look). This affects only the one scene. Do not set the `TDH_ASSETS` environment variable for this: it is shared by the whole TouchDesigner process and would switch every other scene to fallbacks.
3. Blank the `Assets` parameter and rebuild, so the scene is back on the machine's normal pack. On a machine with a pack of its own named in `assets.local.txt`, confirm that pack's version looks as it did before. Leave the parameter blank.
   Builder scripts that need a path at build time (to read a model or font and precompute something) must ask the installed module, `LIB['scene_paths'](scene).model_file('gramophone')`, not `LIB['model_file']`, because only the installed module sees the `Assets` parameter.
4. `tdh.save_tox`, `tdh.snapshot`, then `python -m pytest -q tests/test_portable.py tests/test_generic.py -k <slug>` passes.

## Words, models and tuning belong to the pack

A scene's source is public and generic. Everything in it that is content rather than technique must be replaceable by a pack without editing the scene. Three rules make that work.

**One defaults dict, read through `scene_words`.** A scene keeps its words, the names of the models it uses, and any per-model tuning in a single dict in build.py, and reads it once at build time, after `new_scene` has made the COMP:

```python
DEFAULTS = {
    'LINES': ['SIGNAL FOUND.', 'KEEP TIME.', 'A PICTURE OF A SOUND.'],
    'TITLE': 'REAL TIME',
    'MODELS': ['gramophone', 'astrolabe', 'hourglass'],
    'SHEETS': ['star_chart', 'blueprint', 'ticket'],
    'TUNING': {'gramophone': {'scale': 1.1, 'yaw': 20.0}, 'astrolabe': {'scale': 0.9, 'yaw': 0.0}},
}

scene = LIB['new_scene']('<slug>')
W = LIB['scene_words'](scene, DEFAULTS)     # after new_scene: the module DAT must exist
lines, models = W['LINES'], W['MODELS']
```

`scene_words` returns a copy of the dict in which any top-level name is replaced by the value of the same name in `<pack>/scenes/<slug>/words.json`, when the active pack has that file. The rest of the builder uses only the returned dict, never `DEFAULTS` directly and never a literal phrase or model name somewhere else in the file.

- A replacement is whole: a pack that gives `LINES` replaces the entire list. Names the scene does not have are ignored.
- A replacement must be the same type as the default (text for text, list for list, dict for dict, and a whole number stays a whole number); otherwise the build raises a ValueError naming the file and the key. Use only types JSON can hold: lists, not tuples.
- Code that reads the dict must not assume the default's length. A pack's list may be longer or shorter, so index with `% len(...)`, and look per-model tuning up with a fallback (`W['TUNING'].get(name, {})`) because a pack's models are not the scene's.
- Anything tuned to one model (scale, yaw, camera distance, which face reads best, which texture region is the label) goes in the dict beside the model's name, so that a pack that swaps the model can swap the tuning with it.
- Read the dict once, at build time. It is not a live control; the words a person would want to change while playing still go on the `Controls` page.

**Baked files load through `scene_file`.** Data baked from models, fonts or words (outlines, point sets, shard meshes, atlases) is committed in the experiment's folder, baked from the generic pack, and loaded with `mod.paths.scene_file('<file>')` in a parameter expression or `LIB['scene_paths'](scene).scene_file('<file>')` in the builder. `scene_file(rel)` returns `<pack>/scenes/<slug>/<rel>` when the active pack has that file and `experiments/<slug>/<rel>` otherwise, so a pack can supply data baked from its own models. A baked file must match what the words dict names: if the pack replaces `MODELS`, it also supplies the baked files made from them.

**Source asks for real names.** A scene asks the shipped pack for its models by the names in the next section. The shipped `aliases.json` still answers a few older names with stand-ins; that table is a safety net, and new source must not rely on it. `python -m pytest -q tests/test_generic.py -k <slug>` checks that a scene's tracked files carry no content of a private pack.

## The shared machine: rules that protect everyone

Up to ten agents may be building in the **same** TouchDesigner instance at the same time. The cutter (`/project1/sw_cut`) may also be running and showing scenes, including the one being built: it will change that COMP's `Take`, `Seed` and `Shotstart` parameters during the work. Set them back to the values under test in the same call as the capture.

- Work only inside the scene's own COMP `/project1/<slug>` and its own folder `experiments/<slug>/`. Never edit, cue, re-point or delete anything else: not `/project1/sw_hub`, not other scenes, not `mcp_webserver_base` or `TDMCP`, not the timeline.
- Never call `project.save()`. Never `time.sleep` or loop for a long time in TouchDesigner: all Python runs on its main thread and every other agent waits behind it.
- Do not run git commands that write (add, commit, checkout, stash) while others share the checkout. One coordinating session commits.
- If the bridge stops answering, retry a few times a few seconds apart. Never launch TouchDesigner. If it stays down, stop and report it.
- Budget: output 1280x720, 16-bit float where it matters. Stay under about 8 ms of GPU+CPU cook for the scene. Caps: ray-march at most 80 steps, at most 250k points, at most 4 full-resolution feedback or blur passes, Cache TOPs at most 64 frames at 640x360. No downloads.
- When the work is finished, leave the scene's `Preview` toggle **off** so it stops cooking.

## Tools

TouchDesigner is driven through the `touchdesigner` MCP server. Load the tools with ToolSearch: `select:mcp__touchdesigner__execute_python_script,mcp__touchdesigner__get_top_image,mcp__touchdesigner__get_td_node_errors,mcp__touchdesigner__get_td_node_parameters,mcp__touchdesigner__get_td_class_details,mcp__touchdesigner__get_td_module_help`.

- `execute_python_script` runs each call in a fresh namespace and evaluates the **last line twice**. End every script with a bare variable (`r`) and never with a call that has side effects. Use `detailLevel: "detailed"` to see full results.
- A NaN or numpy value in the returned object makes the call fail with "Unknown error occurred". Return `str(...)` or `float(...)` of anything that comes from a CHOP or TOP.
- `tdh` (this repo's toolkit) is already loaded: `import tdh`, then `tdh.errors(path)`, `tdh.capture(top_path, 'experiments/<slug>/captures/01.png')`, `tdh.stats(top)`, `tdh.check('experiments/<slug>/checks.json')`, `tdh.save_tox(comp, 'experiments/<slug>/<slug>.tox')`, `tdh.snapshot(comp, 'experiments/<slug>/snapshot/network.json')`. Relative paths resolve against the repo root.
- `get_top_image` shows a TOP directly. Look at the output often. Describe what is actually there.
- Look parameters up, do not remember them: `[p.name for p in op(x).pars()]`, `par.menuNames`, `get_td_class_details`.

## A scene's shape

The builder is a real file, `experiments/<slug>/build.py`, run inside TouchDesigner with:

```python
g = {'op': op, 'td': td, '__name__': 'build'}
exec(open(project.folder + '/experiments/<slug>/build.py', encoding='utf-8').read(), g)
path = g['build']()
```

It must be **idempotent**: running it again destroys and rebuilds the whole scene. That is the recovery path if TouchDesigner crashes, so keep it current; do not leave hand-made changes that exist only in the live network. GLSL goes in `experiments/<slug>/shaders/*.frag` (Text DAT with `file` set and `syncfile` on).

Start from the scaffold:

```python
LIB = {'op': op}
exec(open(td.project.folder + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
scene = LIB['new_scene']('<slug>')        # COMP with out1, hub, spectrum, shot, cook_driver, Preview toggle
W = LIB['scene_words'](scene, DEFAULTS)   # the scene's words, model names and tuning (see above)
geo = LIB['import_model'](scene, 'subject', W['MODELS'][0])   # optional: a pack model
```

`new_scene` gives:
- `out1`: the Out TOP. Wire the final image into it. 1280x720.
- `hub`: a Select CHOP carrying the audio feed (below). Reference it as `op('hub')['pulse']`.
- `spectrum`: a 512x1 32-bit float mono TOP of the live spectrum, 0-4.8 kHz left to right. Values are tiny (about 0.0005 to 0.01): multiply by a few hundred. (`TRAPS.md`, under `sc_spectral_terrain`, explains why a scene that needs real spectral peaks should read the hub's `specraw` instead.)
- `shot`: a Constant CHOP with `take`, `seed` and `age`, driven by the COMP's `Take`, `Seed` and `Shotstart` parameters, which the cutter sets (see "Variety is the brief").
- `cook_driver`: cooks `hub` and `out1` every frame while the scene is on screen or its `Preview` toggle is on. Anything that must advance every frame has to be upstream of `out1`, or be added to the driver.
- the parameters `Take`, `Seed`, `Shotstart`, `Describe`, `Input`, `Assets` and `Preview`, and the module DAT `local/modules/paths`. `new_scene` keeps the `Assets` value across a rebuild.

## The audio feed (`op('hub')`)

One sample per channel, updated every frame, read from the track's position. The values come from offline analysis of the track (stems separated by HTDemucs), plus two live channels.

| Channel | Meaning |
|---|---|
| `t` | track time in seconds |
| `track_pos` | 0 to 1 through the track |
| `rms` `bass` `drums` `vocals` `other` | loudness of the mix and of each stem, about 0 to 1 (1 = that stem's loud level; peaks can pass 1) |
| `energy` | 2-second average loudness, about 0 to 1: the slow intensity of the passage |
| `pitch` `pitch_conf` | vocal pitch as a MIDI note number (0 when not singing), and confidence 0 to 1 |
| `bass_pitch` | bass note as a MIDI number (0 when none) |
| `beat` `bar` | phase 0 to 1 through the current beat and bar |
| `beat_i` `bar_i` | whole beat and bar counters (can be negative before the first beat) |
| `pulse` `bar_pulse` | 1 on the beat or bar line, decaying to 0: the simplest thing to drive a kick |
| `beat_pos` `bar_pos` | continuous counters (beat number plus phase) for smooth motion locked to tempo |
| `section` `section_pos` | index of the current musical section, and 0 to 1 through it. Sections change every 5 to 20 seconds on the shipped tracks: use the index to change state (model, phrase, palette, camera) |
| `hit_low` `hit_mid` `hit_high` | drum hits as envelopes: jump to the hit's strength, decay over about 0.15 s. Low is kick-like, mid snare-like, high hat-like |
| `hits_low` `hits_mid` `hits_high` | running counts of those hits (step up by 1 at each hit): compare with last frame to trigger something exactly once |
| `onset` `onsets` | the same pair for every note attack in the mix |
| `level` | live loudness of what is playing now, about 0 to 0.5 |
| `evolve` | time that runs faster when the music is loud: use it instead of `absTime.seconds` for drift and camera travel |

The shipped pack has two instrumental tracks, and the hub's `Track` parameter (or `set_track(slug)` in the hub's build.py) chooses between them. The figures are the ones in each track's `<assets>/feeds/<track>/feed.json`:

| Track | Character | Length | Tempo in the feed | Beats | Bars | Sections |
|---|---|---|---|---|---|---|
| `drive` | fast, four-on-the-floor | 180.0 s | 125.0 bpm | 231 | 58 | 19 |
| `drift` | slow, sparse | 210.1 s | 157.9 bpm | 414 | 104 | 28 |

Both tracks loop. Both are instrumental, so `vocals`, `pitch` and `pitch_conf` may stay near zero for long stretches: a scene must not depend on them for its main motion. A pack of one's own adds its tracks to the hub's list (a track appears when the pack has both `music/<name>.wav` or `.mp3` and `feeds/<name>/feed.chan` with `feed.json`), so nothing in a scene may assume a track's length, tempo or loudness range. Do not seek the track. To see a scene at different moments, capture several times a few seconds apart, and read the feed in the same call to know what the music was doing.

Expressions are Python: `math.sin`, not `sin`. Set them with `op(x).par.y.expr = "..."` through execute_python_script.

## The asset pack

What the shipped pack (`<repo>/assets/`, described in `assets/README.md`) holds. Everything in it was generated for this repository; the prompts are in `tools/assets/objects.json`.

**Models** (`<assets>/models/<name>/`): each has `model.obj` (one joined mesh, centred on the origin, longest side 1 unit, Y up, normals `N` and UVs `Tex` as vertex attributes), `basecolor.png` and `info.json` (triangle count, size, prompt). `LIB['import_model'](scene, name, slug)` builds a Geometry COMP called `name` with `mesh` (File In POP), `tex` and `mat` (PBR MAT) from the model `slug`. TouchDesigner's FBX COMP does **not** read .glb; `tools/models/convert_models.py` (run with Blender) converts GLB models into this format.

The sixteen objects:

| Group | Names |
|---|---|
| abstract sculptures | `ribbon_loop` (a bronze ribbon knot on a plinth), `pierced_stone` (white marble with two holes), `balanced_solids` (sphere on cone on cube on cylinder, painted steel), `crystal_cluster` (black obsidian), `wire_cage` (a geodesic steel cage with a sphere inside) |
| archetypes | `marble_bust`, `hourglass`, `skeleton_key`, `broken_column` |
| from the past | `amphora`, `astrolabe` (a brass armillary sphere), `gramophone` |
| from the present | `traffic_cone`, `rubber_duck` |
| from the future | `space_helmet`, `lander` (a gold-foil lunar lander) |

The three flat sheets, each a thin slab model (12 triangles) with the print as its texture, also available as plain images in `<assets>/sheets/<name>.png`: `star_chart` (constellations on cream paper), `blueprint` (white lines on deep blue), `ticket` (a pink admission ticket with a serial number).

Each object is a single textured mesh of about 29,000 triangles (the count is in its `info.json`), so do not instance the objects by the hundred.

**Fonts** (`<assets>/fonts/`, Open Font License, licence texts beside them)
- `mod.paths.font('archivo')`: Archivo Black, a heavy poster face.
- `mod.paths.font('barlow')`: Barlow Condensed Bold, a tall condensed face.
- `mod.paths.font('chicago')`: the slot for a bitmap-style or monospaced face. The shipped pack answers it with IBM Plex Mono Medium (through `aliases.json`); another pack may hold a true bitmap face there. A scene that draws pixel-exact type must therefore measure the face it is given (`textTOP.evalTextSize`) and not assume glyph widths.

**Lettering art** (`<assets>/art/`, 1920x1440 PNG files made from the fonts by `tools/assets/make_art.py`)
- `art/mark_rgb.png`, `art/mark_alpha.png`: the word HARNESS on one line.
- `art/stack_rgb.png`, `art/stack_alpha.png`: the words REAL / TIME stacked on two lines.
The `_rgb` files are white lettering on black; the `_alpha` files are white lettering with the shape in the alpha channel. Ask for them by these names: a pack with its own lettering answers the same names through its `aliases.json`. The Non-Commercial licence limits any TOP to 1280x1280, so set the Movie File In to a smaller custom resolution.

**Music and feeds**: `<assets>/music/drive.mp3`, `drift.mp3` and `<assets>/feeds/<track>/` (see "The audio feed").

**Words.** The public voice is short, plain and declarative, in capitals, like signage or the labels on test equipment. It talks about sound, signal, time and light, which is what the engine is made of. It is dry rather than funny, and it carries no brand, no story and no reference to a particular place. A starting bank, to use, cut up or replace in a scene's defaults dict:

HARNESS / REAL TIME / SIGNAL FOUND. / LISTENING... / KEEP TIME. / COUNT IN: 1 2 3 4 / ONE BAR AT A TIME. / EVERY FRAME IS NEW. / SIXTY FRAMES A SECOND. / A PICTURE OF A SOUND. / LOUD IS A COLOUR. / THE BEAT IS A CLOCK. / BASS MOVES THE FLOOR. / NOTHING HERE IS RECORDED. / INPUT 1 / LEFT. RIGHT. / SIDE A / TEST PATTERN / PLEASE STAND BY. / END OF SIGNAL

A scene should not use the bank whole: choose and write the few words that suit its technique, and keep them in its defaults dict.

**Palettes** (use, bend or ignore)
- Warm neutrals: grey #7D7E77, putty #C8BFA6, wall #D6CDB5, pale green #DCE4C6 / #6C7860, tube blue #7E9BB0, cream paper #EDE3C8, signal red #A8322B, brass #B5935A, amber #C8892F.
- Poster: ink #192B3B, ivory #EEE4CC, red #DC563D, yellow #DCB53D, blue #287E9B, green #99AB54, pink #B85779.
- 1-bit: pure #000000 and #FFFFFF, dithered.

## Traps already paid for

More, technique by technique, from the first eight builders: `experiments/sw_hub/TRAPS.md`. Read it before starting; it will save an hour. The existing scenes' `build.py` and shader files are working examples of GLSL TOPs with uniforms, feedback loops, instancing, model lighting and text atlases in this build: read the one nearest the technique in hand.

- TouchDesigner cooks on demand. Feedback, Lag, Trail and Cache operators freeze unless something cooks them each frame. Check `op.totalCooks` rises between two calls before believing an animation is dead or alive.
- Feedback TOP does not inherit pixel format: set `par.format` (for example `rgba16float`) and pulse `resetpulse`. A Composite in a loop defaults to multiply: use add, over or maximum. Additive feedback settles at `1/(1-decay)` times the input, so it blows out; use maximum or a decay under about 0.9 with a dim source.
- GLSL TOP: write `out vec4 fragColor;` and `void main()`, sample inputs with `texture(sTD2DInputs[0], vUV.st)`, end with `fragColor = TDOutputSwizzle(color);`. Declare every uniform yourself, then set it on the GLSL TOP's Vectors page (`vec0name`, `vec0valuex`...). Uniforms default to 0. Compile errors appear as warnings in `tdh.errors`. The Text DAT loads its file a frame after it is set.
- `geo.par.material = '../mat'` silently falls back to grey: use an absolute path. PBR MAT defaults (metallic 1, roughness 1) render near black: the scaffold sets 0 and 0.6. An Environment Light does nothing without an environment map.
- Multi-input wiring: `src.outputConnectors[0].connect(dst)` appends an input; `connect(dst.inputConnectors[i])` replaces input i. A GLSL TOP is the exception: always use the indexed form there (see `TRAPS.md`).
- Text POP, Sprinkle POP, Point Generator POP, Noise POP, Feedback POP, GLSL POP, Particle POP, Lookup Texture POP, Copy POP, Time Machine TOP, Optical Flow TOP, Cache TOP, Bloom TOP, SSAO TOP, GLSL MAT and Point Sprite MAT all exist in this build. There is no Line TOP, Force POP or Instance POP; instance through the Geometry COMP's Instance page.
- circleTOP softness is in fraction-of-aspect units; hsvadjustTOP hue offset is in degrees.
- `tdh.check`'s cook_budget counts a one-off expensive cook as per-frame cost. With many scenes cooking, global frame rate will dip: judge a scene's own cost from its operators' `cpuCookTime` and `gpuCookTime` (ms).

## Done means

1. `tdh.errors('/project1/<slug>')` is empty (warnings count).
2. At least four captures taken at different moments of the track have been looked at, and the picture differs between them in a way that follows the feed (NOTES.md says which channel drives what).
3. **Every take** has been captured and viewed (set `Take`, capture, name the file `take_<n>.png`), as a contact sheet where possible, and the takes differ at a glance. NOTES.md lists each take in one line.
4. `experiments/<slug>/NOTES.md` states the intent, the technique, the channel-to-visual mapping, a newest-first log of what was tried with capture file names, and what should come next. It is honest about what is weak.
5. `experiments/<slug>/checks.json` (copy `experiments/_template/checks.json`, set the root) passes `tdh.check` on a second run, or NOTES.md says exactly what fails.
6. `tdh.save_tox` and `tdh.snapshot` are written, with `captures/hero.png` as the best frame.
7. A fresh rebuild from `build.py` reproduces the scene (run it once more at the end and look).
8. `python -m pytest -q tests/test_portable.py tests/test_generic.py -k <slug>` passes: no machine paths, and no content of a private pack in the scene's tracked files.
9. `Preview` is off.
