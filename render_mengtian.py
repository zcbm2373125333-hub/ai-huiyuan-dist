"""千古人物志 · 第伍拾叁集 · 蒙恬 (？–前210)
Look: 边沙黄 + 铁甲青, 烽燧 corner borders, a 长城 chapter card: wall segments climb the ridge (0→3→6→9) and in the
last chapter one segment crumbles.
Set pieces: 6-beat 攻破齐国, 8-beat 北击匈奴, 6-beat 却匈奴七百里, custom 8-beat scene 'changcheng' (起临洮至辽东),
6-beat 秦直道, 6-beat 伪诏赐死, 6-beat 绝地脉.
Birth year unknown: the HUD hides ages (no_age).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_lisi as Ls            # engine + helpers (previous episode)
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
from render_kongzi import slips, bundle
from render_songtaizu import tent
from render_sunwu import army, banner
from render_lisi import emperor, eunuch

F.RIPPLE = False
BIANSHA = (178, 146, 96)            # 边沙黄
TIEJIA = (48, 64, 74)               # 铁甲青
S.LAYERS.append(('biansha', BIANSHA, 0.9, 1.0))
S.LAYERS.append(('tiejia', TIEJIA, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='塞', life='蒙', court='秦', night='夜', war='战', empire='城', works='城', fate='诏', death='死', end='城')
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
G.THEMES['empire']['sun'] = (BIANSHA, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (TIEJIA, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

FRONTIER = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(FRONTIER)
for _k in range(3):                 # 戈壁 dune lines
    _y = 1460 + _k * 22
    _d.line([(60 + i * 40, _y + 8 * math.sin(i * 0.7 + _k)) for i in range(25)], fill=BIANSHA + (50,), width=3)
for _x in (120, 960):               # 烽燧 at the margins
    _d.polygon([(_x - 30, 1440), (_x + 30, 1440), (_x + 20, 1360), (_x - 20, 1360)], fill=(120, 100, 76, 60))
    _d.rectangle((_x - 24, 1350, _x + 24, 1362), fill=(120, 100, 76, 60))
MTN_COL = {'night': (30, 34, 40), 'death': (62, 58, 56), 'war': (110, 64, 50), 'fate': (96, 92, 86)}
def draw_background(t, theme):
    """阴山: bare ridges, gobi dune lines and beacon towers at the margins; a smoke wisp drifts from each beacon."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 184, 170), (160, 150, 130), MTN_COL.get(theme, (120, 110, 92))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(FRONTIER)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for x in (120, 960):
        for k in range(3):
            q = (t * 0.2 + k / 3) % 1
            d.ellipse((x - 14 - 20 * q, 1340 - 160 * q - 12, x + 14 + 20 * q, 1340 - 160 * q + 12), fill=(110, 110, 110, int(60 * (1 - q))))
    canvas.alpha_composite(ov)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """烽燧: a small beacon tower with a flame in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=TIEJIA + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=TIEJIA + (220,), width=3)
        bx, by = x + sx * 46, y + sy * 70
        d.polygon([(bx - 22, by + sy * 30), (bx + 22, by + sy * 30), (bx + 15, by - sy * 30), (bx - 15, by - sy * 30)], fill=BIANSHA + (230,))
        d.ellipse((bx - 10, by - sy * 52 - 10, bx + 10, by - sy * 52 + 10), fill=ZHU + (220,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def meng(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, armour=True, **kw):
    """蒙恬: Qin general — helmet with a crest, lamellar armour panel, red cloak flap, sword."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else 'knot', layer=layer, kneel=kneel, bow=b,
                  sword=kw.pop('sword', None), **kw)
    d = A.d[layer]
    if up and armour:
        A.d['red'].polygon([(x - 0.02 * h, y - 1.05 * h), (x + 0.02 * h, y - 1.05 * h), (x - dir * 0.06 * h, y - 1.18 * h)], fill=255)
        A.d['tiejia'].rectangle((x - 0.1 * h, y - 0.72 * h, x + 0.1 * h, y - 0.45 * h), fill=255)
        for k in range(4):
            A.d['biansha'].line((x - 0.1 * h, y - 0.7 * h + k * 0.07 * h, x + 0.1 * h, y - 0.7 * h + k * 0.07 * h), fill=200, width=2)
        A.d['red'].polygon([(x - dir * 0.08 * h, y - 0.78 * h), (x - dir * 0.2 * h, y - 0.3 * h), (x - dir * 0.06 * h, y - 0.36 * h)], fill=230)
    return hand

