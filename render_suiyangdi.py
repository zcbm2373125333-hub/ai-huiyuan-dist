"""千古人物志 · 第肆拾肆集 · 隋炀帝 (569–618)
Look: 运河碧 + 龙舟金, 柳枝 corner borders (he planted willows along the canal), a 大运河 chapter card: the canal is dug
a section further each chapter; in the last a dragon boat sinks.
Set pieces: 6-beat 平陈, custom 8-beat scene 'yunhe' (大运河 map), 6-beat 龙舟下扬州, 8-beat 三征高句丽,
6-beat 江都兵变.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_tangxuanzong as Tx     # engine + helpers (previous episode)
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
from render_quyuan import river
from render_kongzi import bundle
from render_weizheng import bronze_mirror

F.RIPPLE = False
CANAL = (52, 124, 116)              # 运河碧
DRAGON = (212, 160, 48)             # 龙舟金
S.LAYERS.append(('canal', CANAL, 0.88, 1.0))
S.LAYERS.append(('dragon', DRAGON, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='隋', life='广', court='隋', night='乱', war='征', empire='隋', works='河', fate='游', death='亡', end='河')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court', 'empire'):
    G.THEMES[k]['part'] = 'petal'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (DRAGON, 240, (W * 0.5, 820))
G.THEMES['war']['sun'] = (ZHU, 220, (W * 0.5, 760))
G.THEMES['end']['sun'] = (CANAL, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

WILLOW = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(WILLOW)
for _x in (90, 990):
    _d.line((_x, 1490, _x + 6, 1240), fill=(80, 70, 50, 60), width=8)
    for _k in range(10):
        _a = -0.8 + _k * 0.18
        _px = _x + 100 * math.sin(_a)
        _d.line((_x + 6, 1250, _px, 1250 + 160 + 30 * math.cos(_k)), fill=CANAL + (50,), width=3)
MTN_COL = {'night': (34, 40, 40), 'death': (60, 62, 62), 'war': (104, 66, 50), 'fate': (80, 100, 96)}
def draw_background(t, theme):
    """江淮: flat ridges, weeping willows at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 192, 186), (144, 162, 156), MTN_COL.get(theme, (104, 126, 120))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(WILLOW)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """柳枝: drooping willow strands in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=DRAGON + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=DRAGON + (220,), width=3)
        for k in range(5):
            x0 = x + sx * (20 + k * 22)
            pts = [(x0 + sx * 6 * math.sin(f * 3), y + sy * (6 + f * (60 + k * 10))) for f in np.linspace(0, 1, 8)]
            d.line(pts, fill=CANAL + (230,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def guang(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, crown=True, armour=False, **kw):
    """杨广: handsome, 冕旒 when emperor; armour as a prince-general."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hat = ('helmet' if armour else ('crown' if crown else 'none')) if up else 'knot'
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat=hat, layer=layer, kneel=kneel, bow=bow, **kw)
    if up:
        A.d['dragon'].rectangle((x - 0.1 * h, y - 0.58 * h, x + 0.1 * h, y - 0.52 * h), fill=255)
        A.d[layer].line((x + dir * 0.03 * h, y - 0.86 * h, x + dir * 0.06 * h, y - 0.78 * h), fill=255, width=max(2, int(0.015 * h)))
    return hand

def dragon_boat_big(A, x, y, s, t, sink=0.0):
    yy = y + sink * 0.8 * s
    A.d['dragon'].polygon([(x - s, yy - 0.15 * s), (x + s, yy - 0.15 * s), (x + 0.85 * s, yy + 0.08 * s), (x - 0.85 * s, yy + 0.08 * s)], fill=255)
    A.d['dragon'].polygon([(x + s, yy - 0.15 * s), (x + 1.2 * s, yy - 0.5 * s), (x + 1.3 * s, yy - 0.42 * s), (x + 1.08 * s, yy - 0.12 * s)], fill=255)
    for k in range(4):
        w = 0.7 * s * (1 - k * 0.2); hh = 0.16 * s
        top = yy - 0.15 * s - (k + 1) * hh
        A.d['ink'].rectangle((x - w, top, x + w, top + hh - 4), fill=255 if k % 2 == 0 else 200)
        A.d['red'].rectangle((x - w - 6, top - 4, x + w + 6, top + 2), fill=255)

