"""千古人物志 · 第玖拾玖集 · 上官婉儿 (664–710)
Look: 翰墨蓝 + 梅妆红, little plum-blossom 花钿 corners, palace roofs of 洛阳 and 长安 behind.
Chapter card: 秤 — a steelyard; each chapter a poem-scroll hangs from the hook and the weight slides further along the beam; in the last chapter the beam hangs empty.
Set pieces: custom 8-beat scene 'cailou' (彩楼评诗), 6-beat 掖庭, 6-beat 召试, 6-beat 唐隆政变.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zuchongzhi as Zc      # engine + helpers (previous episode)
import render_long as L
import render_gufeng as G
import render_story as S
import render_full as F
import epkit
from render_gufeng import (W, H, FPS, bt, INK, ZHU, ZHE, BRUSH, SERIF, WILD, font, clamp, lerp, ease_out, ease_expo,
                           cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import (Art, person, horse, carriage, palace, flames, waves, boat, crow, arrow, flag, ground,
                          walk_x, ellipse_pts, GROUND)
from render_full import chars_in, type_in, beat_fx
from render_long import C, rider, city_wall, note_in, stage, DIM, P
from render_wangyangming import desk, scroll, lamp, sitter
from render_simayi import emperor
from render_sunwu import army, banner
from render_lishangyin import candle
from render_zhuxi import book

F.RIPPLE = False
HANMO = (52, 58, 96)                # 翰墨蓝
MEIZHUANG = (200, 92, 110)          # 梅妆红
S.LAYERS.append(('hanmo', HANMO, 0.9, 1.0))
S.LAYERS.append(('meizhuang', MEIZHUANG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='称', life='婉', court='诏', night='墨', war='变', empire='唐', works='诗', fate='宫', death='殁', end='称')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = ((200, 170, 100), 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (MEIZHUANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (HANMO, 170, (W * 0.5, 720))
G.THEMES['night']['sun'] = None
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _x in (120, 960):               # palace corner towers at the margins
    _d.polygon([(_x - 80, 1320), (_x + 80, 1320), (_x + 50, 1290), (_x - 50, 1290)], fill=(110, 106, 118, 70))
    _d.rectangle((_x - 46, 1320, _x + 46, 1420), fill=(120, 116, 126, 50))
for _k in range(3):
    _d.line((220, 1424 + _k * 12, 860, 1424 + _k * 12), fill=HANMO + (40 - _k * 10,), width=2)
MTN_COL = {'night': (26, 28, 44), 'death': (60, 58, 64), 'war': (112, 62, 60), 'fate': (92, 92, 104)}
def draw_background(t, theme):
    """宫城: soft hills, palace corner towers at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 194, 200), (164, 160, 172), MTN_COL.get(theme, (104, 104, 128))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.72))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """花钿: a five-petal plum mark in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=HANMO + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=HANMO + (220,), width=3)
        cx, cy = x + sx * 50, y + sy * 50
        for k in range(5):
            a = k * 2 * math.pi / 5 - math.pi / 2
            px, py = cx + 12 * math.cos(a), cy + 12 * math.sin(a)
            d.ellipse((px - 9, py - 9, px + 9, py + 9), fill=MEIZHUANG + (230,))
        d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(240, 210, 120, 240))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def wan(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, girl=False, **kw):
    """上官婉儿: a Tang court lady — high bun, a plum 花钿 on the brow, an ink-blue robe; as a girl, two small buns and a plain servant's dress."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', female=True, layer=layer, kneel=kneel, bow=bow, **kw)
    if kw.get('fall'):
        return hand
    top = y - (0.62 if kneel else 1.0) * h
    if girl:
        for s in (-1, 1):
            A.d[layer].ellipse((x + s * 0.06 * h - 0.04 * h, top - 0.06 * h, x + s * 0.06 * h + 0.04 * h, top + 0.02 * h), fill=255)
        if not kneel:
            A.d['mid'].polygon([(x - 0.1 * h, y - 0.62 * h), (x + 0.1 * h, y - 0.62 * h), (x + 0.14 * h, y - 0.02 * h), (x - 0.14 * h, y - 0.02 * h)], fill=170)
        return hand
    A.d[layer].ellipse((x - 0.06 * h, top - 0.14 * h, x + 0.06 * h, top + 0.02 * h), fill=255)
    A.d['meizhuang'].ellipse((x + dir * 0.03 * h - 0.015 * h, top + 0.05 * h, x + dir * 0.03 * h + 0.015 * h, top + 0.08 * h), fill=255)
    if not kneel:
        A.d['hanmo'].polygon([(x - 0.11 * h, y - 0.62 * h), (x + 0.11 * h, y - 0.62 * h), (x + 0.16 * h, y - 0.02 * h), (x - 0.16 * h, y - 0.02 * h)], fill=170)
    return hand

