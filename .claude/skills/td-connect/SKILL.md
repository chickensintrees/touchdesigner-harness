---
name: td-connect
description: Connect to the running TouchDesigner session and load the tdh toolkit. Use at the start of every TouchDesigner session, or whenever TD calls start failing.
---

# Connect to TouchDesigner

1. **Find the server.** Call the MCP server's project-info tool (TDMCP: `project_info`; others: see `docs/TRANSPORTS.md`).
   - If there is no TouchDesigner MCP server, or the call fails: stop. Tell the user to open `lab.toe` (or their project), check that the server component is Active, and check `claude mcp list`. If nothing is set up yet, offer the `td-setup` skill (the walk-through in `docs/INSTALL.md`); the same steps by hand are in `docs/SETUP.md`. Don't continue without a connection.
2. **Load tdh** with the execute-python tool (TDMCP: `execute_code`). Use this repo's absolute path: run `pwd` in the shell if you don't know it.

   ```python
   import sys
   p = r'<ABSOLUTE_REPO_PATH>/td'
   if p not in sys.path: sys.path.insert(0, p)
   import tdh
   tdh = tdh.reload()
   r = tdh.info()
   r
   ```

   `sys.path` and the loaded module persist across calls. Your variables may not. **Every later snippet** starts with `import tdh` and ends with a bare variable, like this (AGENTS.md rule 14):

   ```python
   import tdh
   r = tdh.errors('/project1/<slug>')
   r
   ```

3. **Check what came back.**
   - `harness_repo` must match this repo. tdh always reports forward slashes, so compare against `pwd` with backslashes turned into `/` and ignore drive-letter case on Windows. If they don't match, the path is wrong.
   - `td_build` should be 2025.33230 or newer for TDMCP.
   - Note `os`, which matters for file paths.
4. **Check the lab is healthy:** `r = tdh.errors('/project1')`, ending the snippet with `r`. Report any errors that already exist before you change anything, so they aren't blamed on your work.
5. Tell the user, in one line: connected to which project and build, tdh version, and how many errors already exist.

On Windows, pass paths to tdh with forward slashes or raw strings. tdh resolves relative paths against the repo root, not TD's working directory.
