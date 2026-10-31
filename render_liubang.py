# 千古人物志 · 第拾壹集 · 汉高祖刘邦 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈，墨色最后绘制）。每一幕画面均为本集新画，不重复。
# 本集特色：汉代漆器 —— 黑朱两色 · 瓦当章回卡（长乐 未央 千秋 万岁 汉并天下）· 云气纹边角
#          · 八拍「鸿门宴」 · 楚河汉界棋盘回顾 · 六拍「垓下 · 四面楚歌」
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_genghis as Gh         # engine + helpers (ink layers drawn last)
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
from render_kangxi import rect, lantern
from render_songtaizu import tent, campfire

F.RIPPLE = False

BORN, DIED = 256, 195               # 公元前
END_BEAT = 170
LACQ = (150, 30, 24)                # 漆朱
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

# ================================================================ episode look
G.base_bg.cache_clear()
G.draw_background = L.G.draw_background if False else G.draw_background
WM = dict(hook='汉', life='邦', court='约', night='夜', war='戰', empire='汉', works='楚', fate='歌', death='陵', end='汉')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire'):
    G.THEMES[k]['part'] = 'lacq'
for k in ('night', 'death', 'fate', 'war', 'works'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['empire']['sun'] = (LACQ, 260, (W * 0.5, 820))
G.THEMES['works']['sun'] = ((90, 90, 96), 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (LACQ, 210, (W * 0.5, 720))
G.THEMES['hook']['tint'] = (1.02, 0.98, 0.95)
G.base_bg.cache_clear()

MTN_COL = {'night': (44, 40, 44), 'death': (60, 56, 56), 'war': (96, 50, 40), 'works': (70, 62, 60)}
def draw_background(t, theme):
    """漆器: ink-black ranges with a vermilion-washed nearest ridge."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(150, 136, 130), (100, 82, 78), MTN_COL.get(theme, (120, 52, 40))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'lacq':
        return Gh.particle_sprite(kind, q)
    s = 40
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [LACQ, (40, 30, 28), (190, 70, 50)][q]
    d.arc((10, 10, 30, 30), 200, 470, fill=col + (220,), width=4)
    return im.filter(ImageFilter.GaussianBlur(0.6))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """云气纹: vermilion cloud-scroll hooks on a black rule."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 160, y), fill=INK + (190,), width=4); d.line((x, y, x, y + sy * 160), fill=INK + (190,), width=4)
        for k in range(3):
            cx, cy = x + sx * (36 + k * 40), y + sy * 22
            box = (cx - 14, cy - 14, cx + 14, cy + 14)
            d.arc(box, 180 if sx > 0 else 0, 450 if sx > 0 else 270, fill=LACQ + (230,), width=4)
            cx, cy = x + sx * 22, y + sy * (36 + k * 40)
            d.arc((cx - 14, cy - 14, cx + 14, cy + 14), 90, 360, fill=LACQ + (230,), width=4)
G.draw_frame_border = draw_frame_border

# ================================================================ 瓦当 chapter card
TILE = {16: '长乐', 48: '未央', 80: '千秋', 112: '万岁', 144: '汉并天下'}
def wadang(A, cx, cy, r, p, layer='ink'):
    rr = r * ease_out(p)
    if rr < 4: return
    A.d['mid'].ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=200)
    A.d[layer].ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=255, width=max(4, int(r * 0.06)))
    A.d[layer].ellipse((cx - rr * 0.82, cy - rr * 0.82, cx + rr * 0.82, cy + rr * 0.82), outline=255, width=4)
    A.d[layer].ellipse((cx - rr * 0.2, cy - rr * 0.2, cx + rr * 0.2, cy + rr * 0.2), outline=255, width=5)
    for a in range(4):
        ang = a * math.pi / 2 + math.pi / 4
        A.d[layer].line((cx + rr * 0.2 * math.cos(ang), cy + rr * 0.2 * math.sin(ang), cx + rr * 0.82 * math.cos(ang), cy + rr * 0.82 * math.sin(ang)), fill=255, width=4)

