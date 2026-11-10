# SPEC: touchdesigner-harness

## What it is

A harness that lets Claude Code (or another MCP-capable agent) build and change TouchDesigner networks for **experimentation**. Every step the agent takes is seen, checked, logged and reviewable in git.

It does not include an MCP server. It sits on top of one (touchdesigner-mcp, verified; or TDMCP) and adds what those servers don't have:

| Part | What | Where |
|------|------|-------|
| Rules | How the agent behaves around a live TD session | `AGENTS.md` (`CLAUDE.md` imports it) |
| Skills | Repeatable procedures: connect, new experiment, sketch loop, GLSL, verify, snapshot | `.claude/skills/` |
| Toolkit | `tdh`, Python that runs inside TD: error sweep, pixel stats, motion, PNG capture, declarative checks, text snapshots, .tox save | `td/tdh/` |
| Experiments | One folder per idea: `NOTES.md`, `checks.json`, `<slug>.tox`, `snapshot/network.json`, shader and script files, hero capture | `experiments/<slug>/` |
| Checks | Live: `tdh.check(checks.json)`. Offline: `./check.sh` (lint, unit tests with a fake `td`, validation of every checks.json and snapshot). CI runs `./check.sh`. | |

## Decisions

- **Works with any MCP server.** tdh needs only an execute-python tool, which TDMCP, touchdesigner-mcp and Embody all have. The typed build tools come from whichever server you run. Verified end to end: touchdesigner-mcp 2.2.0. Also supported: TDMCP (official, undo stack, consent, localhost only), pending its first full run.
- **tdh observes; it doesn't build.** The one exception is `save_tox`, which writes a file. Building goes through the server's typed tools, so with TDMCP every edit can be undone.
- **Git:** each experiment is a `.tox` (to restore it) plus a deterministic JSON snapshot (to review it). The snapshot records non-default parameters, wiring, layout, expressions and binds, and authored DAT text. It is not a restore format. `lab.toe` stays local, because it contains the MCP server component, and TDMCP's license forbids redistributing it.
- **Platforms:** TD on macOS and Windows. Claude Code either runs locally, or on a GPU VM that runs TD (see `docs/REMOTE.md`). Linux can only edit the harness; it can't run TD.
- **Python 3.11** (the version TD bundles). tdh needs only numpy, which TD includes, and the standard library. It writes PNGs itself, so no PIL is needed.
- **No main-thread blocking.** Anything that needs time, such as motion, is measured across two calls.

## Definition of done (for harness changes)

`./check.sh` passes, and any change to tdh's behavior has a unit test against `tests/fake_td.py`. When the fake and real TD disagree, fix the fake and the code together, and note the TD build where you found it.

## Status

v0.1. The first live run was on Windows (TD 2025.33230, touchdesigner-mcp 2.2.0): all check types passed, and the failure detectors were shown to work. TDMCP and macOS haven't been tested yet. See `docs/KNOWN-ISSUES.md`.

## Not yet (candidates)

- A command-line `td check` that calls the MCP server over HTTP, so checks run without an agent.
- Reference-image comparison checks, and checks over a sequence of frames (GIF/MP4).
- Tracing an error back to the expression, export or bind that caused it.
- `.agents/skills/` mirror for Codex and Cursor, before sharing publicly.
- A self-hosted Mac or Windows CI runner for live checks.
