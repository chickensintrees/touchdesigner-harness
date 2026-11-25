# Install, led by Claude Code

This file is written for Claude Code to follow, step by step, while a person watches and does the few things only a person can do.
A person starts it by pasting this one line into Claude Code, in any folder:

```
Set up touchdesigner-harness with me by following https://billmoore.ai/touchdesigner/install.md
```

To do the same setup by hand, read [SETUP.md](SETUP.md).

## How to run this guide

- Do one step at a time. Say in one sentence what the step is for, do it, check the result yourself, then move on.
- Do everything you can do yourself. Ask the person only for the things marked **The person does this**, and give them one numbered action at a time.
- **Ask before anything that changes the machine outside the clone folder.** That means installing or upgrading software and registering the MCP server. Say what will run and why, and wait for a yes.
- Never ask for a password, a licence key or a token. TouchDesigner's sign-in happens in TouchDesigner's own window.
- Download only from the two GitHub projects named here (`chickensintrees/touchdesigner-harness` and `8beeeaaat/touchdesigner-mcp`) and, for the MCP server in step 4, the npm package `touchdesigner-mcp-server` at 2.2.0, which is touchdesigner-mcp's own published build. For TouchDesigner, Node.js and git, give the person the vendor's link and let them run the installer.
- Never call `project.save()`. The person saves the project themselves (AGENTS.md rule 12).
- Commands are given for **PowerShell** (Windows) and for **bash/zsh** (macOS, or Git Bash on Windows). Use the form that matches the shell tool you have. Do not assume Git Bash on Windows.
- `<CLONE>` means the absolute path of the clone folder. Before you show the person any path or line to paste, replace `<CLONE>` with the real path.
- Tell the person at the start: this route is verified on Windows. On macOS it has not been tested end to end yet, so some steps may need adjusting.

## Step 1. Find the clone

The bootstrap page has normally cloned the repository already, and this file is `docs/INSTALL.md` inside it. `<CLONE>` is the folder that contains `AGENTS.md` and `docs/`.

If there is no clone yet, make one in the person's home folder (`<HOME>` below; use its real absolute path) and tell them where it is. Say first that the download is about 300 MB and can take a few minutes.

```
git clone https://github.com/chickensintrees/touchdesigner-harness.git "<HOME>/touchdesigner-harness"
```

**The clone folder already exists.** Do not delete or overwrite it. Check what it is, using the real path of that folder:

```
git -C "<the existing folder>" remote get-url origin
```

- If the answer is `https://github.com/chickensintrees/touchdesigner-harness` (with or without `.git`, or the same path over SSH), it is an earlier clone and may be out of date. Tell the person, and ask whether to use and update it. After a yes, run `git -C "<CLONE>" pull --ff-only`, then check that `<CLONE>/.claude/skills/td-setup/SKILL.md` exists. Then skip every later step whose check already passes.
- If the answer is anything else, or the pull fails, or the skill file is missing, ask the person for another folder name and clone there.

## Step 2. Check what is installed

These commands change nothing. Run them, then tell the person the result as a short list.

| Check | PowerShell | bash/zsh |
|---|---|---|
| MCP server entry | `claude mcp get touchdesigner` | `claude mcp get touchdesigner` |
| git | `git --version` | `git --version` |
| Node.js | `node --version` | `node --version` |
| TouchDesigner (Windows) | `Test-Path "C:\Program Files\Derivative\TouchDesigner\bin\TouchDesigner.exe"` | `test -f "/c/Program Files/Derivative/TouchDesigner/bin/TouchDesigner.exe"` |
| TouchDesigner (macOS) | | `test -d /Applications/TouchDesigner.app` |

**The MCP server entry decides whether Node.js matters.** If `claude mcp get touchdesigner` prints an entry whose Status line says Connected, the server already runs: skip the Node.js check and step 4, and leave the entry alone. If it prints an entry with a failed status, show the person its Command and Issue lines and ask before changing anything. If it prints no entry, apply the Node.js rule below.

