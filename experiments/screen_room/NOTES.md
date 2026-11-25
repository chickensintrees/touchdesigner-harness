# screen_room

## Intent
A photographed room with a television in it, playing any other picture: the device-in-a-room frame. It works when it reads as a photograph of a set that is showing the picture, not as a picture pasted on a photograph.

## How it is built
- The rooms are pictures (`assets/rooms`, generated). Nothing of a room or a set is drawn. Each room comes with the four corners of its screen and a mask of the glass; `tools/assets/file_generated.py` turns the corners into a matrix (`rooms.tsv`).
- `shaders/room.frag` uses that matrix to pin the picture to the screen, multiplies it by the glass mask, keeps the reflections the photograph has in the glass (only what is brighter than the switched-off glass itself), dims the picture toward the edge of the tube, lets a blurred copy of the picture light the bezel and the room next to it, and pushes the camera in from the shot's start.
- The picture on the glass first goes through a private finish on the CRT preset (`tube`, with its own curvature and corners off, because the photographed glass already has them). The whole frame then goes through a second finish (35mm by default).
- `Take` picks the room. `Input` is the path of any TOP; it starts on the footage player (`/project1/sw_footage/out1`). Blank shows snow. A 16:9 picture loses its sides on these 4:3 tubes.

## Inputs / outputs
- Output TOP: `out1`, 1280x720.
- Source of truth: `build.py` (rebuilding destroys and recreates the COMP).

## Log
2026-11-21: rebuilt on the six generated rooms after the note not to design sets by hand. The drawn television, table and wall are removed from `room.frag` and from the controls (Casing Colour is gone). One take per room; the catalog video shows footage in four rooms and the scan line synth in two. All six rooms are used: the diner's grey reflective glass reads as a lit tube once its own grey is left out of the reflections. captures/hero.png.
Weak: the rooms are stills, so nothing in the room moves except the push and the film grain. The screen's light on the bezel is a glow by distance from the screen, not real lighting, and it does not reach the furniture. A bright clip washes out on the tube. The photographs are scaled to 1280 px, so the end of a push is soft.
2026-11-19: built with a set drawn in the shader. Weak: a flat drawing, not an object. Replaced on 2026-11-21.

## Keepers
