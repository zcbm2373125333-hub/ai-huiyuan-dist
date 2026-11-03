"""千古人物志 · 第叁拾柒集 · 包拯 (999–1062)
Look: 玄青 + 端砚紫, 令签筒 corner borders, a 端砚 chapter card: the ink pool in the inkstone grows deeper each
chapter; in the last the brush is laid down across it.
Set pieces: 6-beat 牛舌案, 6-beat 不持一砚归, custom 8-beat scene 'tanhe' (七弹张尧佐),
8-beat 开封府开正门, 6-beat 家训.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_wanganshi as Was      # engine + helpers (previous episode)
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
from render_quyuan import river
from render_simaqian import brush, bars
from render_kongzi import bundle
from render_libai import moon_phase
from render_songtaizu import tent

F.RIPPLE = False
XUAN = (44, 54, 74)                 # 玄青
DUAN = (118, 76, 98)                # 端砚紫
S.LAYERS.append(('xuan', XUAN, 0.9, 1.0))
S.LAYERS.append(('duan', DUAN, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='包', life='孝', court='宋', night='冤', war='劾', empire='宋', works='廉', fate='直', death='孝', end='公')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (DUAN, 220, (W * 0.5, 820))
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (XUAN, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

HALL = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(HALL)
for _x in (90, 990):
    _d.rectangle((_x - 18, 1160, _x + 18, 1490), fill=XUAN + (44,))
    _d.rectangle((_x - 34, 1150, _x + 34, 1170), fill=XUAN + (54,))
_d.rectangle((60, 1490, W - 60, 1500), fill=XUAN + (40,))
MTN_COL = {'night': (34, 36, 44), 'death': (60, 60, 64), 'war': (92, 64, 70), 'fate': (80, 86, 100)}
def draw_background(t, theme):
    """公堂: low ridges framed by two dark hall pillars."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(182, 184, 192), (140, 144, 160), MTN_COL.get(theme, (100, 104, 124))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(HALL)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """令签筒: a tall tube of lots with red tips in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=XUAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=XUAN + (220,), width=3)
        bx0, bx1 = x + sx * 20, x + sx * 60
        by0, by1 = y + sy * 60, y + sy * 120
        d.rectangle((min(bx0, bx1), min(by0, by1), max(bx0, bx1), max(by0, by1)), fill=DUAN + (220,))
        for k in range(4):
            lx = x + sx * (26 + k * 9)
            ly0, ly1 = y + sy * 60, y + sy * (18 + k * 6)
            d.line((lx, ly0, lx + sx * (k - 1.5) * 3, ly1), fill=XUAN + (230,), width=3)
            d.ellipse((lx - 3, ly1 - 3, lx + 3, ly1 + 3), fill=ZHU + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def bao(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """包拯: stern, long-winged 展脚幞头, full beard; a small crescent on the brow (stage legend)."""
    b = bow + 12 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.07 * h, y - 1.06 * h, x + 0.07 * h, y - 0.94 * h), fill=255)
        d.rectangle((x - 0.34 * h, y - 1.0 * h, x + 0.34 * h, y - 0.985 * h), fill=255)
        d.polygon([(x + dir * 0.0, y - 0.86 * h), (x + dir * 0.1 * h, y - 0.86 * h), (x + dir * 0.05 * h, y - 0.6 * h)], fill=255)
        A.d['gold'].arc((x - 0.03 * h, y - 0.95 * h, x + 0.03 * h, y - 0.9 * h), 20, 160, fill=255, width=max(2, int(0.012 * h)))
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.02 * h, y - 0.84 * h), (x + dir * 0.08 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.66 * h)], fill=255)
    return hand

def inkstone(A, cx, cy, s, depth=0.5, t=0.0, layer='duan'):
    A.d[layer].rounded_rectangle((cx - s, cy - 0.65 * s, cx + s, cy + 0.65 * s), radius=int(0.2 * s), fill=255)
    A.d['ink'].rounded_rectangle((cx - s, cy - 0.65 * s, cx + s, cy + 0.65 * s), radius=int(0.2 * s), outline=255, width=max(3, int(0.04 * s)))
    A.d['wash'].ellipse((cx - 0.75 * s, cy - 0.4 * s, cx + 0.75 * s, cy + 0.45 * s), fill=255)
    r = 0.7 * s * depth
    if r > 2:
        A.d['ink'].ellipse((cx - r, cy - 0.55 * r + 0.05 * s, cx + r, cy + 0.55 * r + 0.05 * s), fill=255)
        A.d['wash'].arc((cx - r * 0.6, cy - 0.3 * r, cx + r * 0.2, cy + 0.1 * r), 200, 300, fill=120, width=3)

