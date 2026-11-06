"""千古人物志 · 第柒拾叁集 · 徐霞客 (1587–1641)
Look: 霞光橙 + 山岚青, 竹杖芒鞋 corner borders (a bamboo staff crossed with a sandal strap), endless ridges behind.
Chapter card: 足迹图 — a dotted route across a blank map grows a little further each chapter; in the last chapter a staff stands at its end.
Set pieces: custom 8-beat scene 'tiantai' (游天台山日记 · 开篇), 6-beat 黄山凿冰, 6-beat 湘江遇盗, 6-beat 七星岩,
6-beat 喀斯特, 6-beat 送骨鸡足, 6-beat 溯江纪源.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_hairui as Hr          # engine + helpers (previous episode)
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
from render_zhuxi import book

F.RIPPLE = False
XIAGUANG = (200, 108, 66)           # 霞光橙
SHANLAN = (84, 112, 124)            # 山岚青
S.LAYERS.append(('xiaguang', XIAGUANG, 0.9, 1.0))
S.LAYERS.append(('shanlan', SHANLAN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='游', life='霞', court='山', night='记', war='险', empire='岳', works='石', fate='行', death='骨', end='游')
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
G.THEMES['empire']['sun'] = (XIAGUANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (XIAGUANG, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
_d.line([(40 + i * 30, 1456 + 10 * math.sin(i * 0.9)) for i in range(35)], fill=XIAGUANG + (50,), width=3)   # a winding footpath
for _i in range(0, 35, 3):
    _d.ellipse((40 + _i * 30 - 4, 1452 + 10 * math.sin(_i * 0.9) - 4, 40 + _i * 30 + 4, 1452 + 10 * math.sin(_i * 0.9) + 4), fill=XIAGUANG + (80,))
for _x in (110, 970):               # tall karst pillars at the margins
    _d.polygon([(_x - 40, 1440), (_x - 30, 1280), (_x - 6, 1230), (_x + 18, 1260), (_x + 40, 1440)], fill=SHANLAN + (50,))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (96, 96, 104)}
def draw_background(t, theme):
    """Ridge after ridge, a footpath at the bottom, karst pillars at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 190, 184), (160, 166, 170), MTN_COL.get(theme, (100, 120, 128))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """竹杖芒鞋: a bamboo staff crossed with a sandal in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=SHANLAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=SHANLAN + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.line((cx - 28, cy + 28, cx + 28, cy - 28), fill=(120, 140, 70, 230), width=5)
        for k in range(3):
            d.ellipse((cx - 28 + k * 19 - 3, cy + 28 - k * 19 - 3, cx - 28 + k * 19 + 3, cy + 28 - k * 19 + 3), fill=(90, 110, 50, 230))
        d.ellipse((cx - 12, cy - 22, cx + 22, cy + 18), outline=XIAGUANG + (230,), width=4)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def staff_of(A, x, y, h, dir=1):
    A.d['grass'].line((x + dir * 0.22 * h, y - 0.62 * h, x + dir * 0.3 * h, y), fill=255, width=max(3, int(0.022 * h)))
    for k in range(3):
        yy = y - (0.15 + 0.15 * k) * h
        xx = lerp(x + dir * 0.3 * h, x + dir * 0.22 * h, (0.15 + 0.15 * k) / 0.62)
        A.d['ink'].line((xx - 4, yy, xx + 4, yy), fill=200, width=3)

def xu(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, staff=True, pack=False, **kw):
    """徐霞客: Ming traveller — a 远游冠 soft hat, short robe tucked up, a bamboo staff, a bundle on the back on long journeys."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.polygon([(x - 0.08 * h, y - 0.94 * h), (x + 0.08 * h, y - 0.94 * h), (x + 0.05 * h, y - 1.1 * h), (x - 0.05 * h, y - 1.1 * h)], fill=255)
        A.d['xiaguang'].rectangle((x - 0.085 * h, y - 0.97 * h, x + 0.085 * h, y - 0.94 * h), fill=255)
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.02 * h, y - 0.84 * h), (x + dir * 0.08 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.72 * h)], fill=255)
        if staff and not kneel:
            staff_of(A, x, y, h, dir)
    if pack:
        bx = x - dir * 0.15 * h
        A.d['shanlan'].ellipse((bx - 0.09 * h, y - 0.82 * h, bx + 0.09 * h, y - 0.56 * h), fill=255)
    return hand

def peaks(A, n, base, hmax, layer='mid', fill=160, seed=0, x0=60, x1=1020):
    rnd = random.Random(seed)
    for k in range(n):
        x = lerp(x0, x1, (k + 0.5) / n)
        h = hmax * (0.6 + 0.4 * rnd.random())
        w = (x1 - x0) / n * 0.7
        A.d[layer].polygon([(x - w, base), (x - 0.15 * w, base - h), (x + 0.12 * w, base - 0.96 * h), (x + w, base)], fill=fill)

