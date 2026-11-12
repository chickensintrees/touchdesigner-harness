# Builder for /project1/sc_shatter. Run inside TouchDesigner:
#   g = {'op': op, 'td': td, '__name__': 'build'}
#   exec(open(project.folder + '/experiments/sc_shatter/build.py', encoding='utf-8').read(), g)
#   path = g['build']()
# Idempotent: destroys and rebuilds the whole scene.
# see: experiments/sc_shatter/NOTES.md (2026-11-10; section "Assets", 2026-11-11)
import math
import os
import td

REPO = td.project.folder.replace(chr(92), '/')      # build-time only: never written into a parameter
SLUG = 'sc_shatter'
HERE = REPO + '/experiments/' + SLUG
CACHE = HERE + '/cache'
NOASSETS = 'noassets'     # cache/noassets/: atlases baked from the stand-ins (teapot, default face)
FONT = 'archivo'          # mod.paths.font name of the extruded phrases' face

# Everything that belongs to an asset pack: which models and phrases the scene shatters, how each
# is cut, and which take shows which. A pack may replace any of these four names with its own
# scenes/sc_shatter/words.json (mod.paths.words); build() reads them once, as W. Keep this a plain
# literal: bake.py reads it as text when it runs in a shell.
#   MODELS   subject name -> the pack's model (slug) and its fracture settings (see bake.py:
#            cells = micro, fine, coarse; thick; decimate, cap, maxedge; scale and yaw turn and size
#            the model before the cut; faceup lays it on its back; shell, inner, instanced). standin is
#            the flat colour (sRGB) of the teapot that replaces a model the pack does not have,
#            a different one per subject so a section change still shows.
#   PHRASES  subject name -> an extruded phrase (text, width in units) and its fracture settings.
#   TAKES    take name -> its subjects (the section and the shot seed pick one), and any of the
#            take's numbers (DEFAULTS below) retuned for these subjects.
#   LABELS   take name -> the first line of the Describe caption, where it names the subject.
WORDS = {
    "MODELS": {
        "bust": {"slug": "marble_bust", "cells": [2400, 260, 12], "thick": 0.02, "shell": True, "standin": [0.93, 0.89, 0.78]},
        "amphora": {"slug": "amphora", "cells": [2400, 260, 12], "thick": 0.025, "shell": True, "standin": [0.72, 0.38, 0.24]},
        "stone": {"slug": "pierced_stone", "cells": [2400, 260, 12], "thick": 0.025, "shell": True, "standin": [0.84, 0.84, 0.82]},
        "gramophone": {"slug": "gramophone", "cells": [2400, 260, 12], "thick": 0.02, "shell": True, "standin": [0.66, 0.50, 0.24]},
        "helmet": {"slug": "space_helmet", "cells": [2400, 260, 12], "thick": 0.025, "shell": True, "standin": [0.90, 0.90, 0.88]},
        "lander": {"slug": "lander", "cells": [2400, 260, 12], "thick": 0.018, "shell": True, "standin": [0.86, 0.71, 0.24]},
        "astrolabe": {"slug": "astrolabe", "cells": [2400, 260, 12], "thick": 0.016, "shell": True, "standin": [0.72, 0.56, 0.28]},
        "hourglass": {"slug": "hourglass", "cells": [2400, 260, 12], "thick": 0.018, "shell": True, "standin": [0.36, 0.20, 0.17]},
        "cone": {"slug": "traffic_cone", "cells": [2400, 260, 12], "thick": 0.022, "shell": True, "standin": [0.92, 0.42, 0.12]},
        "column": {"slug": "broken_column", "cells": [2400, 260, 12], "thick": 0.025, "shell": True, "standin": [0.90, 0.86, 0.76]},
        "solids": {"slug": "balanced_solids", "cells": [2400, 260, 12], "thick": 0.02, "shell": True, "standin": [0.20, 0.36, 0.69]},
        "crystal": {"slug": "crystal_cluster", "cells": [2400, 260, 12], "thick": 0.02, "shell": True, "standin": [0.30, 0.30, 0.34]},
        "cage": {"slug": "wire_cage", "cells": [2400, 260, 12], "thick": 0.012, "shell": True, "standin": [0.49, 0.49, 0.47]},
        "duck_s": {"slug": "rubber_duck", "cells": [280, 44, 6], "thick": 0.03, "shell": True, "decimate": 24, "cap": 2800, "inner": False, "instanced": True, "standin": [0.93, 0.78, 0.16]},
        "amphora_s": {"slug": "amphora", "cells": [280, 44, 6], "thick": 0.03, "shell": True, "decimate": 24, "cap": 2800, "inner": False, "faceup": True, "instanced": True, "standin": [0.72, 0.38, 0.24]},
        "bust_m": {"slug": "marble_bust", "cells": [700, 110, 9], "thick": 0.03, "shell": True, "decimate": 70, "cap": 8300, "instanced": True, "standin": [0.93, 0.89, 0.78]},
    },
    "PHRASES": {
        "w_touch": {"text": "DO NOT\nTOUCH", "width": 2.6, "cells": [2600, 320, 14], "thick": 0.03, "maxedge": 0.03},
        "w_frame": {"text": "EVERY FRAME\nIS MADE NOW.", "width": 3.4, "cells": [2600, 400, 16], "thick": 0.03, "maxedge": 0.03},
        "w_sound": {"text": "SOUND IN.\nPICTURE OUT.", "width": 3.6, "cells": [2600, 400, 16], "thick": 0.03, "maxedge": 0.03},
        "w_nothing": {"text": "NOTHING HERE IS\nPRERENDERED.", "width": 3.5, "cells": [2600, 400, 16], "thick": 0.03, "maxedge": 0.03},
        "w_here": {"text": "HERE.\nNOW.", "width": 2.4, "cells": [2600, 320, 12], "thick": 0.03, "maxedge": 0.03},
        "w_object": {"text": "OBJECT OF\nUNKNOWN USE", "width": 3.6, "cells": [2600, 400, 16], "thick": 0.03, "maxedge": 0.03},
        "w_found": {"text": "FOUND,\nNOT MADE.", "width": 2.8, "cells": [2600, 320, 14], "thick": 0.03, "maxedge": 0.03},
    },
    "TAKES": {
        "porcelain": {"subjects": ["bust", "amphora", "stone"]},
        "mat": {"subjects": ["duck_s", "amphora_s"]},
        "knoll": {"subjects": ["gramophone", "helmet", "lander", "astrolabe", "hourglass", "cone"]},
        "murmur": {"subjects": ["w_frame", "w_sound", "w_nothing", "w_object"]},
        "chorus": {"subjects": ["bust_m"]},
        "slabs": {"subjects": ["column", "solids", "cone", "hourglass"]},
        "glass": {"subjects": ["amphora", "hourglass", "helmet", "crystal", "stone"], "dist": 2.65, "tgty": 0.5, "height": 0.75},
        "collapse": {"subjects": ["w_touch", "w_here", "w_found"]},
        "cloud": {"subjects": ["lander", "gramophone", "crystal", "helmet"]},
        "onebit": {"subjects": ["cage", "astrolabe", "lander", "gramophone"]},
    },
    "LABELS": {
        "chorus": "SEVEN GILDED COPIES OF ONE PRE-CUT MODEL; THE FLOOR REFLECTION IS A MIRRORED COPY",
    },
}
# Subjects that are the same on every pack (their settings are SUBJECTS in bake.py), after the
# pack's own in the atlas switch.
SHARED = [
    # Describe mode's phrases for the two text takes (TAKES 'describe')
    'x_chips', 'x_flock', 'x_bars', 'x_math', 'x_blocks', 'x_fall', 'x_rev',
    # Input: 16:9 slabs that carry the picture named by the Input parameter (TAKES 'input')
    'panel', 'panel_f', 'panel_s', 'panel_m']