def art_tile_chapter(A, cv, t, u):
    wadang(A, 540, 880, 300, u / 0.5)
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_tile_chapter)
    words = TILE.get(c[0], '长乐')
    pos = [(-1, -1), (1, -1), (-1, 1), (1, 1)] if len(words) == 4 else [(0, -1), (0, 1)]
    order = [1, 3, 0, 2] if len(words) == 4 else [0, 1]
    for i, ch in enumerate(words):
        dx, dy = pos[order[i]] if len(words) == 4 else pos[i]
        ink_in(cv, text_img(ch, SERIF, 120 if len(words) == 4 else 150, LACQ, 'Black', bleed=False),
               540 + dx * 115, 880 + dy * 115, t, s0 + 0.3 + i * 0.12, dur=0.25, settle=1.15)
    ink_in(cv, text_img(no, SERIF, 56, LACQ, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ primitives
def snake(A, x0, y0, L_, t, cut=0.0, layer='ink'):
    pts = [(x0 + f * L_, y0 + 24 * math.sin(f * 10 + t * 3)) for f in np.linspace(0, 1, 30)]
    if cut <= 0:
        A.d['wash'].line(pts, fill=255, width=26); A.d[layer].line(pts, fill=255, width=4)
    else:
        a, b = pts[:15], pts[15:]
        sep = 60 * ease_out(cut)
        A.d['wash'].line([(x - sep, y) for x, y in a], fill=255, width=26)
        A.d['wash'].line([(x + sep, y) for x, y in b], fill=255, width=26)
        A.d['red'].ellipse((x0 + L_ / 2 - 20, y0 - 10, x0 + L_ / 2 + 20, y0 + 30), fill=int(255 * min(1, cut * 2)))

def chu_soldier(A, x, y, h, dir=1, layer='ink', **kw):
    person(A, x, y, h, dir=dir, robe=False, hat='helmet', layer=layer, **kw)

def low_table(A, x0, x1, y, layer='ink'):
    A.d[layer].rectangle((x0, y, x1, y + 22), fill=255)
    A.d[layer].rectangle((x0 + 20, y + 22, x0 + 36, y + 70), fill=255)
    A.d[layer].rectangle((x1 - 36, y + 22, x1 - 20, y + 70), fill=255)

# ================================================================ hooks
def art_l_hook_old(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        p = ease_out((u - k * 0.08) / 0.4)
        flag(A, 80 + k * 100, GROUND, 220 * p, t + k, w=70)
    person(A, 540, GROUND, 300, dir=1, hat='knot', arm=lerp(20, 150, ease_out(u / P)), layer='ink')
    A.d['ink'].line((560, GROUND - 260, 600, GROUND - 400), fill=255, width=5)

def art_l_hook_tingzhang(A, cv, t, u):
    A.d['mid'].rectangle((620, 1060, 900, GROUND), fill=255)
    A.d['ink'].polygon([(580, 1070), (940, 1070), (860, 980), (660, 980)], fill=255)
    A.d['ink'].rectangle((700, 1000, 820, 1040), fill=255)
    A.d['ink'].text((712, 1004), '泗水亭', font=font(SERIF, 32, 'Black'), fill=0)
    ground(A, GROUND)
    person(A, 340, GROUND, 240, dir=1, hat='knot', kneel=True, bow=-10, arm=150, layer='ink')
    A.d['ink'].polygon([(360, GROUND - 180), (400, GROUND - 180), (396, GROUND - 140), (364, GROUND - 140)], fill=255)

def art_l_hook_seven(A, cv, t, u):
    n = min(7, int(u / (0.28)) + 1)
    for i in range(n):
        x = 120 + i * 140
        A.d['ink'].rectangle((x, 1100, x + 110, 1260), outline=255, width=5)
        A.d['ink'].text((x + 28, 1130), cn_num(i + 1), font=font(SERIF, 70, 'Black'), fill=255)
    if n >= 7:
        A.flush(cv)
        stamp(cv, seal('汉', 90), 540, 960, t, t - u + 7 * 0.28)
    ground(A, GROUND)

def art_l_hook_commoner(A, cv, t, u):
    ground(A, GROUND)
    person(A, 300, GROUND, 230, dir=1, robe=False, hat='knot', ph=None, arm=60, layer='mid')
    A.d['ink'].line((380, GROUND - 120, 420, GROUND), fill=255, width=5)
    q = ease_out(u / (1.6 * P))
    person(A, lerp(300, 760, q), GROUND - 260 * q, 300, dir=1, hat='crown', arm=60, layer='ink')
    if q > 0.9:
        A.d['ink'].polygon([(560, GROUND - 260), (960, GROUND - 260), (900, GROUND - 230), (620, GROUND - 230)], fill=255)

# ================================================================ 第一回 泗水亭长
def art_l_birth(A, cv, t, u):
    A.d['wash'].ellipse((300, 700, 800, 950), fill=180)
    for k in range(6):
        a = t * 0.8 + k * 1.05
        A.d['ink'].line((540 + 160 * math.cos(a), 820 + 60 * math.sin(a), 540 + 220 * math.cos(a + 0.4), 820 + 80 * math.sin(a + 0.4)), fill=200, width=8)
    ground(A, GROUND)
    A.d['mid'].polygon([(560, GROUND), (720, 1150), (980, 1180), (1020, GROUND)], fill=200)
    person(A, 360, GROUND, 220, dir=1, female=True, kneel=True, bow=30, arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('赤龙', 56), 540, 820, t, t - u + P)

def art_l_idler(A, cv, t, u):
    A.d['red'].rectangle((620, 1060, 900, 1100), fill=200)
    A.d['ink'].rectangle((620, 1100, 900, GROUND), outline=255, width=5)
    A.d['ink'].text((690, 1110), '酒', font=font(SERIF, 90, 'Black'), fill=255)
    ground(A, GROUND)
    low_table(A, 260, 540, GROUND - 70)
    for i, x in enumerate((320, 470)):
        person(A, x, GROUND - 70, 120, dir=1 if i == 0 else -1, kneel=True, bow=-5 + 15 * math.sin(t * 3 + i), arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 3 + i)), hat='knot', layer='ink')
    for k in range(3):
        A.d['ink'].polygon([(380 + k * 30, GROUND - 90), (400 + k * 30, GROUND - 90), (396 + k * 30, GROUND - 74), (384 + k * 30, GROUND - 74)], fill=255)

def art_l_lv(A, cv, t, u):
    for k in range(4):
        lantern(A, 220 + k * 220, 900, t, k, size=22)
    ground(A, GROUND)
    person(A, 760, GROUND, 270, dir=-1, hat='knot', arm=lerp(20, 80, ease_out((u - P) / 0.4)), layer='ink')
    person(A, 900, GROUND, 230, dir=-1, female=True, arm=20, layer='mid')
    x = walk_x(120, 460, u, 1.5 * P)
    person(A, x, GROUND, 260, dir=1, hat='knot', ph=t * 5 if u < 1.5 * P else None, arm=60, layer='ink')
    A.flush(cv)
    if u > P:
        stamp(cv, seal('贺钱万', 46), 300, 980, t, t - u + P, rot=-5)

def art_l_convicts(A, cv, t, u):
    for k in range(30):
        q = (t * 1.0 + k / 30) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 8, y + 36), fill=200, width=2)
    ground(A, GROUND)
    for k in range(7):
        gone = k >= 7 - int(clamp(u / (3 * P)) * 5)
        x = 200 + k * 110 + (200 if gone else 0) * ease_out((u - 0.5) / 2)
        person(A, x, GROUND, 170, dir=1, robe=False, ph=t * 5 + k, arm=20, layer='mid' if not gone else 'wash')
        if k < 6 and not gone:
            A.d['ink'].line((x + 20, GROUND - 120, x + 90, GROUND - 120), fill=200, width=3)
    person(A, 100, GROUND, 230, dir=1, hat='knot', ph=t * 5, arm=40, layer='ink')

