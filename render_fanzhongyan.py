"""千古人物志 · 第叁拾捌集 · 范仲淹 (989–1052)
Look: 洞庭秋水蓝 + 晚霞橙, 孤雁 corner borders, a 岳阳楼 chapter card: the tower rises a storey per chapter;
in the last the evening glow lights it.
Set pieces: 6-beat 断齑画粥, 6-beat 范公堤, custom 8-beat scene 'sanguang' (三次被贬), 8-beat 庆历新政,
8-beat 岳阳楼记.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_baozheng as Bz        # engine + helpers (previous episode)
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
from render_quyuan import river
from render_simaqian import brush, bars
from render_kongzi import bundle
from render_wanganshi import donkey
from render_yuefei import cn_year

F.RIPPLE = False
DONGTING = (64, 112, 146)           # 洞庭秋水蓝
XIA = (226, 128, 62)                # 晚霞橙
S.LAYERS.append(('dongting', DONGTING, 0.88, 1.0))
S.LAYERS.append(('xia', XIA, 0.88, 1.4))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='忧', life='粥', court='宋', night='贬', war='边', empire='宋', works='新', fate='忧', death='乐', end='乐')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court', 'empire'):
    G.THEMES[k]['part'] = 'petal'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (XIA, 230, (W * 0.5, 820))
G.THEMES['end']['sun'] = (XIA, 220, (W * 0.5, 720))
G.THEMES['fate']['sun'] = (XIA, 200, (W * 0.72, 760))
G.base_bg.cache_clear()

LAKE = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(LAKE)
for _k in range(4):
    _y = 1440 + _k * 14
    _d.line((60, _y, W - 60, _y), fill=DONGTING + (36 - _k * 6,), width=3)
for _x, _y in ((140, 1300), (180, 1280), (220, 1310), (880, 1290), (920, 1270)):
    _d.line((_x - 14, _y, _x, _y - 8, _x + 14, _y), fill=(60, 60, 70, 70), width=3)
MTN_COL = {'night': (34, 38, 46), 'death': (60, 60, 64), 'war': (100, 70, 54), 'fate': (90, 92, 110)}
def draw_background(t, theme):
    """洞庭: wide low ridges, faint lake lines, a skein of geese at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(184, 190, 196), (140, 156, 170), MTN_COL.get(theme, (100, 118, 136))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(LAKE)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """孤雁: a single goose in flight in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=DONGTING + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=DONGTING + (220,), width=3)
        cx, cy = x + sx * 70, y + sy * 60
        d.line((cx - 30, cy + 6, cx, cy - 6, cx + 30, cy + 6), fill=(50, 50, 60, 230), width=5)
        d.ellipse((cx - 5, cy - 9, cx + 5, cy + 1), fill=XIA + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def fan(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """范仲淹: thin scholar-official, 幞头 with medium wings, sparse beard; armour cloak in the frontier years."""
    b = bow + 12 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.06 * h, y - 1.04 * h, x + 0.06 * h, y - 0.94 * h), fill=255)
        d.rectangle((x - 0.2 * h, y - 1.0 * h, x + 0.2 * h, y - 0.985 * h), fill=255)
        d.line((x + dir * 0.03 * h, y - 0.86 * h, x + dir * 0.05 * h, y - 0.72 * h), fill=255, width=max(2, int(0.02 * h)))
        if old > 0.4:
            A.d['wash'].line((x + dir * 0.03 * h, y - 0.85 * h, x + dir * 0.05 * h, y - 0.74 * h), fill=255, width=max(2, int(0.015 * h)))
    return hand

def tower(A, cx, base, s, floors, glow=0.0, t=0.0):
    """岳阳楼: up to three storeys with upswept eaves."""
    y = base
    for k in range(min(3, floors)):
        w = s * (1 - k * 0.18)
        h = s * 0.32
        A.d['ink'].rectangle((cx - 0.42 * w, y - h, cx + 0.42 * w, y), fill=255)
        for j in range(4):
            A.d['wash'].rectangle((cx - 0.34 * w + j * 0.2 * w, y - 0.8 * h, cx - 0.26 * w + j * 0.2 * w, y - 0.2 * h), fill=200)
        A.d['ink'].polygon([(cx - 0.62 * w, y - h + 6), (cx - 0.5 * w, y - h - 0.22 * s), (cx + 0.5 * w, y - h - 0.22 * s), (cx + 0.62 * w, y - h + 6),
                            (cx + 0.45 * w, y - h - 0.06 * s), (cx - 0.45 * w, y - h - 0.06 * s)], fill=255)
        y -= h + 0.2 * s
    if floors >= 3:
        A.d['ink'].polygon([(cx - 0.1 * s, y + 0.04 * s), (cx + 0.1 * s, y + 0.04 * s), (cx, y - 0.12 * s)], fill=255)
    if glow > 0:
        for j in range(3):
            r = s * (0.8 + 0.3 * j) * glow
            A.d['xia'].ellipse((cx - r, base - 0.6 * s - r, cx + r, base - 0.6 * s + r), fill=int(40 * glow))

def porridge(A, cx, cy, s, cut=0.0):
    A.d['ink'].chord((cx - s, cy - 0.6 * s, cx + s, cy + 0.6 * s), 0, 180, fill=255)
    A.d['wash'].ellipse((cx - 0.9 * s, cy - 0.25 * s, cx + 0.9 * s, cy + 0.2 * s), fill=255)
    if cut > 0:
        A.d['ink'].line((cx - 0.9 * s * cut, cy - 0.02 * s, cx + 0.9 * s * cut, cy - 0.02 * s), fill=255, width=4)
        A.d['ink'].line((cx, cy - 0.22 * s * cut, cx, cy + 0.18 * s * cut), fill=255, width=4)

def geese(A, x, y, n, t, s=26):
    for k in range(n):
        gx = x - k * s * 1.3; gy = y + abs(k - n // 2) * s * 0.6
        A.d['ink'].line((gx - s, gy + 0.2 * s * math.sin(t * 6 + k), gx, gy - 0.2 * s, gx + s, gy + 0.2 * s * math.sin(t * 6 + k)), fill=255, width=4)

# ================================================================ chapter card
CH = {16: (1, 0.0), 48: (1, 0.0), 80: (2, 0.0), 112: (3, 0.0), 144: (3, 1.0)}
def art_tower_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    floors, glow = CH.get(kb, (1, 0.0))
    q = ease_out(u / (1.2 * P))
    A.d['dongting'].rectangle((60, 1160, W - 60, 1240), fill=130)
    waves(A, 1170, t, rows=2, amp=3, speed=0.8)
    tower(A, 540, 1160, 260 * (0.6 + 0.4 * q) if kb == 16 else 260, floors, glow=glow * q, t=t)
    geese(A, lerp(900, 700, (t * 0.1) % 1), 820, 5, t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_tower_chapter)
    ink_in(cv, text_img(no, SERIF, 56, DONGTING, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_f_hook_worry(A, cv, t, u):
    A.d['dongting'].rectangle((60, 1200, W - 60, GROUND), fill=140)
    waves(A, 1210, t, rows=3, amp=4)
    tower(A, 540, 1200, 240, 3, glow=ease_out(u / (1.6 * P)), t=t)

def art_f_hook_three(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        x = lerp(200 + k * 260, 260 + k * 260, ease_out((u - k * 0.3) / P))
        fan(A, x, GROUND, 180, dir=1, ph=t * 4, arm=-8)

def art_f_hook_bowl(A, cv, t, u):
    desk(A, 540, GROUND, 400, layer='dongting')
    porridge(A, 540, GROUND - 110, 120, cut=ease_out(u / (1.4 * P)))
    ground(A, GROUND)

def art_f_hook_yizhuang(A, cv, t, u):
    for k in range(int(clamp(u / (1.6 * P)) * 8) + 1):
        A.d['grass'].rectangle((120 + k * 110, GROUND - 60, 210 + k * 110, GROUND), fill=200)
    A.d['ink'].rectangle((360, 1080, 720, GROUND - 60), fill=255)
    A.d['ink'].polygon([(320, 1080), (760, 1080), (540, 980)], fill=255)
    ground(A, GROUND)

# ================================================================ 第一回 断齑画粥
def art_f_birth(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='徐州', layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('武宁军节度掌书记之子', 30), 860, 880, t, t - u + P, rot=6)

def art_f_remarry(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(200, 700, ease_out(u / (3 * P)))
    person(A, x, GROUND, 220, dir=1, robe=True, hat='knot', female=True, baby=True, ph=t * 3, layer='ink')
    A.d['mid'].rectangle((800, 1060, 1000, GROUND), fill=200)
    A.d['ink'].polygon([(780, 1060), (1020, 1060), (900, 980)], fill=255)
    A.flush(cv)
    stamp(cv, seal('朱家', 54), 900, 880, t, t - u + 2 * P, rot=6)
    paste(cv, text_img('两岁丧父 · 母改嫁朱氏', SERIF, 46, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_f_porridge(A, cv, t, u):
    """6-beat set piece: 断齑画粥 — in a temple at night he cooks millet, lets it set, cuts it into four; eats two at dawn
    and two at dusk with chopped pickles."""
    ph = u / P
    for k in range(30):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    palace(A, 800, GROUND, 300, layer='mid')
    desk(A, 460, GROUND, 400, layer='dongting')
    porridge(A, 460, GROUND - 110, 110, cut=ease_out((ph - 1.5) / 1.5))
    sitter(A, 220, GROUND, 180, dir=1, bow=lerp(10, 30, 0.5 + 0.5 * math.sin(t * 2)))
    lamp(A, 680, GROUND - 70, 40, t, glow=0.5)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('醴泉寺', 46), 860, 860, t, t - u + 0.4, rot=6)
    if ph >= 3.5:
        paste(cv, text_img('早晚各取二块 · 断齑数茎', SERIF, 44, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 3.5) / 0.4))

def art_f_origin(A, cv, t, u):
    ground(A, GROUND)
    person(A, 700, GROUND, 200, dir=-1, robe=True, hat='knot', female=True, arm=lerp(60, 150, ease_out((u - P) / 0.5)), layer='ink')
    x = lerp(400, 100, ease_out((u - 1.8 * P) / P))
    fan(A, x, GROUND, 200, dir=-1 if u > 1.8 * P else 1, ph=t * 5 if u > 1.8 * P else None, arm=-8)
    A.flush(cv)
    paste(cv, text_img('得知身世 · 泣辞母亲', SERIF, 46, XIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_f_yingtian(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='dongting')
    ground(A, GROUND)
    for k in range(5):
        sitter(A, 200 + k * 160, GROUND, 120, dir=1, bow=15, layer='ink' if k == 2 else 'mid')
    lamp(A, 540, GROUND, 40, t, glow=0.6)
    A.flush(cv)
    stamp(cv, seal('应天书院', 44), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('五年未尝解衣就枕', SERIF, 46, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_f_jinshi(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='xia')
    ground(A, GROUND)
    fan(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 30, ease_out(u / 0.6)))
    A.d['yellow'].rectangle((240, 860, 840, 920), fill=255)
    A.flush(cv)
    stamp(cv, seal('进士', 56), 860, 980, t, t - u + P, rot=6)

def art_f_mother(A, cv, t, u):
    A.d['mid'].rectangle((300, 1060, 780, GROUND), fill=200)
    A.d['ink'].polygon([(270, 1060), (810, 1060), (540, 960)], fill=255)
    ground(A, GROUND)
    person(A, 460, GROUND, 190, dir=1, robe=True, hat='knot', female=True, arm=40, layer='ink')
    fan(A, 640, GROUND, 210, dir=-1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('复姓范', 50), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('迎母奉养 · 复姓归宗', SERIF, 46, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 此行极光
def art_f_seawall(A, cv, t, u):
    """6-beat set piece: 范公堤 — the tide floods the salt fields; workers pile up a dyke mile by mile; the sea is held back."""
    ph = u / P
    lvl = lerp(1180, 1260, ease_out((ph - 3) / 2))
    A.d['dongting'].rectangle((60, lvl, W - 60, GROUND + 40), fill=170)
    waves(A, lvl + 6, t, rows=4, amp=10, speed=3)
    p = ease_out(ph / 4.5)
    A.d['mid'].polygon([(60, 1250), (60 + (W - 120) * p, 1230), (60 + (W - 120) * p, 1290), (60, 1310)], fill=240)
    for k in range(6):
        x = (t * 90 + k * 170) % (W + 200) - 100
        person(A, x, 1230, 90, dir=1, robe=False, hat='knot', load=True, ph=t * 7 + k, arm=160, layer='ink')
    A.flush(cv)
    stamp(cv, seal('泰州', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('修捍海堰 · 后人称范公堤' if ph >= 4.5 else '海潮倒灌 盐场被毁', SERIF, 46, DONGTING if ph >= 4.5 else XIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_f_teach(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='mid')
    ground(A, GROUND)
    fan(A, 540, GROUND, 230, dir=1, arm=lerp(40, 110, 0.5 + 0.5 * math.sin(t * 2)))
    for k in range(6):
        sitter(A, 160 + k * 60 if k < 3 else 760 + (k - 3) * 70, GROUND, 100, dir=1 if k < 3 else -1, bow=15, layer='mid')
    A.flush(cv)
    stamp(cv, seal('母丧', 50, INK), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('守丧期间 主持应天书院', SERIF, 46, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_f_taihou(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='xia')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', female=True, arm=lerp(20, 120, ease_out((u - P) / 0.5)), layer='ink')
    fan(A, 340, GROUND, 220, dir=1, kneel=True, bow=20, arm=110)
    A.flush(cv)
    stamp(cv, seal('刘太后', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('上书请太后还政', SERIF, 46, XIA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_f_suzhou(A, cv, t, u):
    A.d['dongting'].rectangle((60, 1200, W - 60, GROUND), fill=150)
    waves(A, 1210, t, rows=3, amp=4, speed=1.6)
    p = ease_out(u / (2.5 * P))
    for k in range(5):
        x = 160 + k * 190
        A.d['mid'].rectangle((x - 20, 1200 - 120 * p, x + 20, 1200), fill=230)
    fan(A, 860, 1200, 160, dir=-1, arm=60)
    ground(A, 1200, x0=760, x1=W - 60)
    A.flush(cv)
    stamp(cv, seal('苏州', 54), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('疏浚太湖 · 导水入海', SERIF, 46, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_f_kaifeng(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='开封', layer='mid', open_=1.0)
    ground(A, GROUND)
    fan(A, 540, GROUND, 210, dir=1, arm=60)
    for k in range(6):
        person(A, 160 + k * 60 if k < 3 else 760 + (k - 3) * 70, GROUND, 140, dir=1 if k < 3 else -1, robe=True, hat='knot', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='mid')
    A.flush(cv)
    paste(cv, text_img('朝廷无忧有范君', SERIF, 48, DONGTING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

EXILES = [(1029, '河中府', '此行极光'), (1033, '睦州', '此行愈光'), (1036, '饶州', '此行尤光')]
def scene_sanguang(cv, t, c, k):
    """8-beat custom scene: 三光 — three times he speaks out and is sent away; each time friends see him off with
    one more word of praise (极光 · 愈光 · 尤光); his road on the map lengthens each time."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    i = min(2, int(ph / 2.4))
    A.d['wash'].rounded_rectangle((110, 780, 970, 1420), radius=24, fill=180)
    pts = [(880, 900), (620, 980), (820, 1240), (420, 1320)]
    for j in range(i + 1):
        f = clamp((ph - j * 2.4) / 1.6)
        (x0, y0), (x1, y1) = pts[0], pts[j + 1]
        A.d['dongting'].line((x0, y0, lerp(x0, x1, f), lerp(y0, y1, f)), fill=230, width=8)
        if f > 0.1:
            fan(A, lerp(x0, x1, f), lerp(y0, y1, f) + 10, 80, dir=-1, ph=t * 4, arm=-8)
    A.d['ink'].rectangle((860, 870, 900, 900), fill=255)
    A.flush(cv)
    stamp(cv, seal('开封', 32, INK), 880, 840, t, s0)
    for j in range(i + 1):
        yr, nm, w_ = EXILES[j]
        stamp(cv, seal(nm, 32, XIA), pts[j + 1][0], pts[j + 1][1] - 60, t, s0 + (j * 2.4 + 1.2) * P)
    fx = Art()
    chars_in(cv, fx, '三次被贬', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=72)
    fx.flush(cv)
    yr, nm, w_ = EXILES[i]
    paste(cv, text_img(f'公元{cn_year(yr)}年 · 贬{nm}', SERIF, 44, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    for j in range(i + 1):
        ink_in(cv, text_img(EXILES[j][2], BRUSH, 70, ZHU if j == i else DIM), 260 + j * 280, 1460, t, s0 + (j * 2.4 + 1.6) * P, dur=0.3)

# ================================================================ 第三回 军中有一范
def art_f_xixia(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        rider(A, lerp(1200, 500, ease_out(u / (2.5 * P))) + (k % 5) * 90, GROUND - (k // 5) * 40, 110, -1, t * 11 + k, layer='ink', spear=True)
    flames(A, 200, GROUND, 240, 200 * ease_out((u - P) / 0.8), t, n=5, seed=3, smoke=True)
    A.flush(cv)
    stamp(cv, seal('西夏', 54, INK), 860, 860, t, t - u + 0.4, rot=6)
    paste(cv, text_img('宋军三川口大败', SERIF, 48, XIA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_f_yanzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='延州', layer='mid', open_=1.0)
    ground(A, GROUND)
    fan(A, lerp(-80, 540, ease_out(u / (2 * P))), GROUND, 220, dir=1, ph=t * 4 if u < 2 * P else None, arm=40)
    A.flush(cv)
    stamp(cv, seal('经略副使', 44), 860, 860, t, t - u + P, rot=6)
    paste(cv, text_img('年过半百 · 文官守边', SERIF, 46, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_f_forts(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=200)
    n = int(clamp(u / (2.5 * P)) * 6) + 1
    for k in range(n):
        x = 140 + k * 160; y = GROUND - 160 - 40 * math.sin(k)
        A.d['ink'].rectangle((x - 40, y - 60, x + 40, y), fill=255)
        for j in range(4):
            A.d['ink'].rectangle((x - 40 + j * 22, y - 76, x - 28 + j * 22, y - 60), fill=255)
    for k in range(4):
        person(A, 180 + k * 220, GROUND, 100, dir=1, robe=False, hat='knot', arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img(f'筑城修寨 · 第{cn_num(n)}座', SERIF, 46, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_f_chant(A, cv, t, u):
    ground(A, GROUND)
    for k in range(12):
        person(A, 120 + (k % 6) * 150, GROUND - (k // 6) * 50, 120, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink' if k // 6 == 0 else 'mid')
    fan(A, 900, GROUND, 230, dir=-1, arm=60)
    A.flush(cv)
    type_in(cv, text_img('军中有一范', SERIF, 52, DONGTING, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('西贼闻之惊破胆', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 905, t, t - u + 1.5 * P, 0.5)
    stamp(cv, seal('边地民谣', 40, INK), 860, 1060, t, t - u + 0.4, rot=6)

def art_f_recall(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='xia')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 100, ease_out(u / 0.6)), layer='ink')
    fan(A, 360, GROUND, 230, dir=1, kneel=True, bow=30, arm=110)
    A.flush(cv)
    stamp(cv, seal('参知政事', 44), 260, 880, t, t - u + P, rot=-5)

TEN = ['明黜陟', '抑侥幸', '精贡举', '择官长', '均公田', '厚农桑', '修武备', '减徭役', '覃恩信', '重命令']
def art_f_qingli(A, cv, t, u):
    """8-beat set piece: 庆历新政 — 答手诏条陈十事: ten seals appear in two rows, the emperor approves; a stamp of 新政."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 560, layer='dongting')
    fan(A, 200, GROUND, 210, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)))
    person(A, 880, GROUND - 20, 210, dir=-1, robe=True, hat='crown', arm=lerp(20, 100, ease_out((ph - 6) / 0.6)), layer='ink')
    A.flush(cv)
    n = min(10, int(ph * 10 / 5.5) + 1)
    for i in range(n):
        x = 220 + (i % 5) * 160; y = 860 + (i // 5) * 110
        stamp(cv, seal(TEN[i], 30, ZHU if i < 2 else DONGTING), x, y, t, t - u + i * 0.55 * P)
    if ph >= 6:
        stamp(cv, seal('庆历新政', 50), 540, 1100, t, t - u + 6 * P)

def art_f_onefamily(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='xia')
    fan(A, 360, GROUND, 220, dir=1, arm=lerp(40, 160, ease_out((u - 0.3 * P) / 0.4)))
    brush(A, 520, GROUND - 160, 110, ang=-1.1)
    A.flush(cv)
    type_in(cv, text_img('一家哭 何如一路哭', SERIF, 50, XIA, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)

# ================================================================ 第四回 先忧后乐
def art_f_fail(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    for k in range(6):
        person(A, 140 + k * 60 if k < 3 else 780 + (k - 3) * 60, GROUND, 150, dir=1 if k < 3 else -1, robe=True, hat='none', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='ink')
    fan(A, lerp(540, 540, 1), GROUND, 210, dir=1, arm=-8)
    A.flush(cv)
    stamp(cv, seal('朋党', 54, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('新政仅一年余 · 黯然罢去', SERIF, 44, XIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_f_dengzhou(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 260), (x + 200, GROUND)], fill=160)
    ground(A, GROUND)
    x = lerp(-80, 540, ease_out(u / (2 * P)))
    donkey(A, x, GROUND, 140, dir=1, ph=t * 6)
    fan(A, x - 10, GROUND - 80, 130, dir=1, arm=20, old=0.5)
    A.flush(cv)
    stamp(cv, seal('邓州', 54), 860, 1020, t, t - u + P, rot=6)

def art_f_yueyang(A, cv, t, u):
    """8-beat set piece: 岳阳楼记 — a friend's letter and a painting of the tower; he writes; the lake changes from
    gloomy rain to bright spring; the famous line lands in red."""
    ph = u / P
    if ph < 2.5:
        ground(A, GROUND)
        desk(A, 540, GROUND, 420, layer='dongting')
        scroll(A, 540, 1000, 360, 200, ph / 0.8, layer='wash')
        tower(A, 540, 1060, 90, 3)
        sitter(A, 260, GROUND, 200, dir=1, bow=20)
    else:
        bright = ease_out((ph - 4.5) / 1)
        A.d['dongting'].rectangle((60, 1180, W - 60, GROUND + 40), fill=int(lerp(110, 170, bright)))
        waves(A, 1190, t, rows=4, amp=int(lerp(12, 3, bright)), speed=lerp(3, 0.8, bright))
        tower(A, 300, 1180, 220, 3, glow=bright, t=t)
        if bright < 0.5:
            for k in range(50):
                q = (t * 1.0 + k / 50) % 1
                A.d['wash'].line((80 + (k * 17) % 920, lerp(620, 1420, q), 76 + (k * 17) % 920, lerp(620, 1420, q) + 22), fill=int(180 * (1 - bright * 2)), width=2)
        else:
            geese(A, lerp(980, 700, (t * 0.1) % 1), 840, 5, t)
            sun(cv, 820, 900, 70, XIA, int(150 * bright))
    A.flush(cv)
    stamp(cv, seal('滕子京', 46, INK), 860, 1020, t, t - u + 0.4, rot=6)
    if 2.5 <= ph < 4.5:
        paste(cv, text_img('阴风怒号 浊浪排空', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - 2.5) / 0.3))
    if ph >= 4.5:
        type_in(cv, text_img('先天下之忧而忧', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 820, t, t - u + 4.5 * P, 0.5)
        type_in(cv, text_img('后天下之乐而乐', SERIF, 52, DONGTING, 'Black', bleed=False, spacing=8), W / 2, 895, t, t - u + 5.5 * P, 0.5)

def art_f_huazhou(A, cv, t, u):
    A.d['dongting'].ellipse((200, 1240, 880, 1360), fill=140)
    for k in range(6):
        x = 280 + k * 100
        A.d['grass'].ellipse((x - 30, 1280, x + 30, 1300), fill=220)
        A.d['apricot'].polygon([(x, 1250), (x - 12, 1280), (x + 12, 1280)], fill=230)
    palace(A, 760, 1240, 260, layer='mid')
    fan(A, 300, 1240, 180, dir=1, arm=60, old=0.5)
    ground(A, 1240, x0=60, x1=200)
    A.flush(cv)
    stamp(cv, seal('花洲书院', 44), 860, 1020, t, t - u + P, rot=6)

def art_f_hangzhou(A, cv, t, u):
    A.d['dongting'].rectangle((60, 1200, W - 60, GROUND), fill=150)
    waves(A, 1210, t, rows=3, amp=5, speed=2)
    for k in range(3):
        boat(A, lerp(-200, 1200, ((t * 0.12 + k * 0.33) % 1)), 1260 + k * 30, 100, t + k, sail=False)
    for k in range(5):
        A.d['mid'].rectangle((140 + k * 180, 1080, 220 + k * 180, 1200), fill=220)
    A.flush(cv)
    stamp(cv, seal('杭州', 54), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('灾年兴工 · 竞渡游湖 · 以工代赈', SERIF, 42, DONGTING, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_f_yizhuang(A, cv, t, u):
    ph = u / P
    for k in range(int(clamp(ph / 3) * 8) + 1):
        A.d['grass'].rectangle((120 + k * 110, GROUND - 60, 210 + k * 110, GROUND), fill=200)
    A.d['ink'].rectangle((360, 1080, 720, GROUND - 60), fill=255)
    A.d['ink'].polygon([(320, 1080), (760, 1080), (540, 980)], fill=255)
    for k in range(int(clamp((ph - 2) / 3) * 8)):
        person(A, 160 + k * 100, GROUND, 110, dir=1, robe=True, hat='knot', female=k % 3 == 0, arm=40, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('范氏义庄', 46), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('置田千亩 · 赡养全族贫者', SERIF, 44, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 第一流人物
def art_f_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    fan(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('徐州', 54), 300, 880, t, t - u + P, rot=-5)
    paste(cv, text_img('赴任途中病逝 · 家无余财', SERIF, 44, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_f_wenzheng(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 220, dir=1, robe=True, hat='crown', bow=20, arm=60, layer='ink')
    A.flush(cv)
    ink_in(cv, text_img('文正', BRUSH, 140, ZHU), W / 2, 900, t, t - u + 0.5, dur=0.3, settle=1.2)
    paste(cv, text_img('仁宗亲书碑额 · 褒贤之碑', SERIF, 44, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_f_sons(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        person(A, 240 + k * 200, GROUND, 200 - k * 10, dir=1, robe=True, hat='none', arm=40, layer='ink' if k == 1 else 'mid')
    A.flush(cv)
    stamp(cv, seal('范纯仁', 46), 440, 1000, t, t - u + P)
    paste(cv, text_img('次子官至宰相 · 人称布衣宰相', SERIF, 44, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_f_zhuxi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='xia')
    sitter(A, 300, GROUND, 220, dir=1, bow=15)
    A.flush(cv)
    stamp(cv, seal('朱熹', 54, INK), 860, 880, t, t - u + 0.4, rot=6)
    type_in(cv, text_img('天地间气 第一流人物', SERIF, 50, XIA, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + P, 0.5)

def art_f_800(A, cv, t, u):
    ground(A, GROUND)
    n = min(32, int(clamp(u / (2.5 * P)) * 32) + 1)
    for i in range(n):
        x = 120 + (i % 16) * 56; y = GROUND - 30 - (i // 16) * 70
        A.d['grass' if i % 4 else 'dongting'].rectangle((x - 20, y - 40, x + 20, y), fill=230)
    A.flush(cv)
    paste(cv, text_img('义庄延续八百余年', SERIF, 50, DONGTING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_f_today(A, cv, t, u):
    A.d['dongting'].rectangle((60, 1200, W - 60, GROUND), fill=150)
    waves(A, 1210, t, rows=3, amp=4)
    tower(A, 540, 1200, 260, 3, glow=1.0, t=t)
    for k in range(6):
        person(A, 160 + k * 60 if k < 3 else 760 + (k - 3) * 60, 1200, 90, dir=1 if k < 3 else -1, robe=False, hat='knot', arm=60, layer='mid')
    A.flush(cv)
    paste(cv, text_img('千年后 人们仍登楼诵读', SERIF, 46, DONGTING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_f_legacy(A, cv, t, u):
    A.d['dongting'].rectangle((60, 1300, W - 60, GROUND), fill=150)
    tower(A, 860, 1300, 160, 3, glow=1.0, t=t)

def art_f_title(A, cv, t, u):
    tower(A, 820, 1460, 220, 3)
    fan(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))


# ================================================================ script
CHAPTERS = {16: ('第一回', '断齑画粥'), 48: ('第二回', '此行极光'), 80: ('第三回', '军中有范'),
            112: ('第四回', '先忧后乐'), 144: ('第五回', '第一流人')}

CARDS = [
    C(0, 2, 'hook', 'num', num='先忧后乐', line='写进了课本', art=art_f_hook_worry),
    C(2, 4, 'night', 'num', num='三次被贬', line='越贬越光荣', art=art_f_hook_three),
    C(4, 6, 'life', 'num', num='一碗冷粥', line='切成四块吃一天', art=art_f_hook_bowl),
    C(6, 8, 'works', 'num', num='一座义庄', line='养活族人八百年', art=art_f_hook_yizhuang),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 断齑画粥
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=989, main='生于徐州', sub='祖籍苏州吴县', art=art_f_birth),
    C(22, 26, 'death', 'card', year=990, main='母亲改嫁', sub='随继父改名朱说', art=art_f_remarry),
    C(26, 32, 'works', 'card', year=1006, main='断齑画粥', sub='寺中苦读', note='一说 在长白山醴泉寺', art=art_f_porridge),
    C(32, 36, 'night', 'card', year=1011, main='知晓身世', sub='发誓自立门户', art=art_f_origin),
    C(36, 40, 'works', 'card', year=1011, main='应天书院', sub='昼夜苦读', art=art_f_yingtian),
    C(40, 44, 'empire', 'card', year=1015, main='进士及第', sub='二十五岁 · 金榜题名', art=art_f_jinshi),
    C(44, 48, 'life', 'card', year=1017, main='复姓归宗', sub='迎母奉养', note='复姓之年 一说', art=art_f_mother),
    # ---- 第二回 此行极光
    C(48, 50, 'night', 'chapter'),
    C(50, 56, 'works', 'card', year=1024, main='范公堤', sub='主持修复捍海堰', art=art_f_seawall),
    C(56, 60, 'life', 'card', year=1027, main='执掌书院', sub='应天书院 · 以身作则', art=art_f_teach),
    C(60, 64, 'court', 'card', year=1029, main='谏太后', sub='秘阁校理 · 直言犯上', art=art_f_taihou),
    C(64, 68, 'works', 'card', year=1034, main='苏州治水', sub='兴修水利', art=art_f_suzhou),
    C(68, 72, 'court', 'card', year=1035, main='知开封府', sub='京师肃然', art=art_f_kaifeng),
    C(72, 80, 'night', 'sanguang', year=1036),
    # ---- 第三回 军中有范
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'war', 'card', year=1040, main='西夏犯边', sub='李元昊称帝 · 宋军连败', art=art_f_xixia),
    C(86, 90, 'war', 'card', year=1040, main='镇守延州', sub='陕西经略安抚副使', art=art_f_yanzhou),
    C(90, 94, 'works', 'card', year=1041, main='筑城屯田', sub='积极防御', art=art_f_forts),
    C(94, 98, 'war', 'card', year=1042, main='军中有一范', sub='西夏不敢轻犯', art=art_f_chant),
    C(98, 102, 'empire', 'card', year=1043, main='参知政事', sub='奉召回朝', art=art_f_recall),
    C(102, 110, 'works', 'card', year=1043, main='庆历新政', sub='答手诏条陈十事', art=art_f_qingli),
    C(110, 112, 'night', 'card', year=1043, main='一路哭', sub='罢免庸官', art=art_f_onefamily),
    # ---- 第四回 先忧后乐
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'night', 'card', year=1045, main='新政失败', sub='朋党之议四起', art=art_f_fail),
    C(118, 122, 'fate', 'card', year=1045, main='知邓州', sub='自请外放', art=art_f_dengzhou),
    C(122, 130, 'fate', 'card', year=1046, main='岳阳楼记', sub='应滕子京之请', note='他未到过岳阳楼 依画作记', art=art_f_yueyang),
    C(130, 134, 'life', 'card', year=1047, main='花洲书院', sub='邓州兴学', art=art_f_huazhou),
    C(134, 138, 'works', 'card', year=1049, main='杭州赈灾', sub='别出心裁', art=art_f_hangzhou),
    C(138, 144, 'empire', 'card', year=1050, main='义庄', sub='苏州置田 · 中国第一个义庄', art=art_f_yizhuang),
    # ---- 第五回 第一流人
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'death', 'card', year=1052, main='病逝', sub='年六十二', art=art_f_death),
    C(150, 154, 'court', 'card', year=1052, main='谥文正', sub='文臣最高谥号', art=art_f_wenzheng),
    C(154, 158, 'life', 'card', year=1086, main='家风', sub='四子皆有贤名', art=art_f_sons),
    C(158, 162, 'works', 'card', year=1180, main='第一流人物', sub='南宋朱熹评价', art=art_f_zhuxi),
    C(162, 166, 'empire', 'card', year=1911, main='八百年', sub='义庄直到清末仍在', art=art_f_800),
    C(166, 170, 'end', 'card', year=2026, main='岳阳楼', sub='先忧后乐 · 千古传诵', art=art_f_today),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='叁拾捌', col=DONGTING, acc=XIA, born=989, died=1052, age0=989.7,
    hook_q='三次被贬 · 他为什么越贬越被敬重？',
    name_line='范仲淹 · 字希文', name='范仲淹', seal='文正', title_art=art_f_title,
    q1='完人？', q2='书生空想？',
    end_art=art_f_legacy, end_big='先忧后乐', end_seal='文正',
    end_l1='他的改革失败了', end_l2='可他的那句话 成了中国读书人的脊梁',
    end_brush='先天下之忧而忧', end_ask='你做得到吗？评论区聊聊', next='玄奘'),
    scenes=dict(chapter=scene_chapter, sanguang=scene_sanguang))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
