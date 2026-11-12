# Builder for /project1/sc_paper_storm. Run inside TouchDesigner (see SCENE_BRIEF.md).
# Idempotent: destroys and rebuilds the whole scene.
import math
import td

SLUG = 'sc_paper_storm'
# Where files are: nothing here names a folder. Every parameter that names a file is an
# expression on the scene's paths module (local/modules/paths, installed by the scaffold),
# so the saved .tox and the snapshot hold the expression. See NOTES.md, "Assets".
CHICAGO = "mod.paths.font('chicago')"      # '' (TouchDesigner's default face) when there are no assets
BARLOW = "mod.paths.font('barlow')"
WHITE = "mod.paths.here('data/white.png')"  # an 8 px white image: what a Movie File In reads when its picture is missing


def here(rel):
    return "mod.paths.here(%r)" % rel


def texfile(slug):
    return "mod.paths.model_texture(%r) or %s" % (slug, WHITE)


def have_tex(slug):
    return "bool(mod.paths.model_texture(%r))" % slug


# The library models are centred on the origin with their longest side 1 unit. The teapot
# that stands in for a missing model is 1.964 wide and sits on y = 0: FIT is the scale and
# the offset that bring it to the same convention.
FIT_S, FIT_T = 0.509, (0.0071, -0.2331, 0.0)
NL = chr(10)

INK = (0.030, 0.052, 0.066)

# ---- TAKES --------------------------------------------------------------------------------
# One row per take; the cutter's Take parameter picks a row (take % len(TAKES)) and every
# number below reaches the network through the 'tk' CHOP. Anything not given comes from DEF.
# form: which formation field.frag computes (0 tunnel, 1 dome, 2 floor, 3 galaxy, 4 rain,
#       5 flock, 6 prop rings, 7 board).
DEF = dict(
    form=0, cam=(0.0, 0.0, 14.0), aim=(0.0, 0.0, 0.0), fov=78.0,
    sway=1.0,        # camera drift with 'evolve' (0 = locked off)
    dolly=0.25,      # the camera starts this much further out and settles in the first half second
    mirror=0,        # 1: the seed may mirror the camera left-right
    yvar=0.0,        # seed adds up to this to the camera height
    zvar=0.0,        # seed brings the camera up to this fraction closer
    zvard=None,      # the same in Describe mode or with an Input (None = zvar): the board must keep all three
                     # lines, or the whole picture, in frame
    haze=INK, fog=0.035,
    bgk=0.5,         # the camera's Fog Alpha. With the Render TOP's background alpha at 0 (needed: alpha carries
                     # depth) the background you see is fog colour x fog alpha, not the Render TOP's bgcolor
    key=2.6, keyend=46.0, spot=1.0, amb=(0.26, 0.42, 0.60, 0.3),
    skyl=0.0, bouncel=0.0,   # two distant lights, from above and from below, for the daylight takes
    sheets=1, props=1, mono=1, hero=0, idol=0,
    back=0,          # reverse of the sheets: 0 red with the two-line mark (WORDMARK), 1 plain backcol, 2 one of BACK_PHRASES picked by seed
    backcol=(0.86, 0.20, 0.13), backemit=0.55,
    backin=0,        # 1: with an Input picture the reverse carries it as a two-colour print in backcol
    tint=(1.0, 1.0, 1.0),   # multiplies every sheet
    flip=1.0,        # the beat's travelling flip wave
    ring=1.0,        # kick shockwave radius scale (0 = none)
    keepout=2.8,     # nothing comes closer to the lens than this
    glow=1.0, vig=0.7, sat=1.3, dither=0, shadow=(0.74, 0.96, 1.22), sky=0.0,
    bloom=0.35, focus=None, dof0=7.0, dof1=24.0, dofnear=3.6, blur=9.0,
)
TAKES = [
    # 0 TUNNEL: the first cut's picture. Flight down a tube of printed sheets to the monolith, red lettered reverses.
    dict(name='tunnel', form=0, backin=1),
    # 1 BOARD: square-on wall of 96 x 64 sheets; the turned ones spell a page of PAGES, a new page every two beats.
    dict(name='board', form=7, cam=(0.0, 0.0, 166.0), fov=34.0, sway=0.0, dolly=0.12, zvar=0.42,
         haze=(0.016, 0.040, 0.075), fog=0.0, key=3.0, keyend=900.0, spot=0.0, amb=(0.5, 0.6, 0.8, 0.45),
         props=0, mono=0, back=1, backcol=(0.90, 0.68, 0.14), backemit=0.75, flip=0.0, ring=1.5, zvard=0.2,
         glow=0.0, vig=0.45, sat=1.25, bloom=0.22, dof0=400.0, dof1=800.0, dofnear=0.0),
    # 2 MURMURATION: ink silhouettes folding in a pale sky, the monolith tiny on the bottom edge.
    dict(name='murmuration', form=5, cam=(0.0, 1.0, 42.0), aim=(5.0, 10.0, 0.0), fov=64.0, sway=0.6, dolly=0.1,
         mirror=1, haze=(1.20, 1.08, 0.84), bgk=1.0, fog=0.004, key=0.0, spot=0.0, amb=(1.0, 1.0, 1.0, 0.6),
         props=0, back=1, backcol=(0.03, 0.04, 0.06), backemit=0.0, tint=(0.05, 0.07, 0.10), flip=0.0, ring=0.0,
         keepout=0.0, glow=0.0, vig=0.3, sat=1.0, shadow=(1.0, 1.0, 1.0), sky=1.0, bloom=0.0,
         dof0=400.0, dof1=800.0, dofnear=0.0),
    # 3 RITUAL: no paper. Rings of the four PROPS (hoppers, dominoes, an inner eight, an outer eight) round the IDOL, on red.
    dict(name='ritual', form=6, cam=(3.4, 1.5, 9.4), aim=(-1.0, 0.6, 0.0), fov=50.0, sway=0.5, dolly=0.3,
         mirror=1, yvar=4.5, haze=(0.42, 0.045, 0.03), fog=0.02, key=2.2, keyend=40.0, spot=1.6,
         amb=(1.0, 0.75, 0.6, 0.45), sheets=0, mono=0, idol=1, flip=0.0, ring=0.0, keepout=0.0,
         glow=0.25, vig=0.55, sat=1.25, shadow=(1.1, 0.75, 0.7), bloom=0.3,
         focus=7.0, dof0=2.5, dof1=9.0, dofnear=4.2, blur=12.0),
    # 4 RAIN: locked camera in a sick-green fluorescent haze; sheets fall past in steps, near ones soft.
    dict(name='rain', form=4, cam=(0.0, 0.0, 12.0), aim=(-4.2, 0.0, 0.0), fov=70.0, sway=0.0, dolly=0.0,
         mirror=1, haze=(0.92, 1.08, 0.72), bgk=1.0, fog=0.03, key=2.2, keyend=40.0, spot=0.0, amb=(0.9, 1.0, 0.8, 0.9),
         skyl=1.1, bouncel=0.75, backin=1,
         props=0, back=1, backcol=(0.80, 0.82, 0.74), backemit=0.0, flip=0.0, ring=0.0, keepout=1.3,
         glow=0.0, vig=0.35, sat=1.1, shadow=(0.80, 1.05, 0.78), sky=0.6, bloom=0.0,
         focus=9.0, dof0=5.0, dof1=18.0, dofnear=5.5, blur=18.0),
    # 5 FLOOR: straight down on a tidy floor of sheets in 1-bit dither; height rings leave on the beat.
    dict(name='floor', form=2, cam=(0.0, 12.0, 0.6), fov=78.0, sway=0.0, dolly=0.15, zvar=0.4,
         haze=(0.0, 0.0, 0.0), fog=0.0, key=1.2, keyend=60.0, spot=1.5, amb=(1.0, 1.0, 1.0, 0.25),
         props=0, mono=0, back=1, backcol=(0.0, 0.0, 0.0), backemit=0.0, keepout=0.0, ring=0.6, flip=0.0,
         glow=0.0, vig=0.5, sat=1.0, dither=1, shadow=(1.0, 1.0, 1.0), bloom=0.0,
         dof0=400.0, dof1=800.0, dofnear=0.0),
    # 6 ONE SHEET: a single sheet turning close to the lens, sharp; the whole galaxy a blur far behind it.
    dict(name='one_sheet', form=3, cam=(0.0, 3.2, 15.0), sway=0.5, dolly=0.1, mirror=1,
         haze=(0.035, 0.03, 0.075), hero=1, backin=1, key=2.2, spot=1.3, amb=(0.4, 0.35, 0.7, 0.35),
         glow=1.4, vig=0.75, sat=1.35, shadow=(0.85, 0.80, 1.30), bloom=0.4,
         focus=3.6, dof0=1.5, dof1=7.0, dofnear=0.0, blur=22.0),
    # 7 OCULUS: inside the dome looking up; counter-turning rings of paper, phrases on blue reverses.
    dict(name='oculus', form=1, cam=(-2.4, -6.5, 3.2), aim=(3.4, 6.0, -1.0), fov=104.0, sway=0.6, dolly=0.2, mirror=1,
         haze=(0.012, 0.05, 0.065), fog=0.02, key=2.9, keyend=40.0, spot=0.0, amb=(0.3, 0.6, 0.7, 0.3),
         props=0, mono=0, back=2, backin=1, backcol=(0.16, 0.49, 0.61), backemit=0.6,
         glow=1.2, vig=0.6, sat=1.3, shadow=(0.70, 1.00, 1.15), bloom=0.3, dof0=5.0, dof1=14.0, dofnear=0.0),
]
NT = len(TAKES)

