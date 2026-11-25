# sw_footage

## Intent
Plays a folder of video clips as found footage, one clip per channel, and changes channel by hand or in time with the music. It works when it reads as someone flipping through channels: each change rolls, tears, drops to snow and locks onto the next picture, on a bar line.

## How it is built
- Two Movie File In TOPs take turns. One shows the channel that is on. The other keeps the channel that was on while the change plays, then opens the clip that comes next, so a change never waits for a file.
- The frame each one shows is worked out from the clock (`absTime.seconds`), not from the player's own playback. A recording made off the clock (`tools/gallery/sound_reels_td.py`) therefore gets every frame of the clip in order.
- The change is the cutter's picture layer, `experiments/sw_cut/shaders/mix.frag`, read from that folder: the `How The Channel Changes` menu lists its transitions in the same order as `sw_cut/build.py`. The default is `tune`.
- `channels.py` decides which clip is on which channel and has no TouchDesigner in it (`tests/test_footage.py`). With `Clips To Skip Between Channels` at 7 every clip of the folder is shown before any comes back.
- The clips are whatever is in the `Folder Of Clips` (default `assets/footage`, read against the repository). Nothing pictured is drawn here.

## Inputs / outputs
- Inputs: the hub's feed (`bar_pos`), for the bar lines.
- Output TOP: `out1`, 1280x720. Use it as the Input of `sw_finish`, `screen_room` or any scene.
- Source of truth: `build.py` (rebuilding destroys and recreates the COMP).

## Log
2026-11-21: built on the 18 generated clips (1280x720, 16 fps, 5.06 s, silent). A 2 s test recording held 33 different frames, which is 16 a second: the frames arrive in order off the clock. captures/hero.png.
Weak: a clip is five seconds long, so a channel held for longer than that jumps back to its first frame. The clips are 16 fps and soft. Opening a clip costs a long frame on this machine when the idle player loads the next channel, which shows as a hitch when played live (not in a recording).

## Keepers