On Windows the installed build can be read with `(Get-Item "C:\Program Files\Derivative\TouchDesigner\bin\TouchDesigner.exe").VersionInfo.ProductVersion`. It prints a value such as `0.99.2025.33230`; the last two numbers are the build, and it must be 2025.33230 or newer.

**TouchDesigner is not installed** (or the build is older than 2025.33230). The person does this, one item at a time:

1. Open https://derivative.ca/download and download the installer for this system.
2. Run it with the default choices.
3. Start TouchDesigner.
4. In the window that appears, sign in or make a free Derivative account, and choose the free Non-Commercial licence.
5. Say "done" when TouchDesigner shows its network: boxes joined by wires on a dark background.

Then run the check again. If the person installed it somewhere else, ask where.

**Node.js is too old** (or missing). The rule for touchdesigner-mcp 2.2.0: 22.18 or newer in the 22 line, any 24, or 26 and newer pass. Everything else fails, including 20, 23 and 25, and the server will not start. This harness has only been run on 24.

Tell the person the version found. Say that the installer replaces the Node.js on this machine for everything that uses it, and ask whether to go ahead. If they have other projects that need the old version, or use a version manager (nvm, fnm, volta), stop and let them choose how to provide Node.js 24. The person does this:

1. Open https://nodejs.org/en/download.
2. Ignore the box of commands near the top. In the version list, choose **v24 (LTS)**. The page offers v26 first; that also passes the rule, but 24 is the tested one.
3. Download the Windows Installer (.msi), or on macOS the installer (.pkg).
4. Open the downloaded file and accept the default choices until it finishes.

A shell that was already open does not see the new version, so check it by full path: `& "C:\Program Files\nodejs\node.exe" --version` on Windows, `/usr/local/bin/node --version` on macOS.

**git is missing.** On Windows the person installs it from https://git-scm.com/downloads. On macOS, running `git --version` offers to install Apple's command line tools; the person accepts that.

## Step 3. Download the TouchDesigner component

This puts touchdesigner-mcp's component, release 2.2.0, into `<CLONE>/touchdesigner-mcp-td/`. Tell the person what is being downloaded; it stays inside the clone and git ignores it. Skip the step if `<CLONE>/touchdesigner-mcp-td/mcp_webserver_base.tox` exists.

PowerShell:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri https://github.com/8beeeaaat/touchdesigner-mcp/releases/download/v2.2.0/touchdesigner-mcp-td.zip -OutFile "<CLONE>\touchdesigner-mcp-td.zip"
(Get-FileHash "<CLONE>\touchdesigner-mcp-td.zip" -Algorithm SHA256).Hash
Expand-Archive -Path "<CLONE>\touchdesigner-mcp-td.zip" -DestinationPath "<CLONE>\touchdesigner-mcp-td" -Force
```

bash/zsh:

```bash
curl -sSL -o "<CLONE>/touchdesigner-mcp-td.zip" https://github.com/8beeeaaat/touchdesigner-mcp/releases/download/v2.2.0/touchdesigner-mcp-td.zip
shasum -a 256 "<CLONE>/touchdesigner-mcp-td.zip"
unzip -q -o "<CLONE>/touchdesigner-mcp-td.zip" -d "<CLONE>/touchdesigner-mcp-td"
```

Run the three lines one at a time. The hash on the second line must be `67a10b7abba05c2b55912625ad40dcd3d2420e1c8a8d64ca644c473dabf38ec0` (compare without case). If it differs, stop and tell the person; do not unpack the file.

Check that the folder now holds `mcp_webserver_base.tox`, `import_modules.py` and `modules/`. Never move or rename anything inside it: the component finds `modules/` beside the `.tox`.

## Step 4. Register the MCP server (ask first)

Skip this step if `claude mcp get touchdesigner` in step 2 found an entry.

Otherwise tell the person all of this, then wait for a yes:

- This adds one entry named `touchdesigner` to Claude Code's user configuration (`~/.claude.json`), so it is available in every folder, not only this one.
- With it, Claude Code can run Python inside whatever project is open in TouchDesigner, whenever that project holds the component from step 5. That is why step 5 makes a new lab project: never add the component to a show file.
- The server is touchdesigner-mcp 2.2.0. `npx -y` downloads it from the npm registry on first use without a second question, so this yes also covers that download.
- To undo it later: `claude mcp remove touchdesigner -s user`.

```
claude mcp add -s user touchdesigner -- npx -y touchdesigner-mcp-server@2.2.0
```

The version is pinned on purpose: the server and the component from step 3 must come from the same release.

Check with `claude mcp get touchdesigner` and read its Status line. The first run downloads the package, so if the status is not Connected, run the check once more.

- **Connected:** go on.
- **Failed:** do not go on to step 6. Read the Issue line and check Node.js again by full path (step 2). If Node.js was installed during this setup, this shell may still be using the old one: say so, and repeat this check as the first thing in step 6's new session.
- **Failed on Windows although Node.js passes the rule:** Claude Code may not be able to start `npx` directly. This case has not been observed on the test machine. Ask, then remove the entry and add it again with `cmd /c` before `npx` (PowerShell: `claude mcp add -s user touchdesigner -- cmd /c npx -y touchdesigner-mcp-server@2.2.0`; in Git Bash write `cmd //c`).

