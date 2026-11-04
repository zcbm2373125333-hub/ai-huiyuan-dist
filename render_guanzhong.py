"""千古人物志 · 第肆拾玖集 · 管仲 (约前723–前645)
Look: 刀币金 + 海盐青, 齐刀币 corner borders, a 刀币 chapter card: Qi knife-coins stack up (0→3→6→9) and in the
last chapter they scatter.
Set pieces: 6-beat 管鲍分金, custom 8-beat scene 'daigou' (一箭射钩 · 争位), 6-beat 释怨拜相, 6-beat 官山海,
8-beat 九合诸侯 map, 6-beat 病榻遗言.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_goujian as Gj         # engine + helpers (previous episode)
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
DAOBI = (176, 136, 46)              # 刀币金
YANHAI = (64, 118, 136)             # 海盐青
S.LAYERS.append(('daobi', DAOBI, 0.9, 1.0))
S.LAYERS.append(('yanhai', YANHAI, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='相', life='鲍', court='齐', night='夜', war='霸', empire='齐', works='富', fate='囚', death='终', end='相')
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
G.THEMES['empire']['sun'] = (DAOBI, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (YANHAI, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

SALT = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(SALT)
for _k in range(3):                 # 东海 sea lines
    _y = 1470 + _k * 18
    _d.line((60, _y, W - 60, _y), fill=YANHAI + (40 - _k * 8,), width=3)
for _x0 in (90, 830):               # 盐田 salt pans at the margins
    for _i in range(3):
        for _j in range(2):
            _d.rectangle((_x0 + _i * 54, 1380 + _j * 36, _x0 + _i * 54 + 46, 1380 + _j * 36 + 28), fill=(236, 236, 230, 70), outline=YANHAI + (60,))
MTN_COL = {'night': (32, 36, 44), 'death': (60, 60, 62), 'war': (110, 64, 46), 'fate': (90, 96, 104)}
def draw_background(t, theme):
    """齐地: low hills, salt pans and the eastern sea at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 188, 176), (156, 160, 150), MTN_COL.get(theme, (110, 120, 116))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(SALT)
    return canvas
G.draw_background = draw_background

def _knife_pts(x, y, s, sx=1, sy=1):
    pts = [(0, 0), (0.18, -0.02), (0.75, 0.1), (0.95, 0.3), (0.9, 0.38), (0.7, 0.22), (0.2, 0.14), (0.16, 0.3), (0.0, 0.3)]
    return [(x + sx * px * s, y + sy * py * s) for px, py in pts]

def draw_frame_border(canvas):
    """齐刀币: a knife-shaped coin with its ring handle in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=YANHAI + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=YANHAI + (220,), width=3)
        d.polygon(_knife_pts(x + sx * 34, y + sy * 26, 110, sx, sy), fill=DAOBI + (230,))
        cx, cy = x + sx * 26, y + sy * 40
        d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), outline=DAOBI + (230,), width=5)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def guan(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """管仲: Qi chancellor — tall rounded 冠 with a pin, long beard, bronze belt hook."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rounded_rectangle((x - 0.06 * h, y - 1.1 * h, x + 0.06 * h, y - 0.94 * h), radius=int(0.05 * h), fill=255)
        A.d['daobi'].line((x - 0.11 * h, y - 1.02 * h, x + 0.11 * h, y - 1.02 * h), fill=255, width=max(2, int(0.016 * h)))
        d.polygon([(x + dir * 0.04 * h, y - 0.84 * h), (x + dir * 0.1 * h, y - 0.84 * h), (x + dir * 0.06 * h, y - 0.66 * h)], fill=255)
        A.d['daobi'].ellipse((x - 0.03 * h, y - 0.58 * h, x + 0.03 * h, y - 0.52 * h), fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.05 * h, y - 0.82 * h), (x + dir * 0.09 * h, y - 0.82 * h), (x + dir * 0.06 * h, y - 0.68 * h)], fill=255)
    return hand

def duke(A, x, y, h, dir=-1, layer='ink', **kw):
    """齐桓公 (公子小白)."""
    return person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)

