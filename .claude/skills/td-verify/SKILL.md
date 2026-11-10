---
name: td-verify
description: Run an experiment's checks in TouchDesigner plus the harness checks, and report pass/fail honestly. Use before saying any TD work is done, before committing a keeper, and every few sketch steps.
---

# Verify

1. **Live checks** (in TD, via execute-python):

   ```python
   import tdh
   r = tdh.check('experiments/<slug>/checks.json')
   r
   ```

   - It prints one line per check. The overall status is `PASS`, `FAIL` or `PENDING`.
   - `PENDING` is normal on the first run. Both `moving` and `cook_budget` compare two samples:
     - `moving` compares two frames, which must be at least 0.5 s apart by TD's clock;
     - `cook_budget` sums cook time only over the operators that cooked between the two runs. Static operators that cooked once and went idle (a Ramp's 43 ms creation cook, seen live) don't count.

     Run it again about a second later. Calls that come too close together stay `PENDING`, and the hint says so.
2. **Harness checks** (in the shell): `./check.sh`. This lints and tests tdh and validates every `checks.json`.
3. **Look** at a fresh capture of `out1`. The checks catch broken output, but whether it looks right is your call against `NOTES.md`.
4. **Report** exactly what came back. Paste the summary lines. Never round `FAIL` up to "mostly working".
5. **On failure:**
   - `no_errors`: fix the listed operator paths.
   - `not_black`: walk upstream with `tdh.stats` until the output stops being black.
   - `cook_budget`: find the expensive operator (TDMCP `get_cook_performance`) and reduce resolution or particle count.
   - Never loosen a threshold in `checks.json` just to get a pass. Change it only when the intent changed, and say so in `NOTES.md`.

## Adding checks

Add assertions to `checks.json` as the experiment takes shape. Check types: `no_errors`, `not_black`, `no_nan`, `moving`, `chop_range`, `resolution`, `cook_budget`. They are documented in `td/tdh/checks.py`. Give every claim in the Intent a check where one is possible. For example, "reacts to audio" becomes a `chop_range` check on the analysis CHOP plus `moving`.
