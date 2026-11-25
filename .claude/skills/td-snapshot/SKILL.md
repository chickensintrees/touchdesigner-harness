---
name: td-snapshot
description: Save a TouchDesigner experiment as a reviewable git commit (.tox + text snapshot + hero frame). Use when a sketch step is worth keeping, before risky changes, and at the end of a session.
---

# Snapshot and commit

1. **Verify first:** run `td-verify`. If checks fail, the commit message must say so (`wip:`), or don't commit.
2. **Save the COMP:** `tdh.save_tox('/project1/<slug>', 'experiments/<slug>/<slug>.tox')`.
3. **Write the text snapshot:** `tdh.snapshot('/project1/<slug>', 'experiments/<slug>/snapshot/network.json')`.
4. **Hero frame:** `tdh.capture('/project1/<slug>/out1', 'experiments/<slug>/captures/hero.png')`. This is the only capture that is committed; the others are gitignored.
5. **Review the diff:** `git diff --stat` and `git diff experiments/<slug>/snapshot/network.json`.
   - Check that it shows what you meant to change, and nothing else. An operator added by accident or a parameter changed by accident shows up here.
   - Snapshots don't include the MCP server's component or generated DAT text.
6. **Update `NOTES.md`:** a log line, plus a Keepers entry if it's a keeper.
7. **Commit:** `exp(<slug>): <what changed and how it looks>`. Ask before pushing.

The .tox is what restores the experiment, and the snapshot is what makes it reviewable. Commit them together.
