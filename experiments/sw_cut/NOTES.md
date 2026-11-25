# sw_cut

## Intent
Cut between scene networks in time with the music. Works if every cut lands on a beat line, no shot is shorter than a bar, the incoming scene is already alive when it appears, and only the scene on screen (plus the one warming up) cooks.

## How it is made
- `cutlogic.py` holds the decisions and has no TouchDesigner imports; `tests/test_cutlogic.py` runs it over synthetic feeds. `build.py` wires it to the hub and a Switch TOP, and is the source of truth for the COMP.
- The `scenes` table gives each scene an energy band. Bands and the Loud threshold (0.58) are tuned to the track the cutter was first built with (249 s, 125 bpm), whose `energy` only spans about 0.37 to 0.62; another track needs other numbers, or a normalised intensity channel in the feed.
- `record(file, seconds, start=0)` in build.py records the cut frame by frame: the hub's track time is stepped once per cooked frame and the project is off the clock, so the file is right however slowly the machine renders. The file holds the picture only; the sound is added afterwards from the track (the ffmpeg line is in the function's docstring).

## Log
<!-- Newest first. -->
2026-11-23: the demo film has copy. `film_copy.md` is what the words say (twelve lines explaining the harness); `showcase.json` places them. Four changes to the cutter carry it: a shot-list entry may have a third item `{control: value}` that is set on the scene before the shot (`plan["set"]`, tests/test_cutlogic.py), which is how the kinetic type scene gets a line per shot through its Words control; a shot list's `cut` table is written to the cutter's controls when the list is loaded; components a shot list names that are not scenes (image templates, footage player) are loaded with an energy band no music reaches, and because they cook by their own Preview toggle the cutter switches that on while they are on screen or warming up (`_wake`); a scene whose Input names another component's picture keeps that component cooking (`_input_of`). `tests/test_film_copy.py` holds the list to the copy.
2026-11-23: such a component gets an empty energy band (1..0): the first build gave it a band no music reaches, and with no shot list the cutter then layered `screen_room` over a scene. cutlogic never picks or layers an empty band by itself. Also: a scene that follows itself in a list was dressed for its next shot while still on screen (its picture changed 0.4 bar early); it now waits for the cut.
2026-11-23: the film was recorded twice from this list and cut the same both times (53 cuts, same times), but `cutlogic.simulate` over the baked feed gave 52 for the same settings: one cut at 96.1 s that the live feed makes and the rows do not. Count the shots from a recording's log, not from the simulation. The `cook_budget` check on this COMP is not steady: with all scenes loaded it read between 0.2 and 106 ms in successive samples a few seconds apart (most often about 48 ms when it failed); the two passes before this snapshot were 7.7 and 0.2 ms with the film's list on. Not traced.
2026-11-21: the `tune` transition (the channel changes) is now also used outside the cutter: the footage player (`experiments/sw_footage`) reads `shaders/mix.frag` from this folder and changes channel with it. Keep the order of TRANSITIONS in build.py and in `sw_footage/build.py` the same. The cutter itself was not rebuilt.
2026-11-10: first recording, 100 s from the top of the track, all eight scenes appear (captures/hero.png is a frame every 2.5 s). Viewed as a contact sheet only, not yet watched in motion by anyone.
2026-11-10: Movie File Out with h264 wrote nothing: "GPU Accelerated H.264/H.265 Encoding requires a Commercial license". The error only shows in tdh.errors; I waited 100 s before reading it. Motion JPEG records (1.2 GB per 100 s), ffmpeg converts.
2026-11-10: first logic cut mid-bar whenever energy crossed the loud threshold (shots of 0.13 s, 21 cold cuts in simulation over the real feed). Loudness is now latched late in each bar and cuts wait for a beat line: 65 cuts over the track, shortest 1.83 s, none cold.

## Keepers
