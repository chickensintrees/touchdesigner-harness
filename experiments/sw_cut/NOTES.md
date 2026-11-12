# sw_cut

## Intent
Cut between scene networks in time with the music. Works if every cut lands on a beat line, no shot is shorter than a bar, the incoming scene is already alive when it appears, and only the scene on screen (plus the one warming up) cooks.

## How it is made
- `cutlogic.py` holds the decisions and has no TouchDesigner imports; `tests/test_cutlogic.py` runs it over synthetic feeds. `build.py` wires it to the hub and a Switch TOP, and is the source of truth for the COMP.
- The `scenes` table gives each scene an energy band. Bands and the Loud threshold (0.58) are tuned to the track the cutter was first built with (249 s, 125 bpm), whose `energy` only spans about 0.37 to 0.62; another track needs other numbers, or a normalised intensity channel in the feed.
- `record(file, seconds, start=0)` in build.py records the cut frame by frame: the hub's track time is stepped once per cooked frame and the project is off the clock, so the file is right however slowly the machine renders. The file holds the picture only; the sound is added afterwards from the track (the ffmpeg line is in the function's docstring).

## Log
<!-- Newest first. -->
2026-11-10: first recording, 100 s from the top of the track, all eight scenes appear (captures/hero.png is a frame every 2.5 s). Viewed as a contact sheet only, not yet watched in motion by anyone.
2026-11-10: Movie File Out with h264 wrote nothing: "GPU Accelerated H.264/H.265 Encoding requires a Commercial license". The error only shows in tdh.errors; I waited 100 s before reading it. Motion JPEG records (1.2 GB per 100 s), ffmpeg converts.
2026-11-10: first logic cut mid-bar whenever energy crossed the loud threshold (shots of 0.13 s, 21 cold cuts in simulation over the real feed). Loudness is now latched late in each bar and cuts wait for a beat line: 65 cuts over the track, shortest 1.83 s, none cold.

## Keepers
