"""千古人物志 · 第玖拾壹集 · 纪晓岚 (1724–1805)
Look: 四库绿 + 铜烟色, little book-case corners, a study-window lattice behind.
Chapter card: 经史子集 — a four-bay book case (green, red, blue, grey covers like the 四库 bindings) that fills shelf by shelf.
Set pieces: custom 8-beat scene 'siku' (四库全书), 6-beat 盐案, 6-beat 遣戍, 6-beat 禁书, 6-beat 斗和珅 (labelled 影视演绎), 6-beat 阅微草堂.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zhengchenggong as Zc  # engine + helpers (previous episode)
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
from render_wangyangming import desk, scroll, lamp
from render_simayi import emperor
from render_zhuxi import book
from render_wudi import camel
from render_lishangyin import candle

F.RIPPLE = False
SIKULV = (70, 110, 84)              # 四库绿
TONGYAN = (176, 112, 56)            # 铜烟色
S.LAYERS.append(('sikulv', SIKULV, 0.9, 1.0))
S.LAYERS.append(('tongyan', TONGYAN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='书', life='纪', court='清', night='微', war='戍', empire='库', works='书', fate='谪', death='逝', end='阅')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (TONGYAN, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (SIKULV, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (TONGYAN, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _x in (60, 940):                # study-window lattice at the margins
    for _i in range(5):
        _d.line((_x, 1300 + _i * 28, _x + 80, 1300 + _i * 28), fill=SIKULV + (60,), width=2)
    for _i in range(4):
        _d.line((_x + _i * 26, 1300, _x + _i * 26, 1412), fill=SIKULV + (60,), width=2)
for _k in range(3):
    _d.line((160, 1424 + _k * 12, 920, 1424 + _k * 12), fill=TONGYAN + (40 - _k * 10,), width=2)
MTN_COL = {'night': (30, 34, 40), 'death': (60, 60, 62), 'war': (120, 100, 80), 'fate': (96, 98, 96)}
def draw_background(t, theme):
    """京城书斋: far hills, a lattice window at each margin, a faint desk line."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 194, 186), (166, 168, 156), MTN_COL.get(theme, (110, 124, 110))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.72))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

BOOKCOL = [SIKULV, (170, 60, 50), (50, 80, 130), (120, 120, 116)]
def draw_frame_border(canvas):
    """书函: four little book spines (经史子集 colours) in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=SIKULV + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=SIKULV + (220,), width=3)
        cx, cy = x + sx * 44, y + sy * 40
        for k, col in enumerate(BOOKCOL):
            bx = cx + sx * k * 13
            d.rectangle((min(bx, bx + sx * 10), cy - 18, max(bx, bx + sx * 10), cy + 18), fill=col + (220,))

# ================================================================ primitives
def qhat(A, x, y, h, layer='ink'):
    """清官帽: a cone with a red knob on top."""
    A.d[layer].polygon([(x - 0.13 * h, y - 0.95 * h), (x + 0.13 * h, y - 0.95 * h), (x, y - 1.12 * h)], fill=255)
    A.d['red'].ellipse((x - 0.025 * h, y - 1.16 * h, x + 0.025 * h, y - 1.1 * h), fill=255)

def ji_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, pipe=True, t=0.0, **kw):
    """纪晓岚: a Qing official in a green robe and cone hat, with his famous long tobacco pipe."""
    b = bow + 8 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    if kw.get('fall'):
        return hand
    if up:
        qhat(A, x, y, h, layer)
        A.d['wash' if old > 0.4 else layer].polygon([(x, y - 0.85 * h), (x + dir * 0.08 * h, y - 0.85 * h), (x + dir * 0.04 * h, y - 0.68 * h)], fill=255)
        if pipe:
            mx, my = x + dir * 0.07 * h, y - 0.86 * h
            A.d['tongyan'].line((mx, my, mx + dir * 0.34 * h, my + 0.2 * h), fill=255, width=max(3, int(0.018 * h)))
            A.d['tongyan'].ellipse((mx + dir * 0.34 * h - 0.03 * h, my + 0.17 * h, mx + dir * 0.34 * h + 0.03 * h, my + 0.23 * h), fill=255)
            for k in range(3):
                f = ((t * 0.6 + k / 3) % 1)
                r = (0.02 + 0.04 * f) * h
                sx, sy = mx + dir * 0.34 * h + dir * 0.05 * h * f, my + 0.15 * h - 0.3 * h * f
                A.d['wash'].ellipse((sx - r, sy - r, sx + r, sy + r), fill=int(160 * (1 - f)))
    top = y - (0.48 if kneel else 0.76) * h
    A.d['sikulv'].polygon([(x - 0.1 * h, top), (x + 0.1 * h, top), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=150)
    return hand

def heshen(A, x, y, h, dir=-1, layer='mid', **kw):
    """和珅: a portly grandee in a gold-brown robe and cone hat."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        qhat(A, x, y, h, layer)
        A.d['tongyan'].ellipse((x - 0.16 * h, y - 0.7 * h, x + 0.16 * h, y - 0.3 * h), fill=200)
    return hand

