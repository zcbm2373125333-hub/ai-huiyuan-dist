"""千古人物志 · 第叁拾叁集 · 苏轼 (1037–1101)
Look: 竹青 + 东坡赭, 竹叶 corner borders, a 竹杖芒鞋 chapter card: the straw-sandalled walker crosses further with each
chapter while the rain thins, ending in clear sky ("也无风雨也无晴").
Set pieces: 6-beat 名动京师, custom 8-beat scene 'wutai' (乌台诗案: 103 days in prison), 8-beat 赤壁夜游,
6-beat 东坡肉, 6-beat 苏堤, 6-beat 海南儋州, 6-beat 北归.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_dufu as Df            # engine + helpers (previous episode)
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
from render_wangyangming import desk, scroll, lamp, sitter, bamboo
from render_quyuan import river
from render_simaqian import brush, bars
from render_libai import moon_phase, wine_jar
from render_qianlong import palm

F.RIPPLE = False
BAMBOO = (62, 120, 84)              # 竹青
DONGPO = (168, 92, 52)              # 东坡赭
S.LAYERS.append(('bamboo2', BAMBOO, 0.88, 1.0))
S.LAYERS.append(('dongpo', DONGPO, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='坡', life='眉', court='宋', night='狱', war='贬', empire='宋', works='词', fate='风', death='归', end='坡')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court', 'empire'):
    G.THEMES[k]['part'] = 'petal'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (DONGPO, 220, (W * 0.5, 820))
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (BAMBOO, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

GROVE = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(GROVE)
_r = random.Random(33)
for _x in (80, 130, 950, 1000):
    _d.line((_x, 1500, _x + _r.uniform(-12, 12), 1100), fill=BAMBOO + (54,), width=8)
    for _y in range(1130, 1480, 60):
        _d.line((_x - 8, _y, _x + 8, _y), fill=BAMBOO + (70,), width=2)
    for _k in range(5):
        _a = _r.uniform(-2.6, -0.5); _y = _r.uniform(1100, 1300)
        _d.line((_x, _y, _x + 50 * math.cos(_a), _y + 50 * math.sin(_a) * 0.4), fill=BAMBOO + (60,), width=6)
MTN_COL = {'night': (34, 40, 38), 'death': (60, 62, 60), 'war': (96, 72, 56), 'fate': (80, 100, 90)}
def draw_background(t, theme):
    """江南: soft ridges, bamboo at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(184, 192, 182), (140, 160, 144), MTN_COL.get(theme, (100, 124, 108))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(GROVE)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """竹叶: a sprig of three bamboo leaves in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = BAMBOO + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=DONGPO + (200,), width=3); d.line((x, y, x, y + sy * 180), fill=DONGPO + (200,), width=3)
        for a in (0.35, 0.8, 1.25):
            ex, ey = x + sx * 90 * math.cos(a), y + sy * 90 * math.sin(a)
            nx, ny = -math.sin(a) * sx, math.cos(a) * sy
            mx, my = x + sx * 45 * math.cos(a), y + sy * 45 * math.sin(a)
            d.polygon([(x + sx * 10 * math.cos(a), y + sy * 10 * math.sin(a)), (mx + 9 * nx, my + 9 * ny), (ex, ey), (mx - 9 * nx, my - 9 * ny)], fill=col)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def su(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, hat='dongpo', staff=False, **kw):
    """苏轼: plump, full beard, the tall 东坡巾 (high square cap); bamboo staff and straw cape when wandering."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    d = A.d[layer]
    if up:
        if hat == 'dongpo':
            d.rectangle((x - 0.07 * h, y - 1.14 * h, x + 0.07 * h, y - 0.94 * h), fill=255)
            d.rectangle((x - 0.09 * h, y - 1.0 * h, x + 0.09 * h, y - 0.94 * h), fill=255)
        elif hat == 'rain':
            A.d['dongpo'].polygon([(x - 0.2 * h, y - 0.92 * h), (x + 0.2 * h, y - 0.92 * h), (x, y - 1.1 * h)], fill=255)
        d.polygon([(x + dir * 0.0, y - 0.86 * h), (x + dir * 0.09 * h, y - 0.86 * h), (x + dir * 0.05 * h, y - 0.62 * h)], fill=255)
    if staff and not kneel and not kw.get('fall'):
        A.d['bamboo2'].line((x + dir * 0.2 * h, y - 0.6 * h, x + dir * 0.28 * h, y), fill=255, width=max(3, int(0.02 * h)))
        for k in range(3):
            yy = y - 0.15 * h - k * 0.15 * h
            A.d['ink'].line((x + dir * 0.2 * h + dir * 0.08 * h * (1 - k / 3) - 6, yy, x + dir * 0.2 * h + dir * 0.08 * h * (1 - k / 3) + 6, yy), fill=255, width=2)
    return hand

