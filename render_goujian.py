"""千古人物志 · 第肆拾捌集 · 勾践 (？–前465)
Look: 苦胆绿 + 会稽紫, 菱格纹 corner borders, a 薪胆 chapter card: a gall hangs from the beam while the firewood
stack grows (0→2→4→6), and in the last chapter a bronze sword rises out of it.
Set pieces: 6-beat 阵前奇兵, 6-beat 石室养马, custom 8-beat scene 'changdan' (卧薪尝胆 · 十年), 6-beat 黄池之会,
8-beat 灭吴, 6-beat 范蠡泛舟.
Birth year unknown: the HUD hides ages (no_age).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_sunwu as Sw           # engine + helpers (previous episode)
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
KUDAN = (100, 122, 48)              # 苦胆绿
JIZI = (96, 62, 92)                 # 会稽紫
S.LAYERS.append(('kudan', KUDAN, 0.9, 1.0))
S.LAYERS.append(('jizi', JIZI, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='忍', life='越', court='吴', night='胆', war='战', empire='越', works='薪', fate='辱', death='亡', end='剑')
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
G.THEMES['empire']['sun'] = (KUDAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (JIZI, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

PADDY = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(PADDY)
for _k in range(5):                 # 水乡 paddies at the lower margins
    _y = 1430 + _k * 20
    for _x in range(60, W - 60, 120):
        _d.line((_x + (_k % 2) * 40, _y, _x + 80 + (_k % 2) * 40, _y), fill=KUDAN + (40,), width=3)
for _x in (130, 950):               # 会稽 stilt huts
    _d.polygon([(_x - 60, 1360), (_x + 60, 1360), (_x, 1310)], fill=(70, 60, 70, 50))
    _d.rectangle((_x - 46, 1360, _x + 46, 1400), fill=(90, 80, 80, 40))
    for _p in (-36, 0, 36):
        _d.line((_x + _p, 1400, _x + _p, 1430), fill=(70, 60, 70, 50), width=3)
MTN_COL = {'night': (34, 30, 40), 'death': (62, 56, 62), 'war': (104, 58, 50), 'fate': (92, 82, 96)}
def draw_background(t, theme):
    """会稽: misty hills, paddies and stilt huts at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(184, 186, 170), (146, 152, 128), MTN_COL.get(theme, (104, 112, 90))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(PADDY)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """菱格纹: the diamond lattice of the 越王剑 blade in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=JIZI + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=JIZI + (220,), width=3)
        for i in range(3):
            for j in range(3 - i):
                cx, cy = x + sx * (30 + i * 30), y + sy * (30 + j * 30)
                d.polygon([(cx, cy - 13), (cx + 13, cy), (cx, cy + 13), (cx - 13, cy)], outline=KUDAN + (230,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def gou(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, slave=False, old=0.0, **kw):
    """勾践: Yue king — low crown with two prongs, short-cropped Yue hair and a tattooed arm band; as a slave, a bare knot."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not slave, hat='knot' if (slave or not up) else 'none', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up and not slave:
        d.rectangle((x - 0.08 * h, y - 1.0 * h, x + 0.08 * h, y - 0.95 * h), fill=255)
        for px in (-0.05, 0.0, 0.05):
            d.polygon([(x + px * h - 0.015 * h, y - 0.99 * h), (x + px * h + 0.015 * h, y - 0.99 * h), (x + px * h, y - 1.035 * h)], fill=255)
        A.d['kudan'].rectangle((x - 0.08 * h, y - 0.58 * h, x + 0.08 * h, y - 0.53 * h), fill=255)
        A.d['jizi'].line((x - dir * 0.04 * h, y - 0.5 * h, x - dir * 0.28 * h, y - 0.36 * h), fill=255, width=max(3, int(0.022 * h)))
        if old > 0.4:
            A.d['wash'].line((x + dir * 0.06 * h, y - 0.82 * h, x + dir * 0.09 * h, y - 0.72 * h), fill=255, width=max(2, int(0.012 * h)))
    return hand

def fuchai(A, x, y, h, dir=-1, layer='ink', **kw):
    return person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)

def gall(A, x, y, s, t, sway=1.0):
    a = 0.12 * math.sin(t * 1.6) * sway
    bx, by = x + 1.2 * s * math.sin(a), y + 1.2 * s * math.cos(a)
    A.d['ink'].line((x, y, bx, by), fill=255, width=3)
    A.d['kudan'].ellipse((bx - 0.45 * s, by, bx + 0.45 * s, by + 0.95 * s), fill=255)
    A.d['kudan'].polygon([(bx - 0.2 * s, by + 0.1 * s), (bx + 0.2 * s, by + 0.1 * s), (bx, by - 0.15 * s)], fill=255)