# ---- WORDS AND SHAPES ----------------------------------------------------------------------
# Everything the scene shows that is content, not technique: the words, which models, and how
# each model is sized and turned. build() reads it through LIB['scene_words'], so an asset pack
# may replace any of these names with its own scenes/sc_paper_storm/words.json (see NOTES.md,
# "Words and shapes"). Describe mode's own words (further down) are not part of it.
PAPER_W, PAPER_P = [0.965, 0.957, 0.933], [0.94, 0.71, 0.77]
INK_K, INK_R = [0.10, 0.10, 0.12], [0.58, 0.09, 0.17]
DEFAULTS = {
    # the two lines on the red reverses of the takes with back=0 (a 512 x 396 px picture)
    "WORDMARK": "REAL\nTIME",
    "WORDMARK_PX": 96.0,       # its type size (Text TOP points), to suit the face and the length of the lines
    # the board's pages: three lines each, 96 x 48 px in the 12 px face. At most 11 characters a
    # line here (7.2 px each), so a line stays in frame at the closest crop (BOARD_CROP). Eight
    # at most: the Layout TOP laid out only the first eight of twelve (2026-11-10)
    "PAGES": [
        ["HERE.", "NOW.", "HERE. NOW."],
        ["DO NOT", "TOUCH", "PLATE 07"],
        ["NOTHING", "IS", "PRERENDERED"],
        ["SOUND IN.", "PICTURE", "OUT."],
        ["ORIGIN:", "NOT", "RECORDED."],
        ["EVERY FRAME", "IS MADE", "NOW."],
        ["LISTEN", "WITH", "YOUR EYES."],
        ["PAST.", "PRESENT.", "LATER."],
    ],
    # the board: the most the seed may crop in (0 = never, 0.42 = to 56 of the 96 columns), so the
    # three lines of a page stay in frame in this pack's face (its line spacing is the limit: at
    # 0.26 the top and bottom lines were cut)
    "BOARD_CROP": 0.16,
    # Describe mode on the board: the most the seed may crop in (0 = never), so the widest line of
    # PAGES_D (12 characters) stays in frame in this pack's face
    "BOARD_CROP_D": 0.08,
    # the reverse of the sheets in takes with back=2 (the seed picks one)
    "BACK_PHRASES": ["NOW.", "DO NOT\nTOUCH", "SOUND\nIN.", "PLATE\n07", "NOT\nMADE", "LOOP"],
    "BACK_PHRASE_PX": 90.0,    # their type size (Text TOP points); a line too wide for the sheet is shrunk to fit
    # Describe mode's caption for the ritual take: it names the props, so it belongs to the pack
    "RITUAL_LABEL": ["INSTANCING: 196 OBJECTS, EACH ONE PLACED BY A SHADER.",
                     "DUCKS HOP IN A WAVE ON THE BEAT. A KICK DRUM THROWS THE KEYS."],
    # The three printed sheets: 'model' is the flat sheet whose picture is printed on the paper.
    # The rest is the stand-in drawn with Text TOPs when that picture is not in the assets folder.
    "FORMS": [
        {"model": "blueprint", "paper": PAPER_W, "ink": INK_K,
         "top": "CATALOGUE OF UNEXPLAINED OBJECTS", "title": "PLATE 07", "sub": "OBJECT OF UNKNOWN USE, PART 1",
         "rows": [["NAME", ""], ["ORIGIN", ""], ["DATE", ""], ["USE", ""]],
         "foot": "FOUND, NOT MADE.   DO NOT TOUCH"},
        {"model": "star_chart", "paper": PAPER_W, "ink": INK_K,
         "top": "REGISTER OF REAL-TIME PICTURES", "title": "SIGNAL IN", "sub": "SOUND IN. PICTURE OUT. NOTHING KEPT.",
         "rows": [["NAME", ""], ["SIGNAL", "....... OPEN"], ["ON TAPE", "NOTHING"], ["FRAMES", "ARE MADE NOW"]],
         "foot": "NOTHING IS PRERENDERED."},
        {"model": "ticket", "paper": PAPER_P, "ink": INK_R,
         "top": "PAST. PRESENT. LATER.", "title": "EXHIBIT B", "sub": "OBJECT OF UNKNOWN USE",
         "rows": [["ORIGIN", "UNRECORDED, POSSIBLY LATER"], ["NUMBER", "CATALOGUE 0047"],
                  ["NOTE", "HANDLE WITH BOTH HANDS."], ["WHEN", "EVERY FRAME IS MADE NOW."]],
         "foot": "DO NOT TOUCH THE EXHIBITS."},
    ],
    # The instanced props, in the order field.frag knows them (uSeed 10 + row): 0 hops in two
    # rings, 1 is the ring of dominoes, 2 is the inner eight that jab at the idol, 3 the outer
    # eight. w x h = how many. scale also scales the ring's radius (the Geometry COMP's scale
    # comes after the instance positions). rot turns the mesh before it is placed: an instance's
    # +Z points along the shader's facing vector, +Y along its up vector. teapot = the colour of
    # the stand-in when the model is missing. Mind the triangles: w x h x the model's count.
    "PROPS": [
        {"model": "rubber_duck", "w": 10, "h": 4, "scale": 0.45, "rot": [0, 0, 0], "teapot": [0.95, 0.80, 0.20]},
        {"model": "skeleton_key", "w": 14, "h": 10, "scale": 0.5, "rot": [90, 0, 90], "teapot": [0.70, 0.55, 0.25]},
        {"model": "traffic_cone", "w": 4, "h": 2, "scale": 0.6, "rot": [-90, 0, 0], "teapot": [0.90, 0.40, 0.15]},
        {"model": "amphora", "w": 4, "h": 2, "scale": 0.8, "rot": [0, 0, 0], "teapot": [0.70, 0.35, 0.20]},
    ],
    # the one large object in the middle of the paper takes
    "MONOLITH": {"model": "marble_bust", "scale": 5.0, "ry": 24.0, "ty": 0.0, "teapot": [0.78, 0.75, 0.65]},
    # what the prop rings turn round (ritual take only)
    "IDOL": {"model": "lander", "scale": 2.2, "ty": 1.0, "ry": 0.0, "rough": 0.35, "emit": [0.10, 0.07, 0.02],
             "teapot": [0.95, 0.66, 0.20]},
}

