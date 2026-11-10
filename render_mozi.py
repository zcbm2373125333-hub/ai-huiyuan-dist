"""千古人物志 · 第玖拾肆集 · 墨子 (生卒年不详，约战国初年)
Look: 墨褐 + 光金, carpenter's set-square corners, a timber yard and city walls behind.
Chapter card: 墨斗 — a carpenter's ink-line box snaps a straight black line across a plank; one more line each chapter.
Set pieces: custom 8-beat scene 'zhichu' (止楚攻宋), 6-beat 兼爱, 6-beat 小孔成像, 6-beat 墨者.
Birth and death years are unknown (no_age); every year shown is approximate.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_laozi as Lz           # engine + helpers (previous episode)
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
from render_kongzi import kong, slips, bundle
from render_zhuangzi import king
from render_mengzi import meng
from render_sunwu import army, banner
from render_simayi import emperor

F.RIPPLE = False
MOHE = (116, 92, 70)                # 墨褐
GUANGJIN = (222, 178, 76)           # 光金
S.LAYERS.append(('mohe', MOHE, 0.9, 1.0))
S.LAYERS.append(('guangjin', GUANGJIN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='墨', life='匠', court='兼', night='光', war='攻', empire='守', works='经', fate='侠', death='绝', end='墨')
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
G.THEMES['empire']['sun'] = (MOHE, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (GUANGJIN, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(5):                 # stacked timber at the margins
    _d.rectangle((60, 1400 - _k * 18, 200, 1414 - _k * 18), fill=MOHE + (60,))
    _d.rectangle((880, 1400 - _k * 18, 1020, 1414 - _k * 18), fill=MOHE + (60,))
for _k in range(3):
    _d.line((220, 1424 + _k * 12, 860, 1424 + _k * 12), fill=MOHE + (40 - _k * 10,), width=2)
MTN_COL = {'night': (30, 30, 36), 'death': (62, 60, 60), 'war': (112, 66, 50), 'fate': (98, 94, 90)}
def draw_background(t, theme):
    """工匠: low hills, stacks of timber at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(198, 194, 188), (168, 162, 152), MTN_COL.get(theme, (120, 112, 100))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.72))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """矩尺: a carpenter's set-square in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=MOHE + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=MOHE + (220,), width=3)
        cx, cy = x + sx * 24, y + sy * 24
        d.polygon([(cx, cy), (cx + sx * 70, cy), (cx + sx * 70, cy + sy * 12), (cx + sx * 12, cy + sy * 12), (cx + sx * 12, cy + sy * 50), (cx, cy + sy * 50)], fill=GUANGJIN + (230,))
        for k in range(1, 6):
            d.line((cx + sx * 12 * k, cy, cx + sx * 12 * k, cy + sy * 6), fill=(90, 70, 50, 230), width=2)

# ================================================================ primitives
def mo_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, **kw):
    """墨子: lean, hair in a plain knot, a short coarse brown tunic (褐衣), straw sandals, bare shins."""
    hand = person(A, x, y, h, dir=dir, robe=False, hat='knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if kw.get('fall'):
        return hand
    top = y - (0.48 if kneel else 0.76) * h
    A.d['mohe'].polygon([(x - 0.1 * h, top), (x + 0.1 * h, top), (x + 0.14 * h, top + 0.42 * h), (x - 0.14 * h, top + 0.42 * h)], fill=200)
    return hand

def gongshu(A, x, y, h, dir=-1, layer='mid', **kw):
    """公输盘: a master craftsman-official, longer robe, a set-square at his belt."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='knot', layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        A.d['guangjin'].polygon([(x - dir * 0.12 * h, y - 0.5 * h), (x - dir * 0.02 * h, y - 0.5 * h), (x - dir * 0.02 * h, y - 0.46 * h), (x - dir * 0.08 * h, y - 0.46 * h), (x - dir * 0.08 * h, y - 0.36 * h), (x - dir * 0.12 * h, y - 0.36 * h)], fill=255)
    return hand

