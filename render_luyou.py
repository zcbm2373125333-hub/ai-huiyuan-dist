"""千古人物志 · 第捌拾陆集 · 陆游 (1125–1210)
Look: 沈园苔绿 + 钗头红, 梅枝 corner borders, 山阴 hills and the 镜湖 behind.
Chapter card: 咏梅 — a plum branch in snow; its blossoms open and then fall chapter by chapter; in the last chapter the petals lie in the mud,
still faintly red: 零落成泥碾作尘 只有香如故.
Set pieces: custom 8-beat scene 'tiema' (十一月四日风雨大作 · 铁马冰河入梦来), 6-beat 舟中出生, 6-beat 沈园, 6-beat 南郑,
6-beat 书愤, 6-beat 示儿.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_liuyong as Ly         # engine + helpers (previous episode)
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
from render_quyuan import river
from render_simayi import emperor
from render_sunwu import army, banner
from render_songtaizu import tent
from render_yangguifei import yu
from render_lishangyin import candle, rain
from render_jianzhen import tangship
from render_zuozongtang import willow

F.RIPPLE = False
SHENYUAN = (88, 106, 70)            # 沈园苔绿
CHAITOU = (198, 88, 98)             # 钗头红
S.LAYERS.append(('shenyuan', SHENYUAN, 0.9, 1.0))
S.LAYERS.append(('chaitou', CHAITOU, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='陆', life='游', court='宋', night='梦', war='剑', empire='诗', works='梅', fate='放', death='示', end='游')
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
G.THEMES['empire']['sun'] = (SHENYUAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (CHAITOU, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # 镜湖
    _d.line([(40 + i * 30, 1456 + _k * 14 + 3 * math.sin(i * 0.6 + _k)) for i in range(35)], fill=(90, 110, 120, 46 - _k * 10), width=3)
for _x, _s in ((110, 1), (970, -1)):  # plum twigs at the margins
    _d.line([(_x, 1446), (_x + _s * 10, 1380), (_x + _s * 34, 1330)], fill=(80, 60, 50, 80), width=4)
    for _j in range(4):
        _d.ellipse((_x + _s * (4 + _j * 9) - 7, 1390 - _j * 18 - 7, _x + _s * (4 + _j * 9) + 7, 1390 - _j * 18 + 7), fill=CHAITOU + (80,))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (96, 100, 100)}
def draw_background(t, theme):
    """山阴: soft hills over the 镜湖, plum twigs at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(192, 194, 188), (160, 168, 154), MTN_COL.get(theme, (112, 124, 104))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """梅枝: a plum twig with two blossoms in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=SHENYUAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=SHENYUAN + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.line((cx - 26 * sx, cy + 20 * sy, cx + 26 * sx, cy - 20 * sy), fill=(70, 50, 40, 230), width=4)
        for k in (-1, 1):
            px, py = cx + k * 12 * sx, cy - k * 9 * sy
            for a in range(5):
                ang = a * 2 * math.pi / 5
                d.ellipse((px + 6 * math.cos(ang) - 4, py + 6 * math.sin(ang) - 4, px + 6 * math.cos(ang) + 4, py + 6 * math.sin(ang) + 4), fill=CHAITOU + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def lu(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, armour=False, **kw):
    """陆游: a Southern Song scholar — square 东坡巾 cap, a long beard (white when old), a sword at his side on the frontier."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else ('none' if up else 'knot'), layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up and not armour:
        d.rectangle((x - 0.07 * h, y - 1.1 * h, x + 0.07 * h, y - 0.93 * h), fill=255)
        d.polygon([(x - 0.07 * h, y - 1.1 * h), (x + 0.07 * h, y - 1.1 * h), (x, y - 1.15 * h)], fill=255)
    if up:
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.0 * h, y - 0.85 * h), (x + dir * 0.09 * h, y - 0.85 * h), (x + dir * 0.05 * h, y - 0.6 * h), (x + dir * 0.0 * h, y - 0.66 * h)], fill=255)
        A.d['shenyuan'].rectangle((x - 0.09 * h, y - 0.56 * h, x + 0.09 * h, y - 0.52 * h), fill=255)
        if armour:
            A.d['ink'].line((x - dir * 0.1 * h, y - 0.5 * h, x - dir * 0.3 * h, y - 0.1 * h), fill=255, width=max(3, int(0.02 * h)))
    return hand