def firewood(A, cx, base, n, w=360):
    for i in range(n):
        y = base - 14 - i * 22
        A.d['jizi' if i % 2 else 'mid'].rounded_rectangle((cx - w / 2 + (i % 2) * 14, y - 10, cx + w / 2 - (i % 2) * 14, y + 10), radius=10, fill=255)
        A.d['ink'].ellipse((cx + w / 2 - 22 - (i % 2) * 14, y - 9, cx + w / 2 - 4 - (i % 2) * 14, y + 9), outline=200, width=2)

def sword(A, cx, cy, L_, ang=-math.pi / 2, layer='kudan'):
    ca, sa = math.cos(ang), math.sin(ang)
    def R(u, v): return (cx + u * ca - v * sa, cy + u * sa + v * ca)
    A.d[layer].polygon([R(0, -0.06 * L_), R(0.8 * L_, -0.05 * L_), R(L_, 0), R(0.8 * L_, 0.05 * L_), R(0, 0.06 * L_)], fill=255)
    for k in range(6):
        u = 0.1 * L_ + k * 0.11 * L_
        A.d['jizi'].polygon([R(u, 0), R(u + 0.05 * L_, -0.035 * L_), R(u + 0.1 * L_, 0), R(u + 0.05 * L_, 0.035 * L_)], outline=200, width=2)
    A.d['ink'].line([R(0, -0.14 * L_), R(0, 0.14 * L_)], fill=255, width=10)
    A.d['ink'].line([R(0, 0), R(-0.22 * L_, 0)], fill=255, width=12)

def hut(A, cx, base, w, t, lit=1.0):
    A.d['mid'].rectangle((cx - w / 2, base - 0.5 * w, cx + w / 2, base), fill=230)
    A.d['ink'].polygon([(cx - w / 2 - 40, base - 0.5 * w), (cx + w / 2 + 40, base - 0.5 * w), (cx, base - 0.85 * w)], fill=255)
    A.d['ink'].rectangle((cx - 0.12 * w, base - 0.32 * w, cx + 0.12 * w, base), fill=255)

