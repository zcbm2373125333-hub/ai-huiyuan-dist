"""千古人物志 · 第贰拾陆集 · 司马迁 (约前145–约前86)
Look: 灰紫 + 烛黄, 编绳 (slip-binding cord) corner borders, a 毛笔 chapter card that writes one more stroke of 史 each chapter.
Set pieces: custom 8-beat scene 'journey' (二十南游 route map), 6-beat 父亲临终, 8-beat 宫刑 (the cell: death or the book),
6-beat 发愤著书, 8-beat 一百三十篇 (the five sections stack up).
Years are stored negative (BC); epkit prints 公元前.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zhangqian as Zq       # engine + helpers (previous episode)
import render_xiangyu as Xy
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
from render_kongzi import slips, bundle
from render_quyuan import river

F.RIPPLE = False
MAUVE = (88, 70, 100)               # 灰紫
CANDLEY = (216, 176, 72)            # 烛黄
S.LAYERS.append(('mauve', MAUVE, 0.88, 1.0))
S.LAYERS.append(('candley', CANDLEY, 0.85, 2.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='史', life='迁', court='汉', night='狱', war='陵', empire='汉', works='记', fate='忍', death='刑', end='史')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (CANDLEY, 220, (W * 0.5, 820))
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (MAUVE, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

SHELVES = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(SHELVES)
for _x0 in (70, W - 210):
    for _r in range(4):
        _y = 1180 + _r * 70
        _d.rectangle((_x0, _y, _x0 + 140, _y + 6), fill=MAUVE + (40,))
        for _k in range(6):
            _d.ellipse((_x0 + 8 + _k * 22, _y - 26, _x0 + 26 + _k * 22, _y - 4), outline=MAUVE + (44,), width=2)
MTN_COL = {'night': (36, 32, 42), 'death': (58, 56, 62), 'war': (98, 60, 50), 'works': (100, 90, 110)}
def draw_background(t, theme):
    """石室金匮: soft ranges framed by faint shelves of scrolls at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 180, 190), (146, 136, 156), MTN_COL.get(theme, (106, 96, 120))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(SHELVES)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """编绳: three bamboo slips bound by two cords in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = MAUVE + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=col, width=3); d.line((x, y, x, y + sy * 180), fill=col, width=3)
        for k in range(3):
            xx = x + sx * (16 + k * 18)
            d.rectangle((min(xx, xx + sx * 12), min(y + sy * 14, y + sy * 110), max(xx, xx + sx * 12), max(y + sy * 14, y + sy * 110)), fill=CANDLEY + (200,))
        for yy in (40, 86):
            d.line((x + sx * 10, y + sy * yy, x + sx * 74, y + sy * yy), fill=col, width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def sima(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, beard=True, **kw):
    """司马迁: scholar-official, 进贤冠 (slanted ridge cap); beard (lost after the punishment)."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    d = A.d[layer]
    if up:
        d.polygon([(x - dir * 0.07 * h, y - 0.95 * h), (x + dir * 0.06 * h, y - 0.95 * h), (x + dir * 0.02 * h, y - 1.1 * h), (x - dir * 0.06 * h, y - 1.04 * h)], fill=255)
        if beard:
            d.polygon([(x + dir * 0.0, y - 0.86 * h), (x + dir * 0.07 * h, y - 0.86 * h), (x + dir * 0.03 * h, y - 0.7 * h)], fill=255)
    return hand

def brush(A, x, y, s, ang=-0.5, layer='ink'):
    ca, sa = math.cos(ang), math.sin(ang)
    A.d[layer].line((x, y, x + s * ca, y + s * sa), fill=255, width=max(3, int(0.06 * s)))
    A.d[layer].polygon([(x, y), (x - 0.12 * s * ca + 0.04 * s * sa, y - 0.12 * s * sa - 0.04 * s * ca),
                        (x - 0.22 * s * ca, y - 0.22 * s * sa), (x - 0.12 * s * ca - 0.04 * s * sa, y - 0.12 * s * sa + 0.04 * s * ca)], fill=255)

def bars(A, x0, x1, top, base, n=8, layer='ink'):
    for k in range(n):
        x = lerp(x0, x1, k / (n - 1))
        A.d[layer].rectangle((x - 6, top, x + 6, base), fill=255)
    A.d[layer].rectangle((x0 - 10, top - 14, x1 + 10, top), fill=255)

STROKES = [((0.30, 0.10), (0.30, 0.45)), ((0.30, 0.10), (0.70, 0.10)), ((0.70, 0.10), (0.70, 0.45)), ((0.30, 0.45), (0.70, 0.45)),
           ((0.50, 0.00), (0.50, 0.70)), ((0.50, 0.70), (0.15, 1.00)), ((0.40, 0.62), (0.90, 1.00))]
