"""千古人物志 · 第伍拾集 · 孟子 (前372–前289)
Look: 霁蓝 + 织锦红, 梭子 corner borders, a 织机 chapter card: the cloth on the loom grows row by row (0→2→4→6)
and in the last chapter it is rolled into a finished bolt.
Set pieces: custom 8-beat scene 'sanqian' (孟母三迁), 6-beat 断机教子, 8-beat 游说诸侯 map, 6-beat 稷下,
6-beat 以羊易牛, 6-beat 大丈夫, 6-beat 鱼与熊掌, 6-beat 孟子节文.
Ages are counted in 虚岁 (age0 = born - 1) so that he dies 年八十四 as the sources say.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_guanzhong as Gz       # engine + helpers (previous episode)
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
from render_songtaizu import tent
from render_kongzi import slips, bundle
from render_quyuan import river
from render_sunwu import drum, banner, army

F.RIPPLE = False
JILAN = (52, 78, 140)               # 霁蓝
JINHONG = (178, 74, 72)             # 织锦红
S.LAYERS.append(('jilan', JILAN, 0.9, 1.0))
S.LAYERS.append(('jinhong', JINHONG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='仁', life='母', court='王', night='夜', war='战', empire='民', works='义', fate='道', death='轻', end='圣')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZHU, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (JILAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (JINHONG, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

CYPRESS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(CYPRESS)
for _x, _h in ((110, 220), (190, 170), (900, 200), (980, 240)):   # 邹鲁 old cypresses at the margins
    _d.line((_x, 1460, _x, 1460 - _h), fill=(60, 56, 50, 70), width=8)
    for _k in range(4):
        _y = 1460 - _h + _k * 40
        _d.ellipse((_x - 46 + _k * 4, _y - 22, _x + 46 - _k * 4, _y + 22), fill=(70, 90, 70, 46))
for _k in range(3):
    _d.line((60, 1470 + _k * 18, W - 60, 1470 + _k * 18), fill=JILAN + (30,), width=2)
MTN_COL = {'night': (30, 34, 50), 'death': (60, 60, 66), 'war': (110, 62, 56), 'fate': (90, 96, 112)}
def draw_background(t, theme):
    """邹鲁: rolling hills and old cypresses at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(184, 186, 190), (148, 154, 168), MTN_COL.get(theme, (100, 110, 132))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(CYPRESS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """梭子: a weaver's shuttle trailing a thread in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=JILAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=JILAN + (220,), width=3)
        cx, cy = x + sx * 56, y + sy * 40
        d.polygon([(cx - sx * 40, cy), (cx - sx * 10, cy - sy * 12), (cx + sx * 40, cy), (cx - sx * 10, cy + sy * 12)], fill=JINHONG + (230,))
        d.line((cx - sx * 10, cy, cx - sx * 30, cy + sy * 60), fill=JINHONG + (200,), width=2)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def meng(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """孟子: Warring-States scholar — square 儒冠, long beard, a broad blue sash."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.07 * h, y - 1.08 * h, x + 0.07 * h, y - 0.95 * h), fill=255)
        d.rectangle((x - 0.1 * h, y - 1.1 * h, x + 0.1 * h, y - 1.07 * h), fill=255)
        d.polygon([(x + dir * 0.03 * h, y - 0.84 * h), (x + dir * 0.1 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.62 * h)], fill=255)
        A.d['jilan'].rectangle((x - 0.08 * h, y - 0.58 * h, x + 0.08 * h, y - 0.52 * h), fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.04 * h, y - 0.82 * h), (x + dir * 0.09 * h, y - 0.82 * h), (x + dir * 0.05 * h, y - 0.66 * h)], fill=255)
    return hand

def mother(A, x, y, h, dir=-1, **kw):
    kw.setdefault('arm', 40)
    return person(A, x, y, h, dir=dir, robe=True, hat='knot', female=True, layer=kw.pop('layer', 'ink'), **kw)

def child(A, x, y, h, dir=1, **kw):
    kw.setdefault('arm', 40)
    return person(A, x, y, h, dir=dir, robe=True, hat='knot', layer=kw.pop('layer', 'ink'), **kw)

def king(A, x, y, h, dir=-1, layer='ink', **kw):
    return person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)

def loom(A, cx, base, rows, t, cut=0.0):
    w = 360
    A.d['ink'].line((cx - w / 2, base, cx - w / 2, base - 380), fill=255, width=10)
    A.d['ink'].line((cx + w / 2, base, cx + w / 2, base - 380), fill=255, width=10)
    A.d['ink'].line((cx - w / 2 - 20, base - 380, cx + w / 2 + 20, base - 380), fill=255, width=10)
    for k in range(9):
        A.d['wash'].line((cx - w / 2 + 20 + k * 40, base - 370, cx - w / 2 + 20 + k * 40, base - 120), fill=220, width=2)
    for r in range(rows):
        y = base - 140 - r * 34
        A.d['jinhong' if r % 2 else 'jilan'].rectangle((cx - w / 2 + 14, y - 30, cx + w / 2 - 14, y), fill=255)
    if cut > 0:
        A.d['wash'].rectangle((cx - w / 2 + 14, base - 140 - rows * 34 + 10, cx + w / 2 - 14, base - 140 - rows * 34 + 10 + 20 * cut), fill=255)
        A.d['ink'].line((cx - w / 2, base - 140 - rows * 34 + 18, cx - w / 2 + (w) * cut, base - 140 - rows * 34 + 18), fill=255, width=6)

