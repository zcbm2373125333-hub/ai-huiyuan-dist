"""千古人物志 · 第肆拾陆集 · 商鞅 (约前390–前338)
Look: 秦玄 + 法令铜, 回纹 corner borders, a 南门立木 chapter card: law slips hang on the gate one pair per chapter
(0→2→4→6), and in the last chapter the pole topples.
Set pieces: 6-beat 求贤令 西入秦, custom 8-beat scene 'muzi' (徙木立信: 十金→五十金), 6-beat 新法三条,
6-beat 开阡陌 设县, 8-beat 诱擒公子卬, 6-beat 作法自毙.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_linzexu as Lz         # engine + helpers (previous episode)
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

F.RIPPLE = False
QINXUAN = (36, 42, 62)              # 秦玄
FATONG = (150, 112, 50)             # 法令铜
S.LAYERS.append(('qinxuan', QINXUAN, 0.9, 1.0))
S.LAYERS.append(('fatong', FATONG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='法', life='卫', court='秦', night='夜', war='战', empire='秦', works='法', fate='商', death='法', end='信')
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
G.THEMES['empire']['sun'] = (FATONG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (QINXUAN, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

LOESS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(LOESS)
for _k in range(4):                 # 阡陌: field paths at the lower margins
    _y = 1440 + _k * 26
    _d.line((60, _y, W - 60, _y + 6), fill=FATONG + (34,), width=2)
for _x in range(120, W - 60, 140):
    _d.line((_x, 1440, _x + 12, 1530), fill=FATONG + (30,), width=2)
for _x, _w in ((150, 160), (920, 140)):   # 黄土台塬 terraces
    for _s in range(3):
        _d.rectangle((_x - _w / 2 + _s * 18, 1340 - _s * 26, _x + _w / 2 - _s * 18, 1366 - _s * 26), fill=(150, 120, 80, 40))
MTN_COL = {'night': (32, 34, 46), 'death': (60, 58, 60), 'war': (104, 60, 50), 'fate': (92, 90, 100)}
def draw_background(t, theme):
    """关中: loess terraces and field paths at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 184, 170), (160, 146, 124), MTN_COL.get(theme, (120, 108, 90))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(LOESS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """回纹: a squared bronze-vessel spiral in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=QINXUAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=QINXUAN + (220,), width=3)
        pts = [(0, 0), (60, 0), (60, 60), (12, 60), (12, 14), (46, 14), (46, 46), (26, 46), (26, 28)]
        d.line([(x + sx * (14 + px), y + sy * (14 + py)) for px, py in pts], fill=FATONG + (230,), width=5)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def yang(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """商鞅: Warring-States minister — tall slanted 高冠 with a bronze tie, sash, short beard."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.polygon([(x - 0.06 * h, y - 0.95 * h), (x + 0.06 * h, y - 0.95 * h),
                   (x + 0.05 * h + dir * 0.06 * h, y - 1.14 * h), (x - 0.03 * h + dir * 0.06 * h, y - 1.14 * h)], fill=255)
        A.d['fatong'].line((x - 0.02 * h, y - 0.95 * h, x - dir * 0.03 * h, y - 0.84 * h), fill=255, width=max(2, int(0.014 * h)))
        A.d['fatong'].rectangle((x - 0.08 * h, y - 0.58 * h, x + 0.08 * h, y - 0.53 * h), fill=255)
        d.line((x + dir * 0.06 * h, y - 0.82 * h, x + dir * 0.09 * h, y - 0.74 * h), fill=255, width=max(2, int(0.02 * h)))
        if old > 0.4:
            A.d['wash'].line((x + dir * 0.06 * h, y - 0.8 * h, x + dir * 0.09 * h, y - 0.74 * h), fill=255, width=max(2, int(0.012 * h)))
    return hand

def duke(A, x, y, h, dir=-1, layer='ink', **kw):
    """秦孝公: crowned ruler."""
    return person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)

def pole(A, x, base, h, fallen=0.0, layer='fatong'):
    ang = fallen * 1.45
    A.d[layer].line((x, base, x + h * math.sin(ang), base - h * math.cos(ang)), fill=255, width=18)

