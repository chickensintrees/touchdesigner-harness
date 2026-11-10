# sdf_sculpture

## Intent
A raymarched liquid sculpture written in Shader Park: a breathing, noise-displaced core with two drops orbiting and melting into it, iridescent bands sliding over the surface. Works if it renders cleanly (no shards), moves, and stays under budget at 1280x720.

## References
- Shader Park (MIT): https://github.com/shader-park/shader-park-core, docs https://docs.shaderpark.com/. Compiled headless with `shader-park-core@0.2.8`.

## Inputs / outputs
- Source of truth: `shaders/sculpt.js`. Generated: `shaders/sculpt.top.glsl` (GLSL TOP pixel shader) and `shaders/sculpt.uniforms.json`.
- Compile (from this folder, once `npm ci` in `tools/shaderpark/`): `node ../../tools/shaderpark/compile.mjs shaders/sculpt.js shaders`, then delete the `*.full.frag`, `*.td_mat.frag` and `*.vert` side outputs. The adapter turns Shader Park's WebGL2 output into a GLSL TOP shader.
- In TD: `sculpt_frag` Text DAT reads the `.top.glsl` with Sync to File; `glsl1` GLSL TOP (1280x720, 16-bit float) uses it as pixel DAT. Pulse `loaduniformnames`, then set every uniform from `uniforms.json`, with `time` = `absTime.seconds` and `stepSize` = 0.45 (see log).
- Output TOP: `out1`. Budget: 12 ms.

## Log
<!-- Newest first. -->
2026-11-10: tdh.check PASS twice (cook_budget 1.19 ms over 2 active ops; moving delta 0.049 over 107 cooks). One earlier run read cook_budget 109 ms, about 20 s after a shader reload, while TD held 60 fps and per-op times were ~1.2 ms; not reproduced in two full runs or a budget-only run. Unexplained.
2026-11-10: dropped the fine (9x) noise layer and darkened the bands (`band*band*0.55`). Shards gone; saturated iridescent rings over a liquid body, a drop pulling off left. A few fringes at the right edge. GPU 1.8 ms. captures/05-smooth.png.
2026-11-10: stepSize uniform 0.45. Trap: `setStepSize(0.55)` in the sculpture does not change the `stepSize` uniform default in `uniforms.json` (still 0.85), and the uniform wins. Shards remained, so they were not undersampling. captures/04-step045.png.
2026-11-10: bigger core (0.5), drops orbit wider, darker bands. Drop reads; still pastel; shards and speckles. captures/03-chrome.png.
2026-11-10: first own sculpture (noisy core + two blended drops, iridescent sine bands, metal 0.95). Moves, iridescent, but small, washed-out pastel, edge streaks. captures/02-chrome-a.png, 02-chrome-b.png.
2026-11-10: adapter proof with the research `blob.js`: GLSL TOP compiled first time ("Compiled Successfully"), `loaduniformnames` found all six uniforms, lit sphere renders upright with correct aspect. captures/01-blob.png.

## Keepers
