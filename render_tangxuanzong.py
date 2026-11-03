"""千古人物志 · 第肆拾叁集 · 唐玄宗 (685–762)
Look: 盛唐金 + 胭脂红, 霓裳 (rainbow-skirt ribbon) corner borders, a 琵琶 chapter card: a pipa's strings break one
per chapter as the age turns from 开元 to 天宝 to 安史.
Set pieces: 6-beat 先天政变, custom 8-beat scene 'kaiyuan' (开元盛世 granaries & census), 6-beat 霓裳羽衣舞,
6-beat 一骑红尘, 8-beat 马嵬坡, 6-beat 南内凄凉.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_weizheng as Wz        # engine + helpers (previous episode)
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
from render_songtaizu import tent
from render_kongzi import bundle
from render_wudi import camel

F.RIPPLE = False
SHENG = (206, 156, 52)              # 盛唐金
YAN = (196, 66, 96)                 # 胭脂红
S.LAYERS.append(('sheng', SHENG, 0.9, 1.0))
S.LAYERS.append(('yan', YAN, 0.88, 1.2))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='唐', life='隆', court='唐', night='乱', war='乱', empire='盛', works='乐', fate='恨', death='恨', end='恨')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court'):
    G.THEMES[k]['part'] = 'petal'
for k in ('empire',):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (SHENG, 240, (W * 0.5, 820))
G.THEMES['war']['sun'] = (YAN, 220, (W * 0.5, 760))
G.THEMES['end']['sun'] = (YAN, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

LANT = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(LANT)
for _x in (110, 200, 880, 970):
    _d.line((_x, 1140, _x, 1180), fill=(80, 60, 40, 60), width=2)
    _d.ellipse((_x - 18, 1180, _x + 18, 1226), fill=YAN + (50,))
_d.line((60, 1140, W - 60, 1140), fill=(80, 60, 40, 30), width=2)
MTN_COL = {'night': (40, 34, 38), 'death': (62, 58, 60), 'war': (110, 60, 50), 'fate': (100, 80, 86)}
def draw_background(t, theme):
    """长安上元: ridges, festival lanterns strung at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(198, 188, 176), (164, 144, 128), MTN_COL.get(theme, (124, 100, 90))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(LANT)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """霓裳: a fluttering ribbon in each corner, rainbow banded."""
    d = ImageDraw.Draw(canvas)
    m = 44
    cols = [YAN, SHENG, (90, 150, 120), (80, 110, 170)]
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=SHENG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=SHENG + (220,), width=3)
        for j, c in enumerate(cols):
            pts = [(x + sx * (14 + f * 110), y + sy * (20 + j * 6 + 18 * math.sin(f * 6 + j))) for f in np.linspace(0, 1, 12)]
            d.line(pts, fill=c + (220,), width=4)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def ming(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, crown=True, **kw):
    """李隆基: emperor's 冕 / 幞头, yellow robe band; stoops with age."""
    b = bow + 14 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat=('crown' if crown else 'none') if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    if up:
        A.d['sheng'].rectangle((x - 0.1 * h, y - 0.58 * h, x + 0.1 * h, y - 0.52 * h), fill=255)
        A.d[layer].polygon([(x + dir * 0.0, y - 0.86 * h), (x + dir * 0.08 * h, y - 0.86 * h), (x + dir * 0.04 * h, y - 0.74 * h)], fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.01 * h, y - 0.84 * h), (x + dir * 0.07 * h, y - 0.84 * h), (x + dir * 0.04 * h, y - 0.76 * h)], fill=255)
    return hand

def yang(A, x, y, h, dir=1, layer='yan', t=0.0, dance=False, **kw):
    a = lerp(40, 170, 0.5 + 0.5 * math.sin(t * 3)) if dance else kw.pop('arm', 30)
    hand = person(A, x, y, h, dir=dir, robe=True, hat='knot', female=True, arm=a, arm2=(lerp(-40, -160, 0.5 + 0.5 * math.sin(t * 3 + 1)) if dance else None), layer=layer, **kw)
    if not kw.get('kneel') and not kw.get('fall'):
        A.d['sheng'].ellipse((x - 0.07 * h, y - 1.08 * h, x + 0.05 * h, y - 0.96 * h), fill=255)
    if dance:
        hx, hy = hand
        A.d['wash'].line((hx, hy, hx + dir * 0.5 * h * math.cos(t * 3), hy - 0.2 * h), fill=230, width=max(2, int(0.02 * h)))
    return hand

