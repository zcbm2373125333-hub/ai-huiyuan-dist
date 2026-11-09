"""千古人物志 · 第柒拾捌集 · 周瑜 (175–210)
Look: 江东青 + 火攻橙, 琴轸 corner borders (a qin tuning peg with a string), the 长江 and red cliffs behind.
Chapter card: 七弦琴 — each chapter more of the seven strings are strung and shimmer; in the last chapter one string snaps.
Set pieces: custom 8-beat scene 'huoshao' (赤壁火攻), 6-beat 结交孙策, 6-beat 曲有误 周郎顾, 6-beat 廷议拔刀斫案,
6-beat 曹操北还, 6-beat 南郡中箭.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_liubei as Lb          # engine + helpers (previous episode)
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
from render_sunwu import army, banner
from render_songtaizu import tent
from render_huatuo import caocao
from render_guanyu import liubei
from render_sunquan import sun, warship as wu_ship

F.RIPPLE = False
ZHOUQING = (46, 98, 118)            # 江东青
HUOGONG = (212, 100, 42)            # 火攻橙
S.LAYERS.append(('zhouqing', ZHOUQING, 0.9, 1.0))
S.LAYERS.append(('huogong', HUOGONG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='周', life='瑜', court='吴', night='琴', war='火', empire='督', works='曲', fate='谣', death='丘', end='郎')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (HUOGONG, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (ZHOUQING, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (HUOGONG, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(4):                 # the 长江
    _d.line([(40 + i * 30, 1452 + _k * 12 + 4 * math.sin(i * 0.5 + _k)) for i in range(35)], fill=ZHOUQING + (52 - _k * 10,), width=3)
for _x in (120, 960):               # red cliffs at the margins
    _d.polygon([(_x - 60, 1446), (_x - 50, 1340), (_x - 10, 1300), (_x + 40, 1330), (_x + 60, 1446)], fill=(170, 80, 60, 50))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (120, 60, 44), 'fate': (92, 98, 104)}
def draw_background(t, theme):
    """长江: soft hills, the river, red cliffs at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 194, 196), (150, 166, 172), MTN_COL.get(theme, (96, 118, 128))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """琴轸: a tuning peg with a taut string in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=ZHOUQING + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=ZHOUQING + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(110, 70, 40, 230))
        d.line((cx, cy, cx + sx * 60, cy + sy * 60), fill=HUOGONG + (230,), width=2)
        d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(240, 220, 180, 230))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def zhou(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, armour=False, fan=False, **kw):
    """周瑜: a young handsome commander — 纶巾 silk cap with ribbons, no beard, a green robe; armour at war; a feather fan in 苏轼's poem."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else ('none' if up else 'knot'), layer=layer, kneel=kneel, bow=bow, **kw)
    d = A.d[layer]
    if up and not armour:
        d.polygon([(x - 0.08 * h, y - 0.93 * h), (x + 0.08 * h, y - 0.93 * h), (x + 0.05 * h, y - 1.05 * h), (x - 0.05 * h, y - 1.05 * h)], fill=255)
        A.d['zhouqing'].line([(x - dir * 0.05 * h, y - 0.98 * h), (x - dir * 0.15 * h, y - 0.9 * h + 0.02 * h * math.sin(x)), (x - dir * 0.2 * h, y - 0.8 * h)], fill=255, width=max(2, int(0.016 * h)))
    if up:
        A.d['zhouqing'].polygon([(x - 0.11 * h, y - 0.78 * h), (x + 0.11 * h, y - 0.78 * h), (x + 0.14 * h, y - 0.1 * h), (x - 0.14 * h, y - 0.1 * h)], fill=150)
    if fan and hand:
        hx, hy = hand
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.25
            A.d['wash'].polygon([(hx, hy), (hx + 0.18 * h * math.cos(a - 0.1), hy + 0.18 * h * math.sin(a - 0.1)), (hx + 0.2 * h * math.cos(a), hy + 0.2 * h * math.sin(a)), (hx + 0.18 * h * math.cos(a + 0.1), hy + 0.18 * h * math.sin(a + 0.1))], fill=255)
    return hand

