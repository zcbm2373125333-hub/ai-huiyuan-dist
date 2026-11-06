"""千古人物志 · 第陆拾捌集 · 沈括 (1031–1095)
Look: 梦溪碧 + 磁针红, 指南针 corner borders, a 梦溪 chapter card: one more entry of the 梦溪笔谈 notebook opens each chapter —
a compass needle, a strata cliff, a star chart, a movable-type tray — and in the last chapter the book closes.
Set pieces: 6-beat 磁针偏东, 6-beat 太行化石, custom 8-beat scene 'tianwen' (浑仪观星 · 十二气历), 6-beat 永乐城之败,
6-beat 活字印刷 (毕昇).
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_ouyangxiu as Oy       # engine + helpers (previous episode)
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
from render_songtaizu import tent
from render_quyuan import river
from render_sunwu import army, banner
from render_simayi import emperor
from render_zhangheng import armillary

F.RIPPLE = False
MENGXI = (60, 120, 120)             # 梦溪碧
CIZHEN = (196, 58, 44)              # 磁针红
S.LAYERS.append(('mengxi', MENGXI, 0.9, 1.0))
S.LAYERS.append(('cizhen', CIZHEN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='括', life='沈', court='宋', night='星', war='边', empire='谈', works='格', fate='贬', death='溪', end='谈')
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
G.THEMES['empire']['sun'] = (MENGXI, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (CIZHEN, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(4):                 # 梦溪 stream
    _d.line([(60 + i * 30, 1450 + _k * 16 + 6 * math.sin(i * 0.45 + _k)) for i in range(34)], fill=MENGXI + (44 - _k * 8,), width=3)
for _x in (120, 960):               # strata cliffs at the margins
    for _s in range(5):
        _d.rectangle((_x - 70, 1340 + _s * 18, _x + 70, 1356 + _s * 18), fill=((160, 140, 110) if _s % 2 else (120, 110, 96)) + (50,))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (90, 100, 100)}
def draw_background(t, theme):
    """镇江梦溪: hills, a winding stream and layered cliffs at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 192, 190), (152, 168, 166), MTN_COL.get(theme, (100, 128, 126))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """指南针: a small compass dial with a red needle in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=MENGXI + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=MENGXI + (220,), width=3)
        cx, cy = x + sx * 60, y + sy * 60
        d.ellipse((cx - 32, cy - 32, cx + 32, cy + 32), outline=MENGXI + (230,), width=4)
        d.polygon([(cx - 4, cy), (cx + 4, cy), (cx + 3, cy - 26)], fill=CIZHEN + (240,))
        d.polygon([(cx - 4, cy), (cx + 4, cy), (cx - 3, cy + 26)], fill=(60, 60, 66, 240))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def shen(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, armour=False, **kw):
    """沈括: Song scholar-official — 幞头, neat beard, a measuring rod or compass often in hand."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else ('none' if up else 'knot'), layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        if not armour:
            d.chord((x - 0.08 * h, y - 1.06 * h, x + 0.08 * h, y - 0.9 * h), 180, 360, fill=255)
            d.line((x - dir * 0.06 * h, y - 0.97 * h, x - dir * 0.15 * h, y - 0.9 * h), fill=255, width=max(2, int(0.02 * h)))
        d.polygon([(x + dir * 0.03 * h, y - 0.84 * h), (x + dir * 0.08 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.7 * h)], fill=255)
        A.d['mengxi'].rectangle((x - 0.08 * h, y - 0.56 * h, x + 0.08 * h, y - 0.52 * h), fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.03 * h, y - 0.82 * h), (x + dir * 0.08 * h, y - 0.82 * h), (x + dir * 0.05 * h, y - 0.72 * h)], fill=255)
    return hand

def compass(A, cx, cy, r, t, dev=0.12, swing=0.0):
    A.d['wash'].ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    A.d['ink'].ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=max(3, int(0.05 * r)))
    for k in range(24):
        a = k * math.pi / 12
        A.d['ink'].line((cx + 0.82 * r * math.cos(a), cy + 0.82 * r * math.sin(a), cx + 0.94 * r * math.cos(a), cy + 0.94 * r * math.sin(a)), fill=200, width=2)
    A.d['ink'].line((cx, cy - 0.95 * r, cx, cy + 0.95 * r), fill=120, width=2)
    a = -math.pi / 2 + dev + swing * math.sin(t * 6)
    tip = (cx + 0.78 * r * math.cos(a), cy + 0.78 * r * math.sin(a)); tail = (cx - 0.78 * r * math.cos(a), cy - 0.78 * r * math.sin(a))
    nx, ny = -math.sin(a) * 0.07 * r, math.cos(a) * 0.07 * r
    A.d['cizhen'].polygon([(cx + nx, cy + ny), (cx - nx, cy - ny), tip], fill=255)
    A.d['ink'].polygon([(cx + nx, cy + ny), (cx - nx, cy - ny), tail], fill=255)