# ================================================================ chapter card
CH = {16: (0, 0.0), 48: (2, 0.0), 80: (4, 0.0), 112: (6, 0.0), 144: (6, 1.0)}
def art_loom_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g, roll = CH.get(kb, (2, 0.0))
    prev = {48: 0, 80: 2, 112: 4, 144: 6}.get(kb, 0)
    q = ease_out(u / (1.2 * P))
    if roll:
        loom(A, 400, 1200, int(lerp(6, 0, q)), t)
        r = 40 + 50 * q
        A.d['jinhong'].ellipse((780 - r, 1200 - 2 * r, 780 + r, 1200), fill=255)
        A.d['jilan'].ellipse((780 - r * 0.5, 1200 - 1.5 * r, 780 + r * 0.5, 1200 - 0.5 * r), fill=255)
    else:
        loom(A, 540, 1200, int(lerp(prev, g, q)), t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_loom_chapter)
    ink_in(cv, text_img(no, SERIF, 56, JILAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_m_hook_move(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(140, 760, ease_out(u / (1.6 * P)))
    carriage(A, x, GROUND, 100, dir=1, wheel=t * 6, ph=t * 8, canopy=False, layer='mid')
    mother(A, x - 180, GROUND, 160, dir=1, ph=t * 4)
    child(A, x - 260, GROUND, 90, dir=1, ph=t * 4)

def art_m_hook_people(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (1.4 * P)) * 24) + 1
    for i in range(n):
        person(A, 100 + (i % 12) * 80, GROUND - (i // 12) * 70, 90, dir=1, robe=True, hat='knot', arm=30, layer='jilan' if i % 2 else 'ink')
    king(A, 540, GROUND - 200, 70, dir=1, arm=20, layer='mid')

def art_m_hook_cut(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='jilan')
    slips(A, 380, GROUND - 74, 16, 140, layer='mid')
    q = ease_out(u / P)
    for i in range(int(q * 6)):
        A.d['jinhong'].rectangle((380 + i * 50, GROUND - 210, 396 + i * 50, GROUND - 74), fill=230)

def art_m_hook_qi(A, cv, t, u):
    for k in range(6):
        q = (t * 0.25 + k / 6) % 1
        A.d['jilan'].ellipse((540 - 300 * q - 20, 1300 - 500 * q - 20, 540 + 300 * q + 20, 1300 - 500 * q + 20), outline=int(200 * (1 - q)), width=6)
    ground(A, GROUND)
    meng(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 30, ease_out(u / P)))

# ================================================================ 第一回 孟母教子
def art_m_birth(A, cv, t, u):
    A.d['mid'].rectangle((360, 1080, 720, GROUND), fill=220)
    A.d['ink'].polygon([(320, 1080), (760, 1080), (540, 960)], fill=255)
    ground(A, GROUND)
    mother(A, 820, GROUND, 190, dir=-1, arm=60)
    child(A, 900, GROUND, 70, dir=-1, baby=True)
    A.flush(cv)
    stamp(cv, seal('邹国', 56), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('鲁国孟孙氏之后', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_sanqian(cv, t, c, k):
    """8-beat custom scene: 孟母三迁 — by the graveyard the boy plays at funerals; by the market he plays at hawking;
    by the school he bows and recites; the mother nods: 此真可以居吾子矣."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    stage_i = min(2, int(ph / 2.6))
    lp = (ph - stage_i * 2.6)
    if stage_i == 0:
        for j in range(4):
            A.d['mid'].chord((180 + j * 220 - 70, GROUND - 90, 180 + j * 220 + 70, GROUND + 90), 180, 360, fill=220)
        child(A, 540, GROUND, 110, dir=1, kneel=True, bow=lerp(10, 60, 0.5 + 0.5 * math.sin(t * 4)), arm=120)
        lab, sl = '居近墓地 · 嬉戏为墓间之事', '墓'
    elif stage_i == 1:
        for j in range(3):
            A.d['jinhong'].polygon([(160 + j * 300, GROUND - 160), (360 + j * 300, GROUND - 160), (330 + j * 300, GROUND - 200), (190 + j * 300, GROUND - 200)], fill=230)
            A.d['ink'].line((180 + j * 300, GROUND - 160, 180 + j * 300, GROUND), fill=255, width=5)
            A.d['ink'].line((340 + j * 300, GROUND - 160, 340 + j * 300, GROUND), fill=255, width=5)
        child(A, 540, GROUND, 110, dir=1, arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 6)))
        lab, sl = '迁居市旁 · 嬉戏为贾人炫卖', '市'
    else:
        A.d['jilan'].rectangle((620, GROUND - 260, 960, GROUND), fill=200)
        A.d['ink'].polygon([(600, GROUND - 260), (980, GROUND - 260), (790, GROUND - 360)], fill=255)
        for j in range(3):
            sitter(A, 660 + j * 100, GROUND, 90, dir=-1, bow=20, layer='ink')
        child(A, 480, GROUND, 110, dir=1, bow=lerp(0, 40, 0.5 + 0.5 * math.sin(t * 3)), arm=90)
        lab, sl = '再迁学宫之旁 · 设俎豆 揖让进退', '学'
    x_m = lerp(160, 260, clamp(lp / 2))
    mother(A, x_m, GROUND, 180, dir=1, arm=lerp(-8, 70, clamp((lp - 1.6) / 0.4)))
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '孟母三迁', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=50)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, JILAN, 'Black', bleed=False, spacing=4), W / 2, 575, 1, clamp(lp / 0.4))
    stamp(cv, seal(sl, 60, ZHU if stage_i == 2 else INK), 860, 1020, t, s0 + stage_i * 2.6 * P + 0.3, rot=6)
    if ph > 7:
        paste(cv, text_img('此真可以居吾子矣', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 7) / 0.4))
    note_in(cv, '出自刘向列女传', t, s0 + 2 * P)

def art_m_loom(A, cv, t, u):
    """6-beat set piece: 断机教子 — the boy comes home early from school; his mother takes the knife to her weaving."""
    ph = u / P
    ground(A, GROUND)
    loom(A, 640, GROUND, 6, t, cut=clamp((ph - 2) / 0.6))
    mother(A, 380, GROUND, 190, dir=1, arm=lerp(40, 150, clamp((ph - 1.6) / 0.4)))
    child(A, lerp(-60, 180, ease_out(ph / 1.4)), GROUND, 120, dir=1, ph=t * 4 if ph < 1.4 else None, kneel=ph > 3, bow=40 if ph > 3 else 0, arm=-8)
    A.flush(cv)
    type_in(cv, text_img('子之废学 若吾断斯织也', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 2 * P, 0.5)
    type_in(cv, text_img('孟子惧 旦夕勤学不息', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 3.5 * P, 0.5)
    note_in(cv, '出自刘向列女传', t, t - u + P)

def art_m_zisi(A, cv, t, u):
    ground(A, GROUND)
    meng(A, 300, GROUND, 180, dir=1, kneel=True, bow=20, arm=90)
    person(A, 700, GROUND, 220, dir=-1, robe=True, hat='knot', arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    slips(A, 470, GROUND - 40, 6, 120, layer='jilan')
    A.flush(cv)
    paste(cv, text_img('受业子思之门人', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('孔门', 56), 860, 1020, t, t - u + P, rot=6)

def art_m_teach(A, cv, t, u):
    for k in range(3):
        A.d['pine'].polygon([(160 + k * 60, GROUND), (190 + k * 60, GROUND - 240), (220 + k * 60, GROUND)], fill=200)
    ground(A, GROUND)
    meng(A, 760, GROUND, 210, dir=-1, arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 2)))
    n = int(clamp(u / (2 * P)) * 8) + 1
    for i in range(n):
        sitter(A, 340 + (i % 4) * 80, GROUND - (i // 4) * 60, 90, dir=1, bow=15, layer='jilan' if i % 2 else 'ink')
    A.flush(cv)
    paste(cv, text_img('设帐授徒 · 得天下英才而教育之', SERIF, 42, JILAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_m_qi(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 380), (x + 220, GROUND)], fill=180)
    for k in range(5):
        q = (t * 0.3 + k / 5) % 1
        A.d['jilan'].arc((540 - 200 - 120 * q, 900 - 120 * q, 540 + 200 + 120 * q, 1300 + 120 * q), 200, 340, fill=int(200 * (1 - q)), width=5)
    ground(A, GROUND)
    meng(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 40, ease_out(u / 0.6)))
    A.flush(cv)
    type_in(cv, text_img('我善养吾浩然之气', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('至大至刚 以直养而无害', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.5 * P, 0.5)

# ================================================================ 第二回 周游列国
def art_m_teng(A, cv, t, u):
    A.d['grass'].rectangle((240, 900, 840, 1260), fill=150)
    for k in (1, 2):
        A.d['ink'].line((240 + 200 * k, 900, 240 + 200 * k, 1260), fill=220, width=5)
        A.d['ink'].line((240, 900 + 120 * k, 840, 900 + 120 * k), fill=220, width=5)
    A.d['jinhong'].rectangle((440, 1020, 640, 1140), fill=160)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('滕文公问为国 · 劝行井田', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('滕', 60), 860, 1020, t, t - u + P, rot=6)

def art_m_route(A, cv, t, u):
    """8-beat set piece: 游说诸侯 — a cart and retinue travel the map from 邹 to 滕, 宋, 魏 and 齐."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 760, 970, 1420), radius=24, fill=170)
    A.d['ocean'].line([(140, 980), (420, 1020), (700, 960), (960, 900)], fill=200, width=8)
    stops = [('邹', 720, 1300), ('滕', 780, 1180), ('宋', 560, 1240), ('魏', 300, 1080), ('齐', 820, 860)]
    f = clamp(ph / 7)
    n = len(stops) - 1
    m = f * n
    for i in range(n):
        ff = clamp(m - i)
        if ff <= 0: break
        (_, x0, y0), (_, x1, y1) = stops[i], stops[i + 1]
        A.d['jinhong'].line((x0, y0, lerp(x0, x1, ff), lerp(y0, y1, ff)), fill=255, width=8)
    i = min(n - 1, int(m)); ff = clamp(m - i)
    sx, sy = lerp(stops[i][1], stops[i + 1][1], ff), lerp(stops[i][2], stops[i + 1][2], ff)
    carriage(A, sx, sy, 40, dir=1, wheel=t * 6, ph=t * 8, layer='ink')
    A.flush(cv)
    for j, (nm, x, y) in enumerate(stops):
        stamp(cv, seal(nm, 34, ZHU if j == min(n, int(m + 0.5)) else JILAN), x - 70, y, t, t - u + 0.3 + j * 0.3)
    paste(cv, text_img('后车数十乘 从者数百人', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

def art_m_liang(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='jilan')
    ground(A, GROUND)
    king(A, 760, GROUND - 30, 220, dir=-1, arm=lerp(20, 90, ease_out(u / 0.6)))
    meng(A, 360, GROUND, 220, dir=1, arm=lerp(40, 120, ease_out((u - P) / 0.4)))
    A.flush(cv)
    type_in(cv, text_img('叟不远千里而来 亦将有以利吾国乎', SERIF, 40, INK, 'Black', bleed=False, spacing=2), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('王何必曰利 亦有仁义而已矣', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.8 * P, 0.5)
    stamp(cv, seal('梁惠王', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_m_fifty(A, cv, t, u):
    ground(A, GROUND)
    army(A, 940, GROUND, 4, dir=-1, layer='mid', h=100)
    q = ease_out(u / (2.5 * P))
    person(A, lerp(700, 420, q), GROUND, 120, dir=-1, robe=False, hat='helmet', ph=t * 6, arm=-8, layer='ink')
    person(A, lerp(700, 160, q), GROUND, 120, dir=-1, robe=False, hat='helmet', ph=t * 6, arm=-8, layer='ink')
    A.d['jinhong'].line((420, GROUND + 20, 700, GROUND + 20), fill=255, width=6)
    A.d['jilan'].line((160, GROUND + 34, 700, GROUND + 34), fill=255, width=6)
    A.flush(cv)
    paste(cv, text_img('以五十步笑百步 则何如', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_xiang(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    king(A, 720, GROUND - 30, 200, dir=-1, arm=20)
    meng(A, lerp(380, 120, ease_out((u - 2 * P) / P)), GROUND, 210, dir=-1 if u > 2 * P else 1, ph=t * 3 if u > 2 * P else None, arm=-8)
    A.flush(cv)
    type_in(cv, text_img('望之不似人君', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('梁襄王', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_m_jixia(A, cv, t, u):
    """6-beat set piece: 稷下学宫 — scholars of many schools gather in the Qi academy; arguments fly; he holds the floor."""
    ph = u / P
    A.d['jilan'].rectangle((140, 900, 940, 1000), fill=170)
    for k in range(6):
        A.d['ink'].line((180 + k * 140, 1000, 180 + k * 140, GROUND), fill=255, width=12)
    ground(A, GROUND)
    for i in range(8):
        sitter(A, 160 + i * 110, GROUND, 100, dir=1 if i < 4 else -1, bow=lerp(0, 25, 0.5 + 0.5 * math.sin(t * 3 + i)), layer='mid' if i % 2 else 'ink')
    meng(A, 540, GROUND - 40, 200, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 2.5)))
    schools = ['儒', '墨', '道', '法', '农', '阴阳']
    A.flush(cv)
    k2 = min(5, int(ph))
    for j in range(k2 + 1):
        stamp(cv, seal(schools[j], 34, ZHU if j == 0 else INK), 200 + j * 136, 1060, t, t - u + j * P)
    paste(cv, text_img('至齐 · 稷下百家争鸣', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 民贵君轻
def art_m_ox(A, cv, t, u):
    """6-beat set piece: 以羊易牛 — an ox trembles on its way to sacrifice; the king swaps it for a sheep; Mencius names it 仁术."""
    ph = u / P
    palace(A, 540, 1140, 520, layer='mid')
    ground(A, GROUND)
    king(A, 820, GROUND - 30, 200, dir=-1, arm=lerp(20, 120, clamp((ph - 1) / 0.4)))
    if ph < 2.4:
        horse(A, lerp(-100, 420, ease_out(ph / 1.4)), GROUND, 160, dir=1, ph=t * 2 + (0.3 * math.sin(t * 20)), head_down=0.6, layer='ink')
        person(A, lerp(-240, 280, ease_out(ph / 1.4)), GROUND, 150, dir=1, robe=False, hat='knot', arm=80, layer='ink')
    else:
        A.d['wash'].ellipse((340, GROUND - 110, 500, GROUND - 30), fill=255)
        A.d['ink'].ellipse((480, GROUND - 120, 530, GROUND - 80), fill=255)
        for lx in (360, 400, 440, 480):
            A.d['ink'].line((lx, GROUND - 40, lx, GROUND), fill=255, width=6)
        meng(A, 640, GROUND, 200, dir=-1, arm=lerp(-8, 90, clamp((ph - 3.2) / 0.4)))
    A.flush(cv)
    lab = '牛觳觫 若无罪而就死地' if ph < 2.4 else ('以羊易之' if ph < 3.6 else '是乃仁术也 见牛未见羊也')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.6 else JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('齐宣王', 50, INK), 860, 1440, t, t - u + 0.4, rot=6)

def art_m_music(A, cv, t, u):
    ground(A, GROUND)
    for i in range(5):
        A.d['ink'].line((200 + i * 90, GROUND - 200, 200 + i * 90, GROUND - 120), fill=255, width=4)
        A.d['jilan'].polygon([(200 + i * 90 - 26, GROUND - 120), (200 + i * 90 + 26, GROUND - 120), (200 + i * 90 + 32, GROUND - 60), (200 + i * 90 - 32, GROUND - 60)], fill=255)
    n = int(clamp(u / (2 * P)) * 10) + 1
    for i in range(n):
        person(A, 640 + (i % 5) * 70, GROUND - (i // 5) * 60, 110, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 5 + i)), layer='jinhong' if i % 2 else 'ink')
    A.flush(cv)
    paste(cv, text_img('独乐乐 不如与众乐乐', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_people(A, cv, t, u):
    ground(A, GROUND)
    q = ease_out(u / (1.5 * P))
    for i in range(18):
        person(A, 130 + (i % 9) * 100, GROUND - (i // 9) * 80, 100, dir=1, robe=True, hat='knot', arm=30, layer='jilan' if i % 2 else 'ink')
    A.d['mid'].rectangle((470, GROUND - 400, 610, GROUND - 330), fill=255)
    king(A, 540, lerp(GROUND - 400, GROUND - 260, q), 80, dir=1, arm=20, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('民为贵 社稷次之 君为轻', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('尽心下', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_m_yifu(A, cv, t, u):
    palace(A, 540, 1260, 380, collapse=ease_out((u - P) / (2 * P)), layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('闻诛一夫纣矣 未闻弑君也', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('残贼之人', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_m_yan(A, cv, t, u):
    city_wall(A, 520, 1000, 1080, gate_x=760, label='燕', layer='mid', open_=1.0)
    ground(A, GROUND)
    army(A, lerp(-100, 220, ease_out(u / (2 * P))), GROUND, 6, dir=1, layer='jilan', t=t, march=u < 2 * P, h=110)
    A.flush(cv)
    paste(cv, text_img('齐伐燕 · 五旬而举之', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('伐燕', 56), 260, 1020, t, t - u + P, rot=-5)

def art_m_revolt(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='燕', layer='mid', open_=1.0)
    flames(A, 540, 1060, 600, 200 * ease_out(u / P), t, n=7, seed=314, smoke=True)
    ground(A, GROUND)
    army(A, lerp(500, -200, ease_out((u - P) / (2 * P))), GROUND, 5, dir=-1, layer='jilan', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('燕人畔 · 王曰 吾甚惭于孟子', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_leave(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=180)
    ground(A, GROUND)
    x = lerp(300, 820, ease_out(u / (3 * P)))
    carriage(A, x, GROUND, 90, dir=1, wheel=t * 3, ph=t * 4, layer='ink')
    A.flush(cv)
    n = min(3, int(u / P) + 1)
    paste(cv, text_img(f'去齐 · 宿于昼 第{cn_num(n)}夜', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('三宿出昼', 44), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第四回 舍生取义
def art_m_home(A, cv, t, u):
    A.d['mid'].rectangle((600, GROUND - 220, 900, GROUND), fill=220)
    A.d['ink'].polygon([(580, GROUND - 220), (920, GROUND - 220), (750, GROUND - 320)], fill=255)
    ground(A, GROUND)
    meng(A, lerp(120, 480, ease_out(u / (2 * P))), GROUND, 200, dir=1, ph=t * 3, arm=-8, old=0.6)
    A.flush(cv)
    paste(cv, text_img('不得志 · 归邹', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_write(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='jilan')
    meng(A, 300, GROUND, 200, dir=1, kneel=True, bow=20, arm=90, old=0.6)
    sitter(A, 760, GROUND, 160, dir=-1, bow=20, layer='mid')
    sitter(A, 860, GROUND, 150, dir=-1, bow=20, layer='ink')
    n = min(7, int(clamp(u / (2.5 * P)) * 7) + 1)
    for i in range(n):
        bundle(A, 420 + i * 40, GROUND - 74, 36, layer='jinhong')
    A.flush(cv)
    paste(cv, text_img(f'与万章 公孙丑之徒 作孟子{cn_num(n)}篇', SERIF, 42, JILAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, 1)

def art_m_dazhangfu(A, cv, t, u):
    """6-beat set piece: 大丈夫 — gold, rags and a blade in turn press on a standing figure; he does not bend."""
    ph = u / P
    ground(A, GROUND)
    meng(A, 540, GROUND, 240, dir=1, arm=-8)
    k = min(2, int(ph / 2))
    if k == 0:
        for i in range(8):
            A.d['gold'].ellipse((260 + (i % 4) * 40 - 18, GROUND - 40 - (i // 4) * 30, 260 + (i % 4) * 40 + 18, GROUND - 10 - (i // 4) * 30), fill=255)
    elif k == 1:
        A.d['mid'].polygon([(700, GROUND), (760, GROUND - 120), (820, GROUND - 90), (860, GROUND)], fill=200)
        A.d['ink'].ellipse((740, GROUND - 40, 780, GROUND), outline=200, width=4)
    else:
        A.d['ink'].line((760, GROUND - 300, 640, GROUND - 180), fill=255, width=8)
        A.d['jinhong'].line((640, GROUND - 180, 620, GROUND - 160), fill=255, width=12)
    A.flush(cv)
    lines = ['富贵不能淫', '贫贱不能移', '威武不能屈']
    for j in range(k + 1):
        paste(cv, text_img(lines[j], SERIF, 48, ZHU if j == k else DIM, 'Black', bleed=False, spacing=6), W / 2, 700 + j * 66, 1, clamp((ph - j * 2) / 0.4))
    paste(cv, text_img('此之谓大丈夫', SERIF, 44, JILAN, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 5) / 0.4))

def art_m_fish(A, cv, t, u):
    """6-beat set piece: 鱼与熊掌 — a fish and a bear's paw on a scale; then 生 and 义 replace them; 义 is chosen."""
    ph = u / P
    ground(A, GROUND)
    tilt = lerp(0, -0.18, clamp((ph - 3.5) / 0.8))
    cx, cy = 540, 980
    lx, ly = cx - 260 * math.cos(tilt), cy - 260 * math.sin(tilt)
    rx, ry = cx + 260 * math.cos(tilt), cy + 260 * math.sin(tilt)
    A.d['ink'].line((cx, cy, cx, GROUND), fill=255, width=10)
    A.d['ink'].line((lx, ly, rx, ry), fill=255, width=8)
    for (px, py) in ((lx, ly), (rx, ry)):
        A.d['ink'].line((px, py, px, py + 120), fill=255, width=3)
        A.d['mid'].chord((px - 90, py + 80, px + 90, py + 160), 0, 180, fill=230)
    if ph < 3:
        A.d['jilan'].ellipse((lx - 60, ly + 70, lx + 40, ly + 110), fill=255)
        A.d['jilan'].polygon([(lx + 40, ly + 90), (lx + 80, ly + 70), (lx + 80, ly + 110)], fill=255)
        A.d['ink'].ellipse((rx - 40, ry + 60, rx + 40, ry + 120), fill=255)
    A.flush(cv)
    if ph >= 3:
        paste(cv, text_img('生', BRUSH, 110, INK), lx, ly + 60, 1, clamp((ph - 3) / 0.3))
        paste(cv, text_img('义', BRUSH, 110, ZHU), rx, ry + 60, 1, clamp((ph - 3) / 0.3))
    l1 = '鱼 我所欲也 熊掌 亦我所欲也' if ph < 3 else '生 亦我所欲也 义 亦我所欲也'
    paste(cv, text_img(l1, SERIF, 42, JILAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    if ph > 4:
        paste(cv, text_img('二者不可得兼 舍生而取义者也', SERIF, 44, ZHU, 'Black', bleed=False, spacing=2), W / 2, 835, 1, clamp((ph - 4) / 0.4))

def art_m_youhuan(A, cv, t, u):
    for k in range(60):
        q = (t * 0.5 + k / 60) % 1
        A.d['wash'].ellipse((80 + (k * 19) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 19) % 920 + 4, lerp(620, 1420, q) + 4), fill=200)
    ground(A, GROUND)
    for k in range(3):
        A.d['ink'].line((260 + k * 280, GROUND, 260 + k * 280, GROUND - 260), fill=255, width=10)
        A.d['jinhong'].ellipse((260 + k * 280 - 30, GROUND - 300, 260 + k * 280 + 30, GROUND - 240), fill=220)
    A.flush(cv)
    type_in(cv, text_img('生于忧患 而死于安乐也', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)

def art_m_dao(A, cv, t, u):
    ground(A, GROUND)
    q = ease_out(u / (2 * P))
    for i in range(10):
        person(A, lerp(120 + i * 30, 300 + i * 50, q), GROUND, 110, dir=1, robe=True, hat='knot', arm=40, layer='jilan')
    person(A, 860, GROUND, 140, dir=-1, robe=True, hat='crown', arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('得道者多助 失道者寡助', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    meng(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - 0.5 * P) / 0.8))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('年八十四', SERIF, 48, JILAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.3))

# ================================================================ 第五回 亚圣
def art_m_temple(A, cv, t, u):
    palace(A, 540, 1140, 600, layer='jinhong')
    ground(A, GROUND)
    A.d['jilan'].rectangle((620, 1000, 660, 1100), fill=255)
    A.flush(cv)
    paste(cv, text_img('北宋元丰年间 · 配享孔庙', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('配享', 56), 860, 1020, t, t - u + P, rot=6)

def art_m_four(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='jilan')
    names = ['大学', '中庸', '论语', '孟子']
    A.flush(cv)
    for i, nm in enumerate(names):
        im = text_img(nm, SERIF, 40, ZHU if i == 3 else INK, 'Black', bleed=False, vertical=True)
        paste(cv, im, 380 + i * 106, GROUND - 74 - im.height / 2 - 10, 1, clamp((u - i * 0.5 * P) / 0.3))
    paste(cv, text_img('朱熹集注 · 四书', SERIF, 46, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_yasheng(A, cv, t, u):
    for k in range(3):
        A.d['jilan'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    meng(A, 540, GROUND - 180, 200, dir=1, arm=-8)
    A.flush(cv)
    ink_in(cv, text_img('亚圣', BRUSH, 140, ZHU), W / 2, 1000, t, t - u + 0.6, dur=0.3, settle=1.2)
    paste(cv, text_img('元文宗加封 邹国亚圣公', SERIF, 44, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_zhu(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    king(A, 540, GROUND, 230, dir=1, arm=lerp(20, 160, ease_out((u - 0.5 * P) / 0.3)))
    slips(A, 720, GROUND - 4, 8, 60, layer='jilan')
    A.flush(cv)
    paste(cv, text_img('使此老在今日 宁得免焉', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('朱元璋', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_m_jiewen(A, cv, t, u):
    """6-beat set piece: 孟子节文 — the emperor's scholars strike out passage after passage; eighty-five are gone."""
    ph = u / P
    ground(A, GROUND)
    A.d['wash'].rectangle((200, 880, 880, 1300), fill=255)
    A.d['ink'].rectangle((200, 880, 880, 1300), outline=255, width=6)
    n = min(85, int(clamp(ph / 5) * 85))
    for i in range(24):
        x = 840 - i * 27
        A.d['ink'].line((x, 910, x, 1270), fill=90, width=3)
        if i * 85 / 24 < n:
            A.d['jinhong'].line((x - 8, 910, x + 8, 1270), fill=255, width=6)
    A.flush(cv)
    paste(cv, text_img(f'删去{n}条', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    paste(cv, text_img('民为贵 · 闻诛一夫纣矣 皆在删中', SERIF, 40, INK, 'Black', bleed=False, spacing=2), W / 2, 835, 1, clamp((ph - 2) / 0.4))
    note_in(cv, '洪武二十七年刊行 永乐年间恢复全本', t, t - u + 3 * P)

def art_m_haoqi(A, cv, t, u):
    for k in range(5):
        q = (t * 0.3 + k / 5) % 1
        A.d['jilan'].arc((540 - 160 - 160 * q, 900 - 160 * q, 540 + 160 + 160 * q, 1300 + 160 * q), 200, 340, fill=int(200 * (1 - q)), width=6)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('书可以删 话删不掉', SERIF, 48, JILAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    loom(A, 860, 1440, 3, t)

def art_m_title(A, cv, t, u):
    loom(A, 800, 1460, 5, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    meng(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '孟母教子'), 48: ('第二回', '周游列国'), 80: ('第三回', '民贵君轻'),
            112: ('第四回', '舍生取义'), 144: ('第五回', '亚圣')}

CARDS = [
    C(0, 2, 'life', 'num', num='搬三次家', line='为了一个孩子', art=art_m_hook_move),
    C(2, 4, 'empire', 'num', num='民为贵', line='君为轻', art=art_m_hook_people),
    C(4, 6, 'death', 'num', num='一个皇帝', line='删了他的书', art=art_m_hook_cut),
    C(6, 8, 'works', 'num', num='浩然之气', line='至大至刚', art=art_m_hook_qi),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 孟母教子
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-372, main='生于邹国', sub='幼年丧父', note='父早亡之说见后世传记', art=art_m_birth),
    C(22, 30, 'life', 'sanqian', year=-369),
    C(30, 36, 'night', 'card', year=-365, main='断机教子', sub='母亲的一刀', art=art_m_loom),
    C(36, 40, 'works', 'card', year=-355, main='师承子思', sub='孔子四传', art=art_m_zisi),
    C(40, 44, 'court', 'card', year=-340, main='设帐授徒', sub='一乐也', art=art_m_teach),
    C(44, 48, 'empire', 'card', year=-335, main='养浩然气', sub='至大至刚', art=art_m_qi),
    # ---- 第二回 周游列国
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'works', 'card', year=-326, main='滕国问政', sub='小国试井田', art=art_m_teng),
    C(54, 62, 'fate', 'card', year=-324, main='游说诸侯', sub='传食于诸侯', art=art_m_route),
    C(62, 66, 'court', 'card', year=-320, main='见梁惠王', sub='何必曰利', art=art_m_liang),
    C(66, 70, 'war', 'card', year=-320, main='五十步笑百步', sub='寡人之于国也', art=art_m_fifty),
    C(70, 74, 'night', 'card', year=-319, main='不似人君', sub='梁襄王', art=art_m_xiang),
    C(74, 80, 'empire', 'card', year=-319, main='稷下学宫', sub='百家争鸣', art=art_m_jixia),
    # ---- 第三回 民贵君轻
    C(80, 82, 'empire', 'chapter'),
    C(82, 88, 'court', 'card', year=-319, main='以羊易牛', sub='不忍之心', art=art_m_ox),
    C(88, 92, 'life', 'card', year=-318, main='与民同乐', sub='好乐何妨', art=art_m_music),
    C(92, 96, 'empire', 'card', year=-317, main='民为贵', sub='两千年前的惊雷', art=art_m_people),
    C(96, 100, 'death', 'card', year=-316, main='诛一夫', sub='暴君不是君', art=art_m_yifu),
    C(100, 104, 'war', 'card', year=-314, main='齐伐燕', sub='取之而燕民悦则取之', art=art_m_yan),
    C(104, 108, 'night', 'card', year=-312, main='燕人反叛', sub='不听之过', art=art_m_revolt),
    C(108, 112, 'fate', 'card', year=-312, main='去齐', sub='依依不舍', art=art_m_leave),
    # ---- 第四回 舍生取义
    C(112, 114, 'works', 'chapter'),
    C(114, 118, 'fate', 'card', year=-311, main='归邹', sub='道不行', art=art_m_home),
    C(118, 122, 'works', 'card', year=-305, main='著书七篇', sub='退而著述', art=art_m_write),
    C(122, 128, 'empire', 'card', year=-305, main='大丈夫', sub='什么才是真男人', art=art_m_dazhangfu),
    C(128, 134, 'court', 'card', year=-300, main='鱼与熊掌', sub='舍生取义', art=art_m_fish),
    C(134, 138, 'night', 'card', year=-295, main='生于忧患', sub='死于安乐', art=art_m_youhuan),
    C(138, 142, 'life', 'card', year=-295, main='得道多助', sub='失道寡助', art=art_m_dao),
    C(142, 144, 'death', 'card', year=-289, main='孟子辞世', sub='寿终于邹', art=art_m_death),
    # ---- 第五回 亚圣
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'court', 'card', year=1084, main='配享孔庙', sub='千年之后', art=art_m_temple),
    C(150, 154, 'works', 'card', year=1190, main='列入四书', sub='科举必读', art=art_m_four),
    C(154, 158, 'empire', 'card', year=1330, main='加封亚圣', sub='仅次于孔子', art=art_m_yasheng),
    C(158, 162, 'death', 'card', year=1372, main='罢其配享', sub='朱元璋大怒', note='次年即恢复', art=art_m_zhu),
    C(162, 168, 'night', 'card', year=1394, main='孟子节文', sub='皇帝删书', art=art_m_jiewen),
    C(168, 170, 'end', 'card', year=1394, main='浩气长存', sub='删不掉的话', art=art_m_haoqi),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='伍拾', col=JILAN, acc=JINHONG, born=-372, died=-289, age0=-373,
    born_lab='前372年', died_lab='前289年', years_txt='公元前372 — 前289',
    hook_q='他说君为轻 · 皇帝为什么要删他的书？',
    name_line='孟轲 · 字子舆', name='孟子', seal='亚圣', title_art=art_m_title,
    q1='一代亚圣？', q2='迂腐书生？',
    end_art=art_m_legacy, end_big='民贵君轻', end_seal='亚圣',
    end_l1='皇帝删得掉他的书', end_l2='删不掉他说过的话',
    end_brush='威武不能屈', end_ask='鱼和熊掌 你会怎么选？评论区聊聊', next='庄子'),
    scenes=dict(chapter=scene_chapter, sanqian=scene_sanqian))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