def pipa(A, cx, cy, s, strings=4, t=0.0):
    A.d['sheng'].ellipse((cx - 0.45 * s, cy - 0.2 * s, cx + 0.45 * s, cy + 0.8 * s), fill=255)
    A.d['ink'].polygon([(cx - 0.08 * s, cy - 0.2 * s), (cx + 0.08 * s, cy - 0.2 * s), (cx + 0.05 * s, cy - 1.0 * s), (cx - 0.05 * s, cy - 1.0 * s)], fill=255)
    A.d['ink'].polygon([(cx - 0.1 * s, cy - 1.0 * s), (cx + 0.1 * s, cy - 1.0 * s), (cx + 0.06 * s, cy - 1.15 * s), (cx - 0.12 * s, cy - 1.1 * s)], fill=255)
    for i in range(4):
        x = cx - 0.09 * s + i * 0.06 * s
        if i < strings:
            vib = 3 * math.sin(t * 40 + i)
            A.d['ink'].line((x, cy - 1.0 * s, x + vib, cy + 0.6 * s), fill=200, width=2)
        else:
            A.d['red'].line((x, cy - 1.0 * s, x + 0.08 * s, cy - 0.6 * s), fill=255, width=2)
            A.d['red'].line((x, cy + 0.6 * s, x - 0.06 * s, cy + 0.3 * s), fill=255, width=2)

def lychee(A, x, y, s):
    for k in range(6):
        a = k * 1.05
        px, py = x + 0.35 * s * math.cos(a), y + 0.3 * s * math.sin(a)
        A.d['red'].ellipse((px - 0.2 * s, py - 0.2 * s, px + 0.2 * s, py + 0.2 * s), fill=255)
    A.d['grass'].polygon([(x, y - 0.4 * s), (x + 0.5 * s, y - 0.7 * s), (x + 0.2 * s, y - 0.3 * s)], fill=255)