def gavel(A, x, y, s, lift=0.0):
    A.d['xuan'].rectangle((x - 0.5 * s, y - 0.22 * s - lift * 60, x + 0.5 * s, y - lift * 60), fill=255)

def ox(A, x, y, s, dir=1, layer='ink'):
    d = A.d[layer]
    def T(u, v): return (x + dir * u * s, y - v * s)
    d.polygon([T(*p) for p in ellipse_pts(0, 0.55, 0.45, 0.2)], fill=255)
    d.polygon([T(0.38, 0.65), T(0.62, 0.62), T(0.66, 0.42), T(0.42, 0.42)], fill=255)
    d.line([T(0.45, 0.68), T(0.38, 0.82)], fill=255, width=max(2, int(0.04 * s)))
    d.line([T(0.58, 0.68), T(0.66, 0.82)], fill=255, width=max(2, int(0.04 * s)))
    for hu in (-0.3, -0.15, 0.2, 0.32):
        d.line([T(hu, 0.4), T(hu, 0.0)], fill=255, width=max(3, int(0.06 * s)))

def stele(A, cx, base, w, h, layer='xuan'):
    A.d[layer].rectangle((cx - w / 2, base - h, cx + w / 2, base), fill=230)
    A.d[layer].chord((cx - w / 2, base - h - 0.4 * w, cx + w / 2, base - h + 0.4 * w), 180, 360, fill=230)
    A.d['ink'].rectangle((cx - w / 2 - 20, base - 20, cx + w / 2 + 20, base), fill=255)

# ================================================================ chapter card
CH = {16: 0.15, 48: 0.35, 80: 0.6, 112: 0.85, 144: 0.9}
def art_ink_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    dp = CH.get(kb, 0.35)
    q = ease_out(u / (1.2 * P))
    inkstone(A, 540, 1020, 190, depth=lerp(max(0, dp - 0.2), dp, q), t=t)
    if kb == 144:
        brush(A, lerp(700, 380, q), 980, 300, ang=math.pi - 0.08)
    else:
        a = t * 2
        sx, sy = 540 + 80 * math.cos(a), 1020 + 30 * math.sin(a)
        A.d['ink'].rectangle((sx - 18, sy - 150, sx + 18, sy), fill=255)
        A.d['gold'].rectangle((sx - 18, sy - 150, sx + 18, sy - 120), fill=255)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_ink_chapter)
    ink_in(cv, text_img(no, SERIF, 56, DUAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_b_hook_face(A, cv, t, u):
    ground(A, GROUND)
    bao(A, 540, GROUND, 320, dir=1, arm=40)
    moon_phase(A, 820, 820, 60, 0.3)

def art_b_hook_yanluo(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='xuan')
    ground(A, GROUND)
    gavel(A, 540, GROUND - 100, 120, lift=abs(math.sin(t * 4)) if u < 1.4 * P else 0)
    desk(A, 540, GROUND, 360, layer='duan')

def art_b_hook_yan(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=5, speed=1.4)
    p = ease_out(u / (1.4 * P))
    inkstone(A, lerp(300, 620, p), lerp(1100, 1260, p), 60, depth=0.4)
    boat(A, 300, 1270, 110, t, sail=True)

def art_b_hook_rule(A, cv, t, u):
    stele(A, 540, GROUND, 260, 360)
    ground(A, GROUND)

# ================================================================ 第一回 孝子为先
def art_b_hefei(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 220), (x + 200, GROUND)], fill=160)
    A.d['ocean'].line([(60, 1340), (540, 1300), (1020, 1340)], fill=150, width=24)
    ground(A, GROUND)
    person(A, 420, GROUND, 230, dir=1, robe=True, hat='none', arm=40, layer='ink')
    person(A, 560, GROUND, 210, dir=-1, robe=True, hat='knot', female=True, baby=True, layer='ink')
    A.flush(cv)
    stamp(cv, seal('庐州合肥', 46), 860, 880, t, t - u + P, rot=6)

