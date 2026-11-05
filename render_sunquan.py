"""千古人物志 · 第陆拾壹集 · 孙权 (182–252)
Look: 江东碧 + 吴锦紫, 楼船 corner borders, a 长江 chapter card: a river widens and one more warship joins the fleet
each chapter (0→3), and in the last chapter a lone boat drifts.
Set pieces: 6-beat 坐断东南, custom 8-beat scene 'chibi' (赤壁 · 火攻), 6-beat 濡须口 (生子当如孙仲谋),
6-beat 夷陵, 6-beat 南宫之祸 二宫之争.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_guanyu as Gy          # engine + helpers (previous episode)
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
from render_quyuan import river
from render_huatuo import caocao
from render_guanyu import liubei

F.RIPPLE = False
JIANGDONG = (40, 110, 120)          # 江东碧
WUJIN = (112, 70, 120)              # 吴锦紫
S.LAYERS.append(('jiangdong', JIANGDONG, 0.9, 1.0))
S.LAYERS.append(('wujin', WUJIN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='吴', life='孙', court='吴', night='夜', war='江', empire='吴', works='治', fate='荆', death='宫', end='江')
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
G.THEMES['empire']['sun'] = (WUJIN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (JIANGDONG, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

RIVER = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(RIVER)
for _k in range(5):                 # 大江 water bands
    _y = 1440 + _k * 18
    _d.line([(60 + i * 30, _y + 4 * math.sin(i * 0.6 + _k)) for i in range(34)], fill=JIANGDONG + (44 - _k * 6,), width=3)
for _x in list(range(80, 240, 20)) + list(range(860, 1010, 20)):      # reeds
    _h = 50 + (_x * 17) % 40
    _d.line((_x, 1440, _x + 6, 1440 - _h), fill=(90, 100, 70, 60), width=3)
MTN_COL = {'night': (28, 34, 44), 'death': (60, 58, 62), 'war': (112, 60, 48), 'fate': (90, 100, 104)}
def draw_background(t, theme):
    """江东: hills, the great river bands and reeds at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(184, 190, 190), (148, 166, 168), MTN_COL.get(theme, (98, 124, 128))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(RIVER)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """楼船: a small multi-deck warship in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=JIANGDONG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=JIANGDONG + (220,), width=3)
        bx, by = x + sx * 60, y + sy * 60
        d.polygon([(bx - 40, by), (bx + 40, by), (bx + 30, by + 14), (bx - 30, by + 14)], fill=(50, 50, 56, 230))
        d.rectangle((bx - 24, by - 16, bx + 24, by), fill=WUJIN + (220,))
        d.rectangle((bx - 14, by - 30, bx + 14, by - 16), fill=WUJIN + (220,))
        d.line((bx, by - 30, bx, by - 52), fill=(50, 50, 56, 230), width=3)
        d.polygon([(bx, by - 52), (bx + sx * 16, by - 46), (bx, by - 40)], fill=ZHU + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def sun(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, crown=False, **kw):
    """孙权: 紫髯 (purple beard), square jaw, a purple robe; as emperor a 冕."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        if crown:
            d.rectangle((x - 0.15 * h, y - 1.08 * h, x + 0.15 * h, y - 1.03 * h), fill=255)
            d.rectangle((x - 0.05 * h, y - 1.03 * h, x + 0.05 * h, y - 0.95 * h), fill=255)
        else:
            d.rectangle((x - 0.07 * h, y - 1.05 * h, x + 0.07 * h, y - 0.94 * h), fill=255)
        A.d['wujin'].polygon([(x + dir * 0.0 * h, y - 0.84 * h), (x + dir * 0.1 * h, y - 0.84 * h), (x + dir * 0.06 * h, y - 0.66 * h)], fill=255)
        A.d['wujin'].polygon([(x - 0.11 * h, y - 0.78 * h), (x + 0.11 * h, y - 0.78 * h), (x + 0.14 * h, y - 0.1 * h), (x - 0.14 * h, y - 0.1 * h)], fill=150)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.02 * h, y - 0.82 * h), (x + dir * 0.09 * h, y - 0.82 * h), (x + dir * 0.06 * h, y - 0.7 * h)], fill=255)
    return hand

