"""千古人物志 · 第壹佰零贰集 · 秦桧 (1091–1155)
Look: 铁像灰 + 金牌金, little gold-tablet corners, the West Lake hills of 临安 behind.
Chapter card: 金字牌 — gold tablets stack up chapter by chapter (2, 5, 9, 12); in the last chapter they give way to a pair of kneeling iron figures.
Set pieces: custom 8-beat scene 'jinpai' (十二道金牌), 6-beat 靖康北迁, 6-beat 莫须有, 6-beat 跪像.
Presented as plainly as the record allows; the judgement of later ages is shown as such.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_huangchao as Hc       # engine + helpers (previous episode)
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
from render_simayi import emperor
from render_sunwu import army, banner
from render_qijiguang import qi as yue
from render_quyuan import river
from render_songtaizu import tent

F.RIPPLE = False
TIEXIANG = (84, 84, 90)             # 铁像灰
JINPAI = (204, 160, 56)             # 金牌金
JINPAI_D = (140, 104, 24)           # 金牌金 (text)
S.LAYERS.append(('tiexiang', TIEXIANG, 0.9, 1.0))
S.LAYERS.append(('jinpai', JINPAI, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='跪', life='秦', court='相', night='夜', war='金', empire='和', works='书', fate='狱', death='殁', end='鉴')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = ((150, 146, 140), 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (JINPAI, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (TIEXIANG, 170, (W * 0.5, 720))
G.THEMES['night']['sun'] = None
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # West Lake shoreline and a little pagoda at the right margin
    _d.line((80, 1400 + _k * 12, 1000, 1400 + _k * 12), fill=(90, 120, 130, 50 - _k * 12), width=3)
for _k in range(5):
    _d.rectangle((950 - (5 - _k) * 6, 1390 - _k * 26, 950 + (5 - _k) * 6, 1390 - _k * 26 + 20), fill=(110, 106, 100, 60))
MTN_COL = {'night': (28, 30, 34), 'death': (60, 58, 60), 'war': (110, 66, 54), 'fate': (92, 92, 96)}
def draw_background(t, theme):
    """临安: soft lake hills, a shoreline and a small pagoda."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(194, 196, 194), (162, 166, 164), MTN_COL.get(theme, (104, 112, 112))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.72))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """金字牌: a small gold tablet in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=TIEXIANG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=TIEXIANG + (220,), width=3)
        cx, cy = x + sx * 50, y + sy * 50
        d.rectangle((cx - 14, cy - 26, cx + 14, cy + 26), fill=JINPAI + (235,))
        d.rectangle((cx - 9, cy - 20, cx + 9, cy + 20), outline=(120, 80, 20, 235), width=2)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def qin_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """秦桧: a Song chief minister — long-winged 展脚幞头, a grey-purple robe, a thin beard."""
    b = bow + 6 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    if kw.get('fall'):
        return hand
    if up:
        A.d[layer].rectangle((x - 0.07 * h, y - 1.1 * h, x + 0.07 * h, y - 0.93 * h), fill=255)
        A.d[layer].line((x - 0.32 * h, y - 1.0 * h, x + 0.32 * h, y - 1.0 * h), fill=255, width=max(2, int(0.012 * h)))
        A.d['wash' if old > 0.5 else layer].polygon([(x, y - 0.86 * h), (x + dir * 0.05 * h, y - 0.86 * h), (x + dir * 0.03 * h, y - 0.66 * h)], fill=255)
    top = y - (0.48 if kneel else 0.76) * h
    A.d['tiexiang'].polygon([(x - 0.1 * h, top), (x + 0.1 * h, top), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=150)
    return hand

def gaozong(A, x, y, h, dir=-1, **kw):
    return emperor(A, x, y, h, dir=dir, **kw)

def tablet(A, x, y, s, layer='jinpai'):
    A.d[layer].rectangle((x - 0.3 * s, y - s, x + 0.3 * s, y + s), fill=255)
    A.d['ink'].rectangle((x - 0.22 * s, y - 0.86 * s, x + 0.22 * s, y + 0.86 * s), outline=180, width=3)

def kneel_iron(A, x, base, s, dir=1, female=False):
    """跪像: a kneeling iron figure, hands bound behind, on a low plinth."""
    A.d['mid'].rectangle((x - 0.7 * s, base - 0.12 * s, x + 0.7 * s, base), fill=255)
    person(A, x, base - 0.12 * s, s, dir=dir, robe=True, hat='none', female=female, kneel=True, bow=25, arm=-30, layer='tiexiang')

def jin_rider(A, x, y, s, dir=-1, ph=0.0):
    rider(A, x, y, s, dir=dir, ph=ph, layer='mid', spear=True)

# ================================================================ chapter card
CH = {16: (0, 2), 48: (2, 5), 80: (5, 9), 112: (9, 12), 144: None}
def art_tablet_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    q = ease_out(u / (1.4 * P))
    if CH.get(kb, 0) is None:
        ground(A, 1230)
        kneel_iron(A, 440, 1230, 220, dir=1)
        kneel_iron(A, 660, 1230, 200, dir=-1, female=True)
        return
    a, b = CH.get(kb, (2, 5))
    n = int(lerp(a, b, clamp((q - 0.2) / 0.6)))
    for i in range(n):
        tablet(A, 300 + (i % 6) * 96, 1000 + (i // 6) * 190, 80)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_tablet_chapter)
    ink_in(cv, text_img(no, SERIF, 56, TIEXIANG, 'Black', bleed=False, spacing=12), W / 2, 1330, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1450, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_q_hook_kneel(A, cv, t, u):
    ground(A, GROUND)
    kneel_iron(A, 420, GROUND, 260, dir=1)
    kneel_iron(A, 680, GROUND, 240, dir=-1, female=True)

def art_q_hook_tablets(A, cv, t, u):
    for i in range(min(12, int(u / (0.12 * P)) + 1)):
        tablet(A, 300 + (i % 6) * 96, 1000 + (i // 6) * 190, 80)

def art_q_hook_three(A, cv, t, u):
    A.flush(cv)
    paste(cv, text_img('莫须有', SERIF, 120, ZHU, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp(u / 0.6))

def art_q_hook_name(A, cv, t, u):
    ground(A, GROUND)
    qin_(A, 540, GROUND, 300, dir=1, arm=-8, layer='mid')

# ================================================================ 第一回 江宁
def art_q_birth(A, cv, t, u):
    A.d['ocean'].rectangle((60, GROUND - 60, W - 60, GROUND + 40), fill=150)
    river(A, GROUND - 56, t, rows=2, amp=3)
    palace(A, 540, GROUND - 60, 240, layer='mid')
    A.flush(cv)
    paste(cv, text_img('生于江宁 一个小官吏之家', SERIF, 48, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_q_teacher(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 420, layer='mid')
    qin_(A, 760, GROUND, 190, dir=-1, kneel=True, arm=80)
    for k in range(3):
        person(A, 260 + k * 110, GROUND, 110, dir=1, robe=True, hat='none', kneel=True, arm=100, layer='ink')
    A.flush(cv)
    paste(cv, text_img('早年做过私塾先生', SERIF, 50, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '自嘲猢狲王之诗 出自后人笔记', t, t - u + P)

def art_q_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    qin_(A, 540, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('二十五岁 进士及第', SERIF, 52, TIEXIANG, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_q_yushi(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    qin_(A, 380, GROUND, 200, dir=1, arm=80)
    A.flush(cv)
    paste(cv, text_img('靖康年间 力主抗金 反对割地', SERIF, 46, TIEXIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '早年颇有气节 后人常忽略此节', t, t - u + P)

def art_q_jingkang(A, cv, t, u):
    """6-beat set piece: 靖康 — 汴京 falls; he objects to the puppet 张邦昌 and asks that the 赵 house be kept; he is carried north with the two emperors."""
    ph = u / P
    if ph < 3:
        city_wall(A, 160, 920, 1080, gate_x=540, label='汴京', layer='mid', open_=1.0)
        flames(A, 540, 1080, 640, 200, t, n=6, seed=1127, smoke=True)
        ground(A, GROUND)
        lab = '金兵攻破汴京'
    else:
        for k in range(3):
            x = 260 + k * 280
            A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 220), (x + 240, GROUND)], fill=140)
        ground(A, GROUND)
        for k in range(3):
            person(A, lerp(200, 700, clamp((ph - 3) / 3)) + k * 110, GROUND, 170, dir=1, ph=t * 2 + k, robe=True, hat='crown' if k < 2 else 'none', bow=20, arm=-8, layer='ink' if k == 2 else 'mid')
        jin_rider(A, lerp(-100, 400, clamp((ph - 3) / 3)), GROUND, 130, dir=1, ph=t * 6)
        lab = '徽钦二帝被掳北上 秦桧同行'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '他曾上书反对金人另立张邦昌', t, t - u + P)

# ================================================================ 第二回 南归
def art_q_return(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=150)
    waves(A, 1250, t, rows=2, amp=4)
    boat(A, lerp(200, 800, ease_out(u / (3 * P))), 1260, 100, t)
    A.flush(cv)
    paste(cv, text_img('三年后携妻南归 自称杀监而逃', SERIF, 46, TIEXIANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '当时就有人怀疑是金人纵归', t, t - u + P)

def art_q_xiang1(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    gaozong(A, 740, GROUND, 210, dir=-1, arm=60)
    qin_(A, 400, GROUND, 200, dir=1, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('深得宋高宗信任 拜为宰相', SERIF, 48, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_q_nanbei(A, cv, t, u):
    ground(A, GROUND)
    A.d['ocean'].line((60, 1100, 1020, 1120), fill=200, width=8)
    A.flush(cv)
    paste(cv, text_img('南自南 北自北', SERIF, 66, INK, 'Black', bleed=False, spacing=14), W / 2, 1100, 1, clamp(u / 0.4))
    paste(cv, text_img('主张南北分治 不久罢相', SERIF, 48, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '北方人归金 南方人归宋', t, t - u + P)

def art_q_xiang2(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    gaozong(A, 740, GROUND, 210, dir=-1, arm=60)
    qin_(A, 400, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('再度拜相 独揽朝政', SERIF, 50, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '此后独相近二十年', t, t - u + P)

def art_q_yuefei(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        banner(A, 200 + k * 220, GROUND, 260, t, layer='red')
    yue(A, 540, GROUND, 230, dir=1, arm=140)
    A.flush(cv)
    paste(cv, text_img('岳飞北伐 郾城大捷 直抵朱仙镇', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '岳飞见第十四集', t, t - u + P)

# ================================================================ 第三回 金牌
def scene_jinpai(cv, t, c, k):
    """8-beat custom scene: 十二道金牌 — at the front 岳飞 is winning; riders arrive one after another with gold tablets ordering him back;
    twelve in one day; he turns his army around: 十年之功 废于一旦."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    tent(A, 760, GROUND, 260, 220, layer='mid', open_=1.0)
    for kk in range(3):
        banner(A, 900 + kk * 50, GROUND, 240, t, layer='red', fallen=clamp((ph - 6) / 1.5) * (0.5 + 0.2 * kk))
    n = min(12, int(max(0, ph - 0.5) / 0.45) + 1) if ph > 0.5 else 0
    for i in range(n):
        tablet(A, 120 + (i % 6) * 70, 900 + (i // 6) * 130, 50)
    if ph < 6:
        rider(A, lerp(-100, 560, ((ph - 0.5) / 0.45) % 1), GROUND, 120, dir=1, ph=t * 8, layer='ink')
    yue(A, 760, GROUND, 210, dir=-1, kneel=ph >= 6, bow=20 if ph >= 6 else 0, arm=-8)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '十二道金牌', BRUSH, 140, INK, W / 2, 440, t, s0, stagger=0.06, seed=102)
    fx.flush(cv)
    if ph < 6:
        lab, col = f'第{cn_num(max(1, n))}道金字牌 催他班师', JINPAI_D
    else:
        lab, col = '岳飞叹 十年之功 废于一旦', ZHU
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 575, 1, 1)
    note_in(cv, '一日奉十二金字牌 见宋史 岳飞传', t, s0 + 3 * P)

def art_q_bingquan(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    for k in range(3):
        person(A, 300 + k * 120, GROUND, 180, dir=1, robe=False, hat='helmet', bow=20, arm=-8, layer='ink' if k == 1 else 'mid')
    qin_(A, 760, GROUND, 200, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('收韩世忠 张俊 岳飞三大将兵权', SERIF, 44, TIEXIANG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_q_moxuyou(A, cv, t, u):
    """6-beat set piece: 莫须有 — 岳飞 is jailed on a trumped-up charge; 韩世忠 asks for the evidence; the answer is 莫须有."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        for kk in range(7):
            A.d['ink'].rectangle((300 + kk * 70, GROUND - 400, 312 + kk * 70, GROUND), fill=255)
        yue(A, 560, GROUND, 190, dir=1, kneel=True, arm=-8)
        lab, col = '岳飞以谋反罪名下狱', ZHU
    else:
        person(A, 700, GROUND, 210, dir=-1, robe=False, hat='helmet', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='mid')
        qin_(A, 380, GROUND, 200, dir=1, arm=-8)
        lab, col = ('韩世忠质问 证据何在', TIEXIANG) if ph < 4 else ('秦桧答 其事体莫须有', ZHU)
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 50, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('莫须有三字 何以服天下', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 4.5) / 0.4))
    note_in(cv, '见宋史 岳飞传', t, t - u + P)

def art_q_fengbo(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].polygon([(380, GROUND - 260), (700, GROUND - 260), (540, GROUND - 360)], fill=255)
    for x in (400, 680):
        A.d['ink'].rectangle((x - 8, GROUND - 260, x + 8, GROUND), fill=255)
    yue(A, 540, GROUND, 190, dir=1, kneel=True, bow=10, arm=-8)
    A.flush(cv)
    paste(cv, text_img('岳飞遇害 年仅三十九岁', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '后世相传遇害于大理寺风波亭', t, t - u + P)

def art_q_heyi(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('称臣 割地\n岁贡银绢各二十五万', SERIF, 36, INK, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('绍兴和议 以淮水为界', SERIF, 50, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_q_gaozong(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    gaozong(A, 540, GROUND, 230, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('主和与杀岳飞 背后是宋高宗的意志', SERIF, 44, TIEXIANG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '史家多认为高宗才是真正的主导者', t, t - u + P)

# ================================================================ 第四回 专权
def art_q_power(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    qin_(A, 540, GROUND, 230, dir=1, arm=60, old=0.4)
    for k in range(4):
        person(A, 160 + k * 70 if k < 2 else 820 + (k - 2) * 70, GROUND, 150, dir=1 if k < 2 else -1, robe=True, hat='knot', bow=40, arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('专权十九年 党羽遍布朝中', SERIF, 48, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_q_wenziyu(A, cv, t, u):
    ground(A, GROUND)
    for kk in range(7):
        A.d['ink'].rectangle((300 + kk * 70, GROUND - 400, 312 + kk * 70, GROUND), fill=255)
    person(A, 560, GROUND, 180, dir=1, robe=True, hat='knot', kneel=True, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('大兴文字狱 打压主战之士', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '李光 胡铨等人相继被贬', t, t - u + P)

def art_q_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    qin_(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('秦桧病逝 终年六十五岁', SERIF, 50, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '死后追封申王 谥忠献', t, t - u + P)

def art_q_rehab(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((440, GROUND - 420, 640, GROUND), fill=230)
    A.d['ink'].rectangle((440, GROUND - 420, 640, GROUND), outline=255, width=5)
    A.flush(cv)
    paste(cv, text_img('孝宗为岳飞平反昭雪', SERIF, 50, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '追谥武穆 后又追封鄂王', t, t - u + P)

def art_q_miuchou(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((440, GROUND - 420, 640, GROUND), fill=230)
    A.d['ink'].rectangle((440, GROUND - 420, 640, GROUND), outline=255, width=5)
    A.flush(cv)
    paste(cv, text_img('谥\n谬\n丑', SERIF, 60, ZHU, 'Black', bleed=False, spacing=8), W / 2, GROUND - 210, 1, clamp((u - 0.5 * P) / 0.4))
    paste(cv, text_img('宁宗追夺王爵 改谥谬丑', SERIF, 50, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

# ================================================================ 第五回 鉴
def art_q_guixiang(A, cv, t, u):
    """6-beat set piece: 跪像 — before 岳飞's tomb on the West Lake the iron figures of 秦桧 and his wife kneel; they have been recast many times."""
    ph = u / P
    ground(A, GROUND)
    A.d['mid'].chord((620, GROUND - 160, 1000, GROUND + 160), 180, 360, fill=220)
    A.d['ink'].rectangle((790, GROUND - 260, 830, GROUND - 120), fill=255)
    kneel_iron(A, 300, GROUND, 220, dir=1)
    kneel_iron(A, 500, GROUND, 200, dir=1, female=True)
    A.flush(cv)
    lab = '明代起 岳飞墓前铸跪像' if ph < 3 else '跪像屡毁屡铸 至今仍在'
    paste(cv, text_img(lab, SERIF, 50, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '青山有幸埋忠骨 白铁无辜铸佞臣', t, t - u + 3 * P)

def art_q_name(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 220, dir=1, robe=True, hat='knot', bow=30, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('人从宋后少名桧 我到坟前愧姓秦', SERIF, 44, TIEXIANG, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '相传为清人秦大士所作', t, t - u + P)

def art_q_youtiao(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].chord((380, GROUND - 160, 700, GROUND + 60), 180, 360, fill=255)
    for k in range(2):
        A.d['jinpai'].rounded_rectangle((420 + k * 20, GROUND - 220 + k * 30, 660 - k * 20, GROUND - 190 + k * 30), radius=14, fill=255)
    A.flush(cv)
    paste(cv, text_img('相传百姓炸面食泄愤 称油炸桧', SERIF, 46, JINPAI_D, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '民间传说', t, t - u + P)

def art_q_eval(A, cv, t, u):
    ground(A, GROUND)
    qin_(A, 540, GROUND, 280, dir=1, arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('他做的事 史书写得明明白白', SERIF, 48, TIEXIANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('后人的评价 也跪了八百年', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_q_end(A, cv, t, u):
    ground(A, GROUND)
    kneel_iron(A, 420, GROUND, 240, dir=1)
    kneel_iron(A, 660, GROUND, 220, dir=-1, female=True)
    A.flush(cv)
    paste(cv, text_img('以史为鉴', SERIF, 60, TIEXIANG, 'Black', bleed=False, spacing=12), W / 2, 760, 1, clamp(u / 0.4))

def art_q_legacy(A, cv, t, u):
    tablet(A, 860, 1380, 40)

def art_q_title(A, cv, t, u):
    for i in range(3):
        tablet(A, 760 + i * 70, 1240, 60)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    qin_(A, 380, 1460, 680, dir=1, arm=lerp(-5, 30, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '江宁'), 48: ('第二回', '南归'), 80: ('第三回', '金牌'),
            112: ('第四回', '专权'), 144: ('第五回', '跪像')}

CARDS = [
    C(0, 2, 'death', 'num', num='跪了五百年', line='岳飞墓前的铁像', art=art_q_hook_kneel),
    C(2, 4, 'war', 'num', num='十二道金牌', line='一天之内召回岳飞', art=art_q_hook_tablets),
    C(4, 6, 'fate', 'num', num='莫须有', line='三个字杀了一位名将', art=art_q_hook_three),
    C(6, 8, 'night', 'num', num='宋后少名桧', line='连名字都没人敢用', art=art_q_hook_name),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 江宁
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1091, main='生于江宁', sub='小吏之家', art=art_q_birth),
    C(22, 26, 'works', 'card', year=1110, main='私塾先生', sub='早年', note='年份约略', art=art_q_teacher),
    C(26, 30, 'court', 'card', year=1115, main='进士', sub='二十五岁', art=art_q_jinshi),
    C(30, 36, 'empire', 'card', year=1126, main='主战', sub='反对割地', art=art_q_yushi),
    C(36, 48, 'war', 'card', year=1127, main='靖康', sub='被掳北上', art=art_q_jingkang),
    # ---- 第二回 南归
    C(48, 50, 'night', 'chapter'),
    C(50, 56, 'fate', 'card', year=1130, main='南归', sub='疑云', art=art_q_return),
    C(56, 60, 'court', 'card', year=1131, main='拜相', sub='四十一岁', art=art_q_xiang1),
    C(60, 66, 'night', 'card', year=1132, main='南自南', sub='北自北', art=art_q_nanbei),
    C(66, 72, 'empire', 'card', year=1138, main='再相', sub='独揽朝政', art=art_q_xiang2),
    C(72, 80, 'war', 'card', year=1140, main='岳飞北伐', sub='朱仙镇', art=art_q_yuefei),
    # ---- 第三回 金牌
    C(80, 82, 'war', 'chapter'),
    C(82, 90, 'fate', 'jinpai', year=1140),
    C(90, 94, 'court', 'card', year=1141, main='收兵权', sub='三大将', art=art_q_bingquan),
    C(94, 100, 'death', 'card', year=1141, main='莫须有', sub='岳飞下狱', art=art_q_moxuyou),
    C(100, 104, 'death', 'card', year=1142, main='岳飞遇害', sub='三十九岁', art=art_q_fengbo),
    C(104, 108, 'empire', 'card', year=1141, main='绍兴和议', sub='称臣纳贡', art=art_q_heyi),
    C(108, 112, 'night', 'card', year=1142, main='高宗', sub='真正的主导', art=art_q_gaozong),
    # ---- 第四回 专权
    C(112, 114, 'court', 'chapter'),
    C(114, 120, 'court', 'card', year=1145, main='专权', sub='十九年', note='年份约略', art=art_q_power),
    C(120, 126, 'fate', 'card', year=1150, main='文字狱', sub='打压异己', note='年份约略', art=art_q_wenziyu),
    C(126, 132, 'death', 'card', year=1155, main='秦桧病死', sub='六十五岁', art=art_q_death),
    C(132, 138, 'empire', 'card', year=1162, main='岳飞平反', sub='孝宗', art=art_q_rehab),
    C(138, 144, 'war', 'card', year=1206, main='改谥谬丑', sub='宁宗', art=art_q_miuchou),
    # ---- 第五回 跪像
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'death', 'card', year=1513, main='跪像', sub='西湖岳庙', note='年份约略', art=art_q_guixiang),
    C(152, 156, 'night', 'card', year=1760, main='愧姓秦', sub='后人之叹', note='年份约略', art=art_q_name),
    C(156, 160, 'life', 'card', year=1760, main='油炸桧', sub='民间传说', art=art_q_youtiao),
    C(160, 165, 'fate', 'card', year=2000, main='评说', sub='千秋功罪', art=art_q_eval),
    C(165, 170, 'end', 'card', year=2000, main='以史为鉴', sub='跪像无言', art=art_q_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='壹佰零贰', col=TIEXIANG, acc=JINPAI, born=1091, died=1155, age0=1090,
    born_lab='1091年', died_lab='1155年', years_txt='公元1091 — 1155',
    hook_q='他也曾是主战的忠臣 · 后来为什么成了千古罪人？',
    name_line='秦桧 · 字会之', name='秦桧', seal='会之', title_art=art_q_title,
    q1='千古奸臣？', q2='替罪之人？',
    end_art=art_q_legacy, end_big='跪像', end_seal='以史为鉴',
    end_l1='他在位时权倾朝野', end_l2='身后却在岳飞墓前跪了五百年',
    end_brush='以史为鉴', end_ask='你觉得杀岳飞的责任该谁来担？评论区聊聊', next='袁崇焕'),
    scenes=dict(chapter=scene_chapter, jinpai=scene_jinpai))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