def route_map(A, cx, cy, s, frac, t):
    A.d['wash'].rectangle((cx - s, cy - 0.7 * s, cx + s, cy + 0.7 * s), fill=255)
    A.d['ink'].rectangle((cx - s, cy - 0.7 * s, cx + s, cy + 0.7 * s), outline=255, width=4)
    A.d['shanlan'].line([(cx - 0.9 * s, cy - 0.1 * s), (cx - 0.3 * s, cy + 0.05 * s), (cx + 0.3 * s, cy - 0.05 * s), (cx + 0.9 * s, cy + 0.1 * s)], fill=150, width=6)
    pts = [(cx + 0.8 * s, cy + 0.0 * s), (cx + 0.6 * s, cy - 0.3 * s), (cx + 0.3 * s, cy - 0.15 * s), (cx + 0.5 * s, cy + 0.2 * s),
           (cx + 0.1 * s, cy + 0.35 * s), (cx - 0.2 * s, cy + 0.15 * s), (cx - 0.4 * s, cy + 0.45 * s), (cx - 0.75 * s, cy + 0.3 * s)]
    n = frac * (len(pts) - 1)
    for i in range(int(n)):
        for j in range(6):
            q = j / 6
            x = lerp(pts[i][0], pts[i + 1][0], q); y = lerp(pts[i][1], pts[i + 1][1], q)
            A.d['xiaguang'].ellipse((x - 4, y - 4, x + 4, y + 4), fill=255)
    i = int(n)
    if i < len(pts) - 1:
        q = n - i
        x = lerp(pts[i][0], pts[i + 1][0], q); y = lerp(pts[i][1], pts[i + 1][1], q)
    else:
        x, y = pts[-1]
    A.d['red'].ellipse((x - 9, y - 9, x + 9, y + 9), fill=255)
    return x, y

def waterfall(A, cx, top, w, h, t):
    A.d['mid'].rectangle((cx - w - 120, top - 40, cx - w, top + h), fill=180)
    A.d['mid'].rectangle((cx + w, top - 40, cx + w + 120, top + h), fill=180)
    A.d['ocean'].rectangle((cx - w, top, cx + w, top + h), fill=200)
    for k in range(10):
        x = cx - w + (k + 0.5) * 2 * w / 10
        q = (t * 1.5 + k * 0.13) % 1
        A.d['wash'].line((x, top + q * h * 0.7, x, top + q * h * 0.7 + 60), fill=255, width=4)
    for k in range(8):
        a = k * 0.8 + t
        A.d['wash'].ellipse((cx + 1.4 * w * math.cos(a) - 30, top + h - 20 + 14 * math.sin(a) - 16, cx + 1.4 * w * math.cos(a) + 30, top + h - 20 + 14 * math.sin(a) + 16), fill=180)

def cave(A, cx, cy, w, h, t, light=1.0):
    A.d['ink'].rectangle((cx - w, cy - h, cx + w, cy + h), fill=200)
    A.d['mid'].ellipse((cx - 0.8 * w, cy - 0.8 * h, cx + 0.8 * w, cy + 0.8 * h), fill=int(120 + 100 * light))
    rnd = random.Random(7)
    for k in range(9):
        x = cx - 0.7 * w + k * 0.175 * w
        L_ = (0.2 + 0.4 * rnd.random()) * h
        A.d['ink'].polygon([(x - 14, cy - 0.8 * h), (x + 14, cy - 0.8 * h), (x, cy - 0.8 * h + L_)], fill=220)
        A.d['ink'].polygon([(x - 14 + 30, cy + 0.8 * h), (x + 14 + 30, cy + 0.8 * h), (x + 30, cy + 0.8 * h - 0.6 * L_)], fill=200)

