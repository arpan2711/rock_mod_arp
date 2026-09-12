# -*- coding: utf-8 -*-
"""Render the Rocksmith practice shortcuts onto a Wooting 80HE (ANSI) keyboard picture.

Output: docs/keymap-wooting-80he.png. Re-run after changing a keybind in RSMods.ini.
Keys and behaviour come from RSMods.ini [Keybinds] / [Audio Keybindings] and dllmain.cpp.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keymap-wooting-80he.png')

# ---- geometry (1u = one key) --------------------------------------------------------
U = 100         # px per key unit
G = 7           # gap inside the unit
R = 10          # corner radius
X0, Y0 = 60, 130
FROW_GAP = 0.35 # extra vertical gap under the F-row

# ---- colours -----------------------------------------------------------------------
BG        = (24, 25, 28)
CASE      = (38, 39, 43)
KEY       = (58, 60, 66)
KEY_EDGE  = (78, 80, 88)
TEXT      = (215, 216, 220)
TEXT_DIM  = (140, 142, 150)
INK       = (18, 18, 20)

GROUPS = {
    # name: (fill colour, legend text)
    'loop':   ((66, 133, 244),  'Loop'),
    'speed':  ((255, 152, 0),   'Riff Repeater speed'),
    'rewind': ((52, 199, 89),   'Pause / scrub'),
    'amp':    ((175, 82, 222),  'Amp source (game amp vs pedal)'),
    'mod':    ((120, 122, 130), 'Modifier / settings'),
    'game':   ((230, 230, 235), 'Rocksmith itself'),
}

# ---- shortcuts (what gets painted on the keys) ---------------------------------------
# key label -> (group, primary text, ctrl text)
SHORTCUTS = {
    '-':         ('speed',  'Speed\n-2%', None),
    '=':         ('speed',  'Speed\n+2%', None),
    'Backspace': ('rewind', 'Back 5 s', None),
    'Delete':    ('rewind', 'Fwd 5 s', None),
    'P':         ('rewind', 'Pause /\nresume', None),
    '[':         ('loop',   'Loop\nstart', None),
    ']':         ('loop',   'Loop\nend', None),
    '\\':        ('loop',   'Clear loop', None),
    "'":         ('amp',    'Game amp /\npedal only', None),
    'A':         ('mod',    None,         'Ctrl:\nreload ini'),
    'Esc':       ('game',   'Pause', None),
    'Enter':     ('game',   'Tuner screen:\nCalibrate', None),
}

# ---- Wooting 80HE ANSI layout: rows of (label, width_u, x_offset_u_before) ------------
# 84 keys. The TKL nav cluster is condensed to a 2x3 block: PrtSc / Pause on the F-row,
# Insert / Home and Delete / End under them. There are NO PgUp / PgDn keys (Fn layer).
# Arrows sit in the usual spot but pulled in under a 1.75u right Shift.
ROWS = [
    [('Esc',1,0),('F1',1,1),('F2',1,0),('F3',1,0),('F4',1,0),('F5',1,.5),('F6',1,0),('F7',1,0),('F8',1,0),
     ('F9',1,.5),('F10',1,0),('F11',1,0),('F12',1,0),('PrtSc',1,.25),('Pause',1,0)],
    [('`',1,0),('1',1,0),('2',1,0),('3',1,0),('4',1,0),('5',1,0),('6',1,0),('7',1,0),('8',1,0),('9',1,0),('0',1,0),
     ('-',1,0),('=',1,0),('Backspace',2,0),('Insert',1,.25),('Home',1,0)],
    [('Tab',1.5,0),('Q',1,0),('W',1,0),('E',1,0),('R',1,0),('T',1,0),('Y',1,0),('U',1,0),('I',1,0),('O',1,0),('P',1,0),
     ('[',1,0),(']',1,0),('\\',1.5,0),('Delete',1,.25),('End',1,0)],
    [('Caps',1.75,0),('A',1,0),('S',1,0),('D',1,0),('F',1,0),('G',1,0),('H',1,0),('J',1,0),('K',1,0),('L',1,0),(';',1,0),
     ("'",1,0),('Enter',2.25,0)],
    [('Shift',2.25,0),('Z',1,0),('X',1,0),('C',1,0),('V',1,0),('B',1,0),('N',1,0),('M',1,0),(',',1,0),('.',1,0),('/',1,0),
     ('Shift',1.75,0),('\u2191',1,1.25)],
    [('Ctrl',1.25,0),('Win',1.25,0),('Alt',1.25,0),('',6.25,0),('Alt',1.25,0),('Fn',1.25,0),('Ctrl',1.25,0),
     ('\u2190',1,.5),('\u2193',1,0),('\u2192',1,0)],
]

def font(size, bold=False):
    for name in (('seguisb.ttf' if bold else 'segoeui.ttf'), ('arialbd.ttf' if bold else 'arial.ttf')):
        p = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

F_TITLE = font(34, True)
F_SUB   = font(18)
F_KEY   = font(17, True)
F_KEYS  = font(13)
F_SHORT = font(13, True)
F_LEG   = font(16)
F_NOTE  = font(14)

board_w = 17.25 * U
board_h = (6 + FROW_GAP) * U
W = int(X0 * 2 + board_w)
H = int(Y0 + board_h + 250)
img = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(img)

# title
d.text((X0, 36), 'Rocksmith practice keys \u2014 Wooting 80HE', font=F_TITLE, fill=TEXT)
d.text((X0, 84), 'RSMods keybinds from RSMods.ini. Everything works live inside a song, one key each, no Ctrl.',
       font=F_SUB, fill=TEXT_DIM)

# case
d.rounded_rectangle((X0 - 22, Y0 - 22, X0 + board_w + 22, Y0 + board_h + 22), radius=26, fill=CASE)

def draw_key(x, y, w, label):
    px0, py0 = X0 + x * U + G / 2, Y0 + y * U + G / 2
    px1, py1 = X0 + (x + w) * U - G / 2, Y0 + (y + 1) * U - G / 2
    sc = SHORTCUTS.get(label)
    fill = GROUPS[sc[0]][0] if sc else KEY
    ink = INK if sc else TEXT
    d.rounded_rectangle((px0, py0, px1, py1), radius=R, fill=fill, outline=KEY_EDGE if not sc else None, width=1)
    # legend / cap label top-left
    lf = F_KEY if len(label) <= 2 else F_KEYS
    d.text((px0 + 9, py0 + 6), label, font=lf, fill=ink)
    if sc:
        _, primary, ctrl = sc
        ty = py0 + 28
        if primary:
            d.multiline_text((px0 + 9, ty), primary, font=F_SHORT, fill=ink, spacing=1)
            ty += 17 * (primary.count('\n') + 1) + 4
        if ctrl:
            d.multiline_text((px0 + 9, ty), ctrl, font=F_SHORT, fill=ink, spacing=1)

for r, row in enumerate(ROWS):
    y = r if r == 0 else r + FROW_GAP
    x = 0.0
    for label, w, gap in row:
        x += gap
        draw_key(x, y, w, label)
        x += w

# legend
ly = Y0 + board_h + 50
lx = X0
d.text((lx, ly), 'Legend', font=F_LEG, fill=TEXT)
ly += 30
for name in ('loop', 'speed', 'rewind', 'amp', 'mod', 'game'):
    col, txt = GROUPS[name]
    d.rounded_rectangle((lx, ly + 2, lx + 22, ly + 20), radius=5, fill=col)
    d.text((lx + 32, ly), txt, font=F_LEG, fill=TEXT)
    ly += 26

# notes, right of the legend
nx = X0 + 420
ny = Y0 + board_h + 50
notes = [
    'Workflow:  [ and ] around a few bars  ->  tap - to slow it down  ->  work it  ->  tap = past 100%',
    'so real tempo feels easy afterwards  ->  \\ clears the loop.',
    'P pauses the song in place, no menu. While paused, Backspace / Delete move the resume point (shown top-centre); P resumes there.',
    'Loop and speed keys work in Learn A Song, Non-Stop Play and Riff Repeater; pause / scrub only while a song is playing.',
    'Tunables in RSMods.ini:  RewindBy / ForwardBy = 5000 ms,  RRSpeedInterval = 2 %,  LoopingLeadUp = 2000 ms run-in before the loop.',
    '\'  mutes the game\'s guitar tone only - the backing track keeps playing. "PEDAL ONLY" shows top-left while muted.',
    'Top-right overlay while playing:  song timer  /  accuracy %  /  "12 in a row, best 37" streak.',
    'Ctrl + [ or ] still clears the loop and Ctrl + = still slows down, for muscle memory. Delete is the only nav-block key in use.',
]
for t in notes:
    d.text((nx, ny), t, font=F_NOTE, fill=TEXT_DIM)
    ny += 24

img.save(OUT)
print('wrote', OUT, img.size)