def plum(A, cx, base, h, bloom, fall=0.0, t=0.0, snow=True):
    A.d['ink'].line([(cx - 0.6 * h, base), (cx - 0.2 * h, base - 0.4 * h), (cx + 0.2 * h, base - 0.55 * h), (cx + 0.6 * h, base - 0.9 * h)], fill=255, width=max(5, int(0.03 * h)))
    A.d['ink'].line([(cx - 0.2 * h, base - 0.4 * h), (cx - 0.35 * h, base - 0.8 * h)], fill=255, width=max(3, int(0.02 * h)))
    pts = [(cx - 0.45 * h, base - 0.18 * h), (cx - 0.28 * h, base - 0.6 * h), (cx - 0.32 * h, base - 0.74 * h), (cx - 0.05 * h, base - 0.48 * h),
           (cx + 0.15 * h, base - 0.55 * h), (cx + 0.32 * h, base - 0.7 * h), (cx + 0.48 * h, base - 0.8 * h), (cx + 0.57 * h, base - 0.88 * h)]
    n = int(bloom * len(pts))
    for i, (px, py) in enumerate(pts[:n]):
        if fall > 0 and i % 2 == 0:
            q = clamp(fall * 1.3 - i * 0.05)
            py = lerp(py, base + 0.05 * h, q); px += 20 * math.sin(i + q * 4)
        r = 0.035 * h
        for a in range(5):
            ang = a * 2 * math.pi / 5
            A.d['chaitou'].ellipse((px + r * math.cos(ang) - r * 0.7, py + r * math.sin(ang) - r * 0.7, px + r * math.cos(ang) + r * 0.7, py + r * math.sin(ang) + r * 0.7), fill=255)
    if snow:
        for i in range(20):
            q = (t * 0.2 + i / 20) % 1
            x = cx - 0.7 * h + (i * 37) % int(1.4 * h)
            A.d['wash'].ellipse((x - 3, base - h + q * h - 3, x + 3, base - h + q * h + 3), fill=220)

def sword(A, cx, cy, L_, ang=0.0, rust=0.0):
    tx, ty = cx + L_ * math.sin(ang), cy - L_ * math.cos(ang)
    A.d['fangtian'].line((cx, cy, tx, ty), fill=255, width=max(4, int(0.03 * L_)))
    if rust > 0:
        A.d['huyang'].line((cx, cy, lerp(cx, tx, rust), lerp(cy, ty, rust)), fill=int(160 * rust), width=max(4, int(0.03 * L_)))
    A.d['ink'].line((cx - 0.12 * L_ * math.cos(ang), cy - 0.12 * L_ * math.sin(ang), cx + 0.12 * L_ * math.cos(ang), cy + 0.12 * L_ * math.sin(ang)), fill=255, width=max(4, int(0.035 * L_)))
    A.d['ink'].line((cx, cy, cx - 0.2 * L_ * math.sin(ang), cy + 0.2 * L_ * math.cos(ang)), fill=255, width=max(4, int(0.035 * L_)))

def bed(A, cx, base, w):
    A.d['huyang'].rectangle((cx - w, base - 0.25 * w, cx + w, base - 0.15 * w), fill=255)
    A.d['ink'].rectangle((cx - w, base - 0.15 * w, cx - w + 12, base), fill=255)
    A.d['ink'].rectangle((cx + w - 12, base - 0.15 * w, cx + w, base), fill=255)
    A.d['wash'].rectangle((cx - 0.9 * w, base - 0.35 * w, cx + 0.6 * w, base - 0.25 * w), fill=230)

