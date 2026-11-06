"""千古人物志 · 第柒拾壹集 · 李时珍 (1518–1593)
Look: 药柜褐 + 艾叶绿, 药葫芦 corner borders, 蕲州 hills with herb sprigs at the margins.
Chapter card: 百子柜 — a medicine cabinet; each chapter more drawers are filled; in the last chapter the cabinet becomes a closed book.
Set pieces: custom 8-beat scene 'baicao' (远游采药 · 药物计数), 6-beat 曼陀罗亲尝, 6-beat 蕲蛇, 6-beat 穿山甲,
6-beat 驳水银, 6-beat 成书, 6-beat 金陵刻版.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_hubilie as Hb         # engine + helpers (previous episode)
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
from render_kongzi import slips, bundle
from render_quyuan import river
from render_zhuxi import book

F.RIPPLE = False
YAOGUI = (132, 92, 58)              # 药柜褐
AIYE = (104, 138, 84)               # 艾叶绿
S.LAYERS.append(('yaogui', YAOGUI, 0.9, 1.0))
S.LAYERS.append(('aiye', AIYE, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='药', life='李', court='明', night='夜', war='毒', empire='纲', works='草', fate='第', death='逝', end='圣')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZHU, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (YAOGUI, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (AIYE, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # 雨湖 shore line
    _d.line([(60 + i * 30, 1456 + _k * 14 + 5 * math.sin(i * 0.5 + _k)) for i in range(34)], fill=(90, 120, 120, 44 - _k * 10), width=3)
for _x, _s in ((110, 1), (970, -1)):  # herb sprigs at the margins
    _d.line((_x, 1440, _x + _s * 10, 1300), fill=AIYE + (70,), width=4)
    for _j in range(5):
        _y = 1420 - _j * 26
        _d.ellipse((_x + _s * 6 - 22, _y - 8, _x + _s * 6 + 22, _y + 8), fill=AIYE + (60,))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (96, 96, 92)}
def draw_background(t, theme):
    """蕲州: soft hills over 雨湖, herbs at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(192, 192, 182), (160, 170, 150), MTN_COL.get(theme, (110, 130, 100))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """药葫芦: a small gourd with a red cord in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=YAOGUI + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=YAOGUI + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.ellipse((cx - 14, cy - 34, cx + 14, cy - 8), fill=YAOGUI + (230,))
        d.ellipse((cx - 22, cy - 14, cx + 22, cy + 30), fill=YAOGUI + (230,))
        d.line((cx - 12, cy - 12, cx + 12, cy - 12), fill=(178, 52, 40, 230), width=4)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def li(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, basket=False, **kw):
    """李时珍: Ming physician — soft 方巾 cap, a herb basket on the back when travelling, beard white when old."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.075 * h, y - 1.07 * h, x + 0.075 * h, y - 0.93 * h), fill=255)
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.02 * h, y - 0.84 * h), (x + dir * 0.09 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.68 * h)], fill=255)
        A.d['aiye'].rectangle((x - 0.08 * h, y - 0.56 * h, x + 0.08 * h, y - 0.52 * h), fill=255)
    if basket:
        bx = x - dir * 0.16 * h
        A.d['yaogui'].rectangle((bx - 0.09 * h, y - 0.82 * h, bx + 0.09 * h, y - 0.5 * h), fill=255)
        for k in range(3):
            A.d['aiye'].ellipse((bx - 0.07 * h + k * 0.05 * h, y - 0.9 * h, bx - 0.02 * h + k * 0.05 * h, y - 0.8 * h), fill=255)
    return hand

def herb(A, x, base, h, kind=0, layer='aiye', flower='red'):
    A.d['ink'].line((x, base, x, base - h), fill=220, width=max(2, int(0.03 * h)))
    for j in range(4):
        y = base - (0.2 + 0.18 * j) * h; s = 1 if j % 2 else -1
        A.d[layer].ellipse((x + s * 0.02 * h - 0.14 * h if s > 0 else x - 0.26 * h, y - 0.05 * h, x + 0.26 * h if s > 0 else x + s * 0.02 * h + 0.14 * h, y + 0.05 * h), fill=255)
    if kind == 0:
        A.d[flower].ellipse((x - 0.08 * h, base - 1.08 * h, x + 0.08 * h, base - 0.92 * h), fill=255)
    elif kind == 1:
        for k in range(5):
            a = k * 2 * math.pi / 5
            A.d[flower].ellipse((x + 0.08 * h * math.cos(a) - 0.05 * h, base - h + 0.08 * h * math.sin(a) - 0.05 * h, x + 0.08 * h * math.cos(a) + 0.05 * h, base - h + 0.08 * h * math.sin(a) + 0.05 * h), fill=255)
    else:
        A.d[flower].polygon([(x, base - h), (x - 0.1 * h, base - 1.2 * h), (x + 0.1 * h, base - 1.2 * h)], fill=255)

