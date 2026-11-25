# The demo film: what the words say

The film is cut from the scene engine's own scenes. Its words explain the harness, in the order a README would: what it is, how it works, what is in it, why it exists, how to start. This file is the copy. The shot list (`showcase.json`) carries the same words to the kinetic type scene shot by shot; `tests/test_film_copy.py` fails if the two drift apart.

Rules for the copy:

- Every statement is a fact that `README.md`, `SPEC.md` or `AGENTS.md` states. No claims about quality, no first person, no slogans.
- A line has to be read inside one shot, and a shot is two to four bars (about four to eight seconds). Main lines stay under 40 characters.
- Capitals, numerals and `. ! - : ' , ? / & # ( ) + >` only: that is what the kinetic type scene's font atlases hold.
- The film opens on line 1, set so the whole sentence is on screen at once.
- The kinetic type scene is the anchor: all twelve of its takes appear, one line each, spread through the film. The scenes between them show the thing the line before them named.

## 1. What it is

| # | Main line | Small lines |
|---|---|---|
| 1 | AN AGENT BUILDS IN LIVE TOUCHDESIGNER. | (one word to a row, repeated: the opening shot) |
| 2 | IT LOOKS AT WHAT IT MADE. | CAPTURE THE OUTPUT. OPEN THE PICTURE. / LOOK |
| 3 | THEN IT CHECKS. | NOT BLACK. MOVING. INSIDE THE FRAME BUDGET. |

## 2. How it works

| # | Main line | Small lines |
|---|---|---|
| 4 | BUILD. LOOK. CHECK. SAVE. | (one word to a beat) HOW IT WORKS / ONE STEP AT A TIME |
| 5 | (a list, one line to a beat) | RULES THE AGENT FOLLOWS / A SKILL FOR EACH STEP / A TOOLKIT INSIDE TOUCHDESIGNER / BUILD A SMALL PIECE / CAPTURE THE OUTPUT / OPEN THE PICTURE / COMPARE IT WITH THE INTENT / RUN THE CHECKS / SAVE THE .TOX / WRITE THE SNAPSHOT / COMMIT / ASK BEFORE PUSHING |

## 3. What is in it

| # | Main line | Small lines |
|---|---|---|
| 6 | (numerals counting the beat) | THE SCENE ENGINE FOLLOWS THE MUSIC / BEATS, BARS AND SECTIONS / STEMS AND DRUM HITS / ANALYSED AHEAD OF TIME |
| 7 | (a wall of lines) | A SCENE ENGINE THAT FOLLOWS MUSIC / A CUTTER THAT CUTS ON BEAT LINES / FINISHES: FILM, TAPE, TUBE, 1-BIT / IMAGE SETS FROM YOUR OWN PICTURES / CONTROLS ON EVERY EXPERIMENT / CHECKS THAT CAN FAIL / EVERY SCENE HAS SEVERAL TAKES / RENDERED LIVE |
| 8 | (bands of large type) | THE CUTTER CUTS ON THE BEAT / TREATMENTS / TRANSITIONS / TWO SCENES LAYERED / FILM / TAPE / TUBE / 1-BIT / YOUR OWN PICTURES |

## 4. Why it exists

| # | Main line | Small lines |
|---|---|---|
| 9 | (type on rings) | NO PICTURE IS CLAIMED UNSEEN / DONE MEANS CHECKED / A CHECK MUST BE ABLE TO FAIL / REVIEW IT IN A DIFF / WORDS ARE CONTROLS / SILENT UNTIL YOU TURN IT UP |
| 10 | (type as texture under a numeral) | the lines of 9 again, as a field of small letters |
| 11 | EVERY STEP IS SEEN, CHECKED AND SAVED. | WHY: SO THE WORK CAN BE REVIEWED. |

## 5. How to start

| # | Main line | Small lines |
|---|---|---|
| 12 | START IN CLAUDE CODE. | HOW TO START / BILLMOORE.AI/TOUCHDESIGNER; list: TOUCHDESIGNER 2025 / CLAUDE CODE / WINDOWS OR MACOS / GIT AND NODE.JS / A NON-COMMERCIAL LICENCE IS FINE / SET UP TOUCHDESIGNER-HARNESS WITH ME |

Twelve lines, one for each take of the kinetic type scene. Which take carries which line, and the scenes between them, are in the shot list.