def rain(A, t, n=60, strength=1.0):
    for k in range(int(n * strength)):
        q = (t * 1.2 + k / max(1, n)) % 1
        x = 80 + (k * 17) % 920
        A.d['wash'].line((x, lerp(620, 1420, q), x - 6, lerp(620, 1420, q) + 24), fill=200, width=2)

def pot_meat(A, x, base, s, t):
    A.d['ink'].chord((x - s, base - 0.9 * s, x + s, base + 0.4 * s), 0, 180, fill=255)
    A.d['ink'].rectangle((x - 1.1 * s, base - 0.3 * s, x + 1.1 * s, base - 0.22 * s), fill=255)
    for k in range(4):
        A.d['dongpo'].rectangle((x - 0.6 * s + k * 0.32 * s, base - 0.5 * s, x - 0.36 * s + k * 0.32 * s, base - 0.28 * s), fill=255)
    for k in range(5):
        q = (t * 0.5 + k / 5) % 1
        A.d['wash'].ellipse((x - 0.5 * s + k * 0.25 * s - 8, base - 0.6 * s - 120 * q - 8, x - 0.5 * s + k * 0.25 * s + 8, base - 0.6 * s - 120 * q + 8), fill=int(200 * (1 - q)))

# ================================================================ chapter card
CH = {16: (0.15, 1.0), 48: (0.35, 0.8), 80: (0.55, 0.6), 112: (0.75, 0.35), 144: (0.95, 0.0)}
def art_walk_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    reach, wet = CH.get(kb, (0.35, 0.8))
    rain(A, t, n=60, strength=wet)
    if wet == 0:
        sun(cv, 820, 860, 90, DONGPO, 150)
    x = lerp(160, 160 + 760 * reach, ease_out(u / (1.4 * P)))
    pts = [(xx, 1220 - 30 * math.sin(xx / 150)) for xx in range(80, W - 79, 20)]
    A.d['dongpo'].line(pts, fill=200, width=6)
    su(A, x, 1220 - 30 * math.sin(x / 150), 200, dir=1, hat='rain', staff=True, ph=t * 4, arm=30)
    ground(A, 1240)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_walk_chapter)
    ink_in(cv, text_img(no, SERIF, 56, BAMBOO, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_s_hook_exile(A, cv, t, u):
    pts = [(920, 860), (700, 1000), (760, 1180), (520, 1300), (300, 1380)]
    p = ease_out(u / (1.6 * P))
    n = max(2, int(p * len(pts)) + 1)
    A.d['dongpo'].line(pts[:n], fill=230, width=8)
    for (x, y) in pts[:n]:
        A.d['ink'].ellipse((x - 14, y - 14, x + 14, y + 14), fill=255)

def art_s_hook_pork(A, cv, t, u):
    ground(A, GROUND)
    pot_meat(A, 540, GROUND, 160, t)

def art_s_hook_rain(A, cv, t, u):
    rain(A, t, n=60, strength=1 - ease_out(u / (1.6 * P)))
    ground(A, GROUND)
    su(A, 540, GROUND, 280, dir=1, hat='rain', staff=True, ph=t * 4, arm=40)

def art_s_hook_moon(A, cv, t, u):
    moon_phase(A, 540, 900, 130, 1.0)
    river(A, 1260, t, rows=3, amp=4, speed=0.8)
    A.d['moon'].ellipse((440, 1290, 640, 1320), fill=150)

# ================================================================ 第一回 眉山三苏
def art_s_meishan(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['bamboo2'].polygon([(x - 200, GROUND), (x, GROUND - 340 - 60 * (k % 2)), (x + 200, GROUND)], fill=170)
    ground(A, GROUND)
    person(A, 380, GROUND, 240, dir=1, robe=True, hat='none', arm=40, layer='ink')
    person(A, 560, GROUND, 140, dir=1, robe=True, hat='knot', arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    person(A, 680, GROUND, 120, dir=1, robe=True, hat='knot', arm=20, layer='mid')
    A.flush(cv)
    stamp(cv, seal('眉山', 56), 860, 880, t, t - u + P, rot=6)

def art_s_mother(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='bamboo2')
    person(A, 760, GROUND, 220, dir=-1, robe=True, hat='knot', female=True, arm=lerp(20, 100, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    sitter(A, 380, GROUND, 140, dir=1, bow=15)
    scroll(A, 560, GROUND - 120, 220, 60, u / 0.5)
    A.flush(cv)
    stamp(cv, seal('后汉书 范滂传', 32), 260, 880, t, t - u + P, rot=-5)

def art_s_jinshi(A, cv, t, u):
    """6-beat: 名动京师 — the exam hall; 欧阳修 reads his paper and sets it aside; the list: 三苏 名动京师."""
    ph = u / P
    palace(A, 540, 1160, 540, layer='dongpo')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 230, dir=-1, robe=True, hat='none', arm=lerp(40, 140, ease_out(ph / 2)), layer='ink')
    scroll(A, 600, GROUND - 220, 120, 60, ph / 0.5)
    for k in range(3):
        x = 220 + k * 120
        su(A, x, GROUND, 190 - k * 20, dir=1, arm=40, hat='dongpo') if k == 1 else person(A, x, GROUND, 190 - k * 20, dir=1, robe=True, hat='none', arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('欧阳修', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    if ph >= 2.5:
        type_in(cv, text_img('老夫当避路 放他出一头地', SERIF, 44, BAMBOO, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 2.5 * P, 0.5)

def art_s_mourn(A, cv, t, u):
    A.d['mid'].chord((380, 1200, 700, GROUND + 160), 180, 360, fill=230)
    for k in range(10):
        bamboo(A, 120 + k * 30 if k < 5 else 800 + (k - 5) * 30, GROUND, 360, t, layer='bamboo2', width=6, seed=k, leaves=k % 2 == 0)
    ground(A, GROUND)
    su(A, 860, GROUND, 200, dir=-1, kneel=True, bow=45, arm=100)
    A.flush(cv)
    stamp(cv, seal('丁母忧', 50, INK), 540, 1100, t, t - u + P)

def art_s_fengxiang(A, cv, t, u):
    city_wall(A, 120, 960, 1100, gate_x=540, label='凤翔', layer='mid', open_=1.0)
    ground(A, GROUND)
    su(A, 540, GROUND, 210, dir=1, arm=lerp(20, 100, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('签判', 54), 860, 860, t, t - u + P, rot=6)

def art_s_ten_years(A, cv, t, u):
    for k in range(40):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    moon_phase(A, 820, 760, 60, 1.0)
    A.d['mid'].chord((380, 1240, 700, GROUND + 140), 180, 360, fill=230)
    for k in range(6):
        A.d['ink'].polygon([(340 + k * 70, GROUND), (360 + k * 70, GROUND - 120), (380 + k * 70, GROUND)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('十年生死两茫茫', SERIF, 50, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('不思量 自难忘', SERIF, 50, DONGPO, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.6 * P, 0.5)

def art_s_oppose(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='none', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    su(A, 320, GROUND, 230, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3 + 1)))
    A.flush(cv)
    stamp(cv, seal('王安石', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    stamp(cv, seal('新法', 50), 540, 960, t, t - u + P)

def art_s_hangzhou(A, cv, t, u):
    A.d['ocean'].ellipse((140, 1180, 940, 1380), fill=140)
    waves(A, 1220, t, rows=2, amp=3, speed=0.8, x0=200, x1=880)
    A.d['ink'].line((200, 1200, 880, 1240), fill=255, width=8)
    for k in range(6):
        bamboo(A, 260 + k * 110, 1210 + k * 7, 140, t, layer='grass', width=4, seed=40 + k, leaves=True)
    boat(A, lerp(300, 700, (t * 0.05) % 1), 1300, 80, t, sail=False)
    A.flush(cv)
    type_in(cv, text_img('欲把西湖比西子', SERIF, 46, BAMBOO, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)

# ================================================================ 第二回 乌台诗案
def art_s_mizhou(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 300), (x + 200, GROUND)], fill=200)
    ground(A, GROUND)
    x = lerp(-100, 600, ease_out(u / (2.5 * P)))
    horse(A, x, GROUND, 160, dir=1, ph=t * 10, layer='ink')
    su(A, x - 10, GROUND - 120, 150, dir=1, arm=150)
    A.flush(cv)
    type_in(cv, text_img('老夫聊发少年狂', SERIF, 48, DONGPO, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + P, 0.5)

def art_s_shuidiao(A, cv, t, u):
    moon_phase(A, 760, 820, 100, 1.0)
    A.d['ink'].rectangle((200, 1160, 560, 1180), fill=255)
    for sx in (220, 540):
        A.d['ink'].rectangle((sx, 1180, sx + 16, GROUND), fill=255)
    su(A, 380, 1160, 220, dir=1, arm=lerp(80, 170, 0.5 + 0.5 * math.sin(t)))
    wine_jar(A, 260, 1160, 40)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('但愿人长久 千里共婵娟', SERIF, 46, BAMBOO, 'Black', bleed=False, spacing=4), W / 2, 1448, t, t - u + P, 0.5)

def art_s_flood(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='徐州', layer='mid')
    lvl = lerp(1360, 1180, ease_out(u / (2 * P)))
    A.d['ocean'].rectangle((60, lvl, W - 60, GROUND + 40), fill=170)
    waves(A, lvl, t, rows=3, amp=7, speed=2.4)
    su(A, 540, 1100, 160, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    stamp(cv, seal('抗洪', 56), 860, 880, t, t - u + P, rot=6)

def art_s_huzhou(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    su(A, 540, GROUND, 220, dir=1, kneel=True, bow=30, arm=90)
    scroll(A, 700, GROUND - 160, 160, 60, u / 0.5)
    A.flush(cv)
    stamp(cv, seal('湖州谢上表', 38), 860, 880, t, t - u + P, rot=6)

def scene_wutai(cv, t, c, k):
    """8-beat custom scene: 乌台诗案 — the 御史台 (where crows nest); poems are combed for treason; arrest; a cell where a
    day counter climbs to 一百零三; a fish is sent in (the death signal, by mistake); at last 贬黄州."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    if ph < 2:
        palace(A, 540, GROUND, 600, layer='mid')
        A.d['ink'].line((300, 1000, 300, 760), fill=255, width=10)
        for j in range(5):
            crow(A, 260 + j * 30 + 30 * math.sin(t + j), 760 - (j % 2) * 30, 34, t * 6 + j)
        for j in range(4):
            A.d['wash'].rectangle((560 + j * 70, 1180, 620 + j * 70, 1260), fill=255)
            A.d['red'].line((560 + j * 70, 1200, 620 + j * 70, 1240), fill=255, width=4)
    else:
        A.d['mid'].rectangle((200, 860, 880, GROUND), fill=180)
        sitter(A, 540, GROUND, 200, dir=1, bow=lerp(10, 40, 0.5 + 0.5 * math.sin(t)))
        bars(A, 220, 860, 880, GROUND, n=11)
        if 4.5 <= ph < 6:
            A.d['wash'].polygon([(660, GROUND - 60), (720, GROUND - 80), (760, GROUND - 60), (720, GROUND - 40)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '乌台诗案', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=91)
    fx.flush(cv)
    if ph < 2:
        lab = '御史摘其诗句 指为讪谤'
    elif ph < 4.5:
        lab = '押赴御史台狱'
    elif ph < 6:
        lab = '送来一条鱼 以为必死'
    else:
        lab = '神宗不忍 贬黄州'
    paste(cv, text_img(lab, SERIF, 46, DONGPO if ph < 6 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    days = int(lerp(1, 103, clamp((ph - 2) / 5.5)))
    if ph >= 2:
        paste(cv, text_img(f'系狱第{cn_num(days)}天', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    paste(cv, text_img('公元一〇七九年', SERIF, 42, BAMBOO, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_s_brother(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=40, layer='ink')
    person(A, 360, GROUND, 200, dir=1, robe=True, hat='none', kneel=True, bow=50, arm=110, layer='ink')
    A.flush(cv)
    stamp(cv, seal('苏辙', 54), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('愿纳官爵 为兄赎罪', SERIF, 46, BAMBOO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第三回 东坡居士
def art_s_huangzhou(A, cv, t, u):
    river(A, 1260, t, rows=2, amp=4)
    for k in range(3):
        A.d['dongpo'].rectangle((200 + k * 200, 1180, 360 + k * 200, 1260), fill=160)
    ground(A, 1260, x0=60, x1=W - 60)
    su(A, 540, 1260, 220, dir=1, hat='rain', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 4)))
    A.d['ink'].line((560, 1080, 640, 1250), fill=255, width=6)
    A.flush(cv)
    stamp(cv, seal('东坡', 60), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('躬耕东坡 自号东坡居士', SERIF, 44, DONGPO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_dingfengbo(A, cv, t, u):
    rain(A, t, n=70, strength=1 - ease_out((u - 2 * P) / P))
    for k in range(3):
        person(A, 160 + k * 60, GROUND, 150, dir=1, robe=True, hat='knot', ph=t * 8, bow=30, arm=160, layer='mid')
    ground(A, GROUND)
    su(A, 600, GROUND, 250, dir=1, hat='rain', staff=True, ph=t * 3, arm=30)
    A.flush(cv)
    type_in(cv, text_img('竹杖芒鞋轻胜马 谁怕', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('一蓑烟雨任平生', SERIF, 52, BAMBOO, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.6 * P, 0.5)

def art_s_chibi(A, cv, t, u):
    """8-beat set piece: 赤壁夜游 — the red cliff in moonlight, a skiff drifts; flute music; he lies back laughing;
    the river and moon and the line 大江东去 roll by."""
    ph = u / P
    moon_phase(A, 780, 780, 80, 1.0)
    A.d['dongpo'].polygon([(60, 1240), (60, 840), (220, 800), (360, 900), (420, 1240)], fill=230)
    river(A, 1220, t, rows=4, amp=5, speed=1.2)
    A.d['moon'].ellipse((700, 1260, 860, 1290), fill=140)
    x = lerp(800, 560, ease_out(ph / 6))
    boat(A, x, 1270, 140, t, sail=False)
    su(A, x - 30, 1240, 140, dir=-1, bow=lerp(0, -15, ease_out((ph - 4) / 1)), arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t)))
    person(A, x + 50, 1240, 120, dir=-1, robe=True, hat='knot', arm=100, layer='mid')
    A.d['ink'].line((x + 20, 1150, x - 20, 1170), fill=255, width=4)
    A.flush(cv)
    stamp(cv, seal('赤壁', 56), 240, 760, t, t - u + 0.4, rot=-5)
    if ph >= 1.5:
        type_in(cv, text_img('大江东去 浪淘尽', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 1.5 * P, 0.5)
    if ph >= 3.5:
        type_in(cv, text_img('千古风流人物', SERIF, 52, ZHU, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 3.5 * P, 0.5)
    if ph >= 5.5:
        type_in(cv, text_img('惟江上之清风 与山间之明月', SERIF, 40, BAMBOO, 'Black', bleed=False, spacing=2), W / 2, 1448, t, t - u + 5.5 * P, 0.5)

def art_s_pork(A, cv, t, u):
    """6-beat: 东坡肉 — cheap pork, a slow small fire, little water — the pot steams; neighbours gather."""
    ph = u / P
    ground(A, GROUND)
    flames(A, 540, GROUND, 160, 60 + 10 * math.sin(t * 5), t, n=3, seed=6, smoke=False)
    pot_meat(A, 540, GROUND - 60, 150, t)
    su(A, 300, GROUND, 220, dir=1, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 2)))
    for k in range(int(clamp((ph - 2) / 3) * 4)):
        person(A, 760 + k * 60, GROUND, 140, dir=-1, robe=False, hat='knot', arm=60, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('慢著火 少著水 火候足时他自美', SERIF, 42, DONGPO, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.8 * P, 0.6)
    stamp(cv, seal('猪肉颂', 46), 860, 1040, t, t - u + 2.5 * P, rot=6)

def art_s_xilin(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        h = 400 + 120 * math.sin(k * 1.3 + u * 0.4)
        A.d['mid'].polygon([(x - 160, GROUND), (x, GROUND - h), (x + 160, GROUND)], fill=200)
    ground(A, GROUND)
    su(A, lerp(200, 800, ease_out(u / (3 * P))), GROUND, 170, dir=1, staff=True, ph=t * 3, arm=30)
    A.flush(cv)
    type_in(cv, text_img('横看成岭侧成峰', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('只缘身在此山中', SERIF, 46, BAMBOO, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.5 * P, 0.5)

def art_s_wang_meet(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 240), (x + 200, GROUND)], fill=200)
    ground(A, GROUND)
    su(A, 380, GROUND, 220, dir=1, arm=60)
    horse(A, 720, GROUND, 150, dir=-1, ph=0, moving=False, layer='mid')
    person(A, 680, GROUND, 210, dir=-1, robe=True, hat='none', arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('金陵 王安石', 36), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('相逢一笑泯恩仇', SERIF, 48, DONGPO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_s_recall(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='dongpo')
    ground(A, GROUND)
    su(A, 360, GROUND, 230, dir=1, arm=40)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', female=True, arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('翰林学士', 46), 260, 880, t, t - u + P, rot=-5)

# ================================================================ 第四回 苏堤春晓
def art_s_both_sides(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    su(A, 540, GROUND, 230, dir=1, arm=-8)
    for k in range(3):
        person(A, 160 + k * 60, GROUND, 160, dir=1, robe=True, hat='none', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='mid')
        person(A, 920 - k * 60, GROUND, 160, dir=-1, robe=True, hat='none', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 4 + k + 1)), layer='mid')
    A.flush(cv)
    paste(cv, text_img('新党不容 旧党也不容', SERIF, 48, DONGPO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_s_sudi(A, cv, t, u):
    """6-beat: 苏堤 — dredged mud is heaped into a causeway across West Lake; six bridges; willows and peach trees appear."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1000, W - 60, GROUND), fill=140)
    waves(A, 1020, t, rows=3, amp=3, speed=0.8)
    p = ease_out(ph / 3.5)
    A.d['dongpo'].polygon([(120, 1260), (120 + 840 * p, 1160 - 0 * p), (120 + 840 * p, 1190), (120, 1290)], fill=230)
    for k in range(int(p * 6)):
        bx = 180 + k * 140; by = 1270 - k * 17
        A.d['ink'].arc((bx - 40, by - 30, bx + 40, by + 30), 180, 360, fill=255, width=6)
    if ph >= 3.5:
        for k in range(10):
            bx = 160 + k * 84; by = 1260 - k * 10
            A.d['grass'].line((bx, by, bx + 10, by - 70), fill=255, width=4)
            A.d['apricot'].ellipse((bx - 14, by - 90, bx + 14, by - 64), fill=230)
    for k in range(int(clamp(ph / 3) * 5)):
        person(A, 300 + k * 120, 1000, 90, dir=1, robe=False, hat='knot', load=True, ph=t * 6 + k, arm=160, layer='ink')
    A.flush(cv)
    stamp(cv, seal('苏堤', 60), 860, 860, t, t - u + 3.5 * P, rot=6)

def art_s_huizhou(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        A.d['ink'].line((200 + k * 160, GROUND, 220 + k * 160, 1000), fill=255, width=10)
        for j in range(6):
            a = -math.pi / 2 + (j - 2.5) * 0.5
            A.d['grass'].line((220 + k * 160, 1000, 220 + k * 160 + 90 * math.cos(a), 1000 + 50 * math.sin(a) + 40), fill=230, width=6)
        for j in range(4):
            A.d['gold'].ellipse((200 + k * 160 + j * 14, 1040 + (j % 2) * 16, 214 + k * 160 + j * 14, 1054 + (j % 2) * 16), fill=255)
    su(A, 880, GROUND, 200, dir=-1, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    type_in(cv, text_img('日啖荔枝三百颗 不辞长作岭南人', SERIF, 40, BAMBOO, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.5, 0.6)
    stamp(cv, seal('惠州', 54), 300, 960, t, t - u + P, rot=-5)

def art_s_chaoyun(A, cv, t, u):
    A.d['mid'].chord((380, 1200, 700, GROUND + 160), 180, 360, fill=230)
    A.d['ink'].polygon([(490, 1160), (590, 1160), (540, 1100)], fill=255)
    ground(A, GROUND)
    su(A, 860, GROUND, 200, dir=-1, bow=30, arm=60)
    A.flush(cv)
    stamp(cv, seal('王朝云', 50), 540, 1060, t, t - u + P)
    paste(cv, text_img('一肚皮不合时宜', SERIF, 48, DONGPO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_s_danzhou(A, cv, t, u):
    """6-beat: 儋州 — across the sea to 海南; a palm-thatch hut; he opens a school and children gather."""
    ph = u / P
    if ph < 2:
        A.d['ocean'].rectangle((60, 1100, W - 60, GROUND), fill=160)
        waves(A, 1110, t, rows=5, amp=10, speed=2.4)
        boat(A, lerp(200, 800, ease_out(ph / 2)), 1200, 110, t, sail=True)
        su(A, lerp(200, 800, ease_out(ph / 2)), 1170, 120, dir=1, arm=40)
    else:
        Df.hut(A, 720, GROUND, 360, 300, roof=1.0)
        palm(A, 200, GROUND - 360, t)
        su(A, 500, GROUND, 210, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 2)))
        for k in range(int(clamp((ph - 2.5) / 2.5) * 6)):
            sitter(A, 320 + (k % 3) * 70 - 200, GROUND - (k // 3) * 40, 80, dir=1, bow=10, layer='ink')
        ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('儋州', 56), 860, 860, t, t - u + 0.4, rot=6)
    if ph >= 3:
        paste(cv, text_img('海南第一位进士 出自他的学生', SERIF, 42, BAMBOO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 3) / 0.4))

def art_s_old(A, cv, t, u):
    ground(A, GROUND)
    su(A, 540, GROUND, 250, dir=1, staff=True, bow=12, arm=30)
    for k in range(40):
        q = (t * 0.3 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=200)
    A.flush(cv)
    type_in(cv, text_img('问汝平生功业 黄州惠州儋州', SERIF, 44, DONGPO, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)

# ================================================================ 第五回 也无风雨
def art_s_pardon(A, cv, t, u):
    """6-beat: 北归 — pardoned at sixty-four, he sails north up the 运河; crowds line the banks to see him."""
    ph = u / P
    river(A, 1220, t, rows=3, amp=4, speed=1.2)
    ground(A, 1220, x0=60, x1=300)
    ground(A, 1220, x0=780, x1=W - 60)
    x = lerp(200, 600, ease_out(ph / 4))
    boat(A, x, 1270, 120, t, sail=True)
    su(A, x - 20, 1240, 130, dir=1, staff=True, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)))
    for k in range(int(clamp(ph / 3) * 10)):
        person(A, 100 + (k % 4) * 50 if k < 4 else 800 + (k - 4) * 40, 1220, 110, dir=1 if k < 4 else -1, robe=True, hat='knot', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('遇赦北归', 46), 860, 880, t, t - u + 0.4, rot=6)

def art_s_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    su(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('常州', 56), 300, 880, t, t - u + P, rot=-5)

def art_s_last_words(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    ground(A, GROUND)
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    sitter(A, 380, GROUND, 180, dir=1, bow=30)
    A.flush(cv)
    type_in(cv, text_img('著力即差', SERIF, 56, BAMBOO, 'Black', bleed=False, spacing=10), W / 2, 830, t, t - u + P, 0.5)

def art_s_calligraphy(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='bamboo2')
    A.d['wash'].rectangle((360, GROUND - 90, 720, GROUND - 74), fill=255)
    brush(A, 520, GROUND - 160, 120, ang=-1.1 + 0.2 * math.sin(t * 3))
    A.flush(cv)
    ink_in(cv, text_img('寒食帖', BRUSH, 120, INK), W / 2, 960, t, t - u + 0.5, dur=0.3, settle=1.2)
    paste(cv, text_img('天下第三行书', SERIF, 46, DONGPO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_s_tang_song(A, cv, t, u):
    ground(A, GROUND)
    for k in range(8):
        x = 140 + k * 115
        sitter(A, x, GROUND, 110 + (10 if k == 6 else 0), dir=1, bow=10, layer='dongpo' if k >= 5 else 'mid')
    A.flush(cv)
    paste(cv, text_img('唐宋八大家 · 苏家占其三', SERIF, 46, BAMBOO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_s_final(A, cv, t, u):
    sun(cv, 820, 860, 90, DONGPO, 140)
    for k in range(3):
        bamboo(A, 120 + k * 50, GROUND, 560, t, layer='bamboo2', width=10, seed=500 + k, leaves=True)
    ground(A, GROUND)
    su(A, lerp(380, 760, ease_out(u / (3 * P))), GROUND, 220, dir=1, hat='rain', staff=True, ph=t * 3, arm=30)
    A.flush(cv)
    type_in(cv, text_img('回首向来萧瑟处', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('也无风雨也无晴', SERIF, 52, BAMBOO, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.5 * P, 0.5)

def art_s_legacy(A, cv, t, u):
    sun(cv, 820, 860, 90, DONGPO, 120)
    for k in range(5):
        bamboo(A, 160 + k * 40, GROUND, 520, t, layer='bamboo2', width=10, seed=300 + k, leaves=True)
    ground(A, GROUND)

def art_s_title(A, cv, t, u):
    for k in range(4):
        bamboo(A, 800 + k * 50, 1460, 700, t, layer='bamboo2', width=12, seed=k, leaves=True)
    su(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '眉山三苏'), 48: ('第二回', '乌台诗案'), 80: ('第三回', '东坡居士'),
            112: ('第四回', '苏堤春晓'), 144: ('第五回', '也无风雨')}

CARDS = [
    C(0, 2, 'war', 'num', num='一贬再贬', line='越贬越远', art=art_s_hook_exile),
    C(2, 4, 'life', 'num', num='东坡肉', line='贬谪中发明的', art=art_s_hook_pork),
    C(4, 6, 'fate', 'num', num='一蓑烟雨', line='任平生', art=art_s_hook_rain),
    C(6, 8, 'night', 'num', num='千里共婵娟', line='写给弟弟的中秋', art=art_s_hook_moon),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 眉山三苏
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1037, main='生于眉山', sub='父苏洵 弟苏辙', art=art_s_meishan),
    C(22, 26, 'works', 'card', year=1047, main='母亲教读', sub='程夫人教他读范滂传', note='轼若为滂 母许之否乎', art=art_s_mother),
    C(26, 32, 'empire', 'card', year=1057, main='名动京师', sub='二十一岁中进士', art=art_s_jinshi),
    C(32, 36, 'death', 'card', year=1057, main='母亲去世', sub='回乡守丧', art=art_s_mourn),
    C(36, 40, 'court', 'card', year=1061, main='凤翔签判', sub='初入仕途', art=art_s_fengxiang),
    C(40, 44, 'court', 'card', year=1071, main='反对新法', sub='上书论新法之弊 · 自请外放', art=art_s_oppose),
    C(44, 48, 'works', 'card', year=1073, main='西湖', sub='杭州通判', note='水光潋滟晴方好', art=art_s_hangzhou),
    # ---- 第二回 乌台诗案
    C(48, 50, 'night', 'chapter'),
    C(50, 54, 'war', 'card', year=1075, main='密州出猎', sub='左牵黄 右擎苍', art=art_s_mizhou),
    C(54, 58, 'night', 'card', year=1075, main='十年生死', sub='妻子王弗去世十年 · 梦中相见', note='江城子', art=art_s_ten_years),
    C(58, 62, 'night', 'card', year=1076, main='水调歌头', sub='中秋怀弟苏辙', art=art_s_shuidiao),
    C(62, 66, 'works', 'card', year=1077, main='徐州抗洪', sub='筑堤护城 · 过家门不入', art=art_s_flood),
    C(66, 70, 'court', 'card', year=1079, main='湖州谢表', sub='一句牢骚 · 被人抓住', art=art_s_huzhou),
    C(70, 78, 'night', 'wutai', year=1079),
    C(78, 80, 'life', 'card', year=1079, main='兄弟情深', sub='苏辙上书救兄', art=art_s_brother),
    # ---- 第三回 东坡居士
    C(80, 82, 'fate', 'chapter'),
    C(82, 86, 'life', 'card', year=1081, main='东坡居士', sub='贬谪黄州 · 开荒种地', art=art_s_huangzhou),
    C(86, 90, 'fate', 'card', year=1082, main='定风波', sub='沙湖道中遇雨', art=art_s_dingfengbo),
    C(90, 98, 'night', 'card', year=1082, main='赤壁夜游', sub='前后赤壁赋 · 念奴娇', note='一说 此非三国赤壁', art=art_s_chibi),
    C(98, 104, 'life', 'card', year=1083, main='东坡肉', sub='黄州好猪肉 价贱如泥土', note='相传', art=art_s_pork),
    C(104, 108, 'works', 'card', year=1084, main='题西林壁', sub='离开黄州 · 游庐山', art=art_s_xilin),
    C(108, 110, 'court', 'card', year=1084, main='金陵相逢', sub='与王安石同游', art=art_s_wang_meet),
    C(110, 112, 'empire', 'card', year=1086, main='重回朝廷', sub='官至翰林学士', art=art_s_recall),
    # ---- 第四回 苏堤春晓
    C(112, 114, 'works', 'chapter'),
    C(114, 118, 'court', 'card', year=1087, main='两边不讨好', sub='又反对旧党尽废新法', art=art_s_both_sides),
    C(118, 124, 'works', 'card', year=1090, main='苏堤', sub='再任杭州 · 疏浚西湖', note='葑草淤泥 筑成长堤', art=art_s_sudi),
    C(124, 128, 'life', 'card', year=1094, main='贬惠州', sub='年近六十 · 南下岭南', art=art_s_huizhou),
    C(128, 132, 'death', 'card', year=1096, main='朝云病逝', sub='唯一懂他的人', art=art_s_chaoyun),
    C(132, 138, 'war', 'card', year=1097, main='贬儋州', sub='渡海 · 到了天涯海角', art=art_s_danzhou),
    C(138, 144, 'fate', 'card', year=1100, main='三州功业', sub='自题金山画像', note='心似已灰之木 身如不系之舟', art=art_s_old),
    # ---- 第五回 也无风雨
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'end', 'card', year=1100, main='遇赦北归', sub='徽宗即位 · 大赦天下', art=art_s_pardon),
    C(152, 156, 'death', 'card', year=1101, main='病逝常州', sub='享年六十四', art=art_s_death),
    C(156, 160, 'night', 'card', year=1101, main='著力即差', sub='友人劝他念佛往生', note='西方不无 但个里著力不得', art=art_s_last_words),
    C(160, 164, 'works', 'card', year=1101, main='寒食帖', sub='黄州时所书', note='作于一〇八二年', art=art_s_calligraphy),
    C(164, 168, 'empire', 'card', year=1368, main='唐宋八大家', sub='父子三人同列', art=art_s_tang_song),
    C(168, 170, 'end', 'card', year=2026, main='也无风雨', sub='他活成了一种态度', art=art_s_final),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='叁拾叁', col=BAMBOO, acc=DONGPO, born=1037, died=1101, age0=1037.0,
    hook_q='被贬了一辈子 · 他为什么还能活得这么快乐？',
    name_line='苏轼 · 字子瞻', name='苏轼', seal='东坡', title_art=art_s_title,
    q1='旷达天才？', q2='不合时宜？',
    end_art=art_s_legacy, end_big='一蓑烟雨', end_seal='东坡',
    end_l1='他被贬到天涯海角', end_l2='却把每一处都过成了家',
    end_brush='也无风雨也无晴', end_ask='你最想和苏轼做朋友吗？评论区聊聊', next='李清照'),
    scenes=dict(chapter=scene_chapter, wutai=scene_wutai))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