LABEL_FONT = 'barlow'     # mod.paths.font name of the Describe caption's face
LABEL_W, LABEL_H, LABEL_PX = 1232, 84, 27      # the Describe caption strip (pixels) and its font size
TEXT_DEPTH = 0.55     # Text POP extrude depth, in the Text POP's own units (the bake rescales)


def lin(hexcol, gain=1.0):
    """sRGB hex -> linear rgb tuple."""
    h = hexcol.lstrip('#')
    return tuple(round(((int(h[i:i + 2], 16) / 255.0) ** 2.2) * gain, 4) for i in (0, 2, 4))


# Every take is the same machine with different numbers. DEFAULTS documents each number.
DEFAULTS = dict(
    # motion
    level=1,        # 0 micro chips, 1 fine cells, 2 coarse cells, 3 slabs
    power=0.8,      # how far a shard travels at full burst (units)
    spin=0.6,       # turns at full burst
    spread=0.35,    # randomness of the burst direction
    gravity=0.0,    # downward sag at full burst (units)
    swirl=0.0,      # flow-field drift while hanging (murmuration)
    d0=0.15,        # start stagger across cells (fraction of the cycle)
    d1=0.10,        # lock-in stagger
    omode=0,        # stagger order: 0 random, 1 from an impact point, 2 reading order, 3 top first
    cyc=1.0,        # bars per burst cycle
    rest=0.0,       # fraction of the cycle spent whole after locking in
    jolt=0.10,      # how much a kick opens the cracks
    arrp=0.5,       # arrival burst at the cut (closes in the first half second)
    drift=0.25,     # outward drift while hanging
    fclamp=1,       # shards rest on the floor instead of passing through it
    lay=0,          # 0 burst outward, 1 knolling: every cell hops to a slot in a tidy grid on the floor
    kgap=0.2,       # pitch of that grid (units)
    stepq=0.0,      # > 0: the phase moves in this many steps per cycle (stop motion)
    slabdir=0.0,    # direction the slabs slide in, radians in xz (level 3; the planes are baked, 10 per unit)
    # layout
    soup=0,         # 0 the big soup (one object), 1 the small soup (dozens), 2 the mid soup (a handful)
    nx=1, nz=1, sx=1.0, sz=1.0,
    wave=0.0,       # how much of the cycle the instance wave takes to cross the grid
    wavedir=0.0,    # wave direction, radians in xz
    yawjit=0.0,     # per-instance yaw jitter, radians
    oscale=1.0, oyaw=0.0,
    insub=-1,       # Input: index in SUBJ of the slab this take shatters instead of its own subject
                    # (-1 = the take ignores Input); set from the take's 'input' name
    inscale=1.0,    # Input: object scale while the slab is the subject
    inyaw=0.0,      # Input: extra object yaw (radians) while the slab is the subject
    # camera
    dist=3.0, height=0.8, az=20.0, swing=12.0, orbit=0.0, tgtx=0.0, tgty=0.5, tgtz=0.0, fov=40.0,
    azseed=30.0,    # degrees of azimuth the shot seed can add
    # light
    laz=-40.0, lel=52.0,
    keyr=2.6, keyg=2.4, keyb=2.1, amb=0.35,
    envr=0.5, envg=0.55, envb=0.6,
    rough=0.38, envs=1.0, refl=0.3,
    inr=1.0, ing=0.62, inb=0.12, inem=0.5, inmetal=1.0,
    tr=1.0, tg=1.0, tb=1.0,
    burstglow=0.0,
    skinmetal=0.0,  # 1 = the outer skin is gilded (the texture only darkens the gold)
    glass=0,        # 1 = shards drawn additively without depth: rims and glints only
    # backdrop
    wAr=0.03, wAg=0.05, wAb=0.07, wBr=0.004, wBg=0.008, wBb=0.014,
    fAr=0.10, fAg=0.13, fAb=0.16, fBr=0.008, fBg=0.012, fBb=0.018,
    poolr=3.2, shadow=0.75, pattern=0, shR=3.0, shblur=3.0,
    # post
    unlit=0, mode=0, expo=1.0, glow=0.5, vig=0.5, sat=1.05,
)

GOLD = (1.0, 0.62, 0.12)
RED = lin('#C8261C')

IVORY = lin('#EEE4CC')
YELLOW = lin('#DCB53D')
BLUE = lin('#287E9B')
PINK = lin('#B85779')
CREAM = lin('#EDE3C8')
PUTTY = lin('#C8BFA6')


def _c(prefix, rgb, gain=1.0):
    """Expand a colour into the three numbered take parameters, e.g. _c('wA', IVORY)."""
    if prefix in ('in', 't', 'key', 'env'):
        keys = [prefix + k for k in 'rgb']
    else:
        keys = [prefix + k for k in 'rgb']
    return {k: round(v * gain, 4) for k, v in zip(keys, rgb)}


INK = lin('#192B3B')
BRICK = lin('#A8322B')

