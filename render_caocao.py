# 千古人物志 · 第拾贰集 · 魏武帝曹操 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈，墨色最后绘制）。每一幕画面均为本集新画，不重复。
# 本集特色：建安青铜 —— 铜绿玄黑 · 青铜爵章回卡（对酒当歌 每回酒满一分）· 铜雀边角
#          · 煮酒论英雄 · 八拍「官渡 火烧乌巢」 · 统一北方六印回顾 · 八拍「赤壁」
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_liubang as Lb          # engine + helpers (ink layers drawn last)
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
from render_songtaizu import tent, campfire
from render_mingtaizu import big_ship
from render_liubang import low_table

F.RIPPLE = False

BORN, DIED = 155, 220               # 公元
END_BEAT = 170
BRONZE = (52, 120, 104)             # 铜绿
S.LAYERS.append(('bronze', BRONZE, 0.82, 1.3))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

# ================================================================ episode look
WM = dict(hook='魏', life='德', court='相', night='夜', war='戰', empire='魏', works='北', fate='歌', death='陵', end='操')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire', 'works'):
    G.THEMES[k]['part'] = 'patina'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['empire']['sun'] = (BRONZE, 260, (W * 0.5, 820))
G.THEMES['works']['sun'] = ((150, 130, 90), 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (BRONZE, 210, (W * 0.5, 720))
G.THEMES['hook']['tint'] = (0.97, 1.0, 0.99)
G.base_bg.cache_clear()

MTN_COL = {'night': (40, 48, 50), 'death': (60, 62, 62), 'war': (96, 60, 44), 'works': (90, 84, 64)}
def draw_background(t, theme):
    """建安青铜: patina-green ranges over ink."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(140, 168, 156), (86, 120, 108), MTN_COL.get(theme, (44, 80, 70))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'patina':
        return Lb.particle_sprite(kind, q)
    s = 36
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [BRONZE, (90, 150, 130), (40, 70, 60)][q]
    d.polygon([(10, 20), (18, 10), (28, 16), (24, 28), (12, 26)], fill=col + (200,))
    return im.filter(ImageFilter.GaussianBlur(0.7))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """铜雀: a small bronze sparrow perched on each corner rule."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = BRONZE + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 160, y), fill=col, width=3); d.line((x, y, x, y + sy * 160), fill=col, width=3)
        bx, by = x + sx * 50, y + sy * 22
        d.ellipse((bx - 14, by - 8, bx + 14, by + 8), fill=col)
        d.ellipse((bx + sx * 10 - 7, by - 16, bx + sx * 10 + 7, by - 2), fill=col)
        d.polygon([(bx - sx * 12, by), (bx - sx * 30, by - 10), (bx - sx * 26, by + 4)], fill=col)
        d.polygon([(bx + sx * 16, by - 10), (bx + sx * 24, by - 8), (bx + sx * 16, by - 5)], fill=ZHU + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ 青铜爵 chapter card
CH_LEVEL = {16: 0.2, 48: 0.4, 80: 0.6, 112: 0.8, 144: 1.0}
def jue(A, cx, base, s, fill_=0.0, p=1.0, t=0.0):
    """Bronze 爵: tripod wine vessel with a long spout and two capped posts."""
    q = ease_out(p)
    if q <= 0.02: return
    top = base - s * 1.05
    body = [(cx - s * 0.32, top + s * 0.25), (cx + s * 0.32, top + s * 0.25), (cx + s * 0.26, base - s * 0.35), (cx - s * 0.26, base - s * 0.35)]
    A.d['bronze'].polygon(body, fill=int(230 * q))
    A.d['ink'].line(body + [body[0]], fill=255, width=6)
    A.d['ink'].polygon([(cx - s * 0.32, top + s * 0.25), (cx - s * 0.95, top + s * 0.05), (cx - s * 0.9, top + s * 0.16), (cx - s * 0.3, top + s * 0.35)], fill=255)
    A.d['ink'].polygon([(cx + s * 0.32, top + s * 0.25), (cx + s * 0.62, top + s * 0.08), (cx + s * 0.6, top + s * 0.18), (cx + s * 0.3, top + s * 0.35)], fill=255)
    for dx in (-0.12, 0.12):
        A.d['ink'].line((cx + dx * s, top + s * 0.25, cx + dx * s, top), fill=255, width=7)
        A.d['ink'].ellipse((cx + dx * s - 14, top - 18, cx + dx * s + 14, top + 2), fill=255)
    for dx in (-0.24, 0.0, 0.24):
        A.d['ink'].line((cx + dx * s, base - s * 0.35, cx + dx * s * 1.5, base), fill=255, width=8)
    for k in range(3):
        y = top + s * (0.42 + k * 0.12)
        A.d['ink'].line((cx - s * 0.28, y, cx + s * 0.28, y), fill=150, width=3)
    if fill_ > 0:
        lvl = top + s * 0.32
        A.d['red'].ellipse((cx - s * 0.3, lvl - 10 + 3 * math.sin(t * 3), cx + s * 0.3, lvl + 10), fill=int(220 * fill_))
        for k in range(int(fill_ * 5)):
            yy = top - 30 - k * 28 - (t * 40 % 28)
            A.d['wash'].arc((cx - 20 + k * 6, yy - 12, cx + 20 + k * 6, yy + 12), 200, 340, fill=200, width=3)

def art_jue_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    jue(A, 540, 1180, 420, fill_=CH_LEVEL.get(kb, 0.2) * clamp(u / 0.8), p=u / 0.4, t=t)
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_jue_chapter)
    ink_in(cv, text_img(no, SERIF, 56, BRONZE, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ primitives
def general(A, x, y, h, dir=1, layer='ink', **kw):
    person(A, x, y, h, dir=dir, robe=kw.pop('robe', False), hat='helmet', layer=layer, **kw)

def lord(A, x, y, h, dir=1, layer='ink', **kw):
    """Cao Cao figure: robe + tall official cap with a crimson plume."""
    person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, **kw)
    A.d[layer].rectangle((x - 0.06 * h, y - 1.06 * h, x + 0.06 * h, y - 0.94 * h), fill=255)
    A.d['red'].line((x, y - 1.06 * h, x - dir * 0.12 * h, y - 1.18 * h), fill=255, width=max(3, int(0.03 * h)))

def granary(A, x, base, w, layer='mid'):
    A.d[layer].rectangle((x - w / 2, base - w * 0.7, x + w / 2, base), fill=255)
    A.d[layer].polygon([(x - w * 0.6, base - w * 0.7), (x + w * 0.6, base - w * 0.7), (x, base - w * 1.1)], fill=255)

def bronze_sparrow(A, x, y, s, layer='bronze'):
    A.d[layer].ellipse((x - s, y - s * 0.5, x + s, y + s * 0.5), fill=255)
    A.d[layer].ellipse((x + s * 0.6, y - s * 0.95, x + s * 1.1, y - s * 0.35), fill=255)
    A.d[layer].polygon([(x - s * 0.8, y), (x - s * 2, y - s * 0.6), (x - s * 1.8, y + s * 0.3)], fill=255)
    A.d[layer].polygon([(x - s * 0.2, y - s * 0.3), (x - s * 0.4, y - s * 1.4), (x + s * 0.3, y - s * 0.4)], fill=255)

# ================================================================ hooks
def art_c_hook_ning(A, cv, t, u):
    stars = random.Random(2)
    for k in range(20):
        x = stars.uniform(80, 1000); y = stars.uniform(620, 960)
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=255)
    ground(A, GROUND)
    A.d['mid'].rectangle((620, 1100, 960, GROUND), fill=200)
    A.d['ink'].polygon([(580, 1110), (1000, 1110), (900, 1030), (680, 1030)], fill=255)
    lord(A, 380, GROUND, 280, dir=1, arm=lerp(40, 120, ease_out(u / P)), sword=lerp(40, 120, ease_out(u / P)), layer='ink')

def art_c_hook_emperor(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 160, dir=-1, hat='crown', arm=20, layer='mid')
    lord(A, 400, GROUND, 330, dir=1, arm=lerp(20, 70, ease_out(u / P)), layer='ink')
    A.d['ink'].line((440, GROUND - 240, 700, 1190), fill=200, width=3)

def art_c_hook_guandu(A, cv, t, u):
    ground(A, GROUND)
    for k in range(9):
        rider(A, 640 + (k % 3) * 120, GROUND - (k // 3) * 40, 100, -1, 0.5, layer='mid', moving=False)
    for k in range(3):
        rider(A, lerp(-100, 300, ease_out(u / (1.4 * P))) - k * 110, GROUND, 150, 1, t * 13 + k, layer='ink', spear=True)
    A.flush(cv)
    paste(cv, text_img('二万 对 十万', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 960, 1, clamp(u / 0.3))

def art_c_hook_fire(A, cv, t, u):
    A.d['wash'].rectangle((60, 1150, W - 60, 1380), fill=150)
    waves(A, 1160, t, rows=4, amp=8, speed=2)
    for k, x in enumerate((260, 540, 820)):
        big_ship(A, x, 1200, 110, t, layer='ink', burn=clamp(u / (1.4 * P) - k * 0.1))

# ================================================================ 第一回 乱世奸雄
def art_c_birth(A, cv, t, u):
    A.d['mid'].rectangle((240, 1050, 840, GROUND), fill=200)
    A.d['ink'].polygon([(200, 1060), (880, 1060), (780, 960), (300, 960)], fill=255)
    rect(A, 'wash', 480, 1150, 600, GROUND, fill=0)
    for k in range(3):
        lantern(A, 300 + k * 240, 1000, t, k, size=20)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('谯县', 54), 540, 880, t, t - u + P)

def art_c_hawk(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        a = t * 1.4 + k * 2.1
        crow(A, 540 + 300 * math.cos(a), 840 + 80 * math.sin(a), 30, t * 9 + k)
    for k in range(2):
        x = (t * 260 + k * 400) % (W + 300) - 150
        A.d['ink'].ellipse((x - 50, GROUND - 60, x + 50, GROUND - 20), fill=255)
        A.d['ink'].line((x + 40, GROUND - 50, x + 70, GROUND - 80), fill=255, width=8)
    rider(A, lerp(100, 440, ease_out(u / (2 * P))), GROUND, 220, 1, t * 12, layer='ink')

def art_c_palsy(A, cv, t, u):
    ground(A, GROUND)
    fake = u < 2 * P
    if fake:
        person(A, 400, GROUND, 230, dir=1, robe=True, hat='knot', kneel=True, bow=0, fall=-60, arm=30, layer='ink')
    else:
        person(A, 400, GROUND, 230, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    person(A, 760, GROUND, 260, dir=-1, robe=True, hat='knot', arm=lerp(30, 110, ease_out((u - 0.4) / 0.4)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('中风' if fake else '无恙', 56, ZHU if fake else INK), 400, 960, t, t - u + (0.4 if fake else 2 * P), rot=-5)

def art_c_yuedan(A, cv, t, u):
    ground(A, GROUND)
    person(A, 720, GROUND, 270, dir=-1, robe=True, hat='knot', kneel=True, bow=10, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    lord(A, 380, GROUND, 260, dir=1, kneel=True, bow=20, arm=60, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('治世之能臣', BRUSH, 80, INK), W / 2, 880, t, t - u + P, 0.4)
    type_in(cv, text_img('乱世之奸雄', BRUSH, 80, ZHU), W / 2, 1000, t, t - u + 2 * P, 0.4)

def art_c_rods(A, cv, t, u):
    city_wall(A, 520, W - 60, 1140, gate_x=780, label='北部尉', open_=0.0)
    ground(A, GROUND)
    for k in range(5):
        x = 140 + k * 70
        A.d['red' if k % 2 else 'bronze'].rectangle((x - 8, GROUND - 260, x + 8, GROUND), fill=255)
    fall = -70 * ease_out((u - P) / 0.4) if u > P else 0
    person(A, 600, GROUND, 230, dir=-1, robe=True, hat='crown', fall=-fall, arm=40, layer='mid')
    lord(A, 480, GROUND, 250, dir=1, arm=lerp(160, 70, ease_expo((u - 0.8 * P) / 0.2)), layer='ink')
    A.d['red'].line((520, GROUND - 200, 600, GROUND - 300 + 100 * ease_expo((u - 0.8 * P) / 0.2)), fill=255, width=12)

def art_c_dagger(A, cv, t, u):
    A.d['mid'].rectangle((560, 1180, 960, 1220), fill=255)
    person(A, 760, 1180, 150, dir=-1, robe=True, hat='crown', kneel=True, bow=-10, arm=20, fall=-30, layer='mid')
    ground(A, GROUND)
    turn = u > 1.5 * P
    lord(A, 420, GROUND, 260, dir=1, kneel=turn, bow=40 if turn else 0, arm=80 if turn else 100, layer='ink')
    A.d['ink'].line((500, GROUND - (100 if turn else 190), 600, GROUND - (90 if turn else 210)), fill=255, width=6)
    A.flush(cv)
    if turn:
        stamp(cv, seal('献刀', 56), 300, 960, t, t - u + 1.5 * P, rot=-6)

def art_c_flee(A, cv, t, u):
    A.d['wash'].ellipse((780, 640, 900, 760), fill=255)
    ground(A, GROUND)
    for k in range(10):
        x = (k * 120 - t * 800) % (W + 200) - 100
        A.d['wash'].line((x, 1060 + k * 28, x + 160, 1060 + k * 28), fill=255, width=4)
    x = lerp(200, 560, ease_out(u / (2 * P)))
    rider(A, x, GROUND, 240, 1, t * 15, layer='ink')
    rider(A, x - 260, GROUND, 200, 1, t * 15 + 1, layer='mid')
    A.flush(cv)
    stamp(cv, seal('宁我负人', 44, INK), 860, 960, t, t - u + 2 * P, rot=5)

def art_c_jiaozhao(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        p = ease_out((u - k * 0.1) / 0.4)
        flag(A, 90 + k * 100, GROUND, 260 * p, t + k, w=70, layer='red' if k % 2 else 'bronze')
    lord(A, 540, GROUND, 300, dir=1, arm=150, layer='ink')
    A.d['yellow'].rectangle((580, GROUND - 400, 700, GROUND - 330), fill=255)

# ================================================================ 第二回 挟天子
def art_c_bianshui(A, cv, t, u):
    A.d['wash'].rectangle((60, 1250, W - 60, 1380), fill=160)
    waves(A, 1260, t, rows=3, amp=7, speed=2.5)
    ground(A, 1250)
    for k in range(4):
        x = lerp(1000, 640, ease_out(u / (2 * P))) + k * 90
        rider(A, x, 1250, 150, -1, t * 13 + k, layer='mid', spear=True)
    q = ease_out((u - P) / 0.5)
    lord(A, 400, 1250, 230, dir=1, fall=-60 * q, arm=100, layer='ink')
    if u > 2 * P:
        general(A, 300, 1250, 220, dir=1, arm=60, layer='ink')
        A.flush(cv)
        stamp(cv, seal('曹洪让马', 44), 300, 960, t, t - u + 2 * P, rot=-5)

def art_c_qingzhou(A, cv, t, u):
    ground(A, GROUND)
    for r_ in range(3):
        for k in range(8):
            x = 160 + k * 105; y = GROUND - r_ * 60
            joined = ease_out((u - 0.3 - r_ * 0.2) / 0.5)
            person(A, x, y, 110 - r_ * 10, dir=1, robe=False, hat='helmet' if joined > 0.5 else 'knot', spear=joined > 0.5, arm=30, layer='ink' if r_ == 0 else 'mid')
    A.flush(cv)
    stamp(cv, seal('青州兵', 56), 540, 900, t, t - u + 1.5 * P)

def art_c_tuntian(A, cv, t, u):
    sun(cv, 820, 860, 110, (190, 150, 70), 110)
    for r_ in range(4):
        y = 1230 + r_ * 50
        A.d['mid'].line((60, y, W - 60, y), fill=255, width=3)
        for x in range(90, W - 60, 60):
            g = clamp(u / (2.5 * P)) * (30 + r_ * 4)
            A.d['grass'].line((x, y, x + 4 * math.sin(t * 2 + x), y - g), fill=255, width=3)
    for k in range(3):
        general(A, 200 + k * 300, 1260 + k * 30, 170, dir=1, bow=lerp(30, 55, 0.5 + 0.5 * math.sin(t * 3 + k)), arm=120, layer='ink')
    granary(A, 900, 1220, 110)

def art_c_xuchang(A, cv, t, u):
    city_wall(A, 560, W - 60, 1140, gate_x=800, label='许都', open_=1.0)
    ground(A, GROUND)
    x = lerp(-100, 520, ease_out(u / (3 * P)))
    carriage(A, x, GROUND, 170, dir=1, wheel=t * 5, ph=t * 9, canopy=True)
    A.d['yellow'].chord((x - 110, GROUND - 230, x + 90, GROUND - 130), 180, 360, fill=255)
    lord(A, x - 300, GROUND, 230, dir=1, ph=t * 6, arm=30, layer='ink')

def art_c_plum(A, cv, t, u):
    sun(cv, 820, 860, 120, ZHU, 130)
    ground(A, GROUND)
    for k in range(6):
        general(A, 160 + k * 110, GROUND, 160, dir=1, bow=40 - 30 * ease_out((u - P) / 0.5), arm=20, ph=t * 3 + k, layer='mid')
    lord(A, 860, GROUND, 260, dir=-1, arm=150, layer='ink')
    for k in range(6):
        bx, by = 300 + k * 80, 860 + 20 * math.sin(k)
        A.d['red'].ellipse((bx - 14, by - 14, bx + 14, by + 14), fill=int(200 * clamp((u - P) / 0.4)))
    A.flush(cv)
    stamp(cv, seal('望梅', 54), 540, 760, t, t - u + P)

def art_c_wine(A, cv, t, u):
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    A.d['ink'].chord((480, 1180, 600, 1260), 180, 360, fill=255)
    for k in range(4):
        a = t * 2 + k
        A.d['wash'].arc((500 + k * 10, 1120 - 20 * math.sin(a), 540 + k * 10, 1160), 200, 340, fill=200, width=3)
    lord(A, 240, GROUND, 250, dir=1, kneel=True, bow=0, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    thunder = u > 2 * P
    person(A, 840, GROUND, 240, dir=-1, robe=True, hat='knot', kneel=True, bow=50 if thunder else 10, arm=60, layer='ink')
    if thunder:
        v = u - 2 * P
        A.d['wash'].line((700, 620, 760, 760, 720, 780, 800, 960), fill=int(255 * clamp(1 - v / 0.5)), width=10)
        for k in range(2):
            A.d['ink'].line((760 + k * 10, GROUND - 160 + v * 80, 790 + k * 10, GROUND - 120 + v * 80), fill=255, width=3)
    A.flush(cv)
    type_in(cv, text_img('天下英雄 唯使君与操耳', BRUSH, 60, INK), W / 2, 880, t, t - u + P, 0.5)

def art_c_lvbu(A, cv, t, u):
    A.d['mid'].rectangle((560, 900, 960, GROUND), fill=200)
    A.d['ink'].polygon([(520, 910), (1000, 910), (900, 830), (620, 830)], fill=255)
    A.d['ink'].rectangle((700, 860, 820, 900), fill=255)
    A.d['ink'].text((712, 864), '白门楼', font=font(SERIF, 30, 'Black'), fill=0)
    ground(A, GROUND)
    general(A, 440, GROUND, 290, dir=1, kneel=True, bow=10, arm=-20, layer='ink')
    for k in range(3):
        A.d['ink'].line((390, GROUND - 200 + k * 30, 500, GROUND - 200 + k * 30), fill=200, width=4)
    lord(A, 800, GROUND, 260, dir=-1, arm=lerp(30, 100, ease_out((u - 2 * P) / 0.3)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('缚虎', 54, INK), 440, 940, t, t - u + P)

# ================================================================ 第三回 官渡之战
def art_c_yanliang(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        rider(A, 620 + (k % 3) * 120, GROUND - (k // 3) * 50, 110, -1, 0.5, layer='mid', spear=True, moving=False)
    q = ease_out(u / (1.5 * P))
    x = lerp(-150, 560, q)
    rider(A, x, GROUND, 250, 1, t * 15, layer='ink', spear=False)
    A.d['ink'].line((x + 40, GROUND - 330, x + 200, GROUND - 450), fill=255, width=8)
    A.d['ink'].chord((x + 170, GROUND - 500, x + 250, GROUND - 420), 270, 450, fill=255)
    A.d['red'].line((x + 10, GROUND - 330, x + 20, GROUND - 200), fill=255, width=10)
    A.flush(cv)
    if u > 1.5 * P:
        stamp(cv, seal('关羽', 56), 860, 940, t, t - u + 1.5 * P, rot=6)

def art_c_guanyu_leave(A, cv, t, u):
    sun(cv, 820, 900, 120, ZHU, 110)
    ground(A, GROUND)
    x = lerp(400, 1000, ease_out(u / (4 * P)))
    rider(A, x, GROUND, 200, 1, t * 10, layer='ink')
    A.d['red'].polygon([(x - 80, GROUND - 260), (x - 200, GROUND - 220 + 10 * math.sin(t * 6)), (x - 80, GROUND - 200)], fill=255)
    lord(A, 240, GROUND, 260, dir=1, arm=lerp(30, 110, ease_out(u / P)), layer='ink')
    A.d['red'].rectangle((300, GROUND - 250, 380, GROUND - 230), fill=255)

def art_c_guandu(A, cv, t, u):
    """8-beat set piece: two camps face off → 许攸 defects → night ride → 乌巢 burns → Yuan army breaks."""
    ph = u / P
    A.d['wash'].ellipse((760, 640, 880, 760), fill=255)
    ground(A, GROUND)
    if ph < 3:
        for i, x in enumerate((200, 330)):
            tent(A, x, GROUND - 10, 220, 200, layer='mid')
        for i in range(5):
            tent(A, 620 + i * 90, GROUND - 10, 150, 140, layer='mid')
        if ph >= 1:
            q = ease_out((u - P) / (1.5 * P))
            person(A, lerp(700, 440, q), GROUND, 190, dir=-1, robe=True, hat='knot', ph=t * 6, arm=30, layer='ink')
            lord(A, 320, GROUND, 230, dir=1, arm=lerp(30, 120, q), layer='ink')
    elif ph < 5:
        v = u - 3 * P
        for i in range(4):
            granary(A, 560 + i * 130, GROUND - 10, 110)
        for k in range(5):
            x = lerp(-100, 420, ease_out(v / (1.5 * P))) - k * 110
            rider(A, x, GROUND - (k % 2) * 8, 140, 1, t * 14 + k, layer='ink', spear=True)
            flames(A, x + 40, GROUND - 300, 30, 50, t + k, n=2, seed=k, smoke=False)
    else:
        v = u - 5 * P
        for i in range(4):
            granary(A, 560 + i * 130, GROUND - 10, 110)
            flames(A, 560 + i * 130, GROUND - 40, 160, 240 * ease_out((v - i * 0.08) / 0.5), t + i, n=4, seed=30 + i, smoke=True)
        for k in range(5):
            person(A, lerp(500, -100, ease_out(v / (2 * P))) - k * 80, GROUND, 140, dir=-1, robe=False, hat='helmet', ph=t * 12 + k, arm=140, layer='mid')
    A.flush(cv)
    if ph >= 1.2 and ph < 3:
        stamp(cv, seal('许攸', 50, INK), 700, 940, t, t - u + 1.2 * P)
    if ph >= 5:
        stamp(cv, seal('乌巢', 56), 860, 880, t, t - u + 5 * P, rot=6)
    if ph >= 6.6:
        stamp(cv, seal('以少胜多', 44), 260, 880, t, t - u + 6.6 * P, rot=-6)

NORTH = [('吕布', 198), ('袁术', 199), ('袁绍', 200), ('袁谭', 205), ('乌桓', 207), ('辽东', 207)]
def scene_north(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    idx = int(k - c[0])
    A = Art(); beat_fx(A, t)
    pts = []
    for j in range(48):
        a = 2 * math.pi * j / 48
        r = 360 + 40 * math.sin(a * 3 + 1) + 22 * math.sin(a * 7)
        pts.append((540 + r * math.cos(a), 1040 + r * math.sin(a) * 0.72))
    A.d['bronze'].polygon(pts, fill=90); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    A.d['wash'].line([(x, 1200 + 30 * math.sin(x * 0.01)) for x in range(180, 900, 10)], fill=255, width=12)
    pos = [(360, 1150), (560, 1210), (520, 900), (720, 860), (880, 780), (960, 900)]
    for i, (x, y) in enumerate(pos):
        p = ease_out((t - bt(c[0] + i)) / 0.3)
        if p > 0:
            A.d['red'].line((540, 1040, lerp(540, x, p), lerp(1040, y, p)), fill=255, width=8)
    A.flush(cv)
    stamp(cv, seal('曹', 100 if not gather else 220), 540, 1040, t, s0 if not gather else gather_t)
    for i, ((nm, yr), (x, y)) in enumerate(zip(NORTH, pos)):
        if t >= bt(c[0] + i) and not gather:
            stamp(cv, seal(nm, 44, INK), x, y, t, bt(c[0] + i) + 0.12)
    if 0 <= idx < 6 and not gather:
        nm, yr = NORTH[idx]
        ink_in(cv, text_img(f'公元{cn_num(yr)}年 · 平{nm}', SERIF, 50, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1460, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '扫平群雄', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '统一北方', BRUSH, 170, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '三分天下有其二', BRUSH, 100, BRONZE, W / 2, 1460, t, bt(c[0] + 7), stagger=0.06, seed=111)
    fx.flush(cv)

def art_c_jieshi(A, cv, t, u):
    A.d['wash'].rectangle((60, 1150, W - 60, 1380), fill=150)
    waves(A, 1160, t, rows=5, amp=12, speed=2.5)
    A.d['ink'].polygon([(60, 1160), (60, 900), (260, 860), (380, 980), (420, 1160)], fill=255)
    lord(A, 240, 870, 160, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    sun(cv, 780, lerp(1150, 980, ease_out(u / (3 * P))), 110, ZHU, 140)
    A.flush(cv)
    type_in(cv, text_img('东临碣石 以观沧海', BRUSH, 66, INK), W / 2 + 60, 820, t, t - u + P, 0.6)

# ================================================================ 第四回 赤壁
def art_c_jingzhou(A, cv, t, u):
    city_wall(A, 560, W - 60, 1120, gate_x=800, label='襄阳', open_=ease_out((u - 0.6) / 0.5))
    ground(A, GROUND)
    for k in range(6):
        x = walk_x(-100 - k * 110, 520 - k * 90, u, 2.5 * P)
        general(A, x, GROUND - (k % 2) * 10, 170, dir=1, spear=True, ph=t * 8 + k, layer='ink' if k % 2 == 0 else 'mid')
    A.flush(cv)
    stamp(cv, seal('刘琮降', 50, INK), 800, 940, t, t - u + 1.5 * P, rot=5)

def art_c_changban(A, cv, t, u):
    A.d['ink'].rectangle((200, 1220, 880, 1240), fill=255)
    for x in (260, 540, 820):
        A.d['ink'].rectangle((x - 10, 1240, x + 10, GROUND), fill=255)
    A.d['wash'].rectangle((60, 1300, W - 60, 1380), fill=160)
    waves(A, 1310, t, rows=2, amp=5, speed=2)
    rider(A, 540, 1220, 220, -1, 0.3, layer='ink', moving=False, spear=True)
    for k in range(6):
        rider(A, 900 + k * 50 if k < 3 else 120 + (k - 3) * 60, 1220, 110, -1 if k < 3 else 1, 0.4, layer='mid', moving=False)
    A.flush(cv)
    stamp(cv, seal('张飞', 54), 540, 900, t, t - u + P)

def art_c_chain(A, cv, t, u):
    A.d['wash'].rectangle((60, 1150, W - 60, 1380), fill=150)
    waves(A, 1160, t, rows=4, amp=6, speed=1.5)
    n = int(clamp(u / (2 * P)) * 4) + 1
    xs = [180, 420, 660, 900][:n]
    for x in xs:
        big_ship(A, x, 1210, 110, t * 0.3, layer='ink')
    for a_, b_ in zip(xs, xs[1:]):
        A.d['ink'].line((a_ + 110, 1200, b_ - 110, 1200), fill=255, width=6)
    lord(A, 420, 1060, 110, dir=1, arm=120, layer='ink')

def art_c_eastwind(A, cv, t, u):
    for k in range(10):
        y = 720 + k * 60
        x = (t * 600 + k * 190) % (W + 400) - 200
        A.d['wash'].line((x, y, x + 260 * ease_out(u / P), y - 30), fill=255, width=6)
    ground(A, GROUND)
    A.d['ink'].polygon([(380, GROUND), (700, GROUND), (660, 1180), (420, 1180)], fill=255)
    person(A, 540, 1180, 220, dir=1, robe=True, hat='knot', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    for k in range(7):
        a = math.pi + k * math.pi / 6
        flag(A, 540 + 250 * math.cos(a), 1180, 130, t * 1.5 + k, w=60)

def art_c_chibi(A, cv, t, u):
    """8-beat set piece: the chained fleet → wind rises → fire boats → the river burns → retreat."""
    ph = u / P
    A.d['wash'].rectangle((60, 1100, W - 60, 1380), fill=150)
    waves(A, 1110, t, rows=5, amp=10, speed=2.5)
    A.d['mid'].polygon([(60, 1100), (60, 760), (240, 820), (320, 1100)], fill=220)
    A.d['red'].text((120, 860), '赤壁', font=font(BRUSH, 64), fill=200)
    burn = ease_out((u - 4 * P) / (2.5 * P)) if ph > 4 else 0
    xs = [420, 640, 860]
    for i, x in enumerate(xs):
        big_ship(A, x, 1160, 110, t, layer='ink', burn=clamp(burn * 1.2 - i * 0.15))
    for a_, b_ in zip(xs, xs[1:]):
        A.d['ink'].line((a_ + 110, 1150, b_ - 110, 1150), fill=255, width=5)
    if ph >= 1.5:
        w = ease_out((u - 1.5 * P) / 0.6)
        for k in range(8):
            y = 760 + k * 36
            x = (t * 600 + k * 170) % (W + 400) - 200
            A.d['wash'].line((x, y, x + 220 * w, y - 20), fill=255, width=6)
    if ph >= 2.5:
        for k in range(4):
            fx = lerp(220 - k * 60, 400 + k * 150, ease_out((u - 2.5 * P - k * 0.08) / (1.6 * P)))
            fy = 1290 + (k % 2) * 30
            A.d['mid'].polygon([(fx - 50, fy - 10), (fx + 50, fy - 10), (fx + 40, fy + 20), (fx - 40, fy + 20)], fill=255)
            flames(A, fx, fy - 10, 90, 110, t + k, n=3, seed=60 + k, smoke=False)
    A.flush(cv)
    if ph >= 1.5:
        stamp(cv, seal('东风', 54, INK), 860, 800, t, t - u + 1.5 * P, rot=6)
    if ph >= 6.5:
        stamp(cv, seal('火烧赤壁', 46), 300, 1460, t, t - u + 6.5 * P, rot=-5)

def art_c_huarong(A, cv, t, u):
    for k in range(40):
        q = (t * 1.0 + k / 40) % 1
        x = 80 + (k * 29) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 8, y + 36), fill=200, width=2)
    A.d['mid'].polygon([(60, GROUND), (60, 900), (360, 980), (420, GROUND)], fill=200)
    A.d['mid'].polygon([(W - 60, GROUND), (W - 60, 900), (720, 980), (660, GROUND)], fill=200)
    ground(A, GROUND)
    for k in range(4):
        lord(A, lerp(480, 620, ease_out(u / (3 * P))) - k * 70, GROUND, 170 - k * 10, dir=1, bow=30, arm=20, ph=t * 4 + k, layer='ink' if k == 0 else 'mid')
    if u > 2 * P:
        rider(A, 820, GROUND, 200, -1, 0.3, layer='ink', moving=False)
        A.flush(cv)
        stamp(cv, seal('义释', 54), 820, 940, t, t - u + 2 * P, rot=5)

def art_c_tongguan(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        x = (k * 120 - t * 900) % (W + 200) - 100
        A.d['wash'].line((x, 1060 + k * 28, x + 160, 1060 + k * 28), fill=255, width=4)
    x = lerp(300, 820, ease_out(u / (2 * P)))
    rider(A, x, GROUND, 220, 1, t * 15, layer='ink')
    for k in range(2):
        rider(A, x - 340 - k * 160, GROUND, 190, 1, t * 15 + k, layer='mid', spear=True)
    if u > P:
        q = ease_out((u - P) / 0.5)
        A.d['red'].polygon([(x - 60 - 120 * q, GROUND - 320 + 200 * q), (x - 20 - 120 * q, GROUND - 330 + 200 * q), (x - 40 - 120 * q, GROUND - 280 + 200 * q)], fill=255)
    A.flush(cv)
    stamp(cv, seal('割须弃袍', 44, INK), 260, 940, t, t - u + 1.5 * P, rot=-5)

# ================================================================ 第五回 对酒当歌
def art_c_weiwang(A, cv, t, u):
    A.d['ink'].polygon([(260, GROUND), (820, GROUND), (760, 1200), (320, 1200)], fill=255)
    lord(A, 540, 1200, 250, dir=1, arm=lerp(20, 60, ease_out(u / P)), layer='ink')
    for k in range(4):
        for side in (-1, 1):
            person(A, 540 + side * (380 + k * 40), GROUND, 120, dir=-side, kneel=True, bow=50, arm=60, layer='mid')
    A.flush(cv)
    stamp(cv, seal('魏王', 60), 860, 920, t, t - u + P, rot=6)

def art_c_tongque(A, cv, t, u):
    rise = ease_out(u / (2 * P))
    A.d['ink'].rectangle((360, lerp(GROUND, 980, rise), 720, GROUND), fill=255)
    for k in range(4):
        y = lerp(GROUND, 980, rise) + k * 100
        A.d['wash'].line((360, y, 720, y), fill=0, width=4)
    if rise > 0.8:
        palace(A, 540, 990, 420, layer='mid')
        bronze_sparrow(A, 540, 760, 40)
    for k in range(4):
        lantern(A, 200 + k * 230, 900, t, k, size=18) if k in (0, 3) else None
    ground(A, GROUND)

def art_c_poets(A, cv, t, u):
    A.d['ink'].rectangle((160, 1250, 920, 1280), fill=255)
    for k, x in enumerate((260, 540, 820)):
        person(A, x, 1250, 170, dir=1 if k < 2 else -1, robe=True, hat='knot', kneel=True, bow=15, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='ink')
    A.flush(cv)
    for i, nm in enumerate(('曹操', '曹丕', '曹植')):
        stamp(cv, seal(nm, 44, ZHU if i == 0 else INK), 260 + i * 280, 1060, t, t - u + i * 0.4)
    type_in(cv, text_img('建安风骨', BRUSH, 80, BRONZE), W / 2, 880, t, t - u + 1.4 * P, 0.4)

def art_c_qiuxian(A, cv, t, u):
    p = ease_out(u / 0.6)
    w = 720 * p
    x0, x1 = 540 - w / 2, 540 + w / 2
    A.d['mid'].rectangle((x0, 840, x1, 1240), fill=150)
    A.d['ink'].rectangle((x0 - 20, 820, x0, 1260), fill=255); A.d['ink'].rectangle((x1, 820, x1 + 20, 1260), fill=255)
    fo = font(BRUSH, 120)
    for i, ch in enumerate('唯才是举'):
        if u > 0.4 + i * 0.25 and x0 < 300 + i * 150 < x1:
            A.d['ink'].text((240 + i * 150, 970), ch, font=fo, fill=255)
    ground(A, GROUND)
    for k in range(5):
        person(A, walk_x(-100 - k * 110, 300 - k * 70, u, 3 * P), GROUND, 150, dir=1, robe=True, hat='knot', ph=t * 6 + k, arm=20, layer='mid')

def art_c_laoji(A, cv, t, u):
    sun(cv, 780, lerp(980, 1180, ease_out(u / (3 * P))), 160, ZHU, 120)
    ground(A, GROUND)
    horse(A, 520, GROUND, 260, 1, 0.3, layer='ink', moving=False, head_down=12)
    lord(A, 260, GROUND, 250, dir=1, bow=10, arm=60, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('老骥伏枥 志在千里', BRUSH, 70, INK), W / 2, 860, t, t - u + P, 0.5)

def art_c_hua(A, cv, t, u):
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    lord(A, 300, GROUND, 250, dir=1, kneel=True, bow=-10, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    person(A, 780, GROUND, 240, dir=-1, robe=True, hat='knot', arm=lerp(40, 90, ease_out(u / P)), layer='ink')
    A.d['ink'].line((690, GROUND - 170, 600, GROUND - 200), fill=255, width=3)
    if u > 2 * P:
        for k in range(6):
            A.d['ink'].line((700 + k * 20, 900, 700 + k * 20, GROUND), fill=255, width=6)
        A.d['ink'].rectangle((680, 880, 820, 900), fill=255)
    A.flush(cv)
    stamp(cv, seal('华佗', 54, INK), 780, 960, t, t - u + 0.3)
    if u > 2 * P:
        stamp(cv, seal('下狱', 50), 300, 960, t, t - u + 2 * P, rot=-5)

def art_c_death(A, cv, t, u):
    palace(A, 540, GROUND, 760, layer='mid')
    for k in range(50):
        q = (t * 1.2 + k / 50) % 1
        x = 80 + (k * 19) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 8, y + 40), fill=200, width=2)
    lt = clamp(1 - (u - 1.5 * P) / 0.6)
    A.d['wash'].rectangle((470, 1180, 610, 1280), fill=0)
    if lt > 0:
        A.d['yellow'].rectangle((470, 1180, 610, 1280), fill=int(160 * lt))

def art_c_tombs(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (3 * P)) * 12) + 1
    r = random.Random(4)
    for k in range(n):
        x = 120 + (k % 6) * 170 + r.uniform(-20, 20); y = GROUND - (k // 6) * 120
        s = 80 - (k // 6) * 16
        A.d['mid' if k // 6 else 'ink'].chord((x - s, y - s * 0.7, x + s, y + s * 0.7), 180, 360, fill=255)
    A.flush(cv)
    paste(cv, text_img('七十二疑冢', SERIF, 54, ZHU, 'Black', bleed=False), W / 2, 960, 1, clamp(u / 0.4))

def art_c_cao_pi(A, cv, t, u):
    A.d['ink'].polygon([(260, GROUND), (820, GROUND), (760, 1200), (320, 1200)], fill=255)
    person(A, 540, 1200, 240, dir=1, hat='crown', arm=lerp(20, 60, ease_out(u / P)), layer='ink')
    person(A, 860, GROUND, 230, dir=-1, hat='crown', kneel=True, bow=45, arm=70, layer='mid')
    A.d['yellow'].rectangle((720, GROUND - 160, 780, GROUND - 120), fill=255)
    A.flush(cv)
    stamp(cv, seal('魏', 80), 540, 880, t, t - u + P)
    if u > 2 * P:
        type_in(cv, text_img('追尊 魏武帝', SERIF, 50, INK, 'Black', bleed=False, spacing=6), W / 2, 1460, t, t - u + 2 * P, 0.4)

def art_c_drama(A, cv, t, u):
    """Two faces: the white-faced opera villain vs. the poet-statesman."""
    for i, x in enumerate((330, 750)):
        A.d['ink'].ellipse((x - 150, 860, x + 150, 1200), outline=255, width=6)
        if i == 0:
            A.d['wash'].ellipse((x - 140, 870, x + 140, 1190), fill=255)
            for sx in (-1, 1):
                A.d['ink'].polygon([(x + sx * 40, 980), (x + sx * 110, 960), (x + sx * 100, 990)], fill=255)
            A.d['ink'].arc((x - 40, 1080, x + 40, 1130), 200, 340, fill=255, width=5)
        else:
            A.d['bronze'].ellipse((x - 140, 870, x + 140, 1190), fill=180)
            for sx in (-1, 1):
                A.d['ink'].line((x + sx * 30, 990, x + sx * 90, 985), fill=255, width=6)
            A.d['ink'].line((x - 30, 1110, x + 30, 1110), fill=255, width=5)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('奸雄', 54, INK), 330, 1280, t, t - u + 0.3)
    stamp(cv, seal('英雄', 54), 750, 1280, t, t - u + P)

# ================================================================ script
CHAPTERS = {16: ('第一回', '乱世奸雄'), 48: ('第二回', '挟天子'), 80: ('第三回', '官渡之战'),
            112: ('第四回', '赤壁之战'), 144: ('第五回', '对酒当歌')}

CARDS = [
    C(0, 2, 'hook', 'num', num='宁我负人', line='毋人负我', art=art_c_hook_ning),
    C(2, 4, 'hook', 'num', num='挟天子', line='以令诸侯', art=art_c_hook_emperor),
    C(4, 6, 'hook', 'num', num='官渡', line='以少胜多', art=art_c_hook_guandu),
    C(6, 8, 'hook', 'num', num='赤壁', line='一把火烧尽野心', art=art_c_hook_fire),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 乱世奸雄
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'night', 'card', year=155, main='生于谯县', sub='宦官曹腾养孙 · 父曹嵩', note='太祖武皇帝 沛国谯人也', art=art_c_birth),
    C(22, 26, 'life', 'card', year=165, main='飞鹰走狗', sub='少年任侠放荡 · 不治行业', note='好飞鹰走狗 游荡无度', art=art_c_hawk),
    C(26, 30, 'life', 'card', year=168, main='中风装病', sub='骗过叔父 · 父亲从此不信谗言', note='口貌如故 叔父之言 遂不复信', art=art_c_palsy),
    C(30, 34, 'court', 'card', year=174, main='月旦评', sub='许劭一语 · 定他一生', note='子治世之能臣 乱世之奸雄', art=art_c_yuedan),
    C(34, 38, 'court', 'card', year=174, main='五色棒', sub='洛阳北部尉 · 棒杀权宦之叔', note='犯禁者 不避豪强 皆棒杀之', art=art_c_rods),
    C(38, 42, 'night', 'card', year=189, main='刺董献刀', sub='行刺董卓不成 · 改称献刀', note='孟德献刀', art=art_c_dagger),
    C(42, 46, 'night', 'card', year=189, main='连夜逃亡', sub='误杀吕伯奢一家', note='宁我负人 毋人负我', art=art_c_flee),
    C(46, 48, 'war', 'card', year=190, main='起兵讨董', sub='陈留散家财 · 首倡义兵', art=art_c_jiaozhao),
    # ---- 第二回 挟天子
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'war', 'card', year=190, main='汴水之败', sub='孤军追击 · 中箭落马', note='天下可无洪 不可无君', art=art_c_bianshui),
    C(54, 58, 'war', 'card', year=192, main='收编青州兵', sub='降黄巾三十万 · 精锐为青州兵', note='收其精锐者 号为青州兵', art=art_c_qingzhou),
    C(58, 62, 'works', 'card', year=196, main='许下屯田', sub='兵农合一 · 粮草无忧', note='得谷百万斛', art=art_c_tuntian),
    C(62, 66, 'empire', 'card', year=196, main='迎奉天子', sub='迁都许县 · 挟天子以令诸侯', note='奉天子以令不臣', art=art_c_xuchang),
    C(66, 70, 'war', 'card', year=197, main='望梅止渴', sub='行军缺水 · 前有梅林', note='士卒闻之 口皆出水', art=art_c_plum),
    C(70, 74, 'night', 'card', year=199, main='煮酒论英雄', sub='惊雷一声 · 刘备失箸', note='今天下英雄 唯使君与操耳', art=art_c_wine),
    C(74, 80, 'war', 'card', year=198, main='白门楼', sub='水淹下邳 · 擒杀吕布', note='缚虎不得不急', art=art_c_lvbu),
    # ---- 第三回 官渡之战
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'war', 'card', year=200, main='斩颜良', sub='关羽万军之中 · 刺颜良于马下', note='策马刺良于万众之中 斩其首还', art=art_c_yanliang),
    C(86, 90, 'fate', 'card', year=200, main='千里走单骑', sub='封金挂印 · 曹操不追', note='彼各为其主 勿追也', art=art_c_guanyu_leave),
    C(90, 98, 'night', 'card', year=200, main='火烧乌巢', sub='许攸来投 · 夜袭乌巢 · 袁军崩溃', note='公兵不过二万 袁绍十余万', art=art_c_guandu),
    C(98, 106, 'works', 'north'),
    C(106, 112, 'works', 'card', year=207, main='东临碣石', sub='北征乌桓 · 观沧海', note='日月之行 若出其中 星汉灿烂 若出其里', art=art_c_jieshi),
    # ---- 第四回 赤壁之战
    C(112, 114, 'war', 'chapter'),
    C(114, 118, 'war', 'card', year=208, main='南下荆州', sub='刘琮不战而降', note='八十万大军 号称', art=art_c_jingzhou),
    C(118, 122, 'war', 'card', year=208, main='长坂坡', sub='张飞据水断桥', note='身是张益德也 可来共决死', art=art_c_changban),
    C(122, 126, 'works', 'card', year=208, main='铁索连船', sub='北兵不习水战 · 连船如平地', note='首尾相接', art=art_c_chain),
    C(126, 130, 'fate', 'card', year=208, main='东风骤起', sub='孙刘联军 · 等待一夜东风', note='东风不与周郎便', art=art_c_eastwind),
    C(130, 138, 'night', 'card', year=208, main='赤壁之战', sub='黄盖诈降 · 火船冲阵 · 曹军大败', note='时东南风急 船往如箭 烧尽北船', art=art_c_chibi),
    C(138, 142, 'death', 'card', year=208, main='败走华容', sub='泥泞道路 · 狼狈北归', note='羸兵为人马所蹈藉', art=art_c_huarong),
    C(142, 144, 'war', 'card', year=211, main='割须弃袍', sub='潼关大战马超', art=art_c_tongguan),
    # ---- 第五回 对酒当歌
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'empire', 'card', year=216, main='进封魏王', sub='位在诸侯王上 · 终不称帝', note='若天命在吾 吾为周文王矣', art=art_c_weiwang),
    C(150, 154, 'empire', 'card', year=210, main='铜雀台', sub='邺城筑台 · 文士云集', note='铜雀春深锁二乔', art=art_c_tongque),
    C(154, 158, 'court', 'card', year=210, main='建安风骨', sub='三曹七子 · 慷慨悲凉', note='对酒当歌 人生几何', art=art_c_poets),
    C(158, 162, 'court', 'card', year=210, main='唯才是举', sub='三下求贤令 · 不问出身', note='周公吐哺 天下归心', art=art_c_qiuxian),
    C(162, 164, 'fate', 'card', year=215, main='老骥伏枥', sub='烈士暮年 · 壮心不已', art=art_c_laoji),
    C(164, 166, 'death', 'card', year=219, main='华佗之死', sub='头风难治 · 名医下狱', art=art_c_hua),
    C(166, 168, 'death', 'card', year=220, main='崩于洛阳', sub='享年六十六岁 · 遗令薄葬', art=art_c_death),
    C(168, 170, 'end', 'card', year=220, main='曹丕代汉', sub='追尊魏武帝', art=art_c_cao_pi),
    C(170, 999, 'end', 'end'),
]
# extra unique scenes kept in the library: art_c_tombs, art_c_drama (used in the ending)

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb):
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
for mod in (G, L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_num(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=BRONZE + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    def art(A, cv_, t_, u_):
        sun(cv_, 600, 1000, 250, BRONZE, 120)
        ground(A, 1440)
        lord(A, 470, 1440, 700, dir=1, arm=lerp(-5, 55, ease_out(u_ / (2 * P))), layer='ink')
    stage(cv, t, c, art)
    fx = Art()
    ink_in(cv, text_img('曹 操 · 字孟德', SERIF, 46, BRONZE, 'Bold', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '魏武帝', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('孟德', 66), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元155 — 220', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '乱世奸雄？', BRUSH, 120, INK, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '盖世英雄？', BRUSH, 120, BRONZE, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    jue(A, 540, 900, 300, fill_=1.0, p=clamp(u / 0.6), t=t)
    A.flush(cv, alpha=clamp(u / 0.6) * 0.3)
    fx = Art()
    chars_in(cv, fx, '对酒当歌', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('魏武', 60), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('他统一了北方 · 却从未称帝', SERIF, 46, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.4)
    type_in(cv, text_img('戏台上是白脸 · 诗卷里是英雄', SERIF, 50, INK, 'Bold', bleed=False, spacing=4), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '奸雄还是英雄', BRUSH, 100, BRONZE, W / 2, 1190, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('评论区站个队', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=BRONZE + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(250, 250, 245, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=ZHU + (220,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 诸葛亮', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, north=scene_north, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第拾贰集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 570, 170, 1, 1)
    if t < bt(8):
        q = text_img('宁我负人 · 他到底是奸雄还是英雄？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 320, 335, W / 2 + 320, 335), fill=BRONZE + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, BRONZE, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=BRONZE + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=ZHU + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(int(round(yr - BORN + 1))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=BRONZE + (255,))
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
