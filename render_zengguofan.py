"""千古人物志 · 第柒拾肆集 · 曾国藩 (1811–1872)
Look: 湘江蓝 + 灯火黄, 油灯 corner borders, 湘乡 hills and the 湘江 behind.
Chapter card: 日课十二条 — a board of twelve squares; each chapter more squares are ticked in red; in the last chapter all twelve are done.
Set pieces: custom 8-beat scene 'jinggang' (靖港投水), 6-beat 小偷背书, 6-beat 湘军成军, 6-beat 屡败屡战, 6-beat 安庆围城,
6-beat 天京, 6-beat 天津教案, 6-beat 家书.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_xuxiake as Xk         # engine + helpers (previous episode)
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
from render_sunwu import army, banner
from render_linzexu import foreigner, warship
from render_zhuxi import book

F.RIPPLE = False
XIANGLAN = (60, 86, 108)            # 湘江蓝
DENGHUO = (212, 158, 70)            # 灯火黄
S.LAYERS.append(('xianglan', XIANGLAN, 0.9, 1.0))
S.LAYERS.append(('denghuo', DENGHUO, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='曾', life='湘', court='清', night='省', war='战', empire='督', works='勤', fate='拙', death='败', end='恒')
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
G.THEMES['empire']['sun'] = (XIANGLAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (DENGHUO, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # 湘江
    _d.line([(60 + i * 30, 1456 + _k * 14 + 5 * math.sin(i * 0.4 + _k)) for i in range(34)], fill=XIANGLAN + (48 - _k * 10,), width=3)
for _x in (120, 960):               # paddy terraces at the margins
    for _s in range(4):
        _d.line((_x - 70 + _s * 8, 1430 - _s * 22, _x + 70 - _s * 8, 1430 - _s * 22), fill=(110, 130, 90, 60), width=3)
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (92, 96, 104)}
def draw_background(t, theme):
    """湘乡: rounded hills, terraces and the 湘江."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 192, 194), (156, 164, 172), MTN_COL.get(theme, (100, 116, 128))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """油灯: a small oil lamp with a flame in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=XIANGLAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=XIANGLAN + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.chord((cx - 26, cy - 6, cx + 26, cy + 22), 0, 180, fill=XIANGLAN + (230,))
        d.rectangle((cx - 4, cy + 20, cx + 4, cy + 32), fill=XIANGLAN + (230,))
        d.ellipse((cx - 7, cy - 26, cx + 7, cy - 4), fill=DENGHUO + (240,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def zeng(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """曾国藩: Qing official — 顶戴 hat with a red knob, queue, a full beard (grey when old), mandarin square."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.1 * h, y - 1.02 * h, x + 0.1 * h, y - 0.86 * h), 180, 360, fill=255)
        d.rectangle((x - 0.11 * h, y - 0.95 * h, x + 0.11 * h, y - 0.93 * h), fill=255)
        A.d['red'].ellipse((x - 0.025 * h, y - 1.06 * h, x + 0.025 * h, y - 1.01 * h), fill=255)
        d.line((x - dir * 0.05 * h, y - 0.88 * h, x - dir * 0.08 * h, y - 0.55 * h), fill=255, width=max(2, int(0.015 * h)))
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.0 * h, y - 0.85 * h), (x + dir * 0.09 * h, y - 0.85 * h), (x + dir * 0.06 * h, y - 0.66 * h), (x + dir * 0.01 * h, y - 0.7 * h)], fill=255)
        A.d['xianglan'].rectangle((x - 0.07 * h, y - 0.72 * h, x + 0.07 * h, y - 0.6 * h), fill=255)
    return hand

def soldier(A, x, y, h, dir=1, layer='xianglan', **kw):
    """湘勇: a 湘军 soldier — round cap, a 勇 vest, a spear."""
    kw.setdefault('spear', True)
    kw.setdefault('arm', 40)
    hand = person(A, x, y, h, dir=dir, robe=False, hat='knot', layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        A.d['wash'].ellipse((x - 0.05 * h, y - 0.66 * h, x + 0.05 * h, y - 0.56 * h), fill=230)
    return hand

def tick_board(A, cx, cy, s, n):
    A.d['wash'].rectangle((cx - s, cy - 0.75 * s, cx + s, cy + 0.75 * s), fill=255)
    A.d['ink'].rectangle((cx - s, cy - 0.75 * s, cx + s, cy + 0.75 * s), outline=255, width=5)
    for i in range(12):
        x = cx - 0.75 * s + (i % 4) * 0.5 * s; y = cy - 0.45 * s + (i // 4) * 0.45 * s
        A.d['ink'].rectangle((x - 0.17 * s, y - 0.17 * s, x + 0.17 * s, y + 0.17 * s), outline=200, width=3)
        if i < n:
            A.d['red'].line([(x - 0.1 * s, y), (x - 0.02 * s, y + 0.09 * s), (x + 0.12 * s, y - 0.1 * s)], fill=255, width=max(4, int(0.04 * s)))

def letter(A, cx, cy, w, h):
    A.d['wash'].rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), fill=255)
    A.d['red'].rectangle((cx - w / 2 + 6, cy - h / 2 + 6, cx + w / 2 - 6, cy + h / 2 - 6), outline=200, width=2)
    for k in range(6):
        x = cx + w / 2 - 20 - k * (w - 40) / 6
        A.d['ink'].line((x, cy - h / 2 + 20, x, cy + h / 2 - 20 - 30 * (k % 3)), fill=170, width=3)

# ================================================================ chapter card
CH = {16: (0, 2), 48: (2, 5), 80: (5, 8), 112: (8, 11), 144: (11, 12)}
def art_tick_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (2, 5))
    q = ease_out(u / (1.2 * P))
    tick_board(A, 540, 1060, 280, int(lerp(a, b, clamp((q - 0.2) / 0.6))))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_tick_chapter)
    ink_in(cv, text_img(no, SERIF, 56, XIANGLAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_z_hook_thief(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((300, GROUND - 260, 780, GROUND), fill=230)
    A.d['ink'].polygon([(280, GROUND - 260), (800, GROUND - 260), (540, GROUND - 330)], fill=255)
    A.d['denghuo'].rectangle((480, GROUND - 180, 600, GROUND - 100), fill=255)
    person(A, 860, GROUND, 120, dir=-1, robe=False, hat='knot', kneel=True, bow=20, layer='ink')

def art_z_hook_seven(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    for i in range(min(7, int(u / (0.15 * P)) + 1)):
        stamp(cv, seal('落', 40, ZHU if i < 6 else INK), 180 + i * 120, 1100 + 30 * (i % 2), t, t - u + i * 0.15 * P)

def art_z_hook_water(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=150)
    river(A, 1170, t, rows=3, amp=6)
    q = clamp(u / (1.2 * P))
    zeng(A, 540, lerp(1100, 1260, q), 180, dir=1, fall=lerp(0, 70, q), arm=150)

def art_z_hook_letter(A, cv, t, u):
    ground(A, GROUND)
    for k in range(min(5, int(u / (0.25 * P)) + 1)):
        letter(A, 300 + k * 120, 1150 - 20 * k, 150, 240)

# ================================================================ 第一回 笨人
def art_z_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x - 60, GROUND - 260), (x + 60, GROUND - 260), (x + 220, GROUND)], fill=150)
    for s in range(4):
        A.d['grass'].line((200 + s * 20, GROUND - 20 - s * 30, 880 - s * 20, GROUND - 20 - s * 30), fill=200, width=6)
    A.d['wash'].rectangle((440, GROUND - 160, 640, GROUND), fill=255)
    A.d['ink'].polygon([(420, GROUND - 160), (660, GROUND - 160), (540, GROUND - 220)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('湖南湘乡荷叶塘 · 祖辈务农', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('湘乡', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_thief(A, cv, t, u):
    """6-beat set piece: 小偷背书 — legend: a thief hides under his eaves waiting for him to sleep; he reads one essay over and over and still cannot recite it;
    the thief jumps out, recites it perfectly, and leaves."""
    ph = u / P
    ground(A, GROUND)
    A.d['wash'].rectangle((300, GROUND - 260, 780, GROUND), fill=230)
    A.d['ink'].polygon([(280, GROUND - 260), (800, GROUND - 260), (540, GROUND - 330)], fill=255)
    A.d['denghuo'].rectangle((360, GROUND - 200, 560, GROUND - 90), fill=255)
    person(A, 460, GROUND - 90, 80, dir=1, robe=True, hat='none', kneel=True, bow=lerp(0, 20, 0.5 + 0.5 * math.sin(t * 2)), arm=90, layer='ink')
    if ph < 3.5:
        person(A, 880, GROUND, 120, dir=-1, robe=False, hat='knot', kneel=True, bow=20, layer='ink')
    else:
        q = clamp((ph - 3.5) / 1.5)
        person(A, lerp(880, 1100, q), GROUND, 180, dir=1 if q > 0.4 else -1, robe=False, hat='knot', ph=t * 5 if q > 0.4 else None, arm=lerp(120, -8, q), layer='ink')
    A.flush(cv)
    if ph < 1.5:
        lab, col = '夜读一篇文章 反复诵读', XIANGLAN
    elif ph < 3.5:
        lab, col = '读到深夜 仍背不下来', XIANGLAN
    else:
        lab, col = '梁上小偷跳出 一字不差背完 扬长而去', ZHU
    paste(cv, text_img(lab, SERIF, 44 if ph >= 3.5 else 46, col, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    note_in(cv, '民间流传之说 未见正史', t, t - u + P)

def art_z_xiucai(A, cv, t, u):
    ground(A, GROUND)
    for r in range(2):
        for i in range(6):
            x = 160 + i * 150; y = GROUND - r * 170
            A.d['mid'].rectangle((x - 55, y - 130, x + 55, y), fill=200)
    person(A, 540, GROUND, 170, dir=1, robe=True, hat='knot', arm=lerp(-8, 60, ease_out((u - 2 * P) / 0.6)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('考了七次 · 二十三岁才中秀才', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('秀才', 56), 860, 1020, t, t - u + 2 * P, rot=6)

def art_z_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='xianglan')
    ground(A, GROUND)
    zeng(A, 540, GROUND, 200, dir=1, bow=15, arm=-8)
    A.flush(cv)
    paste(cv, text_img('第三次会试 · 中同进士出身', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '名次靠后 自觉羞愧 几欲不就', t, t - u + P)

def art_z_disheng(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='xianglan')
    zeng(A, 280, GROUND, 170, dir=1, kneel=True, bow=20, arm=90)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    type_in(cv, text_img('从前种种 譬如昨日死', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.6)
    note_in(cv, '号涤生 取涤除旧染 重新做人之意', t, t - u + P)

def art_z_rike(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='xianglan')
    zeng(A, 280, GROUND, 170, dir=1, kneel=True, bow=20, arm=90)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    tick_board(A, 560, GROUND - 200, 90, int(clamp(u / (2.5 * P)) * 12))
    A.flush(cv)
    paste(cv, text_img('立日课十二条 · 每日写日记反省', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '同年戒烟 此后终身不吸', t, t - u + P)

def art_z_qiqian(A, cv, t, u):
    for k in range(7):
        A.d['xianglan' if k % 2 else 'mid'].rectangle((300 + k * 20, GROUND - 40 - k * 40, 780 - k * 20, GROUND - k * 40), fill=230 - k * 10)
    ground(A, GROUND)
    zeng(A, 540, GROUND - 280, 150, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('十年七迁 · 三十七岁官至二品', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('侍郎', 56), 860, 1440, t, t - u + P, rot=6)

# ================================================================ 第二回 湘军
def art_z_mother(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, female=True, layer='ink')
    zeng(A, 880, GROUND, 160, dir=-1, kneel=True, bow=30)
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('母亲去世 · 回湘乡守制', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_tuanlian(A, cv, t, u):
    """6-beat set piece: 湘军成军 — ordered to raise local militia, he recruits honest mountain farmers, officers from scholars, and builds a navy."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        zeng(A, 300, GROUND, 190, dir=1, arm=lerp(-8, 120, clamp(ph / 0.6)))
        for j in range(4):
            person(A, lerp(1100, 560, clamp(ph / 2)) + j * 110, GROUND, 140, dir=-1, robe=False, hat='knot', load=True, arm=160, ph=t * 4 + j, layer='mid')
        lab = '奉旨帮办团练 · 招募朴实山农'
    elif ph < 4:
        n = int(clamp((ph - 2) / 1.5) * 8) + 1
        for j in range(n):
            soldier(A, 140 + j * 110, GROUND, 150, dir=1)
        banner(A, 980, GROUND, 360, t, layer='xianglan')
        lab = '以书生为将 以山农为兵'
    else:
        A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=150)
        river(A, 1250, t, rows=2, amp=4)
        for k in range(5):
            boat(A, 140 + k * 190, 1260, 70, t)
        lab = '水陆两军 · 一万七千人'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, XIANGLAN if ph < 4 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('湘军', 60), 860, 1020, t, t - u + 4 * P, rot=6)

def scene_jinggang(cv, t, c, k):
    """8-beat custom scene: 靖港之败 — his first battle: the fleet is routed at 靖港; ashamed, he leaps into the river; an aide drags him out;
    he writes his last letter — and then word comes that 塔齐布 has won at 湘潭."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['ocean'].rectangle((0, 1120, W, GROUND + 40), fill=150)
    river(A, 1130, t, rows=3, amp=6)
    if ph < 2:
        for k in range(5):
            boat(A, 140 + k * 190, 1140 + 10 * math.sin(t * 2 + k), 70, t)
        flames(A, 540, 1120, 700, 160 * clamp(ph / 1.2), t, n=6, seed=1854, smoke=True)
        lab, col = '初战靖港 水师溃败', ZHU
    elif ph < 4:
        q = clamp((ph - 2) / 1)
        boat(A, 400, 1140, 110, t)
        zeng(A, lerp(420, 620, q), lerp(1110, 1240, q), 160, dir=1, fall=lerp(0, 70, q), arm=150)
        if ph > 3:
            person(A, 520, 1130, 140, dir=1, robe=False, hat='knot', bow=50, arm=150, layer='xianglan')
        lab, col = ('羞愤投水' if ph < 3 else '被部下章寿麟救起'), ZHU
    elif ph < 6:
        A.d['ocean'].rectangle((0, 1120, W, GROUND + 40), fill=0)
        ground(A, GROUND)
        desk(A, 540, GROUND, 400, layer='xianglan')
        zeng(A, 300, GROUND, 170, dir=1, kneel=True, bow=30, arm=90)
        lamp(A, 760, GROUND - 74, 30, t, glow=0.7)
        lab, col = '回营写下遗书', XIANGLAN
    else:
        ground(A, GROUND)
        for j in range(3):
            rider(A, lerp(-100, 600, clamp((ph - 6) / 1.5)) - j * 130, GROUND, 110, dir=1, ph=t * 6 + j, layer='xianglan')
        zeng(A, 820, GROUND, 180, dir=-1, arm=lerp(-8, 90, clamp((ph - 6.5) / 0.6)))
        lab, col = '忽报 湘潭大捷', XIANGLAN
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '靖港投水', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=74)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    if ph >= 6:
        note_in(cv, '同一天 塔齐布大破太平军于湘潭', t, s0 + 6 * P)

def art_z_wuchang(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='武昌', layer='mid', open_=1.0)
    ground(A, GROUND)
    for j in range(6):
        soldier(A, lerp(-100, 400, ease_out(u / (2.5 * P))) + j * 80, GROUND, 120, dir=1, ph=t * 4 + j)
    A.flush(cv)
    paste(cv, text_img('湘军克复武昌 · 咸丰大喜', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '旋有人进言 一呼万众 恐非国家之福', t, t - u + P)

def art_z_hukou(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=140)
    river(A, 1170, t, rows=3, amp=5)
    boat(A, 540, 1180, 130, t)
    flames(A, 540, 1160, 220, 140 * clamp(u / (1.5 * P)), t, n=3, seed=1855, smoke=True)
    A.flush(cv)
    paste(cv, text_img('湖口兵败 · 座船被夺 再欲投水', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_reflect(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='xianglan')
    zeng(A, 280, GROUND, 170, dir=1, kneel=True, bow=30, arm=-8, old=0.3)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.7)
    A.flush(cv)
    paste(cv, text_img('父丧回乡 · 闭门思过一年有余', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '自省早年过于刚直 处处碰壁', t, t - u + P)

# ================================================================ 第三回 屡败屡战
def art_z_return(A, cv, t, u):
    ground(A, GROUND)
    zeng(A, lerp(120, 540, ease_out(u / (2.5 * P))), GROUND, 190, dir=1, ph=t * 3 if u < 2.5 * P else None, arm=-8, old=0.3)
    A.flush(cv)
    paste(cv, text_img('再度出山 · 待人处事由刚转柔', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_loubai(A, cv, t, u):
    """6-beat set piece: 屡败屡战 — the draft reads 屡战屡败 (defeated in every battle); he swaps two characters: 屡败屡战 (beaten again and again, fights again and again)."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='xianglan')
    zeng(A, 260, GROUND, 180, dir=1, kneel=True, arm=lerp(80, 110, 0.5 + 0.5 * math.sin(t * 3)), old=0.3)
    scroll(A, 560, 1000, 460, 200, 1.0, layer='wash')
    A.flush(cv)
    if ph < 2.5:
        txt, col = '屡战屡败', INK
    else:
        txt, col = '屡败屡战', ZHU
    q = clamp((ph - 2) / 0.5) if ph < 2.5 else clamp((ph - 2.5) / 0.5)
    paste(cv, text_img(txt, SERIF, 80, col, 'Black', bleed=False, spacing=10), 560, 1000, 1, 1 - q if ph < 2.5 else q)
    lab = '奏报战况 原稿写作' if ph < 2.5 else '只调换两字'
    paste(cv, text_img(lab, SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4:
        paste(cv, text_img('败了再战 这就是他', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4) / 0.4))
    note_in(cv, '此为后世流传之说 出处难考', t, t - u + P)

def art_z_liangjiang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='denghuo')
    ground(A, GROUND)
    zeng(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)), old=0.4)
    A.flush(cv)
    paste(cv, text_img('署两江总督 · 授钦差大臣', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('两江', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_qimen(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x, GROUND - 360), (x + 160, GROUND)], fill=150)
    A.d['xianglan'].polygon([(380, GROUND), (540, GROUND - 200), (700, GROUND)], fill=230)
    zeng(A, 540, GROUND, 140, dir=1, kneel=True, bow=20, arm=90, old=0.4)
    for j in range(8):
        a = j * 2 * math.pi / 8
        person(A, 540 + 440 * math.cos(a), GROUND - 10 * (j % 2), 90, dir=-1 if math.cos(a) > 0 else 1, robe=False, hat='knot', spear=True, arm=40, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('驻祁门遭围 · 帐中悬刀 预写遗嘱', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_anqing(A, cv, t, u):
    """6-beat set piece: 安庆 — 结硬寨 打呆仗: trench after trench around the city; the relief armies break on them; 安庆 falls."""
    ph = u / P
    city_wall(A, 360, 720, 1080, gate_x=540, label='安庆', layer='mid', open_=1.0 if ph >= 4.5 else 0.0)
    n = min(4, int(clamp(ph / 3) * 4) + 1)
    for k in range(n):
        r = 240 + k * 70
        A.d['dune'].arc((540 - r - 200, GROUND - 100 - 0.3 * r, 540 + r + 200, GROUND + 0.3 * r), 180, 360, fill=230, width=12)
    if 3 <= ph < 4.5:
        army(A, -120, GROUND, 4, dir=1, layer='ink', t=t, march=True, h=90)
    if ph >= 4.5:
        for j in range(5):
            soldier(A, 300 + j * 110, GROUND, 120, dir=1, ph=t * 4 + j)
    ground(A, GROUND)
    A.flush(cv)
    lab = '结硬寨 打呆仗' if ph < 3 else ('援军屡攻壕垒不下' if ph < 4.5 else '围城一年 安庆克复')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4.5 else XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '每到一处 先挖壕筑墙 再言战事', t, t - u + P)

def art_z_arsenal(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=3)
    x = lerp(160, 620, ease_out(u / (3 * P)))
    A.d['ink'].polygon([(x - 120, 1200), (x + 140, 1200), (x + 110, 1236), (x - 100, 1236)], fill=255)
    A.d['ink'].rectangle((x - 10, 1120, x + 14, 1200), fill=255)
    A.d['ink'].ellipse((x - 70, 1150, x - 10, 1210), outline=255, width=6)
    for k in range(4):
        q = (t * 0.6 + k / 4) % 1
        A.d['wash'].ellipse((x - 10 - 20 * q, 1100 - 180 * q - 18, x + 30 + 20 * q, 1100 - 180 * q + 18), fill=int(200 * (1 - q)))
    A.flush(cv)
    paste(cv, text_img('设安庆内军械所 · 自造轮船', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '徐寿 华蘅芳主持 黄鹄号于1865年造成', t, t - u + P)

# ================================================================ 第四回 天京
def art_z_tianjing(A, cv, t, u):
    """6-beat set piece: 天京 — 曾国荃's army besieges 天京 for two years; a mine tunnel is blown under the wall; the city falls."""
    ph = u / P
    city_wall(A, 220, 860, 1040, gate_x=None, label='天京', layer='mid')
    if ph < 2:
        for j in range(6):
            soldier(A, 120 + j * 160, GROUND, 110, dir=1, arm=40)
        lab = '围城两年'
    elif ph < 3.5:
        q = clamp((ph - 2) / 1.5)
        A.d['ink'].line((80, GROUND - 20, lerp(80, 540, q), GROUND - 20), fill=200, width=10)
        lab = '挖掘地道 直抵城下'
    else:
        flames(A, 540, 1080, 300, 260 * clamp((ph - 3.5) / 0.6), t, n=5, seed=1864, smoke=True)
        for j in range(6):
            soldier(A, lerp(100, 480, clamp((ph - 4) / 1.5)) + j * 60, GROUND, 110, dir=1, ph=t * 5 + j)
        lab = '轰塌城墙 天京陷落'
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '主将为其弟曾国荃 城破后屠掠甚惨', t, t - u + 3.5 * P)

def art_z_disband(A, cv, t, u):
    ground(A, GROUND)
    for j in range(8):
        soldier(A, lerp(500, -120, ((t * 0.08 + j / 8) % 1)) + 300 * (j % 2), GROUND, 110, dir=-1, ph=t * 4 + j, spear=False, arm=-8)
    zeng(A, 820, GROUND, 190, dir=-1, arm=-8, old=0.5)
    A.flush(cv)
    paste(cv, text_img('功成之日 · 主动裁撤湘军', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '以释朝廷猜疑 自剪羽翼', t, t - u + P)

def art_z_jiangnan(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].rectangle((x - 110, GROUND - 200, x + 110, GROUND), fill=220)
        A.d['ink'].rectangle((x + 50, GROUND - 320, x + 80, GROUND - 200), fill=255)
        q = (t * 0.4 + k / 3) % 1
        A.d['wash'].ellipse((x + 40 - 20 * q, GROUND - 340 - 160 * q - 20, x + 90 + 20 * q, GROUND - 340 - 160 * q + 20), fill=int(200 * (1 - q)))
    A.flush(cv)
    paste(cv, text_img('与李鸿章筹设江南制造总局', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('洋务', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_nian(A, cv, t, u):
    ground(A, GROUND)
    for j in range(5):
        rider(A, lerp(-100, 1200, ((t * 0.15 + j / 5) % 1)), GROUND, 110, dir=1, ph=t * 6 + j, layer='ink')
    zeng(A, 200, GROUND, 180, dir=1, arm=-8, old=0.6)
    A.flush(cv)
    paste(cv, text_img('北上剿捻无功 · 改由李鸿章接替', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_zhili(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    zeng(A, 540, GROUND, 200, dir=1, arm=-8, old=0.6)
    A.flush(cv)
    paste(cv, text_img('调任直隶总督', SERIF, 48, XIANGLAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('直隶', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_tianjin(A, cv, t, u):
    """6-beat set piece: 天津教案 — rumours set a crowd on a church; foreigners are killed; gunboats gather; he settles it by compromise and is reviled."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        A.d['wash'].rectangle((560, GROUND - 260, 860, GROUND), fill=230)
        A.d['ink'].polygon([(540, GROUND - 260), (880, GROUND - 260), (710, GROUND - 360)], fill=255)
        flames(A, 710, GROUND - 200, 260, 160 * clamp(ph / 1), t, n=4, seed=1870, smoke=True)
        for j in range(6):
            person(A, 120 + j * 70, GROUND, 110, dir=1, robe=False, hat='knot', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 5 + j)), layer='ink')
        lab = '流言四起 · 民众焚毁教堂'
    elif ph < 4:
        A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
        waves(A, 1210, t, rows=2, amp=3)
        for k in range(3):
            warship(A, 220 + k * 300, 1220, 90, t)
        lab = '列强兵舰 陈于大沽'
    else:
        palace(A, 540, 1300, 320, layer='mid')
        zeng(A, 540, GROUND, 190, dir=1, bow=25, arm=-8, old=0.8)
        for j in range(4):
            person(A, 120 + j * 70 if j < 2 else 820 + (j - 2) * 70, GROUND, 120, dir=1 if j < 2 else -1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='mid')
        lab = '妥协处置 · 举国唾骂'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4 else XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4:
        note_in(cv, '自言 外惭清议 内疚神明', t, t - u + 4 * P)

def art_z_youtong(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=3)
    warship(A, lerp(300, 700, ease_out(u / (2 * P))), 1220, 100, t)
    A.flush(cv)
    paste(cv, text_img('联奏选派幼童赴美留学', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 家书
def art_z_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    zeng(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于南京两江总督署 · 年六十二', SERIF, 44, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_wenzheng(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('文正', 90, ZHU), 540, 1140, t, t - u + 0.6)
    paste(cv, text_img('谥文正 · 文臣最高的谥号之一', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_kids(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=3)
    warship(A, lerp(200, 800, ease_out(u / (3 * P))), 1220, 100, t)
    A.flush(cv)
    paste(cv, text_img('同年首批三十名幼童赴美', SERIF, 46, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '其中有后来修建京张铁路的詹天佑', t, t - u + P)

def art_z_letters(A, cv, t, u):
    """6-beat set piece: 家书 — over a thousand letters to his brothers and sons; the lines families still copy out."""
    ph = u / P
    ground(A, GROUND)
    n = min(8, int(clamp(ph / 2) * 8) + 1)
    for k in range(n):
        letter(A, 180 + k * 100, 1180 - 14 * (k % 3), 120, 200)
    A.flush(cv)
    lines = [('家俭则兴 人勤则健', XIANGLAN), ('能勤能俭 永不贫贱', XIANGLAN), ('庸人以惰败 才人以傲败', ZHU)]
    for i, (s, col) in enumerate(lines):
        st = t - u + (1.5 + i * 1.2) * P
        if t >= st:
            paste(cv, text_img(s, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 640 + i * 64, 1, clamp((t - st) / 0.4))
    note_in(cv, '曾国藩家书 日记 后世刊行不绝', t, t - u + P)

def art_z_verdict(A, cv, t, u):
    ground(A, GROUND)
    zeng(A, 540, GROUND, 220, dir=1, arm=-8, old=0.8)
    A.flush(cv)
    paste(cv, text_img('有人称他中兴名臣 有人骂他曾剃头', SERIF, 44, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '镇压太平天国 杀戮极重', t, t - u + 0.5)

def art_z_motto(A, cv, t, u):
    tick_board(A, 540, 1120, 220, 12)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('结硬寨 打呆仗 · 以拙胜巧', SERIF, 48, XIANGLAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_z_legacy(A, cv, t, u):
    lamp(A, 860, 1420, 40, t, glow=1.0)

def art_z_title(A, cv, t, u):
    lamp(A, 840, 1440, 60, t, glow=1.0)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    zeng(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '笨人'), 48: ('第二回', '湘军'), 80: ('第三回', '屡败屡战'),
            112: ('第四回', '天京'), 144: ('第五回', '家书')}

CARDS = [
    C(0, 2, 'night', 'num', num='一个小偷', line='比他先背会文章', art=art_z_hook_thief),
    C(2, 4, 'fate', 'num', num='考了七次', line='才中秀才', art=art_z_hook_seven),
    C(4, 6, 'death', 'num', num='两次投水', line='都被人救起', art=art_z_hook_water),
    C(6, 8, 'works', 'num', num='一千多封家书', line='读了一百多年', art=art_z_hook_letter),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 笨人
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1811, main='生于湘乡', sub='农家子弟', art=art_z_birth),
    C(22, 28, 'night', 'card', year=1825, main='梁上君子', sub='民间传说', art=art_z_thief),
    C(28, 32, 'fate', 'card', year=1833, main='七考秀才', sub='二十三岁', art=art_z_xiucai),
    C(32, 36, 'empire', 'card', year=1838, main='同进士', sub='第三次会试', art=art_z_jinshi),
    C(36, 40, 'works', 'card', year=1840, main='号涤生', sub='涤其旧染', art=art_z_disheng),
    C(40, 44, 'night', 'card', year=1842, main='日课十二条', sub='每日反省', art=art_z_rike),
    C(44, 48, 'court', 'card', year=1847, main='十年七迁', sub='二品大员', art=art_z_qiqian),
    # ---- 第二回 湘军
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'death', 'card', year=1852, main='母亲去世', sub='回乡守制', art=art_z_mother),
    C(54, 60, 'war', 'card', year=1853, main='创建湘军', sub='书生带兵', art=art_z_tuanlian),
    C(60, 68, 'death', 'jinggang', year=1854),
    C(68, 72, 'empire', 'card', year=1854, main='克复武昌', sub='咸丰大喜', art=art_z_wuchang),
    C(72, 76, 'war', 'card', year=1855, main='湖口之败', sub='座船被夺', art=art_z_hukou),
    C(76, 80, 'fate', 'card', year=1857, main='回籍反省', sub='由刚转柔', art=art_z_reflect),
    # ---- 第三回 屡败屡战
    C(80, 82, 'fate', 'chapter'),
    C(82, 86, 'life', 'card', year=1858, main='再度出山', sub='外圆内方', art=art_z_return),
    C(86, 92, 'night', 'card', year=1860, main='屡败屡战', sub='两字之易', art=art_z_loubai),
    C(92, 96, 'empire', 'card', year=1860, main='两江总督', sub='钦差大臣', art=art_z_liangjiang),
    C(96, 100, 'death', 'card', year=1861, main='祁门被围', sub='预写遗嘱', art=art_z_qimen),
    C(100, 106, 'war', 'card', year=1861, main='安庆之战', sub='结硬寨', art=art_z_anqing),
    C(106, 112, 'works', 'card', year=1861, main='内军械所', sub='自造轮船', art=art_z_arsenal),
    # ---- 第四回 天京
    C(112, 114, 'war', 'chapter'),
    C(114, 120, 'war', 'card', year=1864, main='攻克天京', sub='地道轰城', art=art_z_tianjing),
    C(120, 124, 'fate', 'card', year=1864, main='裁撤湘军', sub='自剪羽翼', art=art_z_disband),
    C(124, 128, 'works', 'card', year=1865, main='江南制造', sub='洋务', art=art_z_jiangnan),
    C(128, 132, 'fate', 'card', year=1866, main='剿捻无功', sub='李鸿章接替', art=art_z_nian),
    C(132, 136, 'court', 'card', year=1868, main='直隶总督', sub='位极人臣', art=art_z_zhili),
    C(136, 142, 'death', 'card', year=1870, main='天津教案', sub='举国唾骂', art=art_z_tianjin),
    C(142, 144, 'night', 'card', year=1871, main='幼童留美', sub='联名上奏', art=art_z_youtong),
    # ---- 第五回 家书
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=1872, main='曾国藩去世', sub='年六十二', art=art_z_death),
    C(150, 154, 'court', 'card', year=1872, main='谥文正', sub='身后哀荣', art=art_z_wenzheng),
    C(154, 158, 'life', 'card', year=1872, main='幼童启程', sub='身后成行', art=art_z_kids),
    C(158, 164, 'works', 'card', year=1879, main='曾国藩家书', sub='勤俭二字', art=art_z_letters),
    C(164, 168, 'fate', 'card', year=1879, main='功过之争', sub='名臣与剃头', art=art_z_verdict),
    C(168, 170, 'end', 'card', year=1879, main='以拙胜巧', sub='结硬寨', art=art_z_motto),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='柒拾肆', col=XIANGLAN, acc=DENGHUO, born=1811, died=1872, age0=1810,
    born_lab='1811年', died_lab='1872年', years_txt='公元1811 — 1872',
    hook_q='他天资平平 · 为什么被称为晚清第一名臣？',
    name_line='曾国藩 · 字伯涵', name='曾国藩', seal='涤生', title_art=art_z_title,
    q1='中兴名臣？', q2='曾剃头？',
    end_art=art_z_legacy, end_big='屡败屡战', end_seal='涤生',
    end_l1='他笨了一辈子', end_l2='也硬撑了一辈子',
    end_brush='以拙胜巧', end_ask='屡败屡战 你被哪句话激励过？评论区聊聊', next='左宗棠'),
    scenes=dict(chapter=scene_chapter, jinggang=scene_jinggang))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
