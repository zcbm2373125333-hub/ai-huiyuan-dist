"""千古人物志 · 第陆拾集 · 关羽 (？–220)
Look: 枣红 + 青龙绿, 青龙刀 corner borders, a 赤兔 chapter card: a red horse gallops a little further each chapter
and in the last chapter stands riderless.
Set pieces: 6-beat 桃园 (演义), custom 8-beat scene 'baima' (斩颜良), 6-beat 挂印封金, 8-beat 水淹七军,
6-beat 大意失荆州, 6-beat 走麦城.
Birth year unknown: the HUD hides ages (no_age).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_huatuo as Ht          # engine + helpers (previous episode)
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
from render_wangyangming import desk, scroll, lamp, sitter
from render_kongzi import slips, bundle
from render_songtaizu import tent
from render_sunwu import army, banner
from render_quyuan import river
from render_huatuo import caocao

F.RIPPLE = False
ZAOHONG = (150, 40, 36)             # 枣红
QINGLONG = (40, 104, 84)            # 青龙绿
S.LAYERS.append(('zaohong', ZAOHONG, 0.9, 1.0))
S.LAYERS.append(('qinglong', QINGLONG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='义', life='解', court='汉', night='夜', war='战', empire='威', works='春', fate='荆', death='麦', end='义')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZAOHONG, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (QINGLONG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (ZAOHONG, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

PEACH = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(PEACH)
for _x in (110, 200, 880, 970):     # peach trees at the margins
    _d.line((_x, 1470, _x - 6, 1380), fill=(80, 60, 50, 70), width=7)
    for _k in range(6):
        _a = _k * 1.05
        _d.ellipse((_x + 40 * math.cos(_a) - 14, 1370 + 26 * math.sin(_a) - 10, _x + 40 * math.cos(_a) + 14, 1370 + 26 * math.sin(_a) + 10), fill=(220, 150, 160, 60))
for _k in range(3):
    _d.line((60, 1478 + _k * 16, W - 60, 1478 + _k * 16), fill=QINGLONG + (34,), width=2)
MTN_COL = {'night': (32, 34, 40), 'death': (62, 56, 56), 'war': (112, 56, 46), 'fate': (90, 98, 94)}
def draw_background(t, theme):
    """荆襄: hills, peach blossom at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 186, 180), (156, 160, 150), MTN_COL.get(theme, (106, 118, 104))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(PEACH)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """青龙刀: a crescent glaive blade in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=QINGLONG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=QINGLONG + (220,), width=3)
        d.line((x + sx * 20, y + sy * 110, x + sx * 70, y + sy * 30), fill=(60, 40, 30, 230), width=5)
        cx, cy = x + sx * 76, y + sy * 26
        d.chord((cx - 34, cy - 30, cx + 34, cy + 30), 200 if sx > 0 else -20, 340 if sx > 0 else 160, fill=QINGLONG + (230,))
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=ZAOHONG + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def guan(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, glaive=True, armour=True, **kw):
    """关羽: red face, long beard (美髯), green 头巾 and robe over armour, the crescent glaive."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if up:
        A.d['qinglong'].chord((x - 0.09 * h, y - 1.06 * h, x + 0.09 * h, y - 0.9 * h), 180, 360, fill=255)
        A.d['qinglong'].line((x - dir * 0.05 * h, y - 0.98 * h, x - dir * 0.16 * h, y - 0.8 * h), fill=255, width=max(2, int(0.02 * h)))
        A.d['zaohong'].ellipse((x - 0.05 * h + dir * 0.02 * h, y - 0.94 * h, x + 0.05 * h + dir * 0.02 * h, y - 0.82 * h), fill=255)
        A.d['ink'].polygon([(x + dir * 0.0 * h, y - 0.82 * h), (x + dir * 0.09 * h, y - 0.82 * h), (x + dir * 0.05 * h, y - 0.5 * h)], fill=255)
        A.d['qinglong'].polygon([(x - 0.11 * h, y - 0.78 * h), (x + 0.11 * h, y - 0.78 * h), (x + 0.13 * h, y - 0.3 * h), (x - 0.13 * h, y - 0.3 * h)], fill=180)
        if glaive:
            gx = x + dir * 0.3 * h
            A.d['ink'].line((gx, y, gx, y - 1.3 * h), fill=255, width=max(3, int(0.022 * h)))
            A.d['qinglong'].chord((gx - 0.14 * h, y - 1.48 * h, gx + 0.14 * h, y - 1.18 * h), 270 if dir > 0 else 90, 90 if dir > 0 else 270, fill=255)
    return hand

