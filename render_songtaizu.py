# 千古人物志 · 第伍集 · 宋太祖赵匡胤 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈），本集特色：
#   汝窑天青远山 · 梅瓶开片章回卡 · 梅花飘落 · 回纹边角 · 八拍「黄袍加身」 · 六拍「杯酒释兵权」
#   · 「先南后北」诸国回顾 · 八拍「斧声烛影」悬疑长镜
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_wuzetian as Z         # engine + helpers from earlier episodes
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
from render_wudi import art_split, coin
from render_wuzetian import stele

F.RIPPLE = False

BORN, DIED = 927, 976
END_BEAT = 170
QING = (78, 128, 140)               # 天青
YELLOW = (206, 160, 40)             # 黄袍
S.LAYERS.append(('qing', QING, 0.75, 1.4))
S.LAYERS.append(('yellow', YELLOW, 0.92, 1.0))

# ================================================================ episode look
WM = dict(hook='宋', life='胤', court='文', night='夜', war='戰', empire='宋', works='统', fate='谜', death='烛', end='祖')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'fate'):
    G.THEMES[k]['part'] = 'plum'
for k in ('night', 'death'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (YELLOW, 250, (W * 0.5, 820))
G.THEMES['works']['sun'] = (QING, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (QING, 200, (W * 0.5, 720))
G.THEMES['hook']['tint'] = (0.97, 0.99, 1.0)
G.THEMES['life']['tint'] = (0.99, 0.98, 0.95)
G.base_bg.cache_clear()

MTN_COL = {'night': (44, 54, 66), 'death': (58, 60, 64), 'war': (90, 60, 50)}
def draw_background(t, theme):
    """汝窑天青: distant ranges in celadon blue-grey, tall Fan Kuan-like peaks."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(150, 176, 182), (110, 142, 152), MTN_COL.get(theme, (70, 96, 104))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

_orig_sprite = Tz._orig_sprite
@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'plum':
        return Z.particle_sprite(kind, q)
    s = 40
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [(246, 240, 236), (236, 196, 200), (250, 250, 248)][q]
    for j in range(5):
        a = j * 2 * math.pi / 5
        cx, cy = 20 + 7 * math.cos(a), 20 + 7 * math.sin(a)
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=col + (235,))
    d.ellipse((17, 17, 23, 23), fill=(210, 150, 60, 235))
    return im.filter(ImageFilter.GaussianBlur(0.5))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """Song restraint: thin double rule with 回纹 square-spiral corners in celadon."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = QING + (200,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 140, y), fill=col, width=2); d.line((x, y, x, y + sy * 140), fill=col, width=2)
        d.line((x + sx * 8, y + sy * 8, x + sx * 140, y + sy * 8), fill=col, width=1)
        d.line((x + sx * 8, y + sy * 8, x + sx * 8, y + sy * 140), fill=col, width=1)
        pts = [(0, 0), (40, 0), (40, 40), (10, 40), (10, 12), (28, 12), (28, 28), (20, 28)]
        d.line([(x + sx * (16 + px), y + sy * (16 + py)) for px, py in pts], fill=col, width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ meiping chapter card
VASES = {   # (height fraction, half-width) control points for each Song porcelain form
    'mei':   [(0, .10), (.06, .10), (.10, .07), (.30, .40), (1, .20)],                         # 梅瓶
    'yuhu':  [(0, .17), (.05, .15), (.25, .06), (.45, .14), (.74, .36), (.92, .26), (1, .18)],  # 玉壶春瓶
    'goose': [(0, .08), (.05, .06), (.45, .06), (.58, .20), (.78, .33), (.94, .22), (1, .15)],  # 鹅颈瓶
    'hulu':  [(0, .07), (.06, .08), (.24, .21), (.44, .10), (.72, .36), (.92, .28), (1, .20)],  # 葫芦瓶
    'cong':  [(0, .10), (.08, .10), (.12, .07), (.14, .30), (.90, .30), (.92, .13), (1, .15)],  # 琮式瓶
}
CHAPTER_VASE = {16: 'mei', 48: 'yuhu', 80: 'goose', 112: 'hulu', 144: 'cong'}

def meiping(A, cx, cy, s, p, t, crackle=True, shape='mei'):
    """梅瓶: small mouth, broad shoulder, slender foot — outlined, celadon glaze, crackle spreading."""
    if p <= 0: return
    ctrl = VASES.get(shape, VASES['mei'])
    prof = []
    for i in range(41):
        f = i / 40
        y = cy - s * 0.95 + f * s * 1.9
        prof.append((float(np.interp(f, [c_[0] for c_ in ctrl], [c_[1] for c_ in ctrl])) * s, y))
    reveal_y = cy - s * 0.95 + s * 1.9 * ease_out(p)
    right = [(cx + w, y) for w, y in prof if y <= reveal_y]
    left = [(cx - w, y) for w, y in prof if y <= reveal_y][::-1]
    if len(right) > 2:
        A.d['qing'].polygon(right + left, fill=200)
        A.d['ink'].line(right, fill=255, width=4); A.d['ink'].line(left, fill=255, width=4)
    if crackle and p > 0.5:
        r = random.Random(3)
        k = int((p - 0.5) * 2 * 26)
        for j in range(k):
            x0 = cx + r.uniform(-0.3, 0.3) * s; y0 = cy + r.uniform(-0.5, 0.8) * s
            pts = [(x0, y0)]
            for _ in range(3):
                x0 += r.uniform(-0.08, 0.08) * s; y0 += r.uniform(-0.08, 0.08) * s
                pts.append((x0, y0))
            A.d['mid'].line(pts, fill=150, width=2)

def plum_branch(A, x0, y0, p, t, seed=1):
    r = random.Random(seed)
    pts = [(x0, y0)]
    x, y = x0, y0
    for j in range(int(8 * clamp(p)) + 1):
        x += r.uniform(30, 60); y -= r.uniform(10, 50)
        pts.append((x, y))
    A.d['ink'].line(pts, fill=255, width=7)
    for (bx, by) in pts[1:]:
        A.d['red'].ellipse((bx - 10, by - 10, bx + 10, by + 10), fill=230)
        A.d['wash'].ellipse((bx + 10 - 7, by - 16 - 7, bx + 10 + 7, by - 16 + 7), fill=255)

def art_meiping_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    shape = CHAPTER_VASE.get(kb, 'mei')
    meiping(A, 540, 820, 320, u / 0.6, t, shape=shape)
    if shape == 'cong':
        for k in range(5):
            yy = 820 - 320 * 0.95 + 320 * 1.9 * (0.2 + k * 0.15)
            A.d['ink'].line((540 - 0.30 * 320, yy, 540 + 0.30 * 320, yy), fill=180, width=3)
    plum_branch(A, 640 if kb % 32 == 16 else 300, 1040, u / 0.8, t, seed=kb)
    for k in range(4):
        y = 1280 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_meiping_chapter)
    ink_in(cv, text_img(no, SERIF, 56, QING, 'Black', bleed=False, spacing=12), W / 2, 1220, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 170, INK, W / 2, 1380, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ scenes
def tent(A, x, base, w, h, layer='mid', open_=0.0):
    A.d[layer].polygon([(x - w / 2, base), (x, base - h), (x + w / 2, base)], fill=255)
    if open_ > 0:
        A.d[layer].polygon([(x - w * 0.12 * open_, base), (x, base - h * 0.55), (x + w * 0.12 * open_, base)], fill=0)
    A.d['ink'].line((x, base - h, x, base - h - 40), fill=255, width=4)

def campfire(A, x, y, t, size=60):
    flames(A, x, y, size, size * 1.3, t, n=3, seed=int(x), smoke=False)
    A.d['ink'].line((x - size * 0.6, y, x + size * 0.6, y - 10), fill=255, width=6)
    A.d['ink'].line((x - size * 0.6, y - 10, x + size * 0.6, y), fill=255, width=6)

def art_staff(A, cv, t, u):
    ground(A, GROUND)
    cx, cy = 540, GROUND - 160
    person(A, 540, GROUND, 280, dir=1, robe=False, arm=120 + 40 * math.sin(t * 8), layer='ink')
    a = t * 9
    L_ = 260
    A.d['ink'].line((cx + L_ * math.cos(a), cy - 40 + L_ * math.sin(a) * 0.4, cx - L_ * math.cos(a), cy - 40 - L_ * math.sin(a) * 0.4), fill=255, width=9)
    for k, x in enumerate((180, 900)):
        fall = -70 * ease_out((u - P * (1 + k)) / 0.3) if u > P * (1 + k) else 0
        person(A, x, GROUND, 230, dir=1 if x < 540 else -1, robe=False, arm=60, fall=fall * (1 if x < 540 else -1), layer='mid')

def art_jingniang(A, cv, t, u):
    sun(cv, 800, 900, 110, ZHU, 110)
    ground(A, GROUND)
    x = lerp(140, 560, ease_out(u / (4 * P)))
    horse(A, x + 130, GROUND, 200, 1, t * 5, layer='ink')
    person(A, x + 120, GROUND - 0.66 * 200, 120, dir=1, female=True, arm=20, layer='ink')
    person(A, x + 330, GROUND, 230, dir=1, robe=False, ph=t * 5, arm=60, layer='ink')
    A.d['ink'].line((x + 330, GROUND - 150, x + 230, GROUND - 120), fill=255, width=3)
    for k in range(4):
        y = 1180 + k * 40
        xx = (t * 50 + k * 300) % (W + 500) - 300
        A.d['wash'].line((xx, y, xx + 300, y), fill=255, width=14)

def art_mubai(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        person(A, 120 + k * 90, GROUND, 170, dir=1, robe=False, hat='helmet', spear=True, layer='mid')
    rise = ease_out((u - 0.2) / (1.5 * P))
    ty = lerp(GROUND + 60, 980, rise)
    A.d['ink'].rectangle((560, ty, 760, ty + 360), fill=255)
    A.d['ink'].rectangle((650, min(ty + 360, GROUND), 670, GROUND), fill=255)
    fo = font(SERIF, 52, 'Black')
    for j, ch in enumerate('点检作天子'):
        A.d['ink'].text((630, ty + 20 + j * 64), ch, font=fo, fill=0)
    person(A, 900, GROUND, 250, dir=-1, arm=lerp(20, 90, rise), bow=10, hat='crown', layer='ink')

def art_messenger(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        x = (k * 120 - t * 900) % (W + 200) - 100
        A.d['wash'].line((x, 1080 + k * 26, x + 180, 1080 + k * 26), fill=255, width=4)
    x = lerp(-200, 560, ease_out(u / (2 * P)))
    rider(A, x, GROUND, 260, 1, t * 15, layer='ink')
    A.d['ink'].line((x - 30, GROUND - 330, x - 60, GROUND - 520), fill=255, width=5)
    A.d['red'].polygon([(x - 60, GROUND - 520), (x + 20, GROUND - 500 + 8 * math.sin(t * 9)), (x - 52, GROUND - 460)], fill=255)

def art_camp(A, cv, t, u):
    A.d['wash'].ellipse((780, 650, 880, 750), fill=255)
    ground(A, GROUND)
    for k, (x, w, h) in enumerate(((180, 300, 260), (540, 380, 340), (900, 300, 260))):
        tent(A, x, GROUND - 20, w, h, layer='mid' if k != 1 else 'ink')
    campfire(A, 330, GROUND, t)
    campfire(A, 750, GROUND, t + 1)
    for k in range(3):
        person(A, 260 + k * 60, GROUND, 170, dir=1, robe=False, hat='helmet', bow=15 + 8 * math.sin(t * 3 + k), arm=60, layer='ink')
        person(A, 820 - k * 60, GROUND, 170, dir=-1, robe=False, hat='helmet', bow=15 + 8 * math.sin(t * 3 + k + 1), arm=60, layer='ink')

def yellow_robe(A, cx, h, drop):
    """黄袍 falling from above onto the shoulders of a figure of height h standing at GROUND."""
    off = (1 - drop) * 420
    ys = GROUND - 0.80 * h - off
    yb = GROUND - 8 - off * 0.9
    pts = [(cx - 0.17 * h, ys), (cx - 0.05 * h, ys - 0.03 * h), (cx + 0.07 * h, ys - 0.03 * h), (cx + 0.19 * h, ys),
           (cx + 0.36 * h, ys + 0.30 * h), (cx + 0.30 * h, ys + 0.34 * h), (cx + 0.24 * h, yb), (cx - 0.30 * h, yb),
           (cx - 0.34 * h, ys + 0.34 * h), (cx - 0.40 * h, ys + 0.30 * h)]
    A.d['yellow'].polygon(pts, fill=255)
    for k in range(4):   # gold dragon-roundel hints
        yy = lerp(ys + 0.12 * h, yb - 0.1 * h, k / 3)
        A.d['gold'].ellipse((cx - 0.06 * h, yy - 0.04 * h, cx + 0.06 * h, yy + 0.04 * h), outline=255, width=3)
    A.d['gold'].line((cx + 0.01 * h, ys, cx + 0.01 * h, yb), fill=200, width=3)

def art_huangpao(A, cv, t, u):
    """8-beat set piece: dawn in the tent → generals storm in → yellow robe → all kneel."""
    ph = u / P
    sun(cv, 540, lerp(1250, 980, ease_out(u / (8 * P))), 220, ZHU, 110)
    ground(A, GROUND)
    tent(A, 540, GROUND - 10, 760, 640, layer='mid', open_=clamp(ph / 2))
    if ph < 4:
        person(A, 540, GROUND, 300, dir=1, kneel=True, bow=55 if ph < 2 else 20, arm=80, layer='ink')
    else:
        person(A, 540, GROUND, 330, dir=1, arm=lerp(20, 60, ease_out((u - 4 * P) / 0.4)), layer='ink')
    for k in range(4):
        side = -1 if k % 2 == 0 else 1
        x0 = 540 + side * (560 + k * 30)
        x1 = 540 + side * (210 + (k // 2) * 140)
        x = walk_x(x0, x1, u - 1.5 * P, 1.2 * P) if ph >= 1.5 else x0
        kneel = ph >= 6
        person(A, x, GROUND, 230, dir=-side, robe=False, hat='helmet', kneel=kneel, bow=45 if kneel else 0,
               spear=not kneel, arm=60 if kneel else 30, ph=None if kneel else t * 8 + k, layer='ink' if k < 2 else 'mid')
    if ph >= 4:
        yellow_robe(A, 540, 330, ease_expo((u - 4 * P) / 0.35))
    if ph >= 6:
        A.flush(cv)
        stamp(cv, seal('万岁', 60), 860, 860, t, t - u + 6 * P, rot=6)

def art_peaceful(A, cv, t, u):
    city_wall(A, 520, W - 60, 1120, gate_x=780, label='汴京', open_=1.0)
    ground(A, GROUND)
    for k in range(5):
        x = walk_x(-100 - k * 120, 520 - k * 110, u, 3 * P)
        person(A, x, GROUND, 190, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, layer='ink' if k % 2 == 0 else 'mid')
    for k in range(3):
        person(A, 860 + k * 70, GROUND, 150, dir=-1, female=k == 1, arm=30, layer='mid')
    if u > P:
        A.flush(cv)
        stamp(cv, seal('秋毫无犯', 44), 300, 980, t, t - u + P, rot=-5)

def art_banquet(A, cv, t, u):
    """6-beat: cups raised on the beat → generals kneel and surrender their swords."""
    ph = u / P
    A.d['mid'].rectangle((240, 1250, 840, 1280), fill=255)
    for lx in (270, 800): A.d['mid'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    for k in range(5):
        x = 300 + k * 120
        A.d['ink'].polygon([(x - 14, 1220), (x + 14, 1220), (x + 7, 1250), (x - 7, 1250)], fill=255)
    person(A, 540, 1240, 200, dir=1, hat='crown', arm=lerp(20, 140, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    kk = (t - G.B0) / P
    hit = math.exp(-((kk % 1) * P) / 0.15)
    for i, x in enumerate((140, 900, 250, 800)):
        side = 1 if x < 540 else -1
        if ph < 3:
            person(A, x, GROUND, 230, dir=side, robe=True, arm=lerp(40, 150, hit), hat='knot', layer='ink' if i < 2 else 'mid')
        else:
            person(A, x, GROUND, 230, dir=side, kneel=True, bow=45, arm=80, layer='ink' if i < 2 else 'mid')
            sx = x + side * 90
            A.d['ink'].line((sx, GROUND - 40, sx + side * 10, GROUND - 160), fill=255, width=6)
    if ph >= 4:
        A.flush(cv)
        for i in range(3):
            stamp(cv, seal('兵权', 46), 380 + i * 160, 900, t, t - u + 4 * P + i * 0.15, rot=(i - 1) * 6)

def art_snow_visit(A, cv, t, u):
    palace(A, 620, GROUND, 520, layer='mid')
    A.d['wash'].rectangle((520, 1180, 720, GROUND), fill=0)
    A.d['red'].ellipse((580, 1260, 660, 1330), fill=200)
    person(A, 560, GROUND, 180, dir=1, kneel=True, bow=15, arm=70, layer='ink')
    person(A, 690, GROUND, 180, dir=-1, kneel=True, bow=15, arm=70, hat='crown', layer='ink')
    for k in range(30):
        q = (t * 0.25 + k / 30) % 1
        x = 80 + (k * 41) % 920 + 20 * math.sin(t + k); y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    for k in range(3):
        A.d['ink'].line((120 + k * 40, GROUND, 140 + k * 40, GROUND - 20), fill=255, width=4)

KINGDOMS = [('荆南', 963, (420, 1030)), ('湖南', 963, (520, 1170)), ('后蜀', 965, (240, 1030)),
            ('南汉', 971, (560, 1340)), ('南唐', 975, (760, 1130)), ('北汉', 979, (560, 760))]
def scene_unify(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    A = Art(); beat_fx(A, t)
    pts = []
    for j in range(48):
        a = 2 * math.pi * j / 48
        r = 340 + 40 * math.sin(a * 3 + 1) + 20 * math.sin(a * 7)
        pts.append((540 + r * math.cos(a), 1050 + r * math.sin(a) * 0.85))
    A.d['qing'].polygon(pts, fill=120); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    for i, (name, yr, (x, y)) in enumerate(KINGDOMS):
        p = ease_out((t - bt(c[0] + i)) / 0.3)
        if p > 0:
            A.d['red' if name != '北汉' else 'mid'].line((540, 960, lerp(540, x, p), lerp(960, y, p)), fill=255, width=8)
    A.flush(cv)
    stamp(cv, seal('宋', 100 if not gather else 220), 540, 960 if not gather else 1050, t, s0 if not gather else gather_t)
    for i, (name, yr, (x, y)) in enumerate(KINGDOMS):
        if t >= bt(c[0] + i) and not gather:
            stamp(cv, seal(name, 42, ZHU if name != '北汉' else (120, 120, 120)), x, y, t, bt(c[0] + i) + 0.12)
    idx = int(k - c[0])
    if 0 <= idx < 6:
        nm, yr, _ = KINGDOMS[idx]
        txt = f'公元{cn_num(yr)}年 · 平{nm}' if nm != '北汉' else '北汉 · 太祖生前未克'
        ink_in(cv, text_img(txt, SERIF, 50, ZHU if nm != '北汉' else INK, 'Black', bleed=False, spacing=4), W / 2, 1460, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '先南后北', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '结束五代', BRUSH, 170, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '天下归一', BRUSH, 150, QING, W / 2, 1460, t, bt(c[0] + 7), stagger=0.08, seed=111)
    fx.flush(cv)

def art_south_north(A, cv, t, u):
    pts = []
    for j in range(40):
        a = 2 * math.pi * j / 40
        r = 360 + 40 * math.sin(a * 3 + 1)
        pts.append((540 + r * math.cos(a), 1060 + r * math.sin(a) * 0.8))
    A.d['qing'].polygon(pts, fill=110); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    p1 = ease_out(u / (1.2 * P)); p2 = ease_out((u - 1.2 * P) / (0.8 * P))
    A.d['red'].line((540, 1000, 540, lerp(1000, 1320, p1)), fill=255, width=12)
    A.d['red'].polygon([(520, lerp(1000, 1320, p1)), (560, lerp(1000, 1320, p1)), (540, lerp(1000, 1320, p1) + 34)], fill=255)
    if p2 > 0:
        A.d['mid'].line((540, 1000, 540, lerp(1000, 760, p2)), fill=255, width=12)
        A.d['mid'].polygon([(520, lerp(1000, 760, p2)), (560, lerp(1000, 760, p2)), (540, lerp(1000, 760, p2) - 34)], fill=255)

def art_plank_road(A, cv, t, u):
    A.d['mid'].polygon([(60, 1500), (60, 700), (420, 760), (520, 1500)], fill=255)
    A.d['wash'].polygon([(560, 1500), (700, 760), (W - 60, 700), (W - 60, 1500)], fill=255)
    y0 = 1150
    A.d['ink'].line((80, y0, W - 80, y0 - 160), fill=255, width=12)
    for x in range(100, W - 80, 70):
        yy = y0 - (x - 80) / (W - 160) * 160
        A.d['ink'].line((x, yy, x - 30, yy + 70), fill=255, width=4)
    for k in range(6):
        x = (t * 70 + k * 170) % (W + 200) - 100
        yy = y0 - (x - 80) / (W - 160) * 160
        person(A, x, yy, 140, dir=1, robe=False, hat='helmet', spear=True, ph=t * 7 + k, layer='ink')

def elephant(A, x, y, s, dir=1, ph=0.0, layer='ink'):
    d = A.d[layer]
    def T(u, v): return (x + dir * u * s, y - v * s)
    d.polygon([T(*p) for p in ellipse_pts(0, 0.62, 0.48, 0.28)], fill=255)
    d.polygon([T(*p) for p in ellipse_pts(0.48, 0.72, 0.2, 0.2)], fill=255)
    trunk = [T(0.62 + 0.08 * math.sin(ph * 0.5 + f * 2), 0.6 - f * 0.5) for f in np.linspace(0, 1, 8)]
    d.line(trunk, fill=255, width=max(3, int(0.08 * s)))
    d.polygon([T(0.40, 0.84), T(0.30, 0.95), T(0.28, 0.60)], fill=255)
    for hu, off in ((0.28, 0), (0.15, 1.6), (-0.22, 3.1), (-0.35, 4.7)):
        a = 0.2 * math.sin(ph + off)
        d.line([T(hu, 0.45), T(hu + 0.1 * math.sin(a), 0.0)], fill=255, width=max(4, int(0.12 * s)))
    A.d['wash'].line([T(0.6, 0.6), T(0.75, 0.48)], fill=255, width=max(2, int(0.04 * s)))

def art_elephants(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        x = lerp(W + 100, 640, ease_out(u / (2 * P))) + k * 170
        elephant(A, x, GROUND - k * 10, 230 - k * 30, -1, t * 4 + k, layer='ink' if k == 0 else 'mid')
    for k in range(4):
        person(A, 110 + k * 70, GROUND, 170, dir=1, robe=False, hat='helmet', arm=95, arm2=85, layer='ink')
    for k in range(6):
        q = (u * 1.3 + k * 0.17) % 1
        arrow(A, lerp(330, 640, q), 1050 - 120 * math.sin(math.pi * q), math.atan2(-120 * math.pi * math.cos(math.pi * q), 310), 70)

def art_couch(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(580, GROUND), (1000, GROUND), (970, 1300), (610, 1300)], fill=255)
    A.d['ink'].rectangle((640, 1220, 940, 1250), fill=255)
    A.d['ink'].rectangle((640, 1150, 660, 1250), fill=255); A.d['ink'].rectangle((920, 1180, 940, 1250), fill=255)
    person(A, 790, 1220, 210, dir=-1, hat='crown', arm=lerp(30, 110, ease_out((u - P) / 0.3)), layer='ink')
    person(A, 330, GROUND, 230, dir=1, kneel=True, bow=40, arm=80, layer='ink')
    if u > P:
        A.flush(cv)
        stamp(cv, seal('岂容鼾睡', 44), 790, 920, t, t - u + P, rot=6)

def art_pontoon(A, cv, t, u):
    A.d['wash'].rectangle((60, 1150, W - 60, 1360), fill=170)
    waves(A, 1170, t, rows=4, amp=10, speed=2.5)
    p = ease_out(u / (2 * P))
    for k in range(int(12 * p)):
        x = 90 + k * 80
        A.d['ink'].ellipse((x - 30, 1235, x + 30, 1265), fill=255)
    A.d['ink'].rectangle((70, 1225, 70 + 920 * p, 1236), fill=255)
    for k in range(4):
        x = walk_x(60 - k * 110, 60 + 820 * p - k * 110, u - 0.4, 2 * P)
        person(A, x, 1225, 130, dir=1, robe=False, hat='helmet', spear=True, ph=t * 7 + k, layer='ink')
    city_wall(A, 820, W - 60, 1120, label=None, layer='mid')

def art_fengzhuang(A, cv, t, u):
    A.d['mid'].polygon([(60, 1000), (260, 760), (400, 860), (560, 720), (720, 860), (900, 760), (1020, 1000)], fill=150)
    ground(A, GROUND)
    for k in range(int(clamp(u / (3 * P)) * 18)):
        coin(A, 200 + (k % 6) * 110, GROUND - 26 - (k // 6) * 22, 34, layer='ink')
    for k in range(10):
        q = (u * 0.9 + k / 10) % 1
        coin(A, 160 + (k * 83) % 760, lerp(1000, GROUND - 80, q), 26, rot=t * 5 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('燕云', 52, (110, 110, 110)), 540, 820, t, t - u + P)

def art_yanyun(A, cv, t, u):
    A.d['mid'].polygon([(60, 1100), (260, 780), (400, 880), (560, 700), (720, 880), (900, 780), (1020, 1100)], fill=170)
    ground(A, GROUND)
    person(A, 540, GROUND, 300, dir=-1, hat='crown', arm=lerp(20, 60, ease_out(u / P)), bow=8, layer='ink')
    for k in range(4):
        y = 820 + k * 50
        x = (t * 60 + k * 300) % (W + 500) - 300
        A.d['wash'].line((x, y, x + 300, y), fill=255, width=20)

def art_oath(A, cv, t, u):
    palace(A, 540, GROUND, 760, layer='mid')
    A.d['wash'].rectangle((360, 1040, 720, GROUND), fill=0)
    stele(A, 540, GROUND - 20, 360, 160, rise=1.0, layer='mid')
    op = ease_out((u - 0.3) / (1.5 * P))
    A.d['yellow'].rectangle((360, 1040, 540 - 180 * op, GROUND - 20), fill=255)
    A.d['yellow'].rectangle((540 + 180 * op, 1040, 720, GROUND - 20), fill=255)
    if op > 0.6:
        fo = font(SERIF, 30, 'Black')
        for j, col in enumerate(('不杀士大夫', '及上书言事人')):
            for i, ch in enumerate(col):
                A.d['ink'].text((560 - j * 44, 1130 + i * 34), ch, font=fo, fill=255)

def art_axe(A, cv, t, u):
    """8-beat mystery: snowy night, two shadows on the window, the axe strikes, the candle dies."""
    ph = u / P
    palace(A, 540, GROUND, 860, layer='mid')
    wx0, wy0, wx1, wy1 = 330, 1010, 750, 1250
    light = 1.0 if ph < 6 else clamp(1 - (u - 6 * P) / 0.5)
    A.d['wash'].rectangle((wx0, wy0, wx1, wy1), fill=0)
    if light > 0:
        A.d['yellow'].rectangle((wx0, wy0, wx1, wy1), fill=int(150 * light * (0.9 + 0.1 * math.sin(t * 13))))
    for k in range(1, 5):
        A.d['ink'].line((wx0 + k * (wx1 - wx0) / 5, wy0, wx0 + k * (wx1 - wx0) / 5, wy1), fill=255, width=3)
    A.d['ink'].rectangle((wx0, wy0, wx1, wy1), outline=255, width=6)
    if light > 0:
        sway = 10 * math.sin(t * 11)
        person(A, 450 + sway, wy1, 200, dir=1, hat='crown', arm=50, layer='ink')
        lean = 30 if 2 <= ph < 4 else 5
        person(A, 640 - sway, wy1, 200, dir=-1, bow=lean, arm=60 if ph < 4 else 120, layer='ink')
        if ph >= 4:
            v = u - 4 * P
            ax = ease_expo(v / 0.2)
            A.d['ink'].line((470, wy1 - 150, lerp(470, 560, ax), lerp(wy1 - 300, wy1, ax)), fill=255, width=6)
            if v > 0.2:
                for k in range(8):
                    a = k * math.pi / 4
                    r = 50 * ease_out((v - 0.2) / 0.3)
                    A.d['red'].line((560, wy1, 560 + r * math.cos(a), wy1 + r * math.sin(a) * 0.4), fill=int(255 * clamp(1 - (v - 0.2) / 0.6)), width=4)
    for k in range(34):
        q = (t * 0.25 + k / 34) % 1
        x = 80 + (k * 37) % 920 + 20 * math.sin(t + k); y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    if ph >= 6:
        A.flush(cv)
        stamp(cv, seal('千古之谜', 50, INK), 860, 900, t, t - u + 6 * P, rot=6)

def art_golden_box(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(380, GROUND), (700, GROUND), (670, 1290), (410, 1290)], fill=255)
    person(A, 540, 1290, 220, dir=1, hat='crown', arm=40, layer='ink')
    lid = ease_out((u - P) / 0.4)
    A.d['yellow'].rectangle((760, 1260, 960, GROUND), fill=255)
    A.d['yellow'].polygon([(760, 1260), (960, 1260), (960 - 40 * lid, 1260 - 100 * lid), (760 - 40 * lid, 1260 - 100 * lid)], fill=255)
    A.d['ink'].rectangle((760, 1260, 960, GROUND), outline=255, width=4)
    for k in range(3):
        person(A, 120 + k * 80, GROUND, 180, dir=1, kneel=True, bow=40, arm=70, layer='mid')
    if lid > 0.8:
        A.flush(cv)
        stamp(cv, seal('金匮之盟', 44), 860, 1040, t, t - u + P + 0.4, rot=5)

def art_song_legacy(A, cv, t, u):
    sun(cv, 540, 1050, 260, QING, 120)
    fo = font(BRUSH, 520)
    ch = '宋'
    p = ease_out(u / (1.5 * P))
    tmp = Image.new('L', (W, H), 0)
    ImageDraw.Draw(tmp).text((540 - fo.getlength(ch) / 2, 760), ch, font=fo, fill=255)
    fld = G.transition_field()
    a = np.asarray(tmp, np.float32) * np.clip((p * 1.3 - fld) / 0.08, 0, 1)
    m = Image.fromarray(a.astype(np.uint8))
    A.im['ink'].paste(m, (0, 0), m)
    ground(A, GROUND)
    for k in range(6):
        person(A, 140 + k * 160, GROUND, 150 + (k % 2) * 20, dir=1 if k < 3 else -1, arm=40 + 30 * (k % 2), layer='mid')

def art_hook_robe(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 540, GROUND - 10, 640, 560, layer='mid', open_=1.0)
    person(A, 540, GROUND, 300, dir=1, arm=40, layer='ink')
    yellow_robe(A, 540, 300, ease_expo((u - 0.2) / 0.35))
    for k in range(4):
        side = -1 if k % 2 == 0 else 1
        person(A, 540 + side * (230 + (k // 2) * 140), GROUND, 200, dir=-side, robe=False, hat='helmet', kneel=True, bow=45, arm=60, layer='ink')

def art_hook_cups(A, cv, t, u):
    A.d['mid'].rectangle((240, 1250, 840, 1280), fill=255)
    for lx in (270, 800): A.d['mid'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    person(A, 540, 1240, 200, dir=1, hat='crown', arm=140, layer='ink')
    for i, x in enumerate((160, 920, 300, 780)):
        person(A, x, GROUND, 220, dir=1 if x < 540 else -1, arm=150, layer='ink' if i < 2 else 'mid')

def art_hook_axe(A, cv, t, u):
    art_axe(A, cv, t, u + 4 * P)


# ================================================================ unique scenes (no repeats)
def art_jiamaying(A, cv, t, u):
    sun(cv, 540, 900, lerp(80, 220, ease_out(u / (2 * P))), ZHU, 120)
    ground(A, GROUND)
    for k, (x, w, h) in enumerate(((170, 260, 220), (900, 260, 220))):
        tent(A, x, GROUND - 10, w, h, layer='mid')
    A.d['mid'].rectangle((400, 1180, 680, GROUND), fill=255)
    A.d['mid'].polygon([(370, 1180), (710, 1180), (540, 1080)], fill=255)
    A.d['wash'].rectangle((500, 1250, 580, GROUND), fill=0)
    for k in range(6):
        a = t * 1.1 + k * 1.05
        r = 120 + 40 * math.sin(t + k)
        x = 540 + r * math.cos(a); y = 1000 + r * 0.45 * math.sin(a)
        A.d['wash'].arc((x - 40, y - 20, x + 40, y + 20), 0, 270, fill=255, width=6)
    person(A, 760, GROUND, 230, dir=-1, female=True, baby=True, layer='ink')

def art_enlist(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 760, GROUND - 10, 520, 460, layer='mid', open_=1.0)
    flag(A, 980, GROUND, 520, t, w=120)
    A.flush(cv)
    stamp(cv, seal('郭', 50), 1040, GROUND - 470, t, t - u)
    person(A, 780, GROUND, 260, dir=-1, arm=lerp(20, 70, ease_out((u - P) / 0.3)), robe=False, hat='helmet', layer='ink')
    x = walk_x(80, 460, u, 1.5 * P)
    person(A, x, GROUND, 230, dir=1, robe=False, ph=t * 6 if u < 1.5 * P else None,
           kneel=u > 2 * P, bow=35 if u > 2 * P else 0, arm=80 if u > 2 * P else 20, layer='ink')

def art_gaoping(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        x = (k * 120 - t * 700) % (W + 200) - 100
        A.d['wash'].line((x, 1060 + k * 28, x + 160, 1060 + k * 28), fill=255, width=4)
    lead = lerp(-100, 420, ease_out(u / (2 * P)))
    person(A, lead, GROUND, 290, dir=1, robe=False, hat='helmet', ph=t * 12, arm=100, layer='ink')
    A.d['ink'].line((lead + 40, GROUND - 230, lead + 230, GROUND - 330), fill=255, width=7)
    A.d['ink'].polygon([(lead + 220, GROUND - 350), (lead + 260, GROUND - 320), (lead + 230, GROUND - 300)], fill=255)
    for k in range(3):
        person(A, lead - 170 - k * 120, GROUND, 230, dir=1, robe=False, hat='helmet', spear=True, ph=t * 12 + k, layer='mid')
    for k in range(4):
        fall = -60 * ease_out((u - 2 * P - k * 0.1) / 0.3) if u > 2 * P else 0
        person(A, 760 + k * 80, GROUND, 220, dir=-1, robe=False, hat='helmet', spear=True, fall=-fall, layer='mid' if k % 2 else 'ink')

def art_qingliu(A, cv, t, u):
    A.d['mid'].polygon([(60, GROUND), (60, 760), (330, 820), (420, GROUND)], fill=255)
    A.d['mid'].polygon([(W - 60, GROUND), (W - 60, 760), (750, 820), (660, GROUND)], fill=255)
    A.d['ink'].rectangle((420, 1080, 660, 1110), fill=255)
    A.d['ink'].polygon([(400, 1080), (680, 1080), (620, 1020), (460, 1020)], fill=255)
    A.d['ink'].text((505, 1030), '清流', font=font(SERIF, 36, 'Black'), fill=0)
    ground(A, GROUND)
    x = lerp(-150, 720, ease_out(u / (2.4 * P)))
    rider(A, x, GROUND, 230, 1, t * 14, layer='ink', spear=True)
    if u > 2.4 * P:
        person(A, 900, GROUND, 220, dir=-1, robe=False, hat='helmet', kneel=True, bow=45, arm=70, layer='ink')
        A.flush(cv)
        stamp(cv, seal('皇甫晖', 44), 900, 1020, t, t - u + 2.4 * P, rot=6)

def art_young_emperor(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(300, GROUND), (780, GROUND), (740, 1270), (340, 1270)], fill=255)
    A.d['ink'].polygon([(420, 1270), (660, 1270), (660, 1040), (620, 980), (460, 980), (420, 1040)], fill=255)
    A.d['wash'].rectangle((470, 1060, 610, 1270), fill=0)
    person(A, 540, 1270, 110, dir=1, hat='crown', arm=20, layer='ink')
    for k in range(12):
        x = 700 + k * 16
        A.d['gold'].line((x, 760, x + 4 * math.sin(t * 2 + k), 1260), fill=255, width=3)
    person(A, 820, 1270, 220, dir=-1, female=True, hat='crown', arm=30, layer='wash')
    lean = 25 + 8 * math.sin(t * 3)
    for k, x in enumerate((140, 230)):
        person(A, x, GROUND, 220, dir=1, bow=lean, arm=60, layer='ink' if k else 'mid')

def art_song_found(A, cv, t, u):
    city_wall(A, 60, W - 60, 1150, gate_x=540, label='汴京', open_=1.0)
    ground(A, GROUND)
    rise = ease_out(u / (2 * P))
    pole_top = lerp(1150, 660, rise)
    A.d['ink'].line((540, 1150, 540, pole_top), fill=255, width=8)
    pts_top = [(540 + i * 26, pole_top + 10 * math.sin(t * 5 + i * 0.6)) for i in range(11)]
    pts_bot = [(540 + i * 26, pole_top + 220 + 10 * math.sin(t * 5 + i * 0.6)) for i in range(10, -1, -1)]
    A.d['red'].polygon(pts_top + pts_bot, fill=255)
    A.d['red'].text((600, pole_top + 50), '宋', font=font(SERIF, 120, 'Black'), fill=0)
    for k in range(5):
        for side in (-1, 1):
            person(A, 540 + side * (140 + k * 80), GROUND, 150, dir=-side, kneel=u > P, bow=45 if u > P else 0, arm=60,
                   layer='ink' if k % 2 == 0 else 'mid')

def art_two_li(A, cv, t, u):
    ground(A, GROUND)
    for i, x in enumerate((240, 840)):
        cut = ease_out((u - (1 + i) * P) / 0.35) if u > (1 + i) * P else 0
        ang = cut * 1.3 * (1 if i == 0 else -1)
        top = rotp((x, 700), (x, GROUND), ang)
        A.d['ink'].line((x, GROUND, top[0], top[1]), fill=255, width=8)
        fx, fy = top
        A.d['mid'].polygon([(fx, fy), rotp((fx + 160, fy), (fx, fy), ang), rotp((fx + 160, fy + 200), (fx, fy), ang), rotp((fx, fy + 200), (fx, fy), ang)], fill=255)
        A.d['ink'].text(rotp((fx + 40, fy + 50), (fx, fy), ang), '李', font=font(SERIF, 90, 'Black'), fill=0)
    rider(A, lerp(100, 540, ease_out(u / (2 * P))), GROUND, 240, 1, t * 13, layer='ink', spear=True)

def art_sleepless(A, cv, t, u):
    A.d['wash'].ellipse((760, 640, 880, 760), fill=255)
    for k in range(6):
        x = 120 + k * 170
        A.d['mid'].rectangle((x, 900, x + 40, GROUND), fill=255)
    A.d['mid'].rectangle((60, 860, W - 60, 900), fill=255)
    ground(A, GROUND)
    x = 540 + 220 * math.sin(t * 0.9)
    person(A, x, GROUND, 260, dir=1 if math.cos(t * 0.9) > 0 else -1, hat='crown', arm=-10, bow=10, ph=t * 3, layer='ink')
    person(A, 950, GROUND, 230, dir=-1, bow=20, arm=60, layer='mid')

def art_to_capital(A, cv, t, u):
    pts = []
    for j in range(40):
        a = 2 * math.pi * j / 40
        r = 380 + 40 * math.sin(a * 3 + 1)
        pts.append((540 + r * math.cos(a), 1060 + r * math.sin(a) * 0.8))
    A.d['qing'].polygon(pts, fill=110); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    for k in range(10):
        a = k * 2 * math.pi / 10 + 0.3
        sx, sy = 540 + 330 * math.cos(a), 1060 + 260 * math.sin(a)
        q = (u * 0.8 + k * 0.1) % 1
        A.d['red'].line((sx, sy, lerp(sx, 540, 0.8), lerp(sy, 1060, 0.8)), fill=120, width=4)
        px, py = lerp(sx, 540, q * 0.8), lerp(sy, 1060, q * 0.8)
        A.d['ink'].ellipse((px - 10, py - 10, px + 10, py + 10), fill=255)
    A.flush(cv)
    stamp(cv, seal('京', 80), 540, 1060, t, t - u + 0.1)

def art_civil(A, cv, t, u):
    city_wall(A, 520, W - 60, 1150, gate_x=780, label='州府', open_=1.0)
    ground(A, GROUND)
    give = ease_out((u - 0.4) / 0.5)
    person(A, 400, GROUND, 260, dir=1, robe=False, hat='helmet', arm=lerp(20, 80, give), layer='ink')
    person(A, 620, GROUND, 250, dir=-1, robe=True, hat='knot', arm=lerp(20, 80, give), layer='ink')
    sx = lerp(450, 560, give)
    A.d['red'].rectangle((sx - 18, GROUND - 200, sx + 18, GROUND - 164), fill=255)
    if u > P:
        A.flush(cv)
        stamp(cv, seal('知州', 46), 620, 960, t, t - u + P)

def art_court_hu(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(400, 1200), (680, 1200), (650, 1120), (430, 1120)], fill=255)
    person(A, 540, 1120, 170, dir=1, hat='crown', arm=40, layer='ink')
    kk = (t - G.B0) / P
    b = 20 + 25 * math.exp(-((kk % 1) * P) / 0.15)
    for row in range(2):
        for k in range(4):
            for side in (-1, 1):
                x = 540 + side * (150 + k * 95)
                y = GROUND - row * 70
                hand = person(A, x, y, 170 - row * 20, dir=-side, bow=b, arm=70, layer='ink' if row == 0 else 'mid')
                A.d['ink' if row == 0 else 'mid'].line((hand[0], hand[1], hand[0] - side * 4, hand[1] - 50), fill=255, width=6)

def art_li_yu(A, cv, t, u):
    A.d['wash'].rectangle((60, 1180, W - 60, 1320), fill=170)
    waves(A, 1190, t, rows=3, amp=8, speed=1.5)
    boat(A, 820, 1250, 180, t)
    ground(A, GROUND)
    person(A, 380, GROUND, 250, dir=1, kneel=u > P, bow=45 if u > P else 10, arm=80, layer='mid')
    A.d['ink'].rectangle((450, GROUND - 160, 490, GROUND - 120), fill=255)
    for k in range(3):
        person(A, 120 + k * 60, GROUND, 210, dir=1, robe=False, hat='helmet', spear=True, layer='ink')
    for k in range(10):
        q = (u * 0.4 + k / 10) % 1
        x = 160 + k * 90 + 30 * math.sin(t + k); y = lerp(700, 1150, q)
        A.d['wash'].ellipse((x - 8, y - 5, x + 8, y + 5), fill=255)

def art_taiyuan(A, cv, t, u):
    city_wall(A, 360, W - 60, 1120, gate_x=700, label='太原')
    lvl = lerp(GROUND + 20, 1260, ease_out(u / (2.5 * P)))
    A.d['mid'].rectangle((60, lvl, W - 60, GROUND + 30), fill=255)
    waves(A, int(lvl) - 30, t, rows=3, amp=12, speed=4)
    A.d['qing'].polygon([(60, 900), (300, 900), (340, lvl), (60, lvl)], fill=140)
    for k in range(3):
        person(A, 90 + k * 70, 1100, 150, dir=1, robe=False, hat='helmet', spear=True, layer='ink')
    if u > 3 * P:
        A.flush(cv)
        stamp(cv, seal('终不能克', 44, INK), 700, 960, t, t - u + 3 * P, rot=5)

def art_hook_hand_robe(A, cv, t, u):
    """Hook: hands fling the yellow robe — a different framing from the tent set piece."""
    for k in range(3):
        x = 140 + k * 120
        person(A, x, GROUND, 230, dir=1, robe=False, hat='helmet', arm=150, layer='ink' if k == 1 else 'mid')
    q = ease_out(u / 0.6)
    cx, cy = lerp(300, 720, q), lerp(820, 1080, q) - 160 * math.sin(math.pi * q)
    rot_ = q * 1.2
    pts = [(-110, -60), (110, -60), (160, 120), (-160, 120)]
    A.d['yellow'].polygon([rotp((cx + a, cy + b), (cx, cy), rot_) for a, b in pts], fill=255)
    for k in range(3):
        y_ = -20 + k * 45
        A.d['gold'].line([rotp((cx - 100, cy + y_), (cx, cy), rot_), rotp((cx + 100, cy + y_), (cx, cy), rot_)], fill=220, width=3)
    ground(A, GROUND)
    person(A, 860, GROUND, 290, dir=-1, arm=20, layer='ink')

def art_hook_toast(A, cv, t, u):
    """Hook: a close-up of two wine cups clinking."""
    for i, side in enumerate((-1, 1)):
        x = 540 + side * lerp(260, 70, ease_out(u / 0.5))
        A.d['ink'].polygon([(x - 60, 980), (x + 60, 980), (x + 30, 1100), (x - 30, 1100)], fill=255)
        A.d['ink'].rectangle((x - 8, 1100, x + 8, 1200), fill=255)
        A.d['ink'].rectangle((x - 50, 1200, x + 50, 1215), fill=255)
        A.d['mid'].polygon([(x - 260 * side, 1250), (x - 40 * side, 1040), (x - 10 * side, 1070), (x - 220 * side, 1290)], fill=255)
    if u > 0.45:
        for k in range(10):
            a = -math.pi / 2 + (k - 4.5) * 0.25
            r = 140 * ease_out((u - 0.45) / 0.4)
            A.d['qing'].ellipse((540 + r * math.cos(a) - 7, 970 + r * math.sin(a) - 7, 540 + r * math.cos(a) + 7, 970 + r * math.sin(a) + 7), fill=255)

def art_hook_sheathe(A, cv, t, u):
    """Hook: a sword slides back into its sheath while scholars stand safe."""
    ground(A, GROUND)
    for k in range(4):
        person(A, 120 + k * 90, GROUND, 200, dir=1, arm=80, layer='mid')
        A.d['mid'].rectangle((160 + k * 90, GROUND - 160, 176 + k * 90, GROUND - 100), fill=255)
    ins = ease_out(u / (1.5 * P))
    A.d['ink'].rounded_rectangle((640, 900, 690, 1350), radius=14, fill=255)
    A.d['ink'].line((665, lerp(620, 900, ins), 665, lerp(900, 1180, ins)), fill=255, width=14)
    A.d['ink'].rectangle((610, lerp(600, 880, ins), 720, lerp(620, 900, ins)), fill=255)
    if u > 1.5 * P:
        A.flush(cv)
        stamp(cv, seal('不杀', 56), 860, 1000, t, t - u + 1.5 * P, rot=6)

def art_hook_candle(A, cv, t, u):
    """Hook: a single candle; an axe-shaped shadow sweeps across the wall, the flame gutters."""
    A.d['mid'].rectangle((60, 700, W - 60, GROUND), fill=110)
    A.d['ink'].rectangle((520, 1150, 560, GROUND), fill=255)
    A.d['ink'].rectangle((480, GROUND - 20, 600, GROUND), fill=255)
    gut = 1 - ease_out((u - 1.5 * P) / 0.3) if u > 1.5 * P else 1
    fh = (70 + 12 * math.sin(t * 15)) * gut
    if fh > 2:
        A.d['red'].polygon([(522, 1150), (558, 1150), (546 + 6 * math.sin(t * 9), 1150 - fh), (538, 1150 - fh)], fill=255)
    sw = ease_out(u / (1.3 * P))
    ax = lerp(900, 300, sw); ay = lerp(760, 1000, sw)
    A.d['ink'].line((ax, ay, ax + 260, ay - 200), fill=200, width=16)
    A.d['ink'].polygon([(ax - 40, ay - 40), (ax + 30, ay - 70), (ax + 50, ay + 30), (ax - 30, ay + 50)], fill=200)

def art_march_snow(A, cv, t, u):
    ground(A, GROUND)
    for k in range(32):
        q = (t * 0.3 + k / 32) % 1
        x = 80 + (k * 37) % 920 + 20 * math.sin(t + k); y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    lead = lerp(-100, 640, ease_out(u / (3 * P)))
    rider(A, lead, GROUND, 250, 1, t * 7, layer='ink')
    flag(A, lead - 60, GROUND - 230, 300, t, w=110)
    A.flush(cv)
    stamp(cv, seal('周', 46), lead + 10, GROUND - 480, t, t - u)
    for k in range(6):
        x = lead - 220 - k * 110
        person(A, x, GROUND - (k % 2) * 16, 170, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, layer='ink' if k % 2 == 0 else 'mid')

# ================================================================ script
CHAPTERS = {16: ('第一回', '香孩儿'), 48: ('第二回', '陈桥兵变'), 80: ('第三回', '杯酒释兵权'),
            112: ('第四回', '一统江南'), 144: ('第五回', '斧声烛影')}
siege = lambda label: (lambda A, cv, t, u: L.art_siege(A, cv, t, u, label=label))
surrender = lambda label: (lambda A, cv, t, u: L.art_surrender(A, cv, t, u, label=label))

CARDS = [
    C(0, 2, 'hook', 'num', num='黄袍加身', line='一夜之间当皇帝', art=art_hook_hand_robe),
    C(2, 4, 'hook', 'num', num='杯酒', line='轻松收回兵权', art=art_hook_toast),
    C(4, 6, 'hook', 'num', num='不杀士大夫', line='立下太庙誓碑', art=art_hook_sheathe),
    C(6, 8, 'hook', 'num', num='斧声烛影', line='死因千古成谜', art=art_hook_candle),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 香孩儿
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=927, main='生于夹马营', sub='赤光绕室 · 异香经夜不散', note='人称香孩儿', art=art_jiamaying),
    C(22, 26, 'life', 'card', year=940, main='少年习武', sub='一条杆棒 · 打遍天下', note='一条杆棒等身齐 打下四百座军州', art=art_staff),
    C(26, 30, 'life', 'card', year=946, main='千里送京娘', sub='仗义护送 · 不图回报', note='民间传说 流传千年', art=art_jingniang),
    C(30, 34, 'war', 'card', year=948, main='投军郭威', sub='二十二岁 · 投奔郭威帐下', note='自此 戎马半生', art=art_enlist),
    C(34, 38, 'war', 'card', year=954, main='高平之战', sub='率死士冲阵 · 反败为胜', note='太祖率众先犯其锋', art=art_gaoping),
    C(38, 42, 'war', 'card', year=956, main='清流关', sub='奇袭破关 · 生擒皇甫晖', note='一鼓而下滁州', art=art_qingliu),
    C(42, 46, 'court', 'card', year=959, main='点检作天子', sub='北伐途中 · 惊现神秘木牌', note='得一囊 中有木三尺余', art=art_mubai),
    C(46, 48, 'court', 'card', year=959, main='主少国疑', sub='柴荣病逝 · 七岁幼主登基', art=art_young_emperor),
    # ---- 第二回 陈桥兵变
    C(48, 50, 'night', 'chapter'),
    C(50, 54, 'war', 'card', year=960, main='边关急报', sub='契丹北汉 · 联兵南下', note='镇定二州驰奏', art=art_messenger),
    C(54, 58, 'war', 'card', year=960, main='领兵北上', sub='赵匡胤率禁军出征', note='正月初三 大军出汴京', art=art_march_snow),
    C(58, 62, 'night', 'card', year=960, main='夜宿陈桥', sub='兵营之中 · 暗流涌动', note='军中知星者 言日下复有一日', art=art_camp),
    C(62, 70, 'night', 'card', year=960, main='黄袍加身', sub='将士披黄袍于其身 · 拥立为帝', note='诸将已擐甲执兵 直扣寝门', art=art_huangpao),
    C(70, 74, 'court', 'card', year=960, main='兵不血刃', sub='回师汴京 · 秋毫无犯', note='不得惊犯太后幼主 不得凌暴公卿', art=art_peaceful),
    C(74, 80, 'empire', 'card', year=960, main='建立大宋', sub='国号宋 · 年号建隆', seal='建隆', note='自此 大宋三百一十九年', art=art_song_found),
    # ---- 第三回 杯酒释兵权
    C(80, 82, 'court', 'chapter'),
    C(82, 86, 'war', 'card', year=960, main='二李之叛', sub='李筠 李重进 · 先后起兵', note='御驾亲征 数月平定', art=art_two_li),
    C(86, 90, 'night', 'card', year=961, main='夜不能寐', sub='问计赵普 · 如何长治久安', note='此非他 节镇太重 君弱臣强而已', art=art_sleepless),
    C(90, 96, 'court', 'card', year=961, main='杯酒释兵权', sub='一场酒宴 · 收回兵权', note='人生如白驹过隙 不如多积金钱 厚自娱乐', art=art_banquet),
    C(96, 98, 'court', 'card', year=962, main='强干弱枝', sub='禁军尽归中央', art=art_to_capital),
    C(98, 100, 'court', 'card', year=963, main='文官治州', sub='以文臣知州事', art=art_civil),
    C(100, 102, 'night', 'card', year=963, main='雪夜访普', sub='风雪之夜 · 君臣定策', art=art_snow_visit),
    C(102, 104, 'court', 'card', year=963, main='先南后北', sub='统一天下之大计', art=art_south_north),
    C(104, 112, 'works', 'unify'),
    # ---- 第四回 一统江南
    C(112, 114, 'works', 'chapter'),
    C(114, 118, 'war', 'card', year=965, main='平定后蜀', sub='六十六日 · 蜀道不再难', note='十四万人齐解甲 更无一个是男儿', art=art_plank_road),
    C(118, 122, 'war', 'card', year=971, main='平定南汉', sub='破象阵 · 岭南归宋', note='南汉以象为阵 宋军强弩射之', art=art_elephants),
    C(122, 126, 'court', 'card', year=974, main='卧榻之侧', sub='岂容他人鼾睡', note='江南亦有何罪 但天下一家', art=art_couch),
    C(126, 130, 'works', 'card', year=974, main='浮桥渡江', sub='采石矶架浮桥 · 兵临金陵', note='如履平地', art=art_pontoon),
    C(130, 134, 'works', 'card', year=975, main='李煜出降', sub='南唐后主 · 肉袒出降', note='问君能有几多愁 恰似一江春水向东流', art=art_li_yu),
    C(134, 138, 'empire', 'card', year=975, main='封桩库', sub='积攒钱帛 · 欲赎燕云十六州', note='俟满三五百万 当遣使契丹 以赎山后诸郡', art=art_fengzhuang),
    C(138, 142, 'war', 'card', year=969, main='亲征北汉', sub='太原城下 · 无功而返', note='引汾水灌城 终不能克', art=art_taiyuan),
    C(142, 144, 'fate', 'card', year=975, main='燕云之憾', sub='终其一生 · 未能北望', art=art_yanyun),
    # ---- 第五回 斧声烛影
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'court', 'card', year=962, main='太庙誓碑', sub='不杀士大夫 · 及上书言事人', note='子孙有渝此誓者 天必殛之', art=art_oath),
    C(150, 154, 'court', 'card', year=973, main='文人治国', sub='殿试成为定制 · 重文抑武', note='宰相须用读书人', art=art_court_hu),
    C(154, 162, 'death', 'card', year=976, main='斧声烛影', sub='十月二十日夜 · 兄弟对饮', note='烛影下 或见帝离席 引柱斧戳地', art=art_axe),
    C(162, 166, 'death', 'card', year=976, main='兄终弟及', sub='赵光义继位 · 疑云重重', note='金匮之盟 真伪难辨', art=art_golden_box),
    C(166, 170, 'end', 'card', year=976, main='造极赵宋', sub='开创三百年大宋 · 文化登峰', note='华夏民族之文化 造极于赵宋之世', art=art_song_legacy),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z):
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
for mod in (G, L, Wd, Tz, Z):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    s = '公元' + cn_num(yr) + '年'
    im = text_img(s, SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=QING + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, S.art_emperor)
    fx = Art()
    ink_in(cv, text_img('赵 匡 胤', SERIF, 50, QING, 'Bold', bleed=False, spacing=16), W / 2, 300, t, s0)
    chars_in(cv, fx, '宋太祖', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('建隆', 66), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元927 — 976', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '欺负孤儿寡母？', BRUSH, 110, ZHU, W / 2, 420, t, s0, stagger=0.06, seed=5)
    chars_in(cv, fx, '仁厚开国之君？', BRUSH, 110, INK, W / 2, 560, t, bt(c[0] + 1), stagger=0.06, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    meiping(A, 860, 1150, 220, u / 0.8, t)
    plum_branch(A, 120, 760, u / 1.0, t, seed=4)
    A.flush(cv, alpha=clamp(u / 0.6) * 0.75)
    fx = Art()
    chars_in(cv, fx, '开宋之祖', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('太祖', 64), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('不杀功臣 · 不杀前朝孤儿', SERIF, 48, DIM, 'SemiBold', bleed=False, spacing=6), W / 2, 960, t, END + 0.6, 0.4)
    type_in(cv, text_img('却在一个雪夜 · 留下千古之谜', SERIF, 52, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '斧声烛影', BRUSH, 120, QING, W / 2, 1200, t, END + 1.15, stagger=0.07, drop=30, splash=False)
    type_in(cv, text_img('你信哪种说法？评论区聊聊', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=QING + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(252, 248, 240, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=INK + (200,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 明太祖朱元璋', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, unify=scene_unify, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第伍集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(8):
        q = text_img('一夜黄袍加身 · 他凭什么坐稳江山？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 320, 335, W / 2 + 320, 335), fill=QING + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, QING, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=QING + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=ZHU + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(int(round(yr - BORN + 1))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=QING + (255,))
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
