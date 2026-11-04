"""千古人物志 · 第伍拾伍集 · 萧何 (？–前193)
Look: 宫墙朱 + 档案绿, 算筹 corner borders, a 未央宫 chapter card: the palace is built up chapter by chapter
(platform → walls → roof → finished) and in the last chapter the lamps go dark.
Set pieces: 6-beat 丰沛子弟, custom 8-beat scene 'tushu' (收秦图籍), 6-beat 月下追韩信, 6-beat 转漕给军,
6-beat 功人功狗, 6-beat 营建未央, 6-beat 钟室.
Birth year unknown: the HUD hides ages (no_age).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zhangliang as Zl      # engine + helpers (previous episode)
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
from render_zhangliang import liubang
from render_lisi import dog

F.RIPPLE = False
WEIYANG = (160, 70, 56)             # 宫墙朱
DANGAN = (96, 106, 72)              # 档案绿
S.LAYERS.append(('weiyang', WEIYANG, 0.9, 1.0))
S.LAYERS.append(('dangan', DANGAN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='相', life='沛', court='汉', night='夜', war='粮', empire='汉', works='律', fate='追', death='钟', end='规')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (WEIYANG, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (WEIYANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (DANGAN, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

FARMS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(FARMS)
for _k in range(4):
    _y = 1450 + _k * 20
    _d.line((60, _y, W - 60, _y + 4), fill=DANGAN + (40,), width=3)
for _x in (130, 950):               # round granaries at the margins
    _d.ellipse((_x - 40, 1370, _x + 40, 1440), fill=(150, 130, 90, 50))
    _d.polygon([(_x - 50, 1385), (_x + 50, 1385), (_x, 1340)], fill=(110, 90, 70, 60))
MTN_COL = {'night': (32, 32, 40), 'death': (62, 56, 56), 'war': (110, 66, 52), 'fate': (92, 96, 90)}
def draw_background(t, theme):
    """关中: low hills, furrowed fields and granaries at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 186, 176), (156, 158, 140), MTN_COL.get(theme, (112, 118, 98))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(FARMS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """算筹: counting rods laid out as a numeral in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=DANGAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=DANGAN + (220,), width=3)
        for k in range(3):
            rx = x + sx * (20 + k * 14)
            d.line((rx, y + sy * 18, rx, y + sy * 70), fill=WEIYANG + (230,), width=5)
        d.line((x + sx * 70, y + sy * 30, x + sx * 110, y + sy * 30), fill=WEIYANG + (230,), width=5)
        d.line((x + sx * 70, y + sy * 50, x + sx * 110, y + sy * 50), fill=WEIYANG + (230,), width=5)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def xiao(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """萧何: Han chancellor — 进贤冠 with a slanted front ridge, full beard, a bundle of slips at the belt."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.polygon([(x - 0.07 * h, y - 0.95 * h), (x + 0.07 * h, y - 0.95 * h), (x + dir * 0.09 * h, y - 1.12 * h), (x - dir * 0.02 * h, y - 1.06 * h)], fill=255)
        d.polygon([(x + dir * 0.02 * h, y - 0.84 * h), (x + dir * 0.1 * h, y - 0.84 * h), (x + dir * 0.06 * h, y - 0.64 * h)], fill=255)
        A.d['dangan'].rectangle((min(x - dir * 0.12 * h, x - dir * 0.04 * h), y - 0.56 * h, max(x - dir * 0.12 * h, x - dir * 0.04 * h), y - 0.44 * h), fill=255)
        A.d['weiyang'].rectangle((x - 0.08 * h, y - 0.58 * h, x + 0.08 * h, y - 0.53 * h), fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.03 * h, y - 0.82 * h), (x + dir * 0.09 * h, y - 0.82 * h), (x + dir * 0.06 * h, y - 0.68 * h)], fill=255)
    return hand

def hanxin(A, x, y, h, dir=1, layer='mid', **kw):
    return person(A, x, y, h, dir=dir, robe=False, hat='helmet', layer=layer, **kw)

def lvhou(A, x, y, h, dir=-1, layer='ink', **kw):
    kw.setdefault('arm', 40)
    return person(A, x, y, h, dir=dir, robe=True, hat='knot', female=True, layer=layer, **kw)

def chest(A, x, base, s, layer='dangan', open_=0.0):
    A.d[layer].rectangle((x - s, base - 0.8 * s, x + s, base), fill=255)
    A.d['ink'].rectangle((x - s, base - 0.8 * s, x + s, base), outline=255, width=4)
    A.d['ink'].line((x - s - 4, base - 0.8 * s - 8 * open_ * 6, x + s + 4, base - 0.8 * s - 8 * open_ * 2), fill=255, width=8)

