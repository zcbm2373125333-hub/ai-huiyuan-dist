# 千古人物志 · 第拾集 · 成吉思汗铁木真 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈，墨色最后绘制）。每一幕画面均为本集新画，不重复。
# 本集特色：草原长生天 —— 天蓝草绿 · 苏鲁锭章回卡（每回多立一杆）· 盘长结边角 · 八拍「班朱尼河盟誓」
#          · 六拍「斡难河称汗」 · 西征长图回顾
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_qianlong as Q         # engine + helpers (ink layers drawn last)
import render_yongzheng as Y
import render_kangxi as K
import render_mingtaizu as M
import render_songtaizu as St
import render_wuzetian as Z
import render_taizong as Tz
import render_wudi as Wd
import render_long as L
import render_gufeng as G
import render_story as S
import render_full as F
from render_gufeng import (W, H, FPS, bt, INK, ZHU, ZHE, BRUSH, SERIF, WILD, font, clamp, lerp, ease_out, ease_expo,
                           cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import (Art, person, horse, carriage, palace, flames, waves, boat, crow, arrow, flag, ground,
                          sun, walk_x, rotp, ellipse_pts, GROUND)
from render_full import chars_in, type_in, beat_fx
from render_long import C, rider, city_wall, note_in, stage, DIM, P
from render_mingtaizu import cn_year
from render_kangxi import rect, cannon
from render_qianlong import yurt, dome, camel
from render_wudi import camel

F.RIPPLE = False

BORN, DIED = 1162, 1227
END_BEAT = 170
SKY = (54, 104, 168)                # 长生天
GRASS = (88, 128, 64)
S.LAYERS.append(('sky', SKY, 0.80, 1.4))
S.LAYERS.append(('grass', GRASS, 0.80, 1.4))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

# ================================================================ episode look
WM = dict(hook='汗', life='狼', court='盟', night='夜', war='戰', empire='天', works='征', fate='落', death='葬', end='骄')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire', 'works'):
    G.THEMES[k]['part'] = 'dust'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = ((210, 160, 60), 260, (W * 0.5, 820))
G.THEMES['works']['sun'] = (ZHU, 230, (W * 0.5, 820))
G.THEMES['end']['sun'] = (SKY, 210, (W * 0.5, 720))
G.THEMES['hook']['tint'] = (0.97, 1.0, 1.03)
G.THEMES['life']['tint'] = (0.98, 1.01, 0.98)
for k in G.THEMES: G.THEMES[k]['mtn'] = min(G.THEMES[k]['mtn'], 0.45)
G.base_bg.cache_clear()

MTN_COL = {'night': (46, 54, 74), 'death': (64, 64, 70), 'war': (104, 72, 50), 'works': (120, 96, 60)}
HILLS = []
for i, (base, amp, rough) in enumerate(((1200, 46, 0.45), (1290, 36, 0.6), (1390, 28, 0.8))):
    ys = G.ridge(70 + i, base, amp, rough)
    mk = Image.new('L', (W + 400, H), 0)
    ImageDraw.Draw(mk).polygon([(0, H)] + [(x, ys[x]) for x in range(0, W + 400, 4)] + [(W + 399, H)], fill=255)
    HILLS.append(mk.filter(ImageFilter.GaussianBlur(3)))

def draw_background(t, theme):
    """草原: low rolling grass hills under a wide sky band."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    sky = Image.new('RGBA', (W, 520), SKY + (0,))
    a = np.linspace(46, 0, 520, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
    sky.putalpha(Image.fromarray(a.astype(np.uint8)))
    canvas.alpha_composite(sky, (0, 0))
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(170, 190, 160), (132, 160, 112), MTN_COL.get(theme, (96, 128, 74))]
    alphas = [110, 150, 200]
    for i, mk in enumerate(HILLS):
        off = int(200 + t * 10 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(mk.crop((off, 0, off + W, H)).point(lambda v, al=alphas[i]: int(v * al / 255)))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'dust':
        return Q.particle_sprite(kind, q)
    s = 36
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [(200, 170, 110), (170, 150, 110), (220, 200, 150)][q]
    d.ellipse((13, 13, 23, 23), fill=col + (170,))
    return im.filter(ImageFilter.GaussianBlur(1.2))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """盘长结 (endless knot) corners in sky blue."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = SKY + (210,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 160, y), fill=col, width=3); d.line((x, y, x, y + sy * 160), fill=col, width=3)
        cx, cy = x + sx * 40, y + sy * 40
        for k in range(3):
            o = -16 + k * 16
            d.line((cx - 24, cy + o, cx + 24, cy + o), fill=col, width=3)
            d.line((cx + o, cy - 24, cx + o, cy + 24), fill=col, width=3)
        for a0 in (0, 90, 180, 270):
            ox, oy = cx + 28 * math.cos(math.radians(a0)), cy + 28 * math.sin(math.radians(a0))
            d.ellipse((ox - 7, oy - 7, ox + 7, oy + 7), outline=col, width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ 苏鲁锭 chapter card
def sulde(A, x, base, h, t, p=1.0, layer='ink', white=True):
    """苏鲁锭: spear standard with a disk and long flowing horsehair tassels."""
    top = base - h * ease_out(p)
    A.d[layer].line((x, base, x, top), fill=255, width=8)
    if p < 0.6: return
    A.d[layer].polygon([(x - 12, top), (x + 12, top), (x, top - 70)], fill=255)
    A.d[layer].ellipse((x - 34, top + 10, x + 34, top + 28), fill=255)
    for k in range(12):
        sx = x - 28 + k * 5
        pts = [(sx + 30 * math.sin(t * 2.2 + k * 0.4 + j * 0.35) * j / 10 + j * 6, top + 26 + j * 22) for j in range(11)]
        A.d['wash' if white else 'ink'].line(pts, fill=255, width=4)

def art_sulde_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = {16: 1, 48: 2, 80: 3, 112: 4, 144: 5}.get(kb, 1)
    xs = [540] if n == 1 else [lerp(260, 820, i / (n - 1)) for i in range(n)]
    for i, x in enumerate(xs):
        sulde(A, x, 1200, 520 - abs(x - 540) * 0.2, t + i, p=clamp(u / 0.5 - i * 0.12))
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_sulde_chapter)
    ink_in(cv, text_img(no, SERIF, 56, SKY, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ primitives
def mongol(A, x, y, h, dir=1, layer='ink', **kw):
    person(A, x, y, h, dir=dir, robe=kw.pop('robe', True), hat='none', layer=layer, **kw)
    A.d[layer].chord((x - 0.09 * h, y - 1.0 * h, x + 0.09 * h, y - 0.86 * h), 180, 360, fill=255)
    A.d[layer].line((x - 0.11 * h, y - 0.93 * h, x + 0.11 * h, y - 0.93 * h), fill=255, width=max(2, int(0.03 * h)))

def stars(A, t, n=26, seed=1):
    r = random.Random(seed)
    for k in range(n):
        x = r.uniform(80, 1000); y = r.uniform(620, 980)
        tw = 3 + 2 * math.sin(t * 3 + k)
        A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)

def cangue(A, x, y, s, layer='ink'):
    A.d[layer].rectangle((x - s, y - s * 0.12, x + s, y + s * 0.12), fill=255)
    A.d['wash'].ellipse((x - s * 0.18, y - s * 0.1, x + s * 0.18, y + s * 0.1), fill=255)

def trebuchet(A, x, base, s, ph, layer='ink'):
    A.d[layer].polygon([(x - s * 0.5, base), (x + s * 0.5, base), (x + s * 0.06, base - s), (x - s * 0.06, base - s)], fill=255)
    a = math.radians(lerp(-60, 50, ph))
    px, py = x, base - s
    L1, L2 = s * 1.1, s * 0.4
    ex, ey = px + L1 * math.cos(math.pi + a), py + L1 * math.sin(math.pi + a)
    cx, cy = px + L2 * math.cos(a), py + L2 * math.sin(a)
    A.d[layer].line((ex, ey, cx, cy), fill=255, width=10)
    A.d[layer].rectangle((cx - 26, cy, cx + 26, cy + 44), fill=255)

def onion_church(A, x, base, s, layer='mid'):
    A.d[layer].rectangle((x - s * 0.35, base - s * 0.8, x + s * 0.35, base), fill=255)
    A.d[layer].polygon([(x - s * 0.3, base - s * 0.8), (x - s * 0.3, base - s * 1.0), (x, base - s * 1.3), (x + s * 0.3, base - s * 1.0), (x + s * 0.3, base - s * 0.8)], fill=255)
    A.d['ink'].line((x, base - s * 1.3, x, base - s * 1.5), fill=255, width=3)
    A.d['ink'].line((x - s * 0.08, base - s * 1.42, x + s * 0.08, base - s * 1.42), fill=255, width=3)

# ================================================================ hooks
def art_g_hook_orphan(A, cv, t, u):
    ground(A, GROUND)
    yurt(A, 820, GROUND - 10, 220, layer='mid')
    person(A, 420, GROUND, 250, dir=1, female=True, bow=50, arm=110, layer='ink')
    A.d['ink'].line((480, GROUND - 120, 520, GROUND - 4), fill=255, width=5)
    for k in range(3):
        person(A, 240 - k * 70, GROUND, 140 - k * 14, dir=1, robe=False, bow=30, arm=100, layer='ink' if k == 0 else 'mid')
    for k in range(5):
        A.d['grass'].line((560 + k * 30, GROUND, 566 + k * 30, GROUND - 40), fill=255, width=4)

def art_g_hook_unite(A, cv, t, u):
    ground(A, GROUND)
    for k in range(9):
        a = math.pi + k * math.pi / 8
        x = 540 + 420 * math.cos(a); y = GROUND - 30 + 60 * math.sin(a) * 0.5
        rider(A, lerp(540 + 900 * math.cos(a), x, ease_out(u / (1.5 * P))), y, 110, 1 if math.cos(a) < 0 else -1, t * 10 + k, layer='mid')
    mongol(A, 540, GROUND, 280, dir=1, arm=150, layer='ink')

def art_g_hook_west(A, cv, t, u):
    ground(A, GROUND)
    for row, (yy, s_, lay) in enumerate(((1290, 110, 'wash'), (1350, 160, 'mid'), (GROUND, 220, 'ink'))):
        for k in range(7):
            x = (k * s_ * 1.7 - t * 400 * (row + 1) * 0.6) % (W + 400) - 200
            rider(A, W - x, yy, s_, -1, t * 14 + k, layer=lay, spear=row == 2)

def art_g_hook_grave(A, cv, t, u):
    ground(A, GROUND)
    for k in range(40):
        x = 80 + k * 24
        h = 30 + 12 * math.sin(t * 2 + k * 0.6)
        A.d['grass'].line((x, GROUND, x + 6 * math.sin(t * 2 + k), GROUND - h), fill=255, width=4)
    A.d['wash'].ellipse((460, 1180, 620, 1240), fill=150)
    A.flush(cv)
    ink_in(cv, text_img('？', BRUSH, 200, INK), 540, 1060, t, t - u + 0.8 * P, dur=0.3, settle=1.1)

# ================================================================ 第一回 苍狼之子
def art_g_birth(A, cv, t, u):
    stars(A, t, seed=2)
    ground(A, GROUND)
    yurt(A, 540, GROUND - 10, 320, layer='mid')
    A.d['yellow'].rectangle((500, GROUND - 130, 580, GROUND - 10), fill=200)
    A.flush(cv)
    if u > P:
        ink_in(cv, text_img('握血而生', SERIF, 40, ZHU, 'Black', bleed=False), 820, 1000, t, t - u + P, dur=0.3, settle=1.0)
        stamp(cv, seal('髀石', 50), 820, 1100, t, t - u + 1.4 * P)

def art_g_poison(A, cv, t, u):
    stars(A, t, seed=3)
    ground(A, GROUND)
    yurt(A, 820, GROUND - 10, 240, layer='mid')
    campfire_y = GROUND
    flames(A, 560, GROUND, 80, 100, t, n=3, seed=5, smoke=False)
    for k in range(3):
        mongol(A, 680 + k * 70, GROUND, 170, dir=-1, robe=True, kneel=True, bow=10, arm=60, layer='mid')
    fall = -70 * ease_out((u - 2 * P) / 0.4) if u > 2 * P else 0
    mongol(A, 360, GROUND, 230, dir=1, arm=lerp(60, 140, ease_out(u / P)) if u < 2 * P else 40, bow=30 if u > 2 * P else 0, layer='ink')
    A.d['ink'].polygon([(390, GROUND - 230), (420, GROUND - 230), (414, GROUND - 200), (396, GROUND - 200)], fill=255)

def art_g_roots(A, cv, t, u):
    A.d['wash'].rectangle((60, 1300, W - 60, 1360), fill=170)
    waves(A, 1310, t, rows=2, amp=4, speed=1.2)
    ground(A, GROUND)
    person(A, 300, GROUND, 250, dir=1, female=True, bow=50, arm=120, layer='ink')
    A.d['ink'].line((370, GROUND - 120, 400, GROUND - 10), fill=255, width=5)
    for k in range(4):
        person(A, 560 + k * 100, GROUND, 150 - k * 12, dir=-1, robe=False, bow=40, arm=120, layer='ink' if k % 2 == 0 else 'mid')
    for k in range(int(clamp(u / (2 * P)) * 8)):
        A.d['grass'].ellipse((420 + k * 20, GROUND - 22, 436 + k * 20, GROUND - 6), fill=255)

def art_g_cangue(A, cv, t, u):
    A.d['wash'].ellipse((760, 660, 860, 760), fill=255)
    A.d['wash'].rectangle((60, 1230, W - 60, 1380), fill=170)
    waves(A, 1240, t, rows=3, amp=5, speed=1.0)
    y = 1260 + 6 * math.sin(t * 2)
    A.d['ink'].ellipse((500, y - 60, 560, y), fill=255)
    cangue(A, 530, y + 4, 140)
    if u > 2 * P:
        q = ease_out((u - 2 * P) / (2 * P))
        cx = lerp(1100, 760, q)
        A.d['mid'].rectangle((cx - 120, GROUND - 120, cx + 120, GROUND - 40), fill=255)
        A.d['ink'].ellipse((cx - 90, GROUND - 60, cx - 30, GROUND), outline=255, width=6)
        A.d['ink'].ellipse((cx + 30, GROUND - 60, cx + 90, GROUND), outline=255, width=6)
        for k in range(10):
            A.d['wash'].ellipse((cx - 110 + k * 22, GROUND - 160, cx - 80 + k * 22, GROUND - 110), fill=255)

def art_g_bride(A, cv, t, u):
    ground(A, GROUND)
    yurt(A, 820, GROUND - 10, 220, layer='mid')
    x = lerp(-200, 380, ease_out(u / (2 * P)))
    A.d['mid'].rectangle((x - 130, GROUND - 170, x + 70, GROUND - 60), fill=255)
    A.d['red'].polygon([(x - 140, GROUND - 170), (x + 80, GROUND - 170), (x - 30, GROUND - 240)], fill=255)
    for wx in (x - 100, x + 40):
        A.d['ink'].ellipse((wx - 40, GROUND - 80, wx + 40, GROUND), outline=255, width=6)
    camel(A, x + 230, GROUND, 150, 1, t * 5, layer='ink')
    person(A, x - 30, GROUND - 170, 110, dir=1, female=True, arm=20, layer='ink')
    if u > 2 * P:
        A.flush(cv)
        stamp(cv, seal('黑貂裘', 44), 820, 1000, t, t - u + 2 * P, rot=5)

def art_g_rescue(A, cv, t, u):
    stars(A, t, seed=4)
    ground(A, GROUND)
    for i, x in enumerate((760, 940)):
        yurt(A, x, GROUND - 10, 180, layer='mid')
        if u > 1.5 * P:
            flames(A, x, GROUND - 100, 100, 110 * ease_out((u - 1.5 * P) / 0.4), t + i, n=3, seed=20 + i, smoke=True)
    for k in range(3):
        x = lerp(-150 - k * 180, 480 - k * 170, ease_out(u / (2 * P)))
        rider(A, x, GROUND - k * 10, 200 - k * 20, 1, t * 13 + k, layer='ink' if k == 0 else 'mid', spear=True)
    if u > 2.5 * P:
        person(A, 620, GROUND, 200, dir=-1, female=True, arm=120, layer='ink')

def art_g_anda(A, cv, t, u):
    sun(cv, 540, 980, 200, ZHU, 110)
    ground(A, GROUND)
    give = ease_out((u - 0.4) / 0.6)
    mongol(A, 360, GROUND, 260, dir=1, arm=lerp(20, 85, give), layer='ink')
    mongol(A, 720, GROUND, 260, dir=-1, arm=lerp(20, 85, give), layer='ink')
    if give > 0:
        A.d['ink'].line((450, GROUND - 190, 630, GROUND - 190), fill=255, width=4)
        A.d['ink'].polygon([(630, GROUND - 190), (612, GROUND - 200), (612, GROUND - 180)], fill=255)
    A.flush(cv)
    stamp(cv, seal('安答', 56), 540, 900, t, t - u + P)

def art_g_thirteen(A, cv, t, u):
    ground(A, GROUND)
    for k in range(13):
        a = math.pi + k * math.pi / 12
        x = 540 + 380 * math.cos(a); y = 1180 + 120 * math.sin(a) * -1
        r = 34
        A.d['mid'].ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=255)
    kk = (t - G.B0) / P
    for k in range(6):
        x = (t * 300 + k * 200) % (W + 200) - 100
        rider(A, W - x, GROUND, 130, -1, t * 12 + k, layer='ink', spear=True)
    A.flush(cv)
    stamp(cv, seal('十三翼', 50, INK), 540, 1180, t, t - u + 0.3)

# ================================================================ 第二回 统一草原
def art_g_tatar(A, cv, t, u):
    ground(A, GROUND)
    for i, x in enumerate((620, 800, 960)):
        fallen = ease_out((u - 1 * P - i * 0.2) / 0.4)
        A.d['mid'].polygon([(x - 80, GROUND), (x + 80, GROUND), (x + 80 - 60 * fallen, GROUND - 120 + 80 * fallen), (x - 80, GROUND - 120 + 100 * fallen)], fill=255)
    for k in range(4):
        x = lerp(-200 - k * 140, 440 - k * 130, ease_out(u / (1.6 * P)))
        rider(A, x, GROUND - (k % 2) * 12, 170, 1, t * 13 + k, layer='ink' if k % 2 == 0 else 'mid', spear=True)
    A.flush(cv)
    stamp(cv, seal('父仇得报', 44), 820, 960, t, t - u + 2 * P, rot=5)

def art_g_baljuna(A, cv, t, u):
    """8-beat set piece: defeat → the muddy lake → survivors kneel and drink → bowls raised → the oath."""
    ph = u / P
    A.d['mid'].polygon([(60, 1220), (W - 60, 1200), (W - 60, 1380), (60, 1380)], fill=200)
    for k in range(4):
        pts = [(x, 1230 + k * 34 + 6 * math.sin(x * 0.02 + t * 1.5 + k)) for x in range(60, W - 59, 12)]
        A.d['ink'].line(pts, fill=120, width=4)
    ground(A, 1220)
    n = 7
    for i in range(n):
        x = 160 + i * 125
        if ph < 2:
            mongol(A, walk_x(x - 300, x, u, 2 * P), 1220, 170, dir=1, bow=30, arm=20, ph=t * 4 + i, layer='ink' if i % 2 else 'mid')
        elif ph < 5:
            mongol(A, x, 1220, 170, dir=1, kneel=True, bow=55, arm=110, layer='ink' if i % 2 else 'mid')
        else:
            mongol(A, x, 1220, 180, dir=1, arm=160 + 10 * math.sin(t * 4 + i), layer='ink' if i % 2 else 'mid')
    A.flush(cv)
    if ph >= 5:
        type_in(cv, text_img('同饮浑水  永不相负', BRUSH, 80, INK), W / 2, 900, t, t - u + 5 * P, 0.6)
    if ph >= 6.5:
        stamp(cv, seal('班朱尼', 56), 860, 1040, t, t - u + 6.5 * P, rot=6)

def art_g_kereit(A, cv, t, u):
    stars(A, t, seed=6)
    ground(A, GROUND)
    yurt(A, 700, GROUND - 10, 360, layer='mid')
    A.d['gold'].chord((520, GROUND - 330, 880, GROUND - 40), 180, 360, fill=200)
    if u > 1.5 * P:
        flames(A, 700, GROUND - 160, 300, 200 * ease_out((u - 1.5 * P) / 0.5), t, n=6, seed=30, smoke=True)
    for k in range(3):
        x = lerp(-150 - k * 150, 340 - k * 120, ease_out(u / (1.5 * P)))
        rider(A, x, GROUND - k * 8, 170, 1, t * 13 + k, layer='ink', spear=True)

def art_g_naiman(A, cv, t, u):
    A.d['mid'].polygon([(560, GROUND), (560, 900), (700, 840), (1020, 840), (1020, GROUND)], fill=200)
    ground(A, GROUND)
    for k in range(5):
        q = ((u * 0.8 + k * 0.2) % 1)
        x = 600 + k * 40; y = 860 + q * (GROUND - 860)
        person(A, x, y, 90, dir=-1, robe=False, fall=q * 160, arm=150, layer='mid')
    for k in range(3):
        rider(A, lerp(-150, 380, ease_out(u / (2 * P))) - k * 150, GROUND, 190, 1, t * 13 + k, layer='ink', spear=True)
    A.flush(cv)
    stamp(cv, seal('纳忽崖', 50), 820, 780, t, t - u + P, rot=5)

def art_g_jamukha(A, cv, t, u):
    sun(cv, 540, lerp(1000, 1180, ease_out(u / (3 * P))), 200, (140, 120, 110), 120)
    ground(A, GROUND)
    mongol(A, 380, GROUND, 230, dir=1, kneel=True, bow=40, arm=60, layer='ink')
    A.d['ink'].line((330, GROUND - 120, 440, GROUND - 100), fill=200, width=4)
    mongol(A, 760, GROUND, 290, dir=-1, arm=lerp(20, 60, ease_out(u / P)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('安答', 56, INK), 560, 960, t, t - u)
    q = ease_out((u - 1.5 * P) / 0.3)
    if q > 0:
        d = ImageDraw.Draw(cv)
        d.line((520, 920, 520 + 40 * q, 960, 560, 1000 * 1 if q > 0.5 else 960), fill=ZHU + (240,), width=6)

def art_g_khan(A, cv, t, u):
    """6-beat: the nine-tailed white standard rises → riders ring the Onon → 成吉思汗."""
    ph = u / P
    A.d['sky'].rectangle((60, 1300, W - 60, 1360), fill=150)
    waves(A, 1310, t, rows=2, amp=5, speed=1.2)
    ground(A, GROUND)
    rise = ease_out(u / (1.5 * P))
    for i in range(9):
        x = 140 + i * 100
        sulde(A, x, 1300, (300 + (i == 4) * 140) * rise, t + i, p=1.0 if rise > 0.6 else rise / 0.6)
    if ph >= 2:
        for k in range(10):
            a = math.pi + k * math.pi / 9
            x = 540 + 460 * math.cos(a)
            rider(A, lerp(540 + 900 * math.cos(a), x, ease_out((u - 2 * P) / (1.5 * P))), GROUND + 20 * math.sin(a), 100, 1 if math.cos(a) < 0 else -1, t * 9 + k, layer='mid')
    A.flush(cv)
    if ph >= 4:
        stamp(cv, seal('成吉思汗', 56), 880, 880, t, t - u + 4 * P, rot=6)

# ================================================================ 第三回 天骄立国
def art_g_mingghan(A, cv, t, u):
    ph = u / P
    r = random.Random(4)
    pts = [(r.uniform(160, 920), r.uniform(860, 1360)) for _ in range(120)]
    for i, (x, y) in enumerate(pts):
        if ph < 1:
            tx, ty = x, y
        else:
            g = i // 10 if ph < 2.5 else i // 40
            gx = 240 + (g % 4) * 200 if ph < 2.5 else 300 + g * 240
            gy = 940 + (g // 4) * 160 if ph < 2.5 else 1100
            q = ease_out((u - (1 if ph < 2.5 else 2.5) * P) / 0.6)
            tx, ty = lerp(x, gx + (i % 10 - 5) * 10, q), lerp(y, gy + (i % 3) * 12, q)
        A.d['ink'].ellipse((tx - 6, ty - 6, tx + 6, ty + 6), fill=255)
    A.flush(cv)
    lab = '十户' if ph < 1 else ('百户' if ph < 2.5 else '千户')
    paste(cv, text_img(lab, SERIF, 64, ZHU, 'Black', bleed=False), W / 2, 1460, 1, 1)

def art_g_yasa(A, cv, t, u):
    A.d['mid'].polygon([(380, GROUND), (700, GROUND), (680, 860), (400, 860)], fill=220)
    A.d['ink'].polygon([(380, GROUND), (700, GROUND), (680, 860), (400, 860)], outline=255, width=6)
    fo = font(SERIF, 34, 'Bold')
    lines = ['不得盗窃', '不得通奸', '不得说谎', '不得背叛', '违令者斩']
    for i, ln in enumerate(lines):
        if u > 0.3 + i * 0.45:
            A.d['ink'].text((560 - fo.getlength(ln) / 2 - 2, 920 + i * 80), ln, font=fo, fill=255)
    ground(A, GROUND)
    mongol(A, 860, GROUND, 260, dir=-1, arm=90, layer='ink')

def art_g_script(A, cv, t, u):
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    person(A, 540, GROUND, 220, dir=1, hat='knot', kneel=True, bow=20, arm=100, layer='ink')
    A.d['mid'].rectangle((620, 860, 900, 1230), fill=150)
    n = int(clamp(u / (2.5 * P)) * 5)
    for c_ in range(n):
        x = 860 - c_ * 52
        pts = [(x + 10 * math.sin(j * 1.3 + c_), 880 + j * 30) for j in range(11)]
        A.d['ink'].line(pts, fill=255, width=6)
        for j in range(0, 11, 3):
            A.d['ink'].line((pts[j][0], pts[j][1], pts[j][0] + 16, pts[j][1] + 8), fill=255, width=5)

def art_g_keshig(A, cv, t, u):
    stars(A, t, seed=8)
    ground(A, GROUND)
    yurt(A, 540, GROUND - 10, 300, layer='mid')
    A.d['gold'].chord((390, GROUND - 280, 690, GROUND - 40), 180, 360, fill=170)
    for k in range(8):
        a = math.pi + (k + 0.5) * math.pi / 8
        x = 540 + 420 * math.cos(a); y = GROUND + 30 * math.sin(a)
        mongol(A, x, y, 160, dir=1 if x < 540 else -1, robe=False, arm=60, layer='ink')
        A.d['ink'].arc((x + (20 if x < 540 else -60), y - 140, x + (60 if x < 540 else -20), y - 60), 270, 90, fill=255, width=3)

def art_g_xixia(A, cv, t, u):
    city_wall(A, 520, W - 60, 1140, gate_x=780, label='中兴', open_=ease_out((u - 0.6) / 0.6))
    ground(A, GROUND)
    for k in range(3):
        x = walk_x(820 - k * 100, 420 - k * 100, u - 0.8, 2 * P)
        camel(A, x, GROUND, 130, -1, t * 5 + k, layer='mid')
    person(A, walk_x(760, 600, u - 0.8, 2 * P), GROUND, 170, dir=-1, female=True, arm=20, layer='ink')
    mongol(A, 220, GROUND, 270, dir=1, arm=40, layer='ink')

def art_g_yehuling(A, cv, t, u):
    A.d['mid'].polygon([(60, GROUND), (60, 860), (300, 920), (420, GROUND)], fill=200)
    A.d['mid'].polygon([(W - 60, GROUND), (W - 60, 860), (780, 920), (660, GROUND)], fill=200)
    ground(A, GROUND)
    for k in range(8):
        fall = -60 * ease_out((u - 1.5 * P - k * 0.05) / 0.3) if u > 1.5 * P else 0
        person(A, 600 + (k % 4) * 60, GROUND - (k // 4) * 30, 120, dir=-1, robe=False, hat='helmet', spear=True, fall=-fall, layer='mid')
    for k in range(4):
        x = lerp(80, 480, ease_out(u / (1.5 * P))) - k * 90
        y = lerp(900, GROUND, ease_out(u / (1.5 * P))) - k * 10
        rider(A, x, y, 150, 1, t * 14 + k, layer='ink', spear=True)
    A.flush(cv)
    stamp(cv, seal('野狐岭', 50), 820, 820, t, t - u + 2 * P, rot=6)

def art_g_zhongdu(A, cv, t, u):
    city_wall(A, 60, W - 60, 1100, gate_x=540, label='中都')
    burn = ease_out(u / (3 * P))
    for k in range(4):
        flames(A, 160 + k * 260, 1100, 180, 220 * burn, t + k, n=4, seed=50 + k, smoke=True)
    ground(A, GROUND)
    for k in range(3):
        rider(A, 160 + k * 150, GROUND, 150, 1, t * 8 + k, layer='ink', spear=True)
    sulde(A, 820, GROUND, 360, t)

# ================================================================ 第四回 长驱西征
def art_g_otrar(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 200
        fall = ease_out((u - 1 * P - k * 0.2) / 0.3) if u > P else 0
        camel(A, x, GROUND, 130, 1, 0.0 if fall else t * 4 + k, layer='mid')
        person(A, x - 60, GROUND, 150, dir=1, robe=True, hat='knot', fall=-80 * fall, arm=20, layer='ink')
        if fall > 0.5:
            A.d['red'].ellipse((x - 120, GROUND - 16, x - 20, GROUND + 4), fill=200)
    dome(A, 920, GROUND - 10, 160, 180, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('讹答剌', 50, INK), 540, 960, t, t - u + 2 * P, rot=-5)

WEST = [('讹答剌', 1219, 880), ('布哈拉', 1220, 760), ('撒马尔罕', 1220, 640), ('玉龙杰赤', 1221, 500), ('印度河', 1221, 380), ('迦勒迦河', 1223, 180)]
def scene_west(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    idx = int(k - c[0])
    A = Art(); beat_fx(A, t)
    pts = [(x, 1060 + 120 * math.sin(x * 0.006 + 1) + 60 * math.sin(x * 0.019)) for x in range(80, 1001, 10)]
    A.d['sky'].polygon(pts[:1] + [(80, 900)] + [(x, 900 + 30 * math.sin(x * 0.01)) for x in range(80, 1001, 20)] + [(1000, 900)] + pts[::-1], fill=60)
    A.d['ink'].line([(x, 900 + 30 * math.sin(x * 0.01)) for x in range(80, 1001, 20)], fill=200, width=3)
    A.d['ink'].line(pts, fill=200, width=3)
    prog = clamp((t - s0) / (6 * P)) if not gather else 1
    x_head = lerp(980, 160, prog)
    A.d['red'].line((980, 1040, max(x_head, 160), 1040 + 10 * math.sin(x_head * 0.01)), fill=255, width=10)
    A.d['red'].polygon([(x_head - 30, 1040), (x_head + 6, 1020), (x_head + 6, 1060)], fill=255)
    A.flush(cv)
    stamp(cv, seal('蒙古', 60, INK), 980, 990, t, s0)
    for i, (nm, yr, x) in enumerate(WEST):
        st = bt(c[0] + i)
        if t >= st:
            stamp(cv, seal(nm, 34 if len(nm) > 3 else 40, ZHU), x, 1150 - (i % 2) * 170, t, st + 0.1, rot=(i % 3 - 1) * 5)
    if 0 <= idx < 6 and not gather:
        nm, yr, _ = WEST[idx]
        ink_in(cv, text_img(f'公元{cn_year(yr)}年 · {nm}', SERIF, 50, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1460, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '铁骑西征', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '万里西征', BRUSH, 160, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '兵锋直抵东欧', BRUSH, 110, ZHU, W / 2, 1460, t, bt(c[0] + 7), stagger=0.06, seed=111)
    fx.flush(cv)

def art_g_samarkand(A, cv, t, u):
    for i, (x, w, h) in enumerate(((620, 200, 220), (840, 150, 170))):
        dome(A, x, 1240, w, h, layer='mid')
    for x in (500, 960):
        A.d['ink'].rectangle((x - 16, 900, x + 16, 1240), fill=255)
        A.d['ink'].ellipse((x - 24, 880, x + 24, 920), fill=255)
    ground(A, GROUND)
    kk = (t - G.B0) / P
    trebuchet(A, 220, GROUND, 220, 0.5 + 0.5 * math.sin(kk * math.pi))
    q = (kk % 1)
    bx = lerp(260, 640, q); by = GROUND - 240 - 300 * math.sin(math.pi * q)
    A.d['ink'].ellipse((bx - 14, by - 14, bx + 14, by + 14), fill=255)

def art_g_indus(A, cv, t, u):
    A.d['mid'].polygon([(60, GROUND), (60, 980), (500, 1000), (540, GROUND)], fill=220)
    A.d['sky'].rectangle((540, 1200, W - 60, 1380), fill=150)
    waves(A, 1210, t, rows=4, amp=8, speed=2.5, x0=540)
    q = clamp((u - 0.5 * P) / (2 * P))
    x = lerp(470, 820, q); y = 1000 + (1240 - 1000) * q * q - 140 * math.sin(math.pi * q)
    rider(A, x, y, 150, 1, t * 6, layer='ink')
    mongol(A, 200, 990, 220, dir=1, arm=lerp(20, 120, ease_out((u - 3 * P) / 0.4)), layer='ink')

def art_g_qiu(A, cv, t, u):
    ground(A, GROUND)
    yurt(A, 540, GROUND - 10, 520, layer='wash')
    mongol(A, 720, GROUND, 270, dir=-1, kneel=True, bow=10, arm=60, layer='ink')
    person(A, 360, GROUND, 270, dir=1, robe=True, hat='knot', arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.d['ink'].line((420, GROUND - 190, 460, GROUND - 260), fill=255, width=4)
    for k in range(6):
        A.d['wash'].line((460, GROUND - 260, 470 + k * 8 + 6 * math.sin(t * 3 + k), GROUND - 190), fill=255, width=3)
    A.d['wash'].line((360, GROUND - 220, 362, GROUND - 120), fill=255, width=10)
    A.flush(cv)
    stamp(cv, seal('止杀', 60), 540, 900, t, t - u + 1.5 * P)

def art_g_massacre(A, cv, t, u):
    for k in range(7):
        x = 120 + k * 140; h = 100 + (k * 47) % 100
        A.d['mid'].rectangle((x - 50, GROUND - h, x + 50, GROUND), fill=255)
    for k in range(5):
        flames(A, 160 + k * 190, GROUND - 120, 140, 160 * ease_out(u / (2 * P)), t + k, n=3, seed=60 + k, smoke=True)
    for k in range(6):
        a = t * 1.3 + k * 1.05
        crow(A, 540 + 330 * math.cos(a), 820 + 70 * math.sin(a), 22, t * 11 + k)
    ground(A, GROUND)

def art_g_kalka(A, cv, t, u):
    A.d['sky'].rectangle((60, 1280, W - 60, 1360), fill=150)
    waves(A, 1290, t, rows=2, amp=5, speed=2)
    for i, x in enumerate((720, 860, 980)):
        onion_church(A, x, 1270, 150 - i * 20, layer='mid')
    for k in range(10):
        A.d['grass'].polygon([(560 + k * 50, 1270), (580 + k * 50, 1180), (600 + k * 50, 1270)], fill=200)
    ground(A, GROUND)
    for k in range(4):
        rider(A, lerp(-150, 420, ease_out(u / (1.5 * P))) - k * 130, GROUND, 160, 1, t * 13 + k, layer='ink', spear=True)

# ================================================================ 第五回 落日草原
def art_g_fall(A, cv, t, u):
    for k in range(18):
        q = (t * 0.3 + k / 18) % 1
        x = 80 + (k * 53) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    ground(A, GROUND)
    for k in range(4):
        horse(A, (t * 200 + k * 260) % (W + 300) - 150 + 300, GROUND - (k % 2) * 10, 120, 1, t * 12 + k, layer='mid')
    rear = ease_out((u - P) / 0.3) if u > P else 0
    horse(A, 420, GROUND, 230, 1, t * 8 if rear < 1 else 0.5, layer='ink')
    mongol(A, lerp(400, 260, rear), lerp(GROUND - 150, GROUND, rear), 150, dir=1, fall=-80 * rear, arm=120, layer='ink')

def art_g_sick_tent(A, cv, t, u):
    stars(A, t, seed=9)
    ground(A, GROUND)
    yurt(A, 540, GROUND - 10, 420, layer='mid')
    A.d['yellow'].rectangle((470, GROUND - 160, 610, GROUND - 10), fill=180)
    A.d['ink'].rounded_rectangle((470, GROUND - 60, 610, GROUND - 20), radius=14, fill=255)
    city_wall(A, 820, W - 60, 1200, label=None, layer='wash')
    for k in range(3):
        mongol(A, 160 + k * 80, GROUND, 170, dir=1, kneel=True, bow=45, arm=60, layer='mid')

def art_g_death(A, cv, t, u):
    A.d['mid'].polygon([(120, GROUND), (440, 900), (640, 960), (960, GROUND)], fill=200)
    stars(A, t, seed=10)
    yurt(A, 540, 990, 160, layer='ink')
    droop = ease_out((u - P) / (1.5 * P))
    x, base = 700, 1000
    top = base - 300
    A.d['ink'].line((x, base, x + 30 * droop, top + 40 * droop), fill=255, width=8)
    for k in range(12):
        sx = x - 28 + k * 5 + 30 * droop
        pts = [(sx + (1 - droop) * 30 * math.sin(t * 2 + k * 0.4 + j * 0.35) * j / 10, top + 30 + 40 * droop + j * 22) for j in range(11)]
        A.d['wash'].line(pts, fill=255, width=4)
    ground(A, GROUND)

def art_g_hooves(A, cv, t, u):
    ground(A, GROUND)
    flat = clamp(u / (3 * P))
    A.d['mid'].chord((380, GROUND - 120 * (1 - flat), 700, GROUND + 120 * (1 - flat)), 180, 360, fill=255) if flat < 0.98 else None
    for k in range(8):
        x = (t * 520 + k * 150) % (W + 300) - 150
        horse(A, x, GROUND - (k % 3) * 8, 110, 1, t * 16 + k, layer='ink' if k % 2 else 'mid')
    for k in range(10):
        x = (k * 97 - t * 900) % (W + 200) - 100
        A.d['wash'].ellipse((x - 40, GROUND - 40, x + 40, GROUND), fill=200)
    if flat > 0.6:
        for k in range(30):
            gx = 80 + k * 32
            A.d['grass'].line((gx, GROUND, gx + 4, GROUND - 30 * (flat - 0.6) / 0.4), fill=255, width=4)

def art_g_camel_mother(A, cv, t, u):
    for k in range(40):
        x = 80 + k * 24
        h = 26 + 10 * math.sin(t * 2 + k * 0.6)
        A.d['grass'].line((x, GROUND, x + 5 * math.sin(t * 2 + k), GROUND - h), fill=255, width=4)
    ground(A, GROUND)
    camel(A, 540, GROUND, 230, 1, 0.0, layer='ink')
    for k in range(4):
        q = ((t * 0.6 + k * 0.25) % 1)
        A.d['wash'].ellipse((690 + q * 10 - 5, GROUND - 230 + q * 70 - 5, 690 + q * 10 + 5, GROUND - 230 + q * 70 + 5), fill=255)
    A.flush(cv)
    stamp(cv, seal('骆驼认墓', 46), 820, 960, t, t - u + P, rot=5)

def art_g_golden(A, cv, t, u):
    sun(cv, 540, 1020, 200, (210, 160, 60), 130)
    ground(A, GROUND)
    for i, (dx, dy) in enumerate(((-1, 0), (1, 0), (-0.6, -0.5), (0.6, -0.5))):
        q = ease_out(u / (2 * P))
        x = 540 + dx * 420 * q; y = GROUND - 20 + dy * 200 * q
        rider(A, x, y, 120, 1 if dx > 0 else -1, t * 12 + i, layer='ink' if i < 2 else 'mid')
    A.flush(cv)
    for i, (nm, x, y) in enumerate((('元', 160, 1000), ('金帐', 920, 1000), ('察合台', 300, 820), ('伊儿', 780, 820))):
        if u > 2 * P + i * 0.15:
            stamp(cv, seal(nm, 40 if len(nm) > 1 else 54, ZHU if i == 0 else INK), x, y, t, t - u + 2 * P + i * 0.15, rot=(i % 2 * 2 - 1) * 5)

# ================================================================ script
CHAPTERS = {16: ('第一回', '苍狼之子'), 48: ('第二回', '统一草原'), 80: ('第三回', '天骄立国'),
            112: ('第四回', '长驱西征'), 144: ('第五回', '落日草原')}

CARDS = [
    C(0, 2, 'hook', 'num', num='九岁丧父', line='挖野菜活命', art=art_g_hook_orphan),
    C(2, 4, 'hook', 'num', num='四十五岁', line='统一蒙古草原', art=art_g_hook_unite),
    C(4, 6, 'hook', 'num', num='铁骑西征', line='兵锋直抵东欧', art=art_g_hook_west),
    C(6, 8, 'hook', 'num', num='墓葬成谜', line='八百年无人找到', art=art_g_hook_grave),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 苍狼之子
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'night', 'card', year=1162, main='握血而生', sub='斡难河畔 · 手握凝血如髀石', note='生时右手握凝血 如髀石', art=art_g_birth),
    C(22, 26, 'night', 'card', year=1170, main='父亲被毒', sub='塔塔儿人设宴 · 也速该中毒身亡', note='归途毒发而亡', art=art_g_poison),
    C(26, 30, 'life', 'card', year=1171, main='挖野菜', sub='部众离散 · 母亲带孩子艰难求生', note='诃额仑 拾杜梨 掘草根', art=art_g_roots),
    C(30, 34, 'night', 'card', year=1176, main='木枷逃生', sub='被泰赤乌人所擒 · 月夜潜逃', note='藏身羊毛车中 得锁儿罕失剌相救', art=art_g_cangue),
    C(34, 38, 'life', 'card', year=1178, main='迎娶孛儿帖', sub='九岁定亲 · 十余年后迎娶', note='以黑貂裘为嫁妆', art=art_g_bride),
    C(38, 42, 'war', 'card', year=1180, main='夺回妻子', sub='妻子被蔑儿乞人掳走 · 借兵夜袭', note='联合王汗 札木合 三万骑', art=art_g_rescue),
    C(42, 46, 'court', 'card', year=1181, main='札木合安答', sub='三次结义 · 互赠骨箭', note='安答 生死之交', art=art_g_anda),
    C(46, 48, 'war', 'card', year=1190, main='十三翼之战', sub='安答反目 · 首战失利', art=art_g_thirteen),
    # ---- 第二回 统一草原
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'war', 'card', year=1202, main='灭塔塔儿', sub='为父复仇', note='塔塔儿部 自此消亡', art=art_g_tatar),
    C(54, 62, 'court', 'card', year=1203, main='班朱尼河', sub='兵败只剩十九人 · 同饮浑水盟誓', note='使我克定大业 当与汝辈同甘苦', art=art_g_baljuna),
    C(62, 66, 'night', 'card', year=1203, main='灭克烈', sub='夜袭王汗金帐', note='三昼夜鏖战 克烈部亡', art=art_g_kereit),
    C(66, 70, 'war', 'card', year=1204, main='灭乃蛮', sub='纳忽崖之战 · 敌军坠崖', note='乃蛮溃兵 坠崖者不可胜数', art=art_g_naiman),
    C(70, 74, 'death', 'card', year=1205, main='札木合之死', sub='安答被擒 · 求不流血而死', note='愿赐我不流血而死', art=art_g_jamukha),
    C(74, 80, 'empire', 'card', year=1206, main='斡难河称汗', sub='忽里台大会 · 九游白纛高竖', note='尊号成吉思汗 意为拥有四海', art=art_g_khan),
    # ---- 第三回 天骄立国
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'empire', 'card', year=1206, main='千户制', sub='打散部落 · 十户百户千户', note='编为九十五千户', art=art_g_mingghan),
    C(86, 90, 'court', 'card', year=1206, main='大扎撒', sub='颁布法典 · 令行禁止', note='蒙古第一部成文法', art=art_g_yasa),
    C(90, 94, 'court', 'card', year=1204, main='创制文字', sub='以畏兀儿字母 · 拼写蒙古语', note='命塔塔统阿 教太子诸王', art=art_g_script),
    C(94, 98, 'night', 'card', year=1206, main='怯薛军', sub='万人护卫 · 日夜轮值', note='四怯薛 分番宿卫', art=art_g_keshig),
    C(98, 102, 'works', 'card', year=1210, main='臣服西夏', sub='西夏献女纳贡', note='西夏国主 献女请和', art=art_g_xixia),
    C(102, 106, 'war', 'card', year=1211, main='野狐岭', sub='以少胜多 · 大破金军', note='金军精锐 一战而没', art=art_g_yehuling),
    C(106, 112, 'war', 'card', year=1215, main='攻破中都', sub='金朝南迁 · 中都陷落', note='火烧中都 月余不灭', art=art_g_zhongdu),
    # ---- 第四回 长驱西征
    C(112, 114, 'works', 'chapter'),
    C(114, 118, 'death', 'card', year=1218, main='讹答剌血案', sub='商队四百余人被杀 · 西征导火索', note='使者被辱 商人被杀', art=art_g_otrar),
    C(118, 126, 'works', 'west'),
    C(126, 130, 'works', 'card', year=1220, main='撒马尔罕', sub='投石机轰城 · 中亚名城陷落', note='西域第一大城', art=art_g_samarkand),
    C(130, 134, 'war', 'card', year=1221, main='印度河', sub='札兰丁纵马跃河 · 大汗赞叹', note='为父者当有此子', art=art_g_indus),
    C(134, 138, 'court', 'card', year=1222, main='丘处机', sub='长春真人万里西行 · 劝止杀', note='敬天爱民为本 清心寡欲为要', art=art_g_qiu),
    C(138, 142, 'death', 'card', year=1221, main='屠城', sub='抵抗者 · 城破屠尽', note='征服的另一面', art=art_g_massacre),
    C(142, 144, 'works', 'card', year=1223, main='迦勒迦河', sub='哲别速不台 · 远袭罗斯', art=art_g_kalka),
    # ---- 第五回 落日草原
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'fate', 'card', year=1226, main='坠马', sub='围猎野马 · 坠马受伤', note='是夜发热', art=art_g_fall),
    C(150, 154, 'night', 'card', year=1227, main='西夏中兴府', sub='带病出征 · 大军围城', note='誓灭西夏', art=art_g_sick_tent),
    C(154, 158, 'death', 'card', year=1227, main='病逝六盘山', sub='享年六十六岁 · 苏鲁锭垂落', note='七月 崩于萨里川哈老徒行宫', art=art_g_death),
    C(158, 162, 'death', 'card', year=1227, main='万马踏平', sub='秘密下葬 · 万马踏平墓地', note='不封不树', art=art_g_hooves),
    C(162, 166, 'fate', 'card', year=1227, main='骆驼认墓', sub='杀幼驼于墓上 · 母驼悲鸣认墓', note='相传如此 至今无人寻得', art=art_g_camel_mother),
    C(166, 170, 'end', 'card', year=1227, main='黄金家族', sub='子孙建立四大汗国与元朝', note='孙忽必烈 建元一统', art=art_g_golden),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z, St, M, K, Y, Q):
    mod.CHAPTERS = CHAPTERS
G.CHAPTER_BEATS = [0, 16, 48, 80, 112, 144, END_BEAT]
L.CUTS = sorted({c[0] for c in CARDS if c[0] not in G.CHAPTER_BEATS})

def year_at(t):
    pts = sorted((bt(c[0]), c[4]['year']) for c in CARDS if 'year' in c[4])
    if t <= pts[0][0]: return pts[0][1]
    prev = pts[0][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t < t1: return lerp(prev, y0, ease_out((t - t0) / 0.4))
        prev = y0
    return lerp(prev, pts[-1][1], ease_out((t - pts[-1][0]) / 0.4))
for mod in (G, L, Wd, Tz, Z, St, M, K, Y, Q):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_year(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=SKY + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    def art(A, cv_, t_, u_):
        sun(cv_, 600, 1000, 250, SKY, 120)
        ground(A, 1440)
        mongol(A, 470, 1440, 700, dir=1, arm=lerp(-5, 55, ease_out(u_ / (2 * P))), layer='ink')
        sulde(A, 820, 1440, 640, t_)
    stage(cv, t, c, art)
    fx = Art()
    ink_in(cv, text_img('孛儿只斤 · 铁木真', SERIF, 46, SKY, 'Bold', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '成吉思汗', BRUSH, 190, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('天骄', 66), 900, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元1162 — 1227', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '屠城之王？', BRUSH, 120, ZHU, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '一代天骄？', BRUSH, 120, SKY, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    for i, x in enumerate((240, 540, 840)):
        sulde(A, x, 1000, 380, t + i, p=clamp(u / 0.6))
    A.flush(cv, alpha=clamp(u / 0.6) * 0.3)
    fx = Art()
    chars_in(cv, fx, '一代天骄', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('成吉思汗', 52), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('从挖野菜的孤儿', SERIF, 50, DIM, 'SemiBold', bleed=False, spacing=6), W / 2, 960, t, END + 0.6, 0.35)
    type_in(cv, text_img('到改变世界版图的大汗', SERIF, 52, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '征服者？毁灭者？', BRUSH, 96, SKY, W / 2, 1190, t, END + 1.15, stagger=0.05, drop=30, splash=False)
    type_in(cv, text_img('评论区说说你的看法', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=SKY + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(250, 250, 255, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=ZHU + (220,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 汉高祖刘邦', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, west=scene_west, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第拾集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(8):
        q = text_img('一个孤儿 · 如何征服半个世界？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 300, 335, W / 2 + 300, 335), fill=SKY + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, SKY, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=SKY + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=ZHU + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(int(round(yr - BORN + 1))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=SKY + (255,))
        if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * a)))
        canvas.alpha_composite(ov, (0, y - 80))
G.draw_hud = draw_hud

render = L.render

if __name__ == '__main__':
    from multiprocessing import Pool
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for ts in sys.argv[2].split(','):
            Image.frombytes('RGB', (W, H), render(int(float(ts) * FPS))).save(out.replace('.png', f'_{ts}.png'))
        sys.exit()
    nfr = int(round(G.DUR * FPS))
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-i', L.MUSIC,
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, fr in enumerate(pool.imap(render, range(nfr), chunksize=4)):
            ff.stdin.write(fr)
            if i % 300 == 0: print(i, '/', nfr, flush=True)
    ff.stdin.close(); ff.wait()
    if ff.returncode != 0: sys.exit(1)
    print('done', out)