def chitu(A, x, y, s, dir=1, ph=0.0, moving=True, rider_on=True, **kw):
    horse(A, x, y, s, dir, ph, layer='zaohong', moving=moving)
    if rider_on:
        guan(A, x - dir * 0.05 * s, y - 0.66 * s, 0.6 * s, dir=dir, arm=55, glaive=True)

def liubei(A, x, y, h, dir=1, layer='ink', **kw):
    return person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)

def zhangfei(A, x, y, h, dir=1, layer='ink', **kw):
    hand = person(A, x, y, h, dir=dir, robe=False, hat='helmet', layer=layer, **kw)
    if not kw.get('kneel') and not kw.get('fall'):
        A.d['ink'].ellipse((x - 0.08 * h, y - 0.86 * h, x + 0.08 * h, y - 0.74 * h), fill=255)
    return hand

# ================================================================ chapter card
CH = {16: 0.0, 48: 0.25, 80: 0.5, 112: 0.75, 144: 1.0}
def art_horse_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    p0 = CH.get(kb, 0.25)
    q = ease_out(u / (1.2 * P))
    ground(A, 1210)
    if kb == 144:
        chitu(A, 540, 1210, 220, dir=1, moving=False, rider_on=False)
    else:
        x = lerp(200 + 400 * p0, 300 + 400 * p0, q)
        chitu(A, x, 1210, 200, dir=1, ph=t * 8)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_horse_chapter)
    ink_in(cv, text_img(no, SERIF, 56, QINGLONG, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_g_hook_wan(A, cv, t, u):
    ground(A, GROUND)
    army(A, 700, GROUND, 8, dir=1, layer='mid', h=90)
    chitu(A, lerp(-100, 560, ease_out(u / (1.4 * P))), GROUND, 160, dir=1, ph=t * 10)

def art_g_hook_gold(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mid')
    for i in range(6):
        A.d['gold'].rectangle((440 + (i % 3) * 60, GROUND - 110 - (i // 3) * 30, 490 + (i % 3) * 60, GROUND - 82 - (i // 3) * 30), fill=255)
    A.d['red'].rectangle((640, GROUND - 130, 690, GROUND - 80), fill=255)

def art_g_hook_flood(A, cv, t, u):
    q = ease_out(u / (1.4 * P))
    A.d['ocean'].rectangle((60, lerp(GROUND, 1100, q), W - 60, GROUND + 40), fill=180)
    waves(A, lerp(GROUND, 1100, q), t, rows=3, amp=8, speed=3)
    ground(A, GROUND)

def art_g_hook_temple(A, cv, t, u):
    palace(A, 540, 1300, 340, layer='zaohong')
    ground(A, GROUND)
    for i in range(int(clamp(u / (1.4 * P)) * 6) + 1):
        person(A, 200 + i * 130, GROUND, 110, dir=1, robe=True, hat='knot', kneel=True, bow=40, arm=100, layer='mid')

# ================================================================ 第一回 亡命涿郡
def art_g_birth(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 220), (x + 200, GROUND)], fill=150)
    ground(A, GROUND)
    A.d['wash'].rectangle((360, GROUND - 60, 720, GROUND), fill=220)
    A.flush(cv)
    paste(cv, text_img('河东解县 · 盐池之乡', SERIF, 46, QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('解良', 56), 860, 1020, t, t - u + P, rot=6)

def art_g_flee(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    guan(A, lerp(120, 840, ease_out(u / (3 * P))), GROUND, 180, dir=1, ph=t * 5, arm=-8, glaive=False, armour=False)
    A.flush(cv)
    paste(cv, text_img('亡命奔涿郡', SERIF, 48, QINGLONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '亡命之由 史书未载', t, t - u + P)

def art_g_taoyuan(A, cv, t, u):
    """6-beat set piece: 桃园结义 — under peach blossom three men kneel before an altar; petals fall. (From the novel.)"""
    ph = u / P
    for k in range(5):
        x = 120 + k * 210
        A.d['ink'].line((x, GROUND, x - 8, GROUND - 260), fill=255, width=12)
        A.d['pink'].ellipse((x - 110, GROUND - 400, x + 100, GROUND - 230), fill=200)
    for k in range(30):
        q = (t * 0.3 + k / 30) % 1
        A.d['pink'].ellipse((80 + (k * 37) % 920 - 6, lerp(760, 1400, q) - 4, 80 + (k * 37) % 920 + 6, lerp(760, 1400, q) + 4), fill=230)
    ground(A, GROUND)
    A.d['mid'].rectangle((470, GROUND - 90, 610, GROUND), fill=230)
    kneel = ph > 1.5
    liubei(A, 380, GROUND, 180, dir=1, kneel=kneel, bow=30 if kneel else 0, arm=100)
    guan(A, 260, GROUND, 190, dir=1, kneel=kneel, bow=30 if kneel else 0, arm=100, glaive=False, armour=False)
    zhangfei(A, 720, GROUND, 190, dir=-1, kneel=kneel, bow=30 if kneel else 0, arm=100)
    A.flush(cv)
    type_in(cv, text_img('不求同年同月同日生', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 2 * P, 0.5)
    type_in(cv, text_img('但愿同年同月同日死', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 3.2 * P, 0.5)
    note_in(cv, '桃园结义出自三国演义 史载恩若兄弟', t, t - u + 0.5 * P)

def art_g_bed(A, cv, t, u):
    A.d['mid'].rectangle((240, GROUND - 60, 840, GROUND), fill=220)
    liubei(A, 540, GROUND - 60, 170, dir=1, fall=-86, arm=-8)
    guan(A, 300, GROUND, 190, dir=1, arm=-8, glaive=False)
    zhangfei(A, 780, GROUND, 190, dir=-1, arm=-8)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('寝则同床 恩若兄弟', SERIF, 48, QINGLONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '语出三国志关羽传', t, t - u + P)

def art_g_guard(A, cv, t, u):
    ground(A, GROUND)
    liubei(A, 540, GROUND, 200, dir=1, arm=40)
    guan(A, 320, GROUND, 210, dir=1, arm=60)
    zhangfei(A, 760, GROUND, 210, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('稠人广坐 侍立终日', SERIF, 48, QINGLONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_g_xiapi(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='下邳', layer='mid', open_=1.0)
    ground(A, GROUND)
    guan(A, 540, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('守下邳 · 行太守事', SERIF, 46, QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_captured(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='下邳', layer='mid', open_=1.0)
    ground(A, GROUND)
    army(A, lerp(-200, 100, ease_out(u / (2 * P))), GROUND, 6, dir=1, layer='ink', t=t, march=True, h=100)
    guan(A, 700, GROUND, 200, dir=-1, arm=-8, glaive=False)
    A.flush(cv)
    paste(cv, text_img('曹操东征 · 擒羽以归', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('降曹', 56, INK), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第二回 白马
def art_g_cao_favor(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='zaohong')
    ground(A, GROUND)
    caocao(A, 760, GROUND - 30, 190, dir=-1, arm=lerp(20, 100, ease_out(u / 0.5)))
    guan(A, 380, GROUND, 200, dir=1, kneel=True, bow=20, arm=90, glaive=False)
    A.flush(cv)
    paste(cv, text_img('拜为偏将军 · 礼之甚厚', SERIF, 46, QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_heart(A, cv, t, u):
    ground(A, GROUND)
    guan(A, 380, GROUND, 200, dir=1, arm=-8, glaive=False)
    person(A, 700, GROUND, 190, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('吾受刘将军厚恩 誓以共死 不可背之', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('张辽问', 50, INK), 860, 1020, t, t - u + P, rot=6)

def scene_baima(cv, t, c, k):
    """8-beat custom scene: 白马 — 颜良's banner and parasol stand amid ten thousand men; a red horse breaks from the line,
    cuts straight through; the banner falls; he returns with the head; the siege is lifted."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    for j in range(14):
        person(A, 560 + (j % 7) * 64, GROUND - (j // 7) * 50, 90, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    fallen = clamp((ph - 3.6) / 0.4)
    A.d['ink'].line((800, GROUND, 800 + 200 * math.sin(fallen * 1.4), GROUND - 320 * math.cos(fallen * 1.4)), fill=255, width=6)
    if fallen < 0.9:
        A.d['gold'].chord((800 - 90, GROUND - 360, 800 + 90, GROUND - 280), 180, 360, fill=255)
    if ph < 3:
        x = lerp(-120, 760, ease_out(ph / 3))
    elif ph < 4.2:
        x = 760
    else:
        x = lerp(760, -200, ease_out((ph - 4.2) / 2.5))
    chitu(A, x, GROUND, 170, dir=1 if ph < 4.2 else -1, ph=t * 12)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '万众取首', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=60)
    fx.flush(cv)
    lab = '羽望见良麾盖' if ph < 1.5 else ('策马刺良于万众之中' if ph < 4.2 else '斩其首还 · 绍诸将莫能当者')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 1.5 else QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('遂解白马之围', SERIF, 42, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 5.5) / 0.4))
    stamp(cv, seal('颜良', 40, INK), 860, 1060, t, s0 + 0.4, rot=6)

def art_g_hanshou(A, cv, t, u):
    for k in range(3):
        A.d['zaohong'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    guan(A, 540, GROUND - 180, 200, dir=1, arm=60)
    A.flush(cv)
    stamp(cv, seal('汉寿亭侯', 46), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('曹操即表封羽为汉寿亭侯', SERIF, 46, QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_seal(A, cv, t, u):
    """6-beat set piece: 挂印封金 — he seals up every gift, hangs the seal of office on the beam and rides away to find Liu Bei."""
    ph = u / P
    ground(A, GROUND)
    if ph < 3.5:
        palace(A, 540, 1300, 320, layer='mid')
        desk(A, 540, GROUND, 360, layer='mid')
        n = int(clamp(ph / 2) * 6)
        for i in range(6):
            A.d['gold'].rectangle((440 + (i % 3) * 60, GROUND - 110 - (i // 3) * 30, 490 + (i % 3) * 60, GROUND - 82 - (i // 3) * 30), fill=255)
            if i < n:
                A.d['red'].line((440 + (i % 3) * 60, GROUND - 96 - (i // 3) * 30, 490 + (i % 3) * 60, GROUND - 96 - (i // 3) * 30), fill=255, width=4)
        A.d['ink'].line((600, 1060, 600, 1120 * 0 + 1100), fill=255, width=3)
        A.d['red'].rectangle((580, 1100, 620, 1140), fill=255 if ph > 2.4 else 0)
        guan(A, 260, GROUND, 190, dir=1, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 2)), glaive=False)
    else:
        chitu(A, lerp(300, 1100, ease_out((ph - 3.5) / 2.5)), GROUND, 170, dir=1, ph=t * 10)
    A.flush(cv)
    lab = '尽封其所赐' if ph < 2.4 else ('拜书告辞' if ph < 3.5 else '奔先主于袁军')
    paste(cv, text_img(lab, SERIF, 48, ZHU if ph >= 3.5 else QINGLONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    if ph > 3.5:
        paste(cv, text_img('彼各为其主 勿追也', SERIF, 42, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4) / 0.4))

def art_g_pass(A, cv, t, u):
    for k in range(5):
        city_wall(A, 80 + k * 190, 220 + k * 190, 1180, label=None, layer='mid')
    ground(A, GROUND)
    chitu(A, lerp(-100, 1100, ((t * 0.12) % 1)), GROUND, 140, dir=1, ph=t * 10)
    A.flush(cv)
    paste(cv, text_img('过五关斩六将', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '出自三国演义 正史无此事', t, t - u + 0.5 * P)

def art_g_reunion(A, cv, t, u):
    tent(A, 540, GROUND, 420, 280, layer='mid')
    ground(A, GROUND)
    liubei(A, 640, GROUND, 200, dir=-1, arm=lerp(40, 120, ease_out(u / 0.5)))
    guan(A, 420, GROUND, 210, dir=1, arm=lerp(40, 120, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('兄弟重逢', SERIF, 52, QINGLONG, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 镇守荆州
def art_g_jing(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='江陵', layer='qinglong', open_=1.0)
    river(A, 1260, t, rows=2, amp=3)
    A.flush(cv)
    paste(cv, text_img('先主西定益州 · 拜羽董督荆州事', SERIF, 44, QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('荆州', 56), 860, 1020, t, t - u + P, rot=6)

def art_g_beard(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mid')
    scroll(A, 540, GROUND - 160, 260, 70, clamp(u / P), layer='wash')
    guan(A, 300, GROUND, 190, dir=1, kneel=True, arm=90, glaive=False)
    A.flush(cv)
    type_in(cv, text_img('孟起犹未及髯之绝伦逸群也', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('美髯公', 50), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '诸葛亮回书 见三国志', t, t - u + P)

def art_g_arrow(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 640, GROUND, 260, layer='ink')
    guan(A, 460, GROUND, 230, dir=1, kneel=True, arm=110, glaive=False)
    person(A, 280, GROUND, 180, dir=1, robe=True, hat='knot', bow=20, arm=lerp(80, 120, 0.5 + 0.5 * math.sin(t * 8)), layer='mid')
    A.flush(cv)
    paste(cv, text_img('流矢贯臂 · 破臂刮骨去毒', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('羽割炙引酒 言笑自若', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 835, 1, clamp((u - P) / 0.4))
    note_in(cv, '史载为医者刮骨 非华佗', t, t - u + P)

def art_g_dandao(A, cv, t, u):
    tent(A, 540, GROUND, 420, 280, layer='mid')
    ground(A, GROUND)
    guan(A, 360, GROUND, 200, dir=1, arm=60)
    person(A, 720, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('与鲁肃相见 · 各驻兵马百步上', SERIF, 44, QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '单刀赴会 史实与演义人物相反', t, t - u + P)

def art_g_marry(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    guan(A, 360, GROUND, 200, dir=1, arm=lerp(40, 150, ease_out((u - P) / 0.4)))
    person(A, 720, GROUND, 180, dir=-1, robe=True, hat='knot', bow=20, arm=90, layer='ink')
    A.flush(cv)
    paste(cv, text_img('孙权遣使为子求羽女 · 羽骂辱其使', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_g_fivetiger(A, cv, t, u):
    for k in range(3):
        A.d['zaohong'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    guan(A, 540, GROUND - 180, 200, dir=1, arm=60)
    A.flush(cv)
    stamp(cv, seal('前将军', 56), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('先主为汉中王 · 拜羽为前将军 假节钺', SERIF, 42, QINGLONG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 威震华夏
def art_g_fancheng(A, cv, t, u):
    city_wall(A, 520, 1000, 1080, gate_x=760, label='樊城', layer='mid', open_=0.0)
    river(A, 1260, t, rows=2, amp=4)
    for j in range(4):
        boat(A, lerp(-200, 200 + j * 80, ease_out(u / (2 * P))), 1270, 60, t + j, sail=True)
    A.flush(cv)
    paste(cv, text_img('率众攻曹仁于樊', SERIF, 46, QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_flood(A, cv, t, u):
    """8-beat set piece: 水淹七军 — autumn rains; the Han river rises over the plain; Yu Jin's seven armies drown;
    boats move in to take thirty thousand prisoners; Pang De is beheaded."""
    ph = u / P
    lvl = lerp(GROUND, 1040, ease_out(clamp((ph - 0.5) / 3)))
    for k in range(40):
        q = (t * 1.2 + k / 40) % 1
        A.d['wash'].line((80 + (k * 37) % 920, lerp(620, lvl, q), 80 + (k * 37) % 920 - 12, lerp(620, lvl, q) + 40), fill=160, width=2)
    ground(A, GROUND)
    for j in range(7):
        tent(A, 140 + j * 130, GROUND, 110, 90, layer='mid')
    A.d['ocean'].rectangle((60, lvl, W - 60, GROUND + 40), fill=180)
    waves(A, lvl, t, rows=3, amp=8, speed=3)
    if ph > 3.5:
        for j in range(8):
            person(A, 160 + j * 110 + 10 * math.sin(t * 3 + j), lvl + 10, 70, dir=1, robe=False, hat='helmet', fall=-50, arm=160, layer='ink')
    if ph > 5:
        for j in range(3):
            boat(A, lerp(-200, 300 + j * 200, ease_out((ph - 5) / 2)), lvl + 10, 70, t + j, sail=True)
    A.flush(cv)
    lab = '秋大霖雨 汉水泛溢' if ph < 3.5 else ('于禁所督七军皆没' if ph < 5 else '禁降羽 · 斩庞德')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('七军', 54, INK), 860, 1440, t, t - u + 3.5 * P, rot=6)

def art_g_weizhen(A, cv, t, u):
    q = ease_out(u / (2 * P))
    for k in range(6):
        r = 80 + 300 * ((t * 0.3 + k / 6) % 1)
        A.d['zaohong'].ellipse((540 - r, 1100 - 0.5 * r, 540 + r, 1100 + 0.5 * r), outline=int(160 * (1 - r / 380)), width=4)
    ground(A, GROUND)
    guan(A, 540, GROUND, 220, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('威震华夏', SERIF, 56, ZHU, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))

def art_g_qiandu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    caocao(A, 540, GROUND, 210, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3)), bow=10)
    for i in range(3):
        person(A, 760 + i * 70, GROUND, 160, dir=-1, robe=True, hat='knot', kneel=True, bow=30, arm=90, layer='mid')
    A.flush(cv)
    paste(cv, text_img('曹公议徙许都以避其锐', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_lumeng(A, cv, t, u):
    """6-beat set piece: 白衣渡江 — merchant boats glide downriver at night; soldiers hidden below in white robes take the beacon posts one by one."""
    ph = u / P
    river(A, 1200, t, rows=3, amp=4, speed=0.8)
    for j in range(4):
        x = lerp(-200, 900, ((t * 0.08 + j / 4) % 1))
        boat(A, x, 1220, 80, t + j, sail=True)
        person(A, x, 1200, 70, dir=1, robe=True, hat='knot', arm=-8, layer='wash')
    for k in range(4):
        x = 180 + k * 240
        A.d['mid'].rectangle((x - 18, 1000, x + 18, 1140), fill=230)
        lit = ph < (k + 1) * 1.2
        if lit:
            A.d['red'].ellipse((x - 14, 984, x + 14, 1008), fill=200)
    A.flush(cv)
    paste(cv, text_img('吕蒙伏精兵于舟中 使白衣摇橹', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('尽收江边屯候 · 羽不闻知', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 835, 1, clamp((ph - 2) / 0.4))

def art_g_lost(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='江陵', layer='mid', open_=1.0)
    banner(A, 760, 1080, 200, t, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('糜芳 傅士仁降吴 · 荆州尽失', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('失荆州', 50, INK), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第五回 麦城
def art_g_scatter(A, cv, t, u):
    ground(A, GROUND)
    for j in range(8):
        person(A, lerp(540, 540 + (j - 4) * 140, ease_out(u / (2 * P))), GROUND, 110, dir=1 if j > 3 else -1, robe=False, hat='helmet', ph=t * 4 + j, arm=-8, layer='mid')
    chitu(A, 540, GROUND, 160, dir=1, moving=False)
    A.flush(cv)
    paste(cv, text_img('吏士家属皆在城中 · 军心离散', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_maicheng(A, cv, t, u):
    """6-beat set piece: 走麦城 — the small city at night; he slips out by the west road with a dozen riders; ambush ropes in the woods."""
    ph = u / P
    r = 50
    A.d['wash'].ellipse((820 - r, 820 - r, 820 + r, 820 + r), fill=230)
    city_wall(A, 640, 980, 1120, gate_x=None, label=None, layer='mid')
    for k in range(6):
        x = 120 + k * 90
        A.d['ink'].line((x, GROUND, x, GROUND - 260), fill=255, width=10)
        A.d['pine'].ellipse((x - 50, GROUND - 330, x + 50, GROUND - 220), fill=200)
    ground(A, GROUND)
    for j in range(3):
        rider(A, lerp(700, 120, ease_out(ph / 4)) + j * 90, GROUND, 110, dir=-1, ph=t * 8 + j, layer='ink')
    chitu(A, lerp(620, 40, ease_out(ph / 4)), GROUND, 140, dir=-1, ph=t * 8)
    if ph > 3.6:
        A.d['ink'].line((60, GROUND - 30, 400, GROUND - 30), fill=255, width=4)
    A.flush(cv)
    lab = '西保麦城' if ph < 2 else ('夜遁 · 至临沮' if ph < 3.6 else '伏兵绊马')
    paste(cv, text_img(lab, SERIF, 48, ZHU if ph >= 3.6 else QINGLONG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    stamp(cv, seal('麦城', 56, INK), 860, 1440, t, t - u + 0.4, rot=6)

def art_g_death(A, cv, t, u):
    ground(A, GROUND)
    chitu(A, 540, GROUND, 180, dir=1, moving=False, rider_on=False)
    A.d['ink'].line((700, GROUND - 10, 900, GROUND - 30), fill=255, width=6)
    A.flush(cv)
    paste(cv, text_img('孙权斩羽及子平于临沮', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '建安二十四年十二月 时已入公元二二〇年', t, t - u + P)

def art_g_head(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    caocao(A, 540, GROUND, 210, dir=1, bow=lerp(0, 30, ease_out(u / P)), arm=-8)
    A.d['wash'].rectangle((660, GROUND - 90, 760, GROUND), fill=255)
    A.flush(cv)
    paste(cv, text_img('权传首于曹操 · 操以诸侯礼葬其尸骸', SERIF, 42, QINGLONG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '诸侯礼葬见吴历', t, t - u + P)

def art_g_two_tombs(A, cv, t, u):
    for i, x in enumerate((300, 780)):
        A.d['mid'].chord((x - 160, 1140, x + 160, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('当阳', 44), 300, 1060, t, t - u + 0.4)
    stamp(cv, seal('洛阳', 44), 780, 1060, t, t - u + P)
    paste(cv, text_img('头枕洛阳 身卧当阳', SERIF, 48, QINGLONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_g_shou(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    A.flush(cv)
    type_in(cv, text_img('羽刚而自矜 以短取败 理数之常也', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('陈寿', 54), 860, 1020, t, t - u + P, rot=6)

def art_g_wusheng(A, cv, t, u):
    palace(A, 540, 1300, 340, layer='zaohong')
    ground(A, GROUND)
    for i in range(6):
        person(A, 180 + i * 140, GROUND, 110, dir=1, robe=True, hat='knot', kneel=True, bow=40, arm=100, layer='mid')
    A.flush(cv)
    paste(cv, text_img('宋元明清屡加封号 · 终成武圣', SERIF, 44, QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('关帝', 56), 860, 1020, t, t - u + P, rot=6)

def art_g_yi(A, cv, t, u):
    for k in range(5):
        x = 120 + k * 210
        A.d['ink'].line((x, GROUND, x - 8, GROUND - 260), fill=255, width=12)
        A.d['pink'].ellipse((x - 110, GROUND - 400, x + 100, GROUND - 230), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('忠义二字 · 成了他的名字', SERIF, 48, QINGLONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    horse(A, 860, 1380, 90, 1, 0, layer='zaohong', moving=False)

def art_g_title(A, cv, t, u):
    horse(A, 820, 1460, 220, -1, 0, layer='zaohong', moving=False)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    guan(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '亡命涿郡'), 48: ('第二回', '白马'), 80: ('第三回', '镇守荆州'),
            112: ('第四回', '威震华夏'), 144: ('第五回', '麦城')}

CARDS = [
    C(0, 2, 'war', 'num', num='万军之中', line='取上将首级', art=art_g_hook_wan),
    C(2, 4, 'night', 'num', num='金银美女', line='全部封还', art=art_g_hook_gold),
    C(4, 6, 'empire', 'num', num='七支大军', line='一夜淹没', art=art_g_hook_flood),
    C(6, 8, 'end', 'num', num='一个武将', line='被供成了神', art=art_g_hook_temple),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 亡命涿郡
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=170, main='生于解良', sub='河东人', note='生年不详', art=art_g_birth),
    C(22, 26, 'fate', 'card', year=184, main='亡命涿郡', sub='一个逃犯', art=art_g_flee),
    C(26, 32, 'life', 'card', year=184, main='桃园结义', sub='小说里的誓言', art=art_g_taoyuan),
    C(32, 36, 'night', 'card', year=191, main='恩若兄弟', sub='寝则同床', art=art_g_bed),
    C(36, 40, 'court', 'card', year=191, main='侍立终日', sub='护卫', art=art_g_guard),
    C(40, 44, 'works', 'card', year=199, main='守下邳', sub='行太守事', art=art_g_xiapi),
    C(44, 48, 'death', 'card', year=200, main='兵败被擒', sub='归曹', art=art_g_captured),
    # ---- 第二回 白马
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'court', 'card', year=200, main='曹操厚待', sub='偏将军', art=art_g_cao_favor),
    C(54, 58, 'night', 'card', year=200, main='心在汉', sub='张辽问之', art=art_g_heart),
    C(58, 66, 'war', 'baima', year=200),
    C(66, 70, 'empire', 'card', year=200, main='汉寿亭侯', sub='封侯', art=art_g_hanshou),
    C(70, 76, 'fate', 'card', year=200, main='挂印封金', sub='千里寻兄', art=art_g_seal),
    C(76, 78, 'war', 'card', year=200, main='过五关', sub='演义', art=art_g_pass),
    C(78, 80, 'life', 'card', year=200, main='兄弟重逢', sub='汝南', art=art_g_reunion),
    # ---- 第三回 镇守荆州
    C(80, 82, 'fate', 'chapter'),
    C(82, 86, 'court', 'card', year=214, main='督荆州', sub='一方重镇', art=art_g_jing),
    C(86, 90, 'works', 'card', year=214, main='美髯公', sub='绝伦逸群', art=art_g_beard),
    C(90, 94, 'war', 'card', year=215, main='刮骨疗毒', sub='言笑自若', art=art_g_arrow),
    C(94, 98, 'night', 'card', year=215, main='单刀会', sub='与鲁肃', art=art_g_dandao),
    C(98, 104, 'death', 'card', year=216, main='辱吴使', sub='虎女焉嫁犬子', note='虎女犬子之语出自演义', art=art_g_marry),
    C(104, 112, 'empire', 'card', year=219, main='前将军', sub='假节钺', art=art_g_fivetiger),
    # ---- 第四回 威震华夏
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'war', 'card', year=219, main='围樊城', sub='北伐', art=art_g_fancheng),
    C(118, 126, 'war', 'card', year=219, main='水淹七军', sub='于禁投降', art=art_g_flood),
    C(126, 130, 'empire', 'card', year=219, main='威震华夏', sub='一生巅峰', art=art_g_weizhen),
    C(130, 134, 'court', 'card', year=219, main='曹操议迁都', sub='避其锋芒', art=art_g_qiandu),
    C(134, 140, 'night', 'card', year=219, main='白衣渡江', sub='吕蒙偷袭', art=art_g_lumeng),
    C(140, 144, 'death', 'card', year=219, main='失荆州', sub='后院起火', art=art_g_lost),
    # ---- 第五回 麦城
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'fate', 'card', year=219, main='军心离散', sub='四面楚歌', art=art_g_scatter),
    C(150, 156, 'night', 'card', year=219, main='走麦城', sub='最后的突围', art=art_g_maicheng),
    C(156, 160, 'death', 'card', year=220, main='临沮被擒', sub='父子遇害', art=art_g_death),
    C(160, 162, 'court', 'card', year=220, main='传首曹营', sub='以诸侯礼葬', art=art_g_head),
    C(162, 164, 'works', 'card', year=220, main='两处坟茔', sub='身首异处', art=art_g_two_tombs),
    C(164, 166, 'fate', 'card', year=285, main='陈寿评曰', sub='刚而自矜', art=art_g_shou),
    C(166, 168, 'empire', 'card', year=1614, main='武圣', sub='历代加封', art=art_g_wusheng),
    C(168, 170, 'end', 'card', year=1614, main='忠义', sub='一个符号', art=art_g_yi),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='陆拾', col=QINGLONG, acc=ZAOHONG, born=170, died=220, no_age=True,
    born_lab='生年不详', died_lab='220年', years_txt='生年不详 — 公元220',
    hook_q='他威震华夏 · 为什么转眼败走麦城？',
    name_line='关羽 · 字云长', name='关羽', seal='武圣', title_art=art_g_title,
    q1='忠义武圣？', q2='骄傲误国？',
    end_art=art_g_legacy, end_big='威震华夏', end_seal='武圣',
    end_l1='他最辉煌的一仗之后', end_l2='紧跟着的是最惨的一败',
    end_brush='万众取首', end_ask='关羽失荆州 该怪谁？评论区聊聊', next='孙权'),
    scenes=dict(chapter=scene_chapter, baima=scene_baima))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
