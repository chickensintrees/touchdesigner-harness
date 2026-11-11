# AGENTS.md: TouchDesigner harness

You are working with a live TouchDesigner (TD) session through an MCP server. These rules extend the general rules in [ai-coding-rules](https://github.com/chickensintrees/ai-coding-rules/blob/main/RULES.md). Read `SPEC.md` for what this repo is, and the experiment's `NOTES.md` before you touch its network.

## The setup

- **TD runs on the user's Mac or Windows machine.** Claude Code runs on the same machine, or reaches it through the options in `docs/REMOTE.md`. TD cannot run on Linux, so if you are in a Linux container with no MCP server, you can only edit the harness itself. Say so; don't pretend to build networks.
- **MCP server:** touchdesigner-mcp (registered as `touchdesigner`, :9981) is the path verified end to end. TDMCP (registered as `tdmcp` in `.mcp.json`, `http://127.0.0.1:13316/mcp`) is supported and adds an undo stack. Both can be connected at once; use whichever one is connected. touchdesigner-mcp and Embody also work; see `docs/TRANSPORTS.md` for the tool names.
- **tdh** (`td/tdh/`) is this repo's in-TD toolkit for errors, pixel stats, captures, checks and snapshots. Load it with the `td-connect` skill at the start of every session.

## Rules

1. **Connect first.** Before any work, run `td-connect`: confirm the server answers, confirm the TD build, and load tdh. If it fails, stop and report. Don't guess at network state.
2. **Look things up; don't remember them.** Operator types, parameter names and menu values change between TD builds. Use the server's docs/help tools (TDMCP `get_help` and `get_docs`) or introspect with `op(...).pars()` before you set an unfamiliar parameter.
3. **Typed tools over raw Python.** Create, wire and set parameters with the server's typed tools; with TDMCP those go on the undo stack. Use execute-python for tdh calls, for introspection, and for things the typed tools can't do. **Exception, for now: set parameter *expressions* with execute-python** (`op(p).par.x.expr = '...'`). TD crashed once while TDMCP `set_parameters` was setting an expression (see `docs/KNOWN-ISSUES.md`), and touchdesigner-mcp's typed tool refuses expressions outright.
4. **Never block the main thread.** All Python runs on TD's main thread. No `time.sleep`, no long loops, no network calls, no threads that touch TD objects. If something has to wait (for example a second motion sample), make a second call.
5. **Check after every change.** After each edit, run `tdh.errors(<experiment COMP>)`. After any change that affects the output, `tdh.capture(...)` the output TOP, open the PNG and look at it. Compare what you see with what `NOTES.md` says you are going for.
6. **Stay inside the experiment.** Each experiment lives in one COMP (`/project1/<slug>`) and one folder (`experiments/<slug>/`). Don't edit, move or delete anything outside it without asking. Never touch the MCP server's own component (TDMCP, Embody, mcp_webserver_base).
7. **Code lives in files.** GLSL, Python extensions and scripts go in `experiments/<slug>/` as real files. Point a Text DAT at the file (`file` parameter, with Sync to File on) so git can see changes. Don't leave substantial code only inside the .toe.
8. **Save, snapshot, commit the keepers.** When something works, or before something risky, use `td-snapshot`. It saves the experiment COMP as `experiments/<slug>/<slug>.tox`, writes `snapshot/network.json`, captures a hero frame and commits. `lab.toe` (your local project with the MCP server in it) is never committed. A commit with no snapshot is a commit nobody can review.
9. **Done means checked.** An experiment step is done when `tdh.check('experiments/<slug>/checks.json')` reports `PASS` (run it twice if it includes `moving`) and `./check.sh` passes. Report the actual output. Never claim a visual result you didn't capture and look at.
10. **Respect the machine.** The Non-Commercial license caps resolution at 1280×1280. Keep the perf budget in `checks.json`. Ask before raising resolution or adding heavy operators (feedback chains at 4K, large particle counts).
11. **TD cooks on demand.** An operator cooks only when something pulls on it: a viewer, an output, or a reference. Off-screen networks stop cooking, and time-based CHOPs (Trail, Lag, Feedback) freeze. Every experiment has a cook driver (see `td-new-experiment`). If a `moving` check says `stalled`, the network isn't cooking, which doesn't mean it isn't animated. Check `tdh.total_cooks(op)` before trusting any time-based reading.
12. **Don't call `project.save()` from Python, and don't build autosave on it.** It can open a modal save dialog that blocks TD's main thread until someone answers it (one test logged 191 s), and everything the MCP server serves stalls behind it. That is very likely why it "hung the bridge" in the first live run. Save experiments with `tdh.save_tox(...)`. Save `lab.toe` with the server's save tool (TDMCP `save_project`), or ask the user to press Ctrl+S.
13. **Wiring.** `src.outputConnectors[0].connect(dst)` **appends** a new input on dst. `src.outputConnectors[0].connect(dst.inputConnectors[i])` **replaces** input i. Use the indexed form when you mean "this input".
14. **Write every execute-python snippet the same way.** Start it with `import tdh`: some servers (touchdesigner-mcp) run each call in a fresh namespace, so `tdh` from an earlier call is gone, though the module is still loaded. End it with a bare variable name holding the result (`r = tdh.check(...)` then `r`): touchdesigner-mcp evaluates the last line again to get the result, so a last line with side effects (`print`, `create`, `save`) runs twice. The `tdh.x(...)` calls written inline in the skills are shorthand for this pattern.
15. **Ask before outward actions.** That means pushing, opening PRs, sending OSC/MIDI/DMX to real devices, and opening network ports.
16. **Every experiment is playable without reading its network.** The person you are building for should never have to find an operator to change something. As soon as a value is one they would want to change (the words on screen, an amount, a speed, a colour, which file, which variation), put it on the experiment COMP as a custom parameter with a plain label, on a page named `Controls`, and read it inside with `parent().par.Name`. Text is always a control, never typed into an operator. Do this as you build, without being asked, and say which controls you added. After the first working picture and after any change to the controls, run `tdh.show('/project1/<slug>')`: it opens the controls and the output as two windows, so they can move a slider and watch. The `controls` check in `checks.json` fails if there are fewer than three controls or if any control is read by nothing: a slider that does nothing is worse than no slider.

## Quick reference

| Want | Do |
|------|----|
| Is it connected? | `td-connect` skill |
| Start something new | `td-new-experiment` skill |
| Iterate on a look | `td-sketch` skill |
| Shader work | `td-glsl` skill |
| Let the user play with it | `tdh.show('/project1/<slug>')` (controls + output windows) |
| What can the user change? | `tdh.controls('/project1/<slug>')` |
| Is it done? | `td-verify` skill → `tdh.check(...)` |
| Keep this version | `td-snapshot` skill |
| Harness checks (no TD needed) | `./check.sh` |
