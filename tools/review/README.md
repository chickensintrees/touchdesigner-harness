# Layer review film

A film for reviewing layered work: the layers side by side, every event named as it happens, and a timeline
of the music with a playhead. It plays at full speed, then at half speed.

Bill, 2026-11-16: "That interface you built to compare them is killer. Save that. Make it part of our
touchdesigner harness." It came from the mural-hype-video project's two-layer pipeline (a generated plate
under a TouchDesigner layer), after a bare render gave him nothing to react to.

```bash
python tools/review/layer_review.py spec.json
```

The tool knows nothing about a project. A project writes a spec from its own score: the panels (two or
three movies or image sequences), a status line per panel, the music (bars, beats, drum hits, sung words) and
the events (layer, frame, name, what it does, the music point it sits on, who did it). `spec_example()` in
`layer_review.py` shows the shape; `tests/test_layer_review.py` holds the layout, the playhead, the event
rows and the two passes. A working adapter: `mural-hype-video/pipeline/twolayer/review.py`.

Use it whenever work is shown for a reaction: show the layer alone on black as its own panel, so what was
added cannot be missed.
