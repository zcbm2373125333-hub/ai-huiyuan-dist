"""千古人物志 · 第贰拾捌集 · 卫青 (?–前106)
Look: 石板青 + 黄铜, 武刚车轮 corner borders, a 印绶 chapter card: a herd-boy's whip turns into a stack of seals
(侯印 → 大将军印 → 大司马印) chapter by chapter.
Set pieces: 8-beat 奇袭龙城 (four columns, only one succeeds), custom 8-beat scene 'hetao' (收复河南地 map),
6-beat 筑朔方, 8-beat 夜袭右贤王, 6-beat 甘居人后, 8-beat 武刚车阵.
Birth year unknown: the HUD hides ages (no_age).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_huoqubing as Hq       # engine + helpers (previous episode)
import render_simaqian as Sm
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
from render_zhangqian import yurt, sheep

F.RIPPLE = False
SLATE = (58, 88, 96)                # 石板青
BRASS = (196, 148, 58)              # 黄铜
S.LAYERS.append(('slate', SLATE, 0.88, 1.0))
S.LAYERS.append(('brass', BRASS, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='卫', life='奴', court='汉', night='夜', war='戰', empire='将', works='朔', fate='忍', death='冢', end='卫')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire', 'works'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['war']['sun'] = (BRASS, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (SLATE, 220, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (BRASS, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

WALL = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(WALL)
_pts = [(x, 1290 - 50 * math.sin(x / 160)) for x in range(60, W - 59, 12)]
_d.line(_pts, fill=SLATE + (50,), width=8)
for _i in range(0, len(_pts), 7):
    _x, _y = _pts[_i]
    _d.rectangle((_x - 10, _y - 30, _x + 10, _y), fill=SLATE + (50,))
MTN_COL = {'night': (34, 40, 44), 'death': (60, 62, 64), 'war': (104, 70, 46), 'works': (80, 100, 104)}
def draw_background(t, theme):
    """阴山长城: steppe ridges with a faint wall line running along the hills."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(180, 186, 186), (136, 150, 152), MTN_COL.get(theme, (96, 112, 116))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 7 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(WALL)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """武刚车轮: a spoked chariot wheel in each corner on two rails."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = SLATE + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=col, width=3); d.line((x, y, x, y + sy * 180), fill=col, width=3)
        cx, cy, r = x + sx * 48, y + sy * 48, 30
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=4)
        for k in range(8):
            a = k * math.pi / 4
            d.line((cx, cy, cx + r * math.cos(a), cy + r * math.sin(a)), fill=col, width=2)
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=BRASS + (240,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def wei(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, armour=True, **kw):
    """卫青: broad-shouldered, plain helmet with a brass crest plate, long dark cape; calm stance."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if up and armour:
        A.d['brass'].rectangle((x - 0.05 * h, y - 1.02 * h, x + 0.05 * h, y - 0.96 * h), fill=255)
        A.d['slate'].polygon([(x - dir * 0.06 * h, y - 0.84 * h), (x - dir * 0.28 * h, y - 0.05 * h), (x - dir * 0.04 * h, y - 0.1 * h)], fill=255)
    return hand

def cart(A, x, base, s, dir=1, layer='slate'):
    """武刚车: a boxy armoured wagon with a shield wall and spears."""
    d = A.d[layer]
    d.rectangle((x - 0.6 * s, base - 0.7 * s, x + 0.6 * s, base - 0.25 * s), fill=255)
    for k in range(3):
        A.d['ink'].line((x - 0.5 * s + k * 0.5 * s, base - 0.95 * s, x - 0.45 * s + k * 0.5 * s, base - 0.7 * s), fill=255, width=max(2, int(0.03 * s)))
    for wx in (-0.35, 0.35):
        A.d['ink'].ellipse((x + wx * s - 0.22 * s, base - 0.44 * s, x + wx * s + 0.22 * s, base), outline=255, width=max(3, int(0.05 * s)))

def seals_stack(A, cx, base, n, s=60, t=0.0):
    for i in range(n):
        y = base - i * 1.2 * s
        A.d['brass' if i % 2 == 0 else 'slate'].rectangle((cx - 0.6 * s, y - s, cx + 0.6 * s, y), fill=255)
        A.d['ink'].rectangle((cx - 0.15 * s, y - 1.25 * s, cx + 0.15 * s, y - s), fill=255)
        A.d['red'].line((cx + 0.6 * s, y - 0.5 * s, cx + 1.2 * s + 6 * math.sin(t * 2 + i), y + 0.3 * s), fill=255, width=6)

# ================================================================ chapter card
CH = {16: 0, 48: 1, 80: 2, 112: 3, 144: 3}
def art_seal_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = CH.get(kb, 1)
    q = ease_out(u / (1.0 * P))
    if n == 0:
        A.d['ink'].line((480, 1200, 600, 900), fill=255, width=10)
        A.d['ink'].arc((540, 820, 720, 1000), 120, 300, fill=255, width=5)
        for k in range(3):
            sheep(A, 300 + k * 220, GROUND, 70)
    else:
        seals_stack(A, 540, 1220, n, s=lerp(30, 90, q), t=t)
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_seal_chapter)
    ink_in(cv, text_img(no, SERIF, 56, SLATE, 'Black', bleed=False, spacing=12), W / 2, 1290, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_w_hook_7(A, cv, t, u):
    ground(A, GROUND)
    n = min(7, int(clamp(u / (1.6 * P)) * 7) + 1)
    for i in range(n):
        x = 160 + i * 125
        flag(A, x, GROUND, 300, t, w=60, layer='brass' if i % 2 else 'red')

def art_w_hook_shepherd(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        sheep(A, 560 + k * 100 + 10 * math.sin(t + k), GROUND, 60)
    p = ease_out(u / (1.6 * P))
    if p < 0.5:
        person(A, 340, GROUND, 200, dir=1, robe=False, hat='knot', arm=60, layer='ink')
    else:
        wei(A, 340, GROUND, 260, dir=1, arm=60, spear=True)

def art_w_hook_river(A, cv, t, u):
    pts = [(540 + 300 * math.cos(a), 1080 - 220 * math.sin(a)) for a in np.linspace(math.pi, 0, 30)]
    A.d['ocean'].line(pts, fill=200, width=30)
    p = ease_out(u / (1.6 * P))
    A.d['grass'].polygon([(240, 1100), (540, 1100 - 0 * p), (840, 1100), (840, 1100 - 200 * p), (240, 1100 - 200 * p)], fill=150)
    ground(A, GROUND)

def art_w_hook_princess(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='slate')
    ground(A, GROUND)
    person(A, 660, GROUND, 220, dir=-1, robe=True, hat='knot', female=True, arm=40, layer='ink')
    wei(A, 400, GROUND, 240, dir=1, armour=False, arm=lerp(-8, 50, ease_out(u / P)))

# ================================================================ 第一回 骑奴出身
def art_w_shepherd(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        sheep(A, 140 + k * 100 + 15 * math.sin(t * 0.8 + k), GROUND, 60)
    person(A, 760, GROUND, 160, dir=-1, robe=False, hat='knot', arm=60, layer='ink')
    for k in range(2):
        person(A, 880 + k * 70, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(30, 140, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('郑季家', 46, INK), 300, 900, t, t - u + P, rot=-5)

def art_w_prophecy(A, cv, t, u):
    ground(A, GROUND)
    person(A, 700, GROUND, 210, dir=-1, robe=False, hat='knot', arm=lerp(40, 130, 0.5 + 0.5 * math.sin(t * 2)), layer='mid')
    for k in range(5):
        A.d['ink'].ellipse((640 + k * 22, GROUND - 120, 656 + k * 22, GROUND - 104), outline=255, width=3)
    person(A, 380, GROUND, 170, dir=1, robe=False, hat='knot', arm=-8, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('人奴之生 得毋笞骂即足矣', SERIF, 46, SLATE, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 1.2 * P, 0.5)

def art_w_rider_slave(A, cv, t, u):
    palace(A, 760, GROUND, 380, layer='mid')
    ground(A, GROUND)
    carriage(A, lerp(-150, 420, ease_out(u / (2 * P))), GROUND, 140, dir=1, wheel=u * 6, ph=t * 8, moving=u < 2 * P, layer='ink')
    horse(A, lerp(-300, 240, ease_out(u / (2 * P))), GROUND, 120, dir=1, ph=t * 8, layer='ink')
    person(A, lerp(-300, 240, ease_out(u / (2 * P))), GROUND - 95, 110, dir=1, robe=False, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('平阳公主', 44), 760, 880, t, t - u + P, rot=6)

def art_w_sister(A, cv, t, u):
    palace(A, 540, 1140, 540, layer='slate')
    ground(A, GROUND)
    person(A, 460, GROUND - 30, 230, dir=1, robe=True, hat='crown', arm=40, layer='ink')
    person(A, 640, GROUND - 30, 220, dir=-1, robe=True, hat='knot', female=True, arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('卫子夫', 50), 860, 880, t, t - u + P, rot=6)

def art_w_rescue(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    A.d['mid'].rectangle((200, 960, 560, GROUND), fill=190)
    Sm.bars(A, 220, 540, 980, GROUND, n=7)
    wei(A, 380, GROUND, 180, dir=1, armour=False, kneel=True, bow=20, arm=-8)
    x = lerp(1100, 680, ease_out(u / (1.5 * P)))
    person(A, x, GROUND, 210, dir=-1, robe=False, hat='helmet', sword=lerp(40, 150, ease_out((u - 1.5 * P) / 0.3)), arm=100, layer='ink')
    A.flush(cv)
    stamp(cv, seal('公孙敖', 50), 860, 880, t, t - u + P, rot=6)

def art_w_jianzhang(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 90, ease_out(u / 0.5)), layer='ink')
    wei(A, 360, GROUND, 220, dir=1, armour=False, kneel=True, bow=40, arm=100)
    A.flush(cv)
    stamp(cv, seal('建章监', 50), 260, 880, t, t - u + P, rot=-5)

def art_w_years(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        x = 160 + k * 240
        wei(A, x, GROUND, 150 + k * 25, dir=1, armour=k >= 2, arm=40)
    A.flush(cv)
    paste(cv, text_img('十年磨砺', SERIF, 52, SLATE, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))

def art_w_first_cmd(A, cv, t, u):
    ground(A, GROUND)
    wei(A, 380, GROUND, 280, dir=1, arm=lerp(40, 160, ease_out(u / P)), spear=True)
    for k in range(3):
        flag(A, 680 + k * 120, GROUND, 340, t, w=80, layer='brass' if k == 1 else 'red')
    A.flush(cv)
    stamp(cv, seal('车骑将军', 46), 790, 860, t, t - u + P, rot=6)

# ================================================================ 第二回 龙城初捷
def art_w_longcheng(A, cv, t, u):
    """8-beat set piece: 四路出击 — four columns leave four passes; three are beaten back or lost; only 卫青 reaches 龙城."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 780, 970, 1420), radius=24, fill=190)
    A.d['slate'].line((130, 1300, 950, 1300), fill=200, width=10)
    passes = [(230, '上谷'), (430, '代'), (630, '云中'), (830, '雁门')]
    target = (330, 900)
    for i, (x, nm) in enumerate(passes):
        q = clamp(ph / 4)
        if i == 0:
            ex, ey = lerp(x, target[0], q), lerp(1300, target[1], q)
            A.d['brass'].line((x, 1300, ex, ey), fill=255, width=10)
        else:
            fail = 0.4 + 0.1 * i
            qq = min(q, fail)
            ex, ey = x + (i - 1.5) * 60 * qq / fail, lerp(1300, 1000, qq)
            A.d['ink'].line((x, 1300, ex, ey), fill=180, width=8)
            if q >= fail:
                A.d['red'].line((ex - 20, ey - 20, ex + 20, ey + 20), fill=255, width=6); A.d['red'].line((ex + 20, ey - 20, ex - 20, ey + 20), fill=255, width=6)
    if ph >= 4:
        flames(A, target[0], target[1] + 40, 160, 120 * ease_out((ph - 4) / 0.8), t, n=4, seed=5, smoke=True)
    A.flush(cv)
    for i, (x, nm) in enumerate(passes):
        stamp(cv, seal(nm, 30, BRASS if i == 0 else INK), x, 1350, t, t - u + 0.2 + i * 0.1)
    if ph >= 3.5:
        stamp(cv, seal('龙城', 44), target[0], target[1] - 60, t, t - u + 3.5 * P)
    paste(cv, text_img('四将出击 · 唯卫青有功' if ph < 5 else '斩首虏七百', SERIF, 46, SLATE if ph < 5 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_w_yanmen(A, cv, t, u):
    city_wall(A, 60, 460, 1080, gate_x=260, label='雁门', layer='slate', open_=1.0)
    ground(A, GROUND)
    for k in range(6):
        rider(A, lerp(260, 1000, ease_out((u - k * 0.1) / (2.5 * P))) - k * 80, GROUND - (k % 2) * 30, 120, 1, t * 12 + k, layer='ink', spear=True)
    A.flush(cv)
    paste(cv, text_img('斩首虏数千', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def scene_hetao(cv, t, c, k):
    """8-beat custom scene: 收复河南地 — the great loop of the 黄河; a sweep from the west cuts off the 楼烦 白羊 kings;
    the loop turns green and 朔方 appears."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['wash'].rounded_rectangle((110, 760, 970, 1420), radius=24, fill=190)
    loop = [(220, 1360), (200, 1060), (300, 860), (540, 820), (780, 860), (880, 1060), (860, 1360)]
    A.d['ocean'].line(loop, fill=220, width=26)
    fill = ease_out((ph - 4.5) / 2)
    if fill > 0:
        A.d['grass'].polygon(loop + [(540, 1360)], fill=int(150 * fill))
    for i in range(6):
        kx = 380 + (i % 3) * 140; ky = 1060 + (i // 3) * 140
        if ph < 3.5:
            yurt(A, kx, ky, 70, 60, layer='mid')
    sweep = clamp(ph / 3.5)
    path = [(120, 1300), (160, 1000), (260, 820), (540, 780), (820, 820), (900, 1000), (880, 1200)]
    n = len(path) - 1
    m = sweep * n
    for i in range(n):
        f = clamp(m - i)
        if f <= 0: break
        (x0, y0), (x1, y1) = path[i], path[i + 1]
        A.d['brass'].line((x0, y0, lerp(x0, x1, f), lerp(y0, y1, f)), fill=255, width=10)
    if ph >= 6:
        A.d['slate'].rectangle((500, 900, 580, 960), fill=255)
    A.flush(cv)
    if ph >= 6:
        stamp(cv, seal('朔方', 40), 540, 860, t, s0 + 6 * P)
    fx = Art()
    chars_in(cv, fx, '收复河套', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=62)
    fx.flush(cv)
    lab = '迂回包抄 · 断其退路' if ph < 3.5 else ('走白羊 楼烦王' if ph < 6 else '置朔方郡')
    paste(cv, text_img(lab, SERIF, 46, BRASS if ph < 6 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('公元前一二七年 · 河南地', SERIF, 42, SLATE, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_w_changping(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='slate')
    ground(A, GROUND)
    person(A, 700, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 100, ease_out(u / 0.5)), layer='ink')
    wei(A, 360, GROUND, 220, dir=1, kneel=True, bow=40, arm=100)
    A.flush(cv)
    stamp(cv, seal('长平侯', 54), 540, 880, t, t - u + P)

def art_w_shuofang(A, cv, t, u):
    """6-beat: 筑朔方 — the old Qin wall is repaired; workers haul stones; the city walls rise."""
    ph = u / P
    ground(A, GROUND)
    h = 260 * ease_out(ph / 4.5)
    A.d['slate'].rectangle((200, GROUND - h, 880, GROUND), fill=255)
    for k in range(int(680 / 60)):
        A.d['slate'].rectangle((200 + k * 62, GROUND - h - 30, 230 + k * 62, GROUND - h), fill=255)
    for k in range(6):
        x = (t * 80 + k * 190) % (W + 200) - 100
        person(A, x, GROUND, 100, dir=1, robe=False, hat='knot', load=True, arm=160, ph=t * 6 + k, layer='ink')
    A.flush(cv)
    stamp(cv, seal('蒙恬故塞', 44, INK), 860, 860, t, t - u + P, rot=6)
    if ph >= 4.5:
        paste(cv, text_img('朔方城', SERIF, 52, SLATE, 'Black', bleed=False, spacing=10), W / 2, 1448, 1, clamp((ph - 4.5) / 0.3))

# ================================================================ 第三回 大将军
def art_w_night_raid(A, cv, t, u):
    """8-beat set piece: 夜袭右贤王 — a drunk king in his tent; riders cross six hundred li in the dark; the camp falls;
    the king flees with a few hundred; captives stream back."""
    ph = u / P
    for k in range(40):
        x = 80 + (k * 37) % 920; y = 640 + (k * 47) % 320
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    A.d['wash'].ellipse((820, 680, 900, 760), fill=255)
    tent(A, 760, GROUND, 360, 280, layer='mid')
    ground(A, GROUND)
    if ph < 3:
        lamp(A, 760, GROUND, 50, t, glow=0.7)
        person(A, 760, GROUND, 140, dir=-1, robe=True, hat='crown', bow=lerp(0, 30, 0.5 + 0.5 * math.sin(t * 2)), arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    for k in range(8):
        x = lerp(-300, 620, ease_out((ph - 1) / 3)) - (k % 4) * 100
        rider(A, x, GROUND - (k // 4) * 40, 110, 1, t * 12 + k, layer='ink', spear=True)
    if ph >= 4:
        flames(A, 760, GROUND, 400, 240 * ease_out((ph - 4) / 1), t, n=6, seed=17, smoke=True)
        horse(A, lerp(900, 1200, ease_out((ph - 4) / 1.5)), GROUND, 110, dir=1, ph=t * 12, layer='mid')
    A.flush(cv)
    lab = '右贤王饮醉' if ph < 1.5 else ('夜行六七百里' if ph < 4 else ('右贤王仅以身免' if ph < 6 else '得裨王十余人 · 众男女万五千'))
    paste(cv, text_img(lab, SERIF, 46, BRASS if ph < 6 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_w_appoint(A, cv, t, u):
    tent(A, 540, GROUND, 620, 420, layer='mid')
    ground(A, GROUND)
    x = lerp(1100, 700, ease_out(u / (1.5 * P)))
    person(A, x, GROUND, 210, dir=-1, robe=True, hat='none', arm=lerp(20, 100, ease_out((u - 1.5 * P) / 0.4)), layer='ink')
    if u > 1.5 * P:
        seals_stack(A, x - 120, GROUND - 160, 1, s=30, t=t)
    wei(A, 340, GROUND, 230, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('大将军', 56), 540, 860, t, t - u + 2 * P)

def art_w_sons(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        A.d['mid'].ellipse((260 + k * 120, GROUND - 120, 340 + k * 120, GROUND - 60), fill=230)
        A.d['ink'].ellipse((300 + k * 120 - 14, GROUND - 130, 300 + k * 120 + 14, GROUND - 102), fill=255)
    wei(A, 780, GROUND, 240, dir=-1, bow=lerp(0, 30, ease_out((u - P) / 0.5)), arm=lerp(20, 120, ease_out((u - P) / 0.5)))
    A.flush(cv)
    for k in range(3):
        stamp(cv, seal('侯', 40), 300 + k * 120, GROUND - 200, t, t - u + 0.4 + k * 0.2)

def art_w_dingxiang(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        rider(A, lerp(-100, 700, ease_out(u / (3 * P))) - k * 100, GROUND - (k % 2) * 30, 120, 1, t * 12 + k, layer='ink', spear=True)
    Hq.huo_rider(A, lerp(-100, 900, ease_out(u / (2.5 * P))), GROUND - 60, 110, dir=1, ph=t * 13)
    A.flush(cv)
    stamp(cv, seal('定襄', 54), 260, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('霍去病', 44), 860, 900, t, t - u + 1.5 * P, rot=6)

def art_w_sujian(A, cv, t, u):
    tent(A, 540, GROUND, 620, 420, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 190, dir=1, robe=False, hat='helmet', kneel=True, bow=40, arm=100, layer='ink')
    wei(A, 780, GROUND, 240, dir=-1, arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t)))
    for k in range(2):
        person(A, 300 - k * 80, GROUND, 200, dir=1, robe=True, hat='none', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('苏建', 50, INK), 540, 900, t, t - u + 0.4)
    stamp(cv, seal('交天子', 44), 860, 880, t, t - u + 1.6 * P, rot=6)

def art_w_humble(A, cv, t, u):
    """6-beat: 甘居人后 — the young nephew rides ahead in the light; the uncle walks behind in shadow and smiles."""
    ph = u / P
    ground(A, GROUND)
    Hq.huo_rider(A, lerp(300, 820, ease_out(ph / 4)), GROUND, 170, dir=1, ph=t * 10)
    for k in range(5):
        person(A, lerp(200, 700, ease_out((ph - 0.5) / 4)) + k * 50, GROUND, 110, dir=1, robe=True, hat='none', ph=t * 5 + k, arm=40, layer='mid')
    wei(A, lerp(120, 260, ease_out(ph / 5)), GROUND, 230, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('不争功 不结党', SERIF, 50, SLATE, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((ph - 2) / 0.4))

# ================================================================ 第四回 漠北决战
def art_w_wagons(A, cv, t, u):
    """8-beat set piece: 武刚车阵 — wagons roll into a ring; five thousand riders burst out from it toward the 单于's line."""
    ph = u / P
    cx, cy = 540, 1240
    n = min(10, int(ph * 10 / 3) + 1)
    for i in range(n):
        a = math.pi + i * math.pi / 9
        x = cx + 380 * math.cos(a); y = cy + 120 * math.sin(a) + 120
        cart(A, x, y, 80)
    ground(A, GROUND)
    if ph >= 3.5:
        for k in range(10):
            x = lerp(540, 1200, ease_out((ph - 3.5 - (k % 5) * 0.1) / 3)) - (k % 5) * 60
            rider(A, x, GROUND - 120 - (k // 5) * 40, 100, 1, t * 13 + k, layer='ink', spear=True)
    wei(A, 540, 1240, 170, dir=1, arm=lerp(40, 160, ease_out((ph - 3) / 0.6)))
    A.flush(cv)
    lab = '以武刚车自环为营' if ph < 3.5 else '纵五千骑往当匈奴'
    paste(cv, text_img(lab, SERIF, 48, SLATE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)

def art_w_sandstorm(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        rider(A, 160 + (k % 5) * 90, GROUND - (k // 5) * 40, 100, 1, t * 6 + k, layer='ink', spear=True, moving=False)
        rider(A, 960 - (k % 5) * 90, GROUND - (k // 5) * 40, 100, -1, t * 6 + k, layer='mid', spear=True, moving=False)
    for k in range(80):
        q = (t * 1.6 + k / 80) % 1
        y = 700 + (k * 37) % 700
        A.d['dune'].line((lerp(-100, 1200, q), y, lerp(-100, 1200, q) + 60, y + 6), fill=200, width=4)
    A.flush(cv)
    paste(cv, text_img('沙砾击面 两军不相见', SERIF, 46, BRASS, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_chanyu_flees(A, cv, t, u):
    city_wall(A, 520, 1000, 1100, gate_x=760, label='赵信城', layer='mid', open_=1.0)
    flames(A, 760, 1100, 440, 240 * ease_out((u - 1.5 * P) / 0.8), t, n=6, seed=27, smoke=True)
    ground(A, GROUND)
    horse(A, lerp(700, 1200, ease_out(u / (1.5 * P))), GROUND, 120, dir=1, ph=t * 12, layer='ink')
    for k in range(5):
        rider(A, lerp(-200, 440, ease_out(u / (2.5 * P))) - k * 90, GROUND, 110, 1, t * 12 + k, layer='ink', spear=True)
    A.flush(cv)
    paste(cv, text_img('烧其积粟而还', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((u - 2 * P) / 0.3))

def art_w_ligang(A, cv, t, u):
    for k in range(40):
        q = (t * 0.3 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=200)
    tent(A, 760, GROUND, 400, 300, layer='mid')
    ground(A, GROUND)
    person(A, 380, GROUND, 230, dir=1, robe=False, hat='helmet', sword=150, arm=160, kneel=True, layer='ink')
    A.flush(cv)
    stamp(cv, seal('李广', 54, INK), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('迷失道 · 不愿对刀笔之吏', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_w_dasima(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    wei(A, 380, GROUND, 240, dir=1, arm=40)
    Hq.huo(A, 700, GROUND, 230, dir=-1, arm=40)
    A.flush(cv)
    stamp(cv, seal('大司马', 54), 540, 880, t, t - u + P)

def art_w_marriage(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='slate')
    ground(A, GROUND)
    wei(A, 420, GROUND, 230, dir=1, armour=False, arm=lerp(20, 60, ease_out(u / P)))
    person(A, 660, GROUND, 210, dir=-1, robe=True, hat='knot', female=True, arm=lerp(20, 60, ease_out(u / P)), layer='ink')
    A.d['red'].line((480, GROUND - 160, 600, GROUND - 160), fill=255, width=6)
    A.flush(cv)
    stamp(cv, seal('一说', 44, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_w_no_guests(A, cv, t, u):
    palace(A, 760, GROUND, 360, layer='mid')
    ground(A, GROUND)
    wei(A, 540, GROUND, 230, dir=-1, armour=False, arm=lerp(20, 100, ease_out((u - 0.5 * P) / 0.4)))
    for k in range(3):
        person(A, lerp(380, 120, ease_out((u - P) / (2 * P))) - k * 70, GROUND, 170, dir=-1, robe=True, hat='none', ph=t * 4 + k, arm=-8, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('人臣奉法遵职而已 何与招士', SERIF, 42, SLATE, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + P, 0.5)

# ================================================================ 第五回 冢象庐山
def art_w_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    wei(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('烈侯', 56), 540, 900, t, t - u + 1.5 * P)

def art_w_tomb(A, cv, t, u):
    p = ease_out(u / (2 * P))
    A.d['slate'].polygon([(160, GROUND), (360, GROUND - 260 * p), (540, GROUND - 180 * p), (720, GROUND - 300 * p), (920, GROUND)], fill=200)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('庐山', 56), 860, 880, t, t - u + 1.5 * P, rot=6)

def art_w_beside(A, cv, t, u):
    A.d['slate'].polygon([(100, GROUND), (300, 1080), (500, GROUND)], fill=200)
    A.d['qilian'].polygon([(580, GROUND), (780, 1120), (980, GROUND)], fill=200)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('卫青', 44), 300, 980, t, t - u + 0.4)
    stamp(cv, seal('霍去病', 40), 780, 1020, t, t - u + P)
    paste(cv, text_img('舅甥同葬茂陵', SERIF, 48, SLATE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_w_critique(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='slate')
    Sm.sima(A, 300, GROUND, 230, dir=1, beard=False, arm=60)
    A.flush(cv)
    type_in(cv, text_img('以和柔自媚于上', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('一家之言', 40), 860, 1100, t, t - u + 1.6 * P, rot=6)

def art_w_seven(A, cv, t, u):
    ground(A, GROUND)
    for i in range(7):
        x = 150 + i * 130
        h = 80 + 40 * i * ease_out((u - i * 0.15 * P) / P)
        A.d['brass' if i % 2 else 'slate'].rectangle((x - 40, GROUND - h, x + 40, GROUND), fill=255)
    A.flush(cv)
    paste(cv, text_img('凡七出击匈奴 斩捕首虏五万余级', SERIF, 42, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_w_from_stable(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((120, 1100, 400, GROUND), fill=200)
    A.d['ink'].polygon([(100, 1100), (420, 1100), (260, 1020)], fill=255)
    x = lerp(260, 760, ease_out(u / (2.5 * P)))
    wei(A, x, GROUND, lerp(150, 280, ease_out(u / (2.5 * P))), dir=1, ph=t * 4, arm=40, spear=u > 1.5 * P)
    A.flush(cv)
    paste(cv, text_img('从马厩到大将军', SERIF, 50, SLATE, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_w_legacy(A, cv, t, u):
    seals_stack(A, 540, 1260, 3, s=80, t=t)
    ground(A, GROUND)

def art_w_title(A, cv, t, u):
    cart(A, 820, 1460, 260)
    wei(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))), spear=True)

# ================================================================ script
CHAPTERS = {16: ('第一回', '骑奴出身'), 48: ('第二回', '龙城初捷'), 80: ('第三回', '拜大将军'),
            112: ('第四回', '漠北决战'), 144: ('第五回', '冢象庐山')}

CARDS = [
    C(0, 2, 'war', 'num', num='七出匈奴', line='斩捕五万余', art=art_w_hook_7),
    C(2, 4, 'life', 'num', num='牧羊奴', line='官至大将军', art=art_w_hook_shepherd),
    C(4, 6, 'works', 'num', num='收复河套', line='置朔方郡', art=art_w_hook_river),
    C(6, 8, 'court', 'num', num='娶了旧主', line='平阳公主', art=art_w_hook_princess),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 骑奴出身
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-140, main='牧羊少年', sub='郑季之子 · 兄弟视他如奴', note='生年不详', art=art_w_shepherd),
    C(22, 26, 'night', 'card', year=-140, main='笞骂即足', sub='有人说他将来封侯 · 他只是笑', art=art_w_prophecy),
    C(26, 30, 'court', 'card', year=-139, main='平阳骑奴', sub='为平阳公主家骑奴', art=art_w_rider_slave),
    C(30, 34, 'empire', 'card', year=-139, main='姐姐入宫', sub='卫子夫得宠', art=art_w_sister),
    C(34, 38, 'night', 'card', year=-139, main='死里逃生', sub='大长公主囚之欲杀 · 公孙敖救出', art=art_w_rescue),
    C(38, 42, 'court', 'card', year=-139, main='建章监', sub='武帝召见 · 留在身边', art=art_w_jianzhang),
    C(42, 46, 'works', 'card', year=-134, main='十年磨砺', sub='侍从武帝左右', art=art_w_years),
    C(46, 48, 'war', 'card', year=-129, main='车骑将军', sub='首次领兵', art=art_w_first_cmd),
    # ---- 第二回 龙城初捷
    C(48, 50, 'war', 'chapter'),
    C(50, 58, 'war', 'card', year=-129, main='奇袭龙城', sub='四路出击 · 唯他获胜', note='汉军对匈奴首胜', art=art_w_longcheng),
    C(58, 62, 'war', 'card', year=-128, main='出雁门', sub='再战告捷', art=art_w_yanmen),
    C(62, 70, 'works', 'hetao', year=-127),
    C(70, 74, 'empire', 'card', year=-127, main='长平侯', sub='以功封侯', art=art_w_changping),
    C(74, 80, 'works', 'card', year=-127, main='筑朔方', sub='修缮秦时旧塞', art=art_w_shuofang),
    # ---- 第三回 拜大将军
    C(80, 82, 'empire', 'chapter'),
    C(82, 90, 'night', 'card', year=-124, main='夜袭右贤王', sub='出塞六七百里 · 夜围其营', art=art_w_night_raid),
    C(90, 94, 'empire', 'card', year=-124, main='军中拜将', sub='使者持印 · 即军中拜大将军', art=art_w_appoint),
    C(94, 98, 'court', 'card', year=-124, main='三子封侯', sub='儿子尚在襁褓 · 皆封侯', note='青固谢 帝不许', art=art_w_sons),
    C(98, 102, 'war', 'card', year=-123, main='再出定襄', sub='外甥霍去病初次随军', art=art_w_dingxiang),
    C(102, 106, 'court', 'card', year=-123, main='不斩苏建', sub='苏建失军 · 交天子处置', note='人臣不敢专权于境外', art=art_w_sujian),
    C(106, 112, 'fate', 'card', year=-121, main='甘居人后', sub='外甥风头渐盛 · 他从不争功', art=art_w_humble),
    # ---- 第四回 漠北决战
    C(112, 114, 'war', 'chapter'),
    C(114, 122, 'war', 'card', year=-119, main='武刚车阵', sub='深入漠北 · 正面迎击单于', art=art_w_wagons),
    C(122, 126, 'fate', 'card', year=-119, main='大风扬沙', sub='日暮大风 · 纵左右翼包抄', art=art_w_sandstorm),
    C(126, 130, 'war', 'card', year=-119, main='单于遁走', sub='追至赵信城', art=art_w_chanyu_flees),
    C(130, 134, 'death', 'card', year=-119, main='李广自刎', sub='迷路失期', art=art_w_ligang),
    C(134, 138, 'empire', 'card', year=-119, main='大司马', sub='与霍去病并为大司马', art=art_w_dasima),
    C(138, 142, 'court', 'card', year=-115, main='尚平阳公主', sub='昔日骑奴 · 娶了旧主人', art=art_w_marriage),
    C(142, 144, 'life', 'card', year=-110, main='不养宾客', sub='为人仁善退让', art=art_w_no_guests),
    # ---- 第五回 冢象庐山
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'death', 'card', year=-106, main='病逝', sub='谥号为烈', art=art_w_death),
    C(150, 154, 'fate', 'card', year=-106, main='冢象庐山', sub='墓冢修成匈奴庐山之形', art=art_w_tomb),
    C(154, 158, 'court', 'card', year=-106, main='茂陵陪葬', sub='与霍去病墓相邻', art=art_w_beside),
    C(158, 162, 'works', 'card', year=-91, main='史家之笔', sub='史记评他', note='功过并书', art=art_w_critique),
    C(162, 166, 'empire', 'card', year=-91, main='七出匈奴', sub='汉军对匈奴的转折', art=art_w_seven),
    C(166, 170, 'end', 'card', year=2026, main='奴仆将军', sub='出身最低的大将军', art=art_w_from_stable),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='贰拾捌', col=SLATE, acc=BRASS, born=-140, died=-106, no_age=True,
    born_lab='生年不详', died_lab='前106年', years_txt='生年不详 — 公元前106',
    hook_q='从放羊的奴仆 到大将军 · 他怎么做到的？',
    name_line='卫青 · 字仲卿', name='卫青', seal='长平', title_art=art_w_title,
    q1='一代名将？', q2='外戚靠山？',
    end_art=art_w_legacy, end_big='七出匈奴', end_seal='长平',
    end_l1='他从马厩里走出来', end_l2='把匈奴赶出了漠南',
    end_brush='奉法遵职', end_ask='卫青和霍去病 你更佩服谁？评论区聊聊', next='班超'),
    scenes=dict(chapter=scene_chapter, hetao=scene_hetao))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