If the shell cannot find the `claude` command, stop and tell the person. The same step by hand is in [SETUP.md](SETUP.md).

## Step 5. Four things in TouchDesigner's window

Only the person can do these. Give them one numbered group at a time, with the real paths filled in, and run the check after each group before giving the next.

Before 5a, run the port check: Windows `curl.exe -s -m 5 http://127.0.0.1:9981/api/td/server/td`, macOS the same with `curl`. If it already answers with JSON, some TouchDesigner project with the component is open, and the answer does not say which. Ask the person. If it is `<CLONE>/lab.toe`, step 5 is done. If it is another project, ask them to save and close it before going on.

### 5a. Make the lab project

First ask: "Is anything of your own open in TouchDesigner?" The lab project must start as a new, empty project, or the person's own work would be saved as `lab.toe` and built into.

The person does this:

1. Open TouchDesigner. If a project of your own is open, save it first.
2. In the menu bar at the top, click **File**, then **New**.
3. Click **File**, then **Save As...**.
4. Windows: click in the **File name** box, paste `<CLONE>\lab.toe` and press Enter. macOS: choose the folder `<CLONE>`, type `lab.toe` as the name, and click **Save**.

Check: the file `<CLONE>/lab.toe` exists. This project stays out of git.

### 5b. Drop the component in

Open the folder for the person with the file selected. This only opens a file window. PowerShell: `explorer.exe /select,"<CLONE>\touchdesigner-mcp-td\mcp_webserver_base.tox"` (its exit code is 1 even when it works). macOS: `open -R "<CLONE>/touchdesigner-mcp-td/mcp_webserver_base.tox"`. In Git Bash, or if no window opens with the file highlighted, tell the person the folder path and the file name instead.

The person now has a folder window with `mcp_webserver_base.tox` highlighted. The person does this:

1. If TouchDesigner covers the folder window, make TouchDesigner's window smaller so both can be seen.
2. Read out the path shown in the bar above TouchDesigner's network. It is normally `/project1`.
3. Drag `mcp_webserver_base.tox` from the folder window onto an empty part of the dark background in TouchDesigner, and let go.
4. Read out the name under the new box. It is normally `mcp_webserver_base`.

The system may ask whether TouchDesigner may accept incoming connections. Either answer works, because Claude Code connects from this same computer.

There is no check yet. Go straight on to 5c.

### 5c. Point the component at its files

The component must know the full path of its own `.tox`, or it cannot load its Python modules. Build this line with the real path, using forward slashes. If the person read out another path or name in 5b, use that in place of `/project1/mcp_webserver_base`.

