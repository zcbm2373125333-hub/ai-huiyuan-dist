"""千古人物志 · 第陆拾贰集 · 司马懿 (179–251)
Look: 墨玄灰 + 魏金, 狼顾 corner borders (a wolf head turned back), a 棋局 chapter card: one more black stone is placed
each chapter and in the last chapter the board is surrounded.
Set pieces: 6-beat 装病拒辟, custom 8-beat scene 'shangfang' (五丈原 · 死诸葛走生仲达), 6-beat 千里擒孟达,
6-beat 平辽东, 6-beat 高平陵之变.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_sunquan as Sq         # engine + helpers (previous episode)
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
from render_songtaizu import tent
from render_sunwu import army, banner
from render_quyuan import river
from render_huatuo import caocao
from render_lisi import eunuch
from render_huatuo import HULU

F.RIPPLE = False
MOXUAN = (58, 60, 70)               # 墨玄灰
WEIJIN = (170, 140, 70)             # 魏金
S.LAYERS.append(('moxuan', MOXUAN, 0.9, 1.0))
S.LAYERS.append(('weijin', WEIJIN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='忍', life='温', court='魏', night='狼', war='战', empire='晋', works='屯', fate='病', death='权', end='忍')
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
G.THEMES['empire']['sun'] = (WEIJIN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (MOXUAN, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

GRID = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(GRID)
for _k in range(6):                 # a faint go-board grid along the bottom margin
    _d.line((60, 1400 + _k * 24, W - 60, 1400 + _k * 24), fill=MOXUAN + (30,), width=2)
for _x in range(60, W - 59, 48):
    _d.line((_x, 1400, _x, 1520), fill=MOXUAN + (30,), width=2)
for _i in range(9):
    _x = 108 + (_i * 211) % 860; _y = 1400 + ((_i * 3) % 5) * 24
    _d.ellipse((_x - 9, _y - 9, _x + 9, _y + 9), fill=(30, 30, 34, 70) if _i % 2 else (240, 240, 236, 90))
MTN_COL = {'night': (28, 28, 36), 'death': (58, 54, 56), 'war': (110, 60, 50), 'fate': (86, 88, 96)}
def draw_background(t, theme):
    """洛阳: grey hills and a faint go-board along the bottom margin."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 184, 186), (152, 150, 156), MTN_COL.get(theme, (108, 106, 116))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(GRID)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """狼顾: a wolf's head turned back over its shoulder in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=MOXUAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=MOXUAN + (220,), width=3)
        cx, cy = x + sx * 58, y + sy * 58
        d.ellipse((cx - 26, cy - 22, cx + 26, cy + 22), fill=MOXUAN + (230,))
        d.polygon([(cx - sx * 22, cy - 6), (cx - sx * 52, cy + 4), (cx - sx * 22, cy + 14)], fill=MOXUAN + (230,))
        d.polygon([(cx - 16, cy - 18), (cx - 6, cy - 40), (cx + 2, cy - 18)], fill=MOXUAN + (230,))
        d.polygon([(cx + 4, cy - 18), (cx + 16, cy - 40), (cx + 20, cy - 16)], fill=MOXUAN + (230,))
        d.ellipse((cx - sx * 10 - 4, cy - 6, cx - sx * 10 + 4, cy + 2), fill=WEIJIN + (240,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def sima(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, armour=False, wolf=0.0, **kw):
    """司马懿: tall 进贤冠, long narrow beard, dark robe with gold trim; wolf=1 turns the head right round (狼顾)."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else ('none' if up else 'knot'), layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        hd = -dir if wolf > 0.5 else dir
        if not armour:
            d.polygon([(x - 0.07 * h, y - 0.95 * h), (x + 0.07 * h, y - 0.95 * h), (x + hd * 0.08 * h, y - 1.12 * h), (x - hd * 0.03 * h, y - 1.06 * h)], fill=255)
        d.polygon([(x + hd * 0.03 * h, y - 0.84 * h), (x + hd * 0.08 * h, y - 0.84 * h), (x + hd * 0.05 * h, y - 0.6 * h)], fill=255)
        A.d['weijin'].line((x - 0.11 * h, y - 0.78 * h, x - 0.13 * h, y - 0.05 * h), fill=255, width=max(2, int(0.012 * h)))
        A.d['weijin'].line((x + 0.11 * h, y - 0.78 * h, x + 0.13 * h, y - 0.05 * h), fill=255, width=max(2, int(0.012 * h)))
        if old > 0.4:
            A.d['wash'].polygon([(x + hd * 0.03 * h, y - 0.82 * h), (x + hd * 0.08 * h, y - 0.82 * h), (x + hd * 0.05 * h, y - 0.66 * h)], fill=255)
    return hand

def zhuge(A, x, y, h, dir=-1, layer='ink', **kw):
    hand = person(A, x, y, h, dir=dir, robe=True, hat='knot', layer=layer, **kw)
    if not kw.get('kneel') and not kw.get('fall'):
        A.d['wash'].ellipse((x + dir * 0.12 * h - 0.06 * h, y - 0.62 * h, x + dir * 0.12 * h + 0.06 * h, y - 0.48 * h), fill=255)
    return hand

def emperor(A, x, y, h, dir=-1, layer='ink', **kw):
    return person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)

def goboard(A, cx, cy, s, blacks, whites, ring=0.0):
    A.d['weijin'].rectangle((cx - s, cy - s, cx + s, cy + s), fill=200)
    n = 9
    for k in range(n):
        p = cx - s + 2 * s * k / (n - 1)
        A.d['ink'].line((p, cy - s, p, cy + s), fill=140, width=2)
        A.d['ink'].line((cx - s, cy - s + 2 * s * k / (n - 1), cx + s, cy - s + 2 * s * k / (n - 1)), fill=140, width=2)
    r = s / (n - 1) * 0.45
    for (i, j) in whites:
        x = cx - s + 2 * s * i / (n - 1); y = cy - s + 2 * s * j / (n - 1)
        A.d['wash'].ellipse((x - r, y - r, x + r, y + r), fill=255)
        A.d['ink'].ellipse((x - r, y - r, x + r, y + r), outline=200, width=2)
    for (i, j) in blacks:
        x = cx - s + 2 * s * i / (n - 1); y = cy - s + 2 * s * j / (n - 1)
        A.d['ink'].ellipse((x - r, y - r, x + r, y + r), fill=255)

# ================================================================ chapter card
WHITE = [(4, 4), (4, 3), (3, 4), (5, 4)]
BLACKS = [(4, 2), (2, 4), (6, 4), (4, 6), (3, 3), (5, 5), (3, 5), (5, 3), (4, 5)]
CH = {16: (0, 1), 48: (1, 3), 80: (3, 5), 112: (5, 7), 144: (7, 9)}
def art_go_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 3))
    q = ease_out(u / (1.2 * P))
    n = b if q > 0.6 else a
    goboard(A, 540, 1060, 200, BLACKS[:n], WHITE if kb != 144 or q < 0.8 else [])

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_go_chapter)
    ink_in(cv, text_img(no, SERIF, 56, MOXUAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_y_hook_sick(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    sima(A, 540, 1200, 220, dir=1, fall=-86, arm=-8)
    ground(A, GROUND)

def art_y_hook_four(A, cv, t, u):
    ground(A, GROUND)
    n = min(4, int(clamp(u / (1.4 * P)) * 4) + 1)
    for i in range(n):
        emperor(A, 220 + i * 210, GROUND, 170, dir=1, arm=40, layer='mid' if i < n - 1 else 'ink')

def art_y_hook_dress(A, cv, t, u):
    tent(A, 540, GROUND, 420, 280, layer='mid')
    ground(A, GROUND)
    A.d['pink'].polygon([(480, 1140), (600, 1140), (630, 1240), (450, 1240)], fill=255)

def art_y_hook_jin(A, cv, t, u):
    for k in range(3):
        A.d['weijin'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    emperor(A, 540, GROUND - 180, lerp(60, 180, ease_out(u / (1.4 * P))), dir=1, arm=40)

# ================================================================ 第一回 河内司马
def art_y_birth(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for i in range(4):
        person(A, 200 + i * 80 if i < 2 else 760 + (i - 2) * 80, GROUND, 120 + (i % 2) * 20, dir=1 if i < 2 else -1, robe=True, hat='knot', arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('河内温县 · 司马八达之一', SERIF, 46, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('温县', 56), 860, 1020, t, t - u + P, rot=6)

def art_y_young(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='moxuan')
    sima(A, 300, GROUND, 170, dir=1, kneel=True, bow=20, arm=90)
    slips(A, 440, GROUND - 74, int(clamp(u / (2 * P)) * 8) + 1, 90, layer='weijin')
    A.flush(cv)
    paste(cv, text_img('少有奇节 聪朗多大略', SERIF, 46, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_feign(A, cv, t, u):
    """6-beat set piece: 装病拒辟 — Cao Cao's envoy arrives; he lies stiff on the bed for years; one night it rains on his books,
    he leaps up to save them; a maid sees; his wife silences her."""
    ph = u / P
    A.d['mid'].rectangle((240, 1200, 640, 1260), fill=230)
    ground(A, GROUND)
    for i in range(4):
        bundle(A, 760 + (i % 2) * 70, GROUND - (i // 2) * 50, 60, layer='weijin')
    if ph < 3:
        sima(A, 440, 1200, 200, dir=1, fall=-86, arm=-8)
        if ph < 1.6:
            person(A, lerp(1100, 760, ease_out(ph / 1)), GROUND, 170, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
        lab = '曹操辟之 · 辞以风痹 不能起居'
    else:
        for k in range(30):
            q = (t * 1.2 + k / 30) % 1
            A.d['wash'].line((80 + (k * 37) % 920, lerp(620, 1300, q), 80 + (k * 37) % 920 - 10, lerp(620, 1300, q) + 30), fill=150, width=2)
        sima(A, 700, GROUND, 190, dir=1, bow=30, arm=150, ph=t * 6 if ph < 4 else None)
        person(A, 300, GROUND, 150, dir=1, robe=True, hat='knot', female=True, arm=lerp(-8, 120, clamp((ph - 4) / 0.3)), layer='mid')
        lab = '暴书遇雨 不觉自起收之' if ph < 4.5 else '其妻张春华 恐事泄 手杀婢'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 4.5 else MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    note_in(cv, '事见晋书宣帝纪', t, t - u + P)

def art_y_forced(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='weijin')
    ground(A, GROUND)
    caocao(A, 760, GROUND - 30, 200, dir=-1, arm=lerp(20, 140, ease_out(u / 0.5)))
    sima(A, 400, GROUND, 190, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    type_in(cv, text_img('若复盘桓 便收之', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('文学掾', 50), 860, 1020, t, t - u + P, rot=6)

def art_y_wolf(A, cv, t, u):
    ground(A, GROUND)
    sima(A, 480, GROUND, 230, dir=1, arm=-8, wolf=1.0 if u > P else 0.0)
    caocao(A, 820, GROUND, 190, dir=-1, arm=lerp(-8, 80, ease_out((u - P) / 0.4)))
    A.flush(cv)
    paste(cv, text_img('召使前行 令反顾 · 面正向后而身不动', SERIF, 42, MOXUAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('狼顾之相', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 835, 1, clamp((u - 1.5 * P) / 0.3))
    note_in(cv, '狼顾三马同槽事见晋书 带传说色彩', t, t - u + P)

def art_y_caopi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mid')
    person(A, 380, GROUND, 190, dir=1, robe=True, hat='knot', kneel=True, arm=90, layer='weijin')
    sima(A, 720, GROUND, 190, dir=-1, kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    paste(cv, text_img('与太子曹丕游处 · 深为信重', SERIF, 46, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('四友', 56), 860, 1020, t, t - u + P, rot=6)

def art_y_diligent(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='moxuan')
    sima(A, 300, GROUND, 180, dir=1, kneel=True, bow=25, arm=90)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    paste(cv, text_img('勤于吏职 夜以忘寝 · 至于刍牧之间 悉皆临履', SERIF, 40, MOXUAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 抚军
def art_y_caoopi_emp(A, cv, t, u):
    for k in range(3):
        A.d['weijin'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    emperor(A, 540, GROUND - 180, 190, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('曹丕代汉称帝 · 司马懿为尚书', SERIF, 46, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('魏', 60), 860, 1020, t, t - u + P, rot=6)

def art_y_fujun(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='许昌', layer='moxuan', open_=1.0)
    ground(A, GROUND)
    sima(A, 540, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    type_in(cv, text_img('吾东 抚军当总西事 · 吾西 抚军当总东事', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('抚军', 56), 860, 1020, t, t - u + P, rot=6)

def art_y_regent(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    emperor(A, 540, 1200, 200, dir=1, fall=-86, arm=-8)
    for i in range(4):
        person(A, 200 + i * 80 if i < 2 else 820 + (i - 2) * 80, GROUND, 160, dir=1 if i < 2 else -1, robe=True, hat='knot', kneel=True, bow=30, arm=90, layer='mid' if i else 'ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('曹丕崩 · 与曹真 陈群 曹休同受遗诏辅政', SERIF, 42, MOXUAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_y_mengda(A, cv, t, u):
    """6-beat set piece: 千里擒孟达 — Meng Da plots to defect; Sima Yi marches without waiting for orders, eight days for 1200 li;
    the city of Xincheng is taken in sixteen days."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 860, 970, 1320), radius=20, fill=170)
    q = clamp(ph / 3)
    A.d['moxuan'].line((880, 1240, lerp(880, 300, q), lerp(1240, 960, q)), fill=255, width=10)
    stamp_days = min(8, int(q * 8) + 1)
    if ph > 3:
        city_wall(A, 220, 380, 1000, label=None, layer='mid')
        r = 40 + 10 * math.sin(t * 6)
        A.d['red'].ellipse((300 - r, 960 - r, 300 + r, 960 + r), fill=150)
    A.flush(cv)
    stamp(cv, seal('宛', 40, MOXUAN), 880, 1280, t, t - u + 0.3)
    stamp(cv, seal('新城', 40, ZHU), 300, 1060, t, t - u + 0.3)
    lab = f'倍道兼行 第{cn_num(stamp_days)}日' if ph < 3 else ('八日到其城下' if ph < 4.5 else '十六日拔之 · 斩孟达')
    paste(cv, text_img(lab, SERIF, 48, ZHU if ph >= 3 else MOXUAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)

def art_y_jieting(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 360), (x + 220, GROUND)], fill=170)
    ground(A, GROUND)
    army(A, lerp(-200, 160, ease_out(u / (2 * P))), GROUND, 6, dir=1, layer='ink', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('诸葛亮北伐 · 张郃破马谡于街亭', SERIF, 44, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '空城计出自演义 正史此时司马懿在荆州', t, t - u + P)

# ================================================================ 第三回 对阵孔明
def art_y_west(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 320), (x + 200, GROUND)], fill=170)
    ground(A, GROUND)
    rider(A, lerp(-100, 600, ease_out(u / (2.5 * P))), GROUND, 150, dir=1, ph=t * 8, layer='moxuan')
    A.flush(cv)
    paste(cv, text_img('曹真病笃 · 司马懿西屯长安 都督雍凉', SERIF, 44, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_lucheng(A, cv, t, u):
    tent(A, 300, GROUND, 260, 200, layer='moxuan')
    tent(A, 800, GROUND, 260, 200, layer='mid')
    ground(A, GROUND)
    for i in range(4):
        person(A, 420 + i * 60, GROUND, 140, dir=-1, robe=False, hat='helmet', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 4 + i)), layer='ink')
    A.flush(cv)
    type_in(cv, text_img('公畏蜀如虎 奈天下笑何', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('诸将讥之', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_y_hold(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='渭南', layer='moxuan', open_=0.0)
    ground(A, GROUND)
    sima(A, 540, 1080 - 30, 140, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('坚壁拒守 · 以逸待劳', SERIF, 48, MOXUAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_y_dress(A, cv, t, u):
    tent(A, 540, GROUND, 460, 300, layer='mid')
    ground(A, GROUND)
    sima(A, 360, GROUND, 200, dir=1, arm=lerp(40, 120, ease_out(u / 0.5)), armour=True)
    A.d['pink'].polygon([(560, 1180), (660, 1180), (690, 1260), (530, 1260)], fill=255)
    person(A, 800, GROUND, 170, dir=-1, robe=True, hat='knot', bow=20, arm=90, layer='ink')
    A.flush(cv)
    paste(cv, text_img('亮遗以巾帼妇人之服 · 帝怒 表请决战', SERIF, 44, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '天子遣辛毗杖节为军师以制之', t, t - u + P)

def art_y_food(A, cv, t, u):
    tent(A, 540, GROUND, 420, 280, layer='mid')
    ground(A, GROUND)
    sima(A, 360, GROUND, 200, dir=1, arm=60, armour=True)
    person(A, 720, GROUND, 170, dir=-1, robe=True, hat='knot', bow=20, arm=60, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('食少事烦 其能久乎', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.8 * P, 0.5)
    stamp(cv, seal('问使者', 50, INK), 860, 1020, t, t - u + 0.4, rot=6)

def scene_shangfang(cv, t, c, k):
    """8-beat custom scene: 五丈原 — the great star falls over the Shu camp; the Shu army withdraws; Sima Yi pursues;
    Jiang Wei turns the banners and beats the drums; Sima Yi turns back; later he walks the empty camp: 天下奇才也."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    if ph < 2:
        for j in range(4):
            tent(A, 200 + j * 220, GROUND, 160, 130, layer='mid')
        q = clamp(ph / 1.5)
        A.d['red'].ellipse((lerp(820, 540, q) - 16, lerp(700, 1040, q) - 16, lerp(820, 540, q) + 16, lerp(700, 1040, q) + 16), fill=255)
        A.d['red'].line((lerp(820, 540, q), lerp(700, 1040, q), lerp(820, 540, q) + 80, lerp(700, 1040, q) - 120), fill=150, width=6)
        lab = '有长星赤而芒角 坠亮营中'
    elif ph < 5:
        army(A, lerp(120, 300, (ph - 2) / 3), GROUND, 6, dir=1, layer='mid', t=t, march=ph < 3.6, h=100)
        if ph > 3.6:
            for j in range(4):
                banner(A, 640 + j * 90, GROUND, 220, t, layer='red')
        rider(A, lerp(-100, 200, (ph - 2) / 1.6) if ph < 3.6 else lerp(200, -200, (ph - 3.6) / 1.2), GROUND, 140, dir=1 if ph < 3.6 else -1, ph=t * 8, layer='moxuan')
        lab = '蜀军退 · 宣王追之' if ph < 3.6 else '姜维反旗鸣鼓 若将向宣王 · 宣王乃退'
    else:
        for j in range(4):
            A.d['mid'].rectangle((200 + j * 220 - 70, GROUND - 20, 200 + j * 220 + 70, GROUND), fill=200)
        sima(A, lerp(120, 700, ease_out((ph - 5) / 2.5)), GROUND, 190, dir=1, ph=t * 3, arm=-8, armour=True)
        lab = '案行其营垒处所 · 天下奇才也'
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '五丈原', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=62)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 42, ZHU if 2 <= ph < 5 else MOXUAN, 'Black', bleed=False, spacing=2), W / 2, 575, 1, 1)
    if ph > 4:
        paste(cv, text_img('百姓为之谚曰 死诸葛走生仲达', SERIF, 40, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 4) / 0.4))

def art_y_liaodong(A, cv, t, u):
    """6-beat set piece: 平辽东 — a thousand-li march to the northeast in summer rain; the river floods the camp but he holds;
    when the rains stop, Xiangping falls."""
    ph = u / P
    for k in range(40):
        q = (t * 1.2 + k / 40) % 1
        A.d['wash'].line((80 + (k * 37) % 920, lerp(620, 1300, q), 80 + (k * 37) % 920 - 10, lerp(620, 1300, q) + 30), fill=int(150 * clamp(1 - (ph - 3.5))), width=2)
    city_wall(A, 560, 980, 1080, gate_x=770, label='襄平', layer='mid', open_=clamp((ph - 4) / 1))
    A.d['ocean'].rectangle((60, GROUND - 30, 540, GROUND + 40), fill=150)
    ground(A, GROUND)
    army(A, 100, GROUND - 20, 6, dir=1, layer='moxuan', t=t, h=100)
    A.flush(cv)
    lab = '霖雨三十余日 辽水暴涨' if ph < 3.5 else ('雨止 · 起土山 地道 楯橹钩冲' if ph < 4.5 else '城溃 · 斩公孙渊')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4.5 else MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('辽东', 56), 260, 1020, t, t - u + 0.4, rot=-5)

# ================================================================ 第四回 托孤
def art_y_ruidi(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    emperor(A, 540, 1200, 200, dir=1, fall=-82, arm=lerp(-8, 60, ease_out(u / 0.6)))
    sima(A, 840, GROUND, 190, dir=-1, kneel=True, bow=40, arm=100)
    person(A, 680, GROUND, 90, dir=-1, robe=True, hat='crown', arm=40, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('以后事相托 · 死乃复可忍', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('托孤', 56), 260, 1020, t, t - u + P, rot=-5)

def art_y_caoshuang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='weijin')
    ground(A, GROUND)
    person(A, 700, GROUND, 200, dir=-1, robe=True, hat='crown', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)), layer='weijin')
    sima(A, lerp(380, 120, ease_out((u - P) / P)), GROUND, 190, dir=-1 if u > P else 1, ph=t * 3 if u > P else None, arm=-8)
    A.flush(cv)
    paste(cv, text_img('曹爽专权 · 尊懿为太傅 夺其实权', SERIF, 44, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('太傅', 56), 860, 1020, t, t - u + P, rot=6)

def art_y_sick2(A, cv, t, u):
    A.d['mid'].rectangle((240, 1200, 640, 1260), fill=230)
    sima(A, 440, 1200, 200, dir=1, fall=-70, arm=lerp(40, 80, 0.5 + 0.5 * math.sin(t * 2)), old=1.0)
    person(A, 560, 1150, 120, dir=-1, robe=True, hat='knot', female=True, arm=90, layer='mid')
    A.d['hulu'].ellipse((520, 1130, 560, 1160), fill=255)
    person(A, 820, GROUND, 190, dir=-1, robe=True, hat='knot', arm=40, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('李胜来探 · 持杯饮粥 粥皆流出沾胸', SERIF, 44, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('太傅语言错乱 · 尸居余气 形神已离', SERIF, 42, INK, 'Black', bleed=False, spacing=2), W / 2, 835, 1, clamp((u - 1.6 * P) / 0.4))

def art_y_soldiers(A, cv, t, u):
    for k in range(4):
        A.d['mid'].rectangle((100 + k * 240, GROUND - 160, 280 + k * 240, GROUND), fill=170)
    ground(A, GROUND)
    n = int(clamp(u / (2 * P)) * 15) + 1
    for i in range(n):
        person(A, 140 + (i % 8) * 110, GROUND - (i // 8) * 40, 100, dir=1, robe=True, hat='knot', arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('阴养死士三千 · 散在人间', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_gaoping(A, cv, t, u):
    """6-beat set piece: 高平陵之变 — the emperor and Cao Shuang leave the city to visit the tomb; the gates close behind them;
    the old man rides out in armour and seizes the arsenal; Cao Shuang surrenders his seal."""
    ph = u / P
    city_wall(A, 160, 920, 1080, gate_x=540, label='洛阳', layer='mid', open_=1.0 - clamp((ph - 1.5) / 0.6))
    ground(A, GROUND)
    if ph < 1.5:
        for j in range(4):
            carriage(A, lerp(540, 1200, ease_out(ph / 1.5)) + j * 80, GROUND, 60, dir=1, wheel=t * 6, ph=t * 8 + j, layer='weijin')
        lab = '曹爽兄弟从帝谒高平陵'
    elif ph < 4:
        sima(A, 540, GROUND, 200, dir=1, armour=True, arm=lerp(40, 150, clamp((ph - 1.8) / 0.4)))
        for j in range(6):
            person(A, 220 + j * 120, GROUND, 120, dir=1, robe=True, hat='knot', spear=True, arm=40, layer='ink')
        lab = '太傅闭城门 勒兵据武库'
    else:
        person(A, 540, GROUND, 190, dir=1, robe=True, hat='crown', kneel=True, bow=50, arm=100, layer='weijin')
        A.d['red'].rectangle((620, GROUND - 60, 660, GROUND - 20), fill=255)
        lab = '曹爽免官 · 后夷三族'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 1.5 else MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph > 4:
        note_in(cv, '指洛水为誓 许其免死 旋即背誓', t, t - u + 4 * P)

# ================================================================ 第五回 三马同槽
def art_y_wangling(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=4)
    for j in range(3):
        boat(A, lerp(-200, 300 + j * 140, ease_out(u / (2 * P))), 1250, 60, t + j, sail=True)
    A.flush(cv)
    paste(cv, text_img('王凌谋立楚王 · 太傅亲征 王凌自杀', SERIF, 44, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    sima(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('薨于洛阳 · 年七十三', SERIF, 46, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '遗令不坟不树 · 葬首阳山', t, t - u + P)

def art_y_sons(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='weijin')
    ground(A, GROUND)
    for i in range(2):
        person(A, 380 + i * 320, GROUND, 190, dir=1 if i == 0 else -1, robe=True, hat='knot', arm=60, layer='moxuan' if i else 'ink')
    A.flush(cv)
    paste(cv, text_img('子司马师 司马昭 相继专权', SERIF, 46, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_jin(A, cv, t, u):
    for k in range(3):
        A.d['weijin'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    emperor(A, 540, GROUND - 180, 190, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('孙司马炎代魏 · 国号晋', SERIF, 46, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('晋', 60), 860, 1020, t, t - u + P, rot=6)

def art_y_xuandi(A, cv, t, u):
    palace(A, 540, 1360, 260, layer='moxuan')
    ground(A, GROUND)
    A.flush(cv)
    ink_in(cv, text_img('宣帝', BRUSH, 140, ZHU), W / 2, 980, t, t - u + 0.5, dur=0.3, settle=1.2)
    paste(cv, text_img('追尊为宣皇帝', SERIF, 46, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_mingdi(A, cv, t, u):
    ground(A, GROUND)
    emperor(A, 540, GROUND, 190, dir=1, kneel=True, bow=lerp(0, 40, ease_out(u / P)), arm=170)
    A.flush(cv)
    type_in(cv, text_img('若如公言 祚安得长', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    note_in(cv, '晋明帝闻先祖创业之事 覆面著床 见世说新语', t, t - u + P)

def art_y_patience(A, cv, t, u):
    goboard(A, 540, 1060, 200, BLACKS, [])
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('一生隐忍 · 只为最后一步', SERIF, 48, MOXUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_y_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    goboard(A, 860, 1330, 50, BLACKS[:5], WHITE[:1])

def art_y_title(A, cv, t, u):
    goboard(A, 820, 1300, 140, BLACKS[:6], WHITE)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    sima(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '河内司马'), 48: ('第二回', '抚军'), 80: ('第三回', '对阵孔明'),
            112: ('第四回', '高平陵'), 144: ('第五回', '三马同槽')}

CARDS = [
    C(0, 2, 'fate', 'num', num='装病七年', line='不给曹操打工', art=art_y_hook_sick),
    C(2, 4, 'court', 'num', num='熬走了', line='四代曹家君主', art=art_y_hook_four),
    C(4, 6, 'night', 'num', num='一件女装', line='他笑着收下', art=art_y_hook_dress),
    C(6, 8, 'empire', 'num', num='他的孙子', line='当了皇帝', art=art_y_hook_jin),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 河内司马
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=179, main='生于温县', sub='司马八达', art=art_y_birth),
    C(22, 26, 'works', 'card', year=195, main='少有奇节', sub='聪朗多大略', art=art_y_young),
    C(26, 32, 'fate', 'card', year=201, main='装病拒辟', sub='不愿事曹', art=art_y_feign),
    C(32, 36, 'court', 'card', year=208, main='被迫出仕', sub='不来就抓', art=art_y_forced),
    C(36, 40, 'night', 'card', year=208, main='狼顾', sub='曹操的忌惮', art=art_y_wolf),
    C(40, 44, 'life', 'card', year=215, main='结交曹丕', sub='太子四友', art=art_y_caopi),
    C(44, 48, 'works', 'card', year=217, main='勤于吏职', sub='夜以忘寝', art=art_y_diligent),
    # ---- 第二回 抚军
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'empire', 'card', year=220, main='曹丕称帝', sub='魏朝建立', art=art_y_caoopi_emp),
    C(54, 58, 'court', 'card', year=224, main='抚军大将军', sub='留守许昌', art=art_y_fujun),
    C(58, 62, 'death', 'card', year=226, main='受遗诏辅政', sub='四大辅臣', art=art_y_regent),
    C(62, 68, 'war', 'card', year=227, main='千里擒孟达', sub='兵贵神速', art=art_y_mengda),
    C(68, 72, 'fate', 'card', year=228, main='孔明北伐', sub='街亭', art=art_y_jieting),
    C(72, 76, 'works', 'card', year=230, main='都督雍凉', sub='西线主帅', art=art_y_west),
    C(76, 80, 'night', 'card', year=231, main='畏蜀如虎', sub='诸将不服', art=art_y_lucheng),
    # ---- 第三回 对阵孔明
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'fate', 'card', year=234, main='坚壁不战', sub='以逸待劳', art=art_y_hold),
    C(86, 90, 'night', 'card', year=234, main='巾帼之辱', sub='不为所动', art=art_y_dress),
    C(90, 94, 'court', 'card', year=234, main='食少事烦', sub='料定孔明', art=art_y_food),
    C(94, 102, 'war', 'shangfang', year=234),
    C(102, 108, 'empire', 'card', year=238, main='平辽东', sub='一年往返', art=art_y_liaodong),
    C(108, 112, 'death', 'card', year=239, main='明帝托孤', sub='再受顾命', art=art_y_ruidi),
    # ---- 第四回 高平陵
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'court', 'card', year=239, main='曹爽专权', sub='明升暗降', art=art_y_caoshuang),
    C(118, 124, 'night', 'card', year=248, main='装病', sub='又一次', art=art_y_sick2),
    C(124, 128, 'works', 'card', year=248, main='死士三千', sub='暗中布局', art=art_y_soldiers),
    C(128, 136, 'empire', 'card', year=249, main='高平陵之变', sub='一击致命', art=art_y_gaoping),
    C(136, 144, 'war', 'card', year=251, main='平王凌', sub='最后一战', art=art_y_wangling),
    # ---- 第五回 三马同槽
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=251, main='司马懿去世', sub='不坟不树', art=art_y_death),
    C(150, 154, 'court', 'card', year=255, main='师昭专权', sub='司马之心', art=art_y_sons),
    C(154, 158, 'empire', 'card', year=266, main='晋代魏', sub='孙子称帝', art=art_y_jin),
    C(158, 162, 'works', 'card', year=266, main='追尊宣帝', sub='晋宣帝', art=art_y_xuandi),
    C(162, 166, 'night', 'card', year=325, main='覆面著床', sub='后人之叹', art=art_y_mingdi),
    C(166, 170, 'end', 'card', year=325, main='隐忍', sub='最后的赢家', art=art_y_patience),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='陆拾贰', col=MOXUAN, acc=WEIJIN, born=179, died=251, age0=178,
    born_lab='179年', died_lab='251年', years_txt='公元179 — 251',
    hook_q='他装了一辈子病 · 为什么最后赢了天下？',
    name_line='司马懿 · 字仲达', name='司马懿', seal='宣帝', title_art=art_y_title,
    q1='隐忍大师？', q2='乱臣贼子？',
    end_art=art_y_legacy, end_big='隐忍', end_seal='宣帝',
    end_l1='他熬走了曹操 熬走了孔明', end_l2='最后熬来了一个晋朝',
    end_brush='死诸葛走生仲达', end_ask='能忍到最后 才是真本事吗？评论区聊聊', next='王羲之'),
    scenes=dict(chapter=scene_chapter, shangfang=scene_shangfang))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
