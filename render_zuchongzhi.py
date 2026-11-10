"""千古人物志 · 第玖拾捌集 · 祖冲之 (429–500)
Look: 星蓝 + 晷影金, little counting-rod corners, the river and roofs of 建康 behind.
Chapter card: 割圆 — a polygon inscribed in a circle; its sides double each chapter (6, 12, 24, 96 … ) until it is a circle.
Set pieces: custom 8-beat scene 'geyuan' (割圆术 算圆周率), 6-beat 驳议, 6-beat 指南车, 6-beat 千里船与水碓磨.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_diaochan as Dc        # engine + helpers (previous episode)
import render_long as L
import render_gufeng as G
import render_story as S
import render_full as F
import epkit
from render_gufeng import (W, H, FPS, bt, INK, ZHU, ZHE, BRUSH, SERIF, WILD, font, clamp, lerp, ease_out, ease_expo,
                           cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import (Art, person, horse, carriage, palace, flames, waves, boat, crow, arrow, flag, ground,
                          walk_x, ellipse_pts, GROUND)
from render_full import chars_in, type_in, beat_fx
from render_long import C, rider, city_wall, note_in, stage, DIM, P
from render_wangyangming import desk, scroll, lamp, sitter
from render_kongzi import slips, bundle
from render_simayi import emperor
from render_quyuan import river
from render_zhuxi import book

F.RIPPLE = False
XINGLAN = (54, 78, 120)             # 星蓝
GUIYING = (198, 154, 70)            # 晷影金
S.LAYERS.append(('xinglan', XINGLAN, 0.9, 1.0))
S.LAYERS.append(('guiying', GUIYING, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='圆', life='祖', court='历', night='星', war='驳', empire='率', works='算', fate='天', death='逝', end='圆')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZHU, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (GUIYING, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (XINGLAN, 170, (W * 0.5, 720))
G.THEMES['night']['sun'] = None
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
_rng = random.Random(98)
for _k in range(40):                # faint stars in the upper sky
    _x, _y = _rng.randint(80, 1000), _rng.randint(300, 760)
    _d.ellipse((_x - 2, _y - 2, _x + 2, _y + 2), fill=XINGLAN + (70,))
for _k in range(3):
    _d.line((160, 1424 + _k * 12, 920, 1424 + _k * 12), fill=XINGLAN + (40 - _k * 10,), width=2)
MTN_COL = {'night': (24, 30, 46), 'death': (60, 60, 64), 'war': (110, 66, 56), 'fate': (90, 96, 108)}
def draw_background(t, theme):
    """建康: river hills, a faint scatter of stars."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(192, 196, 200), (158, 166, 176), MTN_COL.get(theme, (96, 112, 132))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.72))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """算筹: a few counting rods laid as a numeral in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=XINGLAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=XINGLAN + (220,), width=3)
        cx, cy = x + sx * 34, y + sy * 34
        for k in range(3):
            d.line((cx + sx * k * 12, cy, cx + sx * k * 12, cy + sy * 40), fill=GUIYING + (235,), width=4)
        d.line((cx + sx * 40, cy + sy * 6, cx + sx * 70, cy + sy * 6), fill=GUIYING + (235,), width=4)
        d.line((cx + sx * 55, cy + sy * 14, cx + sx * 55, cy + sy * 40), fill=GUIYING + (235,), width=4)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def zu_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """祖冲之: a Southern-dynasty scholar-official — gauze cap, wide blue robe, a bundle of counting rods at the belt; grey beard with age."""
    b = bow + 6 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    if kw.get('fall'):
        return hand
    if up:
        A.d[layer].rectangle((x - 0.07 * h, y - 1.1 * h, x + 0.07 * h, y - 0.94 * h), fill=255)
        A.d['wash' if old > 0.5 else layer].polygon([(x, y - 0.86 * h), (x + dir * 0.07 * h, y - 0.86 * h), (x + dir * 0.03 * h, y - 0.68 * h)], fill=255)
    top = y - (0.48 if kneel else 0.76) * h
    A.d['xinglan'].polygon([(x - 0.1 * h, top), (x + 0.1 * h, top), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=150)
    return hand

def rods(A, x, y, digits, s=40, layer='guiying'):
    """Counting-rod numerals for a string of digits (vertical form for odd places, horizontal for even)."""
    for i, ch in enumerate(digits):
        n = int(ch); cx = x + i * s * 1.2
        if n == 0:
            continue
        vertical = (len(digits) - i) % 2 == 1
        if n >= 6:
            if vertical:
                A.d[layer].line((cx - 0.4 * s, y - 0.5 * s, cx + 0.4 * s, y - 0.5 * s), fill=255, width=5)
            else:
                A.d[layer].line((cx, y - 0.5 * s, cx, y - 0.1 * s), fill=255, width=5)
        for k in range(n % 6 if n >= 6 else n):
            if vertical:
                xx = cx - 0.4 * s + k * 0.2 * s
                A.d[layer].line((xx, y - 0.4 * s, xx, y + 0.4 * s), fill=255, width=5)
            else:
                yy = y - 0.4 * s + k * 0.2 * s
                A.d[layer].line((cx - 0.4 * s, yy, cx + 0.4 * s, yy), fill=255, width=5)

def polygon_in(A, cx, cy, r, n, layer='xinglan', circle=True):
    if circle:
        A.d['ink'].ellipse((cx - r, cy - r, cx + r, cy + r), outline=200, width=4)
    n = max(3, int(n))
    m = min(n, 360)
    pts = [(cx + r * math.cos(2 * math.pi * k / m - math.pi / 2), cy + r * math.sin(2 * math.pi * k / m - math.pi / 2)) for k in range(m)]
    A.d[layer].polygon(pts, fill=110)
    A.d[layer].line(pts + [pts[0]], fill=255, width=3)

def nanche(A, x, base, s, t, turn=0.0, layer='guiying'):
    """指南车: a two-wheeled cart; the wooden figure on top keeps pointing the same way however the cart turns."""
    A.d[layer].rectangle((x - s, base - 0.55 * s, x + s, base - 0.3 * s), fill=255)
    for wx in (x - 0.6 * s, x + 0.6 * s):
        A.d['ink'].ellipse((wx - 0.3 * s, base - 0.6 * s, wx + 0.3 * s, base), outline=255, width=max(4, int(0.05 * s)))
        a = t * 3
        for k in range(4):
            A.d['ink'].line((wx, base - 0.3 * s, wx + 0.3 * s * math.cos(a + k * math.pi / 2), base - 0.3 * s + 0.3 * s * math.sin(a + k * math.pi / 2)), fill=200, width=2)
    A.d['ink'].line((x - s, base - 0.45 * s, x - 1.6 * s, base - 0.6 * s), fill=255, width=6)
    person(A, x, base - 0.55 * s, 0.9 * s, dir=-1, robe=True, hat='knot', arm=90, layer='ink')

def mill(A, cx, base, s, t):
    """水碓: a water-wheel turning a cam that lifts a pestle."""
    A.d['ocean'].rectangle((cx - 1.6 * s, base - 0.25 * s, cx - 0.2 * s, base), fill=170)
    A.d['ink'].ellipse((cx - 1.4 * s, base - 1.2 * s, cx - 0.4 * s, base - 0.2 * s), outline=255, width=6)
    for k in range(8):
        a = t * 2 + k * math.pi / 4
        A.d['ink'].line((cx - 0.9 * s, base - 0.7 * s, cx - 0.9 * s + 0.5 * s * math.cos(a), base - 0.7 * s + 0.5 * s * math.sin(a)), fill=220, width=3)
    lift = 0.2 * s * max(0, math.sin(t * 4))
    A.d['guiying'].line((cx - 0.4 * s, base - 0.7 * s, cx + 0.8 * s, base - 0.7 * s - lift), fill=255, width=8)
    A.d['ink'].rectangle((cx + 0.7 * s, base - 0.7 * s - lift, cx + 0.82 * s, base - 0.25 * s - lift), fill=255)
    A.d['ink'].chord((cx + 0.5 * s, base - 0.3 * s, cx + 1.0 * s, base + 0.1 * s), 180, 360, fill=255)

# ================================================================ chapter card
CH = {16: (6, 12), 48: (12, 24), 80: (24, 96), 112: (96, 192), 144: (192, 360)}
def art_geyuan_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (12, 24))
    q = ease_out(u / (1.4 * P))
    n = int(a * (b / a) ** clamp((q - 0.2) / 0.6))
    polygon_in(A, 540, 1040, 220, n)
    A.flush(cv)
    paste(cv, text_img(f'{n}边形' if n < 360 else '近乎圆', SERIF, 36, XINGLAN, 'Black', bleed=False), W / 2, 1040, 1, clamp(q / 0.3))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_geyuan_chapter)
    ink_in(cv, text_img(no, SERIF, 56, XINGLAN, 'Black', bleed=False, spacing=12), W / 2, 1340, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1460, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_z_hook_pi(A, cv, t, u):
    polygon_in(A, 540, 1080, 200, int(6 * 2 ** (clamp(u / (1.4 * P)) * 6)))
    A.flush(cv)
    paste(cv, text_img('3.1415926', SERIF, 64, XINGLAN, 'Black', bleed=False, spacing=4), W / 2, 1360, 1, clamp(u / 0.6))

def art_z_hook_ratio(A, cv, t, u):
    A.flush(cv)
    paste(cv, text_img('355\n—\n113', SERIF, 96, XINGLAN, 'Black', bleed=False, spacing=4), W / 2, 1120, 1, clamp(u / 0.6))

def art_z_hook_cart(A, cv, t, u):
    ground(A, GROUND)
    nanche(A, lerp(300, 760, ease_out(u / (2 * P))), GROUND, 150, t)

def art_z_hook_moon(A, cv, t, u):
    A.d['wash'].ellipse((340, 880, 740, 1280), fill=255)
    A.d['mid'].ellipse((340, 880, 740, 1280), outline=200, width=4)
    for (x, y, r) in ((450, 980, 40), (600, 1100, 60), (500, 1180, 30), (640, 960, 25)):
        A.d['mid'].ellipse((x - r, y - r, x + r, y + r), fill=160)

# ================================================================ 第一回 家学
def art_z_birth(A, cv, t, u):
    A.d['ocean'].rectangle((60, GROUND - 60, W - 60, GROUND + 40), fill=150)
    river(A, GROUND - 56, t, rows=2, amp=3)
    palace(A, 540, GROUND - 60, 260, layer='mid')
    A.flush(cv)
    paste(cv, text_img('生于南朝宋都城建康', SERIF, 50, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '祖籍范阳遒县 今河北涞水', t, t - u + P)

def art_z_family(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 210, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
    zu_(A, 380, GROUND, 120, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('祖父掌管土木工程 家传历算之学', SERIF, 44, XINGLAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '祖父祖昌 官至大匠卿', t, t - u + P)

def art_z_study(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 420, layer='mid')
    zu_(A, 300, GROUND, 170, dir=1, kneel=True, arm=100)
    A.flush(cv)
    paste(cv, text_img('搜炼古今 博采沈奥', SERIF, 50, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '自述 少年时已遍读历代历法', t, t - u + P)

def art_z_sky(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((500, GROUND - 260, 516, GROUND), fill=255)
    sh = 300 * (0.5 + 0.5 * math.sin(t * 0.8))
    A.d['guiying'].polygon([(508, GROUND), (508 + sh, GROUND - 4), (508 + sh, GROUND + 4)], fill=255)
    zu_(A, 300, GROUND, 190, dir=1, arm=140)
    A.flush(cv)
    paste(cv, text_img('立表测影 观察日月星辰', SERIF, 50, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_hualin(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    zu_(A, 540, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('被选入华林学省 专心研究', SERIF, 48, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '皇家学术机构', t, t - u + P)

# ================================================================ 第二回 大明历
def art_z_daming(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('大明历', SERIF, 72, INK, 'Black', bleed=False, spacing=12), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('三十四岁 上书宋孝武帝', SERIF, 48, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_z_suicha(A, cv, t, u):
    ground(A, GROUND)
    cx, cy = 540, 1060
    A.d['ink'].ellipse((cx - 160, cy - 160, cx + 160, cy + 160), outline=200, width=4)
    a = t * 0.3
    A.d['xinglan'].line((cx, cy, cx + 160 * math.cos(a), cy + 160 * math.sin(a)), fill=255, width=5)
    A.d['guiying'].ellipse((cx + 160 * math.cos(a) - 14, cy + 160 * math.sin(a) - 14, cx + 160 * math.cos(a) + 14, cy + 160 * math.sin(a) + 14), fill=255)
    A.flush(cv)
    paste(cv, text_img('首次把岁差引入历法', SERIF, 50, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '岁差 东晋虞喜所发现', t, t - u + P)

def art_z_run(A, cv, t, u):
    A.flush(cv)
    paste(cv, text_img('三百九十一年 置一百四十四闰', SERIF, 46, XINGLAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('交点月 27.21223日', SERIF, 52, INK, 'Black', bleed=False, spacing=6), W / 2, 1100, 1, clamp((u - P) / 0.4))
    note_in(cv, '与今测值相差不到一秒', t, t - u + P)

def art_z_debate(A, cv, t, u):
    """6-beat set piece: 驳议 — the favourite 戴法兴 attacks the new calendar as 诬天背经; he answers point by point: 愿闻显据 以核理实."""
    ph = u / P
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    emperor(A, 540, GROUND - 40, 170, dir=1, arm=-8, kneel=True)
    person(A, 780, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)) if ph < 3 else -8, layer='mid')
    zu_(A, 300, GROUND, 200, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)) if ph >= 3 else -8)
    A.flush(cv)
    if ph < 3:
        lab, col = '权臣戴法兴斥为 诬天背经', ZHU
    else:
        lab, col = '他据理驳斥 愿闻显据 以核理实', XINGLAN
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '不虚推古人 不迷信经典', t, t - u + 3 * P)

def art_z_shelve(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    A.d['wash'].rectangle((300, 1250, 780, 1290), fill=230)
    A.flush(cv)
    paste(cv, text_img('孝武帝去世 新历被搁置', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_county(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='娄县', layer='mid', open_=1.0)
    ground(A, GROUND)
    zu_(A, 540, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('外放娄县县令', SERIF, 52, XINGLAN, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '年份约略', t, t - u + P)

# ================================================================ 第三回 割圆
def scene_geyuan(cv, t, c, k):
    """8-beat custom scene: 割圆术 — following 刘徽, he doubles the sides of an inscribed polygon again and again with counting rods,
    6, 12, 24 … up to 24576 sides, and pins π between 3.1415926 and 3.1415927."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    steps = [(6, '3'), (12, '3.1'), (24, '3.13'), (96, '3.141'), (384, '3.1415'), (1536, '3.14159'), (6144, '3.141592'), (24576, '3.1415926')]
    i = min(7, int(ph))
    n, val = steps[i]
    polygon_in(A, 540, 980, 230, n)
    ground(A, GROUND)
    zu_(A, 260, GROUND, 170, dir=1, kneel=True, arm=lerp(90, 110, 0.5 + 0.5 * math.sin(t * 6)))
    rods(A, 420, GROUND - 40, str(n), s=36)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '割圆术', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=98)
    fx.flush(cv)
    paste(cv, text_img(f'{n}边形', SERIF, 46, XINGLAN, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img(val, SERIF, 64, ZHU if i == 7 else INK, 'Black', bleed=False, spacing=4), W / 2, 1270, 1, 1)
    note_in(cv, '具体算法已失传 此为后人推测', t, s0 + 2 * P)

def art_z_bounds(A, cv, t, u):
    A.flush(cv)
    paste(cv, text_img('3.1415926 < π < 3.1415927', SERIF, 52, INK, 'Black', bleed=False, spacing=4), W / 2, 1100, 1, clamp(u / 0.6))
    paste(cv, text_img('精确到小数点后第七位', SERIF, 50, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '记载见隋书 律历志', t, t - u + P)

def art_z_yuelv(A, cv, t, u):
    A.flush(cv)
    paste(cv, text_img('约率 22/7', SERIF, 60, INK, 'Black', bleed=False, spacing=6), W / 2, 1000, 1, clamp(u / 0.4))
    paste(cv, text_img('密率 355/113', SERIF, 60, ZHU, 'Black', bleed=False, spacing=6), W / 2, 1140, 1, clamp((u - P) / 0.4))
    paste(cv, text_img('两个分数 便于实际使用', SERIF, 48, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_z_millennium(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(140, 940, clamp(u / (3 * P)))
    A.d['xinglan'].line((140, GROUND - 120, x, GROUND - 120), fill=255, width=10)
    A.flush(cv)
    paste(cv, text_img('这一精度保持了近千年', SERIF, 50, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '十五世纪阿拉伯数学家阿尔卡西才超过', t, t - u + P)

def art_z_zhuishu(A, cv, t, u):
    ground(A, GROUND)
    book(A, 540, GROUND, 200, 280, layer='xinglan')
    A.flush(cv)
    paste(cv, text_img('著缀术 唐代列为国子监算学教材', SERIF, 44, XINGLAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '学官莫能究其深奥', t, t - u + P)

# ================================================================ 第四回 巧器
def art_z_nanche(A, cv, t, u):
    """6-beat set piece: 指南车 — a south-pointing cart with gear trains; however it turns, the figure on top points south."""
    ph = u / P
    ground(A, GROUND)
    x = 540 + 260 * math.sin(ph * 0.9)
    nanche(A, x, GROUND, 150, t)
    A.flush(cv)
    lab = '为萧道成改造指南车' if ph < 3 else '圆转不穷 而司方如一'
    paste(cv, text_img(lab, SERIF, 50, XINGLAN if ph < 3 else ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '内用铜制齿轮 不靠磁石', t, t - u + P)

def art_z_boat(A, cv, t, u):
    """6-beat set piece: 千里船 and 水碓磨 — a fast boat tried on the river, then a water-powered pestle and mill."""
    ph = u / P
    if ph < 3:
        A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=150)
        river(A, 1250, t, rows=2, amp=3)
        boat(A, lerp(100, 900, clamp(ph / 3)), 1260, 110, t)
        lab = '造千里船 一日行百余里'
    else:
        ground(A, GROUND)
        mill(A, 600, GROUND, 200, t)
        lab = '造水碓磨 借水力舂米磨面'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '见南齐书 祖冲之传', t, t - u + P)

def art_z_qiqi(A, cv, t, u):
    ground(A, GROUND)
    a = 0.3 * math.sin(t)
    A.d['ink'].rectangle((360, GROUND - 260, 376, GROUND), fill=255)
    A.d['ink'].rectangle((704, GROUND - 260, 720, GROUND), fill=255)
    A.d['ink'].line((368, GROUND - 240, 712, GROUND - 240), fill=255, width=4)
    cx, cy = 540, GROUND - 160
    A.d['guiying'].polygon([(cx - 70 * math.cos(a) - 80 * math.sin(a), cy - 70 * math.sin(a) + 80 * math.cos(a)), (cx + 70 * math.cos(a) - 80 * math.sin(a), cy + 70 * math.sin(a) + 80 * math.cos(a)), (cx + 90 * math.cos(a) + 40 * math.sin(a), cy + 90 * math.sin(a) - 40 * math.cos(a)), (cx - 90 * math.cos(a) + 40 * math.sin(a), cy - 90 * math.sin(a) - 40 * math.cos(a))], fill=255)
    A.flush(cv)
    paste(cv, text_img('复制欹器 虚则欹 中则正 满则覆', SERIF, 44, XINGLAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))

def art_z_anbian(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        A.d['grass'].rectangle((120 + k * 180, GROUND - 26, 260 + k * 180, GROUND - 6), fill=200)
    zu_(A, 540, GROUND, 200, dir=1, arm=60, old=0.6)
    A.flush(cv)
    paste(cv, text_img('上安边论 主张开垦屯田', SERIF, 48, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '因战乱未能施行', t, t - u + P)

def art_z_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    zu_(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('祖冲之去世 终年七十二岁', SERIF, 48, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 缀术
def art_z_son(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, robe=True, hat='knot', arm=80, layer='ink')
    A.d['ink'].ellipse((700, 1000, 900, 1200), outline=255, width=4)
    A.flush(cv)
    paste(cv, text_img('儿子祖暅 继承父业', SERIF, 50, XINGLAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('幂势既同 则积不容异', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.4))
    note_in(cv, '祖暅原理 比西方早一千多年', t, t - u + P)

def art_z_used(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('祖暅三次上书 大明历终于颁行', SERIF, 44, XINGLAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '梁天监九年 距编成已近五十年', t, t - u + P)

def art_z_lost(A, cv, t, u):
    ground(A, GROUND)
    book(A, 540, GROUND, 200, 280, layer='mid')
    flames(A, 540, GROUND, 300, 160 * clamp(u / (2 * P)), t, n=3, seed=98, smoke=True)
    A.flush(cv)
    paste(cv, text_img('缀术在宋代以后失传', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_z_moon(A, cv, t, u):
    art_z_hook_moon(A, cv, t, u)
    A.flush(cv)
    paste(cv, text_img('月球背面一座环形山以他命名', SERIF, 46, XINGLAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '另有小行星祖冲之星', t, t - u + P)

def art_z_school(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='mid')
    for k in range(3):
        person(A, 300 + k * 240, GROUND, 130, dir=1, robe=False, hat='none', kneel=True, arm=100, layer='ink')
    A.flush(cv)
    paste(cv, text_img('每个中国孩子都在课本里认识他', SERIF, 44, XINGLAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))

def art_z_end(A, cv, t, u):
    polygon_in(A, 540, 1100, 220, 360)
    A.flush(cv)
    paste(cv, text_img('愿闻显据 以核理实', SERIF, 52, XINGLAN, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))

def art_z_legacy(A, cv, t, u):
    polygon_in(A, 860, 1380, 50, 6 + int(6 * (0.5 + 0.5 * math.sin(t))) * 2)

def art_z_title(A, cv, t, u):
    polygon_in(A, 820, 1200, 130, 24)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    zu_(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '家学'), 48: ('第二回', '大明历'), 80: ('第三回', '割圆'),
            112: ('第四回', '巧器'), 144: ('第五回', '缀术')}

CARDS = [
    C(0, 2, 'works', 'num', num='七位小数', line='领先世界近千年', art=art_z_hook_pi),
    C(2, 4, 'empire', 'num', num='密率', line='一百一十三分之三百五十五', art=art_z_hook_ratio),
    C(4, 6, 'life', 'num', num='一辆小车', line='无论怎么转都指向南', art=art_z_hook_cart),
    C(6, 8, 'night', 'num', num='月球上', line='有一座环形山以他命名', art=art_z_hook_moon),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 家学
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=429, main='生于建康', sub='南朝宋', art=art_z_birth),
    C(22, 26, 'works', 'card', year=435, main='家学', sub='历算世家', note='年份约略', art=art_z_family),
    C(26, 32, 'night', 'card', year=445, main='博览', sub='搜炼古今', note='年份约略', art=art_z_study),
    C(32, 40, 'empire', 'card', year=450, main='观天', sub='立表测影', note='年份约略', art=art_z_sky),
    C(40, 48, 'court', 'card', year=455, main='华林学省', sub='皇家研究', note='年份约略', art=art_z_hualin),
    # ---- 第二回 大明历
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'works', 'card', year=462, main='大明历', sub='三十四岁', art=art_z_daming),
    C(54, 58, 'night', 'card', year=462, main='岁差', sub='首次引入', art=art_z_suicha),
    C(58, 62, 'empire', 'card', year=462, main='精密', sub='交点月', art=art_z_run),
    C(62, 68, 'war', 'card', year=463, main='驳议', sub='愿闻显据', art=art_z_debate),
    C(68, 74, 'fate', 'card', year=464, main='搁置', sub='孝武帝去世', art=art_z_shelve),
    C(74, 80, 'life', 'card', year=465, main='娄县令', sub='外放', note='年份约略', art=art_z_county),
    # ---- 第三回 割圆
    C(80, 82, 'works', 'chapter'),
    C(82, 90, 'night', 'geyuan', year=470),
    C(90, 96, 'empire', 'card', year=470, main='七位小数', sub='圆周率', note='年份约略', art=art_z_bounds),
    C(96, 100, 'works', 'card', year=470, main='密率', sub='三五五 一一三', art=art_z_yuelv),
    C(100, 106, 'court', 'card', year=470, main='领先千年', sub='直到十五世纪', art=art_z_millennium),
    C(106, 112, 'life', 'card', year=475, main='缀术', sub='深奥难懂', note='年份约略', art=art_z_zhuishu),
    # ---- 第四回 巧器
    C(112, 114, 'empire', 'chapter'),
    C(114, 120, 'works', 'card', year=478, main='指南车', sub='铜机', art=art_z_nanche),
    C(120, 126, 'life', 'card', year=490, main='千里船', sub='水碓磨', note='年份约略', art=art_z_boat),
    C(126, 130, 'night', 'card', year=490, main='欹器', sub='满则覆', note='年份约略', art=art_z_qiqi),
    C(130, 136, 'court', 'card', year=494, main='安边论', sub='屯田之策', note='年份约略', art=art_z_anbian),
    C(136, 144, 'death', 'card', year=500, main='祖冲之去世', sub='七十二岁', art=art_z_death),
    # ---- 第五回 缀术
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'works', 'card', year=504, main='父子相传', sub='子承父业', note='年份约略', art=art_z_son),
    C(150, 154, 'court', 'card', year=510, main='大明历颁行', sub='梁天监九年', art=art_z_used),
    C(154, 158, 'fate', 'card', year=1100, main='缀术失传', sub='宋代以后', note='年份约略', art=art_z_lost),
    C(158, 162, 'night', 'card', year=1961, main='环形山', sub='月球背面', note='年份约略', art=art_z_moon),
    C(162, 166, 'life', 'card', year=1961, main='课本', sub='代代传诵', art=art_z_school),
    C(166, 170, 'end', 'card', year=1961, main='愿闻显据', sub='以核理实', art=art_z_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='玖拾捌', col=XINGLAN, acc=GUIYING, born=429, died=500, age0=428,
    born_lab='429年', died_lab='500年', years_txt='公元429 — 500',
    hook_q='没有计算器的年代 · 他怎么把圆周率算到七位？',
    name_line='祖冲之 · 字文远', name='祖冲之', seal='缀术', title_art=art_z_title,
    q1='数学天才？', q2='工匠奇才？',
    end_art=art_z_legacy, end_big='圆周率', end_seal='文远',
    end_l1='别人说天不可测', end_l2='他偏要一位一位算出来',
    end_brush='愿闻显据', end_ask='圆周率你能背到第几位？评论区聊聊', next='上官婉儿'),
    scenes=dict(chapter=scene_chapter, geyuan=scene_geyuan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