```python
op('/project1/mcp_webserver_base').par.externaltox.val = r'<CLONE>/touchdesigner-mcp-td/mcp_webserver_base.tox'
```

Tell the person first: the Textport may already show a red line ending `No module named 'mcp'`. It is from the moment the box was dropped in, before this step, and is expected.

The person does this:

1. In TouchDesigner's menu bar, click **Dialogs**, then the entry that starts with **Textport**. A window with a text prompt opens.
2. Copy the line above and click in the Textport.
3. Paste it with Ctrl+V (Cmd+V on macOS) and press Enter.

The line does what [SETUP.md](SETUP.md) describes by hand: it sets the component's **External .tox** parameter to an absolute path.

Do not ask the person to judge the result. Run the port check from the start of step 5. A good answer is JSON with `success` set to true and TouchDesigner's version in it.

**Port 9981 does not answer.** Read the exit code of the check.

- Exit code 7: nothing is listening. TouchDesigner is closed, or the box is not in the open project. Go back to 5a or 5b.
- Exit code 28: the port accepts the connection and never replies. The component did not load its modules. Ask the person to read out the last lines of the Textport.

**The Textport shows `'NoneType' object has no attribute 'par'`.** The path in the line does not match the box. Ask the person for the path bar and the name under the box again, and rebuild the line.

**The Textport shows `No module named 'mcp'`** after the pasted line. The component is looking for `modules/` in the wrong folder. Check that `<CLONE>/touchdesigner-mcp-td/modules/mcp/` exists and that the path in the pasted line is the real, full path. Then have the person paste the corrected line.

**The path is right and the exit code is still 28.** The person does 5d, closes TouchDesigner, starts it again and opens `<CLONE>/lab.toe` with **File**, then **Open...**. The component reads the stored path when the project loads. Run the port check again.

### 5d. Save the project

The person does this:

1. In TouchDesigner's menu bar, click **File**, then **Save**. (Ctrl+S on Windows does the same.)

Check: `lab.toe` in `<CLONE>`, or a numbered copy such as `lab.2.toe` beside it, was modified in the last minute. TouchDesigner keeps numbered copies and a `Backup` folder; git ignores them, and `lab.toe` is always the newest.

## Step 6. Hand over to a new session

This session cannot use the `touchdesigner` server: **it is registered but the session was not restarted**, and Claude Code loads MCP servers only when a session starts. Give the person the group that matches where this session runs, with the real path filled in. If you cannot tell, ask whether they are in a terminal window or in the Claude Code desktop app.

In a terminal:

1. Leave TouchDesigner open.
2. Open a new terminal window. Windows: press the Windows key, type `PowerShell`, press Enter. macOS: press Cmd+Space, type `Terminal`, press Return.
3. Paste this line and press Enter: `cd "<CLONE>"`
4. Type `claude` and press Enter.
5. If Claude Code asks whether you trust this folder, answer yes. It is the repository cloned in step 1. Setup continues only after a yes.
6. If it asks about an MCP server named `tdmcp`, no is fine. That is a second, optional server that is not installed here, and it can be enabled later.
7. Type: `continue setup`

In the Claude Code desktop app:

1. Leave TouchDesigner open.
2. If Node.js was installed during this setup, quit the app completely and open it again.
3. Start a new session and choose the folder `<CLONE>`.
4. Answer the questions in items 5 and 6 above the same way.
5. Type: `continue setup`

The old session can be closed afterwards. The new one finishes with the `td-setup` skill in `.claude/skills/td-setup/SKILL.md`: it connects, confirms that TouchDesigner answers from `<CLONE>/lab.toe`, and offers to build the scene engine.

## Failures, by name

| What is seen | Where it is handled |
|---|---|
| TouchDesigner is not installed, or is too old | Step 2 |
| Node.js is too old or missing | Step 2 |
| The clone folder already exists | Step 1 |
| Port 9981 does not answer | Step 5c |
| The Textport shows `No module named 'mcp'` | Step 5c |
| The MCP server is registered but the session was not restarted | Step 6, and the `td-setup` skill |
