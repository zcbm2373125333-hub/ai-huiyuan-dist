"""千古人物志 · 第贰拾贰集 · 屈原 (约前340–前278)
Look: 楚漆朱 + 兰草绿 (Chu lacquer red/black), 云纹 spiral corner borders, river-and-reed background;
a 编钟 chapter card: one more bell is struck each chapter.
Set pieces: 4-beat 离骚, 8-beat 武关 (the gate closes behind the king), custom 8-beat scene 'tianwen'
(天问: questions fly up into the night sky), 6-beat 怀沙 (into the 汨罗 river; boats come searching).
Years are stored negative (BC); epkit prints 公元前.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_kongzi as Kz          # engine + helpers (previous episode)
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
from render_wangyangming import desk, scroll, lamp, sitter, leaf
from render_kongzi import slips, bundle

F.RIPPLE = False
LACQ = (160, 38, 30)                # 楚漆朱
ORCHID = (96, 132, 70)              # 兰草绿
S.LAYERS.append(('lacq', LACQ, 0.88, 1.0))
S.LAYERS.append(('orchid', ORCHID, 0.85, 1.2))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='楚', life='平', court='郢', night='夜', war='秦', empire='楚', works='骚', fate='问', death='汨', end='楚')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court'):
    G.THEMES[k]['part'] = 'petal'
for k in ('empire',):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (LACQ, 230, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (ORCHID, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

REEDS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(REEDS)
_d.rectangle((60, 1452, W - 60, 1476), fill=(70, 110, 120, 40))
_r = random.Random(8)
for _k in range(26):
    _x = 70 + _k * 40 + _r.uniform(-10, 10)
    if 260 < _x < 820: continue
    _h = _r.uniform(90, 170)
    _d.line((_x, 1470, _x + _r.uniform(-14, 14), 1470 - _h), fill=ORCHID + (60,), width=3)
    _d.ellipse((_x - 4, 1470 - _h - 14, _x + 6, 1470 - _h + 8), fill=(120, 96, 60, 70))
MTN_COL = {'night': (30, 34, 40), 'death': (56, 60, 62), 'war': (96, 44, 36), 'fate': (52, 70, 76)}
def draw_background(t, theme):
    """沅湘: low misty hills over a river band, reeds at the banks."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(176, 182, 178), (128, 140, 136), MTN_COL.get(theme, (82, 100, 96))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(REEDS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """楚云纹: a lacquer-red spiral scroll curling out of each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 170, y), fill=INK + (200,), width=5); d.line((x, y, x, y + sy * 170), fill=INK + (200,), width=5)
        cx, cy = x + sx * 52, y + sy * 52
        pts = [(cx + sx * (4 + 3.2 * a) * math.cos(a), cy + sy * (4 + 3.2 * a) * math.sin(a)) for a in np.linspace(0, 4.4 * math.pi, 60)]
        d.line(pts, fill=LACQ + (230,), width=4)
        d.ellipse((x + sx * 120 - 6, y + sy * 18 - 6, x + sx * 120 + 6, y + sy * 18 + 6), fill=ORCHID + (230,))
        d.ellipse((x + sx * 18 - 6, y + sy * 120 - 6, x + sx * 18 + 6, y + sy * 120 + 6), fill=ORCHID + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def qu(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, sword_on=True, **kw):
    """屈原: slender robe, tall 切云冠 (cloud-cutting hat), long sword (长铗) slung at the waist, orchid at the belt."""
    capped = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if capped else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if capped:
        d = A.d[layer]
        d.polygon([(x - 0.04 * h, y - 0.95 * h), (x + 0.04 * h, y - 0.95 * h), (x + 0.06 * h, y - 1.2 * h), (x - 0.0 * h, y - 1.22 * h)], fill=255)
        d.line((x - 0.08 * h, y - 1.0 * h, x + 0.09 * h, y - 1.0 * h), fill=255, width=max(2, int(0.012 * h)))
    if sword_on and not kneel and not kw.get('fall'):
        A.d[layer].line((x - dir * 0.28 * h, y - 0.3 * h, x + dir * 0.2 * h, y - 0.55 * h), fill=255, width=max(2, int(0.018 * h)))
        A.d['orchid'].ellipse((x - 0.05 * h, y - 0.55 * h, x + 0.05 * h, y - 0.47 * h), fill=255)
    return hand

def bells(A, cx, y, n, struck, t, p=1.0):
    q = ease_out(p)
    w = 640 * q
    A.d['lacq'].rectangle((cx - w / 2, y - 20, cx + w / 2, y), fill=255)
    for sx in (-1, 1):
        A.d['lacq'].rectangle((cx + sx * w / 2 - 14, y - 20, cx + sx * w / 2 + 14, y + 420), fill=255)
    for i in range(n):
        bx = cx - w / 2 + 60 + i * (w - 120) / max(1, n - 1)
        s = 1.2 - i * 0.07
        sw = 6 * math.sin(t * 12 + i) * (1 if i < struck else 0) * math.exp(-((t * 2) % 2))
        hb = 150 * s
        A.d['ink'].line((bx, y, bx + sw, y + 40), fill=255, width=4)
        x0 = bx + sw
        A.d['gold' if i < struck else 'ink'].polygon([(x0 - 34 * s, y + 40), (x0 + 34 * s, y + 40), (x0 + 48 * s, y + 40 + hb), (x0, y + 30 + hb * 0.92), (x0 - 48 * s, y + 40 + hb)], fill=255)
        for j in range(3):
            A.d['ink'].line((x0 - 30 * s, y + 70 + j * 30 * s, x0 + 30 * s, y + 70 + j * 30 * s), fill=150, width=3)

def river(A, y0, t, rows=4, amp=8, speed=1.2):
    A.d['ocean'].rectangle((60, y0, W - 60, GROUND + 60), fill=120)
    waves(A, y0 + 10, t, rows=rows, amp=amp, speed=speed)

def dragon_boat(A, x, y, s, t, dir=1, rowers=6):
    d = A.d['lacq']
    d.polygon([(x - s, y - 10), (x + s, y - 10), (x + 0.9 * s, y + 14), (x - 0.9 * s, y + 14)], fill=255)
    hx = x + dir * s
    d.polygon([(hx, y - 10), (hx + dir * 0.18 * s, y - 0.45 * s), (hx + dir * 0.32 * s, y - 0.4 * s), (hx + dir * 0.22 * s, y - 0.25 * s), (hx + dir * 0.05 * s, y + 4)], fill=255)
    d.line((x - dir * s, y - 10, x - dir * 1.15 * s, y - 0.35 * s), fill=255, width=8)
    for k in range(rowers):
        rx = x - 0.75 * s + k * (1.5 * s / max(1, rowers - 1))
        person(A, rx, y - 10, 0.28 * s, dir=dir, robe=False, hat='knot', bow=30, arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 9 + k * 0.4)), layer='ink')