# Order matters: the cutter counts a scene's visits 0, 1, 2 ..., so neighbours here are shown on
# consecutive visits. Each neighbour differs in layout, palette and scale.
TAKES = [
    # 0 porcelain: one statuette close up, a few big pieces, cracks lit gold from inside
    dict(name='porcelain',
         label=('SHATTER AND REASSEMBLE: A 3D MODEL CUT INTO ABOUT A DOZEN BIG PIECES BEFORE PLAYBACK',
                'A shader pushes the pieces apart and pulls them back, whole on every bar line. Kick drums open the cracks.'),
         label_in=('SHATTER AND REASSEMBLE: THE INPUT PICTURE ON A SLAB CUT INTO A DOZEN BIG PIECES',),
         input='panel', inscale=0.85,
         level=2, power=0.17, spin=0.035, spread=0.12, d0=0.22, d1=0.12, omode=1, cyc=1.0, rest=0.0,
         jolt=0.6, arrp=1.6, drift=0.5,
         dist=2.8, height=0.80, az=28.0, swing=16.0, tgty=0.53, tgtx=0.18, fov=40.0,
         inr=1.0, ing=0.52, inb=0.07, inem=0.28, refl=0.38, glow=0.45, laz=-50.0, lel=48.0),
    # 1 mat: forty copies of one small object laid out on a green cutting mat, seen from straight
    # above, detonating in a wave (it must read from above: NOTES log 11)
    dict(name='mat',
         label=('FORTY COPIES OF ONE PRE-CUT MODEL, EACH IN ABOUT 40 SHARDS',
                "A burst wave crosses the grid every two bars. Each shard's path is a formula of the bar phase, so it reverses exactly."),
         label_in=('FORTY COPIES OF THE INPUT PICTURE, EACH ON A SLAB PRE-CUT INTO 40 SHARDS',),
         input='panel_s',
         soup=1, nx=8, nz=5, sx=1.32, sz=1.12, oyaw=0.0, yawjit=0.6, wave=0.5,
         level=1, power=0.55, spin=0.9, spread=0.5, d0=0.1, d1=0.05, cyc=2.0, rest=0.25, jolt=0.3, arrp=0.8,
         dist=0.05, height=19.5, az=0.0, swing=0.0, azseed=0.0, tgty=0.0, tgtz=-0.25, fov=33.0,
         laz=-60.0, lel=30.0, keyr=3.0, keyg=2.8, keyb=2.4, amb=0.7, envr=0.9, envg=0.9, envb=0.8,
         inr=RED[0], ing=RED[1], inb=RED[2], inem=0.3, inmetal=0.0,
         **_c('fA', lin('#7F9478')), **_c('fB', lin('#5E6E58')), poolr=14.0, pattern=1, shadow=0.72,
         shR=8.0, shblur=2.0, refl=0.0, glow=0.25, vig=0.35, expo=0.95),
    # 2 knoll: one object takes itself apart into a tidy grid of its own pieces, each lying skin up
    # with its shadow, on ink blue; then the grid flies home (knolling, not an explosion)
    dict(name='knoll',
         label=('KNOLLING: ONE MODEL TAKEN APART INTO ITS 260 PRE-CUT PIECES',
                'Each piece hops to a slot in a grid, turns its skin up and scales to fit, then flies home. One cycle is two bars.'),
         label_in=('KNOLLING: THE INPUT PICTURE ON A SLAB, TAKEN APART INTO ITS 260 PRE-CUT PIECES',),
         input='panel_f',
         lay=1, kgap=0.205, level=1, power=0.3, spin=0.0, spread=0.3, drift=0.0, cyc=2.0, rest=0.125,
         d0=0.3, d1=0.25, jolt=0.35, arrp=0.8,
         dist=0.7, height=6.6, az=0.0, swing=4.0, azseed=8.0, tgty=0.0, tgtz=-0.3, fov=44.0,
         laz=-62.0, lel=34.0, keyr=2.1, keyg=2.0, keyb=1.85, amb=0.55, envr=0.7, envg=0.8, envb=0.9,
         **_c('in', YELLOW), inem=0.06, inmetal=0.0,
         **_c('fA', INK, 2.6), **_c('fB', INK, 1.2), **_c('wA', INK, 1.2), **_c('wB', INK, 0.6),
         poolr=9.0, shadow=0.8, shR=3.6, shblur=1.5, refl=0.0, glow=0.3, vig=0.4),
    # 3 murmur: a sentence made of thousands of chips flocking, then locking in, 1-bit
    dict(name='murmur',
         describe=['x_chips', 'x_flock', 'x_bars', 'x_math'],
         label=('A 3D SENTENCE CUT INTO NEARLY 5,000 CHIPS, DRAWN IN PURE BLACK AND WHITE',
                'The chips ride a flow field, then lock in from left to right and hold for one bar.'),
         label_in=('THE INPUT PICTURE ON A SLAB CUT INTO NEARLY 5,000 CHIPS, DITHERED TO BLACK AND WHITE',),
         input='panel', inscale=2.3,
         level=0, power=1.3, spin=1.6, spread=1.0, swirl=1.6, omode=2, d0=0.3, d1=-0.3, cyc=2.0, rest=0.5,
         jolt=0.08, arrp=0.6, fclamp=0, unlit=1, mode=1, refl=0.0, shadow=0.0, glow=0.0, vig=0.0,
         wAr=0, wAg=0, wAb=0, wBr=0, wBg=0, wBb=0, fAr=0, fAg=0, fAb=0, fBr=0, fBg=0, fBb=0,
         dist=5.2, height=0.6, tgty=0.5, fov=44.0, az=0.0, swing=8.0, azseed=14.0),
    # 4 chorus: a receding line of seven gilded copies of one object on brick red, cracking open one
    # after another along the line; plaster-white insides (its caption's first line is W['LABELS'])
    dict(name='chorus',
         label=('',
                'They crack open one after another down the line, once every two bars. Vocals brighten the white insides.'),
         label_in=('SEVEN GILDED COPIES OF THE INPUT PICTURE; THE FLOOR REFLECTION IS A MIRRORED COPY',),
         input='panel_m', inscale=1.5, inyaw=1.5708,
         soup=2, nx=7, nz=1, sx=0.80, yawjit=0.3, wave=0.6, skinmetal=1.0,
         level=2, power=0.2, spin=0.05, spread=0.15, d0=0.2, d1=0.1, omode=1, cyc=2.0, rest=0.25,
         jolt=0.6, arrp=1.3, drift=0.5,
         dist=4.6, height=0.62, az=52.0, swing=6.0, azseed=30.0, tgty=0.5, tgtx=0.5, fov=36.0,
         **_c('wA', BRICK, 0.9), **_c('wB', BRICK, 0.3), **_c('fA', BRICK, 1.5), **_c('fB', BRICK, 0.5),
         **_c('in', IVORY), inem=0.55, inmetal=0.0, rough=0.26, envs=1.2,
         keyr=2.6, keyg=2.35, keyb=1.9, amb=0.5, envr=1.0, envg=0.6, envb=0.5,
         poolr=7.0, shadow=0.7, shR=5.0, refl=0.4, glow=0.4, laz=-30.0, lel=44.0),
    # 5 slabs: one object sliced into slabs that slide apart, side-on, ident yellow and blue
    dict(name='slabs',
         label=('ONE MODEL SLICED ON HORIZONTAL PLANES, TEN SLICES PER UNIT OF HEIGHT',
                'The slabs slide apart from the top down and close again once per bar. Kick drums nudge them open.'),
         label_in=('THE INPUT PICTURE ON A SLAB SLICED ON HORIZONTAL PLANES, TEN SLICES PER UNIT OF HEIGHT',),
         input='panel',
         level=3, power=0.32, spin=0.12, slabdir=0.3, omode=3, d0=0.45, d1=0.3, cyc=1.0, rest=0.0, jolt=0.25,
         arrp=0.4, drift=0.0,
         dist=5.9, height=0.8, tgty=0.42, tgtx=0.3, fov=24.0, az=14.0, swing=5.0, azseed=20.0,
         **_c('wA', YELLOW), **_c('wB', YELLOW, 0.8), **_c('fA', YELLOW, 1.25), **_c('fB', YELLOW, 0.9),
         **_c('in', BLUE), inem=0.25, inmetal=0.0, keyr=2.6, keyg=2.6, keyb=2.6, amb=0.8,
         envr=0.9, envg=0.85, envb=0.6, shadow=0.55, refl=0.2, poolr=6.0, glow=0.3, sat=1.1, vig=0.3),
    # 6 glass: the object as a ghost of green glass, drawn additively: rims and glints only, shards
    # drifting apart and back, off-centre in the dark
    dict(name='glass',
         label=('THE SAME SHARDS DRAWN ADDITIVELY WITH NO DEPTH TEST',
                'Only edge-on rims and highlights add up to brightness, so the object reads as glass. It opens and closes over two bars.'),
         label_in=('THE INPUT PICTURE ON GLASS SHARDS, DRAWN ADDITIVELY WITH NO DEPTH TEST', 'Rims, highlights and the picture add up to brightness. The slab opens and closes over two bars.'),
         input='panel',
         glass=1, level=1, power=0.4, spin=0.3, spread=0.3, d0=0.25, d1=0.2, cyc=2.0, rest=0.125,
         jolt=0.3, arrp=0.5, drift=0.4, swirl=0.1, fclamp=0,
         dist=2.3, height=0.7, tgty=0.45, tgtx=-0.25, fov=46.0, az=0.0, swing=30.0, orbit=3.0, azseed=360.0,
         tr=0.30, tg=1.0, tb=0.45, inr=0.35, ing=0.75, inb=1.0, inem=0.12, inmetal=0.0,
         keyr=2.4, keyg=2.4, keyb=2.4, envr=0.3, envg=0.5, envb=0.4, rough=0.3,
         wAr=0.0, wAg=0.012, wAb=0.008, wBr=0.0, wBg=0.0, wBb=0.0,
         fAr=0.0, fAg=0.03, fAb=0.02, fBr=0.0, fBg=0.0, fBb=0.0,
         shadow=0.0, refl=0.0, glow=0.9, vig=0.5, expo=1.0),
    # 7 collapse: a red phrase falls into a heap of blocks and un-falls, seen low from one end
    dict(name='collapse',
         describe=['x_blocks', 'x_fall', 'x_rev'], inscale=1.4,
         label=('EXTRUDED 3D TEXT CUT INTO HUNDREDS OF BLOCKS',
                'The blocks fall from the top down, then the same motion runs backwards. One fall and rise takes two bars.'),
         label_in=('THE INPUT PICTURE ON A SLAB CUT INTO 260 BLOCKS',),
         input='panel',
         level=1, power=0.85, spin=0.5, spread=0.6, gravity=1.0, omode=3, d0=0.35, d1=0.2, cyc=2.0, rest=0.25,
         jolt=0.2, **_c('t', RED), inr=0.02, ing=0.035, inb=0.06, inem=0.0, inmetal=0.0,
         dist=2.3, height=0.16, az=-56.0, swing=6.0, tgty=0.42, tgtx=-0.35, fov=66.0, azseed=12.0,
         **_c('wA', CREAM), **_c('wB', CREAM, 0.7), **_c('fA', PUTTY, 1.1), **_c('fB', PUTTY, 0.7),
         shadow=0.65, refl=0.25, amb=0.7, envr=0.9, envg=0.85, envb=0.75, poolr=6.0, glow=0.35),
    # 8 cloud: slow motion, the camera inside a cloud of chips, black room, red lining
    dict(name='cloud',
         label=('THE CAMERA SITS INSIDE ONE BURST THAT LASTS FOUR BARS',
                "Nothing is simulated: each shard's position is a formula of the bar phase, so every piece returns to its place."),
         label_in=('THE CAMERA SITS INSIDE ONE BURST OF THE INPUT PICTURE THAT LASTS FOUR BARS',),
         input='panel',
         level=1, power=0.95, spin=0.5, spread=0.4, d0=0.1, d1=0.2, cyc=4.0, rest=0.125, jolt=0.15, arrp=0.3,
         drift=0.9, swirl=0.12,
         dist=1.45, height=0.55, tgty=0.36, fov=62.0, az=0.0, swing=40.0, orbit=6.0, azseed=360.0,
         wAr=0.012, wAg=0.012, wAb=0.016, wBr=0.0, wBg=0.0, wBb=0.0,
         fAr=0.03, fAg=0.03, fAb=0.035, fBr=0.0, fBg=0.0, fBb=0.0, shadow=0.6, refl=0.25,
         keyr=2.3, keyg=2.2, keyb=2.1, amb=0.25, inr=RED[0], ing=RED[1], inb=RED[2], inem=0.9, inmetal=0.0,
         glow=0.6, burstglow=0.3, shR=4.0, expo=0.9),
    # 9 onebit: one lit object on white paper, everything dithered to pure black and white,
    # moving in twelve steps a burst like stop motion
    dict(name='onebit',
         label=('ONE LIT MODEL AND ITS SHADOW, DITHERED TO PURE BLACK AND WHITE',
                'The burst phase is rounded to twelve steps per burst, which gives the stop-motion look.'),
         label_in=('THE INPUT PICTURE ON A LIT SLAB AND ITS SHADOW, DITHERED TO PURE BLACK AND WHITE',),
         input='panel', inscale=0.8,
         level=1, power=0.75, spin=0.8, spread=0.5, cyc=1.0, rest=0.25, stepq=12.0, mode=1, refl=0.0, shadow=0.85,
         glow=0.0, vig=0.0, expo=0.9, laz=-35.0, lel=40.0, amb=0.5, keyr=2.4, keyg=2.4, keyb=2.4,
         wAr=1.4, wAg=1.4, wAb=1.4, wBr=1.4, wBg=1.4, wBb=1.4, fAr=1.4, fAg=1.4, fAb=1.4, fBr=1.4, fBg=1.4, fBb=1.4,
         inr=0.02, ing=0.02, inb=0.02, inem=0.0, inmetal=0.0, jolt=0.2,
         dist=3.7, height=0.95, tgty=0.52, tgtx=-0.35, fov=40.0, az=24.0, swing=10.0),
]