# ---- DESCRIBE MODE --------------------------------------------------------------------------
# When the COMP's Describe toggle is on, every word on screen says what the viewer is looking
# at. Everything below is built beside its everyday twin and a Switch TOP picks between them, so
# the toggle needs no rebuild. DESCRIBE[i] belongs to TAKES[i]; keys:
#   back    the two lines on the red reverses (takes with back=0)
#   pages   the board's pages (same limits as DEFAULTS['PAGES'])
#   phrases the reverses of takes with back=2 (the seed picks one)
#   hero    the one large sheet of the one_form take (a key of DFORMS)
#   forms   True: the take shows the printed side of the sheets close enough to read, so the
#           three explaining sheets in DFORMS count as its words
#   label   two caption lines along the bottom edge, for takes with no readable text of their own
#   label_key  the same, but the two lines are a name in DEFAULTS (the caption names the pack's props)
#   label_input  the caption while an Input picture is in use (then the printed sides carry the
#           picture instead of words); without one, the take's 'label' stays
# Every statement was checked against this file and shaders/field.frag on 2026-11-11.
# sync_preset.py mirrors these into preset.json ("words") and fails if they drift apart.
PAGES_D = [
    ('INSTANCING', '6144', 'SHEETS'),
    ('EVERY SHEET', 'IS A PIXEL', 'OF THIS TEXT'),
    ('ONE SHADER', 'PLACES', 'THEM ALL'),
    ('LIT PIXEL =', 'SHEET', 'TURNS OVER'),
    ('NEW PAGE', 'EVERY', '2 BEATS'),
    ('KICK DRUM', 'SENDS', 'A RING OUT'),
    ('HI-HATS', 'RATTLE', 'LOOSE SHEETS'),
    ('96 SHEETS', 'ACROSS', '64 DOWN'),
]
BACK_PHRASES_D = ['6144' + NL + 'SHEETS', 'FLIP ON' + NL + 'BEAT', 'ONE' + NL + 'SHADER',
                  'PAPER' + NL + 'COPIES', 'RINGS' + NL + 'TURN', 'KICK' + NL + 'WIDENS']
DESCRIBE = [
    dict(back=('6144', 'COPIES'), forms=True,                                    # 0 tunnel
         label=('INSTANCING: 6144 COPIES OF ONE PAPER SHEET, EACH PLACED BY A SHADER.',
                'THE BAR TURNS THE TUNNEL. THE BEAT FLIPS A RING OF SHEETS TO RED.'),
         label_input=('INSTANCING: THE INPUT PICTURE, PRINTED ON 6144 PAPER SHEETS.',
                      'A SHADER FLIES THEM PAST AS A TUNNEL. THE BEAT FLIPS A RING OF THEM.')),
    dict(pages=PAGES_D,                                                          # 1 board
         label_input=('INSTANCING: A WALL OF 96 X 64 PAPER SHEETS SHOWS THE INPUT PICTURE.',
                      'A SHEET TURNS TO ITS YELLOW BACK WHERE THE PICTURE IS BRIGHT.')),
    dict(label=('INSTANCING: 6144 PAPER SHEETS, EACH ONE PLACED BY A SHADER.',   # 2 murmuration
                'THREE SINE WAVES FOLD THE FLOCK. BASS DEEPENS THE FOLDS.')),
    dict(label_key='RITUAL_LABEL'),                                              # 3 ritual
    dict(forms=True,                                                             # 4 rain
         label=('INSTANCING: 6144 PAPER SHEETS, EACH ONE PLACED BY A SHADER.',
                'THEY FALL ONE STEP PER BEAT. NEAR SHEETS GO OUT OF FOCUS.'),
         label_input=('INSTANCING: THE INPUT PICTURE, PRINTED ON 6144 PAPER SHEETS.',
                      'THEY FALL ONE STEP PER BEAT. NEAR SHEETS GO OUT OF FOCUS.')),
    dict(label=('INSTANCING: A FLOOR OF 6144 SHEETS, DRAWN IN 1-BIT DITHER.',    # 5 floor
                'EVERY 2 BEATS A RING OF SHEETS TURNS OVER TO BLACK.'),
         label_input=('INSTANCING: THE INPUT PICTURE ON A FLOOR OF 6144 SHEETS, IN 1-BIT.',
                      'EVERY 2 BEATS A RING OF SHEETS TURNS OVER TO BLACK.')),
    dict(back=('6144', 'COPIES'), hero='hero',                                   # 6 one_sheet
         label_input=('INSTANCING: THE INPUT PICTURE, PRINTED ON ONE LARGE SHEET.',
                      'THE BLUR BEHIND IT IS 6144 MORE PRINTS. A KICK DRUM TIPS THE SHEET.')),
    dict(phrases=BACK_PHRASES_D, forms=True,                                     # 7 oculus
         label=('INSTANCING: 6144 COPIES OF ONE PAPER SHEET, EACH PLACED BY A SHADER.',
                'RINGS OF PAPER TURN WITH THE BAR. THE BEAT FLIPS A RING TO BLUE.'),
         label_input=('INSTANCING: THE INPUT PICTURE, PRINTED ON 6144 PAPER SHEETS.',
                      'RINGS OF THEM TURN WITH THE BAR. THE BEAT FLIPS A RING OF THEM.')),
]
# label colours per take: (text, band); the band's opacity is LABEL_A
LABEL_COL = {1: ((0.96, 0.90, 0.78), (0.016, 0.040, 0.075)), 2: ((0.05, 0.07, 0.10), (0.93, 0.88, 0.74)),
             3: ((0.96, 0.90, 0.78), (0.20, 0.02, 0.015)), 4: ((0.06, 0.09, 0.05), (0.84, 0.90, 0.72)),
             5: ((1.0, 1.0, 1.0), (0.0, 0.0, 0.0))}
LABEL_A = {5: 1.0}      # band opacity; 0.86 unless given (the 1-bit take stays 1-bit)
# The explaining sheets. In Describe mode the three printed sheets become 'a', 'b', 'c' (white,
# white and pink paper) and the one_sheet take hangs 'hero' in front of the lens. Layout units are
# pixels of a 512 px square, y from the top; the sheet is 1.29 times wider than tall, so the
# condensed type stretches back to a normal width.
DFORMS = {
    'a': dict(paper=PAPER_W, ink=INK_K, top='HOW THIS PICTURE IS MADE   1 OF 3', title='INSTANCING',
              sub='ONE SHEET OF PAPER, 6144 COPIES',
              rows=(('MODEL', 'one flat sheet, 2 triangles'), ('COPIES', '6144, all drawn at once'),
                    ('PLACED BY', 'one shader, every frame'), ('PRINT', '3 sheets like this, mixed')),
              foot='TOUCHDESIGNER   GEOMETRY COMP INSTANCING'),
    'b': dict(paper=PAPER_W, ink=INK_K, top='HOW THIS PICTURE IS MADE   2 OF 3', title='ONE SHADER',
              sub='DECIDES WHERE EVERY SHEET GOES',
              rows=(('OUTPUT', 'a 64 x 96 pixel texture'), ('1 PIXEL', '= 1 sheet of paper'),
                    ('ITS COLOUR', '= the position x, y, z'), ('ALSO', 'facing, up and tint')),
              foot='TOUCHDESIGNER   GLSL TOP TO INSTANCES'),
    'c': dict(paper=PAPER_P, ink=INK_R, top='HOW THIS PICTURE IS MADE   3 OF 3', title='ON THE BEAT',
              sub='THE MUSIC MOVES THE PAPER',
              rows=(('BEAT', 'sheets flip or step'), ('KICK DRUM', 'sheets are thrown'),
                    ('EACH SHOT', 'a new variation'), ('SENT AS', 'a small texture')),
              foot='TOUCHDESIGNER   AUDIO VALUES TO THE SHADER'),
    'hero': dict(paper=PAPER_W, ink=INK_K, top='HOW THIS PICTURE IS MADE', title='INSTANCING',
                 sub='ONE SHEET OF PAPER, 6144 COPIES',
                 body=('This sheet is one flat model: two triangles.',
                       'The blur behind it is 6144 copies of the model,',
                       'arranged in a spiral by one shader. The shader',
                       'writes one pixel per copy: its position and',
                       'which way it faces. The bar turns the spiral.',
                       'Each kick drum tips this sheet back.'),
                 foot='TOUCHDESIGNER   GEOMETRY COMP INSTANCING FROM A GLSL TOP'),
}
# Barlow Condensed is narrow; the default face is not. Without the font the sheets' type is set this much smaller.
NOFONT_K = 0.6