def soldier(A, x, y, h, dir=1, layer='tiejia', **kw):
    kw.setdefault('arm', 40)
    return person(A, x, y, h, dir=dir, robe=False, hat='helmet', spear=True, layer=layer, **kw)

def xiongnu(A, x, y, s, dir=-1, ph=0.0, layer='mid'):
    horse(A, x, y, s, dir, ph, layer=layer, moving=True)
    person(A, x - dir * 0.05 * s, y - 0.66 * s, 0.6 * s, dir=dir, arm=120, hat='none', robe=False, layer=layer)
    A.d[layer].arc((x - 0.25 * s, y - 1.05 * s, x + 0.05 * s, y - 0.65 * s), 90, 270, fill=255, width=4)

def wall(A, pts, h=60, layer='biansha', p=1.0):
    n = max(1, int((len(pts) - 1) * p))
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        A.d[layer].polygon([(x0, y0), (x1, y1), (x1, y1 - h), (x0, y0 - h)], fill=255)
        for k in range(3):
            fx = lerp(x0, x1, (k + 0.3) / 3); fy = lerp(y0, y1, (k + 0.3) / 3)
            A.d[layer].rectangle((fx - 8, fy - h - 14, fx + 8, fy - h), fill=255)
        A.d['ink'].line((x0, y0 - h, x1, y1 - h), fill=160, width=2)
    for i in range(0, n + 1, 3):
        x, y = pts[i]
        A.d['tiejia'].rectangle((x - 22, y - h - 50, x + 22, y), fill=230)

def brush(A, x, y, s, ang=-0.4, hair=1.0):
    ca, sa = math.cos(ang), math.sin(ang)
    def R(u, v): return (x + u * ca - v * sa, y + u * sa + v * ca)
    A.d['biansha'].polygon([R(0, -0.04 * s), R(0.8 * s, -0.04 * s), R(0.8 * s, 0.04 * s), R(0, 0.04 * s)], fill=255)
    if hair > 0:
        A.d['ink'].polygon([R(0.8 * s, -0.06 * s), R((0.8 + 0.3 * hair) * s, 0), R(0.8 * s, 0.06 * s)], fill=255)

