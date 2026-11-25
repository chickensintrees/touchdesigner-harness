# sw_images

## Intent
Plays the pictures of a prepared image set (`tools/imageprep/prepare.py`) in colour order as an ordinary 1280x720 picture, so a folder of photographs can be the Input of any scene. It works when a scene given `/project1/sw_images/out1` visibly applies its technique to the photographs.

## How it is built
- `image_lib.py` and `imset_module.py` are shared by every image template: the Folder control, the set's table, a clock with two picture slots that take turns, and a private finish.
- `shaders/player.frag`: fill the frame or show the whole picture, a slow push, and three ways to change picture (dissolve, hard cut, cut through static).
- There is no finish here on purpose: the output is raw material for another scene.

## Inputs / outputs
- Output TOP: `out1`, 1280x720.
- Source of truth: `build.py` (rebuilding destroys and recreates the COMP).

## Log
2026-11-21: after the note "more colour variety": the default set is now the generated stills (`assets/image_sets/generated_depth`), and a new control, Colour Treatment Per Picture, gives each picture its own treatment by its place in the set (as photographed, two inks, hues turned a third round, a three-ink poster, a tinted negative). 0 shows every picture as photographed. captures/hero.png.
2026-11-19: built. captures/sheet_player.png shows it alone and as the Input of sc_rutt_etra (strong), sc_point_morph (reads) and a slime-mould scene, removed 2026-11-20 (the picture is hard to recognise on that take).
Weak: with a blank Folder the two Movie File In TOPs warn "File not found". The repository ships no sample set, so a fresh clone shows nothing until a set is prepared.

## Keepers

2026-11-23: the generated set moved into the asset pack (`assets/image_sets/`) so it ships with the repository; the top-level `image_sets/` stays for your own pictures and is never committed.