# ================================================================ chapter card
CH = {16: 4, 48: 4, 80: 3, 112: 1, 144: 0}
def art_pipa_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = CH.get(kb, 4)
    q = ease_out(u / (1.0 * P))
    pipa(A, 540, 1060, 260, strings=n if q > 0.5 else min(4, n + 1), t=t)
    if kb == 144:
        for k in range(30):
            qq = (t * 0.4 + k / 30) % 1
            A.d['wash'].ellipse((80 + (k * 37) % 920 - 4, lerp(620, 1300, qq) - 4, 80 + (k * 37) % 920 + 4, lerp(620, 1300, qq) + 4), fill=220)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_pipa_chapter)
    ink_in(cv, text_img(no, SERIF, 56, YAN, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_t_hook_peak(A, cv, t, u):
    palace(A, 540, GROUND, 680, layer='sheng')
    ground(A, GROUND)
    for k in range(10):
        a = k * 2 * math.pi / 10 + t * 0.3
        A.d['yan'].ellipse((540 + 380 * math.cos(a) - 14, 960 + 120 * math.sin(a) - 14, 540 + 380 * math.cos(a) + 14, 960 + 120 * math.sin(a) + 14), fill=230)

def art_t_hook_fall(A, cv, t, u):
    palace(A, 540, GROUND, 600, collapse=ease_out(u / (1.6 * P)), layer='sheng')
    flames(A, 540, GROUND, 700, 260 * ease_out(u / (1.6 * P)), t, n=7, seed=3, smoke=True)
    ground(A, GROUND)

def art_t_hook_love(A, cv, t, u):
    ground(A, GROUND)
    ming(A, 380, GROUND, 250, dir=1, arm=60)
    yang(A, 680, GROUND, 230, dir=-1, t=t, dance=True)

def art_t_hook_mawei(A, cv, t, u):
    A.d['ink'].line((640, GROUND, 660, 900), fill=255, width=20)
    for k in range(6):
        a = -math.pi / 2 + (k - 2.5) * 0.4
        A.d['ink'].line((660, 960, 660 + 140 * math.cos(a), 960 + 100 * math.sin(a)), fill=255, width=6)
    ground(A, GROUND)
    A.d['wash'].line((660 - 40, 1020, 660 - 40, 1020 + 200 * ease_out(u / (1.6 * P))), fill=255, width=4)

# ================================================================ 第一回 临淄郡王
def art_t_birth(A, cv, t, u):
    palace(A, 540, GROUND, 560, layer='sheng')
    ground(A, GROUND)
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='crown', female=True, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('洛阳', 54), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('武则天之孙 · 睿宗第三子', SERIF, 44, YAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_wuyi(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    ming(A, 340, GROUND, 140, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 4)))
    person(A, 720, GROUND, 220, dir=-1, robe=False, hat='helmet', arm=40, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('吾家朝堂 干汝何事', SERIF, 50, YAN, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + P, 0.5)
    stamp(cv, seal('七岁', 54), 860, 1040, t, t - u + 0.4, rot=6)

def art_t_mother(A, cv, t, u):
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, lerp(540, 1100, ease_out(u / (2.5 * P))), GROUND, 200, dir=1, robe=True, hat='knot', female=True, ph=t * 3, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('母亲入宫后 再未出来', SERIF, 46, YAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_luzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='潞州', layer='mid', open_=1.0)
    ground(A, GROUND)
    ming(A, 540, GROUND, 220, dir=1, crown=False, arm=40)
    for k in range(4):
        person(A, 160 + k * 60 if k < 2 else 820 + (k - 2) * 60, GROUND, 140, dir=1 if k < 2 else -1, robe=False, hat='knot', arm=60, layer='mid')
    A.flush(cv)
    stamp(cv, seal('潞州别驾', 44), 860, 1020, t, t - u + P, rot=6)

def art_t_tanglong(A, cv, t, u):
    """6-beat: 唐隆政变 — night; the palace; his men burst in; the 韦后 faction falls."""
    ph = u / P
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    palace(A, 680, GROUND, 520, layer='mid')
    ground(A, GROUND)
    for k in range(8):
        x = lerp(-200, 520, ease_out((ph - k * 0.12) / 2.5)) - (k % 4) * 70
        person(A, x, GROUND - (k // 4) * 30, 130, dir=1, robe=False, hat='helmet', spear=True, ph=t * 7 + k, arm=40, layer='ink')
        A.d['red'].ellipse((x + 30, GROUND - 200 - (k // 4) * 30, x + 54, GROUND - 176 - (k // 4) * 30), fill=230)
    if ph >= 3.5:
        person(A, 760, GROUND, 190, dir=-1, robe=True, hat='crown', female=True, fall=-85 * ease_out((ph - 3.5) / 0.6), arm=60, layer='mid')
    A.flush(cv)
    stamp(cv, seal('唐隆政变', 46), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('诛韦后 · 拥父即位', SERIF, 46, YAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 3.5) / 0.3))

def art_t_crown(A, cv, t, u):
    palace(A, 540, 1140, 600, layer='sheng')
    ground(A, GROUND)
    ming(A, 540, GROUND, 250, dir=1, arm=lerp(-8, 150, ease_out(u / P)))
    for k in range(6):
        person(A, 120 + k * 60 if k < 3 else 800 + (k - 3) * 60, GROUND, 130, dir=1 if k < 3 else -1, robe=True, hat='none', kneel=True, bow=50, arm=100, layer='mid')
    A.flush(cv)
    stamp(cv, seal('即位', 60), 860, 1020, t, t - u + P, rot=6)

def art_t_taiping(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='yan')
    ground(A, GROUND)
    person(A, 720, GROUND, 220, dir=-1, robe=True, hat='crown', female=True, fall=-85 * ease_out((u - 1.5 * P) / 0.6), arm=60, layer='ink')
    ming(A, 340, GROUND, 230, dir=1, arm=lerp(40, 150, ease_out((u - P) / 0.4)))
    A.flush(cv)
    stamp(cv, seal('太平公主', 44, INK), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('先天政变 · 独掌大权', SERIF, 46, YAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

# ================================================================ 第二回 开元盛世
def art_t_yaochong(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='sheng')
    ground(A, GROUND)
    ming(A, 720, GROUND - 30, 230, dir=-1, arm=40)
    for k in range(3):
        person(A, 200 + k * 140, GROUND, 200, dir=1, robe=True, hat='none', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2 + k)), layer='ink')
    A.flush(cv)
    for i, nm in enumerate(('姚崇', '宋璟', '张九龄')):
        stamp(cv, seal(nm, 38, SHENG if i % 2 else YAN), 200 + i * 140, 960, t, t - u + 0.4 + i * 0.5 * P)
    paste(cv, text_img('任用贤相', SERIF, 50, YAN, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_t_frugal(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    flames(A, 540, GROUND, 360, 160 * ease_out((u - P) / 0.8), t, n=4, seed=3, smoke=True)
    ground(A, GROUND)
    for k in range(int(clamp(u / P) * 6)):
        A.d['sheng'].rectangle((440 + k * 36, GROUND - 40 - (k % 2) * 20, 470 + k * 36, GROUND - 10), fill=255)
    A.flush(cv)
    paste(cv, text_img('焚珠玉锦绣于殿前', SERIF, 48, YAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def scene_kaiyuan(cv, t, c, k):
    """8-beat custom scene: 开元盛世 — granaries fill, households grow, caravans arrive; the census number rolls up;
    杜甫's lines on 开元 close it."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    q = ease_out(ph / 6)
    for i in range(6):
        x = 150 + i * 160
        h = 260 * clamp((ph - i * 0.4) / 3)
        A.d['sheng'].rectangle((x - 60, GROUND - h, x + 60, GROUND), fill=255)
        A.d['ink'].polygon([(x - 80, GROUND - h), (x + 80, GROUND - h), (x, GROUND - h - 60)], fill=255)
    for k in range(5):
        camel(A, lerp(1200, -100, ((t * 0.08 + k * 0.2) % 1)), GROUND - 300, 70, -1, t * 5 + k, layer='mid')
    A.flush(cv)
    households = int(lerp(706, 961, q) * 10000)
    fx = Art()
    chars_in(cv, fx, '开元盛世', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=74)
    fx.flush(cv)
    paste(cv, text_img(f'天下户口 {households}', SERIF, 46, YAN, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    if ph >= 5:
        type_in(cv, text_img('稻米流脂粟米白 公私仓廪俱丰实', SERIF, 40, SHENG, 'Black', bleed=False, spacing=2), W / 2, 1448, t, s0 + 5 * P, 0.5)

def art_t_music(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='yan')
    ground(A, GROUND)
    for k in range(6):
        sitter(A, 160 + k * 150, GROUND, 120, dir=1, bow=10, layer='mid')
    ming(A, 540, GROUND - 30, 220, dir=1, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 6)))
    A.flush(cv)
    stamp(cv, seal('梨园', 54), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('亲教乐工 · 梨园弟子', SERIF, 46, YAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_fengshan(A, cv, t, u):
    A.d['mid'].polygon([(160, GROUND), (540, 860), (920, GROUND)], fill=210)
    for k in range(10):
        x = lerp(220, 520, k / 9); y = lerp(GROUND, 900, k / 9)
        person(A, x, y, 60, dir=1, robe=True, hat='none', ph=t * 4 + k, arm=20, layer='ink')
    A.d['sheng'].rectangle((500, 840, 580, 870), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('泰山封禅', 46), 860, 1020, t, t - u + P, rot=6)

def art_t_zhangjiuling(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    ming(A, 720, GROUND - 30, 230, dir=-1, arm=lerp(20, 150, ease_out((u - P) / 0.5)))
    person(A, lerp(340, 80, ease_out((u - 1.8 * P) / P)), GROUND, 210, dir=-1 if u > 1.8 * P else 1, robe=True, hat='none', ph=t * 3 if u > 1.8 * P else None, arm=-8, layer='ink')
    person(A, 520, GROUND, 200, dir=1, robe=True, hat='none', bow=30, arm=100, layer='mid')
    A.flush(cv)
    stamp(cv, seal('张九龄罢相', 40, INK), 260, 1020, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('李林甫', 44), 520, 960, t, t - u + P, rot=5)

def art_t_tired(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='sheng')
    ground(A, GROUND)
    ming(A, 540, GROUND - 30, 230, dir=1, bow=lerp(0, 20, 0.5 + 0.5 * math.sin(t)), arm=-8, old=0.3)
    for k in range(int(clamp(u / (2 * P)) * 12)):
        A.d['wash'].rectangle((200 + (k % 6) * 120, 1260 - (k // 6) * 30, 280 + (k % 6) * 120, 1282 - (k // 6) * 30), fill=255)
    A.flush(cv)
    paste(cv, text_img('倦于政事 · 委政于相', SERIF, 46, YAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 天宝风流
def art_t_yang_meet(A, cv, t, u):
    for k in range(20):
        q = (t * 0.3 + k / 20) % 1
        A.d['wash'].ellipse((80 + (k * 47) % 920 - 30, lerp(1300, 700, q) - 8, 80 + (k * 47) % 920 + 30, lerp(1300, 700, q) + 8), fill=int(140 * math.sin(math.pi * q)))
    palace(A, 540, 1140, 520, layer='yan')
    ground(A, GROUND)
    ming(A, 360, GROUND, 230, dir=1, arm=lerp(20, 80, ease_out(u / P)), old=0.4)
    yang(A, 700, GROUND, 210, dir=-1, arm=30)
    A.flush(cv)
    stamp(cv, seal('华清宫', 50), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('杨玉环 · 本是寿王妃', SERIF, 46, YAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_t_guifei(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='sheng')
    ground(A, GROUND)
    ming(A, 720, GROUND - 30, 230, dir=-1, arm=lerp(20, 100, ease_out(u / 0.6)), old=0.4)
    yang(A, 360, GROUND, 210, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('贵妃', 60), 860, 1020, t, t - u + P, rot=6)

def art_t_nichang(A, cv, t, u):
    """6-beat: 霓裳羽衣舞 — on a terrace she dances; he plays the 羯鼓; ribbons of colour fill the frame."""
    ph = u / P
    A.d['sheng'].rectangle((240, 1160, 840, 1200), fill=255)
    ground(A, GROUND)
    yang(A, 540, 1160, 240, dir=1 if math.sin(t * 1.5) > 0 else -1, t=t, dance=True)
    ming(A, 860, GROUND, 200, dir=-1, arm=lerp(60, 160, abs(math.sin(t * 8))), old=0.4)
    A.d['red'].ellipse((760, GROUND - 120, 820, GROUND - 60), fill=255)
    cols = ['yan', 'sheng', 'grass', 'jian']
    for j, l in enumerate(cols):
        pts = [(lerp(200, 880, f), 1000 + j * 26 + 60 * math.sin(f * 8 + t * 3 + j)) for f in np.linspace(0, 1, 30)]
        A.d[l].line(pts, fill=220, width=6)
    A.flush(cv)
    type_in(cv, text_img('霓裳羽衣曲', SERIF, 50, YAN, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('羯鼓', 44, INK), 860, 960, t, t - u + P, rot=6)

def art_t_lychee(A, cv, t, u):
    """6-beat: 一骑红尘 — a rider gallops across, a basket of lychees; relay horses collapse along the road; she smiles."""
    ph = u / P
    for k in range(6):
        x = 140 + k * 170
        A.d['mid'].polygon([(x - 120, GROUND), (x, GROUND - 260), (x + 120, GROUND)], fill=200)
    ground(A, GROUND)
    x = lerp(-150, 1250, (ph / 5.5))
    rider(A, x, GROUND, 150, 1, t * 14, layer='ink')
    lychee(A, x - 60, GROUND - 170, 50)
    for k in range(int(ph)):
        horse(A, 200 + k * 160, GROUND, 110, dir=1, ph=0, moving=False, head_down=0.6, layer='mid')
    for k in range(10):
        q = (t * 2 + k / 10) % 1
        A.d['dune'].ellipse((x - 80 - 160 * q - 20, GROUND - 20 - 30 * q, x - 80 - 160 * q + 20, GROUND + 10 - 30 * q), fill=int(200 * (1 - q)))
    A.flush(cv)
    type_in(cv, text_img('一骑红尘妃子笑', SERIF, 50, YAN, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('无人知是荔枝来', SERIF, 50, INK, 'Black', bleed=False, spacing=6), W / 2, 835, t, t - u + 2 * P, 0.5)
    stamp(cv, seal('杜牧诗', 40, INK), 860, 1000, t, t - u + 0.4, rot=6)

def art_t_yangguozhong(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 230, dir=1, robe=True, hat='none', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    for k in range(6):
        person(A, 120 + k * 60 if k < 3 else 800 + (k - 3) * 60, GROUND, 130, dir=1 if k < 3 else -1, robe=True, hat='none', bow=40, arm=100, layer='mid')
    A.flush(cv)
    stamp(cv, seal('杨国忠', 50, INK), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('外戚专权 · 一身领四十余使', SERIF, 42, YAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_t_anlushan(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='sheng')
    ground(A, GROUND)
    ming(A, 720, GROUND - 30, 220, dir=-1, arm=lerp(40, 110, 0.5 + 0.5 * math.sin(t)), old=0.5)
    d = A.d['ink']
    x = 360
    d.ellipse((x - 120, GROUND - 260, x + 120, GROUND - 40), fill=255)
    d.ellipse((x - 40, GROUND - 340, x + 40, GROUND - 260), fill=255)
    for sx in (-1, 1):
        d.line((x + sx * 40, GROUND - 60, x + sx * 50, GROUND), fill=255, width=20)
    A.flush(cv)
    stamp(cv, seal('安禄山', 50, INK), 260, 1020, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('身兼三镇节度使', SERIF, 46, YAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第四回 渔阳鼙鼓
def art_t_drums(A, cv, t, u):
    ground(A, GROUND)
    for k in range(12):
        rider(A, lerp(-300, 1200, ((t * 0.18 + k * 0.083) % 1)), GROUND - (k % 3) * 40, 100, 1, t * 13 + k, layer='ink', spear=True)
    for k in range(3):
        A.d['red'].ellipse((160 + k * 80, 940, 220 + k * 80, 1000), fill=255)
    A.flush(cv)
    type_in(cv, text_img('渔阳鼙鼓动地来', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('范阳起兵', 44, INK), 860, 1040, t, t - u + P, rot=6)

def art_t_tongguan(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='潼关', layer='mid', open_=ease_out((u - P) / P))
    flames(A, 540, 1100, 700, 200 * ease_out((u - 1.5 * P) / 0.8), t, n=7, seed=9, smoke=True)
    ground(A, GROUND)
    for k in range(10):
        person(A, 120 + k * 90, GROUND, 110, dir=-1, robe=False, hat='helmet', fall=-80 * ease_out((u - P - k * 0.08) / 0.4), arm=40, layer='mid')
    A.flush(cv)
    paste(cv, text_img('潼关失守 · 长安门户大开', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_t_flee(A, cv, t, u):
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    city_wall(A, 600, 1020, 1100, gate_x=810, label='延秋门', layer='mid', open_=1.0)
    ground(A, GROUND)
    carriage(A, lerp(800, -200, ease_out(u / (3 * P))), GROUND, 130, dir=-1, wheel=t * 6, ph=t * 8, layer='ink')
    for k in range(4):
        rider(A, lerp(900, -100, ease_out((u - k * 0.1) / (3 * P))) + k * 80, GROUND, 100, -1, t * 11 + k, layer='mid', spear=True)
    A.flush(cv)
    paste(cv, text_img('黎明出逃 · 百官不知', SERIF, 46, YAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_mawei(A, cv, t, u):
    """8-beat set piece: 马嵬坡 — the guards halt; 杨国忠 is killed; soldiers refuse to move; she is led away to the
    pear tree; a white silk; the emperor covers his face."""
    ph = u / P
    A.d['ink'].line((820, GROUND, 840, 900), fill=255, width=20)
    for k in range(5):
        a = -math.pi / 2 + (k - 2) * 0.45
        A.d['ink'].line((840, 960, 840 + 130 * math.cos(a), 960 + 90 * math.sin(a)), fill=255, width=6)
    for k in range(12):
        A.d['wash'].ellipse((700 + (k * 23) % 280 - 8, 880 + (k * 31) % 120 - 8, 700 + (k * 23) % 280 + 8, 880 + (k * 31) % 120 + 8), fill=230)
    ground(A, GROUND)
    for k in range(8):
        person(A, 120 + k * 60, GROUND, 140, dir=1, robe=False, hat='helmet', spear=True, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 6 + k)) if ph < 5 else 40, layer='ink')
    ming(A, 640, GROUND, 220, dir=-1, old=0.8, bow=30 if ph > 5.5 else 0, arm=lerp(40, 170, ease_out((ph - 5.5) / 0.6)))
    if ph < 4:
        yang(A, 740, GROUND, 200, dir=-1, arm=30)
    elif ph < 5.5:
        yang(A, lerp(740, 820, ease_out((ph - 4) / 1)), GROUND, 200, dir=1, ph=t * 2, arm=-8)
    else:
        A.d['wash'].line((800, 980, 800, 1200), fill=255, width=6)
    A.flush(cv)
    lab = '六军不发' if ph < 4 else ('宛转蛾眉马前死' if ph < 6 else '君王掩面救不得')
    paste(cv, text_img(lab, SERIF, 50, ZHU if ph >= 4 else INK, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    stamp(cv, seal('马嵬驿', 46, INK), 260, 1040, t, t - u + 0.4, rot=-5)

def art_t_shu(A, cv, t, u):
    for k in range(6):
        x = 120 + k * 170
        A.d['mid'].polygon([(x - 130, GROUND), (x, GROUND - 460 - 60 * (k % 2)), (x + 130, GROUND)], fill=200)
    for k in range(60):
        q = (t * 1.0 + k / 60) % 1
        A.d['wash'].line((80 + (k * 17) % 920, lerp(620, 1420, q), 76 + (k * 17) % 920, lerp(620, 1420, q) + 22), fill=180, width=2)
    pts = [(x, GROUND - 160 - 80 * math.sin(x / 140)) for x in range(80, W - 79, 20)]
    A.d['wash'].line(pts, fill=255, width=10)
    i = min(len(pts) - 1, int(clamp(u / (3 * P)) * (len(pts) - 1)))
    horse(A, pts[i][0], pts[i][1], 80, dir=1, ph=t * 4, layer='ink')
    A.flush(cv)
    stamp(cv, seal('入蜀', 54), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('夜雨闻铃肠断声', SERIF, 48, YAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_t_suzong(A, cv, t, u):
    palace(A, 540, 1140, 520, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 30, 220, dir=1, robe=True, hat='crown', arm=lerp(-8, 150, ease_out(u / P)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('灵武', 54), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('太子即位 · 他成了太上皇', SERIF, 46, YAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第五回 此恨绵绵
def art_t_return(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='长安', layer='mid', open_=1.0)
    ground(A, GROUND)
    carriage(A, lerp(-200, 540, ease_out(u / (2.5 * P))), GROUND, 120, dir=1, wheel=t * 4, ph=t * 6, moving=u < 2.5 * P, layer='ink')
    A.flush(cv)
    stamp(cv, seal('还京', 54), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('归来池苑皆依旧', SERIF, 48, YAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_t_nannei(A, cv, t, u):
    """6-beat: 南内 — the old emperor alone in an empty hall; autumn leaves; the lamp burns down."""
    ph = u / P
    A.d['mid'].rectangle((160, 860, 920, GROUND), fill=180)
    for k in range(30):
        q = (t * 0.4 + k / 30) % 1
        A.d['sheng'].ellipse((80 + (k * 37) % 920 - 8, lerp(620, 1420, q) - 4, 80 + (k * 37) % 920 + 8, lerp(620, 1420, q) + 4), fill=int(200 * (1 - q)))
    ground(A, GROUND)
    sitter(A, 540, GROUND, 200, dir=1, bow=lerp(10, 40, ease_out(ph / 4)))
    lamp(A, 760, GROUND, 50, t, glow=clamp(1 - ph / 5))
    A.flush(cv)
    type_in(cv, text_img('夕殿萤飞思悄然', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('孤灯挑尽未成眠', SERIF, 48, YAN, 'Black', bleed=False, spacing=6), W / 2, 835, t, t - u + 2 * P, 0.5)

def art_t_ximei(A, cv, t, u):
    palace(A, 760, GROUND, 400, layer='mid')
    ground(A, GROUND)
    ming(A, lerp(540, 200, ease_out(u / (3 * P))), GROUND, 200, dir=-1, ph=t * 2, old=1.0, arm=-8)
    for k in range(2):
        person(A, lerp(700, 360, ease_out(u / (3 * P))) + k * 70, GROUND, 190, dir=-1, robe=False, hat='helmet', spear=True, ph=t * 2 + k, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('李辅国', 46, INK), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('被迫迁居西内', SERIF, 48, YAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_t_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    ming(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('抑郁而终 · 年七十八', SERIF, 48, YAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_t_changhen(A, cv, t, u):
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='yan')
    sitter(A, 300, GROUND, 200, dir=1, bow=15)
    A.flush(cv)
    stamp(cv, seal('白居易', 46, INK), 860, 1020, t, t - u + 0.4, rot=6)
    type_in(cv, text_img('天长地久有时尽', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('此恨绵绵无绝期', SERIF, 52, YAN, 'Black', bleed=False, spacing=6), W / 2, 835, t, t - u + 1.6 * P, 0.5)

def art_t_turning(A, cv, t, u):
    ground(A, GROUND)
    p = ease_out(u / (2.5 * P))
    pts = [(lerp(140, 940, f), 1260 - 360 * math.sin(math.pi * min(f / 0.55, 1) * 0.5) + (f > 0.55) * 500 * max(f - 0.55, 0) ** 1.2) for f in np.linspace(0, p, 40)]
    if len(pts) > 1:
        A.d['yan'].line(pts, fill=255, width=10)
    A.flush(cv)
    paste(cv, text_img('盛唐由此转衰', SERIF, 50, YAN, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_t_legacy(A, cv, t, u):
    pipa(A, 880, 1380, 120, strings=0, t=t)

def art_t_title(A, cv, t, u):
    palace(A, 820, 1460, 400, layer='sheng')
    ming(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '临淄郡王'), 48: ('第二回', '开元盛世'), 80: ('第三回', '天宝风流'),
            112: ('第四回', '渔阳鼙鼓'), 144: ('第五回', '此恨绵绵')}

CARDS = [
    C(0, 2, 'empire', 'num', num='开元盛世', line='大唐巅峰', art=art_t_hook_peak),
    C(2, 4, 'war', 'num', num='安史之乱', line='一手造成', art=art_t_hook_fall),
    C(4, 6, 'works', 'num', num='一曲霓裳', line='一段千古爱情', art=art_t_hook_love),
    C(6, 8, 'death', 'num', num='马嵬坡下', line='他没能救她', art=art_t_hook_mawei),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=685, main='生于洛阳', sub='名隆基', art=art_t_birth),
    C(22, 26, 'court', 'card', year=692, main='七岁斥武懿宗', sub='小小年纪 气势凌人', art=art_t_wuyi),
    C(26, 30, 'night', 'card', year=693, main='母亲失踪', sub='被武则天秘密处死', art=art_t_mother),
    C(30, 34, 'life', 'card', year=708, main='潞州别驾', sub='广结豪杰', art=art_t_luzhou),
    C(34, 40, 'war', 'card', year=710, main='唐隆政变', sub='夜入宫城', art=art_t_tanglong),
    C(40, 44, 'empire', 'card', year=712, main='登基', sub='睿宗传位', art=art_t_crown),
    C(44, 48, 'night', 'card', year=713, main='诛太平公主', sub='先天政变', art=art_t_taiping),
    C(48, 50, 'empire', 'chapter'),
    C(50, 54, 'court', 'card', year=713, main='任用贤相', sub='励精图治', art=art_t_yaochong),
    C(54, 58, 'life', 'card', year=714, main='焚珠玉', sub='崇尚节俭', art=art_t_frugal),
    C(58, 66, 'empire', 'kaiyuan', year=720),
    C(66, 70, 'works', 'card', year=725, main='梨园', sub='精通音律', art=art_t_music),
    C(70, 74, 'empire', 'card', year=725, main='泰山封禅', sub='功成告天', art=art_t_fengshan),
    C(74, 78, 'night', 'card', year=736, main='罢张九龄', sub='口蜜腹剑者上位', art=art_t_zhangjiuling),
    C(78, 80, 'fate', 'card', year=740, main='倦政', sub='开元已近尾声', art=art_t_tired),
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'life', 'card', year=740, main='初见玉环', sub='温泉宫中', art=art_t_yang_meet),
    C(86, 90, 'court', 'card', year=745, main='册为贵妃', sub='后宫佳丽三千人', art=art_t_guifei),
    C(90, 96, 'works', 'card', year=747, main='霓裳羽衣', sub='君王亲击羯鼓', art=art_t_nichang),
    C(96, 102, 'fate', 'card', year=750, main='荔枝', sub='驿马传送', note='一说 来自四川涪州', art=art_t_lychee),
    C(102, 106, 'war', 'card', year=751, main='宠信安禄山', sub='边将坐大', art=art_t_anlushan),
    C(106, 112, 'night', 'card', year=752, main='杨国忠', sub='继李林甫为相', art=art_t_yangguozhong),
    C(112, 114, 'war', 'chapter'),
    C(114, 118, 'war', 'card', year=755, main='安史之乱', sub='天下震动', art=art_t_drums),
    C(118, 122, 'death', 'card', year=756, main='潼关失守', sub='哥舒翰被迫出战', art=art_t_tongguan),
    C(122, 126, 'night', 'card', year=756, main='弃京出逃', sub='仓皇西奔', art=art_t_flee),
    C(126, 134, 'death', 'card', year=756, main='马嵬坡', sub='禁军哗变', note='长恨歌所述', art=art_t_mawei),
    C(134, 138, 'fate', 'card', year=756, main='幸蜀', sub='栈道夜雨', art=art_t_shu),
    C(138, 144, 'court', 'card', year=756, main='肃宗即位', sub='被尊为太上皇', art=art_t_suzong),
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'fate', 'card', year=757, main='还京', sub='长安收复', art=art_t_return),
    C(150, 156, 'night', 'card', year=758, main='南内', sub='孤独的太上皇', art=art_t_nannei),
    C(156, 160, 'court', 'card', year=760, main='迁居西内', sub='宦官逼迁', art=art_t_ximei),
    C(160, 164, 'death', 'card', year=762, main='驾崩', sub='神龙殿', art=art_t_death),
    C(164, 168, 'works', 'card', year=806, main='长恨歌', sub='白居易为他们写诗', art=art_t_changhen),
    C(168, 170, 'end', 'card', year=2026, main='盛极而衰', sub='他的一生 就是大唐的转折', art=art_t_turning),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='肆拾叁', col=YAN, acc=SHENG, born=685, died=762,
    hook_q='开创盛世的是他 · 毁掉盛世的也是他？',
    name_line='李隆基 · 唐玄宗', name='唐玄宗', seal='明皇', title_art=art_t_title,
    q1='一代明君？', q2='亡国昏君？',
    end_art=art_t_legacy, end_big='此恨绵绵', end_seal='明皇',
    end_l1='前半生他开创了开元', end_l2='后半生他葬送了天宝',
    end_brush='盛极而衰', end_ask='如果他早死二十年 会怎样？评论区聊聊', next='隋炀帝'),
    scenes=dict(chapter=scene_chapter, kaiyuan=scene_kaiyuan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