def knife_coin(A, x, y, s, layer='daobi', ang=0.0):
    pts = _knife_pts(0, 0, s)
    ca, sa = math.cos(ang), math.sin(ang)
    A.d[layer].polygon([(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts], fill=255)
    A.d['ink'].ellipse((x - 0.1 * s, y + 0.05 * s, x + 0.1 * s, y + 0.25 * s), outline=200, width=3)

def cage_cart(A, x, base, s, t, moving=True):
    carriage(A, x, base, s, dir=1, wheel=t * 4 if moving else 0, ph=t * 6, moving=moving, canopy=False, layer='mid')
    for k in range(6):
        A.d['ink'].line((x - 0.5 * s + k * 0.2 * s, base - 0.5 * s, x - 0.5 * s + k * 0.2 * s, base - 1.4 * s), fill=255, width=4)
    A.d['ink'].line((x - 0.55 * s, base - 1.4 * s, x + 0.55 * s, base - 1.4 * s), fill=255, width=6)

def salt_pot(A, x, base, s, t):
    A.d['ink'].polygon([(x - s, base - 0.8 * s), (x + s, base - 0.8 * s), (x + 0.8 * s, base), (x - 0.8 * s, base)], fill=255)
    flames(A, x, base + 10, 1.6 * s, 0.5 * s, t, n=4, seed=int(x), smoke=False)
    for k in range(4):
        q = (t * 0.6 + k / 4) % 1
        A.d['wash'].ellipse((x - 0.5 * s + k * 0.3 * s - 16, base - 0.8 * s - 200 * q - 16, x - 0.5 * s + k * 0.3 * s + 16, base - 0.8 * s - 200 * q + 16), fill=int(180 * (1 - q)))

# ================================================================ chapter card
CH = {16: (0, 0.0), 48: (3, 0.0), 80: (6, 0.0), 112: (9, 0.0), 144: (9, 1.0)}
def art_coin_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g, scat = CH.get(kb, (3, 0.0))
    prev = {48: 0, 80: 3, 112: 6, 144: 9}.get(kb, 0)
    q = ease_out(u / (1.2 * P))
    n = int(lerp(prev, g, q)) if not scat else 9
    for i in range(n):
        if scat:
            a = i * 0.7 + 0.3
            x = 300 + i * 60 + 200 * q * math.cos(a)
            y = 1080 + 140 * q * math.sin(a) + 120 * q
            knife_coin(A, x, y, 150, ang=0.3 * i * q)
        else:
            knife_coin(A, 380, 1180 - i * 34, 300, ang=-0.12 + 0.03 * (i % 2))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_coin_chapter)
    ink_in(cv, text_img(no, SERIF, 56, YANHAI, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_z_hook_arrow(A, cv, t, u):
    ground(A, GROUND)
    q = ease_out(u / P)
    arrow(A, lerp(200, 700, q), 1100, 0.0, 120)
    A.d['daobi'].ellipse((760 - 30, 1090 - 30, 760 + 30, 1090 + 30), fill=255)

def art_z_hook_nine(A, cv, t, u):
    ground(A, GROUND)
    n = min(9, int(clamp(u / (1.4 * P)) * 9) + 1)
    for i in range(n):
        a = math.radians(-90 + i * 40)
        banner(A, 540 + 330 * math.cos(a), 1180 + 120 * math.sin(a), 180, t, layer='daobi' if i % 2 else 'yanhai')

def art_z_hook_three(A, cv, t, u):
    palace(A, 540, 1140, 520, layer='mid')
    ground(A, GROUND)
    for i in range(3):
        person(A, 300 + i * 220, GROUND, 170, dir=1 if i % 2 else -1, robe=True, hat='knot', arm=lerp(-8, 60, 0.5 + 0.5 * math.sin(t * 3 + i)), layer='ink')

def art_z_hook_kongzi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='yanhai')
    sitter(A, 300, GROUND, 200, dir=1, bow=10)
    slips(A, 460, GROUND - 74, int(clamp(u / P) * 8) + 1, 90, layer='daobi')

# ================================================================ 第一回 管鲍之交
def art_z_birth(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=4)
    A.d['mid'].rectangle((360, 1080, 720, 1240), fill=220)
    A.d['ink'].polygon([(320, 1080), (760, 1080), (540, 960)], fill=255)
    person(A, 820, 1240, 140, dir=-1, robe=True, hat='knot', arm=20, layer='ink')
    A.flush(cv)
    stamp(cv, seal('颍上', 56), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('先祖为周穆王之后 · 家道中落', SERIF, 44, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_friend(A, cv, t, u):
    ground(A, GROUND)
    guan(A, 380, GROUND, 210, dir=1, arm=lerp(-8, 70, ease_out(u / 0.6)))
    person(A, 680, GROUND, 210, dir=-1, robe=True, hat='knot', arm=lerp(-8, 70, ease_out((u - 0.3) / 0.6)), layer='yanhai')
    A.flush(cv)
    paste(cv, text_img('少时与鲍叔牙相识', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('鲍叔牙', 50), 860, 1020, t, t - u + P, rot=6)

def art_z_split(A, cv, t, u):
    """6-beat set piece: 管鲍分金 — two partners split the takings; Guan takes the larger pile; Bao waves it off."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mid')
    guan(A, 260, GROUND, 200, dir=1, arm=lerp(40, 120, clamp((ph - 1.5) / 0.4)))
    person(A, 820, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(40, 100, clamp((ph - 3.5) / 0.4)), layer='yanhai')
    tot = 10
    left = int(lerp(5, 7, clamp((ph - 1.5) / 1)))
    for i in range(tot):
        side = i < left
        x = (420 if side else 600) + (i % 3) * 36 * (1 if side else 1)
        y = GROUND - 90 - (i // 3 if side else (i - left) // 3) * 22
        knife_coin(A, x if side else 600 + ((i - left) % 3) * 36, y, 60, ang=-0.2)
    A.flush(cv)
    lab = '合伙经商 · 分财利' if ph < 1.5 else ('管仲多取' if ph < 3.5 else '鲍叔不以我为贪 知我贫也')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('南阳', 54), 260, 1020, t, t - u + 0.4, rot=-5)

def art_z_fired(A, cv, t, u):
    palace(A, 540, 1140, 520, layer='mid')
    ground(A, GROUND)
    n = min(3, int(u / (1.1 * P)) + 1)
    guan(A, lerp(540, 980, clamp(((u / P) % 1.1) / 1.1)), GROUND, 200, dir=1, ph=t * 4, arm=-8)
    A.flush(cv)
    paste(cv, text_img(f'三仕三见逐于君 · 第{cn_num(n)}次', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('不以我为不肖', 38, INK), 860, 1020, t, t - u + 2 * P, rot=6)

def art_z_retreat(A, cv, t, u):
    ground(A, GROUND)
    army(A, lerp(980, 1100, ease_out(u / P)), GROUND, 4, dir=-1, layer='mid', h=100)
    guan(A, lerp(600, 160, ease_out(u / (2 * P))), GROUND, 190, dir=-1, ph=t * 6, arm=-8)
    A.d['wash'].rectangle((60, GROUND - 160, 220, GROUND), fill=200)
    person(A, 120, GROUND, 120, dir=1, robe=True, hat='knot', female=True, bow=20, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('三战三走 · 鲍叔不以为怯', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('家有老母', 44), 860, 1020, t, t - u + P, rot=6)

def art_z_chaos(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='临淄', layer='mid', open_=1.0)
    flames(A, 540, 1060, 600, 200 * ease_out(u / P), t, n=7, seed=49, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('齐襄公被弑 · 国中无君', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('大乱', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_z_split_ways(A, cv, t, u):
    ground(A, GROUND)
    q = ease_out(u / (2.5 * P))
    guan(A, lerp(500, 140, q), GROUND, 180, dir=-1, ph=t * 4, arm=-8)
    person(A, lerp(460, 120, q) - 50, GROUND, 160, dir=-1, robe=True, hat='crown', ph=t * 4, arm=-8, layer='ink')
    person(A, lerp(580, 940, q), GROUND, 180, dir=1, robe=True, hat='knot', ph=t * 4, arm=-8, layer='yanhai')
    person(A, lerp(620, 990, q) + 50, GROUND, 160, dir=1, robe=True, hat='crown', ph=t * 4, arm=-8, layer='yanhai')
    A.flush(cv)
    stamp(cv, seal('奔鲁', 50, INK), 220, 1020, t, t - u + P, rot=-5)
    stamp(cv, seal('奔莒', 50), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('管仲辅公子纠 · 鲍叔辅公子小白', SERIF, 42, YANHAI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 一箭之仇
def art_z_race(A, cv, t, u):
    A.d['wash'].rounded_rectangle((110, 860, 970, 1320), radius=20, fill=170)
    q = clamp(u / (3.5 * P))
    A.d['ink'].line((200, 1240, lerp(200, 520, q), lerp(1240, 1000, q)), fill=255, width=6)
    A.d['yanhai'].line((900, 1240, lerp(900, 560, q), lerp(1240, 1000, q)), fill=255, width=6)
    A.d['daobi'].ellipse((500, 960, 580, 1040), fill=255)
    A.flush(cv)
    for nm, x, y, col in (('鲁', 200, 1290, INK), ('莒', 900, 1290, YANHAI), ('临淄', 540, 920, ZHU)):
        stamp(cv, seal(nm, 36, col), x, y, t, t - u + 0.3)
    paste(cv, text_img('谁先回到临淄 · 谁就是国君', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_daigou(cv, t, c, k):
    """8-beat custom scene: 一箭射钩 — Guan Zhong lies in wait on the road to Ju; the arrow strikes Xiaobai's belt hook,
    he falls back in the chariot; Guan rides away believing him dead; Xiaobai sits up and races to Linzi."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    for k2 in range(4):
        x = 140 + k2 * 260
        A.d['mid'].polygon([(x - 160, GROUND), (x, GROUND - 200), (x + 160, GROUND)], fill=140)
    cx = lerp(980, 640, ease_out(ph / 2)) if ph < 5 else lerp(640, -200, ease_out((ph - 5) / 2.5))
    carriage(A, cx, GROUND, 110, dir=-1, wheel=t * 8, ph=t * 10, moving=ph < 2.4 or ph >= 5, layer='yanhai')
    fall = clamp((ph - 2.6) / 0.3) * (1 - clamp((ph - 4.6) / 0.4))
    duke(A, cx + 10, GROUND - 90, 120, dir=-1, fall=70 * fall, arm=170 if ph >= 4.8 else -8, layer='ink')
    if ph < 3.6:
        guan(A, 200, GROUND, 200, dir=1, arm=90, bow=0)
        A.d['ink'].arc((230, GROUND - 260, 300, GROUND - 120), 270, 90, fill=255, width=6)
        if 2.0 <= ph < 2.6:
            q = (ph - 2.0) / 0.6
            arrow(A, lerp(300, cx - 20, q), GROUND - 160, 0.0, 90)
    else:
        rider(A, lerp(200, -200, ease_out((ph - 3.6) / 1.2)), GROUND, 120, dir=-1, ph=t * 8)
    if 2.6 <= ph < 5:
        A.d['daobi'].ellipse((cx - 14, GROUND - 160, cx + 14, GROUND - 132), fill=255)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '一箭射钩', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=49)
    fx.flush(cv)
    lab = '管仲伏兵莒道' if ph < 2 else ('一箭正中带钩' if ph < 3.6 else ('小白佯死 · 管仲以为得手' if ph < 5 else '小白昼夜兼程 先入临淄'))
    paste(cv, text_img(lab, SERIF, 46, ZHU if 2 <= ph < 3.6 else YANHAI, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('一枚铜带钩 · 救了一位霸主', SERIF, 40, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 3) / 0.4))

def art_z_huan(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='daobi')
    ground(A, GROUND)
    duke(A, 540, GROUND, 230, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    for i in range(4):
        person(A, 200 + i * 60 if i < 2 else 760 + (i - 2) * 60, GROUND, 150, dir=1 if i < 2 else -1, robe=True, hat='knot', kneel=True, bow=40, arm=90, layer='mid')
    A.flush(cv)
    stamp(cv, seal('齐桓公', 54), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('小白即位 · 誓杀管仲', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_cage(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(160, 800, ease_out(u / (3 * P)))
    cage_cart(A, x, GROUND, 160, t)
    guan(A, x, GROUND - 90, 120, dir=1, kneel=True, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('鲁杀公子纠 · 槛车送管仲回齐', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('槛车', 56, INK), 260, 1020, t, t - u + P, rot=-5)

def art_z_recommend(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    duke(A, 760, GROUND - 30, 220, dir=-1, arm=lerp(20, 140, 0.5 + 0.5 * math.sin(t * 2)))
    person(A, 380, GROUND, 210, dir=1, robe=True, hat='knot', kneel=True, bow=30, arm=lerp(60, 120, ease_out(u / 0.5)), layer='yanhai')
    A.flush(cv)
    type_in(cv, text_img('君将欲霸王 非管夷吾不可', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('鲍叔荐', 50), 860, 1020, t, t - u + P, rot=6)

def art_z_pardon(A, cv, t, u):
    """6-beat set piece: 释怨拜相 — the cage is opened outside the city; three baths and incense; he is seated as chancellor."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2.5:
        cage_cart(A, 540, GROUND, 180, t, moving=False)
        op = clamp((ph - 0.8) / 0.6)
        guan(A, lerp(540, 720, op), GROUND - 100 * (1 - op), 160 if op < 1 else 200, dir=1, kneel=op < 1, bow=20 * (1 - op), arm=-8)
    elif ph < 4:
        A.d['wash'].rectangle((400, GROUND - 60, 680, GROUND), fill=220)
        for k in range(3):
            q = (t * 0.6 + k / 3) % 1
            A.d['wash'].ellipse((440 + k * 80 - 20, GROUND - 60 - 200 * q - 20, 440 + k * 80 + 20, GROUND - 60 - 200 * q + 20), fill=int(160 * (1 - q)))
        guan(A, 540, GROUND - 40, 180, dir=1, kneel=True, bow=10, arm=60)
    else:
        palace(A, 540, 1140, 560, layer='daobi')
        duke(A, 760, GROUND - 30, 220, dir=-1, kneel=True, bow=20, arm=90)
        guan(A, 360, GROUND, 220, dir=1, arm=60)
    A.flush(cv)
    lab = '桓公亲迎于郊' if ph < 2.5 else ('三衅三浴' if ph < 4 else '拜为相 · 尊称仲父')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4 else YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('仲父', 56), 260, 1020, t, t - u + 4.2 * P, rot=-5)

# ================================================================ 第三回 富国强兵
def art_z_granary(A, cv, t, u):
    for i in range(4):
        x = 200 + i * 230
        A.d['daobi'].ellipse((x - 80, GROUND - 200, x + 80, GROUND), fill=220)
        A.d['ink'].polygon([(x - 100, GROUND - 170), (x + 100, GROUND - 170), (x, GROUND - 270)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('仓廪实而知礼节', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('衣食足而知荣辱', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 835, t, t - u + 1.5 * P, 0.5)

def art_z_salt(A, cv, t, u):
    """6-beat set piece: 官山海 — the state boils sea water into salt and casts iron tools; carts carry them inland; coins flow back."""
    ph = u / P
    A.d['yanhai'].rectangle((60, 1240, 420, GROUND + 40), fill=150)
    waves(A, 1250, t, rows=2, amp=4)
    salt_pot(A, 300, 1240, 90, t)
    salt_pot(A, 560, GROUND, 70, t)
    for j in range(3):
        x = lerp(560, 1100, ((t * 0.15 + j / 3) % 1))
        carriage(A, x, GROUND, 60, dir=1, wheel=t * 6, ph=t * 8 + j, layer='ink', canopy=False)
    n = int(clamp((ph - 2) / 3) * 12)
    for i in range(n):
        knife_coin(A, 640 + (i % 6) * 50, 1000 + (i // 6) * 40, 70, ang=-0.3)
    A.flush(cv)
    lab = '煮海为盐' if ph < 2 else ('冶铁铸器 · 官府专营' if ph < 4 else '不加赋而国用足')
    paste(cv, text_img(lab, SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('官山海', 50), 860, 1440, t, t - u + 0.4, rot=6)

def art_z_four(A, cv, t, u):
    ground(A, GROUND)
    roles = [('士', 'knot', False, 'ink'), ('农', 'knot', True, 'grass'), ('工', 'knot', True, 'daobi'), ('商', 'knot', False, 'yanhai')]
    for i, (nm, hat, load, lay) in enumerate(roles):
        if u > i * 0.6 * P:
            person(A, 210 + i * 220, GROUND, 170, dir=1, robe=not load, hat=hat, load=load, arm=40 if not load else 160, layer=lay)
    A.flush(cv)
    for i, (nm, *_rest) in enumerate(roles):
        stamp(cv, seal(nm, 40, ZHU if i % 2 else INK), 210 + i * 220, 1020, t, t - u + i * 0.6 * P)
    paste(cv, text_img('四民分业 · 各安其居', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_army(A, cv, t, u):
    ground(A, GROUND)
    for r in range(3):
        for i in range(5):
            person(A, 200 + i * 150 + r * 30, GROUND - r * 60, 100, dir=1, robe=r > 0, hat='helmet' if r == 0 else 'knot', spear=r == 0, load=r == 2, arm=40, layer=['ink', 'mid', 'grass'][r])
    A.flush(cv)
    paste(cv, text_img('寄军令于内政 · 兵农合一', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('作内政', 50), 860, 1020, t, t - u + P, rot=6)

def art_z_ke(A, cv, t, u):
    for k in range(3):
        A.d['mid'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    duke(A, 480, GROUND - 180, 180, dir=1, arm=lerp(-8, 60, ease_out((u - 1.5 * P) / 0.4)))
    person(A, 640, GROUND - 180, 180, dir=-1, robe=False, hat='knot', arm=120, layer='ink')
    A.d['ink'].line((560, GROUND - 300, 610, GROUND - 260), fill=255, width=6)
    A.flush(cv)
    type_in(cv, text_img('曹沫劫盟 · 桓公许还鲁地', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('管仲劝之 守信 天下归心', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.8 * P, 0.5)
    stamp(cv, seal('柯之盟', 50), 260, 1020, t, t - u + P, rot=-5)

def art_z_nine(A, cv, t, u):
    """8-beat set piece: 九合诸侯 — a map of the central plains; nine meeting places light up one by one."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 760, 970, 1420), radius=24, fill=170)
    A.d['ocean'].line([(140, 1020), (420, 1060), (700, 1000), (960, 940)], fill=200, width=8)
    A.d['yanhai'].rectangle((760, 900, 960, 1160), fill=120)
    sites = [(820, 1040), (620, 1120), (520, 980), (420, 1200), (680, 1260), (300, 1120), (560, 1340), (240, 980), (420, 900)]
    n = min(9, int(clamp(ph / 7) * 9) + 1)
    for i in range(n):
        x, y = sites[i]
        r = 22 + (6 * math.sin(t * 5) if i == n - 1 else 0)
        A.d['daobi'].ellipse((x - r, y - r, x + r, y + r), fill=255)
        if i:
            A.d['ink'].line((sites[0][0], sites[0][1], x, y), fill=90, width=2)
    A.flush(cv)
    stamp(cv, seal('齐', 44, YANHAI), 880, 1100, t, t - u + 0.3)
    paste(cv, text_img(f'九合诸侯 · 第{cn_num(n)}会', SERIF, 48, ZHU if n == 9 else YANHAI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('一匡天下 · 不以兵车', SERIF, 42, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 6.5) / 0.4))

# ================================================================ 第四回 尊王攘夷
def art_z_shanrong(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 340), (x + 150, GROUND)], fill=200)
    ground(A, GROUND)
    for j in range(4):
        rider(A, lerp(-200, 300, ease_out(u / (2 * P))) + j * 130, GROUND, 120, dir=1, ph=t * 8 + j, layer='yanhai', spear=True)
    A.flush(cv)
    paste(cv, text_img('山戎伐燕 · 齐军北上救燕', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('攘夷', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_oldhorse(A, cv, t, u):
    for k in range(60):
        q = (t * 0.5 + k / 60) % 1
        A.d['wash'].ellipse((80 + (k * 19) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 19) % 920 + 4, lerp(620, 1420, q) + 4), fill=230)
    ground(A, GROUND)
    x = lerp(160, 700, ease_out(u / (3 * P)))
    horse(A, x, GROUND, 160, dir=1, ph=t * 3, head_down=0.4)
    army(A, x - 200, GROUND, 4, dir=1, layer='mid', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('归途迷路 · 放老马而随之', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '老马识途出自韩非子', t, t - u + P)

def art_z_xingwei(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='邢', layer='mid', open_=1.0)
    ground(A, GROUND)
    for j in range(6):
        person(A, lerp(-100, 300, ease_out(u / (2 * P))) + j * 70, GROUND, 110, dir=1, robe=False, hat='knot', load=True, ph=t * 6 + j, arm=160, layer='ink')
    A.flush(cv)
    paste(cv, text_img('为邢筑城 · 为卫复国', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('存亡继绝', 44), 860, 1020, t, t - u + P, rot=6)

def art_z_zhaoling(A, cv, t, u):
    tent(A, 200, GROUND, 220, 180, layer='yanhai')
    tent(A, 880, GROUND, 220, 180, layer='mid')
    ground(A, GROUND)
    guan(A, 420, GROUND, 200, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)))
    person(A, 660, GROUND, 200, dir=-1, robe=True, hat='knot', arm=40, layer='ink')
    for k in range(3):
        A.d['grass'].line((520 + k * 20, GROUND, 530 + k * 20, GROUND - 80), fill=255, width=4)
    A.flush(cv)
    type_in(cv, text_img('尔贡包茅不入 王祭不共', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('召陵', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_kuiqiu(A, cv, t, u):
    for k in range(3):
        A.d['daobi'].rectangle((240 + k * 70, GROUND - 60 - k * 60, 840 - k * 70, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    duke(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 80, ease_out(u / 0.6)))
    for i in range(6):
        person(A, 100 + i * 60 if i < 3 else 800 + (i - 3) * 60, GROUND, 140, dir=1 if i < 3 else -1, robe=True, hat='crown', bow=30, arm=90, layer='mid')
    A.flush(cv)
    paste(cv, text_img('诸侯毕至 · 霸业之巅', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('葵丘', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_bow(A, cv, t, u):
    ground(A, GROUND)
    duke(A, 560, GROUND, 210, dir=1, kneel=u > 2 * P, bow=40 if u > 2 * P else 0, arm=90)
    guan(A, 330, GROUND, 200, dir=1, arm=lerp(-8, 100, ease_out((u - P) / 0.4)))
    person(A, 860, GROUND, 190, dir=-1, robe=True, hat='knot', arm=110, layer='mid')
    A.d['daobi'].rectangle((760, GROUND - 160, 820, GROUND - 130), fill=255)
    A.flush(cv)
    paste(cv, text_img('周天子赐胙 · 管仲劝桓公下拜', SERIF, 44, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('尊王', 56), 260, 1020, t, t - u + P, rot=-5)

def art_z_lastwords(A, cv, t, u):
    """6-beat set piece: 病榻遗言 — on his sickbed he names the three men the duke must never trust."""
    ph = u / P
    A.d['mid'].rectangle((200, 1200, 640, 1260), fill=230)
    A.d['ink'].rectangle((180, 1260, 660, 1290), fill=255)
    guan(A, 420, 1200, 200, dir=1, fall=-82, arm=lerp(-8, 50, clamp((ph - 0.5) / 0.4)), old=1.0)
    duke(A, 780, GROUND, 210, dir=-1, kneel=True, bow=20, arm=60)
    lamp(A, 940, GROUND, 60, t, glow=0.8)
    ground(A, GROUND)
    A.flush(cv)
    names = [('易牙', '烹子以媚君'), ('竖刁', '自宫以近君'), ('开方', '弃亲以事君')]
    k = min(2, int(ph / 1.8))
    paste(cv, text_img(f'{names[k][0]} · {names[k][1]}', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp((ph - k * 1.8) / 0.3))
    paste(cv, text_img('非人情 不可近', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 835, 1, clamp((ph - 0.6) / 0.4))

# ================================================================ 第五回 春秋一相
def art_z_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    guan(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('相齐四十年', SERIF, 48, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('卒', 60, INK), 260, 1020, t, t - u + P, rot=-5)

def art_z_huandies(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    A.d['ink'].rectangle((320, 900, 760, GROUND), outline=255, width=8)
    for k in range(9):
        A.d['ink'].line((320 + k * 55, 900, 320 + k * 55, GROUND), fill=200, width=4)
    duke(A, 540, GROUND, 190, dir=1, kneel=True, bow=lerp(10, 60, ease_out(u / (3 * P))), arm=-8)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('仍用三人 · 病中被困 饿死宫中', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('尸虫出于户', 38, INK), 860, 1020, t, t - u + P, rot=6)

def art_z_confucius(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 230, dir=1, robe=True, hat='knot', arm=lerp(-8, 70, ease_out(u / 0.6)), layer='ink')
    for i in range(3):
        sitter(A, 180 + i * 90, GROUND, 120, dir=1, bow=20, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('微管仲 吾其被发左衽矣', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('孔子', 54), 860, 1020, t, t - u + P, rot=6)

def art_z_book(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='yanhai')
    for i in range(int(clamp(u / P) * 6) + 1):
        bundle(A, 400 + i * 56, GROUND - 74, 44, layer='daobi')
    A.flush(cv)
    ink_in(cv, text_img('管子', SERIF, 56, YANHAI, 'Black', bleed=False, spacing=12), W / 2, 830, t, t - u + 0.3, dur=0.3)
    note_in(cv, '多为战国时人托名而作', t, t - u + P)

def art_z_kongming(A, cv, t, u):
    for k in range(3):
        A.d['pine'].polygon([(160 + k * 60, GROUND), (190 + k * 60, GROUND - 240), (220 + k * 60, GROUND)], fill=220)
    A.d['mid'].rectangle((620, GROUND - 200, 900, GROUND), fill=230)
    A.d['ink'].polygon([(600, GROUND - 200), (920, GROUND - 200), (760, GROUND - 290)], fill=255)
    person(A, 480, GROUND, 200, dir=1, robe=True, hat='knot', arm=lerp(-8, 90, ease_out(u / 0.6)), layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('每自比于管仲乐毅', SERIF, 46, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('诸葛亮', 50), 260, 1020, t, t - u + P, rot=-5)

def art_z_guanbao(A, cv, t, u):
    ground(A, GROUND)
    guan(A, 440, GROUND, 220, dir=1, arm=60, old=0.8)
    person(A, 640, GROUND, 220, dir=-1, robe=True, hat='knot', arm=60, layer='yanhai')
    A.flush(cv)
    type_in(cv, text_img('生我者父母 知我者鲍子也', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)

def art_z_kuang(A, cv, t, u):
    q = ease_out(u / P)
    for i in range(9):
        a = math.radians(-90 + i * 40)
        knife_coin(A, 540 + 250 * q * math.cos(a), 1080 + 160 * q * math.sin(a), 110, ang=a)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('民到于今受其赐', SERIF, 48, YANHAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    for i in range(3):
        knife_coin(A, 780 + i * 40, 1360 - i * 20, 120, ang=-0.2)

def art_z_title(A, cv, t, u):
    for i in range(5):
        knife_coin(A, 700, 1440 - i * 40, 260, ang=-0.1)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    guan(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '管鲍之交'), 48: ('第二回', '一箭之仇'), 80: ('第三回', '富国强兵'),
            112: ('第四回', '尊王攘夷'), 144: ('第五回', '春秋一相')}

CARDS = [
    C(0, 2, 'war', 'num', num='一箭', line='射中了国君', art=art_z_hook_arrow),
    C(2, 4, 'empire', 'num', num='九合诸侯', line='一匡天下', art=art_z_hook_nine),
    C(4, 6, 'death', 'num', num='三个小人', line='饿死了霸主', art=art_z_hook_three),
    C(6, 8, 'works', 'num', num='连孔子', line='都服他', art=art_z_hook_kongzi),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 管鲍之交
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-723, main='生于颍上', sub='没落贵族', note='生年约在前七二三年', art=art_z_birth),
    C(22, 26, 'works', 'card', year=-705, main='结识鲍叔', sub='一生知己', art=art_z_friend),
    C(26, 32, 'life', 'card', year=-700, main='管鲍分金', sub='一起做生意', art=art_z_split),
    C(32, 36, 'fate', 'card', year=-695, main='三仕三逐', sub='屡屡碰壁', art=art_z_fired),
    C(36, 40, 'night', 'card', year=-690, main='三战三走', sub='不是怕死', art=art_z_retreat),
    C(40, 44, 'death', 'card', year=-686, main='齐国大乱', sub='襄公被弑', art=art_z_chaos),
    C(44, 48, 'fate', 'card', year=-686, main='各为其主', sub='兄弟分道', art=art_z_split_ways),
    # ---- 第二回 一箭之仇
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'court', 'card', year=-685, main='争夺君位', sub='谁先到临淄', art=art_z_race),
    C(54, 62, 'war', 'daigou', year=-685),
    C(62, 66, 'empire', 'card', year=-685, main='小白即位', sub='齐桓公', art=art_z_huan),
    C(66, 70, 'fate', 'card', year=-685, main='槛车回齐', sub='生死难料', art=art_z_cage),
    C(70, 74, 'court', 'card', year=-685, main='鲍叔力荐', sub='让贤', art=art_z_recommend),
    C(74, 80, 'empire', 'card', year=-685, main='释怨拜相', sub='一箭之仇一笔勾销', art=art_z_pardon),
    # ---- 第三回 富国强兵
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'life', 'card', year=-684, main='仓廪实', sub='管子名言', art=art_z_granary),
    C(86, 92, 'works', 'card', year=-684, main='官山海', sub='盐铁专营', art=art_z_salt),
    C(92, 96, 'court', 'card', year=-684, main='四民分业', sub='士农工商', art=art_z_four),
    C(96, 100, 'war', 'card', year=-682, main='兵农合一', sub='平时为民 战时为兵', art=art_z_army),
    C(100, 104, 'court', 'card', year=-681, main='柯之盟', sub='信义立威', art=art_z_ke),
    C(104, 112, 'empire', 'card', year=-679, main='九合诸侯', sub='齐国始霸', art=art_z_nine),
    # ---- 第四回 尊王攘夷
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'war', 'card', year=-663, main='北伐山戎', sub='救燕', art=art_z_shanrong),
    C(118, 122, 'fate', 'card', year=-663, main='老马识途', sub='迷途知返', art=art_z_oldhorse),
    C(122, 126, 'works', 'card', year=-660, main='存邢救卫', sub='扶危济困', art=art_z_xingwei),
    C(126, 130, 'war', 'card', year=-656, main='召陵之盟', sub='问罪于楚', art=art_z_zhaoling),
    C(130, 134, 'empire', 'card', year=-651, main='葵丘之会', sub='霸业之巅', art=art_z_kuiqiu),
    C(134, 138, 'court', 'card', year=-651, main='天子赐胙', sub='尊王之礼', art=art_z_bow),
    C(138, 144, 'night', 'card', year=-645, main='病榻遗言', sub='三个不能用的人', art=art_z_lastwords),
    # ---- 第五回 春秋一相
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=-645, main='管仲去世', sub='春秋第一相', art=art_z_death),
    C(150, 154, 'night', 'card', year=-643, main='桓公之死', sub='不听仲父言', art=art_z_huandies),
    C(154, 158, 'works', 'card', year=-500, main='孔子评说', sub='如其仁', art=art_z_confucius),
    C(158, 162, 'court', 'card', year=-300, main='管子', sub='托名之书', art=art_z_book),
    C(162, 166, 'life', 'card', year=207, main='自比管乐', sub='卧龙的偶像', art=art_z_kongming),
    C(166, 168, 'empire', 'card', year=207, main='知我者', sub='鲍子也', art=art_z_guanbao),
    C(168, 170, 'end', 'card', year=207, main='一匡天下', sub='后世受其赐', art=art_z_kuang),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='肆拾玖', col=YANHAI, acc=DAOBI, born=-723, died=-645, age0=-723,
    born_lab='约前723年', died_lab='前645年', years_txt='约公元前723 — 前645',
    hook_q='他射过国君一箭 · 为什么反被拜为相？',
    name_line='管仲 · 名夷吾', name='管仲', seal='仲父', title_art=art_z_title,
    q1='春秋第一相？', q2='器量太小？',
    end_art=art_z_legacy, end_big='九合诸侯', end_seal='仲父',
    end_l1='他射过国君一箭', end_l2='国君还给他一个天下',
    end_brush='衣食足而知荣辱', end_ask='你身边有鲍叔牙这样的朋友吗？评论区聊聊', next='孟子'),
    scenes=dict(chapter=scene_chapter, daigou=scene_daigou))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