def zongzi(A, x, y, s, layer='orchid'):
    A.d[layer].polygon([(x, y - s), (x + 0.8 * s, y + 0.5 * s), (x - 0.8 * s, y + 0.5 * s)], fill=255)
    A.d['ink'].line((x - 0.4 * s, y - 0.1 * s, x + 0.4 * s, y - 0.1 * s), fill=220, width=3)
    A.d['ink'].line((x, y - s, x, y + 0.5 * s), fill=160, width=2)

def orchid_tuft(A, x, base, s, t):
    for k in range(7):
        a = -math.pi / 2 + (k - 3) * 0.28 + 0.05 * math.sin(t * 1.5 + k)
        leaf(A, 'orchid', x, base, a, s * (0.7 + 0.1 * (k % 3)), s * 0.05, fill=235)
    for k in range(3):
        fx, fy = x + (k - 1) * 0.25 * s, base - 0.7 * s - 0.1 * s * k
        A.d['apricot'].ellipse((fx - 0.06 * s, fy - 0.04 * s, fx + 0.06 * s, fy + 0.04 * s), fill=230)

# ================================================================ chapter card
CH = {16: 1, 48: 2, 80: 3, 112: 5, 144: 7}
def art_bells_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    bells(A, 540, 830, 7, CH.get(kb, 2), t, p=u / 0.5)
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_bells_chapter)
    ink_in(cv, text_img(no, SERIF, 56, LACQ, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_y_hook_festival(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=6)
    dragon_boat(A, lerp(-100, 540, ease_out(u / (1.6 * P))), 1270, 260, t)

def art_y_hook_lisao(A, cv, t, u):
    n = min(40, int(clamp(u / (1.6 * P)) * 40) + 4)
    slips(A, 540 - n * 19 / 2, 1300, n, 380, layer='lacq')
    ground(A, GROUND)

def art_y_hook_ask(A, cv, t, u):
    r = random.Random(3)
    for k in range(50):
        x = r.uniform(80, 1000); y = r.uniform(640, 1100)
        tw = 2 + 2 * math.sin(t * 3 + k)
        A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)
    ground(A, GROUND)
    qu(A, 540, GROUND, 260, dir=1, arm=lerp(20, 170, ease_out(u / (1.2 * P))))

def art_y_hook_stone(A, cv, t, u):
    river(A, 1200, t, rows=4, amp=8)
    p = ease_out(u / (1.6 * P))
    for k in range(4):
        r = 30 + 80 * p + k * 40
        A.d['wash'].ellipse((540 - r, 1300 - r * 0.25, 540 + r, 1300 + r * 0.25), outline=int(220 * (1 - k * 0.2)), width=4)

# ================================================================ 第一回 楚国才子
def art_y_zigui(A, cv, t, u):
    for k, (x, h) in enumerate(((200, 520), (480, 640), (820, 560))):
        A.d['mid'].polygon([(x - 260, GROUND), (x - 40, GROUND - h), (x + 40, GROUND - h + 40), (x + 260, GROUND)], fill=200)
    pts = [(lerp(60, W - 60, f), 1300 + 40 * math.sin(f * 5)) for f in np.linspace(0, 1, 30)]
    A.d['ocean'].line(pts, fill=160, width=40)
    for k in range(3):
        x = 380 + k * 90
        A.d['ink'].polygon([(x - 40, 1250), (x, 1210), (x + 40, 1250)], fill=255)
        A.d['ink'].rectangle((x - 30, 1250, x + 30, 1290), fill=255)
    A.flush(cv)
    stamp(cv, seal('秭归', 56), 860, 880, t, t - u + P, rot=6)

def art_y_orange(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].line((560, GROUND, 570, 1100), fill=255, width=22)
    r = random.Random(11)
    for k in range(40):
        a = r.uniform(0, 2 * math.pi); rr = r.uniform(0, 1) ** 0.5 * 200
        x, y = 570 + rr * math.cos(a), 1000 + rr * 0.6 * math.sin(a)
        leaf(A, 'orchid', x, y, r.uniform(0, 6.28), 40, 8, fill=230)
    for k in range(int(clamp(u / (2 * P)) * 12)):
        a = k * 0.53 + 0.3; rr = 140 * ((k * 37) % 10) / 10 + 30
        x, y = 570 + rr * math.cos(a), 1000 + rr * 0.6 * math.sin(a)
        A.d['ember'].ellipse((x - 18, y - 18, x + 18, y + 18), fill=255)
    person(A, 300, GROUND, 170, dir=1, robe=True, hat='knot', arm=lerp(20, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.flush(cv)
    type_in(cv, text_img('受命不迁 生南国兮', SERIF, 46, LACQ, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + P, 0.5)

def art_y_zuotu(A, cv, t, u):
    A.d['lacq'].rectangle((300, 860, 780, 1180), fill=255)
    A.d['ink'].polygon([(260, 860), (820, 860), (720, 780), (360, 780)], fill=255)
    for k in range(5):
        A.d['ink'].rectangle((330 + k * 100, 900, 350 + k * 100, 1180), fill=255)
    ground(A, GROUND)
    person(A, 540, 1180, 200, dir=-1, robe=True, hat='crown', arm=50, layer='ink')
    A.d['lacq'].rectangle((300, 1180, 780, 1210), fill=255)
    qu(A, 280, GROUND, 230, dir=1, arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 2.5)))
    A.flush(cv)
    stamp(cv, seal('楚怀王', 46, INK), 860, 960, t, t - u + P, rot=6)

def art_y_hezong(A, cv, t, u):
    names = ['楚', '齐', '魏', '赵', '韩', '燕']
    p = ease_out(u / (2 * P))
    for i, nm in enumerate(names):
        a = -math.pi / 2 + i * 2 * math.pi / 6
        r = lerp(380, 220, p)
        x, y = 540 + r * math.cos(a), 1060 + r * 0.8 * math.sin(a)
        A.d['lacq' if i == 0 else 'mid'].ellipse((x - 60, y - 60, x + 60, y + 60), fill=255 if i == 0 else 200)
        A.d['ink'].line((x, y, 540, 1060), fill=int(160 * p), width=5)
    A.d['ink'].ellipse((480, 1000, 600, 1120), outline=255, width=8)
    A.flush(cv)
    for i, nm in enumerate(names):
        a = -math.pi / 2 + i * 2 * math.pi / 6
        r = lerp(380, 220, p)
        paste(cv, text_img(nm, BRUSH, 70, (250, 240, 230) if i == 0 else INK), 540 + r * math.cos(a), 1060 + r * 0.8 * math.sin(a), 1, 1)
    ink_in(cv, text_img('秦', BRUSH, 80, ZHU), 540, 1060, t, t - u + 1.5 * P, dur=0.3, settle=1.3)

def art_y_draft(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 520, GROUND, 340, layer='lacq')
    n = int(clamp(u / (2 * P)) * 14) + 2
    slips(A, 420, GROUND - 90, n, 120, layer='mid')
    sitter(A, 270, GROUND, 220, dir=1, bow=15)
    x = lerp(1000, 760, ease_out((u - 2 * P) / 0.6))
    person(A, x, GROUND, 230, dir=-1, robe=True, hat='none', arm=lerp(20, 110, ease_out((u - 2.6 * P) / 0.4)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('宪令', 54), 300, 920, t, t - u + P, rot=-5)
    if u > 2.4 * P:
        stamp(cv, seal('上官大夫', 42, INK), 820, 900, t, t - u + 2.4 * P, rot=6)

def art_y_slander(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='lacq')
    ground(A, GROUND)
    person(A, 540, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=lerp(30, 140, ease_out((u - 1.5 * P) / 0.5)), layer='ink')
    person(A, 760, GROUND, 180, dir=-1, robe=True, hat='none', bow=20, arm=90, layer='mid')
    x = lerp(300, 120, ease_out((u - 2 * P) / P))
    qu(A, x, GROUND, 220, dir=-1, ph=t * 4 if u > 2 * P else None, arm=-8)
    A.flush(cv)
    for k in range(int(clamp((u - 0.3) / P) * 3)):
        paste(cv, text_img('谗', BRUSH, 70, ZHU), 820 + k * 50, 1080 - k * 40, 1, 0.9)

def art_y_lisao(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 400
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    ground(A, GROUND)
    sitter(A, 760, GROUND, 230, dir=-1, bow=10)
    p = ease_out(u / (2 * P))
    slips(A, 160, GROUND - 40, int(6 + 20 * p), 300, layer='mid', tied=False)
    lamp(A, 600, GROUND, 60, t, glow=0.6)
    A.flush(cv)
    for i, ln in enumerate(('长太息以掩涕兮', '哀民生之多艰')):
        type_in(cv, text_img(ln, SERIF, 46, LACQ if i else INK, 'Black', bleed=False, vertical=True, spacing=4), 440 - i * 70, 920, t, t - u + 0.4 + i * P, 0.6)

def art_y_zhangyi(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 80, ease_out((u - P) / 0.5)), layer='ink')
    person(A, 380, GROUND, 220, dir=1, robe=True, hat='none', bow=20, arm=lerp(40, 130, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    scroll(A, 560, 980, 260, 120, u / 0.6, layer='yellow')
    A.flush(cv)
    stamp(cv, seal('张仪', 50, INK), 300, 900, t, t - u + 0.4, rot=-5)
    if u > 0.6:
        ink_in(cv, text_img('六百里', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), 560, 980, t, t - u + 0.6, dur=0.3)

# ================================================================ 第二回 张仪欺楚
def art_y_six_li(A, cv, t, u):
    p = ease_out((u - P) / P)
    w = lerp(760, 60, p)
    A.d['grass'].rectangle((540 - w / 2, 1000, 540 + w / 2, 1000 + lerp(300, 40, p)), fill=200)
    A.d['ink'].rectangle((540 - w / 2, 1000, 540 + w / 2, 1000 + lerp(300, 40, p)), outline=255, width=5)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('六百里' if u < 1.2 * P else '六里', SERIF, 72, ZHU, 'Black', bleed=False, spacing=6), W / 2, 900, 1, 1)
    if u > 2 * P:
        stamp(cv, seal('受骗', 60), 860, 1200, t, t - u + 2 * P, rot=8)

def art_y_danyang(A, cv, t, u):
    ground(A, GROUND)
    for k in range(8):
        person(A, 120 + k * 60, GROUND, 130, dir=1, robe=False, hat='helmet', spear=True, fall=-70 * ease_out((u - P - k * 0.08) / 0.4), arm=40, layer='lacq')
    for k in range(5):
        rider(A, lerp(1200, 700, ease_out(u / (1.5 * P))) + k * 90, GROUND, 120, -1, t * 10 + k, layer='ink', spear=True)
    A.flush(cv)
    stamp(cv, seal('丹阳', 56, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('斩首八万', SERIF, 52, ZHU, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((u - 1.6 * P) / 0.3))

def art_y_lantian(A, cv, t, u):
    for k in range(4):
        x = 180 + k * 240
        A.d['mid'].polygon([(x - 180, GROUND), (x, GROUND - 360 - 60 * (k % 2)), (x + 180, GROUND)], fill=200)
    flames(A, 540, GROUND, 760, 220 * ease_out((u - P) / 0.8), t, n=8, seed=33, smoke=True)
    ground(A, GROUND)
    for k in range(4):
        flag(A, 200 + k * 220, GROUND, 300, t, w=70) if k % 2 else None
    A.flush(cv)
    stamp(cv, seal('蓝田', 56, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_y_kill_zhangyi(A, cv, t, u):
    palace(A, 540, 1160, 500, layer='lacq')
    ground(A, GROUND)
    person(A, 700, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=30, layer='ink')
    qu(A, 330, GROUND, 240, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 4)))
    x = lerp(860, 1100, ease_out((u - 1.5 * P) / P))
    carriage(A, x, GROUND, 100, dir=1, wheel=u * 6, ph=t * 9, moving=True, layer='mid')
    A.flush(cv)
    stamp(cv, seal('追之不及', 42, INK), 860, 900, t, t - u + 2.5 * P, rot=6)

def art_y_hanbei(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 210
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 300 - 80 * (k % 2)), (x + 150, GROUND)], fill=200)
    A.d['ocean'].line([(60, 1360), (500, 1330), (1020, 1370)], fill=150, width=26)
    ground(A, GROUND)
    x = lerp(800, 360, ease_out(u / (3 * P)))
    qu(A, x, GROUND, 200, dir=-1, ph=t * 4, arm=-8)
    for k in range(5):
        crow(A, 300 + k * 120 + 30 * math.sin(t + k), 820 + (k % 2) * 40, 26, t * 6 + k)
    A.flush(cv)
    stamp(cv, seal('汉北', 54, INK), 860, 880, t, t - u + P, rot=6)

def art_y_jiuge(A, cv, t, u):
    for k in range(6):
        a = t * 0.8 + k * math.pi / 3
        x, y = 540 + 280 * math.cos(a), GROUND - 60 + 30 * math.sin(a)
        person(A, x, y, 150, dir=1 if math.sin(a) > 0 else -1, robe=True, hat='knot', female=k % 2 == 0,
               arm=lerp(40, 170, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='lacq' if k % 2 else 'ink')
    flames(A, 540, GROUND - 40, 120, 160, t, n=4, seed=8, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('东皇太一', 42), 860, 880, t, t - u + P, rot=6)

def art_y_invite(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(1100, 760, ease_out(u / (1.5 * P)))
    rider(A, x, GROUND, 150, -1, t * 9, layer='ink', moving=u < 1.5 * P)
    scroll(A, 540, 960, 300, 140, (u - 1.5 * P) / 0.5, layer='yellow')
    qu(A, 260, GROUND, 240, dir=1, arm=lerp(20, 140, ease_out((u - 2 * P) / 0.4)))
    A.flush(cv)
    if u > 1.8 * P:
        ink_in(cv, text_img('武关之约', SERIF, 46, ZHU, 'Black', bleed=False, spacing=6), 540, 960, t, t - u + 1.8 * P, dur=0.3)

def art_y_zilan(A, cv, t, u):
    palace(A, 540, 1160, 500, layer='lacq')
    ground(A, GROUND)
    person(A, 540, GROUND, 230, dir=1, robe=True, hat='crown', arm=20, ph=t * 3, layer='ink')
    person(A, 720, GROUND, 180, dir=-1, robe=True, hat='none', bow=20, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 4)), layer='mid')
    qu(A, 280, GROUND, 220, dir=1, kneel=True, bow=40, arm=100)
    A.flush(cv)
    stamp(cv, seal('子兰', 50, INK), 760, 900, t, t - u + 0.4, rot=6)

# ================================================================ 第三回 怀王客死
def art_y_wuguan(A, cv, t, u):
    """8-beat set piece: 武关 — the royal carriage rolls through; the gate shuts behind it; Qin soldiers close in."""
    ph = u / P
    city_wall(A, 60, W - 60, 1060, gate_x=540, label='武关', layer='mid', open_=1 - ease_out((ph - 4) / 1))
    ground(A, GROUND)
    x = lerp(-160, 540, ease_out(ph / 3.5)) if ph < 4 else 540
    if ph < 4.6:
        carriage(A, x, GROUND, 140, dir=1, wheel=u * 5, ph=t * 8, moving=ph < 3.5, layer='ink')
    if ph >= 4.5:
        n = int(clamp((ph - 4.5) / 2) * 10)
        for k in range(n):
            side = -1 if k % 2 else 1
            px = 540 + side * (140 + (k // 2) * 80)
            person(A, px, GROUND, 150, dir=-side, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    if ph >= 4.2:
        stamp(cv, seal('关门闭', 50, INK), 860, 880, t, t - u + 4.2 * P, rot=6)
    if ph >= 6.5:
        paste(cv, text_img('怀王被扣 · 求割地', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 6.5) / 0.3))

def art_y_qingxiang(A, cv, t, u):
    palace(A, 540, GROUND, 600, layer='lacq')
    ground(A, GROUND)
    person(A, 540, GROUND - 60, 190, dir=1, robe=True, hat='crown', arm=20, layer='ink')
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='none', arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('令尹子兰', 44), 300, 920, t, t - u + P, rot=-5)

def art_y_escape(A, cv, t, u):
    city_wall(A, 640, 1020, 1100, gate_x=830, label='赵', layer='mid', open_=0.0)
    ground(A, GROUND)
    x = lerp(100, 560, ease_out(u / (1.5 * P))) - lerp(0, 420, ease_out((u - 2 * P) / P))
    person(A, x, GROUND, 180, dir=1 if u < 2 * P else -1, robe=True, hat='crown', ph=t * 7, arm=40, layer='ink')
    if u > 2 * P:
        for k in range(3):
            rider(A, x - 180 - k * 120, GROUND, 120, 1, t * 11 + k, layer='mid', spear=True)
    A.flush(cv)
    stamp(cv, seal('赵不纳', 48, INK), 830, 900, t, t - u + 1.5 * P, rot=6)

def art_y_dies_qin(A, cv, t, u):
    for k in range(50):
        q = (t * 0.5 + k / 50) % 1
        x = 80 + (k * 19) % 920
        A.d['wash'].ellipse((x - 5, lerp(620, 1420, q) - 5, x + 5, lerp(620, 1420, q) + 5), fill=220)
    A.d['ink'].rectangle((380, 1180, 700, 1260), fill=255)
    A.d['lacq'].rectangle((380, 1180, 700, 1196), fill=255)
    ground(A, GROUND)
    for k in range(5):
        person(A, 160 + k * 60, GROUND, 120, dir=1, robe=True, hat='knot', kneel=True, bow=55, arm=110, layer='mid')
    A.flush(cv)
    stamp(cv, seal('归葬郢', 48), 860, 900, t, t - u + P, rot=6)

def art_y_again(A, cv, t, u):
    ground(A, GROUND)
    person(A, 400, GROUND, 220, dir=1, robe=True, hat='none', bow=30, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 4)), layer='mid')
    person(A, 700, GROUND - 40, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 140, ease_out((u - P) / 0.5)), layer='ink')
    A.d['lacq'].rectangle((560, GROUND - 40, 840, GROUND), fill=255)
    A.flush(cv)
    stamp(cv, seal('迁之', 56), 860, 900, t, t - u + 1.6 * P, rot=6)

def art_y_exile_south(A, cv, t, u):
    """6-beat: 沅湘 — the river winds south; he walks its bank, hair loose; mist rises."""
    pts = [(lerp(60, W - 60, f), 1240 + 60 * math.sin(f * 4 + 0.5)) for f in np.linspace(0, 1, 40)]
    A.d['ocean'].polygon(pts + [(W - 60, GROUND + 40), (60, GROUND + 40)], fill=120)
    waves(A, 1260, t, rows=2, amp=5, speed=1.0)
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, 1240), (x, 1240 - 260 - 60 * (k % 2)), (x + 150, 1240)], fill=180)
    x = lerp(160, 880, clamp(u / (5.5 * P)))
    y = 1240 + 60 * math.sin((x - 60) / (W - 120) * 4 + 0.5) - 6
    qu(A, x, y, 170, dir=1, ph=t * 3, arm=-8, sword_on=True)
    for k in range(14):
        q = (t * 0.2 + k / 14) % 1
        A.d['wash'].ellipse((100 + (k * 71) % 880 - 40, lerp(1240, 900, q) - 12, 100 + (k * 71) % 880 + 40, lerp(1240, 900, q) + 12), fill=int(130 * math.sin(math.pi * q)))
    A.flush(cv)
    stamp(cv, seal('沅湘', 54), 860, 860, t, t - u + P, rot=6)

