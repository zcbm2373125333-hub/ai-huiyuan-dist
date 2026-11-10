"""千古人物志 · 第捌拾捌集 · 俞大猷 (1503–1579)
Look: 晋江赭红 + 齐眉棍黄, 棍头 corner borders (a staff end bound with iron), the 泉州 coast and beacon towers behind.
Chapter card: 海防烽火 — a coastline with five beacon towers; one more tower is lit each chapter; in the last chapter the beacons go out:
the coast is quiet.
Set pieces: custom 8-beat scene 'shaolin' (少林传棍), 6-beat 学剑, 6-beat 王江泾, 6-beat 岑港入狱, 6-beat 车营, 6-beat 平海卫,
6-beat 平曾一本.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_songci as Sc          # engine + helpers (previous episode)
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
from render_qijiguang import ming_soldier, wokou, qi, wo_ship, watchtower
from render_xuanzang import xz
from render_jianzhen import temple

F.RIPPLE = False
JINJIANG = (150, 72, 52)            # 晋江赭红
GUNHUANG = (196, 160, 90)           # 齐眉棍黄
S.LAYERS.append(('jinjiang', JINJIANG, 0.9, 1.0))
S.LAYERS.append(('gunhuang', GUNHUANG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='俞', life='晋', court='明', night='棍', war='倭', empire='将', works='剑', fate='冤', death='正', end='龙')
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
G.THEMES['empire']['sun'] = (JINJIANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (GUNHUANG, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(4):                 # the sea off 泉州
    _d.line([(40 + i * 30, 1450 + _k * 12 + 5 * math.sin(i * 0.7 + _k * 1.3)) for i in range(35)], fill=(80, 110, 130, 50 - _k * 10), width=3)
for _x in (110, 970):               # beacon towers at the margins
    _d.rectangle((_x - 26, 1340, _x + 26, 1440), fill=(120, 100, 80, 60))
    for _k in range(3):
        _d.rectangle((_x - 26 + _k * 20, 1328, _x - 14 + _k * 20, 1340), fill=(120, 100, 80, 60))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (96, 96, 100)}
def draw_background(t, theme):
    """泉州 coast: low hills by the sea, beacon towers at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(194, 190, 186), (166, 158, 150), MTN_COL.get(theme, (124, 110, 100))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.7))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """棍头: an iron-bound staff end in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=JINJIANG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=JINJIANG + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.line((cx - 28 * sx, cy - 28 * sy, cx + 28 * sx, cy + 28 * sy), fill=GUNHUANG + (240,), width=7)
        for k in (12, 20):
            px, py = cx + k * sx, cy + k * sy
            d.line((px - 6 * sx, py + 6 * sy, px + 6 * sx, py - 6 * sy), fill=(60, 60, 60, 240), width=4)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def yu_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, armour=True, staff=False, **kw):
    """俞大猷: a stocky Ming general — helmet with a red plume, a full beard (white when old), often holding a long staff."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else ('none' if up else 'knot'), layer=layer, kneel=kneel, bow=b, **kw)
    if up:
        if armour:
            A.d['jinjiang'].ellipse((x - 0.04 * h, y - 1.12 * h, x + 0.04 * h, y - 1.02 * h), fill=255)
        else:
            A.d[layer].rectangle((x - 0.07 * h, y - 1.06 * h, x + 0.07 * h, y - 0.93 * h), fill=255)
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.0 * h, y - 0.85 * h), (x + dir * 0.1 * h, y - 0.85 * h), (x + dir * 0.06 * h, y - 0.64 * h), (x + dir * 0.0 * h, y - 0.68 * h)], fill=255)
        A.d['jinjiang'].polygon([(x - 0.1 * h, y - 0.76 * h), (x + 0.1 * h, y - 0.76 * h), (x + 0.13 * h, y - 0.3 * h), (x - 0.13 * h, y - 0.3 * h)], fill=150)
        if staff:
            staff_(A, x + dir * 0.24 * h, y, 1.15 * h, dir * 0.08)
    return hand

