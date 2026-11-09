"""千古人物志 · 第捌拾叁集 · 李商隐 (813–858)
Look: 锦瑟紫 + 烛光黄, 烛泪 corner borders (a candle with a drip), 巴山 night rain behind.
Chapter card: 蜡炬 — a candle burns a little lower each chapter, wax tears running down; in the last chapter it goes out in a thread of smoke.
Set pieces: custom 8-beat scene 'yeyu' (夜雨寄北), 6-beat 佣书贩舂, 6-beat 令狐楚授文, 6-beat 党争夹缝, 6-beat 春蚕蜡炬,
6-beat 乐游原, 6-beat 锦瑟.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_hanyu as Hy           # engine + helpers (previous episode)
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
from render_quyuan import river
from render_simayi import emperor
from render_songtaizu import tent
from render_zhouyu import guqin

F.RIPPLE = False
JINSE = (118, 62, 92)               # 锦瑟紫
LAZHU = (228, 168, 68)              # 烛光黄
S.LAYERS.append(('jinse', JINSE, 0.9, 1.0))
S.LAYERS.append(('lazhu', LAZHU, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='李', life='义', court='唐', night='烛', war='党', empire='第', works='诗', fate='寒', death='逝', end='情')
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
G.THEMES['empire']['sun'] = (JINSE, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (LAZHU, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # a rising autumn pond
    _d.line([(60 + i * 30, 1452 + _k * 14 + 3 * math.sin(i * 0.8 + _k)) for i in range(34)], fill=(90, 100, 120, 46 - _k * 10), width=3)
for _x in (110, 970):               # lotus leaves at the margins
    _d.ellipse((_x - 50, 1400, _x + 50, 1436), fill=(90, 110, 90, 60))
    _d.line((_x, 1418, _x + 6, 1340), fill=(90, 110, 90, 70), width=3)
    _d.polygon([(_x - 10, 1346), (_x + 6, 1310), (_x + 22, 1346)], fill=JINSE + (70,))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (96, 96, 108)}
def draw_background(t, theme):
    """巴山: misty ridges over an autumn pond, lotus at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(194, 190, 196), (164, 156, 170), MTN_COL.get(theme, (118, 106, 124))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """烛泪: a small candle with a drip in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=JINSE + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=JINSE + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.rectangle((cx - 8, cy - 12, cx + 8, cy + 26), fill=(200, 60, 50, 230))
        d.ellipse((cx - 6, cy - 32, cx + 6, cy - 14), fill=LAZHU + (240,))
        d.ellipse((cx + 4, cy - 6, cx + 12, cy + 6), fill=(230, 210, 190, 230))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def yishan(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """李商隐: a slender Tang scholar — 幞头 with soft tails, a light beard, a lavender robe."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.075 * h, y - 1.05 * h, x + 0.075 * h, y - 0.9 * h), 180, 360, fill=255)
        d.line([(x - dir * 0.05 * h, y - 0.97 * h), (x - dir * 0.13 * h, y - 0.9 * h), (x - dir * 0.15 * h, y - 0.8 * h)], fill=255, width=max(2, int(0.014 * h)))
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.03 * h, y - 0.84 * h), (x + dir * 0.07 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.74 * h)], fill=255)
    if not kw.get('fall'):
        A.d['jinse'].polygon([(x - 0.1 * h, y - (0.48 if kneel else 0.75) * h), (x + 0.1 * h, y - (0.48 if kneel else 0.75) * h), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=140)
    return hand

def candle(A, cx, base, h, burn, t, lit=True):
    """A red candle that has burned down by `burn` (0..1), with wax tears."""
    hh = h * (1 - 0.8 * burn)
    A.d['red'].rectangle((cx - 0.12 * h, base - hh, cx + 0.12 * h, base), fill=230)
    A.d['ink'].rectangle((cx - 0.2 * h, base, cx + 0.2 * h, base + 0.06 * h), fill=255)
    for k in range(int(2 + 5 * burn)):
        dx = (-0.1 + 0.05 * k) * h
        A.d['wash'].line((cx + dx, base - hh, cx + dx, base - hh + (0.1 + 0.05 * (k % 3)) * h), fill=230, width=max(3, int(0.03 * h)))
    if lit:
        fl = 0.06 * h * (1 + 0.15 * math.sin(t * 9))
        A.d['lazhu'].ellipse((cx - 0.05 * h, base - hh - 2.6 * fl, cx + 0.05 * h, base - hh), fill=255)
        A.d['lazhu'].ellipse((cx - 0.3 * h, base - hh - 0.4 * h, cx + 0.3 * h, base - hh + 0.1 * h), fill=50)
    else:
        for k in range(4):
            q = (t * 0.4 + k / 4) % 1
            A.d['wash'].ellipse((cx - 6 + 10 * math.sin(q * 6), base - hh - 20 - 160 * q - 6, cx + 6 + 10 * math.sin(q * 6), base - hh - 20 - 160 * q + 6), fill=int(180 * (1 - q)))

def rain(A, t, amt=1.0, n=50):
    for i in range(n):
        q = (t * 1.6 + i / n) % 1
        x = 60 + (i * 53) % 960
        A.d['wash'].line((x, lerp(600, 1460, q), x - 6, lerp(600, 1460, q) + 30), fill=int(150 * amt), width=2)

def silkworm(A, x, y, s, t):
    for k in range(6):
        A.d['wash'].ellipse((x + k * 0.22 * s - 0.14 * s, y - 0.1 * s + 0.03 * s * math.sin(t * 3 + k), x + k * 0.22 * s + 0.14 * s, y + 0.1 * s + 0.03 * s * math.sin(t * 3 + k)), fill=255)
    A.d['wash'].line([(x + 1.2 * s, y), (x + 1.6 * s, y - 0.4 * s), (x + 2.2 * s, y - 0.3 * s)], fill=200, width=2)

# ================================================================ chapter card
CH = {16: (0.0, 0.2), 48: (0.2, 0.4), 80: (0.4, 0.6), 112: (0.6, 0.8), 144: (0.8, 1.0)}
def art_candle_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (0.2, 0.4))
    q = ease_out(u / (1.2 * P))
    candle(A, 540, 1200, 380, lerp(a, b, q), t, lit=not (kb == 144 and q > 0.8))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_candle_chapter)
    ink_in(cv, text_img(no, SERIF, 56, JINSE, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_s_hook_untitled(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 420, 280, ease_out(u / (1.0 * P)), layer='wash')
    A.flush(cv)
    stamp(cv, seal('无题', 70, ZHU), 540, 1100, t, t - u + 0.6)

def art_s_hook_candle(A, cv, t, u):
    ground(A, GROUND)
    candle(A, 540, 1260, 360, clamp(u / (1.2 * P)), t)

def art_s_hook_two(A, cv, t, u):
    ground(A, GROUND)
    banner = Hy.banner
    banner(A, 300, GROUND, 360, t, layer='mid')
    banner(A, 780, GROUND, 360, t, layer='jinse')
    yishan(A, 540, GROUND, 220, dir=1 if math.sin(t * 2) > 0 else -1, arm=-8)

def art_s_hook_sunset(A, cv, t, u):
    A.d['lazhu'].ellipse((540 - 140, lerp(900, 1100, clamp(u / (1.2 * P))) - 140, 540 + 140, lerp(900, 1100, clamp(u / (1.2 * P))) + 140), fill=200)
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 200), (x + 240, GROUND)], fill=170)
    ground(A, GROUND)