# ================================================================ 第四回 行吟泽畔
QUESTIONS = ['遂古之初 谁传道之', '上下未形 何由考之', '日月安属 列星安陈', '天何所沓 十二焉分',
             '九天之际 安放安属', '昆仑悬圃 其居安在', '何阖而晦 何开而明', '出自汤谷 次于蒙汜']
def scene_tianwen(cv, t, c, k):
    """8-beat custom scene: 天问 — he stands on a bluff, each beat one question rises into the starry sky; the counter
    climbs toward 一百七十余问; at the end the sky answers nothing."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    r = random.Random(17)
    for k2 in range(80):
        x = r.uniform(80, 1000); y = r.uniform(640, 1200)
        tw = max(0.5, 1.5 + 2 * math.sin(t * 3 + k2))
        A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)
    A.d['ink'].polygon([(60, GROUND), (60, 1300), (380, 1260), (520, 1320), (620, GROUND)], fill=255)
    qu(A, 360, 1262, 200, dir=1, arm=lerp(30, 175, 0.5 + 0.5 * math.sin(t * 1.5)), layer='ink')
    A.flush(cv)
    for i, q in enumerate(QUESTIONS):
        st = i * P
        if ph * P >= st:
            v = (t - s0 - st) / (3 * P)
            if v < 1:
                y = lerp(1240, 680, ease_out(v))
                x = 640 + 220 * math.sin(i * 1.7)
                paste(cv, text_img(q, SERIF, 40, INK if i % 2 else (90, 60, 120), 'Black', bleed=False, vertical=True, spacing=2), x, y, lerp(1.0, 0.7, v), 1 - clamp((v - 0.7) / 0.3))
    n = min(170, int(lerp(1, 170, clamp(ph / 7.5))))
    fx = Art()
    chars_in(cv, fx, '天问', BRUSH, 170, INK, W / 2, 440, t, s0, stagger=0.1, seed=114)
    fx.flush(cv)
    paste(cv, text_img(f'第{cn_num(n)}问' if n < 170 else '一百七十余问', SERIF, 50, ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('问天 问地 问历史 · 无人能答', SERIF, 44, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 6) / 0.4))

def art_y_shejiang(A, cv, t, u):
    river(A, 1260, t, rows=2, amp=5, speed=1.4)
    ground(A, 1260, x0=60, x1=700)
    qu(A, lerp(120, 460, ease_out(u / (3 * P))), 1260, 280, dir=1, ph=t * 4 if u < 3 * P else None, arm=10)
    A.flush(cv)
    type_in(cv, text_img('带长铗之陆离兮 冠切云之崔嵬', SERIF, 40, LACQ, 'Black', bleed=False, spacing=2), W / 2, 1448, t, t - u + P, 0.6)

def art_y_fisherman(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=5, speed=1.0)
    ground(A, 1240, x0=60, x1=480)
    qu(A, 330, 1240, 250, dir=1, arm=lerp(-8, 60, 0.5 + 0.5 * math.sin(t * 2)))
    boat(A, 760, 1280, 120, t, sail=False)
    person(A, 760, 1250, 130, dir=-1, robe=False, hat='knot', arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2.5)), layer='ink')
    A.d['ink'].line((700, 1150, 600, 1050), fill=255, width=4)
    A.flush(cv)
    stamp(cv, seal('渔父', 50, INK), 760, 900, t, t - u + 0.4, rot=6)

def art_y_canglang(A, cv, t, u):
    river(A, 1220, t, rows=4, amp=6, speed=1.2)
    x = lerp(620, 1000, ease_out((u - P) / (2.5 * P)))
    boat(A, x, 1270, 110, t, sail=False)
    person(A, x, 1240, 120, dir=1, robe=False, hat='knot', arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    for k in range(4):
        q = (t * 0.5 + k / 4) % 1
        A.d['wash'].ellipse((x - 140 - 60 * q, 1270 - 10, x - 100 - 60 * q, 1270 + 10), fill=int(200 * (1 - q)))
    A.flush(cv)
    type_in(cv, text_img('沧浪之水清兮 可以濯吾缨', SERIF, 42, LACQ, 'Black', bleed=False, spacing=4), W / 2, 880, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('沧浪之水浊兮 可以濯吾足', SERIF, 42, INK, 'Black', bleed=False, spacing=4), W / 2, 950, t, t - u + 1.4 * P, 0.5)

def art_y_nine_years(A, cv, t, u):
    ground(A, GROUND)
    n = min(9, int(clamp(u / (3 * P)) * 9) + 1)
    for i in range(9):
        x = 160 + i * 95
        A.d['orchid' if i < n else 'mid'].line((x, GROUND, x + 6 * math.sin(t + i), GROUND - 80 - 20 * (i % 3)), fill=255 if i < n else 120, width=8)
    sitter(A, 540, GROUND - 100, 180, dir=-1, bow=20)
    A.d['mid'].polygon([(400, GROUND - 100), (680, GROUND - 100), (720, GROUND), (360, GROUND)], fill=200)
    A.flush(cv)
    paste(cv, text_img(f'流放第{cn_num(n)}年', SERIF, 50, LACQ, 'Black', bleed=False, spacing=6), W / 2, 880, 1, 1)

def art_y_ying_falls(A, cv, t, u):
    palace(A, 540, GROUND, 620, collapse=ease_out((u - P) / (2 * P)), layer='lacq')
    flames(A, 540, GROUND, 700, 300 * ease_out((u - 0.5 * P) / 0.8), t, n=8, seed=44, smoke=True)
    ground(A, GROUND)
    for k in range(4):
        rider(A, lerp(-200, 260, ease_out(u / (2 * P))) - k * 110, GROUND, 120, 1, t * 11 + k, layer='ink', spear=True)
    A.flush(cv)
    stamp(cv, seal('白起', 54, INK), 860, 880, t, t - u + 0.4, rot=6)
    stamp(cv, seal('郢', 64), 300, 900, t, t - u + 1.5 * P, rot=-6)

def art_y_aiying(A, cv, t, u):
    ground(A, GROUND)
    qu(A, 760, GROUND, 230, dir=-1, kneel=True, bow=lerp(10, 60, ease_out(u / P)), arm=60)
    for k in range(6):
        crow(A, lerp(900, 200, ((t * 0.15 + k * 0.17) % 1)), 860 + 30 * math.sin(k), 30, t * 6 + k)
    A.d['mid'].polygon([(120, 1160), (180, 1100), (240, 1160)], fill=180)
    A.d['mid'].rectangle((130, 1160, 230, 1230), fill=180)
    A.flush(cv)
    type_in(cv, text_img('鸟飞反故乡兮 狐死必首丘', SERIF, 44, LACQ, 'Black', bleed=False, spacing=4), W / 2, 1448, t, t - u + 0.5, 0.5)

# ================================================================ 第五回 魂归汨罗
def art_y_huaisha(A, cv, t, u):
    """6-beat set piece: 怀沙 — he walks into the river holding a stone; ripples widen; a single orchid floats away."""
    ph = u / P
    river(A, 1180, t, rows=4, amp=6, speed=0.8)
    ground(A, 1180, x0=60, x1=360)
    if ph < 3:
        x = lerp(200, 560, ease_out(ph / 3))
        sink = clamp((ph - 2) / 1) * 220
        hgt = 230
        qu(A, x, 1180 + sink * 0.2, hgt, dir=1, ph=t * 3, arm=80, sword_on=False)
        A.d['mid'].ellipse((x + 30, 1180 - 150 + sink * 0.2, x + 80, 1180 - 110 + sink * 0.2), fill=255)
        if ph > 2:
            A.d['ocean'].rectangle((x - 60, 1180, x + 80, 1180 + 100), fill=200)
    rp = ease_out((ph - 3) / 2.5)
    if rp > 0:
        for k in range(4):
            r = 40 + 360 * rp + k * 50
            A.d['wash'].ellipse((560 - r, 1220 - r * 0.15, 560 + r, 1220 + r * 0.15), outline=int(220 * (1 - rp) * (1 - k * 0.2)), width=4)
        ox = 560 + 300 * rp
        A.d['orchid'].ellipse((ox - 16, 1214, ox + 16, 1226), fill=255)
    A.flush(cv)
    if ph >= 3.3:
        paste(cv, text_img('五月初五', SERIF, 60, LACQ, 'Black', bleed=False, spacing=10), W / 2, 880, 1, clamp((ph - 3.3) / 0.4))

def art_y_race(A, cv, t, u):
    river(A, 1180, t, rows=4, amp=6, speed=2.4)
    for k in range(3):
        x = lerp(-300, 1300, ((t * 0.12 + k * 0.33) % 1))
        dragon_boat(A, x, 1240 + k * 60, 200 - k * 30, t + k, rowers=5)
    A.flush(cv)
    stamp(cv, seal('相传', 46, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_y_zongzi(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=5)
    ground(A, 1240, x0=60, x1=420)
    for k in range(3):
        person(A, 140 + k * 90, 1240, 150, dir=1, robe=False, hat='knot', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='ink')
    for k in range(6):
        q = ((t * 0.7 + k / 6) % 1)
        x = lerp(420, 860, q); y = 1180 - 220 * math.sin(math.pi * q) + (60 if q > 0.9 else 0)
        zongzi(A, x, y, 26)
    A.flush(cv)
    stamp(cv, seal('相传', 46, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_y_chuci(A, cv, t, u):
    ground(A, GROUND)
    for i in range(int(clamp(u / (2.5 * P)) * 5) + 1):
        bundle(A, 260 + i * 140, GROUND - 40, 110, layer='lacq')
    sitter(A, 900, GROUND, 160, dir=-1, bow=15)
    A.flush(cv)
    stamp(cv, seal('刘向', 50, INK), 860, 920, t, t - u + P, rot=6)

def art_y_world(A, cv, t, u):
    p = ease_out(u / (2 * P))
    for i in range(4):
        a = -math.pi / 2 + i * math.pi / 2 + t * 0.2
        x, y = 540 + 280 * p * math.cos(a), 1060 + 200 * p * math.sin(a)
        A.d['mid' if i else 'lacq'].ellipse((x - 70, y - 70, x + 70, y + 70), fill=220)
        person(A, x, y + 60, 110, dir=1, robe=True, hat='none' if i else 'knot', arm=20, layer='ink')
    A.d['ocean'].ellipse((380, 900, 700, 1220), outline=200, width=6)
    A.flush(cv)
    stamp(cv, seal('屈原', 46), 540, 1060 - 200 * p - 90, t, t - u + 2 * P)

def art_y_duanwu(A, cv, t, u):
    river(A, 1260, t, rows=3, amp=5, speed=1.6)
    dragon_boat(A, lerp(1200, 540, ease_out(u / (1.6 * P))), 1290, 220, t, dir=-1, rowers=6)
    for k in range(3):
        zongzi(A, 820 + k * 60, 1120, 30)
    A.flush(cv)
    stamp(cv, seal('非遗', 54), 300, 900, t, t - u + P, rot=-5)

def art_y_legacy(A, cv, t, u):
    river(A, 1260, t, rows=3, amp=5)
    orchid_tuft(A, 540, 1250, 360, t)

def art_y_title(A, cv, t, u):
    river(A, 1380, t, rows=2, amp=5)
    orchid_tuft(A, 860, 1380, 300, t)
    qu(A, 430, 1400, 680, dir=1, arm=lerp(-5, 35, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '楚国才子'), 48: ('第二回', '张仪欺楚'), 80: ('第三回', '怀王客死'),
            112: ('第四回', '行吟泽畔'), 144: ('第五回', '魂归汨罗')}

CARDS = [
    C(0, 2, 'end', 'num', num='两千多年', line='人们为他过一个节', art=art_y_hook_festival),
    C(2, 4, 'works', 'num', num='两千四百字', line='写尽一生孤愤', art=art_y_hook_lisao),
    C(4, 6, 'night', 'num', num='一百七十问', line='把老天都问住了', art=art_y_hook_ask),
    C(6, 8, 'death', 'num', num='五月初五', line='他抱石投江', art=art_y_hook_stone),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 楚国才子
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-340, main='生于秭归', sub='楚国贵族 · 名平 字原', note='一说 生于寅年寅月寅日', art=art_y_zigui),
    C(22, 26, 'works', 'card', year=-322, main='橘颂', sub='少年咏橘 · 独立不迁', note='一说 屈原早年之作', art=art_y_orange),
    C(26, 30, 'court', 'card', year=-319, main='官拜左徒', sub='深得楚怀王信任', note='入则图议国事 出则接遇宾客', art=art_y_zuotu),
    C(30, 34, 'empire', 'card', year=-318, main='合纵抗秦', sub='东方诸国联手 · 楚王为纵约长', art=art_y_hezong),
    C(34, 38, 'works', 'card', year=-316, main='造为宪令', sub='起草变法之令', note='上官大夫见而欲夺之', art=art_y_draft),
    C(38, 42, 'night', 'card', year=-313, main='谗言', sub='上官大夫进谗 · 怀王疏远屈原', note='王怒而疏屈平', art=art_y_slander),
    C(42, 46, 'fate', 'card', year=-313, main='离骚', sub='忧愁幽思而作', note='作年 一说在此后', art=art_y_lisao),
    C(46, 48, 'court', 'card', year=-313, main='张仪入楚', sub='许地六百里 · 要楚绝齐', art=art_y_zhangyi),
    # ---- 第二回 张仪欺楚
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'night', 'card', year=-313, main='六百变六', sub='楚与齐绝交 · 只得六里地', note='仪曰 臣与王约六里', art=art_y_six_li),
    C(54, 58, 'war', 'card', year=-312, main='丹阳之败', sub='楚军大败 · 大将被俘', art=art_y_danyang),
    C(58, 62, 'war', 'card', year=-312, main='蓝田再败', sub='倾国之兵 · 又遭惨败', art=art_y_lantian),
    C(62, 66, 'court', 'card', year=-311, main='何不杀张仪', sub='出使齐国归来 · 力谏怀王', note='怀王悔 追张仪不及', art=art_y_kill_zhangyi),
    C(66, 70, 'fate', 'card', year=-305, main='放逐汉北', sub='第一次被流放', note='一说', art=art_y_hanbei),
    C(70, 74, 'works', 'card', year=-304, main='九歌', sub='采楚地祭歌 · 改写成诗', note='作年不详', art=art_y_jiuge),
    C(74, 78, 'war', 'card', year=-299, main='秦王相邀', sub='约楚王武关会盟', note='秦虎狼之国 不可信', art=art_y_invite),
    C(78, 80, 'night', 'card', year=-299, main='子兰劝行', sub='怀王执意赴约', art=art_y_zilan),
    # ---- 第三回 怀王客死
    C(80, 82, 'night', 'chapter'),
    C(82, 90, 'war', 'card', year=-299, main='武关', sub='怀王入秦 · 被扣为人质', note='秦闭武关 遂与西至咸阳', art=art_y_wuguan),
    C(90, 94, 'court', 'card', year=-298, main='顷襄即位', sub='子兰出任令尹', art=art_y_qingxiang),
    C(94, 98, 'night', 'card', year=-297, main='怀王出逃', sub='奔赵被拒 · 又被抓回', art=art_y_escape),
    C(98, 102, 'death', 'card', year=-296, main='客死于秦', sub='楚人皆怜之', note='如悲亲戚', art=art_y_dies_qin),
    C(102, 106, 'court', 'card', year=-296, main='再遭谗毁', sub='令尹子兰 · 怂恿谗害', note='顷襄王怒而迁之', art=art_y_again),
    C(106, 112, 'fate', 'card', year=-296, main='流放江南', sub='沅湘之间 · 披发行吟', note='颜色憔悴 形容枯槁', art=art_y_exile_south),
    # ---- 第四回 行吟泽畔
    C(112, 114, 'fate', 'chapter'),
    C(114, 122, 'night', 'tianwen', year=-290),
    C(122, 126, 'works', 'card', year=-290, main='涉江', sub='长剑高冠 · 独行江畔', art=art_y_shejiang),
    C(126, 130, 'life', 'card', year=-285, main='渔父', sub='举世皆浊我独清', note='众人皆醉我独醒', art=art_y_fisherman),
    C(130, 134, 'works', 'card', year=-285, main='沧浪之水', sub='渔父一笑 · 鼓枻而去', art=art_y_canglang),
    C(134, 138, 'fate', 'card', year=-280, main='九年不复', sub='流放多年 · 不得回郢', note='至今九年而不复', art=art_y_nine_years),
    C(138, 142, 'war', 'card', year=-278, main='郢都陷落', sub='秦将白起攻破楚都', art=art_y_ying_falls),
    C(142, 144, 'death', 'card', year=-278, main='哀郢', sub='痛哭故都', art=art_y_aiying),
    # ---- 第五回 魂归汨罗
    C(144, 146, 'death', 'chapter'),
    C(146, 152, 'death', 'card', year=-278, main='怀沙', sub='自沉汨罗江', note='相传 时在五月初五', art=art_y_huaisha),
    C(152, 156, 'end', 'card', year=-278, main='竞渡', sub='百姓划船打捞', note='相传 龙舟由此而来', art=art_y_race),
    C(156, 160, 'life', 'card', year=-278, main='粽子', sub='投米入江 · 护其遗体', note='相传', art=art_y_zongzi),
    C(160, 164, 'works', 'card', year=-26, main='楚辞', sub='刘向辑录成书', note='屈宋诸作 汇为一编', art=art_y_chuci),
    C(164, 168, 'empire', 'card', year=1953, main='世界文化名人', sub='与哥白尼等一同被纪念', art=art_y_world),
    C(168, 170, 'end', 'card', year=2009, main='端午', sub='列入人类非物质文化遗产', art=art_y_duanwu),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='贰拾贰', col=LACQ, acc=ORCHID, born=-340, died=-278,
    born_lab='约前340年', died_lab='前278年', years_txt='约公元前340 — 前278',
    hook_q='端午吃粽子 · 你知道是为了谁吗？',
    name_line='屈平 · 字原', name='屈原', seal='灵均', title_art=art_y_title,
    q1='以死明志？', q2='何必投江？',
    end_art=art_y_legacy, end_big='上下求索', end_seal='灵均',
    end_l1='他输掉了一生的政治', end_l2='却赢得了两千年的端午',
    end_brush='吾将上下而求索', end_ask='你会为理想付出一切吗？评论区聊聊', next='项羽'),
    scenes=dict(chapter=scene_chapter, tianwen=scene_tianwen))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