def guqin(A, cx, cy, s, strings, t, snap=-1, glow=1.0):
    """A seven-string qin seen from above: body, 徽 dots, `strings` strings strung; string `snap` broken."""
    A.d['huyang'].rounded_rectangle((cx - s, cy - 0.16 * s, cx + s, cy + 0.16 * s), radius=int(0.1 * s), fill=255)
    A.d['ink'].rounded_rectangle((cx - s, cy - 0.16 * s, cx + s, cy + 0.16 * s), radius=int(0.1 * s), outline=255, width=4)
    for k in range(13):
        x = cx - 0.6 * s + k * 0.1 * s
        A.d['fangtian'].ellipse((x - 4, cy - 0.13 * s - 4, x + 4, cy - 0.13 * s + 4), fill=255)
    for k in range(min(7, strings)):
        y = cy - 0.1 * s + k * 0.033 * s
        if k == snap:
            A.d['red'].line((cx - 0.92 * s, y, cx - 0.1 * s, y + 0.06 * s), fill=255, width=max(3, int(0.012 * s)))
            A.d['red'].line((cx + 0.92 * s, y, cx + 0.2 * s, y - 0.05 * s), fill=255, width=max(3, int(0.012 * s)))
        else:
            vib = 1.5 * math.sin(t * 30 + k) * glow
            A.d['fangtian'].line([(cx - 0.92 * s, y), (cx, y + vib), (cx + 0.92 * s, y)], fill=255, width=max(2, int(0.01 * s)))

def fire_ship(A, x, y, s, t, burn=1.0):
    A.d['ink'].polygon([(x - s, y - 0.2 * s), (x + s, y - 0.2 * s), (x + 0.8 * s, y + 0.1 * s), (x - 0.8 * s, y + 0.1 * s)], fill=255)
    A.d['dune'].polygon([(x - 0.6 * s, y - 0.2 * s), (x + 0.6 * s, y - 0.2 * s), (x + 0.4 * s, y - 0.6 * s), (x - 0.4 * s, y - 0.6 * s)], fill=230)
    if burn > 0:
        flames(A, x, y - 0.3 * s, 1.6 * s, 1.2 * s * burn, t, n=3, seed=int(x), smoke=True)

