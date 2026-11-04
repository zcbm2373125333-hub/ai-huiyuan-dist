"""千古人物志 · 第伍拾贰集 · 李斯 (约前284–前208)
Look: 廊柱灰蓝 + 篆红, 秦砖 corner borders, a 粮仓 chapter card: grain fills the granary (0→1/4→1/2→full) and in the
last chapter the granary is empty with a yellow dog sitting outside.
Set pieces: 6-beat 厕鼠仓鼠, custom 8-beat scene 'zhuke' (谏逐客书), 8-beat 六王毕, 6-beat 郡县制, 6-beat 书同文,
6-beat 沙丘之谋, 6-beat 黄犬之叹.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zhuangzi as Zz        # engine + helpers (previous episode)
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
from render_quyuan import river
from render_sunwu import army
from render_songtaizu import tent

F.RIPPLE = False
LANG = (78, 84, 108)                # 廊柱灰蓝
ZHUANHONG = (170, 40, 46)           # 篆红
S.LAYERS.append(('lang', LANG, 0.9, 1.0))
S.LAYERS.append(('zhuanhong', ZHUANHONG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='斯', life='楚', court='秦', night='夜', war='并', empire='秦', works='文', fate='犬', death='斩', end='斯')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZHUANHONG, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (LANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (ZHUANHONG, 180, (W * 0.5, 720))
G.base_bg.cache_clear()

ROAD = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(ROAD)
_d.polygon([(60, 1500), (W - 60, 1500), (W - 60, 1470), (60, 1478)], fill=(150, 130, 100, 40))   # 驰道
for _x in range(100, W - 60, 110):          # pines along the imperial road
    _d.polygon([(_x - 18, 1468), (_x + 18, 1468), (_x, 1410)], fill=(60, 80, 64, 60))
for _x0 in (70, 860):                       # far 咸阳 palace walls
    _d.rectangle((_x0, 1360, _x0 + 150, 1400), fill=LANG + (40,))
    _d.polygon([(_x0 - 10, 1360), (_x0 + 160, 1360), (_x0 + 75, 1330)], fill=LANG + (50,))
MTN_COL = {'night': (32, 34, 46), 'death': (64, 56, 58), 'war': (110, 56, 50), 'fate': (92, 92, 104)}
def draw_background(t, theme):
    """关中: far 咸阳 walls and the pine-lined imperial road at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 184, 186), (150, 150, 160), MTN_COL.get(theme, (106, 108, 124))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(ROAD)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """秦砖: staggered bricks stacked into each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=LANG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=LANG + (220,), width=3)
        for r in range(3):
            for c in range(3 - r):
                bx = x + sx * (14 + c * 34 + (r % 2) * 16); by = y + sy * (14 + r * 18)
                d.rectangle((min(bx, bx + sx * 30), min(by, by + sy * 14), max(bx, bx + sx * 30), max(by, by + sy * 14)),
                            fill=(ZHUANHONG if (r + c) % 2 else LANG) + (200,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def li(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """李斯: Qin minister — tall 长冠 tilted back, thin moustache, a jade tablet (笏) and a red sash."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.polygon([(x - 0.05 * h, y - 0.95 * h), (x + 0.05 * h, y - 0.95 * h), (x - dir * 0.02 * h, y - 1.18 * h), (x - dir * 0.1 * h, y - 1.16 * h)], fill=255)
        d.line((x + dir * 0.05 * h, y - 0.8 * h, x + dir * 0.1 * h, y - 0.79 * h), fill=255, width=max(2, int(0.01 * h)))
        A.d['zhuanhong'].rectangle((x - 0.08 * h, y - 0.58 * h, x + 0.08 * h, y - 0.53 * h), fill=255)
        if old > 0.4:
            A.d['wash'].line((x + dir * 0.05 * h, y - 0.82 * h, x + dir * 0.09 * h, y - 0.72 * h), fill=255, width=max(2, int(0.012 * h)))
    return hand

def emperor(A, x, y, h, dir=-1, layer='ink', **kw):
    hand = person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        A.d['ink'].rectangle((x - 0.14 * h, y - 1.06 * h, x + 0.14 * h, y - 1.02 * h), fill=255)
        for k in range(5):
            A.d['zhuanhong'].line((x - 0.12 * h + k * 0.06 * h, y - 1.02 * h, x - 0.12 * h + k * 0.06 * h, y - 0.95 * h), fill=255, width=2)
    return hand

def eunuch(A, x, y, h, dir=1, layer='mid', **kw):
    return person(A, x, y, h, dir=dir, robe=True, hat='knot', layer=layer, **kw)