def empress(A, x, y, h, dir=-1, layer='ink', **kw):
    """武则天: a female sovereign — crown, long dragon robe in gold."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='crown', female=True, layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        A.d['qiuhuang'].polygon([(x - 0.11 * h, y - 0.62 * h), (x + 0.11 * h, y - 0.62 * h), (x + 0.17 * h, y - 0.02 * h), (x - 0.17 * h, y - 0.02 * h)], fill=170)
    return hand

def steelyard(A, cx, cy, s, pos, hang=True, t=0.0):
    """杆秤: a beam hung from a cord; a poem-scroll on the hook at left, a weight sliding to `pos` (0..1) on the right."""
    tilt = 0.06 * (0.5 - pos) * math.sin(t * 2) if hang else 0.0
    x0, x1 = cx - 0.4 * s, cx + s
    y0, y1 = cy + tilt * s, cy - tilt * s
    A.d['ink'].line((cx - 0.2 * s, cy - 0.6 * s, cx - 0.2 * s, cy), fill=255, width=3)
    A.d['ink'].line((x0, y0, x1, y1), fill=255, width=max(5, int(0.03 * s)))
    for k in range(10):
        mx = lerp(x0, x1, 0.3 + k * 0.07)
        A.d['qiuhuang'].ellipse((mx - 3, lerp(y0, y1, 0.3 + k * 0.07) - 3, mx + 3, lerp(y0, y1, 0.3 + k * 0.07) + 3), fill=255)
    wx = lerp(cx, x1, pos); wy = lerp(y0, y1, lerp(0.29, 1.0, pos))
    A.d['ink'].line((wx, wy, wx, wy + 0.25 * s), fill=255, width=2)
    A.d['hanmo'].polygon([(wx - 0.08 * s, wy + 0.25 * s), (wx + 0.08 * s, wy + 0.25 * s), (wx + 0.11 * s, wy + 0.42 * s), (wx - 0.11 * s, wy + 0.42 * s)], fill=255)
    if hang:
        A.d['ink'].line((x0, y0, x0, y0 + 0.2 * s), fill=255, width=2)
        A.d['wash'].rectangle((x0 - 0.12 * s, y0 + 0.2 * s, x0 + 0.12 * s, y0 + 0.62 * s), fill=255)
        A.d['ink'].rectangle((x0 - 0.12 * s, y0 + 0.2 * s, x0 + 0.12 * s, y0 + 0.62 * s), outline=200, width=3)
        for k in range(3):
            A.d['ink'].line((x0 + 0.06 * s - k * 0.06 * s, y0 + 0.26 * s, x0 + 0.06 * s - k * 0.06 * s, y0 + 0.54 * s), fill=160, width=2)

def tower(A, cx, base, w):
    """彩楼: a tall decorated tower with silk banners."""
    A.d['mid'].rectangle((cx - 0.6 * w, base - 1.6 * w, cx + 0.6 * w, base), fill=210)
    A.d['ink'].polygon([(cx - 0.9 * w, base - 1.6 * w), (cx + 0.9 * w, base - 1.6 * w), (cx + 0.5 * w, base - 1.9 * w), (cx - 0.5 * w, base - 1.9 * w)], fill=255)
    A.d['ink'].rectangle((cx - 0.7 * w, base - 1.0 * w, cx + 0.7 * w, base - 0.95 * w), fill=255)
    for s in (-1, 1):
        A.d['meizhuang'].rectangle((cx + s * 0.62 * w - 10, base - 1.55 * w, cx + s * 0.62 * w + 10, base - 0.9 * w), fill=255)

def sheet(A, x, y, s, ang=0.0, layer='wash'):
    c, si = math.cos(ang), math.sin(ang)
    pts = [(-0.5, -0.7), (0.5, -0.7), (0.5, 0.7), (-0.5, 0.7)]
    A.d[layer].polygon([(x + (px * c - py * si) * s, y + (px * si + py * c) * s) for px, py in pts], fill=255)
    A.d['ink'].polygon([(x + (px * c - py * si) * s, y + (px * si + py * c) * s) for px, py in pts], outline=150)

# ================================================================ chapter card
CH = {16: 0.1, 48: 0.3, 80: 0.55, 112: 0.85, 144: None}
def art_scale_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    pos = CH.get(kb, 0.3)
    q = ease_out(u / (1.4 * P))
    if pos is None:
        steelyard(A, 540, 1000, 300, lerp(0.85, 0.5, q), hang=False, t=t)
    else:
        steelyard(A, 540, 1000, 300, lerp(max(0.0, pos - 0.2), pos, q), t=t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_scale_chapter)
    ink_in(cv, text_img(no, SERIF, 56, HANMO, 'Black', bleed=False, spacing=12), W / 2, 1330, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1450, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_w_hook_scale(A, cv, t, u):
    steelyard(A, 540, 1040, 320, clamp(u / (1.4 * P)) * 0.8, t=t)

def art_w_hook_baby(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, female=True, baby=True, kneel=True, bow=20, arm=60, layer='ink')

def art_w_hook_plum(A, cv, t, u):
    ground(A, GROUND)
    wan(A, 540, GROUND, 340, dir=1, arm=-8)

def art_w_hook_candle(A, cv, t, u):
    ground(A, GROUND)
    candle(A, 540, GROUND, 160, clamp(u / (2 * P)), t)

# ================================================================ 第一回 掖庭
def art_w_grandfather(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    person(A, 400, GROUND, 200, dir=1, robe=True, hat='knot', kneel=True, bow=30, arm=-8, layer='ink')
    empress(A, 720, GROUND, 210, dir=-1, arm=80)
    A.flush(cv)
    paste(cv, text_img('祖父上官仪替高宗起草废后诏书', SERIF, 44, HANMO, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '事泄 被武后所杀 父亲同死', t, t - u + P)

def art_w_birth(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 210, dir=1, female=True, baby=True, arm=60, layer='ink')
    A.flush(cv)
    paste(cv, text_img('她出生不久 随母亲没入掖庭为奴', SERIF, 44, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '掖庭 宫中罪人家属服役之所', t, t - u + P)

def art_w_dream(A, cv, t, u):
    ground(A, GROUND)
    person(A, 360, GROUND, 180, dir=1, female=True, kneel=True, arm=-8, layer='ink')
    A.d['wash'].ellipse((480, 880, 960, 1300), fill=80)
    steelyard(A, 660, 1060, 200, 0.6, t=t)
    A.flush(cv)
    paste(cv, text_img('相传母亲梦人送秤 说持此称量天下', SERIF, 44, HANMO, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见新唐书 神异之说', t, t - u + P)

def art_w_yeting(A, cv, t, u):
    """6-beat set piece: 掖庭 — growing up in servitude; the mother teaches her to read by night; she reads everything."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        for k in range(4):
            person(A, 200 + k * 140, GROUND, 150, dir=1, female=True, bow=40, arm=150, layer='mid')
        wan(A, 820, GROUND, 110, dir=-1, girl=True, bow=30, arm=150)
        lab = '在掖庭做苦役'
    else:
        desk(A, 560, GROUND, 400, layer='mid')
        person(A, 760, GROUND, 180, dir=-1, female=True, kneel=True, arm=80, layer='ink')
        wan(A, 360, GROUND, 130 + 20 * clamp((ph - 2) / 4), dir=1, girl=True, kneel=True, arm=100)
        lamp(A, 560, GROUND - 74, 26, t, glow=0.9)
        lab = '母亲夜里教她读书' if ph < 4 else '天性聪敏 文采出众'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 50, HANMO, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '母亲郑氏 出身荥阳郑氏', t, t - u + 2 * P)