# ================================================================ chapter card
CH = {16: (0.0, 0.4, 0.0), 48: (0.4, 0.8, 0.0), 80: (0.8, 1.0, 0.0), 112: (1.0, 1.0, 0.5), 144: (1.0, 1.0, 1.0)}
def art_plum_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b, f = CH.get(kb, (0.4, 0.8, 0.0))
    q = ease_out(u / (1.2 * P))
    prev_f = {112: 0.0, 144: 0.5}.get(kb, 0.0)
    plum(A, 540, 1200, 400, lerp(a, b, q), fall=lerp(prev_f, f, q), t=t)
    A.d['dune'].rectangle((240, 1200, 840, 1214), fill=200)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_plum_chapter)
    ink_in(cv, text_img(no, SERIF, 56, SHENYUAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_y_hook_poems(A, cv, t, u):
    ground(A, GROUND)
    n = min(30, int(clamp(u / (1.2 * P)) * 30) + 1)
    for i in range(n):
        A.d['wash'].rectangle((200 + (i % 10) * 70, GROUND - 120 - (i // 10) * 120, 250 + (i % 10) * 70, GROUND - 20 - (i // 10) * 120), fill=255)
        A.d['ink'].line((225 + (i % 10) * 70, GROUND - 110 - (i // 10) * 120, 225 + (i % 10) * 70, GROUND - 30 - (i // 10) * 120), fill=150, width=2)

def art_y_hook_shier(A, cv, t, u):
    ground(A, GROUND)
    bed(A, 540, GROUND, 280)
    lu(A, 540, GROUND - 90, 160, dir=1, kneel=True, bow=30, arm=90, old=1.0)
    candle(A, 860, GROUND, 120, 0.9, t)

def art_y_hook_chai(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((240, 860, 840, 1320), fill=230)
    A.flush(cv)
    for i, ch in enumerate('错错错'):
        stamp(cv, seal(ch, 70, ZHU), 380 + i * 160, 1090, t, t - u + i * 0.35 * P)

def art_y_hook_boat(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=170)
    waves(A, 1170, t, rows=3, amp=8 + 10 * clamp(u / (1.2 * P)))
    rain(A, t, amt=0.7)
    boat(A, 540, 1190, 140, t)

# ================================================================ 第一回 舟中
def art_y_born(A, cv, t, u):
    """6-beat set piece: 舟中出生 — 1125: his father, recalled to the capital, travels by boat on the 淮河; the boy is born on board in a storm.
    Two years later the north falls."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1120, W - 60, GROUND + 40), fill=150 + int(50 * clamp((ph - 1.5) / 1)))
    waves(A, 1130, t, rows=3, amp=4 + 14 * clamp((ph - 1.5) / 1))
    if ph > 1.5:
        rain(A, t, amt=clamp((ph - 1.5) / 1))
    boat(A, 540, 1160, 160, t)
    lamp(A, 560, 1100, 20, t, glow=0.9)
    A.flush(cv)
    lab = '宣和七年 · 父陆宰携家沿淮河北上' if ph < 1.5 else ('风雨大作' if ph < 3.5 else '陆游生于淮上舟中')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '其自述 予生于淮上 是日风雨大作', t, t - u + P)

def art_y_jingkang(A, cv, t, u):
    palace(A, 540, 1300, 320, collapse=clamp(u / (2 * P)) * 0.5, layer='mid')
    flames(A, 540, 1200, 560, 200, t, n=5, seed=1127, smoke=True)
    ground(A, GROUND)
    for j in range(5):
        person(A, lerp(500, -100, ((t * 0.08 + j / 5) % 1)) + 500, GROUND, 110, dir=-1, robe=True, hat='knot', load=j % 2 == 0, ph=t * 3 + j, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('靖康之变 北宋灭亡 · 随家南逃', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_shanyin(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 200), (x + 220, GROUND)], fill=150)
    ground(A, GROUND)
    for i in range(6):
        A.d['mid'].rectangle((140 + i * 140, GROUND - 330, 250 + i * 140, GROUND), fill=170)
        for j in range(4):
            A.d['shenyuan' if (i + j) % 2 else 'mid'].rectangle((150 + i * 140, GROUND - 90 - j * 76, 240 + i * 140, GROUND - 30 - j * 76), fill=230)
    person(A, 540, GROUND, 120, dir=1, robe=True, hat='none', arm=150, layer='ink')
    A.flush(cv)
    paste(cv, text_img('定居山阴 · 父陆宰藏书万卷', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('山阴', 56), 860, 1020, t, t - u + P, rot=6)

def art_y_zengji(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='mid')
    person(A, 780, GROUND, 190, dir=-1, robe=True, hat='knot', kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    lu(A, 320, GROUND, 160, dir=1, kneel=True, arm=90)
    A.flush(cv)
    paste(cv, text_img('从曾几学诗 · 立志恢复中原', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_tang(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((560, GROUND - 260, 900, GROUND), fill=230)
    A.d['ink'].polygon([(540, GROUND - 260), (920, GROUND - 260), (730, GROUND - 330)], fill=255)
    yu(A, 500, GROUND, 180, dir=-1, arm=60, t=t, layer='mid')
    lu(A, 340, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('娶表妹唐氏 · 夫妻甚相得', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '唐氏名琬之说 出自后世', t, t - u + P)

def art_y_divorce(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='knot', female=True, arm=lerp(-8, 120, ease_out(u / 0.6)), layer='ink')
    lu(A, 520, GROUND, 190, dir=1, bow=25, arm=-8)
    yu(A, lerp(380, -100, ease_out((u - P) / (2 * P))), GROUND, 170, dir=-1, ph=t * 2, arm=-8, t=t, layer='mid')
    A.flush(cv)
    paste(cv, text_img('母亲不喜唐氏 · 被迫离异', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_qinhui(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    scroll(A, 540, 1060, 400, 160, 1.0, layer='wash')
    A.d['ink'].line((380, 1030, 700, 1090), fill=255, width=8)
    lu(A, 300, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('礼部试名列前茅 · 因位在秦桧之孙前 被黜', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '前一年锁厅试 已名列秦桧孙秦埙之前', t, t - u + P)

# ================================================================ 第二回 沈园
def art_y_shenyuan(A, cv, t, u):
    """6-beat set piece: 沈园 — on a spring outing in the 沈 garden he meets 唐氏 and her new husband; she sends wine and food;
    he writes 钗头凤 on the wall: 红酥手 黄縢酒 ... 错 错 错 ... 莫 莫 莫."""
    ph = u / P
    ground(A, GROUND)
    A.d['ocean'].ellipse((300, GROUND - 60, 780, GROUND + 20), fill=140)
    plum(A, 860, GROUND, 360, 0.8, t=t, snow=False)
    if ph < 2:
        yu(A, 620, GROUND, 170, dir=-1, arm=-8, t=t, layer='mid')
        person(A, 720, GROUND, 190, dir=-1, robe=True, hat='knot', arm=-8, layer='mid')
        lu(A, 300, GROUND, 190, dir=1, arm=-8)
        lab, col = '春游沈园 · 偶遇唐氏', SHENYUAN
    elif ph < 3.5:
        A.d['qiuhuang'].ellipse((480, GROUND - 100, 540, GROUND - 74), fill=255)
        lu(A, 300, GROUND, 190, dir=1, bow=20, arm=-8)
        lab, col = '唐氏遣人送来酒肴', SHENYUAN
    else:
        A.d['wash'].rectangle((360, 820, 760, GROUND - 40), fill=230)
        lu(A, 260, GROUND, 190, dir=1, arm=150)
        lab, col = '题钗头凤于园壁', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 720, 1, 1)
    if ph >= 3.5:
        paste(cv, text_img('红\n酥\n手', SERIF, 40, INK, 'Black', bleed=False, spacing=4), 680, 1050, 1, clamp((ph - 3.7) / 0.4))
        paste(cv, text_img('错\n错\n错', SERIF, 40, ZHU, 'Black', bleed=False, spacing=4), 560, 1050, 1, clamp((ph - 4.3) / 0.4))
        paste(cv, text_img('莫\n莫\n莫', SERIF, 40, ZHU, 'Black', bleed=False, spacing=4), 440, 1050, 1, clamp((ph - 4.9) / 0.4))
    note_in(cv, '沈园本事见宋人笔记 学界尚有争议', t, t - u + P)

def art_y_tangdeath(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, female=True, layer='mid')
    plum(A, 860, GROUND, 300, 0.6, fall=clamp(u / (3 * P)), t=t, snow=False)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('不久唐氏郁郁而终', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '同出笔记 年份难考', t, t - u + P)

def art_y_ningde(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='宁德', layer='mid', open_=1.0)
    ground(A, GROUND)
    lu(A, 540, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('秦桧死后 · 始任福州宁德主簿', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='shenyuan')
    ground(A, GROUND)
    lu(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('孝宗即位 赐进士出身 · 时年三十八', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_beifa(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 220), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    army(A, lerp(-300, 300, ease_out(u / (3 * P))), GROUND, 6, dir=1, layer='shenyuan', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('力主北伐 · 隆兴北伐兵败符离', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_baguan(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    lu(A, lerp(400, 120, ease_out((u - P) / P)), GROUND, 180, dir=-1 if u > P else 1, ph=t * 3 if u > P else None, arm=-8)
    A.flush(cv)
    paste(cv, text_img('以 力说张浚用兵 之罪 · 罢官归乡', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_shanxi(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 180, GROUND), (x, GROUND - 360), (x + 180, GROUND)], fill=150)
    ground(A, GROUND)
    for k in range(3):
        A.d['wash'].rectangle((620 + k * 100, GROUND - 120, 700 + k * 100, GROUND), fill=255)
    willow(A, 520, GROUND, 160, t)
    lu(A, lerp(120, 460, ease_out(u / (3 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('山重水复疑无路 柳暗花明又一村', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '游山西村', t, t - u + P)

# ================================================================ 第三回 南郑
def art_y_rushu(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    river(A, 1210, t, rows=3, amp=5)
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, 1200), (x - 40, 820), (x + 40, 820), (x + 160, 1200)], fill=150)
    boat(A, lerp(-100, 600, ease_out(u / (3 * P))), 1220, 90, t)
    A.flush(cv)
    paste(cv, text_img('入蜀任夔州通判 · 作入蜀记', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_y_nanzheng(A, cv, t, u):
    """6-beat set piece: 南郑 — at last on the front: in 王炎's headquarters at 南郑, he rides in armour, patrols the passes,
    and later writes of stabbing a tiger in the snow; the 大散关 in autumn wind."""
    ph = u / P
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 40, GROUND - 420), (x + 40, GROUND - 420), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    if ph < 2:
        tent(A, 760, GROUND, 300, 220, layer='shenyuan', open_=1.0)
        lu(A, 400, GROUND, 200, dir=1, armour=True, arm=60)
        lab, col = '入王炎幕府 · 来到抗金前线南郑', SHENYUAN
    elif ph < 4:
        for i in range(30):
            q = (t * 0.4 + i / 30) % 1
            A.d['wash'].ellipse((80 + (i * 61) % 920 - 4, lerp(600, 1400, q) - 4, 80 + (i * 61) % 920 + 4, lerp(600, 1400, q) + 4), fill=230)
        rider(A, lerp(100, 600, clamp((ph - 2) / 1.5)), GROUND, 150, dir=1, ph=t * 7, layer='ink', spear=True)
        A.d['huyang'].ellipse((760, GROUND - 90, 920, GROUND - 20), fill=255)
        lab, col = '雪中刺虎', ZHU
    else:
        city_wall(A, 360, 720, 1100, gate_x=540, label='大散关', layer='mid')
        for j in range(4):
            rider(A, lerp(-100, 300, ((t * 0.1 + j / 4) % 1)), GROUND, 110, dir=1, ph=t * 6 + j, layer='ink')
        lab, col = '铁马秋风大散关', SHENYUAN
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '刺虎之事见其诗中自述', t, t - u + 2 * P)

def art_y_end8(A, cv, t, u):
    tent(A, 540, GROUND, 400, 280, layer='mid', open_=0.0)
    ground(A, GROUND)
    lu(A, lerp(540, 1100, ease_out(u / (3 * P))), GROUND, 180, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('王炎被召回 · 前线生涯仅八个月', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_jianmen(A, cv, t, u):
    A.d['mid'].polygon([(60, GROUND), (200, 820), (420, 820), (480, GROUND)], fill=170)
    A.d['mid'].polygon([(600, GROUND), (660, 820), (880, 820), (1020, GROUND)], fill=170)
    rain(A, t, amt=0.5)
    ground(A, GROUND)
    horse(A, lerp(200, 560, ease_out(u / (3 * P))), GROUND, 110, dir=1, ph=t * 2, layer='mid')
    lu(A, lerp(200, 560, ease_out(u / (3 * P))) - 4, GROUND - 70, 100, dir=1, kneel=True, arm=-8)
    A.flush(cv)
    paste(cv, text_img('此身合是诗人未 细雨骑驴入剑门', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_y_fanchengda(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    lu(A, 380, GROUND, 200, dir=1, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2 + 1)))
    A.flush(cv)
    paste(cv, text_img('入范成大幕府 · 以文字交 不拘礼法', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_fangweng(A, cv, t, u):
    ground(A, GROUND)
    A.d['qiuhuang'].ellipse((480, GROUND - 100, 540, GROUND - 74), fill=255)
    lu(A, 540, GROUND, 220, dir=1, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 2)), bow=lerp(-5, 5, 0.5 + 0.5 * math.sin(t)))
    A.flush(cv)
    paste(cv, text_img('人讥其颓放 · 遂自号放翁', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('放翁', 60), 860, 1020, t, t - u + P, rot=6)

def art_y_east(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    river(A, 1210, t, rows=3, amp=5)
    boat(A, lerp(200, 900, ease_out(u / (3 * P))), 1220, 90, t)
    A.flush(cv)
    paste(cv, text_img('离蜀东归 · 一别九年', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 放翁
def art_y_shufen(A, cv, t, u):
    """6-beat set piece: 书愤 — at sixty-two he writes: young, how could I know the world was hard ... towered ships in night snow at 瓜洲,
    iron horses in autumn wind at 大散关 ... the 出师表 truly deserves its name."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        desk(A, 540, GROUND, 420, layer='mid')
        lu(A, 280, GROUND, 170, dir=1, kneel=True, arm=100, old=0.5)
        candle(A, 760, GROUND - 74, 70, 0.5, t)
        lab = '早岁那知世事艰 中原北望气如山'
    elif ph < 4:
        A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=140)
        for i in range(30):
            q = (t * 0.3 + i / 30) % 1
            A.d['wash'].ellipse((80 + (i * 61) % 920 - 4, lerp(600, 1160, q) - 4, 80 + (i * 61) % 920 + 4, lerp(600, 1160, q) + 4), fill=230)
        tangship(A, 300, 1180, 90, t)
        for j in range(3):
            rider(A, 600 + j * 140, GROUND, 110, dir=1, ph=t * 6 + j, layer='ink')
        lab = '楼船夜雪瓜洲渡 铁马秋风大散关'
    else:
        desk(A, 540, GROUND, 420, layer='mid')
        lu(A, 280, GROUND, 170, dir=1, kneel=True, bow=30, arm=-8, old=0.5)
        scroll(A, 560, GROUND - 160, 260, 90, 1.0, layer='wash')
        lab = '出师一表真名世 千载谁堪伯仲间'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, ZHU if 2 <= ph < 4 else SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '书愤 时年六十二', t, t - u + P)

def art_y_libu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    lu(A, 540, GROUND, 200, dir=1, arm=60, old=0.6)
    A.flush(cv)
    paste(cv, text_img('任礼部郎中', SERIF, 48, SHENYUAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_y_fengyue(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    lu(A, lerp(400, 120, ease_out((u - P) / P)), GROUND, 180, dir=-1 if u > P else 1, ph=t * 3 if u > P else None, arm=-8, old=0.6)
    A.flush(cv)
    paste(cv, text_img('被劾 嘲咏风月 · 再度罢官', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '归后索性名其居曰 风月轩', t, t - u + P)

def scene_tiema(cv, t, c, k):
    """8-beat custom scene: 十一月四日风雨大作 — an old man lies stiff in a lonely village, not pitying himself, still dreaming of guarding the frontier;
    deep in the night he hears the wind and rain — and iron cavalry cross frozen rivers in his dream."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    if ph < 4:
        A.d['wash'].rectangle((140, 900, 940, GROUND), fill=120)
        A.d['ink'].polygon([(100, 900), (980, 900), (540, 760)], fill=255)
        bed(A, 540, GROUND, 300)
        lu(A, 470, GROUND - 105, 130, dir=1, fall=-88, arm=-8, old=1.0)
        candle(A, 840, GROUND, 100, 0.85, t)
        rain(A, t, amt=0.9)
    else:
        A.d['wash'].rectangle((0, 1160, W, GROUND + 40), fill=230)
        for k2 in range(6):
            A.d['ink'].line((80 + k2 * 160, 1180 + 20 * (k2 % 2), 200 + k2 * 160, 1190 + 20 * (k2 % 2)), fill=120, width=2)
        for i in range(40):
            q = (t * 0.6 + i / 40) % 1
            A.d['wash'].ellipse((80 + (i * 61) % 920 - 4, lerp(600, 1400, q) - 4, 80 + (i * 61) % 920 + 4, lerp(600, 1400, q) + 4), fill=230)
        for j in range(5):
            rider(A, lerp(-150, 1100, ((t * 0.12 + j / 5) % 1)), 1160, 130, dir=1, ph=t * 8 + j, layer='ink', spear=True)
    ground(A, GROUND)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '铁马冰河', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=86)
    fx.flush(cv)
    lines = ['僵卧孤村不自哀', '尚思为国戍轮台', '夜阑卧听风吹雨', '铁马冰河入梦来']
    for i, line in enumerate(lines):
        st = s0 + (0.4 + i * 1.7) * P
        if t >= st:
            paste(cv, text_img(line, SERIF, 44, ZHU if i == 3 else SHENYUAN, 'Black', bleed=False, spacing=6), W / 2, 590 + i * 64, 1, clamp((t - st) / 0.4))
    note_in(cv, '十一月四日风雨大作 时年六十八', t, s0 + 2 * P)

def art_y_jinghong(A, cv, t, u):
    ground(A, GROUND)
    A.d['ocean'].rectangle((200, GROUND - 80, 880, GROUND), fill=140)
    A.d['dune'].chord((300, GROUND - 200, 780, GROUND + 40), 180, 360, outline=255, width=20)
    lu(A, 540, GROUND - 110, 150, dir=1, arm=-8, old=1.0)
    A.flush(cv)
    paste(cv, text_img('伤心桥下春波绿 曾是惊鸿照影来', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '七十五岁重游沈园 作沈园二首', t, t - u + P)

def art_y_yongmei(A, cv, t, u):
    ground(A, GROUND)
    plum(A, 540, GROUND, 420, 1.0, fall=clamp(u / (3 * P)), t=t)
    A.flush(cv)
    paste(cv, text_img('零落成泥碾作尘 只有香如故', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '卜算子 咏梅 作年不详', t, t - u + P)

# ================================================================ 第五回 示儿
def art_y_guoshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='shenyuan')
    ground(A, GROUND)
    lu(A, 540, GROUND, 200, dir=1, arm=60, old=1.0)
    A.flush(cv)
    paste(cv, text_img('七十八岁奉诏入京 · 修两朝实录', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_kaixi(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 220), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    army(A, lerp(300, -300, ease_out(u / (3 * P))), GROUND, 6, dir=-1, layer='shenyuan', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('开禧北伐 · 陆游热切支持 终告失败', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_shier(A, cv, t, u):
    """6-beat set piece: 示儿 — dying, he writes to his sons: in death all is empty, I know — I only grieve not to see the nine provinces one;
    on the day the royal army takes back the north, at the family sacrifice, do not forget to tell your father."""
    ph = u / P
    ground(A, GROUND)
    bed(A, 540, GROUND, 280)
    lu(A, 470, GROUND - 90, 150, dir=1, kneel=True, bow=20, arm=lerp(-8, 90, clamp(ph / 0.6)), old=1.0)
    for j in range(3):
        person(A, 760 + j * 80, GROUND, 140 + 10 * j, dir=-1, robe=True, hat='knot', kneel=True, bow=30, layer='mid')
    candle(A, 200, GROUND, 120, lerp(0.8, 1.0, clamp(ph / 6)), t, lit=ph < 5)
    A.flush(cv)
    lab, col = ('死去元知万事空 但悲不见九州同' if ph < 3 else '王师北定中原日 家祭无忘告乃翁'), (SHENYUAN if ph < 3 else ZHU)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '示儿 绝笔之作', t, t - u + P)

def art_y_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    lu(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    sword(A, 860, 1100, 220, 0.0, rust=0.8)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于山阴 · 年八十六', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_wanshou(A, cv, t, u):
    ground(A, GROUND)
    n = min(40, int(clamp(u / (3 * P)) * 40) + 1)
    for i in range(n):
        x = 160 + (i % 10) * 80; y = GROUND - 20 - (i // 10) * 110
        A.d['wash'].rectangle((x, y - 90, x + 50, y), fill=255)
        A.d['ink'].line((x + 25, y - 80, x + 25, y - 10), fill=150, width=2)
    A.flush(cv)
    paste(cv, text_img('六十年间万首诗 · 今存九千余首', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '剑南诗稿 存诗之多 古今第一', t, t - u + P)

def art_y_end(A, cv, t, u):
    A.d['wash'].rectangle((0, 1180, W, GROUND + 40), fill=200)
    for j in range(5):
        rider(A, lerp(-150, 1100, ((t * 0.08 + j / 5) % 1)), 1180, 120, dir=1, ph=t * 6 + j, layer='mid', spear=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('夜阑卧听风吹雨 铁马冰河入梦来', SERIF, 46, SHENYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_y_legacy(A, cv, t, u):
    plum(A, 860, 1440, 120, 1.0, t=t, snow=False)

def art_y_title(A, cv, t, u):
    plum(A, 820, 1440, 280, 1.0, t=t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    lu(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '舟中'), 48: ('第二回', '沈园'), 80: ('第三回', '南郑'),
            112: ('第四回', '放翁'), 144: ('第五回', '示儿')}

CARDS = [
    C(0, 2, 'works', 'num', num='一万首诗', line='今存九千多首', art=art_y_hook_poems),
    C(2, 4, 'death', 'num', num='一首示儿', line='临终还在等北伐', art=art_y_hook_shier),
    C(4, 6, 'night', 'num', num='一曲钗头凤', line='错错错 莫莫莫', art=art_y_hook_chai),
    C(6, 8, 'war', 'num', num='生在船上', line='长在乱世', art=art_y_hook_boat),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 舟中
    C(16, 18, 'life', 'chapter'),
    C(18, 24, 'life', 'card', year=1125, main='舟中出生', sub='淮河', art=art_y_born),
    C(24, 28, 'death', 'card', year=1127, main='靖康之变', sub='举家南逃', art=art_y_jingkang),
    C(28, 32, 'works', 'card', year=1137, main='山阴', sub='藏书万卷', note='年份约略', art=art_y_shanyin),
    C(32, 36, 'night', 'card', year=1142, main='学诗', sub='师从曾几', art=art_y_zengji),
    C(36, 40, 'empire', 'card', year=1144, main='娶唐氏', sub='夫妻相得', note='年份约略', art=art_y_tang),
    C(40, 44, 'death', 'card', year=1146, main='被迫离异', sub='母命难违', note='年份约略', art=art_y_divorce),
    C(44, 48, 'fate', 'card', year=1154, main='秦桧黜落', sub='名列前茅', art=art_y_qinhui),
    # ---- 第二回 沈园
    C(48, 50, 'night', 'chapter'),
    C(50, 56, 'night', 'card', year=1155, main='沈园', sub='钗头凤', note='年份约略', art=art_y_shenyuan),
    C(56, 60, 'death', 'card', year=1156, main='唐氏早逝', sub='郁郁而终', note='年份难考', art=art_y_tangdeath),
    C(60, 64, 'court', 'card', year=1158, main='初入仕途', sub='宁德主簿', art=art_y_ningde),
    C(64, 68, 'empire', 'card', year=1162, main='赐进士', sub='三十八岁', art=art_y_jinshi),
    C(68, 72, 'war', 'card', year=1163, main='隆兴北伐', sub='兵败符离', art=art_y_beifa),
    C(72, 76, 'fate', 'card', year=1166, main='罢官', sub='力说用兵', art=art_y_baguan),
    C(76, 80, 'works', 'card', year=1167, main='游山西村', sub='柳暗花明', art=art_y_shanxi),
    # ---- 第三回 南郑
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'life', 'card', year=1170, main='入蜀', sub='夔州通判', art=art_y_rushu),
    C(86, 92, 'war', 'card', year=1172, main='南郑', sub='抗金前线', art=art_y_nanzheng),
    C(92, 96, 'fate', 'card', year=1172, main='幕府解散', sub='八个月', art=art_y_end8),
    C(96, 100, 'night', 'card', year=1172, main='剑门', sub='细雨骑驴', art=art_y_jianmen),
    C(100, 104, 'court', 'card', year=1175, main='成都', sub='范成大幕', art=art_y_fanchengda),
    C(104, 108, 'empire', 'card', year=1176, main='自号放翁', sub='颓放', art=art_y_fangweng),
    C(108, 112, 'fate', 'card', year=1178, main='东归', sub='出蜀', art=art_y_east),
    # ---- 第四回 放翁
    C(112, 114, 'fate', 'chapter'),
    C(114, 120, 'works', 'card', year=1186, main='书愤', sub='六十二岁', art=art_y_shufen),
    C(120, 124, 'court', 'card', year=1189, main='礼部郎中', sub='再入朝', art=art_y_libu),
    C(124, 128, 'fate', 'card', year=1190, main='嘲咏风月', sub='再度罢官', art=art_y_fengyue),
    C(128, 136, 'night', 'tiema', year=1192),
    C(136, 140, 'death', 'card', year=1199, main='惊鸿照影', sub='重游沈园', art=art_y_jinghong),
    C(140, 144, 'life', 'card', year=1199, main='咏梅', sub='香如故', note='作年不详', art=art_y_yongmei),
    # ---- 第五回 示儿
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'empire', 'card', year=1202, main='修国史', sub='七十八岁', art=art_y_guoshi),
    C(150, 154, 'war', 'card', year=1206, main='开禧北伐', sub='又一次失败', art=art_y_kaixi),
    C(154, 160, 'death', 'card', year=1209, main='示儿', sub='家祭无忘', art=art_y_shier),
    C(160, 164, 'death', 'card', year=1210, main='陆游去世', sub='年八十六', art=art_y_death),
    C(164, 168, 'works', 'card', year=1210, main='万首诗', sub='剑南诗稿', art=art_y_wanshou),
    C(168, 170, 'end', 'card', year=1210, main='铁马冰河', sub='入梦来', art=art_y_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='捌拾陆', col=SHENYUAN, acc=CHAITOU, born=1125, died=1210, age0=1124,
    born_lab='1125年', died_lab='1210年', years_txt='公元1125 — 1210',
    hook_q='他写了一万首诗 · 为什么到死都放不下？',
    name_line='陆游 · 字务观', name='陆游', seal='放翁', title_art=art_y_title,
    q1='爱国诗人？', q2='痴情才子？',
    end_art=art_y_legacy, end_big='家祭无忘', end_seal='放翁',
    end_l1='北伐的梦他做了一辈子', end_l2='最后只能托付给儿孙',
    end_brush='铁马冰河', end_ask='陆游的诗 你最先想到哪一句？评论区聊聊', next='宋慈'),
    scenes=dict(chapter=scene_chapter, tiema=scene_tiema))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