def label_of(d, words):
    """A take's two caption lines (none: an empty tuple)."""
    return tuple(words[d['label_key']]) if d.get('label_key') else tuple(d.get('label', ()))


def describe_words(i, words=DEFAULTS):
    """The words take i shows in Describe mode, in the order they are used (for preset.json)."""
    d = DESCRIBE[i]
    w = []

    def form(k):
        f = DFORMS[k]
        out = [f['top'], f['title'], f['sub']]
        out += [a + ': ' + b for a, b in f.get('rows', ())]
        if f.get('body'):
            out.append(' '.join(f['body']))
        return out + [f['foot']]
    if d.get('hero'):
        w += form(d['hero'])
    if d.get('back'):
        w.append(' '.join(d['back']))
    if d.get('pages'):
        w += [' '.join(p) for p in d['pages']]
    if d.get('phrases'):
        w += [p.replace(NL, ' ') for p in d['phrases']]
    if d.get('forms'):
        for k in ('a', 'b', 'c'):
            w += form(k)
    w += list(label_of(d, words))
    return w


def make_form(par, name, f, res):
    """An explaining sheet: a chain of Text TOPs over a paper-coloured Constant TOP."""
    k = res / 512.0
    bg = par.create(td.constantTOP, name + '_bg')
    bg.par.colorr, bg.par.colorg, bg.par.colorb = f['paper']
    bg.par.outputresolution = 'custom'
    bg.par.resolutionw = bg.par.resolutionh = res
    src = [bg]

    def layer(suffix, size, items):
        tab = par.create(td.tableDAT, name + suffix + '_spec')
        tab.clear()
        tab.appendRow(['x', 'y', 'text'])
        for x, y, text in items:
            tab.appendRow([int(x * k), int(res - y * k), text])
        t = par.create(td.textTOP, name + suffix)
        t.inputConnectors[0].connect(src[0])
        t.par.specdat = tab.name
        t.par.fontfile.expr = BARLOW
        t.par.fontsizexunit = 'pixels'
        t.par.fontsizex.expr ="%r * (1 if %s else %r)" % (size * k, BARLOW, NOFONT_K)
        t.par.alignx, t.par.aligny = 'left', 'bottom'
        t.par.fontcolorr, t.par.fontcolorg, t.par.fontcolorb = f['ink']
        t.par.bgalpha = 0
        src[0] = t
        return t

    small = [(24, 44, f['top']), (24, 492, f['foot']), (24, 54, '_' * 72)]
    mid = [(24, 200, f['sub'])]
    if f.get('rows'):
        for i, (a, b) in enumerate(f['rows']):
            y = 262 + i * 54
            mid.append((24, y, a))
            mid.append((176, y, b))
            small.append((172, y + 6, '_' * 49))
    if f.get('body'):
        layer('_body', 23, [(24, 248 + i * 36, line) for i, line in enumerate(f['body'])])
    layer('_small', 17, small)
    layer('_mid', 28, mid)
    return layer('_title', 104, [(20, 158, f['title'])])


def _rows():
    """Flatten TAKES into (channel name, values per take)."""
    def val(t, k):
        return t.get(k, DEF[k])
    rows = []
    for k in ('bgk', 'skyl', 'bouncel', 'form', 'fov', 'sway', 'dolly', 'mirror', 'yvar', 'zvar', 'fog', 'key', 'keyend', 'spot',
              'sheets', 'props', 'mono', 'hero', 'idol', 'back', 'backin', 'backemit', 'flip', 'ring', 'keepout',
              'glow', 'vig', 'sat', 'dither', 'sky', 'bloom', 'dof0', 'dof1', 'dofnear', 'blur'):
        rows.append((k, [float(val(t, k)) for t in TAKES]))
    for k, names in (('cam', ('camx', 'camy', 'camz')), ('aim', ('aimx', 'aimy', 'aimz')),
                     ('haze', ('hazer', 'hazeg', 'hazeb')), ('amb', ('ambr', 'ambg', 'ambb', 'ambd')),
                     ('backcol', ('backr', 'backg', 'backb')), ('tint', ('tintr', 'tintg', 'tintb')),
                     ('shadow', ('shr', 'shg', 'shb'))):
        for i, n in enumerate(names):
            rows.append((n, [float(val(t, k)[i]) for t in TAKES]))
    foc = []
    for t in TAKES:
        f = val(t, 'focus')
        if f is None:
            f = math.dist(val(t, 'cam'), val(t, 'aim'))
        foc.append(float(f))
    rows.append(('focus', foc))
    rows.append(('zvard', [float(t.get('zvard', val(t, 'zvar')) if t.get('zvard') is not None else val(t, 'zvar')) for t in TAKES]))
    return rows


def T(name):
    return "op('tk')['%s']" % name


SEED = "op('shot')['seed']"
MIR = "(-1 if (%s > 0.5 and (%s * 3.7) %% 1 > 0.5) else 1)" % (T('mirror'), SEED)
# distance from the aim point: arrival dolly, and the seed's closer framing
DOL = ("((1 + %s * math.exp(-5 * op('shot')['age'])) * (1 - (%s if (op('mode')['describe'] or op('mode')['inp']) else %s) * ((%s * 9.1) %% 1)))"
       % (T('dolly'), T('zvard'), T('zvar'), SEED))
ARR = "(lambda a: (1 - a) * (1 - a))(min(1.0, op('shot')['age'] / 0.7))"

# Order matters: field.frag and post.frag read these rows by index.
CTL = [
    ('bar_pos',  "op('hub')['bar_pos']"),                    # 0
    ('beat_pos', "op('hub')['beat_pos']"),                   # 1
    ('kick',     "op('kicklag')['hit_low']"),                # 2
    ('evolve',   "op('hub')['evolve']"),                     # 3
    ('energy',   "op('hub')['energy']"),                     # 4
    ('form',     T('form')),                                 # 5
    ('seed',     SEED),                                      # 6
    ('arr',      ARR),                                       # 7  1 at the cut, 0 from 0.7 s on
    ('focus',    T('focus')),                                # 8
    ('hit_mid',  "op('hub')['hit_mid']"),                    # 9
    ('age',      "op('shot')['age']"),                       # 10
    ('ring',     "op('ringenv')[0]"),                        # 11 1 at each kick, falling to 0 in 0.85 s
    ('camx',     "(%s + (%s - %s) * %s) * %s + math.sin(op('hub')['evolve'] * 0.23) * 1.3 * %s"
                 % (T('aimx'), T('camx'), T('aimx'), DOL, MIR, T('sway'))),      # 12
    ('camy',     "%s + (%s - %s) * %s + %s * ((%s * 5.3) %% 1) + math.sin(op('hub')['evolve'] * 0.17) * 0.6 * %s"
                 % (T('aimy'), T('camy'), T('aimy'), DOL, T('yvar'), SEED, T('sway'))),   # 13
    ('camz',     "%s + (%s - %s) * %s" % (T('aimz'), T('camz'), T('aimz'), DOL)),          # 14
    ('keepout',  T('keepout')),                              # 15
    ('hit_high', "op('hub')['hit_high']"),                   # 16
    ('bass',     "op('hub')['bass']"),                       # 17
    ('flip',     T('flip')),                                 # 18
    ('ringscale', T('ring')),                                # 19
    ('tintr',    T('tintr')),                                # 20
    ('tintg',    T('tintg')),                                # 21
    ('tintb',    T('tintb')),                                # 22
    ('inp',      "op('mode')['inp']"),                       # 23 1 while an Input picture is in use
]


