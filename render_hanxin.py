"""千古人物志 · 第贰拾肆集 · 韩信 (约前231–前196)
Look: 靛青 + 汉旗赤, 点将台 (stepped platform) corner borders, a 虎符 (tiger tally) chapter card: the two halves slide
together a little more each chapter, and split again at the end.
Set pieces: 8-beat 登坛拜将, custom 8-beat scene 'beishui' (背水一战: 2000 riders swap the flags), 6-beat 潍水囊沙,
8-beat 垓下合围, 6-beat 长乐钟室.
Years are stored negative (BC); epkit prints 公元前.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_xiangyu as Xy         # engine + helpers (previous episode)
import render_long as L
import render_gufeng as G
import render_story as S
import render_full as F
import epkit
from render_gufeng import (W, H, FPS, bt, INK, ZHU, ZHE, BRUSH, SERIF, WILD, font, clamp, lerp, ease_out, ease_expo,
                           cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import (Art, person, horse, carriage, palace, flames, waves, boat, crow, arrow, flag, ground,
                          sun, walk_x, ellipse_pts, GROUND)
from render_full import chars_in, type_in, beat_fx
from render_long import C, rider, city_wall, note_in, stage, DIM, P
from render_wangyangming import desk, scroll, lamp, sitter
from render_songtaizu import tent
from render_quyuan import river
from render_kongzi import bundle

F.RIPPLE = False
INDIGO = (44, 58, 108)              # 靛青
HANRED = (210, 62, 44)              # 汉旗赤
S.LAYERS.append(('indigo2', INDIGO, 0.88, 1.0))
S.LAYERS.append(('hanred', HANRED, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='兵', life='信', court='将', night='夜', war='戰', empire='汉', works='谋', fate='符', death='钟', end='兵')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire', 'works'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['war']['sun'] = (HANRED, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (INDIGO, 220, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['end']['sun'] = (HANRED, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

GRID = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(GRID)
for _k in range(9):
    _x = 80 + _k * 115
    _d.line((_x, 1380, _x - 40 + _k * 10, 1500), fill=INDIGO + (26,), width=2)
for _y in (1400, 1440, 1480):
    _d.line((60, _y, W - 60, _y), fill=INDIGO + (26,), width=2)
MTN_COL = {'night': (32, 36, 50), 'death': (58, 58, 64), 'war': (104, 56, 46), 'empire': (64, 74, 104)}
def draw_background(t, theme):
    """沙盘: ridges over a faint sand-table grid (the general's map table)."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(180, 182, 192), (134, 140, 160), MTN_COL.get(theme, (90, 98, 124))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 7 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.9))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(GRID)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """点将台: three receding steps in each corner, a tiny red pennant on top."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = INDIGO + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=col, width=3); d.line((x, y, x, y + sy * 180), fill=col, width=3)
        for k in range(3):
            a = 70 - k * 20
            d.rectangle((min(x + sx * 10, x + sx * a), min(y + sy * (10 + k * 14), y + sy * (22 + k * 14)),
                         max(x + sx * 10, x + sx * a), max(y + sy * (10 + k * 14), y + sy * (22 + k * 14))), fill=col)
        px, py = x + sx * 24, y + sy * 64
        d.line((px, py, px, py + sy * 40), fill=col, width=3)
        d.polygon([(px, py + sy * 40), (px + sx * 22, py + sy * 34), (px, py + sy * 28)], fill=HANRED + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def han(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, armour=False, **kw):
    """韩信: slim figure, long sword always at the hip; as a general a short cape and a crested 冠."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.05 * h, y - 1.02 * h, x + 0.05 * h, y - 0.94 * h), fill=255)
        d.line((x, y - 1.02 * h, x - dir * 0.08 * h, y - 1.1 * h), fill=255, width=max(2, int(0.02 * h)))
        d.line((x - dir * 0.22 * h, y - 0.18 * h, x + dir * 0.12 * h, y - 0.52 * h), fill=255, width=max(2, int(0.016 * h)))
        if armour:
            A.d['hanred'].polygon([(x - dir * 0.04 * h, y - 0.8 * h), (x - dir * 0.26 * h, y - 0.3 * h), (x - dir * 0.08 * h, y - 0.34 * h)], fill=255)
    return hand

def _tiger_mask(s):
    """side-view crouching tiger silhouette (L image, 2s x 1.2s), head to the right."""
    w, h = int(2.4 * s), int(1.3 * s)
    m = Image.new('L', (w, h), 0); d = ImageDraw.Draw(m)
    ox, oy = 0.2 * s, 0.15 * s
    def T(u, v): return (ox + u * s, oy + v * s)
    d.ellipse([T(0.1, 0.35), T(1.55, 0.85)], fill=255)
    d.ellipse([T(1.35, 0.18), T(1.9, 0.68)], fill=255)
    d.polygon([T(1.42, 0.28), T(1.48, 0.08), T(1.58, 0.24)], fill=255)
    d.polygon([T(1.66, 0.22), T(1.74, 0.04), T(1.82, 0.24)], fill=255)
    d.polygon([T(1.8, 0.45), T(2.02, 0.5), T(1.84, 0.62)], fill=255)
    for lx in (0.25, 0.5, 1.15, 1.4):
        d.polygon([T(lx, 0.7), T(lx + 0.16, 0.7), T(lx + 0.2, 1.02), T(lx - 0.02, 1.02)], fill=255)
    d.line([T(0.15, 0.55), T(-0.1, 0.45), T(-0.15, 0.2), T(0.02, 0.12)], fill=255, width=max(4, int(0.08 * s)))
    for k in range(6):
        x0 = 0.35 + k * 0.18
        d.line([T(x0, 0.4), T(x0 + 0.05, 0.62)], fill=0, width=max(3, int(0.04 * s)))
    d.ellipse([T(1.66, 0.34), T(1.74, 0.42)], fill=0)
    return m

_TIGER = {}
def tiger_tally(A, cx, cy, s, gap, t, p=1.0):
    """虎符: a bronze crouching tiger split lengthwise into two halves separated by `gap`."""
    q = ease_out(p)
    if q < 0.05: return
    key = int(s * q)
    if key not in _TIGER: _TIGER[key] = _tiger_mask(key)
    m = _TIGER[key]
    w, h = m.size
    half = w // 2
    left, right = m.crop((0, 0, half, h)), m.crop((half, 0, w, h))
    x0 = int(cx - w / 2 - gap / 2); y0 = int(cy - h / 2)
    A.im['indigo2'].paste(255, (x0, y0), left)
    A.im['gold'].paste(255, (x0 + half + int(gap), y0), right)
    if gap > 4:
        for k in range(6):
            yy = y0 + h * 0.25 + k * h * 0.1
            A.d['ink'].line((x0 + half, yy, x0 + half + gap, yy), fill=60, width=2)

def platform(A, cx, base, w, steps=3, layer='indigo2', p=1.0):
    for k in range(steps):
        q = ease_out((p - k * 0.2) / 0.4)
        if q <= 0: break
        ww = w * (1 - k * 0.25)
        A.d[layer].rectangle((cx - ww / 2, base - (k + 1) * 60 * q, cx + ww / 2, base - k * 60 * q), fill=255 - k * 20)

def bell(A, x, y, s, swing=0.0, layer='ink'):
    d = A.d[layer]
    a = swing
    def R(u, v): return (x + u * math.cos(a) - v * math.sin(a), y + u * math.sin(a) + v * math.cos(a))
    d.line((x, y - 1.2 * s, x, y), fill=255, width=6)
    d.polygon([R(-0.5 * s, 0), R(0.5 * s, 0), R(0.75 * s, 1.4 * s), R(-0.75 * s, 1.4 * s)], fill=255)
    for k in range(3):
        A.d['gold'].line([R(-0.55 * s, 0.4 * s + k * 0.3 * s), R(0.55 * s, 0.4 * s + k * 0.3 * s)], fill=200, width=4)

# ================================================================ chapter card
CH = {16: 220, 48: 140, 80: 70, 112: 0, 144: 260}
def art_tally_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g1 = CH.get(kb, 140)
    g0 = g1 + 120 if kb != 144 else 0
    gap = lerp(g0, g1, ease_out(u / (1.2 * P)))
    tiger_tally(A, 540, 1020, 240, gap, t, p=u / 0.4)
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_tally_chapter)
    ink_in(cv, text_img(no, SERIF, 56, INDIGO, 'Black', bleed=False, spacing=12), W / 2, 1280, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1425, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_h_hook_crawl(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 260, dir=-1, robe=False, hat='knot', arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t * 3)), layer='mid')
    p = ease_out(u / (1.6 * P))
    han(A, lerp(200, 680, p), GROUND, 200, dir=1, kneel=True, bow=70, arm=150)

def art_h_hook_river(A, cv, t, u):
    river(A, 1340, t, rows=2, amp=5)
    ground(A, 1340, x0=60, x1=W - 60)
    for k in range(16):
        person(A, 120 + (k % 8) * 110, 1340 - (k // 8) * 50, 100, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='indigo2' if k // 8 else 'ink')
    for k in range(int(clamp(u / (1.6 * P)) * 8)):
        rider(A, 1000 - k * 60, 1100, 80, -1, t * 10 + k, layer='mid', spear=True)

def art_h_hook_more(A, cv, t, u):
    ground(A, GROUND)
    n = min(80, int(4 * 2 ** (u / (0.4 * P))))
    for i in range(n):
        row = i // 16; col = i % 16
        person(A, 80 + col * 58, GROUND - row * 40, 70 - row * 4, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink' if row < 2 else 'mid')

def art_h_hook_bow(A, cv, t, u):
    ground(A, GROUND)
    p = ease_out(u / (1.4 * P))
    A.d['ink'].arc((360, 880, 720, 1240), 100, 260, fill=255, width=12)
    A.d['ink'].line((540 - 180 * math.cos(math.radians(80)) + 0, 880 + 180 - 180 * math.sin(math.radians(80)), 540 - 180 * math.cos(math.radians(80)), 1240 - 180 + 180 * math.sin(math.radians(80))), fill=200, width=3)
    A.d['mid'].rectangle((300, GROUND - 40 - 40 * (1 - p), 780, GROUND - 40 * (1 - p)), fill=230)
    for k in range(3):
        crow(A, 760 + k * 60, lerp(1000, 760, p) - k * 30, 34, t * 6 + k)

# ================================================================ 第一回 胯下之辱
def art_h_youth(A, cv, t, u):
    city_wall(A, 520, 1020, 1100, gate_x=760, label='淮阴', layer='mid')
    ground(A, GROUND)
    han(A, 320, GROUND, 220, dir=1, arm=-8)
    for k in range(3):
        person(A, 600 + k * 90, GROUND, 160, dir=-1, robe=True, hat='knot', arm=lerp(40, 130, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('寄食', 54, INK), 260, 900, t, t - u + P, rot=-5)

def art_h_washerwoman(A, cv, t, u):
    river(A, 1260, t, rows=2, amp=4, speed=0.8)
    ground(A, 1260, x0=60, x1=W - 60)
    sitter(A, 280, 1260, 180, dir=1)
    A.d['ink'].line((330, 1170, 560, 1080), fill=255, width=4)
    A.d['ink'].line((560, 1080, 570, 1290), fill=160, width=2)
    person(A, 760, 1260, 180, dir=-1, robe=True, hat='knot', female=True, bow=20, arm=lerp(40, 90, ease_out((u - P) / 0.5)), layer='ink')
    A.d['mid'].chord((620, 1180, 700, 1230), 0, 180, fill=255)
    A.flush(cv)
    stamp(cv, seal('漂母', 54), 860, 900, t, t - u + 0.4, rot=6)

def art_h_crotch(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        person(A, 160 + k * 60, GROUND, 140, dir=1, robe=False, hat='knot', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 6 + k)), layer='mid')
    person(A, 620, GROUND, 270, dir=-1, robe=False, hat='knot', arm=lerp(20, 70, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.d['ink'].rectangle((700, GROUND - 200, 760, GROUND - 120), fill=255)
    ph = u / P
    if ph < 1.5:
        han(A, 420, GROUND, 220, dir=1, arm=-8)
    else:
        han(A, lerp(430, 760, ease_out((ph - 1.5) / 2)), GROUND, 220, dir=1, kneel=True, bow=75, arm=160)
    A.flush(cv)
    paste(cv, text_img('孰视之 俯出胯下', SERIF, 46, INDIGO, 'Black', bleed=False, spacing=6), W / 2, 880, 1, clamp((u - 1.5 * P) / 0.3))

def art_h_join(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        person(A, 500 + k * 80, GROUND, 150, dir=1, robe=False, hat='helmet', spear=True, ph=t * 5 + k, arm=40, layer='mid')
    flag(A, 960, GROUND, 360, t, w=90, layer='red')
    han(A, lerp(-80, 380, ease_out(u / (2 * P))), GROUND, 210, dir=1, ph=t * 5, arm=10)
    A.flush(cv)
    stamp(cv, seal('项梁', 54, INK), 860, 860, t, t - u + P, rot=6)

def art_h_ignored(A, cv, t, u):
    tent(A, 540, GROUND, 620, 420, layer='mid')
    ground(A, GROUND)
    Xy.xiang(A, 720, GROUND, 260, dir=-1, ji=True, arm=40)
    han(A, 340, GROUND, 210, dir=1, arm=lerp(30, 100, 0.5 + 0.5 * math.sin(t * 4)))
    scroll(A, 500, 1000, 160, 80, u / 0.5)
    A.flush(cv)
    if u > 1.5 * P:
        A2 = Art(); A2.d['red'].line((420, 960, 580, 1040), fill=255, width=10); A2.flush(cv)
    stamp(cv, seal('不用', 56, INK), 860, 860, t, t - u + 1.6 * P, rot=6)

def art_h_to_han(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 160, GROUND), (x, GROUND - 380 - 80 * (k % 2)), (x + 160, GROUND)], fill=200)
    ground(A, GROUND)
    pts = [(x, GROUND - 120 - 60 * math.sin(x / 200)) for x in range(80, W - 79, 20)]
    A.d['ujin'].line(pts, fill=230, width=8)
    for i in range(0, len(pts), 3):
        A.d['ink'].line((pts[i][0], pts[i][1], pts[i][0], pts[i][1] + 40), fill=200, width=3)
    i = min(len(pts) - 1, int(clamp(u / (3 * P)) * (len(pts) - 1)))
    han(A, pts[i][0], pts[i][1], 120, dir=1, ph=t * 5, arm=10)
    A.flush(cv)
    stamp(cv, seal('汉中', 54), 860, 880, t, t - u + P, rot=6)

def art_h_spared(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        person(A, 160 + k * 60, GROUND, 120, dir=1, robe=False, hat='knot', kneel=True, bow=10, fall=-80 if k < 3 else 0, arm=-8, layer='mid')
    han(A, 480, GROUND, 200, dir=1, kneel=True, bow=0, arm=-8)
    person(A, 640, GROUND, 230, dir=-1, robe=False, hat='helmet', sword=lerp(170, 120, ease_out((u - P) / 0.4)), arm=lerp(170, 60, ease_out((u - P) / 0.4)), layer='ink')
    person(A, 880, GROUND, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 110, ease_out(u / 0.5)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('夏侯婴', 46), 880, 880, t, t - u + 0.4, rot=6)

def art_h_leave_again(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    A.d['wash'].ellipse((760, 680, 860, 780), fill=255)
    ground(A, GROUND)
    x = lerp(400, 1100, ease_out(u / (1.6 * P)))
    horse(A, x, GROUND, 160, dir=1, ph=t * 8, layer='ink')
    han(A, x - 10, GROUND - 120, 150, dir=1, arm=20)

# ================================================================ 第二回 登坛拜将
def art_h_moon_chase(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 41) % 920; y = 640 + (k * 47) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    A.d['wash'].ellipse((470, 690, 610, 830), fill=255)
    river(A, 1300, t, rows=2, amp=4)
    ground(A, 1300, x0=60, x1=W - 60)
    horse(A, lerp(860, 900, ease_out(u / P)), 1300, 140, dir=-1, ph=0, moving=False, layer='ink')
    han(A, 760, 1300, 180, dir=1, arm=-8)
    x = lerp(-120, 520, ease_out(u / (2.5 * P)))
    horse(A, x, 1300, 150, dir=1, ph=t * 10, moving=u < 2.5 * P, layer='ink')
    person(A, x - 10, 1300 - 115, 140, dir=1, robe=True, hat='none', arm=lerp(40, 160, ease_out((u - 2.5 * P) / 0.3)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('萧何', 54), 260, 900, t, t - u + 0.4, rot=-5)

def art_h_platform(A, cv, t, u):
    """8-beat set piece: 登坛拜将 — the altar rises, banners fill in, the whole army watches; the king hands up the 斧钺."""
    ph = u / P
    platform(A, 540, GROUND, 560, steps=3, p=ph / 2.5)
    for k in range(int(clamp((ph - 1) / 2) * 8)):
        x = 140 + k * 115
        flag(A, x, GROUND, 380 + 30 * (k % 2), t, w=70, layer='hanred' if k % 2 else 'red')
    ground(A, GROUND)
    top = GROUND - 180 * ease_out(ph / 2.5)
    if ph > 2.5:
        han(A, lerp(380, 480, ease_out((ph - 2.5) / 1.5)), top, 200, dir=1, armour=ph > 5.5, kneel=3.5 < ph < 5.5, bow=40 if 3.5 < ph < 5.5 else 0, arm=lerp(-8, 90, ease_out((ph - 4) / 0.6)))
        person(A, 640, top, 210, dir=-1, robe=True, hat='crown', arm=lerp(20, 100, ease_out((ph - 3.5) / 0.6)), layer='ink')
    for k in range(18):
        person(A, 100 + (k % 9) * 110, GROUND + 6 - (k // 9) * 30, 80, dir=1 if (k % 9) < 4 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    A.flush(cv)
    if ph >= 4:
        stamp(cv, seal('大将', 64), 540, 860, t, t - u + 4 * P, rot=0)
    if ph >= 6.5:
        paste(cv, text_img('一军皆惊', SERIF, 52, HANRED, 'Black', bleed=False, spacing=10), W / 2, 1448, 1, clamp((ph - 6.5) / 0.3))

def art_h_hanzhong_talk(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='indigo2')
    person(A, 760, GROUND, 240, dir=-1, robe=True, hat='crown', arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    han(A, 320, GROUND, 230, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)))
    A.d['wash'].rectangle((400, GROUND - 120, 680, GROUND - 74), fill=255)
    A.flush(cv)
    type_in(cv, text_img('匹夫之勇', SERIF, 50, HANRED, 'Black', bleed=False, spacing=6), 330, 880, t, t - u + 0.4, 0.4)
    type_in(cv, text_img('妇人之仁', SERIF, 50, INDIGO, 'Black', bleed=False, spacing=6), 750, 880, t, t - u + 1.4 * P, 0.4)

def art_h_chencang(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 170, GROUND), (x, GROUND - 440 - 60 * (k % 2)), (x + 170, GROUND)], fill=200)
    pts = [(x, 1060 + 30 * math.sin(x / 120)) for x in range(80, W - 79, 20)]
    A.d['ujin'].line(pts, fill=200, width=8)
    for k in range(4):
        x = 200 + k * 200
        person(A, x, 1060 + 30 * math.sin(x / 120), 70, dir=1, robe=False, hat='knot', arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 6 + k)), layer='ink')
    ground(A, GROUND)
    for k in range(8):
        x = lerp(-200, 900, ((u / (4 * P)) + k * 0.06) % 1.2)
        person(A, x, GROUND, 90, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, arm=40, layer='indigo2')
    A.flush(cv)
    stamp(cv, seal('陈仓', 56), 860, 880, t, t - u + P, rot=6)

def art_h_regroup(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (3 * P)) * 24) + 1
    for i in range(n):
        x = lerp(-60 + (i * 97) % 1200, 200 + (i % 8) * 90, ease_out(u / (2 * P)))
        y = GROUND - (i // 8) * 40
        person(A, x, y, 90, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink' if i // 8 == 0 else 'mid')
    han(A, 900, GROUND, 220, dir=-1, armour=True, arm=lerp(20, 140, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('京索之间', 44), 860, 880, t, t - u + P, rot=6)

def art_h_jars(A, cv, t, u):
    """6-beat: 木罂渡河 — while boats feint at 临晋, troops float across on wooden jars upstream and take 安邑."""
    ph = u / P
    river(A, 1180, t, rows=4, amp=6, speed=1.6)
    for k in range(5):
        boat(A, 760 + k * 50, 1240 + (k % 2) * 40, 60, t, sail=True)
    for k in range(int(clamp(ph / 4) * 9)):
        x = lerp(160, 520, clamp((ph - k * 0.3) / 3)); y = 1220 + (k % 3) * 50
        A.d['ujin'].ellipse((x - 26, y - 20, x + 26, y + 20), fill=255)
        person(A, x, y - 10, 60, dir=1, robe=False, hat='helmet', arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('疑兵', 46, INK), 860, 1060, t, t - u + 0.5, rot=6)
    if ph >= 4.5:
        stamp(cv, seal('擒魏豹', 54), 300, 960, t, t - u + 4.5 * P, rot=-5)

# ================================================================ 第三回 兵仙神帅
def scene_beishui(cv, t, c, k):
    """8-beat custom scene: 背水一战 (井陉) — a top-down sand table: 汉 army with a river at its back, 赵 camp opposite;
    2000 riders circle round, pull down 赵 flags and plant 汉 red ones; 赵 army breaks between them."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['wash'].rounded_rectangle((100, 740, 980, 1420), radius=24, fill=180)
    A.d['ocean'].polygon([(100, 1300), (980, 1260), (980, 1420), (100, 1420)], fill=180)
    for k in range(6):
        x = 220 + k * 120
        A.d['indigo2'].rectangle((x - 30, 1220, x + 30, 1250), fill=255)
    A.d['mid'].rectangle((360, 800, 720, 920), fill=230)
    swap = clamp((ph - 4) / 1.5)
    for k in range(5):
        x = 390 + k * 75
        col = 'hanred' if k < int(swap * 5 + 0.01) else 'ink'
        A.d['ink'].line((x, 860, x, 790), fill=255, width=4)
        A.d[col].polygon([(x, 790), (x + 30, 798), (x, 812)], fill=255)
    zhao_y = lerp(900, 1150, ease_out(ph / 3)) if ph < 5.5 else lerp(1150, 980, ease_out((ph - 5.5) / 1.5))
    zhao_x = 540 if ph < 5.5 else 540 + 300 * ease_out((ph - 5.5) / 1.5)
    for k in range(8):
        A.d['ink'].rectangle((zhao_x - 160 + k * 40, zhao_y, zhao_x - 140 + k * 40, zhao_y + 20), fill=255)
    rp = clamp(ph / 4)
    path = [(lerp(200, 140, f), lerp(1200, 980, f)) for f in np.linspace(0, 1, 8)] + [(lerp(140, 360, f), lerp(980, 860, f)) for f in np.linspace(0, 1, 8)]
    m = max(2, int(len(path) * rp))
    A.d['hanred'].line(path[:m], fill=200, width=8)
    A.flush(cv)
    stamp(cv, seal('赵营', 40, INK), 540, 760, t, s0 + 0.2)
    stamp(cv, seal('背水', 40), 860, 1340, t, s0 + 0.5)
    if ph >= 1:
        stamp(cv, seal('二千骑', 38), 140, 960, t, s0 + P)
    fx = Art()
    chars_in(cv, fx, '背水一战', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=83)
    fx.flush(cv)
    lab = '列阵于水边 赵军大笑' if ph < 3 else ('拔赵帜 立汉赤帜' if ph < 5.5 else '赵军大乱 斩陈馀')
    paste(cv, text_img(lab, SERIF, 46, HANRED if ph >= 3 else INDIGO, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('公元前二〇四年 · 井陉', SERIF, 42, INDIGO, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_h_teacher(A, cv, t, u):
    tent(A, 540, GROUND, 600, 400, layer='mid')
    ground(A, GROUND)
    person(A, 700, GROUND, 220, dir=-1, robe=True, hat='knot', arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    han(A, 380, GROUND, 210, dir=1, kneel=True, bow=30, arm=90)
    for k in range(3):
        A.d['ink'].line((640 + k * 20, GROUND - 120, 660 + k * 20, GROUND - 60), fill=int(200 * (1 - ease_out(u / P))), width=4)
    A.flush(cv)
    stamp(cv, seal('李左车', 46), 860, 880, t, t - u + 0.4, rot=6)

def art_h_letter(A, cv, t, u):
    city_wall(A, 560, 1020, 1100, gate_x=790, label='燕', layer='mid', open_=ease_out((u - 2 * P) / P))
    ground(A, GROUND)
    x = lerp(-100, 640, ease_out(u / (2 * P)))
    rider(A, x, GROUND, 140, 1, t * 11, layer='ink', moving=u < 2 * P)
    A.d['wash'].rectangle((x + 40, GROUND - 230, x + 90, GROUND - 200), fill=255)
    if u > 2.5 * P:
        flag(A, 900, 1100, 200, t, w=60, layer='hanred')
    A.flush(cv)
    stamp(cv, seal('传檄', 54), 300, 900, t, t - u + 0.5, rot=-5)

def art_h_weishui(A, cv, t, u):
    """6-beat set piece: 潍水 — sandbags dam the river; 龙且 crosses; the bags are pulled; the flood splits his army."""
    ph = u / P
    flood = ease_out((ph - 3) / 1)
    lvl = lerp(80, 30, clamp(ph / 1.5)) if ph < 3 else lerp(30, 160, flood)
    A.d['ocean'].rectangle((400, GROUND - lvl, 680, GROUND), fill=170)
    waves(A, GROUND - lvl, t, rows=2, amp=4, x0=400, x1=680, speed=3 if ph > 3 else 1)
    if ph < 3:
        for k in range(6):
            A.d['ujin'].ellipse((400 + k * 46, 1080 - (k % 2) * 10, 450 + k * 46, 1110), fill=255)
    ground(A, GROUND, x0=60, x1=400)
    ground(A, GROUND, x0=680, x1=W - 60)
    for k in range(10):
        if ph < 1.5:
            x = 820 + (k % 5) * 40
        else:
            x = lerp(820 + (k % 5) * 40, 300 + (k % 5) * 40, ease_out((ph - 1.5) / 1.5)) if k < 5 else 820 + (k % 5) * 40
        fallen = ph > 3 and 400 < x < 680
        person(A, x, GROUND - (k // 5) * 40, 90, dir=-1, robe=False, hat='helmet', spear=True, fall=-80 if fallen else 0, arm=40, layer='mid')
    for k in range(6):
        person(A, 120 + k * 45, GROUND, 100, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='indigo2')
    A.flush(cv)
    stamp(cv, seal('龙且', 50, INK), 860, 880, t, t - u + 0.4, rot=6)
    lab = '夜囊沙 壅水上流' if ph < 3 else '决壅 水大至'
    paste(cv, text_img(lab, SERIF, 48, INDIGO if ph < 3 else HANRED, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, 1)

def art_h_false_king(A, cv, t, u):
    tent(A, 540, GROUND, 640, 420, layer='mid')
    ground(A, GROUND)
    person(A, 420, GROUND, 240, dir=1, robe=True, hat='crown', arm=lerp(30, 150, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    person(A, 560, GROUND, 200, dir=-1, robe=True, hat='knot', arm=-8, layer='ink')
    A.d['red'].ellipse((470, GROUND - 14, 520, GROUND + 4), fill=int(255 * ease_out((u - P) / 0.3)))
    scroll(A, 780, 960, 220, 100, u / 0.5)
    A.flush(cv)
    if u > 2 * P:
        ink_in(cv, text_img('真王', BRUSH, 80, HANRED), 780, 960, t, t - u + 2 * P, dur=0.3, settle=1.3)
    else:
        ink_in(cv, text_img('假王', BRUSH, 80, INK), 780, 960, t, t - u + 0.5, dur=0.3)
    stamp(cv, seal('张良', 46, INK), 300, 880, t, t - u + P, rot=-5)

def art_h_kuaitong(A, cv, t, u):
    ground(A, GROUND)
    han(A, 300, GROUND, 230, dir=1, arm=lerp(-8, 30, 0.5 + 0.5 * math.sin(t)))
    person(A, 700, GROUND, 210, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    p = ease_out(u / (1.5 * P))
    for i in range(3):
        a = -math.pi / 2 + i * 2 * math.pi / 3
        A.d['mid' if i else 'indigo2'].pieslice((540 - 140, 860 - 140, 540 + 140, 860 + 140), math.degrees(a) + 4, math.degrees(a) + 120 * p - 4, fill=220)
    A.flush(cv)
    for i, nm in enumerate(('齐', '汉', '楚')):
        a = -math.pi / 2 + i * 2 * math.pi / 3 + math.pi / 3
        paste(cv, text_img(nm, BRUSH, 60, INK), 540 + 80 * math.cos(a), 860 + 80 * math.sin(a), 1, p)
    stamp(cv, seal('蒯通', 46, INK), 860, 1060, t, t - u + 0.4, rot=6)

# ================================================================ 第四回 十面埋伏
def art_h_gaixia(A, cv, t, u):
    """8-beat set piece: 垓下 — the commander's flags; ring after ring of troops closes on the 楚 camp at the centre."""
    ph = u / P
    cx, cy = 540, 1100
    A.d['mid'].ellipse((cx - 70, cy - 40, cx + 70, cy + 40), fill=220)
    rings = min(5, int(ph / 1.3) + 1)
    for r in range(rings):
        R = 420 - r * 60
        q = clamp((ph - r * 1.3) / 1)
        n = 16 + r * 2
        for k in range(int(n * q)):
            a = k * 2 * math.pi / n + r * 0.2
            x, y = cx + R * math.cos(a), cy + R * 0.55 * math.sin(a)
            A.d['indigo2' if r % 2 else 'ink'].rectangle((x - 9, y - 9, x + 9, y + 9), fill=255)
    han(A, 900, 1400, 170, dir=-1, armour=True, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 2)))
    flag(A, 980, 1400, 260, t, w=60, layer='hanred')
    A.flush(cv)
    stamp(cv, seal('楚', 50, INK), cx, cy, t, t - u + 0.3)
    paste(cv, text_img(f'合围第{cn_num(rings)}重', SERIF, 48, HANRED, 'Black', bleed=False, spacing=6), W / 2, 820, 1, 1)

def art_h_seize(A, cv, t, u):
    tent(A, 540, GROUND, 560, 400, layer='mid')
    ground(A, GROUND)
    han(A, 640, GROUND, 220, dir=-1, kneel=True, bow=20, arm=60)
    x = lerp(-120, 360, ease_out(u / (1.5 * P)))
    horse(A, x, GROUND, 150, dir=1, ph=t * 9, moving=u < 1.5 * P, layer='ink')
    person(A, x - 10, GROUND - 115, 150, dir=1, robe=True, hat='crown', arm=lerp(20, 120, ease_out((u - 1.5 * P) / 0.4)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('夺其军', 50), 860, 880, t, t - u + 1.8 * P, rot=6)

def art_h_reward(A, cv, t, u):
    palace(A, 540, 1160, 480, layer='indigo2')
    ground(A, GROUND)
    han(A, 540, GROUND - 20, 220, dir=1, arm=40)
    person(A, 300, GROUND, 170, dir=1, robe=True, hat='knot', female=True, bow=20, arm=60, layer='ink')
    for k in range(int(clamp(u / P) * 4)):
        A.d['gold'].rectangle((360 + k * 30, GROUND - 40 - k * 6, 400 + k * 30, GROUND - k * 6), fill=255)
    person(A, 800, GROUND, 180, dir=-1, robe=False, hat='helmet', kneel=True, bow=50, arm=110, layer='mid')
    A.flush(cv)
    stamp(cv, seal('千金', 54), 300, 880, t, t - u + P, rot=-5)
    stamp(cv, seal('中尉', 50, INK), 800, 880, t, t - u + 2 * P, rot=6)

def art_h_yunmeng(A, cv, t, u):
    A.d['ocean'].polygon([(60, 1200), (W - 60, 1180), (W - 60, 1300), (60, 1320)], fill=120)
    ground(A, GROUND)
    carriage(A, 760, GROUND, 140, dir=-1, wheel=0, ph=0, moving=False, layer='ink')
    han(A, 380, GROUND, 220, dir=1, kneel=True, bow=30, arm=90)
    for k in range(2):
        person(A, 260 + k * 260, GROUND, 200, dir=1 if k == 0 else -1, robe=False, hat='helmet', arm=lerp(40, 120, ease_out((u - P) / 0.4)), layer='ink')
    A.d['ujin'].line((260, GROUND - 120, 520, GROUND - 120), fill=255 if u > P else 0, width=6)
    A.flush(cv)
    stamp(cv, seal('伪游云梦', 44), 860, 880, t, t - u + 0.4, rot=6)

def art_h_marquis(A, cv, t, u):
    for k in range(40):
        q = (t * 0.3 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=200)
    A.d['mid'].rectangle((300, 980, 780, GROUND), fill=200)
    A.d['ink'].polygon([(260, 980), (820, 980), (540, 880)], fill=255)
    A.d['wash'].rectangle((480, 1200, 600, GROUND), fill=255)
    ground(A, GROUND)
    sitter(A, 540, GROUND, 120, dir=1, bow=20)
    A.flush(cv)
    stamp(cv, seal('淮阴侯', 50, INK), 860, 900, t, t - u + P, rot=6)

def art_h_more_better(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 240, dir=-1, robe=True, hat='crown', arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    han(A, 320, GROUND, 230, dir=1, arm=lerp(40, 130, 0.5 + 0.5 * math.sin(t * 3)))
    n = min(64, int(2 * 2 ** (u / (0.5 * P))))
    for i in range(n):
        x = 440 + (i % 8) * 24; y = 1160 - (i // 8) * 24
        A.d['indigo2'].rectangle((x - 8, y - 8, x + 8, y + 8), fill=255)
    A.flush(cv)
    type_in(cv, text_img('陛下不过能将十万', SERIF, 44, INDIGO, 'Black', bleed=False, spacing=4), W / 2, 820, t, t - u + 0.3, 0.4)
    type_in(cv, text_img('臣多多而益善耳', SERIF, 48, HANRED, 'Black', bleed=False, spacing=4), W / 2, 890, t, t - u + 1.6 * P, 0.4)

def art_h_chenxi(A, cv, t, u):
    for k in range(4):
        x = 600 + k * 100
        flag(A, x, GROUND, 300, t, w=70, layer='red')
    ground(A, GROUND)
    for k in range(6):
        rider(A, 640 + (k % 3) * 120, GROUND - (k // 3) * 40, 110, -1, t * 10 + k, layer='ink', spear=True, moving=False)
    A.flush(cv)
    stamp(cv, seal('陈豨', 54, INK), 300, 900, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('代', 56), 300, 1050, t, t - u + P, rot=-5)

# ================================================================ 第五回 长乐钟室
def art_h_sick(A, cv, t, u):
    A.d['mid'].rectangle((260, 960, 820, GROUND), fill=200)
    A.d['wash'].rectangle((320, 1020, 760, GROUND - 40), fill=255)
    ground(A, GROUND)
    sitter(A, 440, GROUND - 40, 150, dir=1, bow=10)
    lamp(A, 640, GROUND - 40, 50, t, glow=0.5)
    A.flush(cv)
    stamp(cv, seal('称病', 54, INK), 860, 880, t, t - u + P, rot=6)

def art_h_summoned(A, cv, t, u):
    ground(A, GROUND)
    person(A, 700, GROUND, 230, dir=-1, robe=True, hat='none', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    han(A, 360, GROUND, 220, dir=1, arm=-8)
    A.flush(cv)
    stamp(cv, seal('萧何', 54), 760, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('陈豨已破 群臣皆贺', SERIF, 46, INDIGO, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_h_bell_room(A, cv, t, u):
    """6-beat set piece: 长乐钟室 — the bell hangs; guards close; the bell swings once and goes still."""
    ph = u / P
    A.d['ink'].rectangle((240, 820, 840, 840), fill=255)
    for sx in (260, 800):
        A.d['ink'].rectangle((sx, 840, sx + 20, GROUND), fill=255)
    sw = 0.25 * math.sin(t * 4) * math.exp(-max(0, ph - 3)) if ph > 3 else 0
    bell(A, 540, 900, 120, swing=sw)
    ground(A, GROUND)
    if ph < 3.5:
        han(A, 540, GROUND, 200, dir=1, arm=-8)
    else:
        person(A, 540, GROUND, 200, dir=1, robe=True, hat='knot', fall=-88 * ease_out((ph - 3.5) / 0.6), arm=-8, layer='ink')
    for k in range(4):
        side = -1 if k % 2 else 1
        x = 540 + side * lerp(420, 140 + (k // 2) * 70, ease_out((ph - 1) / 2))
        person(A, x, GROUND, 180, dir=-side, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    A.flush(cv)
    if ph >= 4:
        type_in(cv, text_img('吾悔不用蒯通之计', SERIF, 48, HANRED, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + 4 * P, 0.5)

def art_h_xiaohe(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 260, dir=1, robe=True, hat='none', arm=-8, layer='ink')
    A.flush(cv)
    ink_in(cv, text_img('成', BRUSH, 150, INDIGO), 300, 960, t, t - u + 0.3, dur=0.3, settle=1.3)
    ink_in(cv, text_img('败', BRUSH, 150, HANRED), 780, 960, t, t - u + 1.5 * P, dur=0.3, settle=1.3)

def art_h_biography(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360)
    sitter(A, 300, GROUND, 220, dir=1, bow=15)
    for i in range(int(clamp(u / (2 * P)) * 4) + 1):
        bundle(A, 640 + i * 80, GROUND - 60, 60, layer='indigo2')
    A.flush(cv)
    ink_in(cv, text_img('淮阴侯列传', SERIF, 48, INDIGO, 'Black', bleed=False, spacing=8), W / 2, 880, t, t - u + 0.5, dur=0.3)

def art_h_count(A, cv, t, u):
    ground(A, GROUND)
    for i in range(48):
        row = i // 12; col = i % 12
        x = 100 + col * 80; y = GROUND - row * 50
        on = i < int(clamp(u / (1.5 * P)) * 48)
        person(A, x, y, 70, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink' if on else 'mid')
    A.flush(cv)
    paste(cv, text_img('韩信点兵 多多益善', SERIF, 48, HANRED, 'Black', bleed=False, spacing=6), W / 2, 880, 1, clamp((u - 0.5 * P) / 0.3))

def art_h_legacy(A, cv, t, u):
    tiger_tally(A, 540, 1100, 260, 0, t)
    ground(A, GROUND)

def art_h_title(A, cv, t, u):
    platform(A, 540, 1460, 700, steps=3)
    han(A, 430, 1460 - 180, 560, dir=1, armour=True, arm=lerp(-5, 45, ease_out(u / (2 * P))))
    flag(A, 820, 1280, 420, t, w=120, layer='hanred')

# ================================================================ script
CHAPTERS = {16: ('第一回', '胯下之辱'), 48: ('第二回', '登坛拜将'), 80: ('第三回', '兵仙神帅'),
            112: ('第四回', '十面埋伏'), 144: ('第五回', '长乐钟室')}

CARDS = [
    C(0, 2, 'night', 'num', num='胯下之辱', line='他忍了', art=art_h_hook_crawl),
    C(2, 4, 'war', 'num', num='背水一战', line='置之死地而后生', art=art_h_hook_river),
    C(4, 6, 'empire', 'num', num='多多益善', line='兵越多越好', art=art_h_hook_more),
    C(6, 8, 'death', 'num', num='鸟尽弓藏', line='功高震主的下场', art=art_h_hook_bow),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 胯下之辱
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-231, main='淮阴少年', sub='家贫 · 常寄食于人', note='生年不详 一说', art=art_h_youth),
    C(22, 26, 'works', 'card', year=-220, main='漂母一饭', sub='城下钓鱼 · 洗衣老妇送饭数十日', note='吾必有以重报母', art=art_h_washerwoman),
    C(26, 30, 'night', 'card', year=-215, main='胯下之辱', sub='屠中少年当众羞辱', note='众辱之曰 信能死 刺我', art=art_h_crotch),
    C(30, 34, 'war', 'card', year=-209, main='仗剑从军', sub='投奔项梁', art=art_h_join),
    C(34, 38, 'court', 'card', year=-207, main='执戟郎中', sub='屡次献策 · 项羽不用', art=art_h_ignored),
    C(38, 42, 'fate', 'card', year=-206, main='亡楚归汉', sub='投奔刘邦 · 只做小官', art=art_h_to_han),
    C(42, 46, 'night', 'card', year=-206, main='刀下留人', sub='坐法当斩 · 夏侯婴救之', note='上不欲就天下乎 何为斩壮士', art=art_h_spared),
    C(46, 48, 'fate', 'card', year=-206, main='再次出走', sub='仍不被重用', art=art_h_leave_again),
    # ---- 第二回 登坛拜将
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'night', 'card', year=-206, main='月下追韩信', sub='萧何闻讯 · 连夜追赶', note='诸将易得耳 至如信者 国士无双', art=art_h_moon_chase),
    C(54, 62, 'empire', 'card', year=-206, main='登坛拜将', sub='择良日 设坛场 · 拜为大将', note='诸将皆喜 人人各自以为得大将', art=art_h_platform),
    C(62, 66, 'court', 'card', year=-206, main='汉中对', sub='一席话 · 定下东进大计', art=art_h_hanzhong_talk),
    C(66, 70, 'war', 'card', year=-206, main='暗度陈仓', sub='出故道 · 还定三秦', note='明修栈道 后世之语', art=art_h_chencang),
    C(70, 74, 'works', 'card', year=-205, main='收拢残兵', sub='彭城大败后 · 稳住阵脚', art=art_h_regroup),
    C(74, 80, 'war', 'card', year=-205, main='木罂渡河', sub='以木罂缶渡军 · 袭安邑', art=art_h_jars),
    # ---- 第三回 兵仙神帅
    C(80, 82, 'war', 'chapter'),
    C(82, 90, 'war', 'beishui', year=-204),
    C(90, 94, 'court', 'card', year=-204, main='师事左车', sub='解其缚 · 以师礼待之', note='东乡坐 西乡对 师事之', art=art_h_teacher),
    C(94, 98, 'works', 'card', year=-204, main='传檄定燕', sub='一封书信 · 燕国从风而靡', art=art_h_letter),
    C(98, 104, 'war', 'card', year=-203, main='潍水之战', sub='囊沙壅水 · 斩楚将龙且', art=art_h_weishui),
    C(104, 108, 'court', 'card', year=-203, main='请封假王', sub='刘邦大怒 · 张良蹑其足', note='大丈夫定诸侯 即为真王耳', art=art_h_false_king),
    C(108, 112, 'fate', 'card', year=-203, main='蒯通劝反', sub='三分天下 · 他不忍背汉', note='衣人之衣者怀人之忧', art=art_h_kuaitong),
    # ---- 第四回 十面埋伏
    C(112, 114, 'war', 'chapter'),
    C(114, 122, 'war', 'card', year=-202, main='垓下决战', sub='韩信将三十万 · 合围项羽', note='十面埋伏 后世曲名', art=art_h_gaixia),
    C(122, 126, 'night', 'card', year=-202, main='夺其兵权', sub='项羽刚死 · 刘邦驰入其营', art=art_h_seize),
    C(126, 130, 'empire', 'card', year=-202, main='千金报恩', sub='楚王韩信 · 千金谢漂母', note='召辱己少年 以为中尉', art=art_h_reward),
    C(130, 134, 'night', 'card', year=-201, main='云梦被擒', sub='刘邦伪游云梦 · 韩信被缚', note='狡兔死 良狗烹', art=art_h_yunmeng),
    C(134, 138, 'death', 'card', year=-201, main='贬为淮阴侯', sub='软禁长安', art=art_h_marquis),
    C(138, 142, 'court', 'card', year=-200, main='多多益善', sub='与刘邦论将', art=art_h_more_better),
    C(142, 144, 'war', 'card', year=-197, main='代地叛乱', sub='陈豨起兵于代', art=art_h_chenxi),
    # ---- 第五回 长乐钟室
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'night', 'card', year=-196, main='称病不朝', sub='一说 与陈豨暗通', art=art_h_sick),
    C(150, 154, 'court', 'card', year=-196, main='萧何诈召', sub='诓其入宫道贺', art=art_h_summoned),
    C(154, 160, 'death', 'card', year=-196, main='长乐钟室', sub='吕后斩之于钟室 · 夷三族', art=art_h_bell_room),
    C(160, 164, 'fate', 'card', year=-196, main='成败萧何', sub='成也萧何 败也萧何', note='后世俗语', art=art_h_xiaohe),
    C(164, 168, 'works', 'card', year=-91, main='淮阴侯列传', sub='司马迁为他立传', note='假令韩信学道谦让 不伐己功', art=art_h_biography),
    C(168, 170, 'end', 'card', year=-91, main='韩信点兵', sub='流传两千年', art=art_h_count),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='贰拾肆', col=INDIGO, acc=HANRED, born=-231, died=-196,
    born_lab='约前231年', died_lab='前196年', years_txt='约公元前231 — 前196',
    hook_q='从钻人胯下 到兵仙 · 他经历了什么？',
    name_line='韩信 · 淮阴人', name='韩信', seal='淮阴', title_art=art_h_title,
    q1='兵仙神帅？', q2='不懂进退？',
    end_art=art_h_legacy, end_big='国士无双', end_seal='兵仙',
    end_l1='他为汉朝打下大半江山', end_l2='却死在一口钟下',
    end_brush='鸟尽弓藏', end_ask='韩信该不该反？评论区聊聊', next='张骞'),
    scenes=dict(chapter=scene_chapter, beishui=scene_beishui))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
