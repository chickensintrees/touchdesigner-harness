# Prior Art: Claude Code + TouchDesigner

Research snapshot, 2026-11-10. It covers what already exists for connecting AI coding agents to TouchDesigner (TD), how TD can be controlled from outside, and where the gaps are that this harness should fill.

Labels: **[V]** = confirmed in the repo, README or docs. **[I]** = inferred or third-party claim. Star counts and dates come from the GitHub API on the snapshot date.

---

## 1. The starting video

**"Using an AI Agent Inside TouchDesigner (Embody Tutorial)"**, The Interactive & Immersive HQ: https://youtu.be/3DHewZQTGHQ [V title and channel; transcript not available]

It demos **Embody** ([dylanroscover/Embody](https://github.com/dylanroscover/Embody), MIT, docs at https://dylanroscover.github.io/Embody/). Embody is a `.tox` with four parts:

| Part | What it does |
|------|--------------|
| **Envoy** | An MCP server *inside* TD (about 70 tools) at `127.0.0.1:9870/mcp`. It runs on a worker thread and queues every TD call onto the main thread. A stdio bridge can launch or restart TD. It writes `.mcp.json`, `AGENTS.md` and `CLAUDE.md` for you. [V] |
| **Embody** | Tags COMPs and DATs and externalizes them to files on disk that mirror the network, so they can be diffed in git. [V] |
| **TDXN** | A YAML export of a whole network (ops, wires, non-default params, layout, DAT text) that can be imported back. Round-trip import is experimental. [V] |
| **Convoy** | A relay so one agent can drive Embody instances on other machines on the LAN. [V] |

## 2. Existing MCP servers / bridges

| Project | ★ | Architecture | Tools | Notes |
|---------|---|--------------|-------|-------|
| [TouchDesigner/TDMCP](https://github.com/TouchDesigner/TDMCP) (**official, Derivative, beta**) | 90 | `.tox` that serves streamable-HTTP MCP inside TD at `127.0.0.1:13316/mcp` | 26: inspect, docs (`get_help`, `get_docs`), params, `build_network`, wiring, DAT content, `get_errors`, `inspect_values`, `view_operator` (image), `get_cook_performance`, `execute_code`, `save_project` | **Every edit goes on TD's undo stack**, there is a consent panel, and it binds to localhost only. Companion skills repo: [TDMCPSkills](https://github.com/TouchDesigner/TDMCPSkills). "Shared Use" license, which is not OSI. Needs TD ≥ 2025.33230. [V] |
| [8beeeaaat/touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) | 624 | Node stdio server (`npx touchdesigner-mcp-server`) that calls a Web Server DAT `.tox` on :9981. The API is defined in OpenAPI. | 14: create/delete node, params, exec python, node errors, `get_top_image`, class/module help | Most stars. The only TD server in the official MCP registry. MIT. No undo and no batch operations. [V] |
| [dylanroscover/Embody](https://github.com/dylanroscover/Embody) | 216 | MCP inside the `.tox` on :9870, plus a stdio bridge | about 70, including `export/import_network`, `run_tests` | The only one with text versioning (TDXN) and an in-TD test runner. Large and opinionated. MIT. [V] |
| [satoruhiga/claude-touchdesigner](https://github.com/satoruhiga/claude-touchdesigner) | 129 | Claude Code plugin; Node MCP server that talks to a `.tox` on :44444 | 4 (`td_execute`, pane, selection, operators) plus a `td-guide` skill | Minimal and built around the skill. No license. Idle since Feb 2026. [V] |
| [Pantani/tdmcp](https://github.com/Pantani/tdmcp) | 62 | Node server that calls a REST bridge `.tox` on :9980 | claims 509 | Embedded reference of 629 ops; create → verify → preview loop; automatic layout. [V claims] |
| [dreamrec/TDPilot](https://github.com/dreamrec/TDPilot) | 16 | Plugin or `npx`; Web Server DAT on :9981 plus a WebSocket on :9982 that streams TOPs | 114 | Snapshots and rollback, screenshot self-checks, "technique memory". [V] |
| [twozero-team/twozero-td-mcp](https://github.com/twozero-team/twozero-td-mcp) | 28 | Inside the closed twozero plugin on :40404 | — | Handles several TD instances; error and performance triage flows. [V] |
| [johnsabath/touchdesigner-mcp](https://github.com/johnsabath/touchdesigner-mcp) | 17 | Pure Web Server DAT MCP on :9988 | about 10: run, inspect, create, wire, DAT edit, `observe` (PNG/GIF), `render` (MP4), `map` (text network map) | Compact, well-chosen tool set. [V] |
| [benoitliard/touch-mcp](https://github.com/benoitliard/touch-mcp) | 5 | `pip` stdio server, persistent WebSocket to a `.tox` | 29–37 | Has `td_batch`. [V] |

There are also about ten smaller ones, e.g. familienak-tech "TD-Codex Ultimate", dcc-mcp-touchdesigner, a Rust bridge, and forum `.tox` posts. [I]

**Knowledge resources usable by agents**
- [bottobot/touchdesigner-mcp-server](https://github.com/bottobot/touchdesigner-mcp-server): an MCP server that only serves docs (661 operators, 214 Python classes, 32 workflow patterns). [V]
- [cacheflowe/td-docs-mcp](https://github.com/cacheflowe/td-docs-mcp) and [touchdesigner-wiki-rag](https://github.com/johnnyvincentvitale/touchdesigner-wiki-rag): search and RAG over docs.derivative.ca. [V]
- [td4llms](https://github.com/jcksncllwy/td4llms) and [rootnotez/td-snapshot](https://github.com/rootnotez/td-snapshot): export a network to JSON or text, one way only. [V]
- Skills packs: TDMCPSkills (official), [rheadsh/audiovisual-production-skills](https://github.com/rheadsh/audiovisual-production-skills), and others. [V]
- docs.derivative.ca has **no `llms.txt`**. TDMCP's `get_docs` / `get_help` read the docs from the running build, which is the most reliable grounding available. [V]

## 3. How TD can be controlled (the mechanics)

- **Inbound**
  - The Web Server DAT handles HTTP and WebSockets (`onHTTPRequest`, `onWebSocketReceiveText`, …); bind it to 127.0.0.1. Docs: https://docs.derivative.ca/Web_Server_DAT [V]
  - Alternatives: TCP/IP DAT, OSC In, UDP In. [K]
- **Threading**: TD objects may only be touched on the main thread. Long handlers drop frames. Use a queue drained each frame, `run(..., delayFrames=N)`, or the Thread Manager. Docs: https://docs.derivative.ca/Python_threading_in_TouchDesigner [V]
- **Introspection**: `op.errors(recurse=True)`, `warnings()`, `scriptErrors()`, `cook(force=True)`, `inputConnectors[i].connect()`, `par.X.val/.expr/.mode`. Docs: https://docs.derivative.ca/OP_Class [V]
- **Visual feedback**: `TOP.saveByteArray('.png')` returns PNG bytes, which can be base64-encoded straight into the response for the model. `TOP.numpyArray()` gives pixel data for metrics such as black, NaN or still frames. Downscale to about 512–1024 px before sending. A capture may return the previous frame, so cook first or wait a frame. Docs: https://docs.derivative.ca/TOP_Class [V]
- **Text and versioning**
  - `.toe` and `.tox` are binary.
  - `toeexpand` / `toecollapse` unpack them into ASCII files, but the format is undocumented. [V]
  - Practical git workflow: externalize DATs to `.py` / `.glsl` / `.json` with Sync to File, externalize COMPs as `.tox`, or use Embody's TDXN.
- **Platform**
  - Windows 10/11 and macOS 13+ only, with a GPU (Vulkan 1.1). **No Linux, no headless or no-GPU mode.** [V]
  - Useful environment variables for unattended runs: `TOUCH_TEXT_CONSOLE=1`, `TOUCH_NO_UPDATE_CHECK=1`. Use an Execute DAT `onStart()` for startup hooks. [V]
- **Licensing**: Non-Commercial caps resolution at 1280×1280 and is for unpaid work only. A key runs on one machine at a time. [V]
- **Python**
  - TD bundles Python 3.11 (3.11.15 in 2025.33070). [V]
  - The **TDPyEnvManager** palette component creates `.venv` from TD's own interpreter, using `requirements.txt` / `pyproject.toml`. [V]
- **Current Official build**: 2025.33230 (Sept 2026). [V]

## 4. Gap analysis: what nobody does well yet

1. **Verification beyond one screenshot.** Several servers can grab a TOP image. Nobody offers *assertions*: "this TOP isn't black/NaN", "this CHOP channel stays in [0,1]", "fps ≥ 60 for 5 s", "matches a reference image within tolerance", "it moves over time".
2. **A real "definition of done".** No single command runs every check and reports pass or fail: an error sweep, assertions and a perf budget. Only Embody has an in-TD test runner.
3. **Root-cause errors.** Every server returns error strings per operator. None traces an error back through references, expressions, exports and binds, or maps a script traceback to the line in the externalized source file.
4. **Versioning as a workflow.** Only TDXN round-trips, and it is tied to Embody. Nobody packages "the agent edits text on disk, TD reloads it, git diffs it, the PR reviews it" as a disciplined loop.
5. **Safety is uneven.** Only TDMCP puts every edit on the undo stack and asks for consent. Most other servers expose raw `exec` with no dry-run, diff or checkpoint.
6. **Tool count is all over the place.** Servers expose anywhere from 4 to 509 tools. Nobody has measured which size works best for an agent.
7. **Long-running and multi-session work.** No progress files, specs or project conventions that let the next session pick up the work.
8. **No CI.** TD can't run on Linux, so a cloud agent cannot run TD-dependent tests. Anything that must run in CI has to be checks that don't need TD (e.g. linting externalized code, validating TDXN/JSON structure). Live checks need a self-hosted Windows or Mac runner.

## 5. Recommended direction

**Don't build another MCP server.** About 20 already exist. The official one, TDMCP, has the best safety story (undo, consent, localhost-only) and pulls docs from the running build. Derivative backs it, so it will probably become the default.

**Build the harness around it.** That is the five parts from [harness-engineering](https://github.com/chickensintrees/ai-coding-rules/blob/main/guides/harness-engineering.md):

| Harness part | For TD |
|--------------|--------|
| Instruction file | `AGENTS.md` / `CLAUDE.md` with TD rules: main-thread only, cook before capture, externalize code, never `exec` what a typed tool can do, save checkpoints, respect the resolution cap. |
| Spec | `SPEC.md` for the piece: inputs (audio, OSC, sensors), outputs, resolution, fps budget, look references. |
| Skills | `.claude/skills/`: e.g. `td-connect`, `td-build-network`, `td-glsl-iterate`, `td-verify`, `td-externalize`, `td-checkpoint`. |
| Tools | TDMCP as the primary transport. Optionally a small **companion `.tox` / extension** that adds only what TDMCP lacks (assertions, multi-frame capture, error tracing), served as extra MCP tools or callable through `execute_code`. |
| Checks | `td-check`: an error sweep, assertions declared in the spec, a perf budget, and a visual snapshot diff. It is the definition of done. Externalized source is linted in CI (no TD required). |

**Hard constraint:** TD runs only on Windows or macOS with a GPU, so Claude Code has to run on the user's TD machine. One option is a cloud session connected to that machine through Remote Control. This cloud container can author the harness (docs, skills, Python, tests that don't need TD), but it cannot run TD.

## 6. Open questions for the owner

1. **Base transport:** TDMCP (official, but not OSI-licensed), 8beeeaaat (MIT, most popular), or Embody (MIT, with versioning)? Or keep the harness transport-agnostic?
2. **Target OS, TD build and license tier** (this affects resolution caps and whether TDMCP's ≥ 2025.33230 requirement is met).
3. **What kind of work:** live visuals/VJ, installations, audio-reactive work, GLSL-heavy work, or client projects? This decides which skills come first.
4. **Versioning approach:** plain externalization (DATs and `.tox`) or TDXN?
5. **Audience:** just you, or students and a team (as in the ai-coding-rules worked example)?