def canal_map(A, p, t):
    pts = [(260, 820), (440, 880), (560, 1000), (600, 1120), (640, 1260), (720, 1380)]
    A.d['wash'].rounded_rectangle((110, 760, 970, 1420), radius=24, fill=170)
    A.d['ocean'].line([(140, 900), (500, 980), (960, 940)], fill=140, width=16)
    A.d['ocean'].line([(140, 1240), (500, 1220), (960, 1260)], fill=140, width=16)
    n = len(pts) - 1
    m = p * n
    for i in range(n):
        f = clamp(m - i)
        if f <= 0: break
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        A.d['canal'].line((x0, y0, lerp(x0, x1, f), lerp(y0, y1, f)), fill=255, width=14)
    return pts

# ================================================================ chapter card
CH = {16: 0.15, 48: 0.35, 80: 0.7, 112: 1.0, 144: 1.0}
def art_canal_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    p = CH.get(kb, 0.35)
    prev = {48: 0.15, 80: 0.35, 112: 0.7, 144: 1.0}.get(kb, 0)
    q = ease_out(u / (1.2 * P))
    pts = canal_map(A, lerp(prev, p, q), t)
    if kb == 144:
        dragon_boat_big(A, 600, 1120, 80, t, sink=q)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_canal_chapter)
    ink_in(cv, text_img(no, SERIF, 56, CANAL, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_s_hook_canal(A, cv, t, u):
    canal_map(A, ease_out(u / (1.6 * P)), t)

def art_s_hook_3(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        x = lerp(-200, 300 + k * 260, ease_out((u - k * 0.2) / (1.6 * P)))
        for j in range(4):
            person(A, x - j * 40, GROUND, 90, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + j, arm=40, layer='ink')

def art_s_hook_boat(A, cv, t, u):
    river(A, 1220, t, rows=3, amp=4, speed=1)
    dragon_boat_big(A, lerp(200, 540, ease_out(u / (1.6 * P))), 1260, 220, t)

def art_s_hook_head(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='mid')
    ground(A, GROUND)
    guang(A, 540, GROUND, 260, dir=1, arm=40)
    A.flush(cv)

# ================================================================ 第一回 晋王
def art_s_birth(A, cv, t, u):
    palace(A, 540, GROUND, 560, layer='dragon')
    ground(A, GROUND)
    person(A, 420, GROUND, 240, dir=1, robe=True, hat='crown', arm=40, layer='ink')
    person(A, 640, GROUND, 220, dir=-1, robe=True, hat='crown', female=True, baby=True, layer='ink')
    A.flush(cv)
    stamp(cv, seal('杨坚 独孤后', 36), 860, 1020, t, t - u + P, rot=6)

def art_s_jinwang(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='mid')
    ground(A, GROUND)
    guang(A, 540, GROUND, 160, dir=1, crown=False, arm=40)
    A.flush(cv)
    stamp(cv, seal('晋王', 60), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('十三岁 封晋王 镇并州', SERIF, 46, CANAL, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_frugal(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        A.d['ink'].line((640 + k * 80, GROUND, 640 + k * 80, GROUND - 200), fill=255, width=4)
        A.d['mid'].polygon([(620 + k * 80, GROUND - 200), (660 + k * 80, GROUND - 200), (670 + k * 80, GROUND - 120), (610 + k * 80, GROUND - 120)], fill=200)
    guang(A, 340, GROUND, 230, dir=1, crown=False, arm=-8)
    A.flush(cv)
    paste(cv, text_img('乐器断弦 积满灰尘', SERIF, 46, CANAL, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('伪装节俭', 44, INK), 860, 1040, t, t - u + P, rot=6)

def art_s_chen(A, cv, t, u):
    """6-beat: 平陈 — he leads the southern campaign; boats cross the Yangtze; 建康 falls; the last 陈 emperor is
    pulled from a well."""
    ph = u / P
    river(A, 1200, t, rows=4, amp=6, speed=1.6)
    for k in range(8):
        boat(A, lerp(-200, 300 + (k % 4) * 160, ease_out((ph - k * 0.1) / 2.5)), 1240 + (k // 4) * 40, 70, t + k, sail=True)
    city_wall(A, 640, 1020, 1100, gate_x=830, label='建康', layer='mid', open_=ease_out((ph - 3) / 1))
    if ph >= 4:
        A.d['ink'].ellipse((870, 1150, 950, 1190), outline=255, width=6)
        person(A, 910, 1170 - 60 * ease_out((ph - 4.5) / 1), 80, dir=1, robe=True, hat='crown', arm=150, layer='ink')
    guang(A, 160, 1200, 160, dir=1, armour=True, arm=lerp(60, 160, ease_out(ph / 1.5)))
    A.flush(cv)
    stamp(cv, seal('平陈', 56), 540, 880, t, t - u + 0.4)
    paste(cv, text_img('二十岁 统帅五十万大军', SERIF, 44, CANAL, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(ph / 0.4))

def art_s_yangzhou(A, cv, t, u):
    A.d['canal'].rectangle((60, 1240, W - 60, GROUND), fill=150)
    waves(A, 1250, t, rows=2, amp=3, speed=0.8)
    city_wall(A, 240, 840, 1080, gate_x=540, label='扬州', layer='mid', open_=1.0)
    guang(A, 540, 1080, 160, dir=1, crown=False, arm=60)
    A.flush(cv)
    stamp(cv, seal('扬州总管', 44), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('镇守江南十年', SERIF, 46, CANAL, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_taizi(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='dragon')
    ground(A, GROUND)
    person(A, 760, GROUND, 220, dir=-1, robe=True, hat='crown', arm=-8, ph=t * 2, layer='mid')
    guang(A, 340, GROUND, 230, dir=1, crown=False, arm=lerp(40, 120, ease_out(u / P)))
    A.flush(cv)
    stamp(cv, seal('废太子杨勇', 40, INK), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('夺嫡成功 · 立为太子', SERIF, 46, DRAGON, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_s_renshou(A, cv, t, u):
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    palace(A, 540, GROUND, 600, layer='mid')
    A.d['mid'].rectangle((360, 1240, 720, 1290), fill=230)
    person(A, 540, 1240, 180, dir=1, robe=True, hat='crown', fall=-88, arm=-8, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('仁寿宫', 50, INK), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('文帝驾崩 · 死因成谜', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))
    stamp(cv, seal('一说弑父', 38, INK), 260, 1040, t, t - u + 1.5 * P, rot=-5)

# ================================================================ 第二回 大业
def art_s_crown(A, cv, t, u):
    palace(A, 540, 1140, 600, layer='dragon')
    ground(A, GROUND)
    guang(A, 540, GROUND, 250, dir=1, arm=lerp(-8, 150, ease_out(u / P)))
    for k in range(6):
        person(A, 120 + k * 60 if k < 3 else 800 + (k - 3) * 60, GROUND, 130, dir=1 if k < 3 else -1, robe=True, hat='none', kneel=True, bow=50, arm=100, layer='mid')
    A.flush(cv)
    stamp(cv, seal('大业', 60), 860, 1020, t, t - u + P, rot=6)

def art_s_luoyang(A, cv, t, u):
    ground(A, GROUND)
    p = ease_out(u / (2.5 * P))
    for k in range(5):
        x = 160 + k * 190
        h = 300 * clamp(p * 1.4 - k * 0.1)
        A.d['dragon'].rectangle((x - 70, GROUND - h, x + 70, GROUND), fill=220)
        A.d['ink'].polygon([(x - 90, GROUND - h), (x + 90, GROUND - h), (x, GROUND - h - 50)], fill=255)
    for k in range(6):
        person(A, (t * 80 + k * 170) % (W + 200) - 100, GROUND, 80, dir=1, robe=False, hat='knot', load=True, ph=t * 6 + k, arm=160, layer='ink')
    A.flush(cv)
    stamp(cv, seal('营建东都', 46), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('每月役丁二百万', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

YH = [(0, '通济渠', '洛阳至淮河'), (2, '邗沟', '淮河至长江'), (4, '永济渠', '北至涿郡'), (6, '江南河', '南至余杭')]
def scene_yunhe(cv, t, c, k):
    """8-beat custom scene: 大运河 — four sections dug in turn on the map; laborers; total length counts to 二千七百公里."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['wash'].rounded_rectangle((110, 760, 970, 1420), radius=24, fill=170)
    A.d['ocean'].line([(140, 950), (960, 980)], fill=140, width=14)
    A.d['ocean'].line([(140, 1230), (960, 1250)], fill=140, width=14)
    segs = [[(500, 970), (640, 1060), (720, 1150)], [(720, 1150), (740, 1240)], [(500, 970), (420, 860), (360, 790)], [(740, 1240), (800, 1320), (860, 1390)]]
    for i, seg in enumerate(segs):
        f = clamp((ph - i * 2) / 1.8)
        n = len(seg) - 1
        m = f * n
        for j in range(n):
            ff = clamp(m - j)
            if ff <= 0: break
            (x0, y0), (x1, y1) = seg[j], seg[j + 1]
            A.d['canal'].line((x0, y0, lerp(x0, x1, ff), lerp(y0, y1, ff)), fill=255, width=12)
    A.d['ink'].rectangle((480, 950, 520, 990), fill=255)
    A.flush(cv)
    for nm, (x, y) in (('洛阳', (500, 970)), ('涿郡', (360, 790)), ('江都', (740, 1240)), ('余杭', (860, 1390))):
        stamp(cv, seal(nm, 28, CANAL), x + 70, y - 20, t, s0 + 0.2)
    i = max(j for j, (b, *_) in enumerate(YH) if ph >= b)
    b, nm, txt = YH[i]
    fx = Art()
    chars_in(cv, fx, '大运河', BRUSH, 160, INK, W / 2, 440, t, s0, stagger=0.08, seed=55)
    fx.flush(cv)
    paste(cv, text_img(f'{nm} · {txt}', SERIF, 46, CANAL, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    km = int(lerp(0, 2700, clamp(ph / 7.5)))
    paste(cv, text_img(f'全长约 {km} 公里', SERIF, 44, DRAGON, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_s_keju(A, cv, t, u):
    for r in range(3):
        for c2 in range(6):
            x = 200 + c2 * 140; y = 960 + r * 120
            A.d['mid'].rectangle((x - 50, y, x + 50, y + 90), fill=220)
            A.d['ink'].rectangle((x - 50, y, x + 50, y + 90), outline=255, width=4)
            sitter(A, x, y + 86, 50, dir=1, bow=20)
    A.flush(cv)
    stamp(cv, seal('进士科', 50), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('科举制度的开端', SERIF, 46, CANAL, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('一说', 40, INK), 260, 1020, t, t - u + 0.4, rot=-5)

def art_s_longzhou(A, cv, t, u):
    """6-beat set piece: 龙舟下扬州 — the four-storey dragon boat, a fleet behind it two hundred li long; trackers pull
    the ropes along the willow-lined banks."""
    ph = u / P
    A.d['canal'].rectangle((60, 1180, W - 60, 1320), fill=150)
    waves(A, 1190, t, rows=2, amp=3, speed=1)
    ground(A, 1180, x0=60, x1=W - 60)
    for k in range(10):
        x = 100 + k * 92
        A.d['grass'].line((x, 1180, x + 4, 1080), fill=255, width=4)
    dragon_boat_big(A, lerp(-200, 560, ease_out(ph / 4)), 1270, 160, t)
    for k in range(4):
        boat(A, lerp(-500, 200, ease_out(ph / 4)) - k * 140, 1290, 60, t + k, sail=True)
    for k in range(8):
        x = lerp(-100, 900, ease_out(ph / 4)) - k * 60
        person(A, x + 200, 1180, 80, dir=1, robe=False, hat='knot', bow=40, ph=t * 5 + k, arm=170, layer='ink')
    A.flush(cv)
    paste(cv, text_img('舳舻相接二百余里', SERIF, 48, DRAGON, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(ph / 0.4))
    stamp(cv, seal('三下江都', 44, INK), 860, 1060, t, t - u + P, rot=6)

def art_s_west(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 160, GROUND), (x, GROUND - 360), (x + 160, GROUND)], fill=200)
    ground(A, GROUND)
    for k in range(8):
        rider(A, lerp(-200, 700, ease_out((u - k * 0.1) / (2.5 * P))) - k * 80, GROUND, 100, 1, t * 10 + k, layer='ink', spear=True)
    A.flush(cv)
    stamp(cv, seal('西巡张掖', 44), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('万国博览会 · 二十七国来朝', SERIF, 44, CANAL, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_great_wall(A, cv, t, u):
    pts = [(x, 1200 - 100 * math.sin(x / W * math.pi * 1.5) - 30 * math.sin(x * 0.03)) for x in range(60, W - 59, 20)]
    p = ease_out(u / (2.5 * P))
    n = max(2, int(len(pts) * p))
    A.d['ink'].line(pts[:n], fill=255, width=12)
    for i in range(0, n, 8):
        A.d['ink'].rectangle((pts[i][0] - 18, pts[i][1] - 60, pts[i][0] + 18, pts[i][1]), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('征发百万人修长城', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 三征高句丽
def art_s_goguryeo(A, cv, t, u):
    """8-beat set piece: 三征高句丽 — three campaigns: each a wave of soldiers marching right, each crumbling at 辽东城;
    the counter of men lost climbs."""
    ph = u / P
    city_wall(A, 760, 1020, 1100, gate_x=890, label='辽东', layer='mid')
    ground(A, GROUND)
    wave = min(2, int(ph / 2.6))
    f = (ph - wave * 2.6) / 2.6
    for k in range(10):
        x = lerp(-200, 700, ease_out(f / 0.6)) - (k % 5) * 80
        fallen = f > 0.6 and k % 3 != 2
        person(A, x, GROUND - (k // 5) * 40, 100, dir=1, robe=False, hat='helmet', spear=True, fall=-80 if fallen else 0, ph=t * 6 + k, arm=40, layer='ink')
    A.flush(cv)
    for i in range(wave + 1):
        stamp(cv, seal(['一征', '二征', '三征'][i], 40, ZHU if i == wave else CANAL), 220 + i * 160, 880, t, t - u + i * 2.6 * P)
    lost = ['三十万渡辽 还者二千七百', '再征 杨玄感后方叛乱', '三征 高句丽请降 · 国力耗尽'][wave]
    paste(cv, text_img(lost, SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, 1)

def art_s_yangxuangan(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='洛阳', layer='mid')
    flames(A, 540, 1100, 600, 180 * ease_out((u - P) / 0.8), t, n=6, seed=4, smoke=True)
    ground(A, GROUND)
    for k in range(8):
        person(A, lerp(-100, 400, ease_out(u / (2 * P))) - k * 50, GROUND, 120, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('杨玄感', 50, INK), 860, 1020, t, t - u + 0.4, rot=6)

def art_s_rebels(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 18)
    for i in range(n):
        a = i * 2 * math.pi / 18
        x = 540 + 380 * math.cos(a); y = 1060 + 220 * math.sin(a)
        flag(A, x, y + 60, 100, t, w=30, layer='red')
    A.flush(cv)
    paste(cv, text_img(f'起义 {n * 7} 余路' if n < 18 else '天下反隋者 百余路', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_s_yanmen(A, cv, t, u):
    city_wall(A, 360, 720, 1100, gate_x=540, label='雁门', layer='mid')
    ground(A, GROUND)
    for k in range(16):
        a = math.pi + k * math.pi / 15
        rider(A, 540 + 460 * math.cos(a), GROUND + 20 * math.sin(a) - 10, 80, 1 if math.cos(a) < 0 else -1, t * 4 + k, layer='ink', spear=True, moving=False)
    guang(A, 540, 1100, 120, dir=1, bow=30, arm=150)
    A.flush(cv)
    stamp(cv, seal('雁门被围', 46, INK), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('突厥围城 · 抱幼子痛哭', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_s_jiangdu(A, cv, t, u):
    A.d['canal'].rectangle((60, 1240, W - 60, GROUND), fill=150)
    palace(A, 540, 1240, 520, layer='dragon')
    guang(A, 540, 1240, 150, dir=1, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 3)))
    for k in range(4):
        person(A, 300 + k * 160, 1240, 100, dir=1, robe=True, hat='knot', female=True, arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('三下江都', 44), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('不再回北方', SERIF, 48, CANAL, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_s_mirror(A, cv, t, u):
    bronze_mirror(A, 640, 1020, 120)
    ground(A, GROUND)
    guang(A, 380, GROUND, 240, dir=1, arm=lerp(60, 150, ease_out(u / P)))
    A.flush(cv)
    type_in(cv, text_img('好头颈 谁当斫之', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + P, 0.5)

# ================================================================ 第四回 江都之变
def art_s_coup(A, cv, t, u):
    """6-beat set piece: 江都兵变 — homesick guards mutiny at night; torches; the emperor is strangled with a silk sash."""
    ph = u / P
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    palace(A, 540, GROUND, 560, layer='mid')
    ground(A, GROUND)
    for k in range(8):
        x = lerp(-200, 360, ease_out((ph - k * 0.1) / 2)) - (k % 4) * 60
        person(A, x, GROUND - (k // 4) * 30, 130, dir=1, robe=False, hat='helmet', spear=True, ph=t * 7 + k, arm=40, layer='ink')
        A.d['red'].ellipse((x + 30, GROUND - 200, x + 54, GROUND - 176), fill=230)
    if ph >= 3:
        guang(A, 640, GROUND, 200, dir=-1, fall=-85 * ease_out((ph - 3.5) / 0.8), arm=60)
    A.flush(cv)
    stamp(cv, seal('宇文化及', 44, INK), 860, 1020, t, t - u + 0.4, rot=6)
    if ph >= 3.5:
        paste(cv, text_img('以练巾缢杀 · 年五十', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 3.5) / 0.3))

def art_s_coffin(A, cv, t, u):
    A.d['mid'].rectangle((360, 1220, 720, 1300), fill=230)
    A.d['ink'].rectangle((360, 1220, 720, 1300), outline=255, width=4)
    ground(A, GROUND)
    person(A, 860, GROUND, 180, dir=-1, robe=True, hat='crown', female=True, bow=40, arm=100, layer='ink')
    A.flush(cv)
    paste(cv, text_img('萧后以床板为棺', SERIF, 48, CANAL, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_s_tang(A, cv, t, u):
    palace(A, 540, 1140, 600, layer='yan')
    ground(A, GROUND)
    person(A, 540, GROUND - 30, 230, dir=1, robe=True, hat='crown', arm=lerp(20, 150, ease_out(u / P)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('李渊称帝', 46), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('隋亡 唐兴', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_s_yang(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    ink_in(cv, text_img('炀', BRUSH, 300, ZHU), W / 2, 1060, t, t - u + 0.5, dur=0.3, settle=1.3)
    paste(cv, text_img('好内远礼曰炀 · 唐朝所上谥号', SERIF, 44, DIM, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_s_tomb(A, cv, t, u):
    A.d['mid'].chord((340, 1180, 740, GROUND + 200), 180, 360, fill=230)
    ground(A, GROUND)
    for k in range(3):
        person(A, 860 + k * 50, GROUND, 120, dir=-1, robe=False, hat='knot', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('扬州曹庄', 44), 540, 1100, t, t - u + P)
    paste(cv, text_img('二〇一三年 · 墓葬被发现', SERIF, 46, CANAL, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_pipi(A, cv, t, u):
    A.d['canal'].rectangle((60, 1200, W - 60, GROUND), fill=160)
    waves(A, 1210, t, rows=3, amp=4, speed=1.2)
    for k in range(4):
        boat(A, lerp(-200, 1200, ((t * 0.1 + k * 0.25) % 1)), 1250 + (k % 2) * 40, 90, t + k, sail=True)
    A.flush(cv)
    type_in(cv, text_img('尽道隋亡为此河 至今千里赖通波', SERIF, 40, CANAL, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.5, 0.6)
    stamp(cv, seal('皮日休', 44, INK), 860, 1040, t, t - u + P, rot=6)

def art_s_today(A, cv, t, u):
    canal_map(A, 1.0, t)
    A.flush(cv)
    stamp(cv, seal('世界遗产', 46), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('二〇一四年 · 大运河申遗成功', SERIF, 44, CANAL, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_s_legacy(A, cv, t, u):
    A.d['canal'].rectangle((60, 1360, W - 60, 1440), fill=150)
    boat(A, 860, 1400, 70, t, sail=True)

def art_s_title(A, cv, t, u):
    river(A, 1400, t, rows=2, amp=3)
    dragon_boat_big(A, 820, 1400, 140, t)
    guang(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '晋王杨广'), 48: ('第二回', '大业'), 80: ('第三回', '天下大乱'),
            112: ('第四回', '江都之变'), 144: ('第五回', '千秋功罪')}

CARDS = [
    C(0, 2, 'works', 'num', num='一条运河', line='用了一千四百年', art=art_s_hook_canal),
    C(2, 4, 'war', 'num', num='三征高句丽', line='百万大军有去无回', art=art_s_hook_3),
    C(4, 6, 'fate', 'num', num='龙舟四层', line='三下江都', art=art_s_hook_boat),
    C(6, 8, 'death', 'num', num='好头颈', line='谁当斫之', art=art_s_hook_head),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=569, main='生于长安', sub='隋文帝次子', art=art_s_birth),
    C(22, 26, 'court', 'card', year=581, main='封晋王', sub='隋朝建立', art=art_s_jinwang),
    C(26, 30, 'night', 'card', year=585, main='伪装节俭', sub='讨父母欢心', note='史书所载 或有夸大', art=art_s_frugal),
    C(30, 36, 'war', 'card', year=589, main='平陈', sub='南北重归一统', art=art_s_chen),
    C(36, 40, 'works', 'card', year=590, main='镇守扬州', sub='深爱江南', art=art_s_yangzhou),
    C(40, 44, 'court', 'card', year=600, main='夺嫡', sub='太子杨勇被废', art=art_s_taizi),
    C(44, 48, 'death', 'card', year=604, main='仁寿宫', sub='父亡登基', art=art_s_renshou),
    C(48, 50, 'empire', 'chapter'),
    C(50, 54, 'empire', 'card', year=605, main='即位', sub='年号大业', art=art_s_crown),
    C(54, 58, 'works', 'card', year=605, main='营建东都', sub='洛阳', art=art_s_luoyang),
    C(58, 66, 'works', 'yunhe', year=605),
    C(66, 72, 'fate', 'card', year=605, main='龙舟南巡', sub='至江都', art=art_s_longzhou),
    C(72, 76, 'court', 'card', year=607, main='开科取士', sub='设进士科', art=art_s_keju),
    C(76, 78, 'works', 'card', year=607, main='修长城', sub='北御突厥', art=art_s_great_wall),
    C(78, 80, 'empire', 'card', year=609, main='西巡', sub='至张掖', art=art_s_west),
    C(80, 82, 'war', 'chapter'),
    C(82, 90, 'war', 'card', year=612, main='三征高句丽', sub='倾举国之力', note='六一二至六一四年', art=art_s_goguryeo),
    C(90, 94, 'night', 'card', year=613, main='杨玄感反', sub='贵族起兵', art=art_s_yangxuangan),
    C(94, 98, 'war', 'card', year=614, main='烽烟四起', sub='民不聊生', art=art_s_rebels),
    C(98, 104, 'death', 'card', year=615, main='雁门之围', sub='北巡遇险', art=art_s_yanmen),
    C(104, 108, 'fate', 'card', year=616, main='三下江都', sub='逃避乱局', art=art_s_jiangdu),
    C(108, 112, 'night', 'card', year=617, main='揽镜自照', sub='自知末日将至', art=art_s_mirror),
    C(112, 114, 'night', 'chapter'),
    C(114, 120, 'death', 'card', year=618, main='江都兵变', sub='禁军思归', art=art_s_coup),
    C(120, 124, 'death', 'card', year=618, main='草草收殓', sub='一代帝王的结局', art=art_s_coffin),
    C(124, 128, 'empire', 'card', year=618, main='唐朝建立', sub='李渊于长安称帝', art=art_s_tang),
    C(128, 136, 'court', 'card', year=618, main='谥号炀', sub='恶谥', art=art_s_yang),
    C(136, 144, 'works', 'card', year=870, main='千里通波', sub='唐人重新评价运河', art=art_s_pipi),
    C(144, 146, 'end', 'chapter'),
    C(146, 156, 'life', 'card', year=2013, main='隋炀帝墓', sub='扬州考古', art=art_s_tomb),
    C(156, 170, 'end', 'card', year=2014, main='运河申遗', sub='他留下的工程 至今仍在', art=art_s_today),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='肆拾肆', col=CANAL, acc=DRAGON, born=569, died=618,
    hook_q='千古暴君 · 还是被唐朝抹黑的雄主？',
    name_line='杨广 · 隋炀帝', name='隋炀帝', seal='大业', title_art=art_s_title,
    q1='千古暴君？', q2='急功近利？',
    end_art=art_s_legacy, end_big='千里通波', end_seal='大业',
    end_l1='他十几年做完了几代人的事', end_l2='也耗尽了一个王朝',
    end_brush='功在千秋 罪在当代', end_ask='你怎么看隋炀帝？评论区聊聊', next='林则徐'),
    scenes=dict(chapter=scene_chapter, yunhe=scene_yunhe))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