def art_w_test(A, cv, t, u):
    """6-beat set piece: 召试 — at fourteen she is summoned by 武则天 and given a subject; the piece is done on the spot; she is freed and set to court documents."""
    ph = u / P
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    empress(A, 760, GROUND, 220, dir=-1, arm=60 if ph < 2 else -8)
    wan(A, 360, GROUND, 170, dir=1, girl=ph < 4, kneel=ph < 4, arm=100 if 2 <= ph < 4 else -8, bow=20 if ph >= 4 else 0)
    if 2 <= ph < 4:
        A.d['wash'].rectangle((440, GROUND - 70, 560, GROUND - 40), fill=255)
    A.flush(cv)
    if ph < 2:
        lab = '十四岁 武则天召见试文'
    elif ph < 4:
        lab = '援笔立成 文意俱佳'
    else:
        lab = '免去奴籍 掌管宫中文书'
    paste(cv, text_img(lab, SERIF, 50, HANMO if ph < 4 else ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '仇人之孙 为仇人所用', t, t - u + 4 * P)

# ================================================================ 第二回 制诰
def art_w_brand(A, cv, t, u):
    ground(A, GROUND)
    wan(A, 540, GROUND, 340, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('相传曾忤旨 被黥面 以梅花妆遮掩', SERIF, 44, MEIZHUANG, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '黥面见野史笔记 梅花妆起源之说为民间传说', t, t - u + P)

def art_w_decrees(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 460, layer='mid')
    wan(A, 300, GROUND, 190, dir=1, kneel=True, arm=lerp(95, 110, 0.5 + 0.5 * math.sin(t * 5)))
    for k in range(min(8, int(u / (0.3 * P)) + 1)):
        sheet(A, 440 + k * 50, GROUND - 90 - (k % 2) * 6, 40)
    A.flush(cv)
    paste(cv, text_img('百司表奏 多令参决', SERIF, 52, HANMO, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '武则天晚年 诏令多出其手', t, t - u + P)

def art_w_trust(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    empress(A, 700, GROUND, 220, dir=-1, arm=60)
    wan(A, 420, GROUND, 190, dir=1, bow=20, arm=60)
    A.flush(cv)
    paste(cv, text_img('成为女皇身边最信任的人', SERIF, 48, HANMO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_w_shenlong(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    army(A, lerp(-200, 120, ease_out(u / (2 * P))), GROUND, 7, dir=1, t=t, march=True, h=110)
    A.flush(cv)
    paste(cv, text_img('神龙政变 武则天退位 中宗复位', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_zhaorong(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    emperor(A, 740, GROUND, 210, dir=-1, arm=60)
    wan(A, 400, GROUND, 190, dir=1, kneel=True, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('中宗册封她为昭容 专掌制命', SERIF, 46, HANMO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('昭容', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第三回 称量
def art_w_xiuwen(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='hanmo')
    ground(A, GROUND)
    for k in range(5):
        person(A, 160 + k * 90, GROUND, 150, dir=1, robe=True, hat='knot', arm=60, layer='mid')
    wan(A, 800, GROUND, 190, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('建议设修文馆 广召天下文士', SERIF, 46, HANMO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_cailou(cv, t, c, k):
    """8-beat custom scene: 彩楼评诗 — at a court banquet the ministers write poems; she sits up in a decorated tower and drops
    the losers' sheets one by one until only two remain, 沈佺期 and 宋之问; at last one sheet comes down — 宋之问 wins."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    tower(A, 540, GROUND, 200)
    wan(A, 540, GROUND - 200 * 1.0, 120, dir=1, kneel=True, arm=60)
    for kk in range(5):
        person(A, 140 + kk * 70 if kk < 3 else 820 + (kk - 3) * 80, GROUND, 140, dir=1 if kk < 3 else -1, robe=True, hat='knot', arm=140 if ph > 1 else -8, layer='mid')
    rng = random.Random(99)
    n_fall = int(clamp((ph - 1) / 4) * 14)
    for i in range(n_fall):
        f = clamp((ph - 1 - i * 4 / 14) / 1.2)
        x0 = 540 + rng.uniform(-60, 60)
        x = x0 + rng.uniform(-380, 380) * f
        y = lerp(GROUND - 260, GROUND - 20, f) + 30 * math.sin(t * 3 + i) * (1 - f)
        sheet(A, x, y, 28, ang=rng.uniform(-1, 1) * (1 - f) + (0.3 if f >= 1 else 0))
    if ph > 6:
        f = clamp((ph - 6) / 1.2)
        sheet(A, 540 + 200 * f, lerp(GROUND - 260, GROUND - 20, f), 34, layer='meizhuang')
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '称量天下', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=99)
    fx.flush(cv)
    if ph < 1:
        lab, col = '中宗游昆明池 群臣赋诗百余篇', HANMO
    elif ph < 5:
        lab, col = '她在彩楼上评诗 落选者纷纷飘下', HANMO
    elif ph < 6:
        lab, col = '只剩沈佺期 宋之问两篇', HANMO
    else:
        lab, col = '不愁明月尽 自有夜珠来 宋诗胜出', ZHU
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=2), W / 2, 575, 1, 1)
    note_in(cv, '事见唐诗纪事', t, s0 + 3 * P)

def art_w_poets(A, cv, t, u):
    ground(A, GROUND)
    for k in range(min(6, int(u / (0.3 * P)) + 1)):
        book(A, 220 + k * 120, GROUND, 90, 160, layer='hanmo' if k % 2 else 'mid')
    A.flush(cv)
    paste(cv, text_img('一时文风大盛 朝野争相作诗', SERIF, 46, HANMO, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '为盛唐诗歌铺路', t, t - u + P)

def art_w_poem(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('叶下洞庭初\n思君万里余', SERIF, 46, INK, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('她自己的诗 彩书怨', SERIF, 50, HANMO, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_w_power(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    for k, (x, d) in enumerate(((300, 1), (540, 1), (780, -1))):
        person(A, x, GROUND, 190, dir=d, robe=True, hat='crown' if k == 0 else 'none', female=(k > 0), arm=-8, layer='ink' if k == 1 else 'mid')
    A.flush(cv)
    paste(cv, text_img('周旋在韦后与太平公主之间', SERIF, 46, HANMO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '朝中派系林立', t, t - u + P)

# ================================================================ 第四回 唐隆
def art_w_zhongzong(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    emperor(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('中宗暴崩', SERIF, 54, ZHU, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '一说为韦后与安乐公主毒杀 史家有争议', t, t - u + P)

def art_w_will(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    wan(A, 320, GROUND, 180, dir=1, kneel=True, arm=100)
    person(A, 760, GROUND, 180, dir=-1, female=True, kneel=True, arm=60, layer='mid')
    candle(A, 540, GROUND - 74, 60, 0.4, t)
    A.flush(cv)
    paste(cv, text_img('与太平公主起草遗诏', SERIF, 50, HANMO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '遗诏中让相王李旦辅政', t, t - u + P)

def art_w_tanglong(A, cv, t, u):
    """6-beat set piece: 唐隆政变 — 李隆基 storms the palace at night; she meets the troops holding a candle, with her draft of the will; she is beheaded under the banner."""
    ph = u / P
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    if ph < 2:
        army(A, lerp(-200, 160, clamp(ph / 2)), GROUND, 7, dir=1, t=t, march=True, h=110)
        flames(A, 300, GROUND - 200, 60, 40, t, n=1, seed=710, smoke=False)
        lab, col = '李隆基夜入宫城 诛杀韦后', ZHU
    elif ph < 4:
        wan(A, 620, GROUND, 190, dir=-1, arm=80)
        candle(A, 560, GROUND - 120, 50, 0.3, t)
        person(A, 360, GROUND, 200, dir=1, robe=False, hat='helmet', arm=-8, layer='ink')
        A.d['wash'].rectangle((520, GROUND - 100, 580, GROUND - 70), fill=255)
        lab, col = '她执烛率宫人迎接 出示遗诏草稿', HANMO
    else:
        banner(A, 760, GROUND, 360, t, layer='red')
        wan(A, 600, GROUND, 190, dir=-1, kneel=True, bow=30, arm=-8)
        lab, col = '李隆基不许 斩于旗下', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '年四十七', t, t - u + 4 * P)

def art_w_collect(A, cv, t, u):
    ground(A, GROUND)
    for k in range(min(20, int(u / (0.12 * P)) + 1)):
        book(A, 140 + (k % 10) * 90, GROUND - (k // 10) * 170, 70, 140, layer='hanmo' if k % 2 else 'mid')
    A.flush(cv)
    paste(cv, text_img('玄宗命人收集她的诗文 编为二十卷', SERIF, 44, HANMO, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '张说作序 今多已散佚', t, t - u + P)

def art_w_epitaph(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((360, GROUND - 260, 720, GROUND), fill=230)
    A.d['ink'].rectangle((360, GROUND - 260, 720, GROUND), outline=255, width=5)
    for k in range(10):
        A.d['ink'].line((680 - k * 32, GROUND - 230, 680 - k * 32, GROUND - 30), fill=160, width=3)
    A.flush(cv)
    paste(cv, text_img('咸阳出土上官婉儿墓志', SERIF, 50, HANMO, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '墓室早年已遭严重破坏', t, t - u + P)

# ================================================================ 第五回 称量天下
def art_w_tang(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        person(A, 220 + k * 210, GROUND, 170, dir=1, robe=True, hat='knot', arm=60, layer='ink' if k % 2 else 'mid')
    A.flush(cv)
    paste(cv, text_img('此后盛唐 诗人辈出', SERIF, 50, HANMO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '李白 杜甫 王维相继登场', t, t - u + P)

def art_w_eval(A, cv, t, u):
    ground(A, GROUND)
    wan(A, 540, GROUND, 280, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('有人说她是权谋之臣 有人说她是一代才女', SERIF, 42, HANMO, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))

def art_w_end(A, cv, t, u):
    steelyard(A, 540, 1060, 300, 0.5, hang=False, t=t)
    A.flush(cv)
    paste(cv, text_img('称量天下士', SERIF, 56, HANMO, 'Black', bleed=False, spacing=10), W / 2, 760, 1, clamp(u / 0.4))

def art_w_legacy(A, cv, t, u):
    steelyard(A, 840, 1380, 70, 0.5, t=t)

def art_w_title(A, cv, t, u):
    steelyard(A, 780, 1100, 140, 0.6, t=t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    wan(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '掖庭'), 48: ('第二回', '制诰'), 80: ('第三回', '称量'),
            112: ('第四回', '唐隆'), 144: ('第五回', '才女')}

CARDS = [
    C(0, 2, 'works', 'num', num='一杆秤', line='称量天下文士', art=art_w_hook_scale),
    C(2, 4, 'fate', 'num', num='襁褓为奴', line='祖父被武后所杀', art=art_w_hook_baby),
    C(4, 6, 'life', 'num', num='十四岁', line='却成了武后的秘书', art=art_w_hook_plum),
    C(6, 8, 'death', 'num', num='一支蜡烛', line='照亮了她最后一夜', art=art_w_hook_candle),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 掖庭
    C(16, 18, 'fate', 'chapter'),
    C(18, 22, 'death', 'card', year=664, main='祖父被杀', sub='上官仪', art=art_w_grandfather),
    C(22, 26, 'fate', 'card', year=664, main='没入掖庭', sub='襁褓为奴', art=art_w_birth),
    C(26, 30, 'night', 'card', year=664, main='称量天下', sub='母亲之梦', art=art_w_dream),
    C(30, 36, 'life', 'card', year=670, main='掖庭', sub='母亲教读', note='年份约略', art=art_w_yeting),
    C(36, 48, 'court', 'card', year=677, main='召试', sub='十四岁', art=art_w_test),
    # ---- 第二回 制诰
    C(48, 50, 'court', 'chapter'),
    C(50, 56, 'fate', 'card', year=690, main='梅花妆', sub='传说', note='年份无考', art=art_w_brand),
    C(56, 62, 'works', 'card', year=696, main='参决', sub='掌管诏命', note='年份约略', art=art_w_decrees),
    C(62, 68, 'empire', 'card', year=700, main='心腹', sub='女皇近臣', note='年份约略', art=art_w_trust),
    C(68, 74, 'war', 'card', year=705, main='神龙政变', sub='中宗复位', art=art_w_shenlong),
    C(74, 80, 'court', 'card', year=705, main='昭容', sub='专掌制命', art=art_w_zhaorong),
    # ---- 第三回 称量
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'empire', 'card', year=708, main='修文馆', sub='广召文士', art=art_w_xiuwen),
    C(86, 94, 'works', 'cailou', year=709),
    C(94, 100, 'life', 'card', year=709, main='文风大盛', sub='朝野作诗', art=art_w_poets),
    C(100, 106, 'night', 'card', year=709, main='彩书怨', sub='她的诗', note='作年不详', art=art_w_poem),
    C(106, 112, 'fate', 'card', year=709, main='周旋', sub='派系之间', art=art_w_power),
    # ---- 第四回 唐隆
    C(112, 114, 'war', 'chapter'),
    C(114, 118, 'death', 'card', year=710, main='中宗暴崩', sub='宫廷巨变', art=art_w_zhongzong),
    C(118, 124, 'night', 'card', year=710, main='遗诏', sub='与太平公主', art=art_w_will),
    C(124, 132, 'war', 'card', year=710, main='唐隆政变', sub='执烛相迎', art=art_w_tanglong),
    C(132, 138, 'works', 'card', year=713, main='二十卷', sub='玄宗命编', note='年份约略', art=art_w_collect),
    C(138, 144, 'court', 'card', year=2013, main='墓志出土', sub='咸阳', art=art_w_epitaph),
    # ---- 第五回 才女
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'life', 'card', year=2013, main='盛唐之前', sub='铺路之人', art=art_w_tang),
    C(152, 160, 'fate', 'card', year=2013, main='功过', sub='后人评说', art=art_w_eval),
    C(160, 170, 'end', 'card', year=2013, main='称量天下', sub='一代才女', art=art_w_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='玖拾玖', col=HANMO, acc=MEIZHUANG, born=664, died=710, age0=663,
    born_lab='664年', died_lab='710年', years_txt='公元664 — 710',
    hook_q='仇人杀了她全家 · 她为什么还替仇人写了半辈子诏书？',
    name_line='上官婉儿 · 唐昭容', name='上官婉儿', seal='昭容', title_art=art_w_title,
    q1='一代才女？', q2='弄权之人？',
    end_art=art_w_legacy, end_big='称量天下', end_seal='婉儿',
    end_l1='她从掖庭的奴婢', end_l2='走到了替天下文人打分的位置',
    end_brush='称量天下', end_ask='你怎么看上官婉儿这个人？评论区聊聊', next='颜真卿'),
    scenes=dict(chapter=scene_chapter, cailou=scene_cailou))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
