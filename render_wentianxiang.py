# 千古人物志 · 第拾伍集 · 文天祥 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈，墨色最后绘制）。每一幕画面均为本集新画，不重复。
# 本集特色：丹心汗青 —— 竹青远山 · 竹简章回卡（每回多展开几片简，简上一滴丹红）· 竹节边角
#          · 八拍「过零丁洋」 · 抗元转战六印回顾 · 八拍「崖山海战」 · 八拍「正气歌」 · 柴市就义
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_yuefei as Yf          # engine + helpers (ink layers drawn last)
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
from render_kangxi import rect, lantern
from render_songtaizu import tent
from render_mingtaizu import big_ship
from render_zhuge import starfield
from render_yuefei import jin_rider, cn_year

F.RIPPLE = False

BORN, DIED = 1236, 1283
END_BEAT = 170
BAMBOO = (78, 112, 74)              # 汗青
DAN = (196, 30, 36)                 # 丹心
S.LAYERS.append(('bamboo', BAMBOO, 0.80, 1.3))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

# ================================================================ episode look
WM = dict(hook='丹', life='祥', court='相', night='夜', war='戰', empire='宋', works='海', fate='青', death='义', end='丹')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire', 'works'):
    G.THEMES[k]['part'] = 'ash'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (DAN, 250, (W * 0.5, 820))
