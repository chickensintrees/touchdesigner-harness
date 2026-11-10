# MCP servers (transports)

tdh needs just one thing from a server: **a tool that runs Python on TD's main thread and returns what it prints.** Everything else, such as creating, wiring and setting parameters, comes from the server's typed tools.

| Server | Endpoint | Run Python | Project info | Image | Notes |
|--------|----------|------------|--------------|-------|-------|
| [TDMCP](https://github.com/TouchDesigner/TDMCP) (default) | `http://127.0.0.1:13316/mcp` | `execute_code` | `project_info` | `view_operator` | Official (Derivative). Undo stack, consent panel, `get_help` and `get_docs` from the running build, `build_network`. TD ≥ 2025.33230. Shared Use License: don't redistribute it. |
| [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) | stdio (`npx touchdesigner-mcp-server`), which talks to a Web Server DAT on :9981 | `execute_python_script` | `get_td_info` | `get_top_image` | MIT, the most widely used. No undo, so snapshot before big changes. Confirmed working on the Windows desk machine: server **2.2.0** pinned, with the component zip from the same release (API 1.6.1), on **Node 24** (Node 20 is too old, and `npm install …@2` resolved to 2.0.0). |
| [Embody / Envoy](https://github.com/dylanroscover/Embody) | `http://127.0.0.1:9870/mcp` (or its stdio bridge) | `execute_python` | `get_td_info` | — | MIT. Writes its own `.mcp.json`, `AGENTS.md` and `CLAUDE.md`. Point those at this repo's files, or keep Embody's in the project folder. Its TDXN export works alongside tdh snapshots. |

Tool names were taken from each project's README on 2026-11-10. Check them with `claude mcp list` / `/mcp` after connecting.

## Switching

Server names: `.mcp.json` registers TDMCP as **`tdmcp`**. touchdesigner-mcp's own installer registers **`touchdesigner`** (user scope). Different names, different ports (:13316 and :9981), so **both can be live at once**. That's useful for comparing them. The skills refer to "the TouchDesigner MCP server", so use whichever one you've connected.

To use touchdesigner-mcp only, follow https://github.com/8beeeaaat/touchdesigner-mcp/blob/main/docs/installation.md: an `npx touchdesigner-mcp-server` stdio entry, plus the `mcp_webserver_base.tox` component in `lab.toe`.

**touchdesigner-mcp and `lab.toe` at the repo root.** The External .tox of `mcp_webserver_base` is an expression relative to the project file (`me.parent().fileFolder + '/../Documents/touchdesigner-mcp/mcp_webserver_base.tox'`), and its `import_modules` builds `sys.path` from it. If you move the project into this repo, that path no longer points anywhere. The textport shows `Failed to setup modules: No module named 'mcp'`, and :9981 accepts connections but never replies. **Fix:** set External .tox to the absolute path of `mcp_webserver_base.tox`. The component re-initialises as soon as the parameter changes. (Confirmed on the Windows desk machine.)

The skills say "the execute-python tool"; use the matching name from the table above.

tdh's snapshot excludes these servers' components by name (`TDMCP*`, `Embody*`, `Envoy*`, `mcp_webserver*`, `twozero*`). If yours has another name, pass `exclude=` to `tdh.snapshot`.
