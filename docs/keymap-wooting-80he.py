# -*- coding: utf-8 -*-
r"""Render the Rocksmith practice shortcuts onto a Wooting 80HE (ANSI) keyboard picture.

Usage:  py -3 docs\keymap-wooting-80he.py [--ini <RSMods.ini>] [--out <png>]

Defaults: ..\config\RSMods.ini in, docs\keymap-wooting-80he.png out. The Settings page
in Song Manager runs this after every keybind or tunable change, so the picture never
drifts from the ini. Which key does what is read from the ini; what each feature is
called (FEATURES) and the game's own fixed keys (FIXED) live here.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'SongManager'))
import rsmods_ini  # noqa: E402  - one source of truth for VK -> keycap labels

ap = argparse.ArgumentParser()
ap.add_argument('--ini', default=os.path.join(REPO, 'config', 'RSMods.ini'))
ap.add_argument('--out', default=os.path.join(HERE, 'keymap-wooting-80he.png'))
args = ap.parse_args()

with open(args.ini, 'rb') as fh:
    INI = fh.read().decode('utf-8', 'replace')

def ini_get(section, key, default=''):
    v = rsmods_ini.get(INI, section, key)
    return v.strip() if v is not None else default

def ini_int(section, key, default):
    try:
        return int(ini_get(section, key, str(default)))
    except ValueError:
        return default

# ---- geometry (1u = one key) --------------------------------------------------------
U = 124         # px per key unit
G = 7           # gap inside the unit
R = 10          # corner radius
X0, Y0 = 60, 160
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

# ---- what each ini key means on the picture ------------------------------------------
step = ini_int('Mod Settings', 'RRSpeedInterval', 2)
rew_ms = ini_int('Mod Settings', 'RewindBy', 5000)
fwd_ms = ini_int('Mod Settings', 'ForwardBy', 5000)
lead_ms = ini_int('Mod Settings', 'LoopingLeadUp', 0)
secs = lambda ms: ('%g s' % (ms / 1000.0))

FEATURES = [
    # (section, ini key, group, keycap text)
    ('Keybinds', 'RRSpeedDownKey', 'speed',  'Speed\n-%d%%' % step),
    ('Keybinds', 'RRSpeedKey',     'speed',  'Speed\n+%d%%' % step),
    ('Keybinds', 'RewindKey',      'rewind', 'Back %s' % secs(rew_ms)),
    ('Keybinds', 'ForwardKey',     'rewind', 'Fwd %s' % secs(fwd_ms)),
    ('Keybinds', 'PauseSongKey',   'rewind', 'Pause /\nresume'),
    ('Keybinds', 'LoopStartKey',   'loop',   'Loop\nstart'),
    ('Keybinds', 'LoopEndKey',     'loop',   'Loop\nend'),
    ('Keybinds', 'LoopClearKey',   'loop',   'Clear loop'),
    ('Audio Keybindings', 'ToggleAmpSourceKey', 'amp', 'Game amp /\npedal only'),
]

# Hard-wired in the DLL or the game; not in the ini.
FIXED = {
    'A':     ('mod',  None,                      'Ctrl:\nreload ini'),
    'Esc':   ('game', 'Pause',                   None),
    'Enter': ('game', 'Tuner screen:\nCalibrate', None),
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
ON_BOARD = {label for row in ROWS for label, _, _ in row}

# VK name -> the label used on this board. Space is the blank 6.25u cap.
def board_label(vk):
    lab = rsmods_ini.vk_label(vk)
    return {'Space': '', 'L Shift': 'Shift', 'R Shift': 'Shift', 'L Ctrl': 'Ctrl', 'R Ctrl': 'Ctrl',
            'L Alt': 'Alt', 'R Alt': 'Alt'}.get(lab, lab)

# ---- build the shortcut table from the ini -------------------------------------------
SHORTCUTS = {label: list(v) for label, v in FIXED.items()}   # label -> [group, primary, ctrl]
bound = {}          # ini key -> keycap label (or '' if unbound), for the notes
off_board = []      # (keycap label, text) for keys this keyboard does not have

for section, key, group, text in FEATURES:
    vk = ini_get(section, key)
    lab = board_label(vk) if vk else ''
    bound[key] = lab if vk else ''
    if not vk:
        continue
    if lab not in ON_BOARD:
        off_board.append((lab, text.replace('\n', ' ')))
        continue
    if lab in SHORTCUTS:
        SHORTCUTS[lab][1] = (SHORTCUTS[lab][1] + ' /\n' if SHORTCUTS[lab][1] else '') + text
    else:
        SHORTCUTS[lab] = [group, text, None]

def name(key):
    """Keycap label for the notes, or '(unbound)'."""
    return bound.get(key) or '(unbound)'

def font(size, bold=False):
    for fname in (('seguisb.ttf' if bold else 'segoeui.ttf'), ('arialbd.ttf' if bold else 'arial.ttf')):
        p = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', fname)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

F_TITLE = font(42, True)
F_SUB   = font(22)
F_KEY   = font(23, True)
F_KEYS  = font(17)
F_SHORT = font(19, True)
F_LEG   = font(21)
F_NOTE  = font(19)

board_w = 17.25 * U
board_h = (6 + FROW_GAP) * U
W = int(X0 * 2 + board_w)
H = int(Y0 + board_h + 300)
img = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(img)

# title
d.text((X0, 40), 'Rocksmith practice keys \u2014 Wooting 80HE', font=F_TITLE, fill=TEXT)
d.text((X0, 100), 'RSMods keybinds from RSMods.ini. Everything works live inside a song, one key each, no Ctrl.',
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
        ty = py0 + 36
        if primary:
            d.multiline_text((px0 + 9, ty), primary, font=F_SHORT, fill=ink, spacing=1)
            ty += 24 * (primary.count('\n') + 1) + 5
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
for gname in ('loop', 'speed', 'rewind', 'amp', 'mod', 'game'):
    col, txt = GROUPS[gname]
    d.rounded_rectangle((lx, ly + 4, lx + 26, ly + 26), radius=6, fill=col)
    d.text((lx + 38, ly), txt, font=F_LEG, fill=TEXT)
    ly += 32

# notes, right of the legend - every key name comes from the ini
ls, le, lc = name('LoopStartKey'), name('LoopEndKey'), name('LoopClearKey')
su, sd = name('RRSpeedKey'), name('RRSpeedDownKey')
pa, rw, fw = name('PauseSongKey'), name('RewindKey'), name('ForwardKey')
amp = name('ToggleAmpSourceKey')
nx = X0 + 520
ny = Y0 + board_h + 50
notes = [
    'Workflow:  %s and %s around a few bars  ->  tap %s to slow it down  ->  work it  ->  tap %s past 100%%' % (ls, le, sd, su),
    'so real tempo feels easy afterwards  ->  %s clears the loop.' % lc,
    '%s pauses the song in place, no menu. While paused, %s / %s move the resume point (shown top-centre); %s resumes there.' % (pa, rw, fw, pa),
    'Loop and speed keys work in Learn A Song, Non-Stop Play and Riff Repeater; pause / scrub only while a song is playing.',
    'Tunables in RSMods.ini:  RewindBy / ForwardBy = %d / %d ms,  RRSpeedInterval = %d %%,  LoopingLeadUp = %d ms run-in before the loop.' % (rew_ms, fwd_ms, step, lead_ms),
    '%s  mutes the game\'s guitar tone only - the backing track keeps playing. "PEDAL ONLY" shows top-left while muted.' % amp,
    'Top-right overlay while playing:  song timer  /  accuracy %  /  "12 in a row, best 37" streak.',
    'Ctrl + %s or %s still clears the loop and Ctrl + %s still slows down, for muscle memory.' % (ls, le, su),
]
if off_board:
    notes.append('Not on this keyboard:  ' + ',  '.join('%s = %s' % (lab, txt) for lab, txt in off_board))
for t in notes:
    d.text((nx, ny), t, font=F_NOTE, fill=TEXT_DIM)
    ny += 30

img.save(args.out)
print('wrote', args.out, img.size, 'from', args.ini)
