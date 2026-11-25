# touchdesigner-harness

![One second from each of the sixteen scenes of the scene engine built with this harness, rendered live in TouchDesigner](docs/media/scene-engine.webp)

**Audio-reactive scene templates, an asset pack, and the agent harness that built them, for TouchDesigner and Claude Code.**

touchdesigner-harness is built on [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) by 8beeeaaat, and Derivative's [TDMCP](https://github.com/TouchDesigner/TDMCP) also works. It was made by [Bill Moore](https://billmoore.ai) for his own audio-reactive films and live visuals. The project page at **[billmoore.ai/touchdesigner](https://billmoore.ai/touchdesigner/)** has a film of the templates with sound, and every take of every scene.

## What you get

- [16 audio-reactive scene templates](#the-scenes) with 136 takes between them.
- [7 templates](#pictures-footage-and-titles) for working with images, footage and titles.
- [An asset pack](#the-asset-pack) of 3D models, footage, rooms, images, music and fonts that the templates use.
- Audio analysis of the pack's music, and [an editor that cuts between the scenes on the beat](#the-scene-engine).

Each template keeps its controls on one page, so you can swap in your own words, models, pictures and music without opening the network.

## How the harness works

You describe an idea. The harness guides Claude to build a small piece of the network, capture the frame, look at it, compare it with what you asked for, and decide the next step. Before it calls anything done, it runs checks: not black, actually moving, inside the frame budget. Every version worth keeping is committed to git as a `.tox` plus a readable text snapshot of the network, so a diff shows which operators and parameters changed.

For example, asked for "an inward spiral whose colour slowly drifts", Claude's first capture was soft fog and its second had trails running outward. It changed the network after each look, and the third capture matched. [`experiments/feedback_drift/NOTES.md`](experiments/feedback_drift/NOTES.md) logs every step.

Every trap hit while working with TouchDesigner through MCP is now a rule in [`AGENTS.md`](AGENTS.md) or a test, so the next agent can't repeat it.

## What you need

- **TouchDesigner 2025.33230 or newer.** A Non-Commercial license is fine (outputs are capped at 1280×1280).
- **[Claude Code](https://code.claude.com/docs)**
- **Windows or macOS** with a GPU. TD doesn't run on Linux.
- **git, and Node.js 24** for touchdesigner-mcp (22.18+ and 26+ also satisfy it; 24 is the tested one). The install below checks for both and gives you the download link if one is missing or too old.

## Install

Paste this line into Claude Code, in any folder:

```
Set up touchdesigner-harness with me by following https://billmoore.ai/touchdesigner/install.md
```

Claude Code clones this repository and follows [docs/INSTALL.md](docs/INSTALL.md) with you: it checks what is installed, downloads touchdesigner-mcp 2.2.0, and gives you the few clicks that have to happen in TouchDesigner's window, one at a time. It asks before it changes anything outside the clone folder, and it ends by having you start Claude Code in that folder and say *"continue setup"*. The MCP server it registers lets Claude Code run Python inside whatever project is open in TouchDesigner, so the install makes a new lab project: do not use a show file.

To do it by hand, or to use TDMCP, follow [docs/SETUP.md](docs/SETUP.md).

## The scene engine

The scene engine plays a music track and cuts between sixteen scenes in time with it. Every scene was built through the harness, and the picture is rendered live.

- **The hub** ([`experiments/sw_hub/`](experiments/sw_hub/)) plays a track and publishes what the music is doing on every frame: the loudness of each stem, beats, bars, sections and drum hits. The analysis is done ahead of time (stem separation, then beat, section and drum-hit detection), and [`tools/audiofeed`](tools/audiofeed/) bakes its result into the feed file the hub reads. The feeds for the two tracks in the asset pack are included.
- **Sixteen scenes** (`experiments/sc_*/`) each read the hub and apply a different technique. Each scene has several takes (another camera, subject, palette or mode), 136 in all, so a scene looks different each time it returns.
- **The cutter** ([`experiments/sw_cut/`](experiments/sw_cut/)) switches scenes on beat lines, and can add a treatment, a transition or a second scene layered over the first.
- **The control panel** ([`experiments/sw_panel/`](experiments/sw_panel/)) puts the scene, take, treatment, track and volume on one page, so nobody has to read the network.

### Run it

The install offers to build it as its last step. At any later time, ask Claude to *"build the scene engine with experiments/sw_hub/build_all.py"*, or run this in TouchDesigner's Textport:

```python
g = {'op': op, 'td': td, 'absTime': absTime, 'project': project}
exec(open(project.folder + '/experiments/sw_hub/build_all.py', encoding='utf-8').read(), g)
g['start']()
```

It builds the hub, the scenes, the cutter and the panel, then opens the panel beside the output. The timeline must be playing while it builds. On the panel, raise **Speaker Volume** to hear the track (it starts at 0), or turn **Cut With The Music** off to choose a scene and step through its takes with **Next Take**.

### The scenes

The [preset gallery](docs/GALLERY.md) shows every take of every scene.

| Scene | Technique | Takes |
|---|---|---|
| [Monitor showing itself](docs/GALLERY.md#sc_droste_crt) | A monitor on a 3D desk shows the camera's previous frame, so video feedback builds a tunnel of monitors. | 3 |
| [Exploded technical drawing](docs/GALLERY.md#sc_exploded_view) | 3D models are drawn as engineering line art and come apart, with live dimension lines and labels around them. | 10 |
| [Melting poster datamosh](docs/GALLERY.md#sc_flow_mosh) | A deliberate video-compression glitch: a clean picture flashes, then its own motion drags blocks of the last frame around. | 7 |
| [Ink in water](docs/GALLERY.md#sc_fluid_ink) | A 2D fluid simulation in shaders, where words and model silhouettes are laid down as inks over paper. | 10 |
| [Pictures made of type](docs/GALLERY.md#sc_glyph_render) | A 3D scene, or large lettering with real depth, is redrawn in pure black and white from the letters of one bitmap font. | 11 |
| [Letter architecture](docs/GALLERY.md#sc_kifs_office) | One ray-marched shader draws a folded fractal of blocks with lettering embossed into its surfaces, seen as a 1-bit shaft or as a flat red slice. | 2 |
| [Kinetic type machine](docs/GALLERY.md#sc_kinetic_type) | Moving poster typography: every letter is its own small rectangle cut from a font sheet and animated by a shader. | 12 |
| [Fog and shadow type](docs/GALLERY.md#sc_light_gobo) | A dark, foggy room where patterned light and the shadows of objects hang as solid shafts in the air. | 11 |
| [Paper storm](docs/GALLERY.md#sc_paper_storm) | Thousands of copies of a printed sheet are placed and turned by one shader that arranges them into formations. | 3 |
| [Point cloud shapeshifter](docs/GALLERY.md#sc_point_morph) | A cloud of about 124,000 points, sampled from 3D models and lettering, streams from one shape into the next. | 8 |
| [Misregistered print shop](docs/GALLERY.md#sc_riso_press) | A 3D object is split into spot-colour plates, each screened into dots or lines and overprinted out of register. | 14 |
| [Scan line video synth](docs/GALLERY.md#sc_rutt_etra) | A 1970s-style video synthesizer: a picture is redrawn as glowing scan lines in 3D, displaced by its brightness. | 10 |
| [Shatter and reassemble](docs/GALLERY.md#sc_shatter) | 3D models and phrases are pre-cut into rigid shards that burst apart and pull back together exactly. | 10 |
| [Spectrogram terrain](docs/GALLERY.md#sc_spectral_terrain) | The last few seconds of the sound spectrum become a landscape of glowing ridge lines receding from the viewer. | 7 |
| [Time-sliced objects](docs/GALLERY.md#sc_time_slab) | A slit-scan effect: every part of the picture shows a different moment of a spinning 3D object. | 7 |
| [Oscilloscope beam drawings](docs/GALLERY.md#sc_vector_scope) | A simulated oscilloscope: one glowing beam traces word outlines, 3D wireframes and waveforms with fading phosphor afterglow. | 11 |

A scene can also take another scene's picture as its input and work on that in place of its own subject. Set the scene's **Input** parameter to the other scene's output.

### Pictures, footage and titles

Seven more experiments work with photographs, video and type. Each has its own folder and can be built alone, and the cutter can show any of them in a shot list.

| Experiment | What it does |
|---|---|
| [`sw_footage`](experiments/sw_footage/) | Plays a folder of video clips as channels and changes channel on a bar line, with a roll, a tear and a burst of snow. |
| [`sw_finish`](experiments/sw_finish/) | Gives any picture the texture of 35mm film, VHS tape, a CRT tube or a 1-bit screen. |
| [`screen_room`](experiments/screen_room/) | Shows any picture on the switched-off television in a photograph of a room. |
| [`sw_images`](experiments/sw_images/) | Plays a prepared image set in colour order, so photographs can be the Input of any scene. |
| [`im_depth_relief`](experiments/im_depth_relief/) | Pushes each photograph out into a relief of points by its depth map and streams the points into the next one. |
| [`im_montage`](experiments/im_montage/) | Stands cut-outs as paper cards at different depths in front of a printed ground while a camera drifts past. |
| [`id_title_card`](experiments/id_title_card/) | Sets a phrase from a control on a grid, a different way on each of five takes. |

To use your own photographs, prepare a set from a folder of pictures with `python tools/imageprep/prepare.py <folder>` and set the experiment's **Folder** control to it. Sets you prepare go in `image_sets/`, which git ignores.

### The asset pack

![The 74 objects in the asset pack](docs/media/asset-pack.jpg)

The scenes draw their 3D models, typefaces, lettering and music from [`assets/`](assets/), a pack that ships with the repository. It holds 74 objects, three printed sheets, lettering, two instrumental tracks with their analysis, eighteen short video clips, six photographs of rooms with a television in them, and two prepared image sets (stills with depth maps, and subjects with cut-outs), all generated for this project, and four open-licence typefaces. [`assets/README.md`](assets/README.md) lists the contents and how each part was made.

A scene's words, model names and tuning are one table at the top of its `build.py`. A pack can replace them, and you can point the engine at a pack of your own, without changing a scene's code. With no pack at all, each scene falls back to TouchDesigner's bundled teapot and default typeface, and the hub plays TouchDesigner's bundled sample track.

Most of the project page uses this pack. The film's music and the pictures of treatments, transitions and layers come from a different, private pack.

More preset and asset packs are planned for future releases.

## Smaller examples

Three single experiments came before the scene engine. They are the quickest way to see what one experiment folder holds: its `.tox`, `checks.json`, a readable `snapshot/network.json`, a hero frame, and a `NOTES.md` that logs every step, including the ones that did not work. To try one, drag its `.tox` into your lab project.

| | |
|--|--|
| ![audio_particles](docs/media/audio_particles.gif) | **[`audio_particles`](experiments/audio_particles/)**: a word made of 30,000 POP points that erupts into smoke on the beat and re-forms between beats. The COMP has a **Text** parameter, and **Music Folder** and **Track** parameters for your own audio. |
| ![sdf_sculpture](docs/media/sdf_sculpture.gif) | **[`sdf_sculpture`](experiments/sdf_sculpture/)**: a raymarched liquid sculpture written in a few lines of [Shader Park](https://github.com/shader-park/shader-park-core) JavaScript, compiled headless to a GLSL TOP shader by [`tools/shaderpark`](tools/shaderpark/). |
| ![feedback_drift](docs/media/feedback_drift.gif) | **[`feedback_drift`](experiments/feedback_drift/)**: noise blooms tinted by a hue-drifting ramp, spiralling inward through a 16-bit float feedback loop. Its `NOTES.md` shows the build, look and adjust loop step by step. |

## What's inside

| | |
|--|--|
| [`AGENTS.md`](AGENTS.md) | The rules Claude follows around a live TD session. Several of them came from traps hit on a real install. |
| [`.claude/skills/`](.claude/skills/) | `td-setup` (first-time setup), `td-connect`, `td-new-experiment`, `td-sketch` (the build → look → adjust loop), `td-glsl`, `td-verify`, `td-snapshot` |
| [`td/tdh/`](td/tdh/) | The in-TD toolkit (Python 3.11 + numpy). It handles the error sweep, PNG capture, motion and stall detection, the cook budget, `checks.json` and text snapshots. It observes; it never builds. |
| Controls | You never have to read the network to change something. As it builds, Claude puts the words, amounts and choices on the experiment as labelled controls, a check fails if any control does nothing, and `tdh.show(...)` opens the controls beside the output so you can move a slider and watch. |
| [`experiments/`](experiments/) | One folder per idea, and `_template/` to start from. The scene engine is the `sw_*` and `sc_*` folders. |
| [`assets/`](assets/) | The asset pack the scene engine uses |
| [`tools/`](tools/) | Offline tools: the feed baker, model conversion, the gallery and the asset pack's generators |
| [`docs/`](docs/) | [INSTALL](docs/INSTALL.md) (the walk-through Claude Code follows) · [SETUP](docs/SETUP.md) (the same by hand) · [TRANSPORTS](docs/TRANSPORTS.md) (servers and tool names) · [REMOTE](docs/REMOTE.md) (phone, other machines, GPU VMs) · [KNOWN-ISSUES](docs/KNOWN-ISSUES.md) · [RESEARCH](docs/RESEARCH.md) (what else exists) |

## Status and limits

- **This is version 0.1, and it is early.** One person and one Windows machine have built everything here with it.
- **Verified on:** Windows, TD 2025.33230, touchdesigner-mcp 2.2.0.
  - **It has not been tested on macOS yet.**
  - **TDMCP** works for create and wire. TD crashed once while TDMCP was setting an expression, so the rules route expressions through Python for now. Its first full run is still pending.
- **The scene engine has been built and run on one machine.** Its builder has not yet been tried from a fresh clone on a second machine.
- **The analysis step that makes a feed for a new track is not in the repository yet.** The engine plays the two tracks in the asset pack and TouchDesigner's sample track; a track of your own needs a feed baked from an analysis made elsewhere.
- **Claude judges how things look from downscaled stills.** It can't watch the output as video. The `moving` check confirms motion numerically, not aesthetically.
- **The agent can run arbitrary Python inside your TD session.** The rules keep it inside the experiment COMP and away from saving the whole project, but use a lab project, not a show file.
- `./check.sh` (lint plus unit tests against a fake `td` module) runs in CI. Live checks need TouchDesigner, so they run on your machine.

## Author

touchdesigner-harness is made by [Bill Moore](https://billmoore.ai), who builds agent harnesses and tooling for media work.

## License

This repository is under the MIT license. The typefaces in `assets/fonts/` are under the SIL Open Font License, and their licence texts are beside them. touchdesigner-mcp (MIT) and TDMCP (Derivative's Shared Use License) are separate projects with their own licenses, and neither is included here.
