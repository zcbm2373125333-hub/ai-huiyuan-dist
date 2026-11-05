"""千古人物志 · 第陆拾肆集 · 花木兰 (传说人物 · 出自北朝民歌《木兰诗》)
Look: 木兰花粉 + 戎装铁灰, 织梭+箭 corner borders, a 机杼 chapter card: the loom (机杼) slowly gives way to armour — the
shuttle, then a bow, a helmet, armour — and in the last chapter the armour hangs on the wall beside a hairpin.
Set pieces: 6-beat 唧唧复唧唧 (当户织), 6-beat 东市买骏马, custom 8-beat scene 'mulan' (万里赴戎机), 6-beat 朔气金柝,
6-beat 对镜帖花黄, 6-beat 双兔傍地走.
Legendary figure: no birth/death years; the HUD shows the poem's era and hides ages (no_age).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_wangxizhi as Wx       # engine + helpers (previous episode)
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
from render_sunwu import army, banner
from render_quyuan import river
from render_simayi import emperor
from render_mengzi import loom

F.RIPPLE = False
MULANFEN = (210, 120, 150)          # 木兰花粉
RONGHUI = (82, 90, 100)             # 戎装铁灰
S.LAYERS.append(('mulanfen', MULANFEN, 0.9, 1.0))
S.LAYERS.append(('ronghui', RONGHUI, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='兰', life='织', court='汗', night='月', war='戎', empire='凯', works='织', fate='征', death='战', end='兰')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZHU, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (MULANFEN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (MULANFEN, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

MAGNOLIA = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(MAGNOLIA)
for _x in (120, 960):               # magnolia trees at the margins
    _d.line((_x, 1480, _x - 4, 1360), fill=(80, 64, 60, 70), width=7)
    for _k in range(7):
        _a = _k * 0.9
        _px, _py = _x + 46 * math.cos(_a), 1350 + 30 * math.sin(_a)
        _d.ellipse((_px - 10, _py - 14, _px + 10, _py + 6), fill=MULANFEN + (80,))
for _k in range(3):
    _d.line([(220 + i * 30, 1470 + _k * 14 + 3 * math.sin(i)) for i in range(22)], fill=RONGHUI + (34,), width=2)
MTN_COL = {'night': (30, 30, 42), 'death': (62, 58, 62), 'war': (110, 62, 54), 'fate': (92, 94, 104)}
def draw_background(t, theme):
    """黄河 · 燕山: hills, magnolias at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 186, 188), (160, 156, 166), MTN_COL.get(theme, (116, 112, 128))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(MAGNOLIA)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """织梭与箭: a shuttle and an arrow crossed in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=RONGHUI + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=RONGHUI + (220,), width=3)
        cx, cy = x + sx * 60, y + sy * 60
        d.polygon([(cx - sx * 40, cy + sy * 30), (cx - sx * 6, cy + sy * 4), (cx + sx * 40, cy - sy * 30), (cx + sx * 6, cy - sy * 4)], fill=MULANFEN + (230,))
        d.line((cx - sx * 40, cy - sy * 30, cx + sx * 40, cy + sy * 30), fill=(60, 60, 66, 230), width=4)
        d.polygon([(cx + sx * 40, cy + sy * 30), (cx + sx * 30, cy + sy * 14), (cx + sx * 24, cy + sy * 30)], fill=(60, 60, 66, 230))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def mulan(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, armour=False, **kw):
    """花木兰: as a girl — twin hair buns and a magnolia-pink dress; in armour — helmet with a red plume, grey scale armour."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else 'knot', female=not armour, layer=layer, kneel=kneel, bow=bow, **kw)
    if up:
        if armour:
            A.d['red'].polygon([(x - 0.02 * h, y - 1.05 * h), (x + 0.02 * h, y - 1.05 * h), (x - dir * 0.08 * h, y - 1.2 * h)], fill=255)
            A.d['ronghui'].rectangle((x - 0.11 * h, y - 0.74 * h, x + 0.11 * h, y - 0.42 * h), fill=255)
            for k in range(4):
                A.d['wash'].line((x - 0.11 * h, y - 0.72 * h + k * 0.08 * h, x + 0.11 * h, y - 0.72 * h + k * 0.08 * h), fill=120, width=2)
        else:
            for sx in (-1, 1):
                A.d[layer].ellipse((x + sx * 0.07 * h - 0.04 * h, y - 1.06 * h, x + sx * 0.07 * h + 0.04 * h, y - 0.98 * h), fill=255)
            A.d['mulanfen'].polygon([(x - 0.12 * h, y - 0.6 * h), (x + 0.12 * h, y - 0.6 * h), (x + 0.18 * h, y - 0.02 * h), (x - 0.18 * h, y - 0.02 * h)], fill=200)
    return hand

