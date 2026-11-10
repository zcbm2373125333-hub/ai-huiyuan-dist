"""千古人物志 · 第玖拾贰集 · 林觉民 (1887–1911)
Look: 意映青 + 黄花色, little flower sprigs in the corners, Fuzhou rooftops behind.
Chapter card: 方巾 — the white handkerchief of 与妻书; more columns of writing appear each chapter; in the last chapter yellow flowers grow round it.
Set pieces: custom 8-beat scene 'yuqishu' (与妻书), 6-beat 攻督署, 6-beat 受审, 6-beat 黄花岗.
Ages are counted in 虚岁 (age0 = born - 1); he died at 24 by Western count.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_jixiaolan as Jx       # engine + helpers (previous episode)
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
from render_wangyangming import desk, scroll, lamp
from render_zhuxi import book
from render_jixiaolan import qhat
from render_zhengchenggong import junk, sea

F.RIPPLE = False
YIYING = (64, 104, 112)             # 意映青
HUANGHUA = (214, 170, 60)           # 黄花色
S.LAYERS.append(('yiying', YIYING, 0.9, 1.0))
S.LAYERS.append(('huanghua', HUANGHUA, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='卿', life='林', court='民', night='书', war='义', empire='国', works='志', fate='别', death='殇', end='卿')
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
G.THEMES['empire']['sun'] = (YIYING, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (HUANGHUA, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _x in (130, 950):               # Fuzhou horse-head gables at the margins
    _d.polygon([(_x - 70, 1420), (_x - 70, 1330), (_x - 40, 1300), (_x, 1330), (_x + 40, 1300), (_x + 70, 1330), (_x + 70, 1420)], fill=(120, 120, 116, 60))
for _k in range(3):
    _d.line((200, 1424 + _k * 12, 880, 1424 + _k * 12), fill=YIYING + (40 - _k * 10,), width=2)
MTN_COL = {'night': (28, 34, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (90, 96, 100)}
def draw_background(t, theme):
    """福州: low hills, two horse-head gable walls at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(194, 196, 192), (160, 168, 166), MTN_COL.get(theme, (100, 120, 122))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.72))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """黄花: a small sprig of yellow flowers in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=YIYING + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=YIYING + (220,), width=3)
        cx, cy = x + sx * 50, y + sy * 50
        d.line((cx, cy, cx + sx * 30, cy + sy * 30), fill=(90, 110, 70, 230), width=3)
        for k in range(5):
            a = k * 2 * math.pi / 5
            px, py = cx + 10 * math.cos(a), cy + 10 * math.sin(a)
            d.ellipse((px - 6, py - 6, px + 6, py + 6), fill=HUANGHUA + (235,))
        d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(150, 90, 40, 235))

# ================================================================ primitives
def lin_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, suit=True, **kw):
    """林觉民: short-haired young man (queue cut) in a dark student jacket, a lighter collar."""
    hand = person(A, x, y, h, dir=dir, robe=not suit, hat='none', layer=layer, kneel=kneel, bow=bow, **kw)
    if kw.get('fall'):
        return hand
    top = y - (0.48 if kneel else 0.76) * h
    A.d['yiying'].polygon([(x - 0.1 * h, top), (x + 0.1 * h, top), (x + 0.12 * h, top + 0.38 * h), (x - 0.12 * h, top + 0.38 * h)], fill=170)
    return hand

def wife(A, x, y, h, dir=-1, layer='mid', **kw):
    """陈意映: a young woman with a bun; a pale flowered jacket."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', female=True, layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        A.d['huanghua'].polygon([(x - 0.09 * h, y - 0.76 * h), (x + 0.09 * h, y - 0.76 * h), (x + 0.12 * h, y - 0.45 * h), (x - 0.12 * h, y - 0.45 * h)], fill=140)
    return hand