def staff_(A, x, y, L_, ang, layer='gunhuang'):
    tx, ty = x + L_ * math.sin(ang), y - L_ * math.cos(ang)
    A.d[layer].line((x, y, tx, ty), fill=255, width=max(4, int(0.025 * L_)))
    for f in (0.04, 0.96):
        px, py = lerp(x, tx, f), lerp(y, ty, f)
        A.d['ink'].ellipse((px - 0.015 * L_, py - 0.015 * L_, px + 0.015 * L_, py + 0.015 * L_), fill=255)

def war_cart(A, x, base, s, dir=1, layer='jinjiang'):
    A.d[layer].rectangle((x - s, base - 0.5 * s, x + s, base - 0.15 * s), fill=255)
    A.d['ink'].ellipse((x - 0.2 * s, base - 0.35 * s, x + 0.2 * s, base + 0.05 * s), outline=255, width=6)
    A.d['ink'].line((x - dir * s, base - 0.4 * s, x - dir * 1.6 * s, base - 0.2 * s), fill=255, width=5)
    for k in range(3):
        A.d['ink'].line((x + dir * s, base - 0.45 * s + k * 0.12 * s, x + dir * 1.35 * s, base - 0.5 * s + k * 0.12 * s), fill=255, width=4)

def beacons(A, cx, base, n_lit, t, total=5, out=0.0):
    A.d['dune'].polygon([(cx - 320, base), (cx - 320, base - 40), (cx - 120, base - 70), (cx + 120, base - 50), (cx + 320, base - 80), (cx + 320, base)], fill=220)
    A.d['ocean'].rectangle((cx - 320, base, cx + 320, base + 60), fill=150)
    for i in range(total):
        x = cx - 260 + i * 130
        y = base - 60 - 10 * (i % 2)
        A.d['ink'].rectangle((x - 18, y - 70, x + 18, y), fill=255)
        if i < n_lit and out < 1:
            flames(A, x, y - 70, 50, 70 * (1 - out), t + i, n=1, seed=i + 88, smoke=True)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 5), 144: (5, 5)}
