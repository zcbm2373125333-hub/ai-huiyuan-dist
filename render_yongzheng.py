# 千古人物志 · 第捌集 · 雍正胤禛 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈，墨色最后绘制）。每一幕画面均为本集新画，不重复。
# 本集特色：朱批 —— 胭脂远山 · 奏折朱批章回卡 · 折子边角 · 八拍「正大光明」 · 八拍「朱批万言」
#          · 朱批长卷改革回顾 · 八拍「圆明园之夜」死因之谜
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_kangxi as K           # engine + helpers (also sorts ink layers last)
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
from render_mingtaizu import cn_year, buffalo
from render_kangxi import qing_hat, official, throne, rect, lantern

F.RIPPLE = False

BORN, DIED = 1678, 1735
END_BEAT = 170
YANZHI = (150, 70, 80)              # 胭脂
GOLDC = (190, 140, 50)

# ================================================================ episode look
WM = dict(hook='雍', life='禛', court='继', night='夜', war='戰', empire='正', works='改', fate='勤', death='谜', end='雍')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire', 'works', 'fate'):
    G.THEMES[k]['part'] = 'rouge'
for k in ('night', 'death', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (ZHU, 250, (W * 0.5, 820))
G.THEMES['works']['sun'] = (YANZHI, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (ZHU, 210, (W * 0.5, 720))
G.THEMES['hook']['tint'] = (1.02, 0.98, 0.97)
G.base_bg.cache_clear()

MTN_COL = {'night': (56, 52, 62), 'death': (64, 60, 62), 'war': (96, 58, 52)}
def draw_background(t, theme):
    """胭脂: distant ranges in rouge-grey washes."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], SERIF if th['wm'] == '禛' else WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 168, 168), (158, 120, 124), MTN_COL.get(theme, (116, 82, 88))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'rouge':
        return K.particle_sprite(kind, q)
    s = 40
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [(200, 70, 60), (170, 40, 40), (220, 120, 110)][q]
    d.polygon([(10, 22), (20, 12), (30, 18), (26, 28), (14, 30)], fill=col + (210,))
    return im.filter(ImageFilter.GaussianBlur(0.8))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """奏折 fold corners: zigzag accordion edges with a vermilion 朱批 tick."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        pts = [(x + sx * i * 18, y + sy * (0 if i % 2 == 0 else 10)) for i in range(9)]
        d.line(pts, fill=INK + (170,), width=3)
        pts = [(x + sx * (0 if i % 2 == 0 else 10), y + sy * i * 18) for i in range(9)]
        d.line(pts, fill=INK + (170,), width=3)
        d.line((x + sx * 30, y + sy * 34, x + sx * 44, y + sy * 48, x + sx * 70, y + sy * 22), fill=ZHU + (230,), width=5)
G.draw_frame_border = draw_frame_border

# ================================================================ 奏折朱批 chapter card
def memorial(A, x0, y0, pw, h, n, p, layer='mid'):
    """Accordion memorial (奏折) unfolding left→right; returns its right edge."""
    k = int(n * ease_out(p)) + (1 if p > 0 else 0)
    for i in range(min(n, k)):
        x = x0 + i * pw
        A.d[layer].rectangle((x, y0, x + pw, y0 + h), fill=150 if i % 2 else 200)
        A.d['ink'].line((x, y0, x, y0 + h), fill=160, width=2)
    if k:
        A.d['ink'].rectangle((x0, y0, x0 + min(n, k) * pw, y0 + h), outline=255, width=4)
    return x0 + min(n, k) * pw

CH_CHAR = {16: '闲', 48: '继', 80: '改', 112: '严', 144: '勤'}
def art_memorial_chapter(A, cv, t, u):
    memorial(A, 240, 640, 75, 540, 8, u / 0.5)
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_memorial_chapter)
    ch = CH_CHAR.get(c[0], '批')
    ink_in(cv, text_img(ch, BRUSH, 360, ZHU), 540, 900, t, s0 + 0.35, dur=0.35, settle=1.2)
    ink_in(cv, text_img(no, SERIF, 56, ZHU, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ small primitives
def bamboo(A, x, top, t, layer='mid'):
    sw = 8 * math.sin(t * 1.3 + x)
    A.d[layer].line((x, GROUND, x + sw, top), fill=255, width=9)
    for j in range(int((GROUND - top) / 90)):
        yy = GROUND - j * 90
        A.d['ink'].line((x - 7 + sw * (GROUND - yy) / (GROUND - top), yy, x + 7 + sw * (GROUND - yy) / (GROUND - top), yy), fill=200, width=3)
    for j in range(4):
        yy = top + j * 50
        A.d[layer].polygon([(x + sw, yy), (x + sw + 70, yy + 10), (x + sw + 10, yy + 20)], fill=255)

def ingot(A, x, y, s, layer='mid'):
    A.d[layer].polygon([(x - s, y - s * 0.5), (x - s * 0.5, y), (x + s * 0.5, y), (x + s, y - s * 0.5), (x + s * 0.4, y - s * 0.2), (x - s * 0.4, y - s * 0.2)], fill=255)
    A.d[layer].ellipse((x - s * 0.3, y - s * 0.55, x + s * 0.3, y - s * 0.1), fill=255)

def chest(A, x, base, w, h, fill_=0.0, lid=1.0):
    A.d['ink'].rectangle((x - w / 2, base - h, x + w / 2, base), outline=255, width=6)
    A.d['ink'].line((x - w / 2, base - h * 0.5, x + w / 2, base - h * 0.5), fill=200, width=3)
    if fill_ > 0:
        for k in range(int(fill_ * 6)):
            ingot(A, x - w / 2 + 40 + (k % 3) * (w - 80) / 2, base - 20 - (k // 3) * 40, 26, layer='gold')
    A.d['ink'].polygon([(x - w / 2, base - h), (x + w / 2, base - h), (x + w / 2 - 20 * lid, base - h - 60 * lid), (x - w / 2 - 20 * lid, base - h - 60 * lid)], fill=255)

# ================================================================ hooks
def art_y_hook_45(A, cv, t, u):
    throne(A, 760, GROUND, 1.3)
    person(A, 760, GROUND - 90, 170, dir=-1, hat='crown', arm=30, layer='ink')
    p = ease_out(u / (1.8 * P))
    for k in range(int(14 * p)):
        x = 100 + k * 42; y = GROUND - 10 - (k % 2) * 14
        A.d['mid'].ellipse((x - 10, y - 6, x + 10, y + 6), fill=255)
    person(A, lerp(80, 560, p), GROUND, 200, dir=1, robe=True, hat='none', ph=t * 6, arm=20, layer='mid')

def art_y_hook_13(A, cv, t, u):
    cx, cy = 540, 1080
    A.d['ink'].rectangle((cx - 170, cy - 300, cx + 170, cy - 270), fill=255)
    A.d['ink'].rectangle((cx - 170, cy + 270, cx + 170, cy + 300), fill=255)
    A.d['ink'].polygon([(cx - 140, cy - 270), (cx + 140, cy - 270), (cx + 14, cy), (cx + 140, cy + 270), (cx - 140, cy + 270), (cx - 14, cy)], outline=255, width=5)
    q = clamp(u / (1.8 * P))
    top = lerp(cy - 240, cy - 10, q)
    w = 120 * (cy - top) / 240
    A.d['gold'].polygon([(cx - w, top), (cx + w, top), (cx, cy)], fill=255)
    A.d['gold'].line((cx, cy, cx, cy + 270), fill=255, width=4)
    A.d['gold'].chord((cx - 120 * q, cy + 270 - 120 * q, cx + 120 * q, cy + 270 + 40 * q), 180, 360, fill=255)

def art_y_hook_pile(A, cv, t, u):
    for i, x in enumerate((240, 420, 660, 840)):
        n = int(clamp(u / (1.5 * P)) * (14 + i * 3))
        for k in range(n):
            y = GROUND - 14 - k * 24
            A.d['mid' if k % 2 else 'wash'].rectangle((x - 70, y - 22, x + 70, y), fill=255)
            A.d['ink'].rectangle((x - 70, y - 22, x + 70, y), outline=200, width=2)
    q = ease_out((u - 0.6) / 0.4)
    if q > 0:
        A.d['red'].line((140, 1300, lerp(140, 940, q), lerp(1300, 820, q)), fill=255, width=24)

def art_y_hook_mystery(A, cv, t, u):
    A.d['wash'].ellipse((760, 660, 880, 780), fill=255)
    palace(A, 540, GROUND, 640, layer='mid')
    A.d['yellow'].rectangle((470, 1180, 610, 1260), fill=200)
    q = ease_out(u / (1.6 * P))
    pts = [(540 + 60 * math.sin(f * 7 + t * 2) * f, 1170 - 360 * f * q) for f in np.linspace(0, 1, 30)]
    A.d['wash'].line(pts, fill=255, width=16)
    if q > 0.8:
        A.flush(cv)
        ink_in(cv, text_img('？', BRUSH, 220, INK), 560, 800, t, t - u + 1.6 * P, dur=0.3, settle=1.1)

# ================================================================ 第一回 天下闲人
def art_y_cradle(A, cv, t, u):
    for k in range(4):
        A.d['mid'].line((640 + k * 80, 780, 640 + k * 80, 1020), fill=255, width=4)
        A.d['mid'].line((620, 800 + k * 70, 900, 800 + k * 70), fill=255, width=4)
    A.d['wash'].ellipse((700, 830, 800, 930), fill=255)
    ground(A, GROUND)
    a = 0.25 * math.sin(t * 2.4)
    cx, cy = 500, GROUND - 60
    A.d['ink'].chord((cx - 140, cy - 150, cx + 140, cy + 60), 0, 180, fill=255)
    A.d['ink'].arc((cx - 180, GROUND - 60 + 40 * a, cx + 180, GROUND + 20 - 40 * a), 0, 180, fill=255, width=8)
    A.d['red'].rectangle((cx - 50, cy - 60, cx + 50, cy - 10), fill=255)
    person(A, 250, GROUND, 230, dir=1, female=True, kneel=True, bow=15, arm=lerp(60, 90, 0.5 + 0.5 * math.sin(t * 2.4)), layer='ink')

def art_y_tutor(A, cv, t, u):
    A.d['ink'].rectangle((280, 1240, 800, 1270), fill=255)
    for lx in (300, 760): A.d['ink'].rectangle((lx, 1270, lx + 18, GROUND), fill=255)
    A.d['mid'].rectangle((420, 1210, 680, 1238), fill=255)
    fo = font(BRUSH, 40)
    for i, ch in enumerate('天地玄黄'):
        if u > i * 0.5:
            A.d['ink'].text((440 + i * 60, 1150), ch, font=fo, fill=255)
    person(A, 420, GROUND, 170, dir=1, hat='knot', arm=80, layer='ink')
    person(A, 300, GROUND, 270, dir=1, female=True, hat='crown', bow=20, arm=lerp(60, 85, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    ground(A, GROUND)

def art_y_campaign(A, cv, t, u):
    ground(A, GROUND)
    for k in range(18):
        q = (t * 0.3 + k / 18) % 1
        x = 80 + (k * 53) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    for k in range(4):
        x = (t * 160 + k * 300) % (W + 400) - 200
        rider(A, x, 1320, 120, 1, t * 11 + k, layer='mid', spear=True)
        flag(A, x - 40, 1250, 160, t + k, w=60, layer='red')
    lead = lerp(-100, 520, ease_out(u / (2 * P)))
    rider(A, lead, GROUND, 250, 1, t * 11, layer='ink')
    flag(A, lead - 70, GROUND - 260, 300, t, w=120, layer='red')

def art_y_prince_gate(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((260, 1080, 820, GROUND), fill=255)
    A.d['ink'].polygon([(220, 1090), (860, 1090), (760, 980), (320, 980)], fill=255)
    rect(A, 'wash', 470, 1170, 610, GROUND, fill=0)
    A.d['ink'].rectangle((430, 1000, 650, 1060), fill=255)
    A.d['ink'].text((444, 1006), '雍亲王府', font=font(SERIF, 44, 'Black'), fill=0)
    for x in (200, 880):
        A.d['ink'].rectangle((x - 40, GROUND - 40, x + 40, GROUND), fill=255)
        A.d['ink'].ellipse((x - 50, GROUND - 150, x + 50, GROUND - 40), fill=255)
    A.flush(cv)
    stamp(cv, seal('雍', 70), 540, 880, t, t - u + P, rot=-5)

def art_y_idle(A, cv, t, u):
    for x in (100, 170, 940):
        bamboo(A, x, 760, t)
    A.d['wash'].rectangle((420, 1260, W - 60, 1360), fill=170)
    waves(A, 1270, t, rows=2, amp=5, speed=1.2, x0=420)
    ground(A, GROUND)
    person(A, 380, GROUND - 40, 220, dir=1, kneel=True, bow=5, arm=70, hat='none', layer='ink')
    bob = 10 * math.sin(t * 3)
    A.d['ink'].line((470, GROUND - 200, 760, 1060), fill=255, width=4)
    A.d['ink'].line((760, 1060, 760, 1290 + bob), fill=200, width=2)
    A.d['red'].ellipse((752, 1282 + bob, 768, 1298 + bob), fill=255)
    for k in range(10):
        a = k * 0.6 + 2.2
        A.d['ink'].ellipse((330 + 26 * math.cos(a) - 5, GROUND - 120 + 26 * math.sin(a) - 5, 330 + 26 * math.cos(a) + 5, GROUND - 120 + 26 * math.sin(a) + 5), fill=255)
    A.flush(cv)
    stamp(cv, seal('闲', 64), 860, 860, t, t - u + P, rot=6)

def art_y_lamps(A, cv, t, u):
    for i in range(9):
        x = 140 + i * 100
        out = ease_out((u - 0.3 - i * 0.18) / 0.2) if i != 3 else 0
        A.d['ink'].line((x, 760, x, 820), fill=255, width=2)
        if out < 1:
            A.d['red'].ellipse((x - 30, 820, x + 30, 900), fill=int(255 * (1 - out)))
        A.d['ink'].ellipse((x - 30, 820, x + 30, 900), outline=255, width=3)
        if i == 3 and u > 2 * P:
            r = 60 + 10 * math.sin(t * 5)
            A.d['gold'].ellipse((x - r, 860 - r, x + r, 860 + r), outline=200, width=4)
    ground(A, GROUND)
    for i in range(9):
        person(A, 140 + i * 100, GROUND, 150, dir=1, robe=True, hat='crown', arm=20, layer='ink' if i == 3 else 'mid')

def art_y_audit(A, cv, t, u):
    x0, y0 = 300, 920
    A.d['ink'].rectangle((x0, y0, x0 + 480, y0 + 260), outline=255, width=8)
    A.d['ink'].line((x0, y0 + 80, x0 + 480, y0 + 80), fill=255, width=5)
    kk = (t - G.B0) / P
    for c_ in range(9):
        x = x0 + 30 + c_ * 52
        A.d['ink'].line((x, y0, x, y0 + 260), fill=200, width=2)
        up = ((int(kk) + c_) % 3 == 0)
        for b in range(2):
            A.d['mid'].ellipse((x - 18, y0 + 10 + b * 32 + (0 if up else 10), x + 18, y0 + 36 + b * 32 + (0 if up else 10)), fill=255)
        for b in range(5):
            A.d['ink'].ellipse((x - 18, y0 + 100 + b * 30, x + 18, y0 + 124 + b * 30), fill=255)
    official(A, 880, GROUND, 250, dir=-1, arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    ground(A, GROUND)

def art_y_bell(A, cv, t, u):
    A.d['mid'].rectangle((360, 900, 720, GROUND), fill=200)
    A.d['ink'].polygon([(320, 900), (760, 900), (660, 820), (420, 820)], fill=255)
    a = 0.3 * math.sin(t * 3)
    cx, cy = 540, 940
    pts = [(-14, -20), (14, -20), (14, 0), (60, 10), (78, 120), (126, 200), (-126, 200), (-78, 120), (-60, 10), (-14, 0)]
    A.d['ink'].polygon([rotp((cx + p_[0], cy + p_[1]), (cx, cy), a) for p_ in pts], fill=255)
    for k in range(6):
        x = 120 + k * 170 + (0 if k < 3 else 60)
        if 360 < x < 720: continue
        pts = [(x + 14 * math.sin(t * 3 + j * 0.5 + k) * j / 8, 820 + j * 50) for j in range(9)]
        A.d['wash'].line(pts, fill=255, width=14)
    ground(A, GROUND)
    for k in range(4):
        official(A, 140 + k * 70, GROUND, 150, dir=1, kneel=True, bow=55, arm=60, layer='mid')

# ================================================================ 第二回 继位疑云
def art_y_edict(A, cv, t, u):
    ground(A, GROUND)
    official(A, 760, GROUND, 290, dir=-1, arm=100, arm2=100, layer='ink')
    p = ease_out(u / 0.6)
    A.d['yellow'].rectangle((560 - 120 * p, 1060, 600 + 0 * p, 1160), fill=255)
    A.d['ink'].rectangle((550 - 120 * p, 1050, 560 - 120 * p, 1170), fill=255)
    for k in range(5):
        person(A, 120 + k * 90, GROUND, 150, dir=1, hat='crown', kneel=True, bow=45, arm=60, layer='ink' if k == 3 else 'mid')

def art_y_crown(A, cv, t, u):
    A.d['ink'].ellipse((400, 980, 680, 1260), fill=255)
    A.d['ink'].polygon([(240, GROUND), (840, GROUND), (760, 1240), (320, 1240)], fill=255)
    q = ease_expo(u / (1.4 * P))
    y = lerp(640, 1000, q)
    A.d['yellow'].polygon([(370, y), (710, y), (650, y - 110), (430, y - 110)], fill=255)
    A.d['red'].ellipse((520, y - 160, 560, y - 110), fill=255)
    if q > 0.95:
        for k in range(12):
            a = k * math.pi / 6 + t
            A.d['gold'].line((540 + 200 * math.cos(a), 960 + 120 * math.sin(a), 540 + 240 * math.cos(a), 960 + 150 * math.sin(a)), fill=200, width=4)

def art_y_plaque(A, cv, t, u):
    """8-beat set piece 秘密立储: writes the heir's name → seals it in a box → box placed behind 正大光明."""
    ph = u / P
    for k in range(4):
        x = 140 + k * 260
        A.d['mid'].rectangle((x, 900, x + 40, GROUND), fill=255)
    ground(A, GROUND)
    throne(A, 760, GROUND, 1.0)
    A.d['ink'].rectangle((300, 1250, 560, 1280), fill=255)
    for lx in (320, 520): A.d['ink'].rectangle((lx, 1280, lx + 16, GROUND), fill=255)
    person(A, 250, GROUND, 220, dir=1, hat='crown', arm=lerp(70, 100, 0.5 + 0.5 * math.sin(t * 5)) if ph < 2 else 60, layer='ink')
    if ph < 2:
        A.d['mid'].rectangle((360, 1225, 480, 1248), fill=255)
    if 2 <= ph:
        if ph < 4:
            bx, by = 430, 1200
        else:
            q = ease_out((u - 4 * P) / (2 * P))
            bx, by = lerp(430, 540, q), lerp(1200, 840, q) - 120 * math.sin(math.pi * q)
        A.d['yellow'].rectangle((bx - 50, by - 40, bx + 50, by + 40), fill=255)
        A.d['ink'].rectangle((bx - 50, by - 40, bx + 50, by + 40), outline=255, width=4)
    A.d['ink'].rectangle((280, 760, 800, 880), fill=255)
    A.d['ink'].text((300, 772), '正大光明', font=font(SERIF, 96, 'Black'), fill=0)
    if ph >= 6:
        g = ease_out((u - 6 * P) / 0.5)
        for k in range(14):
            a = -math.pi + k * math.pi / 13
            A.d['gold'].line((540 + 280 * math.cos(a), 820 + 100 * math.sin(a), 540 + (280 + 100 * g) * math.cos(a), 820 + (100 + 80 * g) * math.sin(a)), fill=220, width=5)
    if ph >= 2.6 and ph < 4:
        A.flush(cv)
        stamp(cv, seal('封', 44), 430, 1200, t, t - u + 2.6 * P)
    if ph >= 6.5:
        A.flush(cv)
        stamp(cv, seal('秘密立储', 46), 880, 1000, t, t - u + 6.5 * P, rot=6)

def art_y_brothers(A, cv, t, u):
    ground(A, GROUND)
    for i, x in enumerate((330, 750)):
        person(A, x, GROUND, 240, dir=1 if i == 0 else -1, kneel=True, bow=45, arm=70, hat='none', layer='ink')
        A.d['ink'].line((x - 60, GROUND - 60, x + 60, GROUND - 40), fill=200, width=4)
    A.flush(cv)
    d = ImageDraw.Draw(cv)
    for i, (old, new, x) in enumerate((('胤禩', '阿其那', 330), ('胤禟', '塞思黑', 750))):
        im = text_img(old, SERIF, 60, INK, 'Black', bleed=False)
        paste(cv, im, x, 900, 1, 1)
        q = ease_out((u - (1 + i) * P) / 0.25)
        if q > 0:
            d.line((x - 70, 880, x - 70 + 140 * q, 920), fill=ZHU + (240,), width=8)
        if u > (2 + i) * P:
            stamp(cv, seal(new, 40, INK), x, 1030, t, t - u + (2 + i) * P, rot=(i * 2 - 1) * 5)

def art_y_nian(A, cv, t, u):
    A.d['mid'].polygon([(560, 1180), (720, 900), (820, 980), (980, 860), (1080, 1180)], fill=200)
    A.d['wash'].polygon([(700, 940), (720, 900), (760, 930)], fill=0)
    A.d['wash'].ellipse((380, 1170, 980, 1300), fill=170)
    ground(A, GROUND)
    x = lerp(-150, 420, ease_out(u / (2 * P)))
    rider(A, x, GROUND, 270, 1, t * 13, layer='ink', spear=True)
    A.d['ink'].line((x - 80, GROUND - 280, x - 80, GROUND - 600), fill=255, width=6)
    A.d['red'].polygon([(x - 80, GROUND - 600), (x + 40, GROUND - 590 + 8 * math.sin(t * 6)), (x + 40, GROUND - 480), (x - 80, GROUND - 490)], fill=255)
    A.d['red'].text((x - 60, GROUND - 590), '年', font=font(SERIF, 80, 'Black'), fill=0)
    for k in range(4):
        rider(A, lerp(700, 1150, ease_out(u / (3 * P))) + k * 70, 1330 - k * 8, 90, 1, t * 13 + k, layer='mid')

def art_y_fallen(A, cv, t, u):
    A.d['mid'].rectangle((120, 820, 500, 850), fill=255)
    A.d['wash'].line((300, 850, 300 + 10 * math.sin(t), 1100), fill=255, width=14)
    for k in range(6):
        A.d['ink'].line((620 + k * 60, 900, 620 + k * 60, GROUND), fill=255, width=8)
    A.d['ink'].rectangle((600, 880, 940, 900), fill=255)
    person(A, 780, GROUND, 230, dir=-1, kneel=True, bow=40, arm=60, hat='none', layer='mid')
    ground(A, GROUND)
    official(A, 300, GROUND, 230, dir=1, bow=30, arm=20, layer='ink')
    A.flush(cv)
    stamp(cv, seal('九十二条', 44), 300, 980, t, t - u + P, rot=-6)
    stamp(cv, seal('圈禁', 50, INK), 780, 980, t, t - u + 2 * P, rot=6)

# ================================================================ 第三回 雍正改革
def art_y_deficit(A, cv, t, u):
    chest(A, 360, GROUND, 320, 220, fill_=0, lid=1.0)
    for k in range(4):
        A.d['mid'].line((220 + k * 20, GROUND - 210, 260 + k * 30, GROUND - 120), fill=150, width=2)
    official(A, 820, GROUND, 290, dir=-1, arm=lerp(40, 110, ease_out((u - P) / 0.3)), layer='ink')
    for k in range(3):
        official(A, 560 + k * 70, GROUND, 150, dir=1, kneel=True, bow=55, arm=60, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('亏空', 54, ZHU), 360, 900, t, t - u + 0.5)

def art_y_tanding(A, cv, t, u):
    x0, y0 = 560, 1080
    p = clamp(u / (3 * P))
    for r_ in range(4):
        for c_ in range(4):
            i = r_ * 4 + c_
            x = x0 + c_ * 100; y = y0 + r_ * 70
            A.d['ink'].rectangle((x, y, x + 96, y + 66), outline=255, width=3)
            if i < int(p * 16):
                for j in range(4):
                    A.d['gold'].line((x + 14 + j * 22, y + 60, x + 14 + j * 22, y + 20), fill=255, width=4)
    ground(A, GROUND)
    for k in range(6):
        q = ((u * 0.6 + k / 6) % 1)
        x = lerp(80, 540, q)
        person(A, x, GROUND, 130, dir=1, robe=False, ph=t * 7 + k, arm=20, layer='ink' if k % 2 else 'mid')

def art_y_zhupi(A, cv, t, u):
    """8-beat set piece: night after night of vermilion annotations — 「朕就是这样汉子」."""
    ph = u / P
    mx = lerp(900, 160, clamp(u / (8 * P)))
    A.d['wash'].ellipse((mx - 50, 640, mx + 50, 740), fill=255)
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    person(A, 540, GROUND, 230, dir=1, hat='crown', kneel=True, bow=25, arm=lerp(80, 105, 0.5 + 0.5 * math.sin(t * 7)), layer='ink')
    left = int(14 * (1 - clamp(u / (8 * P))))
    for k in range(left):
        A.d['mid'].rectangle((330, 1240 - k * 16, 430, 1254 - k * 16), fill=255)
    for k in range(14 - left):
        A.d['mid'].rectangle((650, 1240 - k * 16, 750, 1254 - k * 16), fill=255)
        A.d['red'].line((660, 1247 - k * 16, 700, 1247 - k * 16), fill=255, width=3)
    ch = clamp(1 - u / (8 * P)) * 120 + 30
    A.d['ink'].rectangle((860, 1250 - ch, 880, 1250), fill=255)
    fh = 30 + 6 * math.sin(t * 15)
    A.d['red'].polygon([(858, 1250 - ch), (882, 1250 - ch), (872, 1250 - ch - fh), (868, 1250 - ch - fh)], fill=255)
    A.flush(cv)
    for i, c_ in enumerate('朕就是这样汉子'):
        st = t - u + (0.5 + i * 0.95) * P
        if t >= st:
            ink_in(cv, text_img(c_, BRUSH, 84, ZHU), 270 + i * 96, 900, t, st, dur=0.25, settle=1.2)
    if ph >= 7.3:
        stamp(cv, seal('朱批千万言', 40), 880, 1060, t, t - u + 7.3 * P, rot=6)

def art_y_huohao(A, cv, t, u):
    A.d['ink'].polygon([(220, 1060), (380, 1060), (360, 1180), (240, 1180)], fill=255)
    flames(A, 300, 1250, 160, 70, t, n=4, seed=7, smoke=False)
    a = 0.6 * ease_out(u / (1.2 * P))
    A.d['ink'].polygon([rotp(p_, (380, 1060), -a) for p_ in ((300, 1040), (390, 1040), (390, 1060), (300, 1060))], fill=255)
    for k in range(5):
        q = ((u * 1.2 + k / 5) % 1)
        A.d['gold'].ellipse((400 + q * 120 - 8, 1070 + q * q * 160 - 8, 400 + q * 120 + 8, 1070 + q * q * 160 + 8), fill=255)
    for k in range(3):
        ingot(A, 560 + k * 110, GROUND - 20, 40, layer='gold')
    chest(A, 870, GROUND, 180, 150, fill_=clamp(u / (2 * P)), lid=0.0)
    A.flush(cv)
    stamp(cv, seal('公', 50), 870, 1100, t, t - u + P)

def art_y_yanglian(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 270, dir=-1, hat='crown', arm=80, layer='ink')
    official(A, 380, GROUND, 230, dir=1, kneel=True, bow=30, arm=90, layer='ink')
    A.d['red'].rectangle((470, GROUND - 170, 640, GROUND - 155), fill=255)
    for k in range(3):
        ingot(A, 500 + k * 50, GROUND - 175, 22, layer='gold')
    A.flush(cv)
    stamp(cv, seal('廉', 70), 380, 960, t, t - u + P)

def art_y_gaitu(A, cv, t, u):
    A.d['mid'].polygon([(60, 1240), (240, 900), (420, 1060), (600, 880), (800, 1080), (1020, 1240)], fill=180)
    for i, x in enumerate((240, 760)):
        A.d['ink'].rectangle((x - 90, 1120, x + 90, 1200), fill=255)
        A.d['ink'].polygon([(x - 110, 1120), (x + 110, 1120), (x, 1050)], fill=255)
        for lx in (x - 70, x, x + 70):
            A.d['ink'].line((lx, 1200, lx, GROUND), fill=255, width=6)
    ground(A, GROUND)
    person(A, 420, GROUND, 220, dir=1, robe=True, hat='none', arm=80, layer='ink')
    for k in range(3):
        A.d['ink'].line((400 + k * 16, GROUND - 230, 390 + k * 20, GROUND - 290), fill=255, width=3)
    official(A, 640, GROUND, 230, dir=-1, arm=80, layer='ink')
    A.d['red'].rectangle((505, GROUND - 150, 545, GROUND - 120), fill=255)
    p = ease_out((u - P) / 0.4)
    flag(A, 900, GROUND, 360 * p, t, w=100, layer='yellow')

REFORMS = [('清查亏空', 1723), ('摊丁入亩', 1723), ('火耗归公', 1724), ('养廉银', 1724), ('改土归流', 1726), ('设军机处', 1729)]
def scene_reform(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    idx = int(k - c[0])
    A = Art(); beat_fx(A, t)
    x0 = 110
    width = 140 * (min(6, max(0, idx + 1)) if not gather else 6) * ease_out((t - bt(c[0] + min(idx, 5))) / 0.3) if not gather else 840
    width = max(width, 140 * max(0, min(idx, 6)))
    A.d['mid'].rectangle((x0, 860, x0 + 20 + width, 1360), fill=170)
    A.d['ink'].rectangle((x0 - 20, 840, x0, 1380), fill=255)
    A.d['ink'].rectangle((x0 + 20 + width, 840, x0 + 40 + width, 1380), fill=255)
    A.flush(cv)
    for i, (nm, yr) in enumerate(REFORMS):
        st = bt(c[0] + i)
        if t < st: continue
        x = x0 + 90 + i * 140
        ink_in(cv, text_img(nm, BRUSH, 70, ZHU, vertical=True), x, 1100, t, st + 0.1, dur=0.3, settle=1.1)
    if 0 <= idx < 6:
        nm, yr = REFORMS[idx]
        ink_in(cv, text_img(f'公元{cn_year(yr)}年 · {nm}', SERIF, 50, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1460, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '雍正新政', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '十三年改革', BRUSH, 150, INK, W / 2, 440, t, gather_t, stagger=0.07, seed=110)
        chars_in(cv, fx, '一扫积弊', BRUSH, 150, ZHU, W / 2, 1460, t, bt(c[0] + 7), stagger=0.08, seed=111)
    fx.flush(cv)

# ================================================================ 第四回 铁腕治国
def art_y_junji(A, cv, t, u):
    A.d['mid'].rectangle((200, 1050, 880, GROUND), fill=170)
    A.d['ink'].polygon([(160, 1060), (920, 1060), (860, 990), (220, 990)], fill=255)
    rect(A, 'wash', 260, 1100, 820, GROUND, fill=0)
    for k in range(3):
        x = 320 + k * 170
        official(A, x, GROUND, 170, dir=1, kneel=True, bow=30, arm=100, layer='ink')
        A.d['mid'].rectangle((x + 40, GROUND - 60, x + 120, GROUND - 40), fill=255)
    person(A, 860, GROUND, 230, dir=-1, hat='crown', arm=50, layer='ink')
    A.flush(cv)
    stamp(cv, seal('军机', 56), 540, 900, t, t - u + P)

def art_y_jianji(A, cv, t, u):
    q = ease_out((u - 0.5) / 0.4)
    for i in range(2):
        cx = 540 + (i * 2 - 1) * (50 + 140 * q)
        A.d['ink'].ellipse((cx - 70, 1000 - 40, cx + 70, 1000 + 40), outline=255, width=12)
    ground(A, GROUND)
    for k in range(4):
        x = walk_x(300 - k * 60, 700 + k * 40, u - 0.8, 2 * P)
        person(A, x, GROUND, 170, dir=1, robe=False, ph=t * 6 + k, arm=110, layer='ink' if k % 2 else 'mid')

def art_y_gentry(A, cv, t, u):
    A.d['ink'].rectangle((420, 1200, 760, 1230), fill=255)
    A.d['ink'].rectangle((440, 1230, 740, GROUND), outline=255, width=5)
    official(A, 840, GROUND, 230, dir=-1, arm=70, layer='ink')
    person(A, 300, GROUND, 250, dir=1, hat='knot', arm=lerp(30, 85, ease_out((u - 0.3) / 0.5)), layer='ink')
    x = lerp(360, 560, ease_out((u - 0.5) / 0.5))
    ingot(A, x, 1195, 30, layer='gold')
    A.flush(cv)
    stamp(cv, seal('一体纳粮', 44), 590, 940, t, t - u + P, rot=5)

BANNER_COLS = [('yellow', None), ('wash', None), ('red', None), ('cobalt', None)]
def art_y_banners(A, cv, t, u):
    ground(A, GROUND)
    for i in range(8):
        x = 140 + (i % 4) * 240; base = GROUND - (i // 4) * 220
        lay = BANNER_COLS[i % 4][0]
        p = ease_out((u - i * 0.1) / 0.3)
        if p <= 0: continue
        A.d['ink'].line((x, base, x, base - 200 * p), fill=255, width=5)
        pts_top = [(x + j * 16, base - 200 * p + 6 * math.sin(t * 5 + j * 0.6 + i)) for j in range(8)]
        pts_bot = [(x + j * 16, base - 200 * p + 100 + 6 * math.sin(t * 5 + j * 0.6 + i)) for j in range(7, -1, -1)]
        A.d[lay].polygon(pts_top + pts_bot, fill=255)
        if i >= 4:
            A.d['red' if lay != 'red' else 'wash'].line(pts_top + pts_bot + [pts_top[0]], fill=255, width=6)

def art_y_purge(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        x = 130 + k * 160
        official(A, x, GROUND, 200, dir=1, bow=20, arm=30, layer='mid') if not (u > (1 + k * 0.3) * P and k % 2 == 0) else \
            person(A, x, GROUND, 200, dir=1, bow=40, arm=30, hat='none', layer='mid')
        if k % 2 == 0 and u > (1 + k * 0.3) * P:
            q = clamp((u - (1 + k * 0.3) * P) / 0.6)
            hx, hy = x + 120 * q, GROUND - 190 - 200 * q + 260 * q * q
            A.d['ink'].polygon([rotp(p_, (hx, hy), q * 5) for p_ in ((hx - 22, hy + 6), (hx + 22, hy + 6), (hx, hy - 16))], fill=255)

def art_y_zengjing(A, cv, t, u):
    ground(A, GROUND)
    person(A, 300, GROUND, 230, dir=1, kneel=True, bow=50, arm=80, hat='none', layer='ink')
    official(A, 520, GROUND, 250, dir=-1, arm=60, layer='mid')
    n = int(clamp(u / (2.5 * P)) * 12)
    for k in range(n):
        x = 720 + (k % 3) * 90; y = GROUND - 14 - (k // 3) * 30
        A.d['ink'].rectangle((x - 40, y - 26, x + 40, y), fill=255)
        A.d['red'].rectangle((x - 30, y - 22, x - 20, y - 4), fill=255)
    A.flush(cv)
    type_in(cv, text_img('《大义觉迷录》', SERIF, 44, INK, 'Black', bleed=False), 810, 1030, t, t - u + P, 0.4)

def art_y_hetong(A, cv, t, u):
    for k in range(30):
        q = (t * 0.4 + k / 30) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    ground(A, GROUND)
    for k in range(5):
        x = 140 + k * 190
        ang = 0.5 + 0.3 * k % 0.6
        top = rotp((x, GROUND - 300), (x, GROUND), ang * (1 if k % 2 else -1))
        A.d['ink'].line((x, GROUND, top[0], top[1]), fill=255, width=6)
        A.d['red' if k % 2 else 'mid'].polygon([top, (top[0] + 60, top[1] + 10), (top[0] + 50, top[1] + 70), (top[0] - 6, top[1] + 60)], fill=200)
    for k in range(3):
        x = lerp(700, 1100, ease_out(u / (3 * P))) + k * 90
        rider(A, x, GROUND - k * 10, 110, 1, t * 8 + k, layer='mid')

def art_y_porcelain(A, cv, t, u):
    cx, cy = 540, 1120
    p = ease_out(u / 0.6)
    A.d['wash'].chord((cx - 260 * p, cy - 200, cx + 260 * p, cy + 180), 0, 180, fill=230)
    A.d['ink'].arc((cx - 260 * p, cy - 200, cx + 260 * p, cy + 180), 0, 180, fill=255, width=6)
    A.d['ink'].line((cx - 260 * p, cy - 10, cx + 260 * p, cy - 10), fill=255, width=6)
    A.d['ink'].rectangle((cx - 80, cy + 175, cx + 80, cy + 200), fill=255)
    q = clamp((u - 0.5) / (2 * P))
    for k in range(int(q * 5)):
        fx = cx - 160 + k * 80; fy = cy + 60 + 20 * math.sin(k)
        for j in range(5):
            a = j * 2 * math.pi / 5
            A.d['red' if k % 2 else 'cobalt'].ellipse((fx + 16 * math.cos(a) - 10, fy + 16 * math.sin(a) - 10, fx + 16 * math.cos(a) + 10, fy + 16 * math.sin(a) + 10), fill=255)
    A.d['ink'].line((760, 900, 700 + 60 * math.sin(t * 3), 1080), fill=255, width=6)

def art_y_ill(A, cv, t, u):
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    cough = 12 * max(0, math.sin(t * 9)) if u > 0.6 else 0
    person(A, 540, GROUND, 230, dir=1, hat='crown', kneel=True, bow=40 + cough, arm=60, layer='ink')
    for k in range(5):
        q = clamp((u - 0.8 - k * 0.15) / 0.6)
        x = 660 + k * 30 + 100 * q; y = 1240 + (GROUND - 1240) * q
        A.d['mid'].polygon([rotp(p_, (x, y), q * 3) for p_ in ((x - 30, y - 10), (x + 30, y - 10), (x + 30, y + 10), (x - 30, y + 10))], fill=255)
    ground(A, GROUND)

# ================================================================ 第五回 十三年
def art_y_treasury(A, cv, t, u):
    for i in range(4):
        chest(A, 180 + i * 240, GROUND, 200, 170, fill_=clamp(u / (2 * P) - i * 0.15), lid=0.0)
    ground(A, GROUND)

def art_y_alchemy(A, cv, t, u):
    A.d['ink'].chord((300, 1080, 560, 1320), 0, 180, fill=255)
    A.d['ink'].rectangle((300, 1150, 560, 1200), fill=255)
    for lx in (320, 520): A.d['ink'].rectangle((lx, 1290, lx + 20, GROUND), fill=255)
    flames(A, 430, GROUND, 180, 70, t, n=4, seed=13, smoke=False)
    for k in range(4):
        q = ((t * 0.3 + k / 4) % 1)
        x = 430 + 80 * math.sin(q * 6 + k); y = 1140 - 360 * q
        r = 40 + 80 * q
        A.d['purple'].ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=int(150 * (1 - q)))
    person(A, 200, GROUND, 220, dir=1, robe=True, hat='knot', arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 6)), layer='ink')
    person(A, 760, GROUND, 260, dir=-1, hat='crown', arm=60, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('丹', 60), 820, 940, t, t - u + P)

def art_y_night(A, cv, t, u):
    """8-beat mystery: lit window → alchemy smoke → a shadow across the roof → the figure falls → darkness."""
    ph = u / P
    A.d['wash'].ellipse((720, 640, 860, 780), fill=255)
    palace(A, 540, GROUND, 760, layer='mid')
    light = 1.0 if ph < 6 else clamp(1 - (u - 6 * P) / 0.5)
    A.d['wash'].rectangle((400, 1150, 680, 1290), fill=0)
    if light > 0:
        A.d['yellow'].rectangle((400, 1150, 680, 1290), fill=int(170 * light))
        fall = -80 * ease_out((u - 5 * P) / 0.5) if ph >= 5 else 0
        person(A, 540, 1290, 120, dir=1, hat='crown', kneel=True, bow=20, arm=90, fall=fall, layer='ink')
    for k in range(1, 4):
        A.d['ink'].line((400 + k * 70, 1150, 400 + k * 70, 1290), fill=200, width=3)
    if ph >= 2:
        for k in range(3):
            q = ((t * 0.3 + k / 3) % 1)
            A.d['purple'].ellipse((180 + 40 * math.sin(q * 5) - 50 - 60 * q, 1200 - 300 * q - 30, 180 + 40 * math.sin(q * 5) + 50 + 60 * q, 1200 - 300 * q + 30), fill=int(140 * (1 - q)))
    if 4 <= ph < 5.5:
        q = clamp((u - 4 * P) / (1.2 * P))
        x = lerp(140, 940, q); y = 960 - 140 * math.sin(math.pi * q)
        person(A, x, y, 110, dir=1, female=True, robe=False, ph=t * 10, arm=120, layer='ink')
    A.flush(cv)
    for i, (nm, b) in enumerate((('丹药', 2), ('刺杀', 4), ('中风', 5))):
        if ph >= b:
            stamp(cv, seal(nm, 40, INK if i == 1 else ZHU), 180 + i * 360, 760, t, t - u + b * P, rot=(i - 1) * 6)
    if ph >= 6.5:
        stamp(cv, seal('谜', 90, INK), 540, 1000, t, t - u + 6.5 * P)

def art_y_tailing(A, cv, t, u):
    for x in (120, 960):
        A.d['ink'].line((x, GROUND, x, 900), fill=255, width=12)
        for j in range(4):
            A.d['mid'].ellipse((x - 80 + j * 10, 880 + j * 70, x + 80 - j * 10, 940 + j * 70), fill=255)
    for i, x in enumerate((340, 540, 740)):
        h = 360 if i == 1 else 290
        A.d['ink'].rectangle((x - 70, GROUND - h, x - 50, GROUND), fill=255)
        A.d['ink'].rectangle((x + 50, GROUND - h, x + 70, GROUND), fill=255)
        A.d['ink'].polygon([(x - 110, GROUND - h), (x + 110, GROUND - h), (x + 80, GROUND - h - 50), (x - 80, GROUND - h - 50)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('泰陵', 54), 540, 960, t, t - u + P)

def art_y_bridge(A, cv, t, u):
    A.d['wash'].rectangle((60, 1260, W - 60, 1360), fill=170)
    waves(A, 1270, t, rows=2, amp=5, speed=1.5)
    p = ease_out(u / (1.5 * P))
    pts = [(lerp(200, 880, f), 1260 - 200 * math.sin(math.pi * f)) for f in np.linspace(0, p, 30)]
    if len(pts) > 1:
        A.d['ink'].line(pts, fill=255, width=26)
    A.flush(cv)
    stamp(cv, seal('康熙', 50, INK), 170, 1150, t, t - u)
    stamp(cv, seal('雍正', 60), 540, 990, t, t - u + 1.5 * P)
    stamp(cv, seal('乾隆', 50, INK), 910, 1150, t, t - u + 2 * P)

# ================================================================ script
CHAPTERS = {16: ('第一回', '天下闲人'), 48: ('第二回', '继位疑云'), 80: ('第三回', '雍正改革'),
            112: ('第四回', '铁腕治国'), 144: ('第五回', '十三年')}

CARDS = [
    C(0, 2, 'hook', 'num', num='四十五岁', line='才登基为帝', art=art_y_hook_45),
    C(2, 4, 'hook', 'num', num='十三年', line='干完别人百年的改革', art=art_y_hook_13),
    C(4, 6, 'hook', 'num', num='一千万字', line='朱批奏折', art=art_y_hook_pile),
    C(6, 8, 'hook', 'num', num='死因成谜', line='猝逝圆明园', art=art_y_hook_mystery),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 天下闲人
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'night', 'card', year=1678, main='生于紫禁城', sub='康熙皇四子 · 生母乌雅氏', note='十月三十日 生于紫禁城', art=art_y_cradle),
    C(22, 26, 'life', 'card', year=1684, main='养母教字', sub='由孝懿皇后抚养 · 自幼勤学', note='朕之幼年 皆赖皇考教诲', art=art_y_tutor),
    C(26, 30, 'war', 'card', year=1696, main='随父出征', sub='十九岁 · 统领正红旗大营', note='随驾亲征噶尔丹', art=art_y_campaign),
    C(30, 34, 'life', 'card', year=1709, main='封雍亲王', sub='三十二岁 · 晋封亲王', note='赐园 圆明', art=art_y_prince_gate),
    C(34, 38, 'life', 'card', year=1710, main='天下第一闲人', sub='吃斋念佛 · 不争不抢', note='自号破尘居士 圆明居士', art=art_y_idle),
    C(38, 42, 'night', 'card', year=1712, main='九灯余一', sub='兄弟们争得头破血流 · 他按兵不动', note='不争 是最好的争', art=art_y_lamps),
    C(42, 46, 'court', 'card', year=1720, main='替父查账', sub='清查户部 · 赈济灾民 · 得罪满朝', note='办事认真 不避嫌怨', art=art_y_audit),
    C(46, 48, 'death', 'card', year=1722, main='康熙驾崩', sub='畅春园钟声 · 风云突变', art=art_y_bell),
    # ---- 第二回 继位疑云
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'court', 'card', year=1722, main='隆科多宣诏', sub='传位皇四子 · 满座皆惊', note='民间相传 十四子被改为于四子', art=art_y_edict),
    C(54, 58, 'empire', 'card', year=1722, main='四十五岁登基', sub='改元雍正 · 中年天子', note='雍亲王 正大光明', art=art_y_crown),
    C(58, 66, 'empire', 'card', year=1723, main='正大光明', sub='秘密立储 · 遗诏藏于匾后', note='亲书储君之名 缄藏匣内 置于正大光明匾额之后', art=art_y_plaque),
    C(66, 70, 'night', 'card', year=1726, main='兄弟反目', sub='八弟九弟 · 被改名削籍', note='阿其那 塞思黑', art=art_y_brothers),
    C(70, 74, 'war', 'card', year=1724, main='年羹尧', sub='平定青海 · 功高盖世', note='年大将军 威震西陲', art=art_y_nian),
    C(74, 80, 'death', 'card', year=1726, main='功臣末路', sub='年羹尧赐死 · 隆科多圈禁', note='九十二款大罪 令其自裁', art=art_y_fallen),
    # ---- 第三回 雍正改革
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'court', 'card', year=1723, main='清查亏空', sub='国库空虚 · 限期三年补齐', note='亏空钱粮 定限三年 务期如数补足', art=art_y_deficit),
    C(86, 90, 'works', 'card', year=1723, main='摊丁入亩', sub='人头税并入田赋 · 穷人减负', note='地多者多交 地少者少交', art=art_y_tanding),
    C(90, 98, 'night', 'card', year=1727, main='朱批万言', sub='夜夜批阅奏折 · 事必躬亲', note='朕就是这样汉子 就是这样秉性 就是这样皇帝', art=art_y_zhupi),
    C(98, 100, 'works', 'card', year=1724, main='火耗归公', sub='碎银熔铸之耗 · 收归国库', art=art_y_huohao),
    C(100, 102, 'court', 'card', year=1724, main='养廉银', sub='高薪养廉 · 以绝贪念', art=art_y_yanglian),
    C(102, 104, 'works', 'card', year=1726, main='改土归流', sub='西南土司 · 改设流官', art=art_y_gaitu),
    C(104, 112, 'works', 'reform'),
    # ---- 第四回 铁腕治国
    C(112, 114, 'court', 'chapter'),
    C(114, 118, 'court', 'card', year=1729, main='设军机处', sub='几间板房 · 却是帝国中枢', note='军机大臣 跪受笔录', art=art_y_junji),
    C(118, 126, 'empire', 'list', year=1728, items=['废除贱籍', '官绅纳粮', '整顿旗务', '整饬吏治']),
    C(126, 130, 'night', 'card', year=1728, main='曾静案', sub='反清书生被擒 · 皇帝亲自辩驳', note='颁行大义觉迷录 天下学宫', art=art_y_zengjing),
    C(130, 134, 'war', 'card', year=1731, main='和通泊之败', sub='西征准噶尔 · 清军惨败', note='将士死伤过半', art=art_y_hetong),
    C(134, 138, 'empire', 'card', year=1730, main='雍正审美', sub='珐琅彩 粉彩 · 简约雅致', note='亲定瓷样 一器一改', art=art_y_porcelain),
    C(138, 142, 'fate', 'card', year=1733, main='积劳成疾', sub='每日睡不足四个时辰', note='以勤先天下', art=art_y_ill),
    C(142, 144, 'fate', 'card', year=1734, main='国库充盈', sub='一扫康熙末年亏空', art=art_y_treasury),
    # ---- 第五回 十三年
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'fate', 'card', year=1734, main='炼丹求寿', sub='圆明园中 · 道士炼丹', note='张太虚 王定乾 入园炼丹', art=art_y_alchemy),
    C(150, 158, 'death', 'card', year=1735, main='圆明园之夜', sub='八月二十三日 · 骤然驾崩', note='丹药中毒 中风 吕四娘刺杀 众说纷纭', art=art_y_night),
    C(158, 162, 'death', 'card', year=1735, main='葬于泰陵', sub='开辟清西陵', note='享年五十八岁 在位十三年', art=art_y_tailing),
    C(162, 170, 'end', 'card', year=1735, main='承上启下', sub='上承康熙 · 下启乾隆', note='康雍乾盛世 雍正居中', art=art_y_bridge),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z, St, M, K):
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
for mod in (G, L, Wd, Tz, Z, St, M, K):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_year(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=ZHU + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, S.art_emperor)
    fx = Art()
    ink_in(cv, text_img('爱新觉罗 · 胤禛', SERIF, 46, ZHU, 'Bold', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '雍正', BRUSH, 220, INK, W / 2, 450, t, s0, stagger=0.1, seed=77)
    fx.flush(cv)
    stamp(cv, seal('朱批', 66), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元1678 — 1735', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '刻薄寡恩？', BRUSH, 120, INK, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '勤政改革？', BRUSH, 120, ZHU, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

LIST_ART = [art_y_jianji, art_y_gentry, art_y_banners, art_y_purge]
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
    memorial(A, 240, 560, 75, 420, 8, clamp(u / 0.6))
    A.flush(cv, alpha=clamp(u / 0.6) * 0.3)
    fx = Art()
    chars_in(cv, fx, '实干之君', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('胤禛', 64), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('在位十三年 · 朱批一千余万字', SERIF, 48, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.35)
    type_in(cv, text_img('他几乎是累死在龙椅上的', SERIF, 52, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '这样的老板', BRUSH, 110, ZHU, W / 2, 1190, t, END + 1.15, stagger=0.07, drop=30, splash=False)
    type_in(cv, text_img('你愿意给他打工吗？评论区说说', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
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
        d.line(pts, fill=INK + (200,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 乾隆皇帝', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, list=scene_list,
                reform=scene_reform, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第捌集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(8):
        q = text_img('最勤奋的皇帝 · 他到底有多拼？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 300, 335, W / 2 + 300, 335), fill=ZHU + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, ZHU, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=ZHU + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=INK + (255,))
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
    if ff.returncode != 0: sys.exit(1)
    print('done', out)
