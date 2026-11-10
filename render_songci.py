"""千古人物志 · 第捌拾柒集 · 宋慈 (1186–1249)
Look: 提刑青黑 + 红伞朱, 验尸格 corner borders (a measuring ruler with ticks), 建阳 hills behind.
Chapter card: 洗冤集录 — an open book; each chapter a new method appears on its page: 镰刀 红伞 银钗 尺 骨; in the last chapter the book closes.
Set pieces: custom 8-beat scene 'liandao' (镰刀引蝇), 6-beat 平三峒, 6-beat 改道运盐, 6-beat 济粜, 6-beat 红伞验骨,
6-beat 自缢与勒死, 6-beat 银钗, 6-beat 成书.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_luyou as Lu           # engine + helpers (previous episode)
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
from render_simayi import emperor
from render_sunwu import army, banner
from render_zhuxi import book

F.RIPPLE = False
TIXING = (52, 66, 76)               # 提刑青黑
HONGSAN = (196, 52, 40)             # 红伞朱
S.LAYERS.append(('tixing', TIXING, 0.9, 1.0))
S.LAYERS.append(('hongsan', HONGSAN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='冤', life='宋', court='刑', night='验', war='狱', empire='提', works='录', fate='巡', death='骨', end='洗')
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
G.THEMES['empire']['sun'] = (TIXING, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (HONGSAN, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # 建溪
    _d.line([(40 + i * 30, 1456 + _k * 14 + 4 * math.sin(i * 0.5 + _k)) for i in range(35)], fill=(90, 110, 120, 46 - _k * 10), width=3)
for _x in (110, 970):               # wooden 公案 posts at the margins
    _d.rectangle((_x - 8, 1320, _x + 8, 1446), fill=(110, 90, 70, 70))
    _d.rectangle((_x - 30, 1312, _x + 30, 1322), fill=(110, 90, 70, 70))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (96, 100, 104)}
def draw_background(t, theme):
    """建阳: green hills over the 建溪."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 192, 192), (156, 162, 166), MTN_COL.get(theme, (100, 112, 120))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
