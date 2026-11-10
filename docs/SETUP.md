# Setup (macOS or Windows)

Two MCP servers work with this harness. Pick one; you can add the other later, and both can run at the same time.

| | Server | Status |
|--|--------|--------|
| **A** | [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) (MIT) | **Verified.** It carried a full experiment end to end on Windows (TD 2025.33230, server 2.2.0). |
| **B** | [TDMCP](https://github.com/TouchDesigner/TDMCP) (official, Derivative, beta) | Supported, and its typed tools work. Its first full experiment run is still pending (see `KNOWN-ISSUES.md`). |

## 1. Install

- **TouchDesigner 2025.33230 or newer**: https://derivative.ca/download. It needs a GPU with Vulkan support. A Non-Commercial license is fine; it caps resolution at 1280×1280.
- **Claude Code**: https://code.claude.com/docs
- **git**, and **Python 3.11**. Python is only needed to run `./check.sh`; TD bundles its own.
- For option A only: **Node.js 24**. Node 20 is too old for touchdesigner-mcp 2.2.0.

## 2. Clone

```bash
git clone https://github.com/chickensintrees/touchdesigner-harness.git
cd touchdesigner-harness
```

## 3. Make your lab project (once)

Open TouchDesigner and save a new project as **`lab.toe` at the root of this repo**. It's gitignored, because it will contain the MCP server's component. Experiment `.tox` paths are relative to it.

### Option A: touchdesigner-mcp

1. Follow touchdesigner-mcp's [installation guide](https://github.com/8beeeaaat/touchdesigner-mcp/blob/main/docs/installation.md) for Claude Code. Use server **2.2.0** and the component zip **from the same release** (API 1.6.1). A plain `npm install …@2` resolved to 2.0.0 on the test machine, so pin the exact version.
2. Import `mcp_webserver_base.tox` into `/project1` of `lab.toe`.
3. **Make its External .tox path absolute.** The component ships with an expression relative to the project file (`me.parent().fileFolder + '/../Documents/...'`). Once `lab.toe` lives in this repo, that path points nowhere. The textport shows `Failed to setup modules: No module named 'mcp'`, and port 9981 accepts connections but never replies. Set the External .tox parameter to the full path of `mcp_webserver_base.tox` on your disk. The component re-initialises straight away.
4. The installer registers a Claude Code server named **`touchdesigner`**. Check it with `claude mcp list`.

### Option B: TDMCP

1. Download `TDMCP.tox` from https://github.com/TouchDesigner/TDMCP/releases and drag it into `/project1`.
2. On TDMCP's MCP page, turn on **Active**. Optionally pulse **Install Skills**; TDMCP's own skills complement these.
   - Until it's Active, the component's panel shows the TDMCP author's machine (their storage paths and installed-skills count). That fixes itself once you turn it on.
   - **Turn off "Auto-accept deletion" (Yolomode).** It ships **on**, which skips the confirmation before deletes. That confirmation is one of the main reasons to use TDMCP.
3. This repo's `.mcp.json` registers TDMCP as **`tdmcp`** at `http://127.0.0.1:13316/mcp`. Approve it the first time Claude Code asks. If you changed the port, run `claude mcp add --transport http --scope local tdmcp http://127.0.0.1:<port>/mcp`.

### Both

Keep the names distinct: touchdesigner-mcp is `touchdesigner` (port 9981), and TDMCP is `tdmcp` (port 13316). If you only use option A, Claude Code will report `tdmcp` as not connected. That's harmless. Tool names for each server are in `TRANSPORTS.md`.

### Then save

Save `lab.toe` yourself with **Ctrl+S**. Don't have an agent call `project.save()`: it can open a modal dialog that freezes TD's main thread, and the MCP server with it (AGENTS.md rule 12).

## 4. Run

```bash
claude
```

Then ask:

> connect to TouchDesigner

That runs the `td-connect` skill. Then:

> new experiment: slow feedback tunnel driven by noise

## 5. Offline checks

```bash
python -m pip install pytest numpy pillow ruff
./check.sh
```

## Platform notes

- **Windows:**
  - `python3` is often the Microsoft Store placeholder. `check.sh` finds a working `python`/`py` by itself; for manual commands, use `python`.
  - Use forward slashes in paths you pass to tdh (`'experiments/x/captures/a.png'`). Run `./check.sh` from Git Bash.
- **Windows + Git Bash:** MSYS rewrites arguments that look like paths, so `/project1/x` becomes `C:/Program Files/Git/project1/x`. Set `export MSYS_NO_PATHCONV=1` before you pass TD operator paths to any CLI script.
- **macOS:**
  - The first time TD opens a listening port, macOS may ask about incoming connections. Both servers bind to localhost, so "Deny" is fine.
  - Not yet tested end to end on a Mac.
- Keep TD in the foreground, or turn off App Nap / background throttling. A throttled TD cooks slowly, and the `cook_budget` and `moving` checks will be wrong.
