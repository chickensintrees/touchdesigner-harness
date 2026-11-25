# Known issues and things to verify against a live TD

## Confirmed on a real install (Windows desk machine, TD 099.2025.33230, touchdesigner-mcp 2.2.0 / API 1.6.1)

First live run of `54fa587` (PR #1 comment). All seven check types returned PASS with a cook driver running. Without one, `moving` failed with "did not cook". `no_errors` caught a broken driver's traceback.

- `TOP.numpyArray()` rows are bottom-up, so `capture(flip=True)` is correct.
- `cpuCookTime` / `gpuCookTime` exist and are in ms. They read 0.0 until the first cook. The first cook after a build can spike (93 ms against 0.4 ms steady), so `cook_budget` treats one over-budget reading as pending.
- `Par.isDefault`, `isPulse`, `isMomentary` and `bindExpr` exist. `Connector.connections[i].owner` is the upstream OP.
- `COMP.save()` writes a .tox, and `loadTox` restores it. The restored snapshot is byte-identical apart from `root`. Snapshots are deterministic.
- The DAT parameters `file` and `syncfile` exist.
- touchdesigner-mcp runs each `execute_python_script` call in a **fresh namespace**, and **evaluates the last line again** to get the result. Hence AGENTS.md rule 14.
- **Reading a TOP's pixels forces one cook.** With no cook driver and a time-driven source (e.g. noise with `tz = absTime.seconds`), that single cook draws a new frame, so a naive motion check passes. `tdh.motion` therefore treats ≤ 1 cook between samples as `stalled`. Confirmed in the re-run of `874d8a9`.
- **Setting an Execute DAT's `par.active = False` did not stop `onFrameStart`.** out1 kept cooking at about 40/s until the DAT was destroyed. Don't rely on toggling Active to pause a cook driver or to simulate a missing one; delete the DAT, or turn off its Frame Start toggle (not yet verified).
- On Windows, `python3` is the Microsoft Store stub (exit 49). `check.sh` now looks for a working interpreter.

- **Cook on demand.** With no viewer, Trail, Lag and Feedback CHOPs freeze, so experiments need a per-frame Execute DAT cook driver. `tdh.motion` and the `moving` check report `stalled` when `totalCooks` doesn't change between samples.
- **`project.save()` via the exec endpoint on a never-saved project hung the bridge.** TD then restarted under a new PID. AGENTS.md rule 12 forbids it.
- **Git Bash path rewriting.** `/project1` arguments are mangled unless `MSYS_NO_PATHCONV=1` is set.
- **Connector semantics.** `outputConnectors[0].connect(op)` appends an input. `connect(op.inputConnectors[0])` replaces that input (connecting twice overwrites it).
- **touchdesigner-mcp versions.** Use server 2.2.0 with the matching component (API 1.6.1) on Node 24.

## TDMCP 1.1.56 on the desk machine (TD 2025.33230)

- **TD crashed during TDMCP `set_parameters` setting an expression** (`noise1.tz = absTime.seconds`). This happened once and hasn't been reproduced. Create and wire through the typed tools worked. The crash dump is on the desk machine (`TouchDesignerCrash.2025.33230_1.dmp`). Until it's reproduced, or reported to Derivative and fixed, set expressions with execute-python (AGENTS.md rule 3).
- **touchdesigner-mcp's `update_td_node_parameters` refuses expressions** ("Set .expr member instead"), and it has no typed wiring tool. With that server, expressions and wiring go through execute-python.
- **`project.save()` from Python opens a modal dialog** and blocks TD's main thread until it's answered (191 s in a timed-autosave test, and it kept asking). This is the likely cause of the earlier "hung the bridge" report. `COMP.save()` (`tdh.save_tox`) didn't prompt.
- **Yolomode ("Auto-accept deletion") ships on.** Turn it off (SETUP.md).
- **Server name clash.** touchdesigner-mcp registers `touchdesigner`, so this repo names TDMCP `tdmcp`.
- **Moving a project breaks touchdesigner-mcp's relative External .tox path.** Make it absolute (TRANSPORTS.md).

## First real experiment (`feedback_drift`, desk machine)

- **Kebab-case slugs are illegal TD node names** (`Illegal node name specified`). Slugs are snake_case now, and `test_repo.py` checks every experiment folder name.
- **Static ops keep their last `cpuCookTime`.** A Ramp TOP that cooked once (43 ms at creation) was summed on every check and failed a 12 ms budget, while the network's real cost was about 0.4 ms a frame. `cook_budget` now uses `tdh.cook_sample`, which counts only the ops whose `totalCooks` went up between two samples. `tdh.cook_ms` is still the raw sum.
- **`Par.isDefault` can be False for a value equal to its default** (`noiseTOP.par.tx`: 0 with default 0). Snapshots now treat a constant equal to its default as default.
- **`moving` passed with two checks about 0.1 s apart.** It now requires the two samples to be at least 0.5 s apart on `absTime.seconds`.

## Not yet verified

- [ ] TDMCP's `execute_code`: does it keep the namespace between calls, what does it return, and does it run the last line again? Until that's known, use the rule-14 snippet pattern for every server.