def datura(A, x, base, h, t):
    """曼陀罗: a white trumpet flower."""
    A.d['ink'].line((x, base, x, base - h), fill=220, width=4)
    for j in range(3):
        y = base - (0.3 + 0.2 * j) * h
        A.d['aiye'].polygon([(x, y), (x + (1 if j % 2 else -1) * 0.3 * h, y - 0.06 * h), (x + (1 if j % 2 else -1) * 0.2 * h, y + 0.06 * h)], fill=255)
    sw = 0.04 * h * math.sin(t * 2)
    A.d['wash'].polygon([(x, base - h), (x - 0.16 * h + sw, base - 1.38 * h), (x + 0.16 * h + sw, base - 1.38 * h)], fill=255)
    A.d['ink'].polygon([(x, base - h), (x - 0.16 * h + sw, base - 1.38 * h), (x + 0.16 * h + sw, base - 1.38 * h)], outline=200)

def cabinet(A, cx, cy, w, h, lit, layer='yaogui'):
    """百子柜: a medicine cabinet of 6 x 5 drawers; `lit` drawers are marked with a green label."""
    A.d[layer].rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), fill=230)
    A.d['ink'].rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), outline=255, width=5)
    cols, rows = 6, 5
    dw, dh = w / cols, h / rows
    for i in range(cols * rows):
        x0 = cx - w / 2 + (i % cols) * dw; y0 = cy - h / 2 + (i // cols) * dh
        A.d['ink'].rectangle((x0 + 4, y0 + 4, x0 + dw - 4, y0 + dh - 4), outline=200, width=2)
        A.d['ink'].ellipse((x0 + dw / 2 - 4, y0 + dh * 0.7 - 4, x0 + dw / 2 + 4, y0 + dh * 0.7 + 4), fill=255)
        if i < lit:
            A.d['aiye'].rectangle((x0 + dw * 0.3, y0 + dh * 0.18, x0 + dw * 0.7, y0 + dh * 0.5), fill=255)

def snake(A, x0, x1, y, t, amp=26, layer='ink', w=10):
    pts = [(lerp(x0, x1, k / 24), y + amp * math.sin(k * 0.7 + t * 4)) for k in range(25)]
    A.d[layer].line(pts, fill=255, width=w)
    hx, hy = pts[-1]
    A.d[layer].polygon([(hx, hy - 10), (hx + 26, hy), (hx, hy + 10)], fill=255)
    for k in range(0, 24, 3):
        A.d['wash'].ellipse((pts[k][0] - 4, pts[k][1] - 4, pts[k][0] + 4, pts[k][1] + 4), fill=200)

def pangolin(A, cx, base, s, open_=0.0):
    A.d['yaogui'].ellipse((cx - s, base - 0.7 * s, cx + s, base), fill=255)
    for i in range(5):
        for j in range(2):
            x = cx - 0.8 * s + i * 0.36 * s; y = base - 0.55 * s + j * 0.22 * s
            A.d['ink'].arc((x - 0.16 * s, y - 0.12 * s, x + 0.16 * s, y + 0.12 * s), 0, 180, fill=200, width=3)
    A.d['yaogui'].polygon([(cx + s * 0.9, base - 0.35 * s), (cx + 1.4 * s, base - 0.15 * s), (cx + 0.9 * s, base - 0.05 * s)], fill=255)
    A.d['yaogui'].polygon([(cx - s * 0.9, base - 0.3 * s), (cx - 1.6 * s, base - 0.02 * s), (cx - 0.9 * s, base)], fill=255)
    if open_ > 0:
        A.d['wash'].ellipse((cx - 0.5 * s, base - 0.4 * s, cx + 0.5 * s, base - 0.05 * s), fill=255)
        for k in range(int(open_ * 30)):
            ax = cx - 0.4 * s + (k * 37 % 80) / 100 * s; ay = base - 0.32 * s + (k * 23 % 24) / 100 * s
            A.d['ink'].ellipse((ax - 3, ay - 2, ax + 3, ay + 2), fill=255)

# ================================================================ chapter card
CH = {16: (0, 6), 48: (6, 12), 80: (12, 18), 112: (18, 24), 144: (24, 30)}
def art_cab_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (6, 12))
    q = ease_out(u / (1.2 * P))
    if kb == 144 and q > 0.65:
        book(A, 540, 1220, 260, 340, layer='yaogui')
        A.flush(cv)
        paste(cv, text_img('本\n草\n纲\n目', SERIF, 40, INK, 'Black', bleed=False, spacing=2), 540, 1080, 1, clamp((q - 0.65) / 0.2))
    else:
        cabinet(A, 540, 1060, 480, 320, int(lerp(a, b, clamp((q - 0.2) / 0.6))))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_cab_chapter)
    ink_in(cv, text_img(no, SERIF, 56, YAOGUI, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_l_hook_book(A, cv, t, u):
    ground(A, GROUND)
    n = min(14, int(clamp(u / (1.2 * P)) * 14) + 1)
    for i in range(n):
        A.d['yaogui' if i % 2 else 'aiye'].rectangle((400, GROUND - 26 * (i + 1), 680, GROUND - 26 * i - 4), fill=230)

def art_l_hook_herbs(A, cv, t, u):
    ground(A, GROUND)
    cabinet(A, 540, 1100, 520, 340, int(clamp(u / (1.2 * P)) * 30))

def art_l_hook_flower(A, cv, t, u):
    ground(A, GROUND)
    datura(A, 540, GROUND, 300, t)

def art_l_hook_exam(A, cv, t, u):
    ground(A, GROUND)
    for i in range(3):
        A.d['mid'].rectangle((240 + i * 220, GROUND - 260, 380 + i * 220, GROUND), fill=200)
    A.flush(cv)
    for i in range(min(3, int(u / (0.4 * P)) + 1)):
        stamp(cv, seal('落第', 50, ZHU), 310 + i * 220, 1140, t, t - u + i * 0.4 * P)

# ================================================================ 第一回 医家子
def art_l_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 280), (x + 220, GROUND)], fill=150)
    A.d['wash'].rectangle((420, GROUND - 160, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 160), (680, GROUND - 160), (540, GROUND - 230)], fill=255)
    A.d['red'].rectangle((620, GROUND - 120, 640, GROUND - 60), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('蕲州瓦硝坝 · 父李言闻为乡间医生', SERIF, 44, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('蕲州', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '其时医者地位低微 父望其读书入仕', t, t - u + P)

def art_l_xiucai(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='yaogui')
    ground(A, GROUND)
    li(A, 540, GROUND, 150, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('十四岁考中秀才', SERIF, 48, YAOGUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('秀才', 56), 860, 1020, t, t - u + P, rot=6)

def art_l_luodi(A, cv, t, u):
    ground(A, GROUND)
    for r in range(2):
        for i in range(6):
            x = 160 + i * 150; y = GROUND - r * 170
            A.d['mid'].rectangle((x - 55, y - 130, x + 55, y), fill=200)
    li(A, 540, GROUND, 170, dir=-1, bow=25, arm=-8, ph=t * 2)
    A.flush(cv)
    paste(cv, text_img('三赴武昌乡试 · 皆名落孙山', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '1534 1537 1540年', t, t - u + P)

def art_l_resolve(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    river(A, 1210, t, rows=3, amp=6, speed=-1.5)
    A.d['yaogui'].polygon([(380, 1210), (700, 1210), (660, 1250), (420, 1250)], fill=255)
    li(A, 560, 1210, 150, dir=1, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    type_in(cv, text_img('身如逆流船 心比铁石坚', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.6)
    note_in(cv, '相传为其向父亲明志之诗', t, t - u + P)

def art_l_plague(A, cv, t, u):
    ground(A, GROUND)
    for j in range(4):
        person(A, 560 + j * 110, GROUND, 110, dir=-1, robe=False, hat='knot', kneel=True, bow=30, layer='mid')
    person(A, 220, GROUND, 200, dir=1, robe=True, hat='knot', arm=-8, layer='ink')
    li(A, 400, GROUND, 160, dir=1, arm=lerp(40, 90, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    paste(cv, text_img('水灾之后疫病流行 · 随父施药救人', SERIF, 44, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_jiuben(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='yaogui')
    li(A, 260, GROUND, 170, dir=1, kneel=True, arm=100)
    book(A, 560, GROUND - 74, 160, 0, open_=1.0)
    A.flush(cv)
    paste(cv, text_img('旧本草错讹甚多 · 立志重修', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('重修', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '此年开始编撰本草纲目', t, t - u + P)

def art_l_chuwang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 780, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(-8, 80, ease_out(u / 0.6)), layer='yaogui')
    li(A, 360, GROUND, 180, dir=1, bow=15, arm=60)
    A.flush(cv)
    paste(cv, text_img('召入武昌楚王府 · 掌良医所事', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('楚王府', 50), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第二回 远游
def art_l_taiyi(A, cv, t, u):
    ground(A, GROUND)
    for i in range(6):
        A.d['mid'].rectangle((140 + i * 140, GROUND - 400, 250 + i * 140, GROUND), fill=170)
        for j in range(5):
            bundle(A, 195 + i * 140, GROUND - 20 - j * 74, 50, layer='yaogui' if (i + j) % 2 else 'mid')
    li(A, 540, GROUND, 160, dir=1, arm=150)
    A.flush(cv)
    paste(cv, text_img('荐入太医院 · 得读皇家藏书', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '在任约一年即辞归 一说未就任', t, t - u + P)

def scene_baicao(cv, t, c, k):
    """8-beat custom scene: 远游采药 — 武当 庐山 茅山 牛首山 ...; he walks with a herb basket while specimens line up behind him,
    and the count of entries rises."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    places = ['武当山', '庐山', '茅山', '牛首山', '摄山']
    for k in range(4):
        x = 140 + k * 270 - (ph * 40) % 270
        A.d['mid'].polygon([(x - 200, GROUND), (x - 40, GROUND - 420 - 60 * (k % 2)), (x + 40, GROUND - 420 - 60 * (k % 2)), (x + 200, GROUND)], fill=150)
    ground(A, GROUND)
    n = min(10, int(clamp(ph / 7) * 10) + 1)
    for i in range(n):
        herb(A, 120 + i * 90, GROUND, 120 + 20 * (i % 3), kind=i % 3, flower='red' if i % 2 else 'qiuhuang')
    li(A, 540 + 30 * math.sin(t * 0.5), GROUND, 190, dir=1, basket=True, ph=t * 3, arm=lerp(-8, 40, 0.5 + 0.5 * math.sin(t)))
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '远游采药', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=71)
    fx.flush(cv)
    pl = places[min(4, int(ph / 1.6))]
    cnt = int(clamp(ph / 7.5) * 1892)
    paste(cv, text_img(f'{pl} · 收录药物 {cnt} 种', SERIF, 44, AIYE if ph < 7.5 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '远游采访历时多年 具体年份已难确考', t, s0 + 2 * P)

def art_l_datura(A, cv, t, u):
    """6-beat set piece: 曼陀罗 — the books say it makes people laugh and dance; he brews it and tries it on himself, and records its numbing effect."""
    ph = u / P
    ground(A, GROUND)
    datura(A, 800, GROUND, 240, t)
    sway = 14 * clamp((ph - 2) / 1) * math.sin(t * 3) if ph < 4.5 else 0
    li(A, 380 + sway, GROUND, 190, dir=1, arm=lerp(-8, 140, clamp((ph - 1) / 0.6)) if ph < 2 else 60, bow=10 * clamp((ph - 2) / 1) if ph < 4.5 else 0)
    if ph >= 1 and ph < 2:
        A.d['yaogui'].ellipse((440, GROUND - 230, 470, GROUND - 200), fill=255)
    A.flush(cv)
    if ph < 1:
        lab, col = '相传服之令人笑舞', YAOGUI
    elif ph < 2:
        lab, col = '余尝试之', ZHU
    elif ph < 4.5:
        lab, col = '饮须半酣 · 头晕目眩', ZHU
    else:
        lab, col = '割疮灸火 宜先服此 则不觉苦也', YAOGUI
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('以身试药 只为一句实话', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.8) / 0.4))

def art_l_snake(A, cv, t, u):
    """6-beat set piece: 蕲蛇 — the 白花蛇 sold in markets were fakes; he climbs 龙峰山 with snake-catchers at night to see the real one."""
    ph = u / P
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    A.d['mid'].polygon([(100, GROUND), (540, 960), (980, GROUND)], fill=170)
    ground(A, GROUND)
    li(A, 260, GROUND, 170, dir=1, arm=60, basket=True)
    person(A, 400, GROUND, 160, dir=1, robe=False, hat='knot', arm=lerp(40, 120, clamp((ph - 2) / 0.6)), layer='mid')
    if ph > 1.5:
        snake(A, 560, 860, GROUND - 40, t, amp=18, layer='yaogui')
    A.flush(cv)
    lab = '市售白花蛇 多为赝品' if ph < 1.5 else ('随捕蛇人夜登龙峰山' if ph < 3.5 else '龙头虎口 黑质白花')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('蕲蛇', 56), 860, 1440, t, t - u + 3.5 * P, rot=6)

def art_l_pangolin(A, cv, t, u):
    """6-beat set piece: 穿山甲 — old books said it lures ants with its scales; he opens its stomach and finds about a 升 of ants: it licks them up with its tongue."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='mid')
    pangolin(A, 560, GROUND - 74, 120, open_=clamp((ph - 2) / 1.5))
    li(A, 200, GROUND, 180, dir=1, arm=lerp(-8, 100, clamp((ph - 1.5) / 0.6)))
    A.flush(cv)
    lab = '旧说 张鳞诱蚁 闭鳞入水' if ph < 2 else ('剖其胃 得蚁约一升' if ph < 4 else '实为吐舌舔食 亲见方知')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '纲目记 鳞甲之说 时珍以剖验正之', t, t - u + 2 * P)

# ================================================================ 第三回 二十七年
def art_l_drafts(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='yaogui')
    li(A, 260, GROUND, 170, dir=1, kneel=True, bow=20, arm=90, old=0.3)
    lamp(A, 800, GROUND - 74, 30, t, glow=0.9)
    n = min(3, int(u / (1.0 * P)) + 1)
    for i in range(n):
        A.d['wash'].rectangle((420 + i * 40, GROUND - 74 - 120 - i * 12, 620 + i * 40, GROUND - 74 - i * 12), fill=255)
        A.d['ink'].rectangle((420 + i * 40, GROUND - 74 - 120 - i * 12, 620 + i * 40, GROUND - 74 - i * 12), outline=200, width=2)
    A.flush(cv)
    paste(cv, text_img(f'书稿第{cn_num(n)}易', SERIF, 48, YAOGUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    stamp(cv, seal('三易其稿', 46), 860, 1020, t, t - u + 2 * P, rot=6)

def art_l_ask(A, cv, t, u):
    ground(A, GROUND)
    li(A, 300, GROUND, 180, dir=1, arm=60, basket=True, old=0.3)
    kinds = [dict(robe=False, hat='knot', load=True, arm=160), dict(robe=False, hat='knot', arm=60), dict(robe=False, hat='knot', spear=True, arm=40)]
    for j in range(3):
        person(A, 580 + j * 140, GROUND, 160, dir=-1, layer='mid' if j % 2 else 'ink', **kinds[j])
    A.flush(cv)
    paste(cv, text_img('访樵夫 渔人 猎户 药农', SERIF, 48, YAOGUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('不耻下问', 46), 860, 1020, t, t - u + P, rot=6)

def art_l_mercury(A, cv, t, u):
    """6-beat set piece: 驳水银 — alchemists claim long use of mercury makes one immortal; he writes: it is poison, never to be eaten."""
    ph = u / P
    ground(A, GROUND)
    A.d['dune'].rectangle((620, GROUND - 200, 820, GROUND), fill=255)
    A.d['ink'].polygon([(600, GROUND - 200), (840, GROUND - 200), (720, GROUND - 260)], fill=255)
    flames(A, 720, GROUND - 40, 120, 70, t, n=3, seed=71, smoke=True)
    person(A, 900, GROUND, 160, dir=-1, robe=True, hat='knot', arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    li(A, 260, GROUND, 180, dir=1, arm=lerp(-8, 110, clamp((ph - 2) / 0.6)), old=0.4)
    A.flush(cv)
    lab, col = ('方士之说 · 久服水银可成仙', YAOGUI) if ph < 2 else ('水银大毒 · 不可服食', ZHU)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 3.5:
        paste(cv, text_img('服者多死 而方士固执不悟', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 3.5) / 0.4))
    note_in(cv, '其时嘉靖帝崇信丹药 举朝成风', t, t - u + P)

def art_l_done(A, cv, t, u):
    """6-beat set piece: 成书 — after 27 years: 52 卷, 1892 种药, 11096 方, 1160 幅图."""
    ph = u / P
    ground(A, GROUND)
    n = min(26, int(clamp(ph / 3) * 26) + 1)
    for i in range(n):
        A.d['yaogui' if i % 2 else 'aiye'].rectangle((200 + (i % 2) * 360, GROUND - 22 * (i // 2 + 1), 520 + (i % 2) * 360, GROUND - 22 * (i // 2) - 3), fill=230)
    A.flush(cv)
    stats = ['五十二卷', '药物一千八百九十二种', '附方一万一千余首', '插图一千一百余幅']
    for i, s in enumerate(stats):
        st = t - u + (1 + i * 0.8) * P
        if t >= st:
            paste(cv, text_img(s, SERIF, 42, ZHU if i == 1 else YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 640 + i * 60, 1, clamp((t - st) / 0.4))
    stamp(cv, seal('成书', 56), 860, 1020, t, t - u + 4.5 * P, rot=6)
    note_in(cv, '时年六十一 历时二十七年', t, t - u + 4 * P)

def art_l_noprint(A, cv, t, u):
    ground(A, GROUND)
    for j in range(3):
        person(A, 620 + j * 130, GROUND, 160, dir=-1, robe=True, hat='knot', arm=lerp(-8, 60, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='mid')
    li(A, 300, GROUND, 180, dir=1, arm=90, old=0.6)
    book(A, 420, GROUND - 120, 90, 120, layer='yaogui')
    A.flush(cv)
    paste(cv, text_img('卷帙浩繁 · 书商无人愿刻', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_wang(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        A.d['mid'].rectangle((620, GROUND - 260, 920, GROUND), fill=200)
    A.d['ink'].polygon([(600, GROUND - 260), (940, GROUND - 260), (770, GROUND - 330)], fill=255)
    person(A, 700, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(-8, 70, ease_out((u - P) / 0.6)), layer='ink')
    li(A, 320, GROUND, 180, dir=1, bow=20, arm=90, old=0.6)
    A.flush(cv)
    paste(cv, text_img('赴太仓拜访王世贞 · 求其作序', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('太仓', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第四回 刻版
def art_l_preface(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1080, 560, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('博而不繁 详而有要', SERIF, 52, INK, 'Black', bleed=False, spacing=8), W / 2, 1080, 1, clamp((u - P) / 0.4))
    paste(cv, text_img('十年之后 王世贞终为作序', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_l_carve(A, cv, t, u):
    """6-beat set piece: 金陵刻版 — the Nanjing publisher 胡承龙 takes it on; woodblocks pile up, year after year."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    A.d['yaogui'].rectangle((440, GROUND - 120, 640, GROUND - 76), fill=255)
    for k in range(6):
        A.d['ink'].line((450 + k * 32, GROUND - 116, 450 + k * 32, GROUND - 80), fill=200, width=2)
    for j in range(2):
        person(A, 300 + j * 480, GROUND, 160, dir=1 if j == 0 else -1, robe=False, hat='knot', kneel=True, arm=lerp(80, 120, 0.5 + 0.5 * math.sin(t * 8 + j)), layer='ink')
    n = int(clamp(ph / 5) * 12)
    for i in range(n):
        A.d['yaogui'].rectangle((60 + (i % 2) * 70, GROUND - 18 * (i // 2 + 1), 120 + (i % 2) * 70, GROUND - 18 * (i // 2) - 2), fill=230)
        A.d['yaogui'].rectangle((900 + (i % 2) * 70 - 70, GROUND - 18 * (i // 2 + 1), 960 + (i % 2) * 70 - 70, GROUND - 18 * (i // 2) - 2), fill=230)
    A.flush(cv)
    lab = '金陵书商胡承龙承刻' if ph < 2.5 else '一刀一字 刻了数年'
    paste(cv, text_img(lab, SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('金陵', 56), 860, 1020, t, t - u + 0.4, rot=6)

def art_l_sons(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='yaogui')
    for j in range(2):
        person(A, 330 + j * 420, GROUND, 160, dir=1 if j == 0 else -1, robe=True, hat='knot', kneel=True, arm=100, layer='ink')
    for k in range(4):
        herb(A, 450 + k * 60, GROUND - 74, 70, kind=k % 3, flower='red')
    A.flush(cv)
    paste(cv, text_img('子孙皆承家学 · 共绘药图千余幅', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '药图由其子李建元 李建木等绘制', t, t - u + P)

def art_l_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    li(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('书未刻成 · 卒于蕲州 年七十六', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_jinling(A, cv, t, u):
    ground(A, GROUND)
    book(A, 540, GROUND, 220, 320, layer='yaogui')
    A.flush(cv)
    paste(cv, text_img('本\n草\n纲\n目', SERIF, 36, INK, 'Black', bleed=False, spacing=2), 540, GROUND - 200, 1, clamp(u / 0.4))
    paste(cv, text_img('金陵本问世 · 他没能亲眼看到', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('金陵本', 50), 860, 1020, t, t - u + P, rot=6)

def art_l_court(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 400, GROUND, 170, dir=1, robe=True, hat='knot', kneel=True, bow=30, arm=90, layer='ink')
    book(A, 520, GROUND - 40, 60, 80, layer='yaogui')
    A.flush(cv)
    paste(cv, text_img('其子李建元进献万历皇帝', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '御批 书留览 礼部知道 此后再无下文', t, t - u + P)

def art_l_spread(A, cv, t, u):
    ground(A, GROUND)
    for i in range(min(8, int(u / (0.4 * P)) + 1)):
        book(A, 180 + i * 100, GROUND, 80, 140 + 20 * (i % 3), layer='yaogui' if i % 2 else 'aiye')
    A.flush(cv)
    paste(cv, text_img('朝廷未加重视 · 书坊竞相翻刻', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '江西本刊行 此后版本数十种', t, t - u + P)

# ================================================================ 第五回 药圣
def art_l_japan(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=160)
    waves(A, 1170, t, rows=2, amp=4)
    boat(A, lerp(200, 800, ease_out(u / (3 * P))), 1190, 80, t)
    A.flush(cv)
    paste(cv, text_img('东传日本 · 长崎', SERIF, 48, YAOGUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '相传林罗山购得 献于德川家康', t, t - u + P)

def art_l_west(A, cv, t, u):
    ground(A, GROUND)
    langs = ['拉丁文', '法文', '德文', '英文', '俄文']
    A.flush(cv)
    for i in range(min(5, int(u / (0.5 * P)) + 1)):
        stamp(cv, seal(langs[i], 40, ZHU if i % 2 else INK), 220 + (i % 3) * 320, 1000 + (i // 3) * 170, t, t - u + i * 0.5 * P)
    paste(cv, text_img('先后被译为多种文字', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_darwin(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    person(A, 300, GROUND, 200, dir=1, robe=False, hat='none', kneel=True, arm=110, layer='ink')
    book(A, 560, GROUND - 74, 140, 0, open_=1.0)
    A.flush(cv)
    type_in(cv, text_img('古代中国的百科全书', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('达尔文', 50, INK), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '达尔文著作中所引 学界多认为即本草纲目', t, t - u + P)

def art_l_memory(A, cv, t, u):
    ground(A, GROUND)
    book(A, 540, GROUND, 240, 340, layer='yaogui')
    A.flush(cv)
    paste(cv, text_img('本\n草\n纲\n目', SERIF, 40, INK, 'Black', bleed=False, spacing=2), 540, GROUND - 210, 1, 1)
    paste(cv, text_img('金陵本入选世界记忆名录', SERIF, 46, YAOGUI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_l_yaosheng(A, cv, t, u):
    ground(A, GROUND)
    for k in range(7):
        herb(A, 160 + k * 125, GROUND, 140 + 30 * (k % 3), kind=k % 3, flower='red' if k % 2 else 'qiuhuang')
    A.flush(cv)
    paste(cv, text_img('后世尊为药圣', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))

def art_l_path(A, cv, t, u):
    ground(A, GROUND)
    li(A, lerp(200, 700, ease_out(u / (1.6 * P))), GROUND, 180, dir=1, basket=True, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('从落第书生 到一代药圣', SERIF, 48, YAOGUI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_l_root(A, cv, t, u):
    cabinet(A, 540, 1120, 480, 320, 30)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('中医药学的根基之书', SERIF, 48, YAOGUI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_l_legacy(A, cv, t, u):
    herb(A, 860, 1420, 90, kind=1, flower='red')

def art_l_title(A, cv, t, u):
    for k in range(3):
        herb(A, 760 + k * 90, 1440, 160 + 30 * k, kind=k, flower='red')
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    li(A, 380, 1460, 680, dir=1, basket=True, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '医家子'), 48: ('第二回', '远游'), 80: ('第三回', '二十七年'),
            112: ('第四回', '刻版'), 144: ('第五回', '药圣')}

CARDS = [
    C(0, 2, 'works', 'num', num='二十七年', line='只写一本书', art=art_l_hook_book),
    C(2, 4, 'empire', 'num', num='一千八百种药', line='一味一味考证', art=art_l_hook_herbs),
    C(4, 6, 'war', 'num', num='一朵毒花', line='他亲口尝过', art=art_l_hook_flower),
    C(6, 8, 'fate', 'num', num='三次落榜', line='才改行学医', art=art_l_hook_exam),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 医家子
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1518, main='生于蕲州', sub='医家之子', art=art_l_birth),
    C(22, 26, 'empire', 'card', year=1531, main='考中秀才', sub='十四岁', art=art_l_xiucai),
    C(26, 30, 'fate', 'card', year=1540, main='三试不第', sub='乡试落榜', art=art_l_luodi),
    C(30, 34, 'works', 'card', year=1540, main='弃儒学医', sub='逆流之船', art=art_l_resolve),
    C(34, 38, 'death', 'card', year=1545, main='蕲州大疫', sub='随父行医', note='年份约略 史料不详', art=art_l_plague),
    C(38, 42, 'night', 'card', year=1552, main='立志重修', sub='旧本多误', art=art_l_jiuben),
    C(42, 48, 'court', 'card', year=1556, main='楚王府', sub='良医所', art=art_l_chuwang),
    # ---- 第二回 远游
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'court', 'card', year=1558, main='太医院', sub='遍读藏书', art=art_l_taiyi),
    C(54, 62, 'life', 'baicao', year=1565),
    C(62, 68, 'war', 'card', year=1565, main='曼陀罗', sub='以身试药', art=art_l_datura),
    C(68, 74, 'night', 'card', year=1565, main='蕲蛇', sub='夜登龙峰', art=art_l_snake),
    C(74, 80, 'works', 'card', year=1565, main='穿山甲', sub='剖验求真', art=art_l_pangolin),
    # ---- 第三回 二十七年
    C(80, 82, 'night', 'chapter'),
    C(82, 86, 'night', 'card', year=1570, main='三易其稿', sub='一改再改', art=art_l_drafts),
    C(86, 90, 'life', 'card', year=1570, main='不耻下问', sub='樵渔猎农', art=art_l_ask),
    C(90, 96, 'war', 'card', year=1575, main='驳斥丹药', sub='水银有毒', art=art_l_mercury),
    C(96, 102, 'empire', 'card', year=1578, main='本草纲目', sub='成书', art=art_l_done),
    C(102, 106, 'fate', 'card', year=1579, main='无人刊刻', sub='书商摇头', art=art_l_noprint),
    C(106, 112, 'court', 'card', year=1580, main='拜访王世贞', sub='求序太仓', art=art_l_wang),
    # ---- 第四回 刻版
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'empire', 'card', year=1590, main='王序', sub='十年之后', art=art_l_preface),
    C(118, 124, 'works', 'card', year=1590, main='金陵刻版', sub='胡承龙', art=art_l_carve),
    C(124, 128, 'life', 'card', year=1591, main='子孙绘图', sub='家学相承', art=art_l_sons),
    C(128, 132, 'death', 'card', year=1593, main='李时珍去世', sub='年七十六', art=art_l_death),
    C(132, 136, 'empire', 'card', year=1593, main='金陵本', sub='身后问世', art=art_l_jinling),
    C(136, 140, 'court', 'card', year=1596, main='献书朝廷', sub='书留览', art=art_l_court),
    C(140, 144, 'works', 'card', year=1603, main='民间风行', sub='江西重刻', art=art_l_spread),
    # ---- 第五回 药圣
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'life', 'card', year=1607, main='东传日本', sub='长崎', art=art_l_japan),
    C(150, 154, 'night', 'card', year=1735, main='西传欧洲', sub='译成多国文字', note='1735年法文节译本问世', art=art_l_west),
    C(154, 158, 'court', 'card', year=1868, main='达尔文', sub='古代百科全书', art=art_l_darwin),
    C(158, 162, 'empire', 'card', year=2011, main='世界记忆', sub='金陵本', art=art_l_memory),
    C(162, 166, 'works', 'card', year=2011, main='药圣', sub='后世尊称', art=art_l_yaosheng),
    C(166, 168, 'fate', 'card', year=2011, main='落第书生', sub='一代药圣', art=art_l_path),
    C(168, 170, 'end', 'card', year=2011, main='本草', sub='仍在案头', art=art_l_root),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='柒拾壹', col=YAOGUI, acc=AIYE, born=1518, died=1593, age0=1517,
    born_lab='1518年', died_lab='1593年', years_txt='公元1518 — 1593',
    hook_q='三次科举落榜 · 他为什么成了药圣？',
    name_line='李时珍 · 字东璧', name='李时珍', seal='濒湖', title_art=art_l_title,
    q1='一代药圣？', q2='落第书生？',
    end_art=art_l_legacy, end_big='本草纲目', end_seal='濒湖',
    end_l1='科举考场他三次落榜', end_l2='却用一本书走遍了世界',
    end_brush='医者仁心', end_ask='本草纲目里你知道哪味药？评论区聊聊', next='海瑞'),
    scenes=dict(chapter=scene_chapter, baicao=scene_baicao))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
