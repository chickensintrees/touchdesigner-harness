# The asset pack

This folder is the asset pack that ships with the repository. The scene engine looks here for its 3D models, fonts, lettering and music. Everything in it was generated for this project.

![The sixteen objects in the pack, front and back](../docs/media/asset-pack.jpg)

## What is in it

| Folder | Contents | How it was made |
|---|---|---|
| `models/` | 74 objects and three flat printed sheets. The first sixteen are abstract sculptures and archetypal objects from past, present and future; the other 58 were added on 2026-11-20 in ten groups (nature, monuments, broadcast, roadside, machines, music, characters, plastic, sport, arcade) so that each scene shows its own objects (`tests/test_model_spread.py`). Each model has a `model.obj` (30,000 triangles), a `basecolor.png` (1024 px) and an `info.json` with its prompt. | Each object started as a concept image from a text prompt (Krea 2 Turbo) and was turned into a textured mesh by TRELLIS.2. The first sixteen prompts are in `tools/assets/objects.json`; every model's prompt is in its `info.json`. |
| `sheets/` | The three flat sheets as images: a star chart, a blueprint and a ticket. | Generated as images from text prompts. |
| `fonts/` | Archivo Black, Barlow Condensed Bold and Medium, and IBM Plex Mono Medium, each with its licence text (`OFL-BarlowCondensed.txt` covers both Barlow weights). | Open Font License typefaces. Barlow Condensed Medium was added on 2026-11-23 from the Google Fonts repository (`ofl/barlowcondensed`) for the title card's small lines. |
| `art/` | Two pieces of lettering as large PNG files. | Rendered from the fonts by `tools/assets/make_art.py`. |
| `music/` | Two instrumental tracks: `drive` (fast, four-on-the-floor) and `drift` (slow, sparse). | Generated from text prompts with the ElevenLabs Music API by `tools/assets/make_music.py`. |
| `feeds/` | The analysis of each track: the loudness of each stem, beats, bars, sections and drum hits, looked up by track time. | Stem separation and analysis, then `tools/audiofeed/bake_feed.py`. |
| `aliases.json` | A table that names a stand-in for a file the pack does not hold. | Written by `tools/assets/make_aliases.py`. |
| `footage/` | Eighteen short clips of found footage (1280x720, 16 fps, 81 frames, silent): a beach, a parade, a roller rink, a studio and so on. `footage.json` lists them. Played by `experiments/sw_footage`. | Generated from text prompts with Wan 2.2 (text to video). Filed by `tools/assets/file_generated.py --footage <folder>`. |
| `rooms/` | Six photographs of rooms with a switched-off television in them, each with `mask/<name>.png` (white where the glass is). `rooms.json` and `rooms.tsv` hold, for each room, the four corners of the screen and the matrix that places a picture on it. Used by `experiments/screen_room`. | Generated from text prompts with Krea 2 Turbo; the corners were found from the dark screen. Filed by `tools/assets/file_generated.py --rooms <folder>`. |
| `image_sets/` | Two prepared image sets (see `tools/imageprep`): `generated_depth`, 16 stills of places with a depth map each, used by `experiments/im_depth_relief` and `experiments/sw_images`; and `generated_cutouts`, 37 stills of single subjects with a cut-out each, used by `experiments/im_montage`. | Stills generated from text prompts with Krea 2 Turbo; depth maps by MoGe, cut-outs by BiRefNet; then `tools/imageprep/prepare.py`. Your own pictures go in the repository's top-level `image_sets/` folder, which git ignores. |

More preset and asset packs are planned for future releases.

## How the scenes use it

A scene asks for an asset by name, for example the model `amphora`, the sheet `blueprint` or the lettering `art/mark_rgb.png`. Each scene keeps its words, the names of its models and the tuning for each model in one table at the top of its `build.py`, and those defaults are written for this pack.

`aliases.json` lets a pack answer a name with a different file. This pack uses it once: the scenes ask for a typeface called `chicago`, and the pack answers with IBM Plex Mono.

If a file is missing and has no alias, the scene falls back to what TouchDesigner ships with: its bundled teapot for a model, its default typeface for a font, and its own sample track for music.

## Replacing a scene's words and models

A pack can change what a scene shows without any change to the scene's code.

- **`scenes/<scene>/words.json`** replaces entries of that scene's table of defaults. Each top-level name in the file replaces the entry of the same name, and must be the same kind of value (a list for a list). Names the scene does not have are ignored. The file is read when the scene is built, so rebuild the scene after changing it.
- **`scenes/<scene>/<file>`** replaces a data file the scene keeps in its own folder, for example the beam paths that `sc_vector_scope` bakes from models and words.

## Using your own assets

There are three ways to use other files.

- **Replace or add files here.** A folder under `models/` with the name a scene asks for is used in place of the alias. A track appears in the hub when it has both `music/<name>.wav` (or `.mp3`) and `feeds/<name>/feed.chan` with `feed.json`.
- **Keep a separate pack.** Put the path of another folder with the same layout on the first line of a file named `assets.local.txt` in the repository root. That file is ignored by git. The engine then uses that folder instead of this one, and its tracks are added to the hub's list.
- **Set `TDH_ASSETS`.** Setting this environment variable to a folder before starting TouchDesigner does the same for one session.

To see a single scene with no assets at all, set that scene's `Assets` parameter to an empty folder.

To convert your own GLB models into the format used here, run `tools/models/convert_models.py` with Blender. It joins each model into one mesh, centres it, scales its longest side to 1 unit and extracts its colour image.