def rat(A, x, y, s, fat=1.0, layer='ink', t=0.0):
    A.d[layer].ellipse((x - s * fat, y - 0.6 * s * fat, x + s * fat, y + 0.2 * s), fill=255)
    A.d[layer].ellipse((x + 0.8 * s * fat - 0.3 * s, y - 0.5 * s, x + 0.8 * s * fat + 0.3 * s, y), fill=255)
    A.d[layer].line((x - s * fat, y - 0.1 * s, x - 1.9 * s * fat, y - 0.3 * s + 0.2 * s * math.sin(t * 6)), fill=255, width=max(2, int(0.12 * s)))

def dog(A, x, y, s, dir=1, layer='diehuang', ph=None):
    A.d[layer].ellipse((x - 0.6 * s, y - 0.75 * s, x + 0.6 * s, y - 0.35 * s), fill=255)
    hx = x + dir * 0.6 * s
    A.d[layer].ellipse((hx - 0.22 * s, y - 1.0 * s, hx + 0.22 * s, y - 0.65 * s), fill=255)
    A.d[layer].polygon([(hx + dir * 0.1 * s, y - 0.95 * s), (hx + dir * 0.45 * s, y - 0.82 * s), (hx + dir * 0.12 * s, y - 0.75 * s)], fill=255)
    A.d[layer].polygon([(hx - dir * 0.05 * s, y - 0.95 * s), (hx - dir * 0.2 * s, y - 1.18 * s), (hx + dir * 0.02 * s, y - 1.0 * s)], fill=255)
    sw = 0.0 if ph is None else math.sin(ph)
    for k, lx in enumerate((-0.45, -0.25, 0.25, 0.45)):
        A.d[layer].line((x + lx * s, y - 0.45 * s, x + lx * s + sw * 0.15 * s * (1 if k % 2 else -1), y), fill=255, width=max(3, int(0.1 * s)))
    A.d[layer].line((x - dir * 0.6 * s, y - 0.65 * s, x - dir * 0.85 * s, y - 0.95 * s), fill=255, width=max(3, int(0.08 * s)))

def granary(A, cx, base, w, fill, empty=False):
    A.d['mid'].rectangle((cx - w / 2, base - 0.9 * w, cx + w / 2, base), fill=150)
    A.d['ink'].rectangle((cx - w / 2, base - 0.9 * w, cx + w / 2, base), outline=255, width=6)
    A.d['ink'].polygon([(cx - w / 2 - 40, base - 0.9 * w), (cx + w / 2 + 40, base - 0.9 * w), (cx, base - 1.25 * w)], fill=255)
    if not empty and fill > 0:
        A.d['yellow'].rectangle((cx - w / 2 + 8, base - 8 - (0.9 * w - 16) * fill, cx + w / 2 - 8, base - 8), fill=230)

def tablet(A, cx, base, w, h, layer='lang'):
    A.d[layer].rectangle((cx - w / 2, base - h, cx + w / 2, base), fill=230)
    A.d['ink'].rectangle((cx - w / 2, base - h, cx + w / 2, base), outline=255, width=5)

