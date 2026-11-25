# im_depth_relief

## Intent
Each photograph becomes a relief of points pushed out by its depth map, and the points stream from one photograph into the next. It works when a flat picture reads as an object with a front and a back, and the change between pictures is worth watching.

## How it is built
- 480 x 270 points (129,600). `shaders/cloud_vertex.glsl` samples both pictures and both depth maps, so the change is stateless.
- The camera drifts on three loops of different lengths. The render is re-photographed through a private finish (35mm by default).
- Depth comes from the set's `depth/NNN.png`. Tier 0 of the prepare tool writes a guess (brightness and height in frame) and the manifest marks it `depth_source: guess`.

## Inputs / outputs
- Output TOP: `out1`, 1280x720.
- Source of truth: `build.py` (rebuilding destroys and recreates the COMP).

## Log
2026-11-21: moved to stills generated for this technique (`assets/image_sets/generated_depth`, the default set now: 16 stills with MoGe 3 depth). Two of the 18 were left out: `gas_station_road` (one near pump takes the whole depth range and smears at the frame edge) and `drive_in_theatre` (the near car bonnet breaks into speckle). A new control, Depth Curve (0.6), hands some of the depth range back to the distance, because these maps give one near object most of it; Relief Depth now starts at 0.4. captures/hero.png.
Still weak: depth edges still open black gaps behind near objects, widest on the raking and scan-line takes. The maps are 8-bit, so smooth floors step when pushed far.
2026-11-19 (later): re-run on real depth (MoGe 2 "depth" render, near = white, made on a rented pod and filed with `--depth-from`). Subjects now stand off their grounds and crowds have layers (captures/real_0.png, real_4.png, with Relief Depth 0.7).
Still weak: depth edges open black gaps between points, and halfway through a change the frame is still close to snow. One very near object uses most of a depth map's range; the maps were mixed half and half with a rank-equalised copy before filing.
2026-11-19: built on guessed depth only (captures/sheet_stream.png, d_3.png). Settled pictures read well and the stream between them is the best moment.
Weak: the relief is a bump map of brightness, not the real shape of the scene, and steep guessed depth opens holes between points. Halfway through a change the frame is close to uniform snow. It needs real depth maps to be judged properly. It does not follow audio.

## Keepers

2026-11-23: the generated set moved into the asset pack (`assets/image_sets/`) so it ships with the repository; the top-level `image_sets/` stays for your own pictures and is never committed.