def yunti(A, x, base, s, t, dir=1, layer='mohe', rise=1.0):
    """云梯: a wheeled base with a hinged ladder that swings up."""
    A.d[layer].rectangle((x - s, base - 0.35 * s, x + s, base - 0.15 * s), fill=255)
    for wx in (x - 0.7 * s, x + 0.7 * s):
        A.d['ink'].ellipse((wx - 0.18 * s, base - 0.36 * s, wx + 0.18 * s, base), outline=255, width=max(3, int(0.05 * s)))
    a = lerp(0.1, 1.1, rise)
    tx, ty = x - dir * 0.8 * s + dir * 2.4 * s * math.cos(a), base - 0.35 * s - 2.4 * s * math.sin(a)
    for off in (-0.06, 0.06):
        A.d['ink'].line((x - dir * 0.8 * s, base - 0.35 * s + off * s, tx, ty + off * s), fill=255, width=max(3, int(0.04 * s)))
    for k in range(1, 8):
        f = k / 8
        px, py = lerp(x - dir * 0.8 * s, tx, f), lerp(base - 0.35 * s, ty, f)
        A.d['ink'].line((px - 0.04 * s, py - 0.06 * s, px + 0.04 * s, py + 0.06 * s), fill=230, width=3)

def modou(A, cx, cy, s, n, snap=1.0):
    """墨斗: a plank with `n` straight ink lines; the newest line is snapped as `snap` → 1; the ink box sits at the right."""
    A.d['mohe'].rectangle((cx - s, cy - 0.45 * s, cx + s, cy + 0.45 * s), fill=170)
    A.d['ink'].rectangle((cx - s, cy - 0.45 * s, cx + s, cy + 0.45 * s), outline=200, width=4)
    for k in range(n):
        y = cy - 0.35 * s + k * 0.17 * s
        last = (k == n - 1)
        bow = 0.06 * s * (1 - snap) * math.sin(snap * 20) if last else 0
        A.d['ink'].line([(cx - 0.95 * s, y), (cx, y + bow), (cx + 0.95 * s, y)], fill=255, width=4)
    bx, by = cx + 1.15 * s, cy + 0.2 * s
    A.d['mohe'].rectangle((bx - 0.16 * s, by - 0.14 * s, bx + 0.16 * s, by + 0.14 * s), fill=255)
    A.d['ink'].ellipse((bx - 0.1 * s, by - 0.1 * s, bx + 0.1 * s, by + 0.1 * s), outline=255, width=4)

def kite(A, x, y, s, t, layer='mohe'):
    """木鸢: a wooden bird with straight wings."""
    fl = 0.12 * math.sin(t * 6)
    A.d[layer].polygon([(x - s, y + fl * s), (x, y - 0.1 * s), (x + s, y + fl * s), (x, y + 0.12 * s)], fill=255)
    A.d['ink'].polygon([(x - 0.08 * s, y - 0.2 * s), (x + 0.3 * s, y), (x - 0.08 * s, y + 0.2 * s), (x - 0.3 * s, y)], fill=255)

def pinhole(A, t, n_rays=1.0):
    """小孔成像: an upright figure-candle on the left, a wall with a pinhole, an inverted image on the screen at the right."""
    ground(A, GROUND)
    A.d['ink'].rectangle((520, GROUND - 520, 560, GROUND), fill=255)
    A.d['wash'].rectangle((520, GROUND - 300, 560, GROUND - 284), fill=255)
    A.d['mid'].rectangle((900, GROUND - 520, 940, GROUND), fill=230)
    mo_(A, 220, GROUND, 260, dir=1, arm=-8)
    hy = GROUND - 292
    tops = (220, GROUND - 260); feet = (220, GROUND)
    if n_rays > 0:
        for (px, py) in (tops, feet):
            ex = 900; ey = hy + (hy - py) * (ex - 540) / (540 - px)
            q = clamp(n_rays)
            A.d['guangjin'].line((px, py, lerp(px, 540, q), lerp(py, hy, q)), fill=230, width=4)
            if q > 0.5:
                q2 = clamp((n_rays - 0.5) * 2)
                A.d['guangjin'].line((540, hy, lerp(540, ex, q2), lerp(hy, ey, q2)), fill=230, width=4)
    if n_rays >= 1:
        A.d['mohe'].polygon([(870, GROUND - 400), (890, GROUND - 400), (895, GROUND - 230), (865, GROUND - 230)], fill=230)
        A.d['mohe'].ellipse((866, GROUND - 230, 894, GROUND - 200), fill=230)