def weiyang_palace(A, cx, base, stage_, t):
    """stage 0 platform, 1 + walls, 2 + roof, 3 finished with lamps."""
    for k in range(3):
        A.d['mid'].rectangle((cx - 360 + k * 50, base - 40 * (k + 1), cx + 360 - k * 50, base - 40 * k), fill=230 - k * 20)
    if stage_ >= 1:
        q = clamp(stage_ - 1)
        A.d['weiyang'].rectangle((cx - 220, base - 120 - 160 * q, cx + 220, base - 120), fill=255)
        for k in range(6):
            A.d['ink'].line((cx - 200 + k * 80, base - 120, cx - 200 + k * 80, base - 120 - 160 * q), fill=200, width=6)
    if stage_ >= 2:
        q = clamp(stage_ - 2)
        A.d['ink'].polygon([(cx - 300, base - 280), (cx + 300, base - 280), (cx + 200, base - 280 - 90 * q), (cx - 200, base - 280 - 90 * q)], fill=255)
        A.d['ink'].polygon([(cx - 160, base - 370), (cx + 160, base - 370), (cx + 110, base - 370 - 50 * q), (cx - 110, base - 370 - 50 * q)], fill=255)
    if stage_ >= 3:
        for k in (-1, 1):
            lamp(A, cx + k * 260, base - 120, 40, t, glow=clamp(stage_ - 3) if stage_ < 4 else 0.9)

# ================================================================ chapter card
CH = {16: (0.0, 0.8), 48: (0.8, 1.8), 80: (1.8, 2.8), 112: (2.8, 3.9), 144: (3.9, 3.0)}
def art_palace_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    s0, s1 = CH.get(kb, (0.8, 1.8))
    q = ease_out(u / (1.2 * P))
    st = lerp(s0, s1, q)
    weiyang_palace(A, 540, 1220, st if kb != 144 else 2.99, t)
    if kb == 144:
        for k in (-1, 1):
            lamp(A, 540 + k * 260, 1100, 40, t, glow=lerp(0.9, 0.0, q))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_palace_chapter)
    ink_in(cv, text_img(no, SERIF, 56, DANGAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_x_hook_books(A, cv, t, u):
    ground(A, GROUND)
    carriage(A, lerp(-100, 600, ease_out(u / (1.4 * P))), GROUND, 120, dir=1, wheel=t * 6, ph=t * 8, canopy=False, layer='ink')
    chest(A, lerp(-100, 600, ease_out(u / (1.4 * P))), GROUND - 80, 60)

def art_x_hook_moon(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 260), (x + 200, GROUND)], fill=150)
    ground(A, GROUND)
    rider(A, lerp(-100, 700, ease_out(u / (1.6 * P))), GROUND, 140, dir=1, ph=t * 10)