def warship(A, x, y, s, t, layer='jiangdong', fire=0.0):
    A.d['ink'].polygon([(x - s, y - 0.12 * s), (x + 1.1 * s, y - 0.12 * s), (x + 0.9 * s, y + 0.1 * s), (x - 0.9 * s, y + 0.1 * s)], fill=255)
    for k in range(3):
        w = s * (0.8 - k * 0.22)
        A.d[layer].rectangle((x - w, y - 0.12 * s - (k + 1) * 0.22 * s, x + w, y - 0.12 * s - k * 0.22 * s), fill=255 - k * 20)
    A.d['ink'].line((x, y - 0.8 * s, x, y - 1.3 * s), fill=255, width=4)
    A.d['red'].polygon([(x, y - 1.3 * s), (x + 0.3 * s, y - 1.2 * s), (x, y - 1.1 * s)], fill=255)
    if fire > 0:
        flames(A, x, y - 0.12 * s, 2 * s, 1.4 * s * fire, t, n=4, seed=int(x), smoke=True)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 0)}
def art_river_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    A.d['jiangdong'].rectangle((60, 1150, W - 60, 1260), fill=140)
    waves(A, 1160, t, rows=3, amp=5)
    if kb == 144:
        for i in range(4):
            warship(A, 220 + i * 200, 1200, 70 * (1 - q) + 1, t)
        boat(A, lerp(300, 820, q), 1210, 60, t, sail=True)
    else:
        n = b if q > 0.6 else a
        for i in range(n):
            warship(A, 220 + i * 200, 1200, 70, t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_river_chapter)
    ink_in(cv, text_img(no, SERIF, 56, JIANGDONG, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_q_hook_young(A, cv, t, u):
    ground(A, GROUND)
    sun(A, 540, GROUND, lerp(150, 230, ease_out(u / (1.6 * P))), dir=1, arm=40)

def art_q_hook_cao(A, cv, t, u):
    A.d['jiangdong'].rectangle((60, 1200, W - 60, GROUND + 40), fill=140)
    waves(A, 1210, t, rows=2, amp=4)
    caocao(A, 540, 1200, 200, dir=1, arm=lerp(40, 140, ease_out(u / P)))

def art_q_hook_52(A, cv, t, u):
    ground(A, GROUND)
    n = min(52, int(clamp(u / (1.6 * P)) * 52) + 1)
    for i in range(n):
        A.d['wujin'].rectangle((120 + (i % 13) * 66, GROUND - 40 - (i // 13) * 50, 160 + (i % 13) * 66, GROUND - 6 - (i // 13) * 50), fill=230)

def art_q_hook_sons(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for i in range(2):
        person(A, 380 + i * 320, GROUND, 170, dir=1 if i == 0 else -1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3 + i)), layer='wujin' if i else 'ink')

# ================================================================ 第一回 碧眼儿
def art_q_birth(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='下邳', layer='mid', open_=1.0)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('父孙坚为下邳丞 · 生于官舍', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('孙坚之子', 44), 860, 1020, t, t - u + P, rot=6)

def art_q_father(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['ink'].line((x, GROUND, x, GROUND - 240), fill=255, width=10)
        A.d['pine'].ellipse((x - 60, GROUND - 320, x + 60, GROUND - 200), fill=200)
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, robe=False, hat='helmet', fall=-80 * ease_out((u - P) / P), arm=-8, layer='ink')
    for j in range(4):
        arrow(A, lerp(100, 520, ((t * 0.8 + j / 4) % 1)), GROUND - 160 - j * 20, 0.1, 60)
    A.flush(cv)
    paste(cv, text_img('孙坚征刘表 · 于岘山中流矢身亡', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_brother(A, cv, t, u):
    ground(A, GROUND)
    for j in range(4):
        rider(A, lerp(-200, 700, ease_out(u / (3 * P))) - j * 130, GROUND, 120, dir=1, ph=t * 8 + j, spear=True, layer='jiangdong' if j == 0 else 'ink')
    A.flush(cv)
    paste(cv, text_img('兄孙策平定江东 · 小霸王', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('孙策', 56), 860, 1020, t, t - u + P, rot=6)

def art_q_ce_dies(A, cv, t, u):
    A.d['mid'].rectangle((200, 1200, 640, 1260), fill=230)
    A.d['ink'].rectangle((180, 1260, 660, 1290), fill=255)
    person(A, 420, 1200, 200, dir=1, robe=True, hat='knot', fall=-82, arm=lerp(-8, 50, ease_out(u / 0.6)), layer='ink')
    sun(A, 800, GROUND, 190, dir=-1, kneel=True, bow=20, arm=90)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('举贤任能 各尽其心 以保江东 我不如卿', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('临终托付', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_q_heir(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='jiangdong')
    ground(A, GROUND)
    sun(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    for i in range(4):
        person(A, 200 + i * 60 if i < 2 else 820 + (i - 2) * 60, GROUND, 150, dir=1 if i < 2 else -1, robe=True, hat='knot', kneel=True, bow=40, arm=90, layer='mid')
    A.flush(cv)
    paste(cv, text_img('年十九 · 统事江东', SERIF, 48, JIANGDONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_q_talent(A, cv, t, u):
    ground(A, GROUND)
    sun(A, 760, GROUND, 200, dir=-1, arm=lerp(40, 120, ease_out(u / 0.5)))
    names = ['周瑜', '张昭', '鲁肃', '吕蒙']
    for i in range(4):
        person(A, 160 + i * 130, GROUND, 160, dir=1, robe=i != 0 and i != 3, hat='helmet' if i in (0, 3) else 'knot', kneel=True, bow=20, arm=90, layer='mid' if i % 2 else 'ink')
    A.flush(cv)
    for i, nm in enumerate(names):
        stamp(cv, seal(nm, 34, ZHU if i == 0 else INK), 160 + i * 130, 1040, t, t - u + i * 0.4 * P)
    paste(cv, text_img('招延俊秀 聘求名士', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_huangzu(A, cv, t, u):
    """6-beat set piece: 坐断东南 — avenging his father: the river assault on Jiangxia; Huang Zu's fleet burns; the banner of Wu rises."""
    ph = u / P
    A.d['jiangdong'].rectangle((60, 1180, W - 60, GROUND + 40), fill=140)
    waves(A, 1190, t, rows=3, amp=6, speed=2)
    city_wall(A, 640, 1000, 1060, gate_x=None, label=None, layer='mid')
    for j in range(3):
        warship(A, lerp(-200, 200 + j * 150, ease_out(ph / 2.5)), 1230, 60, t)
    for j in range(2):
        warship(A, 720 + j * 140, 1230, 60, t, layer='mid', fire=clamp((ph - 2.5) / 1))
    if ph > 4:
        banner(A, 820, 1060, 200, t, layer='wujin')
    A.flush(cv)
    lab = '溯江西征江夏' if ph < 2.5 else ('火焚敌船' if ph < 4 else '斩黄祖 · 报父仇')
    paste(cv, text_img(lab, SERIF, 48, ZHU if ph >= 2.5 else JIANGDONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    stamp(cv, seal('江夏', 56), 260, 1020, t, t - u + 0.4, rot=-5)

# ================================================================ 第二回 赤壁
def art_q_letter(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    sun(A, 540, GROUND, 210, dir=1, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)))
    scroll(A, 700, GROUND - 160, 160, 50, 1.0, layer='wash')
    A.flush(cv)
    type_in(cv, text_img('今治水军八十万众 方与将军会猎于吴', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('曹操书', 50, INK), 260, 1020, t, t - u + P, rot=-5)

def art_q_debate(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for i in range(4):
        person(A, 160 + i * 90, GROUND, 160, dir=1, robe=True, hat='knot', bow=20, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + i)), layer='mid')
    for i in range(2):
        person(A, 760 + i * 100, GROUND, 170, dir=-1, robe=i == 1, hat='helmet' if i == 0 else 'knot', arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 2 + i)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('群臣多劝迎曹 · 周瑜鲁肃独主战', SERIF, 44, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_desk(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='jiangdong')
    ground(A, GROUND)
    desk(A, 540, GROUND, 320, layer='mid')
    q = ease_out((u - P) / 0.3)
    sun(A, 320, GROUND, 210, dir=1, arm=lerp(60, 160, q))
    A.d['wash'].line((480, GROUND - 74, 600, GROUND - 74 + 40 * q), fill=255, width=6)
    A.flush(cv)
    type_in(cv, text_img('诸将吏敢复有言当迎操者 与此案同', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + P, 0.5)
    stamp(cv, seal('拔刀斫案', 44), 860, 1020, t, t - u + P, rot=6)

def art_q_alliance(A, cv, t, u):
    tent(A, 540, GROUND, 420, 280, layer='mid')
    ground(A, GROUND)
    person(A, 380, GROUND, 190, dir=1, robe=True, hat='knot', arm=lerp(40, 100, ease_out(u / 0.5)), layer='jiangdong')
    liubei(A, 700, GROUND, 200, dir=-1, arm=lerp(40, 100, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('孙刘联合 · 共拒曹操', SERIF, 48, JIANGDONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def scene_chibi(cv, t, c, k):
    """8-beat custom scene: 赤壁 — the chained northern fleet sits on the river; small fire boats ride the southeast wind;
    they ram; flames run along the chain; the sky turns red; the northern army flees over land."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['jiangdong'].rectangle((60, 1100, W - 60, GROUND + 40), fill=140)
    waves(A, 1110, t, rows=4, amp=6, speed=2)
    fire = clamp((ph - 3.2) / 1.2)
    for j in range(5):
        x = 560 + (j % 3) * 150; y = 1140 + (j // 3) * 90
        warship(A, x, y, 60, t, layer='mid', fire=fire * clamp(1 - abs(j - 2) * 0.2 + (ph - 3.5)))
    A.d['ink'].line((500, 1140, 900, 1140), fill=200, width=3)
    if ph < 3.6:
        for j in range(4):
            bx = lerp(-100 - j * 60, 520, clamp((ph - 0.5 - j * 0.15) / 2.6))
            boat(A, bx, 1180 + j * 26, 40, t + j, sail=True)
            if ph > 2.4:
                flames(A, bx, 1170 + j * 26, 60, 50, t, n=2, seed=j, smoke=False)
    for k2 in range(12):
        q = (t * 0.6 + k2 / 12) % 1
        A.d['wash'].line((80 + q * 900, 700 + (k2 * 53) % 300, 140 + q * 900, 700 + (k2 * 53) % 300 - 10), fill=120, width=2)
    if ph > 5.5:
        for j in range(5):
            person(A, lerp(900, 1200, ease_out((ph - 5.5) / 2)) + j * 50, 1100, 70, dir=1, robe=False, hat='helmet', ph=t * 6 + j, arm=-8, layer='ink')
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '赤壁之战', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=61)
    fx.flush(cv)
    lab = '曹军方连船舰 首尾相接' if ph < 2.4 else ('黄盖诈降 · 火船乘东南风' if ph < 4 else ('烟炎张天 人马烧溺死者甚众' if ph < 5.5 else '曹操引军北还'))
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 2.4 else JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('天下三分之势由此而定', SERIF, 40, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 6.4) / 0.4))

def art_q_zhouyu(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, robe=False, hat='helmet', fall=-88, arm=-8, layer='jiangdong')
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('周瑜病逝巴丘 · 年三十六', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('公瑾', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_q_jianye(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='建业', layer='jiangdong', open_=1.0)
    river(A, 1260, t, rows=2, amp=3)
    A.flush(cv)
    paste(cv, text_img('徙治秣陵 · 改名建业', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('石头城', 50), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第三回 生子当如孙仲谋
def art_q_ruxu(A, cv, t, u):
    """6-beat set piece: 濡须口 — the two armies face across the river mouth; Sun Quan rows a light boat right up to the enemy line;
    Cao Cao watches and sighs."""
    ph = u / P
    A.d['jiangdong'].rectangle((60, 1180, W - 60, GROUND + 40), fill=140)
    waves(A, 1190, t, rows=3, amp=5)
    ground(A, 1180, x0=700, x1=W - 60)
    army(A, 720, 1180, 6, dir=-1, layer='mid', h=90)
    caocao(A, 920, 1100, 150, dir=-1, arm=lerp(40, 120, clamp((ph - 3.6) / 0.4)))
    bx = lerp(-100, 580, ease_out(clamp(ph / 3)))
    if ph > 3.6:
        bx = lerp(580, 200, ease_out((ph - 3.6) / 2))
    boat(A, bx, 1210, 90, t, sail=False)
    sun(A, bx, 1190, 110, dir=1 if ph < 3.6 else -1, arm=40)
    if 2 < ph < 4:
        for j in range(6):
            arrow(A, lerp(700, bx + 40, ((t * 1.4 + j / 6) % 1)), 1120 + j * 6, math.pi + 0.1, 40)
    A.flush(cv)
    lab = '孙权乘轻船 从濡须口入曹营' if ph < 3.6 else '生子当如孙仲谋'
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.6 else JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '语出吴历 草船借箭本为此事 演义移于诸葛亮', t, t - u + P)

def art_q_hefei(A, cv, t, u):
    city_wall(A, 520, 1000, 1080, gate_x=760, label='合肥', layer='mid', open_=0.0)
    ground(A, GROUND)
    for j in range(3):
        rider(A, lerp(700, 120, ease_out(u / (2 * P))) + j * 80, GROUND, 120, dir=-1, ph=t * 8 + j, spear=True, layer='ink')
    sun(A, lerp(300, 80, ease_out(u / (2.5 * P))), GROUND, 180, dir=-1, ph=t * 5, arm=-8)
    A.flush(cv)
    paste(cv, text_img('攻合肥不克 · 张辽逍遥津突袭', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('逍遥津', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_q_lvmeng(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='jiangdong')
    person(A, 300, GROUND, 190, dir=1, robe=False, hat='helmet', kneel=True, bow=20, arm=90, layer='ink')
    for i in range(int(clamp(u / (2 * P)) * 6) + 1):
        bundle(A, 440 + i * 44, GROUND - 74, 38, layer='wujin')
    A.flush(cv)
    paste(cv, text_img('劝吕蒙读书 · 士别三日 即更刮目相待', SERIF, 42, JIANGDONG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('吴下阿蒙', 44), 860, 1020, t, t - u + P, rot=6)

def art_q_jingzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='江陵', layer='jiangdong', open_=1.0)
    banner(A, 780, 1080, 200, t, layer='wujin')
    river(A, 1260, t, rows=2, amp=3)
    A.flush(cv)
    paste(cv, text_img('袭取荆州 · 擒杀关羽', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_wuwang(A, cv, t, u):
    for k in range(3):
        A.d['wujin'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    sun(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('向魏称臣 · 受封吴王', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('吴王', 56), 860, 1020, t, t - u + P, rot=6)

def art_q_yiling(A, cv, t, u):
    """6-beat set piece: 夷陵 — Shu camps stretch seven hundred li along the river forest; Lu Xun's men set fire to camp after camp."""
    ph = u / P
    for k in range(8):
        x = 120 + k * 120
        A.d['ink'].line((x, GROUND, x, GROUND - 200), fill=255, width=8)
        A.d['pine'].ellipse((x - 50, GROUND - 260, x + 50, GROUND - 160), fill=200)
    for j in range(7):
        x = 140 + j * 130
        tent(A, x, GROUND, 100, 90, layer='mid')
        if ph > 2 + j * 0.4:
            flames(A, x, GROUND - 40, 120, 140 * clamp((ph - 2 - j * 0.4) / 0.6), t, n=3, seed=j, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    lab = '刘备连营七百里' if ph < 2 else '陆逊火攻 · 连破四十余营'
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('夷陵', 56), 860, 1440, t, t - u + 0.4, rot=6)

# ================================================================ 第四回 称帝
def art_q_peace(A, cv, t, u):
    tent(A, 540, GROUND, 420, 280, layer='mid')
    ground(A, GROUND)
    for i in range(2):
        person(A, 380 + i * 320, GROUND, 180, dir=1 if i == 0 else -1, robe=True, hat='knot', bow=15, arm=90, layer='jiangdong' if i == 0 else 'ink')
    A.flush(cv)
    paste(cv, text_img('与蜀复通好 · 再结盟约', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_emperor(A, cv, t, u):
    for k in range(3):
        A.d['wujin'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    sun(A, 540, GROUND - 180, 200, dir=1, crown=True, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('武昌即皇帝位 · 国号吴', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('黄龙', 56), 860, 1020, t, t - u + P, rot=6)

def art_q_yizhou(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1100, W - 60, GROUND + 40), fill=160)
    waves(A, 1110, t, rows=4, amp=8, speed=2)
    for j in range(3):
        warship(A, lerp(-200, 900, ((t * 0.07 + j / 3) % 1)), 1180, 70, t)
    A.d['grass'].chord((780, 1000, 1000, 1200), 180, 360, fill=220)
    A.flush(cv)
    paste(cv, text_img('遣卫温诸葛直率甲士万人 浮海求夷洲', SERIF, 42, JIANGDONG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('夷洲', 56), 860, 1300, t, t - u + P, rot=6)

def art_q_farm(A, cv, t, u):
    A.d['grass'].rectangle((60, GROUND - 60, W - 60, GROUND), fill=150)
    for k in range(10):
        A.d['jiangdong'].line((140 + k * 84, GROUND - 60, 150 + k * 84, GROUND - 130), fill=255, width=4)
    ground(A, GROUND)
    for j in range(5):
        person(A, 200 + j * 170, GROUND - 60, 110, dir=1, robe=False, hat='knot', bow=40, arm=150, ph=t * 2 + j, layer='ink')
    A.flush(cv)
    paste(cv, text_img('屯田江南 · 江东始富', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_ships(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1140, W - 60, GROUND + 40), fill=160)
    waves(A, 1150, t, rows=3, amp=6)
    for j in range(4):
        warship(A, 200 + j * 200, 1200, 60 + j * 6, t, layer='wujin')
    A.flush(cv)
    paste(cv, text_img('造船通海 · 北至辽东 南至交州', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_lvyi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    sun(A, 760, GROUND - 30, 190, dir=-1, crown=True, arm=40, old=0.5)
    person(A, 400, GROUND, 180, dir=1, robe=True, hat='knot', bow=20, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('宠信校事吕壹 · 举纠百官', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('校事', 56, INK), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第五回 晚节
def art_q_lusun(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, robe=True, hat='knot', fall=-88, arm=-8, layer='jiangdong')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('陆逊为太子事屡遭责问 · 愤恚而卒', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('陆逊', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_q_twopalace(A, cv, t, u):
    """6-beat set piece: 二宫之争 — two princes' palaces, two factions of ministers pulling apart; the father finally strikes both down."""
    ph = u / P
    palace(A, 260, 1300, 240, layer='mid')
    palace(A, 820, 1300, 240, layer='wujin')
    ground(A, GROUND)
    sep = ease_out(clamp(ph / 2.5))
    for i in range(4):
        person(A, 540 - 40 - i * 60 * sep - 40 * sep, GROUND, 130, dir=-1, robe=True, hat='knot', arm=60, layer='ink')
        person(A, 540 + 40 + i * 60 * sep + 40 * sep, GROUND, 130, dir=1, robe=True, hat='knot', arm=60, layer='wujin')
    if ph > 3.5:
        sun(A, 540, GROUND, 200, dir=1, crown=True, arm=lerp(40, 170, clamp((ph - 3.5) / 0.3)), old=0.8)
    A.flush(cv)
    lab = '太子孙和 鲁王孙霸 · 朝臣分党' if ph < 3.5 else '废太子 赐死鲁王 · 牵连者数十人'
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 3.5 else JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

def art_q_heir_young(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    sun(A, 400, GROUND, 190, dir=1, crown=True, arm=60, old=0.9)
    person(A, 620, GROUND, 100, dir=-1, robe=True, hat='crown', arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('立幼子孙亮为太子 · 年方八岁', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    sun(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('薨于建业 · 年七十一', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('大帝', 56), 260, 1020, t, t - u + P, rot=-5)

def art_q_shou(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    A.flush(cv)
    type_in(cv, text_img('屈身忍辱 任才尚计 有勾践之奇', SERIF, 44, ZHU, 'Black', bleed=False, spacing=2), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('性多嫌忌 果于杀戮 暨臻末年 弥以滋甚', SERIF, 40, INK, 'Black', bleed=False, spacing=2), W / 2, 835, t, t - u + 1.6 * P, 0.5)
    stamp(cv, seal('陈寿', 54), 860, 1020, t, t - u + P, rot=6)

def art_q_xinqiji(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 280), (x + 220, GROUND)], fill=150)
    A.d['jiangdong'].rectangle((60, 1240, W - 60, GROUND + 40), fill=140)
    waves(A, 1250, t, rows=2, amp=4)
    A.flush(cv)
    type_in(cv, text_img('天下英雄谁敌手 曹刘 生子当如孙仲谋', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('辛弃疾', 50), 860, 1020, t, t - u + P, rot=6)

def art_q_nanjing(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='金陵', layer='jiangdong', open_=1.0)
    river(A, 1260, t, rows=2, amp=3)
    A.flush(cv)
    paste(cv, text_img('六朝古都 · 自他定都建业始', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_river(A, cv, t, u):
    A.d['jiangdong'].rectangle((60, 1140, W - 60, GROUND + 40), fill=140)
    waves(A, 1150, t, rows=4, amp=5, speed=0.6)
    boat(A, lerp(200, 860, ease_out(u / (2 * P))), 1200, 70, t, sail=True)
    A.flush(cv)
    paste(cv, text_img('坐断东南 · 守江五十二年', SERIF, 46, JIANGDONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_legacy(A, cv, t, u):
    A.d['jiangdong'].rectangle((60, 1380, W - 60, 1440), fill=150)
    warship(A, 860, 1400, 40, t)

def art_q_title(A, cv, t, u):
    A.d['jiangdong'].rectangle((560, 1380, W - 60, 1470), fill=150)
    warship(A, 820, 1420, 110, t, layer='wujin')
    sun(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '少年承业'), 48: ('第二回', '赤壁'), 80: ('第三回', '孙仲谋'),
            112: ('第四回', '称帝'), 144: ('第五回', '晚节')}

CARDS = [
    C(0, 2, 'life', 'num', num='十九岁', line='接手江东', art=art_q_hook_young),
    C(2, 4, 'war', 'num', num='连曹操都说', line='生子当如孙仲谋', art=art_q_hook_cao),
    C(4, 6, 'empire', 'num', num='五十二年', line='三国最长的统治者', art=art_q_hook_52),
    C(6, 8, 'death', 'num', num='两个儿子', line='一场内斗', art=art_q_hook_sons),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 少年承业
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=182, main='生于下邳', sub='将门之后', art=art_q_birth),
    C(22, 26, 'death', 'card', year=191, main='父亲战死', sub='岘山', art=art_q_father),
    C(26, 30, 'war', 'card', year=195, main='兄长孙策', sub='平定江东', art=art_q_brother),
    C(30, 34, 'night', 'card', year=200, main='孙策遇刺', sub='临终托付', art=art_q_ce_dies),
    C(34, 38, 'court', 'card', year=200, main='统事江东', sub='十九岁', art=art_q_heir),
    C(38, 42, 'works', 'card', year=200, main='招贤纳士', sub='群英汇聚', art=art_q_talent),
    C(42, 48, 'war', 'card', year=208, main='斩黄祖', sub='报父仇', art=art_q_huangzu),
    # ---- 第二回 赤壁
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'night', 'card', year=208, main='曹操来信', sub='八十万众', art=art_q_letter),
    C(54, 58, 'court', 'card', year=208, main='战与降', sub='群臣之争', art=art_q_debate),
    C(58, 62, 'empire', 'card', year=208, main='拔刀斫案', sub='决意抗曹', art=art_q_desk),
    C(62, 66, 'works', 'card', year=208, main='孙刘联盟', sub='共抗强敌', art=art_q_alliance),
    C(66, 74, 'war', 'chibi', year=208),
    C(74, 78, 'death', 'card', year=210, main='周瑜病逝', sub='痛失栋梁', art=art_q_zhouyu),
    C(78, 80, 'empire', 'card', year=211, main='定都建业', sub='石头城', art=art_q_jianye),
    # ---- 第三回 孙仲谋
    C(80, 82, 'empire', 'chapter'),
    C(82, 88, 'war', 'card', year=213, main='濡须口', sub='曹操的感叹', art=art_q_ruxu),
    C(88, 92, 'night', 'card', year=215, main='合肥之败', sub='逍遥津', art=art_q_hefei),
    C(92, 96, 'works', 'card', year=215, main='劝蒙读书', sub='刮目相看', art=art_q_lvmeng),
    C(96, 100, 'fate', 'card', year=219, main='袭取荆州', sub='背盟', art=art_q_jingzhou),
    C(100, 104, 'court', 'card', year=221, main='受封吴王', sub='向魏称臣', art=art_q_wuwang),
    C(104, 112, 'war', 'card', year=222, main='夷陵之战', sub='火烧连营', art=art_q_yiling),
    # ---- 第四回 称帝
    C(112, 114, 'court', 'chapter'),
    C(114, 118, 'life', 'card', year=223, main='吴蜀复好', sub='再度联手', art=art_q_peace),
    C(118, 122, 'empire', 'card', year=229, main='称帝', sub='三国鼎立', art=art_q_emperor),
    C(122, 126, 'fate', 'card', year=230, main='浮海求夷洲', sub='万人出海', art=art_q_yizhou),
    C(126, 130, 'works', 'card', year=233, main='屯田江南', sub='开发江东', art=art_q_farm),
    C(130, 136, 'works', 'card', year=235, main='通海', sub='海上之吴', art=art_q_ships),
    C(136, 144, 'night', 'card', year=238, main='校事', sub='猜忌之始', art=art_q_lvyi),
    # ---- 第五回 晚节
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=245, main='陆逊之死', sub='忠臣含恨', art=art_q_lusun),
    C(150, 156, 'night', 'card', year=250, main='二宫之争', sub='父子相残', art=art_q_twopalace),
    C(156, 160, 'court', 'card', year=250, main='立幼子', sub='孙亮', art=art_q_heir_young),
    C(160, 162, 'death', 'card', year=252, main='孙权去世', sub='谥大帝', art=art_q_death),
    C(162, 164, 'works', 'card', year=285, main='陈寿评曰', sub='功过两分', art=art_q_shou),
    C(164, 166, 'life', 'card', year=1205, main='辛弃疾', sub='千古兴亡', art=art_q_xinqiji),
    C(166, 168, 'empire', 'card', year=1205, main='六朝古都', sub='金陵', art=art_q_nanjing),
    C(168, 170, 'end', 'card', year=1205, main='坐断东南', sub='守江一生', art=art_q_river),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='陆拾壹', col=JIANGDONG, acc=WUJIN, born=182, died=252, age0=181,
    born_lab='182年', died_lab='252年', years_txt='公元182 — 252',
    hook_q='曹操夸他生子当如孙仲谋 · 为何晚年众叛亲离？',
    name_line='孙权 · 字仲谋', name='孙权', seal='大帝', title_art=art_q_title,
    q1='守成雄主？', q2='晚年昏聩？',
    end_art=art_q_legacy, end_big='坐断东南', end_seal='大帝',
    end_l1='他守住了江东五十二年', end_l2='却没守住晚年的清醒',
    end_brush='生子当如孙仲谋', end_ask='三国三位君主 你最欣赏谁？评论区聊聊', next='司马懿'),
    scenes=dict(chapter=scene_chapter, chibi=scene_chibi))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
