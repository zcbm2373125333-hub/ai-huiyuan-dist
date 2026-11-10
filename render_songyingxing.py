"""千古人物志 · 第捌拾玖集 · 宋应星 (1587–约1666)
Look: 稻田绿 + 窑火橙, 筒车 corner borders (a little water wheel), 奉新 paddies and kilns behind.
Chapter card: 三卷十八篇 — a page of eighteen small craft tiles; more tiles light up each chapter; in the last chapter the book closes.
Set pieces: custom 8-beat scene 'huaji' (花机提花), 6-beat 六次落第, 6-beat 乃粒, 6-beat 杀青造纸, 6-beat 五金炼锌, 6-beat 陶埏, 6-beat 明亡.
Ages are counted in 虚岁 (age0 = born - 1); the death year is approximate.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_yudayou as Yd         # engine + helpers (previous episode)
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
from render_quyuan import river
from render_simayi import emperor
from render_zhuxi import book
from render_jianzhen import tangship

F.RIPPLE = False
DAOTIAN = (96, 122, 62)             # 稻田绿
YAOHUO = (210, 104, 42)             # 窑火橙
S.LAYERS.append(('daotian', DAOTIAN, 0.9, 1.0))
S.LAYERS.append(('yaohuo', YAOHUO, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='工', life='宋', court='明', night='物', war='火', empire='开', works='天', fate='第', death='隐', end='工')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (YAOHUO, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (DAOTIAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (YAOHUO, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(4):                 # paddy rows
    _d.line((60, 1430 + _k * 14, 1020, 1430 + _k * 14), fill=DAOTIAN + (50 - _k * 8,), width=3)
    for _i in range(0, 1000, 40):
        _d.line((60 + _i, 1430 + _k * 14, 64 + _i, 1418 + _k * 14), fill=DAOTIAN + (70,), width=2)
for _x in (110, 970):               # kiln chimneys at the margins
    _d.polygon([(_x - 40, 1420), (_x - 20, 1300), (_x + 20, 1300), (_x + 40, 1420)], fill=(140, 100, 80, 60))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (96, 98, 96)}
def draw_background(t, theme):
    """奉新: rounded green hills, paddy rows, kiln chimneys at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(192, 194, 184), (160, 170, 148), MTN_COL.get(theme, (112, 126, 96))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """筒车: a small water wheel with buckets in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=DAOTIAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=DAOTIAN + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), outline=(120, 90, 60, 230), width=4)
        for k in range(6):
            a = k * math.pi / 3
            d.line((cx, cy, cx + 26 * math.cos(a), cy + 26 * math.sin(a)), fill=(120, 90, 60, 230), width=2)
            d.rectangle((cx + 26 * math.cos(a) - 4, cy + 26 * math.sin(a) - 4, cx + 26 * math.cos(a) + 4, cy + 26 * math.sin(a) + 4), fill=YAOHUO + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def song_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """宋应星: a late-Ming scholar — square 方巾 cap, a long beard (white when old), a plain green robe, sleeves rolled when in workshops."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.075 * h, y - 1.09 * h, x + 0.075 * h, y - 0.93 * h), fill=255)
        d.line((x - 0.075 * h, y - 1.09 * h, x + 0.075 * h, y - 0.93 * h), fill=0, width=2)
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.0 * h, y - 0.85 * h), (x + dir * 0.09 * h, y - 0.85 * h), (x + dir * 0.05 * h, y - 0.62 * h), (x + dir * 0.0 * h, y - 0.66 * h)], fill=255)
    if not kw.get('fall'):
        A.d['daotian'].polygon([(x - 0.1 * h, y - (0.48 if kneel else 0.76) * h), (x + 0.1 * h, y - (0.48 if kneel else 0.76) * h), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=140)
    return hand

def waterwheel(A, cx, cy, r, t, layer='huyang'):
    A.d[layer].ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=max(4, int(0.04 * r)))
    for k in range(12):
        a = k * math.pi / 6 + t * 0.8
        A.d[layer].line((cx, cy, cx + r * math.cos(a), cy + r * math.sin(a)), fill=200, width=3)
        bx, by = cx + r * math.cos(a), cy + r * math.sin(a)
        A.d['yaohuo'].rectangle((bx - 0.07 * r, by - 0.07 * r, bx + 0.07 * r, by + 0.07 * r), fill=255)
        if -math.pi / 2 < (a % (2 * math.pi)) - math.pi < 0:
            A.d['ocean'].line((bx, by, bx, by + 0.15 * r), fill=160, width=2)