def draw_frame_border(canvas):
    """验尸格: a measuring ruler with tick marks in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=TIXING + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=TIXING + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.rectangle((min(cx - 30 * sx, cx + 30 * sx), cy - 8, max(cx - 30 * sx, cx + 30 * sx), cy + 8), fill=(170, 140, 90, 230))
        for k in range(7):
            xx = cx - 30 * sx + k * 10 * sx
            d.line((xx, cy - 8, xx, cy - 8 + (10 if k % 2 == 0 else 5)), fill=(60, 50, 40, 230), width=2)
        d.ellipse((cx - 5, cy + 12, cx + 5, cy + 22), fill=HONGSAN + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def ci(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """宋慈: Southern Song judicial commissioner — 展脚幞头, a trim beard (white when old), a dark official robe with a red belt."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.08 * h, y - 1.06 * h, x + 0.08 * h, y - 0.92 * h), 180, 360, fill=255)
        d.line((x - 0.26 * h, y - 0.97 * h, x + 0.26 * h, y - 0.97 * h), fill=255, width=max(2, int(0.013 * h)))
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.02 * h, y - 0.85 * h), (x + dir * 0.09 * h, y - 0.85 * h), (x + dir * 0.05 * h, y - 0.68 * h)], fill=255)
    if not kw.get('fall'):
        A.d['tixing'].polygon([(x - 0.1 * h, y - (0.48 if kneel else 0.76) * h), (x + 0.1 * h, y - (0.48 if kneel else 0.76) * h), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=170)
        A.d['hongsan'].rectangle((x - 0.1 * h, y - (0.36 if kneel else 0.56) * h, x + 0.1 * h, y - (0.33 if kneel else 0.53) * h), fill=255)
    return hand

def corpse(A, cx, base, w, layer='mid', mark=None):
    A.d['dune'].rectangle((cx - w, base - 0.1 * w, cx + w, base), fill=200)
    A.d[layer].polygon([(cx - 0.9 * w, base - 0.12 * w), (cx + 0.7 * w, base - 0.12 * w), (cx + 0.7 * w, base - 0.24 * w), (cx - 0.9 * w, base - 0.2 * w)], fill=230)
    A.d[layer].ellipse((cx + 0.68 * w, base - 0.28 * w, cx + 0.92 * w, base - 0.08 * w), fill=230)
    if mark == 'cross':
        A.d['red'].line((cx + 0.64 * w, base - 0.24 * w, cx + 0.64 * w, base - 0.1 * w), fill=255, width=4)
        A.d['red'].line((cx + 0.58 * w, base - 0.17 * w, cx + 0.7 * w, base - 0.17 * w), fill=255, width=4)
    elif mark == 'v':
        A.d['red'].line([(cx + 0.6 * w, base - 0.1 * w), (cx + 0.66 * w, base - 0.22 * w), (cx + 0.72 * w, base - 0.1 * w)], fill=255, width=4)

def sickle(A, x, base, s, layer='ink'):
    A.d['huyang'].line((x, base, x + 0.1 * s, base - 0.6 * s), fill=255, width=max(4, int(0.05 * s)))
    A.d[layer].arc((x + 0.1 * s - 0.4 * s, base - 0.6 * s - 0.4 * s, x + 0.1 * s + 0.4 * s, base - 0.6 * s + 0.4 * s), 200, 340, fill=255, width=max(4, int(0.05 * s)))

def flies(A, cx, cy, n, t, r=40):
    for k in range(n):
        a = t * (3 + k % 3) + k * 1.7
        x = cx + r * math.cos(a) * (0.5 + 0.5 * math.sin(k)); y = cy + 0.6 * r * math.sin(a * 1.3)
        A.d['ink'].ellipse((x - 4, y - 3, x + 4, y + 3), fill=255)
        A.d['wash'].line((x - 6, y - 4, x + 6, y - 4), fill=180, width=1)

def umbrella(A, cx, top, r, layer='hongsan'):
    A.d[layer].chord((cx - r, top, cx + r, top + 0.8 * r), 180, 360, fill=255)
    for k in range(7):
        A.d['ink'].line((cx, top + 0.4 * r, cx - r + k * r / 3, top + 0.4 * r), fill=120, width=2)
    A.d['ink'].line((cx, top, cx, top + 1.6 * r), fill=255, width=6)

def bone(A, cx, cy, L_, crack=0.0):
    A.d['wash'].line((cx - L_ / 2, cy, cx + L_ / 2, cy), fill=255, width=max(8, int(0.08 * L_)))
    for ex in (-1, 1):
        A.d['wash'].ellipse((cx + ex * L_ / 2 - 0.08 * L_, cy - 0.09 * L_, cx + ex * L_ / 2 + 0.08 * L_, cy + 0.09 * L_), fill=255)
    if crack > 0:
        A.d['red'].line([(cx - 0.05 * L_, cy - 0.04 * L_), (cx, cy + 0.02 * L_), (cx + 0.06 * L_, cy - 0.03 * L_)], fill=int(255 * crack), width=4)

def hairpin(A, x, y, L_, black=0.0):
    A.d['fangtian'].line((x, y, x, y + L_), fill=255, width=6)
    if black > 0:
        A.d['ink'].line((x, y + 0.5 * L_, x, y + L_), fill=int(255 * black), width=6)
    A.d['fangtian'].ellipse((x - 10, y - 10, x + 10, y + 10), fill=255)

def method_page(A, cv, cx, cy, s, n, t):
    """Open book with up to n method icons."""
    A.d['wash'].polygon([(cx - s, cy - 0.65 * s), (cx, cy - 0.55 * s), (cx + s, cy - 0.65 * s), (cx + s, cy + 0.65 * s), (cx, cy + 0.75 * s), (cx - s, cy + 0.65 * s)], fill=255)
    A.d['ink'].line((cx, cy - 0.55 * s, cx, cy + 0.75 * s), fill=200, width=3)
    slots = [(cx - 0.55 * s, cy - 0.2 * s), (cx + 0.5 * s, cy - 0.25 * s), (cx - 0.5 * s, cy + 0.35 * s), (cx + 0.5 * s, cy + 0.3 * s), (cx, cy - 0.05 * s)]
    if n >= 1: sickle(A, slots[0][0] - 0.1 * s, slots[0][1] + 0.25 * s, 0.4 * s)
    if n >= 2: umbrella(A, slots[1][0], slots[1][1] - 0.2 * s, 0.22 * s)
    if n >= 3: hairpin(A, slots[2][0], slots[2][1] - 0.2 * s, 0.4 * s, black=0.7)
    if n >= 4:
        A.d['huyang'].rectangle((slots[3][0] - 0.3 * s, slots[3][1] - 0.04 * s, slots[3][0] + 0.3 * s, slots[3][1] + 0.04 * s), fill=255)
        for k in range(7):
            A.d['ink'].line((slots[3][0] - 0.3 * s + k * 0.1 * s, slots[3][1] - 0.04 * s, slots[3][0] - 0.3 * s + k * 0.1 * s, slots[3][1]), fill=255, width=2)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 4)}
