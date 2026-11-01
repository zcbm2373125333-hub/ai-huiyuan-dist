"""千古人物志 · 第拾捌集 · 王阳明 (1472–1529)
Look: 松墨绿 + 烛光橙, 竹节 corner borders, a 心灯 (heart-lamp) chapter card that burns brighter each chapter.
Set pieces: 8-beat 庭前格竹 (seven days and nights), 8-beat 龙场悟道 (night → dawn → 心即理),
custom 8-beat scene 'ningwang' (宁王之乱: day counter + 鄱阳湖 fire attack), 四句教 card.
"""
import math, os, sys, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_zhenghe as Zh         # engine + helpers (previous episode)
import render_qijiguang as Qj
import render_wentianxiang as Wx
import render_yuefei as Yf
import render_zhuge as Zg
import render_caocao as Cc
import render_liubang as Lb
import render_genghis as Gh
import render_qianlong as Q
import render_yongzheng as Y
import render_kangxi as K
import render_mingtaizu as M
import render_songtaizu as St
import render_wuzetian as Z
import render_taizong as Tz
import render_wudi as Wd
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
from render_kangxi import lantern
from render_songtaizu import tent
from render_yuefei import cn_year

F.RIPPLE = False

BORN, DIED = 1472, 1529
AGE0 = 1472.83                      # born 农历九月 (Oct 1472) -> 周岁 in the HUD
END_BEAT = 170
PINE = (44, 86, 66)                 # 松墨绿
CANDLE = (222, 146, 54)             # 烛光橙
S.LAYERS.append(('pine', PINE, 0.85, 1.2))
S.LAYERS.append(('candle', CANDLE, 0.85, 2.2))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

