"""千古人物志 · 第陆拾柒集 · 欧阳修 (1007–1072)
Look: 亭青 + 秋黄, 荻草 corner borders, a 六一 chapter card: the six things of 六一居士 appear one by one —
a stack of books, bronze inscriptions, a qin, a go board, then a wine jar and the old man himself.
Set pieces: 6-beat 画荻教子, custom 8-beat scene 'zuiweng' (醉翁亭记), 6-beat 与高司谏书, 6-beat 知贡举, 6-beat 秋声赋.
Ages are counted in 虚岁 (age0 = born - 1) so he dies 年六十六.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_wangwei as Ww         # engine + helpers (previous episode)
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
from render_quyuan import river
from render_simayi import emperor, goboard
from render_wangwei import qin

F.RIPPLE = False
TINGQING = (70, 112, 104)           # 亭青
QIUHUANG = (196, 150, 62)           # 秋黄
S.LAYERS.append(('tingqing', TINGQING, 0.9, 1.0))
S.LAYERS.append(('qiuhuang', QIUHUANG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='醉', life='荻', court='宋', night='秋', war='谏', empire='文', works='文', fate='贬', death='忠', end='翁')
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
G.THEMES['empire']['sun'] = (QIUHUANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (QIUHUANG, 180, (W * 0.5, 720))
G.base_bg.cache_clear()

REEDS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(REEDS)
for _x in list(range(80, 260, 18)) + list(range(830, 1010, 18)):     # 荻 reeds at the margins
    _h = 90 + (_x * 17) % 60
    _d.line((_x, 1480, _x + 10, 1480 - _h), fill=(110, 100, 70, 60), width=3)
    _d.ellipse((_x + 4, 1480 - _h - 22, _x + 18, 1480 - _h + 4), fill=(200, 180, 140, 70))
for _k in range(3):
    _d.line([(260 + i * 28, 1478 + _k * 12 + 4 * math.sin(i * 0.5 + _k)) for i in range(21)], fill=TINGQING + (40,), width=2)
MTN_COL = {'night': (30, 32, 36), 'death': (62, 60, 58), 'war': (110, 64, 52), 'fate': (92, 100, 94)}
def draw_background(t, theme):
    """滁州琅琊: rolling hills, reeds at the margins and a stream."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 190, 182), (156, 166, 154), MTN_COL.get(theme, (106, 126, 112))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(REEDS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """荻草: a reed stalk drawn like a brush stroke in each corner (画荻教子)."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=TINGQING + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=TINGQING + (220,), width=3)
        d.line((x + sx * 24, y + sy * 110, x + sx * 70, y + sy * 20), fill=(110, 96, 64, 230), width=4)
        d.ellipse((x + sx * 70 - 10, y + sy * 20 - 18, x + sx * 70 + 10, y + sy * 20 + 6), fill=QIUHUANG + (230,))
        d.line((x + sx * 40, y + sy * 80, x + sx * 90, y + sy * 70), fill=(110, 96, 64, 200), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def ouyang(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """欧阳修: Song official — 展脚幞头 with long side wings, thin beard; whitening in age (自号醉翁 at forty)."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.07 * h, y - 1.06 * h, x + 0.07 * h, y - 0.94 * h), fill=255)
        d.line((x - 0.07 * h, y - 0.99 * h, x - 0.3 * h, y - 0.99 * h), fill=255, width=max(2, int(0.014 * h)))
        d.line((x + 0.07 * h, y - 0.99 * h, x + 0.3 * h, y - 0.99 * h), fill=255, width=max(2, int(0.014 * h)))
        d.polygon([(x + dir * 0.03 * h, y - 0.84 * h), (x + dir * 0.08 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.68 * h)], fill=255)
        A.d['tingqing'].rectangle((x - 0.08 * h, y - 0.56 * h, x + 0.08 * h, y - 0.52 * h), fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.03 * h, y - 0.82 * h), (x + dir * 0.08 * h, y - 0.82 * h), (x + dir * 0.05 * h, y - 0.7 * h)], fill=255)
    return hand

def mother(A, x, y, h, dir=-1, **kw):
    kw.setdefault('arm', 40)
    return person(A, x, y, h, dir=dir, robe=True, hat='knot', female=True, layer=kw.pop('layer', 'ink'), **kw)

def pavilion(A, cx, base, w, layer='tingqing'):
    for sx in (-1, 1):
        A.d['ink'].line((cx + sx * 0.35 * w, base, cx + sx * 0.35 * w, base - 0.6 * w), fill=255, width=max(4, int(0.03 * w)))
    A.d[layer].polygon([(cx - 0.6 * w, base - 0.6 * w), (cx + 0.6 * w, base - 0.6 * w), (cx + 0.2 * w, base - 0.95 * w), (cx - 0.2 * w, base - 0.95 * w)], fill=255)
    A.d['ink'].polygon([(cx - 0.65 * w, base - 0.6 * w), (cx - 0.5 * w, base - 0.68 * w), (cx - 0.45 * w, base - 0.6 * w)], fill=255)
    A.d['ink'].polygon([(cx + 0.65 * w, base - 0.6 * w), (cx + 0.5 * w, base - 0.68 * w), (cx + 0.45 * w, base - 0.6 * w)], fill=255)
    A.d['ink'].line((cx, base - 0.95 * w, cx, base - 1.08 * w), fill=255, width=max(3, int(0.02 * w)))
    A.d['mid'].rectangle((cx - 0.5 * w, base - 0.04 * w, cx + 0.5 * w, base), fill=230)

def jar(A, x, base, s, layer='qiuhuang'):
    A.d[layer].ellipse((x - 0.5 * s, base - s, x + 0.5 * s, base), fill=255)
    A.d['ink'].rectangle((x - 0.18 * s, base - 1.15 * s, x + 0.18 * s, base - 0.9 * s), fill=255)

def bronze(A, x, base, s):
    A.d['tingqing'].polygon([(x - 0.6 * s, base - s), (x + 0.6 * s, base - s), (x + 0.45 * s, base), (x - 0.45 * s, base)], fill=255)
    A.d['ink'].line((x - 0.45 * s, base - 0.6 * s, x + 0.45 * s, base - 0.6 * s), fill=180, width=3)
    for sx in (-1, 1):
        A.d['tingqing'].arc((x + sx * 0.5 * s - 0.2 * s, base - 1.2 * s, x + sx * 0.5 * s + 0.2 * s, base - 0.8 * s), 180, 360, fill=255, width=6)

def leaves(A, t, n=24, layer='qiuhuang', y0=640, y1=1420, speed=0.3):
    for k in range(n):
        q = (t * speed + k / n) % 1
        x = 80 + (k * 47) % 920 + 40 * math.sin(t * 2 + k)
        A.d[layer].ellipse((x - 9, lerp(y0, y1, q) - 5, x + 9, lerp(y0, y1, q) + 5), fill=220)

# ================================================================ chapter card
STAGES = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 6)}
def six_things(A, k, t):
    base = 1200
    if k >= 1:
        for i in range(4):
            bundle(A, 230 + (i % 2) * 70, base - (i // 2) * 44, 60, layer='qiuhuang')
    if k >= 2:
        bronze(A, 420, base, 70)
    if k >= 3:
        qin(A, 560, base - 30, 70)
    if k >= 4:
        goboard(A, 720, base - 50, 50, [(2, 2), (4, 5)], [(5, 3)])
    if k >= 5:
        jar(A, 840, base, 60)
    if k >= 6:
        ouyang(A, 940, base, 160, dir=-1, arm=60, old=1.0)

def art_six_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = STAGES.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    six_things(A, b if q > 0.5 else a, t)
    A.d['mid'].rectangle((140, 1200, 940, 1214), fill=180)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_six_chapter)
    ink_in(cv, text_img(no, SERIF, 56, TINGQING, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_o_hook_reed(A, cv, t, u):
    A.d['dune'].rectangle((200, GROUND - 50, 880, GROUND), fill=200)
    q = ease_out(u / (1.4 * P))
    A.d['ink'].line((300, GROUND - 26, 300 + 480 * q, GROUND - 26 + 6 * math.sin(q * 9)), fill=230, width=6)
    ground(A, GROUND)

def art_o_hook_pavilion(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 300), (x + 220, GROUND)], fill=150)
    pavilion(A, 540, GROUND, 300)
    ground(A, GROUND)

def art_o_hook_three(A, cv, t, u):
    ground(A, GROUND)
    n = min(3, int(u / (0.6 * P)) + 1)
    for i in range(n):
        person(A, 300 + i * 240, GROUND, 180, dir=1, robe=True, hat='knot', arm=40, layer='tingqing' if i == 0 else 'ink')

def art_o_hook_six(A, cv, t, u):
    six_things(A, min(6, int(u / (0.3 * P)) + 1), t)
    ground(A, 1214)

# ================================================================ 第一回 画荻
def art_o_birth(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='绵州', layer='mid', open_=1.0)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('生于绵州 · 父为推官', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('绵州', 56), 860, 1020, t, t - u + P, rot=6)

def art_o_orphan(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    mother(A, 300, GROUND, 190, dir=1, bow=30, arm=-8)
    person(A, 380, GROUND, 80, dir=1, robe=True, hat='knot', arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('四岁丧父 · 家贫', SERIF, 48, TINGQING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_o_reed(A, cv, t, u):
    """6-beat set piece: 画荻教子 — no money for paper or brushes; the mother writes characters in the sand with a reed stem; the boy copies."""
    ph = u / P
    A.d['dune'].rectangle((180, GROUND - 60, 900, GROUND), fill=210)
    for k in range(8):
        A.d['wash'].line((60 + k * 14, GROUND, 70 + k * 14, GROUND - 160), fill=200, width=3)
    mother(A, 300, GROUND, 190, dir=1, kneel=True, bow=30, arm=lerp(100, 140, 0.5 + 0.5 * math.sin(t * 4)))
    A.d['qiuhuang'].line((380, GROUND - 90, 450, GROUND - 30), fill=255, width=4)
    person(A, 760, GROUND, 100, dir=-1, robe=True, hat='knot', kneel=True, bow=25, arm=lerp(100, 140, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    chars = '人之初性本善'
    n = min(6, int(clamp(ph / 5) * 6) + 1)
    for i in range(n):
        paste(cv, text_img(chars[i], BRUSH, 44, (90, 72, 50)), 470 + (i % 3) * 70, GROUND - 40 + (i // 3) * 0 - 6, 1, 0.8)
    paste(cv, text_img('家贫 至以荻画地学书', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('画荻教子', SERIF, 50, ZHU, 'Black', bleed=False, spacing=10), W / 2, 835, 1, clamp((ph - 2) / 0.4))

def art_o_borrow(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='tingqing')
    ouyang(A, 300, GROUND, 140, dir=1, kneel=True, bow=20, arm=110)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    n = int(clamp(u / (2 * P)) * 10) + 1
    for i in range(n):
        A.d['wash'].rectangle((420 + (i % 5) * 34, GROUND - 100 - (i // 5) * 16, 450 + (i % 5) * 34, GROUND - 86 - (i // 5) * 16), fill=255)
    A.flush(cv)
    paste(cv, text_img('就闾里士人家借书 · 或因而抄录', SERIF, 44, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_o_hanyu(A, cv, t, u):
    A.d['mid'].rectangle((300, GROUND - 120, 780, GROUND), fill=180)
    for i in range(6):
        bundle(A, 360 + i * 70, GROUND - 120, 50, layer='mid')
    ouyang(A, 220, GROUND, 140, dir=1, arm=lerp(40, 150, ease_out((u - P) / 0.4)))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('于李家废书筐中 得韩愈文集六卷', SERIF, 44, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('昌黎文', 50), 860, 1020, t, t - u + P, rot=6)

def art_o_fail(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    n = min(2, int(u / (1.2 * P)) + 1)
    ouyang(A, lerp(540, 900, ease_out((u % (1.2 * P)) / P)), GROUND, 170, dir=1, ph=t * 3, bow=10, arm=-8)
    A.flush(cv)
    paste(cv, text_img(f'随州应举 · 第{cn_num(n)}次落第', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_o_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qiuhuang')
    ground(A, GROUND)
    ouyang(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('国子监第一 · 礼部省试第一 · 进士及第', SERIF, 40, TINGQING, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('进士', 56), 860, 1020, t, t - u + P, rot=6)

def art_o_luoyang(A, cv, t, u):
    for k in range(5):
        A.d['ink'].line((180 + k * 180, GROUND, 176 + k * 180, GROUND - 160), fill=255, width=6)
        A.d['pink'].ellipse((180 + k * 180 - 60, GROUND - 230, 180 + k * 180 + 60, GROUND - 140), fill=220)
    ground(A, GROUND)
    for i in range(3):
        person(A, 300 + i * 200, GROUND, 160, dir=1 if i % 2 else -1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + i)), layer='tingqing' if i == 1 else 'ink')
    A.flush(cv)
    paste(cv, text_img('西京推官 · 与梅尧臣 尹洙诗文唱和', SERIF, 44, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('洛阳', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第二回 不知人间有羞耻事
def art_o_fanzhongyan(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, lerp(540, 980, ease_out((u - P) / P)), GROUND, 190, dir=1, robe=True, hat='knot', ph=t * 3, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('范仲淹上百官图 · 被贬饶州', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_o_letter(A, cv, t, u):
    """6-beat set piece: 与高司谏书 — the remonstrance official 高若讷 says nothing and even slanders Fan; Ouyang writes in fury."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='tingqing')
    ouyang(A, 300, GROUND, 180, dir=1, kneel=True, bow=10, arm=lerp(80, 140, 0.5 + 0.5 * math.sin(t * 8)))
    scroll(A, 560, GROUND - 120, 260, 60, clamp(ph / 3), layer='wash')
    A.flush(cv)
    lab = '司谏高若讷 不救反诋' if ph < 2 else ('足下犹能以面目见士大夫' if ph < 4 else '不复知人间有羞耻事')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else TINGQING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('与高司谏书', 40), 860, 1440, t, t - u + 0.4, rot=6)

def art_o_yiling(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=6, speed=2)
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, 1240), (x, 1240 - 360), (x + 220, 1240)], fill=170)
    boat(A, lerp(860, 300, ease_out(u / (3 * P))), 1260, 110, t, sail=True)
    A.flush(cv)
    paste(cv, text_img('坐贬夷陵县令', SERIF, 48, TINGQING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('夷陵', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_o_cases(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    ouyang(A, 280, GROUND, 180, dir=1, kneel=True, bow=20, arm=90)
    for i in range(int(clamp(u / (2 * P)) * 8) + 1):
        bundle(A, 400 + i * 40, GROUND - 74, 34, layer='tingqing')
    A.flush(cv)
    paste(cv, text_img('取旧案反复观之 · 枉直乖错不可胜数', SERIF, 44, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    paste(cv, text_img('自尔遇事 不敢忽也', SERIF, 42, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - 2 * P) / 0.4))

def art_o_qingli(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qiuhuang')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 190, dir=-1, arm=lerp(20, 80, ease_out(u / 0.5)))
    for i in range(3):
        person(A, 220 + i * 110, GROUND, 170, dir=1, robe=True, hat='knot', kneel=True, bow=20, arm=100, layer='tingqing' if i == 1 else 'ink')
    A.flush(cv)
    paste(cv, text_img('庆历新政 · 召还知谏院', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('知谏院', 50), 860, 1020, t, t - u + P, rot=6)

def art_o_pengdang(A, cv, t, u):
    ground(A, GROUND)
    q = ease_out(u / (2 * P))
    for i in range(4):
        person(A, lerp(540, 220 + i * 50, q), GROUND, 150, dir=1, robe=True, hat='knot', arm=40, layer='tingqing')
        person(A, lerp(540, 860 - i * 50, q), GROUND, 150, dir=-1, robe=True, hat='knot', arm=40, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('君子以同道为朋 小人以同利为朋', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('朋党论', 54), 860, 1020, t, t - u + P, rot=6)

def art_o_slander(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for i in range(3):
        person(A, 700 + i * 80, GROUND, 160, dir=-1, robe=True, hat='knot', bow=15, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + i)), layer='ink')
    ouyang(A, 320, GROUND, 180, dir=1, arm=-8, bow=10)
    A.flush(cv)
    paste(cv, text_img('新政失败 · 政敌以家事诬陷', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '张甥案 查无实据 仍被贬', t, t - u + P)

# ================================================================ 第三回 醉翁
def art_o_chuzhou(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['tingqing'].polygon([(x - 220, GROUND), (x, GROUND - 380), (x + 220, GROUND)], fill=170)
    ground(A, GROUND)
    ouyang(A, lerp(-60, 400, ease_out(u / (2.5 * P))), GROUND, 180, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('贬知滁州 · 时年三十九', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('滁州', 56), 860, 1020, t, t - u + P, rot=6)

def art_o_kuan(A, cv, t, u):
    A.d['grass'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=150)
    ground(A, GROUND)
    for j in range(5):
        person(A, 200 + j * 170, GROUND - 40, 120, dir=1 if j % 2 else -1, robe=False, hat='knot', bow=30, arm=150, ph=t * 2 + j, layer='ink')
    A.flush(cv)
    paste(cv, text_img('宽简不扰 · 百姓安之', SERIF, 48, TINGQING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def scene_zuiweng(cv, t, c, k):
    """8-beat custom scene: 醉翁亭记 — the hills around Chuzhou; a spring; the pavilion on the slope; the feast of the townsfolk;
    the governor drunk among them, white-haired; at sunset the crowd leaves and the birds sing."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    for kk in range(4):
        x = 160 + kk * 260
        A.d['tingqing'].polygon([(x - 220, GROUND), (x, GROUND - 360 - 40 * (kk % 2)), (x + 220, GROUND)], fill=150 + 20 * (kk % 2))
    A.d['ocean'].line([(80, 1330), (300, 1300), (420, 1340)], fill=200, width=10)
    pavilion(A, 600, 1240, 240)
    if 2 <= ph < 6:
        for j in range(6):
            person(A, 300 + j * 100, GROUND, 110, dir=1 if j % 2 else -1, robe=j % 2 == 0, hat='knot', kneel=j % 3 == 0, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='mid')
        ouyang(A, 600, 1240, 130, dir=1, kneel=True, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 2)), old=0.8, bow=15 if ph > 4 else 0)
        jar(A, 660, 1240, 30)
    if ph >= 6:
        r = 80
        A.d['red'].ellipse((820 - r, 820 - r, 820 + r, 820 + r), fill=160)
        for j in range(4):
            crow(A, 300 + j * 120, 900 + 30 * math.sin(t * 2 + j), 18, t * 5 + j)
    ground(A, GROUND)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '醉翁亭记', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=67)
    fx.flush(cv)
    lines = ['环滁皆山也 · 蔚然而深秀者 琅琊也', '有亭翼然临于泉上者 醉翁亭也', '苍颜白发 颓然乎其间者 太守醉也', '醉翁之意不在酒 在乎山水之间也']
    kq = 0 if ph < 2 else 1 if ph < 4 else 2 if ph < 6 else 3
    paste(cv, text_img(lines[kq], SERIF, 40, ZHU if kq == 3 else TINGQING, 'Black', bleed=False, spacing=2), W / 2, 575, 1, 1)
    paste(cv, text_img('自号醉翁 · 时年四十', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4) / 0.4))

def art_o_fengle(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 300), (x + 220, GROUND)], fill=150)
    pavilion(A, 380, GROUND, 200, layer='qiuhuang')
    for j in range(3):
        person(A, 620 + j * 110, GROUND, 140, dir=-1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + j)), layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('又建丰乐亭 · 与民同乐', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('丰乐亭', 50), 860, 1020, t, t - u + P, rot=6)

def art_o_yingzhou(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    waves(A, 1190, t, rows=3, amp=3, speed=0.5)
    for k in range(6):
        A.d['grass'].ellipse((140 + k * 150 - 40, 1170, 140 + k * 150 + 40, 1200), fill=220)
    A.flush(cv)
    paste(cv, text_img('移知颍州 · 爱西湖之胜 约定终老于此', SERIF, 42, TINGQING, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('颍州西湖', 44), 860, 1020, t, t - u + P, rot=6)

def art_o_oil(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].ellipse((500, GROUND - 30, 580, GROUND), fill=255)
    A.d['gold'].ellipse((528, GROUND - 120, 552, GROUND - 96), outline=255, width=4)
    q = (t * 2) % 1
    A.d['qiuhuang'].line((540, GROUND - 260, 540, lerp(GROUND - 250, GROUND - 30, q)), fill=255, width=3)
    person(A, 620, GROUND, 170, dir=-1, robe=False, hat='knot', arm=170, layer='ink')
    person(A, 280, GROUND, 170, dir=1, robe=True, hat='knot', arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 3)), layer='tingqing')
    A.flush(cv)
    type_in(cv, text_img('无他 但手熟尔', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + P, 0.4)
    stamp(cv, seal('卖油翁', 50), 860, 1020, t, t - u + 0.4, rot=6)

def art_o_tangshu(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='tingqing')
    ouyang(A, 280, GROUND, 180, dir=1, kneel=True, bow=20, arm=90)
    sitter(A, 820, GROUND, 160, dir=-1, bow=20, layer='mid')
    n = int(clamp(u / (2 * P)) * 10) + 1
    for i in range(n):
        bundle(A, 380 + (i % 5) * 54, GROUND - 74 - (i // 5) * 38, 40, layer='qiuhuang')
    A.flush(cv)
    paste(cv, text_img('召回京师 · 与宋祁同修唐书', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 文坛盟主
def art_o_exam(A, cv, t, u):
    """6-beat set piece: 知贡举 — he presides over the examination; fails every essay in the showy 太学体; one plain, powerful paper stands out —
    he marks it second for fear it is his own student's; it was 苏轼."""
    ph = u / P
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    ouyang(A, 280, GROUND, 180, dir=1, kneel=True, bow=15, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 4)))
    n = int(clamp(ph / 3) * 8)
    for i in range(8):
        x = 380 + (i % 4) * 70; y = GROUND - 90 - (i // 4) * 30
        A.d['wash'].rectangle((x, y, x + 56, y + 22), fill=255)
        if i < n and i != 5:
            A.d['red'].line((x, y, x + 56, y + 22), fill=255, width=4)
    if ph > 3.5:
        A.d['qiuhuang'].rectangle((380 + 70, GROUND - 120, 380 + 70 + 56, GROUND - 98), fill=255)
    A.flush(cv)
    lab = '嘉祐二年 知贡举 · 痛抑险怪奇涩之文' if ph < 3.5 else '得一卷 以为曾巩所作 置第二 · 拆号乃苏轼'
    paste(cv, text_img(lab, SERIF, 40, ZHU if ph >= 3.5 else TINGQING, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    if ph > 4.5:
        paste(cv, text_img('老夫当避路 放他出一头地', SERIF, 42, INK, 'Black', bleed=False, spacing=2), W / 2, 835, 1, clamp((ph - 4.5) / 0.4))

def art_o_jiayou(A, cv, t, u):
    ground(A, GROUND)
    names = ['苏轼', '苏辙', '曾巩', '张载', '程颢']
    for i in range(5):
        person(A, 160 + i * 190, GROUND, 160, dir=1, robe=True, hat='knot', arm=40, layer='tingqing' if i < 3 else 'ink')
    A.flush(cv)
    for i, nm in enumerate(names):
        stamp(cv, seal(nm, 34, ZHU if i < 3 else INK), 160 + i * 190, 1060, t, t - u + i * 0.3 * P)
    paste(cv, text_img('嘉祐二年进士榜 · 千年龙虎榜', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_o_wudai(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='tingqing')
    ouyang(A, 300, GROUND, 180, dir=1, kneel=True, bow=20, arm=90, old=0.4)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    paste(cv, text_img('私撰新五代史 · 呜呼 以叹世事', SERIF, 44, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('五代史', 54), 860, 1020, t, t - u + P, rot=6)

def art_o_autumn(A, cv, t, u):
    """6-beat set piece: 秋声赋 — reading at night he hears a sound from the south-west; the boy looks out: stars and moon, no one there;
    the sound is in the trees; autumn."""
    ph = u / P
    r = 50
    A.d['wash'].ellipse((800 - r, 820 - r, 800 + r, 820 + r), fill=240)
    leaves(A, t, n=30, speed=0.4)
    for k in range(3):
        x = 200 + k * 140
        A.d['ink'].line((x, GROUND, x - 6, GROUND - 320), fill=255, width=10)
        A.d['qiuhuang'].ellipse((x - 70, GROUND - 400, x + 70, GROUND - 280), fill=int(lerp(220, 120, clamp(ph / 5))))
    A.d['mid'].rectangle((560, GROUND - 200, 920, GROUND), fill=150)
    ouyang(A, 700, GROUND, 160, dir=-1, kneel=True, arm=lerp(40, 120, clamp((ph - 0.6) / 0.4)), old=0.6)
    lamp(A, 820, GROUND, 30, t, glow=0.9)
    person(A, lerp(560, 420, clamp((ph - 1.5) / 1)), GROUND, 90, dir=-1, robe=True, hat='knot', arm=60, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    lab = '欧阳子方夜读书 闻有声自西南来者' if ph < 2.5 else ('童子曰 星月皎洁 声在树间' if ph < 4 else '噫嘻悲哉 此秋声也')
    paste(cv, text_img(lab, SERIF, 42, ZHU if ph >= 4 else TINGQING, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    stamp(cv, seal('秋声赋', 50), 260, 1440, t, t - u + 0.4, rot=-5)

def art_o_jigu(A, cv, t, u):
    ground(A, GROUND)
    for i in range(int(clamp(u / (2 * P)) * 6) + 1):
        bronze(A, 200 + i * 130, GROUND, 50)
    A.d['wash'].rectangle((300, 920, 780, 1100), fill=255)
    A.d['ink'].rectangle((300, 920, 780, 1100), outline=255, width=4)
    A.flush(cv)
    paste(cv, text_img('集古录 · 收金石遗文一千卷', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '中国现存最早的金石学著作', t, t - u + P)

def art_o_canzheng(A, cv, t, u):
    for k in range(3):
        A.d['qiuhuang'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    ouyang(A, 540, GROUND - 180, 190, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)), old=0.5)
    A.flush(cv)
    paste(cv, text_img('拜枢密副使 · 次年参知政事', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('参知政事', 44), 860, 1020, t, t - u + P, rot=6)

def art_o_puyi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for i in range(3):
        person(A, 160 + i * 90, GROUND, 160, dir=1, robe=True, hat='knot', arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 4 + i)), layer='ink')
    ouyang(A, 720, GROUND, 180, dir=-1, arm=lerp(40, 110, 0.5 + 0.5 * math.sin(t * 2)), old=0.6)
    A.flush(cv)
    paste(cv, text_img('濮议之争 · 台谏交章弹劾', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 六一居士
def art_o_libel(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 170, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    ouyang(A, 360, GROUND, 180, dir=1, kneel=True, bow=30, arm=-8, old=0.8)
    A.flush(cv)
    paste(cv, text_img('又遭诬告 · 虽辨明 坚请外任', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '蒋之奇诬告事 朝廷查无实据', t, t - u + P)

def art_o_qingmiao(A, cv, t, u):
    A.d['grass'].rectangle((60, GROUND - 60, W - 60, GROUND), fill=150)
    for k in range(10):
        A.d['grass'].line((140 + k * 84, GROUND - 60, 150 + k * 84, GROUND - 130), fill=255, width=4)
    ground(A, GROUND)
    ouyang(A, 300, GROUND - 60, 170, dir=1, arm=lerp(40, 140, ease_out(u / 0.5)), old=0.8)
    A.flush(cv)
    paste(cv, text_img('青苗法行 · 擅自停发 被责', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_o_liuyi(A, cv, t, u):
    """6-beat set piece: 六一居士 — one by one: ten thousand books, a thousand inscriptions, a qin, a go set, a jar of wine — and one old man among them."""
    ph = u / P
    k = min(6, int(ph / 0.8) + 1)
    six_things(A, k, t)
    ground(A, 1214)
    A.flush(cv)
    labels = ['藏书一万卷', '集古录一千卷', '琴一张', '棋一局', '酒一壶', '以吾一翁 老于此五物之间']
    paste(cv, text_img(labels[k - 1], SERIF, 48, ZHU if k == 6 else TINGQING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - (k - 1) * 0.8) / 0.3))
    if k == 6:
        paste(cv, text_img('是岂不为六一乎', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.4) / 0.4))

def art_o_retire(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    waves(A, 1190, t, rows=3, amp=3, speed=0.5)
    boat(A, 540, 1210, 140, t, sail=False)
    ouyang(A, 540, 1190, 110, dir=1, kneel=True, arm=-8, old=1.0)
    A.flush(cv)
    paste(cv, text_img('以太子少师致仕 · 归颍州西湖', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_o_sushi(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    waves(A, 1190, t, rows=2, amp=3, speed=0.5)
    ouyang(A, 400, 1180, 170, dir=1, arm=60, old=1.0)
    person(A, 640, 1180, 170, dir=-1, robe=True, hat='knot', kneel=True, bow=20, arm=90, layer='tingqing')
    A.flush(cv)
    paste(cv, text_img('苏轼兄弟来颍州探望恩师', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_o_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    ouyang(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于颍州 · 年六十六', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('文忠', 56), 260, 1020, t, t - u + P, rot=-5)

def art_o_eight(A, cv, t, u):
    ground(A, GROUND)
    names = ['韩愈', '柳宗元', '欧阳修', '苏洵', '苏轼', '苏辙', '王安石', '曾巩']
    for i in range(8):
        person(A, 110 + i * 122, GROUND, 130, dir=1, robe=True, hat='knot', arm=40, layer='tingqing' if i == 2 else 'ink')
    A.flush(cv)
    for i, nm in enumerate(names):
        stamp(cv, seal(nm, 26, ZHU if i == 2 else INK), 110 + i * 122, 1100, t, t - u + i * 0.2 * P)
    paste(cv, text_img('唐宋八大家 · 宋六家中五人出其门下', SERIF, 42, TINGQING, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_o_wenzong(A, cv, t, u):
    for k in range(3):
        A.d['tingqing'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    ouyang(A, 540, GROUND - 180, 190, dir=1, arm=60, old=0.8)
    A.flush(cv)
    paste(cv, text_img('一代文宗', SERIF, 54, ZHU, 'Black', bleed=False, spacing=12), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '宋史称其 天下翕然师尊之', t, t - u + P)

def art_o_pavilion2(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['tingqing'].polygon([(x - 220, GROUND), (x, GROUND - 360), (x + 220, GROUND)], fill=150)
    pavilion(A, 540, GROUND, 260)
    leaves(A, t, n=16, speed=0.25)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('醉翁亭仍在琅琊山中', SERIF, 46, TINGQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_o_legacy(A, cv, t, u):
    pavilion(A, 860, 1440, 100)

def art_o_title(A, cv, t, u):
    pavilion(A, 820, 1460, 260)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    ouyang(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '画荻'), 48: ('第二回', '直言'), 80: ('第三回', '醉翁'),
            112: ('第四回', '文坛盟主'), 144: ('第五回', '六一居士')}

CARDS = [
    C(0, 2, 'life', 'num', num='一根芦苇', line='教出一代文宗', art=art_o_hook_reed),
    C(2, 4, 'empire', 'num', num='一座亭子', line='醉翁之意不在酒', art=art_o_hook_pavilion),
    C(4, 6, 'works', 'num', num='一场考试', line='选出苏轼苏辙曾巩', art=art_o_hook_three),
    C(6, 8, 'end', 'num', num='六个一', line='一个老翁', art=art_o_hook_six),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 画荻
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1007, main='生于绵州', sub='推官之子', art=art_o_birth),
    C(22, 26, 'death', 'card', year=1010, main='四岁丧父', sub='孤儿寡母', art=art_o_orphan),
    C(26, 32, 'life', 'card', year=1011, main='画荻教子', sub='以荻为笔', art=art_o_reed),
    C(32, 36, 'works', 'card', year=1017, main='借书抄读', sub='手不释卷', art=art_o_borrow),
    C(36, 40, 'night', 'card', year=1019, main='得韩愈文', sub='一生的方向', art=art_o_hanyu),
    C(40, 44, 'fate', 'card', year=1023, main='两次落第', sub='随州应举', art=art_o_fail),
    C(44, 46, 'empire', 'card', year=1030, main='进士及第', sub='连中第一', art=art_o_jinshi),
    C(46, 48, 'court', 'card', year=1031, main='西京推官', sub='洛阳诗友', art=art_o_luoyang),
    # ---- 第二回 直言
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'death', 'card', year=1036, main='范仲淹被贬', sub='满朝噤声', art=art_o_fanzhongyan),
    C(54, 60, 'war', 'card', year=1036, main='与高司谏书', sub='骂得痛快', art=art_o_letter),
    C(60, 64, 'fate', 'card', year=1036, main='贬夷陵', sub='三峡小县', art=art_o_yiling),
    C(64, 68, 'works', 'card', year=1037, main='翻阅旧案', sub='从此不敢忽', art=art_o_cases),
    C(68, 72, 'court', 'card', year=1043, main='庆历新政', sub='知谏院', art=art_o_qingli),
    C(72, 76, 'empire', 'card', year=1044, main='朋党论', sub='君子之朋', art=art_o_pengdang),
    C(76, 80, 'night', 'card', year=1045, main='遭诬被贬', sub='新政失败', art=art_o_slander),
    # ---- 第三回 醉翁
    C(80, 82, 'end', 'chapter'),
    C(82, 86, 'fate', 'card', year=1045, main='知滁州', sub='贬谪', art=art_o_chuzhou),
    C(86, 90, 'life', 'card', year=1046, main='宽简', sub='不扰民', art=art_o_kuan),
    C(90, 98, 'end', 'zuiweng', year=1046),
    C(98, 102, 'works', 'card', year=1046, main='丰乐亭', sub='与民同乐', art=art_o_fengle),
    C(102, 106, 'life', 'card', year=1049, main='颍州西湖', sub='终老之约', art=art_o_yingzhou),
    C(106, 108, 'night', 'card', year=1050, main='卖油翁', sub='熟能生巧', note='作年不详', art=art_o_oil),
    C(108, 112, 'works', 'card', year=1054, main='修唐书', sub='召回京师', art=art_o_tangshu),
    # ---- 第四回 文坛盟主
    C(112, 114, 'works', 'chapter'),
    C(114, 120, 'court', 'card', year=1057, main='知贡举', sub='一张卷子', art=art_o_exam),
    C(120, 124, 'empire', 'card', year=1057, main='龙虎榜', sub='千年第一榜', art=art_o_jiayou),
    C(124, 128, 'works', 'card', year=1058, main='新五代史', sub='呜呼', art=art_o_wudai),
    C(128, 134, 'night', 'card', year=1059, main='秋声赋', sub='夜读', art=art_o_autumn),
    C(134, 138, 'life', 'card', year=1062, main='集古录', sub='金石之学', art=art_o_jigu),
    C(138, 142, 'empire', 'card', year=1063, main='参知政事', sub='位至副相', art=art_o_canzheng),
    C(142, 144, 'war', 'card', year=1066, main='濮议', sub='台谏围攻', art=art_o_puyi),
    # ---- 第五回 六一居士
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=1067, main='再遭诬告', sub='心灰意冷', art=art_o_libel),
    C(150, 154, 'fate', 'card', year=1069, main='青苗法', sub='与新法不合', art=art_o_qingmiao),
    C(154, 160, 'end', 'card', year=1070, main='六一居士', sub='五物一翁', art=art_o_liuyi),
    C(160, 162, 'life', 'card', year=1071, main='致仕', sub='归颍州', art=art_o_retire),
    C(162, 164, 'court', 'card', year=1071, main='师徒相见', sub='苏轼来访', art=art_o_sushi),
    C(164, 166, 'death', 'card', year=1072, main='欧阳修去世', sub='谥文忠', art=art_o_death),
    C(166, 168, 'works', 'card', year=1072, main='唐宋八大家', sub='门下五家', art=art_o_eight),
    C(168, 169, 'empire', 'card', year=1072, main='一代文宗', sub='天下师尊', art=art_o_wenzong),
    C(169, 170, 'end', 'card', year=1072, main='醉翁亭', sub='山水之间', art=art_o_pavilion2),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='陆拾柒', col=TINGQING, acc=QIUHUANG, born=1007, died=1072, age0=1006,
    born_lab='1007年', died_lab='1072年', years_txt='公元1007 — 1072',
    hook_q='他一生被贬三次 · 为什么还能笑着当醉翁？',
    name_line='欧阳修 · 字永叔', name='欧阳修', seal='醉翁', title_art=art_o_title,
    q1='一代文宗？', q2='得罪满朝？',
    end_art=art_o_legacy, end_big='醉翁之意', end_seal='醉翁',
    end_l1='母亲用一根芦苇教他写字', end_l2='他用一支笔撑起了一代文坛',
    end_brush='醉翁之意不在酒', end_ask='醉翁亭记你还会背吗？评论区聊聊', next='沈括'),
    scenes=dict(chapter=scene_chapter, zuiweng=scene_zuiweng))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