def father(A, x, y, h, dir=-1, **kw):
    kw.setdefault('arm', -8)
    return person(A, x, y, h, dir=dir, robe=True, hat='knot', layer=kw.pop('layer', 'ink'), bow=kw.pop('bow', 20), **kw)

def hare(A, x, y, s, t, dir=1, run=True):
    b = abs(math.sin(t * 8)) * 0.3 * s if run else 0
    A.d['ink'].ellipse((x - s, y - 0.6 * s - b, x + 0.6 * s, y - b), fill=255)
    A.d['ink'].ellipse((x + dir * 0.4 * s, y - 0.9 * s - b, x + dir * 0.9 * s, y - 0.45 * s - b), fill=255)
    A.d['ink'].line((x + dir * 0.6 * s, y - 0.85 * s - b, x + dir * 0.55 * s, y - 1.5 * s - b), fill=255, width=max(3, int(0.12 * s)))
    A.d['ink'].line((x + dir * 0.75 * s, y - 0.85 * s - b, x + dir * 0.8 * s, y - 1.45 * s - b), fill=255, width=max(3, int(0.12 * s)))

def armour_stand(A, cx, base, s, layer='ronghui'):
    A.d['ink'].line((cx, base, cx, base - 1.6 * s), fill=255, width=8)
    A.d['ink'].line((cx - 0.5 * s, base - 1.3 * s, cx + 0.5 * s, base - 1.3 * s), fill=255, width=8)
    A.d[layer].rectangle((cx - 0.4 * s, base - 1.3 * s, cx + 0.4 * s, base - 0.5 * s), fill=255)
    A.d[layer].chord((cx - 0.3 * s, base - 1.9 * s, cx + 0.3 * s, base - 1.4 * s), 180, 360, fill=255)
    A.d['red'].polygon([(cx - 0.04 * s, base - 1.88 * s), (cx + 0.04 * s, base - 1.88 * s), (cx, base - 2.15 * s)], fill=255)