def hanky(A, cx, cy, s, cols, ang=-0.05):
    """方巾: a white square of cloth, slightly turned; `cols` columns of writing from right to left."""
    c, si = math.cos(ang), math.sin(ang)
    def R(px, py): return (cx + px * c - py * si, cy + px * si + py * c)
    A.d['wash'].polygon([R(-s, -s), R(s, -s), R(s, s), R(-s, s)], fill=255)
    A.d['ink'].polygon([R(-s, -s), R(s, -s), R(s, s), R(-s, s)], outline=180)
    n = int(cols)
    for k in range(min(n, 14)):
        px = s * 0.85 - k * s * 0.13
        L_ = 1.7 * s * (0.9 if k % 4 else 0.6)
        A.d['ink'].line([R(px, -s * 0.85), R(px, -s * 0.85 + L_)], fill=200, width=max(2, int(0.025 * s)))

def flowers(A, x0, x1, base, n, t, grow=1.0, seed=92):
    rng = random.Random(seed)
    for k in range(n):
        x = lerp(x0, x1, rng.random())
        h = (40 + 60 * rng.random()) * grow
        A.d['grass'].line((x, base, x + 6 * math.sin(t + k), base - h), fill=230, width=3)
        if grow > 0.3:
            r = 9 * grow
            A.d['huanghua'].ellipse((x - r + 6 * math.sin(t + k), base - h - r, x + r + 6 * math.sin(t + k), base - h + r), fill=255)

def mound(A, cx, base, w):
    A.d['mid'].chord((cx - w, base - 0.6 * w, cx + w, base + 0.6 * w), 180, 360, fill=220)

def official(A, x, y, h, dir=-1, layer='mid', **kw):
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        qhat(A, x, y, h, layer)
    return hand