G.THEMES['works']['sun'] = ((150, 150, 150), 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (DAN, 210, (W * 0.5, 720))
G.base_bg.cache_clear()

MTN_COL = {'night': (40, 48, 44), 'death': (58, 60, 58), 'war': (94, 58, 46), 'works': (62, 74, 80)}
def draw_background(t, theme):
    """汗青: bamboo-green ranges."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(154, 172, 150), (104, 128, 100), MTN_COL.get(theme, (60, 86, 58))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """竹节: a bamboo stalk with nodes along each corner, a single red dot."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = BAMBOO + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 160, y), fill=col, width=5); d.line((x, y, x, y + sy * 160), fill=col, width=5)
        for k in (50, 105):
            d.line((x + sx * k, y - 6, x + sx * k, y + 6), fill=INK + (200,), width=3)
            d.line((x - 6, y + sy * k, x + 6, y + sy * k), fill=INK + (200,), width=3)
        d.ellipse((x + sx * 20 - 7, y + sy * 20 - 7, x + sx * 20 + 7, y + sy * 20 + 7), fill=DAN + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ 竹简 chapter card
CH_SLIPS = {16: 5, 48: 7, 80: 9, 112: 11, 144: 13}
def slips(A, cx, top, n, p, t, h=520, layer='bamboo'):
    q = ease_out(p)
    k = max(1, int(n * q + 0.999))
    w = 56
    x0 = cx + (n * w) / 2
    for i in range(k):
        x = x0 - (i + 1) * w
        A.d[layer].rectangle((x + 4, top, x + w - 4, top + h), fill=200)
        A.d['ink'].rectangle((x + 4, top, x + w - 4, top + h), outline=200, width=2)
    if k:
        A.d['ink'].line((x0 - k * w, top + 60, x0, top + 60), fill=255, width=4)
        A.d['ink'].line((x0 - k * w, top + h - 60, x0, top + h - 60), fill=255, width=4)
    return x0 - k * w, x0

def art_slip_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = CH_SLIPS.get(kb, 7)
    slips(A, 540, 640, n, u / 0.5, t)
    drop = clamp((u - 0.5) / 0.5)
    if drop > 0:
        y = lerp(560, 900, ease_out(drop))
        r = 26 + 10 * ease_out(drop)
        A.d['red'].ellipse((540 - r, y - r, 540 + r, y + r), fill=255)
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_slip_chapter)
    ink_in(cv, text_img(no, SERIF, 56, DAN, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ primitives
def wen(A, x, y, h, dir=1, layer='ink', **kw):
    """文天祥: scholar-official robe with a tall square cap."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, **kw)
    A.d[layer].rectangle((x - 0.07 * h, y - 1.08 * h, x + 0.07 * h, y - 0.94 * h), fill=255)
    A.d[layer].line((x - 0.16 * h, y - 1.0 * h, x + 0.16 * h, y - 1.0 * h), fill=255, width=max(2, int(0.02 * h)))
    return hand

def yuan_rider(A, x, y, s, dir=-1, ph=0.0, layer='mid', moving=True):
    jin_rider(A, x, y, s, dir, ph, layer=layer, moving=moving)

def cell(A, x0, y0, x1, y1):
    A.d['mid'].rectangle((x0, y0, x1, y1), fill=120)
    A.d['ink'].rectangle((x0, y0, x1, y1), outline=255, width=8)
    A.d['ink'].rectangle((x1 - 160, y0 + 40, x1 - 40, y0 + 140), outline=255, width=4)
    for k in range(1, 4):
        A.d['ink'].line((x1 - 160 + k * 30, y0 + 40, x1 - 160 + k * 30, y0 + 140), fill=255, width=4)

# ================================================================ hooks
def art_w_hook_zhuang(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 150, dir=-1, hat='crown', arm=lerp(20, 80, ease_out(u / P)), layer='mid')
    wen(A, 380, GROUND, 260, dir=1, kneel=True, bow=40, arm=80, layer='ink')
    A.flush(cv)
    stamp(cv, seal('状元', 54), 380, 950, t, t - u + P, rot=-5)

def art_w_hook_three(A, cv, t, u):
    for k in range(3):
        if u > k * 0.5:
            x = 240 + k * 300
            A.d['ink'].rectangle((x - 80, 1100, x + 80, 1300), outline=255, width=6)
            A.d['ink'].text((x - 50, 1140), cn_num(k + 1) + '年', font=font(SERIF, 60, 'Black'), fill=255)
    ground(A, GROUND)

def art_w_hook_slip(A, cv, t, u):
    slips(A, 540, 880, 9, u / 0.6, t, h=420)
    A.flush(cv)
    if u > 0.6:
        for i, ch in enumerate('照汗青'):
            ink_in(cv, text_img(ch, BRUSH, 110, DAN), 540, 960 + i * 120, t, t - u + 0.6 + i * 0.2, dur=0.3, settle=1.2)

def art_w_hook_south(A, cv, t, u):
    for k in range(34):
        q = (t * 0.3 + k / 34) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    ground(A, GROUND)
    wen(A, 540, GROUND, 300, dir=-1, kneel=True, bow=lerp(0, 50, ease_out((u - 0.5) / 0.6)), arm=80, layer='ink')
    A.flush(cv)
    paste(cv, text_img('南', SERIF, 90, DAN, 'Black', bleed=False), 200, 1100, 1, clamp((u - 0.3) / 0.3))

# ================================================================ 第一回 状元
def art_w_birth(A, cv, t, u):
    A.d['mid'].rectangle((220, 1100, 520, GROUND), fill=255)
    A.d['ink'].polygon([(180, 1110), (560, 1110), (480, 1030), (260, 1030)], fill=255)
    for x in (700, 820, 940):
        A.d['bamboo'].line((x, GROUND, x + 6 * math.sin(t + x), 900), fill=255, width=10)
        for j in range(3):
            A.d['bamboo'].polygon([(x, 950 + j * 80), (x + 70, 960 + j * 80), (x + 10, 970 + j * 80)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('庐陵', 56), 380, 940, t, t - u + P)

def art_w_shrine(A, cv, t, u):
    palace(A, 620, GROUND, 520, layer='mid')
    for k in range(3):
        A.d['ink'].rectangle((520 + k * 90, 1180, 560 + k * 90, 1260), outline=255, width=3)
    ground(A, GROUND)
    wen(A, 280, GROUND, 180, dir=1, kneel=True, bow=lerp(10, 45, ease_out((u - 0.5) / 0.5)), arm=80, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('殁不俎豆其间 非夫也', BRUSH, 60, INK), W / 2, 880, t, t - u + P, 0.5)

def art_w_exam(A, cv, t, u):
    palace(A, 540, 1120, 460, layer='mid')
    ground(A, GROUND)
    for r_ in range(2):
        for k in range(5):
            x = 160 + k * 190; y = GROUND - r_ * 90
            wen(A, x, y, 140 - r_ * 20, dir=1, kneel=True, bow=30, arm=100, layer='ink' if (r_ == 0 and k == 2) else 'mid')
    A.flush(cv)
    paste(cv, text_img('万言策', SERIF, 60, DAN, 'Black', bleed=False), W / 2, 960, 1, clamp((u - P) / 0.3))

def art_w_first(A, cv, t, u):
    p = ease_out(u / 0.6)
    w = 300 * p
    A.d['yellow'].rectangle((540 - w, 860, 540 + w, 1100), fill=255)
    A.d['ink'].rectangle((540 - w - 14, 850, 540 - w, 1110), fill=255); A.d['ink'].rectangle((540 + w, 850, 540 + w + 14, 1110), fill=255)
    ground(A, GROUND)
    for k in range(5):
        person(A, 140 + k * 190, GROUND, 150, dir=1 if k < 2 else -1, robe=True, hat='knot', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='mid')
    A.flush(cv)
    if p > 0.8:
        ink_in(cv, text_img('第一甲第一名', SERIF, 50, INK, 'Black', bleed=False), 540, 980, t, t - u + 0.5, dur=0.3, settle=1.1)

def art_w_jia(A, cv, t, u):
    A.d['wash'].rectangle((60, 1240, W - 60, 1340), fill=160)
    waves(A, 1250, t, rows=2, amp=5, speed=1.2)
    A.d['ink'].polygon([(300, 1240), (760, 1240), (720, 1280), (340, 1280)], fill=255)
    A.d['red'].rectangle((380, 1150, 680, 1240), fill=220)
    for k in range(4):
        lantern(A, 400 + k * 90, 1100, t, k, size=14)
    person(A, 540, 1240, 120, dir=1, robe=True, hat='crown', arm=150, layer='ink')
    A.flush(cv)
    stamp(cv, seal('贾似道', 46, INK), 860, 940, t, t - u + P, rot=5)

def art_w_resign(A, cv, t, u):
    ground(A, GROUND)
    x = walk_x(600, 200, u, 3 * P)
    wen(A, x, GROUND, 230, dir=-1, ph=t * 5, arm=40, layer='ink')
    A.d['ink'].rectangle((760, GROUND - 160, 900, GROUND - 120), fill=255)
    A.d['red'].rectangle((800, GROUND - 200, 840, GROUND - 160), fill=255)
    A.flush(cv)
    stamp(cv, seal('罢官', 54, INK), 830, 940, t, t - u + P)

def art_w_army(A, cv, t, u):
    ground(A, GROUND)
    for row, (yy, s_, lay, sp) in enumerate(((1290, 100, 'wash', 260), (1350, 140, 'mid', 360), (GROUND, 190, 'ink', 470))):
        for k in range(7):
            x = W - ((k * s_ * 1.6 + t * sp) % (W + 300) - 150)
            yuan_rider(A, x, yy, s_, -1, t * 13 + k, layer=lay)

def art_w_qinwang(A, cv, t, u):
    ground(A, GROUND)
    for k in range(int(clamp(u / (2 * P)) * 8)):
        x = 120 + k * 100
        A.d['gold'].ellipse((x - 26, GROUND - 40, x + 26, GROUND - 10), fill=255)
    wen(A, 760, GROUND, 260, dir=-1, arm=lerp(30, 150, ease_out((u - P) / 0.4)), layer='ink')
    for k in range(5):
        person(A, walk_x(-100 - k * 100, 260 - k * 60, u - P, 2 * P), GROUND, 160, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('毁家纾难', 44), 760, 940, t, t - u + 1.5 * P, rot=5)

# ================================================================ 第二回 出使
def art_w_envoy(A, cv, t, u):
    tent(A, 760, GROUND - 10, 520, 440, layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(4):
        person(A, 640 + k * 90, GROUND, 180, dir=-1, robe=False, hat='helmet', arm=lerp(30, 120, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='mid')
    wen(A, 320, GROUND, 260, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('抗论', 54), 320, 940, t, t - u + P, rot=-5)

def art_w_detained(A, cv, t, u):
    ground(A, GROUND)
    wen(A, 540, GROUND, 250, dir=1, kneel=False, arm=-10, layer='ink')
    for k in range(4):
        a = math.pi * (k / 3)
        x = 540 - 300 * math.cos(a)
        person(A, x, GROUND, 200, dir=1 if x < 540 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    A.flush(cv)
    stamp(cv, seal('扣留', 54, INK), 540, 900, t, t - u + P)

def art_w_linan(A, cv, t, u):
    city_wall(A, 60, W - 60, 1120, gate_x=540, label='临安', open_=ease_out((u - 0.5) / 0.6))
    ground(A, GROUND)
    for k in range(3):
        x = walk_x(540, 160 - k * 60, u - P, 2.5 * P)
        person(A, x, GROUND, 160, dir=-1, hat='crown' if k == 0 else 'knot', female=k == 1, bow=30, ph=t * 3 + k, arm=20, layer='ink')
    A.flush(cv)
    stamp(cv, seal('降表', 54, INK), 860, 940, t, t - u + P, rot=6)

def art_w_escape(A, cv, t, u):
    A.d['wash'].ellipse((760, 640, 880, 760), fill=255)
    A.d['wash'].rectangle((60, 1220, W - 60, 1380), fill=160)
    waves(A, 1230, t, rows=3, amp=7, speed=2)
    x = lerp(120, 760, ease_out(u / (3 * P)))
    A.d['ink'].polygon([(x - 80, 1240), (x + 80, 1240), (x + 60, 1270), (x - 60, 1270)], fill=255)
    wen(A, x, 1240, 110, dir=1, kneel=True, arm=60, layer='ink')
    A.d['ink'].line((x + 60, 1180, x + 120, 1290), fill=255, width=4)
    A.flush(cv)
    stamp(cv, seal('京口脱险', 44), 300, 940, t, t - u + P, rot=-5)

def art_w_suspect(A, cv, t, u):
    city_wall(A, 360, W - 60, 1120, gate_x=700, label='真州', open_=0.0)
    ground(A, GROUND)
    for k in range(4):
        person(A, 420 + k * 120, 1110, 80, dir=-1, robe=False, hat='helmet', arm=lerp(40, 90, 0.5 + 0.5 * math.sin(t * 6 + k)), bow=-10, layer='ink')
    wen(A, 200, GROUND, 240, dir=1, arm=60, layer='ink')
    for k in range(3):
        q = ((u * 1.2 + k * 0.3) % 1)
        arrow(A, lerp(560, 260, q), lerp(1110, GROUND - 200, q), math.pi * 0.85, 60)
    A.flush(cv)
    stamp(cv, seal('疑为奸细', 44, INK), 860, 940, t, t - u + P, rot=5)

def art_w_chancellor(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 110, dir=-1, hat='crown', arm=20, layer='mid')
    wen(A, 380, GROUND, 270, dir=1, kneel=True, bow=40, arm=80, layer='ink')
    A.flush(cv)
    stamp(cv, seal('右丞相', 50), 380, 940, t, t - u + P, rot=-5)

def art_w_banner(A, cv, t, u):
    for k in range(5):
        A.d['mid'].polygon([(80 + k * 200, GROUND), (180 + k * 200, 980 + (k % 2) * 60), (280 + k * 200, GROUND)], fill=200)
    ground(A, GROUND)
    for k in range(6):
        p = ease_out((u - k * 0.15) / 0.4)
        flag(A, 120 + k * 160, GROUND, 300 * p, t + k, w=90, layer='red')
    wen(A, 540, GROUND, 240, dir=1, arm=150, layer='ink')

# ================================================================ 第三回 转战
WAR = [('赣州起兵', 1275), ('福州', 1276), ('汀州', 1277), ('收复梅州', 1277), ('空坑兵败', 1277), ('五坡岭被俘', 1278)]
def scene_war(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    idx = int(k - c[0])
    A = Art(); beat_fx(A, t)
    pts = []
    for j in range(48):
        a = 2 * math.pi * j / 48
        r = 380 + 40 * math.sin(a * 3 + 1) + 22 * math.sin(a * 7)
        pts.append((540 + r * math.cos(a), 1040 + r * math.sin(a) * 0.78))
    A.d['bamboo'].polygon(pts, fill=80); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    pos = [(400, 900), (760, 980), (580, 1080), (420, 1180), (300, 1060), (640, 1290)]
    for i, (x, y) in enumerate(pos):
        if t >= bt(c[0] + i):
            px, py = pos[i - 1] if i else (360, 800)
            q = ease_out((t - bt(c[0] + i)) / 0.3)
            A.d['red'].line((px, py, lerp(px, x, q), lerp(py, y, q)), fill=255, width=8)
    A.flush(cv)
    for i, ((nm, yr), (x, y)) in enumerate(zip(WAR, pos)):
        if t >= bt(c[0] + i):
            stamp(cv, seal(nm[:2], 44, DAN if i < 4 else INK), x, y, t, bt(c[0] + i) + 0.1)
    if 0 <= idx < 6 and not gather:
        nm, yr = WAR[idx]
        ink_in(cv, text_img(f'公元{cn_year(yr)}年 · {nm}', SERIF, 50, DAN, 'Black', bleed=False, spacing=4), W / 2, 1470, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '转战闽赣', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '屡败屡战', BRUSH, 170, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '至死不降', BRUSH, 140, DAN, W / 2, 1470, t, bt(c[0] + 7), stagger=0.07, seed=111)
    fx.flush(cv)

def art_w_family(A, cv, t, u):
    for k in range(40):
        q = (t * 1.0 + k / 40) % 1
        x = 80 + (k * 29) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 8, y + 36), fill=200, width=2)
    ground(A, GROUND)
    for k in range(3):
        person(A, walk_x(600 + k * 80, 1000 + k * 80, u, 3 * P), GROUND, 170 - k * 30, dir=1, female=True, bow=30, ph=t * 3 + k, arm=20, layer='mid')
    for k in range(2):
        yuan_rider(A, walk_x(500 - k * 140, 900 - k * 140, u, 3 * P), GROUND, 140, 1, t * 6 + k, layer='ink')
    wen(A, 200, GROUND, 240, dir=1, kneel=True, bow=50, arm=110, layer='ink')

def art_w_captured(A, cv, t, u):
    for k in range(5):
        A.d['mid'].polygon([(80 + k * 200, GROUND), (180 + k * 200, 1000), (280 + k * 200, GROUND)], fill=200)
    ground(A, GROUND)
    for k in range(4):
        yuan_rider(A, lerp(1100, 620, ease_out(u / (1.5 * P))) + k * 100, GROUND - (k % 2) * 10, 130, -1, t * 12 + k, layer='mid')
    wen(A, 360, GROUND, 250, dir=1, arm=lerp(40, 150, ease_out((u - 1.5 * P) / 0.3)), layer='ink')
    A.flush(cv)
    if u > 1.6 * P:
        stamp(cv, seal('吞冰片', 50), 360, 940, t, t - u + 1.6 * P, rot=-5)

def art_w_lingding(A, cv, t, u):
    """8-beat set piece: on a Yuan ship crossing the 零丁洋, he answers with a poem, line by line."""
    A.d['wash'].rectangle((60, 1150, W - 60, 1380), fill=150)
    waves(A, 1160, t, rows=5, amp=12, speed=2.2)
    big_ship(A, 760, 1210, 180, t, layer='mid')
    wen(A, 700, 1060, 120, dir=-1, arm=20, layer='ink')
    A.flush(cv)
    lines = ['辛苦遭逢起一经', '干戈寥落四周星', '惶恐滩头说惶恐', '零丁洋里叹零丁']
    for i, ln in enumerate(lines):
        st = t - u + (0.4 + i * 1.8) * P
        if t >= st:
            type_in(cv, text_img(ln, BRUSH, 58, INK, vertical=True), 520 - i * 110, 960, t, st, 0.8)

def art_w_yashan(A, cv, t, u):
    """8-beat set piece: the last Song fleet chained at 崖山 → burns → 陆秀夫 leaps with the child emperor."""
    ph = u / P
    A.d['wash'].rectangle((60, 1100, W - 60, 1380), fill=150)
    waves(A, 1110, t, rows=5, amp=10, speed=2.5)
    burn = ease_out((u - 2 * P) / (3 * P)) if ph > 2 else 0
    for i, x in enumerate((180, 400, 620, 840)):
        big_ship(A, x, 1160, 100, t, layer='ink', burn=clamp(burn - i * 0.1))
    for k in range(3):
        yuan_rider(A, 980 - k * 60, 1080, 60, -1, 0, layer='wash', moving=False)
    if ph >= 5:
        v = u - 5 * P
        q = clamp(v / (1.5 * P))
        x = 520; y = lerp(1000, 1280, q * q)
        person(A, x, y, 140, dir=1, robe=True, hat='knot', baby=True, fall=-60 * q, layer='ink')
        for k in range(6):
            r = 60 * ease_out(q)
            A.d['wash'].ellipse((x - r * 1.5, 1270 - r * 0.3, x + r * 1.5, 1270 + r * 0.3), outline=255, width=3)
    A.flush(cv)
    if ph >= 5.2:
        stamp(cv, seal('陆秀夫', 46, INK), 860, 860, t, t - u + 5.2 * P, rot=6)
    if ph >= 6.6:
        paste(cv, text_img('十万军民 · 蹈海殉国', SERIF, 50, DAN, 'Black', bleed=False, spacing=4), W / 2, 1460, 1, clamp((u - 6.6 * P) / 0.3))

def art_w_witness(A, cv, t, u):
    A.d['wash'].rectangle((60, 1200, W - 60, 1380), fill=160)
    waves(A, 1210, t, rows=4, amp=8, speed=1.4)
    big_ship(A, 360, 1250, 160, t, layer='mid')
    wen(A, 400, 1100, 130, dir=1, kneel=True, bow=55, arm=110, layer='ink')
    for k in range(10):
        q = ((t * 0.3 + k / 10) % 1)
        A.d['wash'].rectangle((620 + k * 36, 1230 + 6 * math.sin(t + k), 650 + k * 36, 1238 + 6 * math.sin(t + k)), fill=int(200 * (1 - q)))

# ================================================================ 第四回 正气
def art_w_dadu(A, cv, t, u):
    for k in range(34):
        q = (t * 0.3 + k / 34) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    city_wall(A, 520, W - 60, 1120, gate_x=780, label='大都', open_=1.0)
    ground(A, GROUND)
    x = lerp(-100, 520, ease_out(u / (3 * P)))
    carriage(A, x, GROUND, 150, dir=1, wheel=t * 4, ph=t * 8, canopy=False)
    for k in range(3):
        yuan_rider(A, x - 220 - k * 120, GROUND, 110, 1, t * 8 + k, layer='mid')

def art_w_tuyao(A, cv, t, u):
    for k in range(3):
        palace(A, 200 + k * 340, 1100, 240, layer='wash')
    ground(A, GROUND)
    person(A, 640, GROUND, 240, dir=-1, robe=True, hat='crown', bow=30, arm=80, layer='mid')
    wen(A, 340, GROUND, 250, dir=1, arm=-20, layer='ink')
    A.flush(cv)
    stamp(cv, seal('留梦炎', 46, INK), 640, 940, t, t - u + 0.3)
    if u > P:
        stamp(cv, seal('骂', 64), 340, 940, t, t - u + P)

def art_w_emperor(A, cv, t, u):
    ground(A, GROUND)
    person(A, 700, GROUND, 180, dir=-1, hat='crown', arm=60, bow=20, layer='mid')
    wen(A, 380, GROUND, 260, dir=1, kneel=True, bow=lerp(0, 50, ease_out((u - P) / 0.4)), arm=80, layer='ink')
    A.flush(cv)
    stamp(cv, seal('宋恭帝', 46, INK), 700, 940, t, t - u + 0.3)
    if u > 2 * P:
        type_in(cv, text_img('圣驾请回', BRUSH, 80, DAN), W / 2, 820, t, t - u + 2 * P, 0.4)

def art_w_prison(A, cv, t, u):
    cell(A, 160, 820, 920, GROUND)
    wen(A, 420, GROUND, 230, dir=1, kneel=True, bow=10, arm=lerp(70, 95, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    for k in range(5):
        q = ((t * 0.5 + k / 5) % 1)
        A.d['wash'].ellipse((760 + k * 20 - 30, lerp(GROUND, 900, q) - 20, 760 + k * 20 + 30, lerp(GROUND, 900, q) + 20), fill=int(150 * (1 - q)))
    A.flush(cv)
    paste(cv, text_img('土室三年', SERIF, 50, DAN, 'Black', bleed=False), W / 2, 1460, 1, clamp((u - P) / 0.3))

def art_w_qixi(A, cv, t, u):
    names = ['水', '土', '日', '火', '米', '人', '秽']
    for i, nm in enumerate(names):
        if u < i * 0.45: continue
        a = -math.pi / 2 + i * 2 * math.pi / 7
        x, y = 540 + 330 * math.cos(a), 1040 + 270 * math.sin(a)
        A.d['wash'].ellipse((x - 70, y - 70, x + 70, y + 70), fill=180)
    A.d['red'].ellipse((470, 970, 610, 1110), fill=255)
    A.flush(cv)
    for i, nm in enumerate(names):
        if u >= i * 0.45:
            a = -math.pi / 2 + i * 2 * math.pi / 7
            paste(cv, text_img(nm + '气', SERIF, 40, INK, 'Black', bleed=False), 540 + 330 * math.cos(a), 1040 + 270 * math.sin(a), 1, 1)
    if u > 3.2 * P:
        ink_in(cv, text_img('一', BRUSH, 120, (250, 240, 230)), 540, 1030, t, t - u + 3.2 * P, dur=0.3)

def art_w_zhengqi(A, cv, t, u):
    """8-beat set piece: 正气歌 written column by column on the prison wall."""
    cell(A, 120, 780, 960, GROUND)
    wen(A, 820, GROUND, 230, dir=-1, kneel=True, bow=10, arm=lerp(80, 110, 0.5 + 0.5 * math.sin(t * 6)), layer='ink')
    A.flush(cv)
    cols = ['天地有正气', '杂然赋流形', '下则为河岳', '上则为日星', '于人曰浩然', '沛乎塞苍冥']
    for i, col in enumerate(cols):
        st = t - u + (0.3 + i * 1.25) * P
        if t >= st:
            type_in(cv, text_img(col, BRUSH, 70, INK, vertical=True), 640 - i * 90, 1100, t, st, 0.7)

def art_w_kublai(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1240), (600, 1240)], fill=255)
    person(A, 770, 1240, 200, dir=-1, hat='crown', arm=lerp(20, 100, ease_out((u - 0.5) / 0.4)), layer='mid')
    wen(A, 340, GROUND, 270, dir=1, arm=-10, layer='ink')
    A.flush(cv)
    stamp(cv, seal('宰相', 54), 680, 920, t, t - u + P, rot=5)
    if u > 2 * P:
        d = ImageDraw.Draw(cv)
        q = ease_out((u - 2 * P) / 0.25)
        d.line((630, 870, 630 + 100 * q, 970), fill=DAN + (240,), width=8)
        type_in(cv, text_img('但愿一死', BRUSH, 80, INK), 340, 860, t, t - u + 2.3 * P, 0.4)

# ================================================================ 第五回 丹心
def art_w_chaishi(A, cv, t, u):
    for k in range(40):
        q = (t * 0.25 + k / 40) % 1
        x = 80 + (k * 23) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    ground(A, GROUND)
    for k in range(8):
        person(A, 120 + k * 120, GROUND, 130, dir=1 if k < 4 else -1, robe=True, hat='knot', bow=20, arm=40, layer='mid')
    wen(A, 540, GROUND - 40, 230, dir=1, arm=-10, layer='ink')
    A.d['ink'].rectangle((420, GROUND - 40, 660, GROUND), fill=255)

def art_w_south_bow(A, cv, t, u):
    for k in range(40):
        q = (t * 0.25 + k / 40) % 1
        x = 80 + (k * 23) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    ground(A, GROUND)
    wen(A, 540, GROUND, 280, dir=-1, kneel=u > P, bow=lerp(0, 60, ease_out((u - P) / 0.4)), arm=80, layer='ink')
    A.flush(cv)
    paste(cv, text_img('南向而拜', SERIF, 50, DAN, 'Black', bleed=False, spacing=6), W / 2, 920, 1, clamp(u / 0.3))

def art_w_belt(A, cv, t, u):
    p = ease_out(u / 0.6)
    A.d['mid'].rectangle((360, 820, 720, 820 + 560 * p), fill=200)
    A.d['ink'].rectangle((360, 820, 720, 820 + 560 * p), outline=255, width=4)
    A.flush(cv)
    lines = ['孔曰成仁', '孟曰取义', '惟其义尽', '所以仁至']
    for i, ln in enumerate(lines):
        st = t - u + (0.5 + i * 0.8) * P
        if t >= st:
            type_in(cv, text_img(ln, BRUSH, 70, INK, vertical=True), 640 - i * 90, 1100, t, st, 0.5)

def art_w_snow_night(A, cv, t, u):
    for k in range(50):
        q = (t * 0.3 + k / 50) % 1
        x = 80 + (k * 19) % 920 + 15 * math.sin(t + k); y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    ground(A, GROUND)
    A.d['wash'].rectangle((300, GROUND - 30, 780, GROUND), fill=255)
    A.d['red'].ellipse((520, GROUND - 26, 560, GROUND - 6), fill=200)
    A.flush(cv)
    paste(cv, text_img('年四十七', SERIF, 50, INK, 'Black', bleed=False, spacing=6), W / 2, 920, 1, clamp((u - P) / 0.3))

def art_w_poem(A, cv, t, u):
    slips(A, 540, 760, 13, u / 0.6, t, h=560)
    A.flush(cv)
    for i, (col, x) in enumerate((('人生自古谁无死', 680), ('留取丹心照汗青', 400))):
        st = t - u + (0.6 + i * 1.6) * P
        if t >= st:
            type_in(cv, text_img(col, BRUSH, 70, DAN if i else INK, vertical=True), x, 1040, t, st, 0.8)

def art_w_shrine_wen(A, cv, t, u):
    palace(A, 540, GROUND, 760, layer='mid')
    A.d['ink'].rectangle((400, 1020, 680, 1090), fill=255)
    A.d['ink'].text((420, 1028), '文丞相祠', font=font(SERIF, 52, 'Black'), fill=0)
    for k in range(4):
        person(A, 280 + k * 160, GROUND, 130, dir=1 if k < 2 else -1, kneel=True, bow=45, arm=60, female=k % 2 == 1, layer='ink')
    for k in range(3):
        q = (t * 0.4 + k / 3) % 1
        A.d['wash'].line((500 + k * 40, 1300 - q * 200, 510 + k * 40 + 10 * math.sin(t * 2 + k), 1260 - q * 200), fill=int(200 * (1 - q)), width=4)

def art_w_heart(A, cv, t, u):
    sun(cv, 540, 1050, 260, DAN, 120)
    fo = font(BRUSH, 420)
    p = ease_out(u / (1.5 * P))
    tmp = Image.new('L', (W, H), 0)
    ImageDraw.Draw(tmp).text((540 - fo.getlength('丹') / 2, 800), '丹', font=fo, fill=255)
    fld = G.transition_field()
    a = np.asarray(tmp, np.float32) * np.clip((p * 1.3 - fld) / 0.08, 0, 1)
    m = Image.fromarray(a.astype(np.uint8))
    A.im['ink'].paste(m, (0, 0), m)
    ground(A, GROUND)

# ================================================================ script
CHAPTERS = {16: ('第一回', '少年状元'), 48: ('第二回', '起兵勤王'), 80: ('第三回', '零丁洋里'),
            112: ('第四回', '天地正气'), 144: ('第五回', '丹心汗青')}

CARDS = [
    C(0, 2, 'hook', 'num', num='二十岁', line='高中状元', art=art_w_hook_zhuang),
    C(2, 4, 'hook', 'num', num='三年囚禁', line='宰相不做', art=art_w_hook_three),
    C(4, 6, 'hook', 'num', num='丹心', line='留取照汗青', art=art_w_hook_slip),
    C(6, 8, 'hook', 'num', num='南向而拜', line='从容就义', art=art_w_hook_south),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 少年状元
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1236, main='生于庐陵', sub='吉州庐陵 · 书香之家', note='庐陵 文章节义之邦', art=art_w_birth),
    C(22, 26, 'court', 'card', year=1250, main='少年立志', sub='拜谒乡贤祠 · 欧阳修 杨邦乂', note='殁不俎豆其间 非夫也', art=art_w_shrine),
    C(26, 30, 'court', 'card', year=1256, main='集英殿对策', sub='万言策论 · 一气呵成', note='不为稿 一挥而成', art=art_w_exam),
    C(30, 34, 'empire', 'card', year=1256, main='状元及第', sub='二十岁 · 宋理宗亲擢第一', note='是卷古谊若龟鉴 忠肝如铁石', art=art_w_first),
    C(34, 38, 'night', 'card', year=1270, main='权臣当道', sub='贾似道把持朝政 · 歌舞湖上', note='西湖歌舞几时休', art=art_w_jia),
    C(38, 42, 'fate', 'card', year=1273, main='屡遭罢官', sub='直言触怒权臣', note='三十七岁 方得起用', art=art_w_resign),
    C(42, 46, 'war', 'card', year=1274, main='元军南下', sub='伯颜率二十万大军 · 直逼临安', note='长江天险 一朝而失', art=art_w_army),
    C(46, 48, 'war', 'card', year=1275, main='毁家纾难', sub='变卖家产 · 起兵勤王', art=art_w_qinwang),
    # ---- 第二回 起兵勤王
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'court', 'card', year=1276, main='出使元营', sub='面斥伯颜 · 据理力争', note='辞色慷慨 元人惊异', art=art_w_envoy),
    C(54, 58, 'night', 'card', year=1276, main='被扣元营', sub='北上途中 · 身为囚徒', art=art_w_detained),
    C(58, 62, 'death', 'card', year=1276, main='临安陷落', sub='谢太后 宋恭帝 · 奉表出降', note='传国玺 献于元', art=art_w_linan),
    C(62, 66, 'night', 'card', year=1276, main='京口脱险', sub='夜半乘小舟逃出', note='九死一生 指南录', art=art_w_escape),
    C(66, 70, 'war', 'card', year=1276, main='真州被疑', sub='守将疑为奸细 · 闭门不纳', note='几为宋人所杀', art=art_w_suspect),
    C(70, 74, 'court', 'card', year=1276, main='福州拜相', sub='南宋小朝廷 · 拜右丞相', note='益王即位于福州', art=art_w_chancellor),
    C(74, 80, 'war', 'card', year=1276, main='再举义旗', sub='南剑州开府 · 招兵买马', note='天下响应', art=art_w_banner),
    # ---- 第三回 零丁洋里
    C(80, 82, 'works', 'chapter'),
    C(82, 90, 'war', 'wardance'),
    C(90, 94, 'death', 'card', year=1277, main='空坑兵败', sub='妻女被俘 · 子女离散', note='妻妾子女 皆为所执', art=art_w_family),
    C(94, 98, 'war', 'card', year=1278, main='五坡岭被俘', sub='吞冰片自尽 · 未死', note='吞脑子 不死', art=art_w_captured),
    C(98, 106, 'works', 'card', year=1279, main='过零丁洋', sub='元将逼其招降 · 以诗作答', note='张弘范见之 笑而置之', art=art_w_lingding),
    C(106, 112, 'night', 'card', year=1279, main='崖山海战', sub='宋军覆没 · 陆秀夫负帝投海', note='崖山之后 宋亡', art=art_w_yashan),
    # ---- 第四回 天地正气
    C(112, 114, 'fate', 'chapter'),
    C(114, 116, 'death', 'card', year=1279, main='船头恸哭', sub='亲眼目睹宋亡', art=art_w_witness),
    C(116, 118, 'night', 'card', year=1279, main='押往大都', sub='北上途中绝食八日不死', art=art_w_dadu),
    C(118, 122, 'court', 'card', year=1279, main='痛斥降臣', sub='留梦炎来劝降 · 被骂而去', note='南宋状元宰相 降元', art=art_w_tuyao),
    C(122, 126, 'court', 'card', year=1279, main='旧主劝降', sub='宋恭帝来劝 · 北跪痛哭', note='圣驾请回', art=art_w_emperor),
    C(126, 130, 'night', 'card', year=1280, main='土牢三年', sub='潮湿污秽 · 七气交侵', note='室广八尺 深可四寻', art=art_w_prison),
    C(130, 134, 'fate', 'card', year=1281, main='以一敌七', sub='吾所养者 浩然之气', note='彼气有七 吾气有一 以一敌七', art=art_w_qixi),
    C(134, 142, 'night', 'card', year=1281, main='正气歌', sub='狱中作 · 天地有正气', note='天地有正气 杂然赋流形', art=art_w_zhengqi),
    C(142, 144, 'empire', 'card', year=1282, main='忽必烈劝降', sub='许以宰相之位', art=art_w_kublai),
    # ---- 第五回 丹心汗青
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'death', 'card', year=1283, main='柴市', sub='数万百姓围观', note='观者万人', art=art_w_chaishi),
    C(150, 154, 'fate', 'card', year=1283, main='南向而拜', sub='问何处是南方 · 拜毕受刑', note='吾事毕矣', art=art_w_south_bow),
    C(154, 158, 'fate', 'card', year=1283, main='衣带赞', sub='死后衣带中留书', note='读圣贤书 所学何事 而今而后 庶几无愧', art=art_w_belt),
    C(158, 162, 'death', 'card', year=1283, main='从容就义', sub='享年四十七岁', note='是日 大风扬沙 天地昼晦', art=art_w_snow_night),
    C(162, 166, 'end', 'card', year=1283, main='丹心汗青', sub='人生自古谁无死', note='留取丹心照汗青', art=art_w_poem),
    C(166, 170, 'end', 'card', year=1283, main='文丞相祠', sub='北京府学胡同 · 香火不绝', note='宋丞相信国公文公之祠', art=art_w_shrine_wen),
    C(170, 999, 'end', 'end'),
]
# art_w_heart kept for the ending backdrop library

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb, Cc, Zg, Yf):
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
for mod in (G, L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb, Cc, Zg, Yf):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_year(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=DAN + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    def art(A, cv_, t_, u_):
        sun(cv_, 600, 1000, 250, DAN, 110)
        ground(A, 1440)
        wen(A, 470, 1440, 700, dir=1, arm=lerp(-5, 55, ease_out(u_ / (2 * P))), layer='ink')
    stage(cv, t, c, art)
    fx = Art()
    ink_in(cv, text_img('文天祥 · 字履善', SERIF, 46, DAN, 'Black', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '文天祥', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('信国公', 50), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元1236 — 1283', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '不识时务？', BRUSH, 120, INK, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '千古气节？', BRUSH, 120, DAN, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    art_w_heart(A, cv, t, u)
    A.flush(cv, alpha=clamp(u / 0.6) * 0.25)
    fx = Art()
    chars_in(cv, fx, '留取丹心', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('履善', 60), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('高官厚禄摆在面前 · 他说只求一死', SERIF, 44, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.4)
    type_in(cv, text_img('一个人 撑起了一个王朝的脊梁', SERIF, 50, INK, 'Bold', bleed=False, spacing=4), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '换作是你', BRUSH, 110, DAN, W / 2, 1190, t, END + 1.15, stagger=0.07, drop=30, splash=False)
    type_in(cv, text_img('降 还是不降？评论区说说', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=DAN + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(252, 240, 226, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=BAMBOO + (230,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 戚继光', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, wardance=scene_war, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第拾伍集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 570, 170, 1, 1)
    if t < bt(8):
        q = text_img('宰相之位摆在面前 · 他为何只求一死？', SERIF, 38, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 330, 335, W / 2 + 330, 335), fill=DAN + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, DAN, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=DAN + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=BAMBOO + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(max(1, int(round(yr - BORN)))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=DAN + (255,))
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