# ================================================================ chapter card
CH = {16: (0, 0.0), 48: (2, 0.0), 80: (4, 0.0), 112: (6, 0.0), 144: (6, 1.0)}
def art_gall_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g, rise = CH.get(kb, (2, 0.0))
    prev = {48: 0, 80: 2, 112: 4, 144: 6}.get(kb, 0)
    q = ease_out(u / (1.2 * P))
    A.d['ink'].line((240, 820, 840, 820), fill=255, width=14)
    gall(A, 540, 820, 70, t)
    firewood(A, 540, 1200, int(lerp(prev, g, q)) if not rise else 6)
    if rise:
        sword(A, 540, 1060, 360 * q, ang=-math.pi / 2)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_gall_chapter)
    ink_in(cv, text_img(no, SERIF, 56, JIZI, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_g_hook_horse(A, cv, t, u):
    ground(A, GROUND)
    horse(A, 640, GROUND, 220, dir=-1, moving=False, head_down=0.3)
    gou(A, 360, GROUND, 190, dir=1, slave=True, bow=20, arm=lerp(40, 110, 0.5 + 0.5 * math.sin(t * 4)))

def art_g_hook_gall(A, cv, t, u):
    A.d['ink'].line((300, 860, 780, 860), fill=255, width=12)
    gall(A, 540, 860, 90, t)
    ground(A, GROUND)
    firewood(A, 540, GROUND, 5)

def art_g_hook_3000(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (1.4 * P)) * 30) + 1
    for i in range(n):
        person(A, 100 + (i % 15) * 60, GROUND - (i // 15) * 60, 80, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='kudan' if i % 2 else 'ink')

def art_g_hook_sword(A, cv, t, u):
    ground(A, GROUND)
    sword(A, 540, 1240, 420 * ease_out(u / P))
    A.d['wash'].ellipse((540 - 40, 1240 - 460 * ease_out(u / P) - 40, 540 + 40, 1240 - 460 * ease_out(u / P) + 40), fill=int(200 * (0.5 + 0.5 * math.sin(t * 6))))

# ================================================================ 第一回 会稽之耻
def art_g_crown(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='kudan')
    ground(A, GROUND)
    gou(A, 540, GROUND, 230, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    for i in range(4):
        person(A, 200 + i * 60 if i < 2 else 760 + (i - 2) * 60, GROUND, 160, dir=1 if i < 2 else -1, robe=True, hat='knot', kneel=True, bow=40, arm=90, layer='mid')
    A.flush(cv)
    stamp(cv, seal('越王', 56), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('父允常去世 · 勾践继位', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_zuili(A, cv, t, u):
    """6-beat set piece: 阵前奇兵 — three ranks of condemned men walk out before the Wu line and fall on their own swords;
    the Wu soldiers stare; the Yue army charges through the confusion."""
    ph = u / P
    ground(A, GROUND)
    army(A, 980, GROUND, 6, dir=-1, layer='mid', t=t, h=100)
    if ph < 4:
        for r in range(3):
            for i in range(5):
                x = lerp(80, 420, ease_out(ph / 1.5)) - r * 60 + i * 50
                fall = clamp((ph - 1.6 - r * 0.5) / 0.4)
                person(A, x, GROUND - r * 6, 100, dir=1, robe=False, hat='knot', fall=-80 * fall, arm=lerp(-8, 140, clamp((ph - 1.2) / 0.3)), layer='ink')
        for i in range(3):
            A.d['wash'].ellipse((700 + i * 70 - 20, GROUND - 260 - 20, 700 + i * 70 + 20, GROUND - 260 + 20), outline=200, width=4)
    else:
        army(A, lerp(-200, 520, ease_out((ph - 4) / 1.6)), GROUND, 7, dir=1, layer='kudan', t=t, march=True, h=110)
    A.flush(cv)
    lab = '罪人三行 · 至吴阵前' if ph < 1.6 else ('自刎于阵前 · 吴军惊愕' if ph < 4 else '越军趁乱突击 · 大败吴师')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 1.6 else JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('檇李', 54, INK), 260, 1020, t, t - u + 0.4, rot=-5)

def art_g_vow(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    fuchai(A, 540, GROUND, 230, dir=1, arm=lerp(20, 60, ease_out(u / 0.6)))
    person(A, 820, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    type_in(cv, text_img('夫差 而忘越王之杀而父乎', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('唯 不敢忘', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 835, t, t - u + 1.8 * P, 0.5)
    stamp(cv, seal('阖闾伤死', 44, INK), 860, 1020, t, t - u + 0.4, rot=6)

def art_g_strike(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='kudan')
    ground(A, GROUND)
    gou(A, 380, GROUND, 220, dir=1, arm=lerp(40, 140, ease_out(u / 0.5)))
    person(A, 720, GROUND, 200, dir=-1, robe=True, hat='knot', bow=25, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    type_in(cv, text_img('兵者凶器也 战者逆德也', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('范蠡谏', 50), 860, 1020, t, t - u + P, rot=6)

def art_g_fujiao(A, cv, t, u):
    river(A, 1180, t, rows=3, amp=7, speed=2)
    for j in range(5):
        boat(A, lerp(1200, 520 + j * 110, ease_out(u / (2 * P))), 1210, 70, t + j, sail=True)
    for j in range(3):
        boat(A, lerp(380 - j * 110, -260 - j * 110, ease_out((u - 1.5 * P) / (2 * P))), 1220, 60, t + j, sail=False)
    A.flush(cv)
    paste(cv, text_img('越军大败 · 仅余五千人', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('夫椒', 56, INK), 260, 1020, t, t - u + P, rot=-5)

def art_g_kuaiji(A, cv, t, u):
    for k in range(3):
        x = 240 + k * 300
        A.d['mid'].polygon([(x - 260, GROUND), (x, GROUND - 440 - 60 * (k == 1)), (x + 260, GROUND)], fill=200)
    ground(A, GROUND)
    for j in range(6):
        x = (j * 157) % 900 + 90
        person(A, x, GROUND - 240 + (j % 3) * 70, 70, dir=1 if j % 2 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='kudan')
    army(A, -40, GROUND, 4, dir=1, layer='mid', h=90)
    army(A, 1120, GROUND, 4, dir=-1, layer='mid', h=90)
    A.flush(cv)
    paste(cv, text_img('吴军四面合围', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('会稽山', 50), 860, 1020, t, t - u + P, rot=6)

def art_g_bribe(A, cv, t, u):
    tent(A, 540, GROUND, 420, 280, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(20, 90, ease_out(u / 0.5)), layer='ink')
    person(A, 360, GROUND, 190, dir=1, robe=True, hat='knot', kneel=True, bow=40, arm=100, layer='ink')
    for i in range(int(clamp(u / P) * 6)):
        A.d['gold'].rectangle((480 + (i % 3) * 40, GROUND - 30 - (i // 3) * 26, 512 + (i % 3) * 40, GROUND - 8 - (i // 3) * 26), fill=255)
    A.flush(cv)
    paste(cv, text_img('文种携美女宝器 · 贿太宰伯嚭', SERIF, 44, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('求和', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第二回 石室三年
def art_g_slave(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=4)
    x = lerp(160, 860, ease_out(u / (3 * P)))
    boat(A, x, 1260, 140, t, sail=True)
    gou(A, x - 40, 1240, 100, dir=1, slave=True, kneel=True, bow=20, arm=60)
    person(A, x + 30, 1240, 90, dir=-1, robe=True, hat='knot', female=True, kneel=True, arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('携夫人入吴 · 为奴为仆', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('入吴', 56, INK), 260, 1020, t, t - u + P, rot=-5)

def art_g_stable(A, cv, t, u):
    """6-beat set piece: 石室养马 — a stone hut beside the stable; he cuts grass and grooms the horse through three years of seasons."""
    ph = u / P
    yr = min(3, int(ph / 2) + 1)
    season = int(ph / 0.75) % 4
    sky = ['grass', 'yellow', 'jizi', 'wash'][season]
    A.d['mid'].rectangle((620, GROUND - 240, 960, GROUND), fill=200)
    A.d['ink'].rectangle((620, GROUND - 240, 960, GROUND), outline=255, width=6)
    A.d['ink'].rectangle((760, GROUND - 130, 820, GROUND), fill=255)
    for k in range(8):
        A.d[sky].ellipse((120 + k * 60 - 18, 980 + (k % 3) * 30 - 18, 120 + k * 60 + 18, 980 + (k % 3) * 30 + 18), fill=180)
    ground(A, GROUND)
    horse(A, 420, GROUND, 200, dir=1, moving=False, head_down=0.5)
    gou(A, 230, GROUND, 170, dir=1, slave=True, bow=lerp(10, 40, 0.5 + 0.5 * math.sin(t * 3)), arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    paste(cv, text_img(f'住石室 养马驾车 · 第{cn_num(yr)}年', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('石室', 54, INK), 860, 1440, t, t - u + 0.4, rot=6)

def art_g_taste(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    A.d['mid'].rectangle((560, 1200, 900, 1250), fill=230)
    fuchai(A, 740, 1200, 200, dir=-1, fall=-80, arm=-8)
    ground(A, GROUND)
    gou(A, 380, GROUND, 200, dir=1, slave=True, kneel=True, bow=40, arm=100)
    A.flush(cv)
    paste(cv, text_img('吴王病 · 勾践问疾', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '尝粪问疾出自吴越春秋', t, t - u + P)

def art_g_release(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='kudan')
    ground(A, GROUND)
    fuchai(A, 740, GROUND - 30, 220, dir=-1, arm=lerp(20, 110, ease_out(u / 0.6)))
    person(A, 900, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 3)), layer='mid')
    gou(A, 380, GROUND, 200, dir=1, slave=True, kneel=True, bow=50, arm=100)
    A.flush(cv)
    paste(cv, text_img('夫差心软 · 放虎归山', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('子胥力谏', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_g_home(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 160, GROUND), (x - 120, GROUND - 120), (x + 120, GROUND - 120), (x + 160, GROUND)], fill=int(lerp(220, 120, k / 3)))
    flames(A, 300, GROUND - 100, 200, 60, t, n=3, seed=48, smoke=True)
    ground(A, GROUND)
    gou(A, lerp(1000, 640, ease_out(u / (2 * P))), GROUND, 190, dir=-1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('回到会稽 · 满目疮痍', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_changdan(cv, t, c, k):
    """8-beat custom scene: 卧薪尝胆 — night in the hut: he lies on the firewood, rises, tastes the hanging gall,
    and a voice asks 汝忘会稽之耻邪; the years tick from one to ten as the gall shrinks and the stack of slips grows."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['night' if False else 'mid'].rectangle((140, 760, 940, GROUND), fill=60)
    A.d['ink'].line((180, 860, 900, 860), fill=255, width=14)
    yrs = min(10, int(ph * 10 / 7.6) + 1)
    gall(A, 600, 860, 80 * lerp(1.0, 0.75, yrs / 10), t)
    firewood(A, 400, GROUND, 4, w=420)
    cyc = (ph * 1.3) % 1
    if cyc < 0.45:
        gou(A, 400, GROUND - 90, 200, dir=1, fall=-86, arm=-8, slave=True)
    else:
        gou(A, 560, GROUND, 210, dir=1, slave=True, arm=lerp(40, 160, clamp((cyc - 0.5) / 0.2)))
    lamp(A, 880, GROUND, 60, t, glow=0.6 + 0.4 * math.sin(t * 3))
    for i in range(yrs):
        A.d['kudan'].rectangle((180 + i * 30, 1300, 200 + i * 30, 1360), fill=255)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '卧薪尝胆', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=48)
    fx.flush(cv)
    paste(cv, text_img(f'第{cn_num(yrs)}年', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 575, 1, 1)
    paste(cv, text_img('汝忘会稽之耻邪', SERIF, 46, KUDAN, 'Black', bleed=False, spacing=6), W / 2, 680, 1, clamp((ph - 1) / 0.4))
    paste(cv, text_img('坐卧即仰胆 饮食亦尝胆', SERIF, 40, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 0.5) / 0.4))
    note_in(cv, '尝胆见史记 卧薪之说出自后世', t, s0 + 3 * P)

# ================================================================ 第三回 十年生聚
def art_g_farm(A, cv, t, u):
    A.d['grass'].rectangle((100, GROUND - 60, 980, GROUND), fill=150)
    for k in range(10):
        A.d['kudan'].line((140 + k * 84, GROUND - 60, 140 + k * 84 + 10, GROUND - 120), fill=255, width=4)
    ground(A, GROUND)
    gou(A, lerp(200, 520, ease_out(u / (2.5 * P))), GROUND - 60, 170, dir=1, slave=True, bow=40, arm=150, ph=t * 3)
    person(A, 820, GROUND - 60, 160, dir=-1, robe=True, hat='knot', female=True, kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 6)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('身自耕作 · 夫人自织', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('食不加肉', 44), 860, 1020, t, t - u + P, rot=6)

def art_g_grow(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 24) + 1
    for i in range(n):
        x = 120 + (i % 12) * 74; y = GROUND - (i // 12) * 120
        person(A, x, y, 80 if i % 3 else 50, dir=1 if i % 2 else -1, robe=True, hat='knot', baby=(i % 3 == 0), arm=30, layer='ink' if i % 2 else 'jizi')
    A.flush(cv)
    paste(cv, text_img('生丈夫 二壶酒一犬 · 生女子 二壶酒一豚', SERIF, 38, JIZI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('生聚', 56), 860, 1020, t, t - u + P, rot=6)

def art_g_nine(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='jizi')
    sitter(A, 300, GROUND, 200, dir=1, bow=15)
    sitter(A, 780, GROUND, 190, dir=-1, bow=15, layer='mid')
    n = min(9, int(u / (0.4 * P)) + 1)
    slips(A, 440, GROUND - 74, n, 100, layer='kudan')
    A.flush(cv)
    paste(cv, text_img(f'文种献伐吴九术 · 第{cn_num(n)}术', SERIF, 44, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_g_xishi(A, cv, t, u):
    river(A, 1220, t, rows=2, amp=4)
    for k in range(4):
        A.d['grass'].line((160 + k * 40, 1220, 170 + k * 40, 1120), fill=255, width=4)
    person(A, 540, 1230, 200, dir=1, robe=True, hat='knot', female=True, bow=30, arm=lerp(120, 160, 0.5 + 0.5 * math.sin(t * 3)), layer='pink')
    A.flush(cv)
    paste(cv, text_img('越女浣纱 · 献于吴王', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '西施事见吴越春秋 史记无载', t, t - u + P)

def art_g_seeds(A, cv, t, u):
    A.d['grass'].rectangle((100, GROUND - 60, 980, GROUND), fill=150)
    q = clamp((u - P) / (2 * P))
    for k in range(10):
        h = 120 * (1 - q)
        A.d['kudan' if q < 0.5 else 'mid'].line((140 + k * 84, GROUND - 60, 140 + k * 84 + 10, GROUND - 60 - h), fill=255, width=4)
    for i in range(6):
        A.d['yellow'].ellipse((380 + i * 50 - 18, 1000 - 18, 380 + i * 50 + 18, 1000 + 18), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('借粟于吴 · 还以蒸熟之种', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '出自吴越春秋', t, t - u + P)

def art_g_drill(A, cv, t, u):
    ground(A, GROUND)
    drum(A, 900, GROUND, 110, t, hit=(u % P) / P)
    for r in range(2):
        for i in range(7):
            step = int(t * 2) % 2
            person(A, 140 + i * 90, GROUND - r * 80, 110, dir=1, robe=False, hat='helmet', spear=True, kneel=step == 1 and r == 0, arm=40, layer='kudan' if r else 'ink')
    A.flush(cv)
    paste(cv, text_img('十年生聚 十年教训', SERIF, 48, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('练兵', 56), 260, 1020, t, t - u + P, rot=-5)

def art_g_huangchi(A, cv, t, u):
    """6-beat set piece: 黄池之会 — Fuchai marches north with his best troops; Yue strikes the empty capital from the south."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 760, 970, 1420), radius=24, fill=170)
    A.d['ocean'].line([(140, 1040), (980, 1000)], fill=200, width=8)
    q = clamp(ph / 3)
    A.d['mid'].line((620, 1280, 620 - 40 * q, 1280 - 420 * q), fill=255, width=10)
    if ph > 2.5:
        r = clamp((ph - 2.5) / 2.5)
        A.d['kudan'].line((820, 1400, lerp(820, 660, r), lerp(1400, 1300, r)), fill=255, width=12)
        if r > 0.9:
            A.d['red'].ellipse((620, 1250, 700, 1330), fill=int(200 * (0.6 + 0.4 * math.sin(t * 6))))
    A.flush(cv)
    for nm, x, y, col in (('黄池', 540, 840, INK), ('姑苏', 640, 1370, ZHU), ('越', 860, 1420 - 40, KUDAN)):
        stamp(cv, seal(nm, 32, col), x, y, t, t - u + 0.3)
    lab = '夫差率精兵北上争霸' if ph < 2.5 else ('越军乘虚而入' if ph < 4.6 else '攻破姑苏 · 杀吴太子')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2.5 else JIZI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

# ================================================================ 第四回 三千越甲
def art_g_lize(A, cv, t, u):
    river(A, 1200, t, rows=3, amp=5)
    for j in range(6):
        x = lerp(-100, 900, ((t * 0.1 + j / 6) % 1))
        boat(A, x, 1220, 60, t + j, sail=False)
        A.d['red'].ellipse((x - 8, 1170 - 8, x + 8, 1170 + 8), fill=220)
    A.flush(cv)
    paste(cv, text_img('夜渡笠泽 · 左右佯攻 中军偷袭', SERIF, 44, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('笠泽', 56), 260, 1020, t, t - u + P, rot=-5)

def art_g_siege(A, cv, t, u):
    city_wall(A, 260, 820, 1080, gate_x=540, label='姑苏', layer='mid', open_=0.0)
    ground(A, GROUND)
    army(A, 40, GROUND, 4, dir=1, layer='kudan', h=100)
    army(A, 1040, GROUND, 4, dir=-1, layer='kudan', h=100)
    A.flush(cv)
    n = min(3, int(u / (1.2 * P)) + 1)
    paste(cv, text_img(f'围吴 · 第{cn_num(n)}年', SERIF, 48, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_g_endwu(A, cv, t, u):
    """8-beat set piece: 灭吴 — the 姑苏台 burns; Fuchai sends envoys to beg as Goujian once did; Goujian wavers;
    Fan Li beats the drum to attack; Fuchai covers his face and falls."""
    ph = u / P
    palace(A, 760, 1140, 420, collapse=ease_out((ph - 5) / 2), layer='mid')
    flames(A, 760, 1080, 460, 220 * ease_out(ph / 1.5), t, n=6, seed=473, smoke=True)
    ground(A, GROUND)
    if ph < 5:
        person(A, 560, GROUND, 180, dir=-1, robe=True, hat='knot', kneel=True, bow=50, arm=100, layer='mid')
        gou(A, 260, GROUND, 210, dir=1, arm=lerp(-8, 60, clamp((ph - 2) / 0.4)), bow=10 if 2 <= ph < 3.4 else 0)
        if ph > 3.4:
            drum(A, 120, GROUND, 80, t, hit=(u % P) / P)
    else:
        fuchai(A, 640, GROUND, 200, dir=-1, fall=-80 * clamp((ph - 6.2) / 0.6), arm=170)
    A.flush(cv)
    lab = ('吴使求和 · 如当年会稽' if ph < 2 else ('勾践心动' if ph < 3.4 else '范蠡鸣鼓进兵')) if ph < 5 else '吾无面目以见子胥'
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 5 else JIZI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('吴亡', 60, INK), 860, 1440, t, t - u + 6.5 * P, rot=6)

def art_g_xuzhou(A, cv, t, u):
    for k in range(3):
        A.d['kudan'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    gou(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 80, ease_out(u / 0.6)))
    for i in range(4):
        person(A, 140 + i * 60 if i < 2 else 820 + (i - 2) * 60, GROUND, 150, dir=1 if i < 2 else -1, robe=True, hat='crown', bow=30, arm=90, layer='mid')
    A.flush(cv)
    paste(cv, text_img('会诸侯于徐州 · 号称霸王', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('霸主', 56), 860, 1020, t, t - u + P, rot=6)

def art_g_fanli(A, cv, t, u):
    """6-beat set piece: 范蠡泛舟 — he slips away by boat into the lake mist and leaves a letter for 文种."""
    ph = u / P
    river(A, 1180, t, rows=3, amp=4, speed=0.8)
    for k in range(5):
        q = (t * 0.06 + k / 5) % 1
        A.d['wash'].ellipse((lerp(-200, 1200, q) - 160, 1060 + k * 20 - 30, lerp(-200, 1200, q) + 160, 1060 + k * 20 + 30), fill=140)
    x = lerp(300, 1000, ease_out(ph / 5))
    boat(A, x, 1200, int(lerp(120, 50, ease_out(ph / 5))), t, sail=True)
    A.flush(cv)
    type_in(cv, text_img('蜚鸟尽 良弓藏', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + P, 0.5)
    type_in(cv, text_img('狡兔死 走狗烹', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 835, t, t - u + 2.5 * P, 0.5)
    paste(cv, text_img('越王为人 可与共患难 不可与共乐', SERIF, 40, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 3.5) / 0.4))

def art_g_wenzhong(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 210, dir=1, robe=True, hat='knot', kneel=True, bow=20, arm=90, layer='ink')
    sword(A, 700, GROUND - 120, 200, ang=-0.3)
    A.flush(cv)
    type_in(cv, text_img('子教寡人伐吴七术 寡人用其三', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('赐剑', 56, INK), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第五回 千古一剑
def art_g_langya(A, cv, t, u):
    river(A, 1220, t, rows=2, amp=4)
    city_wall(A, 300, 980, 1100, gate_x=640, label='琅琊', layer='mid', open_=1.0)
    for j in range(3):
        boat(A, lerp(-200, 140 + j * 70, ease_out(u / (2 * P))), 1240, 60, t + j, sail=True)
    A.flush(cv)
    paste(cv, text_img('迁都琅琊 · 北上中原', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '迁都之说见竹书纪年 一说未迁', t, t - u + P)

def art_g_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    gou(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('在位三十二年', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('薨', 60, INK), 260, 1020, t, t - u + P, rot=-5)

def art_g_yuefalls(A, cv, t, u):
    palace(A, 540, 1160, 520, collapse=ease_out(u / (2.5 * P)), layer='kudan')
    ground(A, GROUND)
    army(A, lerp(-200, 120, ease_out(u / (2 * P))), GROUND, 4, dir=1, layer='mid', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('后世子孙 · 越国终为楚所灭', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '灭越之年 一说前三〇六年', t, t - u + P)

def art_g_couplet(A, cv, t, u):
    for i, x in enumerate((300, 780)):
        A.d['wash'].rectangle((x - 60, 900, x + 60, 1300), fill=255)
        A.d['ink'].rectangle((x - 60, 900, x + 60, 1300), outline=255, width=5)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('有志者事竟成 破釜沉舟', SERIF, 36, INK, 'Black', bleed=False, vertical=True, spacing=2), 780, 1100, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('苦心人天不负 卧薪尝胆', SERIF, 36, ZHU, 'Black', bleed=False, vertical=True, spacing=2), 300, 1100, t, t - u + 1.4 * P, 0.5)
    paste(cv, text_img('相传为蒲松龄自勉联', SERIF, 42, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_dig(A, cv, t, u):
    A.d['dune'].rectangle((200, 1000, 880, GROUND), fill=220)
    A.d['ink'].rectangle((300, 1060, 780, 1240), fill=200)
    q = ease_out((u - 0.5 * P) / P)
    sword(A, 340, 1150, 400 * q, ang=0.0)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('湖北江陵望山一号墓', SERIF, 46, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('出土', 56), 860, 1020, t, t - u + P, rot=6)

def art_g_inscription(A, cv, t, u):
    sword(A, 540, 1340, 560, ang=-math.pi / 2)
    A.flush(cv)
    type_in(cv, text_img('越王鸠浅 自作用剑', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('鸟篆', 54), 260, 1020, t, t - u + P, rot=-5)

def art_g_rust(A, cv, t, u):
    sword(A, 200, 1100, 680, ang=0.0)
    for k in range(5):
        q = (t * 0.6 + k / 5) % 1
        A.d['wash'].ellipse((lerp(200, 880, q) - 10, 1100 - 10, lerp(200, 880, q) + 10, 1100 + 10), fill=int(255 * (1 - abs(q - 0.5) * 2)))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('两千多年 · 寒光依旧', SERIF, 48, JIZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    firewood(A, 860, 1380, 3, w=200)

def art_g_title(A, cv, t, u):
    A.d['ink'].line((640, 900, 1000, 900), fill=255, width=10)
    gall(A, 860, 900, 70, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    gou(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '会稽之耻'), 48: ('第二回', '石室三年'), 80: ('第三回', '十年生聚'),
            112: ('第四回', '三千越甲'), 144: ('第五回', '千古一剑')}

CARDS = [
    C(0, 2, 'fate', 'num', num='三年', line='为吴王养马', art=art_g_hook_horse),
    C(2, 4, 'night', 'num', num='一颗苦胆', line='尝了十年', art=art_g_hook_gall),
    C(4, 6, 'war', 'num', num='三千越甲', line='可吞吴', art=art_g_hook_3000),
    C(6, 8, 'empire', 'num', num='一把剑', line='千年不锈', art=art_g_hook_sword),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 会稽之耻
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'empire', 'card', year=-496, main='越王即位', sub='少年为王', note='生年不详', art=art_g_crown),
    C(22, 28, 'war', 'card', year=-496, main='阵前奇兵', sub='檇李之战', art=art_g_zuili),
    C(28, 32, 'court', 'card', year=-496, main='夫差誓仇', sub='吴越结怨', art=art_g_vow),
    C(32, 36, 'life', 'card', year=-494, main='先发制人', sub='不听范蠡', art=art_g_strike),
    C(36, 40, 'death', 'card', year=-494, main='夫椒大败', sub='一败涂地', art=art_g_fujiao),
    C(40, 44, 'fate', 'card', year=-494, main='困守会稽', sub='山穷水尽', art=art_g_kuaiji),
    C(44, 48, 'court', 'card', year=-494, main='卑辞求和', sub='保住一命', art=art_g_bribe),
    # ---- 第二回 石室三年
    C(48, 50, 'fate', 'chapter'),
    C(50, 54, 'fate', 'card', year=-492, main='入吴为奴', sub='夫妻同往', art=art_g_slave),
    C(54, 60, 'night', 'card', year=-492, main='石室养马', sub='三年之辱', art=art_g_stable),
    C(60, 64, 'court', 'card', year=-491, main='问疾', sub='忍常人所不能忍', art=art_g_taste),
    C(64, 68, 'empire', 'card', year=-490, main='放归越国', sub='夫差的仁慈', art=art_g_release),
    C(68, 72, 'death', 'card', year=-490, main='重回故土', sub='百废待兴', art=art_g_home),
    C(72, 80, 'night', 'changdan', year=-490),
    # ---- 第三回 十年生聚
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'life', 'card', year=-489, main='亲耕', sub='与民同苦', art=art_g_farm),
    C(86, 90, 'works', 'card', year=-488, main='十年生聚', sub='增加人口', art=art_g_grow),
    C(90, 94, 'court', 'card', year=-486, main='伐吴九术', sub='文种献策', art=art_g_nine),
    C(94, 98, 'life', 'card', year=-485, main='美人计', sub='献西施', art=art_g_xishi),
    C(98, 102, 'fate', 'card', year=-485, main='蒸谷还吴', sub='吴地颗粒无收', art=art_g_seeds),
    C(102, 106, 'works', 'card', year=-484, main='十年教训', sub='训练士卒', art=art_g_drill),
    C(106, 112, 'war', 'card', year=-482, main='黄池之会', sub='乘虚而入', art=art_g_huangchi),
    # ---- 第四回 三千越甲
    C(112, 114, 'war', 'chapter'),
    C(114, 118, 'night', 'card', year=-478, main='笠泽之战', sub='夜渡奇袭', art=art_g_lize),
    C(118, 122, 'war', 'card', year=-475, main='围吴三年', sub='姑苏城下', art=art_g_siege),
    C(122, 130, 'death', 'card', year=-473, main='灭吴', sub='二十年终报', art=art_g_endwu),
    C(130, 134, 'empire', 'card', year=-472, main='徐州会盟', sub='春秋最后的霸主', art=art_g_xuzhou),
    C(134, 140, 'fate', 'card', year=-472, main='范蠡远去', sub='泛舟五湖', art=art_g_fanli),
    C(140, 144, 'death', 'card', year=-472, main='文种之死', sub='兔死狗烹', art=art_g_wenzhong),
    # ---- 第五回 千古一剑
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'empire', 'card', year=-468, main='迁都琅琊', sub='北上争雄', art=art_g_langya),
    C(150, 154, 'death', 'card', year=-465, main='越王去世', sub='一代霸主', art=art_g_death),
    C(154, 158, 'fate', 'card', year=-334, main='越国灭亡', sub='百余年后', art=art_g_yuefalls),
    C(158, 162, 'works', 'card', year=1680, main='苦心人', sub='天不负', art=art_g_couplet),
    C(162, 166, 'court', 'card', year=1965, main='越王剑出土', sub='两千年后', art=art_g_dig),
    C(166, 168, 'empire', 'card', year=1965, main='鸠浅自作', sub='剑上的八个字', art=art_g_inscription),
    C(168, 170, 'end', 'card', year=1965, main='千年不锈', sub='天下第一剑', art=art_g_rust),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='肆拾捌', col=JIZI, acc=KUDAN, born=-520, died=-465, no_age=True,
    born_lab='生年不详', died_lab='前465年', years_txt='生年不详 — 公元前465',
    hook_q='他忍了二十年 · 最后得到了什么？',
    name_line='越王 · 名鸠浅', name='勾践', seal='越王', title_art=art_g_title,
    q1='忍辱复国？', q2='鸟尽弓藏？',
    end_art=art_g_legacy, end_big='卧薪尝胆', end_seal='越王',
    end_l1='他用二十年 赢回了一个国家', end_l2='却没能留住陪他吃苦的人',
    end_brush='三千越甲可吞吴', end_ask='能共患难 不能同富贵？评论区聊聊', next='管仲'),
    scenes=dict(chapter=scene_chapter, changdan=scene_changdan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
