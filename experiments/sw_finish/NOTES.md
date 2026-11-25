# sw_finish

## Intent
One component that any picture can pass through to pick up the texture of a period medium: 35mm film, VHS tape, a CRT tube, a 1-bit screen. It works when a clean render stops looking like a render and starts looking like a recording of something.

## How it is built
- Two passes. `shaders/signal.frag` is what happens to the signal: gate weave, tape line jitter, a travelling tracking bar, head-switch noise on the bottom edge, colour bleeding to the right, softness. `shaders/display.frag` is what the display or the film stock does: tube curvature, rounded corners, scan lines, phosphor stripes, misregistration, bloom, red halation, grain, vignette, tinted blacks, letterbox, a 4:3 crop, ordered 1-bit dither. The highlights for bloom and halation come from `shaders/bright.frag`, blurred twice at quarter size.
- Presets live in `presets.json` (clean, film35, vhs, crt, onebit). Choosing one from the Preset menu copies its numbers onto the sliders, so a preset is a starting point and every slider stays live.
- Picture in: the `Input` control (the path of any TOP) or, when that is blank, whatever is wired into the COMP.
- `build(name=..., parent=...)` makes a private copy inside another COMP. The image templates, the title card and the screen-in-a-room each carry one.

Where it belongs (decided 2026-11-19): after the cutter by default, and inside a scene only when the scene shows a device.
- After the cutter, once. A piece commits to one medium, and the cutter's treatments (mirror, kaleido, tiles, slices) are compositional. A finish applied per scene would have its grain and tracking bar mirrored and tiled by a treatment, and the stock would change at every cut.
- Inside a scene, only for a screen within the frame. `screen_room` runs the CRT preset on the picture on the glass and then puts the whole room through 35mm: two media on purpose (a tube, filmed).
- It is not wired into `sw_cut` yet. Point `Input` at `/project1/sw_cut/out1` to see the cut through it.

## Inputs / outputs
- Output TOP: `out1`, 1280x720.
- Source of truth: `build.py` (rebuilding destroys and recreates the COMP).

## Log
2026-11-21: shown on found footage now. `/project1/sw_finish` starts with the footage player (`/project1/sw_footage/out1`) as its Input when that is built. The catalog video is five generated clips, each through clean, 35mm, VHS, CRT and 1-bit, two seconds each. No change to the shaders.
2026-11-19: built. Shown on a slime-mould scene (removed 2026-11-20), sc_point_morph and sc_rutt_etra in all five presets (captures/sheet_phys.png, sheet_morph.png, sheet_rutt.png). The first pass had banded grain (a poor hash) and bloom that whited out bright scenes; both were fixed.
Weak: the letterbox crops the picture, so text near the top edge is cut off. 1-bit turns thin line art into speckle. Scan lines are faint at 720 lines. There is no interlace, no film dust and no scratches.

## Keepers