def _take_values(i, W, SUBJ):
    """Take i's numbers: DEFAULTS, then the take's own, then the pack's retuning (W['TAKES'])."""
    v = dict(DEFAULTS)
    for k, val in list(TAKES[i].items()) + list(W['TAKES'][TAKES[i]['name']].items()):
        if k == 'input':
            v['insub'] = SUBJ.index(val)
        elif k not in ('name', 'subjects', 'describe', 'label', 'label_in'):
            if k not in DEFAULTS:
                raise KeyError('unknown take parameter ' + k)
            v[k] = val
    return v


def _subjects(W):
    """The subject names in atlas-switch order: the pack's models, its phrases, then the shared ones."""
    return list(W['MODELS']) + list(W['PHRASES']) + SHARED


def _vecs(o, rows):
    """rows: [(name, (x, y, z, w))]; each component a number or an expression string."""
    o.seq.vec.numBlocks = len(rows)
    for i, (name, vals) in enumerate(rows):
        getattr(o.par, 'vec%dname' % i).val = name
        for c, v in zip('xyzw', vals):
            p = getattr(o.par, 'vec%dvalue%s' % (i, c))
            if isinstance(v, str):
                p.expr = v
            else:
                p.val = v


def _shader(scene, name, fname, x, y):
    d = scene.create(td.textDAT, name)
    d.par.file.expr = "mod.paths.here(%r)" % fname
    d.par.syncfile = True
    d.text = open(HERE + '/' + fname, encoding='utf-8').read()
    d.nodeX, d.nodeY = x, y
    return d


def _glsl_top(scene, name, fname, x, y, w, h, fmt='rgba16float'):
    d = _shader(scene, name + '_px', 'shaders/' + fname, x, y - 120)
    g = scene.create(td.glslTOP, name)
    for dock in list(g.docked):
        dock.destroy()
    g.par.pixeldat = d.path
    g.par.outputresolution = 'custom'
    g.par.resolutionw, g.par.resolutionh = w, h
    g.par.format = fmt
    g.nodeX, g.nodeY = x, y
    return g