def art_l_snake(A, cv, t, u):
    A.d['wash'].ellipse((760, 640, 880, 760), fill=255)
    A.d['mid'].polygon([(60, GROUND), (200, 1080), (360, 1140), (500, GROUND)], fill=200)
    A.d['mid'].polygon([(620, GROUND), (780, 1060), (980, 1120), (1020, GROUND)], fill=200)
    ground(A, GROUND)
    cut = ease_out((u - 1.5 * P) / 0.3) if u > 1.5 * P else 0
    snake(A, 420, GROUND - 30, 360, t, cut)
    sw = lerp(160, 60, ease_expo((u - 1.4 * P) / 0.2)) if u > 1.4 * P else 160
    person(A, 300, GROUND, 290, dir=1, hat='knot', arm=sw, sword=sw, layer='ink')
    A.flush(cv)
    if u > 2.2 * P:
        stamp(cv, seal('赤帝子', 50), 800, 980, t, t - u + 2.2 * P, rot=6)

def art_l_peixian(A, cv, t, u):
    city_wall(A, 360, W - 60, 1120, gate_x=700, label='沛县', open_=ease_out((u - P) / 0.5))
    ground(A, GROUND)
    q = ease_out(u / (0.8 * P))
    x, y = lerp(560, 900, q), lerp(1080, 1000, q) - 120 * math.sin(math.pi * q)
    A.d['mid'].polygon([(x - 30, y - 20), (x + 30, y - 20), (x + 30, y + 20), (x - 30, y + 20)], fill=255)
    for k in range(5):
        person(A, 120 + k * 80, GROUND, 180, dir=1, robe=False, arm=150 if k == 0 else 40, layer='ink' if k == 0 else 'mid')

def art_l_sanzhang(A, cv, t, u):
    A.d['mid'].rectangle((300, 820, 780, 1230), fill=200)
    A.d['ink'].rectangle((300, 820, 780, 1230), outline=255, width=6)
    fo = font(BRUSH, 80)
    for i, ln in enumerate(('杀人者死', '伤人及盗', '抵罪')):
        if u > 0.3 + i * P:
            A.d['ink'].text((540 - fo.getlength(ln) / 2, 870 + i * 110), ln, font=fo, fill=255)
    ground(A, GROUND)
    for k in range(6):
        person(A, 120 + k * 170, GROUND, 150, dir=1 if k < 3 else -1, kneel=u > 3 * P, bow=40, arm=60, layer='mid')

def art_l_xianyang(A, cv, t, u):
    palace(A, 540, GROUND, 760, layer='mid')
    ground(A, GROUND)
    for k in range(3):
        x = 200 + k * 60
        person(A, x, GROUND, 180, dir=1, kneel=True, bow=50, arm=80, hat='crown' if k == 0 else 'knot', layer='ink')
    A.d['ink'].rectangle((300, GROUND - 40, 360, GROUND), fill=255)
    A.d['ink'].ellipse((300, GROUND - 60, 360, GROUND - 30), fill=255)
    x = walk_x(1000, 700, u, 2 * P)
    person(A, x, GROUND, 260, dir=-1, hat='knot', arm=60, ph=t * 5 if u < 2 * P else None, layer='ink')

# ================================================================ 第二回 鸿门宴
def art_l_hongmen(A, cv, t, u):
    """8-beat set piece: the banquet → 项庄's sword dance → 樊哙 bursts in → 刘邦 slips out."""
    ph = u / P
    tent(A, 540, GROUND - 10, 980, 720, layer='wash', open_=0.6)
    low_table(A, 160, 460, GROUND - 70)
    low_table(A, 620, 920, GROUND - 70)
    person(A, 820, GROUND - 70, 150, dir=-1, kneel=True, hat='crown', arm=60, layer='ink')
    person(A, 700, GROUND - 70, 130, dir=-1, kneel=True, hat='knot', arm=40, layer='mid')
    lb_x = 260 if ph < 6 else lerp(260, -120, ease_out((u - 6 * P) / (1.5 * P)))
    lb_kneel = ph < 6
    person(A, lb_x, GROUND - (70 if lb_kneel else 0), 150 if lb_kneel else 200, dir=1 if lb_kneel else -1, kneel=lb_kneel,
           hat='knot', arm=60, ph=t * 8 if not lb_kneel else None, robe=lb_kneel, layer='ink')
    person(A, 380, GROUND - 70, 120, dir=1, kneel=True, hat='knot', arm=30, layer='mid')
    if 2 <= ph < 5:
        v = u - 2 * P
        x = 540 + 70 * math.sin(v * 5)
        sw = 90 + 70 * math.sin(v * 9)
        chu_soldier(A, x, GROUND, 230, dir=-1 if math.cos(v * 5) > 0 else 1, arm=sw, sword=sw, layer='ink')
        if 0.5 < ph - 2 < 2.5:
            person(A, 600, GROUND, 220, dir=-1, robe=True, hat='knot', arm=100, sword=100, layer='mid')
    if 4 <= ph < 6:
        v = u - 4 * P
        x = lerp(-80, 440, ease_out(v / 0.4))
        chu_soldier(A, x, GROUND, 270, dir=1, arm=60, ph=t * 10 if v < 0.4 else None, layer='ink')
        A.d['ink'].rectangle((x + 30, GROUND - 200, x + 70, GROUND - 120), outline=255, width=5)
    A.flush(cv)
    if ph >= 2:
        stamp(cv, seal('意在沛公', 44, INK), 840, 900, t, t - u + 2 * P, rot=6)
    if ph >= 6.5:
        stamp(cv, seal('尿遁', 54), 240, 900, t, t - u + 6.5 * P, rot=-6)

def art_l_hanzhong(A, cv, t, u):
    for k, (x, h) in enumerate(((200, 560), (520, 640), (860, 540))):
        A.d['mid'].polygon([(x - 260, GROUND), (x, GROUND - h), (x + 260, GROUND)], fill=200)
    ground(A, GROUND)
    x = lerp(900, 360, ease_out(u / (4 * P)))
    for k in range(5):
        person(A, x + k * 80, GROUND - k * 30, 150, dir=-1, robe=False, ph=t * 4 + k, arm=20, bow=20, layer='ink' if k == 0 else 'mid')
    A.flush(cv)
    stamp(cv, seal('汉王', 60), 540, 940, t, t - u + P)