def art_book_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    if kb == 144 and q > 0.6:
        book(A, 540, 1240, 240, 340, layer='tixing')
        A.flush(cv)
        paste(cv, text_img('洗\n冤\n集\n录', SERIF, 40, INK, 'Black', bleed=False, spacing=2), 540, 1080, 1, clamp((q - 0.6) / 0.2))
    else:
        method_page(A, cv, 540, 1060, 320, b if q > 0.5 else a, t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_book_chapter)
    ink_in(cv, text_img(no, SERIF, 56, TIXING, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_c_hook_sickle(A, cv, t, u):
    ground(A, GROUND)
    sickle(A, 500, GROUND, 300)
    flies(A, 560, GROUND - 220, int(clamp(u / (1.2 * P)) * 12) + 1, t, r=60)

def art_c_hook_umbrella(A, cv, t, u):
    ground(A, GROUND)
    umbrella(A, 540, 860, 240)
    bone(A, 540, GROUND - 60, 340, crack=clamp(u / (1.2 * P)))

def art_c_hook_book(A, cv, t, u):
    ground(A, GROUND)
    book(A, 540, GROUND, 240, 340, layer='tixing')
    A.flush(cv)
    paste(cv, text_img('洗\n冤\n集\n录', SERIF, 40, INK, 'Black', bleed=False, spacing=2), 540, GROUND - 200, 1, clamp(u / 0.4))

def art_c_hook_cases(A, cv, t, u):
    ground(A, GROUND)
    n = min(40, int(clamp(u / (1.2 * P)) * 40) + 1)
    for i in range(n):
        A.d['wash'].rectangle((200 + (i % 10) * 70, GROUND - 40 - (i // 10) * 60, 250 + (i % 10) * 70, GROUND - 6 - (i // 10) * 60), fill=255)
        A.d['red'].line((205 + (i % 10) * 70, GROUND - 23 - (i // 10) * 60, 245 + (i % 10) * 70, GROUND - 23 - (i // 10) * 60), fill=200, width=3)

# ================================================================ 第一回 建阳
def art_c_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x - 60, GROUND - 240), (x + 60, GROUND - 240), (x + 220, GROUND)], fill=150)
    A.d['wash'].rectangle((420, GROUND - 160, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 160), (680, GROUND - 160), (540, GROUND - 220)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('福建建阳人 · 父宋巩为广州节度推官', SERIF, 44, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('建阳', 56), 860, 1020, t, t - u + P, rot=6)

def art_c_wuzhi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    person(A, 780, GROUND, 190, dir=-1, robe=True, hat='knot', kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    person(A, 320, GROUND, 140, dir=1, robe=True, hat='none', kneel=True, arm=90, layer='tixing')
    A.flush(cv)
    paste(cv, text_img('少从朱熹弟子吴稚求学', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_c_taixue(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(-8, 80, ease_out(u / 0.6)), layer='ink')
    ci(A, 400, GROUND, 180, dir=1, bow=15, arm=90)
    A.flush(cv)
    paste(cv, text_img('入太学 · 真德秀奇其文 以为出自肺腑', SERIF, 44, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_c_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='tixing')
    ground(A, GROUND)
    ci(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('登进士第 · 时年三十二', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('进士', 56), 860, 1020, t, t - u + P, rot=6)

def art_c_father(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, layer='ink')
    ci(A, 880, GROUND, 150, dir=-1, kneel=True, bow=30)
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('授鄞县尉 · 适逢父丧 未及赴任', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_c_xinfeng(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='信丰', layer='mid', open_=1.0)
    ground(A, GROUND)
    ci(A, 540, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('任江西信丰县主簿', SERIF, 48, TIXING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_c_sandong(A, cv, t, u):
    """6-beat set piece: 平三峒 — rebellion in the hill settlements of 南安; he joins 陈韡's campaign, urges amnesty for those coerced, and wins merit."""
    ph = u / P
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 40, GROUND - 400), (x + 40, GROUND - 400), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    if ph < 3:
        army(A, lerp(-300, 200, clamp(ph / 3)), GROUND, 6, dir=1, layer='tixing', t=t, march=True, h=100)
        lab = '随陈韡平定南安三峒之乱'
    else:
        for j in range(6):
            person(A, 560 + (j % 3) * 120, GROUND - (j // 3) * 40, 120, dir=-1, robe=False, hat='knot', kneel=True, bow=20, layer='ink')
        ci(A, 300, GROUND, 190, dir=1, arm=lerp(-8, 100, clamp((ph - 3) / 0.6)))
        lab = '胁从者 招抚而归'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

# ================================================================ 第二回 初仕
def art_c_changting(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='长汀', layer='mid', open_=1.0)
    ground(A, GROUND)
    ci(A, 540, GROUND, 190, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('知汀州长汀县', SERIF, 48, TIXING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_c_salt(A, cv, t, u):
    """6-beat set piece: 改道运盐 — salt came up-river from 福州, a year's journey, ruinously dear; he ships it down-river from 潮州 instead,
    three months there and back; the price falls."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=150)
    river(A, 1170, t, rows=2, amp=4, speed=-1.0 if ph < 3 else 1.6)
    if ph < 3:
        boat(A, lerp(900, 700, clamp(ph / 3)), 1190, 80, t, sail=False)
        for j in range(3):
            person(A, lerp(980, 780, clamp(ph / 3)) + j * 40, 1160, 90, dir=-1, robe=False, hat='knot', bow=40, arm=160, layer='ink')
        lab, col = '旧时食盐自福州逆流而上 · 一年方至 价高', TIXING
    else:
        for k in range(3):
            boat(A, lerp(-100, 900, ((t * 0.1 + k / 3) % 1)), 1190, 80, t)
        lab, col = '改从潮州顺流运盐 · 往返仅三月', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('盐价大降 百姓称便', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.5) / 0.4))

def art_c_shaowu(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='邵武', layer='mid', open_=1.0)
    ground(A, GROUND)
    ci(A, 540, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('任邵武军通判', SERIF, 48, TIXING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_c_jitiao(A, cv, t, u):
    """6-beat set piece: 济粜 — famine at 南剑州; the rich hoard grain; he ranks households: the richest give a share, the middling sell at fair price, the poor receive."""
    ph = u / P
    ground(A, GROUND)
    for k in range(3):
        x = 260 + k * 280
        A.d['dune'].rectangle((x - 80, GROUND - 160, x + 80, GROUND), fill=230)
        A.d['ink'].polygon([(x - 100, GROUND - 160), (x + 100, GROUND - 160), (x, GROUND - 230)], fill=255)
    if ph < 2:
        for j in range(5):
            person(A, 140 + j * 90, GROUND, 110, dir=1, robe=False, hat='knot', bow=40, arm=-8, layer='mid')
        lab = '南剑州饥荒 · 豪富囤米'
    else:
        for j in range(6):
            person(A, lerp(-100, 900, ((t * 0.08 + j / 6) % 1)), GROUND, 100, dir=1, robe=False, hat='knot', load=True, arm=160, ph=t * 4 + j, layer='ink')
        ci(A, 900, GROUND, 180, dir=-1, arm=lerp(-8, 100, clamp((ph - 2) / 0.6)))
        lab = '分户五等 · 富者出米 中者平价 贫者受济' if ph < 4.5 else '民赖以全'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, TIXING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

def art_c_tixing(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='tixing')
    ground(A, GROUND)
    ci(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('擢广东提点刑狱 · 时年五十四', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('提刑', 56), 860, 1020, t, t - u + P, rot=6)

def art_c_jian(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    ci(A, 280, GROUND, 170, dir=1, kneel=True, arm=lerp(80, 110, 0.5 + 0.5 * math.sin(t * 4)))
    n = int(clamp(u / (3 * P)) * 20)
    for i in range(20 - n):
        A.d['wash'].rectangle((440 + (i % 5) * 40, GROUND - 90 - (i // 5) * 26, 474 + (i % 5) * 40, GROUND - 70 - (i // 5) * 26), fill=255)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    paste(cv, text_img('积案累累 · 八个月审结二百余宗', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 验尸
def scene_liandao(cv, t, c, k):
    """8-beat custom scene: 镰刀引蝇 — a man is hacked to death in a field; no one confesses; every household is told to bring its sickle and lay it in the sun;
    flies gather on one blade alone — drawn by the traces of blood; its owner confesses."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    if ph < 2:
        corpse(A, 540, GROUND, 260)
        for j in range(5):
            person(A, 160 + j * 90 if j < 3 else 760 + (j - 3) * 90, GROUND, 120, dir=1 if j < 3 else -1, robe=False, hat='knot', arm=-8, layer='mid')
        lab, col = '路旁有人被砍杀 · 无人承认', TIXING
    elif ph < 4.5:
        for i in range(9):
            sickle(A, 180 + i * 85, GROUND, 120)
        ci(A, 900, GROUND, 170, dir=-1, arm=lerp(-8, 100, clamp((ph - 2) / 0.6)))
        lab, col = '令各家交出镰刀 · 排于烈日之下', TIXING
    else:
        for i in range(9):
            sickle(A, 180 + i * 85, GROUND, 120, layer='red' if i == 5 else 'ink')
        flies(A, 180 + 5 * 85 + 30, GROUND - 90, int(clamp((ph - 4.5) / 1.5) * 14) + 2, t, r=50)
        lab, col = '苍蝇独聚一刀 · 血腥虽洗犹在', ZHU
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '镰刀引蝇', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=87)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    if ph >= 6.5:
        paste(cv, text_img('凶手叩首服罪', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 6.5) / 0.4))
    note_in(cv, '案例载于洗冤集录 年份不可考', t, s0 + 2 * P)

def art_c_hongsan(A, cv, t, u):
    """6-beat set piece: 红伞验骨 — bruises on the bones can't be seen by eye; on a clear day hold a red oil-paper umbrella over them and the marks appear."""
    ph = u / P
    ground(A, GROUND)
    bone(A, 540, GROUND - 60, 360, crack=clamp((ph - 3) / 1))
    if ph >= 2:
        umbrella(A, 540, lerp(700, 860, clamp((ph - 2) / 0.6)), 240)
        A.d['red'].ellipse((540 - 260, GROUND - 120, 540 + 260, GROUND), fill=int(90 * clamp((ph - 2.5) / 0.6)))
    ci(A, 200, GROUND, 180, dir=1, arm=lerp(-8, 100, clamp((ph - 1.5) / 0.6)))
    A.flush(cv)
    lab = '骨上伤痕 肉眼难辨' if ph < 2 else ('晴日以红油伞遮之' if ph < 3.5 else '伤痕显现')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else TIXING, 'Black', bleed=False, spacing=4), W / 2, 700, 1, 1)
    note_in(cv, '红光滤去杂色 与现代紫外检验原理相近', t, t - u + 3.5 * P)

def art_c_zixia(A, cv, t, u):
    """6-beat set piece: 自缢与勒死 — a hanging leaves a rope mark rising behind the ears, not meeting; a strangling leaves a level mark crossing at the nape."""
    ph = u / P
    ground(A, GROUND)
    for k, (x, kind) in enumerate([(340, 'v'), (740, 'h')]):
        A.d['wash'].ellipse((x - 120, 900, x + 120, 1180), fill=255)
        A.d['ink'].ellipse((x - 120, 900, x + 120, 1180), outline=200, width=4)
        A.d['wash'].rectangle((x - 70, 1180, x + 70, 1300), fill=255)
        if ph >= 1 + 2 * k:
            if kind == 'v':
                A.d['red'].line([(x - 80, 1130), (x, 1200), (x + 80, 1130)], fill=255, width=8)
            else:
                A.d['red'].line((x - 75, 1220, x + 75, 1220), fill=255, width=8)
                A.d['red'].line((x + 50, 1205, x + 80, 1240), fill=255, width=6)
    A.flush(cv)
    if ph < 3:
        lab, col = '自缢 · 绳痕斜上耳后 八字不交', TIXING
    elif ph < 5:
        lab, col = '勒死 · 绳痕平直 交于项后', ZHU
    else:
        lab, col = '一痕之差 生死之辨', TIXING
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '辨伪造自缢 以防凶手脱罪', t, t - u + 2 * P)

def art_c_nisi(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=3)
    corpse(A, 540, 1200, 240)
    for k in range(5):
        A.d['wash'].ellipse((730 + k * 8 - 6, 1120 - k * 10 - 6, 730 + k * 8 + 6, 1120 - k * 10 + 6), fill=255)
    A.flush(cv)
    paste(cv, text_img('生前溺水 口鼻有沫 · 死后抛尸则无', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '辨溺死真伪', t, t - u + P)

def art_c_yinchai(A, cv, t, u):
    """6-beat set piece: 银钗验毒 — a silver hairpin, cleaned with soap-pod water, is put into the dead man's mouth and sealed with paper; drawn out after a while, it is black."""
    ph = u / P
    ground(A, GROUND)
    corpse(A, 500, GROUND, 260)
    if ph < 2:
        hairpin(A, 760, GROUND - 260, 160)
        lab, col = '以皂角水洗净银钗', TIXING
    elif ph < 4:
        hairpin(A, 728, GROUND - 120, 120)
        A.d['wash'].rectangle((700, GROUND - 90, 760, GROUND - 60), fill=255)
        lab, col = '探入死者口中 · 以纸封闭良久', TIXING
    else:
        hairpin(A, 820, GROUND - 260, 160, black=clamp((ph - 4) / 0.6))
        lab, col = '取出 色呈青黑 · 即为中毒', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '今知此法只对含硫之毒有效', t, t - u + 4 * P)

# ================================================================ 第四回 提刑
def art_c_guangxi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    ci(A, 540, GROUND, 200, dir=1, arm=60, old=0.4)
    A.flush(cv)
    paste(cv, text_img('历任江西 广西提点刑狱', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_c_xunxing(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 40, GROUND - 400), (x + 40, GROUND - 400), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    ci(A, lerp(100, 800, (t * 0.06) % 1), GROUND, 170, dir=1, ph=t * 3, arm=-8, old=0.4)
    A.flush(cv)
    paste(cv, text_img('巡行所部 · 虽穷乡僻壤 必亲至', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_c_chuqing(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 580, 320, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('狱事莫重于大辟\n大辟莫重于初情\n初情莫重于检验', SERIF, 44, INK, 'Black', bleed=False, spacing=14), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('洗冤集录 · 自序', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_c_book(A, cv, t, u):
    """6-beat set piece: 成书 — gathering the older manuals, adding what he himself has seen, he compiles 洗冤集录 in five juan."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    ci(A, 260, GROUND, 180, dir=1, kneel=True, bow=20, arm=90, old=0.6)
    lamp(A, 800, GROUND - 74, 30, t, glow=0.9)
    if ph < 2:
        for k in range(4):
            book(A, 420 + k * 70, GROUND - 74, 54, 90, layer='mid')
        lab = '汇集内恕录等前人诸书'
    elif ph < 4:
        slips(A, 440, GROUND - 74, min(14, int(clamp((ph - 2) / 2) * 14) + 1), 70, layer='tixing')
        lab = '参以亲身所历'
    else:
        for k in range(5):
            book(A, 400 + k * 70, GROUND - 74, 54, 110, layer='tixing')
        lab = '洗冤集录 五卷成书 · 时年六十二'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4 else TIXING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('洗冤', 60), 860, 1020, t, t - u + 4 * P, rot=6)

def art_c_hunan(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='tixing')
    ground(A, GROUND)
    ci(A, 540, GROUND, 200, dir=1, arm=60, old=0.6)
    A.flush(cv)
    paste(cv, text_img('任湖南提点刑狱 · 刊行洗冤集录', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_c_shenzhong(A, cv, t, u):
    ground(A, GROUND)
    corpse(A, 620, GROUND, 220)
    ci(A, 300, GROUND, 190, dir=1, bow=20, arm=90, old=0.6)
    A.flush(cv)
    paste(cv, text_img('不敢萌一毫慢易心', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '自序之语', t, t - u + P)

def art_c_jinglue(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='广州', layer='mid', open_=1.0)
    ground(A, GROUND)
    ci(A, 540, GROUND, 190, dir=1, arm=60, old=0.7)
    A.flush(cv)
    paste(cv, text_img('任广东经略安抚使', SERIF, 48, TIXING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 洗冤
def art_c_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    ci(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于广州任上 · 年六十四', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_c_mumen(A, cv, t, u):
    A.d['mid'].chord((380, GROUND - 160, 700, GROUND + 160), 180, 360, fill=230)
    A.d['ink'].rectangle((500, GROUND - 240, 580, GROUND - 60), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('宋理宗亲书墓门 · 以旌其功', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_c_first(A, cv, t, u):
    ground(A, GROUND)
    book(A, 380, GROUND, 200, 300, layer='tixing')
    book(A, 720, GROUND, 160, 220, layer='mid')
    A.flush(cv)
    paste(cv, text_img('1247', SERIF, 40, INK, 'Black', bleed=False), 380, GROUND - 340, 1, 1)
    paste(cv, text_img('1602', SERIF, 40, DIM, 'Black', bleed=False), 720, GROUND - 260, 1, clamp((u - P) / 0.4))
    paste(cv, text_img('世界最早的法医学专著 · 早于欧洲三百余年', SERIF, 44, TIXING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_c_translate(A, cv, t, u):
    ground(A, GROUND)
    for i in range(min(6, int(u / (0.4 * P)) + 1)):
        book(A, 220 + i * 130, GROUND, 100, 160 + 20 * (i % 3), layer='tixing' if i % 2 else 'mid')
    A.flush(cv)
    paste(cv, text_img('先后被译为荷 英 法 德 日等文字', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_c_limit(A, cv, t, u):
    ground(A, GROUND)
    bone(A, 540, GROUND - 80, 300)
    for k in range(3):
        A.d['red'].ellipse((500 + k * 30 - 8, GROUND - 120 - 8, 500 + k * 30 + 8, GROUND - 120 + 8), fill=200)
    A.flush(cv)
    paste(cv, text_img('滴血认亲等法 · 今日看来并无科学依据', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '受时代所限 不必苛责古人', t, t - u + P)

def art_c_bizu(A, cv, t, u):
    ground(A, GROUND)
    ci(A, 540, GROUND, 260, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)), old=0.5)
    A.flush(cv)
    paste(cv, text_img('后世尊为法医学鼻祖', SERIF, 48, TIXING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_c_end(A, cv, t, u):
    ground(A, GROUND)
    method_page(A, cv, 540, 1120, 300, 4, t)
    A.flush(cv)
    paste(cv, text_img('洗冤泽物 当与起死回生同功', SERIF, 46, TIXING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_c_legacy(A, cv, t, u):
    umbrella(A, 860, 1340, 60)

def art_c_title(A, cv, t, u):
    umbrella(A, 820, 1200, 120)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    ci(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '建阳'), 48: ('第二回', '初仕'), 80: ('第三回', '验尸'),
            112: ('第四回', '提刑'), 144: ('第五回', '洗冤')}

CARDS = [
    C(0, 2, 'night', 'num', num='一把镰刀', line='引来苍蝇破了案', art=art_c_hook_sickle),
    C(2, 4, 'works', 'num', num='一把红伞', line='照出骨上伤痕', art=art_c_hook_umbrella),
    C(4, 6, 'empire', 'num', num='一本书', line='世界最早的法医学专著', art=art_c_hook_book),
    C(6, 8, 'court', 'num', num='八个月', line='审结两百多宗积案', art=art_c_hook_cases),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 建阳
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1186, main='生于建阳', sub='童游里', art=art_c_birth),
    C(22, 26, 'works', 'card', year=1200, main='师从吴稚', sub='朱子门人', note='年份约略', art=art_c_wuzhi),
    C(26, 30, 'night', 'card', year=1205, main='入太学', sub='二十岁', art=art_c_taixue),
    C(30, 34, 'empire', 'card', year=1217, main='进士', sub='三十二岁', art=art_c_jinshi),
    C(34, 38, 'death', 'card', year=1217, main='父丧', sub='未及赴任', art=art_c_father),
    C(38, 42, 'court', 'card', year=1226, main='信丰主簿', sub='初入仕途', art=art_c_xinfeng),
    C(42, 48, 'war', 'card', year=1228, main='平三峒', sub='招抚胁从', art=art_c_sandong),
    # ---- 第二回 初仕
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'court', 'card', year=1232, main='知长汀', sub='汀州', note='年份约略', art=art_c_changting),
    C(54, 60, 'works', 'card', year=1235, main='改道运盐', sub='顺流而下', note='年份约略', art=art_c_salt),
    C(60, 64, 'empire', 'card', year=1237, main='邵武通判', sub='邵武军', art=art_c_shaowu),
    C(64, 70, 'life', 'card', year=1238, main='济粜', sub='分户济民', art=art_c_jitiao),
    C(70, 74, 'empire', 'card', year=1239, main='提点刑狱', sub='广东', art=art_c_tixing),
    C(74, 80, 'night', 'card', year=1239, main='清理积案', sub='八个月', art=art_c_jian),
    # ---- 第三回 验尸
    C(80, 82, 'night', 'chapter'),
    C(82, 90, 'death', 'liandao', year=1240),
    C(90, 96, 'works', 'card', year=1241, main='红伞验骨', sub='伤痕显现', note='案例年份不可考', art=art_c_hongsan),
    C(96, 102, 'night', 'card', year=1242, main='自缢勒死', sub='一痕之辨', note='案例年份不可考', art=art_c_zixia),
    C(102, 106, 'war', 'card', year=1243, main='溺死辨', sub='口鼻有沫', note='案例年份不可考', art=art_c_nisi),
    C(106, 112, 'life', 'card', year=1244, main='银钗验毒', sub='青黑即毒', note='案例年份不可考', art=art_c_yinchai),
    # ---- 第四回 提刑
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'empire', 'card', year=1245, main='四任提刑', sub='江西广西', art=art_c_guangxi),
    C(118, 122, 'fate', 'card', year=1246, main='巡行', sub='必亲至', art=art_c_xunxing),
    C(122, 126, 'court', 'card', year=1246, main='初情', sub='莫重于检验', art=art_c_chuqing),
    C(126, 132, 'works', 'card', year=1247, main='洗冤集录', sub='六十二岁', art=art_c_book),
    C(132, 136, 'empire', 'card', year=1247, main='湖南提刑', sub='刊行', art=art_c_hunan),
    C(136, 140, 'night', 'card', year=1248, main='不敢慢易', sub='一毫', art=art_c_shenzhong),
    C(140, 144, 'fate', 'card', year=1249, main='广东经略', sub='安抚使', art=art_c_jinglue),
    # ---- 第五回 洗冤
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=1249, main='宋慈去世', sub='年六十四', art=art_c_death),
    C(150, 154, 'court', 'card', year=1250, main='御书墓门', sub='理宗', note='年份约略', art=art_c_mumen),
    C(154, 158, 'empire', 'card', year=1602, main='世界最早', sub='法医学专著', art=art_c_first),
    C(158, 162, 'works', 'card', year=1874, main='译遍世界', sub='多国文字', art=art_c_translate),
    C(162, 166, 'night', 'card', year=1874, main='时代局限', sub='滴血认亲', art=art_c_limit),
    C(166, 168, 'fate', 'card', year=1874, main='法医鼻祖', sub='后世尊称', art=art_c_bizu),
    C(168, 170, 'end', 'card', year=1874, main='洗冤泽物', sub='起死回生', art=art_c_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='捌拾柒', col=TIXING, acc=HONGSAN, born=1186, died=1249, age0=1185,
    born_lab='1186年', died_lab='1249年', years_txt='公元1186 — 1249',
    hook_q='没有显微镜的年代 · 他怎么让死者开口说话？',
    name_line='宋慈 · 字惠父', name='宋慈', seal='提刑', title_art=art_c_title,
    q1='法医鼻祖？', q2='铁面提刑？',
    end_art=art_c_legacy, end_big='洗冤', end_seal='提刑',
    end_l1='他替死者说话', end_l2='也替活人洗冤',
    end_brush='洗冤泽物', end_ask='洗冤集录里 你最好奇哪个方法？评论区聊聊', next='俞大猷'),
    scenes=dict(chapter=scene_chapter, liandao=scene_liandao))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