def art_b_study(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='xuan')
    sitter(A, 320, GROUND, 180, dir=1, bow=20)
    lamp(A, 700, GROUND - 70, 40, t, glow=0.7)
    for k in range(int(clamp(u / (2 * P)) * 6)):
        bundle(A, 440 + k * 40, GROUND - 74, 34, layer='duan')
    A.flush(cv)
    paste(cv, text_img('少有孝行 · 苦读诗书', SERIF, 46, XUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_jinshi(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='duan')
    ground(A, GROUND)
    bao(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 30, ease_out(u / 0.6)))
    A.d['yellow'].rectangle((240, 860, 840, 920), fill=255)
    A.flush(cv)
    stamp(cv, seal('进士', 56), 860, 980, t, t - u + P, rot=6)

def art_b_parents(A, cv, t, u):
    A.d['xuan'].rectangle((300, 1060, 780, GROUND), fill=200)
    A.d['ink'].polygon([(270, 1060), (810, 1060), (540, 960)], fill=255)
    ground(A, GROUND)
    for k in range(2):
        sitter(A, 440 + k * 120, GROUND, 150, dir=1 if k == 0 else -1, bow=10, layer='mid')
    bao(A, 760, GROUND, 200, dir=-1, kneel=True, bow=40, arm=110)
    A.flush(cv)
    stamp(cv, seal('辞官养亲', 46), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('父母年迈 不愿远离', SERIF, 46, DUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_b_mourn(A, cv, t, u):
    for k in range(2):
        A.d['mid'].chord((300 + k * 260, 1220, 520 + k * 260, GROUND + 120), 180, 360, fill=230)
    A.d['mid'].polygon([(860, 1260), (960, 1180), (1000, 1260)], fill=200)
    ground(A, GROUND)
    bao(A, 880, GROUND, 160, dir=-1, kneel=True, bow=50, arm=100)
    A.flush(cv)
    stamp(cv, seal('庐墓', 54, INK), 540, 1080, t, t - u + P)
    paste(cv, text_img('守墓终丧 · 徘徊不忍去', SERIF, 44, XUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_tongue(A, cv, t, u):
    """6-beat set piece: 牛舌案 — a farmer weeps over his ox whose tongue was cut; 包拯 tells him to slaughter it
    and sell the meat; the culprit comes to accuse him of illegal slaughter — and is caught."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        ox(A, 360, GROUND, 160, dir=1)
        person(A, 600, GROUND, 170, dir=-1, robe=False, hat='knot', bow=40, arm=120, layer='mid')
    elif ph < 3.5:
        desk(A, 540, GROUND, 360, layer='xuan')
        bao(A, 540, GROUND - 40, 210, dir=1, arm=lerp(30, 120, ease_out((ph - 2) / 0.6)))
        person(A, 260, GROUND, 160, dir=1, robe=False, hat='knot', kneel=True, bow=30, arm=100, layer='mid')
    else:
        desk(A, 540, GROUND, 360, layer='xuan')
        bao(A, 540, GROUND - 40, 210, dir=1, arm=lerp(30, 150, ease_out((ph - 3.5) / 0.5)))
        person(A, 820, GROUND, 170, dir=-1, robe=False, hat='knot', kneel=ph > 4.5, bow=50 if ph > 4.5 else 0, arm=lerp(120, 90, ease_out((ph - 3.5) / 1)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('天长县', 50), 860, 880, t, t - u + 0.4, rot=6)
    lab = '有人割了他家的牛舌' if ph < 2 else ('杀牛卖肉 静候其变' if ph < 3.5 else '告状者 正是割舌之人')
    paste(cv, text_img(lab, SERIF, 46, DUAN if ph < 3.5 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_b_duanzhou(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['grass'].polygon([(x - 150, GROUND), (x, GROUND - 340), (x + 150, GROUND)], fill=170)
    A.d['ocean'].line([(60, 1340), (540, 1300), (1020, 1340)], fill=150, width=24)
    ground(A, GROUND)
    bao(A, lerp(-80, 540, ease_out(u / (2 * P))), GROUND, 210, dir=1, ph=t * 4 if u < 2 * P else None, arm=40)
    A.flush(cv)
    stamp(cv, seal('端州', 56), 860, 880, t, t - u + P, rot=6)

# ================================================================ 第二回 不持一砚
def art_b_tribute(A, cv, t, u):
    """6-beat set piece: 贡砚 — previous prefects levied ten times the tribute for gifts; he cuts it to the exact quota;
    a counter falls from 数十方 to the quota; he leaves with empty hands."""
    ph = u / P
    ground(A, GROUND)
    n = int(lerp(30, 6, ease_out((ph - 1) / 2.5)))
    for i in range(n):
        x = 160 + (i % 10) * 76; y = GROUND - 30 - (i // 10) * 70
        inkstone(A, x, y, 30, depth=0.4)
    bao(A, 900, GROUND, 220, dir=-1, arm=lerp(30, 150, ease_out((ph - 1) / 0.6)))
    A.flush(cv)
    paste(cv, text_img('往任多取数十倍 · 以送权贵' if ph < 1 else ('只按贡数' if ph < 4 else '岁满不持一砚归'), SERIF, 46, DUAN if ph < 4 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_b_throw(A, cv, t, u):
    river(A, 1200, t, rows=4, amp=6, speed=1.4)
    boat(A, 420, 1250, 130, t, sail=True)
    bao(A, 420, 1220, 150, dir=1, arm=lerp(60, 160, ease_out((u - 0.5 * P) / 0.6)))
    p = ease_out((u - 1.2 * P) / P)
    A.d['duan'].rounded_rectangle((520 + 260 * p - 30, 1080 + 180 * p - 20, 520 + 260 * p + 30, 1080 + 180 * p + 20), radius=6, fill=255)
    if p > 0.9:
        A.d['grass'].ellipse((720, 1240, 900, 1290), fill=200)
    A.flush(cv)
    stamp(cv, seal('传说', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('掷砚成洲', SERIF, 52, DUAN, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp((u - 2 * P) / 0.3))

def art_b_censor(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='xuan')
    ground(A, GROUND)
    bao(A, 540, GROUND, 240, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)))
    scroll(A, 780, GROUND - 200, 140, 50, u / 0.5)
    A.flush(cv)
    stamp(cv, seal('监察御史', 44), 260, 880, t, t - u + P, rot=-5)

def art_b_khitan(A, cv, t, u):
    tent(A, 760, GROUND, 360, 280, layer='mid')
    ground(A, GROUND)
    person(A, 700, GROUND, 220, dir=-1, robe=True, hat='helmet', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    bao(A, 330, GROUND, 230, dir=1, arm=lerp(30, 100, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    stamp(cv, seal('出使契丹', 44), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('据理驳斥 不辱使命', SERIF, 46, DUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_b_wangkui(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    bao(A, 330, GROUND, 230, dir=1, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 4)))
    person(A, 760, GROUND, 220, dir=-1, robe=True, hat='none', bow=lerp(0, 40, ease_out((u - 2 * P) / 0.6)), arm=60, layer='ink')
    n = min(7, int(u / (0.45 * P)) + 1)
    A.flush(cv)
    for i in range(n):
        stamp(cv, seal(cn_num(i + 1), 30, ZHU), 160 + i * 110, 880, t, t - u + i * 0.45 * P)
    paste(cv, text_img('七次弹劾 终罢其官', SERIF, 46, XUAN, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - 3 * P) / 0.3))

def art_b_salt(A, cv, t, u):
    ground(A, GROUND)
    for k in range(int(clamp(u / (2 * P)) * 8)):
        A.d['wash'].polygon([(160 + k * 100, GROUND), (210 + k * 100, GROUND - 70), (260 + k * 100, GROUND)], fill=255)
        A.d['ink'].polygon([(160 + k * 100, GROUND), (210 + k * 100, GROUND - 70), (260 + k * 100, GROUND)], outline=150, width=2)
    bao(A, 540, GROUND - 90, 180, dir=1, arm=60)
    A.flush(cv)
    stamp(cv, seal('三司户部', 44), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('改革盐法 · 通商便民', SERIF, 46, DUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_jianguan(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='xuan')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 210, dir=1, robe=True, hat='crown', arm=40, layer='ink')
    bao(A, 200, GROUND, 210, dir=1, kneel=True, bow=30, arm=110)
    for k in range(2):
        person(A, 820 + k * 90, GROUND, 160, dir=-1, robe=True, hat='none', bow=30, arm=100, layer='mid')
    A.flush(cv)
    stamp(cv, seal('知谏院', 50), 860, 880, t, t - u + P, rot=6)

# ================================================================ 第三回 犯颜直谏
def scene_tanhe(cv, t, c, k):
    """8-beat custom scene: 弹劾张尧佐 — the favourite consort's uncle is loaded with four posts; 包拯 argues before the
    emperor, leaning closer each beat, until (legend) spittle flies; the posts are withdrawn one by one."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    palace(A, 540, 1100, 620, layer='duan')
    ground(A, GROUND)
    person(A, 760, GROUND - 40, 230, dir=-1, robe=True, hat='crown', bow=lerp(0, -15, ease_out((ph - 4) / 1)), arm=lerp(20, 60, ease_out((ph - 4) / 1)), layer='ink')
    x = lerp(240, 600, ease_out(ph / 4.5))
    bao(A, x, GROUND, 230, dir=1, arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 6)))
    if 4 <= ph < 5:
        for j in range(8):
            q = (ph - 4)
            A.d['wash'].ellipse((x + 60 + 120 * q + j * 6 - 4, GROUND - 230 + j * 4 - 4, x + 60 + 120 * q + j * 6 + 4, GROUND - 230 + j * 4 + 4), fill=230)
    A.flush(cv)
    posts = ['宣徽使', '节度使', '景灵宫使', '群牧制置使']
    gone = int(clamp((ph - 5) / 2.5) * 4)
    for i, nm in enumerate(posts):
        y = 860 + i * 70
        im = seal(nm, 28, INK)
        paste(cv, im, 920, y, 1, 0.35 if i < gone else 1)
        if i < gone:
            ImageDraw.Draw(cv).line((850, y, 990, y), fill=ZHU + (255,), width=6)
    fx = Art()
    chars_in(cv, fx, '弹劾张尧佐', BRUSH, 140, INK, W / 2, 440, t, s0, stagger=0.06, seed=50)
    fx.flush(cv)
    lab = '贵妃之伯父 一日四使' if ph < 2 else ('反复力争 声色俱厉' if ph < 4 else ('传说 唾沫溅到皇帝脸上' if ph < 5 else '仁宗收回成命'))
    paste(cv, text_img(lab, SERIF, 44, DUAN if ph < 5 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('公元一〇五〇年', SERIF, 42, XUAN, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_b_uncle(A, cv, t, u):
    desk(A, 540, GROUND, 360, layer='xuan')
    ground(A, GROUND)
    bao(A, 540, GROUND - 40, 210, dir=1, arm=lerp(30, 140, ease_out((u - P) / 0.5)))
    person(A, 240, GROUND, 170, dir=1, robe=True, hat='none', kneel=True, bow=30, arm=110, layer='mid')
    A.flush(cv)
    stamp(cv, seal('庐州', 54), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('舅父犯法 依法杖责', SERIF, 48, DUAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_b_chizhou(A, cv, t, u):
    A.d['ocean'].ellipse((160, 1240, 920, 1380), fill=150)
    ground(A, GROUND, x0=60, x1=200)
    bao(A, lerp(600, 260, ease_out(u / (2.5 * P))), GROUND, 200, dir=-1, ph=t * 3, arm=-8)
    A.flush(cv)
    stamp(cv, seal('池州', 54), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('因言获罪 · 外放地方', SERIF, 46, XUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_jiangning(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='江宁', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(5):
        person(A, 160 + k * 180, GROUND, 120, dir=1 if k % 2 else -1, robe=False, hat='knot', ph=t * 3 + k, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('江宁府', 50), 860, 880, t, t - u + P, rot=6)

def art_b_kaifeng(A, cv, t, u):
    """8-beat set piece: 开封府 — the side gate where clerks took bribes is shut; the main gate opens; the people walk in
    and kneel straight before him; the saying 关节不到 有阎罗包老 rings out."""
    ph = u / P
    A.d['xuan'].rectangle((140, 900, 940, GROUND), fill=200)
    A.d['ink'].polygon([(110, 900), (970, 900), (540, 800)], fill=255)
    gate = ease_out((ph - 1) / 1.2)
    A.d['ink'].rectangle((420, 1080, 420 + 100 * (1 - gate), GROUND), fill=255)
    A.d['ink'].rectangle((660 - 100 * (1 - gate), 1080, 660, GROUND), fill=255)
    A.d['ink'].rectangle((820, 1180, 880, GROUND), fill=255 if ph > 0.8 else 120)
    ground(A, GROUND)
    n = int(clamp((ph - 2) / 3) * 8)
    for k in range(n):
        x = lerp(1100, 470 + (k % 4) * 40, ease_out((ph - 2 - k * 0.2) / 1.5)); y = GROUND - (k // 4) * 30
        person(A, x, y, 110, dir=-1, robe=False, hat='knot', kneel=ph > 5, bow=40 if ph > 5 else 0, ph=t * 4 + k, arm=100 if ph > 5 else 20, layer='mid')
    bao(A, 540, 1060, 150, dir=1, arm=40)
    A.flush(cv)
    stamp(cv, seal('权知开封府', 40), 860, 860, t, t - u + 0.4, rot=6)
    if ph >= 1:
        paste(cv, text_img('大开正门 · 百姓直诉', SERIF, 46, DUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp((ph - 1) / 0.3))
    if ph >= 5.5:
        type_in(cv, text_img('关节不到 有阎罗包老', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + 5.5 * P, 0.5)

def art_b_smile(A, cv, t, u):
    ground(A, GROUND)
    bao(A, 540, GROUND, 270, dir=1, arm=-8)
    for k in range(6):
        y = 860 + k * 30
        A.d['ocean'].line((700, y, 960, y + 20 * math.sin(t + k)), fill=120, width=3)
    A.flush(cv)
    paste(cv, text_img('包公笑比黄河清', SERIF, 50, XUAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 包青天
def art_b_huimin(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=5, speed=1.6)
    for k in range(3):
        A.d['mid'].rectangle((200 + k * 240, 1100, 320 + k * 240, 1240), fill=230)
        A.d['ink'].polygon([(180 + k * 240, 1100), (340 + k * 240, 1100), (260 + k * 240, 1040)], fill=255)
        if u > (1 + k * 0.5) * P:
            A.d['red'].line((180 + k * 240, 1040, 340 + k * 240, 1240), fill=255, width=8)
    ground(A, 1240, x0=60, x1=W - 60)
    A.flush(cv)
    stamp(cv, seal('惠民河', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('权贵园亭堵塞河道 · 尽数拆除', SERIF, 42, DUAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_b_zhongcheng(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='xuan')
    ground(A, GROUND)
    bao(A, 540, GROUND, 250, dir=1, arm=lerp(40, 150, ease_out(u / P)))
    A.flush(cv)
    stamp(cv, seal('御史中丞', 46), 860, 880, t, t - u + P, rot=6)

def art_b_sansi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='duan')
    for k in range(int(clamp(u / (2 * P)) * 10)):
        A.d['gold'].ellipse((340 + (k % 5) * 80, GROUND - 100 - (k // 5) * 30, 380 + (k % 5) * 80, GROUND - 76 - (k // 5) * 30), fill=255)
    bao(A, 860, GROUND, 210, dir=-1, arm=60)
    A.flush(cv)
    stamp(cv, seal('三司使', 50), 260, 880, t, t - u + P, rot=-5)
    paste(cv, text_img('掌天下财赋', SERIF, 48, DUAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_b_shumi(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='duan')
    ground(A, GROUND)
    bao(A, 540, GROUND, 240, dir=1, arm=40, old=0.6)
    for k in range(4):
        person(A, 160 + k * 60 if k < 2 else 820 + (k - 2) * 60, GROUND, 150, dir=1 if k < 2 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    A.flush(cv)
    stamp(cv, seal('枢密副使', 44), 860, 880, t, t - u + P, rot=6)

def art_b_jiaxun(A, cv, t, u):
    """6-beat set piece: 家训 — a stone tablet; characters are chiselled in, line by line."""
    ph = u / P
    stele(A, 540, GROUND, 360, 480)
    ground(A, GROUND)
    for k in range(3):
        x = 860 + k * 50
        person(A, x, GROUND, 120 - k * 15, dir=-1, robe=True, hat='knot', bow=20, arm=-8, layer='mid')
    A.flush(cv)
    lines = ['后世子孙仕宦', '有犯赃滥者', '不得放归本家', '亡殁之后', '不得葬于大茔']
    for i, ln in enumerate(lines):
        type_in(cv, text_img(ln, SERIF, 34, (250, 246, 236), 'Black', bleed=False, vertical=True, spacing=2), 640 - i * 50, GROUND - 280, t, t - u + 0.3 + i * 0.8 * P, 0.4)
    if ph >= 4.5:
        paste(cv, text_img('不从吾志 非吾子孙', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - 4.5) / 0.3))

def art_b_plain(A, cv, t, u):
    A.d['xuan'].rectangle((300, 1060, 780, GROUND), fill=200)
    A.d['ink'].polygon([(270, 1060), (810, 1060), (540, 960)], fill=255)
    ground(A, GROUND)
    bao(A, 540, GROUND, 200, dir=1, arm=-8, old=0.7)
    A.flush(cv)
    paste(cv, text_img('虽贵 衣服器用饮食 如布衣时', SERIF, 42, XUAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_b_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    bao(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('病逝开封 · 年六十三', SERIF, 48, DUAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第五回 身后千年
def art_b_xiaosu(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 220, dir=1, robe=True, hat='crown', bow=30, arm=-8, layer='ink')
    for k in range(40):
        q = (t * 0.3 + k / 40) % 1
        A.d['wash'].ellipse((80 + (k * 23) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 23) % 920 + 4, lerp(620, 1420, q) + 4), fill=200)
    A.flush(cv)
    stamp(cv, seal('孝肃', 60), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('仁宗亲往吊唁 · 辍朝一日', SERIF, 44, XUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_tablet(A, cv, t, u):
    stele(A, 540, GROUND, 520, 420, layer='mid')
    for r in range(5):
        for c2 in range(8):
            x = 330 + c2 * 60; y = GROUND - 380 + r * 70
            A.d['ink'].rectangle((x - 20, y, x + 20, y + 14), fill=150)
    p = 0.5 + 0.5 * math.sin(t * 3)
    A.d['wash'].ellipse((480, GROUND - 240, 560, GROUND - 200), fill=255)
    person(A, 860, GROUND, 160, dir=-1, robe=True, hat='knot', arm=lerp(80, 150, p), layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('传说', 44, INK), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('题名碑上 他的名字被摸平', SERIF, 44, DUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_opera(A, cv, t, u):
    A.d['red'].rectangle((160, 860, 920, 900), fill=255)
    A.d['mid'].rectangle((180, 900, 900, GROUND - 60), fill=200)
    ground(A, GROUND)
    bao(A, 540, GROUND - 60, 260, dir=1, arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 3)))
    for k in range(10):
        A.d['ink'].ellipse((140 + k * 82, GROUND - 30, 180 + k * 82, GROUND + 10), fill=255)
    A.flush(cv)
    paste(cv, text_img('元杂剧 · 包公戏', SERIF, 48, XUAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_b_zhamei(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((300, GROUND - 80, 780, GROUND - 40), fill=255)
    A.d['blade'].polygon([(320, GROUND - 80), (760, GROUND - 80), (760, GROUND - 120 - 60 * abs(math.sin(t * 2))), (320, GROUND - 100)], fill=255)
    A.d['gold'].ellipse((300, GROUND - 120, 340, GROUND - 80), fill=255)
    bao(A, 880, GROUND, 230, dir=-1, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('戏曲故事', 40, INK), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('铡美案 · 并非史实', SERIF, 48, DUAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_b_temple(A, cv, t, u):
    A.d['ocean'].ellipse((100, 1260, 980, 1400), fill=150)
    palace(A, 540, 1240, 420, layer='xuan')
    ground(A, GROUND, x0=60, x1=200)
    A.flush(cv)
    stamp(cv, seal('包公祠', 54), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('合肥 包河之畔', SERIF, 48, XUAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_b_qingtian(A, cv, t, u):
    for k in range(10):
        a = k * 2 * math.pi / 10 + t * 0.2
        person(A, 540 + 330 * math.cos(a), 1240 + 40 * math.sin(a), 110, dir=1 if math.cos(a) < 0 else -1, robe=True, hat='knot', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 2 + k)), layer='mid')
    bao(A, 540, 1240, 260, dir=1, arm=40)
    ground(A, 1240)
    A.flush(cv)
    ink_in(cv, text_img('包青天', BRUSH, 120, XUAN), W / 2, 880, t, t - u + 0.5, dur=0.3, settle=1.2)

def art_b_legacy(A, cv, t, u):
    inkstone(A, 540, 1200, 220, depth=0.8, t=t)
    ground(A, GROUND)

def art_b_title(A, cv, t, u):
    desk(A, 820, 1460, 360, layer='xuan')
    inkstone(A, 820, 1370, 70, depth=0.6, t=t)
    bao(A, 400, 1460, 700, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '孝子为先'), 48: ('第二回', '不持一砚'), 80: ('第三回', '犯颜直谏'),
            112: ('第四回', '包青天'), 144: ('第五回', '身后千年')}

CARDS = [
    C(0, 2, 'hook', 'num', num='黑脸包公', line='史书从未说他脸黑', art=art_b_hook_face),
    C(2, 4, 'court', 'num', num='关节不到', line='有阎罗包老', art=art_b_hook_yanluo),
    C(4, 6, 'works', 'num', num='三年端州', line='不持一砚归', art=art_b_hook_yan),
    C(6, 8, 'death', 'num', num='一条家训', line='贪官不入祖坟', art=art_b_hook_rule),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 孝子为先
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=999, main='生于合肥', sub='庐州合肥 · 小户人家', art=art_b_hefei),
    C(22, 26, 'works', 'card', year=1015, main='苦读', sub='少以孝闻', art=art_b_study),
    C(26, 30, 'empire', 'card', year=1027, main='进士及第', sub='二十八岁 · 金榜题名', art=art_b_jinshi),
    C(30, 34, 'life', 'card', year=1027, main='辞官养亲', sub='授官不赴 · 回家奉养父母', art=art_b_parents),
    C(34, 38, 'death', 'card', year=1036, main='守墓', sub='父母相继去世', note='庐墓终丧 犹徘徊不忍去', art=art_b_mourn),
    C(38, 44, 'night', 'card', year=1037, main='牛舌案', sub='知天长县', note='宋史所载', art=art_b_tongue),
    C(44, 48, 'works', 'card', year=1040, main='知端州', sub='岭南出名砚之地', art=art_b_duanzhou),
    # ---- 第二回 不持一砚
    C(48, 50, 'works', 'chapter'),
    C(50, 56, 'works', 'card', year=1041, main='不持一砚', sub='只按贡数上缴', art=art_b_tribute),
    C(56, 60, 'fate', 'card', year=1042, main='掷砚成洲', sub='离任时发现船上有砚', note='传说 扔进江中', art=art_b_throw),
    C(60, 64, 'court', 'card', year=1043, main='监察御史', sub='入京任言官', art=art_b_censor),
    C(64, 68, 'war', 'card', year=1044, main='出使契丹', sub='辽人诘难 · 一一驳回', art=art_b_khitan),
    C(68, 72, 'war', 'card', year=1046, main='七弹王逵', sub='酷吏王逵 · 连劾七次', art=art_b_wangkui),
    C(72, 76, 'works', 'card', year=1048, main='改革盐法', sub='主管户部财计', art=art_b_salt),
    C(76, 80, 'court', 'card', year=1049, main='知谏院', sub='专司进谏', art=art_b_jianguan),
    # ---- 第三回 犯颜直谏
    C(80, 82, 'war', 'chapter'),
    C(82, 90, 'war', 'tanhe', year=1050),
    C(90, 94, 'life', 'card', year=1052, main='不徇私情', sub='知庐州 · 家乡亲戚犯法', art=art_b_uncle),
    C(94, 98, 'fate', 'card', year=1054, main='知池州', sub='几经沉浮', art=art_b_chizhou),
    C(98, 102, 'court', 'card', year=1055, main='知江宁', sub='所到之处 吏治肃然', art=art_b_jiangning),
    C(102, 110, 'empire', 'card', year=1056, main='开封府', sub='京城最难当的官', art=art_b_kaifeng),
    C(110, 112, 'night', 'card', year=1056, main='笑比河清', sub='人称其笑难得一见', art=art_b_smile),
    # ---- 第四回 包青天
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'works', 'card', year=1057, main='疏通惠民河', sub='不避权贵', art=art_b_huimin),
    C(118, 122, 'court', 'card', year=1058, main='御史中丞', sub='百官之首的监察者', art=art_b_zhongcheng),
    C(122, 126, 'works', 'card', year=1059, main='三司使', sub='主管国家财政', art=art_b_sansi),
    C(126, 130, 'empire', 'card', year=1061, main='枢密副使', sub='官至副相', art=art_b_shumi),
    C(130, 136, 'night', 'card', year=1061, main='家训', sub='三十七字 · 刻石立于堂屋', note='作年不详', art=art_b_jiaxun),
    C(136, 140, 'life', 'card', year=1061, main='一生清贫', sub='身居高位 生活如常', art=art_b_plain),
    C(140, 144, 'death', 'card', year=1062, main='病逝', sub='卒于任上', art=art_b_death),
    # ---- 第五回 身后千年
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'court', 'card', year=1062, main='谥孝肃', sub='赠礼部尚书', art=art_b_xiaosu),
    C(150, 154, 'fate', 'card', year=1100, main='题名碑', sub='开封府题名记碑', art=art_b_tablet),
    C(154, 158, 'works', 'card', year=1300, main='包公戏', sub='元代杂剧 · 断案如神', art=art_b_opera),
    C(158, 162, 'night', 'card', year=1800, main='铡美案', sub='清代京剧 · 包公形象定型', art=art_b_zhamei),
    C(162, 166, 'life', 'card', year=1882, main='包公祠', sub='合肥重修', art=art_b_temple),
    C(166, 170, 'end', 'card', year=2026, main='包青天', sub='清官的代名词', art=art_b_qingtian),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='叁拾柒', col=XUAN, acc=DUAN, born=999, died=1062, age0=999.3,
    hook_q='真实的包拯 · 和戏里一样吗？',
    name_line='包拯 · 字希仁', name='包拯', seal='孝肃', title_art=art_b_title,
    q1='铁面无私？', q2='被神化了？',
    end_art=art_b_legacy, end_big='包青天', end_seal='孝肃',
    end_l1='他没有铡过驸马', end_l2='却让一千年的百姓相信有清官',
    end_brush='关节不到', end_ask='你心中的清官是谁？评论区聊聊', next='范仲淹'),
    scenes=dict(chapter=scene_chapter, tanhe=scene_tanhe))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
