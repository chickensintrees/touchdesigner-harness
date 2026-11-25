---
name: td-setup
description: Set up touchdesigner-harness from scratch with a person, or finish a setup that docs/INSTALL.md started. Use when the user says "continue setup", "set up", "install", or when td-connect finds no TouchDesigner MCP server.
---

# Set up, or finish setting up

`docs/INSTALL.md` is the walk-through for a person who has nothing installed. This skill is its second half, and the way in when Claude Code is started inside an existing clone. Its rules apply here too: one step at a time, ask before anything that changes the machine outside the clone, never ask for passwords or keys, and never call `project.save()`. The MCP server lets Claude Code run Python inside whatever project is open in TouchDesigner, so work only in the lab project, never in a show file. Say plainly that macOS has not been tested end to end yet.

## 1. Find out what is already done

Check in this order. All of these only read. `<CLONE>` is this repository's absolute path.

| Check | How | If it fails |
|---|---|---|
| The MCP server is registered | `claude mcp get touchdesigner` prints an entry | `docs/INSTALL.md` from step 2 |
| The server starts | the Status line of that entry says Connected | see "The server is registered but failed" below |
| This session has the server's tools | a tool named `get_td_info` from the `touchdesigner` server is available to you | see "Registered but not restarted" below |
| The component is downloaded | `<CLONE>/touchdesigner-mcp-td/mcp_webserver_base.tox` exists | `docs/INSTALL.md` step 3 |
| The lab project exists | `<CLONE>/lab.toe` exists | `docs/INSTALL.md` step 5a |
| TouchDesigner answers | Windows: `curl.exe -s -m 5 http://127.0.0.1:9981/api/td/server/td`; macOS: the same with `curl`. The answer is JSON with `success` set to true | `docs/INSTALL.md` step 5 |

When a check fails, open `docs/INSTALL.md` with the file-reading tool and do that step and the ones after it. Do not redo steps whose checks pass. When every check passes, go on to part 2.

## 2. Connect

1. Run the `td-connect` skill. It confirms that the server answers, loads tdh and reports the TouchDesigner build, the open project and any errors that already exist.
2. **Check which project is open.** In td-connect's report, `project` must be `lab.toe` and `project_folder` must be `<CLONE>` (compare with forward slashes and ignore drive-letter case). The port check cannot tell projects apart. If any other project is open, stop and tell the person: do not build into it. They close it and open `<CLONE>/lab.toe`.
3. The build must be 2025.33230 or newer. If it is older, tell the person and give them https://derivative.ca/download.
4. Tell the person in one line that setup is complete: which project is open, which build, and how many errors already existed.

## 3. Offer the scene engine

Only after part 2's project check has passed. Ask before building. Say what it is: eighteen audio-reactive scenes, a cutter and a control panel, built into the lab project by `experiments/sw_hub/build_all.py`. Say also that this builder has been run on one Windows machine and has not yet been tried from a fresh clone on a second machine, so a failure here is worth reporting. If the person says no, skip to part 4.

1. The timeline must be playing: the builder works on frame starts, and a paused timeline builds nothing. Ask the person whether the frame counter at the bottom of TouchDesigner's window is counting. If it is not, they click the play button in the timeline bar at the bottom.
2. Start it with the execute-python tool (touchdesigner-mcp: `execute_python_script`):

   ```python
   import td
   g = {'op': td.op, 'td': td, 'absTime': td.absTime, 'project': td.project}
   exec(open(td.project.folder + '/experiments/sw_hub/build_all.py', encoding='utf-8').read(), g)
   r = g['start']()
   r
   ```

   It returns the number of build steps. Keep the last line a bare variable (AGENTS.md rule 14): a last line of `g['start']()` would run twice.
3. Read progress with a second call. Wait a few seconds in the shell between calls, never inside TouchDesigner (rule 4):

   ```python
   import td
   g = {'op': td.op, 'td': td, 'absTime': td.absTime, 'project': td.project}
   exec(open(td.project.folder + '/experiments/sw_hub/build_all.py', encoding='utf-8').read(), g)
   r = g['status']()
   r
   ```

   It returns `done`, `of`, `running` and `log`. If `done` does not rise between two calls, the timeline is paused: see item 1.
4. When `running` is false, report `done` of `of`, and paste anything in `log`. Each entry in `log` is a scene whose builder raised; the others still built. Do not call it working if `log` is not empty.
5. Run `tdh.errors('/project1')` and report what it returns.

When the build finishes, the control panel opens beside the output. Show the person these three controls:

- **Speaker Volume** starts at 0. Raise it to hear the track.
- **Cut With The Music** is on. Turn it off to choose a scene by hand.
- **Next Take** steps through the takes of the chosen scene.

## 4. Finish

1. Ask the person to save: in TouchDesigner's menu bar, **File**, then **Save** (Ctrl+S on Windows). Do not save for them.
2. Tell them how to come back next time, with the real path filled in:
   1. Open TouchDesigner and open `lab.toe` from `<CLONE>` (**File**, then **Open...**).
   2. Start Claude Code in `<CLONE>`.
   3. Say "connect to TouchDesigner", then "new experiment:" followed by an idea.
3. Tell them that TouchDesigner keeps numbered copies such as `lab.2.toe` and a `Backup` folder beside the project. That is normal; always open `lab.toe`.

## Failures, by name

- **TouchDesigner is not installed.** `docs/INSTALL.md` step 2. The person installs it from https://derivative.ca/download.
- **Node.js is too old.** touchdesigner-mcp 2.2.0 needs Node.js 22.18 or newer in the 22 line, any 24, or 26 and newer; Node 20 is too old. `claude mcp get touchdesigner` then shows the server as failed. `docs/INSTALL.md` step 2.
- **The clone folder already exists.** Use it; never delete or overwrite it. `docs/INSTALL.md` step 1.
- **Port 9981 does not answer.** Exit code 7 from the `curl` check means nothing is listening: TouchDesigner is closed, or `lab.toe` is not the open project. Exit code 28 means the component accepted the connection and never replied. `docs/INSTALL.md` step 5c.
- **The Textport shows `No module named 'mcp'`.** The component's External .tox parameter is not the absolute path of `mcp_webserver_base.tox`. `docs/INSTALL.md` step 5c.
- **Registered but not restarted.** `claude mcp get touchdesigner` says Connected, but this session has no `touchdesigner` tools: the session is older than the registration. Ask the person to close this session, start Claude Code again in `<CLONE>` and say "continue setup".
- **The server is registered but failed.** The Status line is not Connected. Restarting the session will not help. Read the Issue line, run `node --version` and apply the Node.js rule in `docs/INSTALL.md` step 2; step 4 there has the rest. If Node.js was installed a moment ago, the person quits and reopens the terminal or the desktop app first, so that it sees the new version.