def shelf(A, cx, base, w, h, fill, layer='mid'):
    """经史子集: a four-bay case; each bay holds rows of book boxes in its own colour; `fill` 0..1 fills shelf by shelf."""
    A.d[layer].rectangle((cx - w, base - h, cx + w, base), fill=150)
    A.d['ink'].rectangle((cx - w, base - h, cx + w, base), outline=255, width=5)
    bw = 2 * w / 4
    rows = 5
    n = int(round(fill * rows * 4))
    lays = ['sikulv', 'zaohong', 'chaoshui', 'mid']
    for b in range(4):
        x0 = cx - w + b * bw
        A.d['ink'].line((x0, base - h, x0, base), fill=255, width=4)
        for r in range(rows):
            y1 = base - r * h / rows - 6
            A.d['ink'].line((x0, y1 + 6, x0 + bw, y1 + 6), fill=200, width=3)
            if r * 4 + b < n:
                for k in range(4):
                    bx = x0 + 10 + k * (bw - 20) / 4
                    A.d[lays[b]].rectangle((bx, y1 - h / rows + 16, bx + (bw - 20) / 4 - 6, y1), fill=235)

def snow(A, t, n=40, seed=91):
    rng = random.Random(seed)
    for k in range(n):
        x = (rng.random() * W + 30 * math.sin(t + k)) % W
        y = (rng.random() * H * 0.7 + t * 60 * (0.5 + rng.random())) % (H * 0.7) + 500
        A.d['wash'].ellipse((x - 4, y - 4, x + 4, y + 4), fill=230)

# ================================================================ chapter card
CH = {16: (0.0, 0.25), 48: (0.25, 0.45), 80: (0.45, 1.0), 112: (1.0, 1.0), 144: (1.0, 1.0)}
def art_shelf_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (0.2, 0.5))
    q = ease_out(u / (1.4 * P))
    shelf(A, 540, 1220, 300, 340, lerp(a, b, q))
    if kb == 144:
        lamp(A, 540, 840, 34, t, glow=0.9)
    A.flush(cv)
    for i, ch in enumerate('经史子集'):
        paste(cv, text_img(ch, SERIF, 36, INK, 'Black', bleed=False), 540 - 300 + 75 + i * 150, 1250, 1, clamp(q / 0.3))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_shelf_chapter)
    ink_in(cv, text_img(no, SERIF, 56, SIKULV, 'Black', bleed=False, spacing=12), W / 2, 1320, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1445, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_j_hook_books(A, cv, t, u):
    shelf(A, 540, 1300, 320, 360, clamp(u / (1.4 * P)))

def art_j_hook_pipe(A, cv, t, u):
    ground(A, GROUND)
    ji_(A, 460, GROUND, 320, dir=1, arm=60, t=t)

def art_j_hook_exile(A, cv, t, u):
    for k in range(3):
        x = 220 + k * 320
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 300), (x + 240, GROUND)], fill=160)
        A.d['wash'].polygon([(x - 60, GROUND - 225), (x, GROUND - 300), (x + 60, GROUND - 225)], fill=255)
    ground(A, GROUND)
    camel(A, lerp(200, 600, ease_out(u / (2 * P))), GROUND, 170, dir=1, ph=t * 3)
    snow(A, t)