# ================================================================ chapter card
CH = {16: 1, 48: 2, 80: 3, 112: 4, 144: 5}
def art_modou_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = CH.get(kb, 2)
    q = ease_out(u / (1.2 * P))
    modou(A, 520, 1060, 300, n, snap=clamp((q - 0.2) / 0.5))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_modou_chapter)
    ink_in(cv, text_img(no, SERIF, 56, MOHE, 'Black', bleed=False, spacing=12), W / 2, 1320, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1445, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_m_hook_walk(A, cv, t, u):
    for k in range(3):
        x = 220 + k * 320
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 240), (x + 240, GROUND)], fill=140)
    ground(A, GROUND)
    mo_(A, lerp(200, 800, clamp(u / (2 * P))), GROUND, 220, dir=1, ph=t * 4, arm=-8)

def art_m_hook_nine(A, cv, t, u):
    ground(A, GROUND)
    yunti(A, 360, GROUND, 120, t, rise=0.5 + 0.5 * math.sin(t * 2))
    A.flush(cv)
    for i in range(min(9, int(u / (0.2 * P)) + 1)):
        paste(cv, text_img('距', SERIF, 44, ZHU, 'Black', bleed=False), 560 + (i % 3) * 110, 980 + (i // 3) * 90, 1, 1)

def art_m_hook_light(A, cv, t, u):
    pinhole(A, t, n_rays=clamp(u / (1.4 * P)) * 1.0)

def art_m_hook_sat(A, cv, t, u):
    A.d['ocean'].ellipse((430, 1080, 650, 1300), fill=200)
    cx, cy = 540 + 300 * math.cos(t * 0.6), 1190 + 90 * math.sin(t * 0.6)
    A.d['guangjin'].rectangle((cx - 40, cy - 30, cx + 40, cy + 30), fill=255)
    for s in (-1, 1):
        A.d['mohe'].rectangle((min(cx + s * 50, cx + s * 170), cy - 18, max(cx + s * 50, cx + s * 170), cy + 18), fill=255)

# ================================================================ 第一回 匠人
def art_m_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 200), (x + 240, GROUND)], fill=140)
    A.d['wash'].rectangle((420, GROUND - 140, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 140), (680, GROUND - 140), (540, GROUND - 200)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('姓墨名翟 鲁国人', SERIF, 50, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '一说宋国人 生卒年不可考', t, t - u + P)

def art_m_carpenter(A, cv, t, u):
    ground(A, GROUND)
    A.d['mohe'].rectangle((380, GROUND - 90, 860, GROUND - 60), fill=255)
    for x in (420, 820):
        A.d['ink'].rectangle((x - 10, GROUND - 60, x + 10, GROUND), fill=255)
    mo_(A, 300, GROUND, 190, dir=1, bow=30, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 6)))
    A.flush(cv)
    paste(cv, text_img('出身工匠 精于木工', SERIF, 50, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '自称贱人 即平民百姓', t, t - u + P)

def art_m_ru(A, cv, t, u):
    ground(A, GROUND)
    kong(A, 760, GROUND, 200, dir=-1, arm=60, layer='mid')
    mo_(A, 340, GROUND, 180, dir=1, kneel=True, arm=-8)
    A.flush(cv)
    paste(cv, text_img('早年学儒 受孔子之术', SERIF, 48, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见淮南子 此时孔子已去世 为再传', t, t - u + P)

def art_m_leave(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        person(A, 640 + k * 90, GROUND, 160, dir=1, robe=True, hat='knot', bow=20, arm=60, layer='mid')
    mo_(A, lerp(500, 160, ease_out(u / (3 * P))), GROUND, 190, dir=-1, ph=t * 2, arm=-8)
    A.flush(cv)
    paste(cv, text_img('嫌礼节繁琐 厚葬伤民', SERIF, 48, MOHE, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('另立门户', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_m_kite(A, cv, t, u):
    ground(A, GROUND)
    mo_(A, 300, GROUND, 190, dir=1, arm=lerp(40, 150, clamp(u / P)))
    q = clamp((u - P) / (2 * P))
    kite(A, lerp(380, 820, q), lerp(GROUND - 200, 960 - 80 * math.sin(q * 3), q), 110, t)
    A.flush(cv)
    paste(cv, text_img('造木鸢 三年而成 飞一日而败', SERIF, 46, MOHE, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '见韩非子 墨子鲁问篇则记为公输盘所造', t, t - u + P)

def art_m_axle(A, cv, t, u):
    ground(A, GROUND)
    for wx in (400, 680):
        A.d['ink'].ellipse((wx - 80, GROUND - 160, wx + 80, GROUND), outline=255, width=10)
    A.d['mohe'].rectangle((360, GROUND - 210, 720, GROUND - 150), fill=255)
    A.d['guangjin'].rectangle((390, GROUND - 90, 410, GROUND - 70), fill=255)
    A.flush(cv)
    paste(cv, text_img('不如为车辖 用寸木载重物', SERIF, 48, MOHE, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '有用于人才算巧', t, t - u + P)

# ================================================================ 第二回 墨家
def art_m_jianai(A, cv, t, u):
    """6-beat set piece: 兼爱 — figures from separate houses join one by one into a ring around the screen."""
    ph = u / P
    ground(A, GROUND)
    n = min(10, int(ph * 2) + 2)
    for i in range(10):
        a = i / 10 * 2 * math.pi
        tx, ty = 540 + 330 * math.cos(a), 1180 + 90 * math.sin(a)
        sx = 140 + i * 90
        q = clamp((ph - i * 0.45) / 1.0) if i < n else 0
        x = lerp(sx, tx, ease_out(q)); y = lerp(GROUND, ty + 130, ease_out(q))
        person(A, x, y, 120, dir=1 if math.cos(a) < 0 else -1, robe=(i % 2 == 0), hat='knot', arm=60 if q >= 1 else -8, layer='ink' if i % 3 else 'mohe')
    A.flush(cv)
    if ph < 2:
        lab, col = '视人之国 若视其国', MOHE
    elif ph < 4:
        lab, col = '视人之身 若视其身', MOHE
    else:
        lab, col = '天下兼相爱则治 交相恶则乱', ZHU
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '墨子 兼爱篇', t, t - u + P)

def art_m_feigong(A, cv, t, u):
    ground(A, GROUND)
    army(A, 120, GROUND, 6, dir=1, t=t, h=110)
    mo_(A, 760, GROUND, 200, dir=-1, arm=150)
    A.flush(cv)
    paste(cv, text_img('杀一人谓之不义', SERIF, 48, MOHE, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('攻人之国 却称为义？', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_m_jieyong(A, cv, t, u):
    ground(A, GROUND)
    mo_(A, 540, GROUND, 240, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('节用 节葬 非乐', SERIF, 50, MOHE, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('穿粗布 穿草鞋 日夜不休', SERIF, 46, MOHE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_m_disciples(A, cv, t, u):
    ground(A, GROUND)
    for k in range(min(5, int(u / (0.3 * P)) + 1)):
        mo_(A, 160 + k * 130, GROUND, 130, dir=1, layer='mid', arm=-8)
    mo_(A, 900, GROUND, 200, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('弟子多为工匠 农夫', SERIF, 50, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_m_juzi(A, cv, t, u):
    """6-beat set piece: 墨者 — a tightly disciplined order under a leader (钜子); they would walk into fire for it."""
    ph = u / P
    ground(A, GROUND)
    mo_(A, 540, GROUND, 220, dir=1, arm=60 if ph > 1 else -8)
    for k in range(6):
        x = 140 + k * 80 if k < 3 else 740 + (k - 3) * 80
        mo_(A, x, GROUND, 140, dir=1 if k < 3 else -1, kneel=ph > 2, bow=20 if ph > 2 else 0, arm=-8, layer='mid')
    if ph >= 4:
        flames(A, 540, GROUND, 900, 120 * clamp((ph - 4) / 0.6), t, n=6, seed=941, smoke=False)
    A.flush(cv)
    lab, col = ('首领称为钜子 墨者之法 纪律森严', MOHE) if ph < 4 else ('赴火蹈刃 死不旋踵', ZHU)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '语出淮南子', t, t - u + 4 * P)

def art_m_xianxue(A, cv, t, u):
    ground(A, GROUND)
    kong(A, 380, GROUND, 210, dir=1, arm=-8, layer='mid')
    mo_(A, 700, GROUND, 210, dir=-1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('世之显学 儒墨也', SERIF, 52, MOHE, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '韩非子 显学篇', t, t - u + P)

# ================================================================ 第三回 止楚
def art_m_yunti(A, cv, t, u):
    palace(A, 820, 1300, 220, layer='mid')
    ground(A, GROUND)
    yunti(A, 400, GROUND, 140, t, rise=clamp(u / (2 * P)))
    gongshu(A, 700, GROUND, 200, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('公输盘为楚国造云梯 将攻宋', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def scene_zhichu(cv, t, c, k):
    """8-beat custom scene: 止楚攻宋 — he walks ten days and nights to the Chu capital; with his belt for a wall and
    wooden tablets for engines he meets 公输盘 nine times; the king calls off the attack."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    if ph < 2:
        for kk in range(3):
            x = 220 + kk * 320
            A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 240), (x + 240, GROUND)], fill=140)
        mo_(A, lerp(120, 900, ph / 2), GROUND, 200, dir=1, ph=t * 5, arm=-8)
        A.d['wash'].rectangle((lerp(120, 900, ph / 2) - 14, GROUND - 34, lerp(120, 900, ph / 2) + 14, GROUND - 6), fill=255)
        lab, col = '十日十夜 赶到楚都郢', MOHE
    elif ph < 6:
        A.d['mohe'].rectangle((300, GROUND - 74, 780, GROUND - 60), fill=255)
        A.d['ink'].arc((400, GROUND - 260, 680, GROUND - 80), 200, 340, fill=255, width=8)
        n = min(9, int((ph - 2) / 0.42) + 1)
        for i in range(n):
            x = 420 + (i % 5) * 50; y = GROUND - 120 - (i // 5) * 40
            A.d['ink' if i % 2 else 'mohe'].rectangle((x, y, x + 30, y + 22), fill=255)
        gongshu(A, 220, GROUND, 190, dir=1, kneel=True, arm=100)
        mo_(A, 860, GROUND, 190, dir=-1, kneel=True, arm=100)
        lab, col = f'解带为城 第{cn_num(n)}次攻城 被他化解', MOHE
    else:
        palace(A, 540, 1300, 260, layer='mid')
        king(A, 540, GROUND, 210, dir=-1, arm=60)
        mo_(A, 320, GROUND, 190, dir=1, bow=20, arm=-8)
        gongshu(A, 780, GROUND, 180, dir=-1, kneel=True, bow=20, arm=-8)
        lab, col = '楚王 善哉 吾请无攻宋矣', ZHU
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '止楚攻宋', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=94)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '公输盘之攻械尽 墨子之守圉有余', t, s0 + 3 * P)

def art_m_qin(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='宋', layer='mid')
    for k in range(6):
        mo_(A, 220 + k * 120, 1080, 90, dir=1, arm=40, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('弟子禽滑釐等三百人 已守在宋城', SERIF, 44, MOHE, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '杀了我也没用', t, t - u + P)

def art_m_rain(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='宋', layer='mid', open_=0.0)
    ground(A, GROUND)
    for k in range(30):
        x = (k * 37 + t * 200) % 1000 + 40; y = (k * 91 + t * 900) % 600 + 800
        A.d['wash'].line((x, y, x - 10, y + 40), fill=150, width=2)
    mo_(A, 360, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('归途遇雨 宋人不让他避雨', SERIF, 48, MOHE, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '治于神者 众人不知其功', t, t - u + P)

def art_m_luyang(A, cv, t, u):
    palace(A, 540, 1300, 260, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND, 200, dir=-1, robe=True, hat='crown', arm=-8, layer='ink')
    mo_(A, 360, GROUND, 190, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    paste(cv, text_img('劝鲁阳文君 不要攻郑', SERIF, 48, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见墨子 鲁问篇', t, t - u + P)

def art_m_qi(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        banner(A, 700 + k * 100, GROUND, 220, t, layer='mid', fallen=clamp((u - P - k * 0.2 * P) / P))
    mo_(A, 360, GROUND, 190, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('一生奔走 劝阻诸国攻伐', SERIF, 48, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 墨经
def art_m_pinhole(A, cv, t, u):
    """6-beat set piece: 小孔成像 — light from a standing figure passes through a small hole and forms an upside-down image."""
    ph = u / P
    pinhole(A, t, n_rays=clamp(ph / 3) * 1.0)
    A.flush(cv)
    lab, col = ('光线穿过小孔', MOHE) if ph < 3 else ('成一倒立之像', ZHU)
    paste(cv, text_img(lab, SERIF, 50, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '墨经 景到 在午有端', t, t - u + 3 * P)

def art_m_lever(A, cv, t, u):
    ground(A, GROUND)
    a = 0.15 * math.sin(t)
    cx, cy = 600, GROUND - 120
    A.d['ink'].polygon([(cx - 30, GROUND), (cx + 30, GROUND), (cx, cy)], fill=255)
    A.d['mohe'].line((cx - 400 * math.cos(a), cy - 400 * math.sin(a), cx + 160 * math.cos(a), cy + 160 * math.sin(a)), fill=255, width=12)
    A.d['ink'].rectangle((cx + 160 * math.cos(a) - 50, cy + 160 * math.sin(a) - 100, cx + 160 * math.cos(a) + 50, cy + 160 * math.sin(a)), fill=255)
    A.flush(cv)
    paste(cv, text_img('记载杠杆 浮力 力的道理', SERIF, 48, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_m_circle(A, cv, t, u):
    ground(A, GROUND)
    q = clamp(u / (1.5 * P))
    A.d['ink'].arc((340, 960, 740, 1360), 0, 360 * q, fill=255, width=6)
    A.d['ink'].ellipse((530, 1150, 550, 1170), fill=255)
    for k in range(int(q * 6)):
        a = k * math.pi / 3
        A.d['guangjin'].line((540, 1160, 540 + 200 * math.cos(a), 1160 + 200 * math.sin(a)), fill=255, width=3)
    A.flush(cv)
    paste(cv, text_img('圜 一中同长也', SERIF, 52, MOHE, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '墨经中的几何定义', t, t - u + P)

def art_m_defense(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='城', layer='mid')
    ground(A, GROUND)
    for k in range(4):
        mo_(A, 220 + k * 200, 1080, 90, dir=1, arm=60, layer='ink')
    A.flush(cv)
    paste(cv, text_img('写下备城门诸篇 专讲守城', SERIF, 48, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_m_old(A, cv, t, u):
    ground(A, GROUND)
    mo_(A, lerp(900, 300, ease_out(u / (4 * P))), GROUND, 190, dir=-1, ph=t * 2, bow=10, arm=-8)
    A.flush(cv)
    paste(cv, text_img('摩顶放踵 利天下为之', SERIF, 50, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '语出孟子 本是批评 却成了赞誉', t, t - u + P)

def art_m_death(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 200), (x + 240, GROUND)], fill=130)
    A.d['mid'].chord((440, GROUND - 60, 640, GROUND + 60), 180, 360, fill=220)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('墨子去世 葬处无考', SERIF, 50, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '提倡节葬 桐棺三寸', t, t - u + P)

# ================================================================ 第五回 绝学
def art_m_mencius(A, cv, t, u):
    ground(A, GROUND)
    meng(A, 540, GROUND, 220, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    paste(cv, text_img('孟子痛斥 墨氏兼爱 是无父也', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_lost(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    emperor(A, 540, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('汉代独尊儒术 墨学渐成绝学', SERIF, 46, MOHE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '沉寂近两千年', t, t - u + P)

def art_m_sun(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 420, layer='mid')
    person(A, 300, GROUND, 180, dir=1, robe=True, hat='none', kneel=True, arm=100, layer='ink')
    lamp(A, 760, GROUND - 74, 28, t, glow=0.8)
    A.flush(cv)
    paste(cv, text_img('孙诒让作墨子间诂', SERIF, 50, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '墨子一书才重新读得懂', t, t - u + P)

def art_m_rediscover(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        person(A, 300 + k * 240, GROUND, 190, dir=1, robe=(k == 1), hat='none', arm=60, layer='ink' if k == 1 else 'mid')
    A.flush(cv)
    paste(cv, text_img('梁启超 胡适等人重新推崇', SERIF, 48, MOHE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_m_satellite(A, cv, t, u):
    art_m_hook_sat(A, cv, t, u)
    A.flush(cv)
    paste(cv, text_img('量子科学实验卫星 命名墨子号', SERIF, 46, MOHE, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '纪念他在光学上的贡献', t, t - u + P)

def art_m_end(A, cv, t, u):
    ground(A, GROUND)
    mo_(A, lerp(300, 900, ease_out(u / (4 * P))), GROUND, 210, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('兼爱 非攻', SERIF, 56, MOHE, 'Black', bleed=False, spacing=12), W / 2, 760, 1, clamp(u / 0.4))

def art_m_legacy(A, cv, t, u):
    modou(A, 840, 1400, 60, 3)

def art_m_title(A, cv, t, u):
    yunti(A, 830, 1440, 90, t, rise=0.6)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    mo_(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '匠人'), 48: ('第二回', '墨家'), 80: ('第三回', '止楚'),
            112: ('第四回', '墨经'), 144: ('第五回', '绝学')}

CARDS = [
    C(0, 2, 'fate', 'num', num='十天十夜', line='他走去阻止一场战争', art=art_m_hook_walk),
    C(2, 4, 'war', 'num', num='九次攻城', line='九次被他挡住', art=art_m_hook_nine),
    C(4, 6, 'night', 'num', num='小孔成像', line='两千多年前就写进书里', art=art_m_hook_light),
    C(6, 8, 'empire', 'num', num='墨子号', line='一颗卫星以他命名', art=art_m_hook_sat),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 匠人
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-468, main='生于鲁国', sub='墨翟', note='年份约略', art=art_m_birth),
    C(22, 26, 'works', 'card', year=-458, main='木匠', sub='出身工匠', note='年份约略', art=art_m_carpenter),
    C(26, 32, 'court', 'card', year=-452, main='学儒', sub='受孔子之术', note='年份约略', art=art_m_ru),
    C(32, 38, 'fate', 'card', year=-448, main='弃儒', sub='另立门户', note='年份约略', art=art_m_leave),
    C(38, 44, 'night', 'card', year=-445, main='木鸢', sub='三年而成', note='年份约略', art=art_m_kite),
    C(44, 48, 'life', 'card', year=-445, main='不如车辖', sub='有用为巧', art=art_m_axle),
    # ---- 第二回 墨家
    C(48, 50, 'court', 'chapter'),
    C(50, 56, 'empire', 'card', year=-440, main='兼爱', sub='爱人若己', note='年份约略', art=art_m_jianai),
    C(56, 60, 'war', 'card', year=-440, main='非攻', sub='反对攻伐', art=art_m_feigong),
    C(60, 64, 'life', 'card', year=-440, main='节用', sub='粗衣草鞋', art=art_m_jieyong),
    C(64, 68, 'works', 'card', year=-440, main='墨者', sub='工匠农夫', art=art_m_disciples),
    C(68, 74, 'fate', 'card', year=-440, main='钜子', sub='纪律森严', art=art_m_juzi),
    C(74, 80, 'court', 'card', year=-440, main='显学', sub='儒墨并称', art=art_m_xianxue),
    # ---- 第三回 止楚
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'war', 'card', year=-440, main='云梯', sub='楚将攻宋', note='年份约略', art=art_m_yunti),
    C(86, 94, 'empire', 'zhichu', year=-440),
    C(94, 98, 'court', 'card', year=-440, main='三百弟子', sub='已守宋城', art=art_m_qin),
    C(98, 104, 'night', 'card', year=-440, main='雨中', sub='宋人不纳', art=art_m_rain),
    C(104, 108, 'life', 'card', year=-410, main='止鲁阳', sub='劝阻攻郑', note='年份约略', art=art_m_luyang),
    C(108, 112, 'fate', 'card', year=-405, main='奔走', sub='劝止攻伐', note='年份约略', art=art_m_qi),
    # ---- 第四回 墨经
    C(112, 114, 'works', 'chapter'),
    C(114, 120, 'night', 'card', year=-400, main='小孔成像', sub='墨经', note='年份约略', art=art_m_pinhole),
    C(120, 124, 'works', 'card', year=-400, main='杠杆', sub='力学之理', art=art_m_lever),
    C(124, 128, 'empire', 'card', year=-400, main='圆', sub='一中同长', art=art_m_circle),
    C(128, 132, 'war', 'card', year=-395, main='守城', sub='备城门', art=art_m_defense),
    C(132, 138, 'life', 'card', year=-390, main='摩顶放踵', sub='利天下', note='年份约略', art=art_m_old),
    C(138, 144, 'death', 'card', year=-376, main='墨子去世', sub='卒年无考', note='年份约略', art=art_m_death),
    # ---- 第五回 绝学
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'fate', 'card', year=-310, main='孟子批墨', sub='无父', note='年份约略', art=art_m_mencius),
    C(150, 154, 'death', 'card', year=-134, main='墨学中绝', sub='近两千年', note='年份约略', art=art_m_lost),
    C(154, 158, 'works', 'card', year=1894, main='墨子间诂', sub='孙诒让', art=art_m_sun),
    C(158, 162, 'court', 'card', year=1920, main='重新发现', sub='近代学者', note='年份约略', art=art_m_rediscover),
    C(162, 166, 'empire', 'card', year=2016, main='墨子号', sub='量子卫星', art=art_m_satellite),
    C(166, 170, 'end', 'card', year=2016, main='兼爱非攻', sub='两千年回响', art=art_m_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='玖拾肆', col=MOHE, acc=GUANGJIN, born=-468, died=-376, age0=-469, no_age=True,
    born_lab='生年不详', died_lab='卒年不详', years_txt='约战国初年 生卒年不详',
    hook_q='一个工匠出身的人 · 凭什么能和孔子齐名？',
    name_line='墨翟 · 墨家创始人', name='墨子', seal='兼爱', title_art=art_m_title,
    q1='侠之鼻祖？', q2='空想家？',
    end_art=art_m_legacy, end_big='兼爱非攻', end_seal='墨翟',
    end_l1='他一辈子穿粗布走远路', end_l2='只为让天下少一场战争',
    end_brush='摩顶放踵', end_ask='兼爱非攻 今天还做得到吗？评论区聊聊', next='韩非子'),
    scenes=dict(chapter=scene_chapter, zhichu=scene_zhichu))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
