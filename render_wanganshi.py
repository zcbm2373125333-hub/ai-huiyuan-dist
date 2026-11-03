"""千古人物志 · 第叁拾陆集 · 王安石 (1021–1086)
Look: 春草绿 + 梅花红, 梅枝 corner borders, a 江南岸 chapter card: the far bank greens a little more each chapter
("春风又绿江南岸"), then turns autumn-grey in the last.
Set pieces: 6-beat 万言书, custom 8-beat scene 'xinfa' (six new laws, one panel per law), 6-beat 钟山骑驴.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_xinqiji as Xq         # engine + helpers (previous episode)
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

F.RIPPLE = False
CHUN = (92, 146, 78)                # 春草绿
MEI = (190, 58, 72)                 # 梅花红
S.LAYERS.append(('chun', CHUN, 0.88, 1.0))
S.LAYERS.append(('mei', MEI, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='变', life='安', court='宋', night='夜', war='争', empire='宋', works='法', fate='拗', death='梅', end='变')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court', 'empire'):
    G.THEMES[k]['part'] = 'petal'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (CHUN, 220, (W * 0.5, 820))
G.THEMES['war']['sun'] = (MEI, 220, (W * 0.5, 760))
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (CHUN, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

PLUM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(PLUM)
_r = random.Random(36)
for _x, _s in ((70, 1), (W - 70, -1)):
    _pts = [(_x, 1500), (_x + _s * 30, 1380), (_x + _s * 10, 1290), (_x + _s * 60, 1210)]
    _d.line(_pts, fill=(60, 50, 50, 60), width=8)
    for _k in range(8):
        _px, _py = _x + _s * _r.uniform(0, 70), _r.uniform(1200, 1400)
        _d.ellipse((_px - 7, _py - 7, _px + 7, _py + 7), fill=MEI + (70,))
MTN_COL = {'night': (36, 40, 38), 'death': (62, 60, 60), 'war': (96, 64, 56), 'fate': (86, 96, 86)}
def draw_background(t, theme):
    """钟山: low ridges, an old plum leaning in at each margin."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 192, 180), (146, 162, 138), MTN_COL.get(theme, (104, 124, 98))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(PLUM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """梅枝: a crooked plum twig with three blossoms in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=CHUN + (200,), width=3); d.line((x, y, x, y + sy * 180), fill=CHUN + (200,), width=3)
        pts = [(x + sx * 10, y + sy * 10), (x + sx * 50, y + sy * 30), (x + sx * 70, y + sy * 70), (x + sx * 110, y + sy * 90)]
        d.line(pts, fill=(60, 50, 50, 230), width=4)
        for (u, v) in ((50, 30), (70, 70), (110, 90)):
            cx, cy = x + sx * u, y + sy * v
            for k in range(5):
                a = k * 2 * math.pi / 5
                d.ellipse((cx + 7 * math.cos(a) - 5, cy + 7 * math.sin(a) - 5, cx + 7 * math.cos(a) + 5, cy + 7 * math.sin(a) + 5), fill=MEI + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def wang(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """王安石: official 幞头 with long wings, dark face, rumpled robe, short beard."""
    b = bow + 12 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.065 * h, y - 1.05 * h, x + 0.065 * h, y - 0.94 * h), fill=255)
        d.rectangle((x - 0.24 * h, y - 1.0 * h, x + 0.24 * h, y - 0.985 * h), fill=255)
        d.polygon([(x + dir * 0.0, y - 0.86 * h), (x + dir * 0.08 * h, y - 0.86 * h), (x + dir * 0.04 * h, y - 0.74 * h)], fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.01 * h, y - 0.84 * h), (x + dir * 0.07 * h, y - 0.84 * h), (x + dir * 0.04 * h, y - 0.76 * h)], fill=255)
    return hand