# ================================================================ chapter card
CH = {16: (0, 2), 48: (2, 4), 80: (4, 6), 112: (6, 7), 144: (7, 7)}
def art_qin_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (2, 4))
    q = ease_out(u / (1.2 * P))
    n = b if q > 0.5 else a
    guqin(A, 540, 1080, 330, n, t, snap=3 if (kb == 144 and q > 0.6) else -1)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_qin_chapter)
    ink_in(cv, text_img(no, SERIF, 56, ZHOUQING, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_y_hook_young(A, cv, t, u):
    ground(A, GROUND)
    zhou(A, 540, GROUND, 280, dir=1, arm=lerp(-8, 50, ease_out(u / 0.6)))

def art_y_hook_qin(A, cv, t, u):
    ground(A, GROUND)
    guqin(A, 540, 1120, 320, 7, t)

def art_y_hook_fire(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=150)
    waves(A, 1170, t, rows=2, amp=4)
    for k in range(4):
        fire_ship(A, 200 + k * 230, 1180, 70, t, burn=clamp(u / (1.2 * P)))

def art_y_hook_short(A, cv, t, u):
    ground(A, GROUND)
    guqin(A, 540, 1120, 320, 7, t, snap=3)

# ================================================================ 第一回 周郎
def art_y_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x - 60, GROUND - 200), (x + 60, GROUND - 200), (x + 220, GROUND)], fill=150)
    A.d['wash'].rectangle((360, GROUND - 200, 720, GROUND), fill=255)
    A.d['ink'].polygon([(330, GROUND - 200), (750, GROUND - 200), (540, GROUND - 280)], fill=255)
    A.d['red'].rectangle((510, GROUND - 120, 570, GROUND), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('庐江舒县 · 从祖父周景 周忠皆为太尉', SERIF, 44, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('舒县', 56), 860, 1020, t, t - u + P, rot=6)

def art_y_sunce(A, cv, t, u):
    """6-beat set piece: 结交孙策 — the same age, they become sworn friends; 周瑜 bows to 孙策's mother and gives the family his great house south of the road."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        zhou(A, 380, GROUND, 190, dir=1, arm=lerp(-8, 80, clamp(ph / 0.6)))
        person(A, 700, GROUND, 195, dir=-1, robe=False, hat='helmet', arm=lerp(-8, 80, clamp(ph / 0.6)), layer='jiangdong')
        lab = '与孙策同年 · 推结分好'
    elif ph < 4:
        person(A, 760, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, kneel=True, arm=-8, layer='mid')
        zhou(A, 440, GROUND, 170, dir=1, kneel=True, bow=30, arm=90)
        lab = '升堂拜母 · 有无通共'
    else:
        A.d['wash'].rectangle((500, GROUND - 260, 960, GROUND), fill=255)
        A.d['ink'].polygon([(470, GROUND - 260), (990, GROUND - 260), (730, GROUND - 340)], fill=255)
        zhou(A, 300, GROUND, 190, dir=1, arm=lerp(-8, 110, clamp((ph - 4) / 0.6)))
        lab = '让出道南大宅 与孙家同住'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '时年十六 孙坚举兵讨董卓 家眷寓居舒县', t, t - u + P)

def art_y_music(A, cv, t, u):
    """6-beat set piece: 曲有误 周郎顾 — even after three cups, if the musicians miss a note he turns his head."""
    ph = u / P
    ground(A, GROUND)
    for j in range(3):
        person(A, 600 + j * 120, GROUND, 140, dir=-1, robe=True, hat='knot', female=j == 1, kneel=True, arm=lerp(80, 110, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='mid')
    guqin(A, 720, GROUND - 40, 120, 7, t)
    turn = ph >= 3
    zhou(A, 300, GROUND, 160, dir=1 if turn else -1, kneel=True, arm=lerp(40, 60, 0.5 + 0.5 * math.sin(t)))
    A.d['qiuhuang'].ellipse((160, GROUND - 60, 190, GROUND - 30), fill=255)
    A.flush(cv)
    if ph < 1.5:
        lab, col = '少精意于音乐', ZHOUQING
    elif ph < 3:
        lab, col = '虽三爵之后 其有阙误 瑜必知之', ZHOUQING
    else:
        lab, col = '曲有误 周郎顾', ZHU
    paste(cv, text_img(lab, SERIF, 46 if ph >= 3 else 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '时人之谣 见三国志周瑜传', t, t - u + 3 * P)

def art_y_crossing(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    waves(A, 1190, t, rows=2, amp=4)
    for k in range(4):
        boat(A, lerp(-100, 800, ease_out(u / (3 * P))) - k * 150, 1200, 70, t)
    A.flush(cv)
    paste(cv, text_img('率兵迎孙策渡江 · 策大喜 吾得卿 谐也', SERIF, 44, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_juchao(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='居巢', layer='mid', open_=1.0)
    ground(A, GROUND)
    zhou(A, 540, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('袁术欲用为将 · 瑜观其终无所成 求为居巢长', SERIF, 42, ZHOUQING, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_y_zhoulang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='zhouqing')
    ground(A, GROUND)
    zhou(A, 540, GROUND, 210, dir=1, armour=True, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('建威中郎将 · 时年二十四 吴中皆呼周郎', SERIF, 44, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('周郎', 56), 860, 1020, t, t - u + P, rot=6)

def art_y_xiaoqiao(A, cv, t, u):
    ground(A, GROUND)
    person(A, 620, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, arm=-8, layer='pink')
    zhou(A, 440, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('攻皖 得乔公二女 · 孙策纳大乔 周瑜纳小乔', SERIF, 42, ZHOUQING, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 江东
def art_y_cedeath(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, robe=False, hat='helmet', layer='jiangdong')
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('孙策遇刺身亡 · 年仅二十六', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_fuzuo(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    sun(A, 760, GROUND, 190, dir=-1, arm=-8)
    zhou(A, 420, GROUND, 200, dir=1, bow=25, arm=90)
    for j in range(3):
        person(A, 120 + j * 70, GROUND, 150, dir=1, robe=True, hat='knot', arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('与张昭共辅孙权 · 独先尽敬 执臣节', SERIF, 44, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '时孙权年十九 诸将礼节尚简', t, t - u + P)

def art_y_zhizi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    sun(A, 720, GROUND, 190, dir=-1, kneel=True, arm=-8)
    zhou(A, 400, GROUND, 190, dir=1, kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    paste(cv, text_img('曹操令送质子 · 周瑜力劝不送', SERIF, 46, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '一有质 不得不与曹氏相首尾', t, t - u + P)

def art_y_chengpu(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mid')
    person(A, 760, GROUND, 180, dir=-1, robe=False, hat='helmet', kneel=True, arm=lerp(60, 110, ease_out(u / (2 * P))), layer='ink')
    A.d['wash'].polygon([(760, GROUND - 120), (800, GROUND - 120), (790, GROUND - 90)], fill=255)
    zhou(A, 320, GROUND, 160, dir=1, kneel=True, arm=100)
    A.d['qiuhuang'].ellipse((510, GROUND - 100, 570, GROUND - 74), fill=255)
    A.flush(cv)
    paste(cv, text_img('老将程普轻之 · 周瑜折节容下', SERIF, 46, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '程普叹 与周公瑾交 若饮醇醪 不觉自醉', t, t - u + P)

def art_y_jiangxia(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='江夏', layer='mid', open_=clamp((u - P) / P))
    A.d['ocean'].rectangle((60, GROUND - 30, W - 60, GROUND + 40), fill=140)
    ground(A, GROUND)
    for k in range(3):
        wu_ship(A, lerp(-100, 300, ease_out(u / (3 * P))) + k * 180, GROUND - 20, 50, t)
    A.flush(cv)
    paste(cv, text_img('随孙权讨江夏 · 破黄祖', SERIF, 46, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_jianggan(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 760, GROUND, 300, 220, layer='zhouqing', open_=1.0)
    for j in range(4):
        person(A, 120 + j * 90, GROUND, 140, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    person(A, 560, GROUND, 180, dir=1, robe=True, hat='knot', arm=-8, layer='ink')
    zhou(A, 700, GROUND, 200, dir=-1, arm=lerp(-8, 100, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('蒋干来说 · 周瑜引观营中军资', SERIF, 46, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '蒋干归 称其雅量高致 群英会盗书出自演义', t, t - u + P)

def art_y_tingyi(A, cv, t, u):
    """6-beat set piece: 廷议 — 曹操's letter: 八十万众 方与将军会猎于吴; most ministers urge surrender; 周瑜 and 鲁肃 argue for war;
    孙权 draws his sword and cuts the desk: whoever speaks of surrender again shall be like this desk."""
    ph = u / P
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    desk(A, 540, GROUND, 300, layer='zhouqing')
    if ph < 2:
        for j in range(4):
            person(A, 140 + j * 80, GROUND, 150, dir=1, robe=True, hat='knot', bow=20, arm=90, layer='mid')
        sun(A, 760, GROUND, 190, dir=-1, arm=-8)
        lab, col = '曹操来书 · 群臣多劝迎降', ZHOUQING
    elif ph < 4:
        zhou(A, 300, GROUND, 200, dir=1, arm=lerp(60, 130, 0.5 + 0.5 * math.sin(t * 3)))
        sun(A, 760, GROUND, 190, dir=-1, arm=-8)
        lab, col = '周瑜 鲁肃力主抗曹 · 请得精兵三万', ZHOUQING
    else:
        q = clamp((ph - 4) / 0.5)
        sun(A, 680, GROUND, 200, dir=-1, arm=lerp(-8, 150, q), sword=lerp(40, 160, q))
        A.d['dune'].line((420, GROUND - 74, 660, GROUND - 74 + 30 * q), fill=255, width=8)
        lab, col = '拔刀斫案 · 敢言降者 与此案同', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '周瑜料曹军不过十五六万 且已疲惫', t, t - u + 2 * P)

# ================================================================ 第三回 赤壁
def art_y_dudu(A, cv, t, u):
    ground(A, GROUND)
    banner(A, 900, GROUND, 360, t, layer='zhouqing')
    for j in range(7):
        person(A, 120 + j * 100, GROUND, 120, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    zhou(A, 760, GROUND, 210, dir=-1, armour=True, arm=lerp(-8, 120, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('以周瑜 程普为左右督 · 领兵三万', SERIF, 46, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('都督', 56), 860, 1020, t, t - u + P, rot=6)

def art_y_meet(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    waves(A, 1190, t, rows=2, amp=4)
    for k in range(3):
        wu_ship(A, lerp(-100, 300, ease_out(u / (3 * P))) + k * 170, 1200, 55, t)
    boat(A, lerp(1100, 760, ease_out(u / (3 * P))), 1210, 70, t)
    A.flush(cv)
    paste(cv, text_img('与刘备军会合 · 逆江而上 遇曹军于赤壁', SERIF, 44, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_huoshao(cv, t, c, k):
    """8-beat custom scene: 赤壁火攻 — 黄盖: their ships are joined bow to stern, they can be burned; ten boats of dry reeds and oil
    sail over under a false surrender; the wind is strong; fire races across the 曹 fleet onto the shore camps."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['ocean'].rectangle((0, 1120, W, GROUND + 40), fill=160)
    waves(A, 1130, t, rows=3, amp=5)
    burn = clamp((ph - 4) / 2.5)
    for k in range(5):
        x = 600 + k * 110
        A.d['ink'].polygon([(x - 60, 1140), (x + 60, 1140), (x + 50, 1170), (x - 50, 1170)], fill=255)
        A.d['ink'].line((x, 1140, x, 1020), fill=255, width=4)
        if burn > k / 6:
            flames(A, x, 1120, 140, 220 * burn, t, n=2, seed=k + 9, smoke=True)
    A.d['ink'].line((540, 1150, 1080, 1150), fill=200, width=4)
    if ph < 2:
        zhou(A, 200, 1120, 170, dir=1, armour=True, arm=60)
        person(A, 340, 1120, 160, dir=-1, robe=False, hat='helmet', arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
        lab, col = '黄盖献策 · 操军方连船舰 首尾相接 可烧而走也', ZHOUQING
    else:
        q = clamp((ph - 2) / 2.5)
        for k in range(4):
            fire_ship(A, lerp(-80, 520, q) + k * 60 - 120, 1150 - 10 * (k % 2), 50, t, burn=clamp((ph - 3.5) / 0.8))
        lab, col = ('诈降 · 蒙冲斗舰载薪草灌油' if ph < 4 else '时风盛猛 · 悉延烧岸上营落'), ZHU if ph >= 4 else ZHOUQING
    for i in range(20):
        qq = (t * 1.2 + i / 20) % 1
        A.d['wash'].line((80 + qq * 900, 700 + (i * 37) % 300, 80 + qq * 900 + 40, 700 + (i * 37) % 300), fill=int(100 * clamp(ph - 2)), width=2)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '赤壁火攻', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=78)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 40 if ph < 2 else 44, col, 'Black', bleed=False, spacing=2), W / 2, 575, 1, 1)
    note_in(cv, '火攻之策出自黄盖 主帅为周瑜', t, s0 + 2 * P)