def art_x_hook_bell(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    A.d['ink'].line((540, 1040, 540, 1100), fill=255, width=6)
    A.d['dangan'].polygon([(500, 1100), (580, 1100), (600, 1220), (480, 1220)], fill=255)

def art_x_hook_follow(A, cv, t, u):
    ground(A, GROUND)
    for i in range(2):
        person(A, lerp(200, 600, ease_out(u / (1.6 * P))) - i * 220, GROUND, 190, dir=1, robe=True, hat='knot', ph=t * 4, arm=-8, layer='ink' if i == 0 else 'dangan')

# ================================================================ 第一回 沛县小吏
def art_x_clerk(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='dangan')
    xiao(A, 300, GROUND, 190, dir=1, kneel=True, bow=20, arm=90)
    slips(A, 440, GROUND - 74, int(clamp(u / (2 * P)) * 10) + 1, 90, layer='weiyang')
    A.flush(cv)
    paste(cv, text_img('沛县主吏掾 · 以文无害著称', SERIF, 44, DANGAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('沛县', 56), 860, 1020, t, t - u + P, rot=6)

def art_x_protect(A, cv, t, u):
    ground(A, GROUND)
    liubang(A, 760, GROUND, 200, dir=-1, arm=lerp(20, 100, 0.5 + 0.5 * math.sin(t * 2)))
    xiao(A, 380, GROUND, 200, dir=1, arm=lerp(40, 120, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('刘季为泗水亭长 · 萧何数以吏事护之', SERIF, 42, DANGAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_five(A, cv, t, u):
    ground(A, GROUND)
    liubang(A, 760, GROUND, 200, dir=-1, arm=60)
    xiao(A, 380, GROUND, 200, dir=1, arm=90)
    n = min(5, int(u / (0.5 * P)) + 1)
    for i in range(n):
        A.d['gold'].ellipse((480 + i * 40 - 16, GROUND - 160 - 16, 480 + i * 40 + 16, GROUND - 160 + 16), fill=255)
    A.flush(cv)
    paste(cv, text_img(f'送役咸阳 · 吏皆奉钱三 萧何独以{cn_num(n)}', SERIF, 42, DANGAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, 1)

def art_x_refuse(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(20, 120, ease_out(u / 0.5)), layer='ink')
    xiao(A, 380, GROUND, 200, dir=1, bow=20, arm=90)
    A.flush(cv)
    paste(cv, text_img('秦御史欲征之入咸阳 · 何固请 得毋行', SERIF, 42, DANGAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_rise(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='沛', layer='mid', open_=1.0)
    ground(A, GROUND)
    liubang(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 140, ease_out(u / 0.6)))
    for i in range(4):
        person(A, 240 + i * 50 if i < 2 else 780 + (i - 2) * 50, GROUND, 150, dir=1 if i < 2 else -1, robe=True, hat='knot', arm=110, layer='ink')
    banner(A, 880, GROUND, 280, t, layer='red')
    A.flush(cv)
    paste(cv, text_img('沛中子弟共立刘季为沛公', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_recruit(A, cv, t, u):
    """6-beat set piece: 丰沛子弟 — he lists the young men of Feng and Pei; the column grows to three thousand."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 200, GROUND, 220, layer='dangan')
    xiao(A, 120, GROUND, 160, dir=1, kneel=True, arm=90)
    n = int(clamp(ph / 5) * 30) + 1
    for i in range(n):
        person(A, 360 + (i % 10) * 64, GROUND - (i // 10) * 70, 90, dir=1, robe=False, hat='knot', spear=i % 3 == 0, arm=40, layer='ink' if i % 2 else 'dangan')
    A.flush(cv)
    num = int(lerp(0, 3000, clamp(ph / 5)))
    paste(cv, text_img(f'收沛子弟 {num} 人', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('丰沛', 56), 860, 1020, t, t - u + 0.4, rot=6)

def art_x_rear(A, cv, t, u):
    tent(A, 540, GROUND, 420, 280, layer='dangan')
    ground(A, GROUND)
    xiao(A, 360, GROUND, 200, dir=1, arm=60)
    for i in range(int(clamp(u / (2 * P)) * 6)):
        A.d['yellow'].ellipse((640 + (i % 3) * 60 - 26, GROUND - 40 - (i // 3) * 40, 640 + (i % 3) * 60 + 26, GROUND - (i // 3) * 40), fill=255)
    A.flush(cv)
    paste(cv, text_img('沛公为丞 · 常督事', SERIF, 46, DANGAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 收图籍
def art_x_surrender(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 220), (x + 200, GROUND)], fill=150)
    ground(A, GROUND)
    carriage(A, 760, GROUND, 110, dir=-1, moving=False, horses=True, layer='mid')
    person(A, 560, GROUND, 190, dir=1, robe=True, hat='crown', kneel=True, bow=40, arm=100, layer='ink')
    liubang(A, 240, GROUND, 210, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('秦王子婴 素车白马 降于道旁', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_tushu(cv, t, c, k):
    """8-beat custom scene: 收秦图籍 — in Xianyang the generals rush to the treasuries for gold and silk; he alone goes to the
    chancellor's archive, opens chest after chest of laws, maps and registers, and carts them away."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    A.d['mid'].rectangle((60, 980, 460, GROUND), fill=180)
    A.d['weiyang'].rectangle((620, 980, W - 60, GROUND), fill=150)
    for i in range(5):
        x = (t * 90 + i * 140) % 380 + 80
        person(A, x, GROUND, 110, dir=-1, robe=False, hat='helmet', load=True, ph=t * 5 + i, arm=160, layer='ink')
        A.d['gold'].ellipse((x - 18, GROUND - 140, x + 18, GROUND - 110), fill=255)
    n = min(6, int(clamp((ph - 1) / 4) * 6) + 1)
    for i in range(6):
        chest(A, 700 + (i % 3) * 110, GROUND - (i // 3) * 90, 46, open_=1.0 if i < n else 0.0)
    xiao(A, lerp(560, 640, clamp(ph / 1)), GROUND, 180, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)))
    if ph > 5.5:
        carriage(A, lerp(700, 1200, ease_out((ph - 5.5) / 2)), GROUND, 90, dir=1, wheel=t * 6, ph=t * 8, canopy=False, layer='dangan')
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '收秦图籍', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=55)
    fx.flush(cv)
    lab = '诸将皆争走金帛财物之府' if ph < 2 else ('何独先入收秦丞相御史律令图书' if ph < 5.5 else '汉王所以具知天下阸塞 户口多少')
    paste(cv, text_img(lab, SERIF, 42, ZHU if 2 <= ph < 5.5 else DANGAN, 'Black', bleed=False, spacing=2), W / 2, 575, 1, 1)
    paste(cv, text_img('律令 · 地图 · 户籍', SERIF, 42, DIM, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((ph - 2) / 0.4))

def art_x_burn(A, cv, t, u):
    palace(A, 540, 1260, 440, collapse=ease_out(u / (2.5 * P)), layer='mid')
    flames(A, 540, 1200, 560, 240 * ease_out(u / P), t, n=7, seed=2062, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('项羽焚咸阳 · 大火三月不灭', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('图籍得存', 44), 860, 1020, t, t - u + P, rot=6)

def art_x_hanzhong(A, cv, t, u):
    for k in range(4):
        x = 140 + k * 280
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 420), (x + 200, GROUND)], fill=170)
    ground(A, GROUND)
    liubang(A, 760, GROUND, 200, dir=-1, arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 3)))
    xiao(A, 380, GROUND, 200, dir=1, arm=lerp(40, 110, ease_out(u / 0.5)))
    A.flush(cv)
    type_in(cv, text_img('愿大王王汉中 养其民以致贤人', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('劝王汉中', 44), 260, 1020, t, t - u + P, rot=-5)

def art_x_chase(A, cv, t, u):
    """6-beat set piece: 月下追韩信 — under the moon a lone rider gallops along the river; he catches up with Han Xin at dawn."""
    ph = u / P
    r = 60
    A.d['wash'].ellipse((820 - r, 820 - r, 820 + r, 820 + r), fill=255)
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=120)
    waves(A, 1250, t, rows=2, amp=4)
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, 1240), (x, 1240 - 220), (x + 200, 1240)], fill=110)
    if ph < 4:
        rider(A, lerp(-100, 800, ph / 4), 1240, 130, dir=1, ph=t * 10)
        hanxin(A, 980, 1240, 160, dir=1, ph=t * 3, arm=-8, layer='mid')
    else:
        horse(A, 300, 1240, 130, dir=1, moving=False, head_down=0.4)
        xiao(A, 560, 1240, 180, dir=1, bow=30, arm=100)
        hanxin(A, 760, 1240, 180, dir=-1, arm=40)
    A.flush(cv)
    lab = '人言丞相何亡' if ph < 1.6 else ('上大怒 如失左右手' if ph < 4 else '诸将易得耳 至如信者 国士无双')
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 4 else DANGAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('月下', 56), 260, 1020, t, t - u + 0.4, rot=-5)

def art_x_altar(A, cv, t, u):
    for k in range(3):
        A.d['weiyang'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    hanxin(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 80, ease_out(u / 0.6)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('择良日 斋戒 设坛场 · 拜韩信为大将', SERIF, 42, DANGAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 镇抚关中
def art_x_guard(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='栎阳', layer='dangan', open_=1.0)
    ground(A, GROUND)
    xiao(A, 540, GROUND, 200, dir=1, arm=60)
    person(A, 660, GROUND, 110, dir=-1, robe=True, hat='crown', arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('留收巴蜀 · 侍太子 治栎阳', SERIF, 46, DANGAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('镇抚', 56), 860, 1020, t, t - u + P, rot=6)

def art_x_supply(A, cv, t, u):
    """6-beat set piece: 转漕给军 — an endless line of grain carts and boats moves east from Guanzhong; the counter of loads climbs."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1100, W - 60, 1150), fill=140)
    for j in range(4):
        boat(A, (t * 80 + j * 280) % (W + 200) - 100, 1130, 50, t + j, sail=True)
    ground(A, GROUND)
    for j in range(6):
        x = (t * 110 + j * 190) % (W + 300) - 150
        carriage(A, x, GROUND, 70, dir=1, wheel=t * 6, ph=t * 8 + j, canopy=False, layer='ink')
        A.d['yellow'].ellipse((x - 40, GROUND - 120, x + 40, GROUND - 70), fill=255)
    A.flush(cv)
    n = int(lerp(0, 10000, clamp(ph / 5)))
    paste(cv, text_img(f'关中事计户口转漕给军 · {n} 车', SERIF, 42, DANGAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, 1)
    paste(cv, text_img('汉王数失军遁去 何常兴关中卒 辄补缺', SERIF, 40, INK, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 3) / 0.4))

def art_x_census(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='dangan')
    xiao(A, 280, GROUND, 190, dir=1, kneel=True, bow=20, arm=90)
    n = int(clamp(u / (2 * P)) * 12) + 1
    for i in range(n):
        person(A, 640 + (i % 6) * 50, GROUND - 74 - (i // 6) * 40, 50, dir=-1, robe=i % 2 == 0, hat='knot', arm=30, layer='ink')
    A.flush(cv)
    paste(cv, text_img('彭城大败 · 发关中老弱未傅者悉诣军', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_sons(A, cv, t, u):
    ground(A, GROUND)
    xiao(A, 300, GROUND, 200, dir=1, arm=60)
    for i in range(4):
        person(A, lerp(380, 820, ease_out(u / (2.5 * P))) + i * 60, GROUND, 150, dir=1, robe=False, hat='helmet', spear=True, ph=t * 4 + i, arm=40, layer='dangan')
    A.flush(cv)
    paste(cv, text_img('鲍生曰 王暴衣露盖 数使使劳苦君者 有疑君心', SERIF, 38, DANGAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))
    type_in(cv, text_img('遣子孙昆弟能胜兵者悉诣军所', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 835, t, t - u + 1.5 * P, 0.5)

def art_x_ancestral(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='weiyang')
    ground(A, GROUND)
    for k in range(2):
        A.d['ink'].rectangle((300 + k * 400, GROUND - 120, 380 + k * 400, GROUND), fill=255)
    xiao(A, 540, GROUND, 190, dir=1, bow=20, arm=90)
    A.flush(cv)
    paste(cv, text_img('立宗庙 社稷 宫室 县邑', SERIF, 46, DANGAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_hound(A, cv, t, u):
    """6-beat set piece: 功人功狗 — the generals protest that Xiao He never fought; Liu Bang answers with the hunt: the dogs chase, the hunter points."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        palace(A, 540, 1260, 380, layer='mid')
        for i in range(4):
            person(A, 200 + i * 80, GROUND, 170, dir=1, robe=False, hat='helmet', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 4 + i)), layer='ink')
        liubang(A, 820, GROUND - 30, 200, dir=-1, arm=40)
    else:
        for j in range(3):
            dog(A, lerp(200, 800, ((t * 0.3 + j / 3) % 1)), GROUND, 80, dir=1, ph=t * 12 + j, layer='mid')
        A.d['wash'].ellipse((lerp(320, 920, ((t * 0.3) % 1)) - 20, GROUND - 40, lerp(320, 920, ((t * 0.3) % 1)) + 20, GROUND - 10), fill=255)
        person(A, 160, GROUND, 200, dir=1, robe=True, hat='knot', arm=lerp(40, 100, clamp((ph - 2.6) / 0.4)), layer='ink')
    A.flush(cv)
    lab = '萧何未尝有汗马之劳 顾反居臣等上' if ph < 2 else ('追杀兽兔者狗也 而发踪指示兽处者人也' if ph < 4.4 else '诸君徒能得走兽耳 功狗也 至如萧何 功人也')
    paste(cv, text_img(lab, SERIF, 38, ZHU if ph >= 4.4 else DANGAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    stamp(cv, seal('第一', 60), 860, 1440, t, t - u + 4.4 * P, rot=6)

def art_x_sword(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='weiyang')
    ground(A, GROUND)
    xiao(A, lerp(200, 520, ease_out(u / (1.6 * P))), GROUND, 200, dir=1, arm=-8)
    A.d['ink'].line((560, GROUND - 100, 620, GROUND - 40), fill=255, width=6)
    A.flush(cv)
    paste(cv, text_img('剑履上殿 · 入朝不趋', SERIF, 46, DANGAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 相国
def art_x_law(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='dangan')
    xiao(A, 280, GROUND, 190, dir=1, kneel=True, bow=20, arm=90)
    n = min(9, int(u / (0.4 * P)) + 1)
    for i in range(n):
        bundle(A, 420 + i * 40, GROUND - 74, 34, layer='weiyang')
    A.flush(cv)
    paste(cv, text_img(f'攈摭秦法 取其宜于时者 · 作律{cn_num(n)}章', SERIF, 42, DANGAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, 1)
    stamp(cv, seal('九章律', 50), 860, 1020, t, t - u + P, rot=6)

def art_x_build(A, cv, t, u):
    """6-beat set piece: 营建未央 — terraces, walls, roofs rise; the emperor returns, angry at the cost; Xiao He's answer."""
    ph = u / P
    weiyang_palace(A, 540, GROUND, lerp(0.2, 3.5, clamp(ph / 4)), t)
    for j in range(4):
        x = (t * 70 + j * 260) % (W + 200) - 100
        person(A, x, GROUND, 90, dir=1, robe=False, hat='knot', load=True, ph=t * 5 + j, arm=160, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    lab = '萧丞相营作未央宫' if ph < 3 else ('高祖见其壮甚 怒' if ph < 4.3 else '天子以四海为家 非壮丽无以重威')
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 4.3 else DANGAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('未央宫', 50), 860, 1440, t, t - u + 0.4, rot=6)

def art_x_bell(A, cv, t, u):
    """6-beat set piece: 钟室 — a false report of victory; Han Xin is summoned to court to congratulate; in the bell room behind the Changle palace
    he is seized; the bell swings."""
    ph = u / P
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    if ph < 2.4:
        xiao(A, 700, GROUND, 190, dir=-1, arm=lerp(40, 110, 0.5 + 0.5 * math.sin(t * 2)))
        hanxin(A, 380, GROUND, 190, dir=1, arm=-8, layer='ink')
        lab = '诈称陈豨已破 · 萧何绐信入贺'
    else:
        lvhou(A, 820, GROUND, 190, dir=-1, arm=lerp(40, 140, clamp((ph - 2.4) / 0.4)))
        A.d['ink'].line((540, 1000, 540, 1060), fill=255, width=6)
        a = 0.25 * math.sin(t * 3) * clamp(1 - (ph - 4) / 2)
        A.d['dangan'].polygon([(540 - 50 * math.cos(a), 1060), (540 + 50 * math.cos(a), 1060), (540 + 70 + 100 * a, 1200), (540 - 70 + 100 * a, 1200)], fill=255)
        hanxin(A, 360, GROUND, 180, dir=1, kneel=ph > 3, bow=30 if ph > 3 else 0, arm=-8, layer='ink')
        for j in range(2):
            person(A, 260 - j * 80, GROUND, 170, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
        lab = '吕后使武士缚信 斩之长乐钟室'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 2.4 else DANGAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph > 4.4:
        paste(cv, text_img('成也萧何 败也萧何', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 835, 1, clamp((ph - 4.4) / 0.4))

def art_x_xiangguo(A, cv, t, u):
    for k in range(3):
        A.d['weiyang'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    xiao(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    stamp(cv, seal('相国', 60), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('拜为相国 · 益封五千户 令卒五百人为卫', SERIF, 40, DANGAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_shaoping(A, cv, t, u):
    for k in range(3):
        A.d['grass'].ellipse((160 + k * 140 - 50, GROUND - 60, 160 + k * 140 + 50, GROUND), fill=220)
    ground(A, GROUND)
    person(A, 520, GROUND, 190, dir=1, robe=True, hat='knot', arm=lerp(40, 120, ease_out(u / 0.5)), layer='ink')
    xiao(A, 780, GROUND, 200, dir=-1, arm=40)
    A.flush(cv)
    type_in(cv, text_img('祸自此始矣 · 让封勿受 悉以家私财佐军', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('召平', 54, INK), 260, 1020, t, t - u + P, rot=-5)

def art_x_smear(A, cv, t, u):
    A.d['grass'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=150)
    ground(A, GROUND)
    xiao(A, 700, GROUND - 40, 200, dir=-1, arm=lerp(40, 120, ease_out(u / 0.5)))
    for j in range(4):
        person(A, 200 + j * 90, GROUND - 40, 150, dir=1, robe=True, hat='knot', kneel=j % 2 == 0, bow=20, arm=110, layer='mid')
    A.flush(cv)
    paste(cv, text_img('多买田地 贱贳贷以自污', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '客劝之曰 君灭族不久矣', t, t - u + P)

def art_x_jail(A, cv, t, u):
    A.d['ink'].rectangle((320, 900, 760, GROUND), outline=255, width=8)
    for k in range(9):
        A.d['ink'].line((320 + k * 55, 900, 320 + k * 55, GROUND), fill=200, width=4)
    xiao(A, 540, GROUND, 190, dir=1, kneel=True, bow=30, arm=-8, old=0.8)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('请上林苑空地与民 · 系狱数日', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.3))

# ================================================================ 第五回 萧规曹随
def art_x_caoshen(A, cv, t, u):
    A.d['mid'].rectangle((200, 1200, 640, 1260), fill=230)
    A.d['ink'].rectangle((180, 1260, 660, 1290), fill=255)
    xiao(A, 420, 1200, 200, dir=1, fall=-82, arm=lerp(-8, 50, ease_out(u / 0.6)), old=1.0)
    person(A, 800, GROUND, 200, dir=-1, robe=True, hat='crown', kneel=True, bow=20, arm=60, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('孝惠问谁可代君者 · 帝得之矣 臣死不恨', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('曹参', 54), 860, 1020, t, t - u + P, rot=6)

def art_x_death(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    lamp(A, 820, GROUND, 50, t, glow=clamp(1 - (u - P) / 1))
    A.flush(cv)
    paste(cv, text_img('置田宅必居穷处 为家不治垣屋', SERIF, 42, DANGAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('文终', 56), 260, 1020, t, t - u + P, rot=-5)

def art_x_follow(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='dangan')
    person(A, 300, GROUND, 190, dir=1, robe=True, hat='knot', kneel=True, arm=-8, layer='ink')
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    for i in range(6):
        bundle(A, 440 + i * 40, GROUND - 74, 34, layer='weiyang')
    A.flush(cv)
    paste(cv, text_img('萧何为法 讲若画一 · 曹参代之 守而勿失', SERIF, 40, DANGAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_taishi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    A.flush(cv)
    type_in(cv, text_img('位冠群臣 声施后世', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('太史公', 50), 860, 1020, t, t - u + P, rot=6)

def art_x_proverb(A, cv, t, u):
    q = ease_out(u / P)
    A.d['dangan'].rectangle((280, 1000, 500, 1240), fill=200)
    A.d['weiyang'].rectangle((580, 1000, 800, 1240), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('成', BRUSH, 150, INK), 390, 1120, 1, clamp(u / 0.3))
    paste(cv, text_img('败', BRUSH, 150, ZHU), 690, 1120, 1, clamp((u - P) / 0.3))
    paste(cv, text_img('语出洪迈容斋续笔', SERIF, 44, DANGAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_three(A, cv, t, u):
    ground(A, GROUND)
    for i, (lay, hat) in enumerate((('dangan', 'knot'), ('yunyan', 'knot'), ('mid', 'helmet'))):
        person(A, 300 + i * 240, GROUND, 190, dir=1, robe=hat == 'knot', hat=hat, arm=40, layer=lay)
    A.flush(cv)
    for i, nm in enumerate(('萧何', '张良', '韩信')):
        stamp(cv, seal(nm, 40, ZHU if i == 0 else INK), 300 + i * 240, 1040, t, t - u + i * 0.4 * P)
    paste(cv, text_img('汉初三杰', SERIF, 48, DANGAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_x_root(A, cv, t, u):
    for i in range(6):
        chest(A, 260 + (i % 3) * 280, GROUND - (i // 3) * 110, 60, open_=0.0)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('一车图籍 · 四百年汉家法度', SERIF, 46, DANGAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    chest(A, 860, 1380, 50)

def art_x_title(A, cv, t, u):
    weiyang_palace(A, 820, 1460, 3.6, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    xiao(A, 360, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '沛县小吏'), 48: ('第二回', '收秦图籍'), 80: ('第三回', '镇抚关中'),
            112: ('第四回', '相国'), 144: ('第五回', '萧规曹随')}

CARDS = [
    C(0, 2, 'works', 'num', num='一车图书', line='比金子值钱', art=art_x_hook_books),
    C(2, 4, 'night', 'num', num='一个月夜', line='追回一个大将', art=art_x_hook_moon),
    C(4, 6, 'death', 'num', num='成也萧何', line='败也萧何', art=art_x_hook_bell),
    C(6, 8, 'court', 'num', num='萧规曹随', line='一个成语', art=art_x_hook_follow),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 沛县小吏
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'works', 'card', year=-220, main='沛县主吏', sub='文无害', note='生年不详', art=art_x_clerk),
    C(22, 26, 'life', 'card', year=-215, main='屡护刘季', sub='小吏的眼光', art=art_x_protect),
    C(26, 30, 'court', 'card', year=-212, main='独送五百', sub='多给二百钱', art=art_x_five),
    C(30, 34, 'fate', 'card', year=-210, main='不入咸阳', sub='秦吏的选择', art=art_x_refuse),
    C(34, 38, 'war', 'card', year=-209, main='沛县起兵', sub='立刘季为沛公', art=art_x_rise),
    C(38, 44, 'works', 'card', year=-209, main='丰沛子弟', sub='三千人', art=art_x_recruit),
    C(44, 48, 'court', 'card', year=-208, main='常督后方', sub='沛公之丞', art=art_x_rear),
    # ---- 第二回 收秦图籍
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'empire', 'card', year=-207, main='子婴出降', sub='入关', art=art_x_surrender),
    C(54, 62, 'works', 'tushu', year=-207),
    C(62, 66, 'death', 'card', year=-206, main='火烧咸阳', sub='幸而先取', art=art_x_burn),
    C(66, 70, 'court', 'card', year=-206, main='劝王汉中', sub='退一步', art=art_x_hanzhong),
    C(70, 76, 'night', 'card', year=-206, main='月下追韩信', sub='国士无双', art=art_x_chase),
    C(76, 80, 'empire', 'card', year=-206, main='登坛拜将', sub='力荐韩信', art=art_x_altar),
    # ---- 第三回 镇抚关中
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'court', 'card', year=-205, main='留守关中', sub='镇国家 抚百姓', art=art_x_guard),
    C(86, 92, 'war', 'card', year=-205, main='转漕给军', sub='源源不断', art=art_x_supply),
    C(92, 96, 'night', 'card', year=-205, main='补足兵员', sub='彭城之后', art=art_x_census),
    C(96, 100, 'fate', 'card', year=-203, main='遣子从军', sub='以释君疑', art=art_x_sons),
    C(100, 104, 'works', 'card', year=-203, main='立宗庙', sub='为汉立制', art=art_x_ancestral),
    C(104, 110, 'empire', 'card', year=-202, main='功人功狗', sub='论功第一', art=art_x_hound),
    C(110, 112, 'court', 'card', year=-201, main='剑履上殿', sub='殊礼', art=art_x_sword),
    # ---- 第四回 相国
    C(112, 114, 'court', 'chapter'),
    C(114, 118, 'works', 'card', year=-201, main='九章律', sub='汉律之始', art=art_x_law),
    C(118, 124, 'empire', 'card', year=-200, main='营建未央', sub='非壮丽无以重威', art=art_x_build),
    C(124, 130, 'death', 'card', year=-196, main='钟室', sub='亲手送他入局', art=art_x_bell),
    C(130, 134, 'court', 'card', year=-196, main='拜为相国', sub='恩宠背后', art=art_x_xiangguo),
    C(134, 138, 'night', 'card', year=-196, main='召平之言', sub='让封避祸', art=art_x_shaoping),
    C(138, 142, 'fate', 'card', year=-195, main='自污名节', sub='强买民田', art=art_x_smear),
    C(142, 144, 'death', 'card', year=-195, main='系狱', sub='相国下狱', art=art_x_jail),
    # ---- 第五回 萧规曹随
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'life', 'card', year=-193, main='荐曹参', sub='不计前嫌', art=art_x_caoshen),
    C(150, 154, 'death', 'card', year=-193, main='萧何去世', sub='谥文终', art=art_x_death),
    C(154, 158, 'works', 'card', year=-190, main='萧规曹随', sub='守而勿失', art=art_x_follow),
    C(158, 162, 'court', 'card', year=-91, main='太史公曰', sub='位冠群臣', art=art_x_taishi),
    C(162, 166, 'night', 'card', year=1180, main='成败萧何', sub='一句俗语', art=art_x_proverb),
    C(166, 168, 'empire', 'card', year=1180, main='汉初三杰', sub='居首', art=art_x_three),
    C(168, 170, 'end', 'card', year=1180, main='律令图书', sub='江山之本', art=art_x_root),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='伍拾伍', col=DANGAN, acc=WEIYANG, born=-257, died=-193, no_age=True,
    born_lab='生年不详', died_lab='前193年', years_txt='生年不详 — 公元前193',
    hook_q='他月下追回韩信 · 为什么又亲手送他去死？',
    name_line='萧何 · 沛县丰人', name='萧何', seal='文终', title_art=art_x_title,
    q1='开国第一功臣？', q2='明哲保身者？',
    end_art=art_x_legacy, end_big='萧规曹随', end_seal='文终',
    end_l1='他为汉朝留下了图籍和法度', end_l2='也留下了一句成也萧何',
    end_brush='成也萧何败也萧何', end_ask='萧何害韩信 是自保还是忠心？评论区聊聊', next='刘秀'),
    scenes=dict(chapter=scene_chapter, tushu=scene_tushu))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
