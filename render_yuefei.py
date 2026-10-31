# 千古人物志 · 第拾肆集 · 岳飞 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈，墨色最后绘制）。每一幕画面均为本集新画，不重复。
# 本集特色：铁甲朱旗 —— 铁灰远山 · 「岳」字帅旗章回卡（每回背后多显一字 精忠报国 还我河山）· 枪缨边角
#          · 八拍「岳母刺字」 · 收复失地六印回顾 · 八拍「十二道金牌」 · 风波亭
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_zhuge as Zg            # engine + helpers (ink layers drawn last)
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
from render_liubang import low_table
from render_caocao import general
from render_zhuge import starfield

F.RIPPLE = False

BORN, DIED = 1103, 1142
END_BEAT = 170
IRON = (70, 74, 80)
BLOOD = (170, 24, 20)
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

DIG = '〇一二三四五六七八九'
def cn_year(y): return ''.join(DIG[int(ch)] for ch in str(y))

# ================================================================ episode look
WM = dict(hook='岳', life='飞', court='忠', night='夜', war='戰', empire='宋', works='征', fate='冤', death='亭', end='岳')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire', 'works'):
    G.THEMES[k]['part'] = 'ash'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (BLOOD, 250, (W * 0.5, 820))
G.THEMES['works']['sun'] = (BLOOD, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (BLOOD, 210, (W * 0.5, 720))
G.THEMES['hook']['tint'] = (0.98, 0.98, 0.98)
G.base_bg.cache_clear()

MTN_COL = {'night': (40, 42, 48), 'death': (56, 56, 60), 'war': (90, 54, 46), 'works': (76, 70, 64)}
def draw_background(t, theme):
    """铁甲: iron-grey ranges."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(160, 160, 164), (110, 112, 118), MTN_COL.get(theme, (66, 70, 78))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """枪缨: a spearhead with a red tassel in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = IRON + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 160, y), fill=col, width=3); d.line((x, y, x, y + sy * 160), fill=col, width=3)
        d.line((x + sx * 14, y + sy * 14, x + sx * 70, y + sy * 70), fill=col, width=4)
        d.polygon([(x + sx * 70, y + sy * 70), (x + sx * 96, y + sy * 84), (x + sx * 84, y + sy * 96)], fill=col)
        for k in range(5):
            d.line((x + sx * 66, y + sy * 66, x + sx * (50 + k * 4), y + sy * (86 - k * 4)), fill=BLOOD + (230,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ 帅旗 chapter card
CH_WORDS = {16: '精', 48: '忠', 80: '报', 112: '国', 144: '还我河山'}
def yue_banner(A, x, base, h, t, p=1.0, layer='red'):
    q = ease_out(p)
    top = base - h * q
    A.d['ink'].line((x, base, x, top), fill=255, width=10)
    A.d['ink'].polygon([(x - 12, top), (x + 12, top), (x, top - 50)], fill=255)
    if q < 0.5: return top
    w = 300 * (q - 0.5) * 2
    pts_t = [(x + i * w / 12, top + 20 + 14 * math.sin(t * 4 + i * 0.6) * i / 12) for i in range(13)]
    pts_b = [(x + i * w / 12, top + 380 + 14 * math.sin(t * 4 + i * 0.6) * i / 12) for i in range(12, -1, -1)]
    A.d[layer].polygon(pts_t + pts_b, fill=255)
    for k in range(6):
        A.d['ink'].line((x + w, top + 30 + k * 60, x + w + 26, top + 50 + k * 60), fill=200, width=4)
    return top

def art_banner_chapter(A, cv, t, u):
    yue_banner(A, 380, 1200, 620, t, p=u / 0.5)
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_banner_chapter)
    if t - s0 > 0.3:
        ink_in(cv, text_img('岳', BRUSH, 220, (250, 240, 228)), 530, 790, t, s0 + 0.3, dur=0.3, settle=1.2)
    w = CH_WORDS.get(c[0], '')
    for i, ch in enumerate(w):
        ink_in(cv, text_img(ch, BRUSH, 110 if len(w) > 1 else 160, INK), 830, 640 + i * 120 if len(w) > 1 else 820, t, s0 + 0.5 + i * 0.12, dur=0.3, settle=1.15)
    ink_in(cv, text_img(no, SERIF, 56, BLOOD, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ primitives
def yuefei(A, x, y, h, dir=1, layer='ink', spear=True, **kw):
    """岳飞: armoured, helmet with red plume, spear."""
    person(A, x, y, h, dir=dir, robe=kw.pop('robe', False), hat='helmet', spear=spear, layer=layer, **kw)
    A.d['red'].line((x, y - 0.99 * h, x - dir * 0.12 * h, y - 1.12 * h), fill=255, width=max(3, int(0.03 * h)))

def jin_rider(A, x, y, s, dir=-1, ph=0.0, layer='mid', moving=True):
    rider(A, x, y, s, dir, ph, layer=layer, spear=True, moving=moving)
    A.d[layer].ellipse((x - dir * 0.05 * s - 0.08 * s, y - 1.38 * s, x - dir * 0.05 * s + 0.08 * s, y - 1.26 * s), fill=255)

def gold_plaque(A, x, y, s, rot=0.0):
    pts = [(-0.5, -1), (0.5, -1), (0.5, 1), (-0.5, 1)]
    A.d['gold'].polygon([rotp((x + a * s, y + b * s), (x, y), rot) for a, b in pts], fill=255)
    A.d['ink'].line([rotp((x + a * s, y + b * s), (x, y), rot) for a, b in pts + [pts[0]]], fill=255, width=3)

# ================================================================ hooks
def art_y_hook_tattoo(A, cv, t, u):
    person(A, 540, GROUND, 360, dir=-1, robe=False, hat='knot', kneel=True, bow=10, arm=40, layer='mid')
    A.flush(cv)
    for i, ch in enumerate('精忠报国'):
        if u > 0.2 + i * 0.25:
            ink_in(cv, text_img(ch, SERIF, 50, BLOOD, 'Black', bleed=False), 560, 1180 + i * 52, t, t - u + 0.2 + i * 0.25, dur=0.2, settle=1.2)

def art_y_hook_jin(A, cv, t, u):
    ground(A, GROUND)
    for k in range(8):
        jin_rider(A, lerp(1100, 620, ease_out(u / (1.6 * P))) + (k % 4) * 110, GROUND - (k // 4) * 50, 110, -1, t * 12 + k, layer='mid')
    yuefei(A, 300, GROUND, 300, dir=1, arm=40, layer='ink')

def art_y_hook_plaques(A, cv, t, u):
    for k in range(int(clamp(u / (1.8 * P)) * 12)):
        x = 160 + (k % 6) * 150; y = 860 + (k // 6) * 260
        gold_plaque(A, x, y, 50, rot=0.1 * math.sin(k))
    ground(A, GROUND)

def art_y_hook_pavilion(A, cv, t, u):
    for k in range(40):
        q = (t * 0.25 + k / 40) % 1
        x = 80 + (k * 23) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    A.d['ink'].polygon([(300, 1060), (780, 1060), (700, 980), (380, 980)], fill=255)
    for x in (360, 720):
        A.d['ink'].rectangle((x - 10, 1060, x + 10, GROUND), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('莫须有', 50, INK), 540, 900, t, t - u + P)

# ================================================================ 第一回 精忠
def art_y_birth(A, cv, t, u):
    A.d['mid'].rectangle((220, 1100, 520, GROUND), fill=255)
    A.d['ink'].polygon([(180, 1110), (560, 1110), (480, 1030), (260, 1030)], fill=255)
    ground(A, GROUND)
    a = t * 1.4
    bx, by = 700 + 120 * math.cos(a), 860 + 40 * math.sin(a)
    crow(A, bx, by, 60, t * 6)
    A.flush(cv)
    stamp(cv, seal('鹏举', 56), 380, 940, t, t - u + P)

def art_y_flood(A, cv, t, u):
    lvl = lerp(GROUND + 30, 1200, ease_out(u / (1.5 * P)))
    A.d['mid'].rectangle((60, lvl, W - 60, GROUND + 30), fill=200)
    waves(A, int(lvl), t, rows=3, amp=12, speed=4)
    A.d['ink'].polygon([(420, lvl + 10), (660, lvl + 10), (640, lvl + 60), (440, lvl + 60)], fill=255)
    A.d['ink'].chord((450, lvl - 60, 630, lvl + 40), 180, 360, fill=255)
    person(A, 540, lvl - 30, 110, dir=1, female=True, baby=True, kneel=True, layer='ink')

def art_y_teacher(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 270, dir=-1, robe=True, hat='knot', arm=lerp(30, 100, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    person(A, 380, GROUND, 230, dir=1, robe=False, hat='knot', arm=100, arm2=90, layer='ink')
    draw = ease_out(u / P)
    A.d['ink'].arc((420, GROUND - 260, 520 + 20 * draw, GROUND - 120), 270, 90, fill=255, width=6)
    q = clamp((u - P) / 0.4)
    if q > 0:
        arrow(A, lerp(520, 960, q), GROUND - 190, 0, 80)
    A.d['red'].ellipse((960, GROUND - 230, 1000, GROUND - 150), fill=255)
    A.flush(cv)
    stamp(cv, seal('周侗', 50, INK), 760, 960, t, t - u + 0.3)

def art_y_bow300(A, cv, t, u):
    ground(A, GROUND)
    pull = ease_out(u / (1.6 * P))
    person(A, 540, GROUND, 300, dir=1, robe=False, hat='knot', arm=95, arm2=lerp(80, 60, pull), layer='ink')
    A.d['ink'].arc((600 - 40 * pull, GROUND - 330, 720 + 40 * pull, GROUND - 120), 270, 90, fill=255, width=10)
    A.d['ink'].line((660, GROUND - 330, 600 - 40 * pull, GROUND - 225), fill=200, width=2)
    A.d['ink'].line((600 - 40 * pull, GROUND - 225, 660, GROUND - 120), fill=200, width=2)
    A.flush(cv)
    paste(cv, text_img('三百斤', SERIF, 70, BLOOD, 'Black', bleed=False), 820, 960, 1, clamp((u - P) / 0.3))

def art_y_jingkang(A, cv, t, u):
    for k in range(34):
        q = (t * 0.3 + k / 34) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    ground(A, GROUND)
    for k in range(2):
        x = walk_x(300 + k * 120, 900 + k * 80, u, 4 * P)
        person(A, x, GROUND, 200, dir=1, hat='crown', bow=30, ph=t * 3 + k, arm=20, layer='ink')
        A.d['ink'].line((x - 30, GROUND - 120, x - 100, GROUND - 120), fill=200, width=3)
    for k in range(3):
        jin_rider(A, walk_x(100 - k * 120, 700 - k * 100, u, 4 * P), GROUND, 150, 1, t * 6 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('靖康之耻', 44, INK), 540, 900, t, t - u + P, rot=-5)

def art_y_tattoo(A, cv, t, u):
    """8-beat set piece: mother pricks 精 忠 报 国 into her son's back, one character every two beats."""
    lantern(A, 200, 900, t, 0, size=22)
    ground(A, GROUND)
    person(A, 600, GROUND, 330, dir=1, robe=False, hat='knot', kneel=True, bow=20, arm=60, layer='mid')
    person(A, 400, GROUND, 280, dir=1, female=True, kneel=True, bow=10, arm=lerp(70, 100, 0.5 + 0.5 * math.sin(t * 10)), layer='ink')
    A.d['ink'].line((480, GROUND - 200, 540, GROUND - 230), fill=255, width=3)
    A.flush(cv)
    for i, ch in enumerate('精忠报国'):
        st = t - u + (0.5 + i * 1.9) * P
        if t >= st:
            ink_in(cv, text_img(ch, SERIF, 64, BLOOD, 'Black', bleed=False), 600, 1080 + i * 70, t, st, dur=0.5, settle=1.0)
    if u > 7.5 * P:
        stamp(cv, seal('岳母', 50, INK), 860, 880, t, t - u + 7.5 * P, rot=6)

def art_y_enlist(A, cv, t, u):
    ground(A, GROUND)
    flag(A, 860, GROUND, 520, t, w=130)
    A.flush(cv)
    stamp(cv, seal('宗', 50), 920, GROUND - 470, t, t - u)
    person(A, 760, GROUND, 260, dir=-1, robe=True, hat='crown', arm=lerp(20, 80, ease_out((u - P) / 0.3)), layer='ink')
    x = walk_x(80, 440, u, 1.5 * P)
    yuefei(A, x, GROUND, 250, dir=1, ph=t * 6 if u < 1.5 * P else None, kneel=u > 2 * P, bow=35 if u > 2 * P else 0, arm=80, spear=False, layer='ink')

# ================================================================ 第二回 岳家军
def art_y_army(A, cv, t, u):
    ground(A, GROUND)
    for r_ in range(3):
        for k in range(9):
            x = 140 + k * 100 + (r_ % 2) * 40; y = GROUND - r_ * 60
            yuefei(A, x, y, 130 - r_ * 14, dir=1, arm=30, layer='ink' if r_ == 0 else 'mid') if False else \
                person(A, x, y, 130 - r_ * 14, dir=1, robe=False, hat='helmet', spear=True, arm=30, layer='ink' if r_ == 0 else 'mid')
    A.flush(cv)
    stamp(cv, seal('岳', 90), 540, 940, t, t - u + 0.3)

def art_y_discipline(A, cv, t, u):
    for k in range(40):
        q = (t * 0.25 + k / 40) % 1
        x = 80 + (k * 23) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    for i, x in enumerate((180, 360, 760, 920)):
        A.d['mid'].rectangle((x - 70, 1150, x + 70, GROUND), fill=255)
        A.d['mid'].polygon([(x - 90, 1150), (x + 90, 1150), (x, 1080)], fill=255)
    ground(A, GROUND)
    for k in range(4):
        person(A, 470 + k * 50, GROUND, 150, dir=1, robe=False, hat='helmet', spear=True, kneel=True, bow=30, arm=40, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('冻死不拆屋 饿死不掳掠', BRUSH, 64, INK), W / 2, 900, t, t - u + P, 0.5)

def art_y_jiankang(A, cv, t, u):
    city_wall(A, 480, W - 60, 1120, gate_x=760, label='建康', open_=ease_out((u - P) / 0.5))
    ground(A, GROUND)
    for k in range(4):
        jin_rider(A, lerp(700, -200, ease_out((u - 0.5) / (2 * P))) - k * 110, GROUND, 130, -1, t * 13 + k, layer='mid')
    yuefei(A, lerp(-100, 380, ease_out(u / (2 * P))), GROUND, 250, dir=1, ph=t * 8, arm=40, layer='ink')

def art_y_xiangyang(A, cv, t, u):
    pts = []
    for j in range(40):
        a = 2 * math.pi * j / 40
        r = 340 + 30 * math.sin(a * 3 + 1)
        pts.append((540 + r * math.cos(a), 1040 + r * math.sin(a) * 0.72))
    A.d['mid'].polygon(pts, fill=110); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    A.flush(cv)
    for i in range(6):
        a = i * math.pi / 3
        x, y = 540 + 220 * math.cos(a), 1040 + 150 * math.sin(a)
        if u > i * 0.35:
            stamp(cv, seal(['襄', '邓', '随', '唐', '郢', '信'][i], 50), x, y, t, t - u + i * 0.35)
    if u > 2.5 * P:
        paste(cv, text_img('襄阳六郡', SERIF, 60, BLOOD, 'Black', bleed=False), W / 2, 1420, 1, clamp((u - 2.5 * P) / 0.3))

def art_y_spear(A, cv, t, u):
    for k in range(10):
        x = (k * 120 - t * 700) % (W + 200) - 100
        A.d['wash'].line((x, 1060 + k * 28, x + 160, 1060 + k * 28), fill=255, width=4)
    ground(A, GROUND)
    x = lerp(-100, 480, ease_out(u / (1.6 * P)))
    rider(A, x, GROUND, 280, 1, t * 15, layer='ink', spear=True)
    A.d['red'].line((x, GROUND - 0.99 * 280 * 0.6 - 180, x - 40, GROUND - 0.99 * 280 * 0.6 - 230), fill=255, width=6)
    for k in range(3):
        fall = ease_out((u - 1.6 * P - k * 0.1) / 0.3) if u > 1.6 * P else 0
        jin_rider(A, 760 + k * 110, GROUND - k * 10, 140, -1, 0.4, layer='mid', moving=False) if fall < 0.5 else \
            person(A, 760 + k * 110, GROUND, 160, dir=-1, robe=False, hat='helmet', fall=80, arm=120, layer='mid')

def art_y_oath(A, cv, t, u):
    A.d['mid'].polygon([(60, GROUND), (60, 1000), (400, 1050), (520, GROUND)], fill=220)
    ground(A, GROUND)
    yuefei(A, 300, 1030, 180, dir=1, arm=lerp(40, 150, ease_out(u / P)), spear=False, layer='ink')
    for k in range(6):
        person(A, 520 + k * 80, GROUND, 150, dir=-1, robe=False, hat='helmet', spear=True, arm=lerp(30, 150, ease_out((u - 0.5 * P) / 0.4)), layer='mid')
    A.flush(cv)
    type_in(cv, text_img('直捣黄龙', BRUSH, 110, BLOOD), W / 2 + 100, 880, t, t - u + P, 0.5)

def art_y_manjiang(A, cv, t, u):
    p = ease_out(u / 0.6)
    w = 760 * p
    x0, x1 = 540 - w / 2, 540 + w / 2
    A.d['mid'].rectangle((x0, 840, x1, 1280), fill=150)
    A.d['ink'].rectangle((x0 - 20, 820, x0, 1300), fill=255); A.d['ink'].rectangle((x1, 820, x1 + 20, 1300), fill=255)
    fo = font(BRUSH, 58)
    for j, col in enumerate(('怒发冲冠', '凭栏处', '潇潇雨歇', '抬望眼', '仰天长啸', '壮怀激烈')):
        for i, ch in enumerate(col):
            x = 800 - j * 100
            if x0 + 20 < x < x1 - 40 and u > 0.3 + (j * 4 + i) * 0.045:
                A.d['ink'].text((x, 870 + i * 64), ch, font=fo, fill=255)

# ================================================================ 第三回 北伐
def art_y_guaizi(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        x = lerp(1100, 640, ease_out(u / (1.5 * P))) + k * 150
        for j in range(3):
            jin_rider(A, x + j * 30, GROUND - j * 20, 120, -1, t * 12 + k, layer='ink' if j == 0 else 'mid')
        A.d['ink'].line((x - 20, GROUND - 160, x + 60, GROUND - 200), fill=255, width=6)
    for k in range(4):
        sx = 200 + k * 90
        person(A, sx, GROUND, 170, dir=1, robe=False, hat='helmet', bow=50, arm=150, layer='ink')
        if u > 2 * P:
            A.d['ink'].line((sx + 30, GROUND - 60, sx + 110, GROUND - 4), fill=255, width=5)
    A.flush(cv)
    if u > 2 * P:
        stamp(cv, seal('专砍马腿', 44), 300, 920, t, t - u + 2 * P, rot=-5)

RECOVER = [('建康', 1130), ('襄阳', 1134), ('郾城', 1140), ('颍昌', 1140), ('洛阳', 1140), ('朱仙镇', 1140)]
def scene_recover(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    idx = int(k - c[0])
    A = Art(); beat_fx(A, t)
    pts = []
    for j in range(48):
        a = 2 * math.pi * j / 48
        r = 370 + 40 * math.sin(a * 3 + 1) + 22 * math.sin(a * 7)
        pts.append((540 + r * math.cos(a), 1040 + r * math.sin(a) * 0.78))
    A.d['mid'].polygon(pts, fill=90); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    A.d['wash'].line([(x, 900 + 40 * math.sin(x * 0.01)) for x in range(180, 900, 10)], fill=255, width=12)
    pos = [(640, 1300), (360, 1200), (520, 1060), (620, 990), (380, 920), (560, 870)]
    for i, (x, y) in enumerate(pos):
        if t >= bt(c[0] + i):
            px, py = pos[i - 1] if i else (760, 1380)
            q = ease_out((t - bt(c[0] + i)) / 0.3)
            A.d['red'].line((px, py, lerp(px, x, q), lerp(py, y, q)), fill=255, width=8)
    A.flush(cv)
    for i, ((nm, yr), (x, y)) in enumerate(zip(RECOVER, pos)):
        if t >= bt(c[0] + i):
            stamp(cv, seal(nm, 40 if len(nm) > 2 else 46, ZHU), x, y, t, bt(c[0] + i) + 0.1)
    if not gather:
        stamp(cv, seal('金', 80, INK), 560, 760, t, s0)
    if 0 <= idx < 6 and not gather:
        nm, yr = RECOVER[idx]
        ink_in(cv, text_img(f'公元{cn_year(yr)}年 · 收复{nm}', SERIF, 50, BLOOD, 'Black', bleed=False, spacing=4), W / 2, 1470, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '收复失地', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '还我河山', BRUSH, 170, BLOOD, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '离汴京只剩四十五里', BRUSH, 90, INK, W / 2, 1470, t, bt(c[0] + 7), stagger=0.05, seed=111)
    fx.flush(cv)

def art_y_yingchang(A, cv, t, u):
    ground(A, GROUND)
    yuefei(A, 300, GROUND, 230, dir=1, arm=150, layer='ink')
    for k in range(5):
        x = lerp(1100, 560, ease_out(u / (2 * P))) + k * 100
        person(A, x, GROUND, 150, dir=-1, robe=False, hat='helmet', ph=t * 10 + k, arm=120, layer='mid')
    A.d['ink'].line((440, GROUND - 240, 520, GROUND - 160), fill=255, width=8)
    A.d['ink'].chord((480, GROUND - 300, 600, GROUND - 180), 270, 450, fill=255)
    A.flush(cv)
    stamp(cv, seal('岳云', 50), 300, 940, t, t - u + P)

def art_y_zhuxian(A, cv, t, u):
    for k in range(3):
        palace(A, 200 + k * 340, 1200, 220, layer='wash')
    A.d['ink'].rectangle((360, 1210, 720, 1250), fill=255)
    ground(A, GROUND)
    for k in range(6):
        person(A, 140 + k * 160, GROUND, 150, dir=1 if k < 3 else -1, robe=True, hat='knot', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='mid')
    yuefei(A, 540, 1210, 160, dir=1, arm=60, layer='ink')
    A.flush(cv)
    paste(cv, text_img('距汴京四十五里', SERIF, 50, BLOOD, 'Black', bleed=False), W / 2, 920, 1, clamp(u / 0.3))

def art_y_hanshan(A, cv, t, u):
    A.d['ink'].polygon([(240, GROUND), (540, 860), (840, GROUND)], fill=255)
    ground(A, GROUND)
    for k in range(6):
        x = 120 + k * 170
        sh = 6 * math.sin(t * 30 + k) * clamp(u / P)
        jin_rider(A, x + sh, GROUND + 20, 90, -1 if x > 540 else 1, 0.3, layer='mid', moving=False)
    A.flush(cv)
    type_in(cv, text_img('撼山易 撼岳家军难', BRUSH, 70, INK), W / 2, 820, t, t - u + P, 0.5)

def art_y_huanglong(A, cv, t, u):
    A.d['mid'].polygon([(560, GROUND), (720, 980), (900, 940), (1020, GROUND)], fill=200)
    city_wall(A, 600, W - 60, 1160, gate_x=820, label='黄龙', layer='wash')
    ground(A, GROUND)
    for k in range(4):
        x = lerp(-100, 380, ease_out(u / (2 * P))) - k * 90
        person(A, x, GROUND, 160, dir=1, robe=False, hat='helmet', spear=True, ph=t * 8 + k, layer='ink')
    for k in range(3):
        lantern(A, 640 + k * 120, 1040, t, k, size=16)

# ================================================================ 第四回 金牌
def art_y_qinhui(A, cv, t, u):
    A.d['wash'].ellipse((760, 640, 880, 760), fill=255)
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    person(A, 360, GROUND, 250, dir=1, robe=True, hat='knot', kneel=True, bow=30, arm=90, layer='ink')
    person(A, 720, GROUND, 250, dir=-1, robe=True, hat='crown', kneel=True, bow=10, arm=60, layer='ink')
    lantern(A, 540, 1100, t, 0, size=20)
    A.flush(cv)
    stamp(cv, seal('秦桧', 54, INK), 360, 940, t, t - u + 0.3)
    stamp(cv, seal('议和', 54), 720, 940, t, t - u + P)

def art_y_plaques(A, cv, t, u):
    """8-beat set piece: twelve gold plaques arrive one after another; the army halts."""
    ph = u / P
    ground(A, GROUND)
    tent(A, 820, GROUND - 10, 360, 300, layer='mid')
    yuefei(A, 820, GROUND, 230, dir=-1, arm=lerp(40, 20, clamp(ph / 8)), bow=lerp(0, 30, clamp(ph / 8)), spear=False, layer='ink')
    n = min(12, int(u / (8 * P / 12)) + 1)
    for k in range(n):
        x = 120 + (k % 4) * 120; y = 860 + (k // 4) * 170
        land = ease_out((u - k * 8 * P / 12) / 0.25)
        gold_plaque(A, x, lerp(620, y, land), 40, rot=0.15 * math.sin(k))
    rx = lerp(-160, 360, ease_out((u % (8 * P / 12)) / 0.4))
    rider(A, rx, GROUND, 140, 1, t * 15, layer='mid')
    A.flush(cv)
    paste(cv, text_img(f'第{cn_num(n)}道', SERIF, 56, BLOOD, 'Black', bleed=False), 300, 1450, 1, 1)
    if ph >= 7:
        stamp(cv, seal('班师', 56), 820, 880, t, t - u + 7 * P, rot=6)

def art_y_farewell(A, cv, t, u):
    ground(A, GROUND)
    for k in range(7):
        person(A, 140 + k * 110, GROUND, 150, dir=1, robe=True, hat='knot', kneel=True, bow=40 + 10 * math.sin(t * 2 + k), arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 2 + k)), layer='mid')
    x = lerp(500, 1000, ease_out(u / (4 * P)))
    rider(A, x, GROUND - 20, 200, 1, t * 5, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('十年之功 废于一旦', BRUSH, 70, INK), W / 2, 880, t, t - u + P, 0.5)

def art_y_bingquan(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 160, dir=-1, hat='crown', arm=lerp(20, 80, ease_out(u / P)), layer='mid')
    yuefei(A, 380, GROUND, 250, dir=1, kneel=True, bow=40, arm=80, spear=False, layer='ink')
    q = ease_out((u - P) / 0.5)
    A.d['red'].rectangle((lerp(470, 600, q) - 20, lerp(GROUND - 160, 1200, q) - 20, lerp(470, 600, q) + 20, lerp(GROUND - 160, 1200, q) + 20), fill=255)
    A.flush(cv)
    stamp(cv, seal('解兵权', 50, INK), 300, 940, t, t - u + 1.5 * P, rot=-5)

def art_y_jail(A, cv, t, u):
    for k in range(7):
        A.d['ink'].line((560 + k * 60, 860, 560 + k * 60, GROUND), fill=255, width=10)
    A.d['ink'].rectangle((540, 840, 960, 860), fill=255)
    yuefei(A, 760, GROUND, 230, dir=-1, kneel=True, bow=20, arm=60, spear=False, layer='mid')
    ground(A, GROUND)
    person(A, 300, GROUND, 250, dir=1, robe=True, hat='crown', arm=lerp(40, 110, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('大理寺', 50, INK), 300, 940, t, t - u + 0.3)

def art_y_moxuyou(A, cv, t, u):
    p = ease_out(u / 0.5)
    A.d['mid'].rectangle((540 - 300 * p, 860, 540 + 300 * p, 1260), fill=200)
    A.d['ink'].rectangle((540 - 300 * p, 860, 540 + 300 * p, 1260), outline=255, width=6)
    A.flush(cv)
    for i, ch in enumerate('莫须有'):
        st = t - u + (0.6 + i * 0.9) * P
        if t >= st:
            ink_in(cv, text_img(ch, BRUSH, 170, INK), 540, 960 + i * 0 + (i - 1) * 0, t, st, dur=0.3, settle=1.3) if False else \
                ink_in(cv, text_img(ch, BRUSH, 150, INK), 360 + i * 180, 1060, t, st, dur=0.3, settle=1.3)
    if u > 3.5 * P:
        paste(cv, text_img('何以服天下', SERIF, 50, BLOOD, 'Black', bleed=False, spacing=6), W / 2, 1400, 1, clamp((u - 3.5 * P) / 0.3))

def art_y_tiantiang(A, cv, t, u):
    for k in range(40):
        q = (t * 0.25 + k / 40) % 1
        x = 80 + (k * 23) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    yuefei(A, 540, GROUND, 230, dir=1, kneel=True, bow=10, arm=lerp(80, 105, 0.5 + 0.5 * math.sin(t * 6)), spear=False, layer='ink')
    A.flush(cv)
    for i, ch in enumerate('天日昭昭'):
        if u > 0.5 + i * 0.6:
            ink_in(cv, text_img(ch, BRUSH, 100, BLOOD), 260 + i * 190, 900, t, t - u + 0.5 + i * 0.6, dur=0.3, settle=1.2)

# ================================================================ 第五回 风波亭
def art_y_pavilion(A, cv, t, u):
    for k in range(40):
        q = (t * 0.25 + k / 40) % 1
        x = 80 + (k * 23) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    A.d['ink'].polygon([(260, 1060), (820, 1060), (740, 960), (340, 960)], fill=255)
    A.d['ink'].polygon([(340, 960), (740, 960), (600, 900), (480, 900)], fill=255)
    for x in (320, 760):
        A.d['ink'].rectangle((x - 10, 1060, x + 10, GROUND), fill=255)
    lt = clamp(1 - (u - 2 * P) / 0.6)
    if lt > 0:
        lantern(A, 540, 1100, t, 0, size=int(22 * lt) + 2)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('除夕之夜 · 年三十九', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 1420, 1, clamp((u - P) / 0.3))

def art_y_yun(A, cv, t, u):
    ground(A, GROUND)
    for i, x in enumerate((380, 700)):
        person(A, x, GROUND, 240 - i * 20, dir=1 if i == 0 else -1, robe=False, hat='helmet', kneel=True, bow=50, arm=60, layer='mid')
    A.flush(cv)
    stamp(cv, seal('岳云', 50, INK), 380, 960, t, t - u + 0.3)
    stamp(cv, seal('张宪', 50, INK), 700, 960, t, t - u + P)

def art_y_wei(A, cv, t, u):
    for k in range(40):
        q = (t * 0.25 + k / 40) % 1
        x = 80 + (k * 23) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    A.d['mid'].polygon([(560, GROUND), (720, 1100), (900, 1060), (1020, GROUND)], fill=220)
    ground(A, GROUND)
    x = walk_x(120, 500, u, 3 * P)
    person(A, x, GROUND, 230, dir=1, robe=True, hat='knot', bow=30, ph=t * 4, arm=100, layer='ink')
    A.d['mid'].rounded_rectangle((x + 20, GROUND - 200, x + 180, GROUND - 150), radius=16, fill=255)
    A.flush(cv)
    stamp(cv, seal('隗顺', 50, INK), 300, 960, t, t - u + P)

def art_y_rehab(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 160, dir=-1, hat='crown', arm=60, layer='mid')
    p = ease_out(u / 0.6)
    A.d['yellow'].rectangle((200, 1100 - 200 * p, 520, 1100 + 100 * p), fill=255)
    A.flush(cv)
    if p > 0.8:
        ink_in(cv, text_img('昭雪', BRUSH, 120, BLOOD), 360, 1060, t, t - u + 0.5, dur=0.3, settle=1.2)
    paste(cv, text_img('二十一年后 · 宋孝宗', SERIF, 44, INK, 'Bold', bleed=False, spacing=4), W / 2, 1420, 1, clamp((u - P) / 0.3))

def art_y_temple(A, cv, t, u):
    palace(A, 540, 1240, 640, layer='mid')
    A.d['ink'].rectangle((420, 1000, 660, 1070), fill=255)
    A.d['ink'].text((444, 1008), '岳王庙', font=font(SERIF, 52, 'Black'), fill=0)
    A.d['wash'].rectangle((60, 1240, W - 60, GROUND + 20), fill=255)
    for i, x in enumerate((360, 480, 600, 720)):
        person(A, x, GROUND, 120, dir=1, kneel=True, bow=60, arm=-30, hat='knot' if i else 'crown', female=i == 1, layer='ink')
    A.flush(cv)
    stamp(cv, seal('跪像', 50, INK), 860, 1180, t, t - u + P)

def art_y_legacy(A, cv, t, u):
    sun(cv, 540, 1050, 260, BLOOD, 120)
    fo = font(BRUSH, 420)
    p = ease_out(u / (1.5 * P))
    tmp = Image.new('L', (W, H), 0)
    ImageDraw.Draw(tmp).text((540 - fo.getlength('忠') / 2, 800), '忠', font=fo, fill=255)
    fld = G.transition_field()
    a = np.asarray(tmp, np.float32) * np.clip((p * 1.3 - fld) / 0.08, 0, 1)
    m = Image.fromarray(a.astype(np.uint8))
    A.im['ink'].paste(m, (0, 0), m)
    ground(A, GROUND)

# ================================================================ script
CHAPTERS = {16: ('第一回', '精忠少年'), 48: ('第二回', '岳家军'), 80: ('第三回', '北伐中原'),
            112: ('第四回', '十二金牌'), 144: ('第五回', '风波亭')}

CARDS = [
    C(0, 2, 'hook', 'num', num='精忠报国', line='母亲刺在背上', art=art_y_hook_tattoo),
    C(2, 4, 'hook', 'num', num='岳家军', line='金兵闻风丧胆', art=art_y_hook_jin),
    C(4, 6, 'hook', 'num', num='十二道金牌', line='一日连发', art=art_y_hook_plaques),
    C(6, 8, 'hook', 'num', num='莫须有', line='三字定冤狱', art=art_y_hook_pavilion),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 精忠少年
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1103, main='生于汤阴', sub='大鸟飞鸣屋上 · 取名飞 字鹏举', note='有大禽若鹄 飞鸣室上 因以为名', art=art_y_birth),
    C(22, 26, 'death', 'card', year=1103, main='黄河决堤', sub='母抱婴儿坐瓮中 · 随水漂流得生', note='母姚氏抱飞坐瓮中 冲涛及岸得免', art=art_y_flood),
    C(26, 30, 'life', 'card', year=1115, main='拜师周侗', sub='学射于名师 · 能左右开弓', note='尽得其术', art=art_y_teacher),
    C(30, 34, 'life', 'card', year=1119, main='神力', sub='未冠 · 挽弓三百斤', note='生有神力 未冠 挽弓三百斤', art=art_y_bow300),
    C(34, 38, 'night', 'card', year=1127, main='靖康之耻', sub='金兵破汴京 · 二帝被掳北去', note='靖康耻 犹未雪 臣子恨 何时灭', art=art_y_jingkang),
    C(38, 46, 'night', 'card', year=1127, main='岳母刺字', sub='民间相传 · 母亲在他背上刺字', note='背有旧涅 精忠报国四大字 深入肤理', art=art_y_tattoo),
    C(46, 48, 'war', 'card', year=1128, main='投奔宗泽', sub='东京留守 · 视为奇才', art=art_y_enlist),
    # ---- 第二回 岳家军
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'war', 'card', year=1130, main='岳家军', sub='自成一军 · 号令严明', note='岳家军 天下精兵', art=art_y_army),
    C(54, 58, 'night', 'card', year=1130, main='军纪如山', sub='宁可冻饿 · 不扰百姓', note='冻死不拆屋 饿死不掳掠', art=art_y_discipline),
    C(58, 62, 'war', 'card', year=1130, main='收复建康', sub='大败金兀术', note='建康 一战而复', art=art_y_jiankang),
    C(62, 66, 'works', 'card', year=1134, main='襄阳六郡', sub='三十二岁 · 一举收复', note='为南宋第一次大规模收复失地', art=art_y_xiangyang),
    C(66, 70, 'war', 'card', year=1135, main='沥泉神枪', sub='单骑冲阵 · 万夫莫当', note='每战 身先士卒', art=art_y_spear),
    C(70, 74, 'empire', 'card', year=1136, main='誓师北伐', sub='直捣黄龙 · 与诸君痛饮', note='直抵黄龙府 与诸君痛饮尔', art=art_y_oath),
    C(74, 80, 'court', 'card', year=1136, main='满江红', sub='怒发冲冠 · 壮怀激烈', note='三十功名尘与土 八千里路云和月', art=art_y_manjiang),
    # ---- 第三回 北伐中原
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'war', 'card', year=1140, main='郾城大捷', sub='大破金军拐子马', note='以麻扎刀入阵 勿仰视 第斫马足', art=art_y_guaizi),
    C(86, 94, 'works', 'recover'),
    C(94, 98, 'war', 'card', year=1140, main='颍昌之战', sub='岳云八战 · 金军大溃', note='人为血人 马为血马', art=art_y_yingchang),
    C(98, 102, 'empire', 'card', year=1140, main='朱仙镇', sub='中原父老 · 箪食壶浆迎王师', note='父老百姓争挽车牵牛', art=art_y_zhuxian),
    C(102, 106, 'war', 'card', year=1140, main='撼山易', sub='金人哀叹', note='撼山易 撼岳家军难', art=art_y_hanshan),
    C(106, 112, 'night', 'card', year=1140, main='直捣黄龙', sub='北岸豪杰 · 约日响应', note='期以克日 与官军会', art=art_y_huanglong),
    # ---- 第四回 十二金牌
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'night', 'card', year=1140, main='秦桧议和', sub='宋高宗一心求和', note='必杀飞 始可和', art=art_y_qinhui),
    C(118, 126, 'fate', 'card', year=1140, main='十二道金牌', sub='一日之内 · 金牌连至', note='一日奉十二金字牌', art=art_y_plaques),
    C(126, 130, 'fate', 'card', year=1140, main='泪别百姓', sub='百姓遮马痛哭', note='十年之力 废于一旦', art=art_y_farewell),
    C(130, 134, 'court', 'card', year=1141, main='解除兵权', sub='明升暗降 · 收归枢密', note='罢为万寿观使', art=art_y_bingquan),
    C(134, 138, 'death', 'card', year=1141, main='下狱', sub='诬以谋反 · 屈打不招', note='袒而示之 背有精忠报国四字', art=art_y_jail),
    C(138, 142, 'fate', 'card', year=1141, main='莫须有', sub='韩世忠质问 · 秦桧答以三字', note='莫须有三字 何以服天下', art=art_y_moxuyou),
    C(142, 144, 'night', 'card', year=1141, main='天日昭昭', sub='狱中供状 · 只书八字', art=art_y_tiantiang),
    # ---- 第五回 风波亭
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'death', 'card', year=1142, main='风波亭', sub='除夕之夜 · 遇害 · 年三十九', note='天日昭昭 天日昭昭', art=art_y_pavilion),
    C(150, 154, 'death', 'card', year=1142, main='父子同死', sub='岳云 张宪同日遇害', note='斩于市', art=art_y_yun),
    C(154, 158, 'night', 'card', year=1142, main='狱卒负尸', sub='隗顺冒死 · 背尸葬于九曲丛祠', note='葬于北山之水滨', art=art_y_wei),
    C(158, 162, 'empire', 'card', year=1162, main='平反昭雪', sub='宋孝宗即位 · 追复原官', note='以礼改葬于西湖栖霞岭', art=art_y_rehab),
    C(162, 166, 'end', 'card', year=1221, main='岳王庙', sub='秦桧夫妇 · 长跪墓前', note='青山有幸埋忠骨 白铁无辜铸佞臣', art=art_y_temple),
    C(166, 170, 'end', 'card', year=1221, main='精忠', sub='一个字 · 刻进了民族的脊梁', note='尽忠报国', art=art_y_legacy),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb, Cc, Zg):
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
for mod in (G, L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb, Cc, Zg):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_year(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=BLOOD + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    def art(A, cv_, t_, u_):
        sun(cv_, 600, 1000, 250, BLOOD, 120)
        ground(A, 1440)
        yuefei(A, 470, 1440, 700, dir=1, arm=lerp(-5, 55, ease_out(u_ / (2 * P))), layer='ink')
    stage(cv, t, c, art)
    fx = Art()
    ink_in(cv, text_img('岳 飞 · 字鹏举', SERIF, 46, BLOOD, 'Black', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '岳飞', BRUSH, 220, INK, W / 2, 450, t, s0, stagger=0.1, seed=77)
    fx.flush(cv)
    stamp(cv, seal('武穆', 66), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元1103 — 1142', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '精忠报国？', BRUSH, 120, BLOOD, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '一片愚忠？', BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    yue_banner(A, 760, 1100, 520, t, p=clamp(u / 0.6), layer='red')
    A.flush(cv, alpha=clamp(u / 0.6) * 0.3)
    fx = Art()
    chars_in(cv, fx, '还我河山', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('鹏举', 60), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('他离收复汴京 · 只差四十五里', SERIF, 46, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.4)
    type_in(cv, text_img('却倒在了自己人的刀下', SERIF, 54, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '若他不班师', BRUSH, 100, BLOOD, W / 2, 1190, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('历史会改写吗？评论区说说', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=BLOOD + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(252, 240, 226, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=INK + (220,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 文天祥', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, recover=scene_recover, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第拾肆集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 570, 170, 1, 1)
    if t < bt(8):
        q = text_img('打得金兵闻风丧胆 · 为何死于自己人？', SERIF, 38, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 330, 335, W / 2 + 330, 335), fill=BLOOD + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, BLOOD, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=BLOOD + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=INK + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(max(1, int(round(yr - BORN)))) + '岁' if yr <= DIED + 0.5 else '身后'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=BLOOD + (255,))
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
