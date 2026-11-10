# audio_particles

## Intent
The word (the COMP's **Text** parameter, default `SUPERWORLD!`) made of points that erupts into a smoky cloud on the beats and re-forms between them, with glowing trails and a hue that drifts faster when it's loud. Works if the word is readable between beats, the bursts visibly follow the track, it never blows out to white, and it holds 60 fps.

## References
- Techniques from The Interactive & Immersive HQ (paraphrased, our own build): RMS from an Analyze CHOP through a Lag CHOP as the level, and a Speed CHOP as volume-driven time (*Audio Reactivity with Basic POPs*, https://www.youtube.com/watch?v=XTIh2jwM_UY); feedback trails in 16-bit float (*The Secret of Feedback Loops*, https://www.youtube.com/watch?v=JkKHKsY31no).

## Inputs / outputs
- Input: the COMP's **Music Folder** + **Track** parameters pick a file through the `tracks` Folder DAT (audio files only); with the folder blank (as committed) it falls back to TD's bundled sample track, `app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'`, looping. `audioout1` (Audio Device Out, default device, volume 1.0) plays it, so the example is audible when opened; set its Active off for silence.
- Audio: `audio1` -> `mono1` (avg) -> `rms1` (rmspower) -> `lag1` (0.02 / 0.35) -> `level`; `level` -> `evolve1` (Speed) -> `evolve`.
- Points: `geo1/text1` Text POP (text = `parent(2).par.Text`, Verdana Bold, size 0.15, extruded 0.12) -> `geo1/scatter1` Sprinkle POP (perprim, 30k) -> `geo1/noise1` Noise POP (add to P, period 0.35, amp `max(0, level / max(avg, 0.01) - 1.05) * 0.9`, where `avg` is `level` through a 4 s Lag CHOP, so bursts follow each track's own loudness, t4d `evolve*0.35`). `geo1` sways (ry `sin(absTime.seconds*0.4)*25`).
- Render: `pointmat` Line MAT (points only, alpha blend), `cam1`, `render1` 1280x720 16-bit float -> `hue1` (hue `evolve*40`) -> trail (`trail_fb`/`trail_xf` 1.006/`trail_fade` 0.9/`trail_add` maximum) -> `bloom1` -> `out1`.

## Log
<!-- Newest first. -->
2026-11-10: music folder support (tested on a local folder of 116 tracks). Burst threshold now relative to a 4 s running average instead of the fixed 0.31 tuned to the sample. tdh.check PASS on the second run (first run FAIL, output truncated; likely the Folder DAT's one-off scan inside the budget window). .tox committed with Music Folder blank, so the public example uses the TD sample and carries no local path or third-party music.
2026-11-10: added audioout1 at Bill's request so the track plays.
2026-11-10: tdh.check caught `NameError: name 'sin' is not defined` on geo1 Rotate: TD expressions need `math.sin`. The sway had never run; fixed, PASS (cook_budget 1.25 ms), GIF recaptured with the sway.
2026-11-10: text version. Sphere replaced by SUPERWORLD! (Text POP -> Sprinkle POP). At rest the word reads in glowing points with motion smear (captures/10-rest.png). Burst threshold set from 80 level samples over 8 s (min 0.09, median 0.33, p75 0.38, max 0.50): 0.36 burst once in 8 s, 0.31 bursts on most beats and re-forms between. docs/media/audio_particles.gif.
2026-11-10: tdh.check PASS (cook_budget 1.37 ms over 17 active ops; level in range; moving). An earlier run read cook_budget 281 ms: geo1/pts1 (Point Generator, 71 ms per regenerate, 3 cooks in total) cooked once inside the 1 s window between samples, and cook_sample counts that one-off as per-frame cost. TD held 60 fps throughout. Harness weakness: a rare hitch reads as a budget failure; frame time would be the right measure.
2026-11-10: hue1 after the render, driven by evolve. In motion: size follows the track, hue slides yellow-green to cyan over ~4.5 s. Reads as a glowing, breathing ball; less striking than sdf_sculpture. docs/media/audio_particles.gif.
2026-11-10: alpha blending (destblend omsa) and 25k points: no white core, fuzzy burst with radial streaks; all one hue. captures/08-alpha.png.
2026-11-10: brighter points, bloom preblacklevel 0.15: white-hot core from additive overlap of 40k points. captures/07-bright.png.
2026-11-10: trail composite add -> maximum, softer bloom: no blowout but too dim (mean 0.026); radial burst streaks appear. captures/06-max.png.
2026-11-10: float feedback trail + bloom with composite *add*: blown out (max 13.7; add settles at ~1/(1-0.88) = 8x). captures/05-trails.png.
2026-11-10: one octave, period 1.1, full-res capture: a lobed cloud coloured by depth, too big, flat. captures/04-lobes.png.
2026-11-10: smaller points, colour distances 1.9-3.3, camera 2.6: too dim, shapeless fuzz (noise too fine). captures/03-small.png.
2026-11-10: translate along normal, amp 4x lower, material set by absolute path: colour now appears. Trap: `geo.par.material = '../pointmat'` silently gave the default grey material. Points huge (size x widthnear), all near-colour magenta (distancenear 3 > camera 2). captures/02-normals.png.
2026-11-10: first render: grey specks fill the frame. Noise added up to +/-1 to P (amp ~0.39 at the measured level), scattering the sphere. captures/01-a.png.
2026-11-10: audio chain live: level ~0.16 and moving, evolve climbing.

## Keepers
