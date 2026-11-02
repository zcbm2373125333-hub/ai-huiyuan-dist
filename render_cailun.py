"""千古人物志 · 第叁拾集 · 蔡伦 (?–121)
Look: 麻青 + 纸浆蓝, 抄纸帘 corner borders, a writing-material chapter card that evolves chapter by chapter
(竹简 → 缣帛 → 粗麻纸 → 白纸 → a sheet drifting away).
Set pieces: 6-beat 尚方令 workshop, custom 8-beat scene 'papermaking' (剪 泡 舂 抄 晒), 6-beat 奏上蔡侯纸,
6-beat 纸写经典, 6-beat 饮药而死, 8-beat 纸的西传 map.
Birth year unknown: the HUD hides ages (no_age).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_banchao as Bc         # engine + helpers (previous episode)
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
from render_simaqian import brush, bars
from render_wudi import camel

F.RIPPLE = False
HEMP = (104, 118, 66)               # 麻青
PULP = (88, 148, 188)               # 纸浆蓝
S.LAYERS.append(('hemp', HEMP, 0.88, 1.0))
S.LAYERS.append(('pulp', PULP, 0.85, 1.2))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='纸', life='伦', court='宫', night='冤', war='剑', empire='汉', works='纸', fate='案', death='药', end='纸')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (PULP, 220, (W * 0.5, 820))
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (HEMP, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

SHEETS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(SHEETS)
for _k, (_x, _y) in enumerate(((80, 1200), (150, 1260), (930, 1220), (1000, 1290))):
    _d.line((_x - 40, _y - 60, _x + 40, _y - 60), fill=HEMP + (60,), width=3)
    _d.rectangle((_x - 30, _y - 56, _x + 30, _y + 30), fill=(250, 248, 240, 70))
MTN_COL = {'night': (36, 38, 34), 'death': (60, 60, 58), 'war': (100, 72, 50), 'works': (100, 112, 84)}
def draw_background(t, theme):
    """晒纸场: low ridges; sheets of paper hanging on drying lines at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 188, 176), (148, 154, 128), MTN_COL.get(theme, (110, 118, 90))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.8))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(SHEETS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """抄纸帘: a small bamboo mould screen (fine lines + ribs) in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = HEMP + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=col, width=3); d.line((x, y, x, y + sy * 180), fill=col, width=3)
        x0, y0, x1, y1 = x + sx * 16, y + sy * 16, x + sx * 96, y + sy * 76
        d.rectangle((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), outline=col, width=3)
        for k in range(1, 8):
            yy = y0 + sy * k * 7.5
            d.line((x0, yy, x1, yy), fill=HEMP + (120,), width=1)
        for k in (1, 2, 3):
            xx = x0 + sx * k * 20
            d.line((xx, y0, xx, y1), fill=PULP + (200,), width=2)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def cai(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, **kw):
    """蔡伦: beardless court eunuch, tall 貂蝉冠 style hat with a side plume, long sleeves."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    d = A.d[layer]
    if up:
        d.polygon([(x - 0.07 * h, y - 0.94 * h), (x + 0.07 * h, y - 0.94 * h), (x + 0.05 * h, y - 1.12 * h), (x - 0.05 * h, y - 1.12 * h)], fill=255)
        A.d['pulp'].line((x - dir * 0.05 * h, y - 1.08 * h, x - dir * 0.16 * h, y - 1.24 * h), fill=255, width=max(2, int(0.02 * h)))
    return hand

def vat(A, x, base, w, h, layer='hemp'):
    A.d[layer].polygon([(x - w / 2, base - h), (x + w / 2, base - h), (x + 0.42 * w, base), (x - 0.42 * w, base)], fill=255)
    A.d['pulp'].rectangle((x - 0.46 * w, base - h + 8, x + 0.46 * w, base - h + 30), fill=230)

def sheet(A, x, y, w, h, tone=255, layer='wash', rot=0.0):
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    c, s_ = math.cos(rot), math.sin(rot)
    A.d[layer].polygon([(x + px * c - py * s_, y + px * s_ + py * c) for px, py in pts], fill=tone)
    A.d['ink'].polygon([(x + px * c - py * s_, y + px * s_ + py * c) for px, py in pts], outline=90, width=2)

def silk(A, x, y, w, h, t):
    pts = [(x - w / 2 + k * w / 20, y - h / 2 + 10 * math.sin(t * 2 + k * 0.6)) for k in range(21)]
    pts2 = [(x + w / 2 - k * w / 20, y + h / 2 + 10 * math.sin(t * 2 + (20 - k) * 0.6)) for k in range(21)]
    A.d['gold'].polygon(pts + pts2, fill=220)

def mallet(A, x, base, s, ph):
    lift = 0.5 + 0.5 * math.sin(ph)
    A.d['ink'].rectangle((x - 0.08 * s, base - 0.6 * s - 0.4 * s * lift, x + 0.08 * s, base - 0.1 * s - 0.4 * s * lift), fill=255)
    A.d['ink'].rectangle((x - 0.25 * s, base - 0.15 * s - 0.4 * s * lift, x + 0.25 * s, base - 0.4 * lift * s), fill=255)
    A.d['hemp'].rectangle((x - 0.4 * s, base - 0.1 * s, x + 0.4 * s, base), fill=255)

# ================================================================ chapter card
def art_material_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    q = ease_out(u / (1.2 * P))
    if kb == 16:
        slips(A, 540 - 12 * 19 / 2, 1220, 12, int(360 * q) + 4, layer='hemp')
    elif kb == 48:
        silk(A, 540, 1040, 520 * q + 10, 300, t)
    elif kb == 80:
        sheet(A, 540, 1040, 460 * q + 10, 340, tone=170, layer='hemp')
    elif kb == 112:
        sheet(A, 540, 1040, 460 * q + 10, 340, tone=255)
    else:
        sheet(A, lerp(540, 820, q), lerp(1040, 800, q), 300, 220, tone=255, rot=lerp(0, 0.6, q))
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_material_chapter)
    ink_in(cv, text_img(no, SERIF, 56, HEMP, 'Black', bleed=False, spacing=12), W / 2, 1290, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_c_hook_rags(A, cv, t, u):
    ground(A, GROUND)
    p = ease_out(u / (1.6 * P))
    items = [(220, 'hemp'), (420, 'mid'), (620, 'pulp'), (820, 'ink')]
    for i, (x, layer) in enumerate(items):
        xx = lerp(x, 540, p); yy = lerp(GROUND - 60, 1000, p)
        A.d[layer].ellipse((xx - 50, yy - 30, xx + 50, yy + 30), fill=200)
    if p > 0.8:
        sheet(A, 540, 1000, 300 * (p - 0.8) * 5, 220)

def art_c_hook_four(A, cv, t, u):
    ground(A, GROUND)
    for i in range(4):
        x = 180 + i * 240
        A.d['pulp' if i == 0 else 'mid'].rectangle((x - 80, 960, x + 80, 1200), fill=230)
    A.flush(cv)
    for i, nm in enumerate(('造纸', '印刷', '指南针', '火药')):
        paste(cv, text_img(nm, SERIF, 44, INK if i else ZHU, 'Black', bleed=False, spacing=4), 180 + i * 240, 1080, 1, clamp((u - i * 0.25) / 0.3))

def art_c_hook_eunuch(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    cai(A, 540, GROUND, 280, dir=1, arm=lerp(20, 90, ease_out(u / (1.2 * P))))
    sheet(A, 680, GROUND - 200, 120, 90)

def art_c_hook_cup(A, cv, t, u):
    for k in range(40):
        q = (t * 0.3 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['mid'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=180)
    A.d['ink'].chord((480, 1120, 600, 1220), 0, 180, fill=255)
    A.d['ink'].rectangle((530, 1170, 550, 1260), fill=255)
    ground(A, GROUND)

# ================================================================ 第一回 入宫为宦
def art_c_leiyang(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['hemp'].polygon([(x - 150, GROUND), (x, GROUND - 320 - 60 * (k % 2)), (x + 150, GROUND)], fill=180)
    A.d['ocean'].line([(60, 1340), (540, 1300), (1020, 1340)], fill=150, width=24)
    ground(A, GROUND)
    person(A, 540, GROUND, 150, dir=1, robe=False, hat='knot', arm=lerp(20, 100, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('耒阳', 56), 860, 880, t, t - u + P, rot=6)

def art_c_enter(A, cv, t, u):
    palace(A, 620, GROUND, 600, layer='mid')
    ground(A, GROUND)
    x = lerp(100, 520, ease_out(u / (3 * P)))
    person(A, x, GROUND, 150, dir=1, robe=True, hat='knot', ph=t * 4, arm=-8, layer='ink')
    A.flush(cv)
    stamp(cv, seal('入宫', 56, INK), 260, 880, t, t - u + P, rot=-5)

def art_c_huangmen(A, cv, t, u):
    palace(A, 540, 1140, 520, layer='mid')
    ground(A, GROUND)
    for k in range(3):
        x = 260 + k * 280
        cai(A, x, GROUND, 170, dir=1 if k < 2 else -1, arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 3 + k)))
        sheet(A, x + 60, GROUND - 150, 50, 40, layer='gold')
    A.flush(cv)
    stamp(cv, seal('小黄门', 50), 860, 880, t, t - u + P, rot=6)

def art_c_song_case(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND - 30, 230, dir=-1, robe=True, hat='crown', female=True, arm=lerp(20, 120, ease_out(u / P)), layer='ink')
    cai(A, 520, GROUND, 200, dir=1, kneel=True, bow=40, arm=100)
    person(A, 220, GROUND, 190, dir=1, robe=True, hat='knot', female=True, bow=lerp(0, 50, ease_out((u - 2 * P) / P)), arm=-8, layer='mid')
    A.flush(cv)
    stamp(cv, seal('窦皇后', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    stamp(cv, seal('宋贵人', 46), 220, 880, t, t - u + P, rot=-5)

def art_c_changshi(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='pulp')
    ground(A, GROUND)
    person(A, 700, GROUND - 30, 210, dir=-1, robe=True, hat='crown', arm=40, layer='ink')
    cai(A, 380, GROUND, 230, dir=1, arm=lerp(30, 100, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('中常侍', 50), 260, 880, t, t - u + P, rot=-5)

def art_c_dou_falls(A, cv, t, u):
    palace(A, 540, GROUND, 560, collapse=ease_out((u - P) / (2 * P)), layer='mid')
    ground(A, GROUND)
    for k in range(4):
        person(A, 160 + k * 70, GROUND, 160, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('窦宪', 54, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('宦官得势', SERIF, 50, HEMP, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((u - 2 * P) / 0.3))

def art_c_shangfang(A, cv, t, u):
    """6-beat: 尚方令 — the imperial workshop: a forge glows, swords are hammered and tempered, every piece inspected."""
    ph = u / P
    ground(A, GROUND)
    A.d['mid'].rectangle((140, 1100, 360, GROUND), fill=220)
    flames(A, 250, 1110, 140, 100 + 30 * math.sin(t * 6), t, n=3, seed=2, smoke=True)
    for k in range(2):
        x = 480 + k * 160
        person(A, x, GROUND, 170, dir=-1 if k else 1, robe=False, hat='knot', arm=lerp(40, 170, 0.5 + 0.5 * math.sin(t * 8 + k * 3)), layer='ink')
    A.d['ink'].rectangle((520, GROUND - 60, 600, GROUND - 40), fill=255)
    for k in range(int(clamp(ph / 4) * 6)):
        A.d['pulp'].line((760 + k * 30, GROUND - 10, 770 + k * 30, GROUND - 200), fill=255, width=6)
    cai(A, 940, GROUND, 200, dir=-1, arm=lerp(30, 110, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('尚方令', 50), 300, 880, t, t - u + 0.5, rot=-5)
    if ph >= 3:
        paste(cv, text_img('莫不精工坚密', SERIF, 48, HEMP, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - 3) / 0.4))

# ================================================================ 第二回 竹简太重
def art_c_heavy(A, cv, t, u):
    ground(A, GROUND)
    for k in range(int(clamp(u / (2 * P)) * 12) + 1):
        bundle(A, 200 + (k % 6) * 70, GROUND - (k // 6) * 60, 70, layer='hemp')
    person(A, 780, GROUND, 190, dir=-1, robe=False, hat='knot', load=True, bow=30, arm=160, layer='ink')
    A.flush(cv)
    paste(cv, text_img('一车竹简 · 寥寥几卷书', SERIF, 46, HEMP, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_c_silk(A, cv, t, u):
    ground(A, GROUND)
    silk(A, 540, 1040, 560, 220, t)
    for k in range(int(clamp(u / (2 * P)) * 8)):
        A.d['gold'].ellipse((260 + k * 70, GROUND - 40, 300 + k * 70, GROUND - 10), fill=255)
    A.flush(cv)
    paste(cv, text_img('缣贵而简重', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_c_early(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        sheet(A, 300 + k * 240, 1080, 180, 140, tone=150, layer='hemp', rot=0.1 * (k - 1))
    A.flush(cv)
    stamp(cv, seal('一说', 44, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('粗糙 易破 难写', SERIF, 48, HEMP, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_c_deng(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 30, 230, dir=1, robe=True, hat='crown', female=True, arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    desk(A, 760, GROUND, 220, layer='hemp')
    brush(A, 760, GROUND - 100, 80, ang=-1.2)
    A.flush(cv)
    stamp(cv, seal('邓皇后', 50), 260, 880, t, t - u + 0.5, rot=-5)

STEPS = [('剪', '树皮 麻头 破布 渔网 剪碎'), ('泡', '浸入水中 沤烂'), ('舂', '舂捣成浆'), ('抄', '竹帘抄起一层纤维'), ('晒', '压平 晾干 揭下')]
def scene_papermaking(cv, t, c, k):
    """8-beat custom scene: 造纸五步 — 剪 泡 舂 抄 晒, each with its own little machine; a step seal lights per stage;
    at the end a white sheet is peeled from the wall."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    i = min(4, int(ph / 1.5))
    ground(A, GROUND)
    if i == 0:
        for j, layer in enumerate(('hemp', 'mid', 'pulp', 'ink')):
            x = 220 + j * 200
            A.d[layer].ellipse((x - 60, GROUND - 80, x + 60, GROUND - 20), fill=200)
        A.d['ink'].line((540 + 60 * math.sin(t * 10), 1100, 540, 1240), fill=255, width=8)
    elif i == 1:
        vat(A, 540, GROUND, 420, 260)
        for j in range(8):
            q = (t * 0.5 + j / 8) % 1
            A.d['wash'].ellipse((400 + j * 36 - 6, GROUND - 240 - 40 * q - 6, 400 + j * 36 + 6, GROUND - 240 - 40 * q + 6), fill=int(200 * (1 - q)))
    elif i == 2:
        mallet(A, 540, GROUND, 300, t * 9)
        cai(A, 800, GROUND, 180, dir=-1, arm=60)
    elif i == 3:
        vat(A, 540, GROUND, 460, 240)
        lift = ease_out((ph - 4.5) / 1.2)
        y = lerp(GROUND - 230, GROUND - 420, lift)
        A.d['ink'].rectangle((360, y - 6, 720, y + 6), fill=255)
        sheet(A, 540, y - 20, 340, 30, tone=200, layer='pulp')
        person(A, 300, GROUND, 190, dir=1, robe=False, hat='knot', arm=lerp(60, 160, lift), layer='ink')
    else:
        A.d['mid'].rectangle((200, 900, 880, GROUND), fill=200)
        for j in range(4):
            peel = clamp((ph - 6 - j * 0.3) / 0.8)
            sheet(A, 290 + j * 170, 1080, 140, 200, tone=255, rot=-0.5 * peel)
    A.flush(cv)
    for j, (ch, _) in enumerate(STEPS):
        x = 180 + j * 180
        if j <= i:
            stamp(cv, seal(ch, 44, ZHU if j == i else HEMP), x, 830, t, s0 + j * 1.5 * P)
        else:
            ImageDraw.Draw(cv).rounded_rectangle((x - 34, 796, x + 34, 864), radius=6, outline=HEMP + (120,), width=2)
    fx = Art()
    chars_in(cv, fx, '造纸五步', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=66)
    fx.flush(cv)
    paste(cv, text_img(STEPS[i][1], SERIF, 44, HEMP, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('以树肤 麻头 敝布 鱼网以为纸', SERIF, 40, PULP, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 0.3) / 0.4))

def art_c_present(A, cv, t, u):
    """6-beat: 奏上蔡侯纸 — he kneels with a tray of white sheets; the emperor lifts one to the light; it glows."""
    ph = u / P
    palace(A, 540, 1140, 560, layer='pulp')
    ground(A, GROUND)
    cai(A, 360, GROUND, 210, dir=1, kneel=True, bow=30, arm=90)
    A.d['hemp'].rectangle((420, GROUND - 130, 540, GROUND - 116), fill=255)
    for k in range(4):
        sheet(A, 480, GROUND - 140 - k * 4, 100, 10, tone=255)
    person(A, 760, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=lerp(30, 160, ease_out((ph - 1.5) / 0.8)), layer='ink')
    if ph >= 2:
        sx, sy = 700, lerp(1150, 900, ease_out((ph - 2) / 1))
        for j in range(3):
            r = 120 + 40 * j
            A.d['gold'].ellipse((sx - r, sy - r, sx + r, sy + r), fill=26)
        sheet(A, sx, sy, 160, 200, tone=255)
    A.flush(cv)
    if ph >= 3.5:
        paste(cv, text_img('自是莫不从用焉', SERIF, 48, HEMP, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((ph - 3.5) / 0.4))

# ================================================================ 第三回 蔡侯纸
def art_c_named(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        x = 140 + k * 160
        person(A, x, GROUND, 140, dir=1 if k % 2 else -1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='mid')
        sheet(A, x + 40, GROUND - 120, 50, 40)
    A.flush(cv)
    ink_in(cv, text_img('蔡侯纸', BRUSH, 130, HEMP), W / 2, 960, t, t - u + 0.5, dur=0.3, settle=1.2)

def art_c_hedi_dies(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='mid')
    ground(A, GROUND)
    for k in range(40):
        q = (t * 0.3 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=200)
    person(A, 540, GROUND - 30, 230, dir=1, robe=True, hat='crown', female=True, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('邓太后临朝', 40), 860, 880, t, t - u + P, rot=6)

def art_c_spread(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='hemp')
    sitter(A, 300, GROUND, 210, dir=1, bow=20)
    for k in range(int(clamp(u / (2 * P)) * 10)):
        sheet(A, 440 + (k % 5) * 50, GROUND - 90 - (k // 5) * 14, 44, 12)
    rider(A, (t * 200) % (W + 300) - 150, GROUND, 110, 1, t * 11, layer='mid')
    A.flush(cv)
    paste(cv, text_img('公文 书信 改用纸张', SERIF, 46, HEMP, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_c_marquis(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='hemp')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 230, dir=-1, robe=True, hat='crown', female=True, arm=lerp(20, 90, ease_out(u / 0.5)), layer='ink')
    cai(A, 360, GROUND, 210, dir=1, kneel=True, bow=40, arm=100)
    A.flush(cv)
    stamp(cv, seal('龙亭侯', 54), 540, 880, t, t - u + P)

def art_c_dongguan(A, cv, t, u):
    ground(A, GROUND)
    for r in range(3):
        for c2 in range(7):
            x = 160 + c2 * 120; y = 980 + r * 100
            A.d['hemp'].rectangle((x - 46, y, x + 46, y + 70), outline=255, width=4)
            if r * 7 + c2 < int(clamp(u / (2 * P)) * 21):
                bundle(A, x, y + 66, 56, layer='pulp')
    cai(A, 540, GROUND, 160, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('东观', 54), 860, 880, t, t - u + 0.4, rot=6)

def art_c_taipu(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='pulp')
    ground(A, GROUND)
    cai(A, 540, GROUND, 230, dir=1, arm=40)
    for k in range(4):
        person(A, 160 + k * 60 if k < 2 else 780 + (k - 2) * 60, GROUND, 140, dir=1 if k < 2 else -1, robe=True, hat='knot', bow=30, arm=90, layer='mid')
    A.flush(cv)
    stamp(cv, seal('长乐太仆', 44), 860, 880, t, t - u + P, rot=6)

def art_c_books(A, cv, t, u):
    """6-beat: 纸写经典 — scholars copy books on paper; a single bamboo bundle shrinks into a thin paper volume;
    stacks of volumes multiply."""
    ph = u / P
    ground(A, GROUND)
    q = ease_out(ph / 2)
    bundle(A, 260, GROUND, lerp(160, 40, q), layer='hemp')
    sheet(A, 460, GROUND - 30, 120 * q + 4, 60, tone=255)
    n = int(clamp((ph - 2) / 3.5) * 24)
    for k in range(n):
        x = 620 + (k % 6) * 60; y = GROUND - 10 - (k // 6) * 22
        A.d['wash'].rectangle((x - 26, y - 18, x + 26, y), fill=255)
        A.d['ink'].rectangle((x - 26, y - 18, x + 26, y), outline=120, width=2)
    A.flush(cv)
    paste(cv, text_img('书 从此便宜了', SERIF, 50, HEMP, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((ph - 2) / 0.4))

# ================================================================ 第四回 旧案清算
def art_c_deng_dies(A, cv, t, u):
    for k in range(40):
        q = (t * 0.4 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=220)
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 30, 230, dir=1, robe=True, hat='crown', arm=lerp(20, 120, ease_out((u - P) / 0.6)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('安帝亲政', 46), 860, 880, t, t - u + P, rot=6)

def art_c_grandmother(A, cv, t, u):
    A.d['mid'].chord((360, 1200, 720, GROUND + 160), 180, 360, fill=230)
    ground(A, GROUND)
    person(A, 820, GROUND, 220, dir=-1, robe=True, hat='crown', kneel=True, bow=40, arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('宋贵人', 50), 540, 1100, t, t - u + 0.5)
    paste(cv, text_img('四十年前的旧案', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_c_summons(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(1100, 700, ease_out(u / (1.5 * P)))
    person(A, x, GROUND, 210, dir=-1, robe=True, hat='none', arm=lerp(20, 100, ease_out((u - 1.5 * P) / 0.4)), layer='ink')
    scroll(A, x - 130, GROUND - 180, 140, 50, (u - 1.5 * P) / 0.4, layer='yellow')
    cai(A, 300, GROUND, 220, dir=1, arm=-8)
    A.flush(cv)
    stamp(cv, seal('廷尉', 54, INK), 860, 880, t, t - u + 2 * P, rot=6)

def art_c_poison(A, cv, t, u):
    """6-beat set piece: 饮药而死 — he bathes, puts on his formal robes and hat, sits upright, and drinks."""
    ph = u / P
    A.d['mid'].rectangle((200, 900, 880, GROUND), fill=190)
    ground(A, GROUND)
    if ph < 2:
        A.d['pulp'].ellipse((360, GROUND - 80, 720, GROUND), fill=200)
        person(A, 540, GROUND - 30, 140, dir=1, robe=False, hat='knot', kneel=True, arm=60, layer='ink')
        for k in range(6):
            q = (t * 0.5 + k / 6) % 1
            A.d['wash'].ellipse((420 + k * 40 - 8, lerp(GROUND - 80, GROUND - 260, q) - 8, 420 + k * 40 + 8, lerp(GROUND - 80, GROUND - 260, q) + 8), fill=int(200 * (1 - q)))
    elif ph < 3.5:
        cai(A, 540, GROUND, 230, dir=1, arm=lerp(20, 140, ease_out((ph - 2) / 1)))
    else:
        sitter(A, 540, GROUND, 200, dir=1, bow=lerp(0, 50, ease_out((ph - 4.5) / 1)))
        A.d['ink'].chord((610, GROUND - 140, 660, GROUND - 110), 0, 180, fill=255)
    lamp(A, 860, GROUND, 50, t, glow=clamp(1 - (ph - 4.5) / 1))
    A.flush(cv)
    lab = '沐浴' if ph < 2 else ('整衣冠' if ph < 3.5 else '饮药而死')
    paste(cv, text_img(lab, SERIF, 54, ZHU if ph >= 3.5 else HEMP, 'Black', bleed=False, spacing=10), W / 2, 830, 1, 1)

def art_c_abolished(A, cv, t, u):
    palace(A, 540, GROUND, 460, layer='hemp')
    ground(A, GROUND)
    p = ease_out((u - P) / P)
    A.d['red'].line((300, 940, 300 + 480 * p, 940 + 380 * p), fill=255, width=12)
    A.flush(cv)
    stamp(cv, seal('国除', 60, INK), 540, 880, t, t - u + 0.4)

WEST = [('洛阳', 920, 1020, 105), ('撒马尔罕', 640, 940, 751), ('巴格达', 470, 1080, 794), ('开罗', 340, 1240, 900),
        ('西班牙', 180, 960, 1150), ('意大利', 300, 840, 1276)]
def art_c_west(A, cv, t, u):
    """8-beat set piece: 纸的西传 — from 洛阳 the route crawls west across the map, one city and year per beat."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 780, 970, 1420), radius=24, fill=190)
    A.d['ocean'].polygon([(130, 1100), (420, 1120), (520, 1180), (300, 1300), (130, 1260)], fill=110)
    n = min(len(WEST), int(ph / 1.2) + 1)
    for i in range(1, n):
        (_, x0, y0, _), (_, x1, y1, _) = WEST[i - 1], WEST[i]
        f = clamp((ph - (i - 1) * 1.2) / 1.0)
        A.d['pulp'].line((x0, y0, lerp(x0, x1, f), lerp(y0, y1, f)), fill=255, width=8)
    nm, x, y, yr = WEST[n - 1]
    sheet(A, x, y + 40, 50, 36, rot=0.2 * math.sin(t * 3))
    A.flush(cv)
    for i in range(n):
        nm2, x2, y2, yr2 = WEST[i]
        stamp(cv, seal(nm2, 28, ZHU if i == 0 else HEMP), x2, y2 - 46, t, t - u + i * 1.2 * P)
    paste(cv, text_img(f'公元{yr}年 · {nm}', SERIF, 48, HEMP, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)

# ================================================================ 第五回 纸寿千年
def art_c_europe(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((300, 1000, 760, GROUND), fill=210)
    A.d['ink'].polygon([(280, 1000), (780, 1000), (530, 880)], fill=255)
    A.d['ink'].ellipse((780, 1140, 940, 1300), outline=255, width=8)
    for k in range(8):
        a = k * math.pi / 4 + t
        A.d['ink'].line((860, 1220, 860 + 80 * math.cos(a), 1220 + 80 * math.sin(a)), fill=255, width=4)
    A.d['ocean'].rectangle((780, 1300, 1000, GROUND), fill=150)
    for k in range(3):
        sheet(A, 160, 1080 + k * 30, 80, 60)
    A.flush(cv)
    stamp(cv, seal('造纸坊', 50), 530, 860, t, t - u + P)

def art_c_printing(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((360, 900, 720, 940), fill=255)
    A.d['ink'].rectangle((520, 940, 560, 1100 + 40 * math.sin(t * 4)), fill=255)
    A.d['hemp'].rectangle((360, 1140, 720, 1180), fill=255)
    for k in range(int(clamp(u / (2 * P)) * 20)):
        sheet(A, 160 + (k % 10) * 80, GROUND - 20 - (k // 10) * 30, 60, 20)
    A.flush(cv)
    paste(cv, text_img('纸 加上 印刷', SERIF, 50, HEMP, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_c_baqiao(A, cv, t, u):
    A.d['mid'].rectangle((200, 1100, 880, GROUND), fill=170)
    ground(A, GROUND)
    for k in range(2):
        person(A, 360 + k * 300, 1100, 150, dir=1 if k == 0 else -1, robe=False, hat='knot', bow=50, arm=150, layer='ink')
    sheet(A, 540, 1060, 120 * ease_out(u / P) + 4, 80, tone=150, layer='hemp')
    A.flush(cv)
    stamp(cv, seal('灞桥纸', 50), 860, 880, t, t - u + P, rot=6)

def art_c_hundred(A, cv, t, u):
    ground(A, GROUND)
    n = min(100, int(clamp(u / (2 * P)) * 100) + 1)
    for i in range(n):
        x = 110 + (i % 20) * 44; y = GROUND - 30 - (i // 20) * 50
        A.d['pulp' if i == 6 else 'mid'].ellipse((x - 14, y - 14, x + 14, y + 14), fill=255)
    A.flush(cv)
    if n > 6:
        stamp(cv, seal('第七', 40), 110 + 6 * 44, GROUND - 100, t, t - u + 0.5)
    paste(cv, text_img('影响人类进程的一百人', SERIF, 46, HEMP, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_c_tomb(A, cv, t, u):
    A.d['mid'].chord((340, 1120, 740, GROUND + 260), 180, 360, fill=230)
    for k in range(4):
        A.d['hemp'].rectangle((200 + k * 200, GROUND - 160, 220 + k * 200, GROUND), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('龙亭', 56), 540, 1060, t, t - u + P)
    paste(cv, text_img('陕西洋县 · 蔡伦墓', SERIF, 48, HEMP, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_c_today(A, cv, t, u):
    ground(A, GROUND)
    for k in range(12):
        x = 120 + (k % 6) * 170; y = 980 + (k // 6) * 160
        sheet(A, x, y + 6 * math.sin(t * 2 + k), 120, 90, rot=0.05 * math.sin(t + k))
    A.flush(cv)
    paste(cv, text_img('你手中的每一张纸', SERIF, 50, PULP, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_c_legacy(A, cv, t, u):
    sheet(A, 540, 1060, 460, 340)
    ground(A, GROUND)

def art_c_title(A, cv, t, u):
    vat(A, 820, 1460, 320, 200)
    cai(A, 400, 1460, 680, dir=1, arm=lerp(-5, 45, ease_out(u / (2 * P))))
    sheet(A, 600, 1100, 160, 120)

# ================================================================ script
CHAPTERS = {16: ('第一回', '入宫为宦'), 48: ('第二回', '竹简太重'), 80: ('第三回', '蔡侯之纸'),
            112: ('第四回', '旧案清算'), 144: ('第五回', '纸寿千年')}

CARDS = [
    C(0, 2, 'works', 'num', num='破布渔网', line='变成了纸', art=art_c_hook_rags),
    C(2, 4, 'empire', 'num', num='四大发明', line='其一与他有关', art=art_c_hook_four),
    C(4, 6, 'court', 'num', num='宦官', line='改变了世界', art=art_c_hook_eunuch),
    C(6, 8, 'death', 'num', num='饮药自尽', line='为一桩旧案', art=art_c_hook_cup),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 入宫为宦
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=63, main='生于耒阳', sub='桂阳郡 耒阳县', note='生年不详 一说六十一年', art=art_c_leiyang),
    C(22, 26, 'court', 'card', year=75, main='入宫', sub='少年入宫为宦官', note='永平末', art=art_c_enter),
    C(26, 30, 'court', 'card', year=76, main='小黄门', sub='在宫中当差', art=art_c_huangmen),
    C(30, 34, 'night', 'card', year=82, main='宋贵人案', sub='奉窦皇后之命 · 诬陷宋贵人', note='宋贵人被逼自尽', art=art_c_song_case),
    C(34, 38, 'empire', 'card', year=88, main='中常侍', sub='和帝即位 · 参与机密', art=art_c_changshi),
    C(38, 42, 'war', 'card', year=92, main='窦氏倒台', sub='和帝诛窦宪', art=art_c_dou_falls),
    C(42, 48, 'works', 'card', year=97, main='尚方令', sub='主管宫廷器物制造', note='为后世法', art=art_c_shangfang),
    # ---- 第二回 竹简太重
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'life', 'card', year=97, main='竹简笨重', sub='读一部书 · 要搬一车', note='始皇日阅奏章一石', art=art_c_heavy),
    C(54, 58, 'court', 'card', year=97, main='缣帛昂贵', sub='丝织品写字 · 贵不堪用', art=art_c_silk),
    C(58, 62, 'works', 'card', year=100, main='早期麻纸', sub='西汉已有粗糙麻纸', art=art_c_early),
    C(62, 66, 'empire', 'card', year=102, main='邓皇后', sub='好文墨 · 不喜珍玩', note='岁时但供纸墨而已', art=art_c_deng),
    C(66, 74, 'works', 'papermaking', year=104),
    C(74, 80, 'empire', 'card', year=105, main='奏上新纸', sub='和帝大为赞赏', art=art_c_present),
    # ---- 第三回 蔡侯之纸
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'life', 'card', year=105, main='天下咸称', sub='人们叫它蔡侯纸', art=art_c_named),
    C(86, 90, 'death', 'card', year=105, main='和帝驾崩', sub='邓太后临朝', art=art_c_hedi_dies),
    C(90, 94, 'works', 'card', year=107, main='纸张流行', sub='公文书信 · 开始用纸', art=art_c_spread),
    C(94, 98, 'court', 'card', year=114, main='龙亭侯', sub='封邑三百户', art=art_c_marquis),
    C(98, 102, 'works', 'card', year=117, main='东观校书', sub='监督校订经传', art=art_c_dongguan),
    C(102, 106, 'court', 'card', year=117, main='长乐太仆', sub='太后宫中要职', art=art_c_taipu),
    C(106, 112, 'life', 'card', year=120, main='纸写经典', sub='知识变得便宜', art=art_c_books),
    # ---- 第四回 旧案清算
    C(112, 114, 'night', 'chapter'),
    C(114, 118, 'death', 'card', year=121, main='邓太后崩', sub='安帝亲政', art=art_c_deng_dies),
    C(118, 122, 'night', 'card', year=121, main='祖母之冤', sub='安帝正是宋贵人之孙', art=art_c_grandmother),
    C(122, 126, 'court', 'card', year=121, main='下诏廷尉', sub='令其自往廷尉受审', art=art_c_summons),
    C(126, 132, 'death', 'card', year=121, main='饮药而死', sub='耻受辱', note='乃沐浴 整衣冠 饮药而死', art=art_c_poison),
    C(132, 136, 'fate', 'card', year=121, main='国除', sub='封国被撤', art=art_c_abolished),
    C(136, 144, 'works', 'card', year=751, main='纸的西传', sub='沿丝路 一路向西', note='一说经怛罗斯之战传入中亚', art=art_c_west),
    # ---- 第五回 纸寿千年
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'works', 'card', year=1150, main='纸入欧洲', sub='西班牙出现造纸作坊', art=art_c_europe),
    C(150, 154, 'empire', 'card', year=1450, main='纸与印刷', sub='书走进千家万户', art=art_c_printing),
    C(154, 158, 'life', 'card', year=1957, main='灞桥纸', sub='考古发现西汉麻纸', note='造纸术非他首创 他让纸变得好用', art=art_c_baqiao),
    C(158, 162, 'empire', 'card', year=1978, main='百人榜', sub='影响人类进程 · 位列第七', note='麦克 哈特 著', art=art_c_hundred),
    C(162, 166, 'court', 'card', year=2001, main='蔡伦墓', sub='列为全国重点文物保护单位', art=art_c_tomb),
    C(166, 170, 'end', 'card', year=2026, main='纸寿千年', sub='至今仍在用', art=art_c_today),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='叁拾', col=HEMP, acc=PULP, born=63, died=121, no_age=True,
    born_lab='生年不详', died_lab='121年', years_txt='生年不详 — 公元121',
    hook_q='一个宦官 · 怎么改变了人类的书写？',
    name_line='蔡伦 · 字敬仲', name='蔡伦', seal='龙亭', title_art=art_c_title,
    q1='发明家？', q2='改良者？',
    end_art=art_c_legacy, end_big='蔡侯纸', end_seal='龙亭',
    end_l1='他是宦官 也卷入过冤案', end_l2='却让全人类有了纸',
    end_brush='纸寿千年', end_ask='功与过 能相抵吗？评论区聊聊', next='李白'),
    scenes=dict(chapter=scene_chapter, papermaking=scene_papermaking))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