# ================================================================ chapter card
CH = {16: (0.0, 0.2), 48: (0.2, 0.4), 80: (0.4, 0.65), 112: (0.65, 0.9), 144: (0.9, 1.0)}
def art_route_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (0.2, 0.4))
    q = ease_out(u / (1.2 * P))
    x, y = route_map(A, 540, 1060, 320, lerp(a, b, q), t)
    if kb == 144 and q > 0.6:
        staff_of(A, x - 30, y + 10, 180, 1)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_route_chapter)
    ink_in(cv, text_img(no, SERIF, 56, XIAGUANG, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_x_hook_road(A, cv, t, u):
    route_map(A, 540, 1060, 320, clamp(u / (1.2 * P)), t)

def art_x_hook_date(A, cv, t, u):
    ground(A, GROUND)
    book(A, 540, GROUND - 60, 260, 0, open_=1.0)
    A.flush(cv)
    stamp(cv, seal('五月十九', 60, ZHU), 540, 1080, t, t - u + 0.4)

def art_x_hook_staff(A, cv, t, u):
    ground(A, GROUND)
    staff_of(A, 380, GROUND, 600, 1)
    A.d['dune'].ellipse((580, GROUND - 40, 700, GROUND), fill=255)
    A.d['dune'].ellipse((720, GROUND - 40, 840, GROUND), fill=255)

def art_x_hook_bones(A, cv, t, u):
    peaks(A, 4, GROUND, 360, seed=3)
    ground(A, GROUND)
    xu(A, lerp(200, 600, ease_out(u / (1.2 * P))), GROUND, 220, dir=1, ph=t * 3, arm=-8, pack=True)
    A.d['wash'].ellipse((lerp(200, 600, ease_out(u / (1.2 * P))) - 60, GROUND - 190, lerp(200, 600, ease_out(u / (1.2 * P))) - 20, GROUND - 150), fill=255)

# ================================================================ 第一回 志在四方
def art_x_birth(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=140)
    river(A, 1250, t, rows=2, amp=3)
    A.d['wash'].rectangle((360, 1080, 720, 1240), fill=255)
    A.d['ink'].polygon([(340, 1080), (740, 1080), (540, 1000)], fill=255)
    A.flush(cv)
    paste(cv, text_img('南直隶江阴 · 书香世家', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('江阴', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '父徐有勉 不愿为官', t, t - u + P)

def art_x_books(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='shanlan')
    person(A, 280, GROUND, 140, dir=1, robe=True, hat='none', kneel=True, arm=100, layer='ink')
    A.d['wash'].rectangle((440, GROUND - 200, 680, GROUND - 80), fill=255)
    A.d['ink'].line([(470, GROUND - 120), (520, GROUND - 170), (600, GROUND - 130), (650, GROUND - 160)], fill=255, width=3)
    A.flush(cv)
    paste(cv, text_img('不应科举 · 专读舆地图经之书', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '少应童子试不第 年份约略', t, t - u + P)

def art_x_father(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, layer='ink')
    person(A, 880, GROUND, 140, dir=-1, robe=True, hat='knot', kneel=True, bow=30, layer='shanlan')
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('父徐有勉病故', SERIF, 48, XIAGUANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_x_mother(A, cv, t, u):
    ground(A, GROUND)
    person(A, 680, GROUND, 210, dir=-1, robe=True, hat='knot', female=True, arm=lerp(40, 110, ease_out(u / 0.8)), layer='ink')
    xu(A, 400, GROUND, 200, dir=1, bow=15, arm=60, staff=False)
    A.d['xiaguang'].rectangle((560, GROUND - 160, 620, GROUND - 130), fill=255)
    A.flush(cv)
    type_in(cv, text_img('身为男子 当志在四方', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.6)
    note_in(cv, '母王孺人亲手为其缝制远游冠', t, t - u + P)

def art_x_taihu(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=160)
    waves(A, 1170, t, rows=2, amp=4)
    A.d['mid'].ellipse((640, 1100, 960, 1200), fill=170)
    boat(A, lerp(150, 520, ease_out(u / (3 * P))), 1210, 90, t)
    A.flush(cv)
    paste(cv, text_img('泛舟太湖 · 登东西洞庭山', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('太湖', 56), 860, 1020, t, t - u + P, rot=6)

def scene_tiantai(cv, t, c, k):
    """8-beat custom scene: 游天台山日记 — the first entry of the travel diary: leaving 宁海's west gate, clouds clear, the sun bright;
    man's mood and the mountain light are both joyful. The diary page fills while he climbs."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    clear = clamp(ph / 2)
    peaks(A, 3, GROUND, 520, layer='mid', fill=int(lerp(120, 170, clear)), seed=13)
    for k in range(4):
        x = 140 + ((k * 260 + t * 30) % 1000)
        A.d['wash'].ellipse((x - 120, 900 + 40 * k - 30, x + 120, 900 + 40 * k + 30), fill=int(200 * (1 - clear)))
    ground(A, GROUND)
    xu(A, lerp(120, 700, ease_out(ph / 8)), GROUND - lerp(0, 0, 1), 200, dir=1, ph=t * 3, arm=-8, pack=True)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '游天台山日记', BRUSH, 130, INK, W / 2, 440, t, s0, stagger=0.06, seed=73)
    fx.flush(cv)
    lines = ['癸丑之三月晦', '自宁海出西门', '云散日朗', '人意山光 俱有喜态']
    for i, line in enumerate(lines):
        start = s0 + (0.4 + i * 1.6) * P
        if t >= start:
            paste(cv, text_img(line, SERIF, 44, ZHU if i == 3 else XIAGUANG, 'Black', bleed=False, spacing=6), W / 2, 590 + i * 64, 1, clamp((t - start) / 0.4))
    note_in(cv, '游记由此开篇 此后三十年从未停笔', t, s0 + 3 * P)

def art_x_joy(A, cv, t, u):
    peaks(A, 3, GROUND, 460, layer='shanlan', fill=170, seed=21)
    ground(A, GROUND)
    xu(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 140, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('这一天 后来成了中国旅游日', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 名山
def art_x_huangshan(A, cv, t, u):
    """6-beat set piece: 黄山凿冰 — in deep snow the stone steps are sheathed in ice; he chips footholds with his staff, step by step, to the top."""
    ph = u / P
    A.d['mid'].polygon([(120, GROUND), (420, 900), (520, 950), (620, 860), (960, GROUND)], fill=200)
    for k in range(10):
        x = lerp(220, 600, k / 9); y = lerp(GROUND - 20, 900, k / 9)
        A.d['wash'].rectangle((x - 30, y - 8, x + 30, y + 8), fill=255)
    n = int(clamp(ph / 5) * 10)
    for k in range(n):
        x = lerp(220, 600, k / 9); y = lerp(GROUND - 20, 900, k / 9)
        A.d['ink'].line((x - 14, y - 4, x + 14, y - 4), fill=255, width=4)
    for i in range(40):
        q = (t * 0.6 + i / 40) % 1
        x = 80 + (i * 61) % 920
        A.d['wash'].ellipse((x - 4, lerp(600, 1400, q) - 4, x + 4, lerp(600, 1400, q) + 4), fill=230)
    k = min(9, n)
    xu(A, lerp(220, 600, k / 9) - 30, lerp(GROUND - 20, 900, k / 9) - 6, 150, dir=1, bow=20, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 6)), pack=True)
    ground(A, GROUND)
    A.flush(cv)
    lab = '大雪封山 · 石阶尽成坚冰' if ph < 2 else ('以杖凿冰 凿一孔 进一步' if ph < 4.5 else '终至绝顶')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4.5 else XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 700, 1, 1)
    stamp(cv, seal('黄山', 56), 860, 1440, t, t - u + 0.4, rot=6)

def art_x_wuyi(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 90, GROUND), (x - 40, GROUND - 420), (x + 40, GROUND - 440), (x + 90, GROUND)], fill=160)
    A.d['ocean'].line([(60, GROUND - 30), (300, GROUND - 60), (540, GROUND - 30), (800, GROUND - 60), (1020, GROUND - 30)], fill=200, width=18)
    xr = lerp(100, 820, (t * 0.05) % 1)
    A.d['dune'].rectangle((xr - 60, GROUND - 52, xr + 60, GROUND - 40), fill=255)
    xu(A, xr, GROUND - 52, 90, dir=1, arm=-8, staff=False)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('同年游武夷 · 竹筏过九曲溪', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_tiandu(A, cv, t, u):
    A.d['mid'].polygon([(100, GROUND), (320, 900), (400, 960), (480, GROUND)], fill=200)
    A.d['shanlan'].polygon([(560, GROUND), (760, 820), (840, 900), (980, GROUND)], fill=200)
    for k in range(5):
        x = 120 + ((k * 230 + t * 20) % 900)
        A.d['wash'].ellipse((x - 140, 1180 - 26, x + 140, 1180 + 26), fill=200)
    xu(A, 760, 830, 90, dir=1, arm=140)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('再上黄山 · 登天都 莲花二峰', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '相传有 登黄山天下无山 之叹 原文未见', t, t - u + P)

def art_x_three(A, cv, t, u):
    peaks(A, 3, GROUND, 480, layer='mid', fill=170, seed=5)
    ground(A, GROUND)
    xu(A, lerp(100, 900, (t * 0.06) % 1), GROUND, 150, dir=1, ph=t * 4, arm=-8, pack=True)
    A.flush(cv)
    for i, nm in enumerate(['嵩山', '华山', '武当']):
        stamp(cv, seal(nm, 50), 260 + i * 280, 1000, t, t - u + (0.5 + i * 0.6) * P, rot=-4 + 4 * i)
    paste(cv, text_img('一年之中 遍游嵩山 华山 武当', SERIF, 44, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_withmother(A, cv, t, u):
    cave(A, 760, 1180, 200, 160, t, light=0.6)
    ground(A, GROUND)
    person(A, 420, GROUND, 170, dir=1, robe=True, hat='knot', female=True, bow=20, arm=-8, ph=t * 2, layer='mid')
    xu(A, 280, GROUND, 190, dir=1, arm=80, ph=t * 2)
    A.flush(cv)
    paste(cv, text_img('母亲八十 · 陪她同游善卷洞', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '母亲坚持走在前面 以示自己尚健', t, t - u + P)

def art_x_motherdeath(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, female=True, layer='ink')
    xu(A, 880, GROUND, 160, dir=-1, kneel=True, bow=30)
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('母亲病逝 · 守丧数年不出', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_north(A, cv, t, u):
    peaks(A, 4, GROUND, 420, layer='shanlan', fill=150, seed=9)
    for i in range(40):
        q = (t * 0.4 + i / 40) % 1
        x = 80 + (i * 61) % 920
        A.d['wash'].ellipse((x - 3, lerp(600, 1400, q) - 3, x + 3, lerp(600, 1400, q) + 3), fill=200)
    ground(A, GROUND)
    xu(A, 540, GROUND, 180, dir=1, arm=-8, pack=True)
    A.flush(cv)
    paste(cv, text_img('北上 · 游五台山 恒山', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('北岳', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第三回 万里遐征
def art_x_depart(A, cv, t, u):
    ground(A, GROUND)
    xu(A, lerp(100, 520, ease_out(u / (3 * P))), GROUND, 190, dir=1, ph=t * 3, arm=-8, pack=True, old=0.3)
    person(A, lerp(-40, 380, ease_out(u / (3 * P))), GROUND, 170, dir=1, robe=True, hat='none', ph=t * 3 + 1, arm=-8, load=True, layer='qiuhuang')
    A.flush(cv)
    paste(cv, text_img('五十岁出发 · 万里遐征西南', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '同行僧人静闻 欲将血书法华经供于鸡足山', t, t - u + P)

def art_x_robbers(A, cv, t, u):
    """6-beat set piece: 湘江遇盗 — anchored at night on the 湘江, bandits board with torches; he leaps into the river; money and belongings are gone;
    静闻 stays aboard to guard the sutra and is wounded."""
    ph = u / P
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=110)
    river(A, 1170, t, rows=3, amp=4)
    boat(A, 540, 1180, 130, t, sail=False)
    if ph > 1:
        flames(A, 540, 1150, 260, 120 * clamp((ph - 1) / 1), t, n=3, seed=1637, smoke=True)
        for j in range(3):
            person(A, 420 + j * 100, 1150, 120, dir=1 if j % 2 else -1, robe=False, hat='knot', sword=60, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 6 + j)), layer='ink')
    if ph > 2.5:
        q = clamp((ph - 2.5) / 1)
        xu(A, lerp(700, 860, q), lerp(1150, 1260, q), 120, dir=1, staff=False, fall=lerp(0, 60, q), arm=150)
    A.flush(cv)
    lab = '夜泊湘江' if ph < 1 else ('群盗持火登舟' if ph < 2.5 else ('跃入江中 仅以身免' if ph < 4.5 else '行李资财尽失'))
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 1 else XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('静闻守护经卷 身受刀伤', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.5) / 0.4))

def art_x_jingwen(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, hat='none', layer='qiuhuang')
    xu(A, 880, GROUND, 160, dir=-1, kneel=True, bow=30, old=0.3)
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('静闻病逝南宁 · 临终托以遗骨', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '求葬鸡足山', t, t - u + P)

def art_x_qixing(A, cv, t, u):
    """6-beat set piece: 七星岩 — in 桂林 he goes deep into the caves with a torch, measuring and recording each hall and passage."""
    ph = u / P
    light = 0.4 + 0.6 * clamp(ph / 2)
    cave(A, 540, 1060, 440, 320, t, light=light)
    xu(A, lerp(200, 640, ease_out(ph / 5)), 1300, 150, dir=1, ph=t * 3, arm=120, staff=False)
    tx = lerp(200, 640, ease_out(ph / 5)) + 40
    flames(A, tx, 1130, 30, 40, t, n=1, seed=73, smoke=False)
    ground(A, GROUND)
    A.flush(cv)
    n = min(15, int(clamp(ph / 5) * 15) + 1)
    lab = f'桂林七星岩 · 已记洞穴{cn_num(n)}处' if ph < 5 else '一洞一记 方位 深浅 形态'
    paste(cv, text_img(lab, SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 680, 1, 1)
    note_in(cv, '游记所载 广西 贵州 云南岩洞数以百计', t, t - u + 2 * P)

def art_x_baishui(A, cv, t, u):
    waterfall(A, 540, 900, 180, 380, t)
    ground(A, GROUND)
    xu(A, 160, GROUND, 160, dir=1, arm=60, pack=True, old=0.4)
    A.flush(cv)
    paste(cv, text_img('捣珠崩玉 飞沫反涌 如烟雾腾空', SERIF, 44, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '贵州白水河瀑布 即今黄果树瀑布', t, t - u + P)

def art_x_karst(A, cv, t, u):
    ph = u / P
    for k in range(9):
        x = 100 + k * 110
        h = 300 + 120 * math.sin(k * 1.7)
        A.d['shanlan' if k % 2 else 'mid'].polygon([(x - 46, GROUND), (x - 36, GROUND - h + 40), (x - 10, GROUND - h), (x + 20, GROUND - h + 30), (x + 46, GROUND)], fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('系统记述石灰岩地貌', SERIF, 48, XIAGUANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    if ph >= 2:
        paste(cv, text_img('峰林 溶洞 天坑 伏流', SERIF, 44, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - 2) / 0.4))
    note_in(cv, '常被认为早于欧洲同类考察百余年', t, t - u + 2 * P)

# ================================================================ 第四回 鸡足山
def art_x_jizu(A, cv, t, u):
    """6-beat set piece: 送骨鸡足 — he carries 静闻's bones across 广西 贵州 into 云南, and buries them at 鸡足山 as promised."""
    ph = u / P
    if ph < 3:
        peaks(A, 4, GROUND, 400, layer='mid', fill=160, seed=int(ph) + 30)
        ground(A, GROUND)
        x = lerp(120, 860, (ph / 3))
        xu(A, x, GROUND, 180, dir=1, ph=t * 3, arm=-8, pack=True, old=0.4)
        A.d['wash'].ellipse((x - 50, GROUND - 160, x - 14, GROUND - 124), fill=255)
        lab = '背负遗骨 跋涉数千里'
    else:
        A.d['mid'].polygon([(200, GROUND), (420, 900), (540, 820), (660, 900), (880, GROUND)], fill=180)
        A.d['qiuhuang'].rectangle((500, 780, 580, 830), fill=255)
        A.d['ink'].polygon([(490, 780), (590, 780), (540, 750)], fill=255)
        A.d['mid'].chord((460, GROUND - 80, 620, GROUND + 80), 180, 360, fill=230)
        ground(A, GROUND)
        xu(A, 360, GROUND, 170, dir=1, kneel=True, bow=30, old=0.4)
        lab = '葬于鸡足山 · 了其遗愿'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3 else XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 700, 1, 1)
    stamp(cv, seal('鸡足', 56), 860, 1020, t, t - u + 3 * P, rot=6)
    if ph >= 4.5:
        paste(cv, text_img('一诺 走了三年', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.5) / 0.4))

def art_x_volcano(A, cv, t, u):
    A.d['mid'].polygon([(160, GROUND), (420, 960), (660, 960), (920, GROUND)], fill=180)
    A.d['ink'].rectangle((420, 950, 660, 970), fill=255)
    for k in range(5):
        q = (t * 0.3 + k / 5) % 1
        A.d['wash'].ellipse((540 - 40 - 50 * q, 940 - 220 * q - 26, 540 + 40 + 50 * q, 940 - 220 * q + 26), fill=int(160 * (1 - q)))
    ground(A, GROUND)
    xu(A, 180, GROUND, 160, dir=1, arm=110, pack=True, old=0.4)
    A.flush(cv)
    paste(cv, text_img('腾冲打鹰山 · 记火山遗迹', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '记山顶石皆赭赤 轻浮如蜂房', t, t - u + P)

def art_x_mu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='shanlan')
    ground(A, GROUND)
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='helmet', arm=lerp(-8, 80, ease_out(u / 0.6)), layer='qiuhuang')
    xu(A, 360, GROUND, 180, dir=1, bow=15, arm=60, old=0.4)
    A.flush(cv)
    paste(cv, text_img('丽江土司木增 · 礼请其修鸡足山志', SERIF, 44, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_jiangyuan(A, cv, t, u):
    """6-beat set piece: 溯江纪源 — the classics say the 长江 rises from the 岷山; following the rivers, he argues the 金沙江 is the true source."""
    ph = u / P
    A.d['shanlan'].line([(160, 820), (300, 960), (420, 1100), (540, 1220), (700, 1300), (920, 1340)], fill=230, width=26)
    A.d['ocean'].line([(800, 760), (720, 900), (640, 1040), (580, 1160), (540, 1220)], fill=200, width=14)
    if ph >= 2:
        A.d['red'].line([(160, 820), (300, 960), (420, 1100), (540, 1220)], fill=230, width=8)
    A.flush(cv)
    paste(cv, text_img('金沙江', SERIF, 40, XIAGUANG, 'Black', bleed=False, spacing=4), 230, 1000, 1, 1)
    paste(cv, text_img('岷江', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), 840, 900, 1, 1)
    lab, col = ('禹贡旧说 岷山导江', XIAGUANG) if ph < 2 else ('推江源者 必当以金沙为首', ZHU)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 700, 1, 1)
    note_in(cv, '见其所著溯江纪源', t, t - u + 2 * P)

def art_x_carried(A, cv, t, u):
    peaks(A, 4, GROUND, 380, layer='mid', fill=160, seed=44)
    ground(A, GROUND)
    x = lerp(900, 200, (t * 0.04) % 1)
    A.d['guanmu'].rectangle((x - 90, GROUND - 150, x + 90, GROUND - 90), fill=255)
    A.d['ink'].line((x - 200, GROUND - 130, x + 200, GROUND - 130), fill=255, width=6)
    xu(A, x, GROUND - 150, 70, dir=-1, kneel=True, staff=False, old=0.8)
    for j in (-1, 1):
        person(A, x + j * 170, GROUND, 130, dir=-1, robe=False, hat='knot', ph=t * 4 + j, arm=100, layer='ink')
    A.flush(cv)
    paste(cv, text_img('双足俱废 · 木增派人抬送回乡', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '一路一百五十余日', t, t - u + P)

def art_x_sickbed(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((200, GROUND - 90, 640, GROUND - 60), fill=230)
    xu(A, 360, GROUND - 90, 170, dir=1, kneel=True, bow=20, arm=100, old=0.9)
    lamp(A, 760, GROUND - 74, 30, t, glow=0.9)
    for i in range(min(12, int(u / (0.3 * P)) + 1)):
        A.d['wash'].rectangle((660 + (i % 4) * 50, GROUND - 40 - (i // 4) * 30, 700 + (i % 4) * 50, GROUND - 14 - (i // 4) * 30), fill=255)
    A.flush(cv)
    paste(cv, text_img('卧病江阴 · 整理游记手稿', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 游记
def art_x_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    xu(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, staff=False)
    staff_of(A, 800, GROUND, 300, 1)
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于江阴 · 年五十五', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '吾以老布衣 孤筇双屦 与三人而为四 死不恨矣', t, t - u + P)

def art_x_manuscript(A, cv, t, u):
    ground(A, GROUND)
    flames(A, 800, GROUND, 200, 140 * clamp(1 - u / (2 * P)), t, n=3, seed=1642, smoke=True)
    desk(A, 420, GROUND, 360, layer='shanlan')
    person(A, 200, GROUND, 170, dir=1, robe=True, hat='knot', kneel=True, arm=100, layer='ink')
    slips(A, 360, GROUND - 74, 10, 70, layer='xiaguang')
    A.flush(cv)
    paste(cv, text_img('手稿屡遭兵火 · 友人季梦良等收拾整理', SERIF, 42, XIAGUANG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_qian(A, cv, t, u):
    ground(A, GROUND)
    book(A, 540, GROUND - 60, 260, 0, open_=1.0)
    A.flush(cv)
    type_in(cv, text_img('世间真文字 大文字 奇文字', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.6)
    stamp(cv, seal('钱谦益', 50, INK), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '钱谦益又称其为千古奇人', t, t - u + P)

def art_x_print(A, cv, t, u):
    ground(A, GROUND)
    for i in range(min(10, int(u / (0.3 * P)) + 1)):
        book(A, 160 + i * 84, GROUND, 70, 140 + 20 * (i % 3), layer='xiaguang' if i % 2 else 'shanlan')
    A.flush(cv)
    paste(cv, text_img('徐氏后人刊行游记', SERIF, 48, XIAGUANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '此前百余年间 只以抄本流传', t, t - u + P)

def art_x_day(A, cv, t, u):
    peaks(A, 3, GROUND, 460, layer='shanlan', fill=160, seed=21)
    ground(A, GROUND)
    for j in range(6):
        person(A, lerp(-100, 1100, ((t * 0.05 + j / 6) % 1)), GROUND, 110 + 20 * (j % 2), dir=1, robe=False, hat='none', ph=t * 4 + j, arm=-8, layer='ink' if j % 2 else 'xiaguang')
    A.flush(cv)
    paste(cv, text_img('定每年五月十九日为中国旅游日', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '取游天台山日记开篇之日', t, t - u + P)

def art_x_staffs(A, cv, t, u):
    ground(A, GROUND)
    staff_of(A, 380, GROUND, 600, 1)
    A.d['dune'].ellipse((580, GROUND - 40, 700, GROUND), fill=255)
    A.d['dune'].ellipse((720, GROUND - 40, 840, GROUND), fill=255)
    A.flush(cv)
    paste(cv, text_img('一根竹杖 一双草鞋 三十余年', SERIF, 46, XIAGUANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_x_mountains(A, cv, t, u):
    peaks(A, 6, GROUND, 520, layer='mid', fill=150, seed=99)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('他写下的山河 仍在原处', SERIF, 48, XIAGUANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_x_legacy(A, cv, t, u):
    staff_of(A, 820, 1440, 160, 1)

def art_x_title(A, cv, t, u):
    peaks(A, 3, 1440, 260, layer='shanlan', fill=150, seed=2, x0=600, x1=1020)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    xu(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))), pack=True)

# ================================================================ script
CHAPTERS = {16: ('第一回', '志在四方'), 48: ('第二回', '名山'), 80: ('第三回', '万里遐征'),
            112: ('第四回', '鸡足山'), 144: ('第五回', '游记')}

CARDS = [
    C(0, 2, 'life', 'num', num='三十余年', line='走遍大半个中国', art=art_x_hook_road),
    C(2, 4, 'empire', 'num', num='五月十九', line='成了中国旅游日', art=art_x_hook_date),
    C(4, 6, 'works', 'num', num='孤筇双屦', line='一杖一鞋走天下', art=art_x_hook_staff),
    C(6, 8, 'death', 'num', num='一副遗骨', line='背了几千里', art=art_x_hook_bones),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 志在四方
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1587, main='生于江阴', sub='书香世家', art=art_x_birth),
    C(22, 26, 'works', 'card', year=1601, main='无意科举', sub='舆地之书', art=art_x_books),
    C(26, 30, 'death', 'card', year=1604, main='父亲去世', sub='十八岁', art=art_x_father),
    C(30, 34, 'court', 'card', year=1607, main='母亲赠冠', sub='志在四方', art=art_x_mother),
    C(34, 38, 'life', 'card', year=1607, main='初游太湖', sub='第一次远行', art=art_x_taihu),
    C(38, 46, 'night', 'tiantai', year=1613),
    C(46, 48, 'empire', 'card', year=1613, main='人意山光', sub='俱有喜态', art=art_x_joy),
    # ---- 第二回 名山
    C(48, 50, 'empire', 'chapter'),
    C(50, 56, 'war', 'card', year=1616, main='黄山凿冰', sub='以杖开路', art=art_x_huangshan),
    C(56, 60, 'works', 'card', year=1616, main='武夷九曲', sub='竹筏', art=art_x_wuyi),
    C(60, 64, 'empire', 'card', year=1618, main='再登黄山', sub='天都莲花', art=art_x_tiandu),
    C(64, 68, 'court', 'card', year=1623, main='一年三山', sub='嵩华武当', art=art_x_three),
    C(68, 72, 'life', 'card', year=1624, main='侍母出游', sub='母亲八十', art=art_x_withmother),
    C(72, 76, 'death', 'card', year=1625, main='母亲去世', sub='守丧', art=art_x_motherdeath),
    C(76, 80, 'night', 'card', year=1633, main='五台恒山', sub='北上', art=art_x_north),
    # ---- 第三回 万里遐征
    C(80, 82, 'fate', 'chapter'),
    C(82, 86, 'empire', 'card', year=1636, main='万里遐征', sub='五十岁', art=art_x_depart),
    C(86, 92, 'war', 'card', year=1637, main='湘江遇盗', sub='资财尽失', art=art_x_robbers),
    C(92, 96, 'death', 'card', year=1637, main='静闻之死', sub='托以遗骨', art=art_x_jingwen),
    C(96, 102, 'night', 'card', year=1637, main='七星岩', sub='一洞一记', art=art_x_qixing),
    C(102, 106, 'life', 'card', year=1638, main='白水河', sub='飞瀑', art=art_x_baishui),
    C(106, 112, 'works', 'card', year=1638, main='石灰岩地貌', sub='峰林溶洞', art=art_x_karst),
    # ---- 第四回 鸡足山
    C(112, 114, 'death', 'chapter'),
    C(114, 120, 'death', 'card', year=1639, main='送骨鸡足', sub='一诺千里', art=art_x_jizu),
    C(120, 124, 'war', 'card', year=1639, main='腾冲火山', sub='打鹰山', art=art_x_volcano),
    C(124, 128, 'court', 'card', year=1639, main='丽江木增', sub='修鸡足山志', art=art_x_mu),
    C(128, 134, 'empire', 'card', year=1640, main='溯江纪源', sub='金沙为首', art=art_x_jiangyuan),
    C(134, 138, 'fate', 'card', year=1640, main='抬送回乡', sub='双足俱废', art=art_x_carried),
    C(138, 144, 'night', 'card', year=1640, main='病榻整稿', sub='江阴', art=art_x_sickbed),
    # ---- 第五回 游记
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=1641, main='徐霞客去世', sub='年五十五', art=art_x_death),
    C(150, 154, 'fate', 'card', year=1642, main='手稿劫余', sub='友人整理', art=art_x_manuscript),
    C(154, 158, 'works', 'card', year=1650, main='奇文字', sub='钱谦益之评', note='评语年份约略', art=art_x_qian),
    C(158, 162, 'empire', 'card', year=1776, main='刊刻行世', sub='徐氏后人', art=art_x_print),
    C(162, 166, 'life', 'card', year=2011, main='中国旅游日', sub='五月十九日', art=art_x_day),
    C(166, 168, 'court', 'card', year=2011, main='孤筇双屦', sub='三十余年', art=art_x_staffs),
    C(168, 170, 'end', 'card', year=2011, main='山河', sub='仍在原处', art=art_x_mountains),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='柒拾叁', col=XIAGUANG, acc=SHANLAN, born=1587, died=1641, age0=1586,
    born_lab='1587年', died_lab='1641年', years_txt='公元1587 — 1641',
    hook_q='他不考功名不做官 · 为什么一辈子都在走路？',
    name_line='徐霞客 · 名弘祖', name='徐霞客', seal='霞客', title_art=art_x_title,
    q1='千古奇人？', q2='不务正业？',
    end_art=art_x_legacy, end_big='孤筇双屦', end_seal='霞客',
    end_l1='他一生没做过一天官', end_l2='却替后人走遍了山河',
    end_brush='志在四方', end_ask='徐霞客走过的山 你最想去哪一座？评论区聊聊', next='曾国藩'),
    scenes=dict(chapter=scene_chapter, tiantai=scene_tiantai))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