def strata(A, x0, x1, top, base, layers=7, shells=0):
    hh = (base - top) / layers
    for k in range(layers):
        A.d['mid' if k % 2 else 'dune'].rectangle((x0, top + k * hh, x1, top + (k + 1) * hh), fill=230 if k % 2 else 200)
    for i in range(shells):
        sx = x0 + 40 + (i * 97) % max(1, int(x1 - x0 - 80)); sy = top + hh * (2 + (i % 3)) + hh / 2
        A.d['wash'].pieslice((sx - 14, sy - 12, sx + 14, sy + 12), 180, 360, fill=255)
        for j in range(3):
            A.d['ink'].line((sx, sy, sx - 10 + j * 10, sy - 10), fill=160, width=1)

def type_tray(A, cx, cy, s, n, layer='mengxi'):
    A.d[layer].rectangle((cx - s, cy - 0.6 * s, cx + s, cy + 0.6 * s), fill=200)
    A.d['ink'].rectangle((cx - s, cy - 0.6 * s, cx + s, cy + 0.6 * s), outline=255, width=4)
    cols, rows = 8, 5
    for i in range(min(n, cols * rows)):
        x = cx - s + 0.12 * s + (i % cols) * 0.235 * s; y = cy - 0.5 * s + (i // cols) * 0.22 * s
        A.d['dune'].rectangle((x, y, x + 0.18 * s, y + 0.17 * s), fill=255)

def notebook(A, cx, cy, s, page, t):
    A.d['wash'].rectangle((cx - s, cy - 0.7 * s, cx + s, cy + 0.7 * s), fill=255)
    A.d['ink'].rectangle((cx - s, cy - 0.7 * s, cx + s, cy + 0.7 * s), outline=255, width=5)
    A.d['ink'].line((cx, cy - 0.7 * s, cx, cy + 0.7 * s), fill=200, width=3)
    if page >= 1: compass(A, cx - 0.5 * s, cy - 0.3 * s, 0.22 * s, t, swing=0.03)
    if page >= 2: strata(A, cx + 0.2 * s, cx + 0.8 * s, cy - 0.55 * s, cy - 0.05 * s, layers=5, shells=2)
    if page >= 3:
        for k in range(8):
            a = k * 0.8
            A.d['cizhen'].ellipse((cx - 0.5 * s + 0.2 * s * math.cos(a) - 4, cy + 0.35 * s + 0.15 * s * math.sin(a) - 4, cx - 0.5 * s + 0.2 * s * math.cos(a) + 4, cy + 0.35 * s + 0.15 * s * math.sin(a) + 4), fill=255)
    if page >= 4: type_tray(A, cx + 0.5 * s, cy + 0.35 * s, 0.25 * s, 30)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 4)}
