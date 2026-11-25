# im_montage

## Intent
Cut-outs from a prepared image set stand as flat cards at different depths in front of a two-colour sunburst while a camera drifts past, and the result is re-photographed. It works when it reads as a deliberate paper collage with parallax.

## How it is built
- Nine cards, each a rectangle with a Constant MAT and an alpha test (hard paper edges, no sorting). The cards float on loops of different lengths. `shaders/ground.frag` draws the sunburst.
- Cut-outs come from the set's `cut/NNN.png`. Tier 0 of the prepare tool writes a rough key against each picture's border colour.

## Inputs / outputs
- Output TOP: `out1`, 1280x720.
- Source of truth: `build.py` (rebuilding destroys and recreates the COMP).

## Log
2026-11-21: moved to the 37 generated cut-outs (`assets/image_sets/generated_cutouts`, the default set now), after the note "too much repetition of the same images". Pictures are dealt from a shuffled deck of the whole set (`deal()` in layouts.py): no subject comes back until every one has been shown, across takes and cuts, and `tests/test_montage.py` holds that. A conveyor card that leaves one side now comes back as a new picture. captures/hero.png.
Still weak: a subject fills only part of its square card, so sizes are uneven; in the giant take the small cards along the bottom are mostly out of frame. Glass subjects (goldfish bowl, snow globe, lava lamp) keep their backdrop colour inside the glass.
2026-11-19 (later): re-run on real cut-outs (BiRefNet, made on a rented pod and filed with `--cutouts-from`). It now reads as a deliberate collage (captures/real_0.png, real_7.png, with Card Size 1.7). The earlier "weak" verdict was the rough key, not the template.
Still weak: the cards pile up in the middle of the frame, a subject fills only part of its card so sizes are uneven, and nothing changes over time except drift.
2026-11-19: built on rough cut-outs only (captures/b_1.png).
Weak, and not worth judging yet: on ordinary photographs the rough key leaves ragged fragments, so the frame is a mess. It needs real cut-outs. The layout is fixed at build time apart from Shuffle.

## Keepers

2026-11-23: the generated set moved into the asset pack (`assets/image_sets/`) so it ships with the repository; the top-level `image_sets/` stays for your own pictures and is never committed.