def art_beacon_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    beacons(A, 540, 1160, int(lerp(a, b, clamp((q - 0.2) / 0.6) + 0.001)), t, out=clamp((q - 0.4) / 0.5) if kb == 144 else 0.0)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_beacon_chapter)
    ink_in(cv, text_img(no, SERIF, 56, JINJIANG, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_d_hook_staff(A, cv, t, u):
    ground(A, GROUND)
    temple(A, 540, GROUND - 60, 220, layer='mid')
    a = t * 3
    staff_(A, 540 - 260 * math.sin(a), GROUND - 160 + 260 * math.cos(a), 520, a + math.pi)

def art_d_hook_credit(A, cv, t, u):
    ground(A, GROUND)
    yu_(A, 360, GROUND, 230, dir=1, arm=-8)
    person(A, 700, GROUND, 230, dir=-1, robe=True, hat='knot', arm=lerp(-8, 140, clamp(u / (0.8 * P))), layer='mid')

def art_d_hook_tiger(A, cv, t, u):
    ground(A, GROUND)
    yu_(A, 380, GROUND, 230, dir=1, arm=60, staff=True)
    qi(A, 700, GROUND, 230, dir=-1, arm=60)

def art_d_hook_cart(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        war_cart(A, 220 + k * 300, GROUND, 90, dir=1)
    for j in range(4):
        rider(A, lerp(1100, 900, clamp(u / (1.2 * P))) + j * 80, GROUND, 110, dir=-1, ph=t * 6 + j, layer='ink')

# ================================================================ 第一回 晋江
def art_d_birth(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=150)
    waves(A, 1250, t, rows=2, amp=3)
    city_wall(A, 160, 920, 1100, gate_x=540, label='泉州', layer='mid', open_=1.0)
    A.flush(cv)
    paste(cv, text_img('泉州晋江人 · 家世袭百户', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('晋江', 56), 860, 1020, t, t - u + P, rot=6)

def art_d_yi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    person(A, 780, GROUND, 190, dir=-1, robe=True, hat='knot', kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    person(A, 320, GROUND, 140, dir=1, robe=True, hat='none', kneel=True, arm=90, layer='jinjiang')
    A.flush(cv)
    paste(cv, text_img('少好读书 · 从王宣 林福学易', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_jian(A, cv, t, u):
    """6-beat set piece: 学剑 — from 李良钦 he learns the long sword of 荆楚; the art is built on the staff; it becomes his 剑经."""
    ph = u / P
    ground(A, GROUND)
    a = 0.6 * math.sin(t * 3)
    person(A, 720, GROUND, 200, dir=-1, robe=False, hat='knot', arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 3 + 1)), layer='ink')
    staff_(A, 700, GROUND - 120, 300, -0.9 + 0.3 * math.sin(t * 3 + 1))
    person(A, 380, GROUND, 170, dir=1, robe=False, hat='none', arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 3)), layer='jinjiang')
    staff_(A, 400, GROUND - 100, 280, 0.9 + a)
    A.flush(cv)
    lab = '从李良钦学荆楚长剑' if ph < 2 else ('剑法以棍为本' if ph < 4 else '后著剑经 · 实为棍法')
    paste(cv, text_img(lab, SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '年份约略', t, t - u + P)

def art_d_father(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, layer='ink')
    yu_(A, 880, GROUND, 150, dir=-1, kneel=True, bow=30, armour=False)
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('父亲去世 · 承袭百户', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_wujinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='jinjiang')
    ground(A, GROUND)
    yu_(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('中武进士 · 授千户 守御金门', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('武进士', 50), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '时年三十三', t, t - u + P)

def art_d_shangshu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    yu_(A, 400, GROUND, 190, dir=1, bow=20, arm=90)
    scroll(A, 600, GROUND - 60, 200, 60, 1.0, layer='wash')
    A.flush(cv)
    paste(cv, text_img('屡次上书论海防 · 不被采纳', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_dong(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 40, GROUND - 380), (x + 40, GROUND - 380), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    army(A, lerp(-300, 200, ease_out(u / (4 * P))), GROUND, 6, dir=1, layer='jinjiang', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('平定广东新兴 恩平之乱', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 抗倭
def art_d_wo(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    waves(A, 1190, t, rows=2, amp=4)
    for k in range(4):
        wo_ship(A, lerp(1100, 500, ease_out(u / (3 * P))) + k * 150, 1200, 50, t)
    flames(A, 200, 1180, 240, 140, t, n=3, seed=1552, smoke=True)
    A.flush(cv)
    paste(cv, text_img('倭寇大举侵扰东南沿海', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_cantiang(A, cv, t, u):
    ground(A, GROUND)
    banner(A, 860, GROUND, 340, t, layer='jinjiang')
    yu_(A, 540, GROUND, 210, dir=1, arm=60, staff=True)
    A.flush(cv)
    paste(cv, text_img('调任浙江 · 宁台参将', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_wangjiangjing(A, cv, t, u):
    """6-beat set piece: 王江泾 — pirates raid 嘉兴; under 张经's command 俞大猷 and others close in; nineteen hundred heads — the greatest victory yet."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1200, W - 60, 1260), fill=140)
    river(A, 1210, t, rows=2, amp=3)
    ground(A, GROUND)
    if ph < 2:
        for j in range(6):
            wokou(A, lerp(1100, 600, clamp(ph / 2)) + j * 80, GROUND, 130, dir=-1, ph=t * 4 + j, arm=60)
        lab, col = '倭寇进犯嘉兴', JINJIANG
    elif ph < 4:
        for j in range(5):
            ming_soldier(A, lerp(-100, 400, clamp((ph - 2) / 1.5)) + j * 70, GROUND, 130, dir=1, weapon='spear', arm=40)
        for j in range(5):
            wokou(A, 700 + j * 70, GROUND, 130, dir=-1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 6 + j)))
        lab, col = '张经调度 · 俞大猷等合击', JINJIANG
    else:
        for j in range(5):
            wokou(A, 680 + j * 70, GROUND, 130, dir=-1, fall=80, arm=-8)
        yu_(A, 400, GROUND, 210, dir=1, arm=140, staff=True)
        lab, col = '斩首一千九百余级 · 抗倭以来第一大捷', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('王江泾', 50), 860, 1020, t, t - u + 4 * P, rot=6)

def art_d_zhangjing(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, robe=True, hat='knot', kneel=True, bow=50, layer='ink')
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='mid')
    A.flush(cv)
    paste(cv, text_img('赵文华冒功 诬陷张经 · 张经被斩', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '赵文华为严嵩义子', t, t - u + P)

def art_d_maogong(A, cv, t, u):
    ground(A, GROUND)
    yu_(A, 360, GROUND, 220, dir=1, arm=-8, staff=True)
    person(A, 700, GROUND, 220, dir=-1, robe=True, hat='knot', arm=lerp(-8, 140, ease_out(u / 0.8)), layer='mid')
    A.flush(cv)
    paste(cv, text_img('俞大猷的战功 · 屡被他人冒领', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '他从不争功', t, t - u + P)

def art_d_xuhai(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        x = 300 + k * 240
        A.d['wash'].rectangle((x - 80, GROUND - 140, x + 80, GROUND), fill=230)
        A.d['ink'].polygon([(x - 100, GROUND - 140), (x + 100, GROUND - 140), (x, GROUND - 200)], fill=255)
    flames(A, 540, GROUND - 140, 500, 160 * clamp(u / (2 * P)), t, n=4, seed=1556, smoke=True)
    for j in range(5):
        ming_soldier(A, 100 + j * 220, GROUND, 120, dir=1 if j < 3 else -1, weapon='spear', arm=40)
    A.flush(cv)
    paste(cv, text_img('胡宗宪设计招抚 · 俞大猷围歼徐海', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_cengang(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=4)
    A.d['mid'].polygon([(560, 1200), (760, 980), (960, 1200)], fill=170)
    city_wall(A, 640, 900, 1060, gate_x=None, label='岑港', layer='mid')
    for k in range(3):
        boat(A, 160 + k * 150, 1220, 60, t)
    A.flush(cv)
    paste(cv, text_img('围汪直余部于舟山岑港 · 久攻不下', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

# ================================================================ 第三回 入狱
def art_d_prison(A, cv, t, u):
    """6-beat set piece: 岑港之后 — the pirates escape; 胡宗宪 shifts the blame; 俞大猷 is arrested and jailed in Beijing;
    陆炳 spends his own money to save him; he is sent north to 大同 to redeem himself."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        person(A, 700, GROUND, 210, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)), layer='mid')
        yu_(A, 380, GROUND, 200, dir=1, bow=20, arm=-8)
        lab, col = '倭寇遁走 · 胡宗宪推卸罪责', JINJIANG
    elif ph < 4:
        for k in range(9):
            A.d['ink'].line((260 + k * 70, 900, 260 + k * 70, GROUND), fill=255, width=10)
        A.d['ink'].rectangle((240, 880, 840, 900), fill=255)
        yu_(A, 540, GROUND, 170, dir=1, kneel=True, bow=10, armour=False)
        lab, col = '俞大猷被逮 · 下锦衣卫狱', ZHU
    else:
        person(A, 760, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(-8, 100, clamp((ph - 4) / 0.6)), layer='ink')
        A.d['qiuhuang'].ellipse((560, GROUND - 120, 620, GROUND - 80), fill=255)
        yu_(A, 380, GROUND, 190, dir=1, bow=20, arm=-8, armour=False)
        lab, col = '陆炳倾私财营救 · 戴罪发往大同', JINJIANG
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

def art_d_datong(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 180, GROUND), (x, GROUND - 220), (x + 180, GROUND)], fill=170)
    ground(A, GROUND)
    city_wall(A, 160, 920, 1120, gate_x=540, label='大同', layer='mid', open_=1.0)
    yu_(A, 540, GROUND, 180, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('戴罪发往大同 · 抵御鞑靼', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_cheying(A, cv, t, u):
    """6-beat set piece: 车营 — to meet the steppe cavalry he builds a wagon fort: carts in a ring, spears out, guns behind; the riders cannot close."""
    ph = u / P
    ground(A, GROUND)
    n = min(4, int(clamp(ph / 2) * 4) + 1)
    for k in range(n):
        war_cart(A, 180 + k * 200, GROUND, 80, dir=1)
    if ph >= 2:
        for j in range(5):
            x = lerp(1100, 920, clamp((ph - 2) / 1)) + j * 70
            if ph > 3.5:
                x = lerp(920, 1200, clamp((ph - 3.5) / 1.5)) + j * 70
            rider(A, x, GROUND, 110, dir=-1 if ph < 3.5 else 1, ph=t * 6 + j, layer='ink')
    A.flush(cv)
    lab = '以车御骑' if ph < 2 else ('战车列营 · 长枪向外 火器在后' if ph < 3.5 else '鞑靼骑兵不能近')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('车营', 56), 860, 1020, t, t - u + 2 * P, rot=6)

def scene_shaolin(cv, t, c, k):
    """8-beat custom scene: 少林传棍 — passing 嵩山 he visits 少林寺 and watches the monks' famous staff; the true art is lost;
    he teaches; two monks follow him south for three years and carry the method back."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    for k2 in range(3):
        x = 260 + k2 * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 380), (x + 240, GROUND)], fill=150)
    temple(A, 540, GROUND - 120, 260, layer='mid')
    ground(A, GROUND)
    if ph < 2.5:
        for j in range(4):
            xz(A, 200 + j * 120, GROUND, 140, dir=1, staff=False, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 4 + j)))
            staff_(A, 230 + j * 120, GROUND - 90, 200, 0.7 * math.sin(t * 4 + j))
        yu_(A, 860, GROUND, 190, dir=-1, arm=-8)
        lab, col = '途经嵩山 · 观少林僧演棍', JINJIANG
    elif ph < 5:
        yu_(A, 420, GROUND, 190, dir=1, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 4)), staff=False)
        staff_(A, 440, GROUND - 120, 300, 0.9 * math.sin(t * 4))
        for j in range(4):
            xz(A, 640 + j * 90, GROUND, 130, dir=-1, kneel=True, staff=False, bow=20)
        lab, col = '传其真诀已失 · 俞大猷亲授棍法', ZHU
    else:
        for j in range(2):
            xz(A, lerp(500, 1100, clamp((ph - 5) / 2.5)) + j * 90, GROUND, 150, dir=1, staff=False, ph=t * 3 + j, arm=-8)
        yu_(A, lerp(380, 980, clamp((ph - 5) / 2.5)), GROUND, 180, dir=1, ph=t * 3, arm=-8)
        lab, col = '宗擎 普从二僧随军学艺 三年而返', JINJIANG
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '少林传棍', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=88)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '事见俞大猷正气堂集 新建十方禅院碑', t, s0 + 3 * P)

def art_d_fujian(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='兴化', layer='mid', open_=1.0)
    flames(A, 540, 1080, 500, 160, t, n=4, seed=1562, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('倭寇攻陷兴化 · 俞大猷调任福建总兵', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 平海
def art_d_pinghai(A, cv, t, u):
    """6-beat set piece: 平海卫 — 俞大猷 on the left, 戚继光 in the centre, 刘显 on the right; the pirate camp at 平海卫 is broken; 兴化 retaken."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        yu_(A, 240, GROUND, 190, dir=1, arm=60, staff=True)
        qi(A, 540, GROUND, 190, dir=1, arm=60)
        person(A, 840, GROUND, 190, dir=1, robe=False, hat='helmet', arm=60, layer='mid')
        lab, col = '俞大猷居左 戚继光居中 刘显居右', JINJIANG
    elif ph < 4:
        for j in range(4):
            wo_ship(A, 700 + j * 100, 1180, 40, t, burn=clamp((ph - 2) / 1))
        for j in range(5):
            ming_soldier(A, lerp(-100, 450, clamp((ph - 2) / 1.5)) + j * 70, GROUND, 120, dir=1, weapon='spear', arm=40)
        lab, col = '三路合击 · 平海卫倭巢大破', ZHU
    else:
        city_wall(A, 160, 920, 1080, gate_x=540, label='兴化', layer='mid', open_=1.0)
        flag(A, 540, 1080, 220, t, layer='red')
        lab, col = '斩倭两千余 · 收复兴化', JINJIANG
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('平海', 56), 860, 1020, t, t - u + 4 * P, rot=6)

def art_d_longhu(A, cv, t, u):
    ground(A, GROUND)
    yu_(A, 380, GROUND, 230, dir=1, arm=60, staff=True)
    qi(A, 700, GROUND, 230, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('时人并称 俞龙戚虎', SERIF, 50, JINJIANG, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))

def art_d_lian(A, cv, t, u):
    tent(A, 540, GROUND, 400, 280, layer='mid', open_=1.0)
    ground(A, GROUND)
    yu_(A, 540, GROUND, 180, dir=1, kneel=True, arm=90, armour=False, old=0.5)
    for j in range(4):
        ming_soldier(A, 140 + j * 70 if j < 2 else 820 + (j - 2) * 70, GROUND, 130, dir=1 if j < 2 else -1, weapon='spear', arm=40)
    A.flush(cv)
    paste(cv, text_img('为将清廉 驭下有恩 · 数建大功', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见明史俞大猷传', t, t - u + P)

def art_d_wuping(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    waves(A, 1190, t, rows=2, amp=4)
    A.d['mid'].polygon([(560, 1180), (780, 980), (1000, 1180)], fill=170)
    for k in range(3):
        wo_ship(A, 760 + k * 70, 1200, 30, t, burn=clamp(u / (3 * P)))
    for k in range(3):
        boat(A, lerp(-100, 400, ease_out(u / (3 * P))) - k * 120, 1210, 60, t)
    A.flush(cv)
    paste(cv, text_img('追剿海盗吴平 · 平定南澳', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_d_zengyiben(A, cv, t, u):
    """6-beat set piece: 曾一本 — the great pirate 曾一本 terrorises 广东 and 福建; the navies of two provinces join; his fleet is destroyed."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1140, W - 60, GROUND + 40), fill=160)
    waves(A, 1150, t, rows=3, amp=5)
    for k in range(4):
        wo_ship(A, 700 + k * 90, 1170, 40, t, burn=clamp((ph - 2.5) / 1))
    for k in range(4):
        boat(A, lerp(-100, 480, clamp(ph / 3)) - k * 110, 1180, 60, t)
    A.flush(cv)
    lab = '大海寇曾一本 · 横行闽粤' if ph < 2 else ('闽粤水师会剿' if ph < 3.5 else '曾一本覆灭')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

def art_d_tanhe(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for j in range(3):
        person(A, 640 + j * 100, GROUND, 170, dir=-1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + j)), layer='mid')
    yu_(A, 340, GROUND, 190, dir=1, arm=-8, old=0.7)
    A.flush(cv)
    paste(cv, text_img('晚年屡遭弹劾 · 起落不定', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 俞龙
def art_d_jianjing(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    yu_(A, 260, GROUND, 180, dir=1, kneel=True, arm=90, armour=False, old=0.8)
    Sc.book(A, 560, GROUND - 74, 140, 0, open_=1.0)
    A.flush(cv)
    paste(cv, text_img('著剑经 · 后为戚继光纪效新书收录', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '另有文集正气堂集', t, t - u + P)

def art_d_zhishi(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=140)
    waves(A, 1250, t, rows=2, amp=3)
    A.d['wash'].rectangle((620, 1100, 860, 1240), fill=255)
    A.d['ink'].polygon([(600, 1100), (880, 1100), (740, 1040)], fill=255)
    yu_(A, 360, 1240, 180, dir=1, arm=-8, armour=False, old=0.9, staff=True)
    A.flush(cv)
    paste(cv, text_img('年老致仕 · 归隐故里', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    yu_(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, armour=False)
    staff_(A, 860, GROUND, 360, 0.0)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('俞大猷卒 · 年七十七', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_wuxiang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('武襄', 90, ZHU), 540, 1140, t, t - u + 0.6)
    paste(cv, text_img('追赠左都督 · 谥武襄', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_fame(A, cv, t, u):
    ground(A, GROUND)
    qi(A, 640, GROUND, 260, dir=-1, arm=60)
    yu_(A, 380, GROUND, 200, dir=1, arm=-8, old=0.6, layer='mid')
    A.flush(cv)
    paste(cv, text_img('同为抗倭名将 · 名声却远不如戚继光', SERIF, 46, JINJIANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '其功多被他人所冒 又少有人为其立传', t, t - u + P)

def art_d_gun(A, cv, t, u):
    ground(A, GROUND)
    temple(A, 540, GROUND - 120, 240, layer='mid')
    for j in range(3):
        xz(A, 300 + j * 240, GROUND, 150, dir=1, staff=False, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 4 + j)))
        staff_(A, 330 + j * 240, GROUND - 100, 220, 0.7 * math.sin(t * 4 + j))
    A.flush(cv)
    paste(cv, text_img('少林棍法 因他得以重振', SERIF, 48, JINJIANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_d_end(A, cv, t, u):
    beacons(A, 540, 1200, 5, t, out=1.0)
    A.flush(cv)
    paste(cv, text_img('海不扬波 · 一生正气', SERIF, 48, JINJIANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_d_legacy(A, cv, t, u):
    staff_(A, 860, 1440, 160, 0.2)

def art_d_title(A, cv, t, u):
    beacons(A, 800, 1440, 2, t, total=3)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    yu_(A, 380, 1460, 640, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))), staff=True)

# ================================================================ script
CHAPTERS = {16: ('第一回', '晋江'), 48: ('第二回', '抗倭'), 80: ('第三回', '入狱'),
            112: ('第四回', '平海'), 144: ('第五回', '俞龙')}

CARDS = [
    C(0, 2, 'works', 'num', num='一根长棍', line='教会了少林和尚', art=art_d_hook_staff),
    C(2, 4, 'fate', 'num', num='一辈子战功', line='常被别人冒领', art=art_d_hook_credit),
    C(4, 6, 'empire', 'num', num='俞龙戚虎', line='抗倭双雄', art=art_d_hook_tiger),
    C(6, 8, 'war', 'num', num='一座车营', line='挡住蒙古骑兵', art=art_d_hook_cart),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 晋江
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1503, main='生于晋江', sub='世袭百户', art=art_d_birth),
    C(22, 26, 'works', 'card', year=1515, main='读易', sub='王宣林福', note='年份约略', art=art_d_yi),
    C(26, 32, 'night', 'card', year=1520, main='学剑', sub='李良钦', note='年份约略', art=art_d_jian),
    C(32, 36, 'death', 'card', year=1522, main='父亲去世', sub='承袭百户', note='年份约略', art=art_d_father),
    C(36, 40, 'empire', 'card', year=1535, main='武进士', sub='守御金门', art=art_d_wujinshi),
    C(40, 44, 'court', 'card', year=1540, main='上书言兵', sub='不被采纳', note='年份约略', art=art_d_shangshu),
    C(44, 48, 'war', 'card', year=1546, main='平定峒乱', sub='广东', note='年份约略', art=art_d_dong),
    # ---- 第二回 抗倭
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'fate', 'card', year=1552, main='倭寇大至', sub='东南沿海', art=art_d_wo),
    C(54, 58, 'empire', 'card', year=1553, main='宁台参将', sub='浙江', art=art_d_cantiang),
    C(58, 64, 'war', 'card', year=1555, main='王江泾', sub='第一大捷', art=art_d_wangjiangjing),
    C(64, 68, 'death', 'card', year=1555, main='张经冤死', sub='赵文华冒功', art=art_d_zhangjing),
    C(68, 72, 'night', 'card', year=1556, main='功被冒领', sub='从不争功', art=art_d_maogong),
    C(72, 76, 'war', 'card', year=1556, main='平徐海', sub='沈家庄', art=art_d_xuhai),
    C(76, 80, 'fate', 'card', year=1558, main='岑港', sub='久攻不下', art=art_d_cengang),
    # ---- 第三回 入狱
    C(80, 82, 'death', 'chapter'),
    C(82, 88, 'death', 'card', year=1559, main='下狱', sub='代人受过', art=art_d_prison),
    C(88, 92, 'court', 'card', year=1559, main='发往大同', sub='戴罪立功', art=art_d_datong),
    C(92, 98, 'works', 'card', year=1560, main='车营', sub='以车御骑', art=art_d_cheying),
    C(98, 106, 'night', 'shaolin', year=1561),
    C(106, 112, 'fate', 'card', year=1562, main='南调福建', sub='兴化失陷', art=art_d_fujian),
    # ---- 第四回 平海
    C(112, 114, 'empire', 'chapter'),
    C(114, 120, 'war', 'card', year=1563, main='平海卫', sub='三路合击', art=art_d_pinghai),
    C(120, 124, 'empire', 'card', year=1563, main='俞龙戚虎', sub='时人并称', art=art_d_longhu),
    C(124, 128, 'life', 'card', year=1564, main='为将清廉', sub='驭下有恩', note='年份约略', art=art_d_lian),
    C(128, 132, 'war', 'card', year=1565, main='平吴平', sub='南澳', art=art_d_wuping),
    C(132, 138, 'war', 'card', year=1569, main='曾一本', sub='闽粤会剿', art=art_d_zengyiben),
    C(138, 144, 'fate', 'card', year=1570, main='屡遭弹劾', sub='起落不定', note='年份约略', art=art_d_tanhe),
    # ---- 第五回 俞龙
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'works', 'card', year=1575, main='剑经', sub='正气堂集', note='年份约略', art=art_d_jianjing),
    C(150, 154, 'life', 'card', year=1577, main='致仕', sub='归隐', note='年份约略', art=art_d_zhishi),
    C(154, 158, 'death', 'card', year=1579, main='俞大猷去世', sub='年七十七', art=art_d_death),
    C(158, 162, 'court', 'card', year=1579, main='谥武襄', sub='左都督', art=art_d_wuxiang),
    C(162, 166, 'night', 'card', year=1579, main='名不如戚', sub='功常被冒', art=art_d_fame),
    C(166, 168, 'works', 'card', year=1579, main='少林棍', sub='因他重振', art=art_d_gun),
    C(168, 170, 'end', 'card', year=1579, main='正气', sub='海不扬波', art=art_d_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='捌拾捌', col=JINJIANG, acc=GUNHUANG, born=1503, died=1579, age0=1502,
    born_lab='1503年', died_lab='1579年', years_txt='公元1503 — 1579',
    hook_q='他打了一辈子胜仗 · 为什么名气远不如戚继光？',
    name_line='俞大猷 · 字志辅', name='俞大猷', seal='虚江', title_art=art_d_title,
    q1='抗倭名将？', q2='功高不赏？',
    end_art=art_d_legacy, end_big='俞龙戚虎', end_seal='虚江',
    end_l1='功劳他常常让给了别人', end_l2='正气却一分都没让',
    end_brush='正气', end_ask='在这之前 你听说过俞大猷吗？评论区聊聊', next='宋应星'),
    scenes=dict(chapter=scene_chapter, shaolin=scene_shaolin))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