# ================================================================ chapter card
CH = {16: (0.0, 0), 48: (0.25, 0), 80: (0.5, 0), 112: (1.0, 0), 144: (1.0, 1)}
def art_granary_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g, empty = CH.get(kb, (0.25, 0))
    prev = {16: 0.0, 48: 0.0, 80: 0.25, 112: 0.5, 144: 1.0}.get(kb, 0.0)
    q = ease_out(u / (1.2 * P))
    if empty:
        granary(A, 540, 1200, 360, lerp(1.0, 0.0, q))
        dog(A, 820, 1200, 90, dir=-1)
    else:
        granary(A, 540, 1200, 360, lerp(prev, g, q))
        rat(A, 540, 1200 - 8 - 324 * lerp(prev, g, q) - 10, 26, fat=lerp(0.8, 1.4, lerp(prev, g, q)), t=t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_granary_chapter)
    ink_in(cv, text_img(no, SERIF, 56, LANG, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_s_hook_rat(A, cv, t, u):
    ground(A, GROUND)
    granary(A, 700, GROUND, 260, 0.8)
    rat(A, lerp(200, 640, ease_out(u / (1.6 * P))), GROUND - 10, 30, t=t)

def art_s_hook_memo(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1080, 520, 200, clamp(u / P), layer='wash')

def art_s_hook_script(A, cv, t, u):
    ground(A, GROUND)
    n = min(6, int(u / (0.25 * P)) + 1)
    for i in range(n):
        a = math.radians(-150 + i * 24)
        r = lerp(360, 0, ease_out((u - 1.2 * P) / (0.6 * P)))
        tablet(A, 540 + r * math.cos(a), 1200 + 0.4 * r * math.sin(a), 90, 120, layer='lang' if i % 2 else 'mid')

def art_s_hook_dog(A, cv, t, u):
    ground(A, GROUND)
    dog(A, lerp(200, 700, ease_out(u / (1.6 * P))), GROUND, 110, dir=1, ph=t * 10)

# ================================================================ 第一回 仓中之鼠
def art_s_birth(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='上蔡', layer='mid', open_=1.0)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('楚国上蔡 · 布衣之家', SERIF, 46, LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('楚', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_clerk(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='lang')
    li(A, 300, GROUND, 190, dir=1, kneel=True, bow=20, arm=90)
    slips(A, 440, GROUND - 74, int(clamp(u / (2 * P)) * 10) + 1, 80, layer='mid')
    A.flush(cv)
    paste(cv, text_img('为郡小吏 · 掌管文书', SERIF, 46, LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_rats(A, cv, t, u):
    """6-beat set piece: 厕鼠仓鼠 — a thin rat in the privy flees at every footstep; a fat rat in the granary eats in peace."""
    ph = u / P
    ground(A, GROUND)
    A.d['mid'].rectangle((140, GROUND - 160, 420, GROUND), fill=170)
    A.d['ink'].rectangle((140, GROUND - 160, 420, GROUND), outline=255, width=5)
    granary(A, 760, GROUND, 300, 0.8)
    rx = 280 + (120 * math.sin(t * 5) if ph > 1 else 0)
    rat(A, rx, GROUND - 10, 20, fat=0.7, t=t)
    if ph > 2.5:
        rat(A, 760, GROUND - 8 - 270 * 0.8 - 12, 32, fat=1.5, t=t * 0.3, layer='ink')
    if 1 < ph < 2.5:
        person(A, lerp(-60, 200, (ph - 1) / 1.5), GROUND, 150, dir=1, robe=False, hat='knot', ph=t * 4, arm=-8, layer='mid')
    li(A, 540, GROUND, 180, dir=1 if ph > 2.5 else -1, arm=lerp(-8, 70, clamp((ph - 4) / 0.4)))
    A.flush(cv)
    lab = '厕中鼠 食不洁 近人犬 数惊恐之' if ph < 2.5 else ('仓中鼠 食积粟 居大庑之下 不见人犬之忧' if ph < 4 else '人之贤不肖譬如鼠矣 在所自处耳')
    paste(cv, text_img(lab, SERIF, 40 if ph < 4 else 44, ZHU if ph >= 4 else LANG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, 1)

def art_s_xunzi(A, cv, t, u):
    for k in range(3):
        A.d['pine'].polygon([(160 + k * 60, GROUND), (190 + k * 60, GROUND - 240), (220 + k * 60, GROUND)], fill=200)
    ground(A, GROUND)
    person(A, 760, GROUND, 220, dir=-1, robe=True, hat='knot', arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    li(A, 480, GROUND, 170, dir=1, kneel=True, bow=25, arm=90)
    A.flush(cv)
    paste(cv, text_img('从荀卿学帝王之术', SERIF, 46, LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('荀子', 54), 260, 1020, t, t - u + P, rot=-5)

def art_s_hanfei(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='mid')
    li(A, 300, GROUND, 180, dir=1, kneel=True, bow=10, arm=40)
    person(A, 780, GROUND, 180, dir=-1, robe=True, hat='knot', kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='lang')
    n = int(clamp(u / (2 * P)) * 8) + 1
    slips(A, 600, GROUND - 74, n, 90, layer='zhuanhong')
    A.flush(cv)
    paste(cv, text_img('同窗韩非 · 斯自以为不如非', SERIF, 44, LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_farewell(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=180)
    ground(A, GROUND)
    person(A, 220, GROUND, 200, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    li(A, lerp(400, 820, ease_out(u / (3 * P))), GROUND, 190, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    type_in(cv, text_img('诟莫大于卑贱 而悲莫甚于穷困', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)

def art_s_qin(A, cv, t, u):
    city_wall(A, 360, 1000, 1080, gate_x=680, label='咸阳', layer='lang', open_=1.0)
    ground(A, GROUND)
    li(A, lerp(-60, 300, ease_out(u / (2.5 * P))), GROUND, 190, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('西入秦 · 为吕不韦舍人', SERIF, 46, LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('入秦', 56), 260, 1020, t, t - u + P, rot=-5)

# ================================================================ 第二回 谏逐客书
def art_s_persuade(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='lang')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 220, dir=-1, arm=lerp(20, 90, ease_out((u - P) / 0.5)))
    li(A, 360, GROUND, 210, dir=1, kneel=True, bow=20, arm=lerp(60, 130, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    type_in(cv, text_img('灭诸侯 成帝业 为天下一统', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('秦王政', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_s_spies(A, cv, t, u):
    A.d['wash'].rounded_rectangle((110, 860, 970, 1300), radius=20, fill=170)
    for i in range(6):
        x = 200 + (i % 3) * 300; y = 960 + (i // 3) * 200
        A.d['mid'].rectangle((x - 60, y - 40, x + 60, y + 40), fill=200)
        q = clamp((u - i * 0.4 * P) / (0.5 * P))
        A.d['gold'].ellipse((lerp(900, x, q) - 14, lerp(1260, y, q) - 14, lerp(900, x, q) + 14, lerp(1260, y, q) + 14), fill=255)
    A.flush(cv)
    paste(cv, text_img('阴遣谋士 赍持金玉以游说诸侯', SERIF, 42, LANG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('客卿', 56), 260, 1380, t, t - u + P, rot=-5)

def art_s_expel(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    emperor(A, 540, GROUND, 230, dir=1, arm=lerp(20, 160, ease_out((u - 0.5 * P) / 0.3)))
    for i in range(4):
        person(A, lerp(700, 1100, ease_out((u - P) / (2 * P))) + i * 70, GROUND, 150, dir=1, robe=True, hat='knot', ph=t * 4 + i, arm=-8, layer='lang')
    A.flush(cv)
    paste(cv, text_img('郑国渠事发 · 宗室请一切逐客', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('逐客令', 50, INK), 260, 1020, t, t - u + P, rot=-5)

ZHUKE = ['泰山不让土壤 故能成其大', '河海不择细流 故能就其深', '王者不却众庶 故能明其德']
def scene_zhuke(cv, t, c, k):
    """8-beat custom scene: 谏逐客书 — on the road out of Qin he writes the memorial on his knee; the lines rise one by one;
    a rider gallops after him; he turns back toward the capital."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    for k2 in range(5):
        x = 140 + k2 * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 280), (x + 150, GROUND)], fill=150)
    ground(A, GROUND)
    if ph < 5.2:
        li(A, lerp(540, 760, clamp(ph / 1.5)) if ph < 1.5 else 760, GROUND, 190, dir=1, kneel=1.5 <= ph, bow=20 if ph >= 1.5 else 0, ph=t * 3 if ph < 1.5 else None, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 4)))
        if ph >= 4:
            rider(A, lerp(-200, 560, ease_out((ph - 4) / 1.2)), GROUND, 120, dir=1, ph=t * 10)
    else:
        li(A, lerp(760, 300, ease_out((ph - 5.2) / 2.5)), GROUND, 190, dir=-1, ph=t * 4, arm=-8)
        rider(A, lerp(560, 140, ease_out((ph - 5.2) / 2.5)), GROUND, 120, dir=-1, ph=t * 8)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '谏逐客书', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=52)
    fx.flush(cv)
    n = min(3, max(0, int((ph - 1.2) / 0.9) + 1)) if ph > 1.2 else 0
    for j in range(n):
        paste(cv, text_img(ZHUKE[j], SERIF, 40, ZHU if j == n - 1 else INK, 'Black', bleed=False, spacing=2), W / 2, 580 + j * 60, 1, clamp((ph - 1.2 - j * 0.9) / 0.3))
    lab = '李斯亦在逐中 · 道上上书' if ph < 4 else ('秦王追之' if ph < 5.2 else '乃除逐客之令 复李斯官')
    paste(cv, text_img(lab, SERIF, 44, LANG, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_s_canal(A, cv, t, u):
    A.d['grass'].rectangle((60, 1120, W - 60, GROUND), fill=140)
    q = ease_out(u / (3 * P))
    A.d['ocean'].line((60, 1200, 60 + (W - 120) * q, 1200), fill=230, width=22)
    for k in range(int(q * 8)):
        A.d['grass'].line((100 + k * 120, 1230, 110 + k * 120, 1160), fill=255, width=6)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('郑国渠成 · 关中为沃野', SERIF, 46, LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('郑国渠', 50), 860, 1020, t, t - u + P, rot=6)

def art_s_hanfei_dies(A, cv, t, u):
    A.d['ink'].rectangle((320, 900, 760, GROUND), outline=255, width=8)
    for k in range(9):
        A.d['ink'].line((320 + k * 55, 900, 320 + k * 55, GROUND), fill=200, width=4)
    person(A, 540, GROUND, 180, dir=1, robe=True, hat='knot', kneel=True, bow=lerp(10, 50, ease_out(u / (3 * P))), arm=60, layer='lang')
    A.d['ink'].ellipse((600, GROUND - 40, 640, GROUND), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('韩非使秦 · 李斯谗之 下狱遗药', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('同窗', 54, INK), 860, 1020, t, t - u + P, rot=6)

def art_s_tingwei(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='lang')
    ground(A, GROUND)
    li(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    stamp(cv, seal('廷尉', 60), 860, 1020, t, t - u + 0.5 * P, rot=6)

# ================================================================ 第三回 六王毕
SIX = ['韩', '赵', '魏', '楚', '燕', '齐']
YRS = [230, 228, 225, 223, 222, 221]
def art_s_six(A, cv, t, u):
    """8-beat set piece: 六王毕 — six state seals in a ring; one by one they are struck through, year by year, until one seal remains."""
    ph = u / P
    ground(A, GROUND)
    n = min(6, int(ph / 1.15) + 1)
    A.flush(cv)
    for i, nm in enumerate(SIX):
        a = math.radians(-90 + i * 60)
        x, y = 540 + 300 * math.cos(a), 1100 + 230 * math.sin(a)
        if i < n:
            q = clamp((ph - i * 1.15) / 0.4)
            stamp(cv, seal(nm, 60, DIM), x, y, t, t - u + i * 1.15 * P)
            d = ImageDraw.Draw(cv)
            d.line((x - 50 * q, y - 50 * q, x + 50 * q, y + 50 * q), fill=ZHUANHONG + (240,), width=8)
        else:
            stamp(cv, seal(nm, 60, INK), x, y, t, t - u)
    if ph > 7:
        stamp(cv, seal('秦', 96, ZHUANHONG), 540, 1100, t, t - u + 7 * P, rot=0)
    yr = YRS[n - 1]
    paste(cv, text_img(f'灭{SIX[n - 1]} · 公元前{cn_num(yr)}年', SERIF, 46, ZHUANHONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('十年之间 六国尽灭', SERIF, 42, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 6.6) / 0.4))

def art_s_title_huangdi(A, cv, t, u):
    for k in range(3):
        A.d['lang'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    emperor(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    for i in range(4):
        li(A, 140 + i * 60, GROUND, 140, dir=1, kneel=True, bow=40, arm=90) if i == 0 else person(A, 140 + i * 60, GROUND, 140, dir=1, robe=True, hat='knot', kneel=True, bow=40, arm=90, layer='mid')
    A.flush(cv)
    paste(cv, text_img('议帝号 · 德兼三皇 功过五帝', SERIF, 44, LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('始皇帝', 50), 860, 1020, t, t - u + P, rot=6)

def art_s_jun(A, cv, t, u):
    """6-beat set piece: 郡县制 — feudal fiefs dissolve; the map fills with thirty-six commanderies, the counter climbing."""
    ph = u / P
    A.d['wash'].rounded_rectangle((140, 820, 940, 1360), radius=20, fill=170)
    n = min(36, int(clamp((ph - 1) / 4) * 36))
    for i in range(36):
        x = 170 + (i % 9) * 86; y = 850 + (i // 9) * 124
        if i < n:
            A.d['lang'].rectangle((x, y, x + 76, y + 112), fill=200 if i % 2 else 150)
        elif ph < 1:
            A.d['mid'].ellipse((x + 10, y + 20, x + 66, y + 90), fill=150)
    A.flush(cv)
    lab = '廷尉李斯议 · 置诸侯不便' if ph < 1 else f'分天下以为{cn_num(max(1, n))}郡'
    paste(cv, text_img(lab, SERIF, 46, ZHU if n == 36 else LANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('郡置守 尉 监', SERIF, 42, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4) / 0.4))

def art_s_script(A, cv, t, u):
    """6-beat set piece: 书同文 — six differently scrawled glyph tiles slide together and become one square 小篆 tile."""
    ph = u / P
    ground(A, GROUND)
    q = ease_out(clamp((ph - 2) / 2))
    for i in range(6):
        a = math.radians(-150 + i * 24)
        x = 540 + 360 * (1 - q) * math.cos(a); y = 1160 + 220 * (1 - q) * math.sin(a)
        A.d['mid' if q < 1 else 'lang'].rectangle((x - 70, y - 70, x + 70, y + 70), fill=200)
        rnd = random.Random(i)
        for s in range(5):
            pts = [(x - 50 + rnd.random() * 100, y - 50 + rnd.random() * 100) for _ in range(3)]
            A.d['ink'].line(pts, fill=int(220 * (1 - q)) + 30, width=5)
    if q >= 1:
        for k2 in range(4):
            A.d['zhuanhong'].line((470 + k2 * 46, 1100, 470 + k2 * 46, 1220), fill=255, width=6)
        A.d['zhuanhong'].line((470, 1100, 610, 1100), fill=255, width=6)
        A.d['zhuanhong'].arc((470, 1160, 610, 1240), 0, 180, fill=255, width=6)
    A.flush(cv)
    lab = '六国文字 异形' if ph < 2 else ('罢其不与秦文合者' if ph < 4 else '李斯作仓颉篇 · 统一为小篆')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4 else LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    for i, nm in enumerate(SIX):
        stamp(cv, seal(nm, 30, DIM), 180 + i * 144, 1440, t, t - u + 0.2 + i * 0.15)

def art_s_road(A, cv, t, u):
    A.d['dune'].polygon([(480, 900), (600, 900), (980, GROUND), (100, GROUND)], fill=200)
    for k in range(6):
        q = (t * 0.3 + k / 6) % 1
        y = lerp(900, GROUND, q)
        A.d['ink'].line((lerp(500, 300, q), y, lerp(580, 780, q), y), fill=int(160 * q), width=3)
    carriage(A, lerp(540, 600, (t * 0.2) % 1), lerp(1000, 1200, (t * 0.2) % 1), lerp(30, 80, (t * 0.2) % 1), dir=1, wheel=t * 6, ph=t * 8, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('车同轨 · 修驰道', SERIF, 46, LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_taishan(A, cv, t, u):
    A.d['mid'].polygon([(200, GROUND), (540, 860), (880, GROUND)], fill=200)
    tablet(A, 540, GROUND, 100, 260, layer='lang')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('泰山刻石', 46), 860, 1020, t, t - u + 0.3 * P, rot=6)

# ================================================================ 第四回 沙丘
def art_s_chancellor(A, cv, t, u):
    for k in range(3):
        A.d['zhuanhong'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    li(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    stamp(cv, seal('丞相', 60), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('诸男皆尚秦公主 女悉嫁秦诸公子', SERIF, 42, LANG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_s_burn(A, cv, t, u):
    ground(A, GROUND)
    for i in range(6):
        bundle(A, 300 + i * 90, GROUND, 70, layer='mid')
    flames(A, 540, GROUND, 600, 260 * ease_out(u / (1.5 * P)), t, n=7, seed=213, smoke=True)
    A.flush(cv)
    paste(cv, text_img('丞相李斯奏请 · 以吏为师', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('焚书', 56, INK), 260, 1020, t, t - u + P, rot=-5)

def art_s_peak(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    for j in range(int(clamp(u / (2 * P)) * 8) + 1):
        carriage(A, 120 + j * 110, GROUND, 50, dir=1, moving=False, layer='lang' if j % 2 else 'ink')
    li(A, 820, GROUND, 200, dir=-1, arm=-8)
    A.flush(cv)
    type_in(cv, text_img('物极则衰 吾未知所税驾也', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.8 * P, 0.5)
    stamp(cv, seal('车骑以千数', 38, INK), 260, 1020, t, t - u + 0.4, rot=-5)

def art_s_shaqiu(A, cv, t, u):
    tent(A, 540, GROUND, 460, 300, layer='mid')
    ground(A, GROUND)
    emperor(A, 540, GROUND - 20, 200, dir=1, fall=-86, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    A.flush(cv)
    paste(cv, text_img('始皇崩于沙丘 · 秘不发丧', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('沙丘', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_s_plot(A, cv, t, u):
    """6-beat set piece: 沙丘之谋 — in the dark tent the eunuch whispers; Li Si wavers; the forged edict is sealed."""
    ph = u / P
    A.d['mid'].rectangle((140, 860, 940, GROUND), fill=50)
    ground(A, GROUND)
    lamp(A, 540, GROUND - 74, 40, t, glow=0.9)
    desk(A, 540, GROUND, 300, layer='mid')
    eunuch(A, 300, GROUND, 190, dir=1, bow=20, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    li(A, 780, GROUND, 200, dir=-1, bow=lerp(0, 30, clamp((ph - 2.5) / 1)), arm=lerp(-8, 80, clamp((ph - 3.6) / 0.4)))
    if ph > 3.6:
        scroll(A, 540, GROUND - 160, 200, 60, clamp((ph - 3.6) / 0.8), layer='wash')
    A.flush(cv)
    lab = '赵高 · 君侯自料能孰与蒙恬' if ph < 2.5 else ('斯乃仰天而叹 垂泪太息' if ph < 3.6 else '矫诏 立胡亥 赐死扶苏')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.6 else LANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph > 4.4:
        stamp(cv, seal('伪诏', 60), 540, 1100, t, t - u + 4.4 * P, rot=-4)

def art_s_fusu(A, cv, t, u):
    for k in range(4):
        A.d['mid'].rectangle((100 + k * 220, GROUND - 160 - (k % 2) * 40, 260 + k * 220, GROUND), fill=170)
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, robe=True, hat='knot', kneel=True, bow=lerp(10, 60, ease_out(u / (2 * P))), arm=120, layer='ink')
    A.flush(cv)
    paste(cv, text_img('上郡 · 扶苏自杀 蒙恬下狱', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_duze(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='lang')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 190, dir=-1, arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t * 2)))
    li(A, 380, GROUND, 200, dir=1, kneel=True, bow=40, arm=100, old=0.6)
    A.flush(cv)
    paste(cv, text_img('上书行督责之术 · 以求容', SERIF, 46, LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('秦二世', 50, INK), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第五回 黄犬之叹
def art_s_jail(A, cv, t, u):
    A.d['ink'].rectangle((320, 900, 760, GROUND), outline=255, width=8)
    for k in range(9):
        A.d['ink'].line((320 + k * 55, 900, 320 + k * 55, GROUND), fill=200, width=4)
    li(A, 540, GROUND, 190, dir=1, kneel=True, bow=30, arm=-8, old=0.8)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('赵高诬其谋反 · 榜掠千余', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_seven(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='mid')
    li(A, 300, GROUND, 180, dir=1, kneel=True, bow=20, arm=90, old=0.8)
    n = min(7, int(u / (0.5 * P)) + 1)
    slips(A, 440, GROUND - 74, n, 100, layer='lang')
    A.flush(cv)
    paste(cv, text_img(f'狱中上书 · 自陈罪七 第{cn_num(n)}', SERIF, 44, LANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('所谓七罪 实为七功', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, 1, clamp((u - 3 * P) / 0.4))

def art_s_dog(A, cv, t, u):
    """6-beat set piece: 黄犬之叹 — on the way to execution he turns to his son; the memory of Shangcai's east gate:
    a man and a boy run out with a yellow dog after hares; the memory fades."""
    ph = u / P
    ground(A, GROUND)
    if ph < 1.6 or ph > 4.8:
        li(A, 440, GROUND, 190, dir=1, arm=-8, old=1.0, bow=10)
        person(A, 620, GROUND, 170, dir=-1, robe=True, hat='knot', kneel=True, bow=30, arm=-8, layer='mid')
        for j in range(3):
            person(A, 200 - j * 60, GROUND, 160, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='lang')
    else:
        q = (ph - 1.6) / 3.2
        city_wall(A, 60, 380, 1080, gate_x=220, label='东门', layer='mid', open_=1.0)
        x = lerp(320, 980, q)
        person(A, x, GROUND, 170, dir=1, ph=t * 6, robe=True, hat='knot', arm=80, layer='ink')
        person(A, x - 90, GROUND, 110, dir=1, ph=t * 6, robe=True, hat='knot', arm=40, layer='ink')
        dog(A, x + 150, GROUND, 90, dir=1, ph=t * 12)
        A.d['wash'].ellipse((x + 300 - 20, GROUND - 40, x + 300 + 20, GROUND - 10), fill=255)
    A.flush(cv)
    type_in(cv, text_img('吾欲与若复牵黄犬 俱出上蔡东门逐狡兔', SERIF, 40, INK, 'Black', bleed=False, spacing=2), W / 2, 760, t, t - u + 0.8 * P, 0.6)
    type_in(cv, text_img('岂可得乎', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 840, t, t - u + 4.2 * P, 0.4)

def art_s_end(A, cv, t, u):
    ground(A, GROUND)
    for j in range(3):
        A.d['lang'].rectangle((300 + j * 180, GROUND - 160, 360 + j * 180, GROUND), fill=200)
    A.d['red'].ellipse((520, GROUND - 40, 560, GROUND), fill=int(200 * (1 - ease_out(u / (2 * P)))))
    A.flush(cv)
    paste(cv, text_img('具五刑 · 腰斩咸阳市 夷三族', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '史记 李斯列传', t, t - u + P)

def art_s_fall(A, cv, t, u):
    palace(A, 540, 1200, 480, collapse=ease_out(u / (2.5 * P)), layer='lang')
    flames(A, 540, 1140, 560, 200 * ease_out(u / P), t, n=7, seed=206, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('李斯死后两年 · 秦亡', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_zichu(A, cv, t, u):
    granary(A, 380, GROUND, 240, 0.0, empty=True)
    A.d['mid'].rectangle((620, GROUND - 160, 860, GROUND), fill=170)
    rat(A, lerp(380, 740, (t * 0.2) % 1), GROUND - 10, 22, t=t)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('仓与厕 · 终究在所自处', SERIF, 46, LANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    dog(A, 860, 1380, 80, dir=-1)

def art_s_title(A, cv, t, u):
    granary(A, 820, 1460, 280, 0.7)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    li(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '仓中之鼠'), 48: ('第二回', '谏逐客书'), 80: ('第三回', '六王毕'),
            112: ('第四回', '沙丘之谋'), 144: ('第五回', '黄犬之叹')}

CARDS = [
    C(0, 2, 'life', 'num', num='一只老鼠', line='改变了他的一生', art=art_s_hook_rat),
    C(2, 4, 'works', 'num', num='一篇奏章', line='留住天下人才', art=art_s_hook_memo),
    C(4, 6, 'empire', 'num', num='统一文字', line='写的是他的字', art=art_s_hook_script),
    C(6, 8, 'death', 'num', num='最后一句话', line='是一只黄狗', art=art_s_hook_dog),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 仓中之鼠
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-284, main='生于上蔡', sub='楚国布衣', note='生年约在前二八四年', art=art_s_birth),
    C(22, 26, 'works', 'card', year=-265, main='郡中小吏', sub='一个书记员', art=art_s_clerk),
    C(26, 32, 'fate', 'card', year=-262, main='厕鼠仓鼠', sub='他的人生哲学', art=art_s_rats),
    C(32, 36, 'works', 'card', year=-255, main='师从荀子', sub='学帝王之术', art=art_s_xunzi),
    C(36, 40, 'night', 'card', year=-252, main='同窗韩非', sub='既生瑜', art=art_s_hanfei),
    C(40, 44, 'fate', 'card', year=-248, main='辞别荀子', sub='不甘贫贱', art=art_s_farewell),
    C(44, 48, 'court', 'card', year=-247, main='西入秦国', sub='寻找粮仓', art=art_s_qin),
    # ---- 第二回 谏逐客书
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'empire', 'card', year=-246, main='说秦王', sub='一统之策', art=art_s_persuade),
    C(54, 58, 'works', 'card', year=-240, main='拜为客卿', sub='离间六国', art=art_s_spies),
    C(58, 62, 'death', 'card', year=-237, main='逐客令', sub='他也在被逐之列', art=art_s_expel),
    C(62, 70, 'fate', 'zhuke', year=-237),
    C(70, 74, 'works', 'card', year=-237, main='郑国渠', sub='万世之功', art=art_s_canal),
    C(74, 78, 'night', 'card', year=-233, main='韩非之死', sub='同窗相残', art=art_s_hanfei_dies),
    C(78, 80, 'court', 'card', year=-230, main='升任廷尉', sub='执掌刑狱', art=art_s_tingwei),
    # ---- 第三回 六王毕
    C(80, 82, 'war', 'chapter'),
    C(82, 90, 'war', 'card', year=-230, main='六王毕', sub='四海一', art=art_s_six),
    C(90, 94, 'empire', 'card', year=-221, main='议帝号', sub='始皇帝', art=art_s_title_huangdi),
    C(94, 100, 'court', 'card', year=-221, main='郡县制', sub='废分封', art=art_s_jun),
    C(100, 106, 'works', 'card', year=-221, main='书同文', sub='小篆', art=art_s_script),
    C(106, 110, 'empire', 'card', year=-220, main='车同轨', sub='驰道', art=art_s_road),
    C(110, 112, 'works', 'card', year=-219, main='泰山刻石', sub='李斯手书', art=art_s_taishan),
    # ---- 第四回 沙丘之谋
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'empire', 'card', year=-213, main='官至丞相', sub='位极人臣', art=art_s_chancellor),
    C(118, 122, 'death', 'card', year=-213, main='焚书', sub='以吏为师', art=art_s_burn),
    C(122, 126, 'night', 'card', year=-212, main='物极则衰', sub='他也害怕', art=art_s_peak),
    C(126, 130, 'death', 'card', year=-210, main='始皇驾崩', sub='沙丘', art=art_s_shaqiu),
    C(130, 136, 'night', 'card', year=-210, main='沙丘之谋', sub='一念之差', art=art_s_plot),
    C(136, 140, 'fate', 'card', year=-210, main='扶苏之死', sub='矫诏', art=art_s_fusu),
    C(140, 144, 'court', 'card', year=-209, main='督责书', sub='曲意逢迎', art=art_s_duze),
    # ---- 第五回 黄犬之叹
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'night', 'card', year=-208, main='下狱', sub='赵高的报复', art=art_s_jail),
    C(150, 154, 'works', 'card', year=-208, main='狱中上书', sub='七罪', art=art_s_seven),
    C(154, 160, 'fate', 'card', year=-208, main='黄犬之叹', sub='临刑之言', art=art_s_dog),
    C(160, 164, 'death', 'card', year=-208, main='身死族灭', sub='咸阳', art=art_s_end),
    C(164, 168, 'war', 'card', year=-206, main='二世而亡', sub='秦的终点', art=art_s_fall),
    C(168, 170, 'end', 'card', year=-206, main='在所自处', sub='老鼠哲学的结局', art=art_s_zichu),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='伍拾贰', col=LANG, acc=ZHUANHONG, born=-284, died=-208, age0=-284,
    born_lab='约前284年', died_lab='前208年', years_txt='约公元前284 — 前208',
    hook_q='他帮秦始皇统一天下 · 为什么落得腰斩？',
    name_line='李斯 · 楚国上蔡人', name='李斯', seal='丞相', title_art=art_s_title,
    q1='千古一相？', q2='一念成魔？',
    end_art=art_s_legacy, end_big='黄犬东门', end_seal='丞相',
    end_l1='他用一生 从厕所爬进了粮仓', end_l2='最后只想再牵一次黄狗',
    end_brush='泰山不让土壤', end_ask='李斯是能臣还是小人？评论区聊聊', next='蒙恬'),
    scenes=dict(chapter=scene_chapter, zhuke=scene_zhuke))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