def art_j_hook_tv(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((180, 940, 900, 1380), outline=255, width=14)
    ji_(A, 400, 1340, 300, dir=1, arm=lerp(-8, 80, 0.5 + 0.5 * math.sin(t * 3)), t=t)
    heshen(A, 700, 1340, 300, dir=-1, arm=lerp(-8, 60, 0.5 + 0.5 * math.cos(t * 3)))

# ================================================================ 第一回 献县
def art_j_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x - 40, GROUND - 160), (x + 40, GROUND - 160), (x + 240, GROUND)], fill=130)
    A.d['wash'].rectangle((380, GROUND - 200, 700, GROUND), fill=255)
    A.d['ink'].polygon([(350, GROUND - 200), (730, GROUND - 200), (540, GROUND - 270)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('生于直隶河间府献县', SERIF, 48, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('献县', 56), 860, 1020, t, t - u + P, rot=6)

def art_j_family(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='mid')
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='knot', kneel=True, arm=90, layer='mid')
    person(A, 330, GROUND, 120, dir=1, robe=True, hat='none', kneel=True, arm=100, layer='ink')
    A.flush(cv)
    paste(cv, text_img('父亲纪容舒 精于考据', SERIF, 48, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '纪家世代读书', t, t - u + P)

def art_j_jieyuan(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    ji_(A, 540, GROUND, 200, dir=1, arm=60, pipe=False, t=t)
    A.flush(cv)
    paste(cv, text_img('顺天乡试第一名', SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('解元', 56), 860, 1020, t, t - u + P, rot=6)

def art_j_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for k in range(4):
        person(A, 220 + k * 120, GROUND, 150, dir=1, robe=True, hat='none', bow=20, arm=60, layer='mid')
    ji_(A, 760, GROUND, 190, dir=-1, arm=60, pipe=False, t=t)
    A.flush(cv)
    paste(cv, text_img('三十一岁中进士 入翰林院', SERIF, 46, SIKULV, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_pipe(A, cv, t, u):
    ground(A, GROUND)
    ji_(A, 440, GROUND, 300, dir=1, arm=60, t=t)
    A.flush(cv)
    paste(cv, text_img('嗜烟如命 人称纪大烟袋', SERIF, 48, TONGYAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '烟袋之说出自清人笔记 多有夸张', t, t - u + P)

def art_j_liujing(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 760, GROUND, 200, dir=-1, arm=60)
    ji_(A, 380, GROUND, 180, dir=1, bow=30, arm=-8, t=t)
    A.flush(cv)
    paste(cv, text_img('外放知府 乾隆留他在京', SERIF, 48, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '以学问优长 加四品衔留任', t, t - u + P)

# ================================================================ 第二回 戍边
def art_j_salt(A, cv, t, u):
    """6-beat set piece: 盐案 — his in-law 卢见曾 is to be searched over the 两淮 salt-tax deficit; 纪昀 warns him; the leak is traced back."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        for k in range(6):
            A.d['wash'].rectangle((160 + k * 80, GROUND - 90 - (k % 2) * 30, 220 + k * 80, GROUND), fill=255)
            A.d['ink'].rectangle((160 + k * 80, GROUND - 90 - (k % 2) * 30, 220 + k * 80, GROUND), outline=200, width=3)
        lab, col = '两淮盐引亏空 案发', SIKULV
    elif ph < 4:
        desk(A, 540, GROUND, 360, layer='mid')
        ji_(A, 320, GROUND, 170, dir=1, kneel=True, arm=100, pipe=False, t=t)
        A.d['wash'].rectangle((500, GROUND - 110, 600, GROUND - 76), fill=255)
        A.d['sikulv'].ellipse((520, GROUND - 100, 540, GROUND - 86), fill=255)
        A.d['wash'].ellipse((560, GROUND - 100, 580, GROUND - 86), fill=255)
        lab, col = '亲家卢见曾 他暗中报信', SIKULV
    else:
        ji_(A, 540, GROUND, 190, dir=1, kneel=True, bow=30, arm=-8, pipe=False, t=t)
        lab, col = '事泄 革职问罪', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '以茶叶和盐封入空信传话 系民间传说', t, t - u + 2 * P)

def art_j_exile(A, cv, t, u):
    """6-beat set piece: 遣戍 — the long road to 乌鲁木齐 over the snow mountains, a camel caravan."""
    ph = u / P
    for k in range(3):
        x = 220 + k * 320
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 320), (x + 240, GROUND)], fill=160)
        A.d['wash'].polygon([(x - 60, GROUND - 240), (x, GROUND - 320), (x + 60, GROUND - 240)], fill=255)
    ground(A, GROUND)
    camel(A, lerp(-100, 700, ph / 6), GROUND, 170, dir=1, ph=t * 3)
    ji_(A, lerp(-260, 540, ph / 6), GROUND, 170, dir=1, ph=t * 3, arm=-8, pipe=False, t=t)
    snow(A, t)
    A.flush(cv)
    lab = '遣戍乌鲁木齐' if ph < 3 else '万里西行 一路风雪'
    paste(cv, text_img(lab, SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '时年四十五', t, t - u + P)

def art_j_urumqi(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='迪化', layer='mid', open_=1.0)
    ground(A, GROUND)
    ji_(A, 540, GROUND, 190, dir=1, arm=60, t=t)
    A.flush(cv)
    paste(cv, text_img('在军中掌管文书', SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '乌鲁木齐清时称迪化', t, t - u + P)

def art_j_poems(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('乌鲁木齐杂诗', SERIF, 60, INK, 'Black', bleed=False, spacing=12), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('写下一百六十首边塞风物', SERIF, 46, SIKULV, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_j_return(A, cv, t, u):
    ground(A, GROUND)
    ji_(A, lerp(900, 400, ease_out(u / (3 * P))), GROUND, 190, dir=-1, ph=t * 2, arm=-8, t=t)
    A.flush(cv)
    paste(cv, text_img('遇赦东归 回到京城', SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_j_fuzhi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    ji_(A, 540, GROUND, 200, dir=1, arm=60, t=t)
    A.flush(cv)
    paste(cv, text_img('重入翰林 授编修', SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 四库
def art_j_guan(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 760, GROUND, 200, dir=-1, arm=lerp(-8, 60, clamp((u - P) / 0.4)))
    ji_(A, 380, GROUND, 180, dir=1, kneel=True, bow=30, arm=-8, t=t)
    A.flush(cv)
    paste(cv, text_img('开四库全书馆 任总纂官', SERIF, 48, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '时年五十', t, t - u + P)

def scene_siku(cv, t, c, k):
    """8-beat custom scene: 四库全书 — books gathered from the whole empire; reviewed and summarised;
    three thousand-odd copyists write it all out by hand; seven sets for seven pavilions."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    if ph < 2:
        for i in range(min(16, int(ph * 8) + 1)):
            book(A, 160 + (i % 8) * 110, GROUND - (i // 8) * 170, 80, 140, layer=['sikulv', 'zaohong', 'chaoshui', 'mid'][i % 4])
        lab, col = '向天下征集图书 一万余种', SIKULV
    elif ph < 4:
        desk(A, 560, GROUND, 440, layer='mid')
        for i in range(5):
            book(A, 420 + i * 60, GROUND - 74, 50, 0, layer='sikulv', open_=1.0) if i == 2 else book(A, 420 + i * 60, GROUND - 74, 40, 70 + 20 * i, layer='mid')
        ji_(A, 260, GROUND, 180, dir=1, kneel=True, arm=100, t=t)
        lab, col = '逐部校勘 撰写提要', SIKULV
    elif ph < 6:
        for r in range(2):
            for j in range(5):
                x = 170 + j * 180; y = GROUND - r * 220
                A.d['mid'].rectangle((x + 30, y - 70, x + 130, y - 58), fill=255)
                person(A, x, y, 110, dir=1, robe=True, hat='none', kneel=True, arm=lerp(90, 110, 0.5 + 0.5 * math.sin(t * 6 + j + r)), layer='ink')
        lab, col = '三千八百余人 一笔一画抄写', SIKULV
    else:
        for i in range(min(7, int((ph - 6) * 4) + 1)):
            palace(A, 160 + i * 127, GROUND - 40, 60, layer='sikulv')
        lab, col = '共抄七部 分藏七阁', ZHU
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '四库全书', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=91)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '收书三千四百余种 约八亿字', t, s0 + 4 * P)

def art_j_tiyao(A, cv, t, u):
    ground(A, GROUND)
    for i in range(min(10, int(u / (0.3 * P)) + 1)):
        book(A, 180 + i * 80, GROUND, 66, 160 + (i % 3) * 20, layer='sikulv' if i % 2 else 'mid')
    A.flush(cv)
    paste(cv, text_img('四库全书总目 二百卷', SERIF, 48, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '提要多经他亲手删定', t, t - u + P)

def art_j_ban(A, cv, t, u):
    """6-beat set piece: 寓禁于征 — while gathering books, the court also banned and burned those it disliked."""
    ph = u / P
    ground(A, GROUND)
    for i in range(6):
        book(A, 220 + i * 110, GROUND, 80, 150, layer='mid')
    if ph >= 2:
        flames(A, 540, GROUND, 640, 260 * clamp((ph - 2) / 1), t, n=6, seed=1774, smoke=True)
    A.flush(cv)
    lab, col = ('征书的同时 也在查禁', SIKULV) if ph < 2 else ('违碍之书 或删改 或焚毁', ZHU)
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '修书期间禁毁书籍约三千种', t, t - u + 2 * P)

def art_j_first(A, cv, t, u):
    palace(A, 540, 1300, 340, layer='sikulv')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('第一部抄成 藏于文渊阁', SERIF, 48, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('文渊', 56), 860, 1020, t, t - u + P, rot=6)

def art_j_seven(A, cv, t, u):
    ground(A, GROUND)
    for i in range(min(7, int(u / (0.4 * P)) + 1)):
        palace(A, 150 + i * 130, GROUND - 40, 60, layer='sikulv')
    A.flush(cv)
    paste(cv, text_img('北四阁 南三阁', SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '文渊 文源 文津 文溯 文汇 文宗 文澜', t, t - u + P)

# ================================================================ 第四回 宦海
def art_j_laotouzi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 760, GROUND, 200, dir=-1, arm=60)
    ji_(A, 380, GROUND, 180, dir=1, bow=20, arm=lerp(-8, 60, 0.5 + 0.5 * math.sin(t * 3)), pipe=False, t=t)
    A.flush(cv)
    paste(cv, text_img('背后称乾隆老头子', SERIF, 46, TONGYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '野史传说 他巧解为万寿无疆之意', t, t - u + P)

def art_j_heshen(A, cv, t, u):
    """6-beat set piece: 斗和珅 — the TV version (inside a frame), then the record: little actual sparring between them."""
    ph = u / P
    ground(A, GROUND)
    if ph < 3:
        A.d['ink'].rectangle((160, 900, 920, 1400), outline=255, width=14)
        ji_(A, 380, 1360, 300, dir=1, arm=lerp(-8, 80, 0.5 + 0.5 * math.sin(t * 3)), t=t)
        heshen(A, 700, 1360, 300, dir=-1, arm=lerp(-8, 60, 0.5 + 0.5 * math.cos(t * 3)))
        lab, col = '电视剧里 他与和珅斗智', TONGYAN
    else:
        ji_(A, 300, GROUND, 190, dir=1, arm=-8, t=t)
        heshen(A, 800, GROUND, 190, dir=-1, arm=-8)
        lab, col = '史书中 二人少有正面交锋', SIKULV
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '斗和珅情节多为影视演绎', t, t - u + 0.5 * P)

def art_j_yuewei(A, cv, t, u):
    """6-beat set piece: 阅微草堂 — at night, by lamplight, he writes down ghost and fox stories; their shadows play on the wall."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    ji_(A, 300, GROUND, 180, dir=1, kneel=True, arm=100, old=0.5, t=t)
    candle(A, 700, GROUND - 74, 80, clamp(ph / 6), t)
    if ph >= 2:
        a = int(140 * clamp((ph - 2) / 1))
        fx = 760 + 30 * math.sin(t)
        A.d['wash'].polygon([(fx, 1040), (fx + 60, 1000), (fx + 120, 1040), (fx + 150, 1120), (fx + 40, 1130)], fill=a)
        A.d['wash'].polygon([(fx + 10, 1040), (fx + 20, 990), (fx + 40, 1030)], fill=a)
        A.d['wash'].polygon([(fx + 80, 1035), (fx + 100, 985), (fx + 110, 1030)], fill=a)
        A.d['wash'].line((fx + 150, 1110, fx + 230, 1060), fill=a, width=18)
    A.flush(cv)
    lab = '晚年写阅微草堂笔记' if ph < 3 else '谈狐说鬼 意在劝世'
    paste(cv, text_img(lab, SERIF, 48, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '自号观弈道人', t, t - u + 3 * P)

def art_j_five(A, cv, t, u):
    ground(A, GROUND)
    for i in range(min(5, int(u / (0.5 * P)) + 1)):
        book(A, 240 + i * 150, GROUND, 110, 200, layer='sikulv')
    A.flush(cv)
    paste(cv, text_img('前后十年 五种成书', SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '共二十四卷', t, t - u + P)

def art_j_qianlong(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    A.d['wash'].rectangle((300, 1250, 780, 1290), fill=230)
    A.flush(cv)
    paste(cv, text_img('乾隆驾崩', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '纪昀已侍奉他四十余年', t, t - u + P)

def art_j_hefall(A, cv, t, u):
    ground(A, GROUND)
    heshen(A, 540, GROUND, 220, dir=-1, kneel=u > P, arm=-8)
    A.flush(cv)
    paste(cv, text_img('嘉庆赐和珅自尽', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '和珅倒台与纪晓岚并无直接关系', t, t - u + P)

# ================================================================ 第五回 文达
def art_j_daxueshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    ji_(A, 540, GROUND, 200, dir=1, arm=60, old=0.8, t=t)
    A.flush(cv)
    paste(cv, text_img('八十岁 任协办大学士', SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_j_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    ji_(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('纪昀病逝于京城', SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_j_wenda(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((440, GROUND - 420, 640, GROUND), fill=230)
    A.d['ink'].rectangle((440, GROUND - 420, 640, GROUND), outline=255, width=5)
    A.flush(cv)
    paste(cv, text_img('谥\n文\n达', SERIF, 60, INK, 'Black', bleed=False, spacing=8), W / 2, GROUND - 210, 1, clamp((u - 0.5 * P) / 0.4))
    paste(cv, text_img('嘉庆御赐碑文', SERIF, 48, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '敏而好学可为文 授之以政无不达', t, t - u + P)

def art_j_tv(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((180, 940, 900, 1380), outline=255, width=14)
    ji_(A, 540, 1340, 320, dir=1, arm=60, t=t)
    A.flush(cv)
    paste(cv, text_img('电视剧让他家喻户晓', SERIF, 48, TONGYAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '剧中情节多为虚构', t, t - u + P)

def art_j_today(A, cv, t, u):
    ground(A, GROUND)
    for i in range(4):
        palace(A, 200 + i * 230, GROUND - 40, 80 if i < 3 else 50, layer='sikulv' if i < 3 else 'mid')
    A.flush(cv)
    paste(cv, text_img('七部四库 今存三部半', SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '其余毁于战火 文澜阁本为补抄', t, t - u + P)

def art_j_end(A, cv, t, u):
    ground(A, GROUND)
    shelf(A, 540, GROUND, 300, 340, 1.0)
    A.flush(cv)
    paste(cv, text_img('替皇帝编了一部大书', SERIF, 50, SIKULV, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_j_legacy(A, cv, t, u):
    candle(A, 860, 1420, 70, 0.5, t)

def art_j_title(A, cv, t, u):
    shelf(A, 840, 1440, 150, 300, 1.0)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    ji_(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))), t=t)

# ================================================================ script
CHAPTERS = {16: ('第一回', '献县'), 48: ('第二回', '戍边'), 80: ('第三回', '四库'),
            112: ('第四回', '宦海'), 144: ('第五回', '文达')}

CARDS = [
    C(0, 2, 'works', 'num', num='三万六千册', line='他是四库全书总纂官', art=art_j_hook_books),
    C(2, 4, 'life', 'num', num='一根烟袋', line='名气比他的书还大', art=art_j_hook_pipe),
    C(4, 6, 'fate', 'num', num='发配新疆', line='只因走漏了一个消息', art=art_j_hook_exile),
    C(6, 8, 'night', 'num', num='斗智斗嘴', line='其实多是电视剧编的', art=art_j_hook_tv),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 献县
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1724, main='生于献县', sub='直隶河间', art=art_j_birth),
    C(22, 26, 'works', 'card', year=1730, main='书香门第', sub='父纪容舒', note='年份约略', art=art_j_family),
    C(26, 30, 'empire', 'card', year=1747, main='解元', sub='二十四岁', art=art_j_jieyuan),
    C(30, 34, 'court', 'card', year=1754, main='进士', sub='入翰林', art=art_j_jinshi),
    C(34, 40, 'night', 'card', year=1760, main='纪大烟袋', sub='嗜烟', note='年份约略', art=art_j_pipe),
    C(40, 48, 'court', 'card', year=1768, main='留京', sub='乾隆赏识', art=art_j_liujing),
    # ---- 第二回 戍边
    C(48, 50, 'fate', 'chapter'),
    C(50, 56, 'death', 'card', year=1768, main='盐案', sub='走漏消息', art=art_j_salt),
    C(56, 62, 'war', 'card', year=1768, main='遣戍新疆', sub='四十五岁', art=art_j_exile),
    C(62, 66, 'life', 'card', year=1769, main='乌鲁木齐', sub='军中文书', art=art_j_urumqi),
    C(66, 70, 'works', 'card', year=1771, main='边塞杂诗', sub='一百六十首', art=art_j_poems),
    C(70, 76, 'night', 'card', year=1771, main='赐还', sub='东归', art=art_j_return),
    C(76, 80, 'court', 'card', year=1772, main='复职', sub='编修', note='年份约略', art=art_j_fuzhi),
    # ---- 第三回 四库
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'empire', 'card', year=1773, main='四库馆', sub='总纂官', art=art_j_guan),
    C(86, 94, 'works', 'siku', year=1773),
    C(94, 98, 'night', 'card', year=1781, main='总目提要', sub='二百卷', art=art_j_tiyao),
    C(98, 104, 'war', 'card', year=1782, main='寓禁于征', sub='禁毁', art=art_j_ban),
    C(104, 108, 'court', 'card', year=1782, main='第一部告成', sub='文渊阁', art=art_j_first),
    C(108, 112, 'empire', 'card', year=1787, main='七阁', sub='共抄七部', art=art_j_seven),
    # ---- 第四回 宦海
    C(112, 114, 'court', 'chapter'),
    C(114, 118, 'life', 'card', year=1788, main='老头子', sub='野史', note='年份无考', art=art_j_laotouzi),
    C(118, 124, 'fate', 'card', year=1788, main='荧屏斗智', sub='影视演绎', art=art_j_heshen),
    C(124, 130, 'night', 'card', year=1789, main='阅微草堂', sub='笔记', art=art_j_yuewei),
    C(130, 134, 'works', 'card', year=1798, main='五种成书', sub='二十四卷', art=art_j_five),
    C(134, 138, 'death', 'card', year=1799, main='乾隆驾崩', sub='太上皇', art=art_j_qianlong),
    C(138, 144, 'fate', 'card', year=1799, main='权臣倒台', sub='嘉庆亲政', art=art_j_hefall),
    # ---- 第五回 文达
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'court', 'card', year=1803, main='协办大学士', sub='八十岁', art=art_j_daxueshi),
    C(150, 154, 'death', 'card', year=1805, main='纪晓岚去世', sub='八十二岁', art=art_j_death),
    C(154, 158, 'empire', 'card', year=1805, main='谥文达', sub='御赐碑文', art=art_j_wenda),
    C(158, 162, 'life', 'card', year=2002, main='家喻户晓', sub='荧屏', art=art_j_tv),
    C(162, 166, 'works', 'card', year=2002, main='四库今存', sub='三部半', art=art_j_today),
    C(166, 170, 'end', 'card', year=2002, main='一部大书', sub='一部小书', art=art_j_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='玖拾壹', col=SIKULV, acc=TONGYAN, born=1724, died=1805, age0=1723,
    born_lab='1724年', died_lab='1805年', years_txt='公元1724 — 1805',
    hook_q='电视剧里他斗和珅 · 历史上的纪晓岚是什么样？',
    name_line='纪昀 · 字晓岚', name='纪晓岚', seal='文达', title_art=art_j_title,
    q1='风流才子？', q2='御用文人？',
    end_art=art_j_legacy, end_big='阅微草堂', end_seal='晓岚',
    end_l1='一辈子替皇帝编书', end_l2='晚年才为自己写了一部',
    end_brush='观弈道人', end_ask='你是从哪部剧认识纪晓岚的？评论区聊聊', next='林觉民'),
    scenes=dict(chapter=scene_chapter, siku=scene_siku))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