def loom(A, cx, base, s, t, pattern=0.0):
    A.d['huyang'].rectangle((cx - s, base - 0.15 * s, cx + s, base - 0.1 * s), fill=255)
    for x in (cx - 0.9 * s, cx + 0.9 * s):
        A.d['ink'].line((x, base, x, base - 0.7 * s), fill=255, width=6)
    A.d['ink'].line((cx - 0.1 * s, base - 0.7 * s, cx + 0.1 * s, base - 1.5 * s), fill=255, width=6)
    A.d['ink'].line((cx - 0.3 * s, base - 1.5 * s, cx + 0.5 * s, base - 1.5 * s), fill=255, width=6)
    for k in range(12):
        x = cx - 0.6 * s + k * 0.1 * s
        A.d['wash'].line((x, base - 1.45 * s, x, base - 0.6 * s), fill=150, width=1)
    A.d['wash'].rectangle((cx - 0.7 * s, base - 0.6 * s, cx + 0.7 * s, base - 0.15 * s), fill=255)
    rows = int(pattern * 8)
    for r in range(rows):
        for k in range(7):
            if (r + k) % 3 == 0 or (r * k) % 5 == 1:
                A.d['yaohuo' if r % 2 else 'daotian'].rectangle((cx - 0.65 * s + k * 0.19 * s, base - 0.2 * s - r * 0.05 * s - 0.04 * s, cx - 0.55 * s + k * 0.19 * s, base - 0.2 * s - r * 0.05 * s), fill=255)

def kiln(A, cx, base, w, t, fire=1.0):
    A.d['dune'].chord((cx - w, base - w, cx + w, base + w * 0.3), 180, 360, fill=230)
    A.d['ink'].rectangle((cx - 0.2 * w, base - 0.3 * w, cx + 0.2 * w, base), fill=255)
    if fire > 0:
        flames(A, cx, base - 0.05 * w, 0.35 * w, 0.3 * w * fire, t, n=2, seed=89, smoke=False)
    A.d['dune'].rectangle((cx + 0.5 * w, base - 1.1 * w, cx + 0.7 * w, base - 0.4 * w), fill=230)