# ================================================================ chapter card
CH = {16: (0, 3), 48: (3, 6), 80: (6, 9), 112: (9, 12), 144: (12, 14)}
def art_hanky_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (3, 6))
    q = ease_out(u / (1.4 * P))
    hanky(A, 540, 1040, 220, lerp(a, b, clamp((q - 0.2) / 0.6)))
    if kb == 144:
        flowers(A, 260, 820, 1250, 14, t, grow=clamp((q - 0.3) / 0.5))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_hanky_chapter)
    ink_in(cv, text_img(no, SERIF, 56, YIYING, 'Black', bleed=False, spacing=12), W / 2, 1320, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1445, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_l_hook_age(A, cv, t, u):
    ground(A, GROUND)
    lin_(A, 540, GROUND, 320, dir=1, arm=-8)

def art_l_hook_hanky(A, cv, t, u):
    hanky(A, 540, 1120, 240, clamp(u / (1.4 * P)) * 12)

def art_l_hook_qing(A, cv, t, u):
    ground(A, GROUND)
    wife(A, 540, GROUND, 300, dir=1, arm=-8)

def art_l_hook_graves(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        mound(A, 180 + k * 180, GROUND, 70)
    flowers(A, 100, 980, GROUND, 18, t, grow=clamp(u / (1.4 * P)))

# ================================================================ 第一回 闽县
def art_l_birth(A, cv, t, u):
    A.d['wash'].rectangle((360, GROUND - 200, 720, GROUND), fill=255)
    A.d['ink'].polygon([(330, GROUND - 200), (750, GROUND - 200), (540, GROUND - 270)], fill=255)
    for x in (330, 750):
        A.d['mid'].polygon([(x - 40, GROUND), (x - 40, GROUND - 260), (x - 10, GROUND - 300), (x + 20, GROUND - 260), (x + 20, GROUND)], fill=230)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('生于福建闽县 今福州', SERIF, 48, YIYING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('福州', 56), 860, 1020, t, t - u + P, rot=6)

def art_l_adopt(A, cv, t, u):
    ground(A, GROUND)
    person(A, 640, GROUND, 200, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
    person(A, 440, GROUND, 90, dir=1, robe=True, hat='none', arm=60, layer='ink')
    A.flush(cv)
    paste(cv, text_img('过继给叔父林孝颖', SERIF, 50, YIYING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '嗣父是当地有名的才子', t, t - u + P)

def art_l_exam(A, cv, t, u):
    ground(A, GROUND)
    for i in range(5):
        x = 180 + i * 180
        A.d['mid'].rectangle((x - 60, GROUND - 150, x + 60, GROUND), fill=200)
    lin_(A, lerp(540, 1000, clamp((u - P) / (2 * P))), GROUND, 130, dir=1, suit=False, ph=t * 3 if u > P else None, arm=-8)
    A.flush(cv)
    paste(cv, text_img('应童子试 写下七字 掷笔而去', SERIF, 46, YIYING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '相传所写为 少年不望万户侯', t, t - u + P)

def art_l_school(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    lin_(A, 540, GROUND, 190, dir=1, suit=False, arm=60)
    A.flush(cv)
    paste(cv, text_img('考入全闽大学堂', SERIF, 50, YIYING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '接触新学 立志革命', t, t - u + P)

def art_l_speech(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((400, GROUND - 120, 680, GROUND), fill=220)
    lin_(A, 540, GROUND - 120, 190, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)))
    for k in range(6):
        person(A, 120 + k * 60 if k < 3 else 760 + (k - 3) * 70, GROUND, 120, dir=1 if k < 3 else -1, robe=True, hat='none', arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('当众演说 挽救垂亡之中国', SERIF, 46, YIYING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '听者动容 有人当场落泪', t, t - u + P)

def art_l_marry(A, cv, t, u):
    ground(A, GROUND)
    lin_(A, 420, GROUND, 200, dir=1, suit=False, arm=40)
    wife(A, 660, GROUND, 180, dir=-1, arm=40)
    A.flush(cv)
    paste(cv, text_img('娶妻陈意映', SERIF, 52, YIYING, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('意映', 56), 860, 1020, t, t - u + P, rot=6)

def art_l_shuangqi(A, cv, t, u):
    A.d['wash'].ellipse((700, 860, 820, 980), fill=255)
    A.d['wash'].rectangle((240, GROUND - 260, 840, GROUND), fill=200)
    A.d['ink'].rectangle((240, GROUND - 260, 840, GROUND), outline=255, width=6)
    for k in range(1, 4):
        A.d['ink'].line((240 + k * 150, GROUND - 260, 240 + k * 150, GROUND), fill=160, width=3)
    ground(A, GROUND)
    lin_(A, 480, GROUND, 180, dir=1, arm=-8)
    wife(A, 600, GROUND, 165, dir=-1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('后街小屋 月下并肩低语', SERIF, 48, YIYING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '此景后来写进与妻书', t, t - u + P)

# ================================================================ 第二回 东渡
def art_l_japan(A, cv, t, u):
    sea(A, 1260, t)
    junk(A, lerp(200, 800, ease_out(u / (3 * P))), 1280, 100, t, layer='yiying', flag_=False)
    A.flush(cv)
    paste(cv, text_img('东渡日本 入庆应大学', SERIF, 48, YIYING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '攻读文科 兼习英文 德文', t, t - u + P)

def art_l_tongmenghui(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        lin_(A, 240 + k * 200, GROUND, 180, dir=1, arm=lerp(-8, 150, clamp((u - 0.8 * P - k * 0.2 * P) / 0.4)), layer='ink' if k == 1 else 'mid')
    A.flush(cv)
    paste(cv, text_img('加入中国同盟会', SERIF, 50, YIYING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_l_plan(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 480, layer='mid')
    A.d['wash'].rectangle((360, GROUND - 90, 720, GROUND - 74), fill=255)
    lin_(A, 260, GROUND, 180, dir=1, arm=100)
    person(A, 820, GROUND, 190, dir=-1, robe=False, hat='none', arm=100, layer='mid')
    A.flush(cv)
    paste(cv, text_img('黄兴 赵声在香港筹划起义', SERIF, 46, YIYING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_recruit(A, cv, t, u):
    ground(A, GROUND)
    for k in range(min(6, int(u / (0.4 * P)) + 1)):
        person(A, 600 + k * 70, GROUND, 140, dir=-1, robe=False, hat='none', arm=-8, layer='mid')
    lin_(A, 360, GROUND, 190, dir=1, arm=80)
    A.flush(cv)
    paste(cv, text_img('回福州 招募敢死之士', SERIF, 48, YIYING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_l_lastsight(A, cv, t, u):
    A.d['wash'].rectangle((240, GROUND - 260, 840, GROUND), fill=200)
    A.d['ink'].rectangle((240, GROUND - 260, 840, GROUND), outline=255, width=6)
    ground(A, GROUND)
    wife(A, 640, GROUND, 170, dir=-1, arm=-8)
    lin_(A, lerp(460, 160, clamp((u - 2 * P) / (2 * P))), GROUND, 185, dir=1 if u < 2 * P else -1, arm=-8, ph=t * 2 if u > 2 * P else None)
    A.flush(cv)
    paste(cv, text_img('回家一趟 终究没有说出口', SERIF, 46, YIYING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '妻子已有身孕', t, t - u + P)

YUQI = ['意映卿卿如晤', '吾今以此书与汝永别矣', '吾至爱汝', '即此爱汝一念', '使吾勇于就死也']
def scene_yuqishu(cv, t, c, k):
    """8-beat custom scene: 与妻书 — night in Hong Kong three days before the rising; by lamplight he writes
    on a white handkerchief; the opening lines appear column by column."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    lin_(A, 260, GROUND, 180, dir=1, kneel=True, arm=lerp(95, 105, 0.5 + 0.5 * math.sin(t * 5)))
    lamp(A, 800, GROUND - 74, 30, t, glow=1.0)
    A.d['wash'].rectangle((420, GROUND - 86, 620, GROUND - 74), fill=255)
    hanky(A, 540, 1010, 190, 0, ang=0.0)
    A.flush(cv)
    n = min(len(YUQI), int(max(0, ph - 1.5) / 1.1) + 1) if ph > 1.5 else 0
    for i in range(n):
        a = clamp((ph - 1.5 - i * 1.1) / 0.6)
        paste(cv, text_img('\n'.join(YUQI[i]), SERIF, 32, INK, 'Black', bleed=False, spacing=2), 680 - i * 70, 1010, 1, a)
    fx = Art()
    chars_in(cv, fx, '与妻书', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=92)
    fx.flush(cv)
    if ph < 2:
        lab, col = '起义前三日 香港滨江楼', YIYING
    elif ph < 5:
        lab, col = '写在一方白巾之上', YIYING
    else:
        lab, col = '纸短情长 天亮前写完', ZHU
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '同夜还写了禀父书', t, s0 + 5 * P)

# ================================================================ 第三回 起义
def art_l_329(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='广州', layer='mid', open_=1.0)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('农历三月二十九 广州起义', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '公历4月27日 史称黄花岗起义', t, t - u + P)

def art_l_attack(A, cv, t, u):
    """6-beat set piece: 攻督署 — the dare-to-die squad storms the 两广总督署; it is empty; they fight on in the streets."""
    ph = u / P
    palace(A, 760, 1300, 300, layer='mid')
    ground(A, GROUND)
    if ph >= 1.5:
        flames(A, 760, 1240, 520, 220 * clamp((ph - 1.5) / 0.8), t, n=5, seed=1911, smoke=True)
    for k in range(5):
        x = lerp(80, 420, clamp(ph / 3)) + k * 60
        lin_(A, x, GROUND, 140, dir=1, ph=t * 6 + k, arm=80, layer='ink' if k == 2 else 'mid')
    A.flush(cv)
    if ph < 2:
        lab, col = '一百余人 直扑两广总督署', YIYING
    elif ph < 4:
        lab, col = '督署已空 放火后转战街巷', ZHU
    else:
        lab, col = '寡不敌众 清军四面合围', ZHU
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '黄兴亲率先锋 断去两指', t, t - u + 2 * P)

def art_l_captured(A, cv, t, u):
    ground(A, GROUND)
    lin_(A, 540, GROUND, 190, dir=1, kneel=u > P, arm=-8)
    for j in (-1, 1):
        person(A, 540 + j * 200, GROUND, 190, dir=-j, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    A.flush(cv)
    paste(cv, text_img('腰部中弹 力竭被俘', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_l_trial(A, cv, t, u):
    """6-beat set piece: 受审 — in chains before the governor and the admiral; his shackles are taken off and he is given a seat; he talks of the world for hours."""
    ph = u / P
    A.d['wash'].rectangle((560, GROUND - 90, 940, GROUND - 74), fill=255)
    A.d['ink'].rectangle((560, GROUND - 74, 940, GROUND), outline=255, width=5)
    official(A, 680, GROUND - 80, 160, dir=-1, kneel=True)
    official(A, 840, GROUND - 80, 160, dir=-1, kneel=True)
    ground(A, GROUND)
    if ph < 2:
        lin_(A, 320, GROUND, 190, dir=1, arm=-8)
        A.d['ink'].line((300, GROUND - 90, 340, GROUND - 90), fill=255, width=6)
        lab, col = '带镣上堂 立而不跪', YIYING
    elif ph < 3.5:
        A.d['mid'].rectangle((260, GROUND - 90, 380, GROUND - 76), fill=255)
        lin_(A, 320, GROUND, 190, dir=1, kneel=True, arm=60)
        lab, col = '据载李准命人去镣 赐座', YIYING
    else:
        A.d['mid'].rectangle((260, GROUND - 90, 380, GROUND - 76), fill=255)
        lin_(A, 320, GROUND, 190, dir=1, kneel=True, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 3)))
        lab, col = '纵论天下大势 劝其反正', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '主审为两广总督张鸣岐 水师提督李准', t, t - u + 0.5 * P)

def art_l_death(A, cv, t, u):
    ground(A, GROUND)
    lin_(A, 540, GROUND, 200, dir=1, arm=-8, fall=-88 * clamp((u - 1.5 * P) / 0.5))
    A.flush(cv)
    paste(cv, text_img('从容就义', SERIF, 56, ZHU, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '周岁二十四', t, t - u + P)

def art_l_bury(A, cv, t, u):
    ground(A, GROUND)
    for k in range(min(6, int(u / (0.4 * P)) + 1)):
        mound(A, 160 + k * 150, GROUND, 60)
    person(A, 900, GROUND, 170, dir=-1, robe=True, hat='none', bow=30, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('潘达微冒险收殓七十二具遗骸', SERIF, 44, YIYING, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '葬于红花岗 改名黄花岗', t, t - u + P)

# ================================================================ 第四回 意映
def art_l_letter(A, cv, t, u):
    A.d['ink'].rectangle((380, GROUND - 400, 700, GROUND), fill=255)
    A.d['wash'].rectangle((538, GROUND - 400, 542, GROUND), fill=255)
    ground(A, GROUND)
    q = clamp((u - 0.5 * P) / P)
    A.d['wash'].rectangle((lerp(560, 600, q), GROUND - 210, lerp(620, 660, q), GROUND - 190), fill=255)
    A.flush(cv)
    paste(cv, text_img('遗书被悄悄塞进家门', SERIF, 48, YIYING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '塞门缝之说出自后人回忆 细节不一', t, t - u + P)

def art_l_house(A, cv, t, u):
    A.d['wash'].rectangle((300, GROUND - 220, 780, GROUND), fill=255)
    for x in (300, 780):
        A.d['mid'].polygon([(x - 40, GROUND), (x - 40, GROUND - 280), (x - 10, GROUND - 320), (x + 20, GROUND - 280), (x + 20, GROUND)], fill=230)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('林家避祸搬离 旧宅易主', SERIF, 48, YIYING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '买下此宅的 是冰心的祖父', t, t - u + P)

def art_l_wuchang(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='武昌', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(3):
        A.d['ink'].line((260 + k * 280, 1080, 260 + k * 280, 900), fill=255, width=6)
        A.d['red'].rectangle((260 + k * 280, 900, 360 + k * 280, 960), fill=255)
    A.flush(cv)
    paste(cv, text_img('半年后 武昌起义成功', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_l_minguo(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('中华民国成立 清帝退位', SERIF, 48, YIYING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_l_yiying(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    wife(A, 540, 1200, 200, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('陈意映悲痛成疾 两年后病逝', SERIF, 46, YIYING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '遗腹子林仲新', t, t - u + P)

def art_l_huanghua(A, cv, t, u):
    """6-beat set piece: 黄花岗 — the burial mounds; a memorial arch rises; year after year yellow flowers grow."""
    ph = u / P
    ground(A, GROUND)
    for k in range(6):
        mound(A, 140 + k * 160, GROUND, 55)
    if ph >= 1.5:
        q = clamp((ph - 1.5) / 1.2)
        A.d['mid'].rectangle((380, GROUND - 120 - 300 * q, 700, GROUND - 120), fill=230)
        A.d['ink'].rectangle((360, GROUND - 120, 720, GROUND - 100), fill=255)
    flowers(A, 80, 1000, GROUND, 24, t, grow=clamp((ph - 3) / 1.5))
    A.flush(cv)
    lab = '七十二烈士墓' if ph < 3 else '黄花年年开'
    paste(cv, text_img(lab, SERIF, 52, YIYING if ph < 3 else (160, 112, 20), 'Black', bleed=False, spacing=8), W / 2, 760, 1, 1)
    note_in(cv, '后查明殉难者实为八十六人', t, t - u + 2 * P)

def art_l_visit(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        mound(A, 200 + k * 220, GROUND, 60)
    flowers(A, 100, 980, GROUND, 18, t)
    person(A, 540, GROUND, 170, dir=1, robe=True, hat='none', bow=30, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('后人年年凭吊', SERIF, 50, YIYING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 卿卿
def art_l_spread(A, cv, t, u):
    hanky(A, 540, 1120, 240, 14)
    A.flush(cv)
    paste(cv, text_img('与妻书广为传诵', SERIF, 50, YIYING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '原件今藏福州', t, t - u + P)

def art_l_textbook(A, cv, t, u):
    ground(A, GROUND)
    book(A, 540, GROUND - 74, 200, 0, layer='yiying', open_=1.0)
    desk(A, 540, GROUND, 460, layer='mid')
    A.flush(cv)
    paste(cv, text_img('选入中学语文课本', SERIF, 50, YIYING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def _quote(A, cv, t, u, text, note=None):
    hanky(A, 540, 1200, 190, 14)
    A.flush(cv)
    paste(cv, text_img(text, SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.5))
    if note:
        note_in(cv, note, t, t - u + P)

def art_l_q1(A, cv, t, u):
    _quote(A, cv, t, u, '吾至爱汝 即此爱汝一念\n使吾勇于就死也')

def art_l_q2(A, cv, t, u):
    _quote(A, cv, t, u, '吾充吾爱汝之心\n助天下人爱其所爱')

def art_l_q3(A, cv, t, u):
    _quote(A, cv, t, u, '汝幸而偶我\n又何不幸而生今日之中国', '黄花岗起义一百周年')

def art_l_end(A, cv, t, u):
    ground(A, GROUND)
    flowers(A, 100, 980, GROUND, 26, t)
    lin_(A, 440, GROUND, 190, dir=1, arm=-8)
    wife(A, 620, GROUND, 175, dir=-1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('意映卿卿如晤', SERIF, 52, YIYING, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))

def art_l_legacy(A, cv, t, u):
    flowers(A, 800, 920, 1420, 6, t)

def art_l_title(A, cv, t, u):
    hanky(A, 820, 1220, 120, 10)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    lin_(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '闽县'), 48: ('第二回', '东渡'), 80: ('第三回', '起义'),
            112: ('第四回', '意映'), 144: ('第五回', '卿卿')}

CARDS = [
    C(0, 2, 'death', 'num', num='二十五岁', line='他在广州从容就义', art=art_l_hook_age),
    C(2, 4, 'night', 'num', num='一方白巾', line='写下一封诀别信', art=art_l_hook_hanky),
    C(4, 6, 'life', 'num', num='意映卿卿', line='是写给妻子的开头', art=art_l_hook_qing),
    C(6, 8, 'fate', 'num', num='七十二人', line='同葬黄花岗', art=art_l_hook_graves),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 闽县
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1887, main='生于福州', sub='闽县', art=art_l_birth),
    C(22, 26, 'works', 'card', year=1888, main='过继叔父', sub='林孝颖', note='年份约略', art=art_l_adopt),
    C(26, 30, 'fate', 'card', year=1899, main='童子试', sub='掷笔而去', note='年份约略', art=art_l_exam),
    C(30, 34, 'court', 'card', year=1902, main='全闽大学堂', sub='十六岁', art=art_l_school),
    C(34, 40, 'empire', 'card', year=1903, main='演说', sub='挽救中国', note='年份约略', art=art_l_speech),
    C(40, 44, 'life', 'card', year=1905, main='娶妻', sub='陈意映', art=art_l_marry),
    C(44, 48, 'night', 'card', year=1906, main='双栖之所', sub='后街小屋', note='年份约略', art=art_l_shuangqi),
    # ---- 第二回 东渡
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'life', 'card', year=1907, main='留学日本', sub='庆应大学', art=art_l_japan),
    C(54, 58, 'empire', 'card', year=1907, main='同盟会', sub='立誓革命', note='年份约略', art=art_l_tongmenghui),
    C(58, 62, 'court', 'card', year=1911, main='筹划起义', sub='香港', art=art_l_plan),
    C(62, 66, 'works', 'card', year=1911, main='回闽招募', sub='敢死之士', art=art_l_recruit),
    C(66, 72, 'fate', 'card', year=1911, main='最后一面', sub='不忍明言', art=art_l_lastsight),
    C(72, 80, 'night', 'yuqishu', year=1911),
    # ---- 第三回 起义
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'empire', 'card', year=1911, main='三二九', sub='广州', art=art_l_329),
    C(86, 92, 'war', 'card', year=1911, main='攻督署', sub='敢死队', art=art_l_attack),
    C(92, 96, 'fate', 'card', year=1911, main='被俘', sub='身负重伤', art=art_l_captured),
    C(96, 102, 'court', 'card', year=1911, main='受审', sub='慷慨陈词', art=art_l_trial),
    C(102, 106, 'death', 'card', year=1911, main='就义', sub='二十五岁', art=art_l_death),
    C(106, 112, 'night', 'card', year=1911, main='黄花岗', sub='七十二烈士', art=art_l_bury),
    # ---- 第四回 意映
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'night', 'card', year=1911, main='遗书到家', sub='门缝', art=art_l_letter),
    C(118, 122, 'life', 'card', year=1911, main='故居易主', sub='冰心家', art=art_l_house),
    C(122, 126, 'war', 'card', year=1911, main='武昌起义', sub='半年后', art=art_l_wuchang),
    C(126, 130, 'empire', 'card', year=1912, main='民国', sub='清帝退位', art=art_l_minguo),
    C(130, 134, 'death', 'card', year=1913, main='意映病逝', sub='悲痛成疾', art=art_l_yiying),
    C(134, 140, 'works', 'card', year=1921, main='烈士墓', sub='黄花岗', note='年份约略', art=art_l_huanghua),
    C(140, 144, 'life', 'card', year=1921, main='凭吊', sub='年年黄花', art=art_l_visit),
    # ---- 第五回 卿卿
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'night', 'card', year=1921, main='与妻书', sub='广为传诵', note='年份约略', art=art_l_spread),
    C(150, 154, 'court', 'card', year=1990, main='入选课本', sub='中学语文', note='年份约略', art=art_l_textbook),
    C(154, 158, 'life', 'card', year=2011, main='吾至爱汝', sub='勇于就死', art=art_l_q1),
    C(158, 162, 'empire', 'card', year=2011, main='为天下人', sub='爱其所爱', art=art_l_q2),
    C(162, 166, 'fate', 'card', year=2011, main='纸短情长', sub='百年', art=art_l_q3),
    C(166, 170, 'end', 'card', year=2011, main='意映卿卿', sub='如晤', art=art_l_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='玖拾贰', col=YIYING, acc=HUANGHUA, born=1887, died=1911, age0=1886,
    born_lab='1887年', died_lab='1911年', years_txt='公元1887 — 1911',
    hook_q='他有爱妻 有未出世的孩子 · 为什么偏要去赴死？',
    name_line='林觉民 · 字意洞', name='林觉民', seal='意洞', title_art=art_l_title,
    q1='革命烈士？', q2='痴情丈夫？',
    end_art=art_l_legacy, end_big='与妻书', end_seal='意洞',
    end_l1='他比谁都爱自己的家', end_l2='所以想让天下人都有家',
    end_brush='爱其所爱', end_ask='读与妻书时 哪一句让你最难受？评论区聊聊', next='敬请期待'),
    scenes=dict(chapter=scene_chapter, yuqishu=scene_yuqishu))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