# ================================================================ chapter card
def art_loom_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    q = ease_out(u / (1.2 * P))
    if kb == 16:
        loom(A, 540, 1220, 4, t)
    elif kb == 48:
        loom(A, 380, 1220, 4, t)
        A.d['ink'].arc((640, 900, 760, 1200), 270, 90, fill=int(255 * q), width=8)
        A.d['ink'].line((700, 900, 700, 1200), fill=int(200 * q), width=2)
    elif kb == 80:
        armour_stand(A, 540, 1220, 180 * q + 10)
    elif kb == 112:
        armour_stand(A, 540, 1220, 190)
        banner(A, 760, 1220, 300 * q + 10, t, layer='red')
    else:
        armour_stand(A, 400, 1220, 180)
        A.d['mulanfen'].ellipse((660, 1000, 760, 1060), fill=int(255 * q))
        A.d['gold'].line((640, 1060, 780, 1000), fill=int(255 * q), width=4)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_loom_chapter)
    ink_in(cv, text_img(no, SERIF, 56, RONGHUI, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_m_hook_12(A, cv, t, u):
    ground(A, GROUND)
    n = min(12, int(clamp(u / (1.4 * P)) * 12) + 1)
    for i in range(n):
        x = 900 - (i % 6) * 140; y = GROUND - (i // 6) * 150
        A.d['ronghui'].rectangle((x - 40, y - 120, x + 40, y), fill=230)

def art_m_hook_armour(A, cv, t, u):
    ground(A, GROUND)
    armour_stand(A, 540, GROUND, 200)

def art_m_hook_hares(A, cv, t, u):
    A.d['grass'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=150)
    ground(A, GROUND)
    hare(A, lerp(-100, 600, ease_out(u / (1.6 * P))), GROUND - 40, 50, t)
    hare(A, lerp(-200, 500, ease_out(u / (1.6 * P))), GROUND - 40, 50, t + 0.3)

def art_m_hook_poem(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1080, 520, 240, clamp(u / P), layer='wash')

# ================================================================ 第一回 当户织
def art_m_home(A, cv, t, u):
    A.d['mid'].rectangle((360, 1080, 720, GROUND), fill=220)
    A.d['ink'].polygon([(320, 1080), (760, 1080), (540, 960)], fill=255)
    A.d['ink'].rectangle((500, 1160, 580, GROUND), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('北朝 · 黄河之滨一户人家', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_weave(A, cv, t, u):
    """6-beat set piece: 唧唧复唧唧 — she weaves at the door; the shuttle clacks; then it stops; she sighs."""
    ph = u / P
    ground(A, GROUND)
    loom(A, 620, GROUND, 4 + int(ph) if ph < 3 else 6, t)
    mulan(A, 360, GROUND, 180, dir=1, kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 8)) if ph < 3 else 40, bow=0 if ph < 3 else 30)
    A.flush(cv)
    type_in(cv, text_img('唧唧复唧唧 木兰当户织', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('不闻机杼声 唯闻女叹息', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 3 * P, 0.5)

def art_m_notice(A, cv, t, u):
    A.d['mid'].rectangle((300, 900, 780, 1200), fill=230)
    A.d['ink'].rectangle((300, 900, 780, 1200), outline=255, width=6)
    n = int(clamp(u / (2 * P)) * 12)
    for i in range(n):
        A.d['ink'].rectangle((720 - (i % 6) * 70, 940 + (i // 6) * 120, 750 - (i % 6) * 70, 1040 + (i // 6) * 120), fill=150)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('昨夜见军帖 可汗大点兵', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('军帖', 56), 860, 1260, t, t - u + P, rot=6)

def art_m_name(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 480, 160, 1.0, layer='wash')
    A.flush(cv)
    for i in range(min(12, int(u / (0.25 * P)) + 1)):
        paste(cv, text_img('爷', SERIF, 34, ZHU if i == 11 else INK, 'Black', bleed=False), 760 - i * 40, 1100, 1, 1)
    paste(cv, text_img('军书十二卷 卷卷有爷名', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_father(A, cv, t, u):
    A.d['mid'].rectangle((600, GROUND - 200, 900, GROUND), fill=200)
    A.d['ink'].polygon([(580, GROUND - 200), (920, GROUND - 200), (750, GROUND - 280)], fill=255)
    ground(A, GROUND)
    father(A, 460, GROUND, 190, dir=1, bow=30, arm=-8)
    person(A, 300, GROUND, 100, dir=1, robe=True, hat='knot', arm=40, layer='mid')
    A.flush(cv)
    paste(cv, text_img('阿爷无大儿 木兰无长兄', SERIF, 48, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_decide(A, cv, t, u):
    ground(A, GROUND)
    loom(A, 760, GROUND, 4, t)
    mulan(A, 420, GROUND, 190, dir=1, arm=lerp(-8, 120, ease_out((u - P) / 0.4)))
    A.flush(cv)
    type_in(cv, text_img('愿为市鞍马 从此替爷征', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('替父', 56), 260, 1020, t, t - u + P, rot=-5)

def art_m_market(A, cv, t, u):
    """6-beat set piece: 四市备鞍马 — east market a fine horse, west market a saddle, south market a bridle, north market a long whip."""
    ph = u / P
    ground(A, GROUND)
    k = min(3, int(ph / 1.5))
    items = ['东市买骏马', '西市买鞍鞯', '南市买辔头', '北市买长鞭']
    for j in range(3):
        A.d['mulanfen' if j == k % 3 else 'mid'].polygon([(160 + j * 300, GROUND - 160), (380 + j * 300, GROUND - 160), (350 + j * 300, GROUND - 200), (190 + j * 300, GROUND - 200)], fill=230)
        A.d['ink'].line((180 + j * 300, GROUND - 160, 180 + j * 300, GROUND), fill=255, width=5)
        A.d['ink'].line((360 + j * 300, GROUND - 160, 360 + j * 300, GROUND), fill=255, width=5)
    horse(A, 700, GROUND, 170, dir=-1, moving=False, layer='ink')
    if k >= 1:
        A.d['mulanfen'].rectangle((660, GROUND - 130, 740, GROUND - 110), fill=255)
    if k >= 2:
        A.d['ink'].line((560, GROUND - 160, 620, GROUND - 140), fill=255, width=3)
    mulan(A, 400, GROUND, 170, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)) if k < 3 else 150)
    if k >= 3:
        A.d['ink'].line((420, GROUND - 210, 520, GROUND - 300), fill=255, width=3)
    A.flush(cv)
    paste(cv, text_img(items[k], SERIF, 50, RONGHUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - k * 1.5) / 0.3))

def art_m_dress(A, cv, t, u):
    ground(A, GROUND)
    q = ease_out((u - 1.5 * P) / P)
    mulan(A, 540, GROUND, 200, dir=1, armour=q > 0.5, arm=40)
    A.flush(cv)
    paste(cv, text_img('脱我女儿装 · 著我战时袍', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '此句为后世戏曲语 原诗无', t, t - u + P)

# ================================================================ 第二回 万里赴戎机
def art_m_leave(A, cv, t, u):
    A.d['mid'].rectangle((600, GROUND - 200, 900, GROUND), fill=200)
    A.d['ink'].polygon([(580, GROUND - 200), (920, GROUND - 200), (750, GROUND - 280)], fill=255)
    ground(A, GROUND)
    father(A, 640, GROUND, 180, dir=-1, arm=60)
    person(A, 720, GROUND, 160, dir=-1, robe=True, hat='knot', female=True, arm=60, layer='mid')
    x = lerp(500, -100, ease_out(u / (3 * P)))
    horse(A, x, GROUND, 160, dir=-1, ph=t * 6)
    mulan(A, x + 8, GROUND - 106, 120, dir=-1, armour=True, arm=55)
    A.flush(cv)
    paste(cv, text_img('旦辞爷娘去', SERIF, 50, RONGHUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_m_yellowriver(A, cv, t, u):
    r = 50
    A.d['wash'].ellipse((820 - r, 820 - r, 820 + r, 820 + r), fill=230)
    A.d['yellow'].rectangle((60, 1200, W - 60, GROUND + 40), fill=170)
    waves(A, 1210, t, rows=3, amp=6, speed=2)
    tent(A, 300, 1200, 160, 120, layer='ronghui')
    mulan(A, 500, 1200, 160, dir=1, kneel=True, armour=True, bow=20, arm=-8)
    A.flush(cv)
    type_in(cv, text_img('不闻爷娘唤女声', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('但闻黄河流水鸣溅溅', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.6 * P, 0.5)

def art_m_yanshan(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 380), (x + 150, GROUND)], fill=170)
        A.d['wash'].polygon([(x - 40, GROUND - 280), (x, GROUND - 380), (x + 40, GROUND - 280)], fill=255)
    ground(A, GROUND)
    for j in range(3):
        rider(A, (t * 50 + j * 300) % (W + 200) - 100, GROUND, 90, dir=1, ph=t * 8 + j, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('暮至黑山头 · 但闻燕山胡骑鸣啾啾', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('燕山', 56, INK), 860, 1020, t, t - u + P, rot=6)

def scene_mulan(cv, t, c, k):
    """8-beat custom scene: 万里赴戎机 — a single rider crosses mountain after mountain on a long map line; the passes fly by;
    the line reaches the frontier camp."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    off = (ph * 260) % 400
    for k2 in range(6):
        x = 140 + k2 * 200 - off
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 300 - 80 * (k2 % 2)), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    horse(A, 500, GROUND, 190, dir=1, ph=t * 12)
    mulan(A, 492, GROUND - 126, 140, dir=1, armour=True, arm=55)
    A.d['wash'].rounded_rectangle((140, 640, 940, 720), radius=14, fill=200)
    q = clamp(ph / 7)
    A.d['ronghui'].line((180, 680, 180 + 720 * q, 680), fill=255, width=8)
    A.d['red'].ellipse((180 + 720 * q - 10, 670, 180 + 720 * q + 10, 690), fill=255)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '万里赴戎机', BRUSH, 140, INK, W / 2, 440, t, s0, stagger=0.06, seed=64)
    fx.flush(cv)
    li = int(lerp(0, 10000, q))
    paste(cv, text_img(f'关山度若飞 · {li} 里', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    stamp(cv, seal('家', 34, INK), 180, 740, t, s0 + 0.2)
    if ph > 6.5:
        stamp(cv, seal('边', 34, ZHU), 900, 740, t, s0 + 6.5 * P)
    paste(cv, text_img('万里赴戎机 关山度若飞', SERIF, 42, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 1) / 0.4))

def art_m_night(A, cv, t, u):
    """6-beat set piece: 朔气传金柝 — winter night at the frontier; the watchman's clapper sounds; cold moonlight glints on iron armour."""
    ph = u / P
    r = 60
    A.d['wash'].ellipse((800 - r, 840 - r, 800 + r, 840 + r), fill=240)
    for k2 in range(50):
        q = (t * 0.4 + k2 / 50) % 1
        A.d['wash'].ellipse((80 + (k2 * 19) % 920 - 3, lerp(620, 1420, q) - 3, 80 + (k2 * 19) % 920 + 3, lerp(620, 1420, q) + 3), fill=220)
    tent(A, 260, GROUND, 220, 170, layer='ronghui')
    tent(A, 820, GROUND, 220, 170, layer='ronghui')
    ground(A, GROUND)
    mulan(A, 540, GROUND, 190, dir=1, armour=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 4)))
    hit = (u % P) / P
    A.d['wash'].ellipse((620 - 40 * hit, GROUND - 200 - 40 * hit, 620 + 40 * hit, GROUND - 200 + 40 * hit), outline=int(200 * (1 - hit)), width=3)
    A.flush(cv)
    type_in(cv, text_img('朔气传金柝', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.4, 0.4)
    type_in(cv, text_img('寒光照铁衣', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 835, t, t - u + 2 * P, 0.4)

# ================================================================ 第三回 将军百战死
def art_m_battle(A, cv, t, u):
    ground(A, GROUND)
    for j in range(5):
        rider(A, lerp(1200, 600, ease_out(u / (2 * P))) + j * 100, GROUND - (j % 2) * 20, 110, dir=-1, ph=t * 10 + j, layer='mid')
    army(A, 100, GROUND, 6, dir=1, layer='ronghui', t=t, h=110)
    mulan(A, 460, GROUND, 180, dir=1, armour=True, arm=150, spear=True)
    A.flush(cv)
    paste(cv, text_img('将军百战死', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_m_comrades(A, cv, t, u):
    tent(A, 540, GROUND, 460, 300, layer='mid')
    ground(A, GROUND)
    for j in range(5):
        person(A, 300 + j * 110, GROUND, 150, dir=1 if j % 2 else -1, robe=False, hat='helmet', kneel=True, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + j)), layer='ink' if j != 2 else 'ronghui')
    lamp(A, 540, GROUND, 40, t, glow=0.9)
    A.flush(cv)
    paste(cv, text_img('同行十二年 · 不知木兰是女郎', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_years(A, cv, t, u):
    ground(A, GROUND)
    n = min(12, int(u / (0.3 * P)) + 1)
    for i in range(n):
        A.d['ronghui'].rectangle((140 + i * 68, GROUND - 40 - i * 14, 190 + i * 68, GROUND), fill=200 if i < n - 1 else 255)
    A.flush(cv)
    paste(cv, text_img(f'壮士十年归 · 第{cn_num(n)}年', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    note_in(cv, '诗言十年 又言十二年 皆为约数', t, t - u + P)

def art_m_victory(A, cv, t, u):
    ground(A, GROUND)
    army(A, lerp(-200, 200, ease_out(u / (2 * P))), GROUND, 8, dir=1, layer='ronghui', t=t, march=True, h=110)
    for j in range(3):
        banner(A, 700 + j * 100, GROUND, 260, t, layer='red')
    A.flush(cv)
    paste(cv, text_img('壮士十年归 · 凯旋', SERIF, 48, RONGHUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_m_court(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mulanfen')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 190, dir=-1, arm=lerp(20, 100, ease_out(u / 0.5)))
    mulan(A, 400, GROUND, 180, dir=1, armour=True, kneel=True, bow=30, arm=100)
    A.flush(cv)
    paste(cv, text_img('归来见天子 天子坐明堂', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_rewards(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    n = int(clamp(u / (2 * P)) * 12)
    for i in range(n):
        A.d['gold'].rectangle((280 + (i % 6) * 90, GROUND - 40 - (i // 6) * 34, 340 + (i % 6) * 90, GROUND - 12 - (i // 6) * 34), fill=255)
    A.flush(cv)
    paste(cv, text_img('策勋十二转 赏赐百千强', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_refuse(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 190, dir=-1, arm=60)
    mulan(A, 400, GROUND, 180, dir=1, armour=True, kneel=True, bow=20, arm=lerp(60, 120, ease_out(u / 0.5)))
    A.flush(cv)
    type_in(cv, text_img('木兰不用尚书郎', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.4)
    type_in(cv, text_img('愿驰千里足 送儿还故乡', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.6 * P, 0.5)

# ================================================================ 第四回 当窗理云鬓
def art_m_welcome(A, cv, t, u):
    A.d['mid'].rectangle((600, GROUND - 200, 900, GROUND), fill=200)
    A.d['ink'].polygon([(580, GROUND - 200), (920, GROUND - 200), (750, GROUND - 280)], fill=255)
    ground(A, GROUND)
    father(A, 540, GROUND, 170, dir=-1, bow=30, arm=90)
    person(A, 460, GROUND, 160, dir=-1, robe=True, hat='knot', female=True, bow=30, arm=90, layer='mid')
    person(A, 360, GROUND, 150, dir=-1, robe=True, hat='knot', female=True, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 4)), layer='mulanfen')
    person(A, 240, GROUND, 150, dir=-1, robe=False, hat='knot', arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 6)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('爷娘出郭相扶将 · 阿姊理红妆 · 小弟磨刀霍霍', SERIF, 38, RONGHUI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_m_room(A, cv, t, u):
    A.d['mid'].rectangle((200, 900, 880, GROUND), fill=150)
    A.d['ink'].rectangle((200, 900, 880, GROUND), outline=255, width=6)
    A.d['wash'].rectangle((620, 960, 820, 1160), fill=230)
    ground(A, GROUND)
    mulan(A, 420, GROUND, 190, dir=1, armour=u < 2 * P, arm=60)
    A.flush(cv)
    paste(cv, text_img('开我东阁门 坐我西阁床', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_mirror(A, cv, t, u):
    """6-beat set piece: 对镜帖花黄 — she takes off the armour, puts on her old dress, combs her hair at the window and sets a yellow flower ornament before the mirror."""
    ph = u / P
    A.d['mid'].rectangle((200, 900, 880, GROUND), fill=150)
    A.d['wash'].rectangle((600, 940, 860, 1180), fill=255)
    A.d['ink'].rectangle((600, 940, 860, 1180), outline=255, width=6)
    A.d['ink'].line((730, 940, 730, 1180), fill=200, width=3)
    A.d['gold'].ellipse((260, 1000, 380, 1120), fill=255)
    A.d['ink'].ellipse((260, 1000, 380, 1120), outline=255, width=6)
    ground(A, GROUND)
    if ph < 2:
        armour_stand(A, 160, GROUND, 120)
    mulan(A, 460, GROUND, 190, dir=-1, armour=ph < 1.5, arm=lerp(60, 170, 0.5 + 0.5 * math.sin(t * 3)) if ph > 2 else 40)
    if ph > 4:
        A.d['yellow'].ellipse((440, GROUND - 180, 460, GROUND - 160), fill=255)
    A.flush(cv)
    type_in(cv, text_img('脱我战时袍 著我旧时裳', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('当窗理云鬓 对镜帖花黄', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 2.5 * P, 0.5)

def art_m_reveal(A, cv, t, u):
    A.d['mid'].rectangle((600, GROUND - 200, 900, GROUND), fill=200)
    A.d['ink'].polygon([(580, GROUND - 200), (920, GROUND - 200), (750, GROUND - 280)], fill=255)
    ground(A, GROUND)
    mulan(A, 700, GROUND, 190, dir=-1, arm=40)
    for j in range(4):
        person(A, 160 + j * 100, GROUND, 160, dir=1, robe=False, hat='helmet', arm=lerp(40, 150, ease_out((u - P) / 0.4)), bow=-10, layer='ronghui')
    A.flush(cv)
    type_in(cv, text_img('出门看火伴 火伴皆惊忙', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)

def art_m_hares(A, cv, t, u):
    """6-beat set piece: 双兔傍地走 — two hares run side by side; one hops like a buck, one blinks like a doe; side by side, who can tell?"""
    ph = u / P
    A.d['grass'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=150)
    ground(A, GROUND)
    if ph < 2.5:
        hare(A, 360, GROUND - 40, 60, t, run=ph < 1.2)
        hare(A, 720, GROUND - 40, 60, t + 0.5, run=1.2 <= ph < 2.5)
    else:
        x = lerp(-100, 1100, ((t * 0.15) % 1))
        hare(A, x, GROUND - 40, 60, t)
        hare(A, x - 140, GROUND - 40, 60, t + 0.3)
    A.flush(cv)
    lines = [('雄兔脚扑朔 雌兔眼迷离', INK), ('双兔傍地走 安能辨我是雄雌', ZHU)]
    k = 0 if ph < 2.5 else 1
    paste(cv, text_img(lines[k][0], SERIF, 44, lines[k][1], 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 2.5 * k) / 0.4))

def art_m_poem_end(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1080, 520, 240, 1.0, layer='wash')
    A.flush(cv)
    paste(cv, text_img('木兰诗 · 三百余字', SERIF, 48, RONGHUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '与孔雀东南飞并称乐府双璧', t, t - u + P)

# ================================================================ 第五回 木兰诗
def art_m_tang(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='mid')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    A.flush(cv)
    paste(cv, text_img('唐代已广为传诵 · 宋郭茂倩编入乐府诗集', SERIF, 42, RONGHUI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_m_surname(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    names = ['魏', '朱', '木', '花']
    n = min(4, int(u / (0.6 * P)) + 1)
    for i in range(n):
        stamp(cv, seal(names[i], 54, ZHU if i == 3 else INK), 240 + i * 200, 1080, t, t - u + i * 0.6 * P)
    paste(cv, text_img('她姓什么 · 历代说法不一', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '花姓之说始见明代徐渭雌木兰', t, t - u + P)

def art_m_opera(A, cv, t, u):
    for k in range(3):
        A.d['mid'].rectangle((240 + k * 80, GROUND - 60 - k * 40, 840 - k * 80, GROUND - k * 40), fill=230 - k * 20)
    ground(A, GROUND)
    mulan(A, 540, GROUND - 120, 180, dir=1, armour=True, arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    paste(cv, text_img('豫剧 · 谁说女子不如男', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('常香玉', 50), 860, 1020, t, t - u + P, rot=6)

def art_m_world(A, cv, t, u):
    A.d['wash'].ellipse((300, 900, 780, 1300), fill=200)
    A.d['ink'].ellipse((300, 900, 780, 1300), outline=255, width=6)
    for k in range(5):
        A.d['mulanfen'].ellipse((380 + (k * 67) % 300, 960 + (k * 53) % 280, 440 + (k * 67) % 300, 1000 + (k * 53) % 280), fill=220)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('走向世界 · 动画电影', SERIF, 46, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_venus(A, cv, t, u):
    r = 120
    A.d['yellow'].ellipse((540 - r, 1060 - r, 540 + r, 1060 + r), fill=180)
    A.d['mid'].ellipse((480, 1010, 540, 1060), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('金星上有一座环形山 · 以木兰命名', SERIF, 42, RONGHUI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_m_both(A, cv, t, u):
    ground(A, GROUND)
    mulan(A, 360, GROUND, 200, dir=1, arm=40)
    mulan(A, 720, GROUND, 200, dir=-1, armour=True, arm=40)
    A.flush(cv)
    paste(cv, text_img('能织布 也能上战场', SERIF, 48, RONGHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_magnolia(A, cv, t, u):
    A.d['ink'].line((540, GROUND, 530, GROUND - 320), fill=255, width=16)
    q = ease_out(u / P)
    for k in range(12):
        a = k * 0.52
        px, py = 530 + 160 * math.cos(a) * q, GROUND - 360 + 100 * math.sin(a) * q
        A.d['mulanfen'].ellipse((px - 24, py - 34, px + 24, py + 14), fill=230)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('木兰花开', SERIF, 52, RONGHUI, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))

def art_m_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    armour_stand(A, 860, 1380, 50)

def art_m_title(A, cv, t, u):
    armour_stand(A, 820, 1460, 160)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    mulan(A, 380, 1460, 680, dir=1, armour=True, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '当户织'), 48: ('第二回', '万里赴戎机'), 80: ('第三回', '将军百战死'),
            112: ('第四回', '对镜帖花黄'), 144: ('第五回', '木兰诗')}

CARDS = [
    C(0, 2, 'war', 'num', num='十二年', line='没人发现', art=art_m_hook_12),
    C(2, 4, 'works', 'num', num='一副战袍', line='一个秘密', art=art_m_hook_armour),
    C(4, 6, 'life', 'num', num='两只兔子', line='谁是雄雌', art=art_m_hook_hares),
    C(6, 8, 'end', 'num', num='一首民歌', line='传唱千年', art=art_m_hook_poem),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 当户织
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=429, main='北朝人家', sub='一个女孩', note='出自木兰诗 年代仅为示意', art=art_m_home),
    C(22, 28, 'works', 'card', year=429, main='当户织', sub='唧唧复唧唧', art=art_m_weave),
    C(28, 32, 'war', 'card', year=429, main='可汗点兵', sub='军帖', art=art_m_notice),
    C(32, 36, 'night', 'card', year=429, main='卷卷有爷名', sub='父亲老了', art=art_m_name),
    C(36, 40, 'fate', 'card', year=429, main='无大儿', sub='家中无人', art=art_m_father),
    C(40, 44, 'empire', 'card', year=429, main='替父从军', sub='一个决定', art=art_m_decide),
    C(44, 48, 'court', 'card', year=429, main='四市备马', sub='东西南北', art=art_m_market),
    # ---- 第二回 万里赴戎机
    C(48, 50, 'fate', 'chapter'),
    C(50, 54, 'life', 'card', year=429, main='女儿换戎装', sub='后世戏文', art=art_m_dress),
    C(54, 58, 'fate', 'card', year=429, main='辞爷娘', sub='旦辞', art=art_m_leave),
    C(58, 62, 'night', 'card', year=429, main='黄河边', sub='暮宿', art=art_m_yellowriver),
    C(62, 66, 'war', 'card', year=429, main='黑山头', sub='燕山胡骑', art=art_m_yanshan),
    C(66, 74, 'war', 'mulan', year=429),
    C(74, 80, 'night', 'card', year=430, main='寒光铁衣', sub='边关之夜', art=art_m_night),
    # ---- 第三回 将军百战死
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'death', 'card', year=431, main='百战', sub='沙场', art=art_m_battle),
    C(86, 90, 'night', 'card', year=433, main='同袍', sub='无人知晓', art=art_m_comrades),
    C(90, 94, 'fate', 'card', year=435, main='十二年', sub='春去秋来', art=art_m_years),
    C(94, 98, 'empire', 'card', year=441, main='凯旋', sub='壮士归来', art=art_m_victory),
    C(98, 102, 'court', 'card', year=441, main='见天子', sub='明堂', art=art_m_court),
    C(102, 106, 'empire', 'card', year=441, main='策勋十二转', sub='重赏', art=art_m_rewards),
    C(106, 112, 'life', 'card', year=441, main='不用尚书郎', sub='只想回家', art=art_m_refuse),
    # ---- 第四回 对镜帖花黄
    C(112, 114, 'end', 'chapter'),
    C(114, 118, 'life', 'card', year=441, main='爷娘出郭', sub='全家相迎', art=art_m_welcome),
    C(118, 122, 'night', 'card', year=441, main='东阁西阁', sub='回到闺房', art=art_m_room),
    C(122, 128, 'end', 'card', year=441, main='对镜帖花黄', sub='做回自己', art=art_m_mirror),
    C(128, 132, 'court', 'card', year=441, main='火伴皆惊忙', sub='十二年', art=art_m_reveal),
    C(132, 138, 'works', 'card', year=441, main='双兔', sub='安能辨我是雄雌', art=art_m_hares),
    C(138, 144, 'fate', 'card', year=441, main='木兰诗', sub='乐府双璧', art=art_m_poem_end),
    # ---- 第五回 木兰诗
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'works', 'card', year=1080, main='乐府诗集', sub='收录', art=art_m_tang),
    C(150, 154, 'night', 'card', year=1580, main='姓花', sub='名字的由来', art=art_m_surname),
    C(154, 158, 'court', 'card', year=1951, main='谁说女子', sub='不如男', art=art_m_opera),
    C(158, 162, 'empire', 'card', year=1998, main='走向世界', sub='银幕', art=art_m_world),
    C(162, 166, 'fate', 'card', year=1998, main='金星环形山', sub='木兰', art=art_m_venus),
    C(166, 168, 'life', 'card', year=1998, main='织布与征战', sub='两种勇气', art=art_m_both),
    C(168, 170, 'end', 'card', year=1998, main='木兰花开', sub='千年', art=art_m_magnolia),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='陆拾肆', col=RONGHUI, acc=MULANFEN, born=429, died=441, no_age=True,
    born_lab='北朝', died_lab='传说人物', years_txt='北朝民歌 · 传说人物',
    hook_q='她女扮男装打了十二年仗 · 为什么没人发现？',
    name_line='木兰 · 出自木兰诗', name='花木兰', seal='木兰', title_art=art_m_title,
    q1='巾帼英雄？', q2='文学虚构？',
    end_art=art_m_legacy, end_big='替父从军', end_seal='木兰',
    end_l1='她不要尚书郎', end_l2='只要回家对镜帖花黄',
    end_brush='安能辨我是雄雌', end_ask='你相信历史上真有木兰吗？评论区聊聊', next='白居易'),
    scenes=dict(chapter=scene_chapter, mulan=scene_mulan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
