---
name: td-new-experiment
description: Start a new TouchDesigner experiment, with its own folder, COMP, notes and checks. Use when the user wants to try a new idea, look or technique.
---

# New experiment

1. **Name it.** Pick a short **snake_case** slug from the idea (for example `audio_ribbons`). Confirm it with the user if the idea is vague. TD operator names allow only letters, digits and `_`, and the slug is also the COMP name: `create(baseCOMP, 'audio-ribbons')` raises `Illegal node name specified`. Use the same slug for the folder, the COMP and the branch.
2. **Branch:** `git checkout -b exp/<slug>` (unless the user wants to work on the current branch).
3. **Folder:** `cp -r experiments/_template experiments/<slug>`. Then replace `SLUG` in `NOTES.md` and `checks.json`.
4. **Fill in `NOTES.md` → Intent** from what the user said. Ask one question if "what makes it work?" is unclear. That answer is what you'll judge captures against.
5. **Create the COMP in TD** (make sure `td-connect` has been run):
   - Create a Base COMP `/project1/<slug>`, with an Out TOP named `out1` inside it.
   - Set its `externaltox` parameter to `experiments/<slug>/<slug>.tox`. Paths are relative to `lab.toe`, which sits at the repo root.
   - Add a **cook driver**: an Execute DAT `cook_driver` *inside* the COMP, with Active and Frame Start turned on. TD cooks on demand, so without this an experiment that's off-screen stops updating, and Trail, Lag and Feedback CHOPs freeze. Its callback:

     ```python
     def onFrameStart(frame):
         op('out1').cook(force=True)   # relative to this COMP; NOT '../out1'
         return
     ```

     `op('name')` inside a DAT resolves relative to the COMP that holds the DAT. `'../out1'` points one level higher, outside the experiment.
   - Check with `tdh.errors('/project1/<slug>')`. Then check the driver works: `tdh.total_cooks('/project1/<slug>/out1')` should go up between two calls.
6. **First save:** `tdh.save_tox('/project1/<slug>', 'experiments/<slug>/<slug>.tox')`.
7. **Commit** the folder: `exp(<slug>): start`.
8. Move on to `td-sketch`.
