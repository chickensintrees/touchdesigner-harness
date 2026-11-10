# feedback_drift

## Intent
Soft noise blooms feed back on themselves, spiralling slowly inward and fading into smeared trails, tinted by a colour ramp whose hue drifts all the way round about every 20 s. It works if it never goes black, never freezes, visibly changes colour within 20 s, and holds 60 fps.

## References
- First experiment built end to end with the harness on the desk machine (TD 099.2025.33230, touchdesigner-mcp 2.2.0 bridge).

## Inputs / outputs
- Inputs: none.
- Output TOP: `out1`. Resolution: 1280x720 (Non-Commercial max 1280x1280).
- Budget: holds 60 fps (see `checks.json` cook_budget).

## Log
<!-- Newest first. One entry per meaningful step: what changed, what it looked like, what next. -->
2026-11-10: parked. Kept 16-bit float, removed smear1; steps accepted, Bill moved on to other examples.
2026-11-10: smear1 blurTOP (size 3, preshrink 1) between xf1 and fade1. Smokier overall, loses crisp blooms; outer striations remain (red trail). Gap per frame at the edge is ~10 px from rotate 0.8 plus ~8 px from scale 0.988, so a 3 px blur can't bridge it. Output now reaches max 2.7 (float). captures/06-blur3.png. Two tries on the stepping: stop and ask. Options: slower spiral (smaller rotate/scale per frame), heavier blur, or accept the steps.
2026-11-10: loop to 16-bit float (IHQ digest: 8-bit quantises decay). The Feedback TOP did NOT inherit: setting noise1/ramp1 to rgba16float left fb1/xf1/fade1/add1/out1 at 8-bit until fb1.par.format was set and reset. Result: faint tails survive, so trails are longer and glow more, but the stair-stepping is unchanged. It is spatial (copy spacing), not quantisation. captures/04-before-8bit.png, 05-after-16float.png.
2026-11-09: re-verified on harness 69679a7 (cook_budget counts only ops that cooked between samples). tdh.check PASS: cook_ms 0.6 over 9 active ops, 4 idle ignored; moving delta 0.14 over 105 cooks. A 0.01 ms budget fails (0.40 ms), so the check can fail. Snapshot no longer records noise1 tx/ty. Network unchanged.
2026-11-09: xf1 scale 0.988, rotate 0.8. Reads as intended: blooms curl inward in a spiral, hue drifts (orange/violet/blue/green), never black. Flaw: visible stair-steps on the outer trails where feedback copies sit. captures/03-a.png, hero.png. Checks: 5 pass; cook_budget FAIL at 43 ms, but that is static ramp1's one-off first cook (it has cooked once in total); the rest cooks ~0.4 ms a frame and TD holds 60 fps. tdh.cook_ms sums last cook times of ops that are not cooking: harness bug, threshold left at 12 ms. Next: smooth the stepping (slight blur in the feedback path).
2026-11-09: level after noise (blacklevel 0.55, contrast 2), period 1.2. Distinct blooms with trails, but trails radiate outward (zoom >1) and the twist barely reads. captures/02-a.png. Next: scale 0.988, rotate 0.8 for an inward spiral.
2026-11-09: wired noise x hue-drifting ramp -> feedback (zoom 1.012, rotate 0.35, fade 0.965) -> maximum. Hue drift visible, never black (mean 0.25), moving. But soft fog: no visible spiral or trails. captures/01-a.png, 01-b.png. Next: contrastier noise (isolated blooms) so trails read.

## Keepers
<!-- Commits worth returning to: short hash + one line. -->
- The commit after `a4ddad4` on `exp/feedback_drift`: inward hue-drifting spiral, all checks pass. Edge stair-stepping still visible.
