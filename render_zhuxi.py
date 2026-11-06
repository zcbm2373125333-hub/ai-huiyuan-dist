"""千古人物志 · 第陆拾玖集 · 朱熹 (1130–1200)
Look: 方塘青 + 丹砂, 方塘 corner borders (a small square pond with a ripple), 武夷 peaks and 九曲 stream behind.
Chapter card: 四书 — one more book stands up each chapter (大学 中庸 论语 孟子); in the last chapter they are bound as 集注.
Set pieces: custom 8-beat scene 'fangtang' (观书有感 · 半亩方塘), 6-beat 鹅湖之会, 6-beat 白鹿洞书院,
6-beat 四书章句集注, 6-beat 庆元党禁.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_shenkuo as Sk         # engine + helpers (previous episode)
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
FANGTANG = (58, 108, 132)           # 方塘青
DANSHA = (178, 72, 48)              # 丹砂
S.LAYERS.append(('fangtang', FANGTANG, 0.9, 1.0))
S.LAYERS.append(('dansha', DANSHA, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='朱', life='熹', court='宋', night='理', war='辩', empire='书', works='学', fate='禁', death='晦', end='源')
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
G.THEMES['empire']['sun'] = (FANGTANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (DANSHA, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # 九曲溪 winding at the foot of the hills
    _d.line([(40 + i * 32, 1460 + _k * 14 + 22 * math.sin(i * 0.32 + _k * 0.4)) for i in range(33)], fill=FANGTANG + (46 - _k * 10,), width=4)
_d.rectangle((150, 1446, 250, 1454), fill=(90, 70, 50, 70))   # a bamboo raft
for _x in (110, 970):               # 武夷 rock pillars at the margins
    _d.polygon([(_x - 50, 1430), (_x - 36, 1250), (_x, 1210), (_x + 36, 1250), (_x + 50, 1430)], fill=(120, 96, 80, 46))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (92, 98, 104)}
def draw_background(t, theme):
    """武夷: steep peaks, the 九曲 stream and a bamboo raft."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 190, 192), (150, 162, 170), MTN_COL.get(theme, (96, 120, 132))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """方塘: a small square pond with a ripple in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=FANGTANG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=FANGTANG + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.rectangle((cx - 30, cy - 30, cx + 30, cy + 30), outline=FANGTANG + (230,), width=4)
        d.line([(cx - 20 + i * 5, cy + 4 * math.sin(i * 1.2)) for i in range(9)], fill=DANSHA + (220,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def zhu(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """朱熹: Southern Song scholar — 幅巾 soft cap, long beard (white when old), a book in hand."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.085 * h, y - 1.08 * h, x + 0.085 * h, y - 0.9 * h), 180, 360, fill=255)
        d.polygon([(x - dir * 0.05 * h, y - 1.0 * h), (x - dir * 0.16 * h, y - 0.86 * h), (x - dir * 0.1 * h, y - 0.84 * h)], fill=255)
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.02 * h, y - 0.84 * h), (x + dir * 0.09 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.64 * h)], fill=255)
        A.d['fangtang'].rectangle((x - 0.08 * h, y - 0.56 * h, x + 0.08 * h, y - 0.52 * h), fill=255)
    return hand

def book(A, cx, base, w, h, layer='fangtang', open_=0.0):
    """A thread-bound book standing on `base`; open_ > 0 draws it lying open instead."""
    if open_ > 0:
        A.d['wash'].polygon([(cx - w, base), (cx, base - 0.18 * w), (cx + w, base), (cx, base + 0.12 * w)], fill=255)
        for k in range(4):
            A.d['ink'].line((cx - 0.8 * w + k * 0.12 * w, base - 0.02 * w + k * 0.01 * w, cx - 0.2 * w + k * 0.06 * w, base - 0.12 * w + k * 0.01 * w), fill=150, width=2)
        return
    A.d[layer].rectangle((cx - w / 2, base - h, cx + w / 2, base), fill=230)
    A.d['ink'].rectangle((cx - w / 2, base - h, cx + w / 2, base), outline=255, width=3)
    A.d['wash'].rectangle((cx - 0.22 * w, base - 0.92 * h, cx + 0.22 * w, base - 0.42 * h), fill=255)
    for k in range(4):
        yy = base - h + (k + 0.5) * h / 4
        A.d['ink'].line((cx - w / 2, yy, cx - w / 2 + 10, yy), fill=255, width=3)

def pond(A, cx, cy, s, t, clear=1.0, clouds=1.0, inflow=0.0):
    """半亩方塘: a stone-edged square pond reflecting sky and drifting clouds; inflow draws the living source stream."""
    A.d['fangtang'].rectangle((cx - s, cy - 0.55 * s, cx + s, cy + 0.55 * s), fill=int(90 + 140 * clear))
    A.d['ink'].rectangle((cx - s - 14, cy - 0.55 * s - 14, cx + s + 14, cy + 0.55 * s + 14), outline=230, width=14)
    A.d['wash'].rectangle((cx - s, cy - 0.55 * s, cx + s, cy + 0.55 * s), fill=int(200 * (1 - clear)))
    for k in range(3):
        if clouds <= 0: break
        x = cx - s + ((t * 18 + k * 0.7 * s) % (2 * s))
        y = cy - 0.3 * s + k * 0.2 * s
        r = 0.18 * s
        A.d['wash'].ellipse((max(cx - s, x - r), y - 0.4 * r, min(cx + s, x + r), y + 0.4 * r), fill=int(230 * clouds))
    A.d['qiuhuang'].ellipse((cx + 0.45 * s - 0.1 * s, cy - 0.38 * s - 0.1 * s, cx + 0.45 * s + 0.1 * s, cy - 0.38 * s + 0.1 * s), fill=int(200 * clouds))
    if inflow > 0:
        x1 = cx - s
        pts = [(x1 - 340 * (1 - k / 10), cy - 0.2 * s - 120 * (1 - k / 10) + 10 * math.sin(k + t * 3)) for k in range(11)]
        n = max(2, int(11 * clamp(inflow)))
        A.d['fangtang'].line(pts[:n], fill=230, width=22)
        for k in range(n - 1):
            q = (t * 1.5 + k / 10) % 1
            px = lerp(pts[k][0], pts[k + 1][0], q); py = lerp(pts[k][1], pts[k + 1][1], q)
            A.d['wash'].ellipse((px - 4, py - 3, px + 4, py + 3), fill=255)

def academy(A, cx, base, w, layer='mid', plaque=True):
    """书院 gate: white walls, two pillars, a sweeping tiled roof and a red plaque."""
    A.d['wash'].rectangle((cx - w, base - 0.42 * w, cx + w, base), fill=230)
    A.d[layer].rectangle((cx - 0.34 * w, base - 0.62 * w, cx + 0.34 * w, base), fill=230)
    A.d['ink'].rectangle((cx - 0.3 * w, base - 0.62 * w, cx - 0.24 * w, base), fill=255)
    A.d['ink'].rectangle((cx + 0.24 * w, base - 0.62 * w, cx + 0.3 * w, base), fill=255)
    A.d['ink'].rectangle((cx - 0.16 * w, base - 0.42 * w, cx + 0.16 * w, base), fill=200)
    A.d['ink'].polygon([(cx - 0.5 * w, base - 0.6 * w), (cx + 0.5 * w, base - 0.6 * w), (cx + 0.36 * w, base - 0.74 * w), (cx - 0.36 * w, base - 0.74 * w)], fill=255)
    A.d['ink'].polygon([(cx - 0.56 * w, base - 0.58 * w), (cx - 0.5 * w, base - 0.6 * w), (cx - 0.48 * w, base - 0.66 * w)], fill=255)
    A.d['ink'].polygon([(cx + 0.56 * w, base - 0.58 * w), (cx + 0.5 * w, base - 0.6 * w), (cx + 0.48 * w, base - 0.66 * w)], fill=255)
    A.d['ink'].rectangle((cx - w, base - 0.46 * w, cx + w, base - 0.42 * w), fill=255)
    if plaque:
        A.d['dansha'].rectangle((cx - 0.18 * w, base - 0.56 * w, cx + 0.18 * w, base - 0.46 * w), fill=255)

BOOKS = ['大学', '中庸', '论语', '孟子']
def four_books(A, cv, t, n, cx=540, base=1200, h=300, bound=0.0, alpha=1.0):
    for i in range(n):
        book(A, cx + (i - 1.5) * 150, base, 120, h, layer='fangtang' if i % 2 else 'dansha')
    if bound > 0:
        A.d['qiuhuang'].rectangle((cx - 290, base - 0.5 * h - 14, cx - 290 + 580 * bound, base - 0.5 * h + 14), fill=255)
    A.flush(cv)
    for i in range(n):
        paste(cv, text_img('\n'.join(BOOKS[i]), SERIF, 40, INK, 'Black', bleed=False, spacing=4), cx + (i - 1.5) * 150, base - 0.67 * h, 1, alpha)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 4)}
def art_book_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    if kb == 144:
        four_books(A, cv, t, 4, base=1180, h=280, bound=q)
        if q > 0.7:
            paste(cv, text_img('四书章句集注', SERIF, 44, DANSHA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((q - 0.7) / 0.3))
    else:
        four_books(A, cv, t, b if q > 0.5 else a, base=1180, h=280)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_book_chapter)
    ink_in(cv, text_img(no, SERIF, 56, FANGTANG, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_z_hook_pond(A, cv, t, u):
    pond(A, 540, 1060, 300, t, clear=ease_out(u / (1.2 * P)))
    ground(A, GROUND)

def art_z_hook_books(A, cv, t, u):
    ground(A, GROUND)
    four_books(A, cv, t, min(4, int(u / (0.3 * P)) + 1), base=1250)

def art_z_hook_debate(A, cv, t, u):
    ground(A, GROUND)
    zhu(A, 300, GROUND, 230, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)))
    person(A, 780, GROUND, 230, dir=-1, robe=True, hat='knot', arm=lerp(120, 40, 0.5 + 0.5 * math.sin(t * 3)), layer='fangtang')

def art_z_hook_ban(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1060, 520, 300, ease_out(u / (1.0 * P)), layer='wash')
    A.flush(cv)
    stamp(cv, seal('伪学', 90, ZHU), 540, 1060, t, t - u + 0.5)

# ================================================================ 第一回 天之上
def art_z_birth(A, cv, t, u):
    for k in range(4):
        x = 180 + k * 240
        A.d['mid'].polygon([(x - 140, GROUND), (x - 30, GROUND - 380 - 60 * (k % 2)), (x + 30, GROUND - 380 - 60 * (k % 2)), (x + 140, GROUND)], fill=160)
    A.d['wash'].rectangle((420, GROUND - 160, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 160), (680, GROUND - 160), (540, GROUND - 230)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('南剑州尤溪 · 父朱松寓居于此', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('尤溪', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '祖籍徽州婺源', t, t - u + P)

def art_z_sky(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 360
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    person(A, 380, GROUND, 230, dir=1, robe=True, hat='knot', arm=lerp(-8, 150, ease_out(u / 0.6)), layer='ink')
    person(A, 560, GROUND, 110, dir=-1, robe=True, hat='none', arm=lerp(-8, 160, ease_out((u - P) / 0.6)), layer='fangtang')
    A.flush(cv)
    lab = '父指天曰 天也' if u < 2 * P else '问曰 天之上何物'
    paste(cv, text_img(lab, SERIF, 48, ZHU if u >= 2 * P else FANGTANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    note_in(cv, '事见朱子年谱 或有后人附会', t, t - u + P)

def art_z_xiaojing(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='fangtang')
    person(A, 330, GROUND, 120, dir=1, robe=True, hat='none', kneel=True, arm=lerp(60, 100, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    book(A, 560, GROUND - 74, 160, 0, open_=1.0)
    A.flush(cv)
    type_in(cv, text_img('书其上曰 不若是 非人也', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.6)
    stamp(cv, seal('孝经', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_father(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, layer='ink')
    person(A, 880, GROUND, 130, dir=-1, robe=True, hat='none', kneel=True, bow=30, layer='fangtang')
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('父卒 托孤刘子羽 从学武夷三先生', SERIF, 44, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '三先生 胡宪 刘勉之 刘子翚', t, t - u + P)

def art_z_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='fangtang')
    ground(A, GROUND)
    zhu(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('进士及第 · 时年十九', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('进士', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_tongan(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='同安', layer='mid', open_=1.0)
    ground(A, GROUND)
    zhu(A, 540, GROUND, 190, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('同安主簿 · 整顿县学 清理簿书', SERIF, 44, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_liyan(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x - 20, GROUND - 300), (x + 20, GROUND - 300), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    x = lerp(100, 640, ease_out(u / (3.5 * P)))
    zhu(A, x, GROUND, 170, dir=1, ph=t * 4 if u < 3.5 * P else None, arm=-8)
    person(A, 860, GROUND, 180, dir=-1, robe=True, hat='knot', arm=lerp(-8, 90, clamp((u - 3.5 * P) / 0.6)), layer='fangtang')
    A.flush(cv)
    paste(cv, text_img('徒步数百里 · 拜李侗为师', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '延平答问记其师徒问答', t, t - u + 2 * P)

# ================================================================ 第二回 半亩方塘
def art_z_chuigong(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 780, GROUND, 200, dir=-1)
    zhu(A, 340, GROUND, 190, dir=1, bow=15, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    paste(cv, text_img('入对垂拱殿 · 力言复仇之义', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '与主和之议不合 辞归', t, t - u + P)

POEM = ['半亩方塘一鉴开', '天光云影共徘徊', '问渠那得清如许', '为有源头活水来']
def scene_fangtang(cv, t, c, k):
    """8-beat custom scene: 观书有感 — a half-acre pond opens like a mirror; sky light and clouds drift across it;
    why is it so clear? because living water flows in from the source. Reading is the source."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    pond(A, 600, 1120, 280, t, clear=clamp(ph / 1.5), clouds=clamp((ph - 1.5) / 1), inflow=clamp((ph - 5) / 1.5))
    ground(A, GROUND)
    zhu(A, 170, GROUND, 170, dir=1, arm=lerp(-8, 70, clamp((ph - 4) / 0.6)))
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '观书有感', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=69)
    fx.flush(cv)
    for i, line in enumerate(POEM):
        start = s0 + (0.3 + i * 1.8) * P
        if t >= start:
            paste(cv, text_img(line, SERIF, 44, ZHU if i == 3 else FANGTANG, 'Black', bleed=False, spacing=6), W / 2, 590 + i * 66, 1, clamp((t - start) / 0.4))
    if ph >= 7:
        paste(cv, text_img('读书明理 如活水入塘', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 7) / 0.4))
    note_in(cv, '方塘所在 尤溪 建阳等地说法不一', t, s0 + 2 * P)

def art_z_yuelu(A, cv, t, u):
    """6-beat set piece: 朱张会讲 — at 岳麓书院 in 长沙 he and 张栻 debate 中和 for two months; listeners crowd the hall."""
    ph = u / P
    academy(A, 540, 1240, 320, layer='mid')
    ground(A, GROUND)
    zhu(A, 380, GROUND, 180, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)))
    person(A, 700, GROUND, 180, dir=-1, robe=True, hat='knot', arm=lerp(120, 40, 0.5 + 0.5 * math.sin(t * 3)), layer='fangtang')
    n = int(clamp((ph - 1) / 3) * 10)
    for j in range(n):
        person(A, 100 + j * 92 if j < 5 else 980 - (j - 5) * 92, GROUND + 10, 70, dir=1 if j < 5 else -1, robe=True, hat='knot', kneel=True, layer='mid')
    A.flush(cv)
    lab = '赴长沙访张栻 · 岳麓书院' if ph < 3 else '论学两月 · 三日夜不能合'
    paste(cv, text_img(lab, SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('岳麓', 56), 860, 1440, t, t - u + 0.4, rot=6)
    note_in(cv, '相传听者千人 饮马池水为之竭', t, t - u + 3 * P)

def art_z_hanquan(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].polygon([(560, GROUND), (720, GROUND - 120), (880, GROUND)], fill=200)
    academy(A, 300, GROUND, 180, layer='mid', plaque=False)
    zhu(A, 600, GROUND, 160, dir=1, kneel=True, bow=30, arm=-8)
    A.flush(cv)
    paste(cv, text_img('母祝氏卒 · 筑寒泉精舍 守墓著书', SERIF, 44, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_shecang(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        x = 300 + k * 240
        A.d['dune'].rectangle((x - 80, GROUND - 160, x + 80, GROUND), fill=230)
        A.d['ink'].polygon([(x - 100, GROUND - 160), (x + 100, GROUND - 160), (x, GROUND - 230)], fill=255)
    for j in range(4):
        person(A, lerp(-100, 960, ((t * 0.08 + j / 4) % 1)), GROUND, 90, dir=1, robe=False, hat='knot', load=True, ph=t * 4 + j, arm=160, layer='ink')
    A.flush(cv)
    paste(cv, text_img('丰年收粮 荒年借民 · 后推行天下', SERIF, 44, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('社仓', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_jinsilu(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='fangtang')
    zhu(A, 260, GROUND, 170, dir=1, kneel=True, arm=100)
    person(A, 820, GROUND, 170, dir=-1, robe=True, hat='knot', kneel=True, arm=100, layer='mid')
    slips(A, 470, GROUND - 74, min(14, int(clamp(u / (2.5 * P)) * 14) + 1), 80, layer='dansha')
    A.flush(cv)
    paste(cv, text_img('与吕祖谦同编近思录 · 理学入门之书', SERIF, 42, FANGTANG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 鹅湖
def art_z_ehu(A, cv, t, u):
    """6-beat set piece: 鹅湖之会 — at 鹅湖寺 吕祖谦 brings 朱熹 and the 陆 brothers together.
    朱: read widely and investigate things (道问学); 陆: first find the original mind (尊德性). Days of debate, no agreement."""
    ph = u / P
    A.d['mid'].polygon([(200, GROUND), (540, GROUND - 420), (880, GROUND)], fill=120)
    A.d['ocean'].ellipse((260, GROUND - 90, 820, GROUND - 10), fill=150)
    ground(A, GROUND)
    zhu(A, 280, GROUND, 200, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)) if 1 < ph < 3 else 60)
    person(A, 800, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)) if 3 <= ph < 5 else 60, layer='fangtang')
    person(A, 900, GROUND, 180, dir=-1, robe=True, hat='knot', arm=-8, layer='mid')
    person(A, 540, GROUND, 170, dir=1, robe=True, hat='knot', arm=-8, layer='mid')
    A.flush(cv)
    if ph < 1:
        lab, col = '吕祖谦约朱陆会于鹅湖寺', FANGTANG
    elif ph < 3:
        lab, col = '朱 先博览而后归约 格物穷理', FANGTANG
    elif ph < 5:
        lab, col = '陆 先发明本心 易简工夫终久大', DANSHA
    else:
        lab, col = '论辩数日 终不能合', ZHU
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if 3 <= ph < 5:
        paste(cv, text_img('支离事业竟浮沉', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 3.6) / 0.4))
    note_in(cv, '陆九渊讥朱学支离 朱熹不怿', t, t - u + 3 * P)

def art_z_nankang(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='南康', layer='mid', open_=1.0)
    ground(A, GROUND)
    zhu(A, 540, GROUND, 190, dir=1, arm=60, old=0.3)
    A.flush(cv)
    paste(cv, text_img('知南康军 · 时年五十', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('南康', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_bailu(A, cv, t, u):
    """6-beat set piece: 白鹿洞书院 — he finds the old academy in ruins under weeds, rebuilds it, writes the 揭示 and lectures."""
    ph = u / P
    for k in range(3):
        x = 220 + k * 320
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 360), (x + 220, GROUND)], fill=150)
    ground(A, GROUND)
    if ph < 2:
        for i in range(8):
            A.d['dune'].rectangle((300 + i * 60, GROUND - 30 - 40 * ((i * 37) % 3), 340 + i * 60, GROUND), fill=200)
        for i in range(30):
            x = 200 + (i * 53) % 680
            A.d['grass'].line((x, GROUND, x + 6, GROUND - 40 - (i * 7) % 30), fill=230, width=4)
        zhu(A, 180, GROUND, 170, dir=1, arm=-8, old=0.3)
        lab = '白鹿洞旧址 荒草满地'
    else:
        q = ease_out(clamp((ph - 2) / 1.5))
        academy(A, 540, GROUND, 300 * (0.6 + 0.4 * q), layer='mid')
        if ph > 3.5:
            for j in range(6):
                person(A, lerp(-80, 260, ((t * 0.12 + j / 6) % 1)), GROUND, 80, dir=1, robe=True, hat='knot', ph=t * 4 + j, arm=-8, layer='fangtang')
        zhu(A, 860, GROUND, 170, dir=-1, arm=lerp(-8, 100, clamp((ph - 2) / 0.6)), old=0.3)
        lab = '重修书院 亲订学规' if ph < 4 else '博学之 审问之 慎思之 明辨之 笃行之'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 40 if ph >= 4 else 46, ZHU if ph >= 4 else FANGTANG, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    if ph >= 2:
        stamp(cv, seal('白鹿洞', 50), 860, 1440, t, t - u + 2 * P, rot=6)
    note_in(cv, '白鹿洞书院揭示 成为后世书院学规范本', t, t - u + 4 * P)

def art_z_lujiuyuan(A, cv, t, u):
    academy(A, 540, 1240, 300, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 190, dir=1, robe=True, hat='knot', arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='fangtang')
    zhu(A, 220, GROUND, 170, dir=1, kneel=True, arm=-8, old=0.3)
    for j in range(4):
        person(A, 700 + j * 80, GROUND, 80, dir=-1, robe=True, hat='knot', kneel=True, layer='mid')
    A.flush(cv)
    paste(cv, text_img('请陆九渊登白鹿洞讲席 · 君子喻于义', SERIF, 42, FANGTANG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '朱熹称其切中学者隐微深痼之病', t, t - u + P)

def art_z_zhedong(A, cv, t, u):
    ground(A, GROUND)
    for j in range(5):
        person(A, 560 + j * 90, GROUND, 110, dir=-1, robe=False, hat='knot', kneel=True, bow=20, layer='mid')
    zhu(A, 300, GROUND, 190, dir=1, arm=lerp(40, 110, ease_out(u / 0.5)), old=0.4)
    A.flush(cv)
    paste(cv, text_img('巡行浙东赈灾 · 六上奏章劾唐仲友', SERIF, 44, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('六劾', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '此案牵涉营妓严蕊 后世多有演绎', t, t - u + P)

def art_z_wuyi(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 90, GROUND), (x - 40, GROUND - 420), (x + 40, GROUND - 440), (x + 90, GROUND)], fill=160)
    A.d['ocean'].line([(60, GROUND - 30), (300, GROUND - 60), (540, GROUND - 30), (800, GROUND - 60), (1020, GROUND - 30)], fill=200, width=18)
    xr = lerp(100, 820, (t * 0.05) % 1)
    A.d['dune'].rectangle((xr - 60, GROUND - 52, xr + 60, GROUND - 40), fill=255)
    person(A, xr, GROUND - 52, 70, dir=1, robe=False, hat='knot', arm=140, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('筑武夷精舍 · 讲学九曲溪畔', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '次年作武夷棹歌十首', t, t - u + P)

# ================================================================ 第四回 伪学
def art_z_zhangzhou(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='mid')
    for i in range(4):
        book(A, 390 + i * 100, GROUND - 74, 80, 160, layer='fangtang' if i % 2 else 'dansha')
    zhu(A, 160, GROUND, 180, dir=1, arm=110, old=0.5)
    A.flush(cv)
    paste(cv, text_img('知漳州 · 首次合刻四书', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('漳州', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_sishu(A, cv, t, u):
    """6-beat set piece: 四书章句集注 — the four books stand up one by one; then the key line of 大学 and his gloss of 格物."""
    ph = u / P
    ground(A, GROUND)
    if ph < 3:
        four_books(A, cv, t, min(4, int(ph / 0.6) + 1), base=1250, h=300)
        lab, col = '大学 中庸 论语 孟子 合为四书', FANGTANG
    else:
        desk(A, 540, GROUND, 460, layer='fangtang')
        zhu(A, 260, GROUND, 180, dir=1, kneel=True, bow=20, arm=90, old=0.6)
        lamp(A, 800, GROUND - 74, 30, t, glow=0.9)
        book(A, 560, GROUND - 74, 150, 0, open_=1.0)
        A.flush(cv)
        lab, col = ('致知在格物', FANGTANG) if ph < 4.5 else ('格物者 即物而穷其理也', ZHU)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('四十余年 修改不辍', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.8) / 0.4))

def art_z_tanzhou(A, cv, t, u):
    academy(A, 540, 1240, 320, layer='mid')
    ground(A, GROUND)
    zhu(A, 260, GROUND, 180, dir=1, arm=lerp(-8, 110, ease_out(u / 0.5)), old=0.6)
    A.flush(cv)
    paste(cv, text_img('知潭州 · 修复岳麓书院', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('岳麓', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_shijiang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 780, GROUND, 200, dir=-1)
    zhu(A, 340, GROUND, 190, dir=1, bow=15, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)), old=0.6)
    A.flush(cv)
    paste(cv, text_img('为宁宗侍讲 · 劝君正心 触怒韩侂胄', SERIF, 44, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '立朝仅四十六日即被罢', t, t - u + P)

def art_z_dangjin(A, cv, t, u):
    """6-beat set piece: 庆元党禁 — 韩侂胄 brands 道学 as 伪学; a blacklist of fifty-nine names; students scatter or change teachers."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        palace(A, 540, 1300, 320, layer='mid')
        emperor(A, 780, GROUND, 200, dir=-1)
        scroll(A, 400, 1100, 360, 200, ease_out(clamp(ph / 1)), layer='wash')
        A.flush(cv)
        stamp(cv, seal('伪学', 70, ZHU), 400, 1100, t, t - u + 0.6 * P)
        lab = '韩侂胄专权 · 斥道学为伪学'
    elif ph < 4:
        scroll(A, 540, 1080, 520, 380, 1.0, layer='wash')
        A.flush(cv)
        n = min(59, int(clamp((ph - 2) / 1.6) * 59))
        for i in range(n):
            x = 330 + (i % 10) * 46; y = 920 + (i // 10) * 54
            A.d['ink'].rectangle((x, y, x + 30, y + 10), fill=200)
        A.flush(cv)
        lab = f'伪学逆党籍 · {cn_num(max(1, n))}人'
    else:
        academy(A, 540, 1240, 280, layer='mid', plaque=False)
        for j in range(6):
            q = clamp((ph - 4) / 1.5)
            person(A, 540 + (j - 2.5) * 40 + (j - 2.5) * 140 * q, GROUND, 80, dir=1 if j >= 3 else -1, robe=True, hat='knot', ph=t * 4 + j, arm=-8, layer='fangtang')
        zhu(A, 540, GROUND, 170, dir=1, arm=-8, old=0.8)
        A.flush(cv)
        lab = '门人故旧 或更名他师'
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '监察御史上疏诬其十罪 多属构陷', t, t - u + P)

def art_z_kaoting(A, cv, t, u):
    ground(A, GROUND)
    academy(A, 700, GROUND, 200, layer='mid', plaque=False)
    desk(A, 300, GROUND, 300, layer='fangtang')
    zhu(A, 160, GROUND, 160, dir=1, kneel=True, bow=20, arm=90, old=0.9)
    lamp(A, 420, GROUND - 74, 26, t, glow=0.9)
    A.flush(cv)
    paste(cv, text_img('退居建阳考亭 · 讲学著书不辍', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 源头活水
def art_z_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    zhu(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于建阳考亭 · 年七十一', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '临终前三日 仍在修改大学诚意章', t, t - u + P)

def art_z_funeral(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 300), (x + 220, GROUND)], fill=150)
    ground(A, GROUND)
    for j in range(12):
        person(A, lerp(-100, 1100, ((t * 0.04 + j / 12) % 1)), GROUND - 6 * (j % 2), 80, dir=1, robe=True, hat='knot', ph=t * 3 + j, arm=-8, layer='ink' if j % 3 else 'fangtang')
    A.flush(cv)
    paste(cv, text_img('朝廷禁止会葬 · 仍有近千人送行', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_xueguan(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='fangtang')
    ground(A, GROUND)
    for i in range(4):
        book(A, 390 + i * 100, GROUND, 80, 140, layer='fangtang' if i % 2 else 'dansha')
    A.flush(cv)
    paste(cv, text_img('党禁解除 · 论语孟子集注立于学官', SERIF, 44, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '1209年追谥曰文 世称朱文公', t, t - u + P)

def art_z_congsi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for j in range(4):
        person(A, 300 + j * 160, GROUND, 150, dir=1, robe=True, hat='knot', bow=25, layer='ink')
    A.flush(cv)
    paste(cv, text_img('从祀孔庙 · 世称朱子', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('朱子', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_keju(A, cv, t, u):
    ground(A, GROUND)
    for r in range(3):
        for i in range(7):
            x = 140 + i * 134; y = GROUND - r * 150
            A.d['mid'].rectangle((x - 50, y - 120, x + 50, y), fill=200)
            person(A, x, y, 70, dir=1, robe=True, hat='knot', kneel=True, bow=20, layer='ink')
    A.flush(cv)
    paste(cv, text_img('元仁宗定科举 · 以朱注四书取士', SERIF, 46, FANGTANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '至1905年废科举 前后约六百年', t, t - u + P)

def art_z_debate_today(A, cv, t, u):
    ground(A, GROUND)
    four_books(A, cv, t, 4, base=1250, h=260, alpha=0.6)
    paste(cv, text_img('存天理 灭人欲', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '原意在克制私欲 后世常被用作礼教枷锁', t, t - u + 0.4)

def art_z_source(A, cv, t, u):
    pond(A, 620, 1150, 260, t, clear=1.0, inflow=1.0)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('为有源头活水来', SERIF, 48, FANGTANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_z_legacy(A, cv, t, u):
    pond(A, 860, 1360, 60, t, clear=1.0)

def art_z_title(A, cv, t, u):
    pond(A, 800, 1340, 130, t, clear=1.0)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    zhu(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))), old=0.2)

# ================================================================ script
CHAPTERS = {16: ('第一回', '天之上'), 48: ('第二回', '半亩方塘'), 80: ('第三回', '鹅湖'),
            112: ('第四回', '伪学'), 144: ('第五回', '源头活水')}

CARDS = [
    C(0, 2, 'works', 'num', num='半亩方塘', line='一首小诗读了八百年', art=art_z_hook_pond),
    C(2, 4, 'empire', 'num', num='四本书', line='科举考了六百年', art=art_z_hook_books),
    C(4, 6, 'court', 'num', num='一场辩论', line='谁也没说服谁', art=art_z_hook_debate),
    C(6, 8, 'death', 'num', num='伪学魁首', line='晚年被朝廷禁学', art=art_z_hook_ban),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 天之上
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1130, main='生于尤溪', sub='父朱松', art=art_z_birth),
    C(22, 26, 'night', 'card', year=1133, main='天之上', sub='四岁问天', art=art_z_sky),
    C(26, 30, 'works', 'card', year=1137, main='题书孝经', sub='八岁', art=art_z_xiaojing),
    C(30, 34, 'death', 'card', year=1143, main='父亲病逝', sub='托孤于友', art=art_z_father),
    C(34, 38, 'empire', 'card', year=1148, main='进士及第', sub='十九岁', art=art_z_jinshi),
    C(38, 42, 'court', 'card', year=1153, main='同安主簿', sub='初入仕途', art=art_z_tongan),
    C(42, 48, 'fate', 'card', year=1160, main='拜师李侗', sub='始归正学', art=art_z_liyan),
    # ---- 第二回 半亩方塘
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'court', 'card', year=1163, main='垂拱殿奏对', sub='力主抗金', art=art_z_chuigong),
    C(54, 62, 'works', 'fangtang', year=1166),
    C(62, 68, 'court', 'card', year=1167, main='朱张会讲', sub='岳麓书院', art=art_z_yuelu),
    C(68, 72, 'death', 'card', year=1170, main='寒泉精舍', sub='守墓著书', art=art_z_hanquan),
    C(72, 76, 'life', 'card', year=1171, main='五夫社仓', sub='荒年借粮', art=art_z_shecang),
    C(76, 80, 'works', 'card', year=1175, main='近思录', sub='与吕祖谦', art=art_z_jinsilu),
    # ---- 第三回 鹅湖
    C(80, 82, 'war', 'chapter'),
    C(82, 88, 'war', 'card', year=1175, main='鹅湖之会', sub='朱陆之辩', art=art_z_ehu),
    C(88, 92, 'empire', 'card', year=1179, main='知南康军', sub='五十岁', art=art_z_nankang),
    C(92, 98, 'works', 'card', year=1180, main='白鹿洞书院', sub='重修讲学', art=art_z_bailu),
    C(98, 102, 'life', 'card', year=1181, main='陆九渊讲学', sub='义利之辨', art=art_z_lujiuyuan),
    C(102, 106, 'court', 'card', year=1182, main='浙东赈灾', sub='六劾唐仲友', art=art_z_zhedong),
    C(106, 112, 'life', 'card', year=1183, main='武夷精舍', sub='九曲溪畔', art=art_z_wuyi),
    # ---- 第四回 伪学
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'court', 'card', year=1190, main='知漳州', sub='合刻四书', art=art_z_zhangzhou),
    C(118, 124, 'night', 'card', year=1190, main='四书集注', sub='格物致知', art=art_z_sishu),
    C(124, 128, 'works', 'card', year=1194, main='知潭州', sub='修复岳麓', art=art_z_tanzhou),
    C(128, 132, 'empire', 'card', year=1194, main='帝王之师', sub='四十六日', art=art_z_shijiang),
    C(132, 138, 'death', 'card', year=1196, main='庆元党禁', sub='伪学之祸', art=art_z_dangjin),
    C(138, 144, 'fate', 'card', year=1197, main='考亭讲学', sub='闭门著书', art=art_z_kaoting),
    # ---- 第五回 源头活水
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=1200, main='朱熹去世', sub='年七十一', art=art_z_death),
    C(150, 154, 'night', 'card', year=1200, main='千人会葬', sub='禁令之下', art=art_z_funeral),
    C(154, 158, 'court', 'card', year=1212, main='立于学官', sub='党禁解除', art=art_z_xueguan),
    C(158, 162, 'empire', 'card', year=1241, main='从祀孔庙', sub='世称朱子', art=art_z_congsi),
    C(162, 166, 'works', 'card', year=1313, main='科举定本', sub='六百年', art=art_z_keju),
    C(166, 168, 'fate', 'card', year=1313, main='功过之争', sub='天理人欲', art=art_z_debate_today),
    C(168, 170, 'end', 'card', year=1313, main='源头活水', sub='流淌至今', art=art_z_source),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='陆拾玖', col=FANGTANG, acc=DANSHA, born=1130, died=1200, age0=1129,
    born_lab='1130年', died_lab='1200年', years_txt='公元1130 — 1200',
    hook_q='他被骂了几百年 · 为什么又被尊为朱子？',
    name_line='朱熹 · 字元晦', name='朱熹', seal='晦庵', title_art=art_z_title,
    q1='一代宗师？', q2='礼教枷锁？',
    end_art=art_z_legacy, end_big='半亩方塘', end_seal='晦庵',
    end_l1='生前他被禁为伪学', end_l2='死后他的书考了六百年',
    end_brush='源头活水', end_ask='存天理灭人欲 你怎么看？评论区聊聊', next='忽必烈'),
    scenes=dict(chapter=scene_chapter, fangtang=scene_fangtang))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