def donkey(A, x, y, s, dir=1, ph=0.0, moving=True, layer='ink'):
    d = A.d[layer]
    def T(u, v): return (x + dir * u * s, y - v * s)
    d.polygon([T(*p) for p in ellipse_pts(0, 0.5, 0.38, 0.15)], fill=255)
    d.polygon([T(0.3, 0.55), T(0.5, 0.82), T(0.6, 0.78), T(0.42, 0.5)], fill=255)
    d.polygon([T(0.5, 0.82), T(0.75, 0.74), T(0.72, 0.66), T(0.5, 0.7)], fill=255)
    d.line([T(0.52, 0.84), T(0.5, 1.02)], fill=255, width=max(2, int(0.04 * s)))
    d.line([T(0.57, 0.84), T(0.6, 1.0)], fill=255, width=max(2, int(0.04 * s)))
    for k, off in enumerate((0, 1.7, 3.1, 4.6)):
        a = 0.3 * math.sin(ph + off) if moving else 0
        hu = -0.28 + 0.52 * (k // 2) + 0.04 * (k % 2)
        d.line([T(hu, 0.4), T(hu + 0.12 * math.sin(a), 0.0)], fill=255, width=max(2, int(0.04 * s)))
    d.line([T(-0.38, 0.55), T(-0.48, 0.3)], fill=255, width=max(2, int(0.02 * s)))

def bank(A, y, green, t, layer_far='chun'):
    """the 江南 far bank: a strip whose greenness (0..1) grows."""
    pts = [(x, y - 30 * math.sin(x / 140) - 10 * math.sin(x / 37)) for x in range(60, W - 59, 12)]
    A.d['mid'].polygon(pts + [(W - 60, y + 40), (60, y + 40)], fill=200)
    if green > 0:
        A.d[layer_far].polygon(pts + [(W - 60, y + 40), (60, y + 40)], fill=int(250 * green))
        for k in range(int(green * 30)):
            gx = 80 + (k * 31) % 920; gy = y - 30 * math.sin(gx / 140)
            A.d[layer_far].line((gx, gy, gx + 4 * math.sin(t + k), gy - 30 - (k % 3) * 10), fill=255, width=3)

# ================================================================ chapter card
CH = {16: 0.15, 48: 0.4, 80: 0.7, 112: 1.0, 144: -1}
def art_bank_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g = CH.get(kb, 0.4)
    A.d['ocean'].rectangle((60, 1040, W - 60, 1170), fill=120)
    waves(A, 1050, t, rows=2, amp=4, speed=1.0)
    q = ease_out(u / (1.2 * P))
    if g >= 0:
        bank(A, 1000, lerp(max(0, g - 0.25), g, q), t)
    else:
        bank(A, 1000, 0.0, t)
        for k in range(30):
            qq = (t * 0.4 + k / 30) % 1
            A.d['wash'].ellipse((80 + (k * 37) % 920 - 4, lerp(620, 1300, qq) - 4, 80 + (k * 37) % 920 + 4, lerp(620, 1300, qq) + 4), fill=220)
    boat(A, 540, 1130, 80, t, sail=True)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_bank_chapter)
    ink_in(cv, text_img(no, SERIF, 56, CHUN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_w_hook_900(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        person(A, 160 + k * 70, GROUND, 150, dir=1, robe=True, hat='none', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='chun')
        person(A, 920 - k * 70, GROUND, 150, dir=-1, robe=True, hat='none', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 4 + k + 1)), layer='mei')
    wang(A, 540, GROUND, 260, dir=1, arm=-8)

def art_w_hook_three(A, cv, t, u):
    for k in range(40):
        q = (t * 0.6 + k / 40) % 1
        A.d['wash'].line((80 + (k * 23) % 920, lerp(620, 1420, q), 76 + (k * 23) % 920, lerp(620, 1420, q) + 24), fill=180, width=2)
    if int(t * 3) % 4 == 0:
        A.d['wash'].line((760, 640, 700, 800, 740, 820, 680, 980), fill=255, width=8)
    ground(A, GROUND)
    wang(A, 420, GROUND, 280, dir=1, arm=lerp(40, 160, ease_out(u / (1.2 * P))))

def art_w_hook_two(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    wang(A, lerp(540, 120, ease_out(u / (1.6 * P))), GROUND, 230, dir=-1, ph=t * 4, arm=-8)

def art_w_hook_lv(A, cv, t, u):
    river(A, 1180, t, rows=3, amp=4)
    bank(A, 1120, ease_out(u / (1.6 * P)), t)

# ================================================================ 第一回 临川少年
def art_w_linchuan(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['chun'].polygon([(x - 200, GROUND), (x, GROUND - 300 - 60 * (k % 2)), (x + 200, GROUND)], fill=170)
    A.d['ocean'].line([(60, 1340), (540, 1300), (1020, 1340)], fill=150, width=24)
    ground(A, GROUND)
    person(A, 420, GROUND, 230, dir=1, robe=True, hat='none', arm=40, layer='ink')
    person(A, 560, GROUND, 120, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('临川', 56), 860, 880, t, t - u + P, rot=6)

def art_w_travel(A, cv, t, u):
    pts = [(lerp(120, 960, f), 1200 + 80 * math.sin(f * 7)) for f in np.linspace(0, 1, 30)]
    A.d['mei'].line(pts, fill=200, width=6)
    i = min(len(pts) - 1, int(clamp(u / (3 * P)) * (len(pts) - 1)))
    carriage(A, pts[i][0], pts[i][1], 80, dir=1, wheel=u * 6, ph=t * 8, moving=True, layer='ink')
    for k, (nm, f) in enumerate((('韶州', 0.25), ('江宁', 0.6), ('开封', 0.9))):
        j = int(f * (len(pts) - 1))
        A.d['ink'].rectangle((pts[j][0] - 10, pts[j][1] - 50, pts[j][0] + 10, pts[j][1] - 30), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    for k, (nm, f) in enumerate((('韶州', 0.25), ('江宁', 0.6), ('开封', 0.9))):
        j = int(f * (len(pts) - 1))
        if u > f * 3 * P:
            stamp(cv, seal(nm, 30, CHUN), pts[j][0], pts[j][1] - 90, t, t - u + f * 3 * P)

def art_w_father(A, cv, t, u):
    A.d['mid'].chord((380, 1200, 700, GROUND + 160), 180, 360, fill=230)
    ground(A, GROUND)
    for k in range(3):
        person(A, 760 + k * 70, GROUND, 170 - k * 15, dir=-1, robe=True, hat='knot', kneel=True, bow=50, arm=100, layer='ink')
    A.flush(cv)
    stamp(cv, seal('王益', 50, INK), 540, 1100, t, t - u + P)
    paste(cv, text_img('家贫 奋发苦读', SERIF, 48, CHUN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_w_jinshi(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='chun')
    ground(A, GROUND)
    wang(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 30, ease_out(u / 0.6)))
    A.d['yellow'].rectangle((240, 860, 840, 920), fill=255)
    A.flush(cv)
    stamp(cv, seal('第四名', 50), 860, 980, t, t - u + P, rot=6)

def art_w_yinxian(A, cv, t, u):
    A.d['ocean'].polygon([(60, 1280), (W - 60, 1240), (W - 60, GROUND), (60, GROUND)], fill=150)
    for k in range(int(clamp(u / (2.5 * P)) * 6)):
        A.d['mid'].rectangle((140 + k * 140, 1250 - k * 6, 230 + k * 140, 1290 - k * 6), fill=230)
    ground(A, GROUND, x0=60, x1=420)
    wang(A, 260, GROUND, 200, dir=1, arm=60)
    for k in range(3):
        person(A, 120 + k * 50, GROUND, 120, dir=1, robe=False, hat='knot', load=True, arm=160, ph=t * 6 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('鄞县', 54), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('兴修水利 贷谷与民', SERIF, 46, CHUN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_w_shuzhou(A, cv, t, u):
    for k in range(10):
        x = 100 + k * 92
        A.d['chun'].rectangle((x, GROUND - 70 - 20 * (k % 3), x + 70, GROUND), fill=200)
    ground(A, GROUND)
    wang(A, 540, GROUND, 220, dir=1, arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t)))
    x = lerp(1100, 800, ease_out(u / (1.5 * P)))
    rider(A, x, GROUND, 130, -1, t * 10, layer='mid', moving=u < 1.5 * P)
    A.flush(cv)
    stamp(cv, seal('舒州', 54), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('屡召不赴京城', SERIF, 48, MEI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_w_unwashed(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 360, layer='chun')
    sitter(A, 320, GROUND, 220, dir=1, bow=25)
    for k in range(int(clamp(u / (2 * P)) * 10)):
        bundle(A, 440 + (k % 5) * 50, GROUND - 74 - (k // 5) * 30, 40, layer='mei' if k % 2 else 'mid')
    for k in range(4):
        A.d['ink'].ellipse((300 + k * 16, GROUND - 230 - 8 * k, 308 + k * 16, GROUND - 222 - 8 * k), fill=180)
    A.flush(cv)
    stamp(cv, seal('传说', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('读书忘洗脸 衣服不换', SERIF, 46, CHUN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第二回 万言书
def art_w_wanyan(A, cv, t, u):
    """6-beat set piece: 上仁宗皇帝言事书 — the scroll unrolls across the screen as a counter climbs to 一万; the emperor
    glances, sets it aside."""
    ph = u / P
    w = lerp(100, 860, ease_out(ph / 3.5))
    scroll(A, 540, 1040, w, 220, 1.0, layer='wash')
    for k in range(int(w / 22)):
        x = 540 - w / 2 + 14 + k * 22
        for j in range(6):
            A.d['ink'].rectangle((x, 950 + j * 30, x + 8, 966 + j * 30), fill=120)
    ground(A, GROUND)
    wang(A, 200, GROUND, 200, dir=1, kneel=True, bow=30, arm=100)
    if ph >= 4:
        person(A, 860, GROUND - 20, 210, dir=-1, robe=True, hat='crown', arm=lerp(60, 10, ease_out((ph - 4) / 1)), layer='ink')
    A.flush(cv)
    n = int(lerp(100, 10000, ease_out(ph / 3.5)))
    paste(cv, text_img(f'{n} 字' if n < 10000 else '洋洋万言', SERIF, 50, MEI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('仁宗未予理会', SERIF, 46, DIM, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((ph - 4.5) / 0.3))

def art_w_ignored(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    for k in range(int(clamp(u / (2 * P)) * 12)):
        A.d['wash'].rectangle((300 + (k % 6) * 80, 1240 - (k // 6) * 30, 360 + (k % 6) * 80, 1262 - (k // 6) * 30), fill=255)
        A.d['ink'].rectangle((300 + (k % 6) * 80, 1240 - (k // 6) * 30, 360 + (k % 6) * 80, 1262 - (k // 6) * 30), outline=120, width=1)
    A.flush(cv)
    stamp(cv, seal('束之高阁', 46, INK), 860, 880, t, t - u + P, rot=6)

def art_w_mourn(A, cv, t, u):
    A.d['mid'].chord((380, 1200, 700, GROUND + 160), 180, 360, fill=230)
    for k in range(30):
        q = (t * 0.3 + k / 30) % 1
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 37) % 920 + 4, lerp(620, 1420, q) + 4), fill=200)
    ground(A, GROUND)
    wang(A, 860, GROUND, 200, dir=-1, kneel=True, bow=45, arm=100)
    A.flush(cv)
    stamp(cv, seal('母丧', 54, INK), 540, 1100, t, t - u + P)
    paste(cv, text_img('归江宁守制 · 开门讲学', SERIF, 44, CHUN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_w_refuse(A, cv, t, u):
    ground(A, GROUND)
    A.d['chun'].rectangle((140, 1060, 440, GROUND), fill=200)
    A.d['ink'].polygon([(120, 1060), (460, 1060), (290, 980)], fill=255)
    n = int(clamp(u / (2.5 * P)) * 5)
    for k in range(n):
        rider(A, 700 + k * 80, GROUND, 110, -1, t * 5 + k, layer='mid', moving=False)
    wang(A, 540, GROUND, 210, dir=1, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    paste(cv, text_img(f'召而不起 第{cn_num(max(1, n))}次', SERIF, 48, MEI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)

def art_w_shenzong(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='chun')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 200, dir=1, robe=True, hat='crown', arm=lerp(20, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    for k in range(4):
        person(A, 160 + k * 60 if k < 2 else 820 + (k - 2) * 60, GROUND, 150, dir=1 if k < 2 else -1, robe=True, hat='none', kneel=True, bow=45, arm=100, layer='mid')
    A.flush(cv)
    stamp(cv, seal('宋神宗', 50), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('年方二十 · 一心富国强兵', SERIF, 44, CHUN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_audience(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 740, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 80, ease_out(u / P)), layer='ink')
    wang(A, 360, GROUND, 230, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    stamp(cv, seal('越次入对', 46), 260, 880, t, t - u + 0.4, rot=-5)
    type_in(cv, text_img('当法尧舜 何必唐太宗', SERIF, 46, MEI, 'Black', bleed=False, spacing=4), W / 2, 1448, t, t - u + P, 0.5)

def art_w_vice(A, cv, t, u):
    ground(A, GROUND)
    A.d['red'].rectangle((470, 880, 610, 1020), fill=255)
    A.d['wash'].rectangle((500, 910, 580, 990), fill=255)
    wang(A, 540, GROUND, 250, dir=1, arm=lerp(-8, 150, ease_out(u / (1.5 * P))))
    A.flush(cv)
    stamp(cv, seal('参知政事', 44), 840, 960, t, t - u + 1.5 * P, rot=6)

# ================================================================ 第三回 熙宁变法
def art_w_tiaoli(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='chun')
    for k in range(5):
        person(A, 300 + k * 120, GROUND, 150, dir=1 if k < 2 else -1, robe=True, hat='none', bow=10, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='ink' if k == 2 else 'mid')
    A.flush(cv)
    stamp(cv, seal('制置三司条例司', 30), 860, 880, t, t - u + P, rot=6)

LAWS = ['青苗法', '募役法', '保甲法', '方田均税', '市易法', '将兵法']
def scene_xinfa(cv, t, c, k):
    """8-beat custom scene: 熙宁新法 — a 2x3 grid of panels; one law per beat lights up with its own small picture
    and seal; the last beats show the whole grid at once."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    n = min(6, int(ph * 6 / 6) + 1)
    for i in range(6):
        cx = 220 + (i % 3) * 320; cy = 960 + (i // 3) * 300
        on = i < n
        A.d['chun' if on else 'mid'].rectangle((cx - 140, cy - 120, cx + 140, cy + 120), outline=255, width=6)
        if not on:
            continue
        q = ease_out((ph - i) / 0.8)
        if i == 0:
            for j in range(5):
                A.d['chun'].line((cx - 100 + j * 50, cy + 80, cx - 100 + j * 50, cy + 80 - 100 * q), fill=255, width=6)
            A.d['gold'].ellipse((cx - 30, cy - 90, cx + 30, cy - 50), fill=255)
        elif i == 1:
            for j in range(int(q * 6)):
                A.d['gold'].ellipse((cx - 90 + j * 34, cy - 10, cx - 66 + j * 34, cy + 14), fill=255)
            person(A, cx + 80, cy + 100, 90, dir=-1, robe=False, hat='knot', arm=60, layer='ink')
        elif i == 2:
            for j in range(5):
                person(A, cx - 100 + j * 50, cy + 100, 80, dir=1, robe=False, hat='knot', spear=True, arm=40, layer='ink')
        elif i == 3:
            for a in range(4):
                A.d['chun'].line((cx - 110, cy - 80 + a * 50, cx - 110 + 220 * q, cy - 80 + a * 50), fill=255, width=4)
                A.d['chun'].line((cx - 110 + a * 70, cy - 90, cx - 110 + a * 70, cy - 90 + 180 * q), fill=255, width=4)
        elif i == 4:
            A.d['ink'].line((cx, cy - 90, cx, cy + 90), fill=255, width=6)
            tilt = 0.25 * math.sin(t * 2)
            A.d['ink'].line((cx - 100, cy - 60 + 40 * tilt, cx + 100, cy - 60 - 40 * tilt), fill=255, width=6)
            A.d['mei'].ellipse((cx - 120, cy - 40 + 40 * tilt, cx - 80, cy + 0 + 40 * tilt), fill=255)
        else:
            flag(A, cx - 40, cy + 100, 200, t, w=70, layer='mei')
            for j in range(3):
                person(A, cx + 20 + j * 40, cy + 100, 80, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    for i in range(n):
        cx = 220 + (i % 3) * 320; cy = 960 + (i // 3) * 300
        stamp(cv, seal(LAWS[i], 28, MEI if i == n - 1 and ph < 6 else CHUN), cx, cy - 150, t, s0 + i * P)
    fx = Art()
    chars_in(cv, fx, '熙宁新法', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=69)
    fx.flush(cv)
    paste(cv, text_img('富国 强兵 · 抑制兼并', SERIF, 46, CHUN, 'Black', bleed=False, spacing=4), W / 2, 570, 1, 1)
    paste(cv, text_img('公元一〇六九年起 · 陆续推行', SERIF, 42, MEI, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_w_three_nots(A, cv, t, u):
    for k in range(40):
        q = (t * 0.8 + k / 40) % 1
        A.d['wash'].line((80 + (k * 23) % 920, lerp(620, 1420, q), 76 + (k * 23) % 920, lerp(620, 1420, q) + 24), fill=180, width=2)
    ground(A, GROUND)
    wang(A, 540, GROUND, 260, dir=1, arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    for i, ln in enumerate(('天变不足畏', '祖宗不足法', '人言不足恤')):
        type_in(cv, text_img(ln, SERIF, 42, MEI if i == 0 else INK, 'Black', bleed=False, vertical=True, spacing=4), 900 - i * 70, 980, t, t - u + 0.3 + i * 0.8 * P, 0.4)
    stamp(cv, seal('一说', 40, INK), 200, 880, t, t - u + 0.4, rot=-5)

def art_w_simaguang(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    wang(A, 330, GROUND, 230, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)))
    person(A, 750, GROUND, 230, dir=-1, robe=True, hat='none', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3 + 1.5)), layer='ink')
    A.d['ink'].rectangle((690, GROUND - 240, 810, GROUND - 228), fill=255)
    A.flush(cv)
    stamp(cv, seal('司马光', 50, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('三封书信 · 各不相让', SERIF, 46, CHUN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_w_chancellor(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='chun')
    ground(A, GROUND)
    wang(A, 540, GROUND, 250, dir=1, arm=40)
    for k in range(6):
        person(A, 120 + k * 60 if k < 3 else 780 + (k - 3) * 70, GROUND, 140, dir=1 if k < 3 else -1, robe=True, hat='none', bow=30, arm=90, layer='mid')
    A.flush(cv)
    stamp(cv, seal('同中书门下平章事', 30), 860, 880, t, t - u + P, rot=6)

def art_w_abuse(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 220, dir=-1, robe=True, hat='none', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    for k in range(4):
        person(A, 200 + k * 90, GROUND, 140, dir=1, robe=False, hat='knot', bow=40, arm=120, layer='mid')
    for k in range(int(clamp(u / (2 * P)) * 6)):
        A.d['gold'].ellipse((560 + k * 26, GROUND - 40, 584 + k * 26, GROUND - 16), fill=255)
    A.flush(cv)
    paste(cv, text_img('地方强行摊派 · 利息变高利', SERIF, 44, MEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_liumin(A, cv, t, u):
    """郑侠流民图: a scroll opens showing a line of starving refugees."""
    scroll(A, 540, 1040, 760, 260, u / (1.2 * P), layer='wash')
    p = ease_out(u / (1.2 * P))
    for k in range(int(p * 10)):
        person(A, 210 + k * 66, 1150, 90, dir=1, robe=False, hat='knot', bow=35, ph=t * 2 + k, arm=-8, layer='ink')
    A.flush(cv)
    stamp(cv, seal('流民图', 50, INK), 860, 860, t, t - u + P, rot=6)

# ================================================================ 第四回 两度罢相
def art_w_first_out(A, cv, t, u):
    palace(A, 760, GROUND, 400, layer='mid')
    ground(A, GROUND)
    wang(A, lerp(600, 200, ease_out(u / (2.5 * P))), GROUND, 220, dir=-1, ph=t * 4, arm=-8)
    A.flush(cv)
    stamp(cv, seal('罢相', 60, INK), 760, 860, t, t - u + 0.4, rot=6)
    paste(cv, text_img('知江宁府', SERIF, 48, CHUN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_w_back(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='chun')
    ground(A, GROUND)
    wang(A, lerp(-80, 540, ease_out(u / (2 * P))), GROUND, 230, dir=1, ph=t * 4 if u < 2 * P else None, arm=40)
    A.flush(cv)
    stamp(cv, seal('复相', 60), 860, 880, t, t - u + 2 * P, rot=6)

def art_w_guazhou(A, cv, t, u):
    """泊船瓜洲: the boat moored at 瓜洲; across the river 京口; the bright moon; the one changed word 绿 drops in."""
    moon_phase(A, 820, 780, 70, 1.0)
    river(A, 1180, t, rows=3, amp=4, speed=0.8)
    bank(A, 1120, ease_out((u - 2 * P) / P), t)
    boat(A, 300, 1250, 110, t, sail=False)
    wang(A, 300, 1220, 140, dir=1, arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t)))
    A.flush(cv)
    type_in(cv, text_img('春风又绿江南岸', SERIF, 50, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    if u > 1.5 * P:
        for i, w_ in enumerate(('到', '过', '入', '满')):
            paste(cv, text_img(w_, SERIF, 46, DIM, 'Black', bleed=False), 300 + i * 90, 920, 1, clamp(1 - (u - 1.5 * P - i * 0.1) / 0.4))
        ink_in(cv, text_img('绿', BRUSH, 120, CHUN), 760, 940, t, t - u + 2.2 * P, dur=0.3, settle=1.3)
    stamp(cv, seal('一说', 40, INK), 200, 1060, t, t - u + 0.4, rot=-5)

def art_w_son(A, cv, t, u):
    A.d['mid'].chord((380, 1200, 700, GROUND + 160), 180, 360, fill=230)
    for k in range(40):
        q = (t * 0.3 + k / 40) % 1
        A.d['wash'].ellipse((80 + (k * 23) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 23) % 920 + 4, lerp(620, 1420, q) + 4), fill=200)
    ground(A, GROUND)
    wang(A, 860, GROUND, 210, dir=-1, kneel=True, bow=50, arm=100)
    A.flush(cv)
    stamp(cv, seal('王雱', 54, INK), 540, 1100, t, t - u + P)
    paste(cv, text_img('爱子早逝 心灰意冷', SERIF, 48, MEI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_w_second_out(A, cv, t, u):
    palace(A, 760, GROUND, 400, layer='mid')
    ground(A, GROUND)
    wang(A, lerp(600, 160, ease_out(u / (3 * P))), GROUND, 210, dir=-1, ph=t * 3, arm=-8, old=0.5)
    A.flush(cv)
    stamp(cv, seal('再罢', 60, INK), 760, 860, t, t - u + 0.4, rot=6)
    paste(cv, text_img('从此不再回朝', SERIF, 48, CHUN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_w_zhongshan(A, cv, t, u):
    """6-beat set piece: 钟山骑驴 — the retired chancellor on a donkey, ambling the hill path; seasons pass; a temple."""
    ph = u / P
    A.d['mid'].polygon([(120, GROUND), (420, 900), (720, GROUND)], fill=210)
    A.d['chun'].polygon([(500, GROUND), (760, 960), (1000, GROUND)], fill=int(lerp(220, 100, clamp(ph / 6))))
    palace(A, 420, 940, 160, layer='ink')
    pts = [(lerp(120, 960, f), GROUND - 60 - 40 * math.sin(f * 6)) for f in np.linspace(0, 1, 30)]
    A.d['wash'].line(pts, fill=255, width=10)
    i = min(len(pts) - 1, int(clamp(ph / 5.5) * (len(pts) - 1)))
    x, y = pts[i]
    donkey(A, x, y, 120, dir=1, ph=t * 6)
    wang(A, x - 10, y - 70, 110, dir=1, arm=20, old=0.8)
    if ph > 3:
        for k in range(20):
            q = (t * 0.4 + k / 20) % 1
            A.d['mei'].ellipse((80 + (k * 47) % 920 - 5, lerp(620, 1300, q) - 3, 80 + (k * 47) % 920 + 5, lerp(620, 1300, q) + 3), fill=int(200 * (1 - q)))
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('半山园', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('骑驴游山 · 一住十年', SERIF, 46, CHUN, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 1) / 0.4))

def art_w_yuanfeng(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 210, dir=1, robe=True, hat='crown', arm=lerp(20, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    for k in range(4):
        rider(A, lerp(-200, 360, ease_out(u / (2 * P))) - k * 100, GROUND, 100, 1, t * 11 + k, layer='mid', spear=True)
    A.flush(cv)
    stamp(cv, seal('元丰改制', 44), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('神宗亲自主持 · 新法继续', SERIF, 44, CHUN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 晚岁钟山
def art_w_shenzong_dies(A, cv, t, u):
    for k in range(40):
        q = (t * 0.3 + k / 40) % 1
        A.d['wash'].ellipse((80 + (k * 23) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 23) % 920 + 4, lerp(620, 1420, q) + 4), fill=200)
    palace(A, 540, 1160, 540, layer='mid')
    ground(A, GROUND)
    A.d['ink'].rectangle((420, GROUND - 60, 660, GROUND - 40), fill=255)
    A.flush(cv)
    stamp(cv, seal('神宗崩', 54, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_w_repeal(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 30, 220, dir=1, robe=True, hat='none', arm=lerp(40, 160, ease_out(u / P)), layer='ink')
    for i, nm in enumerate(LAWS):
        x = 160 + i * 150
        q = ease_out((u - P - i * 0.12 * P) / 0.6)
        A.d['wash'].rectangle((x - 50, 900, x + 50, 980), fill=255)
        A.d['red'].line((x - 50, 900, x - 50 + 100 * q, 900 + 80 * q), fill=255, width=6)
    A.flush(cv)
    stamp(cv, seal('司马光', 46, INK), 860, 1060, t, t - u + 0.4, rot=6)
    paste(cv, text_img('元祐更化 · 新法尽废', SERIF, 46, MEI, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - 2 * P) / 0.3))

def art_w_yibazhi(A, cv, t, u):
    A.d['mid'].rectangle((240, 900, 840, GROUND), fill=180)
    lamp(A, 700, GROUND, 50, t, glow=0.5)
    ground(A, GROUND)
    sitter(A, 440, GROUND, 200, dir=1, bow=lerp(10, 45, ease_out((u - P) / P)))
    A.flush(cv)
    type_in(cv, text_img('亦罢至此乎', SERIF, 56, MEI, 'Black', bleed=False, spacing=10), W / 2, 830, t, t - u + 1.2 * P, 0.5)
    paste(cv, text_img('闻募役法也被废除', SERIF, 42, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp(u / 0.4))

def art_w_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    wang(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('钟山', 54), 300, 880, t, t - u + P, rot=-5)
    paste(cv, text_img('数月后病逝 · 年六十四', SERIF, 46, CHUN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_w_plum(A, cv, t, u):
    for k in range(50):
        q = (t * 0.5 + k / 50) % 1
        A.d['wash'].ellipse((80 + (k * 19) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 19) % 920 + 4, lerp(620, 1420, q) + 4), fill=230)
    A.d['mid'].rectangle((600, 900, 640, GROUND), fill=200)
    A.d['ink'].line((620, GROUND - 20, 520, 1160, 560, 1060, 470, 980), fill=255, width=10)
    for k in range(int(clamp(u / (2 * P)) * 9)):
        x = 470 + (k * 37) % 120; y = 980 + (k * 61) % 220
        A.d['mei'].ellipse((x - 14, y - 14, x + 14, y + 14), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    for i, ln in enumerate(('墙角数枝梅', '凌寒独自开', '遥知不是雪', '为有暗香来')):
        type_in(cv, text_img(ln, SERIF, 40, MEI if i == 3 else INK, 'Black', bleed=False, vertical=True, spacing=4), 340 - i * 62, 980, t, t - u + 0.3 + i * 0.5 * P, 0.4)
    stamp(cv, seal('作年不详', 36, INK), 860, 1080, t, t - u + 0.4, rot=6)

def art_w_niu(A, cv, t, u):
    ground(A, GROUND)
    wang(A, 540, GROUND, 260, dir=1, arm=-8, old=0.6)
    for k in range(3):
        person(A, 160 + k * 70, GROUND, 150, dir=1, robe=True, hat='none', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='mid')
        person(A, 920 - k * 70, GROUND, 150, dir=-1, robe=True, hat='none', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 5 + k + 2)), layer='mid')
    A.flush(cv)
    ink_in(cv, text_img('拗相公', BRUSH, 120, MEI), W / 2, 900, t, t - u + 0.5, dur=0.3, settle=1.2)
    paste(cv, text_img('南宋起 被归咎为祸国', SERIF, 44, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_w_reformer(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        x = 160 + k * 150
        A.d['chun' if k % 2 else 'mei'].rectangle((x - 50, GROUND - 80 - 40 * k * ease_out(u / (2 * P)), x + 50, GROUND), fill=220)
    A.flush(cv)
    paste(cv, text_img('后世重新评价 · 中国十一世纪的改革家', SERIF, 40, CHUN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('梁启超', 44, INK), 860, 960, t, t - u + P, rot=6)

def art_w_legacy(A, cv, t, u):
    river(A, 1420, t, rows=2, amp=4)
    bank(A, 1400, 1.0, t)

def art_w_title(A, cv, t, u):
    river(A, 1400, t, rows=2, amp=4)
    bank(A, 1340, 0.8, t)
    wang(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '临川少年'), 48: ('第二回', '万言书'), 80: ('第三回', '熙宁变法'),
            112: ('第四回', '两度罢相'), 144: ('第五回', '晚岁钟山')}

CARDS = [
    C(0, 2, 'war', 'num', num='九百年', line='还在争论他', art=art_w_hook_900),
    C(2, 4, 'night', 'num', num='三不足', line='天变不足畏', art=art_w_hook_three),
    C(4, 6, 'court', 'num', num='两次罢相', line='一意孤行', art=art_w_hook_two),
    C(6, 8, 'works', 'num', num='春风又绿', line='一个字改了十多次', art=art_w_hook_lv),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 临川少年
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1021, main='生于临江', sub='祖籍抚州临川', art=art_w_linchuan),
    C(22, 26, 'works', 'card', year=1030, main='随父宦游', sub='走遍南北 · 见识民间疾苦', art=art_w_travel),
    C(26, 30, 'death', 'card', year=1039, main='父亲去世', sub='家道中落', art=art_w_father),
    C(30, 34, 'empire', 'card', year=1042, main='进士及第', sub='庆历二年 · 进士及第', note='一说 本为第一 因用语不当降为第四', art=art_w_jinshi),
    C(34, 38, 'works', 'card', year=1047, main='鄞县知县', sub='试行贷谷 · 变法雏形', art=art_w_yinxian),
    C(38, 42, 'court', 'card', year=1051, main='甘守地方', sub='舒州通判', note='朝廷屡召 皆辞不就', art=art_w_shuzhou),
    C(42, 48, 'life', 'card', year=1056, main='不修边幅', sub='衣垢不浣 面垢不洗', note='传说', art=art_w_unwashed),
    # ---- 第二回 万言书
    C(48, 50, 'works', 'chapter'),
    C(50, 56, 'works', 'card', year=1058, main='万言书', sub='上仁宗皇帝言事书', note='指陈积弊 主张变法', art=art_w_wanyan),
    C(56, 60, 'court', 'card', year=1059, main='束之高阁', sub='朝廷不予采纳', art=art_w_ignored),
    C(60, 64, 'death', 'card', year=1063, main='母丧守制', sub='江宁讲学 · 声望日隆', art=art_w_mourn),
    C(64, 68, 'fate', 'card', year=1065, main='屡召不起', sub='英宗时多次征召', art=art_w_refuse),
    C(68, 72, 'empire', 'card', year=1067, main='神宗即位', sub='少年天子 · 锐意改革', art=art_w_shenzong),
    C(72, 76, 'court', 'card', year=1068, main='越次入对', sub='君臣相得', art=art_w_audience),
    C(76, 80, 'empire', 'card', year=1069, main='参知政事', sub='主持变法', art=art_w_vice),
    # ---- 第三回 熙宁变法
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'works', 'card', year=1069, main='条例司', sub='设立变法机构', art=art_w_tiaoli),
    C(86, 94, 'works', 'xinfa', year=1070),
    C(94, 98, 'night', 'card', year=1070, main='三不足', sub='反对者为他总结的三句话', art=art_w_three_nots),
    C(98, 102, 'war', 'card', year=1070, main='司马光', sub='昔日好友 · 变法死敌', note='答司马谏议书', art=art_w_simaguang),
    C(102, 106, 'empire', 'card', year=1070, main='拜相', sub='同中书门下平章事', art=art_w_chancellor),
    C(106, 110, 'night', 'card', year=1072, main='执行走样', sub='好法遇上坏吏', art=art_w_abuse),
    C(110, 112, 'death', 'card', year=1074, main='流民图', sub='郑侠绘图上奏', art=art_w_liumin),
    # ---- 第四回 两度罢相
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'court', 'card', year=1074, main='第一次罢相', sub='大旱 · 太后哭诉', art=art_w_first_out),
    C(118, 122, 'empire', 'card', year=1075, main='复相', sub='神宗再召', art=art_w_back),
    C(122, 126, 'works', 'card', year=1075, main='泊船瓜洲', sub='明月何时照我还', art=art_w_guazhou),
    C(126, 130, 'death', 'card', year=1076, main='爱子病逝', sub='长子王雱卒', art=art_w_son),
    C(130, 134, 'fate', 'card', year=1076, main='再度罢相', sub='退居江宁', art=art_w_second_out),
    C(134, 140, 'life', 'card', year=1077, main='钟山骑驴', sub='筑半山园', art=art_w_zhongshan),
    C(140, 144, 'court', 'card', year=1080, main='元丰改制', sub='新法仍在推行', art=art_w_yuanfeng),
    # ---- 第五回 晚岁钟山
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'death', 'card', year=1085, main='神宗驾崩', sub='最大的支持者离去', art=art_w_shenzong_dies),
    C(150, 154, 'war', 'card', year=1086, main='新法尽废', sub='司马光为相', art=art_w_repeal),
    C(154, 158, 'night', 'card', year=1086, main='亦罢至此', sub='闻之愕然', art=art_w_yibazhi),
    C(158, 162, 'death', 'card', year=1086, main='病逝钟山', sub='同年 司马光亦卒', art=art_w_death),
    C(162, 166, 'fate', 'card', year=1086, main='墙角梅', sub='凌寒独自开', art=art_w_plum),
    C(166, 168, 'court', 'card', year=1130, main='拗相公', sub='身后毁誉', art=art_w_niu),
    C(168, 170, 'end', 'card', year=1908, main='改革家', sub='梁启超为他作传', art=art_w_reformer),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='叁拾陆', col=CHUN, acc=MEI, born=1021, died=1086, age0=1021.9,
    hook_q='他想救大宋 · 为什么全天下都反对他？',
    name_line='王安石 · 字介甫', name='王安石', seal='半山', title_art=art_w_title,
    q1='改革先驱？', q2='祸国权臣？',
    end_art=art_w_legacy, end_big='春风又绿', end_seal='荆公',
    end_l1='他想一次改变整个大宋', end_l2='却在身后被全部推翻',
    end_brush='天变不足畏', end_ask='变法者 是对是错？评论区聊聊', next='包拯'),
    scenes=dict(chapter=scene_chapter, xinfa=scene_xinfa))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