def art_l_plank(A, cv, t, u):
    A.d['mid'].polygon([(60, 1500), (60, 720), (460, 760), (520, 1500)], fill=255)
    burn = ease_out(u / (1.5 * P))
    y0 = 1100
    A.d['ink'].line((80, y0, 460, y0 - 60), fill=255, width=10)
    if burn > 0:
        flames(A, 270, y0 - 30, 300, 120 * burn, t, n=5, seed=9, smoke=True)
    if u > 2 * P:
        q = ease_out((u - 2 * P) / (2 * P))
        for k in range(5):
            x = lerp(1000, 560, q) - k * 60; y = lerp(1300, 1420, q)
            person(A, x, y, 110, dir=-1, robe=False, hat='helmet', ph=t * 8 + k, spear=True, layer='ink')
        A.flush(cv)
        stamp(cv, seal('陈仓', 54), 860, 1100, t, t - u + 2 * P, rot=5)

def art_l_sanqin(A, cv, t, u):
    pts = []
    for j in range(40):
        a = 2 * math.pi * j / 40
        r = 340 + 30 * math.sin(a * 3 + 1)
        pts.append((540 + r * math.cos(a), 1060 + r * math.sin(a) * 0.7))
    A.d['mid'].polygon(pts, fill=120); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    A.d['ink'].line((300, 1120, 780, 980), fill=200, width=4)
    A.d['ink'].line((420, 860, 620, 1260), fill=200, width=4)
    A.flush(cv)
    for i, (nm, x, y) in enumerate((('雍', 340, 960), ('塞', 720, 920), ('翟', 620, 1180))):
        stamp(cv, seal(nm, 60, INK), x, y, t, t - u)
        if u > (1 + i) * P:
            stamp(cv, seal('汉', 46), x + 40, y + 40, t, t - u + (1 + i) * P, rot=8)

def art_l_pengcheng(A, cv, t, u):
    city_wall(A, 560, W - 60, 1120, gate_x=800, label='彭城')
    ground(A, GROUND)
    for k in range(5):
        x = lerp(1000, 520, ease_out(u / (2 * P))) + k * 90
        rider(A, x, GROUND - (k % 2) * 10, 160, -1, t * 14 + k, layer='ink', spear=True)
    for k in range(6):
        x = lerp(420, -200, ease_out(u / (2.5 * P))) - k * 70
        person(A, x, GROUND, 150, dir=-1, robe=False, ph=t * 12 + k, arm=120, layer='mid')
    A.flush(cv)
    stamp(cv, seal('五十六万溃', 40, INK), 300, 960, t, t - u + 1.5 * P, rot=-5)

def art_l_children(A, cv, t, u):
    for k in range(10):
        x = (k * 120 - t * 700) % (W + 200) - 100
        A.d['wash'].line((x, 1060 + k * 28, x + 180, 1060 + k * 28), fill=255, width=4)
    ground(A, GROUND)
    carriage(A, 540, GROUND, 180, dir=1, wheel=t * 8, ph=t * 12, canopy=True)
    for i in range(2):
        q = ease_out((u - (1 + i) * P) / 0.4)
        if q > 0:
            x = lerp(420, 220 - i * 80, q); y = lerp(GROUND - 140, GROUND, q)
            person(A, x, y, 90, dir=-1, robe=False, fall=-70 * q, arm=100, layer='ink')

def art_l_xingyang(A, cv, t, u):
    city_wall(A, 220, 860, 1100, gate_x=540, label='荥阳', open_=0.6 if u > 2 * P else 0)
    for k in range(6):
        a = math.pi * (k / 5)
        x = 540 - 460 * math.cos(a); y = GROUND + 10
        chu_soldier(A, x, y, 150, dir=1 if x < 540 else -1, spear=True, arm=40, layer='mid')
    if u > 2 * P:
        carriage(A, 540, GROUND, 150, dir=1, horses=False, moving=False, canopy=True, layer='ink')
        A.d['yellow'].chord((420, GROUND - 240, 620, GROUND - 120), 180, 360, fill=255)
    A.flush(cv)
    if u > 2 * P:
        stamp(cv, seal('纪信', 54), 820, 960, t, t - u + 2 * P, rot=6)

