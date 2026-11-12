# sw_hub

## Intent
The one audio source for the scene engine: plays a track, and publishes a per-frame feed that combines offline analysis (stems, beats, bars, sections, drum hits, pitch) with live level and spectrum. Scenes read `feed` through a Select CHOP and never touch the audio themselves. Works if every channel in `SCENE_BRIEF.md` moves with the music and no scene needs its own analysis.

## How it is made
- `build.py` is the source of truth; the .tox is its output. `set_track(slug)` switches track and feed.
- Feeds are baked by `tools/audiofeed/bake_feed.py` from scores written by an offline audio analysis (stem separation, then beats, bars, sections, drum hits and pitch). A track is found when a pack holds both `music/<name>.wav` or `.mp3` and `feeds/<name>/feed.chan` with `feed.json`; `hub_module.py` lists the tracks of every pack in use and holds no machine paths. The shipped pack's two tracks and their feeds are in `<assets>/music/` and `<assets>/feeds/`. With no pack at all the hub plays TouchDesigner's bundled sample track with the feed in `experiments/sw_hub/sample_feed/`. Feeds of music that may not be redistributed belong in a pack kept outside the repository.
- Track time = the Audio File In CHOP's `true_sample / sample_rate` (Info CHOP), fed to a Lookup CHOP over the 100 Hz feed table.

## Log
<!-- Newest first. -->
2026-11-10: models. TouchDesigner's FBX COMP rejects .glb ("unsupported file extension") while still showing its placeholder mesh (4438 points), which read as success until the error sweep. `tools/models/convert_models.py` (Blender) writes OBJ/FBX/PNG copies; `scene_lib.import_model` uses the OBJ. Blender saved JPEG bytes under a .png name, which Movie File In refused; re-encoded with PIL.
2026-11-10: the live `level` was NaN forever: the RMS Analyze CHOP's first cook is NaN and Lag/Speed CHOPs hold it. `rms_clean` replaces NaN with 0 before the Lag.
2026-11-10: File In CHOP's rate option `resample` stretched the 100 Hz table to 60 Hz timing (19855 samples for 11913 rows); `override` is the right one.
2026-11-10: TouchDesigner's timeline was paused when the session started, and with it paused `absTime.frame` did not advance and no Execute DAT fired, although the bridge kept answering. Set `/local/time` play to 1. Speaker volume is its own parameter (default 0) so analysis and recording are unaffected.

## Keepers