TILE_COL = ['daotian', 'nichang', 'chaitou', 'dune', 'wash', 'qiuhuang', 'yaohuo', 'ink', 'huyang']
def tiles(A, cx, cy, s, n):
    A.d['wash'].rectangle((cx - s, cy - 0.7 * s, cx + s, cy + 0.7 * s), fill=255)
    A.d['ink'].rectangle((cx - s, cy - 0.7 * s, cx + s, cy + 0.7 * s), outline=255, width=4)
    for i in range(18):
        x = cx - 0.85 * s + (i % 6) * 0.34 * s; y = cy - 0.55 * s + (i // 6) * 0.42 * s
        A.d['ink'].rectangle((x, y, x + 0.26 * s, y + 0.32 * s), outline=180, width=2)
        if i < n:
            A.d[TILE_COL[i % len(TILE_COL)] if TILE_COL[i % len(TILE_COL)] != 'wash' else 'mid'].rectangle((x + 6, y + 6, x + 0.26 * s - 6, y + 0.32 * s - 6), fill=230)

# ================================================================ chapter card
CH = {16: (0, 3), 48: (3, 8), 80: (8, 13), 112: (13, 18), 144: (18, 18)}
def art_tile_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (3, 8))
    q = ease_out(u / (1.2 * P))
    if kb == 144 and q > 0.6:
        book(A, 540, 1240, 240, 340, layer='daotian')
        A.flush(cv)
        paste(cv, text_img('天\n工\n开\n物', SERIF, 40, INK, 'Black', bleed=False, spacing=2), 540, 1080, 1, clamp((q - 0.6) / 0.2))
    else:
        tiles(A, 540, 1060, 320, int(lerp(a, b, clamp((q - 0.2) / 0.6))))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_tile_chapter)
    ink_in(cv, text_img(no, SERIF, 56, DAOTIAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_s_hook_book(A, cv, t, u):
    tiles(A, 540, 1100, 320, int(clamp(u / (1.2 * P)) * 18))

def art_s_hook_six(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    for i in range(min(6, int(u / (0.2 * P)) + 1)):
        stamp(cv, seal('落第', 48, ZHU), 220 + (i % 3) * 320, 1020 + (i // 3) * 170, t, t - u + i * 0.2 * P)

def art_s_hook_ship(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=4)
    tangship(A, lerp(200, 700, ease_out(u / (1.2 * P))), 1220, 110, t)

def art_s_hook_grain(A, cv, t, u):
    ground(A, GROUND)
    for k in range(8):
        x = 160 + k * 110
        A.d['daotian'].line((x, GROUND, x + 6, GROUND - 200), fill=255, width=4)
        A.d['qiuhuang'].ellipse((x - 4, GROUND - 240, x + 18, GROUND - 190), fill=255)
    A.d['qiuhuang'].ellipse((480, GROUND - 60, 600, GROUND), fill=int(200 * (1 - clamp(u / (1.2 * P)))))

# ================================================================ 第一回 奉新
def art_s_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x - 60, GROUND - 220), (x + 60, GROUND - 220), (x + 220, GROUND)], fill=150)
    A.d['wash'].rectangle((360, GROUND - 200, 720, GROUND), fill=255)
    A.d['ink'].polygon([(330, GROUND - 200), (750, GROUND - 200), (540, GROUND - 280)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('江西奉新人 · 曾祖官至左都御史 后家道中落', SERIF, 42, DAOTIAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('奉新', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_study(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='mid')
    person(A, 320, GROUND, 130, dir=1, robe=True, hat='none', kneel=True, arm=90, layer='ink')
    person(A, 760, GROUND, 140, dir=-1, robe=True, hat='none', kneel=True, arm=90, layer='daotian')
    A.flush(cv)
    paste(cv, text_img('与兄宋应升同窗 · 相传过目成诵', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '过目成诵之说见县志 或有夸饰', t, t - u + P)

def art_s_bolan(A, cv, t, u):
    ground(A, GROUND)
    for i in range(6):
        A.d['mid'].rectangle((140 + i * 140, GROUND - 330, 250 + i * 140, GROUND), fill=170)
        for j in range(4):
            A.d['daotian' if (i + j) % 2 else 'mid'].rectangle((150 + i * 140, GROUND - 90 - j * 76, 240 + i * 140, GROUND - 30 - j * 76), fill=230)
    song_(A, 540, GROUND, 160, dir=1, arm=150)
    A.flush(cv)
    paste(cv, text_img('熟读经史 · 兼及天文 音律 诸子', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_juren(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='daotian')
    ground(A, GROUND)
    song_(A, 440, GROUND, 190, dir=1, arm=60)
    person(A, 640, GROUND, 190, dir=-1, robe=True, hat='none', arm=60, layer='mid')
    A.flush(cv)
    paste(cv, text_img('与兄同中举人 · 时人称奉新二宋', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('二宋', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_luodi(A, cv, t, u):
    """6-beat set piece: 六上公车 — six trips to the capital for the metropolitan exam, 1616 to 1631; six failures."""
    ph = u / P
    ground(A, GROUND)
    for r in range(2):
        for i in range(6):
            x = 160 + i * 150; y = GROUND - r * 170
            A.d['mid'].rectangle((x - 55, y - 130, x + 55, y), fill=200)
    n = min(6, int(ph / 0.9) + 1)
    song_(A, 540, GROUND, 170, dir=-1, arm=-8, ph=t * 2, old=0.1 * n)
    A.flush(cv)
    for i in range(n):
        stamp(cv, seal('落第', 40, ZHU), 220 + i * 128, 1000 - 30 * (i % 2), t, t - u + i * 0.9 * P)
    paste(cv, text_img(f'第{cn_num(n)}次会试 · 落第', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '前后十五年 六上公车', t, t - u + P)

def art_s_road(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        x = 160 + k * 250
        A.d['daotian'].rectangle((x - 100, GROUND - 30, x + 100, GROUND - 6), fill=200)
    kiln(A, 780, GROUND, 140, t)
    person(A, 400, GROUND, 140, dir=1, robe=False, hat='knot', bow=40, arm=150, layer='ink')
    song_(A, lerp(100, 260, ease_out(u / (3 * P))), GROUND, 180, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('往返京城途中 · 留心农夫与工匠', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_jueyi(A, cv, t, u):
    ground(A, GROUND)
    song_(A, lerp(540, 1100, ease_out(u / (3 * P))), GROUND, 180, dir=1, ph=t * 3, arm=-8, old=0.3)
    A.flush(cv)
    paste(cv, text_img('第六次落第 · 从此绝意仕途', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '时年四十五', t, t - u + P)

# ================================================================ 第二回 天工
def art_s_jiaoyu(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    song_(A, 260, GROUND, 180, dir=1, kneel=True, arm=100, old=0.3)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    paste(cv, text_img('任分宜县学教谕 · 微官清闲 专心著述', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '时年四十八', t, t - u + P)

def art_s_yeyi(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 460, 260, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('野议', SERIF, 64, INK, 'Black', bleed=False, spacing=12), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('作野议 · 痛陈时弊', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_s_nali(A, cv, t, u):
    """6-beat set piece: 乃粒 — the first chapter is grain: soaking seed, transplanting rice, the bamboo water-wheel lifting water to the paddies."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1240, 420, GROUND + 40), fill=150)
    river(A, 1250, t, rows=2, amp=3)
    for k in range(4):
        A.d['daotian'].rectangle((460 + k * 140, 1260, 580 + k * 140, GROUND - 10), fill=150 + 20 * (k % 2))
    if ph >= 2:
        waterwheel(A, 300, 1160, 140, t)
    for j in range(3):
        person(A, 560 + j * 150, GROUND - 10, 110, dir=1, robe=False, hat='knot', bow=50, arm=150, layer='ink')
    A.flush(cv)
    lab = '浸种 插秧 耘田' if ph < 2 else ('筒车引水 灌溉稻田' if ph < 4 else '贵五谷而贱金玉')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4 else DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '全书以乃粒为首 珠玉为末', t, t - u + 4 * P)

def scene_huaji(cv, t, c, k):
    """8-beat custom scene: 花机 — the drawloom: one weaver throws the shuttle below, a drawboy pulls the pattern cords above;
    the brocade pattern grows row by row."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    loom(A, 540, GROUND, 300, t, pattern=clamp(ph / 7))
    person(A, 360, GROUND, 150, dir=1, robe=False, hat='knot', kneel=True, arm=lerp(70, 110, 0.5 + 0.5 * math.sin(t * 6)), layer='ink')
    person(A, 560, GROUND - 420, 110, dir=1, robe=False, hat='none', kneel=True, arm=lerp(110, 160, 0.5 + 0.5 * math.sin(t * 3)), layer='mid')
    song_(A, 900, GROUND, 170, dir=-1, arm=lerp(-8, 80, clamp((ph - 5) / 0.6)))
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '花机提花', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=89)
    fx.flush(cv)
    if ph < 3:
        lab, col = '乃服篇 · 记提花机', DAOTIAN
    elif ph < 5.5:
        lab, col = '一人提花在上 一人投梭在下', DAOTIAN
    else:
        lab, col = '花本一定 千匹如一', ZHU
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '书中附有花机全图', t, s0 + 3 * P)

def art_s_kanxing(A, cv, t, u):
    ground(A, GROUND)
    for i in range(min(18, int(clamp(u / (3 * P)) * 18) + 1)):
        book(A, 160 + (i % 9) * 95, GROUND - (i // 9) * 180, 80, 150, layer='daotian' if i % 2 else 'mid')
    A.flush(cv)
    paste(cv, text_img('天工开物刊行 · 友人涂绍煃出资', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('天工开物', 50), 860, 1440, t, t - u + P, rot=6)

def art_s_xu(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 560, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('丐大业文人 弃掷案头\n此书于功名进取\n毫不相关也', SERIF, 44, INK, 'Black', bleed=False, spacing=14), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('天工开物 · 自序', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

# ================================================================ 第三回 开物
def art_s_paper(A, cv, t, u):
    """6-beat set piece: 杀青 — bamboo paper in five steps: cut and soak the bamboo; boil it; scoop pulp with a screen; press; dry against a heated wall."""
    ph = u / P
    ground(A, GROUND)
    steps = ['斩竹漂塘', '煮楻足火', '荡料入帘', '覆帘压纸', '透火焙干']
    i = min(4, int(ph / 1.15))
    if i == 0:
        A.d['ocean'].rectangle((300, GROUND - 60, 780, GROUND), fill=170)
        for k in range(8):
            A.d['grass'].line((320 + k * 56, GROUND - 40, 360 + k * 56, GROUND - 40), fill=255, width=8)
    elif i == 1:
        A.d['dune'].rectangle((420, GROUND - 200, 660, GROUND), fill=230)
        flames(A, 540, GROUND, 200, 80, t, n=3, seed=891, smoke=True)
    elif i == 2:
        A.d['dune'].rectangle((360, GROUND - 120, 720, GROUND), fill=230)
        A.d['wash'].rectangle((420, GROUND - 160 + 20 * math.sin(t * 3), 660, GROUND - 140 + 20 * math.sin(t * 3)), fill=255)
        for j in (-1, 1):
            person(A, 540 + j * 220, GROUND, 150, dir=-j, robe=False, hat='knot', arm=110, layer='ink')
    elif i == 3:
        for k in range(10):
            A.d['wash'].rectangle((420, GROUND - 20 - k * 12, 660, GROUND - 10 - k * 12), fill=255)
        A.d['huyang'].line((360, GROUND - 160, 760, GROUND - 140), fill=255, width=14)
    else:
        A.d['dune'].rectangle((400, GROUND - 320, 680, GROUND), fill=230)
        for k in range(4):
            A.d['wash'].rectangle((420 + (k % 2) * 130, GROUND - 300 + (k // 2) * 140, 530 + (k % 2) * 130, GROUND - 180 + (k // 2) * 140), fill=255)
        flames(A, 540, GROUND, 120, 50, t, n=2, seed=892, smoke=False)
    song_(A, 160, GROUND, 170, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img(f'杀青篇 · {steps[i]}', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '世界上最早的竹纸制作工艺图解', t, t - u + 4 * P)

def art_s_zinc(A, cv, t, u):
    """6-beat set piece: 倭铅 — calamine is packed into clay pots, sealed with mud, stacked among coal cakes and fired; the pots are broken open: zinc."""
    ph = u / P
    ground(A, GROUND)
    for k in range(5):
        x = 300 + k * 110
        A.d['dune'].rectangle((x - 30, GROUND - 160, x + 30, GROUND - 40), fill=255)
        A.d['ink'].rectangle((x - 30, GROUND - 160, x + 30, GROUND - 40), outline=200, width=3)
    if ph >= 2:
        for k in range(12):
            A.d['ink'].ellipse((260 + k * 50 - 18, GROUND - 40 - 18 * (k % 2), 260 + k * 50 + 18, GROUND - 4 - 18 * (k % 2)), fill=255)
        flames(A, 520, GROUND - 40, 560, 160 * clamp((ph - 2) / 1), t, n=5, seed=893, smoke=True)
    if ph >= 4.5:
        A.d['fangtian'].ellipse((800, GROUND - 80, 900, GROUND - 20), fill=255)
    A.flush(cv)
    lab = '炉甘石装入泥罐 · 泥封' if ph < 2 else ('煤饼围烧 · 罐中熔化' if ph < 4.5 else '冷定毁罐取出 · 即为倭铅')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4.5 else DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '倭铅即锌 是世界上最早的炼锌记载之一', t, t - u + 4 * P)

def art_s_porcelain(A, cv, t, u):
    """6-beat set piece: 陶埏 — one porcelain cup passes through seventy-two hands before it is done."""
    ph = u / P
    ground(A, GROUND)
    kiln(A, 820, GROUND, 160, t)
    for j in range(5):
        person(A, 140 + j * 110, GROUND, 120, dir=1, robe=False, hat='knot', kneel=True, arm=lerp(80, 120, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='ink')
        A.d['wash'].ellipse((180 + j * 110, GROUND - 70, 220 + j * 110, GROUND - 40), fill=255)
    n = min(72, int(clamp(ph / 4.5) * 72) + 1)
    A.flush(cv)
    lab = f'第{cn_num(n)}道工序' if ph < 4.5 else '共计一坯工力 过手七十二 方克成器'
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4.5 else DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('陶埏', 56), 860, 1020, t, t - u + 0.4, rot=6)

def art_s_jiabing(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        x = 300 + k * 240
        A.d['ink'].rectangle((x - 60, GROUND - 40, x + 60, GROUND - 20), fill=255)
        A.d['ink'].line((x + 60, GROUND - 30, x + 120, GROUND - 40), fill=255, width=10)
    flames(A, 420, GROUND - 40, 60, 40, t, n=1, seed=894, smoke=True)
    A.flush(cv)
    paste(cv, text_img('佳兵篇 · 记弓弩 火药 火器', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_zhouche(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    river(A, 1210, t, rows=2, amp=3)
    tangship(A, 340, 1220, 110, t)
    carriage(A, 780, 1200, 90, dir=1, wheel=t * 4, ph=t * 6, layer='huyang')
    A.flush(cv)
    paste(cv, text_img('舟车篇 · 记漕舫 海舟与骡车', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_s_eighteen(A, cv, t, u):
    tiles(A, 540, 1100, 340, 18)
    A.flush(cv)
    paste(cv, text_img('三卷十八篇 · 附图一百二十三幅', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

# ================================================================ 第四回 乱世
def art_s_tingzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='汀州', layer='mid', open_=1.0)
    ground(A, GROUND)
    song_(A, 540, GROUND, 190, dir=1, arm=-8, old=0.4)
    A.flush(cv)
    paste(cv, text_img('升福建汀州推官', SERIF, 48, DAOTIAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_s_bozhou(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='亳州', layer='mid', open_=1.0)
    ground(A, GROUND)
    song_(A, 540, GROUND, 190, dir=1, arm=60, old=0.5)
    A.flush(cv)
    paste(cv, text_img('升南直隶亳州知州', SERIF, 48, DAOTIAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_s_mingwang(A, cv, t, u):
    """6-beat set piece: 甲申 — 李自成 takes Beijing; the 崇祯 emperor hangs himself; 宋应星 resigns and goes home."""
    ph = u / P
    if ph < 3:
        palace(A, 540, 1300, 320, collapse=clamp(ph / 3) * 0.5, layer='mid')
        flames(A, 540, 1200, 560, 200, t, n=5, seed=1644, smoke=True)
        ground(A, GROUND)
        lab, col = '李自成破北京 · 崇祯自缢', ZHU
    else:
        for k in range(3):
            x = 260 + k * 280
            A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 200), (x + 220, GROUND)], fill=150)
        ground(A, GROUND)
        song_(A, lerp(900, 300, clamp((ph - 3) / 2.5)), GROUND, 180, dir=-1, ph=t * 2, arm=-8, old=0.6)
        lab, col = '宋应星辞官归乡', DAOTIAN
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('甲申', 56), 860, 1020, t, t - u + 0.4, rot=6)

def art_s_brother(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, layer='ink')
    song_(A, 880, GROUND, 150, dir=-1, kneel=True, bow=30, old=0.6)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('兄宋应升 服毒殉明', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_s_yinju(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x - 60, GROUND - 220), (x + 60, GROUND - 220), (x + 220, GROUND)], fill=150)
    A.d['wash'].rectangle((620, GROUND - 160, 860, GROUND), fill=255)
    A.d['ink'].polygon([(600, GROUND - 160), (880, GROUND - 160), (740, GROUND - 220)], fill=255)
    ground(A, GROUND)
    song_(A, 360, GROUND, 180, dir=1, arm=-8, old=0.7)
    A.flush(cv)
    paste(cv, text_img('隐居奉新 · 拒不出仕清朝', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_poor(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 380, layer='mid')
    song_(A, 300, GROUND, 170, dir=1, kneel=True, bow=30, arm=-8, old=0.9)
    lamp(A, 640, GROUND - 74, 26, t, glow=0.5)
    A.flush(cv)
    paste(cv, text_img('晚年家贫 · 所著多已散佚', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '野议 论气等书 直到上世纪才重新发现', t, t - u + P)

# ================================================================ 第五回 回归
def art_s_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    song_(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('约在此年前后去世', SERIF, 48, DAOTIAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '卒年史无确载', t, t - u + P)

def art_s_japan(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=4)
    tangship(A, lerp(200, 700, ease_out(u / (3 * P))), 1220, 110, t)
    A.flush(cv)
    paste(cv, text_img('日本刊刻天工开物 · 大受推崇', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '菅生堂和刻本', t, t - u + P)

def art_s_siku(A, cv, t, u):
    ground(A, GROUND)
    for i in range(8):
        A.d['mid'].rectangle((140 + i * 105, GROUND - 360, 230 + i * 105, GROUND), fill=170)
    book(A, 540, GROUND - 380, 80, 120, layer='daotian')
    A.flush(cv)
    stamp(cv, seal('不收', 60, ZHU), 540, GROUND - 440, t, t - u + P)
    paste(cv, text_img('清修四库全书 未收天工开物 · 渐在国内失传', SERIF, 42, DAOTIAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))

def art_s_west(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=4)
    boat(A, lerp(200, 800, ease_out(u / (3 * P))), 1220, 100, t)
    A.flush(cv)
    paste(cv, text_img('部分篇章译为法文 · 传入欧洲', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_s_home(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    person(A, 280, GROUND, 190, dir=1, robe=False, hat='none', kneel=True, arm=100, layer='ink')
    book(A, 560, GROUND - 74, 140, 0, open_=1.0)
    A.flush(cv)
    paste(cv, text_img('丁文江从日本找回 · 重新刊印', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '一本书在故国失传近二百年', t, t - u + P)

def art_s_diderot(A, cv, t, u):
    ground(A, GROUND)
    song_(A, 540, GROUND, 260, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('李约瑟称他为 中国的狄德罗', SERIF, 46, DAOTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '狄德罗主编法国百科全书', t, t - u + P)

def art_s_end(A, cv, t, u):
    tiles(A, 540, 1120, 300, 18)
    A.flush(cv)
    paste(cv, text_img('天工人其代之', SERIF, 52, DAOTIAN, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '书名取自尚书 天之工 人代为之', t, t - u + P)

def art_s_legacy(A, cv, t, u):
    waterwheel(A, 860, 1360, 60, t)

def art_s_title(A, cv, t, u):
    waterwheel(A, 820, 1300, 130, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    song_(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '奉新'), 48: ('第二回', '天工'), 80: ('第三回', '开物'),
            112: ('第四回', '乱世'), 144: ('第五回', '回归')}

CARDS = [
    C(0, 2, 'works', 'num', num='一本书', line='记下三百年前的工业', art=art_s_hook_book),
    C(2, 4, 'fate', 'num', num='六次落榜', line='才写出了它', art=art_s_hook_six),
    C(4, 6, 'war', 'num', num='国内失传', line='日本却在刊印', art=art_s_hook_ship),
    C(6, 8, 'life', 'num', num='贵五谷', line='贱金玉', art=art_s_hook_grain),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 奉新
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1587, main='生于奉新', sub='江西', art=art_s_birth),
    C(22, 26, 'works', 'card', year=1595, main='兄弟同窗', sub='过目成诵', note='年份约略', art=art_s_study),
    C(26, 30, 'night', 'card', year=1605, main='博览群书', sub='兼及天文', note='年份约略', art=art_s_bolan),
    C(30, 34, 'empire', 'card', year=1615, main='中举', sub='奉新二宋', art=art_s_juren),
    C(34, 40, 'fate', 'card', year=1616, main='六上公车', sub='十五年', art=art_s_luodi),
    C(40, 44, 'life', 'card', year=1625, main='留心工艺', sub='田间作坊', note='年份约略', art=art_s_road),
    C(44, 48, 'death', 'card', year=1631, main='绝意仕途', sub='四十五岁', art=art_s_jueyi),
    # ---- 第二回 天工
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'court', 'card', year=1634, main='分宜教谕', sub='四十八岁', art=art_s_jiaoyu),
    C(54, 58, 'night', 'card', year=1636, main='野议', sub='痛陈时弊', art=art_s_yeyi),
    C(58, 64, 'life', 'card', year=1636, main='乃粒', sub='五谷为先', art=art_s_nali),
    C(64, 72, 'works', 'huaji', year=1636),
    C(72, 76, 'empire', 'card', year=1637, main='天工开物', sub='刊行', art=art_s_kanxing),
    C(76, 80, 'fate', 'card', year=1637, main='自序', sub='与功名无关', art=art_s_xu),
    # ---- 第三回 开物
    C(80, 82, 'night', 'chapter'),
    C(82, 88, 'works', 'card', year=1637, main='杀青', sub='竹纸五步', art=art_s_paper),
    C(88, 94, 'war', 'card', year=1637, main='五金', sub='倭铅', art=art_s_zinc),
    C(94, 100, 'night', 'card', year=1637, main='陶埏', sub='七十二道', art=art_s_porcelain),
    C(100, 104, 'war', 'card', year=1637, main='佳兵', sub='火器', art=art_s_jiabing),
    C(104, 108, 'life', 'card', year=1637, main='舟车', sub='漕舫', art=art_s_zhouche),
    C(108, 112, 'empire', 'card', year=1637, main='十八篇', sub='百廿三图', art=art_s_eighteen),
    # ---- 第四回 乱世
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'court', 'card', year=1638, main='汀州推官', sub='福建', art=art_s_tingzhou),
    C(118, 122, 'empire', 'card', year=1640, main='亳州知州', sub='南直隶', art=art_s_bozhou),
    C(122, 128, 'death', 'card', year=1644, main='明亡', sub='辞官归乡', art=art_s_mingwang),
    C(128, 132, 'death', 'card', year=1646, main='兄长殉国', sub='宋应升', art=art_s_brother),
    C(132, 138, 'fate', 'card', year=1650, main='隐居', sub='不仕清', note='年份约略', art=art_s_yinju),
    C(138, 144, 'night', 'card', year=1655, main='晚年清贫', sub='著述散佚', note='年份约略', art=art_s_poor),
    # ---- 第五回 回归
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=1666, main='宋应星去世', sub='约八十岁', art=art_s_death),
    C(150, 154, 'works', 'card', year=1771, main='东传日本', sub='和刻本', art=art_s_japan),
    C(154, 158, 'fate', 'card', year=1773, main='四库不收', sub='国内失传', art=art_s_siku),
    C(158, 162, 'empire', 'card', year=1837, main='西传', sub='法文', note='年份约略', art=art_s_west),
    C(162, 166, 'court', 'card', year=1926, main='重回故国', sub='丁文江', art=art_s_home),
    C(166, 168, 'night', 'card', year=1926, main='狄德罗', sub='李约瑟之评', art=art_s_diderot),
    C(168, 170, 'end', 'card', year=1926, main='天工开物', sub='人代天工', art=art_s_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='捌拾玖', col=DAOTIAN, acc=YAOHUO, born=1587, died=1666, age0=1586,
    born_lab='1587年', died_lab='约1666年', years_txt='公元1587 — 约1666',
    hook_q='他六次考进士都落榜 · 为什么写出了中国的工业百科？',
    name_line='宋应星 · 字长庚', name='宋应星', seal='长庚', title_art=art_s_title,
    q1='东方狄德罗？', q2='落第书生？',
    end_art=art_s_legacy, end_big='天工开物', end_seal='长庚',
    end_l1='书生们看不起的手艺', end_l2='他一笔一画写进了书里',
    end_brush='开物成务', end_ask='天工开物里 你最想看哪一篇？评论区聊聊', next='郑成功'),
    scenes=dict(chapter=scene_chapter, huaji=scene_huaji))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
