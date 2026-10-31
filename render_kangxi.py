# 千古人物志 · 第柒集 · 康熙玄烨 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈）。每一幕画面均为本集新画，不重复。
# 本集特色：明黄宝蓝 · 浑天仪章回卡 · 黄菊飘落 · 如意云头边角 · 八拍「智擒鳌拜」 · 六拍「收复台湾」 · 六扇屏风回顾
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_mingtaizu as M        # engine + helpers from earlier episodes
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
from render_wudi import camel
from render_mingtaizu import big_ship, cn_year
from render_songtaizu import tent

F.RIPPLE = False
# this episode: ink and vermilion drawn last so figures stay visible on the yellow thrones/scrolls
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

BORN, DIED = 1654, 1722
END_BEAT = 170
HUANG = (200, 152, 28)              # 明黄
LAN = (34, 78, 132)                 # 宝蓝

def rect(A, layer, x0, y0, x1, y1, **kw):
    A.d[layer].rectangle((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), **kw)

# ================================================================ episode look
WM = dict(hook='康', life='烨', court='政', night='夜', war='戰', empire='熙', works='疆', fate='嗣', death='园', end='康')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire', 'fate'):
    G.THEMES[k]['part'] = 'chrys'
for k in ('night', 'death', 'works'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (HUANG, 260, (W * 0.5, 820))
G.THEMES['works']['sun'] = (LAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (HUANG, 210, (W * 0.5, 720))
G.THEMES['hook']['tint'] = (1.02, 1.0, 0.94)
G.THEMES['life']['tint'] = (1.03, 1.0, 0.92)
G.base_bg.cache_clear()

MTN_COL = {'night': (56, 54, 66), 'death': (64, 62, 64), 'war': (104, 62, 40), 'works': (70, 86, 110)}
def draw_background(t, theme):
    """Amber-ochre ranges like Qing court landscape painting."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 170, 120), (160, 128, 78), MTN_COL.get(theme, (116, 88, 50))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'chrys':
        return M.particle_sprite(kind, q)
    s = 40
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [(222, 170, 40), (240, 196, 70), (200, 140, 30)][q]
    for j in range(10):
        a = j * math.pi / 5
        d.line((20, 20, 20 + 13 * math.cos(a), 20 + 13 * math.sin(a)), fill=col + (230,), width=3)
    d.ellipse((16, 16, 24, 24), fill=(170, 100, 20, 235))
    return im.filter(ImageFilter.GaussianBlur(0.5))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """如意云头 corners in imperial yellow with a 宝蓝 double rule."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 160, y), fill=LAN + (200,), width=3); d.line((x, y, x, y + sy * 160), fill=LAN + (200,), width=3)
        cx, cy = x + sx * 34, y + sy * 34
        for a0 in (0, 90, 180, 270):
            ox, oy = cx + 13 * math.cos(math.radians(a0 + 45)), cy + 13 * math.sin(math.radians(a0 + 45))
            d.ellipse((ox - 11, oy - 11, ox + 11, oy + 11), outline=HUANG + (230,), width=3)
        d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=ZHU + (220,))
G.draw_frame_border = draw_frame_border

# ================================================================ 浑天仪 chapter card
def armillary(A, cx, cy, r, p, t, rings=3, layer='ink'):
    tilts = [0, 90, 23.5, 60, 120]
    for i in range(rings):
        a = math.radians(tilts[i % len(tilts)])
        phi = t * (0.4 + 0.15 * i) * (1 if i % 2 == 0 else -1)
        n = int(64 * ease_out(clamp(p * 1.3 - i * 0.12))) + 1
        pts = []
        for j in range(n + 1):
            th = 2 * math.pi * j / 64
            X, Y, Zz = math.cos(th), math.sin(th) * math.cos(a), math.sin(th) * math.sin(a)
            xp = X * math.cos(phi) + Zz * math.sin(phi)
            pts.append((cx + r * xp, cy - r * Y))
        if len(pts) > 1:
            A.d['gold' if i == 0 else layer].line(pts, fill=255, width=7 if i == 0 else 5)
    A.d[layer].ellipse((cx - r * 0.09, cy - r * 0.09, cx + r * 0.09, cy + r * 0.09), fill=255)
    if p > 0.3:
        A.d[layer].line((cx, cy + r, cx, cy + r * 1.25), fill=255, width=10)
        A.d[layer].polygon([(cx - r * 0.5, cy + r * 1.38), (cx + r * 0.5, cy + r * 1.38), (cx + r * 0.25, cy + r * 1.22), (cx - r * 0.25, cy + r * 1.22)], fill=255)
        for sgn in (-1, 1):
            A.d[layer].line((cx + sgn * r * 0.4, cy + r * 1.3, cx + sgn * r * 1.0, cy + r * 0.3), fill=180, width=5)

CH_RINGS = {16: 2, 48: 3, 80: 3, 112: 4, 144: 5}
def art_armillary_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    armillary(A, 540, 820, 270, u / 0.7, t, rings=CH_RINGS.get(kb, 3))
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_armillary_chapter)
    ink_in(cv, text_img(no, SERIF, 56, LAN, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ primitives
def qing_hat(A, x, y, h, layer='ink'):
    """Qing official's conical hat with red tassel, on a standing figure at (x, y) of height h."""
    hy = y - 0.955 * h
    A.d[layer].polygon([(x - 0.11 * h, hy + 0.03 * h), (x + 0.11 * h, hy + 0.03 * h), (x, hy - 0.07 * h)], fill=255)
    A.d['red'].ellipse((x - 0.03 * h, hy - 0.10 * h, x + 0.03 * h, hy - 0.04 * h), fill=255)

def official(A, x, y, h, dir=1, layer='ink', **kw):
    person(A, x, y, h, dir=dir, hat='none', layer=layer, **kw)
    qing_hat(A, x, y, h, layer)

def throne(A, x, base, s=1.0, layer='yellow'):
    A.d[layer].rounded_rectangle((x - 90 * s, base - 230 * s, x + 90 * s, base - 60 * s), radius=int(30 * s), fill=255)
    A.d[layer].rectangle((x - 120 * s, base - 70 * s, x + 120 * s, base - 40 * s), fill=255)
    A.d['ink'].rectangle((x - 110 * s, base - 40 * s, x + 110 * s, base), fill=255)

def deer(A, x, y, s, dir=1, ph=0.0, layer='ink'):
    horse(A, x, y, s, dir, ph, layer=layer)
    hx, hy = x + dir * 0.72 * s, y - 1.02 * s
    for k in (-1, 1):
        A.d[layer].line((hx, hy, hx + dir * 0.10 * s + k * 0.06 * s, hy - 0.30 * s), fill=255, width=3)
        A.d[layer].line((hx + dir * 0.05 * s, hy - 0.15 * s, hx + dir * 0.18 * s, hy - 0.22 * s), fill=255, width=3)

def cannon(A, x, y, s, dir=1, fire=0.0):
    A.d['ink'].polygon([(x, y - 0.25 * s), (x + dir * s, y - 0.4 * s), (x + dir * s, y - 0.22 * s), (x, y - 0.08 * s)], fill=255)
    A.d['ink'].ellipse((x - 0.25 * s, y - 0.3 * s, x + 0.25 * s, y + 0.0 * s), outline=255, width=4)
    if fire > 0:
        mx, my = x + dir * s * 1.05, y - 0.32 * s
        r = 0.5 * s * ease_out(fire)
        A.d['wash'].ellipse((mx - r + dir * r * 0.6, my - r, mx + r + dir * r * 0.6, my + r), fill=int(255 * (1 - fire * 0.6)))

def lantern(A, x, y, t, k=0, size=26):
    sw = 6 * math.sin(t * 2 + k)
    A.d['ink'].line((x, y - 60, x + sw, y), fill=255, width=2)
    A.d['red'].ellipse((x + sw - size, y, x + sw + size, y + size * 2.4), fill=255)

def willow(A, x, top, t):
    A.d['ink'].line((x, GROUND, x + 10, top), fill=255, width=10)
    for k in range(9):
        sx = x - 60 + k * 18
        pts = [(sx + 14 * math.sin(t * 1.5 + k + j * 0.4) * j / 8, top + 20 + j * 40) for j in range(9)]
        A.d['mid'].line(pts, fill=255, width=3)

# ================================================================ hooks
def art_k_boy_throne(A, cv, t, u):
    for i, x in enumerate((140, 270, 810, 940)):
        lean = 10 + 12 * ease_out(u / (2 * P))
        official(A, x, GROUND, 560, dir=1 if x < 540 else -1, bow=lean, arm=30, layer='wash')
    throne(A, 540, GROUND, 1.5)
    person(A, 540, GROUND - 100, 130, dir=1, hat='crown', arm=20, layer='ink')

def art_k_cup(A, cv, t, u):
    A.d['ink'].rectangle((160, 1080, 900, 1110), fill=255)
    for lx in (200, 840): A.d['ink'].rectangle((lx, 1110, lx + 24, GROUND), fill=255)
    q = clamp(u / (0.6 * P))
    cx = lerp(820, 940, q); cy = 1050 + (GROUND - 40 - 1050) * q * q
    if q < 1:
        pts = [(-30, -30), (30, -30), (20, 30), (-20, 30)]
        A.d['cobalt'].polygon([rotp((cx + a, cy + b), (cx, cy), q * 4) for a, b in pts], fill=255)
    else:
        r = random.Random(3)
        v = u - 0.6 * P
        for k in range(9):
            a = r.uniform(math.pi, 2 * math.pi); d_ = 140 * ease_out(v / 0.3)
            sx, sy = 940 + d_ * math.cos(a), GROUND - 20 + 0.4 * d_ * math.sin(a)
            A.d['cobalt'].polygon([(sx - 10, sy), (sx + 6, sy - 10), (sx + 12, sy + 6)], fill=255)
        for k in range(4):
            x = lerp(-100 + k * 60, 300 + k * 80, ease_out(v / 0.4))
            person(A, x, GROUND, 200, dir=1, robe=False, ph=t * 12 + k, arm=100, layer='ink' if k % 2 else 'mid')
    ground(A, GROUND)

def art_k_island(A, cv, t, u):
    A.d['wash'].rectangle((60, 1170, W - 60, 1380), fill=150)
    A.d['mid'].polygon([(560, 1200), (650, 1000), (720, 1060), (800, 900), (900, 1080), (1020, 1200)], fill=255)
    waves(A, 1200, t, rows=4, amp=10, speed=2.4)
    x = lerp(140, 520, ease_out(u / (1.5 * P)))
    boat(A, x, 1240, 200, t)
    if u > P:
        p = ease_out((u - P) / 0.4)
        flag(A, 800, lerp(1000, 900, p), 220 * p, t, w=110, layer='yellow')

def art_k_calendar(A, cv, t, u):
    A.d['ink'].rounded_rectangle((330, 820, 750, 1300), radius=20, fill=255)
    A.d['red'].rectangle((330, 820, 750, 920), fill=255)
    A.d['wash'].rectangle((350, 940, 730, 1280), fill=0)
    for k in range(5):
        A.d['ink'].ellipse((370 + k * 80, 800, 400 + k * 80, 840), outline=255, width=5)
    n = min(61, 1 + int(clamp(u / (1.7 * P)) * 60))
    A.d['ink'].text((540 - font(SERIF, 130, 'Black').getlength(str(n)) / 2, 1030), str(n), font=font(SERIF, 130, 'Black'), fill=255)
    for k in range(5):
        q = ((u * 3 + k / 5) % 1)
        x, y = 540 - 300 * q, 980 - 300 * q
        A.d['mid'].polygon([rotp((x + a, y + b), (x, y), q * 3) for a, b in ((-60, -40), (60, -40), (60, 40), (-60, 40))], fill=int(200 * (1 - q)))

# ================================================================ 第一回
def art_k_birth(A, cv, t, u):
    A.d['wash'].ellipse((780, 640, 880, 740), fill=255); A.d['wash'].ellipse((806, 630, 906, 730), fill=0)
    palace(A, 540, GROUND, 640, layer='mid')
    for k, x in enumerate((180, 330, 750, 900)):
        lantern(A, x, 1000, t, k, size=24)
    x = walk_x(120, 400, u, 3 * P)
    person(A, x, GROUND, 190, dir=1, female=True, arm=60, ph=t * 5, layer='ink')
    A.d['red'].ellipse((x + 50, GROUND - 120, x + 80, GROUND - 80), fill=255)

def art_k_pox(A, cv, t, u):
    A.d['mid'].rectangle((240, 1260, 760, 1290), fill=255)
    for lx in (260, 730): A.d['mid'].rectangle((lx, 1290, lx + 20, GROUND), fill=255)
    A.d['ink'].ellipse((260, 1205, 320, 1260), fill=255)
    A.d['ink'].rounded_rectangle((320, 1215, 700, 1260), radius=18, fill=255)
    official(A, 900, GROUND, 260, dir=-1, arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    cx, cy, r = 600, 960, 150
    A.d['wash'].ellipse((cx - r, cy - r, cx + r, cy + r), fill=200)
    A.d['ink'].ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=5)
    grow = clamp(u / (1.5 * P)); fade = clamp((u - 2.5 * P) / (1.2 * P))
    rr = random.Random(9)
    for k in range(int(40 * grow)):
        a = rr.uniform(0, 2 * math.pi); d_ = rr.uniform(0, 0.8) * r
        A.d['red'].ellipse((cx + d_ * math.cos(a) - 6, cy + d_ * math.sin(a) - 6, cx + d_ * math.cos(a) + 6, cy + d_ * math.sin(a) + 6), fill=int(255 * (1 - 0.7 * fade)))

def art_k_coronation(A, cv, t, u):
    for k in range(8):
        y = GROUND - k * 40; w = 420 - k * 26
        A.d['mid'].rectangle((540 - w, y - 40, 540 + w, y), fill=255)
    A.d['red'].polygon([(470, GROUND), (610, GROUND), (570, GROUND - 320), (510, GROUND - 320)], fill=255)
    throne(A, 540, GROUND - 320, 0.9)
    q = ease_out(u / (3 * P))
    y = lerp(GROUND, GROUND - 320, q)
    person(A, 540, y, lerp(130, 100, q), dir=1, hat='crown', arm=10, ph=t * 5 if q < 0.98 else None, layer='ink')
    for k in range(4):
        for side in (-1, 1):
            official(A, 540 + side * (480 + (k % 2) * 60), GROUND - k * 40, 120, dir=-side, kneel=True, bow=45, arm=60, layer='ink')

REGENTS = [('索尼', 200), ('苏克萨哈', 410), ('遏必隆', 620), ('鳌拜', 850)]
def art_k_regents(A, cv, t, u):
    g = ease_out(u / (3 * P))
    for i, (nm, x) in enumerate(REGENTS):
        h = lerp(300, 260, g) if i < 3 else lerp(300, 440, g)
        official(A, x, GROUND, h, dir=-1 if i == 3 else 1, arm=30 if i < 3 else 60, layer='mid' if i < 3 else 'ink')
    A.flush(cv)
    for i, (nm, x) in enumerate(REGENTS):
        h = lerp(300, 260, g) if i < 3 else lerp(300, 440, g)
        stamp(cv, seal(nm, 34 if len(nm) > 2 else 42, ZHU if i < 3 else INK), x, GROUND - h - 90, t, t - u + i * 0.18)

def art_k_aobai(A, cv, t, u):
    throne(A, 280, 1180, 0.8)
    person(A, 280, 1100, 110, dir=1, hat='crown', arm=20, layer='ink')
    A.d['mid'].rectangle((60, 1180, 500, GROUND), fill=150)
    x = walk_x(980, 640, u, 2 * P)
    official(A, x, GROUND, 360, dir=-1, ph=t * 5 if u < 2 * P else None, arm=-20, robe=True, layer='ink')
    A.d['ink'].line((x + 40, GROUND - 170, x + 120, GROUND - 40), fill=255, width=8)
    fall = -80 * ease_out((u - 2.5 * P) / 0.3) if u > 2.5 * P else 0
    official(A, 440, GROUND, 230, dir=1, kneel=True, bow=40, arm=70, fall=fall, layer='mid')

def art_k_xiaozhuang(A, cv, t, u):
    for k in range(4):
        A.d['mid'].line((620 + k * 90, 800, 620 + k * 90, 1080), fill=255, width=4)
        A.d['mid'].line((600, 820 + k * 80, 920, 820 + k * 80), fill=255, width=4)
    ground(A, GROUND)
    person(A, 330, GROUND, 300, dir=1, female=True, hat='crown', kneel=True, bow=5, arm=lerp(30, 70, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    person(A, 700, GROUND, 190, dir=-1, kneel=True, bow=30, arm=95, layer='ink')
    A.d['yellow'].rectangle((560, GROUND - 120, 640, GROUND - 100), fill=255)
    A.d['ink'].rectangle((500, GROUND - 90, 512, GROUND), fill=255)
    fh = 30 + 6 * math.sin(t * 15)
    A.d['red'].polygon([(498, GROUND - 90), (514, GROUND - 90), (508, GROUND - 90 - fh), (504, GROUND - 90 - fh)], fill=255)

def art_k_qinzheng(A, cv, t, u):
    A.d['mid'].rectangle((420, 860, 860, 1280), fill=150)
    A.d['ink'].rectangle((400, 840, 880, 860), fill=255); A.d['ink'].rectangle((400, 1280, 880, 1300), fill=255)
    fo = font(BRUSH, 170)
    for i, ch in enumerate('亲政'):
        if u > 0.3 + i * P:
            A.d['ink'].text((560, 880 + i * 190), ch, font=fo, fill=255)
    person(A, 250, GROUND, 290, dir=1, hat='crown', arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    A.d['ink'].line((310, GROUND - 230, 470 + 40 * math.sin(t * 4), 1040), fill=255, width=12)
    ground(A, GROUND)

def art_k_buku(A, cv, t, u):
    ground(A, GROUND)
    kk = (t - G.B0) / P
    hit = math.exp(-((kk % 1) * P) / 0.15)
    for i, x in enumerate((220, 540, 860)):
        bob = 10 * hit
        person(A, x - 60, GROUND - bob, 210, dir=1, robe=False, bow=35, arm=80, layer='ink')
        fall = -70 * ease_out((u - P - i * 0.1) / 0.3) if (u > P and i == 1) else 0
        person(A, x + 60, GROUND - bob, 210, dir=-1, robe=False, bow=35, arm=80, fall=fall, layer='mid')

# ================================================================ 第二回
def art_k_capture(A, cv, t, u):
    """8-beat set piece: 鳌拜 strides in → teacup falls → the wrestlers pounce → he is pinned."""
    ph = u / P
    for k in range(5):
        x = 120 + k * 210
        A.d['mid'].rectangle((x, 800, x + 36, GROUND), fill=255)
    A.d['mid'].rectangle((60, 770, W - 60, 800), fill=255)
    ground(A, GROUND)
    throne(A, 230, 1240, 0.75)
    person(A, 230, 1180, 120, dir=1, hat='crown', arm=60 if 2 <= ph < 3 else 20, layer='ink')
    if 2 <= ph:
        q = clamp((u - 2 * P) / (0.5 * P))
        cy = 1110 + (GROUND - 1110) * q * q
        if q < 1:
            A.d['cobalt'].polygon([(300, cy - 20), (330, cy - 20), (324, cy + 10), (306, cy + 10)], fill=255)
        else:
            for k in range(6):
                a = math.pi + k * 0.6
                A.d['cobalt'].polygon([(315 + 60 * math.cos(a), GROUND - 10 + 20 * math.sin(a)), (325 + 60 * math.cos(a), GROUND - 18 + 20 * math.sin(a)), (322 + 60 * math.cos(a), GROUND - 4 + 20 * math.sin(a))], fill=255)
    ax = walk_x(1000, 680, u, 2 * P)
    fall = 0 if ph < 5 else 85 * ease_out((u - 5 * P) / (0.6 * P))
    official(A, ax, GROUND, 360, dir=-1, ph=t * 5 if ph < 2 else None, arm=-15 if ph < 3 else 140, fall=fall, layer='ink') if fall < 1 else \
        person(A, ax, GROUND, 360, dir=-1, robe=True, arm=140, fall=fall, layer='ink')
    starts = [(380, GROUND), (480, GROUND), (900, GROUND), (1000, GROUND)]
    for i, (sx, sy) in enumerate(starts):
        if ph < 3:
            person(A, sx, sy, 180, dir=1 if sx < ax else -1, robe=False, kneel=True, bow=10, arm=40, layer='mid')
        else:
            q = ease_out((u - 3 * P - i * 0.08) / (1.2 * P))
            tx = ax + (-1 if sx < ax else 1) * (60 + i % 2 * 50) - (180 if fall > 40 else 0) * 0.5
            x = lerp(sx, tx, q); y = sy - 160 * math.sin(math.pi * q) * (1 if q < 1 else 0)
            person(A, x, y, 190, dir=1 if sx < ax else -1, robe=False, arm=110, bow=30 * q, ph=None, layer='ink' if i % 2 else 'mid')
    if ph >= 6.5:
        A.flush(cv)
        stamp(cv, seal('擒', 90), 820, 900, t, t - u + 6.5 * P, rot=8)

def art_k_cheshan(A, cv, t, u):
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (330, 730): A.d['ink'].rectangle((lx, 1280, lx + 20, GROUND), fill=255)
    person(A, 540, 1250, 220, dir=1, hat='crown', arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    A.d['mid'].rectangle((600, 1220, 720, 1248), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    d = ImageDraw.Draw(cv)
    for i, (nm, x) in enumerate((('吴', 260), ('尚', 540), ('耿', 820))):
        stamp(cv, seal(nm, 64, INK), x, 900, t, t - u)
        q = ease_out((u - (1 + i) * P) / 0.25)
        if q > 0:
            d.line((x - 60, 840, x - 60 + 120 * q, 840 + 120 * q), fill=ZHU + (240,), width=9)

def art_k_wu(A, cv, t, u):
    for k in range(6):
        flames(A, 120 + k * 170, 1130, 90, 110 + 30 * math.sin(t + k), t + k, n=3, seed=60 + k, smoke=True)
    ground(A, GROUND)
    x = lerp(-150, 520, ease_out(u / (2.5 * P)))
    rider(A, x, GROUND, 280, 1, t * 11, layer='ink', spear=True)
    pole_x = x - 70
    A.d['ink'].line((pole_x, GROUND - 300, pole_x, GROUND - 640), fill=255, width=6)
    pts_top = [(pole_x + i * 20, GROUND - 640 + 8 * math.sin(t * 6 + i * 0.6)) for i in range(9)]
    pts_bot = [(pole_x + i * 20, GROUND - 480 + 8 * math.sin(t * 6 + i * 0.6)) for i in range(8, -1, -1)]
    A.d['red'].polygon(pts_top + pts_bot, fill=255)
    A.d['red'].text((pole_x + 40, GROUND - 620), '周', font=font(SERIF, 90, 'Black'), fill=0)
    for k in range(4):
        person(A, x - 330 - k * 110, GROUND, 190, dir=1, robe=False, hat='helmet', spear=True, ph=t * 9 + k, layer='mid')

def art_k_chess(A, cv, t, u):
    x0, x1, y0, y1 = 220, 860, 800, 1380
    for i in range(9):
        x = lerp(x0, x1, i / 8)
        A.d['ink'].line((x, y0, x, (y0 + y1) / 2 - 30), fill=200, width=3)
        A.d['ink'].line((x, (y0 + y1) / 2 + 30, x, y1), fill=200, width=3)
    for j in range(10):
        y = lerp(y0, y1, j / 9)
        A.d['ink'].line((x0, y, x1, y), fill=200, width=3)
    A.d['wash'].rectangle((x0, (y0 + y1) / 2 - 30, x1, (y0 + y1) / 2 + 30), fill=180)
    adv = clamp(u / (3.5 * P))
    for i in range(9):
        row = 6 - int(adv * 5 * (0.4 + 0.6 * ((i * 37) % 9) / 8))
        x = lerp(x0, x1, i / 8); y = lerp(y0, y1, row / 9)
        A.d['red'].ellipse((x - 28, y - 28, x + 28, y + 28), fill=255)
    for i in (0, 4, 8):
        x = lerp(x0, x1, i / 8)
        A.d['ink'].ellipse((x - 28, y0 - 28, x + 28, y0 + 28), fill=255)
    if u > 2 * P:
        A.flush(cv)
        stamp(cv, seal('半壁', 54), 860, 760, t, t - u + 2 * P, rot=6)

def art_k_calm(A, cv, t, u):
    A.d['mid'].polygon([(760, 1180), (800, 1060), (840, 1010), (880, 1060), (920, 1180)], fill=255)
    A.d['mid'].rectangle((825, 940, 855, 1010), fill=255)
    A.d['mid'].rectangle((720, 1180, 960, 1210), fill=255)
    ground(A, GROUND)
    x = lerp(60, 480, ease_out(u / (4 * P)))
    rider(A, x, GROUND, 230, 1, t * 4, layer='ink')
    person(A, x - 150, GROUND, 200, dir=1, robe=False, ph=t * 4, arm=150, layer='ink')
    A.d['ink'].line((x - 130, GROUND - 180, x - 30, GROUND - 460), fill=255, width=5)
    A.d['yellow'].chord((x - 130, GROUND - 520, x + 70, GROUND - 400), 180, 360, fill=255)
    for k in range(4):
        official(A, 700 + k * 90, GROUND, 160, dir=-1, kneel=True, bow=40, arm=60, layer='mid')

def art_k_kunming(A, cv, t, u):
    city_wall(A, 60, W - 60, 1100, gate_x=540, label='昆明', open_=ease_out((u - 2 * P) / 0.5))
    ground(A, GROUND)
    pole = (540, 900)
    A.d['ink'].line((pole[0], 1000, pole[0], 800), fill=255, width=6)
    swap = u > 1.5 * P
    pts_top = [(540 + i * 20, 800 + 8 * math.sin(t * 6 + i * 0.6)) for i in range(9)]
    pts_bot = [(540 + i * 20, 920 + 8 * math.sin(t * 6 + i * 0.6)) for i in range(8, -1, -1)]
    A.d['yellow' if swap else 'red'].polygon(pts_top + pts_bot, fill=255)
    for k in range(6):
        x = 120 + k * 150
        person(A, x, GROUND, 180, dir=1, robe=False, hat='helmet', spear=True, layer='ink' if k % 2 else 'mid')

# ================================================================ 第三回
def art_k_fleet(A, cv, t, u):
    A.d['wash'].rectangle((60, 1120, W - 60, 1380), fill=150)
    waves(A, 1130, t, rows=5, amp=10, speed=2.5)
    A.d['mid'].rectangle((60, 1080, 220, 1140), fill=255)
    for r_ in range(2):
        for k in range(3):
            x = lerp(-200 - k * 260, 820 - k * 260, ease_out(u / (4 * P))) + r_ * 120
            big_ship(A, x, 1190 + r_ * 90, 90 - r_ * 20, t + k, layer='ink' if r_ else 'mid')
    official(A, lerp(-200, 820, ease_out(u / (4 * P))), 1130, 120, dir=1, arm=60, layer='ink')

def art_k_penghu(A, cv, t, u):
    A.d['wash'].rectangle((60, 1120, W - 60, 1380), fill=150)
    waves(A, 1130, t, rows=5, amp=10, speed=2.5)
    big_ship(A, 260, 1200, 150, t, layer='ink')
    big_ship(A, 820, 1220, 140, t + 1, layer='mid')
    kk = (t - G.B0) / P
    q = (kk % 1)
    A.d['wash'].ellipse((420 - 80 * q, 1080 - 60 * q, 420 + 80 * q, 1080 + 60 * q), fill=int(255 * (1 - q)))
    sx = lerp(420, 760, q); sy = 1080 - 200 * math.sin(math.pi * q)
    A.d['ink'].ellipse((sx - 10, sy - 10, sx + 10, sy + 10), fill=255)
    if q > 0.85:
        A.d['mid'].ellipse((740, 1050, 790, 1200), fill=200)

def art_k_taiwan(A, cv, t, u):
    """6-beat: the landing → 郑克塽 offers his seal → the flag is planted → 台湾府."""
    ph = u / P
    A.d['wash'].rectangle((60, 1150, W - 60, 1380), fill=150)
    A.d['mid'].polygon([(360, 1180), (440, 900), (540, 960), (640, 800), (760, 960), (880, 1100), (980, 1180)], fill=255)
    waves(A, 1180, t, rows=4, amp=10, speed=2.4)
    boat(A, lerp(60, 300, ease_out(u / (1.5 * P))), 1250, 180, t)
    if ph >= 1.5:
        official(A, 520, 1180, 170, dir=1, robe=True, layer='ink', arm=60)
        person(A, 700, 1180, 170, dir=-1, kneel=True, bow=45, arm=80, layer='ink')
        A.d['red'].rectangle((610, 1100, 640, 1125), fill=255)
    if ph >= 3:
        p = ease_out((u - 3 * P) / 0.5)
        flag(A, 640, lerp(880, 800, p), 260 * p, t, w=120, layer='yellow')
    if ph >= 4:
        A.flush(cv)
        stamp(cv, seal('台湾府', 46), 860, 860, t, t - u + 4 * P, rot=6)

def art_k_yakesa(A, cv, t, u):
    for k in range(34):
        q = (t * 0.3 + k / 34) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    for k in range(14):
        x = 560 + k * 32
        A.d['ink'].polygon([(x, GROUND), (x + 26, GROUND), (x + 26, 1120), (x + 13, 1090), (x, 1120)], fill=255)
    A.d['ink'].rectangle((800, 960, 900, 1120), fill=255)
    A.d['ink'].polygon([(780, 960), (920, 960), (850, 900)], fill=255)
    ground(A, GROUND)
    kk = (t - G.B0) / P
    for i, x in enumerate((140, 320)):
        f = ((kk + i * 0.5) % 1)
        cannon(A, x, GROUND, 120, 1, fire=f if f < 0.6 else 0)
        bx = lerp(x + 130, 600, f); by = GROUND - 60 - 260 * math.sin(math.pi * f)
        A.d['ink'].ellipse((bx - 9, by - 9, bx + 9, by + 9), fill=255)

def art_k_nerchinsk(A, cv, t, u):
    tent(A, 540, 1240, 700, 380, layer='wash')
    A.d['ink'].rectangle((380, 1260, 700, 1290), fill=255)
    for lx in (400, 670): A.d['ink'].rectangle((lx, 1290, lx + 18, GROUND), fill=255)
    for k in range(3):
        official(A, 300 - k * 90, GROUND, 230, dir=1, arm=60 if k == 0 else 20, layer='ink' if k == 0 else 'mid')
        person(A, 780 + k * 90, GROUND, 240, dir=-1, robe=False, hat='helmet', arm=60 if k == 0 else 20, layer='ink' if k == 0 else 'mid')
    p = ease_out(u / 0.6)
    A.d['mid'].rectangle((540 - 120 * p, 1230, 540 + 120 * p, 1258), fill=255)
    A.flush(cv)
    stamp(cv, seal('尼布楚', 44), 540, 920, t, t - u + P, rot=-4)

def art_k_camelwall(A, cv, t, u):
    ground(A, GROUND)
    for k in range(7):
        x = 520 + k * 80
        camel(A, x, GROUND, 110, -1, 0.0, layer='mid')
        A.d['wash'].rectangle((x - 50, GROUND - 100, x + 50, GROUND - 60), fill=255)
    for k in range(3):
        person(A, 640 + k * 120, GROUND - 130, 120, dir=-1, robe=False, hat='helmet', spear=True, layer='mid')
    kk = (t - G.B0) / P
    for i, x in enumerate((120, 280)):
        f = ((kk + i * 0.5) % 1)
        cannon(A, x, GROUND, 110, 1, fire=f if f < 0.6 else 0)
    if u > 1.2 * P:
        for k in range(3):
            rr = 50 + 40 * ((t * 2 + k) % 1)
            A.d['wash'].ellipse((600 + k * 150 - rr, 1160 - rr, 600 + k * 150 + rr, 1160 + rr), fill=200)

def art_k_tibet(A, cv, t, u):
    A.d['mid'].polygon([(200, GROUND), (420, 1000), (540, 940), (660, 1000), (880, GROUND)], fill=200)
    for r_ in range(4):
        w = 260 - r_ * 40; y = 1180 - r_ * 60
        A.d['ink'].rectangle((540 - w, y - 60, 540 + w, y), outline=255, width=4)
        for k in range(int(w / 30)):
            A.d['ink'].rectangle((540 - w + 16 + k * 60, y - 40, 540 - w + 30 + k * 60, y - 20), fill=255)
    A.d['red'].rectangle((470, 960, 610, 1060), fill=255)
    for k in range(5):
        p = ease_out((u - 0.3 - k * 0.12) / 0.4)
        flag(A, 140 + k * 200, GROUND, 200 * p, t + k, w=70, layer='yellow')

SCREEN = [('鳌', '1669 擒鳌拜'), ('藩', '1681 平三藩'), ('台', '1683 收台湾'), ('俄', '1689 尼布楚'),
          ('准', '1697 破噶尔丹'), ('藏', '1720 驱准安藏')]
def scene_screen(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    A = Art(); beat_fx(A, t)
    gu = ease_expo((t - gather_t) / 0.4) if gather else 0
    pw, gap = 150, 12
    x0 = 540 - 3 * pw - 2.5 * gap
    for i in range(6):
        st = bt(c[0] + i)
        x = x0 + i * (pw + gap) + gu * (2.5 - i) * (pw + gap) * 0.15
        open_ = ease_out((t - st) / 0.3) if t >= st else 0
        if open_ <= 0:
            A.d['mid'].rectangle((x, 880, x + pw, 1340), fill=120)
            A.d['ink'].rectangle((x, 880, x + pw, 1340), outline=255, width=4)
            continue
        A.d['yellow'].rectangle((x, 880, x + pw, 1340), fill=int(140 + 80 * open_))
        A.d['ink'].rectangle((x, 880, x + pw, 1340), outline=255, width=4)
        A.d['ink'].rectangle((x + 10, 890, x + pw - 10, 1330), outline=255, width=2)
    A.flush(cv)
    for i, (ch, lab) in enumerate(SCREEN):
        st = bt(c[0] + i)
        if t < st: continue
        x = x0 + i * (pw + gap) + pw / 2 + gu * (2.5 - i) * (pw + gap) * 0.15
        stamp(cv, seal(ch, 64, ZHU if i % 2 == 0 else LAN), x, 1040, t, st + 0.05)
        paste(cv, text_img(lab.split(' ')[0], SERIF, 34, INK, 'Bold', bleed=False), x, 1200, 1, clamp((t - st) / 0.3))
    idx = int(k - c[0])
    if 0 <= idx < 6:
        y_, txt = SCREEN[idx][1].split(' ')
        ink_in(cv, text_img(f'公元{cn_year(int(y_))}年 · {txt}', SERIF, 50, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1460, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '平定四方', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '奠定版图', BRUSH, 170, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '天下一统', BRUSH, 150, LAN, W / 2, 1460, t, bt(c[0] + 7), stagger=0.08, seed=111)
    fx.flush(cv)

# ================================================================ 第四回
def art_k_river(A, cv, t, u):
    pts_t = [(x, 1080 + 0.25 * (x - 60)) for x in range(60, W - 59, 10)]
    pts_b = [(x, 1200 + 0.25 * (x - 60)) for x in range(W - 60, 59, -10)]
    A.d['wash'].polygon(pts_t + pts_b, fill=160)
    for k in range(4):
        pts = [(x, 1110 + 0.25 * (x - 60) + 20 * k + 6 * math.sin(x * 0.02 + t * 3 + k)) for x in range(60, W - 59, 12)]
        A.d['mid'].line(pts, fill=255, width=3)
    lev = ease_out(u / (3 * P))
    A.d['ink'].polygon([(60, 1060), (W - 60, 1060 + 0.25 * (W - 120)), (W - 60, 1060 + 0.25 * (W - 120) - 40 * lev), (60, 1060 - 40 * lev)], fill=255)
    for k in range(4):
        x = (t * 80 + k * 260) % (W + 200) - 100
        person(A, x, 1050 + 0.25 * (x - 60) - 40 * lev, 130, dir=1, robe=False, load=True, ph=t * 6 + k, arm=160, layer='mid')
    official(A, 260, GROUND, 260, dir=1, arm=lerp(30, 110, ease_out((u - P) / 0.4)), layer='ink')
    ground(A, GROUND)

def art_k_nanxun(A, cv, t, u):
    A.d['wash'].rectangle((60, 1170, W - 60, 1300), fill=160)
    waves(A, 1180, t, rows=3, amp=6, speed=1.8)
    for x in (120, 960):
        willow(A, x, 900, t)
    x = lerp(-200, 560, ease_out(u / (1.8 * P)))
    A.d['ink'].polygon([(x - 260, 1200), (x + 220, 1200), (x + 180, 1240), (x - 220, 1240)], fill=255)
    A.d['ink'].polygon([(x + 220, 1200), (x + 280, 1130), (x + 300, 1150), (x + 250, 1210)], fill=255)
    A.d['yellow'].rectangle((x - 140, 1100, x + 100, 1200), fill=255)
    A.d['red'].polygon([(x - 160, 1100), (x + 120, 1100), (x + 80, 1060), (x - 120, 1060)], fill=255)
    ground(A, GROUND)
    for k in range(5):
        person(A, 300 + k * 110, GROUND, 140, dir=-1, kneel=True, bow=45, arm=60, layer='mid')

def art_k_tax(A, cv, t, u):
    ground(A, GROUND)
    for i, x in enumerate((220, 420)):
        A.d['mid'].rectangle((x - 80, GROUND - 220, x + 80, GROUND), fill=255)
        A.d['mid'].polygon([(x - 100, GROUND - 220), (x + 100, GROUND - 220), (x, GROUND - 320)], fill=255)
        fill = clamp(u / (1.5 * P))
        A.d['yellow'].rectangle((x - 60, GROUND - 20 - 160 * fill, x + 60, GROUND - 20), fill=255)
    A.d['ink'].rectangle((600, 1120, 900, 1340), outline=255, width=6)
    for k in range(6):
        A.d['ink'].line((620, 1150 + k * 30, 880, 1150 + k * 30), fill=200, width=3)
    person(A, 720, GROUND, 160, dir=-1, robe=False, bow=10, arm=60, layer='ink')
    A.flush(cv)
    if u > P:
        stamp(cv, seal('永不加赋', 46), 750, 1040, t, t - u + P, rot=5)

def art_k_dict(A, cv, t, u):
    A.d['ink'].polygon([(300, 1300), (540, 1340), (540, 1100), (300, 1060)], fill=255)
    A.d['ink'].polygon([(780, 1300), (540, 1340), (540, 1100), (780, 1060)], fill=255)
    A.d['wash'].polygon([(320, 1280), (530, 1315), (530, 1115), (320, 1080)], fill=0)
    A.d['wash'].polygon([(760, 1280), (550, 1315), (550, 1115), (760, 1080)], fill=0)
    r = random.Random(4)
    pool = '天地人日月山水木火土金石鸟鱼龙凤虎马牛羊心手目口耳言文字书'
    fo = font(SERIF, 44, 'Bold')
    for k in range(18):
        q = ((u * 0.9 + k / 18) % 1)
        a = r.uniform(0, 2 * math.pi); d0 = r.uniform(380, 520)
        x = 540 + d0 * (1 - q) * math.cos(a); y = 1180 + d0 * (1 - q) * math.sin(a) * 0.7 - 120 * (1 - q)
        A.d['ink'].text((x - 22, y - 22), pool[k % len(pool)], font=fo, fill=int(255 * (1 - q * 0.6)))
    if u > 2 * P:
        A.flush(cv)
        type_in(cv, text_img('收字四万七千零三十五', SERIF, 40, INK, 'Bold', bleed=False, spacing=4), 540, 1400, t, t - u + 2 * P, 0.4)

def art_k_west(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((300, 1260, 780, 1290), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1290, lx + 18, GROUND), fill=255)
    a = t * 2.5
    cx, cy = 560, 1100
    A.d['ink'].line((cx, cy - 120, cx, cy), fill=255, width=6)
    ex, ey = cx + 110 * math.cos(a), cy + 40 * math.sin(a)
    A.d['ink'].line((cx, cy - 120, ex, ey), fill=255, width=6)
    A.d['cobalt'].arc((cx - 110, cy - 40, cx + 110, cy + 40), 0, (math.degrees(a) % 360) + 1, fill=255, width=4)
    A.d['ink'].polygon([(380, 1240), (500, 1240), (380, 1140)], outline=255, width=5)
    gx, gy, gr = 860, 1100, 100
    A.d['mid'].ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=200)
    for j in range(4):
        w = gr * abs(math.cos(t + j * 0.8))
        A.d['ink'].ellipse((gx - w, gy - gr, gx + w, gy + gr), outline=255, width=3)
    A.d['ink'].line((gx, gy + gr, gx, GROUND), fill=255, width=6)
    person(A, 200, GROUND, 250, dir=1, hat='crown', arm=80, layer='ink')

def art_k_feast(A, cv, t, u):
    for k in range(4):
        lantern(A, 200 + k * 230, 760, t, k, size=22)
    official(A, 540, 1100, 200, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.d['mid'].rectangle((420, 1100, 660, 1130), fill=255)
    for row in range(2):
        for k in range(5):
            for side in (-1, 1):
                x = 540 + side * (130 + k * 80); y = GROUND - row * 70
                person(A, x, y, 130 - row * 15, dir=-side, kneel=True, bow=15 + 6 * math.sin(t * 2 + k), arm=70, layer='ink' if row == 0 else 'mid')
                A.d['wash'].line((x - side * 14, y - 85 + row * 10, x - side * 18, y - 60 + row * 10), fill=255, width=4)
    A.d['mid'].rectangle((200, GROUND - 40, 880, GROUND - 26), fill=200)

def art_k_inoc(A, cv, t, u):
    ground(A, GROUND)
    person(A, 420, GROUND, 170, dir=1, robe=False, kneel=True, bow=0, arm=20, layer='ink')
    official(A, 640, GROUND, 260, dir=-1, arm=85, layer='ink')
    A.d['ink'].line((560, GROUND - 190, 470, GROUND - 160), fill=255, width=5)
    q = (u * 1.5) % 1
    for k in range(6):
        px = lerp(560, 475, q) + k * 6; py = lerp(GROUND - 190, GROUND - 160, q) - k * 3
        A.d['gold'].ellipse((px - 4, py - 4, px + 4, py + 4), fill=int(255 * (1 - q)))
    for k in range(5):
        person(A, 840 + k * 50, GROUND, 120, dir=-1, robe=False, arm=20, layer='mid')
    A.flush(cv)
    stamp(cv, seal('种痘', 54), 300, 1000, t, t - u + P)

def art_k_hunt(A, cv, t, u):
    for k in range(20):
        q = (t * 0.35 + k / 20) % 1
        x = 80 + (k * 47) % 920 + 30 * math.sin(t + k); y = lerp(620, 1420, q)
        A.d['gold'].ellipse((x - 9, y - 5, x + 9, y + 5), fill=230)
    ground(A, GROUND)
    for k in range(3):
        x = (t * 240 + k * 220) % (W + 400) - 100
        deer(A, x + 300, GROUND - k * 14, 140 - k * 15, 1, t * 14 + k, layer='ink' if k == 0 else 'mid')
    rx = lerp(-150, 300, ease_out(u / (2 * P)))
    rider(A, rx, GROUND, 230, 1, t * 13, layer='ink')
    A.d['ink'].arc((rx + 20, GROUND - 330, rx + 120, GROUND - 200), 270, 90, fill=255, width=5)
    for k in range(3):
        q = clamp((u - P - k * 0.2) / 0.4)
        if 0 < q < 1:
            arrow(A, lerp(rx + 120, rx + 520, q), GROUND - 260 + 60 * q, 0.15, 70)

def art_k_confucius(A, cv, t, u):
    palace(A, 540, GROUND, 760, layer='mid')
    A.d['ink'].rectangle((390, 1000, 690, 1080), fill=255)
    fo = font(SERIF, 54, 'Black')
    A.d['ink'].text((404, 1008), '万世师表', font=fo, fill=0)
    kk = (t - G.B0) / P
    b = 30 + 35 * math.exp(-((kk % 1) * P) / 0.15)
    person(A, 540, GROUND, 220, dir=-1, hat='crown', kneel=True, bow=b, arm=60, layer='ink')
    for k in range(3):
        official(A, 200 + k * 80, GROUND, 160, dir=1, kneel=True, bow=b, arm=60, layer='mid')

def art_k_worry(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((160, GROUND - 260, 420, GROUND), fill=255)
    A.d['wash'].rectangle((230, GROUND - 180, 350, GROUND), fill=0)
    x = walk_x(500, 900, u, 1.8 * P)
    official(A, x, GROUND, 230, dir=1, ph=t * 6, arm=60, layer='ink')
    for k in range(2):
        A.d['yellow'].ellipse((x + 30 - k * 120, GROUND - 160, x + 90 - k * 120, GROUND - 90), fill=255)
    A.flush(cv)
    stamp(cv, seal('亏空', 54, INK), 290, 980, t, t - u + 0.4, rot=-5)

# ================================================================ 第五回
def art_k_depose(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 290, dir=-1, hat='crown', arm=lerp(30, 100, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    person(A, 400, GROUND, 230, dir=1, kneel=True, bow=30, arm=70, hat='none', layer='ink')
    states = [0, 1, 0, 1]
    i = min(3, int(u / P))
    on = states[i] == 0
    prev_on = states[i - 1] == 0 if i else True
    q = ease_out((u - i * P) / 0.35)
    hy_on, hy_off = GROUND - 210, GROUND - 420
    hy = lerp(hy_on if prev_on else hy_off, hy_on if on else hy_off, q)
    A.d['yellow'].polygon([(420, hy), (500, hy), (480, hy - 50), (440, hy - 50)], fill=255)
    A.flush(cv)
    for j, ch in enumerate(('废', '复', '废')):
        if u > (j + 1) * P:
            stamp(cv, seal(ch, 54, ZHU if ch == '废' else LAN), 180 + j * 0, 860 + j * 120, t, t - u + (j + 1) * P, rot=-6)

def art_k_nine(A, cv, t, u):
    throne(A, 540, 1220, 1.0)
    for i in range(9):
        a = math.pi * (0.1 + 0.8 * i / 8)
        x = 540 - 420 * math.cos(a); y = GROUND - 70 * math.sin(a)
        person(A, x, y, 170, dir=1 if x < 540 else -1, robe=True, arm=70, hat='crown', layer='ink' if i % 2 else 'mid')
        fh = 20 + 5 * math.sin(t * 13 + i)
        cx = x + (40 if x < 540 else -40)
        A.d['red'].polygon([(cx - 5, y - 120), (cx + 5, y - 120), (cx, y - 120 - fh)], fill=255)
    A.flush(cv)
    stamp(cv, seal('九子', 54), 540, 900, t, t - u + P)

def art_k_death(A, cv, t, u):
    A.d['wash'].ellipse((800, 640, 900, 740), fill=255)
    A.d['wash'].rectangle((60, 1250, W - 60, 1340), fill=150)
    waves(A, 1260, t, rows=2, amp=5, speed=1.2)
    willow(A, 150, 900, t)
    A.d['mid'].rectangle((440, 1080, 760, 1250), fill=255)
    A.d['mid'].polygon([(400, 1080), (800, 1080), (720, 1000), (480, 1000)], fill=255)
    light = clamp(1 - (u - 2 * P) / 0.6)
    A.d['wash'].rectangle((520, 1120, 680, 1220), fill=0)
    if light > 0:
        A.d['yellow'].rectangle((520, 1120, 680, 1220), fill=int(170 * light))
    ground(A, GROUND)

def art_k_will(A, cv, t, u):
    p = ease_out(u / 0.6)
    w = 300 * p
    A.d['yellow'].rectangle((540 - w, 860, 540 + w, 1240), fill=255)
    A.d['ink'].rectangle((540 - w - 18, 840, 540 - w, 1260), fill=255); A.d['ink'].rectangle((540 + w, 840, 540 + w + 18, 1260), fill=255)
    fo = font(SERIF, 64, 'Black')
    for j, col in enumerate(('传位', '皇四子')):
        for i, ch in enumerate(col):
            if u > 0.6 + (j * 3 + i) * 0.12:
                A.d['ink'].text((560 - j * 110, 890 + i * 80), ch, font=fo, fill=255)
    A.flush(cv)
    if u > 2 * P:
        stamp(cv, seal('雍正', 54), 820, 1180, t, t - u + 2 * P, rot=6)

def art_k_rings(A, cv, t, u):
    n = min(61, int(clamp(u / (3 * P)) * 61))
    cx, cy = 540, 1080
    A.d['mid'].ellipse((cx - 300, cy - 200, cx + 300, cy + 200), fill=170)
    for k in range(n):
        rr = 10 + k * 4.6
        A.d['ink'].ellipse((cx - rr, cy - rr * 0.66, cx + rr, cy + rr * 0.66), outline=200 if k % 5 else 255, width=2 if k % 5 else 3)
    A.flush(cv)
    lab = text_img(f'{cn_num(max(1, n))}年', SERIF, 70, ZHU, 'Black', bleed=False)
    paste(cv, lab, cx, cy, 1, 1)

def art_k_dawn(A, cv, t, u):
    sun(cv, 540, lerp(1250, 980, ease_out(u / (3 * P))), 240, HUANG, 140)
    for k, (x, s, lay) in enumerate(((540, 640, 'ink'), (200, 320, 'mid'), (880, 320, 'mid'))):
        palace(A, x, GROUND - (0 if k == 0 else 60), s, layer=lay)
    ground(A, GROUND)
    if u > 1.5 * P:
        A.flush(cv)
        stamp(cv, seal('康乾盛世', 50), 860, 820, t, t - u + 1.5 * P, rot=6)

# ================================================================ script
CHAPTERS = {16: ('第一回', '少年天子'), 48: ('第二回', '亲政平乱'), 80: ('第三回', '一统海疆'),
            112: ('第四回', '康熙盛世'), 144: ('第五回', '九子夺嫡')}

CARDS = [
    C(0, 2, 'hook', 'num', num='八岁', line='登基为帝', art=art_k_boy_throne),
    C(2, 4, 'hook', 'num', num='十六岁', line='智擒权臣鳌拜', art=art_k_cup),
    C(4, 6, 'hook', 'num', num='平三藩', line='收台湾 定边疆', art=art_k_island),
    C(6, 8, 'hook', 'num', num='六十一年', line='在位最久的皇帝', art=art_k_calendar),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 少年天子
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'night', 'card', year=1654, main='生于景仁宫', sub='顺治帝第三子 · 名玄烨', note='三月十八日 生于景仁宫', art=art_k_birth),
    C(22, 26, 'life', 'card', year=1656, main='幼年出痘', sub='闯过天花鬼门关 · 脸上留下麻点', note='汤若望进言 已出痘者 可保无虞', art=art_k_pox),
    C(26, 30, 'empire', 'card', year=1661, main='八岁登基', sub='顺治驾崩 · 幼子继位', note='年号康熙 取万民康宁 天下熙盛', art=art_k_coronation),
    C(30, 34, 'court', 'card', year=1661, main='四臣辅政', sub='索尼 苏克萨哈 遏必隆 鳌拜', note='四大臣同心辅佐', art=art_k_regents),
    C(34, 38, 'court', 'card', year=1667, main='鳌拜专横', sub='擅杀辅臣苏克萨哈 · 欺君罔上', note='鳌拜攘臂上前 强奏累日', art=art_k_aobai),
    C(38, 42, 'night', 'card', year=1667, main='祖母孝庄', sub='太皇太后 · 灯下教诲', note='祖母教以为君之道', art=art_k_xiaozhuang),
    C(42, 46, 'court', 'card', year=1667, main='十四亲政', sub='御门听政 · 却仍受制于人', note='七月初七 御太和殿 亲政', art=art_k_qinzheng),
    C(46, 48, 'life', 'card', year=1668, main='布库少年', sub='暗中挑选少年 · 习练摔跤', art=art_k_buku),
    # ---- 第二回 亲政平乱
    C(48, 50, 'court', 'chapter'),
    C(50, 58, 'court', 'card', year=1669, main='智擒鳌拜', sub='一声令下 · 布库少年一拥而上', note='鳌拜入见 即令侍卫擒之', art=art_k_capture),
    C(58, 62, 'court', 'card', year=1673, main='毅然撤藩', sub='吴三桂 尚可喜 耿精忠 · 三藩坐大', note='撤亦反 不撤亦反 不若先发', art=art_k_cheshan),
    C(62, 66, 'war', 'card', year=1673, main='吴三桂起兵', sub='自称周王 · 号召天下反清', note='一时间 云贵川湘 尽陷', art=art_k_wu),
    C(66, 70, 'war', 'card', year=1674, main='半壁江山', sub='六省叛乱 · 大清危如累卵', note='东南西北 在在鼎沸', art=art_k_chess),
    C(70, 74, 'empire', 'card', year=1674, main='镇定自若', sub='照常出游景山 · 安定人心', note='每日出游 以示闲暇', art=art_k_calm),
    C(74, 80, 'war', 'card', year=1681, main='平定三藩', sub='八年苦战 · 攻克昆明', note='吴世璠自尽 三藩悉平', art=art_k_kunming),
    # ---- 第三回 一统海疆
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'works', 'card', year=1683, main='施琅出海', sub='福建水师 · 二万精兵东渡', note='战舰三百余艘 自铜山出发', art=art_k_fleet),
    C(86, 90, 'war', 'card', year=1683, main='澎湖海战', sub='七日激战 · 郑军主力覆没', note='炮火连天 海水为赤', art=art_k_penghu),
    C(90, 96, 'works', 'card', year=1683, main='收复台湾', sub='郑克塽归降 · 设台湾府', note='台湾自此正式纳入版图', art=art_k_taiwan),
    C(96, 98, 'works', 'card', year=1686, main='雅克萨之战', sub='炮击沙俄据点', art=art_k_yakesa),
    C(98, 100, 'works', 'card', year=1689, main='尼布楚条约', sub='划定中俄东段边界', art=art_k_nerchinsk),
    C(100, 102, 'war', 'card', year=1690, main='乌兰布通', sub='炮破噶尔丹驼城', art=art_k_camelwall),
    C(102, 104, 'works', 'card', year=1720, main='驱准安藏', sub='清军入藏 · 安定西藏', art=art_k_tibet),
    C(104, 112, 'war', 'screen'),
    # ---- 第四回 康熙盛世
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'works', 'card', year=1684, main='治理黄河', sub='三藩 河务 漕运 · 书于宫柱', note='朕以三藩及河务 漕运为三大事', art=art_k_river),
    C(118, 126, 'empire', 'list', year=1712, items=['六次南巡', '永不加赋', '康熙字典', '学习西学']),
    C(126, 130, 'empire', 'card', year=1713, main='千叟宴', sub='六旬万寿 · 宴请天下老人', note='赴宴老者 逾千人', art=art_k_feast),
    C(130, 134, 'life', 'card', year=1681, main='推广种痘', sub='自己出过天花 · 下令宫中种痘', note='朕之子女 及尔等子女 皆以种痘得无恙', art=art_k_inoc),
    C(134, 138, 'war', 'card', year=1681, main='木兰围猎', sub='设木兰围场 · 每年秋狝', note='习劳苦 演骑射', art=art_k_hunt),
    C(138, 142, 'court', 'card', year=1684, main='曲阜祭孔', sub='行三跪九叩大礼 · 题万世师表', note='满汉一体 尊孔崇儒', art=art_k_confucius),
    C(142, 144, 'fate', 'card', year=1710, main='盛世隐忧', sub='宽仁之下 · 国库亏空', art=art_k_worry),
    # ---- 第五回 九子夺嫡
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'fate', 'card', year=1708, main='两废太子', sub='一废 复立 再废 · 父子相疑', note='不法祖德 不遵朕训', art=art_k_depose),
    C(150, 154, 'night', 'card', year=1712, main='九子夺嫡', sub='众皇子结党 · 明争暗斗', note='储位虚悬 诸王觊觎', art=art_k_nine),
    C(154, 158, 'death', 'card', year=1722, main='崩于畅春园', sub='冬月十三夜 · 一代大帝落幕', note='享年六十九岁', art=art_k_death),
    C(158, 162, 'death', 'card', year=1722, main='传位四子', sub='皇四子胤禛继位 · 是为雍正', note='遗诏真伪 争议至今', art=art_k_will),
    C(162, 166, 'end', 'card', year=1722, main='六十一年', sub='中国历史上 · 在位最久的皇帝', note='一年一轮 刻进历史', art=art_k_rings),
    C(166, 170, 'end', 'card', year=1722, main='康乾盛世', sub='开启一百三十余年盛世', note='万民康宁 天下熙盛', art=art_k_dawn),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z, St, M):
    mod.CHAPTERS = CHAPTERS
G.CHAPTER_BEATS = [0, 16, 48, 80, 112, 144, END_BEAT]
L.CUTS = sorted({c[0] for c in CARDS if c[0] not in G.CHAPTER_BEATS} | {120, 122, 124})

def year_at(t):
    pts = sorted((bt(c[0]), c[4]['year']) for c in CARDS if 'year' in c[4])
    if t <= pts[0][0]: return pts[0][1]
    prev = pts[0][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t < t1: return lerp(prev, y0, ease_out((t - t0) / 0.4))
        prev = y0
    return lerp(prev, pts[-1][1], ease_out((t - pts[-1][0]) / 0.4))
for mod in (G, L, Wd, Tz, Z, St, M):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_year(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=HUANG + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, S.art_emperor)
    fx = Art()
    ink_in(cv, text_img('爱新觉罗 · 玄烨', SERIF, 46, LAN, 'Bold', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '康熙', BRUSH, 220, INK, W / 2, 450, t, s0, stagger=0.1, seed=77)
    fx.flush(cv)
    stamp(cv, seal('康熙', 66), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元1654 — 1722', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '盛世明君？', BRUSH, 120, ZHU, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '错过世界？', BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

LIST_ART = [art_k_nanxun, art_k_tax, art_k_dict, art_k_west]
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
            stamp(cv, seal('壹贰叁肆'[j], 36, LAN), x, 575, t, bt(c[0] + 2 * j))
        else:
            ImageDraw.Draw(cv).rounded_rectangle((x - 30, 545, x + 30, 605), radius=6, outline=LAN + (110,), width=2)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    armillary(A, 540, 760, 300, clamp(u / 0.8), t, rings=5, layer='mid')
    A.flush(cv, alpha=clamp(u / 0.6) * 0.35)
    fx = Art()
    chars_in(cv, fx, '康熙大帝', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('玄烨', 64), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('八岁登基 · 在位六十一年', SERIF, 50, DIM, 'SemiBold', bleed=False, spacing=6), W / 2, 960, t, END + 0.6, 0.35)
    type_in(cv, text_img('他学过几何 看过地球仪', SERIF, 52, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '若西学推广', BRUSH, 110, LAN, W / 2, 1190, t, END + 1.15, stagger=0.07, drop=30, splash=False)
    type_in(cv, text_img('中国会不一样吗？评论区聊聊', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=HUANG + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(40, 30, 10, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=LAN + (220,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 雍正皇帝', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, list=scene_list,
                screen=scene_screen, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第柒集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(8):
        q = text_img('八岁登基 · 他凭什么坐稳六十一年？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 310, 335, W / 2 + 310, 335), fill=HUANG + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, LAN, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=HUANG + (240,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=LAN + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(int(round(yr - BORN + 1))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=LAN + (255,))
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