def build():
    LIB = {'op': op}
    exec(open(td.project.folder + '/experiments/sw_hub/scene_lib.py', encoding='utf-8').read(), LIB)
    scene = LIB['new_scene'](SLUG, 1250, -700)
    out1 = scene.op('out1')
    W = LIB['scene_words'](scene, DEFAULTS)     # the pack's own words and shapes, or the ones above
    FORMS, PAGES, BACK_PHRASES = W['FORMS'], [tuple(p) for p in W['PAGES']], tuple(W['BACK_PHRASES'])

    def model(name, slug, own_mesh=None, rot=(0, 0, 0), teapot=(0.8, 0.8, 0.8)):
        """A library model as a Geometry COMP (the scaffold's), made safe for a missing library.

        own_mesh: a mesh file in this folder to use instead of the library's (the sheets).
        Otherwise the mesh may be the stand-in teapot, which 'fit' brings to the library's
        size and centre; with the real model 'fit' only turns it by `rot` (degrees, x then y
        then z), for a model whose own axes do not suit the place it is used.
        teapot: what the stand-in is painted (a real model's texture multiplies white).
        """
        g = LIB['import_model'](scene, name, slug)
        mesh, tex, mat = g.op('mesh'), g.op('tex'), g.op('mat')
        tex.par.file.expr = texfile(slug)     # never an empty file: that is a warning
        mat.par.basecolormap = tex.path       # the white stand-in picture multiplies the colour below
        if own_mesh:
            mesh.par.file.expr = here(own_mesh)
            return g
        real = "mod.paths.have('models/%s/model.obj')" % slug
        fit = g.create(td.transformPOP, 'fit')
        fit.inputConnectors[0].connect(mesh)
        fit.par.scale.expr = "1 if %s else %r" % (real, FIT_S)
        for ax, v in zip('xyz', FIT_T):
            getattr(fit.par, 't' + ax).expr = "0 if %s else %r" % (real, v)
        for ax, v in zip('xyz', rot):
            if v:
                getattr(fit.par, 'r' + ax).expr = "%r if %s else 0" % (float(v), real)
        mesh.render = mesh.display = False
        fit.render = fit.display = True
        for ch, v in zip('rgb', teapot):
            getattr(mat.par, 'basecolor' + ch).expr = "1 if %s else %r" % (have_tex(slug), v)
        return g

    def form_pictures(par, res):
        """The three printed sheets inside `par`: each a Switch ('pic0..2') between the pack's
        picture ('tex', 'tex1', 'tex2') and a stand-in drawn here ('sform0..2')."""
        out = []
        for i, f in enumerate(FORMS):
            slug = f['model']
            t = par.op('tex') if i == 0 else par.create(td.moviefileinTOP, 'tex%d' % i)
            t.par.file.expr = texfile(slug)
            if res:
                t.par.outputresolution = 'custom'
                t.par.resolutionw, t.par.resolutionh = res, res
            sf = make_form(par, 'sform%d' % i, f, res or 1024)
            sw = par.create(td.switchTOP, 'pic%d' % i)
            t.outputConnectors[0].connect(sw)
            sf.outputConnectors[0].connect(sw)
            sw.par.index.expr = "0 if %s else 1" % have_tex(slug)
            sw.nodeX, sw.nodeY = 150, 200 - 120 * i
            out.append(sw)
        return out

    # ---- the take table as a CHOP: one channel per look value, switched by shot/take
    tk = scene.create(td.constantCHOP, 'tk')
    TAKES[1]['zvar'] = W['BOARD_CROP']        # how close the seed may crop the board depends on the pack's face
    TAKES[1]['zvard'] = W['BOARD_CROP_D']     # and the same in Describe mode
    rows = _rows()
    tk.seq.const.numBlocks = len(rows)
    for i, (name, vals) in enumerate(rows):
        getattr(tk.par, 'const%dname' % i).val = name
        getattr(tk.par, 'const%dvalue' % i).expr = "%r[int(op('shot')['take']) %% %d]" % (tuple(vals), NT)
    tk.nodeX, tk.nodeY = -400, 460

    # ---- Describe and Input: the two switches every other switch reads
    # Input: the picture comes in through 'inp'. A blank, missing or own-scene path falls back to
    # 'inblank', so nothing errors and nothing can loop; 'inp' only reads the other TOP.
    inblank = scene.create(td.constantTOP, 'inblank')
    inblank.par.outputresolution = 'custom'
    inblank.par.resolutionw, inblank.par.resolutionh = 16, 16
    inblank.par.colorr = inblank.par.colorg = inblank.par.colorb = 0
    inp = scene.create(td.selectTOP, 'inp')
    inp.par.top.expr = ("(lambda p: p if (p and op(p) is not None and op(p).isTOP "
                        "and not op(p).path.startswith(parent().path + '/')) else 'inblank')"
                        "(parent().par.Input.eval().strip())")
    mode = scene.create(td.constantCHOP, 'mode')
    mode.par.name0, mode.par.name1 = 'describe', 'inp'
    mode.par.value0.expr = "int(parent().par.Describe)"
    mode.par.value1.expr = "int(op('inp').par.top.eval() != op('inblank'))"   # eval() gives the operator
    # the board reads the picture as 96 x 54 sheets (16:9 inside its 96 x 64)
    inlum = scene.create(td.resolutionTOP, 'inlum')
    inlum.inputConnectors[0].connect(inp)
    inlum.par.outputresolution = 'custom'
    inlum.par.resolutionw, inlum.par.resolutionh = 96, 54
    inlum.par.inputfiltertype = 'mipmap'
    inlum.par.filtertype = 'nearest'
    for i, o in enumerate((inblank, inp, inlum, mode)):
        o.nodeX, o.nodeY = -900 + 130 * i, 460
    pr_frag = scene.create(td.textDAT, 'print_frag')
    pr_frag.par.file.expr = here('shaders/print.frag')
    pr_frag.par.syncfile = True
    pr_frag.nodeX, pr_frag.nodeY = -380, 460
    MODESW = "2 if op('../mode')['inp'] else int(op('../mode')['describe'])"   # everyday / describe / input

    def printed(par, name, paper, res):
        """The Input picture printed on a sheet of the given paper stock."""
        sel = par.create(td.selectTOP, name + '_in')
        sel.par.top = '../inp'
        g = par.create(td.glslTOP, name)
        g.par.pixeldat = '../print_frag'
        g.par.outputresolution = 'custom'
        g.par.resolutionw = g.par.resolutionh = res
        g.par.inputfiltertype = 'mipmap'
        g.inputConnectors[0].connect(sel)
        g.seq.vec.numBlocks = 2
        g.par.vec0name = 'uPaper'
        g.par.vec0valuex, g.par.vec0valuey, g.par.vec0valuez = paper
        g.par.vec1name = 'uDuo'       # w = 1: the reverse side, a two-colour print (set by the caller)
        g.par.vec1valuew = 0          # a new vector block's w defaults to 1
        return g

    # ---- control: music values in one CHOP, sent to the shaders as a texture
    sel = scene.create(td.selectCHOP, 'kicksel')
    sel.par.chop = 'hub'
    sel.par.channames = 'hit_low'
    lag = scene.create(td.lagCHOP, 'kicklag')
    lag.inputConnectors[0].connect(sel)
    lag.par.lag1, lag.par.lag2 = 0.0, 0.22
    # every kick restarts a linear 1 -> 0 ramp; field.frag turns it into a ring leaving the middle
    ring = scene.create(td.triggerCHOP, 'ringenv')
    # (triggered from the hit counter's step, not the hit_low envelope: the envelope does not
    # always fall back under a threshold between two close kicks, and then the ramp never restarts)
    hsel = scene.create(td.selectCHOP, 'hitsel')
    hsel.par.chop = 'hub'
    hsel.par.channames = 'hits_low'
    hslope = scene.create(td.slopeCHOP, 'hitslope')
    hslope.inputConnectors[0].connect(hsel)
    hsel.nodeX, hsel.nodeY = -200, 420
    hslope.nodeX, hslope.nodeY = -50, 420
    ring.inputConnectors[0].connect(hslope)
    ring.par.threshup, ring.par.threshdown = 0.5, 0.5
    ring.par.multitrigger = 'restart'
    ring.par.attack, ring.par.peak, ring.par.peaklen = 0, 1, 0
    ring.par.decay, ring.par.dshape, ring.par.sustain, ring.par.release = 0.85, 'linear', 0, 0
    ring.nodeX, ring.nodeY = 100, 420
    ctl = scene.create(td.constantCHOP, 'ctl')
    ctl.seq.const.numBlocks = len(CTL)
    for i, (name, expr) in enumerate(CTL):
        getattr(ctl.par, 'const%dname' % i).val = name
        getattr(ctl.par, 'const%dvalue' % i).expr = expr
    ctltex = scene.create(td.choptoTOP, 'ctltex')
    ctltex.par.chop = 'ctl'
    ctltex.par.dataformat = 'r'
    ctltex.par.format = 'r32float'
    sel.nodeX, sel.nodeY = -200, 320
    lag.nodeX, lag.nodeY = -50, 320
    ctl.nodeX, ctl.nodeY = -200, 200
    ctltex.nodeX, ctltex.nodeY = -50, 200

    # ---- the board's pages: one 96 x 48 Text TOP each, stacked into an atlas the field shader reads
    def atlas(name, prefix, book, y0):
        pgs = []
        for i, lines in enumerate(book):
            t = scene.create(td.textTOP, '%s%d' % (prefix, i))
            t.par.text = NL.join(lines)
            t.par.fontfile.expr = CHICAGO
            t.par.fontsizexunit = 'pixels'
            t.par.fontsizex = 12
            t.par.outputresolution = 'custom'
            t.par.resolutionw, t.par.resolutionh = 96, 48
            t.par.alignx, t.par.aligny = 'center', 'center'
            t.par.bgalpha = 1
            t.nodeX, t.nodeY = -900 + 130 * (i % 4), y0 - 110 * (i // 4)
            pgs.append(t)
        a = scene.create(td.layoutTOP, name)
        a.par.tops = ' '.join(t.name for t in pgs)
        a.par.align = 'vertbt'
        a.par.fit = 'fill'    # the default (fitbest) squeezes each page into a square cell
        a.par.outputresolution = 'custom'
        a.par.resolutionw, a.par.resolutionh = 96, 48 * len(book)
        a.par.filtertype = 'nearest'
        a.nodeX, a.nodeY = -330, y0 - 390
        return a
    assert len(PAGES_D) == len(PAGES)
    pages = atlas('pages', 'pg', PAGES, 60)
    pages_d = atlas('pages_d', 'pgd', PAGES_D, -520)      # the same board, explaining itself
    pagesw = scene.create(td.switchTOP, 'pagesw')
    pages.outputConnectors[0].connect(pagesw)
    pages_d.outputConnectors[0].connect(pagesw)
    pagesw.par.index.expr = "op('mode')['describe']"
    pagesw.nodeX, pagesw.nodeY = -200, -330
    pages_d.cook(force=True)

    frag = scene.create(td.textDAT, 'field_frag')
    frag.par.file.expr = here('shaders/field.frag')
    frag.par.syncfile = True
    frag.nodeX, frag.nodeY = -200, 60

    fy = [0]

    def field(name, w, h, prop, seed):
        """Four tiny GLSL TOPs: <name>_p (position), _n (facing), _u (up), _c (colour)."""
        tops = []
        for k, suf in enumerate(('p', 'n', 'u', 'c')):
            g = scene.create(td.glslTOP, name + '_' + suf)
            g.par.pixeldat = frag.name
            g.par.outputresolution = 'custom'
            g.par.resolutionw, g.par.resolutionh = w, h
            g.par.format = 'rgba32float'
            g.par.filtertype = 'nearest'
            g.par.inputfiltertype = 'nearest'
            g.inputConnectors[0].connect(ctltex)
            g.inputConnectors[1].connect(pagesw)
            g.inputConnectors[2].connect(inlum)    # the Input picture, one pixel per board sheet
            g.seq.vec.numBlocks = 4
            for j, (un, uv) in enumerate((('uOut', k), ('uProp', prop), ('uSeed', seed), ('uPages', len(PAGES)))):
                getattr(g.par, 'vec%dname' % j).val = un
                getattr(g.par, 'vec%dvaluex' % j).val = uv
            g.nodeX, g.nodeY = 150 + 150 * k, 300 - fy[0] * 110
            tops.append(g)
        fy[0] += 1
        return tops

    def instance(geo, tops, forward, scale):
        p, n, u, c = tops
        geo.par.instancing = True
        geo.par.instancecountmode = 'oplength'
        geo.par.instanceop = p.path
        geo.par.instancetx, geo.par.instancety, geo.par.instancetz = 'r', 'g', 'b'
        geo.par.instancerottoop = n.path
        geo.par.instancerottox, geo.par.instancerottoy, geo.par.instancerottoz = 'r', 'g', 'b'
        geo.par.instancerottoforward = forward
        geo.par.instancerotupop = u.path
        geo.par.instancerotupx, geo.par.instancerotupy, geo.par.instancerotupz = 'r', 'g', 'b'
        geo.par.instancecolorop = c.path
        geo.par.instancecolormode = 'multiply'
        geo.par.instancer, geo.par.instanceg, geo.par.instanceb = 'r', 'g', 'b'
        geo.par.instancesx = geo.par.instancesy = geo.par.instancesz = ''
        geo.par.scale = scale

    def show(geo, key):
        geo.par.render.expr = "op('tk')['%s'] > 0.5" % key

    # ---- sheets: 64 x 96 = 6144 instances, three form textures picked per instance
    # The printed side and the reverse are two single-sided meshes on the same instance field,
    # so a turning sheet shows its reverse, not a mirrored form.
    sheets = model('sheets', FORMS[0]['model'], 'meshes/sheet_front.obj')
    sheets.op('mat').par.cullface = 'backfaces'
    st = field('sheet', 64, 96, 0, 1)
    instance(sheets, st, 'posy', 1.0)
    texs = form_pictures(sheets, 512)
    # each of the three printed sides is a Switch: the pack's sheet, the explaining sheet
    # (Describe), or the Input picture printed on that paper stock
    faces = []
    for i, (t, key) in enumerate(zip(texs, ('a', 'b', 'c'))):
        d = make_form(sheets, 'dform_' + key, DFORMS[key], 512)
        pr = printed(sheets, 'print%d' % i, DFORMS[key]['paper'], 512)
        sw = sheets.create(td.switchTOP, 'face%d' % i)
        for src in (t, d, pr):
            src.outputConnectors[0].connect(sw)
        sw.par.index.expr = MODESW
        sw.nodeX, sw.nodeY = 300, 200 - 120 * i
        faces.append(sw)
    sheets.par.instancetexmode = 'replace'
    sheets.par.instancetexs = ' '.join(t.path for t in faces)
    sheets.par.instancetexindexop = st[0].path
    sheets.par.instancetexindex = 'a'
    sheets.op('mat').par.roughness = 0.85
    sm = sheets.op('mat')
    sm.par.emitr, sm.par.emitg, sm.par.emitb = 0.035, 0.045, 0.06   # unlit paper is ink, never a black hole
    sheets.nodeX, sheets.nodeY = 800, 300
    show(sheets, 'sheets')

    # the reverse: three versions stay loaded, the take switches between them
    backs = model('backs', FORMS[0]['model'], 'meshes/sheet_back.obj')
    instance(backs, st, 'posy', 1.0)

    def backtext(name):
        bt = backs.create(td.textTOP, name)
        bt.par.fontfile.expr = CHICAGO
        bt.par.outputresolution = 'custom'
        bt.par.resolutionw, bt.par.resolutionh = 512, 396
        bt.par.fontsizex = 84
        bt.par.alignx, bt.par.aligny = 'center', 'center'
        bt.par.fontcolorr, bt.par.fontcolorg, bt.par.fontcolorb = 0.96, 0.90, 0.78
        bt.par.bgalpha = 1
        return bt
    bt = backtext('backtex')                       # 0: red with the two-line mark
    bt.par.text = W['WORDMARK']
    bt.par.fontsizex = W['WORDMARK_PX']
    bt.par.bgcolorr, bt.par.bgcolorg, bt.par.bgcolorb = DEF['backcol']
    bp = backs.create(td.constantTOP, 'backplain')  # 1: plain paper in the take's colour
    bp.par.outputresolution = 'custom'
    bp.par.resolutionw, bp.par.resolutionh = 64, 48
    bp.par.colorr.expr, bp.par.colorg.expr, bp.par.colorb.expr = ("op('../tk')['backr']", "op('../tk')['backg']", "op('../tk')['backb']")
    bph = backtext('backphrase')                    # 2: one of BACK_PHRASES on the take's colour; the seed picks it
    bph.par.text.expr = "%r[int(op('../shot')['seed'] * 61) %% %d]" % (tuple(BACK_PHRASES), len(BACK_PHRASES))
    bph.par.fontautosize = 'fitiffat'
    bph.par.fontsizex = W['BACK_PHRASE_PX']
    bph.par.bgcolorr.expr, bph.par.bgcolorg.expr, bph.par.bgcolorb.expr = ("op('../tk')['backr']", "op('../tk')['backg']", "op('../tk')['backb']")
    # Describe twins of the two lettered reverses
    btd = backtext('backtex_d')
    btd.par.text.expr = "%r[int(op('../shot')['take']) %% %d]" % (
        tuple(NL.join(d.get('back', ('', ''))) for d in DESCRIBE), NT)
    btd.par.bgcolorr, btd.par.bgcolorg, btd.par.bgcolorb = DEF['backcol']
    btd.par.fontautosize = 'fitiffat'
    bphd = backtext('backphrase_d')
    bphd.par.text.expr = "%r[int(op('../shot')['seed'] * 61) %% %d]" % (tuple(BACK_PHRASES_D), len(BACK_PHRASES_D))
    bphd.par.fontautosize = 'fitiffat'
    bphd.par.fontsizex = 110
    bphd.par.bgcolorr.expr, bphd.par.bgcolorg.expr, bphd.par.bgcolorb.expr = ("op('../tk')['backr']", "op('../tk')['backg']", "op('../tk')['backb']")
    btsw = backs.create(td.switchTOP, 'backtexsw')
    bphsw = backs.create(td.switchTOP, 'backphrasesw')
    for sw, a, b in ((btsw, bt, btd), (bphsw, bph, bphd)):
        a.outputConnectors[0].connect(sw)
        b.outputConnectors[0].connect(sw)
        sw.par.index.expr = "op('../mode')['describe']"
        b.cook(force=True)
    # 3: the Input picture as a two-colour print in the take's reverse colour
    bpr = printed(backs, 'backprint', (1.0, 1.0, 1.0), 512)
    bpr.par.resolutionh = 396
    for ax, ch in zip('xyz', ('backr', 'backg', 'backb')):
        getattr(bpr.par, 'vec1value' + ax).expr = "op('../tk')['%s']" % ch
    bpr.par.vec1valuew = 1
    bsw = backs.create(td.switchTOP, 'backsw')
    for i, t in enumerate((btsw, bp, bphsw, bpr)):
        t.outputConnectors[0].connect(bsw)
        t.nodeX, t.nodeY = -150, 200 - 120 * i
        t.cook(force=True)
    for i, t in enumerate((bt, btd, bph, bphd)):
        t.nodeX, t.nodeY = -300, 200 - 120 * i
    bsw.par.index.expr = ("3 if (op('../mode')['inp'] and op('../tk')['backin'] > 0.5 and not op('../mode')['describe']) "
                          "else op('../tk')['back']")   # Describe keeps its words on the reverses
    bm = backs.op('mat')
    bm.par.basecolormap = bsw.path
    bm.par.emitmap = bsw.path
    bm.par.emitr.expr = bm.par.emitg.expr = bm.par.emitb.expr = "op('../tk')['backemit']"   # the reverse glows a little in the void
    bm.par.roughness = 0.85
    bm.par.cullface = 'backfaces'
    backs.nodeX, backs.nodeY = 950, 300
    show(backs, 'sheets')

    # ---- props: light ones in bulk, heavy ones sparingly (the rows of PROPS)
    props = []
    for i, row in enumerate(W['PROPS']):
        g = model('prop%d' % i, row['model'], rot=row['rot'], teapot=row['teapot'])
        instance(g, field('prop%d' % i, int(row['w']), int(row['h']), 1, 10 + i), 'posz', row['scale'])
        g.nodeX, g.nodeY = 800, 190 - 110 * i
        show(g, 'props')
        props.append(g)

    # ---- the monolith
    M = W['MONOLITH']
    mono = model('monolith', M['model'], teapot=M['teapot'])
    mono.par.scale = M['scale']
    mono.par.ry = M['ry']
    mono.par.ty = M['ty']
    mono.nodeX, mono.nodeY = 800, -260
    show(mono, 'mono')

    # ---- the idol the prop rings turn round (ritual take only)
    I = W['IDOL']
    idol = model('idol', I['model'], teapot=I['teapot'])
    idol.par.scale.expr = "%r * (1 + 0.07 * op('ctl')['kick'])" % float(I['scale'])
    idol.par.ty = I['ty']
    idol.par.ry.expr = "%sop('hub')['evolve'] * 25 + 200 * op('ctl')['arr']" % ('%r + ' % float(I['ry']) if I['ry'] else '')
    cm = idol.op('mat')
    cm.par.roughness = I['rough']
    cm.par.emitr, cm.par.emitg, cm.par.emitb = I['emit']
    idol.nodeX, idol.nodeY = 950, -260
    show(idol, 'idol')

    # ---- the one sheet: a single large sheet close to the lens (one_sheet take only)
    hero = model('hero', FORMS[0]['model'], 'meshes/sheet_front.obj')
    hb = hero.create(td.fileinPOP, 'mesh_back')
    hb.par.file.expr = here('meshes/sheet_back.obj')
    hb.render = True
    htex = form_pictures(hero, 0)     # the pictures at their own size
    hsw = hero.create(td.switchTOP, 'texsw')
    for t in htex:
        t.outputConnectors[0].connect(hsw)
        t.cook(force=True)
    hsw.par.index.expr = "int(op('../shot')['seed'] * 31) % 3"
    # the pack's sheet / the explaining sheet with real sentences / the Input picture as a large print
    hd = make_form(hero, 'dform_hero', DFORMS['hero'], 1024)
    hpr = printed(hero, 'print', PAPER_W, 1024)
    hface = hero.create(td.switchTOP, 'face')
    for src in (hsw, hd, hpr):
        src.outputConnectors[0].connect(hface)
    hface.par.index.expr = MODESW
    hm = hero.op('mat')
    hm.par.basecolormap = hface.path
    hm.par.roughness = 0.8
    hm.par.cullface = 'backfaces'   # the two sides are coplanar: without culling the wrong one wins
    hm.par.emitr, hm.par.emitg, hm.par.emitb = 0.03, 0.03, 0.04
    hero.par.scale = 2.3
    # it hangs left or right of centre, 3.6 units in front of the lens, and swoops in at the cut
    hero.par.tx.expr = "%s * (-1.45 - 7 * op('ctl')['arr']) + op('ctl')['camx']" % MIR
    hero.par.ty.expr = "op('ctl')['camy'] - 0.75 + 0.15 * math.sin(op('hub')['evolve'] * 1.1)"
    hero.par.tz.expr = "op('ctl')['camz'] - 3.6"
    hero.par.rx.expr = "78 + 14 * math.sin(op('hub')['evolve'] * 0.6) + 22 * op('ctl')['kick']"
    hero.par.ry.expr = "%s * 18 + 24 * math.sin(op('hub')['evolve'] * 0.8)" % MIR
    hero.par.rz.expr = "%s * (-8 + 150 * op('ctl')['arr']) + 6 * math.sin(op('hub')['bar_pos'] * math.pi)" % MIR
    hero.nodeX, hero.nodeY = 1100, -260
    show(hero, 'hero')

    # nothing a take needs is loaded at the cut: models and textures are read now
    for g in [sheets, backs, mono, idol, hero] + props:
        for c in g.children:
            if c.family in ('POP', 'TOP'):
                c.cook(force=True)

    # ---- camera, light, render
    aim = scene.create(td.nullCOMP, 'aim')
    aim.par.tx.expr = "%s * %s" % (T('aimx'), MIR)
    aim.par.ty.expr = T('aimy')
    aim.par.tz.expr = T('aimz')
    aim.nodeX, aim.nodeY = 950, -370
    cam = scene.create(td.cameraCOMP, 'cam')
    cam.par.tx.expr = "op('ctl')['camx']"
    cam.par.ty.expr = "op('ctl')['camy']"
    cam.par.tz.expr = "op('ctl')['camz']"
    cam.par.lookat = aim.path
    cam.par.fov.expr = T('fov')  # horizontal field of view
    cam.par.near, cam.par.far = 0.2, 900
    cam.par.fog = 'exp'
    cam.par.fogdensity.expr = T('fog')
    cam.par.fogalpha.expr = T('bgk')
    cam.par.fogcolorr.expr, cam.par.fogcolorg.expr, cam.par.fogcolorb.expr = T('hazer'), T('hazeg'), T('hazeb')
    cam.nodeX, cam.nodeY = 800, -370

    # headlamp: a point light riding with the camera, so near sheets are bright and depth falls off
    key = scene.create(td.lightCOMP, 'key')
    key.par.lighttype = 'point'
    # (kept close to the lens: at -2.5, +3.0 a sheet 3 units away could face the camera and still
    # have its back to the lamp, which drew pure black polygons over the monolith)
    key.par.tx.expr = "op('cam').par.tx - 1.1"
    key.par.ty.expr = "op('cam').par.ty + 1.4"
    key.par.tz.expr = "op('cam').par.tz + 0.6"
    key.par.dimmer.expr = T('key')
    key.par.cr, key.par.cg, key.par.cb = 1.0, 0.95, 0.84
    key.par.attenuated = True
    key.par.attenuationstart = 4
    key.par.attenuationend.expr = T('keyend')
    key.nodeX, key.nodeY = 800, -480
    # one hard lamp straight above the middle: sheets flare as they cross its cone
    spot = scene.create(td.lightCOMP, 'spot')
    spot.par.lighttype = 'cone'
    spot.par.tx, spot.par.ty, spot.par.tz = 1.5, 15, 4
    spot.par.lookat = mono.path
    spot.par.coneangle, spot.par.conedelta = 38, 10
    spot.par.dimmer.expr = "(2.6 + 2.6 * op('hub')['energy']) * %s" % T('spot')
    spot.par.cr, spot.par.cg, spot.par.cb = 1.0, 0.86, 0.62
    spot.nodeX, spot.nodeY = 950, -480
    amb = scene.create(td.ambientlightCOMP, 'amb')
    amb.par.cr.expr, amb.par.cg.expr, amb.par.cb.expr = T('ambr'), T('ambg'), T('ambb')
    amb.par.dimmer.expr = T('ambd')
    amb.nodeX, amb.nodeY = 800, -590
    # (the ambient light alone leaves a sheet facing away from the lamps nearly black)
    skyl = scene.create(td.lightCOMP, 'skyl')
    skyl.par.lighttype = 'distant'
    skyl.par.rx, skyl.par.ry = -70, 20
    skyl.par.dimmer.expr = T('skyl')
    skyl.nodeX, skyl.nodeY = 950, -590
    bouncel = scene.create(td.lightCOMP, 'bouncel')
    bouncel.par.lighttype = 'distant'
    bouncel.par.rx, bouncel.par.ry = 75, -30
    bouncel.par.dimmer.expr = T('bouncel')
    bouncel.par.cr, bouncel.par.cg, bouncel.par.cb = 0.85, 1.0, 0.8
    bouncel.nodeX, bouncel.nodeY = 1100, -590

    allgeo = [sheets, backs, mono, idol, hero] + props
    render = scene.create(td.renderTOP, 'render')
    render.par.camera = cam.path
    render.par.geometry = ' '.join(g.path for g in allgeo)
    render.par.lights = ' '.join((key.path, spot.path, amb.path, skyl.path, bouncel.path))
    render.par.outputresolution = 'custom'
    render.par.resolutionw, render.par.resolutionh = 1280, 720
    render.par.format = 'rgba16float'
    render.par.bgcolorr.expr, render.par.bgcolorg.expr, render.par.bgcolorb.expr = T('hazer'), T('hazeg'), T('hazeb')
    render.par.bgcolora = 0
    # every material writes camera depth to alpha: post.frag uses it for depth of field (0 = nothing drawn)
    for g in allgeo:
        g.op('mat').par.writecameradepthtoalpha = True
    render.nodeX, render.nodeY = 1000, 0

    pfrag = scene.create(td.textDAT, 'post_frag')
    pfrag.par.file.expr = here('shaders/post.frag')
    pfrag.par.syncfile = True
    pfrag.nodeX, pfrag.nodeY = 1000, -220
    post = scene.create(td.glslTOP, 'post')
    post.par.pixeldat = pfrag.name
    post.par.format = 'rgba16float'
    post.inputConnectors[0].connect(render)
    blur = scene.create(td.blurTOP, 'blur')
    blur.inputConnectors[0].connect(render)
    blur.par.size.expr = T('blur')
    blur.nodeX, blur.nodeY = 1100, 110
    post.inputConnectors[1].connect(ctltex)
    post.inputConnectors[2].connect(blur)
    post.seq.vec.numBlocks = 4
    for j, (un, chans) in enumerate((('uHaze', ('hazer', 'hazeg', 'hazeb')), ('uShadow', ('shr', 'shg', 'shb')),
                                     ('uP1', ('glow', 'vig', 'sat', 'dither')), ('uP2', ('dof0', 'dof1', 'dofnear', 'sky')))):
        getattr(post.par, 'vec%dname' % j).val = un
        for c, ax in zip(chans, 'xyzw'):
            getattr(post.par, 'vec%dvalue%s' % (j, ax)).expr = T(c)
    post.nodeX, post.nodeY = 1000, -110
    bloom = scene.create(td.bloomTOP, 'bloom')
    bloom.inputConnectors[0].connect(post)
    bloom.par.bloomthreshold = 0.6
    bloom.par.bloomintensity.expr = T('bloom')
    bloom.nodeX, bloom.nodeY = 1100, -110

    # ---- Describe: a two-line caption along the bottom edge, for the takes with no readable text
    # (with an Input the printed sides carry the picture, not words, so every take gets a caption then)
    labels, labels_in, fg, bg = [], [], [], []
    for i, d in enumerate(DESCRIBE):
        labels.append(NL.join(label_of(d, W)))
        labels_in.append(NL.join(d.get('label_input') or label_of(d, W)))
        c = LABEL_COL.get(i, ((0.96, 0.90, 0.78), INK))
        fg.append(c[0])
        bg.append(c[1])
    TK = "[int(op('shot')['take']) %% %d]" % NT
    LAB = "(%r if op('mode')['inp'] else %r)%s" % (tuple(labels_in), tuple(labels), TK)
    cap = scene.create(td.textTOP, 'cap')
    cap.par.text.expr = LAB
    cap.par.fontfile.expr = CHICAGO
    cap.par.fontsizexunit = 'pixels'
    cap.par.fontsizex = 24
    cap.par.outputresolution = 'custom'
    cap.par.resolutionw, cap.par.resolutionh = 1280, 80
    cap.par.alignx, cap.par.aligny = 'left', 'center'
    cap.par.positionunit = 'pixels'
    cap.par.positionx = 24
    for j, ax in enumerate('rgb'):
        getattr(cap.par, 'fontcolor' + ax).expr = "%r%s" % (tuple(c[j] for c in fg), TK)
        getattr(cap.par, 'bgcolor' + ax).expr = "%r%s" % (tuple(c[j] for c in bg), TK)
    cap.par.bgalpha.expr = "%r%s" % (tuple(LABEL_A.get(i, 0.86) for i in range(NT)), TK)
    capover = scene.create(td.overTOP, 'capover')
    capover.inputConnectors[0].connect(cap)
    capover.inputConnectors[1].connect(bloom)
    capover.par.size = 'input2'
    capover.par.prefit = 'nativeres'
    capover.par.justifyh, capover.par.justifyv = 'left', 'bottom'
    capsw = scene.create(td.switchTOP, 'capsw')       # index 0 (Describe off) is the untouched picture
    bloom.outputConnectors[0].connect(capsw)
    capover.outputConnectors[0].connect(capsw)
    capsw.par.index.expr = "1 if (op('mode')['describe'] and %s) else 0" % LAB
    cap.nodeX, cap.nodeY = 1100, -330
    capover.nodeX, capover.nodeY = 1200, -220
    capsw.nodeX, capsw.nodeY = 1200, -110
    cap.cook(force=True)

    out1.inputConnectors[0].connect(capsw)
    return scene.path