# ================================================================ episode look
WM = dict(hook='心', life='云', court='儒', night='夜', war='戰', empire='明', works='竹', fate='知', death='光', end='心')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (CANDLE, 240, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['end']['sun'] = (CANDLE, 210, (W * 0.5, 720))
G.base_bg.cache_clear()

MTN_COL = {'night': (30, 44, 40), 'death': (60, 62, 60), 'war': (98, 58, 40), 'works': (52, 96, 74)}
def draw_background(t, theme):
    """竹林远山: soft green ranges with a faint bamboo screen at the far edges."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(170, 186, 172), (118, 150, 126), MTN_COL.get(theme, (64, 104, 82))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn']))))
        canvas.alpha_composite(layer)
    d = ImageDraw.Draw(canvas)
    for k, x in enumerate((70, 104, W - 70, W - 106)):
        sw = 6 * math.sin(t * 0.8 + k)
        d.line((x, 1500, x + sw, 640), fill=PINE + (36,), width=10)
        for y in range(660, 1500, 110):
            d.line((x - 8 + sw * (1500 - y) / 860, y, x + 8 + sw * (1500 - y) / 860, y), fill=PINE + (50,), width=3)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """竹节: two jointed bamboo canes meeting at each corner, a small leaf pair on the joint."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = PINE + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 170, y), fill=col, width=6); d.line((x, y, x, y + sy * 170), fill=col, width=6)
        for k in (55, 115):
            d.line((x + sx * k, y - 7, x + sx * k, y + 7), fill=CANDLE + (230,), width=3)
            d.line((x - 7, y + sy * k, x + 7, y + sy * k), fill=CANDLE + (230,), width=3)
        for a in (-0.5, 0.3):
            ang = math.atan2(sy, sx) + a
            tip = (x + 24 * sx + 46 * math.cos(ang), y + 24 * sy + 46 * math.sin(ang))
            d.line((x + 24 * sx, y + 24 * sy, tip[0], tip[1]), fill=col, width=5)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def leaf(A, layer, x, y, ang, L_=70, w=9, fill=230):
    ca, sa = math.cos(ang), math.sin(ang)
    A.d[layer].polygon([(x, y), (x + 0.45 * L_ * ca - w * sa, y + 0.45 * L_ * sa + w * ca), (x + L_ * ca, y + L_ * sa),
                        (x + 0.45 * L_ * ca + w * sa, y + 0.45 * L_ * sa - w * ca)], fill=fill)

def bamboo(A, x, base, h, t, layer='pine', lean=0.0, width=14, seed=0, leaves=True, wilt=0.0):
    segs = max(3, int(h / 95))
    sway = 10 * math.sin(t * 1.1 + x * 0.013)
    pts = []
    for i in range(segs + 1):
        f = i / segs
        pts.append((x + lean * h * f + sway * f * f, base - h * f))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        A.d[layer].line((x0, y0, x1, y1), fill=255, width=width)
        A.d['ink'].line((x1 - width * 0.7, y1, x1 + width * 0.7, y1), fill=170, width=3)
    if leaves:
        r = random.Random(seed)
        for (px, py) in pts[-4:]:
            for _ in range(3):
                a = r.uniform(-0.6, 0.6) + (math.pi if r.random() < 0.5 else 0) + 0.15 * math.sin(t * 1.5 + px)
                a += wilt * (math.pi / 2 - a) * 0.8
                leaf(A, layer, px, py, a, r.uniform(55, 90), 8)

def wang(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, **kw):
    """王阳明: scholar's robe with a square 方巾 cap."""
    capped = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if capped else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if capped:
        A.d[layer].rectangle((x - 0.065 * h, y - 1.08 * h, x + 0.065 * h, y - 0.93 * h), fill=255)
        A.d[layer].polygon([(x - dir * 0.065 * h, y - 1.05 * h), (x - dir * 0.13 * h, y - 0.92 * h), (x - dir * 0.065 * h, y - 0.95 * h)], fill=255)
    return hand

def sitter(A, x, y, h, dir=1, layer='ink', bow=0):
    """seated cross-legged figure (meditation)."""
    d = A.d[layer]
    def T(u_, v): return (x + dir * u_ * h, y - v * h)
    d.polygon([T(-0.30, 0), T(0.30, 0), T(0.22, 0.12), T(-0.22, 0.12)], fill=255)
    br = math.radians(bow)
    def B(u_, v):
        v0 = 0.12
        return T(u_ * math.cos(br) + (v - v0) * math.sin(br), v0 - u_ * math.sin(br) + (v - v0) * math.cos(br))
    d.polygon([B(-0.12, 0.10), B(0.12, 0.10), B(0.09, 0.46), B(-0.09, 0.46)], fill=255)
    cx, cy = B(0, 0.54)
    d.ellipse((cx - 0.07 * h, cy - 0.07 * h, cx + 0.07 * h, cy + 0.07 * h), fill=255)
    d.polygon([B(0.08, 0.40), B(0.20, 0.20), B(0.04, 0.16)], fill=255)

def desk(A, x, y, w, layer='ink'):
    A.d[layer].rectangle((x - w / 2, y - 70, x + w / 2, y - 58), fill=255)
    for sx in (-1, 1):
        A.d[layer].rectangle((x + sx * (w / 2 - 20) - 5, y - 58, x + sx * (w / 2 - 20) + 5, y), fill=255)

def lamp(A, x, y, s, t, glow=1.0, layer='ink'):
    """oil lamp: dish on a stand, flickering flame, warm halo on the candle layer."""
    A.d[layer].rectangle((x - 0.06 * s, y - 0.9 * s, x + 0.06 * s, y), fill=255)
    A.d[layer].rectangle((x - 0.3 * s, y - 0.06 * s, x + 0.3 * s, y), fill=255)
    A.d[layer].chord((x - 0.35 * s, y - 1.1 * s, x + 0.35 * s, y - 0.8 * s), 0, 180, fill=255)
    fl = 1 + 0.12 * math.sin(t * 13) + 0.07 * math.sin(t * 29)
    r = (0.6 + 1.0 * glow) * s * fl
    for j in range(4):
        rr = r * (1 - j * 0.22)
        A.d['candle'].ellipse((x - rr, y - 1.1 * s - rr, x + rr, y - 1.1 * s + rr), fill=int(14 + 22 * glow))
    fh = 0.35 * s * fl
    A.d['red'].polygon([(x - 0.07 * s, y - 0.98 * s), (x + 0.07 * s, y - 0.98 * s), (x + 0.02 * s, y - 0.98 * s - fh)], fill=255)

def stone_coffin(A, x, y, w, h, lid=0.0, layer='mid'):
    A.d[layer].rectangle((x - w / 2, y - h, x + w / 2, y), fill=235)
    A.d['ink'].rectangle((x - w / 2, y - h, x + w / 2, y), outline=255, width=5)
    lx = x + lid * w * 0.4
    A.d['ink'].polygon([(lx - w / 2 - 14, y - h - 4), (lx + w / 2 + 14, y - h - 4), (lx + w / 2, y - h - 34), (lx - w / 2, y - h - 34)], fill=255)

def cave(A, x, base, w, h, layer='mid'):
    A.d[layer].polygon([(x - w, base), (x - w * 0.8, base - h * 0.8), (x - w * 0.3, base - h), (x + w * 0.4, base - h * 0.95),
                        (x + w, base - h * 0.5), (x + w * 1.1, base)], fill=230)
    A.d['wash'].chord((x - w * 0.45, base - h * 0.62, x + w * 0.45, base + h * 0.5), 180, 360, fill=255)

def fire_boat(A, x, y, s, t, burn=1.0, seed=0):
    A.d['ink'].polygon([(x - s, y - 20), (x + s, y - 20), (x + 0.8 * s, y + 12), (x - 0.8 * s, y + 12)], fill=255)
    A.d['ink'].line((x, y - 20, x, y - 20 - 1.3 * s), fill=255, width=4)
    if burn > 0:
        flames(A, x, y - 20, 1.6 * s, 1.6 * s * burn, t, n=4, seed=seed, smoke=False)

def scroll(A, x, y, w, h, p, layer='wash'):
    q = ease_out(p)
    A.d[layer].rectangle((x - w / 2 * q, y - h / 2, x + w / 2 * q, y + h / 2), fill=255)
    for sx in (-1, 1):
        A.d['ink'].rectangle((x + sx * w / 2 * q - 9, y - h / 2 - 16, x + sx * w / 2 * q + 9, y + h / 2 + 16), fill=255)

def heart_lamp(A, cx, cy, r, level, t, p=1.0):
    """chapter object: a lotus-dish lamp whose halo and flame grow with each chapter."""
    q = ease_out(p)
    if q <= 0.02: return
    fl = 1 + 0.1 * math.sin(t * 11) + 0.05 * math.sin(t * 23)
    for k in range(level):
        rr = r * (0.45 + 0.22 * k) * q * fl
        A.d['candle'].ellipse((cx - rr, cy - rr - 90, cx + rr, cy + rr - 90), fill=34)
    for i in range(7):
        a = math.pi + (i + 0.5) * math.pi / 7
        px, py = cx + 0.9 * r * math.cos(a) * q, cy + 0.32 * r * math.sin(a) * q
        leaf(A, 'pine', cx, cy + 30, math.atan2(py - cy - 30, px - cx), 0.95 * r * q, 26 * q, fill=235)
    A.d['ink'].chord((cx - 0.55 * r * q, cy - 40 * q, cx + 0.55 * r * q, cy + 60 * q), 0, 180, fill=255)
    A.d['ink'].rectangle((cx - 16, cy + 60 * q, cx + 16, cy + 200 * q), fill=255)
    A.d['ink'].rectangle((cx - 0.4 * r * q, cy + 196 * q, cx + 0.4 * r * q, cy + 214 * q), fill=255)
    fh = (60 + 40 * level) * q * fl
    A.d['red'].polygon([(cx - 22 * q, cy - 18), (cx + 22 * q, cy - 18), (cx + 8 * math.sin(t * 7), cy - 18 - fh)], fill=255)

# ================================================================ chapter card
CH = {16: 1, 48: 2, 80: 3, 112: 4, 144: 5}
def art_heart_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    heart_lamp(A, 540, 960, 220, CH.get(kb, 2), t, p=u / 0.6)
    for k in range(5):
        x = 140 + k * 200
        bamboo(A, x if k < 2 else x + 120, 1420, 340 + 60 * (k % 2), t, layer='mid', width=9, seed=k, leaves=k % 2 == 0)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_heart_chapter)
    ink_in(cv, text_img(no, SERIF, 56, PINE, 'Black', bleed=False, spacing=12), W / 2, 1290, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_y_hook_bamboo(A, cv, t, u):
    for k, x in enumerate((330, 470, 650, 780)):
        bamboo(A, x, GROUND, 620 + 60 * (k % 2), t, width=16, seed=k)
    ground(A, GROUND)
    sitter(A, 540, GROUND, 200, dir=1, bow=lerp(0, 18, ease_out(u / (1.6 * P))))

def art_y_hook_war(A, cv, t, u):
    A.d['mid'].rectangle((60, 1240, W - 60, 1420), fill=150)
    waves(A, 1250, t, rows=3, amp=6)
    for k in range(4):
        fire_boat(A, 200 + k * 220, 1260 + (k % 2) * 30, 70, t, burn=ease_out((u - k * 0.15) / 0.6), seed=k)

def art_y_hook_cave(A, cv, t, u):
    for k, (x, h) in enumerate(((180, 520), (420, 640), (700, 560), (920, 480))):
        A.d['mid' if k % 2 else 'pine'].polygon([(x - 230, GROUND), (x, GROUND - h), (x + 230, GROUND)], fill=200)
    cave(A, 540, GROUND, 230, 300, layer='ink')
    lamp(A, 540, GROUND - 20, 70, t, glow=ease_out(u / (1.6 * P)))

def art_y_hook_three(A, cv, t, u):
    ground(A, GROUND)
    for i, ch in enumerate('德功言'):
        p = ease_out((u - i * 0.25) / 0.4)
        x = 270 + i * 270
        h = 420 * p
        A.d['ink'].rectangle((x - 40, GROUND - h, x + 40, GROUND), fill=255)
        A.d['ink'].rectangle((x - 70, GROUND - h - 30, x + 70, GROUND - h), fill=255)
    A.flush(cv)
    for i, ch in enumerate('德功言'):
        if u > i * 0.25 + 0.3:
            stamp(cv, seal(ch, 54), 270 + i * 270, GROUND - 520, t, t - u + i * 0.25 + 0.3)

# ================================================================ 第一回 少年立志
def art_y_cloud_birth(A, cv, t, u):
    for k in range(5):
        x = lerp(-200, 900, ((t * 0.06 + k * 0.23) % 1))
        y = 760 + (k % 3) * 70
        for j in range(4):
            A.d['wash'].ellipse((x + j * 60 - 70, y - 40 - (j % 2) * 20, x + j * 60 + 70, y + 40), fill=255)
    p = ease_out(u / (2.5 * P))
    cx, cy = lerp(840, 560, p), lerp(720, 1020, p)
    for j in range(5):
        A.d['candle'].ellipse((cx + j * 40 - 80, cy - 36 - (j % 2) * 16, cx + j * 40 + 10, cy + 30), fill=200)
    person(A, cx + 60, cy - 10, 150, dir=-1, robe=True, hat='crown', baby=True, layer='ink')
    palace(A, 360, GROUND, 360, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('瑞云楼', 46), 360, 1040, t, t - u + 2.5 * P, rot=-4)

def art_y_silent(A, cv, t, u):
    ground(A, GROUND)
    person(A, 400, GROUND, 150, dir=1, robe=True, hat='knot', arm=lerp(-8, 30, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    person(A, 700, GROUND, 290, dir=-1, robe=True, hat='none', arm=lerp(20, 80, ease_out((u - P) / 0.4)), layer='ink')
    A.d['ink'].ellipse((700 - 22, GROUND - 290 * 0.97, 700 + 22, GROUND - 290 * 0.93), fill=255)
    A.flush(cv)
    if u < 2 * P:
        paste(cv, text_img('……', SERIF, 60, DIM, 'Black', bleed=False), 400, GROUND - 230, 1, clamp(u / 0.3))
    else:
        ink_in(cv, text_img('守仁', BRUSH, 110, ZHU), 420, GROUND - 260, t, t - u + 2 * P, dur=0.3, settle=1.2)

def art_y_to_capital(A, cv, t, u):
    city_wall(A, 560, 1020, 1080, gate_x=790, label='京师', layer='mid', open_=1.0)
    ground(A, GROUND)
    x = lerp(-160, 520, ease_out(u / (3.2 * P)))
    carriage(A, x, GROUND, 150, dir=1, wheel=u * 6, ph=t * 9, moving=u < 3.2 * P, layer='ink')
    A.flush(cv)
    stamp(cv, seal('状元之子', 44), 330, 980, t, t - u + P, rot=-5)

def art_y_first_thing(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360)
    for k in range(3):
        A.d['wash'].rectangle((430 + k * 80, GROUND - 92, 490 + k * 80, GROUND - 72), fill=255)
    person(A, 790, GROUND, 290, dir=-1, robe=True, hat='crown', arm=lerp(10, 70, ease_out(u / 0.5)), layer='ink')
    wang(A, 300, GROUND, 170, dir=1, arm=lerp(20, 120, ease_out((u - P) / 0.4)), layer='ink')
    A.flush(cv)
    if u > 2 * P:
        type_in(cv, text_img('学圣贤', BRUSH, 96, ZHU), 330, 960, t, t - u + 2 * P, 0.4)

def art_y_juyong(A, cv, t, u):
    for k, (x, h) in enumerate(((240, 470), (560, 560), (880, 440))):
        A.d['mid'].polygon([(x - 280, GROUND), (x, GROUND - h), (x + 280, GROUND)], fill=200)
    pts = [(x, GROUND - 260 - 140 * math.sin(x / W * math.pi) - 40 * math.sin(x * 0.02)) for x in range(80, W - 79, 20)]
    A.d['ink'].line(pts, fill=255, width=14)
    for i in range(0, len(pts), 6):
        A.d['ink'].rectangle((pts[i][0] - 14, pts[i][1] - 40, pts[i][0] + 14, pts[i][1]), fill=255)
    ground(A, GROUND)
    rider(A, lerp(200, 640, ease_out(u / (3 * P))), GROUND, 170, 1, t * 11, layer='ink', moving=u < 3 * P)
    A.flush(cv)
    stamp(cv, seal('居庸关', 46), 860, 900, t, t - u + P, rot=6)

def art_y_wedding_night(A, cv, t, u):
    A.d['wash'].ellipse((780, 660, 900, 780), fill=255)
    palace(A, 540, GROUND, 400, layer='mid')
    ground(A, GROUND)
    sitter(A, 380, GROUND, 220, dir=1)
    sitter(A, 700, GROUND, 220, dir=-1)
    lamp(A, 540, GROUND, 90, t, glow=0.6)
    A.flush(cv)
    stamp(cv, seal('铁柱宫', 46), 260, 960, t, t - u + P, rot=-5)
    if u > 2 * P:
        type_in(cv, text_img('一坐至天明', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + 2 * P, 0.4)

def art_y_loujing(A, cv, t, u):
    A.d['mid'].rectangle((60, 1250, W - 60, 1420), fill=140)
    waves(A, 1260, t, rows=3, amp=5, speed=1.2)
    x = lerp(180, 620, ease_out(u / (3 * P)))
    boat(A, x, 1290, 110, t, sail=True)
    for k in range(4):
        bamboo(A, 860 + k * 40, 1260, 280 + k * 30, t, width=8, seed=10 + k, leaves=k % 2 == 0)
    A.flush(cv)
    stamp(cv, seal('娄谅', 50, INK), 300, 960, t, t - u + P, rot=-4)

def art_y_exam(A, cv, t, u):
    n = int(clamp(u / (1.4 * P)) * 15) + 1
    for i in range(n):
        x = 180 + (i % 5) * 180; y = 920 + (i // 5) * 170
        A.d['mid'].rectangle((x - 70, y, x + 70, y + 130), fill=220)
        A.d['ink'].rectangle((x - 70, y, x + 70, y + 130), outline=255, width=4)
        A.d['ink'].rectangle((x - 18, y + 40, x + 18, y + 110), fill=255)
    A.flush(cv)
    stamp(cv, seal('乡试中举', 48), 860, 760, t, t - u + 1.4 * P, rot=6)

# ================================================================ 第二回 格竹之惑
def art_y_gezhu(A, cv, t, u):
    """8-beat set piece: 庭前格竹 — seven days and nights, sky cycles, he sinks and falls ill."""
    ph = u / P
    day = min(7, int(ph) + 1)
    night = 0.5 - 0.5 * math.cos(2 * math.pi * clamp(ph / 7) * 7)
    if night > 0.5:
        A.d['wash'].ellipse((800, 680, 900, 780), fill=int(255 * (night - 0.5) * 2))
    else:
        sun(cv, 860, 730, 60, CANDLE, int(200 * (0.5 - night) * 2))
    wilt = clamp((ph - 3) / 4)
    for k, x in enumerate((360, 520, 690)):
        bamboo(A, x, GROUND, 640 - 40 * k, t, width=18, seed=20 + k, wilt=0.0)
    ground(A, GROUND)
    if ph < 6.5:
        sitter(A, 260, GROUND, 230, dir=1, bow=10 + 30 * wilt)
    else:
        person(A, 300, GROUND, 230, dir=1, robe=True, hat='knot', fall=-80 * ease_out((ph - 6.5) / 0.6), layer='ink')
    A.flush(cv)
    for i in range(day):
        stamp(cv, seal(cn_num(i + 1), 34, ZHU if i == 6 else PINE), 300 + i * 70, 1452, t, t - u + i * P + 0.1)
    if ph >= 6.5:
        stamp(cv, seal('病倒', 60), 300, 1000, t, t - u + 6.5 * P, rot=-6)

def art_y_failed(A, cv, t, u):
    A.d['mid'].rectangle((300, 860, 780, 1260), fill=220)
    A.d['ink'].rectangle((300, 860, 780, 1260), outline=255, width=6)
    for k in range(6):
        A.d['ink'].line((340, 910 + k * 55, 740 - (k * 37) % 120, 910 + k * 55), fill=150, width=6)
    ground(A, GROUND)
    for k in range(3):
        person(A, 200 + k * 80, GROUND, 150, dir=1, robe=True, hat='knot', bow=40, arm=-20, layer='mid')
    wang(A, 860, GROUND, 200, dir=-1, arm=10)
    A.flush(cv)
    stamp(cv, seal('落第', 60, INK), 540, 1060, t, t - u + P, rot=-8)

def art_y_jinshi(A, cv, t, u):
    p = ease_out(u / (2 * P))
    A.d['yellow'].rectangle((240, 860, 840, 1060), fill=255)
    for k in range(int(p * 12)):
        A.d['ink'].rectangle((280 + k * 46, 890, 300 + k * 46, 1030), fill=200 if k != 7 else 0)
    palace(A, 540, GROUND, 300, layer='mid')
    ground(A, GROUND)
    wang(A, 540, GROUND, 210, dir=1, arm=20)
    A.flush(cv)
    stamp(cv, seal('进士', 56), 540 + 140 * 0 + 120, 960, t, t - u + 2 * P, rot=5)

def art_y_yangming_cave(A, cv, t, u):
    for k, (x, h) in enumerate(((260, 560), (640, 660), (920, 520))):
        A.d['pine'].polygon([(x - 300, GROUND), (x - 60, GROUND - h), (x + 60, GROUND - h + 30), (x + 300, GROUND)], fill=150 + 30 * k)
    cave(A, 600, GROUND, 180, 250, layer='mid')
    sitter(A, 600, GROUND - 10, 150, dir=-1)
    for k in range(18):
        q = (t * 0.25 + k / 18) % 1
        x = 140 + (k * 53) % 820; y = lerp(1300, 700, q)
        A.d['wash'].ellipse((x - 30, y - 10, x + 30, y + 10), fill=int(120 * math.sin(math.pi * q)))
    A.flush(cv)
    stamp(cv, seal('阳明子', 50), 300, 980, t, t - u + P, rot=-5)

def art_y_teaching_capital(A, cv, t, u):
    ground(A, GROUND)
    wang(A, 540, GROUND, 250, dir=1, arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 2.2)))
    n = int(clamp(u / (2 * P)) * 6) + 1
    for k in range(n):
        side = -1 if k % 2 == 0 else 1
        x = 540 + side * (170 + (k // 2) * 110)
        sitter(A, x, GROUND, 130, dir=-side, bow=5)
    A.flush(cv)
    stamp(cv, seal('湛若水', 44, INK), 860, 960, t, t - u + 2 * P, rot=5)

def art_y_beaten(A, cv, t, u):
    palace(A, 540, 1180, 520, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 160, dir=1, robe=True, hat='knot', fall=-88, layer='ink')
    for k, sx in enumerate((-1, 1)):
        x = 540 + sx * 230
        sw = math.sin(t * 9 + k * math.pi)
        person(A, x, GROUND, 220, dir=-sx, robe=False, hat='helmet', arm=lerp(-10, 150, 0.5 + 0.5 * sw), layer='ink')
        hx = x - sx * 60; hy = GROUND - 250
        A.d['ink'].line((hx, hy, hx - sx * 140 * (0.5 + 0.5 * sw), hy + 160), fill=255, width=12)
    A.flush(cv)
    n = min(40, int(u / (0.1 * P)) + 1)
    paste(cv, text_img(f'廷杖{cn_num(n)}', SERIF, 60, ZHU, 'Black', bleed=False), W / 2, 1440, 1, 1)

def art_y_exile(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 210; h = 380 + (k * 97) % 220
        A.d['mid'].polygon([(x - 160, GROUND), (x, GROUND - h), (x + 160, GROUND)], fill=200)
    pts = [(lerp(120, 960, f), GROUND - 60 - 160 * f + 40 * math.sin(f * 12)) for f in np.linspace(0, 1, 30)]
    A.d['wash'].line(pts, fill=255, width=16)
    f = clamp(u / (2 * P))
    i = min(len(pts) - 1, int(f * (len(pts) - 1)))
    wang(A, pts[i][0], pts[i][1], 110, dir=1, ph=t * 6, arm=20)
    A.flush(cv)
    stamp(cv, seal('龙场驿', 50, INK), 860, 860, t, t - u + P, rot=6)

# ================================================================ 第三回 龙场悟道
def art_y_fake_drown(A, cv, t, u):
    A.d['mid'].rectangle((60, 1200, W - 60, 1420), fill=150)
    waves(A, 1210, t, rows=4, amp=10, speed=2.4)
    A.d['ink'].polygon([(60, 1210), (360, 1210), (330, 1080), (60, 1060)], fill=255)
    p = ease_out((u - P) / 0.6)
    A.d['wash'].polygon([(300 + 260 * p, 1180 + 30 * p), (380 + 260 * p, 1180 + 30 * p), (360 + 260 * p, 1205 + 30 * p), (320 + 260 * p, 1205 + 30 * p)], fill=255)
    A.d['ink'].polygon([(330 + 260 * p, 1172 + 30 * p), (350 + 260 * p, 1172 + 30 * p), (340 + 260 * p, 1186 + 30 * p)], fill=255)
    for k in range(2):
        person(A, 120 + k * 90, 1070, 150, dir=1, robe=False, hat='helmet', sword=30, arm=60, layer='ink')
    boat(A, lerp(980, 820, ease_out(u / (3 * P))), 1240, 70, t, sail=False)
    A.flush(cv)
    stamp(cv, seal('一说', 40, INK), 860, 940, t, t - u + P, rot=6)

def art_y_wilds(A, cv, t, u):
    for k in range(7):
        x = 80 + k * 155; h = 520 + (k * 131) % 260
        A.d['pine' if k % 2 else 'mid'].polygon([(x - 140, GROUND), (x - 30, GROUND - h), (x + 30, GROUND - h + 40), (x + 140, GROUND)], fill=210)
    pts = [(x, 1300 + 18 * math.sin(x * 0.03 + t * 3)) for x in range(160, 900, 12)]
    A.d['ink'].line(pts, fill=255, width=14)
    A.d['ink'].ellipse((892, 1286, 924, 1314), fill=255)
    for k in range(10):
        x = 120 + k * 92
        A.d['ink'].line((x, GROUND, x - 20, GROUND - 60, x + 6, GROUND - 90), fill=200, width=4)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('蛮荒', 54, INK), 300, 940, t, t - u + P, rot=-5)

def art_y_coffin(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 380
        tw = 2 + 2 * math.sin(t * 2 + k)
        A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)
    cave(A, 540, GROUND, 360, 470, layer='mid')
    stone_coffin(A, 540, GROUND - 6, 360, 120, lid=0.0)
    sitter(A, 540, GROUND - 160, 170, dir=1, bow=lerp(0, 8, 0.5 + 0.5 * math.sin(t)))
    A.flush(cv)
    type_in(cv, text_img('吾惟俟命而已', SERIF, 50, INK, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + 1.5 * P, 0.5)

def art_y_wudao(A, cv, t, u):
    """8-beat set piece: 龙场悟道 — deep night, a cry at midnight, light floods the cave, 心即理 appears."""
    ph = u / P
    burst = ease_expo((ph - 4) / 1.5)
    for k in range(40):
        x = 80 + (k * 47) % 920; y = 640 + (k * 61) % 420
        tw = (2 + 2 * math.sin(t * 2.5 + k)) * (1 - burst)
        if tw > 0.3: A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)
    if burst > 0:
        for i in range(16):
            a = -math.pi + i * math.pi / 15
            L_ = 900 * burst
            A.d['candle'].polygon([(540, 1240), (540 + L_ * math.cos(a - 0.04), 1240 + L_ * math.sin(a - 0.04)),
                                   (540 + L_ * math.cos(a + 0.04), 1240 + L_ * math.sin(a + 0.04))], fill=int(60 * burst))
        for j in range(3):
            r = 420 * burst * (1 - j * 0.3)
            A.d['candle'].ellipse((540 - r, 1240 - r, 540 + r, 1240 + r), fill=int(28 * burst))
    cave(A, 540, GROUND, 420, 560, layer='mid')
    stone_coffin(A, 540, GROUND - 6, 340, 110)
    if ph < 3.5:
        sitter(A, 540, GROUND - 150, 180, dir=1, bow=6)
    else:
        rise = ease_out((ph - 3.5) / 0.6)
        wang(A, 540, GROUND - 150, lerp(150, 230, rise), dir=1, arm=lerp(20, 165, rise), arm2=lerp(-8, -150, rise))
    lamp(A, 300, GROUND, 70, t, glow=0.3 + burst)
    A.flush(cv)
    if 2.5 <= ph < 4:
        paste(cv, text_img('中夜大悟', SERIF, 52, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp((ph - 2.5) / 0.3))
    if ph >= 5:
        fx = Art()
        chars_in(cv, fx, '心即理', BRUSH, 170, ZHU, W / 2, 800, t, t - u + 5 * P, stagger=0.15, seed=301)
        fx.flush(cv)
    if ph >= 6.5:
        type_in(cv, text_img('圣人之道 吾性自足', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + 6.5 * P, 0.5)

def art_y_zhixing(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    wang(A, 540, GROUND, 250, dir=1, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)))
    for k in range(8):
        x = 140 + k * 110 if k < 4 else 600 + (k - 4) * 110 + 60
        if abs(x - 540) < 120: continue
        sitter(A, x, GROUND, 110, dir=1 if x < 540 else -1, bow=4)
    p = ease_out((u - P) / 0.5)
    A.d['ink'].line((320, 800, 320 + 440 * p, 800), fill=255, width=10)
    A.flush(cv)
    if p > 0.5:
        ink_in(cv, text_img('知', BRUSH, 130, INK), 400, 900, t, t - u + P + 0.2, dur=0.3, settle=1.2)
        ink_in(cv, text_img('行', BRUSH, 130, ZHU), 680, 900, t, t - u + 1.5 * P, dur=0.3, settle=1.2)
    stamp(cv, seal('贵阳书院', 44), 860, 1100, t, t - u + 2.5 * P, rot=6)

def art_y_liujin_falls(A, cv, t, u):
    palace(A, 540, GROUND, 520, collapse=ease_out((u - P) / (1.5 * P)), layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, robe=True, hat='crown', fall=-85 * ease_out((u - P) / 0.5), layer='ink')
    A.flush(cv)
    stamp(cv, seal('刘瑾伏诛', 48, INK), 300, 960, t, t - u + 1.5 * P, rot=-5)
    if u > 2.5 * P:
        stamp(cv, seal('庐陵', 50), 820, 960, t, t - u + 2.5 * P, rot=6)

def art_y_nangan(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['pine'].polygon([(x - 200, GROUND), (x, GROUND - 480 - (k % 2) * 120), (x + 200, GROUND)], fill=200)
    ground(A, GROUND)
    x = lerp(-100, 520, ease_out(u / (1.5 * P)))
    horse(A, x, GROUND, 150, dir=1, ph=t * 9, moving=u < 1.5 * P)
    wang(A, x - 10, GROUND - 120, 150, dir=1, arm=30)
    flag(A, x - 120, GROUND, 360, t, w=90)

# ================================================================ 第四回 文臣用兵
def art_y_tenhouse(A, cv, t, u):
    n = int(clamp(u / (2 * P)) * 10) + 1
    for i in range(10):
        x = 180 + (i % 5) * 180; y = 1000 + (i // 5) * 220
        A.d['mid'].polygon([(x - 70, y), (x, y - 60), (x + 70, y)], fill=220)
        A.d['mid'].rectangle((x - 56, y, x + 56, y + 110), fill=220)
        if i < n:
            A.d['wash'].rectangle((x - 26, y + 20, x + 26, y + 90), fill=255)
            A.d['ink'].rectangle((x - 26, y + 20, x + 26, y + 90), outline=255, width=4)
            for j in range(3):
                A.d['ink'].line((x - 16, y + 38 + j * 18, x + 16, y + 38 + j * 18), fill=200, width=3)
    A.flush(cv)
    stamp(cv, seal('连坐', 54), 860, 860, t, t - u + 2 * P, rot=6)

def art_y_heart_thief(A, cv, t, u):
    for k in range(3):
        x = 220 + k * 320
        A.d['mid'].polygon([(x - 260, GROUND), (x, GROUND - 520 - (k % 2) * 100), (x + 260, GROUND)], fill=200)
    for k in range(3):
        x = 640 + k * 90
        tent(A, x, GROUND - 330, 90, 80, layer='ink')
        flames(A, x, GROUND - 330, 80, 120 * ease_out((u - P - k * 0.2) / 0.5), t, n=3, seed=40 + k, smoke=True)
    ground(A, GROUND)
    wang(A, 260, GROUND, 230, dir=1, arm=lerp(10, 80, ease_out(u / 0.6)))
    A.flush(cv)
    if u > 1.6 * P:
        ink_in(cv, text_img('心中贼', BRUSH, 110, ZHU), 330, 900, t, t - u + 1.6 * P, dur=0.3, settle=1.2)

NW_DAYS = [(0, '六月十四', '宁王起兵 号称十万'), (2, '七月初', '佯檄四方 迟滞叛军'), (4, '七月二十', '直捣南昌老巢'),
           (6, '七月二十四', '鄱阳湖火攻')]
def scene_ningwang(cv, t, c, k):
    """8-beat custom scene: 宁王之乱 — rebel arrows spread, 南昌 taken back, fire ships on 鄱阳湖, 生擒宸濠."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['mid'].rounded_rectangle((100, 720, 980, 1400), radius=40, fill=110)
    A.d['ocean'].polygon([(520, 880), (640, 820), (760, 900), (820, 1040), (780, 1200), (660, 1260), (560, 1180), (500, 1020)], fill=170)
    A.d['ocean'].line([(640, 820), (720, 760), (840, 720), (980, 700)], fill=170, width=26)
    ink_rv = [(100, 1300), (260, 1240), (380, 1160), (500, 1080)]
    A.d['ocean'].line(ink_rv, fill=150, width=16)
    # rebel thrust from 南昌 toward 安庆 (north-east), then pulled back
    rx, ry = 380, 1100
    if ph < 4:
        reach = ease_out(ph / 2)
        pts = [(rx + 520 * reach * f, ry - 320 * reach * f - 40 * math.sin(math.pi * f)) for f in np.linspace(0, 1, 16)]
        A.d['ink'].line(pts, fill=255, width=12)
        ax, ay = pts[-1]
        A.d['ink'].polygon([(ax + 30, ay - 18), (ax - 10, ay - 26), (ax + 4, ay + 12)], fill=255)
    if ph >= 2:
        back = ease_out((ph - 2) / 1.5)
        pts = [(160 + (rx - 160) * back * f, 1260 - (1260 - ry) * back * f) for f in np.linspace(0, 1, 12)]
        A.d['red'].line(pts, fill=255, width=12)
    if ph >= 6:
        for i in range(5):
            fire_boat(A, 640 + (i % 3) * 90, 1000 + (i // 3) * 120 + (i % 2) * 30, 34, t, burn=ease_out((ph - 6 - i * 0.12) / 0.5), seed=60 + i)
    A.flush(cv)
    stamp(cv, seal('南昌', 44, INK), rx, ry, t, s0)
    if ph >= 1: stamp(cv, seal('安庆', 40, INK), 900, 780, t, s0 + P)
    if ph >= 4: stamp(cv, seal('收复', 44), rx - 170, ry + 120, t, s0 + 4 * P, rot=-6)
    i = max(j for j, (b, *_) in enumerate(NW_DAYS) if ph >= b)
    b, dd, txt = NW_DAYS[i]
    ink_in(cv, text_img(f'{dd} · {txt}', SERIF, 46, PINE, 'Black', bleed=False, spacing=4), W / 2, 1448, t, s0 + b * P, dur=0.2, settle=1.0)
    days = int(lerp(1, 43, clamp(ph / 7.5)))
    fx = Art()
    chars_in(cv, fx, '宁王之乱', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=122)
    fx.flush(cv)
    paste(cv, text_img(f'第{cn_num(days)}天', SERIF, 52, ZHU, 'Black', bleed=False, spacing=4), W / 2, 570, 1, 1)

def art_y_capture(A, cv, t, u):
    A.d['mid'].rectangle((60, 1220, W - 60, 1420), fill=140)
    waves(A, 1230, t, rows=3, amp=6, speed=1.4)
    fire_boat(A, 760, 1250, 80, t, burn=0.7, seed=71)
    boat(A, 420, 1260, 120, t, sail=True)
    person(A, 400, 1190, 150, dir=1, robe=True, hat='crown', kneel=True, bow=30, arm=80, layer='ink')
    person(A, 500, 1190, 150, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('宸濠就擒', 46), 300, 920, t, t - u + P, rot=-5)

def art_y_slander(A, cv, t, u):
    palace(A, 540, GROUND, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 230, dir=1, robe=True, hat='crown', arm=20, layer='ink')
    for k in range(3):
        person(A, 760 + k * 70, GROUND, 160, dir=-1, robe=True, hat='none', bow=30, arm=100, layer='ink')
    wang(A, 220, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    for k in range(int(clamp((u - P) / P) * 3)):
        paste(cv, text_img('谗', BRUSH, 80, ZHU), 760 + k * 70, 1050 - k * 20, 1, 0.9)

def art_y_liangzhi(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 400
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=255)
    lamp(A, 540, GROUND, 160, t, glow=0.4 + 0.6 * ease_out(u / (2 * P)))
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('百死千难中得来', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + 1.5 * P, 0.5)

def art_y_earl(A, cv, t, u):
    scroll(A, 540, 960, 520, 220, u / 0.6, layer='yellow')
    ground(A, GROUND)
    wang(A, 540, GROUND, 160, dir=1, kneel=True, bow=40, arm=80)
    A.flush(cv)
    if u > 0.5:
        ink_in(cv, text_img('新建伯', BRUSH, 110, ZHU), W / 2, 960, t, t - u + 0.5, dur=0.3, settle=1.2)

# ================================================================ 第五回 此心光明
def art_y_mourning(A, cv, t, u):
    A.d['mid'].rectangle((380, 900, 700, 1220), fill=230)
    A.d['ink'].rectangle((470, 940, 610, 1180), fill=255)
    for k in range(10):
        q = (t * 0.25 + k / 10) % 1
        x = 440 + (k * 23) % 200; y = lerp(1180, 760, q)
        A.d['wash'].ellipse((x - 10, y - 10, x + 10, y + 10), fill=int(160 * math.sin(math.pi * q)))
    ground(A, GROUND)
    wang(A, 540, GROUND, 170, dir=1, kneel=True, bow=55, arm=60)
    A.flush(cv)
    stamp(cv, seal('丁忧', 52, INK), 860, 960, t, t - u + P, rot=6)

def art_y_jishan(A, cv, t, u):
    palace(A, 540, 1120, 480, layer='mid')
    ground(A, GROUND)
    wang(A, 540, GROUND - 30, 200, dir=1, arm=lerp(30, 80, 0.5 + 0.5 * math.sin(t * 2)))
    n = int(clamp(u / (2.5 * P)) * 40) + 1
    for i in range(n):
        ring = i // 10; j = i % 10
        a = math.pi * (j + 0.5) / 10
        x = 540 + (240 + ring * 90) * math.cos(a); y = GROUND + 10 - (60 + ring * 20) * math.sin(a) * 0.25 - ring * 6
        sitter(A, x, y, 70 - ring * 6, dir=1 if x < 540 else -1, layer='ink' if ring < 2 else 'mid')
    A.flush(cv)
    paste(cv, text_img(f'环坐而听者{cn_num(n * 10)}人' if n < 40 else '环坐而听者数百人', SERIF, 44, PINE, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_y_four(A, cv, t, u):
    A.d['wash'].ellipse((760, 660, 880, 780), fill=255)
    A.d['ocean'].polygon([(120, 1300), (500, 1260), (960, 1300), (960, 1420), (120, 1420)], fill=120)
    A.d['ink'].arc((360, 1170, 720, 1330), 180, 360, fill=255, width=10)
    sitter(A, 470, 1250, 110, dir=1)
    sitter(A, 610, 1250, 110, dir=-1)
    wang(A, 540, 1270, 160, dir=1, arm=60)
    A.flush(cv)
    lines = ['无善无恶心之体', '有善有恶意之动', '知善知恶是良知', '为善去恶是格物']
    for i, ln in enumerate(lines):
        type_in(cv, text_img(ln, SERIF, 46, ZHU if i == 2 else INK, 'Black', bleed=False, spacing=6), W / 2, 760 + i * 74, t, t - u + 0.2 + i * 0.6 * P, 0.4)

def art_y_sitian(A, cv, t, u):
    for k in range(5):
        x = 120 + k * 210
        A.d['pine'].polygon([(x - 150, GROUND), (x - 40, GROUND - 420 - (k % 2) * 160), (x + 40, GROUND - 400 - (k % 2) * 160), (x + 150, GROUND)], fill=200)
    ground(A, GROUND)
    x = lerp(-120, 480, ease_out(u / (3 * P)))
    carriage(A, x, GROUND, 140, dir=1, wheel=u * 5, ph=t * 7, moving=u < 3 * P, canopy=True)
    for k in range(5):
        person(A, x - 220 - k * 80, GROUND, 130, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('抱病出征', 44), 860, 900, t, t - u + P, rot=6)

def art_y_last_words(A, cv, t, u):
    A.d['mid'].rectangle((60, 1240, W - 60, 1420), fill=130)
    waves(A, 1250, t, rows=3, amp=4, speed=0.8)
    A.d['ink'].polygon([(240, 1230), (840, 1230), (800, 1290), (280, 1290)], fill=255)
    A.d['mid'].rectangle((380, 1120, 700, 1230), fill=230)
    sitter(A, 540, 1228, 120, dir=-1, bow=lerp(0, 25, ease_out((u - 2 * P) / 1.0)))
    lt = clamp(1 - (u - 2.5 * P) / 0.8)
    lamp(A, 660, 1228, 50, t, glow=lt)
    A.flush(cv)
    if u > P:
        fx = Art()
        chars_in(cv, fx, '此心光明', BRUSH, 120, ZHU, W / 2, 820, t, t - u + P, stagger=0.15, drop=20, splash=False, seed=401)
        fx.flush(cv)
    if u > 2.2 * P:
        type_in(cv, text_img('亦复何言', SERIF, 56, INK, 'Black', bleed=False, spacing=10), W / 2, 950, t, t - u + 2.2 * P, 0.5)

def art_y_temple(A, cv, t, u):
    palace(A, 540, GROUND, 620, layer='mid')
    ground(A, GROUND)
    for k in range(4):
        x = 280 + k * 170
        if k in (1, 2): continue
        A.d['ink'].rectangle((x - 22, GROUND - 260, x + 22, GROUND - 210), fill=255)
        A.d['ink'].rectangle((x - 14, GROUND - 210, x + 14, GROUND), fill=255)
    lamp(A, 540, GROUND, 90, t, glow=1.0)
    for i, (nm, x) in enumerate((('日本', 230), ('朝鲜', 850))):
        p = ease_out((u - P - i * 0.3) / 0.6)
        A.d['candle'].line((540, 1200, lerp(540, x, p), lerp(1200, 900, p)), fill=180, width=8)
    A.flush(cv)
    stamp(cv, seal('从祀孔庙', 46), 540, 860, t, t - u + 0.4, rot=0)
    for i, (nm, x) in enumerate((('日本', 230), ('朝鲜', 850))):
        if u > P + i * 0.3 + 0.6:
            stamp(cv, seal(nm, 40, PINE), x, 880, t, t - u + P + i * 0.3 + 0.6)

def art_y_legacy(A, cv, t, u):
    for k, x in enumerate((140, 250, 830, 940)):
        bamboo(A, x, GROUND, 820 - 60 * (k % 2), t, width=16, seed=500 + k)
    lamp(A, 540, GROUND, 120, t, glow=1.0)
    ground(A, GROUND)

# ================================================================ script
CHAPTERS = {16: ('第一回', '少年立志'), 48: ('第二回', '格竹之惑'), 80: ('第三回', '龙场悟道'),
            112: ('第四回', '文臣用兵'), 144: ('第五回', '此心光明')}

CARDS = [
    C(0, 2, 'hook', 'num', num='七天七夜', line='盯着竹子看', art=art_y_hook_bamboo),
    C(2, 4, 'war', 'num', num='四十余天', line='平定藩王叛乱', art=art_y_hook_war),
    C(4, 6, 'night', 'num', num='贬到龙场', line='在山洞里悟道', art=art_y_hook_cave),
    C(6, 8, 'hook', 'num', num='三不朽', line='立德 立功 立言', art=art_y_hook_three),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 少年立志
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1472, main='瑞云送子', sub='生于浙江余姚 · 初名王云', note='传说 祖母梦神人驾云送子', art=art_y_cloud_birth),
    C(22, 26, 'life', 'card', year=1476, main='五岁不语', sub='改名守仁 · 方才开口', note='传说 一高僧点破', art=art_y_silent),
    C(26, 30, 'court', 'card', year=1482, main='随父进京', sub='父亲王华 · 高中状元', note='年十一 寓京师', art=art_y_to_capital),
    C(30, 34, 'court', 'card', year=1483, main='第一等事', sub='塾师说是读书登第 · 他说是做圣贤', note='何为第一等事', art=art_y_first_thing),
    C(34, 38, 'war', 'card', year=1486, main='出游居庸关', sub='纵观塞外 · 慨然有经略四方之志', art=art_y_juyong),
    C(38, 42, 'night', 'card', year=1488, main='新婚夜失踪', sub='与道士对坐 · 忘了回家', note='次早方迎归', art=art_y_wedding_night),
    C(42, 46, 'works', 'card', year=1489, main='拜访娄谅', sub='得闻 圣人必可学而至', note='遂深契之', art=art_y_loujing),
    C(46, 48, 'empire', 'card', year=1492, main='乡试中举', sub='浙江乡试', art=art_y_exam),
    # ---- 第二回 格竹之惑
    C(48, 50, 'works', 'chapter'),
    C(50, 58, 'works', 'card', year=1492, main='庭前格竹', sub='想从竹子里格出天理 · 七日病倒', note='格物致知 一无所得', art=art_y_gezhu),
    C(58, 62, 'night', 'card', year=1496, main='会试落第', sub='世以不第为耻 · 吾以不第动心为耻', note='两次落榜 处之泰然', art=art_y_failed),
    C(62, 66, 'empire', 'card', year=1499, main='进士及第', sub='观政工部 · 初入仕途', art=art_y_jinshi),
    C(66, 70, 'works', 'card', year=1502, main='阳明洞', sub='告病归越 · 筑室会稽山', note='自号阳明子', art=art_y_yangming_cave),
    C(70, 74, 'court', 'card', year=1505, main='京师讲学', sub='开门授徒 · 结交湛若水', note='倡言身心之学', art=art_y_teaching_capital),
    C(74, 78, 'war', 'card', year=1506, main='廷杖四十', sub='上疏救言官 · 触怒刘瑾', note='几死复苏', art=art_y_beaten),
    C(78, 80, 'death', 'card', year=1506, main='贬谪龙场', sub='贵州龙场驿 · 一个驿丞', art=art_y_exile),
    # ---- 第三回 龙场悟道
    C(80, 82, 'night', 'chapter'),
    C(82, 86, 'night', 'card', year=1507, main='钱塘遁迹', sub='刘瑾派人追杀 · 托言投江', note='一说 伪作投水', art=art_y_fake_drown),
    C(86, 90, 'fate', 'card', year=1508, main='万山丛棘', sub='蛇虺魍魉 · 言语不通', note='居夷处困', art=art_y_wilds),
    C(90, 94, 'night', 'card', year=1508, main='石椁自誓', sub='生死一念 · 置之度外', note='为石椁 日夜端居澄默', art=art_y_coffin),
    C(94, 102, 'night', 'card', year=1508, main='龙场悟道', sub='中夜忽悟格物致知之旨', note='不觉呼跃 从者皆惊', art=art_y_wudao),
    C(102, 106, 'works', 'card', year=1509, main='知行合一', sub='知是行之始 · 行是知之成', note='贵阳书院 首倡此说', art=art_y_zhixing),
    C(106, 110, 'court', 'card', year=1510, main='刘瑾伏诛', sub='复出 · 任庐陵知县', art=art_y_liujin_falls),
    C(110, 112, 'war', 'card', year=1516, main='巡抚南赣', sub='受命平定山中盗匪', art=art_y_nangan),
    # ---- 第四回 文臣用兵
    C(112, 114, 'war', 'chapter'),
    C(114, 118, 'court', 'card', year=1517, main='十家牌法', sub='十家一牌 · 断了匪寇耳目', note='一家有犯 十家连坐', art=art_y_tenhouse),
    C(118, 122, 'war', 'card', year=1518, main='山中贼', sub='破山中贼易 · 破心中贼难', note='数月间 积年匪患尽平', art=art_y_heart_thief),
    C(122, 130, 'war', 'ningwang'),
    C(130, 134, 'empire', 'card', year=1519, main='生擒宁王', sub='鄱阳湖一战 · 叛军覆灭', note='以文臣之身 立不世之功', art=art_y_capture),
    C(134, 138, 'court', 'card', year=1520, main='功高遭忌', sub='武宗南巡 · 宦官构陷', note='将宸濠交与张永', art=art_y_slander),
    C(138, 142, 'fate', 'card', year=1521, main='致良知', sub='一生学问 · 归于三字', note='百死千难中得来', art=art_y_liangzhi),
    C(142, 144, 'empire', 'card', year=1521, main='封新建伯', sub='论平宁王之功', art=art_y_earl),
    # ---- 第五回 此心光明
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'death', 'card', year=1522, main='丁忧归越', sub='父亲去世 · 居家守制', art=art_y_mourning),
    C(150, 154, 'life', 'card', year=1524, main='稽山讲学', sub='四方来学 · 寺院住满', note='环坐而听者 常数百人', art=art_y_jishan),
    C(154, 158, 'night', 'card', year=1527, main='天泉证道', sub='临行前 留下四句教', art=art_y_four),
    C(158, 162, 'war', 'card', year=1528, main='出征思田', sub='抱病平定广西', note='不战而降数万人', art=art_y_sitian),
    C(162, 166, 'death', 'card', year=1529, main='此心光明', sub='归途中 病逝于南安舟中', note='问遗言 微哂曰', art=art_y_last_words),
    C(166, 170, 'end', 'card', year=1584, main='从祀孔庙', sub='心学流传 · 远播日本朝鲜', note='立德立功立言 真三不朽', art=art_y_temple),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
ALL = (L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb, Cc, Zg, Yf, Wx, Qj, Zh)
for mod in ALL:
    mod.CHAPTERS = CHAPTERS
G.CHAPTER_BEATS = [0, 16, 48, 80, 112, 144, END_BEAT]
L.CUTS = sorted({c[0] for c in CARDS if c[0] not in G.CHAPTER_BEATS})

def year_at(t):
    pts = sorted((bt(c[0]), c[4]['year']) for c in CARDS if 'year' in c[4])
    if t <= pts[0][0]: return pts[0][1]
    prev = pts[0][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t < t1: return lerp(prev, y0, ease_out((t - t0) / 0.4))
        prev = y0
    return lerp(prev, pts[-1][1], ease_out((t - pts[-1][0]) / 0.4))
for mod in (G,) + ALL:
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_year(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=PINE + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    def art(A, cv_, t_, u_):
        for j, x in enumerate((150, 270, 820, 930)):
            bamboo(A, x, 1460, 900, t_, width=18, seed=900 + j)
        lamp(A, 760, 1460, 110, t_, glow=ease_out(u_ / (2 * P)))
        wang(A, 450, 1460, 700, dir=1, arm=lerp(-5, 40, ease_out(u_ / (2 * P))))
    stage(cv, t, c, art)
    fx = Art()
    ink_in(cv, text_img('王守仁 · 号阳明', SERIF, 46, PINE, 'Black', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '王阳明', BRUSH, 210, INK, W / 2, 450, t, s0, stagger=0.1, seed=77)
    fx.flush(cv)
    stamp(cv, seal('伯安', 66), 900, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元1472 — 1529', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '千古完人？', BRUSH, 120, PINE, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '空谈心性？', BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    art_y_legacy(A, cv, t, u)
    A.flush(cv, alpha=clamp(u / 0.6) * 0.25)
    fx = Art()
    chars_in(cv, fx, '此心光明', BRUSH, 220, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('阳明', 60), W / 2 + 390, 540, t, END + 0.45, rot=6)
    type_in(cv, text_img('他说 知而不行 只是未知', SERIF, 48, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.4)
    type_in(cv, text_img('五百年后 仍有人照着活', SERIF, 52, INK, 'Bold', bleed=False, spacing=4), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '知行合一', BRUSH, 100, PINE, W / 2, 1190, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('你做到了吗？评论区聊聊', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=PINE + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(250, 250, 245, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=CANDLE + (230,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 张居正', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, ningwang=scene_ningwang, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第拾捌集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 570, 170, 1, 1)
    if t < bt(8):
        q = text_img('一个文官 · 凭什么被称为千古完人？', SERIF, 36, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 340, 335, W / 2 + 340, 335), fill=PINE + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, PINE, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=PINE + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=CANDLE + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(max(1, int(round(yr - AGE0)))) + '岁' if yr <= DIED + 0.5 else '身后'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=PINE + (255,))
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
    if ff.returncode != 0: sys.exit(1)
    print('done', out)
