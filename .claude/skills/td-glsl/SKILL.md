---
name: td-glsl
description: Write and iterate on GLSL shaders (GLSL TOP / GLSL MAT) as files in git, with compile-error feedback. Use for any shader work in an experiment.
---

# GLSL iteration

1. **The shader is a file:** `experiments/<slug>/shaders/<name>.frag`. Write it with your file tools. Don't type it into a DAT.
2. **Link it to TD (once):**
   - Create a Text DAT `<name>_frag` inside the experiment COMP.
   - Set its `file` parameter to `experiments/<slug>/shaders/<name>.frag` and turn on Sync to File. Check the exact parameter names with `get_help` for your build.
   - Point the GLSL TOP's pixel shader parameter at that DAT.
3. **Edit, then check.** After each edit to the file, TD reloads the DAT.
   - Run `tdh.errors('/project1/<slug>')`. Compile errors show up on the GLSL TOP with line numbers. Map them to lines in the file.
   - If the error text is truncated, look at the GLSL TOP's info DAT or the Info DAT pointed at it.
4. **Look:** capture the GLSL TOP (`tdh.capture`), and read and judge the PNG as in `td-sketch`.
5. **Uniforms:** drive them from TD (CHOP exports or expressions) rather than hard-coding values. List them in `NOTES.md` so the next session knows the knobs.
6. **TD's GLSL dialect:** TD wraps your code, so use `TDOutputSwizzle()` and the `sTD2DInputs[]` samplers. Check `get_docs` for the GLSL TOP in your build before you rely on any built-in. If unsure, start from the default shader TD puts in a new GLSL TOP.