def art_note_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    if kb == 144:
        w = lerp(300, 160, q)
        notebook(A, 540, 1060, w, 4 if q < 0.6 else 0, t)
        if q >= 0.6:
            A.d['mengxi'].rectangle((540 - w, 1060 - 0.7 * w, 540 + w, 1060 + 0.7 * w), fill=255)
    else:
        notebook(A, 540, 1060, 300, b if q > 0.5 else a, t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_note_chapter)
    ink_in(cv, text_img(no, SERIF, 56, MENGXI, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_s_hook_needle(A, cv, t, u):
    compass(A, 540, 1060, 220, t, dev=lerp(0, 0.12, ease_out(u / (1.2 * P))))
    ground(A, GROUND)

def art_s_hook_shell(A, cv, t, u):
    strata(A, 240, 840, 900, GROUND, layers=8, shells=int(clamp(u / (1.2 * P)) * 8))
    ground(A, GROUND)

def art_s_hook_oil(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((480, GROUND - 120, 600, GROUND), fill=255)
    for k in range(6):
        q = (t * 0.4 + k / 6) % 1
        A.d['ink'].ellipse((540 - 30 - 40 * q, GROUND - 140 - 300 * q - 24, 540 + 30 + 40 * q, GROUND - 140 - 300 * q + 24), fill=int(200 * (1 - q)))

def art_s_hook_book(A, cv, t, u):
    notebook(A, 540, 1060, 300, min(4, int(u / (0.4 * P)) + 1), t)

# ================================================================ 第一回 随父宦游
def art_s_birth(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='钱塘', layer='mid', open_=1.0)
    river(A, 1260, t, rows=2, amp=3)
    A.flush(cv)
    paste(cv, text_img('杭州钱塘 · 父沈周为地方官', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('钱塘', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_travel(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    carriage(A, lerp(120, 840, ease_out(u / (3 * P))), GROUND, 90, dir=1, wheel=t * 6, ph=t * 8, layer='mengxi')
    A.flush(cv)
    paste(cv, text_img('随父宦游 · 泉州 开封 江宁 简州', SERIF, 44, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_mother(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='mengxi')
    person(A, 760, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    shen(A, 320, GROUND, 120, dir=1, kneel=True, arm=90)
    A.flush(cv)
    paste(cv, text_img('母许氏亲授经书', SERIF, 48, MENGXI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_s_eyes(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mengxi')
    shen(A, 300, GROUND, 160, dir=1, kneel=True, bow=30, arm=90)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    paste(cv, text_img('苦读伤目 · 随父访医 留心药方', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '后编有良方 苏沈良方即合编本', t, t - u + P)

def art_s_shuzhou(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=3)
    q = ease_out(u / (2.5 * P))
    A.d['mid'].polygon([(60, 1240), (60 + 880 * q, 1220), (60 + 880 * q, 1250), (60, 1270)], fill=230)
    for j in range(4):
        person(A, lerp(-100, 600, ((t * 0.08 + j / 4) % 1)), 1236, 80, dir=1, robe=False, hat='knot', load=True, ph=t * 4 + j, arm=160, layer='ink')
    A.flush(cv)
    paste(cv, text_img('沭阳主簿 · 治沭水 得良田七千顷', SERIF, 44, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('沭阳', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mengxi')
    ground(A, GROUND)
    shen(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('进士及第 · 时年三十三', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('进士', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_zhaowen(A, cv, t, u):
    ground(A, GROUND)
    for i in range(6):
        A.d['mid'].rectangle((140 + i * 140, GROUND - 400, 250 + i * 140, GROUND), fill=170)
        for j in range(5):
            bundle(A, 195 + i * 140, GROUND - 20 - j * 74, 50, layer='mengxi' if (i + j) % 2 else 'mid')
    shen(A, 540, GROUND, 160, dir=1, arm=150)
    A.flush(cv)
    paste(cv, text_img('昭文馆校书 · 博览天文 方志 律历', SERIF, 44, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 司天监
def art_s_sitian(A, cv, t, u):
    for k in range(3):
        A.d['mengxi'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    shen(A, 540, GROUND - 180, 190, dir=1, arm=lerp(-8, 150, ease_out(u / 0.5)))
    A.flush(cv)
    stamp(cv, seal('提举司天监', 40), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('整顿司天监 · 罢黜不学之官', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_tianwen(cv, t, c, k):
    """8-beat custom scene: 观星 — three times a night for five years he plots the pole star through a sighting tube;
    the tube widens until the star stays inside; 极星离天极三度有余. Then the 十二气历: a solar calendar of twelve seasons."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    for i in range(40):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 420
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    if ph < 5:
        cx, cy = 540, 900
        A.d['ink'].ellipse((cx - 160, cy - 160, cx + 160, cy + 160), outline=160, width=3)
        n = int(clamp(ph / 4.5) * 200)
        for i in range(n):
            a = i * 0.31
            A.d['cizhen'].ellipse((cx + 60 * math.cos(a) - 4, cy + 60 * math.sin(a) - 4, cx + 60 * math.cos(a) + 4, cy + 60 * math.sin(a) + 4), fill=255)
        A.d['ink'].ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=255)
        A.d['mid'].line((540, GROUND, 600, 1100), fill=255, width=20)
        shen(A, 470, GROUND, 170, dir=1, arm=130)
        lab = f'每夜三测 · 第{cn_num(max(1, int(clamp(ph / 4.5) * 3 * 365 * 5) // 365 + 1))}年'
    else:
        A.d['wash'].ellipse((300, 760, 780, 1240), fill=200)
        for kk in range(12):
            a = -math.pi / 2 + kk * math.pi / 6
            A.d['ink'].line((540, 1000, 540 + 240 * math.cos(a), 1000 + 240 * math.sin(a)), fill=200, width=3)
            A.d['mengxi' if kk % 2 else 'cizhen'].ellipse((540 + 200 * math.cos(a + 0.26) - 14, 1000 + 200 * math.sin(a + 0.26) - 14, 540 + 200 * math.cos(a + 0.26) + 14, 1000 + 200 * math.sin(a + 0.26) + 14), fill=255)
        lab = '十二气历 · 以节气定月 大尽三十一 小尽三十'
    ground(A, GROUND)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '观天测星', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=68)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 42, ZHU if ph >= 5 else MENGXI, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    if ph < 5:
        paste(cv, text_img('极星离天极三度有余', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 3.5) / 0.4))
    else:
        note_in(cv, '十二气历当时未被采用 沈括自言后世必有用吾说者', t, s0 + 5 * P)

def art_s_hunyi(A, cv, t, u):
    armillary(A, 540, 1000, 180, 4, t, spin=t * 0.3)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('改制浑仪 浮漏 景表', SERIF, 48, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('浑仪议', 50), 860, 1440, t, t - u + P, rot=6)

def art_s_xining(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(40, 110, ease_out(u / 0.5)), layer='ink')
    shen(A, 400, GROUND, 190, dir=1, bow=15, arm=90)
    A.flush(cv)
    paste(cv, text_img('参与王安石变法 · 察访两浙水利', SERIF, 44, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_bian(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=3)
    n = min(8, int(clamp(u / (2.5 * P)) * 8) + 1)
    for i in range(n):
        x = 120 + i * 110
        A.d['mid'].rectangle((x, 1180 - i * 14, x + 90, 1200), fill=230)
    A.flush(cv)
    paste(cv, text_img(f'分层筑堰测汴渠 · 第{cn_num(n)}级', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    note_in(cv, '京师至泗州八百四十里 地势高差十九丈余', t, t - u + P)

def art_s_needle(A, cv, t, u):
    """6-beat set piece: 磁针偏东 — a magnetised needle hung on a silk thread; it points south but always a little east — the first record of declination."""
    ph = u / P
    A.d['ink'].line((540, 760, 540, 1020), fill=200, width=2)
    compass(A, 540, 1120, 200, t, dev=lerp(0, 0.14, clamp((ph - 2) / 1)), swing=0.05 * clamp(1 - ph / 2))
    ground(A, GROUND)
    A.flush(cv)
    lab = '方家以磁石磨针锋 则能指南' if ph < 2 else '然常微偏东 不全南也'
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else MENGXI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('世界最早的磁偏角记录', SERIF, 42, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 3.5) / 0.4))

def art_s_ambassador(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    for j in range(3):
        rider(A, lerp(-100, 600, ease_out(u / (2.5 * P))) - j * 130, GROUND, 120, dir=1, ph=t * 6 + j, layer='mengxi' if j == 0 else 'ink')
    A.flush(cv)
    paste(cv, text_img('出使辽国 · 据档案力争 寸土不让', SERIF, 44, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('使辽', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_mapmodel(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='mid')
    for k in range(5):
        x = 360 + k * 80
        A.d['dune'].polygon([(x - 50, GROUND - 74), (x, GROUND - 74 - 40 - 20 * (k % 2)), (x + 50, GROUND - 74)], fill=255)
    shen(A, 220, GROUND, 170, dir=1, arm=110)
    A.flush(cv)
    paste(cv, text_img('以面糊木屑塑立体地图', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('木图', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第三回 格物
def art_s_fossil(A, cv, t, u):
    """6-beat set piece: 太行化石 — along the Taihang cliffs he sees bands of shells and pebbles: this was once the sea shore."""
    ph = u / P
    strata(A, 140, 940, 840, GROUND, layers=9, shells=int(clamp(ph / 3) * 14))
    if ph > 3.5:
        q = clamp((ph - 3.5) / 1.5)
        A.d['ocean'].rectangle((140, lerp(GROUND, 840, q), 940, GROUND), fill=int(110 * q))
        waves(A, lerp(GROUND, 840, q), t, rows=2, amp=4)
    shen(A, 80, GROUND, 150, dir=1, arm=120)
    ground(A, GROUND)
    A.flush(cv)
    lab = '山崖之间 往往衔螺蚌壳及石子如鸟卵者' if ph < 3.5 else '此乃昔之海滨'
    paste(cv, text_img(lab, SERIF, 42, ZHU if ph >= 3.5 else MENGXI, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    stamp(cv, seal('太行', 56), 860, 1440, t - 0 * u, t - u + 0.4, rot=6)

def art_s_shiyou(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((300, GROUND - 60, 420, GROUND), fill=255)
    for k in range(6):
        q = (t * 0.4 + k / 6) % 1
        A.d['ink'].ellipse((360 - 30 - 40 * q, GROUND - 80 - 260 * q - 24, 360 + 30 + 40 * q, GROUND - 80 - 260 * q + 24), fill=int(200 * (1 - q)))
    shen(A, 700, GROUND, 180, dir=-1, arm=lerp(40, 120, ease_out(u / 0.5)))
    A.flush(cv)
    type_in(cv, text_img('此物后必大行于世', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + P, 0.5)
    stamp(cv, seal('石油', 56), 260, 1020, t, t - u + 0.4, rot=-5)
    note_in(cv, '石油一词首见梦溪笔谈', t, t - u + P)

def art_s_rainbow(A, cv, t, u):
    for k, lay in enumerate(('cizhen', 'qiuhuang', 'grass', 'mengxi')):
        r = 380 - k * 22
        A.d[lay].arc((540 - r, 1200 - r, 540 + r, 1200 + r), 180, 360, fill=200, width=20)
    for k in range(30):
        q = (t * 1.0 + k / 30) % 1
        A.d['wash'].line((80 + (k * 37) % 920, lerp(620, 1300, q), 80 + (k * 37) % 920 - 6, lerp(620, 1300, q) + 24), fill=120, width=2)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('虹乃雨中日影也 · 日照雨则有之', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_s_pinhole(A, cv, t, u):
    A.d['mid'].rectangle((140, 860, 940, GROUND), fill=110)
    A.d['wash'].rectangle((520, 1000, 540, 1020), fill=255)
    A.d['ink'].line((200, 900, 860, 1160), fill=120, width=2)
    A.d['ink'].line((200, 1160, 860, 900), fill=120, width=2)
    crow(A, 220, 900, 40, t * 4)
    crow(A, 840, 1140, 40, t * 4 + 1)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('窗隙成像 · 鸢东则影西 鸢西则影东', SERIF, 44, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '小孔成像 墨子已有记载 沈括详加解释', t, t - u + P)

def art_s_resonance(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='mid')
    A.d['ink'].line((300, GROUND - 90, 780, GROUND - 90), fill=255, width=4)
    q = 0.5 + 0.5 * math.sin(t * 20)
    A.d['ink'].line((300, GROUND - 110, 780, GROUND - 110 + 6 * q), fill=255, width=4)
    A.d['cizhen'].polygon([(600, GROUND - 120), (630, GROUND - 120 - 30 * q), (660, GROUND - 120)], fill=255)
    A.flush(cv)
    paste(cv, text_img('剪纸人置弦上 · 应声而跃', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('共振', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_bisheng(A, cv, t, u):
    """6-beat set piece: 活字印刷 — 毕昇 carves characters in clay, fires them, sets them in an iron frame with wax; prints, then melts the wax and reuses."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='mid')
    person(A, 220, GROUND, 170, dir=1, robe=False, hat='knot', kneel=True, arm=lerp(80, 120, 0.5 + 0.5 * math.sin(t * 6)), layer='ink')
    if ph < 2:
        for i in range(int(clamp(ph / 2) * 12)):
            A.d['dune'].rectangle((360 + (i % 6) * 34, GROUND - 100 - (i // 6) * 30, 384 + (i % 6) * 34, GROUND - 76 - (i // 6) * 30), fill=255)
        lab = '用胶泥刻字 薄如钱唇 每字为一印'
    elif ph < 3.5:
        flames(A, 700, GROUND - 74, 140, 80, t, n=3, seed=68, smoke=True)
        type_tray(A, 480, GROUND - 130, 120, 40)
        lab = '火烧令坚 · 铁范置字 药熔则平'
    else:
        type_tray(A, 480, GROUND - 130, 120, 40)
        A.d['wash'].rectangle((620, GROUND - 160, 820, GROUND - 90), fill=255)
        for k in range(4):
            A.d['ink'].line((640, GROUND - 150 + k * 16, 800, GROUND - 150 + k * 16), fill=200, width=3)
        lab = '若印数十百千本 则极为神速'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 42, ZHU if ph >= 3.5 else MENGXI, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    note_in(cv, '布衣毕升发明活字 赖梦溪笔谈记载传世', t, t - u + P)

# ================================================================ 第四回 永乐城
def art_s_yanzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='延州', layer='mid', open_=1.0)
    ground(A, GROUND)
    shen(A, 540, GROUND, 190, dir=1, armour=True, arm=60)
    A.flush(cv)
    paste(cv, text_img('知延州 · 兼鄜延路经略安抚使', SERIF, 44, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('经略', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_victory(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 300), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    army(A, lerp(-200, 300, ease_out(u / (2 * P))), GROUND, 6, dir=1, layer='mengxi', t=t, march=True, h=110)
    A.flush(cv)
    paste(cv, text_img('抵御西夏 · 收复浮图 吴堡等寨', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_yongle(A, cv, t, u):
    """6-beat set piece: 永乐城之败 — 徐禧 builds the new fort on a waterless ridge against advice; Western Xia besieges it; the fort falls;
    Shen Kuo, held back to guard the rear, is blamed."""
    ph = u / P
    city_wall(A, 380, 700, 1100, label=None, layer='mid')
    A.d['dune'].polygon([(240, GROUND), (540, 1060), (840, GROUND)], fill=200)
    if ph > 1.5:
        for j in range(10):
            a = j * 2 * math.pi / 10
            person(A, 540 + 400 * math.cos(a), GROUND - 20 * (j % 2), 90, dir=-1 if math.cos(a) > 0 else 1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    if ph > 3.5:
        flames(A, 540, 1100, 340, 200 * clamp((ph - 3.5) / 1), t, n=5, seed=1082, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    lab = '徐禧筑永乐城 · 城中无水' if ph < 1.5 else ('西夏三十万围城' if ph < 3.5 else '城陷 · 将士死者数万')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 1.5 else MENGXI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '沈括奉命守绥德 未能救援', t, t - u + 2 * P)

def art_s_demoted(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    shen(A, lerp(400, 120, ease_out((u - P) / P)), GROUND, 180, dir=-1 if u > P else 1, ph=t * 3 if u > P else None, arm=-8, old=0.5)
    A.flush(cv)
    paste(cv, text_img('坐贬均州团练副使 · 随州安置', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_tianxia(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='mengxi')
    A.d['wash'].rectangle((300, GROUND - 200, 780, GROUND - 80), fill=255)
    A.d['ink'].line([(340, GROUND - 120), (440, GROUND - 170), (560, GROUND - 130), (700, GROUND - 160), (740, GROUND - 110)], fill=255, width=4)
    shen(A, 200, GROUND, 170, dir=1, kneel=True, arm=110, old=0.6)
    A.flush(cv)
    paste(cv, text_img('献守令图 · 十二年乃成', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('天下州县图', 40), 860, 1020, t, t - u + P, rot=6)

def art_s_mengxi(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 300), (x + 220, GROUND)], fill=150)
    A.d['ocean'].line([(80, GROUND - 40), (300, GROUND - 70), (540, GROUND - 40), (800, GROUND - 70), (1000, GROUND - 40)], fill=200, width=16)
    A.d['mid'].rectangle((620, GROUND - 200, 880, GROUND - 60), fill=230)
    A.d['ink'].polygon([(600, GROUND - 200), (900, GROUND - 200), (750, GROUND - 270)], fill=255)
    ground(A, GROUND)
    shen(A, lerp(200, 540, ease_out(u / (2.5 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8, old=0.7)
    A.flush(cv)
    paste(cv, text_img('定居润州 · 名其园曰梦溪', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '少年曾梦一园 后至润州见之 恍如梦中', t, t - u + P)

# ================================================================ 第五回 梦溪笔谈
def art_s_write(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mengxi')
    shen(A, 280, GROUND, 180, dir=1, kneel=True, bow=20, arm=90, old=0.8)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    n = min(26, int(clamp(u / (2.5 * P)) * 26) + 1)
    slips(A, 400, GROUND - 74, min(16, n), 80, layer='cizhen')
    A.flush(cv)
    paste(cv, text_img(f'梦溪笔谈 · 第{cn_num(n)}卷', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    note_in(cv, '与宾客言者 惟笔砚而已 故谓之笔谈', t, t - u + P)

def art_s_categories(A, cv, t, u):
    ground(A, GROUND)
    cats = ['象数', '乐律', '异事', '技艺', '器用', '药议']
    A.flush(cv)
    n = min(6, int(u / (0.5 * P)) + 1)
    for i in range(n):
        stamp(cv, seal(cats[i], 50, ZHU if i % 2 else INK), 230 + (i % 3) * 310, 980 + (i // 3) * 170, t, t - u + i * 0.5 * P)
    paste(cv, text_img('六百零九条 · 天文数学地理医药无所不包', SERIF, 42, MENGXI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_s_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    shen(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于梦溪园 · 年六十五', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_needham(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    person(A, 300, GROUND, 200, dir=1, robe=False, hat='none', kneel=True, arm=110, layer='ink')
    notebook(A, 560, GROUND - 160, 100, 4, t)
    A.flush(cv)
    type_in(cv, text_img('中国科学史上的坐标', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('李约瑟', 50, INK), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '李约瑟中国科学技术史之评', t, t - u + P)

def art_s_asteroid(A, cv, t, u):
    for i in range(50):
        x = 100 + (i * 97) % 880; y = 760 + (i * 53) % 560
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=180)
    q = ease_out(u / (2 * P))
    A.d['mengxi'].arc((180, 840, 900, 1300), 200, 200 + 300 * q, fill=255, width=4)
    a = math.radians(200 + 300 * q)
    A.d['cizhen'].ellipse((540 + 360 * math.cos(a) - 14, 1070 + 230 * math.sin(a) - 14, 540 + 360 * math.cos(a) + 14, 1070 + 230 * math.sin(a) + 14), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('小行星2027号 · 命名为沈括星', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_s_today(A, cv, t, u):
    compass(A, 540, 1060, 200, t, dev=0.12)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('一根偏东的磁针 · 指向千年后的科学', SERIF, 44, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_s_garden(A, cv, t, u):
    A.d['ocean'].line([(80, GROUND - 40), (300, GROUND - 70), (540, GROUND - 40), (800, GROUND - 70), (1000, GROUND - 40)], fill=200, width=16)
    A.d['mid'].rectangle((380, GROUND - 200, 700, GROUND - 60), fill=230)
    A.d['ink'].polygon([(360, GROUND - 200), (720, GROUND - 200), (540, GROUND - 270)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('梦溪园旧址仍在镇江', SERIF, 46, MENGXI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_s_legacy(A, cv, t, u):
    compass(A, 860, 1360, 50, t, dev=0.12)

def art_s_title(A, cv, t, u):
    compass(A, 820, 1300, 140, t, dev=0.12, swing=0.02)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    shen(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '随父宦游'), 48: ('第二回', '司天监'), 80: ('第三回', '格物'),
            112: ('第四回', '永乐城'), 144: ('第五回', '梦溪笔谈')}

CARDS = [
    C(0, 2, 'works', 'num', num='一根磁针', line='总是偏东一点', art=art_s_hook_needle),
    C(2, 4, 'life', 'num', num='山上的贝壳', line='这里曾是大海', art=art_s_hook_shell),
    C(4, 6, 'night', 'num', num='石油二字', line='是他起的名字', art=art_s_hook_oil),
    C(6, 8, 'empire', 'num', num='一本笔记', line='中国科学的坐标', art=art_s_hook_book),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 随父宦游
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1031, main='生于钱塘', sub='官宦之家', art=art_s_birth),
    C(22, 26, 'fate', 'card', year=1040, main='随父宦游', sub='走遍南北', art=art_s_travel),
    C(26, 30, 'works', 'card', year=1042, main='母亲授书', sub='许氏', art=art_s_mother),
    C(30, 34, 'night', 'card', year=1048, main='苦读伤目', sub='因病学医', art=art_s_eyes),
    C(34, 40, 'court', 'card', year=1054, main='沭阳治水', sub='初试身手', art=art_s_shuzhou),
    C(40, 44, 'empire', 'card', year=1063, main='进士及第', sub='三十三岁', art=art_s_jinshi),
    C(44, 48, 'works', 'card', year=1066, main='昭文馆', sub='校书', art=art_s_zhaowen),
    # ---- 第二回 司天监
    C(48, 50, 'night', 'chapter'),
    C(50, 54, 'court', 'card', year=1072, main='提举司天监', sub='整顿天文', art=art_s_sitian),
    C(54, 62, 'night', 'tianwen', year=1072),
    C(62, 66, 'works', 'card', year=1072, main='改制浑仪', sub='浮漏景表', art=art_s_hunyi),
    C(66, 70, 'court', 'card', year=1072, main='参与变法', sub='察访两浙', art=art_s_xining),
    C(70, 74, 'works', 'card', year=1072, main='测量汴渠', sub='分层筑堰', art=art_s_bian),
    C(74, 80, 'empire', 'card', year=1074, main='磁偏角', sub='常微偏东', note='笔谈成书于晚年 此为后来追记', art=art_s_needle),
    # ---- 第三回 格物
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'war', 'card', year=1075, main='出使辽国', sub='据理力争', art=art_s_ambassador),
    C(86, 90, 'works', 'card', year=1075, main='立体地图', sub='木图', art=art_s_mapmodel),
    C(90, 96, 'life', 'card', year=1075, main='太行化石', sub='沧海桑田', art=art_s_fossil),
    C(96, 100, 'night', 'card', year=1080, main='石油', sub='首次命名', art=art_s_shiyou),
    C(100, 102, 'fate', 'card', year=1080, main='虹', sub='雨中日影', art=art_s_rainbow),
    C(102, 104, 'works', 'card', year=1080, main='小孔成像', sub='鸢影', art=art_s_pinhole),
    C(104, 106, 'court', 'card', year=1080, main='共振', sub='纸人跳舞', art=art_s_resonance),
    C(106, 112, 'empire', 'card', year=1080, main='活字印刷', sub='毕升的发明', art=art_s_bisheng),
    # ---- 第四回 永乐城
    C(112, 114, 'war', 'chapter'),
    C(114, 118, 'court', 'card', year=1080, main='知延州', sub='镇守西北', art=art_s_yanzhou),
    C(118, 122, 'war', 'card', year=1081, main='收复诸寨', sub='边功', art=art_s_victory),
    C(122, 128, 'death', 'card', year=1082, main='永乐城之败', sub='代人受过', art=art_s_yongle),
    C(128, 132, 'fate', 'card', year=1082, main='贬谪随州', sub='仕途终结', art=art_s_demoted),
    C(132, 138, 'works', 'card', year=1087, main='天下州县图', sub='十二年', art=art_s_tianxia),
    C(138, 144, 'life', 'card', year=1088, main='梦溪园', sub='梦中之地', art=art_s_mengxi),
    # ---- 第五回 梦溪笔谈
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'works', 'card', year=1088, main='梦溪笔谈', sub='与笔砚谈', art=art_s_write),
    C(150, 154, 'empire', 'card', year=1090, main='无所不包', sub='六百零九条', art=art_s_categories),
    C(154, 158, 'death', 'card', year=1095, main='沈括去世', sub='梦溪园', art=art_s_death),
    C(158, 162, 'court', 'card', year=1954, main='科学坐标', sub='李约瑟之评', art=art_s_needham),
    C(162, 166, 'night', 'card', year=1964, main='沈括星', sub='小行星', art=art_s_asteroid),
    C(166, 168, 'fate', 'card', year=1964, main='偏东的磁针', sub='千年回响', art=art_s_today),
    C(168, 170, 'end', 'card', year=1964, main='梦溪', sub='旧址仍在', art=art_s_garden),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='陆拾捌', col=MENGXI, acc=CIZHEN, born=1031, died=1095, age0=1030,
    born_lab='1031年', died_lab='1095年', years_txt='公元1031 — 1095',
    hook_q='他是宋朝的官 · 为什么被称为中国的达芬奇？',
    name_line='沈括 · 字存中', name='沈括', seal='存中', title_art=art_s_title,
    q1='百科全才？', q2='官场失意？',
    end_art=art_s_legacy, end_big='梦溪笔谈', end_seal='存中',
    end_l1='官场上他输得一塌糊涂', end_l2='却在一本笔记里赢了千年',
    end_brush='格物致知', end_ask='梦溪笔谈里你最惊讶哪一条？评论区聊聊', next='朱熹'),
    scenes=dict(chapter=scene_chapter, tianwen=scene_tianwen))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