def _paths(scene):
    """The installed paths module. Not scene_lib's copy: only this one sees the Assets parameter."""
    dat = scene.op('local/modules/paths')
    if 'def model_file' not in dat.text:       # a Text DAT loads its file a frame after it is set
        dat.text = open(REPO + '/experiments/sw_hub/paths_module.py', encoding='utf-8').read()
    return dat.module


def _source(P, cfg):
    """Where a subject's atlas lives under cache/, and what it is baked from.
    Returns (sub-folder, model file or None, stand-in flag). A model that is not in the assets
    folder is TouchDesigner's teapot; a phrase without the font is set in the default face. Those
    stand-in atlases are kept apart in cache/noassets/ so they never replace the real ones."""
    if cfg['kind'] == 'model':
        real = P.have('models/%s/model.obj' % cfg['slug'])
        return ('' if real else NOASSETS + '/'), P.model_file(cfg['slug']), not real
    if cfg['kind'] == 'text':
        return ('' if P.font(FONT) else NOASSETS + '/'), None, not P.font(FONT)
    return '', None, False


def _dump_text(scene, name, cfg, folder):
    """Dump a Text POP's triangles to <folder>/raw_<name>.npy so the bake (here or in system Python) can read them."""
    import numpy as np
    tp = scene.create(td.textPOP, 'tmp_text')
    tp.par.text = cfg['text']
    tp.par.fontfile.expr = "mod.paths.font(%r)" % FONT
    tp.par.alignx = 'center'
    tp.par.aligny = 'center'
    tp.par.linespacing = -0.18
    tp.par.extrude = True
    tp.par.extrudedepth = TEXT_DEPTH
    fc = scene.create(td.facetPOP, 'tmp_facet')
    fc.par.operation = 'unique'
    fc.par.computenormals = False
    tp.outputConnectors[0].connect(fc)
    pt = scene.create(td.poptoTOP, 'tmp_p')
    pt.par.pop = fc.path
    pt.par.rgbamode = 'custom'
    pt.par.extract = 'point'
    pt.par.layout = 'square'
    pt.par.attribscope = 'P'
    pt.cook(force=True)
    nv = fc.numPoints()
    a = np.asarray(pt.numpyArray(), dtype=np.float32)
    flat = a.reshape(-1, a.shape[-1])[:nv, :3].copy()
    ok = nv % 3 == 0 and nv > 0
    if ok:
        np.save(folder + '/raw_' + name + '.npy', flat)
    for o in (pt, fc, tp):
        o.destroy()
    return ok


def _bake_module():
    B = {'__file__': HERE + '/bake.py', '__name__': 'bake'}
    exec(open(HERE + '/bake.py', encoding='utf-8').read(), B)
    return B


def dump_texts():
    """Dump the raw mesh of every text subject that has none yet, inside the existing scene COMP,
    without rebuilding and without baking. Then run `python bake.py <names>` in system Python, so
    the bake (about a second per subject) does not hold up TouchDesigner."""
    scene = op('/project1/' + SLUG)
    B = _bake_module()
    P = _paths(scene)
    table = B['subjects'](P.words(WORDS))
    made = []
    for name, cfg in table.items():
        folder = CACHE + '/' + _source(P, cfg)[0].rstrip('/')
        os.makedirs(folder, exist_ok=True)
        if cfg['kind'] == 'text' and not (os.path.exists(folder + '/raw_' + name + '.npy')
                                          and B['is_current'](name, folder, B['signature'](cfg, None, P.font(FONT)))):
            made.append((name, _dump_text(scene, name, cfg, folder)))
    return made


def _ensure_atlases(scene, W):
    """Make sure every subject has its atlas under cache/ (cache/noassets/ for a stand-in), baked
    from what the pack asks for now (bake.py writes a .sig beside each atlas); bake the missing and
    the outdated ones here. Returns (what was baked, the subject table, {subject: atlas file
    relative to this folder}, {subject: True when it is a stand-in})."""
    os.makedirs(CACHE + '/' + NOASSETS, exist_ok=True)
    gi = HERE + '/cache/.gitignore'
    if not os.path.exists(gi):
        open(gi, 'w').write('*\n')
    B = _bake_module()
    P = _paths(scene)
    table = B['subjects'](W)
    made, files, standin = [], {}, {}
    for name, cfg in table.items():
        sub, model, fallback = _source(P, cfg)
        folder = CACHE + '/' + sub.rstrip('/')
        files[name] = 'cache/' + sub + name + '.npy'
        standin[name] = fallback
        font = P.font(FONT) if cfg['kind'] == 'text' else ''
        if B['is_current'](name, folder, B['signature'](cfg, model, font)):
            continue
        if cfg['kind'] == 'text':
            _dump_text(scene, name, cfg, folder)
        atlas, info = B['bake_subject'](name, cfg, folder, model, fallback, font)
        made.append((name, str(info)))
    return made, table, files, standin


# Triangles each soup draws (the grids in build(): rows-1 x cols-1 quads, two triangles each),
# by the take's `soup` number. A subject with more than that would be drawn with pieces missing.
SOUP_TRIS = {0: 220 * 400 * 2, 1: 72 * 100 * 2, 2: 135 * 200 * 2}


def _check_budgets(W, SUBJ, files):
    """Stop the build when a take's subject (or its Input slab) has more triangles than its soup."""
    import numpy as np
    over = []
    for i, take in enumerate(TAKES):
        vals = _take_values(i, W, SUBJ)
        names = list(W['TAKES'][take['name']]['subjects']) + list(take.get('describe', [])) + [SUBJ[vals['insub']]]
        for name in names:
            tris = int(np.load(HERE + '/' + files[name], mmap_mode='r')[-1, 0, 0]) // 3
            if tris > SOUP_TRIS[int(vals['soup'])]:
                over.append('%s in take %s: %d triangles, the soup draws %d' % (name, take['name'], tris, SOUP_TRIS[int(vals['soup'])]))
    if over:
        raise ValueError('bake these coarser (a lower cap or decimate in WORDS): ' + '; '.join(over))


LOADER = '''# Script TOP callbacks: load one baked fracture atlas (see bake.py) into a float texture.
import numpy as np


def onCook(scriptOp):
    name = scriptOp.name[len('atlas_'):]
    a = np.load(mod.paths.here(scriptOp.parent().fetch('atlas_files')[name]))
    scriptOp.copyNumpyArray(a)
    return
'''


