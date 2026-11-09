"""千古人物志 · 第捌拾集 · 鉴真 (688–763)
Look: 唐海蓝 + 招提金, 莲瓣 corner borders, the sea between 扬州 and 日本 behind.
Chapter card: 东渡图 — two shores and the sea; each chapter adds the failed crossings as dotted lines ending in a red cross;
the sixth line reaches the far shore, and in the last chapter a temple stands there.
Set pieces: custom 8-beat scene 'haishang' (第五次东渡 · 漂流十四日), 6-beat 东渡之请, 6-beat 失明, 6-beat 第六次东渡,
6-beat 东大寺授戒, 6-beat 坐化.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zhaoyun as Zn         # engine + helpers (previous episode)
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

F.RIPPLE = False
TANGHAI = (38, 78, 110)             # 唐海蓝
ZHAOTI = (184, 118, 50)             # 招提金
S.LAYERS.append(('tanghai', TANGHAI, 0.9, 1.0))
S.LAYERS.append(('zhaoti', ZHAOTI, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='鉴', life='真', court='律', night='暗', war='浪', empire='戒', works='法', fate='渡', death='寂', end='缘')
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
G.THEMES['empire']['sun'] = (ZHAOTI, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (ZHAOTI, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(4):                 # the sea
    _d.line([(40 + i * 30, 1450 + _k * 12 + 6 * math.sin(i * 0.7 + _k * 1.3)) for i in range(35)], fill=TANGHAI + (54 - _k * 10,), width=3)
for _x in (110, 970):               # lotus buds at the margins
    _d.line((_x, 1446, _x, 1350), fill=(90, 120, 80, 70), width=4)
    _d.polygon([(_x - 18, 1356), (_x, 1310), (_x + 18, 1356)], fill=(200, 140, 140, 70))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (80, 80, 100), 'fate': (92, 100, 110)}
def draw_background(t, theme):
    """扬州 and the sea: low hills over open water, lotus at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 194, 198), (154, 166, 178), MTN_COL.get(theme, (94, 114, 134))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.6))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """莲瓣: a lotus petal pair in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=TANGHAI + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=TANGHAI + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        for a in (-0.5, 0.0, 0.5):
            px, py = cx + 24 * math.sin(a), cy - 24 * math.cos(a)
            d.polygon([(cx, cy + 10), (px - 8, py + 6), (px, py - 6), (px + 8, py + 6)], fill=ZHAOTI + (220,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def jz(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, blind=False, staff=False, **kw):
    """鉴真: a shaven-headed monk in a 袈裟; eyes closed (a dark band) once blind; seated in meditation at the end."""
    b = bow + 10 * old
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, kneel=kneel, bow=b, **kw)
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    if not kw.get('fall'):
        top = y - (0.62 if kneel else 1.0) * h
        A.d['zhaoti'].polygon([(x - 0.09 * h, top + 0.22 * h), (x + 0.1 * h, top + 0.5 * h), (x + 0.16 * h, y - 0.1 * h if not kneel else y - 0.05 * h), (x + 0.02 * h, y - 0.1 * h if not kneel else y - 0.05 * h)], fill=255)
        if blind and up:
            A.d['wash'].line((x + dir * 0.0 * h, y - 0.9 * h, x + dir * 0.08 * h, y - 0.9 * h), fill=255, width=max(2, int(0.015 * h)))
    if staff and up:
        sx = x + dir * 0.22 * h
        A.d[layer].line((sx, y, sx + dir * 0.02 * h, y - 1.2 * h), fill=255, width=max(2, int(0.016 * h)))
        A.d['zhaoti'].ellipse((sx + dir * 0.02 * h - 0.05 * h, y - 1.28 * h, sx + dir * 0.02 * h + 0.05 * h, y - 1.18 * h), outline=255, width=max(2, int(0.012 * h)))
    return hand

def seated(A, x, y, h, layer='ink', blind=True):
    """Seated cross-legged in meditation, facing the viewer."""
    A.d[layer].polygon([(x - 0.5 * h, y), (x + 0.5 * h, y), (x + 0.3 * h, y - 0.25 * h), (x - 0.3 * h, y - 0.25 * h)], fill=255)
    A.d['zhaoti'].polygon([(x - 0.3 * h, y - 0.2 * h), (x + 0.3 * h, y - 0.2 * h), (x + 0.22 * h, y - 0.75 * h), (x - 0.22 * h, y - 0.75 * h)], fill=255)
    A.d[layer].polygon([(x - 0.05 * h, y - 0.75 * h), (x + 0.22 * h, y - 0.75 * h), (x + 0.3 * h, y - 0.2 * h), (x + 0.06 * h, y - 0.2 * h)], fill=255)
    A.d[layer].ellipse((x - 0.14 * h, y - 1.05 * h, x + 0.14 * h, y - 0.75 * h), fill=255)
    if blind:
        A.d['wash'].line((x - 0.08 * h, y - 0.92 * h, x - 0.02 * h, y - 0.92 * h), fill=255, width=max(2, int(0.012 * h)))
        A.d['wash'].line((x + 0.02 * h, y - 0.92 * h, x + 0.08 * h, y - 0.92 * h), fill=255, width=max(2, int(0.012 * h)))

def tangship(A, x, y, s, t, tilt=0.0, sail=True):
    bob = 6 * math.sin(t * 2 + x * 0.01)
    c, si = math.cos(tilt), math.sin(tilt)
    def R(px, py):
        return (x + px * c - py * si, y + bob + px * si + py * c)
    A.d['ink'].polygon([R(-s, -0.15 * s), R(s, -0.25 * s), R(0.8 * s, 0.12 * s), R(-0.8 * s, 0.12 * s)], fill=255)
    A.d['zhaoti'].polygon([R(-0.4 * s, -0.15 * s), R(0.3 * s, -0.2 * s), R(0.3 * s, -0.4 * s), R(-0.4 * s, -0.35 * s)], fill=230)
    if sail:
        A.d['ink'].line([R(0, -0.2 * s), R(0, -1.3 * s)], fill=255, width=4)
        A.d['dune'].polygon([R(0.04 * s, -1.25 * s), R(0.6 * s, -1.15 * s), R(0.55 * s, -0.4 * s), R(0.04 * s, -0.35 * s)], fill=230)

def temple(A, cx, base, w, layer='zhaoti'):
    """唐招提寺 金堂: a low, broad Tang hall with a single sweeping roof and a row of columns."""
    A.d['wash'].rectangle((cx - w, base - 0.36 * w, cx + w, base), fill=230)
    for k in range(8):
        x = cx - 0.9 * w + k * 0.257 * w
        A.d['ink'].rectangle((x - 6, base - 0.36 * w, x + 6, base), fill=255)
    A.d['ink'].polygon([(cx - 1.25 * w, base - 0.34 * w), (cx + 1.25 * w, base - 0.34 * w), (cx + 0.7 * w, base - 0.62 * w), (cx - 0.7 * w, base - 0.62 * w)], fill=255)
    A.d[layer].ellipse((cx - 0.05 * w, base - 0.7 * w, cx + 0.05 * w, base - 0.6 * w), fill=255)

def crossing_map(A, cx, cy, s, n_fail, success, t, temple_=False):
    A.d['tanghai'].rectangle((cx - s, cy - 0.6 * s, cx + s, cy + 0.6 * s), fill=110)
    A.d['dune'].polygon([(cx - s, cy - 0.6 * s), (cx - 0.65 * s, cy - 0.6 * s), (cx - 0.55 * s, cy), (cx - 0.7 * s, cy + 0.6 * s), (cx - s, cy + 0.6 * s)], fill=230)
    A.d['dune'].polygon([(cx + s, cy - 0.6 * s), (cx + 0.7 * s, cy - 0.55 * s), (cx + 0.55 * s, cy - 0.1 * s), (cx + 0.75 * s, cy + 0.3 * s), (cx + s, cy + 0.2 * s)], fill=230)
    A.d['ink'].rectangle((cx - s, cy - 0.6 * s, cx + s, cy + 0.6 * s), outline=255, width=4)
    for i in range(n_fail):
        y0 = cy - 0.4 * s + i * 0.16 * s
        L_ = [0.15, 0.3, 0.2, 0.1, 0.55][i % 5] * s
        for k in range(int(L_ / 18)):
            x = cx - 0.55 * s + k * 18
            A.d['wash'].ellipse((x - 3, y0 + 0.3 * k - 3, x + 3, y0 + 0.3 * k + 3), fill=255)
        xe = cx - 0.55 * s + L_
        A.d['red'].line((xe - 9, y0 - 9, xe + 9, y0 + 9), fill=255, width=4)
        A.d['red'].line((xe - 9, y0 + 9, xe + 9, y0 - 9), fill=255, width=4)
    if success > 0:
        y0 = cy + 0.4 * s
        n = int(clamp(success) * 1.1 * s / 18)
        for k in range(n):
            x = cx - 0.55 * s + k * 18
            A.d['zhaoti'].ellipse((x - 4, y0 - 0.3 * s * (k * 18 / (1.1 * s)) - 4, x + 4, y0 - 0.3 * s * (k * 18 / (1.1 * s)) + 4), fill=255)
    if temple_:
        temple(A, cx + 0.8 * s, cy - 0.15 * s, 0.12 * s)

# ================================================================ chapter card
CH = {16: (0, 0, 0.0), 48: (0, 2, 0.0), 80: (2, 5, 0.0), 112: (5, 5, 1.0), 144: (5, 5, 1.0)}
def art_sea_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b, sc = CH.get(kb, (0, 2, 0.0))
    q = ease_out(u / (1.2 * P))
    n = int(lerp(a, b, clamp((q - 0.2) / 0.6) + 0.001))
    crossing_map(A, 540, 1060, 320, n, sc * (q if kb == 112 else 1.0), t, temple_=(kb == 144 and q > 0.5))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_sea_chapter)
    ink_in(cv, text_img(no, SERIF, 56, TANGHAI, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_j_hook_six(A, cv, t, u):
    crossing_map(A, 540, 1060, 320, min(5, int(u / (0.2 * P)) + 1), clamp((u - P) / (0.8 * P)), t)

def art_j_hook_blind(A, cv, t, u):
    ground(A, GROUND)
    jz(A, 540, GROUND, 280, dir=1, blind=True, staff=True, arm=-8, old=0.6)

def art_j_hook_statue(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((360, GROUND - 60, 720, GROUND), fill=200)
    seated(A, 540, GROUND - 60, 320)

def art_j_hook_storm(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1100, W - 60, GROUND + 40), fill=180)
    waves(A, 1110, t, rows=3, amp=20)
    tangship(A, 540, 1140, 160, t, tilt=0.2 * math.sin(t * 2))

# ================================================================ 第一回 扬州
def art_j_birth(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=140)
    river(A, 1250, t, rows=2, amp=3)
    city_wall(A, 160, 920, 1100, gate_x=540, label='扬州', layer='mid', open_=1.0)
    A.flush(cv)
    paste(cv, text_img('扬州江阳县 · 俗姓淳于', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('扬州', 56), 860, 1020, t, t - u + P, rot=6)

def art_j_chujia(A, cv, t, u):
    ground(A, GROUND)
    seated(A, 760, GROUND - 40, 320, layer='zhaoti', blind=False)
    A.d['mid'].rectangle((600, GROUND - 40, 920, GROUND), fill=200)
    person(A, 340, GROUND, 200, dir=1, robe=True, hat='knot', arm=-8, layer='ink')
    person(A, 460, GROUND, 120, dir=1, robe=True, hat='none', arm=lerp(-8, 90, ease_out((u - P) / 0.6)), layer='tanghai')
    A.flush(cv)
    paste(cv, text_img('十四岁随父入大云寺 · 见佛像感动 求出家', SERIF, 44, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_changan(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='zhaoti')
    ground(A, GROUND)
    jz(A, 540, GROUND, 190, dir=1, kneel=True, bow=20, arm=90)
    A.flush(cv)
    paste(cv, text_img('二十一岁 · 于长安实际寺受具足戒', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('长安', 56), 860, 1020, t, t - u + P, rot=6)

def art_j_daming(A, cv, t, u):
    ground(A, GROUND)
    temple(A, 540, GROUND - 40, 280, layer='mid')
    jz(A, 540, GROUND, 150, dir=1, kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)))
    for j in range(6):
        jz(A, 140 + j * 70 if j < 3 else 760 + (j - 3) * 70, GROUND, 100, dir=1 if j < 3 else -1, kneel=True, bow=20)
    A.flush(cv)
    paste(cv, text_img('归扬州 · 于大明寺讲授戒律', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_shoujie(A, cv, t, u):
    ground(A, GROUND)
    n = min(40, int(clamp(u / (3 * P)) * 40) + 1)
    for i in range(n):
        x = 140 + (i % 10) * 90; y = GROUND - (i // 10) * 60
        jz(A, x, y, 60, dir=1, kneel=True, bow=30)
    A.flush(cv)
    paste(cv, text_img('造寺施药 · 前后授戒四万余人', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '号为江淮化主', t, t - u + P)

def art_j_kasaya(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        x = 220 + k * 160
        A.d['zhaoti'].polygon([(x - 60, GROUND - 260), (x + 60, GROUND - 260), (x + 70, GROUND - 40), (x - 70, GROUND - 40)], fill=230)
        for j in range(4):
            A.d['ink'].line((x - 60, GROUND - 220 + j * 50, x + 60, GROUND - 220 + j * 50), fill=120, width=2)
    A.flush(cv)
    type_in(cv, text_img('山川异域 风月同天', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 760, t, t - u + 0.4, 0.6)
    note_in(cv, '日本长屋王造袈裟千领 绣此四句 鉴真闻之 深为所动', t, t - u + P)

def art_j_qing(A, cv, t, u):
    """6-beat set piece: 东渡之请 — the Japanese monks 荣叡 and 普照 bow before him; his disciples fall silent;
    鉴真: this is for the Dharma — why spare one's life? If none of you will go, I will go."""
    ph = u / P
    ground(A, GROUND)
    temple(A, 540, GROUND - 120, 300, layer='mid')
    jz(A, 540, GROUND, 190, dir=-1, arm=lerp(-8, 100, clamp((ph - 3.5) / 0.6)), old=0.4)
    for j in range(2):
        jz(A, 760 + j * 100, GROUND, 150, dir=-1, kneel=True, bow=40)
    for j in range(4):
        jz(A, 120 + j * 80, GROUND, 130, dir=1, kneel=True, bow=10 if ph < 2 else 25)
    A.flush(cv)
    if ph < 2:
        lab, col = '日本僧荣叡 普照来扬州相请', TANGHAI
    elif ph < 3.5:
        lab, col = '众弟子默然无应', TANGHAI
    else:
        lab, col = '是为法事也 何惜身命 诸人不去 我即去耳', ZHU
    paste(cv, text_img(lab, SERIF, 42 if ph >= 3.5 else 46, col, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    note_in(cv, '时年五十五 见唐大和上东征传', t, t - u + 2 * P)

# ================================================================ 第二回 东渡
def art_j_try1(A, cv, t, u):
    ground(A, GROUND)
    tangship(A, 700, GROUND - 40, 140, t)
    for j in range(3):
        person(A, 200 + j * 90, GROUND, 160, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    A.flush(cv)
    paste(cv, text_img('弟子争执 有人诬告勾结海盗 · 船被没收', SERIF, 44, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('其一', 56, ZHU), 860, 1020, t, t - u + P, rot=6)

def art_j_try2(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=180)
    waves(A, 1170, t, rows=3, amp=12)
    A.d['mid'].polygon([(700, GROUND), (780, 1100), (880, GROUND)], fill=230)
    tangship(A, lerp(300, 640, ease_out(u / (2 * P))), 1180, 120, t, tilt=lerp(0, 0.4, clamp((u - 2 * P) / P)))
    A.flush(cv)
    paste(cv, text_img('出海遇风 船破于狼沟浦', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('其二', 56, ZHU), 860, 1020, t, t - u + P, rot=6)

def art_j_try3(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label=None, layer='mid', open_=0.0)
    ground(A, GROUND)
    jz(A, 540, GROUND, 180, dir=1, arm=-8, old=0.5)
    A.flush(cv)
    paste(cv, text_img('再度筹备 · 又被官府截留', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('其三', 56, ZHU), 860, 1020, t, t - u + P, rot=6)

def art_j_try4(A, cv, t, u):
    ground(A, GROUND)
    jz(A, 300, GROUND, 190, dir=1, staff=True, ph=t * 3, arm=-8, old=0.5)
    jz(A, 760, GROUND, 160, dir=-1, kneel=True, bow=40)
    A.flush(cv)
    paste(cv, text_img('弟子不忍其远行 告官阻拦', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('其四', 56, ZHU), 860, 1020, t, t - u + P, rot=6)

def art_j_try5(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=4)
    tangship(A, lerp(200, 640, ease_out(u / (3 * P))), 1220, 130, t)
    A.flush(cv)
    paste(cv, text_img('六十一岁 · 第五次出海', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_haishang(cv, t, c, k):
    """8-beat custom scene: 第五次东渡 — a storm drives the ship south; for days they drift; the water runs out and they chew raw rice,
    drinking sea water; after fourteen days they make land — at 振州 on 海南."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    storm = clamp(ph / 1.5) * clamp((6.5 - ph) / 1)
    A.d['ocean'].rectangle((0, 1080, W, GROUND + 40), fill=int(150 + 60 * storm))
    waves(A, 1090, t, rows=3, amp=4 + 24 * storm)
    for i in range(40):
        q = (t * 2.5 + i / 40) % 1
        x = 80 + (i * 53) % 920
        A.d['wash'].line((x + 60 * q, lerp(620, 1300, q), x + 60 * q - 20, lerp(620, 1300, q) + 30), fill=int(160 * storm), width=2)
    if ph >= 6.5:
        A.d['grass'].polygon([(700, 1100), (800, 1020), (960, 1040), (1080, 1100)], fill=230)
    tangship(A, lerp(300, 620, ph / 8), 1120, 140, t, tilt=0.3 * storm * math.sin(t * 2.5))
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '漂流十四日', BRUSH, 140, INK, W / 2, 440, t, s0, stagger=0.06, seed=80)
    fx.flush(cv)
    day = min(14, int(ph / 6.5 * 14) + 1)
    if ph < 6.5:
        lab = f'狂风巨浪 · 漂流第{cn_num(day)}日'
        col = ZHU if storm > 0.5 else TANGHAI
    else:
        lab, col = '漂至海南振州', TANGHAI
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    if 3 <= ph < 6.5:
        note_in(cv, '淡水已尽 嚼生米 饮海水 见东征传', t, s0 + 3 * P)

def art_j_hainan(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=140)
    waves(A, 1250, t, rows=2, amp=3)
    for x in (220, 860):
        A.d['huyang'].line([(x, 1240), (x + 10, 1100), (x + 24, 980)], fill=255, width=10)
        for a in (-2.6, -2.0, -1.2, -0.6):
            A.d['grass'].line((x + 24, 980, x + 24 + 110 * math.cos(a), 980 + 60 * math.sin(a) + 50), fill=255, width=8)
    jz(A, 540, 1240, 180, dir=1, staff=True, arm=-8, old=0.5)
    A.flush(cv)
    paste(cv, text_img('漂至海南振州 · 造寺讲律', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 漂流
def art_j_wanan(A, cv, t, u):
    ground(A, GROUND)
    temple(A, 540, GROUND, 240, layer='mid')
    A.flush(cv)
    paste(cv, text_img('在振州 万安州停留年余', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_north(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x - 30, GROUND - 320), (x + 30, GROUND - 320), (x + 150, GROUND)], fill=160)
    ground(A, GROUND)
    for j in range(4):
        jz(A, lerp(-100, 700, ((t * 0.05 + j / 4) % 1)), GROUND, 140 if j else 160, dir=1, staff=j == 0, ph=t * 3 + j, arm=-8, old=0.5 if j == 0 else 0)
    A.flush(cv)
    paste(cv, text_img('取道广西 广东 · 跋涉北归', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_rongrui(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    jz(A, 540, 1200, 200, dir=1, fall=-88, arm=-8)
    jz(A, 880, GROUND, 150, dir=-1, kneel=True, bow=30, old=0.5)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('荣叡病逝于端州 · 鉴真哀恸', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_blind(A, cv, t, u):
    """6-beat set piece: 失明 — the heat and the long road inflame his eyes; a foreign healer treats them; his sight goes dark for good."""
    ph = u / P
    ground(A, GROUND)
    jz(A, 540, GROUND, 230, dir=1, arm=-8, old=0.6, blind=ph >= 3.5)
    dark = clamp((ph - 1) / 2.5)
    A.flush(cv)
    if dark > 0:
        ov = Image.new('RGBA', (W, H), (16, 16, 20, int(150 * dark)))
        mask = Image.new('L', (W, H), 255)
        md = ImageDraw.Draw(mask)
        r = lerp(700, 160, dark)
        md.ellipse((540 - r, 1100 - r, 540 + r, 1100 + r), fill=0)
        ov.putalpha(Image.fromarray(np.minimum(np.array(ov.split()[3]), np.array(mask))))
        cv.alpha_composite(ov)
    if ph < 1.5:
        lab, col = '炎热跋涉 · 目疾渐重', TANGHAI
    elif ph < 3.5:
        lab, col = '有胡人言能治目 · 加以疗治', TANGHAI
    else:
        lab, col = '眼遂失明', ZHU
    paste(cv, text_img(lab, SERIF, 48, col if dark < 0.3 else (236, 226, 206), 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('东渡之志 仍然不改', SERIF, 40, (220, 210, 190), 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.5) / 0.4))
    note_in(cv, '时年六十三 见东征传', t, t - u + 3 * P)

def art_j_puzhao(A, cv, t, u):
    ground(A, GROUND)
    jz(A, 440, GROUND, 190, dir=1, arm=90, blind=True, old=0.7)
    jz(A, 600, GROUND, 180, dir=-1, arm=90)
    A.flush(cv)
    paste(cv, text_img('普照辞别 · 鉴真执手悲泣', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_xiangyan(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=140)
    river(A, 1210, t, rows=2, amp=3)
    boat(A, 540, 1220, 120, t, sail=False)
    A.flush(cv)
    paste(cv, text_img('弟子祥彦坐化于吉州舟中', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_home(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=140)
    river(A, 1250, t, rows=2, amp=3)
    city_wall(A, 160, 920, 1100, gate_x=540, label='扬州', layer='mid', open_=1.0)
    jz(A, 540, 1240, 140, dir=1, staff=True, arm=-8, blind=True, old=0.7)
    A.flush(cv)
    paste(cv, text_img('辗转回到扬州 · 东渡之志不改', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 抵日
def art_j_envoy(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    temple(A, 540, GROUND - 100, 280, layer='mid')
    for j in range(3):
        person(A, 720 + j * 90, GROUND, 170, dir=-1, robe=True, hat='crown', bow=30, arm=90, layer='tanghai')
    jz(A, 420, GROUND, 180, dir=1, arm=-8, blind=True, old=0.8)
    A.flush(cv)
    paste(cv, text_img('日本遣唐使来请 · 唐廷不许 乃秘密登船', SERIF, 44, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_try6(A, cv, t, u):
    """6-beat set piece: 第六次东渡 — four ships sail together; the envoy 藤原清河's ship is blown to 安南;
    鉴真's ship reaches 萨摩 秋妻屋浦. He is sixty-six."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1100, W - 60, GROUND + 40), fill=160)
    waves(A, 1110, t, rows=3, amp=6)
    if ph >= 4:
        A.d['grass'].polygon([(680, 1110), (800, 1020), (960, 1040), (1080, 1110)], fill=230)
    for k in range(4):
        y = 1130 + (k % 2) * 60
        x = lerp(-100, 520, clamp(ph / 4)) - k * 140
        if k == 0 and ph > 2.5:
            y += lerp(0, 160, clamp((ph - 2.5) / 1))
        tangship(A, x, y, 70, t)
    A.flush(cv)
    lab = '四船同发' if ph < 2.5 else ('大使藤原清河之船漂至安南' if ph < 4 else '鉴真所乘之船 抵达萨摩秋妻屋浦')
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 4 else TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('其六', 56, ZHU), 860, 1020, t, t - u + 4 * P, rot=6)
    note_in(cv, '时年六十六 前后历时十二年', t, t - u + 4 * P)

def art_j_nara(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 240), (x + 220, GROUND)], fill=150)
    ground(A, GROUND)
    for j in range(6):
        jz(A, lerp(-100, 600, ease_out(u / (3 * P))) - j * 90, GROUND, 140 if j else 160, dir=1, ph=t * 3 + j, arm=-8, blind=j == 0, old=0.8 if j == 0 else 0)
    A.flush(cv)
    paste(cv, text_img('入奈良 · 安置东大寺', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('奈良', 56), 860, 1020, t, t - u + P, rot=6)

def art_j_jietan(A, cv, t, u):
    """6-beat set piece: 东大寺授戒 — before the great Buddha a precept platform is built; the retired emperor 圣武, the empress dowager and
    the reigning empress mount it and take the precepts from him."""
    ph = u / P
    seated(A, 540, 1060, 360, layer='zhaoti', blind=False)
    for k in range(3):
        A.d['mid'].rectangle((300 + k * 40, GROUND - (k + 1) * 50, 780 - k * 40, GROUND - k * 50), fill=230 - k * 20)
    ground(A, GROUND)
    jz(A, 540, GROUND - 150, 130, dir=1, kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)), blind=True)
    n = min(3, int(clamp((ph - 1.5) / 2.5) * 3) + (1 if ph >= 1.5 else 0))
    for j in range(n):
        person(A, 300 + j * 230, GROUND, 130, dir=1, robe=True, hat='crown', kneel=True, bow=30, layer='tanghai')
    A.flush(cv)
    lab = '卢舍那佛殿前 · 设立戒坛' if ph < 1.5 else '上皇 皇太后 天皇 · 登坛受戒'
    paste(cv, text_img(lab, SERIF, 44, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 700, 1, 1)
    note_in(cv, '日本始有正规授戒制度', t, t - u + 3 * P)

def art_j_chuandeng(A, cv, t, u):
    ground(A, GROUND)
    temple(A, 540, GROUND, 260, layer='mid')
    A.flush(cv)
    paste(cv, text_img('建东大寺戒坛院 · 授传灯大法师', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_yao(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    for k in range(5):
        A.d['zhaoti'].ellipse((400 + k * 60, GROUND - 100, 440 + k * 60, GROUND - 74), fill=255)
    jz(A, 260, GROUND, 170, dir=1, kneel=True, bow=20, arm=100, blind=True, old=0.8)
    A.flush(cv)
    paste(cv, text_img('以鼻嗅之 辨别药物 一无错失', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '随行带去药物 书法真迹与蔗糖等', t, t - u + P)

# ================================================================ 第五回 招提
def art_j_zhaoti(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 200), (x + 220, GROUND)], fill=150)
    ground(A, GROUND)
    temple(A, 540, GROUND, 300 * (0.5 + 0.5 * ease_out(u / (2 * P))))
    A.flush(cv)
    paste(cv, text_img('于奈良建成唐招提寺', SERIF, 48, TANGHAI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('招提', 56), 860, 1440, t, t - u + P, rot=6)

def art_j_death(A, cv, t, u):
    """6-beat set piece: 坐化 — he dies seated cross-legged, facing west; his disciple 忍基 makes a lacquer statue of him."""
    ph = u / P
    ground(A, GROUND)
    temple(A, 540, GROUND - 260, 200, layer='mid')
    seated(A, 540, GROUND, 300, layer='ink' if ph < 3 else 'zhaoti')
    lamp(A, 300, GROUND, 50, t, glow=clamp(1 - (ph - 2) / 1))
    A.flush(cv)
    lab = '结跏趺坐 面西而化 · 年七十六' if ph < 3 else '弟子忍基为师造像'
    paste(cv, text_img(lab, SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

def art_j_statue(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((360, GROUND - 60, 720, GROUND), fill=200)
    seated(A, 540, GROUND - 60, 360, layer='zhaoti')
    A.flush(cv)
    paste(cv, text_img('干漆夹纻鉴真坐像 · 日本国宝', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_j_basho(A, cv, t, u):
    ground(A, GROUND)
    seated(A, 720, GROUND - 40, 240, layer='zhaoti')
    person(A, 360, GROUND, 180, dir=1, robe=True, hat='knot', bow=30, arm=90, layer='ink')
    for k in range(6):
        A.d['grass'].ellipse((300 + k * 30, GROUND - 260 + 10 * (k % 2), 330 + k * 30, GROUND - 240 + 10 * (k % 2)), fill=255)
    A.flush(cv)
    paste(cv, text_img('松尾芭蕉拜像 · 愿以嫩叶拭尊师之泪', SERIF, 44, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_j_return(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=140)
    river(A, 1250, t, rows=2, amp=3)
    city_wall(A, 160, 920, 1100, gate_x=540, label='扬州', layer='mid', open_=1.0)
    A.flush(cv)
    paste(cv, text_img('鉴真像回扬州 探亲巡展', SERIF, 46, TANGHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '扬州大明寺建有鉴真纪念堂', t, t - u + P)

def art_j_end(A, cv, t, u):
    crossing_map(A, 540, 1100, 300, 5, 1.0, t, temple_=True)
    A.flush(cv)
    paste(cv, text_img('山川异域 风月同天', SERIF, 50, TANGHAI, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))

def art_j_legacy(A, cv, t, u):
    seated(A, 860, 1440, 120, layer='zhaoti')

def art_j_title(A, cv, t, u):
    tangship(A, 820, 1430, 120, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    jz(A, 380, 1460, 640, dir=1, staff=True, arm=lerp(-5, 40, ease_out(u / (2 * P))), blind=True)

# ================================================================ script
CHAPTERS = {16: ('第一回', '扬州'), 48: ('第二回', '东渡'), 80: ('第三回', '漂流'),
            112: ('第四回', '抵日'), 144: ('第五回', '招提')}

CARDS = [
    C(0, 2, 'fate', 'num', num='六次东渡', line='前后十二年', art=art_j_hook_six),
    C(2, 4, 'night', 'num', num='双目失明', line='仍要去日本', art=art_j_hook_blind),
    C(4, 6, 'works', 'num', num='一尊坐像', line='成了日本国宝', art=art_j_hook_statue),
    C(6, 8, 'war', 'num', num='五次失败', line='第六次才成功', art=art_j_hook_storm),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 扬州
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=688, main='生于扬州', sub='俗姓淳于', art=art_j_birth),
    C(22, 26, 'works', 'card', year=701, main='出家', sub='十四岁', art=art_j_chujia),
    C(26, 30, 'empire', 'card', year=708, main='长安受戒', sub='实际寺', art=art_j_changan),
    C(30, 34, 'court', 'card', year=713, main='归扬州', sub='大明寺', art=art_j_daming),
    C(34, 38, 'works', 'card', year=725, main='授戒四万', sub='江淮化主', note='年份约略', art=art_j_shoujie),
    C(38, 42, 'night', 'card', year=730, main='风月同天', sub='长屋王袈裟', note='年份约略', art=art_j_kasaya),
    C(42, 48, 'fate', 'card', year=742, main='东渡之请', sub='我即去耳', art=art_j_qing),
    # ---- 第二回 东渡
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'fate', 'card', year=743, main='第一次', sub='遭人诬告', art=art_j_try1),
    C(54, 58, 'war', 'card', year=743, main='第二次', sub='触礁船破', art=art_j_try2),
    C(58, 62, 'night', 'card', year=744, main='第三次', sub='官府截留', art=art_j_try3),
    C(62, 66, 'death', 'card', year=744, main='第四次', sub='弟子告官', art=art_j_try4),
    C(66, 70, 'empire', 'card', year=748, main='第五次', sub='六十一岁', art=art_j_try5),
    C(70, 78, 'war', 'haishang', year=748),
    C(78, 80, 'life', 'card', year=748, main='海南', sub='振州', art=art_j_hainan),
    # ---- 第三回 漂流
    C(80, 82, 'fate', 'chapter'),
    C(82, 86, 'works', 'card', year=749, main='万安州', sub='造寺讲律', art=art_j_wanan),
    C(86, 90, 'life', 'card', year=749, main='北归', sub='跋涉万里', art=art_j_north),
    C(90, 94, 'death', 'card', year=750, main='痛失弟子', sub='端州', note='年份约略', art=art_j_rongrui),
    C(94, 100, 'night', 'card', year=750, main='双目失明', sub='韶州', art=art_j_blind),
    C(100, 104, 'fate', 'card', year=750, main='普照辞别', sub='执手悲泣', art=art_j_puzhao),
    C(104, 108, 'death', 'card', year=751, main='祥彦坐化', sub='吉州', art=art_j_xiangyan),
    C(108, 112, 'court', 'card', year=752, main='回到扬州', sub='其志不改', art=art_j_home),
    # ---- 第四回 抵日
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'night', 'card', year=753, main='遣唐使', sub='秘密登船', art=art_j_envoy),
    C(118, 124, 'war', 'card', year=753, main='第六次', sub='抵达萨摩', art=art_j_try6),
    C(124, 128, 'court', 'card', year=754, main='入奈良', sub='东大寺', art=art_j_nara),
    C(128, 134, 'empire', 'card', year=754, main='登坛授戒', sub='天皇受戒', art=art_j_jietan),
    C(134, 138, 'works', 'card', year=755, main='戒坛院', sub='传灯大法师', art=art_j_chuandeng),
    C(138, 144, 'life', 'card', year=756, main='鼻嗅辨药', sub='医药', note='年份约略', art=art_j_yao),
    # ---- 第五回 招提
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'empire', 'card', year=759, main='唐招提寺', sub='奈良', art=art_j_zhaoti),
    C(150, 156, 'death', 'card', year=763, main='鉴真圆寂', sub='面西而化', art=art_j_death),
    C(156, 160, 'works', 'card', year=763, main='鉴真坐像', sub='日本国宝', art=art_j_statue),
    C(160, 164, 'night', 'card', year=1688, main='芭蕉俳句', sub='嫩叶拭泪', art=art_j_basho),
    C(164, 168, 'court', 'card', year=1980, main='回乡探亲', sub='扬州', art=art_j_return),
    C(168, 170, 'end', 'card', year=1980, main='风月同天', sub='千年之缘', art=art_j_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='捌拾', col=TANGHAI, acc=ZHAOTI, born=688, died=763, age0=687,
    born_lab='688年', died_lab='763年', years_txt='公元688 — 763',
    hook_q='五次东渡失败 双目失明 · 为什么非去日本不可？',
    name_line='鉴真 · 俗姓淳于', name='鉴真', seal='鉴真', title_art=art_j_title,
    q1='弘法圣僧？', q2='执念太深？',
    end_art=art_j_legacy, end_big='何惜身命', end_seal='鉴真',
    end_l1='他用十二年渡过一片海', end_l2='两国记了他一千多年',
    end_brush='风月同天', end_ask='山川异域 风月同天 你还知道哪句？评论区聊聊', next='杨贵妃'),
    scenes=dict(chapter=scene_chapter, haishang=scene_haishang))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
