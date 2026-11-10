---
name: td-sketch
description: The core build-look-adjust loop for a TouchDesigner experiment. Use whenever building or changing a network to reach a visual or behavioral goal.
---

# Sketch loop

Each pass through this loop makes **one** meaningful change and then looks at the result.

1. **Re-read** `experiments/<slug>/NOTES.md`: the intent and the last log entry.
2. **Plan one step.** Pick the smallest change that moves toward the intent, such as adding a feedback loop or swapping noise for a ramp. Look up any operator or parameter you're unsure of (TDMCP `get_help` / `get_docs`). Don't rely on memory.
3. **Make the change** with typed tools: create, wire, set parameters. TDMCP's `build_network` handles several operators in one call. Keep everything inside `/project1/<slug>`, and lay operators out left to right.
4. **Errors:** `tdh.errors('/project1/<slug>')`. Fix anything new before going further.
5. **Look:** `tdh.capture('/project1/<slug>/out1', 'experiments/<slug>/captures/<n>.png')`. Then **open the PNG with the Read tool and look at it.** Describe what you actually see, not what you expect to see.
   - Upside down? Pass `flip=False`.
   - Black? Check `tdh.stats(...)`, then check each operator upstream in turn.
   - For motion or animation, capture twice a second or more apart. Or use `tdh.motion(...)` (call it twice).
   - If motion says `stalled`, the TOP cooked at most once between the two calls, and that one cook was tdh's own read. Fix the cook driver before judging any animation. Sample about a second apart.
6. **Judge** the capture against the intent. Write a one-line log entry in `NOTES.md`: the change, what it looked like, the capture file, and what to try next.
7. **Decide:**
   - Better: keep it. If it's a real step forward, run `td-snapshot`.
   - Worse: undo (Ctrl+Z through TDMCP's undo, or revert the parameter) and log why.
   - Stuck after 3 tries on the same problem: stop, show the user the captures, and ask.
8. Repeat. Every few steps, run `td-verify`.

Experiments are allowed to be weird. The loop exists so that every step is seen, logged and reversible, not to keep the results tame.