# ================================================================ 第一回 孤寒
def art_s_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x - 60, GROUND - 220), (x + 60, GROUND - 220), (x + 220, GROUND)], fill=150)
    A.d['wash'].rectangle((420, GROUND - 160, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 160), (680, GROUND - 160), (540, GROUND - 220)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('怀州河内人 · 自称唐宗室远支', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('河内', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_father(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 30, GROUND - 300), (x + 30, GROUND - 300), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    x = lerp(900, 300, ease_out(u / (3 * P)))
    A.d['mid'].rectangle((x - 90, GROUND - 80, x + 90, GROUND - 36), fill=255)
    person(A, x + 140, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, ph=t * 2, arm=-8, layer='ink')
    person(A, x + 230, GROUND, 110, dir=-1, robe=True, hat='none', ph=t * 2 + 1, arm=-8, layer='jinse')
    A.flush(cv)
    paste(cv, text_img('十岁左右丧父 · 扶柩还乡', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_yongshu(A, cv, t, u):
    """6-beat set piece: 佣书贩舂 — as a boy he copies books for hire and pounds rice for sale to keep the family."""
    ph = u / P
    ground(A, GROUND)
    if ph < 3:
        desk(A, 540, GROUND, 420, layer='mid')
        person(A, 300, GROUND, 130, dir=1, robe=True, hat='none', kneel=True, arm=lerp(80, 110, 0.5 + 0.5 * math.sin(t * 6)), layer='ink')
        lamp(A, 780, GROUND - 74, 26, t, glow=0.8)
        slips(A, 440, GROUND - 74, min(16, int(clamp(ph / 3) * 16) + 1), 70, layer='jinse')
        lab = '佣书 · 替人抄书换钱'
    else:
        A.d['dune'].chord((440, GROUND - 120, 640, GROUND + 40), 0, 180, fill=255)
        q = 0.5 + 0.5 * math.sin(t * 5)
        A.d['huyang'].line((540, GROUND - 70 - 160 * q, 540, GROUND - 260 - 160 * q), fill=255, width=16)
        person(A, 360, GROUND, 140, dir=1, robe=False, hat='none', arm=lerp(110, 160, q), layer='ink')
        lab = '贩舂 · 舂米出售 养活全家'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '佣书贩舂 语见其祭裴氏姊文', t, t - u + P)

def art_s_guwen(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='jinse')
    person(A, 280, GROUND, 150, dir=1, robe=True, hat='none', kneel=True, arm=100, layer='ink')
    A.d['wash'].rectangle((440, GROUND - 140, 640, GROUND - 76), fill=255)
    A.flush(cv)
    paste(cv, text_img('十六岁著才论 圣论 · 以古文出诸公间', SERIF, 44, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_linghu(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 780, GROUND, 280, 220, layer='mid', open_=1.0)
    person(A, 640, GROUND, 210, dir=-1, robe=True, hat='knot', arm=lerp(-8, 80, ease_out(u / 0.6)), layer='ink')
    yishan(A, 380, GROUND, 180, dir=1, bow=25, arm=90)
    A.flush(cv)
    paste(cv, text_img('天平节度使令狐楚爱其才 · 收入幕中', SERIF, 44, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_teach(A, cv, t, u):
    """6-beat set piece: 令狐楚授文 — the old statesman personally teaches him the formal parallel style of memorials;
    he studies beside 令狐's sons and his writing transforms."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    person(A, 780, GROUND, 180, dir=-1, robe=True, hat='knot', kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    yishan(A, 300, GROUND, 160, dir=1, kneel=True, arm=100)
    if ph >= 2:
        for j in range(2):
            person(A, 160 + j * 70, GROUND, 140, dir=1, robe=True, hat='none', kneel=True, arm=90, layer='mid')
    lamp(A, 540, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    lab = '令狐楚亲授今体章奏之法' if ph < 2 else ('与令狐诸子同游' if ph < 4 else '自是文章大进')
    paste(cv, text_img(lab, SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '其子令狐绹 后来成了他一生的心结', t, t - u + 2 * P)

def art_s_fail(A, cv, t, u):
    ground(A, GROUND)
    for r in range(2):
        for i in range(6):
            x = 160 + i * 150; y = GROUND - r * 170
            A.d['mid'].rectangle((x - 55, y - 130, x + 55, y), fill=200)
    yishan(A, 540, GROUND, 170, dir=-1, arm=-8, ph=t * 2)
    A.flush(cv)
    paste(cv, text_img('应进士试 · 屡试不第', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 党争
def art_s_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='jinse')
    ground(A, GROUND)
    yishan(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('经令狐绹推荐 · 二十五岁中进士', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('进士', 56), 860, 1020, t, t - u + P, rot=6)

def art_s_linghudeath(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, layer='ink')
    yishan(A, 880, GROUND, 150, dir=-1, kneel=True, bow=30, arm=90)
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('令狐楚病危 · 命其代草遗表', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_wangshi(A, cv, t, u):
    """6-beat set piece: 党争夹缝 — 王茂元 admires him and gives him his daughter; but 王 belongs to the 李 faction and the 令狐 to the 牛;
    the 牛 men call him ungrateful, and he is caught between both parties for life."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        A.d['wash'].rectangle((560, GROUND - 260, 900, GROUND), fill=230)
        A.d['ink'].polygon([(540, GROUND - 260), (920, GROUND - 260), (730, GROUND - 330)], fill=255)
        A.d['red'].rectangle((690, GROUND - 160, 770, GROUND), fill=220)
        Hy.Yg.yu(A, 520, GROUND, 180, dir=-1, arm=-8, t=t, layer='mid')
        yishan(A, 360, GROUND, 190, dir=1, arm=60)
        lab, col = '泾原节度使王茂元 以女妻之', JINSE
    elif ph < 4:
        Hy.banner(A, 260, GROUND, 360, t, layer='mid')
        Hy.banner(A, 820, GROUND, 360, t, layer='jinse')
        yishan(A, 540, GROUND, 200, dir=1 if math.sin(t * 3) > 0 else -1, arm=-8)
        A.flush(cv)
        paste(cv, text_img('牛', SERIF, 50, INK, 'Black', bleed=False), 320, 1080, 1, 1)
        paste(cv, text_img('李', SERIF, 50, INK, 'Black', bleed=False), 880, 1080, 1, 1)
        lab, col = '令狐属牛党 王茂元属李党', JINSE
    else:
        for j in range(4):
            person(A, 640 + j * 90, GROUND, 160, dir=-1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + j)), layer='ink')
        yishan(A, 360, GROUND, 190, dir=1, bow=25, arm=-8)
        lab, col = '牛党斥之 背恩无行', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('从此夹在两党之间 一生不得志', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.5) / 0.4))

def art_s_hongci(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 420, 260, 1.0, layer='wash')
    A.d['ink'].line((380, 1060, 700, 1140), fill=255, width=10)
    A.flush(cv)
    paste(cv, text_img('博学宏词 已取又被抹去', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '中书长者曰 此人不堪', t, t - u + P)

def art_s_xiaoshu(A, cv, t, u):
    ground(A, GROUND)
    for i in range(6):
        A.d['mid'].rectangle((140 + i * 140, GROUND - 400, 250 + i * 140, GROUND), fill=170)
        for j in range(5):
            bundle(A, 195 + i * 140, GROUND - 20 - j * 74, 50, layer='jinse' if (i + j) % 2 else 'mid')
    yishan(A, 540, GROUND, 160, dir=1, arm=150)
    A.flush(cv)
    paste(cv, text_img('任秘书省校书郎 · 旋调弘农尉', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_huoyu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 210, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    yishan(A, 400, GROUND, 190, dir=1, bow=10, arm=-8)
    A.flush(cv)
    paste(cv, text_img('为囚犯减刑 触怒上司 · 请辞而去', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_mother(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, female=True, layer='ink')
    yishan(A, 880, GROUND, 150, dir=-1, kneel=True, bow=30)
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('母亲去世 · 居丧三年', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 漂泊
def art_s_wuti(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        x = 200 + k * 140
        A.d['pink'].ellipse((x - 30, GROUND - 200 + 60 * clamp(u / (3 * P)) * (k % 2) - 30, x + 30, GROUND - 200 + 60 * clamp(u / (3 * P)) * (k % 2) + 30), fill=200)
        A.d['grass'].line((x, GROUND, x, GROUND - 170), fill=200, width=3)
    A.flush(cv)
    paste(cv, text_img('相见时难别亦难 东风无力百花残', SERIF, 44, JINSE, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '无题诗作年多不可考', t, t - u + P)

def art_s_chuncan(A, cv, t, u):
    """6-beat set piece: 春蚕蜡炬 — the silkworm spins until it dies; the candle weeps until it is ash."""
    ph = u / P
    ground(A, GROUND)
    if ph < 3:
        A.d['grass'].ellipse((260, 1100, 820, 1260), fill=200)
        silkworm(A, 360, 1180, 140, t)
        for k in range(int(clamp(ph / 3) * 20)):
            A.d['wash'].arc((600 - k * 6, 1120 - k * 3, 760 + k * 6, 1240 + k * 3), 0, 360, fill=120, width=1)
        lab = '春蚕到死丝方尽'
    else:
        candle(A, 540, 1260, 360, clamp((ph - 3) / 2.5), t)
        lab = '蜡炬成灰泪始干'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 50, ZHU if ph >= 3 else JINSE, 'Black', bleed=False, spacing=8), W / 2, 760, 1, 1)
    note_in(cv, '无题 相见时难别亦难', t, t - u + P)

def art_s_guilin(A, cv, t, u):
    for k in range(9):
        x = 100 + k * 110
        h = 300 + 120 * math.sin(k * 1.7)
        A.d['mid'].polygon([(x - 46, GROUND), (x - 36, GROUND - h + 40), (x - 10, GROUND - h), (x + 20, GROUND - h + 30), (x + 46, GROUND)], fill=180)
    ground(A, GROUND)
    yishan(A, 540, GROUND, 180, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('随郑亚赴桂州幕府 · 远走岭南', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_xuzhou(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 760, GROUND, 300, 220, layer='mid', open_=1.0)
    yishan(A, 420, GROUND, 190, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('入武宁节度使卢弘止幕', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_wife(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, female=True, layer='ink')
    yishan(A, 880, GROUND, 150, dir=-1, kneel=True, bow=30)
    for j in range(2):
        person(A, 120 + j * 80, GROUND, 90 + 20 * j, dir=1, robe=True, hat='none', arm=-8, layer='jinse')
    candle(A, 260, 1180, 120, 0.9, t)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('妻王氏病逝 · 留下一双儿女', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_rushu(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 40, GROUND - 440), (x + 40, GROUND - 440), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    yishan(A, lerp(100, 700, ease_out(u / (5 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('入柳仲郢东川幕府 · 远赴梓州', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '在蜀中前后五年', t, t - u + P)

# ================================================================ 第四回 巴山
def scene_yeyu(cv, t, c, k):
    """8-beat custom scene: 夜雨寄北 — rain all night on the 巴山; the autumn pond rises; alone at the west window he trims the candle,
    imagining the day they will talk of this rain together."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    for k2 in range(3):
        x = 260 + k2 * 280
        A.d['mid'].polygon([(x - 240, 1180), (x, 900), (x + 240, 1180)], fill=120)
    A.d['ocean'].rectangle((0, lerp(1240, 1160, clamp(ph / 6)), W, GROUND + 40), fill=120)
    rain(A, t, amt=0.9)
    A.d['mid'].rectangle((620, 960, 940, GROUND), fill=220)
    A.d['lazhu'].rectangle((660, 1000, 900, 1200), fill=120)
    candle(A, 820, 1200, 90, 0.4, t)
    yishan(A, 720, GROUND, 170, dir=1, kneel=True, arm=lerp(80, 120, clamp((ph - 5) / 0.6)), layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '夜雨寄北', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=83)
    fx.flush(cv)
    lines = ['君问归期未有期', '巴山夜雨涨秋池', '何当共剪西窗烛', '却话巴山夜雨时']
    for i, line in enumerate(lines):
        st = s0 + (0.4 + i * 1.7) * P
        if t >= st:
            paste(cv, text_img(line, SERIF, 44, ZHU if i == 3 else JINSE, 'Black', bleed=False, spacing=6), W / 2, 590 + i * 64, 1, clamp((t - st) / 0.4))
    note_in(cv, '寄给妻子还是友人 学界说法不一', t, s0 + 3 * P)

def art_s_jiasheng(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 760, GROUND, 200, dir=-1, kneel=True, bow=-10, arm=90)
    person(A, 380, GROUND, 180, dir=1, robe=True, hat='knot', kneel=True, arm=90, layer='ink')
    candle(A, 570, GROUND, 80, 0.5, t)
    A.flush(cv)
    paste(cv, text_img('可怜夜半虚前席 不问苍生问鬼神', SERIF, 44, JINSE, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '贾生 借汉文帝召见贾谊讽喻时事', t, t - u + P)

def art_s_lingxi(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    for k in range(2):
        q = (t * 0.15 + k * 0.5) % 1
        A.d['jinse'].polygon([(lerp(100, 980, q), 900 + 40 * k), (lerp(100, 980, q) + 60, 880 + 40 * k), (lerp(100, 980, q) + 20, 920 + 40 * k)], fill=255)
    A.flush(cv)
    paste(cv, text_img('身无彩凤双飞翼 心有灵犀一点通', SERIF, 44, JINSE, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_s_huijing(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='长安', layer='mid', open_=1.0)
    ground(A, GROUND)
    yishan(A, 540, GROUND, 190, dir=1, arm=-8, old=0.3)
    A.flush(cv)
    paste(cv, text_img('随柳仲郢回京 · 任盐铁推官', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_leyou(A, cv, t, u):
    """6-beat set piece: 乐游原 — restless at dusk, he drives up to the old plateau; the setting sun is boundlessly fine — only, it is near nightfall."""
    ph = u / P
    sy = lerp(880, 1160, clamp(ph / 6))
    A.d['lazhu'].ellipse((540 - 150, sy - 150, 540 + 150, sy + 150), fill=220)
    A.d['red'].ellipse((540 - 150, sy - 150, 540 + 150, sy + 150), fill=int(120 * clamp(ph / 5)))
    A.d['mid'].polygon([(60, GROUND), (400, 1160), (700, 1180), (1020, GROUND)], fill=200)
    carriage(A, lerp(100, 360, clamp(ph / 2)), 1190, 90, dir=1, wheel=t * 4 if ph < 2 else 0, ph=t * 6 if ph < 2 else 0, moving=ph < 2, layer='ink')
    yishan(A, 520, 1180, 140, dir=1, arm=-8, old=0.4) if ph >= 2 else None
    ground(A, GROUND)
    A.flush(cv)
    lab, col = ('向晚意不适 驱车登古原' if ph < 2.5 else '夕阳无限好 只是近黄昏'), (JINSE if ph < 2.5 else ZHU)
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '登乐游原 作年不详', t, t - u + P)

def art_s_zhengzhou(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 180), (x + 220, GROUND)], fill=150)
    A.d['wash'].rectangle((420, GROUND - 160, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 160), (680, GROUND - 160), (540, GROUND - 220)], fill=255)
    ground(A, GROUND)
    yishan(A, 760, GROUND, 170, dir=-1, arm=-8, old=0.5)
    A.flush(cv)
    paste(cv, text_img('罢官 · 闲居郑州', SERIF, 48, JINSE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 锦瑟
def art_s_jinse(A, cv, t, u):
    """6-beat set piece: 锦瑟 — the ornate zither has fifty strings for no reason; each string recalls a year of youth;
    this feeling could be a memory — only, even then, it was already lost."""
    ph = u / P
    ground(A, GROUND)
    guqin(A, 540, 1140, 360, 7, t, glow=0.6)
    for k in range(int(clamp(ph / 3) * 50)):
        x = 220 + (k % 25) * 26
        A.d['lazhu'].line((x, 1080 + 60 * (k // 25), x, 1110 + 60 * (k // 25)), fill=180, width=2)
    A.flush(cv)
    if ph < 3:
        lab, col = '锦瑟无端五十弦 一弦一柱思华年', JINSE
    else:
        lab, col = '此情可待成追忆 只是当时已惘然', ZHU
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '锦瑟一诗 千年来众说纷纭', t, t - u + P)

def art_s_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    yishan(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    candle(A, 860, GROUND, 120, 1.0, t, lit=False)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于郑州 · 年四十六', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_cuijue(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 560, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('虚负凌云万丈才\n一生襟抱未曾开', SERIF, 50, INK, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('友人崔珏哭李商隐', SERIF, 46, JINSE, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_s_xiaolidu(A, cv, t, u):
    ground(A, GROUND)
    yishan(A, 400, GROUND, 220, dir=1, arm=-8)
    person(A, 680, GROUND, 220, dir=-1, robe=True, hat='knot', arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('与杜牧并称小李杜', SERIF, 48, JINSE, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '晚唐诗坛双星', t, t - u + P)

def art_s_zhengjian(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    person(A, 280, GROUND, 170, dir=1, robe=True, hat='knot', kneel=True, bow=20, arm=90, layer='ink')
    scroll(A, 560, GROUND - 160, 260, 90, 1.0, layer='wash')
    A.flush(cv)
    paste(cv, text_img('诗家总爱西昆好 独恨无人作郑笺', SERIF, 44, JINSE, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '元好问论诗绝句 叹其诗难解', t, t - u + P)

def art_s_end(A, cv, t, u):
    ground(A, GROUND)
    candle(A, 540, 1260, 300, 0.95, t, lit=False)
    A.flush(cv)
    paste(cv, text_img('没有题目的诗 读了一千多年', SERIF, 48, JINSE, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_s_legacy(A, cv, t, u):
    candle(A, 860, 1430, 100, 0.3, t)

def art_s_title(A, cv, t, u):
    candle(A, 820, 1430, 200, 0.2, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    yishan(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '孤寒'), 48: ('第二回', '党争'), 80: ('第三回', '漂泊'),
            112: ('第四回', '巴山'), 144: ('第五回', '锦瑟')}

CARDS = [
    C(0, 2, 'night', 'num', num='一首无题', line='读了一千多年', art=art_s_hook_untitled),
    C(2, 4, 'works', 'num', num='蜡炬成灰', line='泪始干', art=art_s_hook_candle),
    C(4, 6, 'war', 'num', num='一场党争', line='夹了他一辈子', art=art_s_hook_two),
    C(6, 8, 'fate', 'num', num='夕阳无限好', line='只是近黄昏', art=art_s_hook_sunset),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 孤寒
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=813, main='生于河内', sub='怀州', art=art_s_birth),
    C(22, 26, 'death', 'card', year=822, main='父亲去世', sub='扶柩还乡', note='年份约略', art=art_s_father),
    C(26, 32, 'works', 'card', year=823, main='佣书贩舂', sub='养活全家', note='年份约略', art=art_s_yongshu),
    C(32, 36, 'night', 'card', year=828, main='能为古文', sub='十六岁', art=art_s_guwen),
    C(36, 40, 'court', 'card', year=829, main='令狐楚', sub='爱其才', art=art_s_linghu),
    C(40, 46, 'works', 'card', year=829, main='亲授章奏', sub='文章大进', art=art_s_teach),
    C(46, 48, 'fate', 'card', year=833, main='屡试不第', sub='科场蹉跎', art=art_s_fail),
    # ---- 第二回 党争
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'empire', 'card', year=837, main='进士', sub='二十五岁', art=art_s_jinshi),
    C(54, 58, 'death', 'card', year=837, main='恩师去世', sub='代草遗表', art=art_s_linghudeath),
    C(58, 64, 'war', 'card', year=838, main='娶王氏', sub='背恩之名', art=art_s_wangshi),
    C(64, 68, 'night', 'card', year=838, main='宏词被黜', sub='此人不堪', art=art_s_hongci),
    C(68, 72, 'court', 'card', year=839, main='校书郎', sub='弘农尉', art=art_s_xiaoshu),
    C(72, 76, 'fate', 'card', year=840, main='活狱', sub='请辞', art=art_s_huoyu),
    C(76, 80, 'death', 'card', year=842, main='母亲去世', sub='居丧', art=art_s_mother),
    # ---- 第三回 漂泊
    C(80, 82, 'fate', 'chapter'),
    C(82, 86, 'life', 'card', year=845, main='无题', sub='相见时难', note='作年不详', art=art_s_wuti),
    C(86, 92, 'night', 'card', year=845, main='春蚕蜡炬', sub='到死方尽', note='作年不详', art=art_s_chuncan),
    C(92, 96, 'war', 'card', year=847, main='远走桂林', sub='郑亚幕府', art=art_s_guilin),
    C(96, 100, 'court', 'card', year=849, main='徐州', sub='卢弘止幕', art=art_s_xuzhou),
    C(100, 106, 'death', 'card', year=851, main='妻王氏卒', sub='一双儿女', art=art_s_wife),
    C(106, 112, 'fate', 'card', year=851, main='入蜀', sub='东川幕府', art=art_s_rushu),
    # ---- 第四回 巴山
    C(112, 114, 'night', 'chapter'),
    C(114, 122, 'night', 'yeyu', year=852),
    C(122, 126, 'works', 'card', year=852, main='贾生', sub='问鬼神', note='作年不详', art=art_s_jiasheng),
    C(126, 130, 'life', 'card', year=853, main='心有灵犀', sub='一点通', note='作年不详', art=art_s_lingxi),
    C(130, 134, 'empire', 'card', year=855, main='回长安', sub='盐铁推官', art=art_s_huijing),
    C(134, 140, 'fate', 'card', year=856, main='乐游原', sub='近黄昏', note='作年不详', art=art_s_leyou),
    C(140, 144, 'life', 'card', year=857, main='罢官', sub='闲居郑州', art=art_s_zhengzhou),
    # ---- 第五回 锦瑟
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'night', 'card', year=858, main='锦瑟', sub='思华年', note='作年不详', art=art_s_jinse),
    C(152, 156, 'death', 'card', year=858, main='李商隐去世', sub='年四十六', art=art_s_death),
    C(156, 160, 'fate', 'card', year=858, main='襟抱未开', sub='崔珏之哭', art=art_s_cuijue),
    C(160, 164, 'works', 'card', year=858, main='小李杜', sub='与杜牧', art=art_s_xiaolidu),
    C(164, 168, 'court', 'card', year=1217, main='无人作笺', sub='元好问', art=art_s_zhengjian),
    C(168, 170, 'end', 'card', year=1217, main='无题', sub='千年', art=art_s_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='捌拾叁', col=JINSE, acc=LAZHU, born=813, died=858, age0=812,
    born_lab='813年', died_lab='858年', years_txt='公元813 — 858',
    hook_q='他写尽了深情 · 为什么一辈子郁郁不得志？',
    name_line='李商隐 · 字义山', name='李商隐', seal='义山', title_art=art_s_title,
    q1='深情才子？', q2='背恩之人？',
    end_art=art_s_legacy, end_big='此情可待', end_seal='义山',
    end_l1='他把一生的委屈', end_l2='都写成了没有题目的诗',
    end_brush='心有灵犀', end_ask='李商隐哪句诗戳中了你？评论区聊聊', next='寇准'),
    scenes=dict(chapter=scene_chapter, yeyu=scene_yeyu))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
