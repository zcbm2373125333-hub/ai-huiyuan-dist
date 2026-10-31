# 千古人物志 · 第叁集 · 唐太宗李世民 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效），本集特色：
#   青绿山水远山 · 唐式铜镜章回卡 · 牡丹花瓣 · 卷草纹边角 · 昭陵六骏回顾 · 八拍「玄武门之变」长镜
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_wudi as Wd           # brings in the long-version engine + 汉武帝 helpers (camel, coin, ...)
import render_long as L
import render_gufeng as G
import render_story as S
import render_full as F
from render_gufeng import (W, H, FPS, bt, INK, ZHU, ZHE, BRUSH, SERIF, WILD, font, clamp, lerp, ease_out, ease_expo,
                           cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import (Art, person, horse, carriage, palace, flames, waves, boat, crow, arrow, flag, ground,
                          sun, walk_x, rotp, ellipse_pts, GROUND)
from render_full import chars_in, type_in, beat_fx
from render_long import C, rider, city_wall, note_in, stage, DIM, P
from render_wudi import camel, art_split

BORN, DIED = 598, 649
END_BEAT = 170
GOLD = (184, 134, 52)
QING = (46, 98, 96)        # 石绿
QING2 = (52, 84, 112)      # 石青

# ================================================================ episode look
WM = dict(hook='唐', life='民', night='变', court='观', war='戰', empire='盛', works='汗', fate='镜', death='陵', end='宗')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire'):
    G.THEMES[k]['part'] = 'peony'
G.THEMES['empire']['sun'] = (GOLD, 260, (W * 0.5, 820))
G.THEMES['works']['sun'] = (GOLD, 220, (W * 0.5, 820))
G.base_bg.cache_clear()

MTN_COL = {'night': (40, 52, 70), 'death': (60, 60, 64), 'war': (88, 48, 36)}
def draw_background(t, theme):
    """青绿山水: distant ranges in malachite / azurite instead of plain ink."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [QING2, QING, MTN_COL.get(theme, (34, 60, 56))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

_orig_sprite = G.particle_sprite
@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'peony':
        return _orig_sprite(kind, q)
    s = 48
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [(206, 92, 110), (226, 140, 150), (190, 60, 80)][q]
    d.pieslice((8, 12, 40, 40), 200, 340, fill=col + (225,))
    d.ellipse((12, 18, 36, 34), fill=col + (225,))
    d.line((24, 20, 24, 32), fill=tuple(max(0, c - 40) for c in col) + (160,), width=1)
    return im.filter(ImageFilter.GaussianBlur(0.7))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """Tang scroll-leaf (卷草) corner ornaments in gold."""
    d = ImageDraw.Draw(canvas)
    m = 46
    col = GOLD + (190,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 120, y), fill=col, width=3); d.line((x, y, x, y + sy * 120), fill=col, width=3)
        for k, r in enumerate((26, 16)):
            cx, cy = x + sx * (44 + k * 46), y + sy * 24
            box = (min(cx - r, cx + r), cy - r, max(cx - r, cx + r), cy + r)
            d.arc(box, 0 if sy > 0 else 180, 270 if sy > 0 else 90, fill=col, width=3)
            cx2, cy2 = x + sx * 24, y + sy * (44 + k * 46)
            d.arc((cx2 - r, cy2 - r, cx2 + r, cy2 + r), 90 if sx > 0 else 270, 360 if sx > 0 else 180, fill=col, width=3)
        d.ellipse((x + sx * 8 - 6, y + sy * 8 - 6, x + sx * 8 + 6, y + sy * 8 + 6), fill=ZHU + (220,))
G.draw_frame_border = draw_frame_border

# ================================================================ bronze-mirror chapter card
def bronze_mirror(A, cx, cy, r, p, rot, layer='ink', knob=True):
    d = A.d[layer]
    rr = r * ease_out(p)
    if rr < 4: return
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=255, width=max(3, int(r * 0.06)))
    d.ellipse((cx - rr * 0.86, cy - rr * 0.86, cx + rr * 0.86, cy + rr * 0.86), outline=200, width=3)
    A.d['wash'].ellipse((cx - rr * 0.84, cy - rr * 0.84, cx + rr * 0.84, cy + rr * 0.84), fill=110)
    n = 8
    for j in range(n):             # 宝相花 petals
        a = rot + j * 2 * math.pi / n
        px, py = cx + rr * 0.68 * math.cos(a), cy + rr * 0.68 * math.sin(a)
        pts = [rotp(q, (px, py), a) for q in ((px - rr * 0.13, py), (px, py - rr * 0.07), (px + rr * 0.13, py), (px, py + rr * 0.07))]
        A.d['mid'].polygon(pts, fill=255)
    for j in range(24):
        a = -rot * 0.5 + j * math.pi / 12
        d.line((cx + rr * 0.90 * math.cos(a), cy + rr * 0.90 * math.sin(a),
                cx + rr * 0.97 * math.cos(a), cy + rr * 0.97 * math.sin(a)), fill=255, width=3)
    if knob:
        d.ellipse((cx - rr * 0.08, cy - rr * 0.08, cx + rr * 0.08, cy + rr * 0.08), fill=255)

def art_mirror_chapter(A, cv, t, u):
    bronze_mirror(A, 540, 960, 400, u / 0.5, t * 0.35, knob=False)
    for k in range(4):
        y = 1260 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)
L.art_chapter = art_mirror_chapter

# ================================================================ scenes
def art_birth(A, cv, t, u):
    sun(cv, 540, 900, lerp(80, 200, ease_out(u / (2 * P))), ZHU, 130)
    ground(A, GROUND)
    palace(A, 520, GROUND, 460, layer='mid')
    for k in range(5):
        a = t * 0.8 + k * 1.25
        x = 540 + 300 * math.cos(a); y = 860 + 90 * math.sin(a)
        A.d['wash'].ellipse((x - 70, y - 26, x + 70, y + 26), fill=255)
    person(A, 880, GROUND, 230, dir=-1, arm=lerp(20, 130, ease_out((u - P) / 0.4)), layer='ink')

def art_yanmen(A, cv, t, u):
    city_wall(A, 300, 780, 1150, gate_x=540, label='雁门')
    for k in range(6):
        a = t * 1.1 + k * 1.05
        x = 540 + 420 * math.cos(a)
        rider(A, x, GROUND + 10 * math.sin(a), 120, -1 if math.sin(a) > 0 else 1, t * 12 + k,
              layer='ink' if math.sin(a) > 0 else 'mid', spear=True)
    if u > 2 * P:
        v = u - 2 * P
        for k in range(10):
            p = ease_out((v - k * 0.06) / 0.25)
            if p > 0:
                x = 80 + k * 100
                flag(A, x, lerp(1180, 1110, p), 160 * p, t + k, w=60)

def art_jinyang(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(560, GROUND), (980, GROUND), (950, 1300), (590, 1300)], fill=255)
    person(A, 780, 1300, 230, dir=-1, arm=30, layer='ink')
    person(A, 420, GROUND, 250, dir=1, kneel=True, bow=lerp(10, 40, ease_out(u / P)), arm=lerp(40, 100, ease_out(u / P)), layer='ink')
    if u > 2 * P:
        v = u - 2 * P
        for k in range(8):
            p = ease_out((v - k * 0.05) / 0.3)
            flag(A, 90 + k * 125, lerp(1300, 1160, p), 220 * p, t + k, w=80)

def art_hulao(A, cv, t, u):
    A.d['mid'].polygon([(60, GROUND), (60, 760), (240, 820), (330, GROUND)], fill=255)
    A.d['mid'].polygon([(W - 60, GROUND), (W - 60, 760), (840, 820), (750, GROUND)], fill=255)
    ground(A, GROUND)
    for i in range(14):
        x = 560 + (i % 7) * 60; y = 1300 + (i // 7) * 60
        person(A, x, y, 110, dir=-1, robe=False, hat='helmet', spear=True, layer='wash' if i < 7 else 'mid')
    x = lerp(-150, 620, ease_out(u / (3 * P)))
    for k in range(3):
        rider(A, x - k * 170, GROUND - k * 14, 200 - k * 20, 1, t * 15 + k, layer='ink' if k == 0 else 'mid', spear=True)
    if u > 3 * P:
        A.flush(cv)
        stamp(cv, seal('窦', 54), 760, 960, t, t - u + 3 * P)
        stamp(cv, seal('王', 54, INK), 880, 960, t, t - u + 3 * P + 0.15)

def art_tiance(A, cv, t, u):
    ground(A, GROUND)
    rider(A, 520, GROUND, 300, 1, 0.0, layer='ink', spear=False, moving=False)
    A.d['ink'].line((560, GROUND - 200, 560, 640), fill=255, width=8)
    pts_top = [(560 + i * 24, 660 + 10 * math.sin(t * 5 + i * 0.6)) for i in range(11)]
    pts_bot = [(560 + i * 24, 900 + 10 * math.sin(t * 5 + i * 0.6)) for i in range(10, -1, -1)]
    A.d['red'].polygon(pts_top + pts_bot, fill=255)
    fo = font(SERIF, 70, 'Black')
    A.d['red'].text((640, 700), '天', font=fo, fill=0); A.d['red'].text((640, 790), '策', font=fo, fill=0)
    for k in range(4):
        person(A, 140 + k * 90, GROUND, 170, dir=1, robe=False, hat='helmet', spear=True, layer='mid')

def art_rivals(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(380, GROUND), (700, GROUND), (670, 1300), (410, 1300)], fill=255)
    person(A, 540, 1300, 220, dir=1, hat='crown', arm=30, layer='ink')
    lean = 20 + 8 * math.sin(t * 3)
    person(A, 760, GROUND, 250, dir=-1, bow=lean, arm=60, hat='crown', layer='ink')
    person(A, 870, GROUND, 240, dir=-1, bow=lean, arm=60, layer='mid')
    person(A, 220, GROUND, 260, dir=1, arm=-10, layer='ink')
    if u > P:
        A.flush(cv)
        stamp(cv, seal('忌', 54), 810, 960, t, t - u + P, rot=8)

def art_wine(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((300, 1280, 780, 1310), fill=255)
    for lx in (330, 730): A.d['mid'].rectangle((lx, 1310, lx + 20, GROUND), fill=255)
    for k in range(4):
        x = 360 + k * 110
        A.d['ink'].polygon([(x - 16, 1250), (x + 16, 1250), (x + 8, 1280), (x - 8, 1280)], fill=255)
    person(A, 880, GROUND, 250, dir=-1, hat='crown', bow=10, arm=50, layer='mid')
    sick = u > 2 * P
    person(A, 200, GROUND, 250, dir=1, bow=55 if sick else 0, arm=80 if sick else 50, layer='ink')
    if sick:
        v = u - 2 * P
        for k in range(10):
            q = clamp((v - k * 0.04) / 0.5)
            A.d['red'].ellipse((300 + q * 80 - 7, GROUND - 120 + q * 100 - 7, 300 + q * 80 + 7, GROUND - 120 + q * 100 + 7), fill=int(255 * q))

def art_council(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].ellipse((380, 960, 700, 1280), fill=190)
    A.d['ink'].rectangle((530, 1270, 550, GROUND), fill=255)
    fh = 44 + 8 * math.sin(t * 17)
    A.d['red'].polygon([(528, 1270), (552, 1270), (544 + 4 * math.sin(t * 9), 1270 - fh), (540, 1270 - fh)], fill=255)
    for k, x in enumerate((240, 380, 700)):
        person(A, x, GROUND, 210, dir=1 if x < 540 else -1, kneel=True, bow=25 + 8 * math.sin(t * 2 + k), arm=80, layer='ink')
    draw = ease_out((u - 2 * P) / 0.5)
    person(A, 860, GROUND, 280, dir=-1, arm=lerp(30, 95, draw), arm2=lerp(30, 85, draw), layer='ink')
    if draw > 0:
        A.d['ink'].arc((640, 1000, 760, 1200), 100, 260, fill=255, width=6)

def art_xuanwu(A, cv, t, u):
    """8-beat set piece: dawn gate → ambush → the fatal arrow → the gate shut."""
    sun(cv, 540, lerp(1150, 950, ease_out(u / (8 * P))), 230, ZHU, 110)
    city_wall(A, 60, W - 60, 1080, gate_x=540, label='玄武', open_=1.0 if u < 6 * P else 1 - ease_out((u - 6 * P) / 0.4))
    ground(A, GROUND)
    ph = u / P
    if ph < 4:
        x = lerp(-150, 330, ease_out(u / (2 * P)))
        rider(A, x, GROUND, 190, 1, t * 11 if ph < 2 else 0.4, layer='ink', moving=ph < 2)
        rider(A, x - 210, GROUND - 8, 180, 1, t * 11 + 1 if ph < 2 else 0.9, layer='mid', moving=ph < 2)
    if ph >= 2:
        v = u - 2 * P
        for k in range(6):
            p = ease_out((v - k * 0.05) / 0.25)
            px = 150 + k * 150
            A.d['ink'].ellipse((px - 18, lerp(1100, 1032, p) - 18, px + 18, lerp(1100, 1032, p) + 18), fill=255)
            A.d['ink'].line((px + 16, lerp(1100, 1032, p), px + 30, lerp(1100, 1032, p) - 110), fill=255, width=4)
    if 2 <= ph < 6:
        v = u - 2 * P
        draw = ease_out(v / 0.5)
        person(A, 820, GROUND, 290, dir=-1, robe=False, arm=95, arm2=lerp(60, 85, draw), hat='knot', layer='ink')
        A.d['ink'].arc((640, 1060, 780, 1260), 100, 260, fill=255, width=6)
        if ph >= 4:
            w = u - 4 * P
            q = clamp(w / 0.25)
            arrow(A, lerp(690, 360, q), 1150, math.pi, 90)
            fall = -80 * ease_out((w - 0.2) / 0.4)
            person(A, 330, GROUND - 0.66 * 190, 115, dir=1, arm=40, fall=fall, layer='ink')
            if w > 0.2:
                for k in range(8):
                    a = k * 0.8
                    r = 60 * ease_out((w - 0.2) / 0.3)
                    A.d['red'].ellipse((330 + r * math.cos(a) - 8, 1180 + r * math.sin(a) * 0.5 - 8,
                                        330 + r * math.cos(a) + 8, 1180 + r * math.sin(a) * 0.5 + 8), fill=255)
    if ph >= 6:
        person(A, 540, GROUND, 330, dir=1, robe=False, hat='helmet', arm=150, sword=150, layer='ink')
        A.flush(cv)
        stamp(cv, seal('六月初四', 52), 860, 900, t, t - u + 6 * P, rot=6)

def art_weishui(A, cv, t, u):
    A.d['wash'].rectangle((60, 1190, W - 60, 1300), fill=200)
    waves(A, 1200, t, rows=3, amp=8, speed=2)
    for k in range(10):
        rider(A, 120 + k * 95, 1140, 90, -1, t * 4 + k, layer='mid', moving=False)
    for k in range(6):
        rider(A, 200 + k * 120, GROUND, 150, 1, 0.3 * k, layer='ink', moving=False)
    p = ease_out((u - 2 * P) / 0.6)
    if p > 0:
        A.d['ink'].rectangle((300, 1250, 300 + 480 * p, 1266), fill=255)
        for k in range(int(8 * p)):
            A.d['ink'].rectangle((310 + k * 60, 1266, 318 + k * 60, 1310), fill=255)

def art_mirror(A, cv, t, u):
    bronze_mirror(A, 640, 1010, 260, u / 0.4, t * 0.2)
    person(A, 650, 1170, 230, dir=-1, hat='crown', arm=20, layer='wash')
    ground(A, GROUND)
    person(A, 260, GROUND, 260, dir=1, kneel=True, bow=lerp(10, 35, 0.5 + 0.5 * math.sin(t * 3)), arm=90, layer='ink')
    if u > P:
        A.flush(cv)
        stamp(cv, seal('谏', 56), 260, 1000, t, t - u + P)

def art_farm(A, cv, t, u):
    sun(cv, 820, 860, 110, GOLD, 120)
    for r in range(4):
        y = 1230 + r * 50
        A.d['mid'].line((60, y, W - 60, y), fill=255, width=3)
        for x in range(90, W - 60, 60):
            sw = 6 * math.sin(t * 2 + x * 0.02)
            A.d['ink'].line((x, y, x + sw, y - 30 - r * 4), fill=255, width=3)
    for k in range(3):
        x = 260 + k * 260
        person(A, x, 1250 + k * 30, 180, dir=1, bow=lerp(40, 60, 0.5 + 0.5 * math.sin(t * 3 + k)), arm=120, layer='ink')

def art_exam(A, cv, t, u):
    ground(A, GROUND)
    palace(A, 540, 1100, 420, layer='mid')
    for r in range(2):
        for k in range(5):
            x = 150 + k * 190; y = GROUND - r * 90
            person(A, x, y, 150 - r * 20, dir=1, kneel=True, bow=30 + 5 * math.sin(t * 4 + k), arm=110,
                   layer='ink' if r == 0 else 'mid')
            A.d['mid'].rectangle((x + 40, y - 40, x + 90, y - 30), fill=255)

def art_market(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        palace(A, x, 1240, 260, layer='mid')
    for k in range(6):
        x = 120 + k * 170
        sw = 10 * math.sin(t * 2 + k)
        A.d['ink'].line((x, 1010, x + sw, 1050), fill=255, width=2)
        A.d['red'].ellipse((x + sw - 18, 1050, x + sw + 18, 1100), fill=255)
    ground(A, GROUND)
    for k in range(5):
        x = (t * 70 * (1 if k % 2 else -1) + k * 230) % (W + 200) - 100
        person(A, x, GROUND, 150 + (k % 3) * 15, dir=1 if k % 2 else -1, arm=20, female=k % 3 == 0, layer='ink')
    camel(A, (t * 50 + 400) % (W + 300) - 150, GROUND, 140, 1, t * 5, layer='ink')

def art_boat_water(A, cv, t, u):
    tilt = 0.15 * math.sin(t * 2.5) + (0.5 * ease_out((u - 2 * P) / 0.4) if u > 2 * P else 0)
    cx, cy = 540, 1180 - 40 * math.sin(t * 2.5)
    hull = [(-260, -30), (260, -20), (200, 40), (-190, 40)]
    A.d['ink'].polygon([rotp((cx + a, cy + b), (cx, cy), tilt) for a, b in hull], fill=255)
    A.d['ink'].line([rotp((cx, cy - 30), (cx, cy), tilt), rotp((cx, cy - 330), (cx, cy), tilt)], fill=255, width=6)
    for k in range(5):
        y = 1210 + k * 40
        pts = [(x, y + 30 * math.sin(x * 0.012 + t * 3 + k)) for x in range(60, W - 59, 10)]
        A.d['ink' if k == 0 else 'mid'].line(pts, fill=255, width=6 if k == 0 else 4)

def art_prisoners(A, cv, t, u):
    city_wall(A, 640, W - 60, 1150, gate_x=860, label='狱')
    ground(A, GROUND)
    back = u > 2 * P
    for k in range(4):
        if not back:
            x = walk_x(780 - k * 60, 200 - k * 60, u, 2 * P)
            person(A, x, GROUND, 190, dir=-1, robe=False, ph=t * 7 + k, layer='ink' if k == 0 else 'mid')
        else:
            x = walk_x(150 - k * 60, 740 - k * 60, u - 2 * P, 2 * P)
            person(A, x, GROUND, 190, dir=1, robe=False, ph=t * 7 + k, layer='ink' if k == 0 else 'mid')
    if back:
        A.flush(cv)
        stamp(cv, seal('无一亡匿', 44), 360, 980, t, t - u + 3 * P, rot=-5)

def art_envoys(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(400, GROUND), (680, GROUND), (650, 1270), (430, 1270)], fill=255)
    person(A, 540, 1270, 230, dir=1, hat='crown', arm=50, layer='ink')
    hats = ['helmet', 'knot', 'crown', 'helmet']
    for i in range(4):
        for side in (-1, 1):
            p = ease_out((u - i * 0.15) / 0.4)
            x = 540 + side * lerp(560, 200 + i * 110, p)
            person(A, x, GROUND, 170 - i * 8, dir=-side, kneel=p > 0.9, bow=40 if p > 0.9 else 0, arm=70,
                   hat=hats[i], layer='ink' if i % 2 == 0 else 'mid')
    if u > P:
        A.flush(cv)
        stamp(cv, seal('可汗', 58), 540, 900, t, t - u + P)

def art_wencheng(A, cv, t, u):
    for k, (x, h) in enumerate(((200, 380), (480, 460), (760, 400), (980, 340))):
        A.d['mid'].polygon([(x - 260, 1260), (x, 1260 - h), (x + 260, 1260)], fill=255)
        A.d['wash'].polygon([(x - 70, 1260 - h * 0.72), (x, 1260 - h), (x + 70, 1260 - h * 0.72)], fill=0)
    ground(A, GROUND)
    off = t * 90
    for k in range(4):
        x = (k * 280 + off) % (W + 500) - 400
        if k == 1:
            carriage(A, x, GROUND, 160, dir=1, wheel=t * 4, ph=t * 8)
        elif k == 2:
            camel(A, x, GROUND, 150, 1, t * 5, layer='ink')
        else:
            for j in range(2):
                person(A, x + j * 60, GROUND, 150, dir=1, robe=False, hat='helmet', spear=True, ph=t * 7 + j, layer='ink')
            flag(A, x + 30, GROUND - 150, 200, t + k, w=70)

def art_xuanzang(A, cv, t, u):
    sun(cv, 760, 880, 120, GOLD, 120)
    d = A.d['mid']
    for k, (y0, amp, ph) in enumerate(((1300, 60, 0.4), (1370, 40, 2.0))):
        pts = [(x, y0 - amp * math.sin(x * 0.006 + ph)) for x in range(60, W - 59, 10)]
        (A.d['wash'] if k == 0 else d).polygon(pts + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=255)
    x = lerp(860, 420, ease_out(u / (4 * P)))
    person(A, x, 1350, 230, dir=-1, robe=True, arm=70, layer='ink')
    A.d['ink'].rectangle((x + 20, 1350 - 220, x + 70, 1350 - 120), fill=255)
    A.d['ink'].line((x + 45, 1350 - 220, x + 45, 1350 - 300), fill=255, width=4)
    A.d['mid'].pieslice((x - 20, 1350 - 330, x + 110, 1350 - 270), 180, 360, fill=255)
    A.d['ink'].line((x - 40, 1350 - 120, x - 50, 1350), fill=255, width=4)
    if u > 2 * P:
        A.flush(cv)
        stamp(cv, seal('真经', 52), 820, 1060, t, t - u + 2 * P)

def art_lingyan(A, cv, t, u):
    palace(A, 540, GROUND, 520, layer='mid')
    palace(A, 540, 1040, 300, layer='ink')
    for k in range(24):
        p = ease_out((u - k * 0.03) / 0.25)
        if p <= 0: continue
        col_ = k % 12; row = k // 12
        x = 110 + col_ * 78 + (0 if row == 0 else 0); y = 690 + row * 80
        A.d['ink'].rectangle((x, y, x + 56 * p, y + 64), outline=255, width=3)
        A.d['mid'].ellipse((x + 18, y + 10, x + 38, y + 30), fill=255)
        A.d['mid'].rectangle((x + 14, y + 32, x + 42, y + 58), fill=255)

def art_broken_mirror(A, cv, t, u):
    bronze_mirror(A, 540, 960, 260, 1.0, 0.3)
    crack = ease_out((u - P) / 0.35)
    if crack > 0:
        r = random.Random(7)
        for k in range(7):
            a = r.uniform(0, 2 * math.pi)
            pts = [(540, 960)]
            for j in range(1, 5):
                rr = 260 * j / 4 * crack
                pts.append((540 + rr * math.cos(a + r.uniform(-0.2, 0.2)), 960 + rr * math.sin(a + r.uniform(-0.2, 0.2))))
            A.d['red'].line(pts, fill=255, width=5)
    ground(A, GROUND)
    person(A, 760, GROUND, 250, dir=-1, hat='crown', kneel=True, bow=lerp(10, 45, crack), arm=70, layer='ink')

def art_depose(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(600, GROUND), (980, GROUND), (950, 1300), (630, 1300)], fill=255)
    person(A, 800, 1300, 220, dir=-1, hat='crown', arm=lerp(20, 120, ease_out((u - P) / 0.3)), layer='ink')
    person(A, 420, GROUND, 230, dir=1, kneel=True, bow=50, arm=70, hat='crown', layer='ink')
    for k in range(2):
        person(A, 160 + k * 100, GROUND, 220, dir=1, robe=False, hat='helmet', spear=True, layer='mid')
    if u > P:
        A.flush(cv)
        stamp(cv, seal('废', 64), 430, 980, t, t - u + P, rot=-6)

def art_zhaoling(A, cv, t, u):
    A.d['mid'].polygon([(120, 1300), (420, 860), (540, 800), (660, 860), (960, 1300)], fill=255)
    A.d['wash'].polygon([(0, 1300), (240, 1080), (420, 1300)], fill=255)
    ground(A, GROUND)
    for k in range(6):
        p = ease_out((u - P - k * 0.12) / 0.3)
        if p <= 0: continue
        x = 130 + k * 165
        A.d['mid'].rectangle((x - 70, 1300, x + 70, 1400), fill=200)
        horse(A, x - 5, 1390, 72 * p, 1, k * 1.1, layer='ink', moving=k % 2 == 0)

def art_tang_legacy(A, cv, t, u):
    sun(cv, 540, 1050, 260, ZHU, 130)
    fo = font(BRUSH, 520)
    ch = '唐'
    p = ease_out(u / (1.5 * P))
    tmp = Image.new('L', (W, H), 0)
    ImageDraw.Draw(tmp).text((540 - fo.getlength(ch) / 2, 760), ch, font=fo, fill=255)
    fld = G.transition_field()
    a = np.asarray(tmp, np.float32) * np.clip((p * 1.3 - fld) / 0.08, 0, 1)
    m = Image.fromarray(a.astype(np.uint8))
    A.im['ink'].paste(m, (0, 0), m)
    ground(A, GROUND)
    for k in range(6):
        person(A, 140 + k * 160, GROUND, 150 + (k % 2) * 20, dir=1 if k < 3 else -1, arm=40, female=k % 2 == 1, layer='mid')

def art_xuanwu_hook(A, cv, t, u):
    city_wall(A, 60, W - 60, 1080, gate_x=540, label='玄武')
    ground(A, GROUND)
    for k in range(5):
        q = (u * 1.4 + k * 0.2) % 1
        arrow(A, lerp(900, 250, q), 1000 - 140 * math.sin(math.pi * q), math.atan2(-140 * math.pi * math.cos(math.pi * q), -650), 80)
    rider(A, 300, GROUND, 200, 1, t * 10, layer='ink')

# ================================================================ 昭陵六骏 recap
STEEDS = [('拳毛騧', '平刘黑闼', True), ('什伐赤', '平王世充', True), ('白蹄乌', '平薛仁杲', True),
          ('特勒骠', '平宋金刚', False), ('青骓', '平窦建德', True), ('飒露紫', '战洛阳', False)]
PANELS = [(220, 930), (540, 930), (860, 930), (220, 1250), (540, 1250), (860, 1250)]
def scene_steeds(cv, t, c, k):
    s0 = bt(c[0])
    gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    A = Art(); beat_fx(A, t)
    gu = ease_expo((t - gather_t) / 0.4) if gather else 0
    for i, ((name, battle, gallop), (x, y)) in enumerate(zip(STEEDS, PANELS)):
        st = bt(c[0] + i)
        if t < st: continue
        p = ease_out((t - st) / 0.25)
        sc = lerp(1.0, 0.82, gu)
        cx = lerp(x, 540 + (x - 540) * 0.95, gu); cy = lerp(y, 1060 + (y - 1090) * 0.85, gu)
        A.d['mid'].rounded_rectangle((cx - 145 * sc * p, cy - 120 * sc, cx + 145 * sc * p, cy + 120 * sc), radius=12, fill=150)
        A.d['ink'].rounded_rectangle((cx - 145 * sc * p, cy - 120 * sc, cx + 145 * sc * p, cy + 120 * sc), radius=12, outline=255, width=4)
        if p > 0.6:
            horse(A, cx - 10 * sc, cy + 95 * sc, 165 * sc, 1 if i % 2 == 0 else -1, t * 12 + i if gallop else 0.6, layer='ink', moving=gallop)
            if name == '飒露紫':
                person(A, cx + 60 * sc, cy + 100 * sc, 130 * sc, dir=-1, robe=False, arm=80, layer='ink')
    A.flush(cv)
    if not gather:
        fx = Art()
        chars_in(cv, fx, '昭陵六骏', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=134)
        fx.flush(cv)
        for i, ((name, battle, _), (x, y)) in enumerate(zip(STEEDS, PANELS)):
            st = bt(c[0] + i)
            if t >= st:
                ink_in(cv, text_img(name, SERIF, 36, ZHU, 'Black', bleed=False, spacing=4), x, y + 150, t, st + 0.1, dur=0.2, settle=1.0)
        idx = int(k - c[0])
        if 0 <= idx < 6:
            lab = text_img(f'{STEEDS[idx][0]} · {STEEDS[idx][1]}', SERIF, 50, INK, 'Black', bleed=False, spacing=4)
            ink_in(cv, lab, W / 2, 570, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    else:
        fx = Art()
        chars_in(cv, fx, '六骏', BRUSH, 190, INK, W / 2, 430, t, gather_t, stagger=0.1, seed=140)
        chars_in(cv, fx, '陪他打下江山', BRUSH, 110, ZHU, W / 2, 1460, t, bt(c[0] + 7), stagger=0.06, seed=141, splash=False)
        fx.flush(cv)

# ================================================================ script
CHAPTERS = {16: ('第一回', '少年英雄'), 48: ('第二回', '玄武惊变'), 80: ('第三回', '贞观之治'),
            112: ('第四回', '天可汗'), 144: ('第五回', '晚节余晖')}
siege = lambda label: (lambda A, cv, t, u: L.art_siege(A, cv, t, u, label=label))
surrender = lambda label: (lambda A, cv, t, u: L.art_surrender(A, cv, t, u, label=label))

CARDS = [
    C(0, 2, 'hook', 'num', num='玄武门', line='弑兄逼父夺皇位', art=art_xuanwu_hook),
    C(2, 4, 'hook', 'num', num='贞观之治', line='开创大唐盛世', art=art_market),
    C(4, 6, 'hook', 'num', num='天可汗', line='万国来朝', art=art_envoys),
    C(6, 8, 'hook', 'num', num='以人为镜', line='千古纳谏第一人', art=art_mirror),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 少年英雄
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=598, main='生于武功', sub='书生相面 · 济世安民 故名世民', note='龙凤之姿 天日之表', art=art_birth),
    C(22, 26, 'life', 'card', year=615, main='雁门救驾', sub='隋炀帝被突厥围困 · 少年献疑兵计', note='多赍旗鼓以设疑兵', art=art_yanmen),
    C(26, 30, 'life', 'card', year=617, main='晋阳起兵', sub='力劝父亲李渊 · 起兵反隋', note='今盗贼日繁 遍于天下', art=art_jinyang),
    C(30, 34, 'life', 'card', year=618, main='大唐开国', sub='李渊称帝 · 李世民封秦王', note='武德元年 国号曰唐', art=S.art_enthrone),
    C(34, 38, 'war', 'card', year=618, main='浅水原', sub='初战告捷 · 大破薛仁杲', note='追奔二百余里', art=L.art_cavalry),
    C(38, 42, 'war', 'card', year=621, main='虎牢关', sub='三千五百骑 · 一战擒两王', note='一战而擒窦建德 降王世充', art=art_hulao),
    C(42, 46, 'war', 'card', year=621, main='天策上将', sub='功高无可再赏 · 特设此号', note='位在王公之上', art=art_tiance),
    C(46, 48, 'court', 'card', year=622, main='功高震主', sub='太子与齐王 · 如芒在背', art=art_rivals),
    # ---- 第二回 玄武惊变
    C(48, 50, 'night', 'chapter'),
    C(50, 54, 'court', 'card', year=624, main='兄弟相争', sub='太子建成 齐王元吉 · 联手排挤', note='建成 元吉 日夜谮诉', art=art_rivals),
    C(54, 58, 'court', 'card', year=626, main='毒酒之谋', sub='东宫夜宴 · 秦王饮酒吐血', note='暴心痛 吐血数升', art=art_wine),
    C(58, 62, 'night', 'card', year=626, main='箭在弦上', sub='房杜长孙 · 力劝先发制人', note='事急矣 不可不发', art=art_council),
    C(62, 70, 'night', 'card', year=626, main='玄武门之变', sub='伏兵玄武门 · 射杀太子建成', note='六月庚申 世民帅长孙无忌等入 伏兵于玄武门', art=art_xuanwu),
    C(70, 74, 'court', 'card', year=626, main='立为太子', sub='三日后 · 李渊立其为太子', note='自今军国庶事 皆委太子处决', art=S.art_throne),
    C(74, 80, 'empire', 'card', year=626, main='登基称帝', sub='李渊退位 · 唐太宗即位', seal='贞观', note='明年改元 贞观', art=S.art_enthrone),
    # ---- 第三回 贞观之治
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'night', 'card', year=626, main='渭水之盟', sub='突厥二十万兵临渭水 · 太宗六骑临阵', note='与颉利隔水而语', art=art_weishui),
    C(86, 90, 'court', 'card', year=630, main='以人为镜', sub='魏征犯颜直谏二百余事', note='以铜为镜 可以正衣冠 以人为镜 可以明得失', art=art_mirror),
    C(90, 98, 'empire', 'list', year=630, items=['轻徭薄赋', '科举取士', '三省六部', '路不拾遗']),
    C(98, 102, 'works', 'card', year=632, main='水能载舟', sub='民为邦本 · 本固邦宁', note='君 舟也 人 水也 水能载舟 亦能覆舟', art=art_boat_water),
    C(102, 106, 'court', 'card', year=632, main='纵囚归狱', sub='放死囚三百九十人归家 · 来年秋全数归来', note='应期毕至 无一人亡匿', art=art_prisoners),
    C(106, 112, 'empire', 'card', year=633, main='贞观盛世', sub='米斗三四钱 · 外户不闭', note='行旅自京师至于岭表 皆不赍粮', art=art_market),
    # ---- 第四回 天可汗
    C(112, 114, 'works', 'chapter'),
    C(114, 118, 'night', 'card', year=630, main='夜袭阴山', sub='李靖雪夜奔袭 · 生擒颉利可汗', note='以三千骁骑 夜袭定襄', art=L.art_cavalry),
    C(118, 122, 'works', 'card', year=630, main='天可汗', sub='四夷君长 · 共尊太宗', note='四夷君长诣阙 请上为天可汗', art=art_envoys),
    C(122, 126, 'works', 'card', year=640, main='平定西域', sub='灭高昌 · 设安西都护府', note='西域诸国 皆来朝贡', art=surrender('高昌')),
    C(126, 130, 'works', 'card', year=641, main='文成入藏', sub='文成公主远嫁吐蕃 · 汉藏和亲', note='松赞干布 亲迎于柏海', art=art_wencheng),
    C(130, 134, 'works', 'card', year=645, main='玄奘归来', sub='西行求法十七年 · 太宗亲见', note='往返五万里 历百三十八国', art=art_xuanzang),
    C(134, 142, 'war', 'steeds'),
    C(142, 144, 'empire', 'card', year=643, main='凌烟阁', sub='二十四功臣 · 画像留名', art=art_lingyan),
    # ---- 第五回 晚节余晖
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'fate', 'card', year=643, main='一镜已亡', sub='魏征病逝 · 太宗痛哭', note='魏征没 朕遂亡一镜矣', art=art_broken_mirror),
    C(150, 154, 'death', 'card', year=643, main='太子之祸', sub='太子承乾谋反被废 · 改立李治', note='玄武门的影子 再次笼罩东宫', art=art_depose),
    C(154, 158, 'war', 'card', year=645, main='东征受挫', sub='亲征高句丽 · 安市城下无功而返', note='魏征若在 不使我有是行也', art=siege('安市')),
    C(158, 162, 'death', 'card', year=649, main='崩于含风殿', sub='在位二十三年 · 享年五十二岁', note='五月己巳 上崩于含风殿', art=Wd.art_dusk_palace),
    C(162, 166, 'death', 'card', year=649, main='葬于昭陵', sub='因山为陵 · 六骏石刻长伴', note='因山为陵 不复起坟', art=art_zhaoling),
    C(166, 170, 'end', 'card', year=649, main='千古明君', sub='贞观之治 · 后世帝王的楷模', note='唐人 唐装 唐人街 由此流传', art=art_tang_legacy),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS; L.CHAPTERS = CHAPTERS; Wd.CHAPTERS = CHAPTERS
G.CHAPTER_BEATS = [0, 16, 48, 80, 112, 144, 150, END_BEAT]
L.CUTS = sorted({c[0] for c in CARDS if c[0] not in G.CHAPTER_BEATS} | {92, 94, 96})

def year_at(t):
    pts = sorted((bt(c[0]), c[4]['year']) for c in CARDS if 'year' in c[4])
    if t <= pts[0][0]: return pts[0][1]
    prev = pts[0][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t < t1: return lerp(prev, y0, ease_out((t - t0) / 0.4))
        prev = y0
    return lerp(prev, pts[-1][1], ease_out((t - pts[-1][0]) / 0.4))
G.year_at = year_at; L.year_at = year_at; Wd.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    s = '公元' + cn_num(yr) + '年'
    im = text_img(s, SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=ZHU + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, S.art_emperor)
    fx = Art()
    ink_in(cv, text_img('李 世 民', SERIF, 50, ZHE, 'Bold', bleed=False, spacing=16), W / 2, 300, t, s0)
    chars_in(cv, fx, '唐太宗', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('贞观', 66), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元598 — 649', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '弑兄篡位？', BRUSH, 120, ZHU, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '千古明君？', BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

def art_roads(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        x = 120 + k * 200
        A.d['mid'].rectangle((x, 1150, x + 120, GROUND), fill=255)
        A.d['wash'].rectangle((x + 30, 1250, x + 90, GROUND), fill=0)
        A.d['red'].ellipse((x + 45, 1100 + 6 * math.sin(t * 2 + k), x + 75, 1140 + 6 * math.sin(t * 2 + k)), fill=255)
    A.d['red'].ellipse((520, GROUND - 30, 560, GROUND - 4), fill=255)
    for k in range(3):
        x = (t * 80 + k * 360) % (W + 200) - 100
        person(A, x, GROUND, 160, dir=1, arm=20, layer='ink')

LIST_ART = [art_farm, art_exam, art_split('皇', '省', '部'), art_roads]
def scene_list(cv, t, c, k):
    i = min(3, int((k - c[0]) / 2))
    st = bt(c[0] + 2 * i)
    A = Art()
    LIST_ART[i](A, cv, t, t - st)
    beat_fx(A, t)
    A.flush(cv, reveal=ease_out((t - st) / 0.25))
    year_line(cv, t, c[4]['year'], bt(c[0]))
    it = c[4]['items'][i]
    fx = Art()
    chars_in(cv, fx, it, BRUSH, 140, INK, W / 2, 440, t, st, stagger=0.05, seed=50 + i)
    fx.flush(cv)
    for j in range(4):
        x = W / 2 + (j - 1.5) * 95
        if j <= i:
            stamp(cv, seal('壹贰叁肆'[j], 36), x, 575, t, bt(c[0] + 2 * j))
        else:
            ImageDraw.Draw(cv).rounded_rectangle((x - 30, 545, x + 30, 605), radius=6, outline=ZHU + (110,), width=2)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    bronze_mirror(A, 540, 760, 330, u / 0.6, t * 0.25, layer='wash', knob=False)
    rise = ease_out(u / 1.6)
    person(A, 230, lerp(1820, 1700, rise), 760, dir=1, hat='crown', arm=lerp(10, 40, rise), layer='wash')
    beat_fx(A, t)
    A.flush(cv, alpha=clamp(u / 0.6))
    fx = Art()
    chars_in(cv, fx, '千古明君', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('贞观之治', 64), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('夺位于玄武门 · 治世于贞观', SERIF, 50, DIM, 'SemiBold', bleed=False, spacing=6), W / 2, 960, t, END + 0.6, 0.35)
    type_in(cv, text_img('一手染血 一手开创盛世', SERIF, 54, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '功能掩过吗？', BRUSH, 120, ZHU, W / 2, 1200, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('评论区留下你的看法', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=ZHU + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(252, 240, 226, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=GOLD + (230,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 女皇武则天', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, list=scene_list, steeds=scene_steeds, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第叁集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(8):
        q = text_img('玄武门弑兄 · 为何成了千古明君？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 320, 335, W / 2 + 320, 335), fill=ZHU + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, ZHU, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.9)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=GOLD + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=ZHU + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(int(round(yr - BORN + 1))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=ZHU + (255,))
        if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * a)))
        canvas.alpha_composite(ov, (0, y - 80))
G.draw_hud = draw_hud

render = L.render

if __name__ == '__main__':
    from multiprocessing import Pool
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for ts in sys.argv[2].split(','):
            Image.frombytes('RGB', (W, H), render(int(float(ts) * FPS))).save(out.replace('.png', f'_{ts}.png'))
        sys.exit()
    nfr = int(round(G.DUR * FPS))
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-i', L.MUSIC,
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, fr in enumerate(pool.imap(render, range(nfr), chunksize=4)):
            ff.stdin.write(fr)
            if i % 300 == 0: print(i, '/', nfr, flush=True)
    ff.stdin.close(); ff.wait()
    print('done', out)