def shi_glyph(A, cx, cy, s, n, p=1.0, layer='ink'):
    """the character 史 drawn as n broad strokes (the last one growing by p)."""
    for i in range(min(n, len(STROKES))):
        (u0, v0), (u1, v1) = STROKES[i]
        q = 1 if i < n - 1 else ease_out(p)
        x0, y0 = cx + (u0 - 0.5) * s, cy + (v0 - 0.5) * s
        x1, y1 = cx + (lerp(u0, u1, q) - 0.5) * s, cy + (lerp(v0, v1, q) - 0.5) * s
        A.d[layer].line((x0, y0, x1, y1), fill=255, width=int(0.07 * s))
    return (cx + (lerp(STROKES[min(n, 7) - 1][0][0], STROKES[min(n, 7) - 1][1][0], ease_out(p)) - 0.5) * s,
            cy + (lerp(STROKES[min(n, 7) - 1][0][1], STROKES[min(n, 7) - 1][1][1], ease_out(p)) - 0.5) * s)

# ================================================================ chapter card
CH = {16: 2, 48: 3, 80: 4, 112: 6, 144: 7}
def art_brush_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = CH.get(kb, 3)
    tip = shi_glyph(A, 540, 960, 380, n, p=u / (1.2 * P))
    brush(A, tip[0], tip[1], 240, ang=-0.9)
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_brush_chapter)
    ink_in(cv, text_img(no, SERIF, 56, MAUVE, 'Black', bleed=False, spacing=12), W / 2, 1290, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_s_hook_words(A, cv, t, u):
    n = min(48, int(clamp(u / (1.6 * P)) * 48) + 6)
    slips(A, 540 - n * 19 / 2, 1300, n, 420, layer='mauve')
    ground(A, GROUND)

def art_s_hook_cell(A, cv, t, u):
    A.d['mid'].rectangle((240, 860, 840, GROUND), fill=190)
    sitter(A, 540, GROUND, 200, dir=1, bow=lerp(10, 40, ease_out(u / (1.6 * P))))
    bars(A, 260, 820, 880, GROUND, n=10)
    ground(A, GROUND)

def art_s_hook_130(A, cv, t, u):
    ground(A, GROUND)
    n = min(130, int(clamp(u / (1.6 * P)) * 130) + 1)
    for i in range(n):
        x = 110 + (i % 26) * 34; y = GROUND - 30 - (i // 26) * 44
        A.d['mauve' if i % 7 else 'candley'].rectangle((x - 12, y - 36, x + 12, y), fill=255)

def art_s_hook_scale(A, cv, t, u):
    A.d['mid'].polygon([(200, GROUND), (540, 860), (880, GROUND)], fill=200)
    p = ease_out(u / (1.4 * P))
    for k in range(5):
        q = (t * 0.6 + k / 5) % 1
        A.d['wash'].ellipse((760 + 60 * math.sin(k) - 20, lerp(900, 1300, q) - 6, 760 + 60 * math.sin(k) + 20, lerp(900, 1300, q) + 6), fill=int(200 * (1 - q) * p))
    ground(A, GROUND)

# ================================================================ 第一回 龙门少年
def art_s_longmen(A, cv, t, u):
    for k, x in enumerate((240, 840)):
        A.d['mid'].polygon([(x - 200, GROUND), (x - 40 + 80 * k, 900), (x + 200, GROUND)], fill=220)
    A.d['ocean'].polygon([(440, 900), (640, 900), (700, GROUND), (380, GROUND)], fill=170)
    waves(A, 1100, t, rows=4, amp=6, x0=420, x1=660, speed=3)
    for k in range(3):
        Zq.sheep(A, 160 + k * 80, GROUND, 50)
    person(A, 860, GROUND, 140, dir=-1, robe=False, hat='knot', arm=lerp(20, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('龙门', 56), 540, 860, t, t - u + P)

def art_s_reading(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 340, layer='mauve')
    sitter(A, 320, GROUND, 160, dir=1, bow=15)
    scroll(A, 560, GROUND - 120, 220, 60, u / 0.5)
    for k in range(int(clamp(u / (2 * P)) * 6)):
        bundle(A, 800 + (k % 2) * 90, GROUND - (k // 2) * 50, 70, layer='mauve')
    A.flush(cv)
    type_in(cv, text_img('年十岁则诵古文', SERIF, 46, MAUVE, 'Black', bleed=False, spacing=6), W / 2, 880, t, t - u + P, 0.4)

def art_s_father(A, cv, t, u):
    r = random.Random(4)
    for k in range(50):
        x, y = r.uniform(120, 960), r.uniform(660, 1060)
        tw = max(0.5, 2 + 2 * math.sin(t * 2 + k))
        A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)
    for k in range(6):
        a = k * 1.1
        A.d['candley'].line((300 + 80 * k, 760 + 40 * math.sin(a), 380 + 80 * k, 780 + 40 * math.sin(a + 1)), fill=200, width=3)
    ground(A, GROUND)
    person(A, 420, GROUND, 260, dir=1, robe=True, hat='none', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t)), layer='ink')
    sima(A, 640, GROUND, 150, dir=-1, beard=False, arm=40)
    A.flush(cv)
    stamp(cv, seal('司马谈', 46, INK), 860, 1100, t, t - u + P, rot=6)

TRAVEL = [('长安', 360, 980), ('江淮', 640, 1060), ('会稽', 840, 1220), ('九疑', 520, 1360), ('沅湘', 380, 1280),
          ('汶泗', 700, 900), ('齐鲁', 820, 840), ('彭城', 740, 1000), ('长安', 360, 980)]
def scene_journey(cv, t, c, k):
    """8-beat custom scene: 二十南游 — a route traced across a map; one stop per beat; each stop shows what he sought there."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['wash'].rounded_rectangle((120, 760, 960, 1420), radius=24, fill=200)
    A.d['ocean'].line([(140, 1000), (500, 1040), (960, 1020)], fill=150, width=18)
    A.d['ocean'].line([(140, 1180), (480, 1160), (960, 1200)], fill=130, width=12)
    stops = min(len(TRAVEL), int(ph) + 2)
    pts = [(x, y) for _, x, y in TRAVEL[:stops]]
    if stops >= 2:
        f = clamp(ph - (stops - 2))
        last = (lerp(pts[-2][0], pts[-1][0], f), lerp(pts[-2][1], pts[-1][1], f))
        A.d['red'].line(pts[:-1] + [last], fill=220, width=6)
        sima(A, last[0], last[1] + 10, 90, dir=1 if pts[-1][0] >= pts[-2][0] else -1, ph=t * 6, arm=20)
    A.flush(cv)
    for i, (nm, x, y) in enumerate(TRAVEL[:stops]):
        if i == len(TRAVEL) - 1: continue
        stamp(cv, seal(nm, 32, ZHU if i == 0 else MAUVE), x, y - 50, t, s0 + max(0, i - 1) * P + 0.3)
    NOTES = ['', '江淮', '上会稽 探禹穴', '窥九疑', '浮沅湘', '北涉汶泗', '讲业齐鲁 观孔子遗风', '厄困鄱薛彭城', '归长安']
    i = min(len(NOTES) - 1, max(0, stops - 1))
    fx = Art()
    chars_in(cv, fx, '二十南游', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=30)
    fx.flush(cv)
    paste(cv, text_img(NOTES[i] or '公元前一二六年', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('行万里路 · 为写史积累见闻', SERIF, 42, MAUVE, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 6) / 0.4))

def art_s_langzhong(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='mauve')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 230, dir=1, robe=True, hat='crown', arm=20, layer='ink')
    sima(A, 300, GROUND, 200, dir=1, arm=40)
    person(A, 780, GROUND, 200, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('郎中', 54), 860, 880, t, t - u + P, rot=6)

def art_s_southwest(A, cv, t, u):
    for k in range(6):
        x = 120 + k * 170
        A.d['grass'].polygon([(x - 130, GROUND), (x, GROUND - 420 - 80 * (k % 2)), (x + 130, GROUND)], fill=200)
    pts = [(x, GROUND - 160 - 70 * math.sin(x / 170)) for x in range(80, W - 79, 20)]
    A.d['mauve'].line(pts, fill=220, width=6)
    i = min(len(pts) - 1, int(clamp(u / (3 * P)) * (len(pts) - 1)))
    horse(A, pts[i][0], pts[i][1], 90, dir=1, ph=t * 6, layer='ink')
    sima(A, pts[i][0] - 6, pts[i][1] - 70, 90, dir=1, arm=20)
    A.flush(cv)
    stamp(cv, seal('巴蜀以南', 44), 860, 860, t, t - u + P, rot=6)

def art_s_fengshan(A, cv, t, u):
    A.d['mid'].polygon([(160, GROUND), (540, 860), (920, GROUND)], fill=200)
    A.d['candley'].rectangle((470, 840, 610, 880), fill=255)
    for k in range(10):
        x = lerp(200, 520, k / 9); y = lerp(GROUND, 900, k / 9)
        person(A, x, y, 60, dir=1, robe=True, hat='none', ph=t * 4 + k, arm=20, layer='ink')
    ground(A, GROUND)
    person(A, 880, GROUND, 160, dir=-1, robe=True, hat='none', bow=30, arm=-8, layer='mid')
    A.flush(cv)
    stamp(cv, seal('泰山', 56), 300, 880, t, t - u + 0.5, rot=-5)

# ================================================================ 第二回 父子之托
def art_s_deathbed(A, cv, t, u):
    """6-beat: 父亲临终 — the father on his bed grips his son's hand; the lamp gutters; the charge is spoken."""
    ph = u / P
    A.d['mid'].rectangle((300, 1180, 780, 1240), fill=230)
    A.d['ink'].rectangle((280, 1240, 800, 1270), fill=255)
    person(A, 520, 1180, 220, dir=1, robe=True, hat='knot', fall=-80, arm=lerp(0, 60, ease_out(ph / 1.5)), layer='ink')
    sima(A, 820, GROUND, 200, dir=-1, kneel=True, bow=lerp(10, 40, ease_out(ph / 3)), arm=110)
    lamp(A, 200, GROUND, 60, t, glow=clamp(1 - (ph - 4) / 1.5))
    ground(A, GROUND)
    A.flush(cv)
    for i, ln in enumerate(('余死 汝必为太史', '无忘吾所欲论著矣')):
        if ph >= 1 + i * 1.6:
            type_in(cv, text_img(ln, SERIF, 46, ZHU if i else INK, 'Black', bleed=False, spacing=4), W / 2, 830 + i * 70, t, t - u + (1 + i * 1.6) * P, 0.5)

def art_s_taishiling(A, cv, t, u):
    ground(A, GROUND)
    for r in range(3):
        for c2 in range(7):
            x = 160 + c2 * 120; y = 980 + r * 110
            A.d['mauve'].rectangle((x - 46, y, x + 46, y + 80), outline=255, width=4)
            if (r * 7 + c2) < int(clamp(u / (2 * P)) * 21):
                bundle(A, x, y + 76, 60, layer='candley')
    sima(A, 540, GROUND, 160, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('太史令', 50), 860, 880, t, t - u + 0.4, rot=6)

def art_s_calendar(A, cv, t, u):
    p = ease_out(u / (2 * P))
    A.d['mauve'].ellipse((300, 800, 780, 1280), outline=255, width=8)
    A.d['candley'].ellipse((480, 980, 600, 1100), fill=255)
    for k in range(int(p * 24)):
        a = k * 2 * math.pi / 24 + t * 0.2
        A.d['ink'].line((540 + 220 * math.cos(a), 1040 + 220 * math.sin(a), 540 + 240 * math.cos(a), 1040 + 240 * math.sin(a)), fill=255, width=4)
    for k in range(12):
        a = k * 2 * math.pi / 12 - t * 0.3
        A.d['wash'].ellipse((540 + 160 * math.cos(a) - 6, 1040 + 160 * math.sin(a) - 6, 540 + 160 * math.cos(a) + 6, 1040 + 160 * math.sin(a) + 6), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('太初', 56), 860, 860, t, t - u + P, rot=6)

def art_s_begin(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 400, layer='mauve')
    sitter(A, 300, GROUND, 220, dir=1, bow=15)
    n = int(clamp(u / (3 * P)) * 20) + 2
    slips(A, 400, GROUND - 74, n, 60, layer='candley', tied=False)
    brush(A, 400 + n * 19, GROUND - 160, 120, ang=-1.2)
    A.flush(cv)
    type_in(cv, text_img('上起黄帝', SERIF, 48, MAUVE, 'Black', bleed=False, spacing=6), 330, 880, t, t - u + 0.4, 0.4)
    type_in(cv, text_img('下至太初', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), 760, 880, t, t - u + 1.5 * P, 0.4)

def art_s_losers(A, cv, t, u):
    ground(A, GROUND)
    Xy.xiang(A, 330, GROUND, 250, dir=1, ji=True, arm=40)
    person(A, 720, GROUND, 220, dir=-1, robe=False, hat='knot', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('项羽本纪', 40), 330, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('陈涉世家', 40), 720, 880, t, t - u + 1.5 * P, rot=5)

def art_s_lingout(A, cv, t, u):
    ground(A, GROUND)
    for k in range(16):
        x = lerp(-100, 600, ease_out(u / (3 * P))) - (k % 8) * 70
        person(A, x, GROUND - (k // 8) * 40, 100, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, arm=40, layer='ink' if k // 8 == 0 else 'mid')
    for k in range(10):
        rider(A, 1100 - (k % 5) * 70 - 60 * ease_out(u / (3 * P)), GROUND - (k // 5) * 50, 100, -1, t * 10 + k, layer='mid', spear=True)
    A.flush(cv)
    stamp(cv, seal('李陵', 54), 300, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('步卒五千', SERIF, 52, MAUVE, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_s_surrender(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='mauve')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 230, dir=1, robe=True, hat='crown', arm=lerp(20, 140, ease_out((u - P) / 0.5)), layer='ink')
    for k in range(6):
        x = 120 + k * 60 if k < 3 else 760 + (k - 3) * 70
        person(A, x, GROUND, 150, dir=1 if x < 540 else -1, robe=True, hat='none', bow=30, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('降匈奴', 50, INK), 860, 860, t, t - u + 0.4, rot=6)

# ================================================================ 第三回 李陵之祸
def art_s_defend(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mauve')
    ground(A, GROUND)
    person(A, 760, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t)), layer='ink')
    sima(A, 330, GROUND, 230, dir=1, arm=lerp(40, 130, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    stamp(cv, seal('仗义执言', 44), 260, 880, t, t - u + P, rot=-5)

def art_s_arrest(A, cv, t, u):
    ground(A, GROUND)
    sima(A, 540, GROUND, 220, dir=1, beard=True, arm=-8)
    for k, sx in enumerate((-1, 1)):
        x = lerp(540 + sx * 500, 540 + sx * 150, ease_out(u / (1.5 * P)))
        person(A, x, GROUND, 210, dir=-sx, robe=False, hat='helmet', arm=lerp(20, 100, ease_out((u - 1.5 * P) / 0.4)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('诬上', 56, INK), 860, 860, t, t - u + 1.6 * P, rot=6)

def art_s_poor(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((340, 1100, 740, GROUND), fill=200)
    A.d['ink'].rectangle((340, 1100, 740, GROUND), outline=255, width=6)
    A.d['wash'].rectangle((380, 1140, 700, GROUND - 30), fill=255)
    for k in range(4):
        x = 160 + k * 240
        person(A, x, GROUND, 150, dir=1 if k % 2 else -1, robe=True, hat='none', ph=t * 3 + k, arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('家贫 不足以自赎', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 880, 1, clamp((u - 0.5 * P) / 0.3))

def art_s_punish(A, cv, t, u):
    """8-beat set piece: 宫刑 — the dark cell; a rope and the scroll lie side by side; the lamp sways between them;
    he turns from the rope to the scroll."""
    ph = u / P
    A.d['mid'].rectangle((160, 820, 920, GROUND), fill=170)
    bars(A, 180, 900, 840, GROUND, n=12)
    A.d['ink'].line((330, 860, 330, 1080), fill=255, width=6)
    A.d['ink'].ellipse((300, 1070, 360, 1130), outline=255, width=6)
    scroll(A, 760, 1260, 200, 60, 1.0, layer='candley')
    look = ease_out((ph - 4) / 1.5)
    sitter(A, 540, GROUND, 190, dir=-1 if ph < 4 else 1, bow=lerp(40, 10, look))
    lamp(A, lerp(380, 700, 0.5 + 0.5 * math.sin(t * 0.8)) if ph < 4 else 700, GROUND, 50, t, glow=lerp(0.3, 1.0, look))
    ground(A, GROUND)
    A.flush(cv)
    if ph < 3:
        paste(cv, text_img('死？', SERIF, 60, INK, 'Black', bleed=False, spacing=6), 330, 760 + 0 * ph, 1, clamp(ph / 0.4))
    if 1.5 <= ph:
        paste(cv, text_img('书未成', SERIF, 52, ZHU, 'Black', bleed=False, spacing=6), 760, 760, 1, clamp((ph - 1.5) / 0.4))
    if ph >= 6:
        type_in(cv, text_img('受腐刑 · 奇耻大辱', SERIF, 46, MAUVE, 'Black', bleed=False, spacing=4), W / 2, 1448, t, t - u + 6 * P, 0.5)

def art_s_endure(A, cv, t, u):
    ground(A, GROUND)
    sima(A, 540, GROUND, 250, dir=1, beard=False, arm=lerp(-8, 30, 0.5 + 0.5 * math.sin(t)))
    for k in range(40):
        q = (t * 0.25 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['mid'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=180)
    A.flush(cv)
    type_in(cv, text_img('所以隐忍苟活', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('恨私心有所不尽', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.6 * P, 0.5)

def art_s_fafen(A, cv, t, u):
    """6-beat: 发愤著书 — the sages who wrote in adversity appear one by one; he joins the row."""
    ph = u / P
    ground(A, GROUND)
    names = ['文王拘', '仲尼厄', '屈原放逐', '左丘失明', '孙子膑脚']
    for i, nm in enumerate(names):
        if ph >= i * 0.9:
            x = 140 + i * 170
            sitter(A, x, GROUND, 110, dir=1, bow=10, layer='mid')
    if ph >= 4.5:
        sima(A, 980, GROUND, 160, dir=-1, beard=False, arm=40)
    A.flush(cv)
    for i, nm in enumerate(names):
        if ph >= i * 0.9:
            stamp(cv, seal(nm, 28, MAUVE), 140 + i * 170, 1160, t, t - u + i * 0.9 * P)
    type_in(cv, text_img('皆意有所郁结 · 发愤之所为作也', SERIF, 42, INK, 'Black', bleed=False, spacing=4), W / 2, 880, t, t - u + 4.5 * P, 0.6)

# ================================================================ 第四回 一家之言
def art_s_zhongshu(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mauve')
    ground(A, GROUND)
    sima(A, 380, GROUND, 210, dir=1, beard=False, arm=60)
    scroll(A, 600, 1080, 200, 70, u / 0.6)
    person(A, 760, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=50, layer='ink')
    A.flush(cv)
    stamp(cv, seal('中书令', 50), 260, 880, t, t - u + P, rot=-5)

SECTIONS = [('本纪', 12), ('表', 10), ('书', 8), ('世家', 30), ('列传', 70)]
def art_s_130(A, cv, t, u):
    """8-beat set piece: 一百三十篇 — five stacks rise in turn (本纪12 表10 书8 世家30 列传70); the total counts to 一百三十."""
    ph = u / P
    ground(A, GROUND)
    total = 0
    for i, (nm, n) in enumerate(SECTIONS):
        q = clamp((ph - i * 1.3) / 1.1)
        k = int(n * q)
        total += k
        x = 180 + i * 180
        for j in range(k):
            y = GROUND - 8 - j * 7
            A.d['mauve' if j % 2 else 'candley'].rectangle((x - 60, y - 6, x + 60, y), fill=255)
    A.flush(cv)
    for i, (nm, n) in enumerate(SECTIONS):
        if ph >= i * 1.3:
            stamp(cv, seal(nm, 36, ZHU if i == 4 else MAUVE), 180 + i * 180, GROUND + 40 - 0, t, t - u + i * 1.3 * P)
    paste(cv, text_img(f'{cn_num(total)}篇' if total < 130 else '一百三十篇 · 五十二万六千五百字', SERIF, 50, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_s_letter(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mauve')
    sitter(A, 300, GROUND, 220, dir=1, bow=20)
    scroll(A, 560, GROUND - 110, 280, 70, u / 0.6, layer='wash')
    lamp(A, 760, GROUND - 70, 40, t, glow=0.7)
    A.flush(cv)
    stamp(cv, seal('任安', 50, INK), 860, 880, t, t - u + P, rot=6)

def art_s_taishan(A, cv, t, u):
    A.d['mid'].polygon([(120, GROUND), (330, 900), (540, GROUND)], fill=220)
    p = ease_out((u - P) / (2 * P))
    for k in range(8):
        q = ((t * 0.4 + k / 8) % 1)
        x = 760 + 120 * math.sin(k * 1.7 + t)
        y = lerp(1300, 820, q)
        A.d['wash'].ellipse((x - 18, y - 4, x + 18, y + 4), fill=int(200 * (1 - q) * p))
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('重于泰山', SERIF, 54, MAUVE, 'Black', bleed=False, spacing=8), 330, 830, t, t - u + 0.4, 0.4)
    type_in(cv, text_img('轻于鸿毛', SERIF, 54, DIM, 'Black', bleed=False, spacing=8), 760, 830, t, t - u + 1.5 * P, 0.4)

def art_s_jiu(A, cv, t, u):
    r = random.Random(9)
    for k in range(60):
        x, y = r.uniform(120, 960), r.uniform(660, 1100)
        tw = max(0.5, 2 + 2 * math.sin(t * 2.4 + k))
        A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)
    A.d['ink'].polygon([(60, GROUND), (60, 1300), (420, 1260), (640, GROUND)], fill=255)
    sima(A, 300, 1290, 200, dir=1, beard=False, arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t)))
    A.flush(cv)
    for i, ln in enumerate(('究天人之际', '通古今之变', '成一家之言')):
        type_in(cv, text_img(ln, SERIF, 44, ZHU if i == 2 else INK, 'Black', bleed=False, vertical=True, spacing=4), 900 - i * 70, 980, t, t - u + 0.3 + i * 0.9 * P, 0.4)

def art_s_hide(A, cv, t, u):
    A.d['mid'].polygon([(120, GROUND), (420, 900), (720, GROUND)], fill=210)
    A.d['ink'].chord((330, 1160, 510, 1340), 180, 360, fill=255)
    bundle(A, 420, 1300, 80, layer='candley')
    city_wall(A, 700, 1020, 1160, gate_x=860, label='京师', layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('正本', 44), 420, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('副本', 44, INK), 860, 1000, t, t - u + 1.5 * P, rot=5)

def art_s_unknown(A, cv, t, u):
    for k in range(40):
        q = (t * 0.2 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 30, lerp(1300, 700, q) - 8, x + 30, lerp(1300, 700, q) + 8), fill=int(140 * math.sin(math.pi * q)))
    ground(A, GROUND)
    x = lerp(400, 1000, ease_out(u / (2 * P)))
    sima(A, x, GROUND, 200, dir=1, beard=False, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('卒年不详', SERIF, 52, MAUVE, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 史家绝唱
def art_s_yangyun(A, cv, t, u):
    ground(A, GROUND)
    person(A, 400, GROUND, 230, dir=1, robe=True, hat='none', arm=lerp(40, 140, ease_out(u / 0.6)), layer='ink')
    scroll(A, 620, 1000, 320, 100, u / 0.6, layer='candley')
    for k in range(5):
        person(A, 740 + k * 60, GROUND, 130, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
    A.flush(cv)
    stamp(cv, seal('杨恽', 54), 260, 880, t, t - u + 0.4, rot=-5)
    ink_in(cv, text_img('太史公书', SERIF, 40, INK, 'Black', bleed=False, spacing=6), 620, 1000, t, t - u + 0.6, dur=0.3)

def art_s_hanshu(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mauve')
    sitter(A, 300, GROUND, 210, dir=1, bow=15)
    for i in range(int(clamp(u / (2 * P)) * 4) + 1):
        bundle(A, 640 + i * 80, GROUND - 60, 60, layer='candley')
    A.flush(cv)
    stamp(cv, seal('班固', 54), 860, 880, t, t - u + 0.4, rot=6)

def art_s_shrine(A, cv, t, u):
    A.d['mid'].polygon([(120, GROUND), (540, 880), (960, GROUND)], fill=200)
    for k in range(10):
        x = lerp(220, 520, k / 9); y = lerp(GROUND, 980, k / 9)
        A.d['ink'].rectangle((x - 30, y - 10, x + 30, y), fill=255)
    palace(A, 560, 990, 260, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('韩城', 54), 860, 880, t, t - u + P, rot=6)

def art_s_24(A, cv, t, u):
    ground(A, GROUND)
    n = min(24, int(clamp(u / (2.5 * P)) * 24) + 1)
    for i in range(n):
        x = 120 + (i % 12) * 76; y = GROUND - 10 - (i // 12) * 150
        A.d['candley' if i == 0 else 'mauve'].rectangle((x - 28, y - 130, x + 28, y), fill=255)
    A.flush(cv)
    stamp(cv, seal('第一', 50), 120, 1100, t, t - u + 0.3)
    paste(cv, text_img(f'{cn_num(n)}史', SERIF, 54, MAUVE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)

def art_s_luxun(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mauve')
    person(A, 320, GROUND, 220, dir=1, robe=True, hat='none', arm=60, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('史家之绝唱', SERIF, 54, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('无韵之离骚', SERIF, 54, INK, 'Black', bleed=False, spacing=8), W / 2, 910, t, t - u + 1.4 * P, 0.5)
    stamp(cv, seal('鲁迅', 50, INK), 860, 1100, t, t - u + 2.2 * P, rot=6)

def art_s_today(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        x = 160 + k * 150
        sitter(A, x, GROUND, 120, dir=1, bow=20, layer='ink' if k % 2 else 'mid')
        A.d['candley'].rectangle((x + 20, GROUND - 70, x + 70, GROUND - 40), fill=255)
    A.flush(cv)
    paste(cv, text_img('两千年后 仍在被读', SERIF, 50, MAUVE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - 0.5 * P) / 0.3))

def art_s_legacy(A, cv, t, u):
    shi_glyph(A, 540, 1040, 420, 7)
    ground(A, GROUND)

def art_s_title(A, cv, t, u):
    desk(A, 780, 1460, 360, layer='mauve')
    slips(A, 660, 1390, 14, 70, layer='candley', tied=False)
    sima(A, 380, 1460, 680, dir=1, arm=lerp(-5, 45, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '龙门少年'), 48: ('第二回', '父子之托'), 80: ('第三回', '李陵之祸'),
            112: ('第四回', '一家之言'), 144: ('第五回', '史家绝唱')}

CARDS = [
    C(0, 2, 'works', 'num', num='五十二万字', line='写尽三千年', art=art_s_hook_words),
    C(2, 4, 'night', 'num', num='宫刑', line='他选择活下去', art=art_s_hook_cell),
    C(4, 6, 'empire', 'num', num='一百三十篇', line='二十四史第一部', art=art_s_hook_130),
    C(6, 8, 'fate', 'num', num='泰山鸿毛', line='人固有一死', art=art_s_hook_scale),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 龙门少年
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-145, main='生于龙门', sub='夏阳龙门 · 耕牧河山之阳', note='生年 一说前一三五年', art=art_s_longmen),
    C(22, 26, 'works', 'card', year=-136, main='诵读古文', sub='少年随父在长安读书', art=art_s_reading),
    C(26, 30, 'night', 'card', year=-136, main='父亲太史令', sub='司马谈 · 掌天文史籍', note='父有著史之志', art=art_s_father),
    C(30, 38, 'works', 'journey', year=-126),
    C(38, 42, 'court', 'card', year=-125, main='仕为郎中', sub='侍从汉武帝左右', art=art_s_langzhong),
    C(42, 46, 'war', 'card', year=-111, main='奉使西南', sub='出使巴蜀以南', note='南略邛笮昆明', art=art_s_southwest),
    C(46, 48, 'empire', 'card', year=-110, main='泰山封禅', sub='父亲滞留周南 · 未能随行', art=art_s_fengshan),
    # ---- 第二回 父子之托
    C(48, 50, 'court', 'chapter'),
    C(50, 56, 'death', 'card', year=-110, main='父亲临终', sub='执子之手 · 泣嘱著史', art=art_s_deathbed),
    C(56, 60, 'court', 'card', year=-108, main='太史令', sub='继承父职', note='遍读皇家藏书', art=art_s_taishiling),
    C(60, 64, 'empire', 'card', year=-104, main='太初历', sub='参与改定历法', note='与唐都 落下闳等共定', art=art_s_calendar),
    C(64, 68, 'works', 'card', year=-104, main='始作史记', sub='一部通史 · 从头写起', art=art_s_begin),
    C(68, 72, 'life', 'card', year=-102, main='为败者立传', sub='项羽入本纪 · 陈涉入世家', note='不以成败论英雄', art=art_s_losers),
    C(72, 76, 'war', 'card', year=-99, main='李陵出征', sub='率步卒深入匈奴', art=art_s_lingout),
    C(76, 80, 'night', 'card', year=-99, main='李陵投降', sub='满朝文武 · 争相指责', art=art_s_surrender),
    # ---- 第三回 李陵之祸
    C(80, 82, 'night', 'chapter'),
    C(82, 86, 'court', 'card', year=-99, main='仗义直言', sub='为李陵辩护', note='彼观其意 且欲得其当而报于汉', art=art_s_defend),
    C(86, 90, 'night', 'card', year=-99, main='下狱', sub='以诬上之罪 · 下狱论死', art=art_s_arrest),
    C(90, 94, 'fate', 'card', year=-98, main='无钱赎罪', sub='亲友无人相救', note='交游莫救 左右亲近不为一言', art=art_s_poor),
    C(94, 102, 'death', 'card', year=-98, main='宫刑', sub='在死与书之间', note='一说在前九八年', art=art_s_punish),
    C(102, 106, 'fate', 'card', year=-98, main='隐忍苟活', sub='只为写完这部书', art=art_s_endure),
    C(106, 112, 'works', 'card', year=-97, main='发愤著书', sub='古来圣贤 · 多在困厄中写作', art=art_s_fafen),
    # ---- 第四回 一家之言
    C(112, 114, 'works', 'chapter'),
    C(114, 118, 'court', 'card', year=-96, main='中书令', sub='出狱后任中书令', art=art_s_zhongshu),
    C(118, 126, 'works', 'card', year=-91, main='史记成书', sub='本纪 表 书 世家 列传', note='凡百三十篇', art=art_s_130),
    C(126, 130, 'night', 'card', year=-91, main='报任安书', sub='写给友人的长信', note='一说作于前九三年', art=art_s_letter),
    C(130, 134, 'fate', 'card', year=-91, main='泰山鸿毛', sub='人固有一死', art=art_s_taishan),
    C(134, 138, 'night', 'card', year=-91, main='一家之言', sub='他为史书立下的志向', art=art_s_jiu),
    C(138, 142, 'empire', 'card', year=-91, main='藏之名山', sub='正本藏于名山 · 副本留在京师', art=art_s_hide),
    C(142, 144, 'death', 'card', year=-86, main='不知所终', sub='卒年不详', art=art_s_unknown),
    # ---- 第五回 史家绝唱
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'court', 'card', year=-60, main='公之于世', sub='外孙杨恽 · 将史记公布', note='宣帝时', art=art_s_yangyun),
    C(150, 154, 'works', 'card', year=82, main='汉书', sub='班固继之 · 断代为史', art=art_s_hanshu),
    C(154, 158, 'life', 'card', year=310, main='司马迁祠', sub='西晋时始建于韩城', art=art_s_shrine),
    C(158, 162, 'empire', 'card', year=1775, main='二十四史', sub='史记位列第一', art=art_s_24),
    C(162, 166, 'works', 'card', year=1926, main='史家绝唱', sub='鲁迅 汉文学史纲要', art=art_s_luxun),
    C(166, 170, 'end', 'card', year=2026, main='至今仍读', sub='历史因他而有血有肉', art=art_s_today),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='贰拾陆', col=MAUVE, acc=CANDLEY, born=-145, died=-86,
    born_lab='约前145年', died_lab='约前86年', years_txt='约公元前145 — 约前86',
    hook_q='受尽屈辱 · 他为什么没有去死？',
    name_line='司马迁 · 字子长', name='司马迁', seal='太史公', title_art=art_s_title,
    q1='忍辱负重？', q2='苟且偷生？',
    end_art=art_s_legacy, end_big='一家之言', end_seal='太史公',
    end_l1='他失去了做人的尊严', end_l2='却给了历史尊严',
    end_brush='究天人之际', end_ask='换作是你 会选择活下来吗？评论区聊聊', next='霍去病'),
    scenes=dict(chapter=scene_chapter, journey=scene_journey))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