def coins(A, x, y, n, s=16):
    for i in range(n):
        A.d['gold'].ellipse((x + (i % 5) * (s + 6) - s, y - (i // 5) * (s - 2) - s / 2, x + (i % 5) * (s + 6) + s, y - (i // 5) * (s - 2) + s / 2), fill=255)
        A.d['ink'].ellipse((x + (i % 5) * (s + 6) - 4, y - (i // 5) * (s - 2) - 3, x + (i % 5) * (s + 6) + 4, y - (i // 5) * (s - 2) + 3), fill=200)

def law_board(A, x, y, n, layer='qinxuan'):
    """A row of hanging law slips (n pairs) on a gate beam."""
    for i in range(n):
        sx = x + i * 46
        A.d['ink'].line((sx + 8, y - 30, sx + 8, y), fill=220, width=2)
        A.d[layer].rectangle((sx, y, sx + 16, y + 150), fill=255)

def measure(A, cx, cy, s, layer='fatong'):
    """商鞅方升: a rectangular bronze measure with a handle."""
    A.d[layer].rectangle((cx - s, cy - 0.6 * s, cx + s, cy + 0.6 * s), fill=255)
    A.d['ink'].rectangle((cx - 0.8 * s, cy - 0.45 * s, cx + 0.8 * s, cy + 0.45 * s), outline=200, width=4)
    A.d[layer].rectangle((cx + s, cy - 0.15 * s, cx + 1.9 * s, cy + 0.15 * s), fill=255)

def inn(A, cx, base, w, t, lit=1.0):
    A.d['mid'].rectangle((cx - w / 2, base - 0.55 * w, cx + w / 2, base), fill=230)
    A.d['ink'].polygon([(cx - w / 2 - 40, base - 0.55 * w), (cx + w / 2 + 40, base - 0.55 * w), (cx + w / 2 - 20, base - 0.75 * w), (cx - w / 2 + 20, base - 0.75 * w)], fill=255)
    A.d['ink'].rectangle((cx - 0.12 * w, base - 0.36 * w, cx + 0.12 * w, base), fill=255)
    A.d['ink'].line((cx + w / 2 - 30, base - 0.55 * w, cx + w / 2 - 30, base - 0.44 * w), fill=255, width=3)
    lamp(A, cx + w / 2 - 30, base - 0.36 * w, 36, t, glow=lit)

# ================================================================ chapter card
CH = {16: (0, 0.0), 48: (2, 0.0), 80: (4, 0.0), 112: (6, 0.0), 144: (6, 1.0)}
def art_gate_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g, fallen = CH.get(kb, (2, 0.0))
    prev = {48: 0, 80: 2, 112: 4, 144: 6}.get(kb, 0)
    q = ease_out(u / (1.2 * P))
    city_wall(A, 160, 920, 1000, gate_x=470, label='南门', layer='mid', open_=1.0)
    law_board(A, 340, 1020, int(lerp(prev, g, q)))
    pole(A, 820, GROUND, 520, fallen=fallen * q)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_gate_chapter)
    ink_in(cv, text_img(no, SERIF, 56, QINXUAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_s_hook_pole(A, cv, t, u):
    ground(A, GROUND)
    pole(A, 540, GROUND, 520, fallen=0.0)
    coins(A, 700, GROUND - 20, min(10, int(clamp(u / (1.4 * P)) * 10) + 1))

def art_s_hook_twenty(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (1.6 * P)) * 20) + 1
    for i in range(n):
        h = 40 + i * 14
        A.d['qinxuan'].rectangle((120 + i * 42, GROUND - h, 150 + i * 42, GROUND), fill=255)

def art_s_hook_inn(A, cv, t, u):
    ground(A, GROUND)
    inn(A, 640, GROUND, 360, t, lit=0.6)
    yang(A, 300, GROUND, 220, dir=1, bow=15, arm=lerp(-8, 60, ease_out(u / P)))

def art_s_hook_law(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (1.4 * P)) * 14) + 1
    slips(A, 540 - n * 19 / 2, GROUND - 20, n, 320, layer='fatong')

# ================================================================ 第一回 卫国公孙
def art_s_birth(A, cv, t, u):
    palace(A, 540, 1160, 480, layer='mid')
    ground(A, GROUND)
    person(A, 420, GROUND, 230, dir=1, robe=True, hat='knot', arm=40, layer='ink')
    person(A, 560, GROUND, 120, dir=-1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('卫国', 54), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('公孙鞅 · 卫国公族庶出', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_study(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='qinxuan')
    sitter(A, 300, GROUND, 200, dir=1, bow=15)
    for k in range(int(clamp(u / (2 * P)) * 6) + 1):
        slips(A, 440 + k * 40, GROUND - 74, 1, 90, layer='fatong', tied=False)
    A.flush(cv)
    stamp(cv, seal('刑名之学', 44), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('李悝法经 · 吴起变法', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_wei(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='fatong')
    ground(A, GROUND)
    person(A, 720, GROUND, 220, dir=-1, robe=True, hat='knot', arm=lerp(20, 80, ease_out(u / 0.6)), layer='ink', bow=10)
    yang(A, 380, GROUND, 210, dir=1, arm=60)
    A.flush(cv)
    stamp(cv, seal('中庶子', 50), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('魏相公叔痤门下', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_deathbed(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, robe=True, hat='knot', fall=-80, arm=lerp(-8, 50, ease_out(u / P)), layer='ink')
    person(A, 860, GROUND, 220, dir=-1, robe=True, hat='crown', arm=20, layer='ink')
    lamp(A, 220, GROUND, 60, t, glow=0.8)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('若不用鞅 必杀之', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)

def art_s_ignored(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 700, GROUND, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 140, ease_out(u / 0.6)), layer='ink')
    yang(A, 380, GROUND, 200, dir=1, arm=-8)
    A.flush(cv)
    stamp(cv, seal('魏惠王', 50, INK), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('以为病中胡言 · 不用也不杀', SERIF, 44, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_decree(A, cv, t, u):
    """6-beat set piece: 求贤令 — the young duke unrolls the decree; then 卫鞅 walks west over the 函谷 hills to 秦."""
    ph = u / P
    if ph < 2.6:
        palace(A, 540, 1140, 560, layer='qinxuan')
        ground(A, GROUND)
        duke(A, 380, GROUND, 230, dir=1, arm=90)
        scroll(A, 560, GROUND - 150, 300, 90, clamp(ph / 1.6), layer='wash')
    else:
        for k in range(5):
            x = 140 + k * 200
            A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 300 - 40 * (k % 2)), (x + 150, GROUND)], fill=200)
        ground(A, GROUND)
        x = lerp(980, 160, ease_out((ph - 2.6) / 3.0))
        yang(A, x, GROUND, 180, dir=-1, ph=t * 3, arm=-8)
        bundle(A, x + 40, GROUND - 120, 50, layer='fatong')
    A.flush(cv)
    if ph < 2.6:
        type_in(cv, text_img('有能出奇计强秦者', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.5)
        type_in(cv, text_img('吾且尊官 与之分土', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.2 * P, 0.5)
    else:
        paste(cv, text_img('秦孝公求贤 · 卫鞅西入秦', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 2.6) / 0.4))
        stamp(cv, seal('栎阳', 54), 260, 1020, t, t - u + 3 * P, rot=-5)

def art_s_four(A, cv, t, u):
    ground(A, GROUND)
    duke(A, 760, GROUND, 230, dir=-1, kneel=True, arm=40, bow=lerp(30, 0, ease_out((u - 2.5 * P) / 0.4)))
    yang(A, 360, GROUND, 210, dir=1, kneel=True, arm=lerp(40, 110, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    labs = ['帝道', '王道', '霸道', '强国之术']
    n = min(4, int(u / (0.9 * P)) + 1)
    for i in range(n):
        col = ZHU if i == 3 else DIM
        paste(cv, text_img(labs[i], SERIF, 44, col, 'Black', bleed=False, spacing=4), 210 + i * 220, 830, 1, clamp((u - i * 0.9 * P) / 0.3))
    if n >= 4:
        stamp(cv, seal('孝公大悦', 44), 860, 1020, t, t - u + 3.2 * P, rot=6)

# ================================================================ 第二回 变法图强
def art_s_debate(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(20, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    person(A, 880, GROUND, 190, dir=-1, robe=True, hat='knot', arm=40, layer='ink')
    yang(A, 320, GROUND, 210, dir=1, arm=lerp(40, 120, ease_out((u - P) / 0.4)))
    A.flush(cv)
    type_in(cv, text_img('治世不一道', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + P, 0.4)
    type_in(cv, text_img('便国不法古', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 835, t, t - u + 2 * P, 0.4)
    stamp(cv, seal('甘龙杜挚', 40, INK), 860, 1020, t, t - u + 0.4, rot=6)

def art_s_zuoshuzhang(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='qinxuan')
    ground(A, GROUND)
    duke(A, 720, GROUND - 30, 220, dir=-1, arm=lerp(20, 100, ease_out(u / 0.6)))
    yang(A, 360, GROUND, 220, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('左庶长', 54), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('孝公拜之 · 主持变法', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_muzi(cv, t, c, k):
    """8-beat custom scene: 徙木立信 — a three-zhang pole at the south gate; nobody believes the ten-gold notice;
    the reward is raised to fifty; one man carries it to the north gate and is paid on the spot."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    city_wall(A, 60, 330, 1040, label=None, layer='mid')
    city_wall(A, 750, 1020, 1040, label=None, layer='mid')
    ground(A, GROUND)
    carry = clamp((ph - 4) / 2.5)
    if carry <= 0:
        pole(A, 250, GROUND, 460)
        for j in range(6):
            person(A, 380 + j * 60, GROUND, 120 + (j % 3) * 10, dir=-1, robe=True, hat='knot', arm=lerp(-8, 30, (j % 2)), layer='mid')
    else:
        x = lerp(260, 860, ease_out(carry))
        person(A, x, GROUND, 170, dir=1, ph=t * 5 if carry < 1 else None, robe=False, hat='knot', arm=150, layer='ink')
        A.d['fatong'].line((x - 220, GROUND - 260, x + 120, GROUND - 160), fill=255, width=18)
        for j in range(4):
            person(A, 420 + j * 70, GROUND, 120, dir=1, robe=True, hat='knot', arm=60, layer='mid')
    yang(A, 160, GROUND, 190, dir=1, arm=lerp(-8, 60, clamp((ph - 6.5) / 0.4)))
    if ph >= 6.5:
        n = int(clamp((ph - 6.5) / 1.0) * 10)
        coins(A, 780, GROUND - 260, n, s=14)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '徙木立信', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=46)
    fx.flush(cv)
    gold = '十金' if ph < 2.2 else '五十金'
    paste(cv, text_img(f'徙至北门者 予{gold}', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    lab = '民怪之 莫敢徙' if ph < 4 else ('有一人徙之' if ph < 6.5 else '辄予五十金 以明不欺')
    paste(cv, text_img(lab, SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph % 2.2 if ph < 4 else ph) / 0.4))

def art_s_laws(A, cv, t, u):
    """6-beat set piece: 新法三条 — 什伍连坐 (houses chained), 军功爵 (a soldier climbs twenty steps), 重农抑商 (grain heaped, cart barred)."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        for i in range(5):
            x = 220 + i * 160
            A.d['mid'].rectangle((x - 50, GROUND - 120, x + 50, GROUND), fill=230)
            A.d['ink'].polygon([(x - 70, GROUND - 120), (x + 70, GROUND - 120), (x, GROUND - 190)], fill=255)
        q = clamp((ph - 0.6) / 1.0)
        A.d['red'].line((220, GROUND - 60, 220 + 640 * q, GROUND - 60), fill=255, width=6)
        lab, sl = '什伍连坐 · 告奸者赏', '连坐'
    elif ph < 4:
        for i in range(20):
            A.d['qinxuan'].rectangle((120 + i * 42, GROUND - 20 - i * 18, 162 + i * 42, GROUND), fill=200)
        i = min(19, int(clamp((ph - 2) / 1.8) * 20))
        person(A, 140 + i * 42, GROUND - 20 - i * 18, 110, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
        lab, sl = '军功爵二十级 · 宗室无功不得属籍', '军功'
    else:
        for k in range(int(clamp((ph - 4) / 1.5) * 6) + 1):
            A.d['yellow'].polygon([(200 + k * 70, GROUND), (230 + k * 70, GROUND - 160), (260 + k * 70, GROUND)], fill=230)
        carriage(A, 800, GROUND, 90, dir=-1, moving=False, horses=False, layer='mid')
        A.d['red'].line((700, GROUND - 160, 900, GROUND), fill=255, width=10)
        A.d['red'].line((700, GROUND, 900, GROUND - 160), fill=255, width=10)
        lab, sl = '重农抑商 · 耕织致粟帛多者复其身', '耕战'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 42, QINXUAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp((ph % 2) / 0.3))
    stamp(cv, seal(sl, 54), 860, 1020, t, t - u + int(ph / 2) * 2 * P + 0.3, rot=6)

def art_s_prince(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='fatong')
    ground(A, GROUND)
    person(A, 720, GROUND, 160, dir=-1, robe=True, hat='knot', arm=20, layer='mid')
    person(A, 560, GROUND, 200, dir=-1, robe=True, hat='knot', kneel=True, bow=40, arm=100, layer='ink')
    yang(A, 320, GROUND, 220, dir=1, arm=lerp(40, 120, ease_out((u - P) / 0.4)))
    A.flush(cv)
    type_in(cv, text_img('法之不行 自上犯之', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + P, 0.5)
    stamp(cv, seal('公子虔', 50, INK), 860, 1020, t, t - u + 0.4, rot=6)

def art_s_daliangzao(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        A.d['qinxuan'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    yang(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 40, ease_out(u / 0.6)))
    A.flush(cv)
    stamp(cv, seal('大良造', 56), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('秦国最高官爵 · 军政一身', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 商君之法
def art_s_xianyang(A, cv, t, u):
    q = ease_out(u / (2 * P))
    city_wall(A, 160, 920, lerp(1240, 1080, q), gate_x=540, label='咸阳', layer='qinxuan', open_=1.0)
    ground(A, GROUND)
    for k in range(4):
        x = (t * 70 + k * 240) % (W + 200) - 100
        person(A, x, GROUND, 90, dir=1, robe=False, hat='knot', load=True, ph=t * 6 + k, arm=160, layer='ink')
    A.flush(cv)
    stamp(cv, seal('迁都', 56), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('筑冀阙宫庭 · 自栎阳徙都', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_fields(A, cv, t, u):
    """6-beat set piece: 废井田 开阡陌 — the nine-square well-fields are redrawn as long strips; then villages merge into counties (counter to 31)."""
    ph = u / P
    x0, y0, s = 240, 900, 600
    A.d['grass'].rectangle((x0, y0, x0 + s, y0 + s * 0.6), fill=150)
    if ph < 2.5:
        for k in (1, 2):
            A.d['ink'].line((x0 + s * k / 3, y0, x0 + s * k / 3, y0 + s * 0.6), fill=220, width=5)
            A.d['ink'].line((x0, y0 + s * 0.2 * k, x0 + s, y0 + s * 0.2 * k), fill=220, width=5)
        A.d['yellow'].rectangle((x0 + s / 3, y0 + s * 0.2, x0 + 2 * s / 3, y0 + s * 0.4), fill=200)
        lab = '井田 · 九百亩为一井'
    else:
        q = clamp((ph - 2.5) / 1.5)
        n = int(lerp(3, 12, q))
        for k in range(1, n):
            A.d['fatong'].line((x0 + s * k / n, y0, x0 + s * k / n, y0 + s * 0.6), fill=230, width=4)
        A.d['fatong'].line((x0, y0 + s * 0.3, x0 + s, y0 + s * 0.3), fill=255, width=8)
        lab = '开阡陌封疆 · 土地可以买卖'
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    if ph >= 4:
        n = min(31, int(clamp((ph - 4) / 1.6) * 31) + 1)
        paste(cv, text_img(f'集小乡邑为县 · {n}县', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_s_measure(A, cv, t, u):
    ground(A, GROUND)
    measure(A, 500, 1080, 150)
    q = ease_out((u - P) / 0.6)
    A.d['yellow'].rectangle((380, 1080 - 70 * q, 620, 1150), fill=200)
    A.flush(cv)
    stamp(cv, seal('商鞅方升', 46), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('平斗桶权衡丈尺', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '原器今藏上海博物馆', t, t - u + 2 * P)

def art_s_order(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 240), (x + 200, GROUND)], fill=160)
    ground(A, GROUND)
    A.d['fatong'].rectangle((500, GROUND - 40, 560, GROUND), fill=255)
    for j in range(3):
        x = lerp(-60 - j * 140, 1100 - j * 140, ((t * 0.12 + j * 0.3) % 1))
        person(A, x, GROUND, 120, dir=1, ph=t * 4 + j, robe=True, hat='knot', arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('道不拾遗 · 山无盗贼', SERIF, 48, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('家给人足', 44), 260, 1020, t, t - u + P, rot=-5)

def art_s_grudge(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    for j in range(4):
        person(A, 640 + j * 90, GROUND, 180, dir=-1, robe=True, hat='knot', bow=15, arm=lerp(-8, 30, (j % 2)), layer='ink')
    yang(A, 300, GROUND, 210, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('宗室贵戚多怨望者', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('积怨', 54, INK), 860, 1020, t, t - u + P, rot=6)

def art_s_battle(A, cv, t, u):
    """8-beat set piece: 诱擒公子卬 — the two camps; a peace banquet between them; the hidden soldiers rise and seize him;
    the Wei army routs and 河西 is ceded."""
    ph = u / P
    ground(A, GROUND)
    tent(A, 160, GROUND, 200, 170, layer='mid')
    tent(A, 920, GROUND, 200, 170, layer='qinxuan')
    A.d['fatong'].rectangle((420, GROUND - 70, 660, GROUND - 56), fill=255)
    if ph < 5:
        yang(A, 680, GROUND, 190, dir=-1, kneel=True, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)))
        cap = ph >= 3
        person(A, 400, GROUND, 190, dir=1, robe=True, hat='knot', kneel=True, bow=40 if cap else 0, arm=60 if not cap else 150, layer='mid')
        if ph >= 3:
            for j in range(4):
                x = lerp(1040, 470 + j * 50, ease_out((ph - 3) / 0.8))
                person(A, x, GROUND, 150, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    else:
        for j in range(5):
            x = lerp(400 + j * 60, -200 + j * 60, ease_out((ph - 5) / 2.5))
            rider(A, x, GROUND, 110, dir=-1, ph=t * 8 + j, layer='mid')
        for j in range(4):
            rider(A, lerp(900, 600, ease_out((ph - 5) / 2)) + j * 90, GROUND, 120, dir=-1, ph=t * 8 + j, layer='ink', spear=True)
    A.flush(cv)
    lab = '约魏将会盟饮酒' if ph < 3 else ('伏甲士而袭虏之' if ph < 5 else '大破魏军 · 魏献河西之地')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3 else QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('河西', 54), 260, 1020, t, t - u + 5.2 * P, rot=-5)

# ================================================================ 第四回 商於十五邑
def art_s_fief(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=200)
    ground(A, GROUND)
    n = int(clamp(u / (2 * P)) * 15) + 1
    for i in range(n):
        x = 150 + (i % 8) * 110; y = 1200 + (i // 8) * 70
        A.d['qinxuan'].rectangle((x - 30, y - 30, x + 30, y + 10), fill=230)
        A.d['ink'].polygon([(x - 40, y - 30), (x + 40, y - 30), (x, y - 60)], fill=255)
    A.flush(cv)
    stamp(cv, seal('商君', 60), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img(f'封于商 · 十五邑', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_zhaoliang(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='qinxuan')
    yang(A, 300, GROUND, 210, dir=1, kneel=True, arm=40)
    person(A, 780, GROUND, 200, dir=-1, robe=True, hat='knot', kneel=True, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.flush(cv)
    type_in(cv, text_img('君之危若朝露', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('何不归十五都 灌园于鄙', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.5 * P, 0.5)
    stamp(cv, seal('赵良', 50, INK), 860, 1020, t, t - u + 0.4, rot=6)

def art_s_escort(A, cv, t, u):
    ground(A, GROUND)
    for j in range(4):
        carriage(A, (t * 90 + j * 300) % (W + 400) - 200, GROUND, 80, dir=1, wheel=t * 6, ph=t * 8 + j, layer='ink' if j == 1 else 'mid')
    for j in range(5):
        person(A, (t * 90 + j * 240 + 120) % (W + 400) - 200, GROUND, 110, dir=1, ph=t * 5 + j, robe=False, hat='helmet', spear=True, arm=40, layer='qinxuan')
    A.flush(cv)
    paste(cv, text_img('后车十数 · 持矛操戟者旁车而趋', SERIF, 42, QINXUAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('不听', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_s_duke_dies(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    duke(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('孝公薨', 50, INK), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('欲传位商君 · 辞不受', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_accused(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='qinxuan')
    ground(A, GROUND)
    person(A, 760, GROUND - 30, 200, dir=-1, robe=True, hat='crown', arm=lerp(20, 140, ease_out((u - P) / 0.5)), layer='ink')
    person(A, 420, GROUND, 200, dir=1, robe=True, hat='knot', kneel=True, bow=20, arm=110, layer='ink')
    A.flush(cv)
    paste(cv, text_img('公子虔之徒 告商君欲反', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('秦惠文王', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_s_flee(A, cv, t, u):
    for k in range(60):
        q = (t * 0.2 + k / 60) % 1
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 400 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 400 + 2), fill=int(200 * (0.5 + 0.5 * math.sin(t * 2 + k))))
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 300), (x + 150, GROUND)], fill=200)
    ground(A, GROUND)
    person(A, lerp(-60, 760, ease_out(u / (3 * P))), GROUND, 180, dir=1, ph=t * 6, robe=True, hat='knot', arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('连夜出逃 · 至关下', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_inn(A, cv, t, u):
    """6-beat set piece: 作法自毙 — night at the border inn; he asks to lodge; the keeper refuses by his own law; he sighs."""
    ph = u / P
    ground(A, GROUND)
    inn(A, 680, GROUND, 400, t, lit=1.0 if ph < 3 else clamp(1 - (ph - 3) / 1))
    person(A, 820, GROUND, 170, dir=-1, robe=True, hat='knot', arm=lerp(-8, 150, clamp((ph - 1) / 0.4)), layer='ink')
    yang(A, lerp(200, 440, ease_out(ph / 1.2)), GROUND, 190, dir=1, ph=t * 3 if ph < 1.2 else None, bow=lerp(0, 30, clamp((ph - 3.5) / 1)), arm=-8)
    A.flush(cv)
    type_in(cv, text_img('商君之法 舍人无验者坐之', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 1.2 * P, 0.5)
    type_in(cv, text_img('嗟乎 为法之敝一至此哉', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 3.5 * P, 0.5)

# ================================================================ 第五回 人亡政存
def art_s_wei_refuse(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='魏', layer='mid', open_=lerp(1.0, 0.0, ease_out(u / P)))
    ground(A, GROUND)
    yang(A, 540, GROUND, 190, dir=-1, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('魏人怨其诈 · 弗受', SERIF, 44, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('闭关', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_s_end(A, cv, t, u):
    ground(A, GROUND)
    q = ease_out(u / (2 * P))
    for j in range(5):
        a = math.radians(-90 + j * 72)
        r = lerp(60, 300, q)
        x, y = 540 + r * math.cos(a), 1060 + 0.6 * r * math.sin(a)
        A.d['mid'].ellipse((x - 26, y - 26, x + 26, y + 26), fill=200)
        A.d['ink'].line((540, 1060, x, y), fill=int(160 * (1 - q)), width=3)
    A.d['red'].ellipse((520, 1040, 560, 1080), fill=int(220 * (1 - q)))
    A.flush(cv)
    paste(cv, text_img('秦惠王车裂商君以徇', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('灭其家', 50, INK), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '史记 商君列传', t, t - u + 2 * P)

def art_s_law_stays(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2 * P)) * 14) + 1
    slips(A, 540 - n * 19 / 2, GROUND - 20, n, 300, layer='qinxuan')
    A.flush(cv)
    paste(cv, text_img('人虽死 · 秦法未败', SERIF, 48, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('其法不废', 44), 260, 1020, t, t - u + P, rot=-5)

def art_s_unify(A, cv, t, u):
    for j in range(6):
        x = lerp(-120, 1200, ((t * 0.08 + j / 6) % 1))
        carriage(A, x, GROUND, 70, dir=1, wheel=t * 6, ph=t * 8 + j, layer='qinxuan' if j % 2 else 'ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('百余年后 · 秦灭六国', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('一统', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_edict(A, cv, t, u):
    ground(A, GROUND)
    measure(A, 500, 1080, 150, layer='qinxuan')
    A.flush(cv)
    type_in(cv, text_img('方升底部 加刻始皇诏书', SERIF, 46, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('统一度量衡', 40), 860, 1020, t, t - u + P, rot=6)

def art_s_book(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='qinxuan')
    for i in range(int(clamp(u / P) * 6) + 1):
        bundle(A, 400 + i * 56, GROUND - 74, 44, layer='fatong')
    A.flush(cv)
    ink_in(cv, text_img('商君书', SERIF, 52, QINXUAN, 'Black', bleed=False, spacing=10), W / 2, 830, t, t - u + 0.3, dur=0.3)

def art_s_gate(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='南门', layer='mid', open_=1.0)
    pole(A, 820, GROUND, 460)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('立木之信 · 后世变法者必言', SERIF, 44, QINXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    pole(A, 860, 1440, 300)

def art_s_title(A, cv, t, u):
    pole(A, 820, 1460, 560)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    yang(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '卫国公孙'), 48: ('第二回', '变法图强'), 80: ('第三回', '商君之法'),
            112: ('第四回', '商於之地'), 144: ('第五回', '人亡政存')}

CARDS = [
    C(0, 2, 'works', 'num', num='一根木头', line='换五十金', art=art_s_hook_pole),
    C(2, 4, 'empire', 'num', num='二十年', line='秦国脱胎换骨', art=art_s_hook_twenty),
    C(4, 6, 'night', 'num', num='逃亡之夜', line='无处投宿', art=art_s_hook_inn),
    C(6, 8, 'death', 'num', num='人死了', line='法还在', art=art_s_hook_law),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 卫国公孙
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-390, main='生于卫国', sub='公族之后', note='生年约在前三九〇年', art=art_s_birth),
    C(22, 26, 'works', 'card', year=-372, main='好刑名', sub='少年读法家', art=art_s_study),
    C(26, 30, 'court', 'card', year=-365, main='魏相门客', sub='才而未用', art=art_s_wei),
    C(30, 34, 'night', 'card', year=-361, main='临终荐贤', sub='公叔痤遗言', art=art_s_deathbed),
    C(34, 38, 'fate', 'card', year=-361, main='魏王不用', sub='明珠暗投', art=art_s_ignored),
    C(38, 44, 'empire', 'card', year=-361, main='求贤令', sub='秦孝公', art=art_s_decree),
    C(44, 48, 'court', 'card', year=-361, main='四见孝公', sub='数日不厌', art=art_s_four),
    # ---- 第二回 变法图强
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'court', 'card', year=-359, main='朝堂论战', sub='变还是不变', art=art_s_debate),
    C(54, 58, 'empire', 'card', year=-356, main='左庶长', sub='第一次变法', art=art_s_zuoshuzhang),
    C(58, 66, 'works', 'muzi', year=-356),
    C(66, 72, 'war', 'card', year=-356, main='新法', sub='奖励耕战', art=art_s_laws),
    C(72, 76, 'night', 'card', year=-356, main='太子犯法', sub='刑其傅 黥其师', art=art_s_prince),
    C(76, 80, 'empire', 'card', year=-352, main='大良造', sub='位极人臣', art=art_s_daliangzao),
    # ---- 第三回 商君之法
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'empire', 'card', year=-350, main='迁都咸阳', sub='第二次变法', art=art_s_xianyang),
    C(86, 92, 'works', 'card', year=-350, main='开阡陌', sub='废井田 设县制', art=art_s_fields),
    C(92, 96, 'court', 'card', year=-344, main='统一度量', sub='一斗一尺皆有定', art=art_s_measure),
    C(96, 100, 'life', 'card', year=-344, main='秦民大悦', sub='行之十年', art=art_s_order),
    C(100, 104, 'night', 'card', year=-343, main='怨声暗起', sub='得罪了所有贵族', art=art_s_grudge),
    C(104, 112, 'war', 'card', year=-340, main='诱擒魏将', sub='一场不讲信用的胜利', art=art_s_battle),
    # ---- 第四回 商於之地
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'empire', 'card', year=-340, main='封商君', sub='商於之地', art=art_s_fief),
    C(118, 122, 'night', 'card', year=-340, main='危若朝露', sub='赵良进言', art=art_s_zhaoliang),
    C(122, 126, 'court', 'card', year=-339, main='出必重兵', sub='他知道仇人多', art=art_s_escort),
    C(126, 130, 'death', 'card', year=-338, main='孝公病逝', sub='靠山倒了', note='传位之说出自战国策', art=art_s_duke_dies),
    C(130, 134, 'court', 'card', year=-338, main='被告谋反', sub='新君旧怨', art=art_s_accused),
    C(134, 138, 'fate', 'card', year=-338, main='出逃', sub='亡命关下', art=art_s_flee),
    C(138, 144, 'night', 'card', year=-338, main='作法自毙', sub='客舍不纳', art=art_s_inn),
    # ---- 第五回 人亡政存
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'fate', 'card', year=-338, main='魏不收留', sub='无路可走', art=art_s_wei_refuse),
    C(150, 154, 'death', 'card', year=-338, main='车裂', sub='身死族灭', art=art_s_end),
    C(154, 158, 'works', 'card', year=-337, main='秦法不废', sub='惠文王仍行其法', art=art_s_law_stays),
    C(158, 162, 'empire', 'card', year=-221, main='秦并天下', sub='商鞅打下的根基', art=art_s_unify),
    C(162, 166, 'court', 'card', year=-221, main='始皇诏书', sub='刻在商鞅方升上', art=art_s_edict),
    C(166, 168, 'works', 'card', year=-221, main='商君书', sub='法家经典', art=art_s_book),
    C(168, 170, 'end', 'card', year=-221, main='立木为信', sub='变法者的起点', art=art_s_gate),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='肆拾陆', col=QINXUAN, acc=FATONG, born=-390, died=-338, age0=-390,
    born_lab='约前390年', died_lab='前338年', years_txt='约公元前390 — 前338',
    hook_q='他让秦国变强 · 为什么秦人不怜他？',
    name_line='公孙鞅 · 卫鞅', name='商鞅', seal='商君', title_art=art_s_title,
    q1='千古变法者？', q2='刻薄寡恩人？',
    end_art=art_s_legacy, end_big='徙木立信', end_seal='商君',
    end_l1='他让秦国强了一百多年', end_l2='却没能为自己留一条退路',
    end_brush='便国不法古', end_ask='改革者注定孤独吗？评论区聊聊', next='孙武'),
    scenes=dict(chapter=scene_chapter, muzi=scene_muzi))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