# ================================================================ chapter card
RIDGE = [(120 + i * 70, 1220 - 140 * math.sin(i * 0.5) - i * 12) for i in range(13)]
CH = {16: (0, 0.0), 48: (3, 0.0), 80: (6, 0.0), 112: (12, 0.0), 144: (12, 1.0)}
def art_wall_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g, crumble = CH.get(kb, (3, 0.0))
    prev = {16: 0, 48: 0, 80: 3, 112: 6, 144: 12}.get(kb, 0)
    q = ease_out(u / (1.2 * P))
    A.d['mid'].polygon([(60, 1260)] + [(x, y + 20) for x, y in RIDGE] + [(W - 60, 1260)], fill=150)
    n = lerp(prev, g, q) if not crumble else 12
    if n >= 1:
        wall(A, RIDGE[:int(n) + 1], h=46)
    if crumble:
        x, y = RIDGE[6]
        for k in range(6):
            A.d['biansha'].rectangle((x - 30 + k * 12, y - 30 + 80 * q * (k % 3) / 2, x - 18 + k * 12, y - 18 + 80 * q * (k % 3) / 2), fill=255)
        A.d['mid'].rectangle((x - 36, y - 70, x + 36, y + 4), fill=int(255 * q))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_wall_chapter)
    ink_in(cv, text_img(no, SERIF, 56, TIEJIA, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_t_hook_army(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (1.4 * P)) * 30) + 1
    for i in range(n):
        soldier(A, 100 + (i % 15) * 60, GROUND - (i // 15) * 60, 80, dir=1)

def art_t_hook_wall(A, cv, t, u):
    A.d['mid'].polygon([(60, GROUND)] + [(x, y + 20) for x, y in RIDGE] + [(W - 60, GROUND)], fill=150)
    wall(A, RIDGE, h=50, p=clamp(u / (1.6 * P)))
    ground(A, GROUND)

def art_t_hook_brush(A, cv, t, u):
    ground(A, GROUND)
    brush(A, 340, 1160, 420, ang=-0.3, hair=ease_out(u / P))

def art_t_hook_edict(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 460, 160, clamp(u / P), layer='wash')

# ================================================================ 第一回 将门之后
def art_t_grandpa(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    rider(A, lerp(980, 400, ease_out(u / (3 * P))), GROUND, 140, dir=-1, ph=t * 6, spear=True)
    A.flush(cv)
    paste(cv, text_img('祖父蒙骜 · 自齐事秦', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('蒙骜', 54), 260, 1020, t, t - u + P, rot=-5)

def art_t_father(A, cv, t, u):
    tent(A, 540, GROUND, 420, 280, layer='tiejia')
    ground(A, GROUND)
    meng(A, 300, GROUND, 210, dir=1, arm=60)
    soldier(A, 760, GROUND, 160, dir=-1)
    soldier(A, 840, GROUND, 160, dir=-1)
    A.flush(cv)
    paste(cv, text_img('父亲蒙武 · 秦国名将', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_law(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='biansha')
    meng(A, 300, GROUND, 190, dir=1, kneel=True, bow=20, arm=90, armour=False)
    slips(A, 440, GROUND - 74, int(clamp(u / (2 * P)) * 10) + 1, 90, layer='tiejia')
    A.flush(cv)
    paste(cv, text_img('尝书狱典文学', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('狱法', 56), 860, 1020, t, t - u + P, rot=6)

def art_t_chu(A, cv, t, u):
    ground(A, GROUND)
    army(A, lerp(-100, 300, ease_out(u / (2 * P))), GROUND, 7, dir=1, layer='tiejia', t=t, march=True, h=110)
    banner(A, 860, GROUND, 300, t, layer='red', fallen=ease_out((u - 2 * P) / P))
    A.flush(cv)
    paste(cv, text_img('父蒙武与王翦 · 灭楚', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('灭楚', 56), 260, 1020, t, t - u + P, rot=-5)

def art_t_general(A, cv, t, u):
    for k in range(3):
        A.d['tiejia'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    meng(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('因家世得为秦将', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('秦将', 56), 860, 1020, t, t - u + P, rot=6)

def art_t_qi(A, cv, t, u):
    """6-beat set piece: 攻破齐国 — the last of the six states: Qin columns march on Linzi; the gate opens; the King of Qi surrenders."""
    ph = u / P
    city_wall(A, 520, 1000, 1080, gate_x=760, label='临淄', layer='mid', open_=clamp((ph - 2.5) / 1))
    ground(A, GROUND)
    army(A, lerp(-200, 160, ease_out(ph / 2.5)), GROUND, 6, dir=1, layer='tiejia', t=t, march=ph < 2.5, h=110)
    meng(A, lerp(-80, 460, ease_out(ph / 2.5)), GROUND, 170, dir=1, arm=60)
    if ph > 3.5:
        person(A, 760, GROUND, 170, dir=-1, robe=True, hat='crown', kneel=True, bow=40, arm=100, layer='ink')
    A.flush(cv)
    lab = '自燕南下 · 直取临淄' if ph < 2.5 else ('齐军不战' if ph < 3.5 else '齐王建降 · 六国尽灭')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('齐亡', 56, INK), 260, 1020, t, t - u + 3.5 * P, rot=-5)

def art_t_neishi(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='tiejia')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 210, dir=-1, arm=lerp(20, 90, ease_out(u / 0.6)))
    meng(A, 380, GROUND, 200, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('内史', 60), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('掌治京师', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 北逐匈奴
def art_t_prophecy(A, cv, t, u):
    for k in range(40):
        a = k * 2.399
        r = 20 * math.sqrt(k)
        A.d['wash'].ellipse((540 + r * math.cos(a + t * 0.2) - 3, 900 + r * math.sin(a + t * 0.2) * 0.6 - 3, 540 + r * math.cos(a + t * 0.2) + 3, 900 + r * math.sin(a + t * 0.2) * 0.6 + 3), fill=220)
    ground(A, GROUND)
    scroll(A, 540, 1160, 360, 140, clamp(u / P), layer='wash')
    person(A, 260, GROUND, 180, dir=1, robe=True, hat='knot', bow=20, arm=110, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('亡秦者胡也', SERIF, 56, ZHU, 'Black', bleed=False, spacing=10), W / 2, 830, t, t - u + 0.5, 0.5)
    note_in(cv, '卢生献录图书 见史记秦始皇本纪', t, t - u + P)

def art_t_300k(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 40) + 1
    for i in range(n):
        soldier(A, 80 + (i % 20) * 48, GROUND - (i // 20) * 80, 70, dir=1, ph=t * 6 + i)
    A.flush(cv)
    paste(cv, text_img(f'发兵三十万 · 北击胡', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('北伐', 56), 860, 1020, t, t - u + P, rot=6)

def art_t_battle(A, cv, t, u):
    """8-beat set piece: 北击匈奴 — Xiongnu horsemen pour over the ridge; the Qin crossbow line looses volleys; the cavalry turns and flees north."""
    ph = u / P
    A.d['mid'].polygon([(60, GROUND), (300, GROUND - 200), (600, GROUND - 120), (900, GROUND - 240), (W - 60, GROUND)], fill=130)
    ground(A, GROUND)
    if ph < 4.5:
        for j in range(5):
            xiongnu(A, lerp(1200, 700, ease_out(ph / 2.5)) + j * 90, GROUND - (j % 2) * 30, 110, dir=-1, ph=t * 10 + j)
    else:
        for j in range(5):
            xiongnu(A, lerp(700, 1300, ease_out((ph - 4.5) / 2.5)) + j * 90, GROUND - (j % 2) * 30, 100, dir=1, ph=t * 10 + j)
    for j in range(6):
        soldier(A, 120 + j * 70, GROUND, 120, dir=1, kneel=j % 2 == 0, arm=90)
    if 2 < ph < 5:
        for k in range(8):
            q = ((t * 1.6 + k / 8) % 1)
            arrow(A, lerp(500, 900, q), GROUND - 120 - 120 * math.sin(q * math.pi), -0.4 + 0.8 * q, 50)
    meng(A, 140, GROUND - 200, 140, dir=1, arm=120)
    A.flush(cv)
    lab = '匈奴骑兵南下' if ph < 2 else ('强弩齐发' if ph < 4.5 else '匈奴大败北逃')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4.5 else TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('河南地', 50), 860, 1440, t, t - u + 5 * P, rot=6)

def art_t_hetao(A, cv, t, u):
    A.d['wash'].rounded_rectangle((110, 860, 970, 1320), radius=20, fill=170)
    pts = [(200, 1250), (260, 950), (540, 900), (820, 950), (880, 1250)]
    A.d['ocean'].line(pts, fill=220, width=12)
    q = ease_out(u / (2 * P))
    A.d['biansha'].polygon([(260, 1250), (300, 980), (540, 940), (780, 980), (820, 1250)], fill=int(160 * q))
    n = min(44, int(clamp(u / (3 * P)) * 44))
    for i in range(n):
        x = 330 + (i % 11) * 40; y = 1000 + (i // 11) * 55
        A.d['tiejia'].rectangle((x - 8, y - 8, x + 8, y + 8), fill=255)
    A.flush(cv)
    paste(cv, text_img(f'收河南地 · 置{cn_num(max(1, n))}县', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('黄河', 44), 540, 1290, t, t - u + 0.3)

def art_t_migrate(A, cv, t, u):
    A.d['grass'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=150)
    ground(A, GROUND)
    for j in range(6):
        x = lerp(-200, 1100, ((t * 0.08 + j / 6) % 1))
        person(A, x, GROUND - 40, 110, dir=1, robe=True, hat='knot', load=j % 2 == 0, ph=t * 4 + j, arm=160 if j % 2 == 0 else 30, layer='ink')
    carriage(A, lerp(-100, 1000, ((t * 0.08 + 0.5) % 1)), GROUND - 40, 70, dir=1, wheel=t * 4, ph=t * 6, canopy=False, layer='mid')
    A.flush(cv)
    paste(cv, text_img('徙谪实之 · 移民屯边', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_awe(A, cv, t, u):
    """6-beat set piece: 却匈奴七百里 — the frontier line pushes north; the nomad camps withdraw beyond it, mile counter climbing."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 860, 970, 1360), radius=20, fill=170)
    y_line = lerp(1300, 940, ease_out(ph / 4.5))
    A.d['tiejia'].line((130, y_line, 950, y_line), fill=255, width=10)
    A.d['biansha'].rectangle((130, y_line, 950, 1340), fill=110)
    for j in range(5):
        cx = 200 + j * 170; cy = min(y_line - 60, 1100 - (j % 2) * 40)
        A.d['mid'].chord((cx - 40, cy - 30, cx + 40, cy + 30), 180, 360, fill=230)
    A.flush(cv)
    li_ = int(lerp(0, 700, clamp(ph / 4.5)))
    paste(cv, text_img(f'却匈奴 {li_} 余里', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('胡人不敢南下而牧马', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.5) / 0.4))

# ================================================================ 第三回 万里长城
def scene_changcheng(cv, t, c, k):
    """8-beat custom scene: 起临洮 至辽东 — a map line draws itself west to east across the north; the counter climbs
    to 万余里; below, files of conscripts haul stones up a ridge and a wall section rises."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['wash'].rounded_rectangle((110, 640, 970, 960), radius=20, fill=160)
    path = [(160, 900), (260, 820), (380, 760), (520, 720), (660, 700), (800, 690), (920, 730)]
    q = clamp(ph / 6.5)
    nseg = len(path) - 1
    m = q * nseg
    for i in range(nseg):
        ff = clamp(m - i)
        if ff <= 0: break
        (x0, y0), (x1, y1) = path[i], path[i + 1]
        A.d['biansha'].line((x0, y0, lerp(x0, x1, ff), lerp(y0, y1, ff)), fill=255, width=10)
    A.d['mid'].polygon([(60, GROUND)] + [(x, y + 40) for x, y in RIDGE] + [(W - 60, GROUND)], fill=150)
    wall(A, RIDGE, h=50, p=clamp(ph / 7))
    for j in range(5):
        x = lerp(100, 900, ((t * 0.07 + j / 5) % 1))
        person(A, x, GROUND, 90, dir=1, robe=False, hat='knot', load=True, ph=t * 5 + j, arm=160, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '万里长城', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=53)
    fx.flush(cv)
    li_ = int(lerp(0, 10000, q))
    paste(cv, text_img(f'起临洮 至辽东 · {li_} 余里', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    stamp(cv, seal('临洮', 34, TIEJIA), 160, 940, t, s0 + 0.3)
    if ph > 6:
        stamp(cv, seal('辽东', 34, ZHU), 920, 770, t, s0 + 6 * P)
    paste(cv, text_img('因地形 用制险塞 · 连接秦赵燕旧长城', SERIF, 38, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 1) / 0.4))

def art_t_toil(A, cv, t, u):
    for k in range(60):
        q = (t * 0.5 + k / 60) % 1
        A.d['wash'].ellipse((80 + (k * 19) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 19) % 920 + 4, lerp(620, 1420, q) + 4), fill=220)
    A.d['mid'].polygon([(60, GROUND), (540, GROUND - 300), (W - 60, GROUND)], fill=170)
    for j in range(6):
        x = 200 + j * 120
        person(A, x, GROUND - 300 * (1 - abs(x - 540) / 480), 100, dir=1, robe=False, hat='knot', load=True, bow=30, ph=t * 2 + j, arm=160, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('暴师于外十余年 · 戍卒之苦', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_zhidao(A, cv, t, u):
    """6-beat set piece: 秦直道 — the road is cut straight from 九原 to 云阳 through hills:堑山堙谷; the mile counter reaches 1800."""
    ph = u / P
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260 - 60 * (k % 2)), (x + 150, GROUND)], fill=180)
    q = ease_out(clamp(ph / 4.5))
    A.d['biansha'].polygon([(530, GROUND), (550, GROUND), (550 + 20 * q, GROUND - 560 * q), (530 - 20 * q, GROUND - 560 * q)], fill=255)
    A.d['dune'].rectangle((500, GROUND - 560 * q, 580, GROUND), fill=120)
    for j in range(3):
        rider(A, 540, lerp(GROUND, GROUND - 500 * q, ((t * 0.2 + j / 3) % 1)), lerp(80, 30, ((t * 0.2 + j / 3) % 1)), dir=1, ph=t * 8 + j, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    li_ = int(lerp(0, 1800, clamp(ph / 4.5)))
    paste(cv, text_img(f'自九原抵云阳 · {li_} 里', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('堑山堙谷 · 秦代高速公路', SERIF, 42, INK, 'Black', bleed=False, spacing=2), W / 2, 835, 1, clamp((ph - 1) / 0.4))

def art_t_fusu(A, cv, t, u):
    tent(A, 540, GROUND, 420, 280, layer='tiejia')
    ground(A, GROUND)
    person(A, 360, GROUND, 200, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    meng(A, 720, GROUND, 210, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('长子扶苏谏焚书 · 被派往上郡监军', SERIF, 42, TIEJIA, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('上郡', 56), 860, 1020, t, t - u + P, rot=6)

def art_t_brothers(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    meng(A, 380, GROUND, 200, dir=1, arm=60)
    person(A, 700, GROUND, 200, dir=-1, robe=True, hat='knot', arm=60, layer='tiejia')
    A.flush(cv)
    paste(cv, text_img('弟蒙毅位至上卿 · 出则参乘 入则御前', SERIF, 40, TIEJIA, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('蒙毅', 56), 860, 1020, t, t - u + P, rot=6)

def art_t_brush(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='biansha')
    brush(A, 380, GROUND - 110, 300, ang=-0.15, hair=ease_out(u / P))
    A.flush(cv)
    paste(cv, text_img('以枯木为管 鹿毛为柱 羊毛为被', SERIF, 42, TIEJIA, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '蒙恬造笔出自古今注 实则毛笔早已有之', t, t - u + 0.5 * P)

# ================================================================ 第四回 沙丘矫诏
def art_t_tour(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 280), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    carriage(A, lerp(1000, 300, ease_out(u / (3 * P))), GROUND, 110, dir=-1, wheel=t * 4, ph=t * 6, layer='tiejia')
    person(A, 820, GROUND, 170, dir=1, robe=True, hat='knot', arm=60, layer='mid')
    A.flush(cv)
    paste(cv, text_img('始皇东巡 · 途中病 遣蒙毅还祷山川', SERIF, 42, TIEJIA, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_t_shaqiu(A, cv, t, u):
    tent(A, 540, GROUND, 460, 300, layer='mid')
    ground(A, GROUND)
    eunuch(A, 330, GROUND, 180, dir=1, bow=15, arm=100, layer='ink')
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='knot', bow=20, arm=60, layer='tiejia')
    A.flush(cv)
    paste(cv, text_img('始皇崩 · 赵高李斯合谋', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('沙丘', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_t_edict(A, cv, t, u):
    """6-beat set piece: 伪诏赐死 — the envoy rides north with the sealed edict; Fusu reads it and weeps; Meng Tian grips his arm."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        rider(A, lerp(-100, 900, ease_out(ph / 2)), GROUND, 130, dir=1, ph=t * 10)
    else:
        tent(A, 540, GROUND, 460, 300, layer='tiejia')
        person(A, 380, GROUND, 200, dir=1, robe=True, hat='knot', kneel=ph > 3.5, bow=40 if ph > 3.5 else 10, arm=110, layer='ink')
        scroll(A, 470, GROUND - 160, 160, 50, 1.0, layer='wash')
        meng(A, 680, GROUND, 210, dir=-1, arm=lerp(40, 140, clamp((ph - 3.6) / 0.4)))
    A.flush(cv)
    lab = '使者奉诏至上郡' if ph < 2 else ('扶苏为人子不孝 蒙恬为人臣不忠' if ph < 3.6 else '陛下居外 未立太子 安知其非诈')
    paste(cv, text_img(lab, SERIF, 44, ZHU if 2 <= ph < 3.6 else TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph > 2:
        stamp(cv, seal('赐死', 60), 860, 1020, t, t - u + 2 * P, rot=6)

def art_t_fusu_dies(A, cv, t, u):
    tent(A, 540, GROUND, 460, 300, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, robe=True, hat='knot', fall=-80 * ease_out((u - 2 * P) / P), arm=140, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('父而赐子死 尚安复请', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)

def art_t_refuse(A, cv, t, u):
    A.d['ink'].rectangle((320, 900, 760, GROUND), outline=255, width=8)
    for k in range(9):
        A.d['ink'].line((320 + k * 55, 900, 320 + k * 55, GROUND), fill=200, width=4)
    meng(A, 540, GROUND, 200, dir=1, arm=-8, old=0.4)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('蒙恬不肯死 · 囚于阳周', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('阳周', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_t_yi(A, cv, t, u):
    for k in range(4):
        A.d['mid'].polygon([(160 + k * 260 - 200, GROUND), (160 + k * 260, GROUND - 260), (160 + k * 260 + 200, GROUND)], fill=150)
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, robe=True, hat='knot', kneel=True, bow=lerp(10, 50, ease_out(u / (2 * P))), arm=-8, layer='tiejia')
    A.flush(cv)
    paste(cv, text_img('代郡 · 蒙毅被杀', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('赵高之怨', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_t_ziying(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 190, dir=-1, arm=20)
    person(A, 380, GROUND, 200, dir=1, robe=True, hat='knot', kneel=True, bow=30, arm=lerp(60, 130, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.flush(cv)
    type_in(cv, text_img('诛杀忠臣而立无节行之人', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('子婴谏', 50, INK), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第五回 绝地脉
def art_t_poison(A, cv, t, u):
    """6-beat set piece: 绝地脉 — in the cell he recounts his loyalty, then wonders whether the wall he built cut the veins of the earth,
    and drinks the poison."""
    ph = u / P
    A.d['ink'].rectangle((200, 880, 880, GROUND), outline=255, width=8)
    for k in range(13):
        A.d['ink'].line((200 + k * 56, 880, 200 + k * 56, GROUND), fill=150, width=3)
    wall(A, [(240, 1080), (360, 1040), (480, 1060), (600, 1020), (720, 1050), (840, 1010)], h=30, layer='mid')
    meng(A, 540, GROUND, 210, dir=1, kneel=ph > 3, bow=20 if ph > 3 else 0, arm=lerp(-8, 140, clamp((ph - 4) / 0.4)), fall=-80 * clamp((ph - 5.2) / 0.6))
    ground(A, GROUND)
    A.flush(cv)
    lab1 = '吾何罪于天 无过而死乎' if ph < 3 else '起临洮属之辽东 城堑万余里'
    paste(cv, text_img(lab1, SERIF, 44, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph > 3:
        paste(cv, text_img('此其中不能无绝地脉哉 此乃恬之罪也', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 835, 1, clamp((ph - 3) / 0.4))

def art_t_dazexiang(A, cv, t, u):
    for k in range(60):
        q = (t * 0.6 + k / 60) % 1
        A.d['wash'].line((80 + (k * 19) % 920, lerp(620, 1420, q), 80 + (k * 19) % 920 - 10, lerp(620, 1420, q) + 30), fill=180, width=2)
    ground(A, GROUND)
    for j in range(6):
        person(A, 200 + j * 120, GROUND, 130, dir=1, robe=False, hat='knot', arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='ink')
    banner(A, 860, GROUND, 300, t, layer='red')
    A.flush(cv)
    paste(cv, text_img('陈胜吴广起事 · 天下响应', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('大泽乡', 50, INK), 260, 1020, t, t - u + P, rot=-5)

def art_t_qinfall(A, cv, t, u):
    palace(A, 540, 1260, 420, collapse=ease_out(u / (2.5 * P)), layer='tiejia')
    flames(A, 540, 1200, 520, 200 * ease_out(u / P), t, n=7, seed=2061, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('北边无人 · 秦二世而亡', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_sima(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    A.flush(cv)
    type_in(cv, text_img('不以此时强谏 而阿意兴功', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('其兄弟遇诛 不亦宜乎', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.6 * P, 0.5)
    stamp(cv, seal('太史公曰', 44), 860, 1020, t, t - u + P, rot=6)

def art_t_heritage(A, cv, t, u):
    A.d['mid'].polygon([(60, GROUND)] + [(x, y + 20) for x, y in RIDGE] + [(W - 60, GROUND)], fill=150)
    wall(A, RIDGE, h=50)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('长城列入世界遗产名录', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('世界遗产', 46), 860, 1020, t, t - u + P, rot=6)

def art_t_lintao(A, cv, t, u):
    q = ease_out(u / (1.6 * P))
    A.d['biansha'].polygon([(60, GROUND)] + [(x, y + 20) for x, y in RIDGE] + [(W - 60, GROUND)], fill=110)
    wall(A, RIDGE, h=50, p=1.0)
    for j in range(3):
        x, y = RIDGE[j * 5]
        A.d['red'].ellipse((x - 10, y - 110 - 10, x + 10, y - 110 + 10), fill=int(220 * q))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('烽火连天 · 守了两千年', SERIF, 46, TIEJIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    wall(A, [(700, 1380), (780, 1360), (860, 1370), (940, 1350)], h=30)

def art_t_title(A, cv, t, u):
    wall(A, [(600, 1460), (680, 1420), (760, 1440), (840, 1390), (920, 1410), (1000, 1370)], h=50)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    meng(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '将门之后'), 48: ('第二回', '北逐匈奴'), 80: ('第三回', '万里长城'),
            112: ('第四回', '沙丘矫诏'), 144: ('第五回', '绝地脉')}

CARDS = [
    C(0, 2, 'war', 'num', num='三十万大军', line='北逐匈奴', art=art_t_hook_army),
    C(2, 4, 'empire', 'num', num='万里长城', line='他主持修建', art=art_t_hook_wall),
    C(4, 6, 'works', 'num', num='一支毛笔', line='传说是他造的', art=art_t_hook_brush),
    C(6, 8, 'death', 'num', num='一纸假诏书', line='要了他的命', art=art_t_hook_edict),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 将门之后
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-249, main='祖父蒙骜', sub='自齐入秦', note='蒙恬生年不详', art=art_t_grandpa),
    C(22, 26, 'war', 'card', year=-240, main='父亲蒙武', sub='三代为将', art=art_t_father),
    C(26, 30, 'works', 'card', year=-230, main='习狱法', sub='先文后武', art=art_t_law),
    C(30, 34, 'war', 'card', year=-224, main='父亲灭楚', sub='与王翦同行', art=art_t_chu),
    C(34, 38, 'court', 'card', year=-221, main='初为秦将', sub='将门之子', art=art_t_general),
    C(38, 44, 'war', 'card', year=-221, main='攻破齐国', sub='最后一战', art=art_t_qi),
    C(44, 48, 'empire', 'card', year=-221, main='拜为内史', sub='京畿长官', art=art_t_neishi),
    # ---- 第二回 北逐匈奴
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'night', 'card', year=-215, main='亡秦者胡', sub='一句谶语', art=art_t_prophecy),
    C(54, 58, 'empire', 'card', year=-215, main='三十万众', sub='奉命北伐', art=art_t_300k),
    C(58, 66, 'war', 'card', year=-215, main='北击匈奴', sub='强弩破骑', art=art_t_battle),
    C(66, 70, 'works', 'card', year=-214, main='收河南地', sub='河套归秦', art=art_t_hetao),
    C(70, 74, 'life', 'card', year=-214, main='徙民实边', sub='屯垦戍边', art=art_t_migrate),
    C(74, 80, 'empire', 'card', year=-214, main='威震匈奴', sub='北方安宁', art=art_t_awe),
    # ---- 第三回 万里长城
    C(80, 82, 'works', 'chapter'),
    C(82, 90, 'works', 'changcheng', year=-214),
    C(90, 94, 'death', 'card', year=-213, main='戍卒之苦', sub='长城的代价', art=art_t_toil),
    C(94, 100, 'works', 'card', year=-212, main='秦直道', sub='一千八百里', art=art_t_zhidao),
    C(100, 104, 'fate', 'card', year=-212, main='扶苏监军', sub='君臣相知', art=art_t_fusu),
    C(104, 108, 'court', 'card', year=-212, main='兄弟同荣', sub='蒙氏极盛', art=art_t_brothers),
    C(108, 112, 'life', 'card', year=-211, main='蒙恬造笔', sub='一个美丽的传说', art=art_t_brush),
    # ---- 第四回 沙丘矫诏
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'fate', 'card', year=-210, main='始皇东巡', sub='最后一次出巡', art=art_t_tour),
    C(118, 122, 'night', 'card', year=-210, main='沙丘之变', sub='赵高李斯', art=art_t_shaqiu),
    C(122, 128, 'death', 'card', year=-210, main='伪诏赐死', sub='千里之外', art=art_t_edict),
    C(128, 132, 'death', 'card', year=-210, main='扶苏自尽', sub='一念之差', art=art_t_fusu_dies),
    C(132, 136, 'night', 'card', year=-210, main='不肯就死', sub='囚于阳周', art=art_t_refuse),
    C(136, 140, 'death', 'card', year=-210, main='蒙毅被杀', sub='斩草除根', art=art_t_yi),
    C(140, 144, 'court', 'card', year=-210, main='子婴进谏', sub='无人能救', art=art_t_ziying),
    # ---- 第五回 绝地脉
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'death', 'card', year=-210, main='吞药自尽', sub='三代忠良', art=art_t_poison),
    C(152, 156, 'war', 'card', year=-209, main='大泽乡', sub='天下大乱', art=art_t_dazexiang),
    C(156, 160, 'death', 'card', year=-206, main='秦亡', sub='北边再无蒙恬', art=art_t_qinfall),
    C(160, 164, 'works', 'card', year=-91, main='太史公曰', sub='另一种评价', art=art_t_sima),
    C(164, 168, 'empire', 'card', year=1987, main='世界遗产', sub='长城', art=art_t_heritage),
    C(168, 170, 'end', 'card', year=1987, main='长城仍在', sub='两千年风雨', art=art_t_lintao),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='伍拾叁', col=TIEJIA, acc=BIANSHA, born=-260, died=-210, no_age=True,
    born_lab='生年不详', died_lab='前210年', years_txt='生年不详 — 公元前210',
    hook_q='他为秦朝挡住匈奴 · 为什么死于一纸诏书？',
    name_line='蒙恬 · 秦国名将', name='蒙恬', seal='内史', title_art=art_t_title,
    q1='忠勇名将？', q2='愚忠误国？',
    end_art=art_t_legacy, end_big='万里长城', end_seal='内史',
    end_l1='他筑起长城 挡住了匈奴', end_l2='却挡不住宫里的一纸假诏',
    end_brush='起临洮至辽东', end_ask='如果蒙恬起兵 历史会改写吗？评论区聊聊', next='张良'),
    scenes=dict(chapter=scene_chapter, changcheng=scene_changcheng))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