def build():
    LIB = {'op': op}
    exec(open(REPO + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    scene = LIB['new_scene'](SLUG, 2000, -1100)
    P = _paths(scene)
    W = LIB['scene_words'](scene, WORDS)     # the pack's models, phrases and take subjects
    SUBJ = _subjects(W)
    page = scene.customPages[0]
    page.appendToggle('Manual', label='Manual phase (ignore the bar)')[0].val = False
    ph = page.appendFloat('Phase', label='Phase (manual, 0-1)')[0]
    ph.normMin, ph.normMax, ph.val = 0, 1, 0.3
    sb = page.appendInt('Subject', label='Subject (-1 = from take and section)')[0]
    sb.normMin, sb.normMax, sb.val = -1, len(SUBJ) - 1, -1
    made, subjects, files, standin = _ensure_atlases(scene, W)
    _check_budgets(W, SUBJ, files)
    scene.store('atlas_files', files)      # relative to this folder: the loader adds mod.paths.here
    scene.store('baked_now', made)
    scene.store('standins', sorted(n for n in SUBJ if standin[n]))

    H = "op('hub')"
    T = "op('tk')"
    S = "op('shot')"
    C = "op('ctl')"

    # ---- take table: one Constant CHOP per take, a Switch CHOP picks one ----
    names = list(DEFAULTS.keys())
    tk = scene.create(td.switchCHOP, 'tk')
    tk.par.index.expr = "int(%s['take']) %% %d" % (S, len(TAKES))
    tk.nodeX, tk.nodeY = -100, 330
    for i in range(len(TAKES)):
        vals = _take_values(i, W, SUBJ)
        c = scene.create(td.constantCHOP, 'take%d' % i)
        c.seq.const.numBlocks = len(names)
        for j, n in enumerate(names):
            c.par['const%dname' % j] = n
            c.par['const%dvalue' % j] = float(vals[n])
        c.nodeX, c.nodeY = -250, 330 + 110 * (len(TAKES) - i)
        c.outputConnectors[0].connect(tk)

    # ---- Describe and Input switches (their own CHOP, so ctl can read them without a loop) ----
    # Input counts only when it names a TOP outside this scene (never its own out1: a cook loop).
    sw = scene.create(td.constantCHOP, 'modes')
    sw.seq.const.numBlocks = 2
    sw.par.const0name = 'describe'
    sw.par.const0value.expr = "1 if parent().par.Describe else 0"
    sw.par.const1name = 'input'
    sw.par.const1value.expr = ("(lambda o: 1 if (o is not None and o.isTOP and not (o.path + '/').startswith(parent().path + '/')) else 0)"
                               "(op(parent().par.Input.eval().strip()) if parent().par.Input.eval().strip() else None)")
    sw.nodeX, sw.nodeY = -400, 460
    M = "op('modes')"
    # 1 while this take is shattering the Input picture
    useinp = "(1.0 if (float(%s['input']) > 0.5 and float(%s['insub']) >= 0) else 0.0)" % (M, T)

    # ---- derived control channels ----
    own = [W['TAKES'][t['name']]['subjects'] for t in TAKES]
    subj_lists = tuple(tuple(SUBJ.index(s) for s in names_) for names_ in own)
    desc_lists = tuple(tuple(SUBJ.index(s) for s in t.get('describe', names_)) for t, names_ in zip(TAKES, own))
    textured = tuple(0 if subjects[s]['kind'] == 'text' else 1 for s in SUBJ)
    ctl = scene.create(td.constantCHOP, 'ctl')
    ctl.nodeX, ctl.nodeY = 50, 330
    # Input: the slab is flat, so the camera keeps to its front (no orbit, small swing and seed
    # range); otherwise a 360 degree take shows it edge-on as a sliver
    az = ("(lambda u: math.radians(float({T}['az']) + min(float({T}['swing']), 18.0 if u else 1e9)*math.sin(float({H}['evolve'])*0.35 + float({S}['seed'])*6.283)"
          " + (0.0 if u else float({T}['orbit'])*float({H}['evolve'])) + (float({S}['seed'])-0.5)*min(float({T}['azseed']), 50.0 if u else 1e9)))"
          "({useinp} > 0.5)").format(T=T, H=H, S=S, useinp=useinp)
    arr = "max(0.0, 1.0 - float(%s['age'])/0.5)**2" % S
    # a section change swaps the subject: it arrives the same way, a little smaller
    arrs = "max(%s, 0.75*max(0.0, 1.0 - float(%s['section_pos'])/0.07)**2)" % (arr, H)
    dist = "(float({T}['dist'])*(1.0 + 0.22*{arr})*(1.0 - 0.025*float({H}['pulse']) - 0.03*min(float({H}['hit_low']), 1.3)))".format(T=T, H=H, arr=arr)
    laz = "math.radians(float(%s['laz']))" % T
    lel = "math.radians(float(%s['lel']))" % T
    chans = [
        ('subj', ("(int(parent().par.Subject) if parent().par.Subject >= 0 else (int({T}['insub']) if {useinp} > 0.5 else "
                  "(lambda L: L[(int({H}['section']) + int(float({S}['seed'])*97.0)) % len(L)])"
                  "(({dlists} if float({M}['describe']) > 0.5 else {lists})[int({S}['take']) % {n}])))").format(
            H=H, S=S, T=T, M=M, useinp=useinp, lists=repr(subj_lists), dlists=repr(desc_lists), n=len(TAKES))),
        ('q', "(float(parent().par.Phase) if parent().par.Manual else (lambda q, n: (math.floor(q*n)/n if n > 0.5 else q))(min(1.0, ((float({H}['bar_pos'])/float({T}['cyc'])) % 1.0)/max(1e-3, 1.0-float({T}['rest']))), float({T}['stepq'])))".format(H=H, T=T)),
        ('arr', "(0.0 if parent().par.Manual else %s)" % arrs),
        ('jolt', "(0.0 if parent().par.Manual else float(%s['jolt'])*min(float(%s['hit_low']), 1.3))" % (T, H)),
        ('camx', "float({T}['tgtx']) + {dist}*math.sin({az})".format(T=T, dist=dist, az=az)),
        ('camy', "float({T}['height']) + 0.04*float({T}['dist'])*math.sin(float({H}['evolve'])*0.23)".format(T=T, H=H)),
        ('camz', "float({T}['tgtz']) + {dist}*math.cos({az})".format(T=T, dist=dist, az=az)),
        ('lx', "math.cos({el})*math.sin({a})".format(el=lel, a=laz)),
        ('ly', "math.sin(%s)" % lel),
        ('lz', "math.cos({el})*math.cos({a})".format(el=lel, a=laz)),
        ('usetex', "1.0 if int(op('ctl')['subj']) < %d else 0.0" % sum(1 for s in SUBJ if subjects[s]['kind'] == 'model')),
        ('th', "math.tan(math.radians(float(%s['fov']))*0.5)" % T),
        ('hit', "min(float(%s['hit_low']), 1.3)" % H),
        # loud passages burst further (energy only spans about 0.37 to 0.62 on this track)
        ('pw', "float(%s['power'])*(0.72 + 0.5*min(1.0, max(0.0, (float(%s['energy'])-0.33)/0.32)))" % (T, H)),
        ('glowin', "float(%s['inem'])*(1.0 + 0.8*min(float(%s['vocals']), 1.5))" % (T, H)),
    ]
    # usetex reads ctl itself: write the subject expression inline instead (a self-reference loops)
    subj_expr = chans[0][1]
    chans[10] = ('usetex', "float(%r[int(%s)])" % (textured, subj_expr))
    chans.append(('useinp', useinp))
    ctl.seq.const.numBlocks = len(chans)
    for i, (n, e) in enumerate(chans):
        ctl.par['const%dname' % i] = n
        ctl.par['const%dvalue' % i].expr = e

    # ---- atlases and textures ----
    loader = scene.create(td.textDAT, 'load_atlas')
    loader.text = LOADER
    loader.nodeX, loader.nodeY = -1500, 500
    asw = scene.create(td.switchTOP, 'atlas')
    tsw = scene.create(td.switchTOP, 'tex')
    white = scene.create(td.constantTOP, 'white')
    white.par.colorr = white.par.colorg = white.par.colorb = 1
    white.par.outputresolution = 'custom'
    white.par.resolutionw = white.par.resolutionh = 16
    white.nodeX, white.nodeY = -1100, 650
    # Input: the picture that the slab subjects carry. Only read (a Select TOP), and only while a
    # take is using it; blank or unusable falls back to white.
    inp = scene.create(td.selectTOP, 'input_pic')
    inp.par.top.expr = "parent().par.Input.eval().strip() if float(%s['input']) > 0.5 else 'white'" % M
    inp.nodeX, inp.nodeY = -1100, 780
    for i, name in enumerate(SUBJ):
        y = 400 - i * 120
        a = scene.create(td.scriptTOP, 'atlas_' + name)
        for d in list(a.docked):
            d.destroy()
        a.par.callbacks = loader.path
        a.nodeX, a.nodeY = -1300, y
        a.cook(force=True)
        a.outputConnectors[0].connect(asw)
        if subjects[name]['kind'] == 'model':
            slug = subjects[name]['slug']
            if not standin[name] and P.model_texture(slug):
                t = scene.create(td.moviefileinTOP, 'tex_' + name)
                t.par.file.expr = "mod.paths.model_texture(%r)" % slug
            else:
                # no library model (the subject is the teapot) or no picture for it: a flat colour
                t = scene.create(td.constantTOP, 'tex_' + name)
                t.par.colorr, t.par.colorg, t.par.colorb = W['MODELS'][name]['standin']
                t.par.outputresolution = 'custom'
                t.par.resolutionw = t.par.resolutionh = 16
            t.nodeX, t.nodeY = -1100, y
            t.cook(force=True)
            t.outputConnectors[0].connect(tsw)
        elif subjects[name]['kind'] == 'panel':
            inp.outputConnectors[0].connect(tsw)
        else:
            white.outputConnectors[0].connect(tsw)
    asw.par.index.expr = "int(%s['subj'])" % C
    tsw.par.index.expr = "int(%s['subj'])" % C
    asw.nodeX, asw.nodeY = -900, 400
    tsw.nodeX, tsw.nodeY = -900, 250

    # ---- material ----
    vert = _shader(scene, 'shard_vert', 'shaders/shard.vert', -700, -250)
    frag = _shader(scene, 'shard_frag', 'shaders/shard.frag', -700, -370)
    mat = scene.create(td.glslMAT, 'mat')
    for d in list(mat.docked):
        d.destroy()
    mat.par.vdat = vert.path
    mat.par.pdat = frag.path
    mat.par.cullface = 'neither'
    mat.seq.sampler.numBlocks = 2
    mat.par.sampler0name = 'sAtlas'
    mat.par.sampler0top = asw.path
    mat.par.sampler0filter = 'nearest'
    mat.par.sampler1name = 'sTex'
    mat.par.sampler1top = tsw.path
    mat.par.sampler1filter = 'mipmap'

    def t(n):
        return "%s['%s']" % (T, n)

    def c(n):
        return "%s['%s']" % (C, n)
    _vecs(mat, [
        ('uBurst', (c('q'), c('pw'), t('spin'), t('level'))),
        ('uShape', (t('d0'), t('d1'), t('gravity'), t('swirl'))),
        ('uAudio', (c('jolt'), "%s['evolve']" % H, "%s*float(%s)" % (c('arr'), t('arrp')), t('spread'))),
        ('uGrid', (t('nx'), t('nz'), t('sx'), t('sz'))),
        ('uWave', (t('wave'), t('wavedir'), "%s['seed']" % S, t('yawjit'))),
        ('uLight', (c('lx'), c('ly'), c('lz'), "1.0 if %s > 0.01 else 0.0" % t('refl'))),
        ('uSlab', ("math.cos(float(%s))" % t('slabdir'), 0.0, "math.sin(float(%s))" % t('slabdir'), 10.0)),
        ('uOrder', (t('omode'), "0.5 + 0.4*math.sin(float(%s['seed'])*40.0)" % S, "0.55 + 0.35*math.sin(float(%s['seed'])*71.0)" % S, 1.0)),
        ('uXform', ("float(%s)*(float(%s) if %s > 0.5 else 1.0)" % (t('oscale'), t('inscale'), c('useinp')),
                    "float(%s) + (float(%s) if %s > 0.5 else 0.0)" % (t('oyaw'), t('inyaw'), c('useinp')),
                    t('drift'), t('fclamp'))),
        ('uMode', (t('lay'), t('kgap'), t('skinmetal'), t('glass'))),
        ('uKey', (t('keyr'), t('keyg'), t('keyb'), t('amb'))),
        ('uInner', (t('inr'), t('ing'), t('inb'), c('glowin'))),
        ('uTint', (t('tr'), t('tg'), t('tb'), c('usetex'))),
        ('uLook', (t('rough'), t('envs'), t('unlit'), t('refl'))),
        ('uHits', (c('hit'), "min(float(%s['hit_high']), 1.2)" % H, "%s['pulse']" % H, t('inmetal'))),
        ('uEnv', (t('envr'), t('envg'), t('envb'), t('burstglow'))),
        ('uInput', (c('useinp'), 0.0, 0.0, 0.0)),
    ])
    # glass takes: additive, no depth
    mat.par.blending.expr = "%s > 0.5" % t('glass')
    mat.par.srcblend, mat.par.destblend = 'one', 'one'
    mat.par.depthtest.expr = "%s < 0.5" % t('glass')
    mat.par.depthwriting.expr = "%s < 0.5" % t('glass')
    mat.nodeX, mat.nodeY = -500, -250

    # ---- the triangle soups: the shader moves every corner, the grid only supplies vertex ids ----
    geos = []
    for name, rows, cols, flag in (('big', 221, 401, '< 0.5'), ('small', 73, 101, '== 1.0'), ('mid', 136, 201, '== 2.0')):
        geo = scene.create(td.geometryCOMP, name)
        for ch in geo.children:
            ch.destroy()
        grid = geo.create(td.gridPOP, 'grid')
        grid.par.surftype = 'triangles'
        grid.par.rows, grid.par.cols = rows, cols
        soup = geo.create(td.facetPOP, 'soup')
        soup.par.operation = 'unique'
        soup.par.computenormals = False
        grid.outputConnectors[0].connect(soup)
        soup.render = True
        soup.display = True
        geo.par.material = mat.path
        geo.par.instancing = True
        geo.par.instancecountmode = 'manual'
        geo.par.numinstances.expr = "2*int(%s)*int(%s)" % (t('nx'), t('nz'))
        geo.par.render.expr = "float(%s) %s" % (t('soup'), flag)
        geo.nodeX, geo.nodeY = -300, -100 - 130 * len(geos)
        geos.append(geo)

    # ---- camera, render ----
    target = scene.create(td.nullCOMP, 'target')
    target.par.tx.expr, target.par.ty.expr, target.par.tz.expr = t('tgtx'), t('tgty'), t('tgtz')
    target.nodeX, target.nodeY = -300, 150
    cam = scene.create(td.cameraCOMP, 'cam')
    cam.par.tx.expr, cam.par.ty.expr, cam.par.tz.expr = c('camx'), c('camy'), c('camz')
    cam.par.lookat = target.path
    cam.par.fov.expr = t('fov')
    cam.par.near, cam.par.far = 0.03, 120
    cam.nodeX, cam.nodeY = -150, 150
    render = scene.create(td.renderTOP, 'render')
    render.par.camera = cam.path
    render.par.geometry = 'big small mid'
    render.par.lights = ''
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.par.format = 'rgba16float'
    render.par.bgcolorr = render.par.bgcolorg = render.par.bgcolorb = render.par.bgcolora = 0
    render.nodeX, render.nodeY = 0, 0

    # ---- shadow map: the same geometry, flattened along the light onto the floor, seen from above ----
    scam = scene.create(td.cameraCOMP, 'shadow_cam')
    scam.par.projection = 'ortho'
    scam.par.orthowidth.expr = "2.0*float(%s)" % t('shR')
    scam.par.tx, scam.par.ty, scam.par.tz = 0, 30, 0     # a new Camera COMP sits at z = 5
    scam.par.rx = -90
    scam.par.near, scam.par.far = 0.1, 100
    scam.nodeX, scam.nodeY = -150, -400
    srender = scene.create(td.renderTOP, 'shadow')
    srender.par.camera = scam.path
    srender.par.geometry = 'big small mid'
    srender.par.lights = ''
    srender.par.outputresolution = 'custom'
    srender.par.resolutionw, srender.par.resolutionh = 768, 768
    srender.par.format = 'rgba8fixed'
    srender.par.bgcolorr = srender.par.bgcolorg = srender.par.bgcolorb = srender.par.bgcolora = 0
    srender.nodeX, srender.nodeY = 0, -400
    sblur = scene.create(td.blurTOP, 'shadow_blur')
    sblur.par.size.expr = t('shblur')
    srender.outputConnectors[0].connect(sblur)
    sblur.nodeX, sblur.nodeY = 150, -400

    # ---- backdrop + composite ----
    comp = _glsl_top(scene, 'comp', 'comp.frag', 350, 0, 1280, 720)
    render.outputConnectors[0].connect(comp.inputConnectors[0])
    sblur.outputConnectors[0].connect(comp.inputConnectors[1])
    _vecs(comp, [
        ('uCamPos', (c('camx'), c('camy'), c('camz'), c('th'))),
        ('uCamTgt', (t('tgtx'), t('tgty'), t('tgtz'), 0.0)),
        ('uFloorA', (t('fAr'), t('fAg'), t('fAb'), t('poolr'))),
        ('uFloorB', (t('fBr'), t('fBg'), t('fBb'), t('shadow'))),
        ('uWallA', (t('wAr'), t('wAg'), t('wAb'), t('pattern'))),
        ('uWallB', (t('wBr'), t('wBg'), t('wBb'), t('shR'))),
        ('uFx', ("%s['pulse']" % H, c('hit'), "%s['evolve']" % H, t('tgtx'))),
    ])

    # ---- glow and grade ----
    bright = _glsl_top(scene, 'bright', 'bright.frag', 550, -250, 320, 180)
    comp.outputConnectors[0].connect(bright.inputConnectors[0])
    _vecs(bright, [('uThr', (1.0, 0, 0, 0))])
    glow = scene.create(td.blurTOP, 'glow')
    glow.par.size = 9
    bright.outputConnectors[0].connect(glow)
    glow.nodeX, glow.nodeY = 700, -250
    post = _glsl_top(scene, 'post', 'post.frag', 900, 0, 1280, 720, 'rgba8fixed')
    comp.outputConnectors[0].connect(post.inputConnectors[0])
    glow.outputConnectors[0].connect(post.inputConnectors[1])
    # ---- Describe caption: one small strip per take, drawn once at build time; a Switch TOP hands
    # post.frag the current take's strip only while Describe is on (otherwise a 16 px blank) ----
    blank = scene.create(td.constantTOP, 'label_off')
    blank.par.colorr = blank.par.colorg = blank.par.colorb = blank.par.alpha = 0
    blank.par.outputresolution = 'custom'
    blank.par.resolutionw = blank.par.resolutionh = 16
    blank.nodeX, blank.nodeY = 550, -520
    lsw = scene.create(td.switchTOP, 'label')
    blank.outputConnectors[0].connect(lsw)
    widths = []
    # the first set describes the take's own subject, the second the take shattering an Input picture
    # (label_in gives a new first line and, optionally, a new second line)
    lines = [(W['LABELS'].get(r['name']) or r['label'][0], r['label'][1]) for r in TAKES]
    lines += [(r['label_in'][0], r['label_in'][1] if len(r['label_in']) > 1 else r['label'][1]) for r in TAKES]
    scene.store('label_lines', lines)
    for i, pair in enumerate(lines):
        lt = scene.create(td.textTOP, 'label%d' % i)
        lt.par.text = '\n'.join(pair)
        lt.par.fontfile.expr = "mod.paths.font(%r)" % LABEL_FONT
        lt.par.fontsizex = LABEL_PX
        lt.par.fontsizexunit = 'pixels'
        lt.par.linespacing = 6
        lt.par.linespacingunit = 'pixels'
        lt.par.alignx, lt.par.aligny = 'left', 'center'
        lt.par.wordwrap = False
        lt.par.fontcolorr = lt.par.fontcolorg = lt.par.fontcolorb = lt.par.fontalpha = 1
        lt.par.bgalpha = 0
        lt.par.outputresolution = 'custom'
        lt.par.resolutionw, lt.par.resolutionh = LABEL_W, LABEL_H
        lt.nodeX, lt.nodeY = 400 - 200 * (i // len(TAKES)), -640 - 110 * (i % len(TAKES))
        lt.cook(force=True)
        wpx = max(float(lt.evalTextSize(line)[0]) for line in pair)
        if wpx > LABEL_W - 4 and not P.font(LABEL_FONT):
            # the default face is wider than Barlow Condensed: shrink the caption until it fits
            lt.par.fontsizex = math.floor(LABEL_PX * (LABEL_W - 8) / wpx)
            lt.cook(force=True)
            wpx = min(max(float(lt.evalTextSize(line)[0]) for line in pair), LABEL_W - 4)
        if wpx > LABEL_W - 4:
            raise ValueError('Describe caption of take %d is %d px wide: shorten it' % (i, wpx))
        widths.append(int(round(wpx)))
        lt.outputConnectors[0].connect(lsw)
    lidx = "(int(%s['take']) %% %d + (%d if %s > 0.5 else 0))" % (S, len(TAKES), len(TAKES), c('useinp'))
    lsw.par.index.expr = "(1 + %s) if float(%s['describe']) > 0.5 else 0" % (lidx, M)
    lsw.nodeX, lsw.nodeY = 700, -520
    lsw.outputConnectors[0].connect(post.inputConnectors[2])
    scene.store('label_widths', widths)
    _vecs(post, [
        ('uPost', (t('expo'), t('glow'), t('vig'), t('mode'))),
        ('uBeat', (c('hit'), "%s['pulse']" % H, "%s['t']" % H, t('sat'))),
        # x Describe on, y caption width in pixels (measured above), zw strip size in pixels
        ('uDesc', ("%s['describe']" % M, "%r[%s]" % (tuple(widths), lidx),
                   float(LABEL_W), float(LABEL_H))),
    ])
    post.outputConnectors[0].connect(scene.op('out1'))
    return scene.path