# ================================================================ 第三回 楚汉相争
WAR6 = [('还定三秦', 206), ('彭城之败', 205), ('荥阳对峙', 204), ('韩信背水', 204), ('鸿沟议和', 203), ('垓下合围', 202)]
def scene_chess(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    idx = int(k - c[0])
    A = Art(); beat_fx(A, t)
    x0, x1, y0, y1 = 200, 880, 780, 1380
    for i in range(9):
        x = lerp(x0, x1, i / 8)
        A.d['ink'].line((x, y0, x, (y0 + y1) / 2 - 34), fill=200, width=3)
        A.d['ink'].line((x, (y0 + y1) / 2 + 34, x, y1), fill=200, width=3)
    for j in range(10):
        A.d['ink'].line((x0, lerp(y0, y1, j / 9), x1, lerp(y0, y1, j / 9)), fill=200, width=3)
    A.d['wash'].rectangle((x0, (y0 + y1) / 2 - 34, x1, (y0 + y1) / 2 + 34), fill=200)
    A.flush(cv)
    paste(cv, text_img('楚 河', SERIF, 50, INK, 'Black', bleed=False, spacing=20), 380, (y0 + y1) / 2, 1, 1)
    paste(cv, text_img('汉 界', SERIF, 50, LACQ, 'Black', bleed=False, spacing=20), 700, (y0 + y1) / 2, 1, 1)
    adv = 0 if idx < 0 else min(6, idx + 1) if not gather else 6
    for i in range(5):
        col_ = i * 2
        x = lerp(x0, x1, col_ / 8)
        row = 6 - (adv if i == 2 else min(adv, 3) if i % 2 == 0 else max(0, adv - 2))
        row = max(1, row)
        y = lerp(y0, y1, row / 9)
        stamp(cv, seal('汉', 34), x, y, t, s0, rot=0)
    for i in range(5):
        x = lerp(x0, x1, (i * 2) / 8)
        alive = not (gather and i != 2) and not (adv >= 4 + (i % 3))
        if alive:
            stamp(cv, seal('楚', 34, INK), x, lerp(y0, y1, 3 / 9), t, s0)
    if 0 <= idx < 6 and not gather:
        nm, yr = WAR6[idx]
        ink_in(cv, text_img(f'公元前{cn_num(yr)}年 · {nm}', SERIF, 50, LACQ, 'Black', bleed=False, spacing=4), W / 2, 1470, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '楚汉相争', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '四年鏖战', BRUSH, 160, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '将死霸王', BRUSH, 130, LACQ, W / 2, 1470, t, bt(c[0] + 7), stagger=0.07, seed=111)
    fx.flush(cv)

def art_l_beishui(A, cv, t, u):
    A.d['wash'].rectangle((60, 1290, W - 60, 1380), fill=170)
    waves(A, 1300, t, rows=2, amp=5, speed=2)
    ground(A, 1280)
    for k in range(6):
        person(A, 160 + k * 90, 1280, 170, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.d['mid'].rectangle((700, 960, 940, 1280), fill=200)
    q = ease_out((u - P) / 0.5)
    for k in range(4):
        flag(A, 720 + k * 60, lerp(1040, 960, q), 160 * q, t + k, w=50)
    A.flush(cv)
    stamp(cv, seal('韩信', 54), 300, 960, t, t - u + 0.3)

def art_l_honggou(A, cv, t, u):
    A.d['wash'].polygon([(480, 700), (600, 700), (640, GROUND + 20), (440, GROUND + 20)], fill=180)
    waves(A, 1200, t, rows=2, amp=4, speed=1.5, x0=440, x1=640)
    ground(A, GROUND)
    chu_soldier(A, 300, GROUND, 260, dir=1, arm=60, layer='ink')
    person(A, 780, GROUND, 260, dir=-1, hat='knot', arm=60, layer='ink')
    p = ease_out((u - P) / 0.4)
    if p > 0:
        person(A, lerp(380, 620, p), GROUND, 160, dir=1, female=True, ph=t * 5, arm=20, layer='mid')
        person(A, lerp(330, 570, p), GROUND, 180, dir=1, hat='knot', ph=t * 5, arm=20, layer='mid')
    A.flush(cv)
    stamp(cv, seal('鸿沟', 56), 540, 900, t, t - u + 0.3)

def art_l_gaixia(A, cv, t, u):
    """6-beat: the camp ringed by Han lanterns → songs of Chu on every side → farewell → 乌江."""
    ph = u / P
    A.d['wash'].ellipse((760, 660, 880, 780), fill=255)
    ground(A, GROUND)
    if ph < 4:
        tent(A, 540, GROUND - 10, 360, 320, layer='mid')
        n = int(clamp(u / (2 * P)) * 14)
        for k in range(n):
            a = math.pi * (k / 13)
            x = 540 - 460 * math.cos(a); y = GROUND - 10 - 120 * math.sin(a)
            A.d['red'].ellipse((x - 10, y - 14, x + 10, y + 14), fill=255)
        if ph >= 2:
            chu_soldier(A, 470, GROUND, 230, dir=1, arm=40, bow=20, layer='ink')
            person(A, 620, GROUND, 210, dir=-1, female=True, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
            A.d['ink'].line((680, GROUND - 160, 720, GROUND - 260), fill=255, width=3)
        A.flush(cv)
        if ph >= 1:
            for i, x in enumerate((140, 940)):
                ink_in(cv, text_img('楚歌', BRUSH, 70, LACQ, vertical=True), x, 960, t, t - u + (1 + i * 0.4) * P, dur=0.3, settle=1.1)
    else:
        v = u - 4 * P
        A.d['wash'].rectangle((60, 1250, W - 60, 1380), fill=170)
        waves(A, 1260, t, rows=3, amp=6, speed=1.5)
        horse(A, 360, 1250, 220, 1, 0.3, layer='mid', moving=False)
        chu_soldier(A, 620, 1250, 250, dir=-1, arm=lerp(40, 150, ease_out(v / 0.4)), sword=lerp(40, 150, ease_out(v / 0.4)), layer='ink')
        A.flush(cv)
        stamp(cv, seal('乌江', 60, INK), 860, 960, t, t - u + 4.5 * P, rot=6)

def art_l_dingtao(A, cv, t, u):
    A.d['ink'].polygon([(240, GROUND), (840, GROUND), (760, 1180), (320, 1180)], fill=255)
    for k in range(5):
        A.d['wash'].line((300 + k * 16, GROUND - k * 30, 780 - k * 16, GROUND - k * 30), fill=0, width=3)
    person(A, 540, 1180, 240, dir=1, hat='crown', arm=lerp(20, 60, ease_out(u / P)), layer='ink')
    for k in range(4):
        for side in (-1, 1):
            person(A, 540 + side * (380 + k * 40), GROUND, 120, dir=-side, kneel=True, bow=50, arm=60, layer='mid')

# ================================================================ 第四回 大汉开国
def art_l_changan(A, cv, t, u):
    q = ease_out(u / (3 * P))
    city_wall(A, 60, W - 60, lerp(GROUND - 180, 1080, q), gate_x=540, label='长安' if q > 0.6 else None, open_=1.0)
    for k in range(4):
        x = (t * 80 + k * 300) % (W + 200) - 100
        person(A, x, GROUND, 140, dir=1, robe=False, load=True, ph=t * 6 + k, arm=160, layer='mid')

SANJIE = [('萧何', '镇国家 抚百姓'), ('张良', '运筹帷幄之中'), ('韩信', '战必胜 攻必取')]
def art_l_sanjie(A, cv, t, u):
    ground(A, GROUND)
    for i, (nm, _) in enumerate(SANJIE):
        x = 240 + i * 300
        p = ease_out((u - i * P) / 0.4)
        if p > 0:
            hat = 'helmet' if i == 2 else 'knot'
            person(A, x, lerp(GROUND + 300, GROUND, p), 260, dir=1, robe=i != 2, hat=hat, arm=40 if i != 1 else 100, layer='ink')
    A.flush(cv)
    for i, (nm, tx) in enumerate(SANJIE):
        x = 240 + i * 300
        if u > i * P + 0.3:
            stamp(cv, seal(nm, 46), x, 1000, t, t - u + i * P + 0.3)
            paste(cv, text_img(tx, SERIF, 30, INK, 'Bold', bleed=False, vertical=True), x + 110, 1100, 1, clamp((u - i * P - 0.4) / 0.3))

def art_l_reward(A, cv, t, u):
    low_table(A, 380, 700, 1250)
    person(A, 540, 1250, 200, dir=1, hat='crown', arm=lerp(30, 120, ease_out((u - 0.3) / 0.4)), layer='ink')
    n = int(clamp(u / (2.5 * P)) * 8)
    for k in range(n):
        x = 160 + k * 100
        person(A, x, GROUND, 150, dir=1 if x < 540 else -1, kneel=True, bow=45, arm=60, layer='mid')
    A.flush(cv)
    stamp(cv, seal('雍齿封侯', 44), 860, 960, t, t - u + 2 * P, rot=5)

def art_l_baideng(A, cv, t, u):
    for k in range(34):
        q = (t * 0.3 + k / 34) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    A.d['mid'].polygon([(380, GROUND), (540, 1060), (700, GROUND)], fill=220)
    person(A, 540, 1100, 120, dir=1, hat='crown', arm=20, layer='ink')
    for k in range(10):
        a = t * 0.8 + k * 2 * math.pi / 10
        x = 540 + 440 * math.cos(a); y = GROUND - 20 + 60 * math.sin(a)
        rider(A, x, y, 100, -1 if math.sin(a) > 0 else 1, t * 12 + k, layer='ink' if math.sin(a) > 0 else 'mid')
    A.flush(cv)
    stamp(cv, seal('七日', 56, INK), 860, 920, t, t - u + P)

def art_l_heqin(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(100, 700, ease_out(u / (4 * P)))
    carriage(A, x, GROUND, 160, dir=1, wheel=t * 4, ph=t * 8, canopy=True)
    for k in range(4):
        camel_x = x - 260 - k * 120
        from render_wudi import camel
        camel(A, camel_x, GROUND, 110, 1, t * 5 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('和亲', 56), 860, 960, t, t - u + P)

def art_l_hanxin(A, cv, t, u):
    A.d['wash'].ellipse((760, 660, 880, 780), fill=255)
    for k in range(4):
        x = 160 + k * 240
        A.d['mid'].rectangle((x, 880, x + 40, GROUND), fill=255)
    A.d['ink'].rectangle((60, 860, W - 60, 890), fill=255)
    for k in range(3):
        lantern(A, 300 + k * 240, 920, t, k, size=20)
    ground(A, GROUND)
    person(A, 760, GROUND, 250, dir=-1, female=True, hat='crown', arm=lerp(30, 110, ease_out((u - P) / 0.3)), layer='ink')
    fall = -80 * ease_out((u - 2 * P) / 0.4) if u > 2 * P else 0
    chu_soldier(A, 360, GROUND, 260, dir=1, arm=30, fall=fall, layer='ink')
    A.flush(cv)
    stamp(cv, seal('长乐钟室', 44, INK), 300, 940, t, t - u + 2.2 * P, rot=-5)

def art_l_dafeng(A, cv, t, u):
    for k in range(8):
        y = 760 + k * 50
        x = (t * 500 + k * 170) % (W + 400) - 200
        A.d['wash'].line((x, y, x + 260, y - 20), fill=255, width=6)
    ground(A, GROUND)
    person(A, 540, GROUND, 300, dir=1, hat='crown', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.d['ink'].line((600, GROUND - 260, 640, GROUND - 340), fill=255, width=4)
    for k in range(6):
        person(A, 120 + k * 60 if k < 3 else 780 + (k - 3) * 70, GROUND, 140, dir=1 if k < 3 else -1, robe=False, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='mid')
    A.flush(cv)
    type_in(cv, text_img('大风起兮云飞扬', BRUSH, 70, LACQ), W / 2, 820, t, t - u + P, 0.6)

def art_l_wound(A, cv, t, u):
    ground(A, GROUND)
    rider(A, 380, GROUND, 230, 1, t * 6, layer='ink')
    q = clamp(u / 0.4)
    arrow(A, lerp(980, 420, q), lerp(1000, GROUND - 230, q), math.pi + 0.15, 90)
    if q >= 1:
        A.d['red'].ellipse((400, GROUND - 250, 440, GROUND - 210), fill=255)
    for k in range(4):
        rider(A, 760 + k * 70, GROUND - k * 8, 110, -1, t * 10 + k, layer='mid', spear=True)
    A.flush(cv)
    stamp(cv, seal('英布', 50, INK), 860, 960, t, t - u + 0.3)

# ================================================================ 第五回 大风起兮
def art_l_refuse(A, cv, t, u):
    for k in range(4):
        A.d['mid'].line((620 + k * 80, 780, 620 + k * 80, 1020), fill=255, width=4)
        A.d['mid'].line((600, 800 + k * 70, 900, 800 + k * 70), fill=255, width=4)
    ground(A, GROUND)
    A.d['mid'].rectangle((200, 1250, 640, 1290), fill=255)
    person(A, 420, 1250, 180, dir=1, hat='crown', kneel=True, bow=-20, arm=lerp(30, 120, ease_out((u - P) / 0.3)), layer='ink')
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='knot', bow=30, arm=80, layer='ink')
    A.flush(cv)
    stamp(cv, seal('命乃在天', 44), 300, 940, t, t - u + 1.5 * P, rot=-5)

def art_l_changle(A, cv, t, u):
    palace(A, 540, GROUND, 760, layer='mid')
    for k in range(50):
        q = (t * 1.0 + k / 50) % 1
        x = 80 + (k * 19) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 8, y + 40), fill=200, width=2)
    lt = clamp(1 - (u - 1.5 * P) / 0.6)
    A.d['wash'].rectangle((470, 1180, 610, 1280), fill=0)
    if lt > 0:
        A.d['yellow'].rectangle((470, 1180, 610, 1280), fill=int(160 * lt))

def art_l_changling(A, cv, t, u):
    A.d['mid'].polygon([(180, GROUND), (420, 1020), (660, 1020), (900, GROUND)], fill=230)
    A.d['ink'].polygon([(180, GROUND), (420, 1020), (660, 1020), (900, GROUND)], outline=255, width=5)
    for k in range(2):
        x = 120 + k * 840
        A.d['ink'].rectangle((x - 30, 1100, x + 30, GROUND), fill=255)
        A.d['ink'].polygon([(x - 50, 1100), (x + 50, 1100), (x, 1060)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('长陵', 60), 540, 960, t, t - u + P)

def art_l_lvhou(A, cv, t, u):
    throne_x = 540
    A.d['ink'].polygon([(300, GROUND), (780, GROUND), (720, 1200), (360, 1200)], fill=255)
    person(A, 540, 1200, 170, dir=1, hat='crown', arm=20, layer='mid')
    for k in range(12):
        x = 680 + k * 16
        A.d['mid'].line((x, 860, x + 4 * math.sin(t * 2 + k), 1190), fill=255, width=3)
    person(A, 760, 1200, 220, dir=-1, female=True, hat='crown', arm=60, layer='ink')
    for k in range(4):
        person(A, 120 + k * 70, GROUND, 140, dir=1, kneel=True, bow=45, arm=60, layer='mid')
    A.flush(cv)
    stamp(cv, seal('吕后', 56, INK), 860, 920, t, t - u + P, rot=6)

def art_l_hanzu(A, cv, t, u):
    sun(cv, 540, 1050, 260, LACQ, 130)
    fo = font(BRUSH, 520)
    p = ease_out(u / (1.5 * P))
    tmp = Image.new('L', (W, H), 0)
    ImageDraw.Draw(tmp).text((540 - fo.getlength('汉') / 2, 760), '汉', font=fo, fill=255)
    fld = G.transition_field()
    a = np.asarray(tmp, np.float32) * np.clip((p * 1.3 - fld) / 0.08, 0, 1)
    m = Image.fromarray(a.astype(np.uint8))
    A.im['ink'].paste(m, (0, 0), m)
    ground(A, GROUND)
    for k in range(6):
        person(A, 140 + k * 160, GROUND, 150 + (k % 2) * 20, dir=1 if k < 3 else -1, arm=40, female=k % 2 == 1, layer='mid')

def art_l_400(A, cv, t, u):
    n = int(clamp(u / (3 * P)) * 400)
    for k in range(min(n, 400)):
        x = 140 + (k % 25) * 32; y = 800 + (k // 25) * 32
        A.d['red' if k < 210 else 'ink'].rectangle((x, y, x + 24, y + 24), fill=255)
    A.flush(cv)
    paste(cv, text_img(f'{n}年', SERIF, 80, LACQ, 'Black', bleed=False), W / 2, 1400, 1, 1)
    if u > 3 * P:
        paste(cv, text_img('西汉 · 东汉', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), W / 2, 1480, 1, 1)

# ================================================================ script
CHAPTERS = {16: ('第一回', '泗水亭长'), 48: ('第二回', '鸿门脱险'), 80: ('第三回', '楚汉相争'),
            112: ('第四回', '大汉开国'), 144: ('第五回', '大风起兮')}

CARDS = [
    C(0, 2, 'hook', 'num', num='四十八岁', line='才起兵造反', art=art_l_hook_old),
    C(2, 4, 'hook', 'num', num='泗水亭长', line='一个基层小吏', art=art_l_hook_tingzhang),
    C(4, 6, 'hook', 'num', num='七年', line='得天下', art=art_l_hook_seven),
    C(6, 8, 'hook', 'num', num='第一位', line='平民出身的皇帝', art=art_l_hook_commoner),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 泗水亭长
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'night', 'card', year=256, main='丰邑中阳里', sub='农家之子 · 排行第三', note='其母梦与神遇 是时雷电晦冥', art=art_l_birth),
    C(22, 26, 'life', 'card', year=230, main='游手好闲', sub='不事生产 · 好酒及色', note='常从王媪武负贳酒', art=art_l_idler),
    C(26, 30, 'court', 'card', year=216, main='吕公嫁女', sub='空手赴宴 · 谎称贺钱一万', note='吕公一见 大惊 引入坐', art=art_l_lv),
    C(30, 34, 'night', 'card', year=209, main='押送刑徒', sub='役徒沿途逃亡 · 索性全部放走', note='公等皆去 吾亦从此逝矣', art=art_l_convicts),
    C(34, 38, 'night', 'card', year=209, main='斩白蛇', sub='芒砀山中 · 醉斩拦路白蛇', note='吾子 白帝子也 今为赤帝子斩之', art=art_l_snake),
    C(38, 42, 'war', 'card', year=209, main='沛县起兵', sub='父老杀县令 · 迎为沛公', note='书帛射城上', art=art_l_peixian),
    C(42, 46, 'empire', 'card', year=206, main='先入咸阳', sub='秦王子婴 · 素车白马出降', note='系颈以组 封皇帝玺符节', art=art_l_xianyang),
    C(46, 48, 'court', 'card', year=206, main='约法三章', sub='秦民大喜', art=art_l_sanzhang),
    # ---- 第二回 鸿门脱险
    C(48, 50, 'night', 'chapter'),
    C(50, 58, 'night', 'card', year=206, main='鸿门宴', sub='项庄舞剑 · 樊哙闯帐 · 借如厕脱身', note='项庄舞剑 意在沛公', art=art_l_hongmen),
    C(58, 62, 'works', 'card', year=206, main='封汉中王', sub='被逐入巴蜀汉中', note='汉 自此为名', art=art_l_hanzhong),
    C(62, 66, 'works', 'card', year=206, main='暗度陈仓', sub='烧绝栈道 · 示无东意', note='明修栈道 暗度陈仓', art=art_l_plank),
    C(66, 70, 'war', 'card', year=206, main='还定三秦', sub='雍 塞 翟 · 三王相继败降', note='关中尽归于汉', art=art_l_sanqin),
    C(70, 74, 'war', 'card', year=205, main='彭城大败', sub='五十六万大军 · 被三万楚骑击溃', note='睢水为之不流', art=art_l_pengcheng),
    C(74, 78, 'death', 'card', year=205, main='推子下车', sub='逃亡途中 · 三次推儿女下车', note='夏侯婴每收载之', art=art_l_children),
    C(78, 80, 'night', 'card', year=204, main='纪信替死', sub='乘王车出东门诈降', art=art_l_xingyang),
    # ---- 第三回 楚汉相争
    C(80, 82, 'works', 'chapter'),
    C(82, 90, 'works', 'chess'),
    C(90, 94, 'war', 'card', year=204, main='背水一战', sub='韩信破赵 · 拔赵旗立汉旗', note='陷之死地而后生', art=art_l_beishui),
    C(94, 98, 'works', 'card', year=203, main='鸿沟议和', sub='中分天下 · 太公吕后获释', note='楚河汉界 由此而来', art=art_l_honggou),
    C(98, 104, 'fate', 'card', year=202, main='四面楚歌', sub='垓下被围 · 霸王别姬 · 乌江自刎', note='力拔山兮气盖世 时不利兮骓不逝', art=art_l_gaixia),
    C(104, 112, 'empire', 'card', year=202, main='定陶称帝', sub='汜水之阳 · 即皇帝位', seal='汉', note='四十八岁起兵 五十五岁称帝', art=art_l_dingtao),
    # ---- 第四回 大汉开国
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'works', 'card', year=200, main='定都长安', sub='娄敬献策 · 建都关中', note='长治久安 由此得名', art=art_l_changan),
    C(118, 126, 'court', 'card', year=202, main='汉初三杰', sub='吾能用之 · 此吾所以取天下也', note='夫运筹帷幄之中 决胜千里之外 吾不如子房', art=art_l_sanjie),
    C(126, 130, 'court', 'card', year=201, main='论功行赏', sub='先封最恨之人雍齿 · 群臣安心', note='雍齿且侯 我属无患矣', art=art_l_reward),
    C(130, 134, 'night', 'card', year=200, main='白登之围', sub='被匈奴四十万骑围困七日', note='用陈平奇计 乃得出', art=art_l_baideng),
    C(134, 138, 'works', 'card', year=198, main='和亲匈奴', sub='以宗室女嫁单于 · 换取和平', note='岁奉絮缯酒食', art=art_l_heqin),
    C(138, 142, 'death', 'card', year=196, main='诛杀韩信', sub='吕后设计 · 长乐宫钟室', note='狡兔死 良狗烹', art=art_l_hanxin),
    C(142, 144, 'war', 'card', year=196, main='亲征英布', sub='为流矢所中', art=art_l_wound),
    # ---- 第五回 大风起兮
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'empire', 'card', year=196, main='还乡沛县', sub='击筑高歌 · 慷慨伤怀', note='大风起兮云飞扬 威加海内兮归故乡', art=art_l_dafeng),
    C(150, 154, 'fate', 'card', year=195, main='拒医', sub='吾以布衣提三尺剑取天下', note='命乃在天 虽扁鹊何益', art=art_l_refuse),
    C(154, 158, 'death', 'card', year=195, main='崩于长乐宫', sub='享年六十二岁', note='四月甲辰 崩于长乐宫', art=art_l_changle),
    C(158, 162, 'death', 'card', year=195, main='葬于长陵', sub='谥号高皇帝', note='长陵 汉家第一陵', art=art_l_changling),
    C(162, 166, 'court', 'card', year=195, main='吕后临朝', sub='他身后 · 大汉风云再起', note='诸吕用事', art=art_l_lvhou),
    C(166, 170, 'end', 'card', year=195, main='汉家天下', sub='汉人 汉字 汉族 · 由此得名', note='两汉 四百余年', art=art_l_hanzu),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z, St, M, K, Y, Q, Gh):
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
for mod in (G, L, Wd, Tz, Z, St, M, K, Y, Q, Gh):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元前' + cn_num(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=LACQ + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, S.art_emperor)
    fx = Art()
    ink_in(cv, text_img('刘 邦 · 字季', SERIF, 46, LACQ, 'Bold', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '汉高祖', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('汉', 80), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('前256 — 前195', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '流氓皇帝？', BRUSH, 120, INK, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '知人善任？', BRUSH, 120, LACQ, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    wadang(A, 540, 640, 260, clamp(u / 0.6), layer='mid')
    A.flush(cv, alpha=clamp(u / 0.6) * 0.3)
    fx = Art()
    chars_in(cv, fx, '布衣天子', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('高皇帝', 54), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('他打不过项羽 · 谋不过张良', SERIF, 46, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.4)
    type_in(cv, text_img('却赢下了整个天下', SERIF, 54, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '他靠的是什么', BRUSH, 100, LACQ, W / 2, 1190, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('评论区说出你的答案', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=LACQ + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(252, 240, 226, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=INK + (220,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 魏武帝曹操', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, chess=scene_chess, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第拾壹集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 570, 170, 1, 1)
    if t < bt(8):
        q = text_img('一个小混混 · 凭什么打败项羽？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 300, 335, W / 2 + 300, 335), fill=LACQ + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, LACQ, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((BORN - yr) / (BORN - DIED))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=LACQ + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=INK + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'前{BORN}', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'前{DIED}'), 102), f'前{DIED}', font=f, fill=INK + (170,))
        lab = cn_num(int(round(BORN - yr + 1))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=LACQ + (255,))
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
