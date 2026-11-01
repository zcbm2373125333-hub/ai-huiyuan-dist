"""千古人物志 · 第贰拾叁集 · 项羽 (前232–前202)
Look: 乌金 + 虞美人红, 戟头 corner borders, a 鼎 chapter card (力能扛鼎): the cauldron is hoisted a little higher each
chapter, and in the last chapter it cracks.
Set pieces: custom 8-beat scene 'julu' (巨鹿: boats sunk, pots smashed, nine battles), 6-beat 鸿门宴,
8-beat 彭城之战, 8-beat 四面楚歌, 6-beat 乌江.
Years are stored negative (BC); epkit prints 公元前.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_quyuan as Qy          # engine + helpers (previous episode)
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
from render_wangyangming import desk, scroll, lamp, sitter, leaf
from render_songtaizu import tent
from render_quyuan import river

F.RIPPLE = False
UJIN = (92, 70, 42)                 # 乌金
POPPY = (204, 58, 70)               # 虞美人红
S.LAYERS.append(('ujin', UJIN, 0.88, 1.0))
S.LAYERS.append(('poppy', POPPY, 0.88, 1.2))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='霸', life='籍', court='楚', night='歌', war='戰', empire='霸', works='鼎', fate='骓', death='江', end='霸')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire', 'works'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['war']['sun'] = (POPPY, 240, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (UJIN, 230, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['end']['sun'] = (POPPY, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

BANNERS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(BANNERS)
for _x in (110, 200, 880, 970):
    _d.line((_x, 1470, _x, 1180), fill=UJIN + (60,), width=5)
    _d.polygon([(_x, 1180), (_x + 60, 1196), (_x + 52, 1240), (_x, 1236)], fill=POPPY + (46,))
MTN_COL = {'night': (36, 32, 36), 'death': (60, 56, 56), 'war': (104, 52, 40), 'empire': (110, 86, 54)}
def draw_background(t, theme):
    """楚地平野: wide low ridges, faded war banners at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 180, 168), (150, 132, 112), MTN_COL.get(theme, (110, 90, 70))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 7 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.95))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(BANNERS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """戟头: a halberd head (spear tip + crescent blade) pointing out of each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = UJIN + (230,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x + sx * 40, y + sy * 40, x + sx * 190, y + sy * 0), fill=col, width=4)
        d.line((x + sx * 40, y + sy * 40, x + sx * 0, y + sy * 190), fill=col, width=4)
        d.polygon([(x, y), (x + sx * 46, y + sy * 18), (x + sx * 18, y + sy * 46)], fill=col)
        d.arc((min(x + sx * 30, x + sx * 90), min(y + sy * 30, y + sy * 90), max(x + sx * 30, x + sx * 90), max(y + sy * 30, y + sy * 90)),
              0, 360, fill=POPPY + (200,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def xiang(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, ji=True, **kw):
    """项羽: armoured, helmet with a tall red plume, a 戟 (halberd) in hand, cloak."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=False, hat='helmet', layer=layer, kneel=kneel, bow=bow, **kw)
    d = A.d[layer]
    if up:
        d.polygon([(x - dir * 0.05 * h, y - 0.82 * h), (x - dir * 0.3 * h, y - 0.2 * h), (x - dir * 0.12 * h, y - 0.25 * h)], fill=255)
        A.d['poppy'].polygon([(x, y - 1.08 * h), (x - dir * 0.16 * h, y - 1.22 * h + 0.03 * h * math.sin(h)), (x - dir * 0.05 * h, y - 1.04 * h)], fill=255)
        d.rectangle((x - 0.1 * h, y - 0.62 * h, x + 0.1 * h, y - 0.56 * h), fill=255)
    if ji and up and not kw.get('sword'):
        hx, hy = hand
        d.line((hx, hy + 0.35 * h, hx + dir * 0.05 * h, hy - 0.75 * h), fill=255, width=max(3, int(0.022 * h)))
        tx, ty = hx + dir * 0.05 * h, hy - 0.75 * h
        d.polygon([(tx - 0.02 * h, ty), (tx + 0.02 * h, ty), (tx, ty - 0.12 * h)], fill=255)
        d.chord((tx - dir * 0.0 - 0.1 * h, ty - 0.02 * h, tx + 0.1 * h, ty + 0.12 * h), 90 if dir > 0 else 270, 270 if dir > 0 else 90, fill=255)
    return hand

def ding(A, cx, base, s, crack=0.0, layer='ujin'):
    """鼎: round-bellied cauldron with two upright handles and three legs."""
    d = A.d[layer]
    d.chord((cx - s, base - 1.25 * s, cx + s, base - 0.15 * s), 0, 180, fill=255)
    d.rectangle((cx - 1.02 * s, base - 0.72 * s, cx + 1.02 * s, base - 0.62 * s), fill=255)
    for sx in (-1, 1):
        d.rectangle((cx + sx * 0.6 * s - 0.08 * s, base - 0.98 * s, cx + sx * 0.6 * s + 0.08 * s, base - 0.72 * s), outline=255, width=max(3, int(0.06 * s)))
    for lx in (-0.6, 0.0, 0.6):
        d.polygon([(cx + lx * s - 0.1 * s, base - 0.3 * s), (cx + lx * s + 0.1 * s, base - 0.3 * s), (cx + lx * s + 0.06 * s, base), (cx + lx * s - 0.06 * s, base)], fill=255)
    for k in range(3):
        A.d['ink'].line((cx - 0.8 * s, base - 0.55 * s + k * 0.1 * s, cx + 0.8 * s, base - 0.55 * s + k * 0.1 * s), fill=110, width=3)
    if crack > 0:
        pts = [(cx + 0.1 * s, base - 0.72 * s), (cx - 0.05 * s, base - 0.55 * s), (cx + 0.12 * s, base - 0.42 * s), (cx - 0.02 * s, base - 0.3 * s)]
        n = max(2, int(len(pts) * crack + 0.5))
        A.d['ink'].line(pts[:n], fill=255, width=max(3, int(0.04 * s)))

def pot(A, x, y, s, broken=0.0, layer='ink'):
    if broken < 0.5:
        A.d[layer].chord((x - s, y - 1.2 * s, x + s, y + 0.2 * s), 0, 180, fill=255)
        A.d[layer].rectangle((x - 1.1 * s, y - 0.55 * s, x + 1.1 * s, y - 0.45 * s), fill=255)
    else:
        r = random.Random(int(x))
        for k in range(5):
            px, py = x + r.uniform(-1.6, 1.6) * s, y + r.uniform(-0.1, 0.1) * s
            A.d[layer].polygon([(px, py), (px + 0.4 * s, py - 0.1 * s), (px + 0.3 * s, py + 0.15 * s)], fill=255)

def yuji(A, x, y, h, dir=1, t=0.0, dance=True, layer='poppy'):
    a = lerp(40, 170, 0.5 + 0.5 * math.sin(t * 3)) if dance else 30
    hand = person(A, x, y, h, dir=dir, robe=True, hat='knot', female=True, arm=a, arm2=lerp(-20, -120, 0.5 + 0.5 * math.sin(t * 3 + 1)) if dance else None, layer=layer)
    if dance:
        hx, hy = hand
        A.d['ink'].line((hx, hy, hx + dir * 0.4 * h * math.cos(t * 3), hy - 0.4 * h * abs(math.sin(t * 3)) - 0.1 * h), fill=255, width=max(2, int(0.015 * h)))
    return hand

# ================================================================ chapter card
CH = {16: (0.15, 0.0), 48: (0.4, 0.0), 80: (0.75, 0.0), 112: (0.55, 0.0), 144: (0.0, 1.0)}
def art_ding_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    lift, crack = CH.get(kb, (0.4, 0.0))
    q = ease_out(u / (1.2 * P))
    base = 1200
    yb = base - lift * q * 220
    ding(A, 540, yb, 140, crack=crack * q)
    if lift > 0:
        xiang(A, 540, base, 230, dir=1, ji=False, arm=170, arm2=-170)
    A.d['ujin'].rectangle((300, base, 780, base + 14), fill=200)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_ding_chapter)
    ink_in(cv, text_img(no, SERIF, 56, UJIN, 'Black', bleed=False, spacing=12), W / 2, 1290, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_x_hook_30k(A, cv, t, u):
    ground(A, GROUND)
    p = ease_out(u / (1.6 * P))
    for k in range(6):
        rider(A, lerp(-200, 600, p) - k * 90, GROUND - (k % 2) * 30, 120, 1, t * 12 + k, layer='ink', spear=True)
    for k in range(14):
        person(A, 640 + (k % 7) * 60, GROUND - (k // 7) * 40, 90, dir=-1, robe=False, hat='helmet', fall=-60 * ease_out((p - 0.5 - k * 0.02) / 0.3), arm=40, layer='mid')

def art_x_hook_pots(A, cv, t, u):
    river(A, 1300, t, rows=2, amp=5)
    ground(A, 1300, x0=60, x1=W - 60)
    for k in range(5):
        pot(A, 200 + k * 170, 1290, 50, broken=1.0 if u > 0.3 + k * 0.12 else 0.0)
    boat(A, 540, 1360 + 60 * ease_out(u / (1.6 * P)), 120, t, sail=False)

def art_x_hook_farewell(A, cv, t, u):
    tent(A, 540, GROUND, 520, 360, layer='mid')
    ground(A, GROUND)
    xiang(A, 380, GROUND, 250, dir=1, ji=False, arm=40)
    yuji(A, 660, GROUND, 210, dir=-1, t=t)

def art_x_hook_wujiang(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=6)
    ground(A, 1240, x0=60, x1=560)
    xiang(A, 420, 1240, 280, dir=1, ji=False, sword=lerp(60, 150, ease_out(u / (1.4 * P))), arm=lerp(40, 160, ease_out(u / (1.4 * P))))

# ================================================================ 第一回 将门之后
def art_x_birth(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        flag(A, 260 + k * 280, GROUND, 420, t, w=110, layer='poppy' if k == 1 else 'red')
    A.d['ujin'].rectangle((380, 1180, 700, GROUND), fill=255)
    A.d['ink'].polygon([(340, 1180), (740, 1180), (540, 1060)], fill=255)
    A.flush(cv)
    stamp(cv, seal('项氏', 56), 540, 900, t, t - u + P)
    stamp(cv, seal('下相', 46, INK), 860, 1000, t, t - u + 1.5 * P, rot=6)

def art_x_grandfather(A, cv, t, u):
    for k in range(40):
        q = (t * 0.6 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['mid'].line((x, lerp(620, 1420, q), x - 8, lerp(620, 1420, q) + 30), fill=180, width=2)
    ground(A, GROUND)
    person(A, 540, GROUND, 250, dir=1, robe=False, hat='helmet', spear=True, fall=-85 * ease_out((u - P) / 0.6), arm=40, layer='ink')
    A.d['ink'].line((700, GROUND, 760, GROUND - 260), fill=255, width=6)
    A.d['red'].polygon([(760, GROUND - 260), (700, GROUND - 230), (720, GROUND - 190)], fill=255)
    A.flush(cv)
    stamp(cv, seal('项燕', 56, INK), 300, 900, t, t - u + 0.4, rot=-5)

def art_x_wanren(A, cv, t, u):
    ground(A, GROUND)
    ph = u / P
    if ph < 1.3:
        desk(A, 360, GROUND, 240)
        person(A, 560, GROUND, 160, dir=-1, robe=True, hat='knot', arm=-8, layer='ink')
        A.d['red'].line((260, GROUND - 120, 460, GROUND - 60), fill=255, width=10)
    elif ph < 2.6:
        person(A, 540, GROUND, 170, dir=1, robe=False, hat='knot', sword=lerp(30, 150, (t * 2) % 1), arm=lerp(40, 160, (t * 2) % 1), layer='ink')
        A.d['red'].line((420, 1100, 660, 1260), fill=255, width=10)
    else:
        for i in range(3):
            for j in range(6):
                A.d['mid'].rectangle((240 + j * 100, 960 + i * 80, 300 + j * 100, 1010 + i * 80), fill=220)
                A.d['ink'].polygon([(300 + j * 100, 985 + i * 80), (320 + j * 100, 975 + i * 80), (320 + j * 100, 995 + i * 80)], fill=255)
        person(A, 540, GROUND, 170, dir=1, robe=False, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    lab = '学书不成' if ph < 1.3 else ('学剑不成' if ph < 2.6 else '学万人敌')
    paste(cv, text_img(lab, SERIF, 56, ZHU if ph >= 2.6 else INK, 'Black', bleed=False, spacing=8), W / 2, 880, 1, 1)

def art_x_lift_ding(A, cv, t, u):
    p = ease_out((u - 0.5 * P) / (1.5 * P))
    ding(A, 540, GROUND - 260 * p, 150)
    xiang(A, 540, GROUND, 300, dir=1, ji=False, arm=lerp(120, 175, p), arm2=lerp(-120, -175, p))
    ground(A, GROUND)
    for k in range(4):
        person(A, 150 + k * 60, GROUND, 130, dir=1, robe=True, hat='knot', arm=lerp(20, 150, p), layer='mid')
    A.flush(cv)
    paste(cv, text_img('身长八尺余', SERIF, 48, UJIN, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((u - 2 * P) / 0.3))

def art_x_replace(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(1100, 560, ease_out(u / (2.5 * P)))
    carriage(A, x, GROUND, 160, dir=-1, wheel=u * 5, ph=t * 8, moving=u < 2.5 * P, layer='ink')
    for k in range(4):
        person(A, x + 260 + k * 80, GROUND, 130, dir=-1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, arm=40, layer='mid')
    xiang(A, 200, GROUND, 220, dir=1, ji=False, arm=lerp(20, 100, ease_out((u - 2 * P) / 0.4)))
    person(A, 100, GROUND, 230, dir=1, robe=True, hat='knot', arm=lerp(-8, 120, ease_out((u - 2.8 * P) / 0.3)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('秦始皇', 46, INK), 860, 900, t, t - u + 0.6, rot=6)

def art_x_rise(A, cv, t, u):
    palace(A, 680, GROUND, 420, layer='mid')
    ground(A, GROUND)
    xiang(A, 380, GROUND, 260, dir=1, ji=False, sword=lerp(30, 150, ease_out((u - P) / 0.3)), arm=lerp(40, 160, ease_out((u - P) / 0.3)))
    person(A, 640, GROUND, 220, dir=-1, robe=True, hat='crown', fall=-85 * ease_out((u - 1.3 * P) / 0.4), arm=20, layer='ink')
    A.flush(cv)
    stamp(cv, seal('会稽', 56), 860, 900, t, t - u + 2 * P, rot=6)

def art_x_eight_thousand(A, cv, t, u):
    river(A, 1260, t, rows=2, amp=5, speed=1.4)
    n = min(5, int(clamp(u / (2 * P)) * 5) + 1)
    for k in range(n):
        x = lerp(-200, 140 + k * 190, ease_out((u - k * 0.25 * P) / (2 * P)))
        boat(A, x, 1290 + (k % 2) * 40, 90, t + k, sail=True)
        for j in range(3):
            person(A, x - 40 + j * 40, 1270 + (k % 2) * 40, 60, dir=1, robe=False, hat='helmet', spear=True, arm=30, layer='ink')
    A.flush(cv)
    paste(cv, text_img(f'江东子弟 {n * 1600}' if n < 5 else '江东子弟八千人', SERIF, 48, UJIN, 'Black', bleed=False, spacing=4), W / 2, 880, 1, 1)

def art_x_xiangliang(A, cv, t, u):
    for k in range(40):
        q = (t * 0.7 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['mid'].line((x, lerp(620, 1420, q), x - 10, lerp(620, 1420, q) + 36), fill=200, width=2)
    tent(A, 540, GROUND, 420, 300, layer='mid')
    flames(A, 540, GROUND, 460, 200 * ease_out((u - 0.5 * P) / 0.6), t, n=6, seed=9, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('定陶', 54, INK), 860, 900, t, t - u + 0.4, rot=6)

# ================================================================ 第二回 破釜沉舟
def art_x_songyi(A, cv, t, u):
    tent(A, 540, GROUND, 600, 420, layer='mid')
    ground(A, GROUND)
    person(A, 680, GROUND, 230, dir=-1, robe=True, hat='crown', fall=-85 * ease_out((u - 1.2 * P) / 0.4), arm=20, layer='ink')
    xiang(A, 360, GROUND, 270, dir=1, ji=False, sword=lerp(30, 160, ease_out((u - P) / 0.3)), arm=lerp(40, 160, ease_out((u - P) / 0.3)))
    A.flush(cv)
    stamp(cv, seal('宋义', 54, INK), 760, 900, t, t - u + 0.4, rot=6)
    if u > 2 * P:
        stamp(cv, seal('夺兵', 56), 300, 900, t, t - u + 2 * P, rot=-5)

def scene_julu(cv, t, c, k):
    """8-beat custom scene: 巨鹿 — boats are scuttled, pots smashed, then nine clashes (one seal each) and the Qin line breaks."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    if ph < 3:
        river(A, 1240, t, rows=2, amp=5)
        ground(A, 1240, x0=60, x1=W - 60)
        for i in range(3):
            sink = ease_out((ph - 0.3 - i * 0.3) / 0.8)
            boat(A, 220 + i * 300, 1290 + 80 * sink, 100, t, sail=True)
        for i in range(5):
            pot(A, 180 + i * 180, 1236, 40, broken=1.0 if ph > 1.6 + i * 0.15 else 0.0)
        for k2 in range(3):
            A.d['wash'].rectangle((300 + k2 * 160, 1180 - (ph > 2.3) * 20, 380 + k2 * 160, 1200), fill=255 if ph < 2.3 else 0)
    else:
        n = min(9, int((ph - 3) * 1.9) + 1)
        for k2 in range(12):
            x = lerp(-100, 520, ease_out((ph - 3) / 3)) - (k2 % 6) * 80
            rider(A, x, GROUND - (k2 // 6) * 50, 110, 1, t * 12 + k2, layer='ink', spear=True)
        for k2 in range(16):
            fall = 0 if k2 >= n * 2 else -70
            person(A, 640 + (k2 % 8) * 50, GROUND - (k2 // 8) * 40, 100, dir=-1, robe=False, hat='helmet', spear=True, fall=fall, arm=40, layer='mid')
        ground(A, GROUND)
    A.flush(cv)
    fx = Art()
    if ph < 3:
        chars_in(cv, fx, '破釜沉舟', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=55)
        paste(cv, text_img('沉船 破釜 烧庐舍 · 持三日粮', SERIF, 44, UJIN, 'Black', bleed=False, spacing=4), W / 2, 575, 1, clamp(ph / 0.4))
    else:
        chars_in(cv, fx, '九战九捷', BRUSH, 150, ZHU, W / 2, 440, t, s0 + 3 * P, stagger=0.06, seed=56)
        paste(cv, text_img('以一当十 · 呼声动天', SERIF, 44, UJIN, 'Black', bleed=False, spacing=4), W / 2, 575, 1, clamp((ph - 3) / 0.4))
        n = min(9, int((ph - 3) * 1.9) + 1)
        for i in range(n):
            stamp(cv, seal(cn_num(i + 1), 34, POPPY if i == 8 else INK), 180 + i * 90, 820, t, s0 + (3 + i / 1.9) * P)
    paste(cv, text_img('公元前二〇七年 · 巨鹿', SERIF, 42, UJIN, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_x_kneel(A, cv, t, u):
    tent(A, 760, GROUND, 400, 340, layer='mid')
    ground(A, GROUND)
    xiang(A, 760, GROUND, 230, dir=-1, arm=40)
    n = int(clamp(u / (1.5 * P)) * 8) + 1
    for k in range(n):
        x = lerp(-40, 500 - k * 60, ease_out((u - k * 0.15) / P))
        person(A, x, GROUND, 140, dir=1, robe=True, hat='crown', kneel=True, bow=55, arm=110, layer='ink')
    A.flush(cv)
    paste(cv, text_img('膝行而前 莫敢仰视', SERIF, 48, POPPY, 'Black', bleed=False, spacing=6), W / 2, 880, 1, clamp((u - P) / 0.3))

def art_x_zhanghan(A, cv, t, u):
    ground(A, GROUND)
    xiang(A, 740, GROUND, 260, dir=-1, arm=40)
    person(A, 380, GROUND, 230, dir=1, robe=False, hat='helmet', kneel=True, bow=40, arm=lerp(40, 110, ease_out(u / 0.6)), layer='ink')
    for k in range(6):
        A.d['ink'].line((100 + k * 40, GROUND, 140 + k * 40, GROUND - 6), fill=255, width=6)
    A.flush(cv)
    stamp(cv, seal('章邯', 54, INK), 300, 900, t, t - u + 0.4, rot=-5)

def art_x_xinan(A, cv, t, u):
    for k in range(40):
        x = 80 + (k * 29) % 920; y = 640 + (k * 47) % 320
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    A.d['ink'].polygon([(100, GROUND), (300, 1200), (780, 1200), (980, GROUND)], fill=255)
    for k in range(int(clamp(u / (2 * P)) * 30)):
        A.d['mid'].ellipse((320 + (k % 10) * 46, 1210 + (k // 10) * 30, 340 + (k % 10) * 46, 1230 + (k // 10) * 30), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('新安', 56, INK), 860, 900, t, t - u + 0.4, rot=6)
    paste(cv, text_img('二十余万', SERIF, 56, ZHU, 'Black', bleed=False, spacing=8), W / 2, 880, 1, clamp((u - P) / 0.3))

def art_x_hongmen(A, cv, t, u):
    """6-beat set piece: 鸿门宴 — banquet in the tent; 范增 raises the jade jue three times; 项庄 dances with a sword;
    樊哙 bursts in; 刘邦 slips away."""
    ph = u / P
    tent(A, 540, GROUND, 900, 560, layer='mid')
    A.d['ujin'].rectangle((240, GROUND - 60, 840, GROUND - 46), fill=255)
    ground(A, GROUND)
    xiang(A, 300, GROUND, 230, dir=1, ji=False, arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t)))
    person(A, 200, GROUND, 200, dir=1, robe=True, hat='knot', arm=lerp(30, 160 if ph < 2 and int(ph * 3) % 2 == 0 else 60, 0.7), layer='mid')
    if ph < 4.5:
        person(A, 800, GROUND, 200, dir=-1, robe=True, hat='crown', arm=30, layer='ink')
    else:
        person(A, lerp(800, 1100, ease_out((ph - 4.5) / 1)), GROUND, 200, dir=1, robe=True, hat='crown', ph=t * 8, arm=30, layer='ink')
    if 1.5 <= ph < 4:
        sx = 540 + 80 * math.sin(t * 5)
        person(A, sx, GROUND, 210, dir=1 if math.sin(t * 5) > 0 else -1, robe=False, hat='helmet', sword=lerp(30, 170, 0.5 + 0.5 * math.sin(t * 8)), arm=lerp(60, 170, 0.5 + 0.5 * math.sin(t * 8)), layer='ink')
    if ph >= 3:
        fx_ = lerp(1100, 680, ease_out((ph - 3) / 0.6))
        person(A, fx_, GROUND, 230, dir=-1, robe=False, hat='helmet', sword=60, arm=90, layer='ink')
    A.flush(cv)
    if ph < 1.5:
        A2 = Art(); A2.d['wash'].ellipse((170, GROUND - 260, 210, GROUND - 220), outline=255, width=6); A2.flush(cv)
        paste(cv, text_img('举玦示意', SERIF, 44, UJIN, 'Black', bleed=False, spacing=4), W / 2, 880, 1, 1)
    elif ph < 3:
        paste(cv, text_img('项庄舞剑 意在沛公', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 880, 1, 1)
    elif ph < 4.5:
        paste(cv, text_img('樊哙闯帐', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 880, 1, 1)
    else:
        paste(cv, text_img('沛公如厕 一去不返', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 880, 1, 1)

# ================================================================ 第三回 西楚霸王
def art_x_burn_xianyang(A, cv, t, u):
    for k in range(3):
        palace(A, 220 + k * 320, GROUND, 300 + 60 * (k == 1), collapse=ease_out((u - P - k * 0.3) / (2 * P)), layer='mid')
    flames(A, 540, GROUND, 960, 380 * ease_out(u / (1.5 * P)), t, n=10, seed=71, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('咸阳', 56, INK), 860, 860, t, t - u + 0.4, rot=6)

def art_x_home(A, cv, t, u):
    ground(A, GROUND)
    xiang(A, 640, GROUND, 260, dir=-1, arm=40)
    for k in range(10):
        q = (t * 0.2 + k / 10) % 1
        A.d['wash'].ellipse((640 + 80 * math.sin(k), lerp(1100, 800, q) - 6, 660 + 80 * math.sin(k), lerp(1100, 800, q) + 6), fill=int(200 * (1 - q)))
    person(A, 260, GROUND, 190, dir=1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 4)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('沐猴而冠', 42, INK), 260, 900, t, t - u + 1.5 * P, rot=-5)

def art_x_fief(A, cv, t, u):
    n = min(18, int(clamp(u / (2.5 * P)) * 18) + 1)
    for i in range(n):
        a = -math.pi / 2 + i * 2 * math.pi / 18
        x, y = 540 + 330 * math.cos(a), 1060 + 260 * math.sin(a)
        A.d['mid'].ellipse((x - 34, y - 34, x + 34, y + 34), fill=200)
        A.d['ink'].line((540, 1060, x, y), fill=90, width=3)
    ding(A, 540, 1140, 90, layer='ujin')
    A.flush(cv)
    paste(cv, text_img(f'分封{cn_num(n)}王', SERIF, 50, POPPY, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, 1)

def art_x_pengcheng(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='彭城', layer='ujin', open_=1.0)
    ground(A, GROUND)
    x = lerp(-150, 540, ease_out(u / (2.5 * P)))
    horse(A, x, GROUND, 170, dir=1, ph=t * 9, moving=u < 2.5 * P, layer='ink')
    xiang(A, x - 10, GROUND - 130, 170, dir=1, arm=40)
    A.flush(cv)
    stamp(cv, seal('都彭城', 48), 860, 900, t, t - u + 2 * P, rot=6)

def art_x_pengcheng_battle(A, cv, t, u):
    """8-beat set piece: 彭城之战 — dawn raid of 三万 riders; the 汉 host collapses into the 睢水."""
    ph = u / P
    river(A, 1300, t, rows=2, amp=6, speed=2)
    ground(A, 1300, x0=60, x1=W - 60)
    sun(cv, 860, lerp(1200, 820, ease_out(ph / 4)), 120, POPPY, 140)
    n_han = 24
    for k in range(n_han):
        fallen = ph > 3 + (k % 8) * 0.25
        x = 520 + (k % 8) * 60; y = 1300 - (k // 8) * 40
        if fallen:
            x += 120 * ease_out((ph - 3 - (k % 8) * 0.25) / 1.5); y += 60 * ease_out((ph - 3 - (k % 8) * 0.25) / 1.5)
        person(A, x, y, 90, dir=-1, robe=False, hat='helmet', fall=-80 if fallen else 0, arm=40, layer='mid')
    for k in range(10):
        rider(A, lerp(-300, 600, ease_out(ph / 5)) - (k % 5) * 90, 1300 - (k // 5) * 50, 120, 1, t * 13 + k, layer='ink', spear=True)
    A.flush(cv)
    lab = '三万骑' if ph < 3 else ('五十六万' if ph < 6 else '睢水为之不流')
    paste(cv, text_img(lab, SERIF, 56, POPPY if ph >= 6 else UJIN, 'Black', bleed=False, spacing=8), W / 2, 880, 1, 1)

def art_x_xingyang(A, cv, t, u):
    for k in range(2):
        city_wall(A, 120 + k * 520, 440 + k * 520, 1140, gate_x=280 + k * 520, label='荥阳' if k == 0 else '成皋', layer='mid')
    ground(A, GROUND)
    pts = [(lerp(60, W - 60, f), 1360 + 10 * math.sin(f * 8)) for f in np.linspace(0, 1, 20)]
    A.d['ujin'].line(pts, fill=200, width=10)
    for k in range(4):
        x = (t * 160 + k * 270) % (W + 100) - 50
        person(A, x, GROUND, 90, dir=1, robe=False, hat='knot', load=True, arm=160, ph=t * 6 + k, layer='ink')
        if k == 1:
            A.d['red'].line((x - 50, GROUND - 120, x + 50, GROUND), fill=255, width=8)
    A.flush(cv)
    stamp(cv, seal('粮道被截', 44), 860, 900, t, t - u + P, rot=6)

def art_x_fanzeng(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(600, 980, ease_out((u - 0.5 * P) / (1.5 * P)))
    person(A, x, GROUND, 220, dir=1, robe=True, hat='knot', bow=20, ph=t * 3, arm=-8, layer='ink')
    A.d['ink'].line((x + 50, GROUND - 180, x + 70, GROUND), fill=255, width=6)
    xiang(A, 300, GROUND, 250, dir=1, arm=lerp(20, 90, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('范增', 54, INK), 860, 880, t, t - u + 0.4, rot=6)

# ================================================================ 第四回 楚汉相争
def art_x_honggou(A, cv, t, u):
    A.d['ocean'].polygon([(500, 820), (580, 820), (600, GROUND), (480, GROUND)], fill=150)
    ground(A, GROUND)
    for k in range(3):
        flag(A, 200 + k * 90, GROUND, 340, t, w=80, layer='poppy')
        flag(A, 720 + k * 90, GROUND, 340, t, w=80, layer='red')
    A.flush(cv)
    stamp(cv, seal('楚', 64, INK), 300, 900, t, t - u + 0.4)
    stamp(cv, seal('汉', 64), 800, 900, t, t - u + 0.8)
    paste(cv, text_img('中分天下', SERIF, 50, UJIN, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_x_betrayal(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        person(A, lerp(200, -100, ease_out(u / (3 * P))) + k * 80, GROUND, 120, dir=-1, robe=False, hat='helmet', spear=True, ph=t * 5 + k, arm=40, layer='ujin')
    for i, (nm, y) in enumerate((('刘邦', 1000), ('韩信', 1140), ('彭越', 1280))):
        x = lerp(1100, 700, ease_out((u - i * 0.4) / (2 * P)))
        for j in range(3):
            rider(A, x + j * 80, y + 80, 90, -1, t * 11 + j + i, layer='ink' if i == 0 else 'mid', spear=True)
    A.flush(cv)
    for i, (nm, y) in enumerate((('刘邦', 1000), ('韩信', 1140), ('彭越', 1280))):
        stamp(cv, seal(nm, 36, ZHU if i == 0 else INK), 960, y - 30, t, t - u + 0.5 + i * 0.4)

def art_x_chu_songs(A, cv, t, u):
    """8-beat set piece: 四面楚歌 — night camp in a ring; song marks rise from every side; soldiers slip away one by one."""
    ph = u / P
    for k in range(40):
        x = 80 + (k * 29) % 920; y = 640 + (k * 43) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    A.d['wash'].ellipse((800, 680, 900, 780), fill=255)
    tent(A, 540, GROUND, 360, 280, layer='mid')
    lamp(A, 540, GROUND, 50, t, glow=0.5)
    ground(A, GROUND)
    stay = 12 - int(clamp((ph - 2) / 5) * 10)
    for k in range(12):
        x = 160 + k * 66 if k < 6 else 700 + (k - 6) * 66
        if k < stay:
            person(A, x, GROUND, 100, dir=1 if x < 540 else -1, robe=False, hat='helmet', spear=True, arm=30, layer='ink')
        elif k < stay + 2:
            person(A, x + (60 if x > 540 else -60) * ((t % 1)), GROUND, 100, dir=1 if x > 540 else -1, robe=False, hat='helmet', ph=t * 6, arm=20, layer='mid')
    A.flush(cv)
    for i in range(int(clamp(ph / 6) * 16)):
        a = i * 2 * math.pi / 16 + 0.2
        r = 380 + 40 * math.sin(t * 2 + i)
        x, y = 540 + r * math.cos(a), 1060 + 0.7 * r * math.sin(a)
        if 640 < y < 1440:
            paste(cv, text_img('楚', BRUSH, 56, POPPY if i % 3 == 0 else INK), x, y, 1, 0.75)
    if ph >= 5:
        paste(cv, text_img('汉皆已得楚乎', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((ph - 5) / 0.4))

def art_x_bieji(A, cv, t, u):
    tent(A, 540, GROUND, 760, 480, layer='mid')
    lamp(A, 540, GROUND, 50, t, glow=0.7)
    ground(A, GROUND)
    xiang(A, 330, GROUND, 260, dir=1, ji=False, arm=lerp(20, 50, 0.5 + 0.5 * math.sin(t)))
    yuji(A, 720, GROUND, 220, dir=-1, t=t)
    A.flush(cv)
    for i, ln in enumerate(('力拔山兮气盖世', '时不利兮骓不逝')):
        type_in(cv, text_img(ln, SERIF, 40, POPPY if i else INK, 'Black', bleed=False, vertical=True, spacing=4), 960 - i * 60, 940, t, t - u + 0.3 + i * P, 0.5)

def art_x_breakout(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    ground(A, GROUND)
    for k in range(10):
        x = lerp(200, 1200, (u / (4 * P))) - (k % 5) * 100
        rider(A, x, GROUND - (k // 5) * 40, 110, 1, t * 13 + k, layer='ink' if k else 'ujin', spear=True)
    A.flush(cv)
    paste(cv, text_img('八百骑', SERIF, 56, UJIN, 'Black', bleed=False, spacing=8), W / 2, 880, 1, 1)

def art_x_dongcheng(A, cv, t, u):
    for k in range(3):
        A.d['mid'].polygon([(200 + k * 300 - 160, GROUND), (200 + k * 300, GROUND - 220), (200 + k * 300 + 160, GROUND)], fill=200)
    ground(A, GROUND)
    n = 28
    for k in range(n):
        a = k * 2 * math.pi / n
        x, y = 540 + 170 * math.cos(a), GROUND - 140 + 50 * math.sin(a)
        A.d['ink'].ellipse((x - 10, y - 10, x + 10, y + 10), fill=255)
    for k in range(10):
        a = k * 2 * math.pi / 10 + t * 0.2
        x = 540 + 420 * math.cos(a); y = GROUND - 140 + 120 * math.sin(a)
        A.d['mid'].ellipse((x - 14, y - 14, x + 14, y + 14), fill=220)
    A.flush(cv)
    paste(cv, text_img('二十八骑', SERIF, 52, POPPY, 'Black', bleed=False, spacing=6), W / 2, 880, 1, 1)
    for i in range(3):
        if u > (0.8 + i * 0.8) * P:
            stamp(cv, seal('胜', 44), 380 + i * 160, 1000, t, t - u + (0.8 + i * 0.8) * P)

def art_x_marsh(A, cv, t, u):
    A.d['ocean'].polygon([(400, GROUND), (500, 1260), (980, 1220), (980, GROUND)], fill=110)
    for k in range(20):
        x = 420 + k * 28
        A.d['grass'].line((x, GROUND, x + 6 * math.sin(t + k), GROUND - 80 - 20 * (k % 3)), fill=220, width=4)
    ground(A, GROUND, x0=60, x1=500)
    person(A, 200, GROUND, 170, dir=1, robe=False, hat='knot', arm=lerp(20, 100, ease_out(u / 0.5)), layer='mid')
    x = lerp(300, 680, ease_out((u - P) / (2 * P)))
    horse(A, x, GROUND + 20 * ease_out((u - 2 * P) / P), 140, dir=1, ph=t * 7, moving=u < 3 * P, layer='ink')
    A.flush(cv)
    stamp(cv, seal('田父绐曰左', 38, INK), 260, 900, t, t - u + 0.5, rot=-5)

# ================================================================ 第五回 乌江自刎
def art_x_wujiang(A, cv, t, u):
    """6-beat set piece: 乌江 — the ferryman holds the boat; he looks back to the pursuing riders and refuses."""
    ph = u / P
    river(A, 1220, t, rows=4, amp=7, speed=1.6)
    ground(A, 1220, x0=60, x1=600)
    boat(A, 760, 1270, 120, t, sail=False)
    person(A, 760, 1240, 130, dir=-1, robe=False, hat='knot', arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    xiang(A, 460, 1220, 250, dir=1 if ph < 2 else -1, ji=True, arm=40)
    for k in range(6):
        rider(A, lerp(-300, 160, ease_out(ph / 6)) - k * 90, 1220, 90, 1, t * 11 + k, layer='mid', spear=True)
    A.flush(cv)
    if ph >= 1:
        type_in(cv, text_img('江东虽小 亦足王也', SERIF, 44, UJIN, 'Black', bleed=False, spacing=4), W / 2, 820, t, t - u + P, 0.4)
    if ph >= 3:
        type_in(cv, text_img('天之亡我 我何渡为', SERIF, 50, POPPY, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 3 * P, 0.5)

def art_x_wuzhui(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=6)
    ground(A, 1240, x0=60, x1=520)
    horse(A, 400, 1240, 200, dir=1, ph=0, moving=False, head_down=0.4, layer='ink')
    xiang(A, 220, 1240, 230, dir=1, ji=False, arm=lerp(30, 90, ease_out(u / 0.6)))
    boat(A, 760, 1290, 120, t, sail=False)
    A.flush(cv)
    stamp(cv, seal('乌骓', 56), 400, 900, t, t - u + P)

def art_x_sword(A, cv, t, u):
    for k in range(60):
        q = (t * 0.4 + k / 60) % 1
        x = 80 + (k * 17) % 920
        A.d['poppy'].ellipse((x - 5, lerp(620, 1420, q) - 4, x + 5, lerp(620, 1420, q) + 4), fill=int(200 * (1 - q)))
    river(A, 1260, t, rows=2, amp=4, speed=0.6)
    ground(A, 1260, x0=60, x1=W - 60)
    p = ease_out((u - 1.5 * P) / 0.8)
    xiang(A, 540, 1260, 280, dir=1, ji=False, sword=lerp(80, 160, ease_out(u / P)), arm=lerp(60, 170, ease_out(u / P)), kneel=p > 0.5, bow=0)
    A.flush(cv)
    paste(cv, text_img('年仅三十', SERIF, 52, POPPY, 'Black', bleed=False, spacing=8), W / 2, 880, 1, clamp((u - 2 * P) / 0.3))

def art_x_burial(A, cv, t, u):
    A.d['mid'].chord((340, 1180, 740, GROUND + 200), 180, 360, fill=230)
    ground(A, GROUND)
    person(A, 820, GROUND, 230, dir=-1, robe=True, hat='crown', bow=30, arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('谷城', 54, INK), 540, 1100, t, t - u + P)
    paste(cv, text_img('为发哀 泣之而去', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - 1.5 * P) / 0.3))

def art_x_benji(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360)
    sitter(A, 300, GROUND, 220, dir=1, bow=15)
    p = ease_out(u / (2 * P))
    A.d['wash'].rectangle((420, GROUND - 120, 420 + 260 * p, GROUND - 74), fill=255)
    A.flush(cv)
    ink_in(cv, text_img('项羽本纪', SERIF, 48, POPPY, 'Black', bleed=False, spacing=8), W / 2, 880, t, t - u + P, dur=0.3)
    stamp(cv, seal('司马迁', 46, INK), 860, 1060, t, t - u + 0.4, rot=6)

def art_x_liqingzhao(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=5)
    person(A, 300, 1240, 220, dir=1, robe=True, hat='knot', female=True, arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t)), layer='ink')
    ground(A, 1240, x0=60, x1=480)
    A.flush(cv)
    for i, ln in enumerate(('生当作人杰', '死亦为鬼雄', '至今思项羽', '不肯过江东')):
        type_in(cv, text_img(ln, SERIF, 40, POPPY if i == 3 else INK, 'Black', bleed=False, vertical=True, spacing=4), 900 - i * 62, 960, t, t - u + 0.2 + i * 0.4 * P, 0.4)

def art_x_legacy(A, cv, t, u):
    river(A, 1260, t, rows=3, amp=5)
    ding(A, 540, 1240, 200, crack=1.0)

def art_x_title(A, cv, t, u):
    horse(A, 760, 1460, 300, dir=-1, ph=0, moving=False, layer='mid')
    xiang(A, 400, 1460, 700, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '将门之后'), 48: ('第二回', '破釜沉舟'), 80: ('第三回', '西楚霸王'),
            112: ('第四回', '楚汉相争'), 144: ('第五回', '乌江自刎')}

CARDS = [
    C(0, 2, 'war', 'num', num='三万', line='击溃五十六万大军', art=art_x_hook_30k),
    C(2, 4, 'works', 'num', num='破釜沉舟', line='只带三天干粮', art=art_x_hook_pots),
    C(4, 6, 'night', 'num', num='四面楚歌', line='霸王别姬', art=art_x_hook_farewell),
    C(6, 8, 'death', 'num', num='三十岁', line='乌江自刎', art=art_x_hook_wujiang),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 将门之后
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-232, main='生于下相', sub='楚国名将项燕之孙 · 名籍 字羽', note='传说 项羽重瞳', art=art_x_birth),
    C(22, 26, 'death', 'card', year=-223, main='国破家亡', sub='秦灭楚 · 祖父项燕战死', art=art_x_grandfather),
    C(26, 30, 'works', 'card', year=-220, main='万人敌', sub='学书不成 学剑不成 · 要学兵法', note='剑一人敌 不足学', art=art_x_wanren),
    C(30, 34, 'works', 'card', year=-215, main='力能扛鼎', sub='才气过人 · 吴中子弟皆惮之', art=art_x_lift_ding),
    C(34, 38, 'court', 'card', year=-210, main='彼可取而代', sub='始皇巡游会稽 · 他脱口而出', note='梁掩其口 毋妄言 族矣', art=art_x_replace),
    C(38, 42, 'war', 'card', year=-209, main='会稽起兵', sub='斩郡守 · 随叔父项梁举事', art=art_x_rise),
    C(42, 46, 'life', 'card', year=-209, main='八千子弟', sub='江东子弟八千人 · 渡江而西', art=art_x_eight_thousand),
    C(46, 48, 'death', 'card', year=-208, main='项梁战死', sub='定陶兵败', art=art_x_xiangliang),
    # ---- 第二回 破釜沉舟
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'night', 'card', year=-207, main='斩宋义', sub='上将军畏敌不前 · 项羽斩之', note='当是时 诸将皆慑服', art=art_x_songyi),
    C(54, 62, 'war', 'julu', year=-207),
    C(62, 66, 'empire', 'card', year=-207, main='诸侯膝行', sub='入辕门 无不膝行而前', note='由是始为诸侯上将军', art=art_x_kneel),
    C(66, 70, 'war', 'card', year=-207, main='章邯投降', sub='秦军主力覆灭', art=art_x_zhanghan),
    C(70, 74, 'night', 'card', year=-207, main='新安坑卒', sub='夜坑秦降卒二十余万', note='关中人心尽失', art=art_x_xinan),
    C(74, 80, 'night', 'card', year=-206, main='鸿门宴', sub='项王默然不应', note='竖子不足与谋', art=art_x_hongmen),
    # ---- 第三回 西楚霸王
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'war', 'card', year=-206, main='火烧咸阳', sub='屠城 烧秦宫室', note='火三月不灭', art=art_x_burn_xianyang),
    C(86, 90, 'court', 'card', year=-206, main='衣锦还乡', sub='富贵不归故乡 · 如衣绣夜行', note='人言楚人沐猴而冠耳', art=art_x_home),
    C(90, 94, 'empire', 'card', year=-206, main='分封天下', sub='立十八诸侯 · 自立西楚霸王', art=art_x_fief),
    C(94, 98, 'empire', 'card', year=-206, main='定都彭城', sub='弃关中而东归', art=art_x_pengcheng),
    C(98, 106, 'war', 'card', year=-205, main='彭城之战', sub='三万骑兵 · 大破汉军', note='汉卒十余万人皆入睢水', art=art_x_pengcheng_battle),
    C(106, 110, 'works', 'card', year=-204, main='荥阳相持', sub='楚汉对峙 · 粮道屡被截断', art=art_x_xingyang),
    C(110, 112, 'night', 'card', year=-204, main='范增离去', sub='中反间计 · 亚父辞归', art=art_x_fanzeng),
    # ---- 第四回 楚汉相争
    C(112, 114, 'night', 'chapter'),
    C(114, 118, 'court', 'card', year=-203, main='鸿沟为界', sub='约和东归', art=art_x_honggou),
    C(118, 122, 'war', 'card', year=-202, main='汉军背约', sub='刘邦追击 · 诸侯会师', art=art_x_betrayal),
    C(122, 130, 'night', 'card', year=-202, main='四面楚歌', sub='垓下被围 · 夜闻楚歌', note='是何楚人之多也', art=art_x_chu_songs),
    C(130, 134, 'death', 'card', year=-202, main='霸王别姬', sub='美人名虞 · 骏马名骓', note='虞兮虞兮奈若何', art=art_x_bieji),
    C(134, 138, 'war', 'card', year=-202, main='八百突围', sub='夜率八百骑南逃', art=art_x_breakout),
    C(138, 142, 'fate', 'card', year=-202, main='东城快战', sub='仅剩二十八骑 · 三战三胜', note='此天之亡我 非战之罪也', art=art_x_dongcheng),
    C(142, 144, 'fate', 'card', year=-202, main='迷途', sub='田父欺之 · 陷入大泽', art=art_x_marsh),
    # ---- 第五回 乌江自刎
    C(144, 146, 'death', 'chapter'),
    C(146, 152, 'death', 'card', year=-202, main='乌江', sub='亭长舣船以待 · 他不肯渡', note='纵江东父兄怜而王我 我何面目见之', art=art_x_wujiang),
    C(152, 156, 'fate', 'card', year=-202, main='赠马', sub='乌骓赠与亭长', note='吾知公长者', art=art_x_wuzhui),
    C(156, 160, 'death', 'card', year=-202, main='自刎', sub='身被十余创 · 自刎而死', art=art_x_sword),
    C(160, 164, 'court', 'card', year=-202, main='鲁公之礼', sub='刘邦以鲁公之礼葬之', art=art_x_burial),
    C(164, 168, 'works', 'card', year=-91, main='列入本纪', sub='司马迁为失败者立本纪', art=art_x_benji),
    C(168, 170, 'end', 'card', year=1129, main='不肯过江东', sub='李清照 夏日绝句', art=art_x_liqingzhao),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='贰拾叁', col=UJIN, acc=POPPY, born=-232, died=-202,
    born_lab='前232年', died_lab='前202年', years_txt='公元前232 — 前202',
    hook_q='天下几乎是他的 · 为何输给了刘邦？',
    name_line='项籍 · 字羽', name='项羽', seal='霸王', title_art=art_x_title,
    q1='盖世英雄？', q2='有勇无谋？',
    end_art=art_x_legacy, end_big='力拔山兮', end_seal='西楚',
    end_l1='身经七十余战 未尝败北', end_l2='却只输了最后一战',
    end_brush='不肯过江东', end_ask='如果他过了江东 结局会怎样？评论区聊聊', next='韩信'),
    scenes=dict(chapter=scene_chapter, julu=scene_julu))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