def art_y_beihuan(A, cv, t, u):
    """6-beat set piece: 曹操北还 — fleeing through the marshes of 华容, the road deep in mud; 曹操 later writes: 我烧船自退 横使周瑜虚获此名."""
    ph = u / P
    ground(A, GROUND)
    A.d['dune'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=150)
    for i in range(12):
        A.d['grass'].line((100 + i * 80, GROUND - 40, 110 + i * 80, GROUND - 120), fill=200, width=4)
    for j in range(5):
        person(A, lerp(1000, 100, ((t * 0.06 + j / 5) % 1)), GROUND - 20, 110, dir=-1, robe=False, hat='helmet', bow=30, arm=-8, ph=t * 2 + j, layer='ink')
    caocao(A, lerp(700, 400, clamp(ph / 4)), GROUND - 20, 170, dir=-1, ph=t * 2, arm=-8)
    A.flush(cv)
    lab, col = ('曹军败走华容 · 道路泥泞' if ph < 3 else '孤烧船自退 横使周瑜虚获此名'), ZHU if ph >= 3 else ZHOUQING
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '曹操事后致孙权书中语', t, t - u + 3 * P)

def art_y_dongfeng(A, cv, t, u):
    A.d['wash'].rectangle((300, 980, 780, GROUND - 60), fill=150)
    for k in range(3):
        A.d['mid'].rectangle((360 + k * 40, GROUND - 60 - (k + 1) * 60, 720 - k * 40, GROUND - 60 - k * 60), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('草船借箭 借东风', SERIF, 48, ZHOUQING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '均为演义情节 正史无载', t, t - u + 0.4)

def art_y_nanjun(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='江陵', layer='mid')
    A.d['ocean'].rectangle((60, GROUND - 30, W - 60, GROUND + 40), fill=140)
    ground(A, GROUND)
    for k in range(3):
        wu_ship(A, 160 + k * 200, GROUND - 20, 50, t)
    A.flush(cv)
    paste(cv, text_img('乘胜进军南郡 · 与曹仁隔江对峙', SERIF, 46, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 南郡
def art_y_arrow(A, cv, t, u):
    """6-beat set piece: 南郡中箭 — riding the lines, he is hit by a stray arrow in the right side; 曹仁 hears he is bedridden and attacks;
    周瑜 rises, tours the camp and rallies the men; 曹仁 withdraws."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        rider(A, 540, GROUND, 150, dir=1, ph=t * 6, layer='zhouqing')
        if ph > 1:
            ax = lerp(1000, 560, clamp((ph - 1) / 0.4))
            A.d['ink'].line((ax, GROUND - 160, ax + 60, GROUND - 170), fill=255, width=4)
        lab, col = '亲跨马掠阵 · 流矢中右胁', ZHU
    elif ph < 3.5:
        tent(A, 540, GROUND, 360, 260, layer='mid', open_=1.0)
        zhou(A, 540, GROUND, 160, dir=1, kneel=True, bow=30, arm=-8)
        lab, col = '疮甚 卧床不起 · 曹仁闻之 勒兵来攻', ZHOUQING
    else:
        for j in range(6):
            person(A, 120 + j * 90, GROUND, 130, dir=1, robe=False, hat='helmet', spear=True, arm=lerp(40, 140, clamp((ph - 4) / 0.6)), layer='mid')
        zhou(A, 760, GROUND, 210, dir=-1, armour=True, arm=lerp(-8, 140, clamp((ph - 3.5) / 0.6)))
        lab, col = '周瑜强起 巡营激励 · 曹仁退走', ZHOUQING
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('南郡', 56), 860, 1020, t, t - u + 4 * P, rot=6)

def art_y_taishou(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='zhouqing')
    ground(A, GROUND)
    zhou(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('拜偏将军 领南郡太守', SERIF, 48, ZHOUQING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_y_liubei(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='zhouqing')
    zhou(A, 280, GROUND, 170, dir=1, kneel=True, arm=100)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    paste(cv, text_img('上疏孙权 · 宜徙刘备置吴 盛为筑宫室', SERIF, 44, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '刘备枭雄 关张熊虎之将 必非久屈为人用者', t, t - u + P)

def art_y_shu(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((300, 900, 780, 1300), fill=200)
    A.d['zhouqing'].line([(340, 1100), (440, 1060), (540, 1100), (640, 1040), (740, 1100)], fill=255, width=6)
    q = ease_out(u / (2.5 * P))
    A.d['red'].line([(700, 1120), (lerp(700, 380, q), lerp(1120, 1000, q))], fill=255, width=6)
    A.flush(cv)
    paste(cv, text_img('请与孙瑜进取蜀地 · 结援马超 再图襄阳', SERIF, 44, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_y_baqiu(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=3)
    wu_ship(A, lerp(900, 540, ease_out(u / (3 * P))), 1220, 80, t)
    A.flush(cv)
    paste(cv, text_img('还江陵治行装 · 行至巴丘 病重', SERIF, 46, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('巴丘', 56), 860, 1020, t, t - u + P, rot=6)

def art_y_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    zhou(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于巴丘 · 年三十六', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 千古
def art_y_mourn(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    sun(A, 540, GROUND, 200, dir=1, bow=30, arm=-8, layer='wash')
    A.flush(cv)
    paste(cv, text_img('公瑾有王佐之资 今忽短命 孤何赖哉', SERIF, 44, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '孙权素服举哀 感动左右', t, t - u + P)

def art_y_emperor(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qiuhuang')
    ground(A, GROUND)
    sun(A, 540, GROUND, 210, dir=1, crown=True, arm=60, old=0.6)
    A.flush(cv)
    paste(cv, text_img('孤非周公瑾 不帝矣', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '孙权称帝之时 对公卿所言', t, t - u + P)

def art_y_sushi(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=140)
    waves(A, 1210, t, rows=2, amp=4)
    A.d['red'].polygon([(60, 1200), (120, 980), (260, 900), (360, 1200)], fill=160)
    boat(A, 640, 1220, 80, t, sail=False)
    A.flush(cv)
    paste(cv, text_img('遥想公瑾当年 小乔初嫁了 雄姿英发', SERIF, 44, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '苏轼念奴娇 赤壁怀古', t, t - u + P)

def art_y_novel(A, cv, t, u):
    ground(A, GROUND)
    A.d['red'].rectangle((200, 960, 880, 1000), fill=200)
    A.d['ink'].rectangle((200, 1000, 220, GROUND), fill=255); A.d['ink'].rectangle((860, 1000, 880, GROUND), fill=255)
    A.d['dune'].rectangle((200, GROUND - 60, 880, GROUND), fill=230)
    zhou(A, 540, GROUND - 60, 200, dir=1, bow=lerp(0, 40, 0.5 + 0.5 * math.sin(t * 2)), arm=150)
    A.flush(cv)
    paste(cv, text_img('演义中 他被诸葛亮三气而死', SERIF, 46, ZHOUQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_jisheng(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 460, 260, ease_out(u / (1.0 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('既生瑜 何生亮', SERIF, 56, DIM, 'Black', bleed=False, spacing=10), W / 2, 1100, 1, clamp((u - 0.6 * P) / 0.4))
    paste(cv, text_img('正史并无此语', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp((u - 1.5 * P) / 0.4))

def art_y_verdict(A, cv, t, u):
    ground(A, GROUND)
    zhou(A, 540, GROUND, 250, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)), fan=True)
    A.flush(cv)
    paste(cv, text_img('性度恢廓 大率为得人', SERIF, 48, ZHOUQING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '三国志之评', t, t - u + P)

def art_y_end(A, cv, t, u):
    ground(A, GROUND)
    guqin(A, 540, 1140, 320, 7, t, snap=3, glow=0.3)
    A.flush(cv)
    paste(cv, text_img('曲有误 周郎顾', SERIF, 50, ZHOUQING, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))

def art_y_legacy(A, cv, t, u):
    guqin(A, 860, 1400, 80, 7, t)

def art_y_title(A, cv, t, u):
    guqin(A, 820, 1400, 160, 7, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    zhou(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '周郎'), 48: ('第二回', '江东'), 80: ('第三回', '赤壁'),
            112: ('第四回', '南郡'), 144: ('第五回', '千古')}

CARDS = [
    C(0, 2, 'life', 'num', num='二十四岁', line='吴中皆呼周郎', art=art_y_hook_young),
    C(2, 4, 'works', 'num', num='一首曲子', line='错一个音他都回头', art=art_y_hook_qin),
    C(4, 6, 'war', 'num', num='三万精兵', line='一把火烧退曹军', art=art_y_hook_fire),
    C(6, 8, 'death', 'num', num='三十六岁', line='死在出征路上', art=art_y_hook_short),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 周郎
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=175, main='生于舒县', sub='世家子弟', art=art_y_birth),
    C(22, 28, 'court', 'card', year=190, main='结交孙策', sub='升堂拜母', art=art_y_sunce),
    C(28, 34, 'works', 'card', year=192, main='周郎顾', sub='精于音律', note='年份约略', art=art_y_music),
    C(34, 38, 'war', 'card', year=195, main='助策渡江', sub='吾得卿 谐也', art=art_y_crossing),
    C(38, 42, 'fate', 'card', year=197, main='辞别袁术', sub='居巢长', art=art_y_juchao),
    C(42, 46, 'empire', 'card', year=198, main='周郎', sub='二十四岁', art=art_y_zhoulang),
    C(46, 48, 'life', 'card', year=199, main='娶小乔', sub='乔公之女', art=art_y_xiaoqiao),
    # ---- 第二回 江东
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'death', 'card', year=200, main='孙策遇刺', sub='临终托付', art=art_y_cedeath),
    C(54, 58, 'court', 'card', year=200, main='辅佐孙权', sub='执臣节', art=art_y_fuzuo),
    C(58, 62, 'night', 'card', year=202, main='拒送质子', sub='不受制于人', art=art_y_zhizi),
    C(62, 66, 'life', 'card', year=203, main='若饮醇醪', sub='程普折服', note='年份约略', art=art_y_chengpu),
    C(66, 70, 'war', 'card', year=208, main='破江夏', sub='黄祖', art=art_y_jiangxia),
    C(70, 74, 'fate', 'card', year=208, main='蒋干来说', sub='雅量高致', art=art_y_jianggan),
    C(74, 80, 'court', 'card', year=208, main='战与降', sub='拔刀斫案', art=art_y_tingyi),
    # ---- 第三回 赤壁
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'empire', 'card', year=208, main='左右都督', sub='精兵三万', art=art_y_dudu),
    C(86, 90, 'works', 'card', year=208, main='孙刘会师', sub='遇于赤壁', art=art_y_meet),
    C(90, 98, 'war', 'huoshao', year=208),
    C(98, 104, 'fate', 'card', year=208, main='曹操北还', sub='败走华容', art=art_y_beihuan),
    C(104, 108, 'night', 'card', year=208, main='借东风', sub='演义情节', art=art_y_dongfeng),
    C(108, 112, 'court', 'card', year=209, main='进军南郡', sub='曹仁', art=art_y_nanjun),
    # ---- 第四回 南郡
    C(112, 114, 'empire', 'chapter'),
    C(114, 120, 'death', 'card', year=209, main='流矢中胁', sub='强起激励', art=art_y_arrow),
    C(120, 124, 'empire', 'card', year=209, main='南郡太守', sub='偏将军', art=art_y_taishou),
    C(124, 128, 'night', 'card', year=209, main='徙备置吴', sub='上疏之策', art=art_y_liubei),
    C(128, 132, 'court', 'card', year=210, main='取蜀之策', sub='再图襄阳', art=art_y_shu),
    C(132, 138, 'fate', 'card', year=210, main='病重巴丘', sub='壮志未酬', art=art_y_baqiu),
    C(138, 144, 'death', 'card', year=210, main='周瑜去世', sub='年三十六', art=art_y_death),
    # ---- 第五回 千古
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'fate', 'card', year=210, main='孙权素服', sub='王佐之资', art=art_y_mourn),
    C(150, 154, 'empire', 'card', year=229, main='孙权称帝', sub='孤非公瑾', art=art_y_emperor),
    C(154, 158, 'works', 'card', year=1082, main='赤壁怀古', sub='苏轼', art=art_y_sushi),
    C(158, 162, 'night', 'card', year=1522, main='三国演义', sub='三气周瑜', art=art_y_novel),
    C(162, 166, 'fate', 'card', year=1522, main='既生瑜', sub='何生亮', art=art_y_jisheng),
    C(166, 168, 'court', 'card', year=1522, main='性度恢廓', sub='正史之评', art=art_y_verdict),
    C(168, 170, 'end', 'card', year=1522, main='周郎顾', sub='千古', art=art_y_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='柒拾捌', col=ZHOUQING, acc=HUOGONG, born=175, died=210, age0=174,
    born_lab='175年', died_lab='210年', years_txt='公元175 — 210',
    hook_q='他是赤壁的主帅 · 为什么被演义写成小心眼？',
    name_line='周瑜 · 字公瑾', name='周瑜', seal='周郎', title_art=art_y_title,
    q1='雅量高致？', q2='气量狭小？',
    end_art=art_y_legacy, end_big='雄姿英发', end_seal='周郎',
    end_l1='历史上他雅量高致', end_l2='演义却让他被活活气死',
    end_brush='曲有误', end_ask='你心中的周瑜 是正史还是演义？评论区聊聊', next='赵云'),
    scenes=dict(chapter=scene_chapter, huoshao=scene_huoshao))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
