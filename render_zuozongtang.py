"""千古人物志 · 第柒拾伍集 · 左宗棠 (1812–1885)
Look: 胡杨褐 + 柳绿, 柳枝 corner borders, 戈壁 dunes and distant snow peaks behind.
Chapter card: 左公柳 — a desert road; one more willow is planted along it each chapter; in the last chapter a gate (玉门关) stands at its end.
Set pieces: custom 8-beat scene 'saifang' (塞防海防之争), 6-beat 湘江夜话, 6-beat 樊燮案, 6-beat 缓进急战,
6-beat 舆榇出关, 6-beat 左公柳.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zengguofan as Zg      # engine + helpers (previous episode)
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
from render_linzexu import foreigner, warship
from render_hairui import coffin
from render_wudi import camel
from render_zengguofan import soldier, letter

F.RIPPLE = False
HUYANG = (172, 110, 50)             # 胡杨褐
LIULV = (96, 140, 76)               # 柳绿
S.LAYERS.append(('huyang', HUYANG, 0.9, 1.0))
S.LAYERS.append(('liulv', LIULV, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='左', life='湘', court='清', night='谋', war='征', empire='疆', works='柳', fate='棺', death='襄', end='疆')
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
G.THEMES['empire']['sun'] = (HUYANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (LIULV, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # dunes
    _d.arc((-200 + _k * 420, 1420 + _k * 6, 400 + _k * 420, 1540), 200, 340, fill=HUYANG + (60 - _k * 10,), width=4)
for _x in (110, 970):               # willows at the margins
    _d.line((_x, 1446, _x, 1330), fill=(110, 90, 70, 70), width=6)
    for _j in range(6):
        _d.line((_x, 1336, _x - 40 + _j * 16, 1420 - 10 * (_j % 2)), fill=LIULV + (70,), width=3)
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (100, 96, 92)}
def draw_background(t, theme):
    """戈壁: low dunes, distant snow peaks, willows at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(206, 200, 190), (186, 170, 146), MTN_COL.get(theme, (150, 120, 90))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.7))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """柳枝: a drooping willow sprig in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=HUYANG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=HUYANG + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.line((cx - 26, cy - 22, cx + 26, cy - 22), fill=(110, 90, 70, 230), width=4)
        for k in range(5):
            xx = cx - 20 + k * 10
            d.line((xx, cy - 22, xx + 3, cy + 14 + 6 * (k % 2)), fill=LIULV + (230,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def zuo(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, armour=False, **kw):
    """左宗棠: Qing official — 顶戴 with a red knob, queue, a stout figure with a thick moustache (grey when old)."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.1 * h, y - 1.02 * h, x + 0.1 * h, y - 0.86 * h), 180, 360, fill=255)
        d.rectangle((x - 0.11 * h, y - 0.95 * h, x + 0.11 * h, y - 0.93 * h), fill=255)
        A.d['red'].ellipse((x - 0.025 * h, y - 1.06 * h, x + 0.025 * h, y - 1.01 * h), fill=255)
        d.line((x - dir * 0.05 * h, y - 0.88 * h, x - dir * 0.08 * h, y - 0.55 * h), fill=255, width=max(2, int(0.015 * h)))
        stache = 'wash' if old > 0.4 else layer
        A.d[stache].line((x - dir * 0.0 * h, y - 0.83 * h, x + dir * 0.1 * h, y - 0.8 * h), fill=255, width=max(3, int(0.022 * h)))
        A.d['huyang'].rectangle((x - 0.08 * h, y - 0.72 * h, x + 0.08 * h, y - 0.6 * h), fill=255)
        if armour:
            A.d['ink'].rectangle((x - 0.1 * h, y - 0.56 * h, x + 0.1 * h, y - 0.5 * h), fill=255)
    return hand

def willow(A, x, base, h, t, layer='liulv'):
    A.d['huyang'].line((x, base, x + 4, base - h), fill=255, width=max(4, int(0.05 * h)))
    for k in range(9):
        a = -math.pi / 2 + (k - 4) * 0.28
        tx, ty = x + 4 + 0.3 * h * math.cos(a), base - h + 0.3 * h * math.sin(a)
        sw = 0.04 * h * math.sin(t * 1.5 + k)
        A.d[layer].line([(tx, ty), (tx + sw + 0.05 * h * math.cos(a), ty + 0.35 * h), (tx + 2 * sw, ty + 0.6 * h)], fill=230, width=max(2, int(0.02 * h)))

def gate(A, cx, base, w, layer='huyang'):
    """玉门关: a square earthen fort."""
    A.d[layer].rectangle((cx - w / 2, base - 0.7 * w, cx + w / 2, base), fill=230)
    for k in range(5):
        A.d[layer].rectangle((cx - w / 2 + k * w / 4.5, base - 0.78 * w, cx - w / 2 + k * w / 4.5 + w / 9, base - 0.7 * w), fill=230)
    A.d['ink'].rectangle((cx - 0.12 * w, base - 0.3 * w, cx + 0.12 * w, base), fill=255)

def dunes(A, base, layer='dune', fill=200):
    for k in range(4):
        A.d[layer].chord((-200 + k * 340, base - 160, 340 + k * 340, base + 160), 180, 360, fill=fill - 20 * (k % 2))

def road(A, base):
    A.d['dune'].polygon([(480, base - 360), (600, base - 360), (980, base), (100, base)], fill=150)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 5)}
POS = [(250, 1220, 200), (830, 1220, 200), (340, 1120, 140), (740, 1120, 140), (400, 1060, 100)]
def art_willow_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    A.d['dune'].polygon([(500, 960), (580, 960), (900, 1240), (180, 1240)], fill=150)
    n = b if q > 0.5 else a
    for i in range(min(n, 4)):
        x, y, h = POS[i]
        willow(A, x, y, h, t)
    if kb == 144 and q > 0.6:
        gate(A, 540, 960, 120)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_willow_chapter)
    ink_in(cv, text_img(no, SERIF, 56, HUYANG, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_q_hook_old(A, cv, t, u):
    dunes(A, GROUND)
    ground(A, GROUND)
    zuo(A, 540, GROUND, 260, dir=1, arm=lerp(-8, 100, ease_out(u / 0.6)), old=0.9)

def art_q_hook_willow(A, cv, t, u):
    ground(A, GROUND)
    road(A, GROUND)
    n = min(6, int(u / (0.2 * P)) + 1)
    for i in range(n):
        s = 1 - i * 0.13
        willow(A, 540 - (300 - i * 40) * (1 if i % 2 else -1), GROUND - i * 50, 200 * s, t)

def art_q_hook_couplet(A, cv, t, u):
    ground(A, GROUND)
    for x in (360, 720):
        A.d['red'].rectangle((x - 50, 860, x + 50, 1360), fill=230)
    A.flush(cv)
    paste(cv, text_img('身\n无\n半\n亩', SERIF, 50, INK, 'Black', bleed=False, spacing=10), 720, 1110, 1, clamp(u / 0.4))
    paste(cv, text_img('心\n忧\n天\n下', SERIF, 50, INK, 'Black', bleed=False, spacing=10), 360, 1110, 1, clamp((u - 0.5) / 0.4))

def art_q_hook_son(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((560, GROUND - 260, 900, GROUND), fill=230)
    A.d['ink'].polygon([(540, GROUND - 260), (920, GROUND - 260), (730, GROUND - 330)], fill=255)
    person(A, lerp(120, 480, ease_out(u / (1.2 * P))), GROUND, 200, dir=1, robe=True, hat='knot', ph=t * 3, arm=-8, load=True, layer='ink')

# ================================================================ 第一回 身无半亩
def art_q_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x - 60, GROUND - 240), (x + 60, GROUND - 240), (x + 220, GROUND)], fill=150)
    A.d['wash'].rectangle((440, GROUND - 160, 640, GROUND), fill=255)
    A.d['ink'].polygon([(420, GROUND - 160), (660, GROUND - 160), (540, GROUND - 220)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('湖南湘阴左家塘 · 家境清寒', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('湘阴', 56), 860, 1020, t, t - u + P, rot=6)

def art_q_juren(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='huyang')
    ground(A, GROUND)
    zuo(A, 540, GROUND, 190, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('中举人 · 时年二十一', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('举人', 56), 860, 1020, t, t - u + P, rot=6)

def art_q_ruzhui(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((560, GROUND - 260, 900, GROUND), fill=230)
    A.d['ink'].polygon([(540, GROUND - 260), (920, GROUND - 260), (730, GROUND - 330)], fill=255)
    A.d['red'].rectangle((690, GROUND - 160, 770, GROUND), fill=220)
    person(A, 520, GROUND, 180, dir=1, robe=True, hat='knot', female=True, arm=-8, layer='liulv')
    zuo(A, 360, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('入赘湘潭周家 · 妻周诒端', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '寄人篱下 发奋读书', t, t - u + P)

def art_q_couplet(A, cv, t, u):
    ground(A, GROUND)
    for x in (300, 780):
        A.d['red'].rectangle((x - 50, 900, x + 50, 1400), fill=230)
    zuo(A, 540, GROUND, 180, dir=1, arm=lerp(-8, 80, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('身\n无\n半\n亩', SERIF, 46, INK, 'Black', bleed=False, spacing=8), 780, 1150, 1, clamp(u / 0.4))
    paste(cv, text_img('心\n忧\n天\n下', SERIF, 46, INK, 'Black', bleed=False, spacing=8), 300, 1150, 1, clamp((u - 0.5) / 0.4))
    paste(cv, text_img('读破万卷 神交古人', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_q_luodi(A, cv, t, u):
    ground(A, GROUND)
    for r in range(2):
        for i in range(6):
            x = 160 + i * 150; y = GROUND - r * 170
            A.d['mid'].rectangle((x - 55, y - 130, x + 55, y), fill=200)
    zuo(A, 540, GROUND, 170, dir=-1, arm=-8, ph=t * 2)
    A.flush(cv)
    paste(cv, text_img('三赴京师会试 · 皆名落孙山', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '从此不再应考 专研舆地兵法', t, t - u + P)

def art_q_anhua(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='huyang')
    zuo(A, 760, GROUND, 180, dir=-1, kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)))
    person(A, 320, GROUND, 120, dir=1, robe=True, hat='none', kneel=True, arm=90, layer='liulv')
    A.flush(cv)
    paste(cv, text_img('受陶澍之托 · 在安化教其子八年', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '得以遍读陶家藏书', t, t - u + P)

def art_q_linzexu(A, cv, t, u):
    """6-beat set piece: 湘江夜话 — 林则徐, passing 长沙 on his way home, invites the unknown 左宗棠 to his boat; they talk all night;
    林 hands him his notes on 新疆."""
    ph = u / P
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=120)
    river(A, 1210, t, rows=2, amp=3)
    A.d['ink'].polygon([(240, 1200), (840, 1200), (800, 1250), (280, 1250)], fill=255)
    A.d['mid'].rectangle((380, 1080, 700, 1200), fill=220)
    lamp(A, 540, 1200, 30, t, glow=1.0)
    person(A, 640, 1200, 150, dir=-1, robe=True, hat='none', kneel=True, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    zuo(A, 440, 1200, 150, dir=1, kneel=True, arm=lerp(100, 40, 0.5 + 0.5 * math.sin(t * 2)))
    if ph >= 3.5:
        A.d['wash'].rectangle((500, 1150, 580, 1180), fill=255)
    A.flush(cv)
    lab = '林则徐归途过长沙 · 邀左宗棠舟中相见' if ph < 2 else ('湘江夜话 彻夜长谈' if ph < 3.5 else '以新疆资料相托')
    paste(cv, text_img(lab, SERIF, 44 if ph < 2 else 46, ZHU if ph >= 3.5 else HUYANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4:
        paste(cv, text_img('东南洋夷 吾能御之 西定新疆 舍君莫属', SERIF, 38, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 4) / 0.4))
    note_in(cv, '林则徐所言见后人记述 原话或有出入', t, t - u + 4 * P)

# ================================================================ 第二回 今亮
def art_q_mufu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    zuo(A, 540, GROUND, 190, dir=1, arm=lerp(-8, 80, ease_out(u / 0.6)), old=0.2)
    A.flush(cv)
    paste(cv, text_img('四十一岁 · 入湖南巡抚幕府', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_luo(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='huyang')
    zuo(A, 280, GROUND, 180, dir=1, kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3)), old=0.2)
    person(A, 820, GROUND, 180, dir=-1, robe=True, hat='knot', kneel=True, arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('入骆秉章幕府 · 湖南军政多出其手', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '自号今亮 以诸葛亮自比', t, t - u + P)

def art_q_fanxie(A, cv, t, u):
    """6-beat set piece: 樊燮案 — the 永州总兵 樊燮 will not bow to a mere advisor; 左宗棠 drives him out with curses;
    樊 accuses him at court; the emperor orders him executed if guilty; friends across the realm plead for him."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2.5:
        person(A, 760, GROUND, 200, dir=-1, robe=False, hat='helmet', arm=-8, layer='mid')
        zuo(A, 360, GROUND, 190, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 6)) if ph > 1 else -8, old=0.2)
        lab = '永州总兵樊燮 拒不行礼' if ph < 1 else '左宗棠怒骂 逐出门外'
    elif ph < 4:
        palace(A, 540, 1300, 320, layer='mid')
        emperor(A, 760, GROUND, 200, dir=-1)
        scroll(A, 400, 1100, 300, 160, 1.0, layer='wash')
        lab = '樊燮反诬 朝廷密令 若属实 就地正法'
    else:
        for j in range(5):
            person(A, 160 + j * 180, GROUND, 150, dir=1 if j < 3 else -1, robe=True, hat='knot', kneel=True, bow=20, arm=90, layer='ink' if j % 2 else 'mid')
        lab = '胡林翼 郭嵩焘 曾国藩等合力营救'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 2.5 else HUYANG, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    note_in(cv, '所骂之语 后世流传多个版本', t, t - u + P)

def art_q_pan(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 600, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('国家不可一日无湖南\n湖南不可一日无左宗棠', SERIF, 44, INK, 'Black', bleed=False, spacing=14), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('潘祖荫上疏 化险为夷', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_q_chujun(A, cv, t, u):
    ground(A, GROUND)
    n = min(8, int(clamp(u / (2.5 * P)) * 8) + 1)
    for j in range(n):
        soldier(A, 140 + j * 110, GROUND, 150, dir=1, layer='huyang')
    banner(A, 980, GROUND, 360, t, layer='huyang')
    A.flush(cv)
    paste(cv, text_img('募五千人 组建楚军 · 时年四十九', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('楚军', 56), 860, 1020, t, t - u + P, rot=6)

def art_q_zhejiang(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='杭州', layer='mid', open_=clamp((u - 2 * P) / P))
    ground(A, GROUND)
    for j in range(6):
        soldier(A, lerp(-100, 400, ease_out(u / (2.5 * P))) + j * 80, GROUND, 120, dir=1, ph=t * 4 + j, layer='huyang')
    A.flush(cv)
    paste(cv, text_img('授浙江巡抚 · 两年后收复杭州', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_mawei(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=3)
    for k in range(3):
        x = 220 + k * 260
        A.d['mid'].rectangle((x - 90, 1020, x + 90, 1200), fill=220)
        A.d['ink'].rectangle((x + 40, 920, x + 66, 1020), fill=255)
    warship(A, lerp(300, 700, ease_out(u / (3 * P))), 1230, 90, t)
    A.flush(cv)
    paste(cv, text_img('创办福州船政局 · 附设船政学堂', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '船政学堂首届学生中有邓世昌', t, t - u + P)

# ================================================================ 第三回 塞防
def art_q_shaangan(A, cv, t, u):
    dunes(A, GROUND)
    ground(A, GROUND)
    for j in range(4):
        camel(A, lerp(-100, 900, ((t * 0.06 + j / 4) % 1)), GROUND, 80, dir=1, ph=t * 3 + j, layer='huyang')
    zuo(A, 820, GROUND, 190, dir=-1, arm=-8, old=0.5)
    A.flush(cv)
    paste(cv, text_img('调任陕甘总督 · 经营西北', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_lanzhou(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].rectangle((x - 110, GROUND - 200, x + 110, GROUND), fill=220)
        A.d['ink'].rectangle((x + 50, GROUND - 320, x + 80, GROUND - 200), fill=255)
    A.d['ocean'].line([(60, GROUND - 20), (1020, GROUND - 30)], fill=200, width=20)
    A.flush(cv)
    paste(cv, text_img('设兰州制造局 · 兰州织呢局', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('兰州', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '西北近代工业由此起步', t, t - u + P)

def scene_saifang(cv, t, c, k):
    """8-beat custom scene: 塞防海防之争 — 李鸿章: give up 新疆, put the money into the navy; 左宗棠: lose 新疆 and you lose 蒙古, and then 京师.
    The court sides with 左."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    A.d['ocean'].rectangle((620, 960, 980, 1300), fill=int(120 + 80 * clamp((ph - 0.5) / 1)))
    waves(A, 1000, t, rows=2, amp=3)
    A.d['dune'].rectangle((100, 960, 460, 1300), fill=int(140 + 80 * clamp((ph - 2.5) / 1)))
    if ph < 2.5:
        person(A, 800, GROUND, 210, dir=-1, robe=True, hat='none', arm=lerp(-8, 100, clamp((ph - 0.5) / 0.6)), layer='ink')
        lab, col = '李鸿章 · 停撤西征 专力海防', HUYANG
    elif ph < 5:
        zuo(A, 280, GROUND, 210, dir=1, arm=lerp(-8, 120, clamp((ph - 2.5) / 0.6)), old=0.6)
        lab, col = '左宗棠 · 塞防海防 二者并重', ZHU
    else:
        palace(A, 540, 1300, 260, layer='mid')
        zuo(A, 280, GROUND, 180, dir=1, bow=15, arm=60, old=0.6)
        person(A, 800, GROUND, 180, dir=-1, robe=True, hat='none', bow=15, arm=-8, layer='ink')
        lab, col = '朝廷采纳左议 · 收复新疆', HUYANG
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '塞防之争', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=75)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    if 3 <= ph < 5:
        paste(cv, text_img('重新疆者所以保蒙古 保蒙古者所以卫京师', SERIF, 38, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 3.4) / 0.4))
    note_in(cv, '其时阿古柏据南疆 沙俄占伊犁', t, s0 + P)

def art_q_dubang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='huyang')
    ground(A, GROUND)
    zuo(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)), old=0.7)
    A.flush(cv)
    paste(cv, text_img('钦差大臣督办新疆军务 · 时年六十四', SERIF, 42, HUYANG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('钦差', 56), 860, 1020, t, t - u + P, rot=6)

def art_q_huanjin(A, cv, t, u):
    """6-beat set piece: 缓进急战 — a year and more spent on grain, camels, carts and farming colonies; then the strike: 北疆 in months, 南疆 the next year."""
    ph = u / P
    dunes(A, GROUND)
    ground(A, GROUND)
    if ph < 2.5:
        for j in range(5):
            camel(A, lerp(-100, 1000, ((t * 0.05 + j / 5) % 1)), GROUND, 80, dir=1, ph=t * 3 + j, layer='huyang')
        for i in range(6):
            A.d['grass'].rectangle((140 + i * 140, GROUND - 30, 230 + i * 140, GROUND - 10), fill=200)
        lab, col = '缓进 · 筹粮 屯田 修路 一年有余', HUYANG
    else:
        army(A, lerp(-200, 500, clamp((ph - 2.5) / 2)), GROUND, 6, dir=1, layer='huyang', t=t, march=True, h=110)
        flag(A, lerp(-40, 660, clamp((ph - 2.5) / 2)), GROUND - 140, 260, t, layer='red')
        lab, col = ('急战 · 数月收复北疆' if ph < 4.5 else '次年 南疆收复'), ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '西征粮饷多赖胡雪岩筹借', t, t - u + P)

def art_q_hou(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    zuo(A, 540, GROUND, 200, dir=1, bow=15, arm=60, old=0.7)
    A.flush(cv)
    paste(cv, text_img('晋封二等恪靖侯', SERIF, 48, HUYANG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('侯', 70, ZHU), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第四回 舆榇出关
def art_q_chonghou(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    person(A, 300, GROUND, 180, dir=1, robe=True, hat='knot', kneel=True, arm=100, layer='ink')
    foreigner(A, 800, GROUND, 190, dir=-1, kneel=True, arm=100)
    A.d['wash'].rectangle((470, GROUND - 120, 610, GROUND - 80), fill=255)
    A.flush(cv)
    paste(cv, text_img('崇厚擅签条约 · 伊犁名还实失', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '举朝哗然', t, t - u + P)

def art_q_coffin(A, cv, t, u):
    """6-beat set piece: 舆榇出关 — at sixty-nine he marches out from 肃州 to 哈密 with his own coffin carried behind him: no retreat."""
    ph = u / P
    dunes(A, GROUND)
    gate(A, 900, GROUND, 180)
    ground(A, GROUND)
    x = lerp(-100, 520, ease_out(ph / 5))
    army(A, x - 520, GROUND, 4, dir=1, layer='huyang', t=t, march=True, h=100)
    for j in (-1, 1):
        person(A, x - 160 + j * 110, GROUND, 120, dir=1, robe=False, hat='knot', ph=t * 4 + j, arm=100, layer='ink')
    coffin(A, x - 160, GROUND - 110, 220)
    zuo(A, x + 60, GROUND, 190, dir=1, ph=t * 3, arm=-8, old=0.9)
    A.flush(cv)
    lab = '六十九岁 · 自肃州出关' if ph < 2 else ('身后抬着一口棺材' if ph < 4 else '此去不胜 不归')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else HUYANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('哈密', 56), 860, 1020, t, t - u + 4 * P, rot=6)

def art_q_liu(A, cv, t, u):
    """6-beat set piece: 左公柳 — along the road from 兰州 westward his troops plant willows mile after mile."""
    ph = u / P
    ground(A, GROUND)
    road(A, GROUND)
    n = min(10, int(clamp(ph / 4) * 10) + 1)
    for i in range(n):
        side = 1 if i % 2 else -1
        d = i // 2
        s = 1 - d * 0.16
        willow(A, 540 + side * (360 - d * 60), GROUND - d * 70, 240 * s, t)
    if ph < 3:
        soldier(A, 760, GROUND, 140, dir=-1, spear=False, bow=40, arm=150, layer='huyang')
    A.flush(cv)
    if ph < 3:
        lab, col = '大军所过 沿途植柳', HUYANG
    else:
        lab, col = '新栽杨柳三千里 引得春风度玉关', ZHU
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 700, 1, 1)
    note_in(cv, '诗为其部将杨昌濬所作', t, t - u + 3 * P)

def art_q_yili(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    person(A, 300, GROUND, 180, dir=1, robe=True, hat='knot', kneel=True, arm=lerp(80, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    foreigner(A, 800, GROUND, 190, dir=-1, kneel=True, arm=60)
    A.flush(cv)
    paste(cv, text_img('曾纪泽赴俄改约 · 收回伊犁大部', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '左宗棠兵临哈密 为谈判之后盾', t, t - u + P)

def art_q_junji(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    zuo(A, 540, GROUND, 190, dir=1, arm=-8, old=0.9)
    A.flush(cv)
    paste(cv, text_img('入值军机 · 旋任两江总督', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_province(A, cv, t, u):
    q = ease_out(u / (2.5 * P))
    A.d['huyang'].polygon([(240, 1200), (360, 960), (620, 900), (860, 1000), (900, 1220), (640, 1300), (380, 1300)], fill=int(220 * q))
    A.d['ink'].polygon([(240, 1200), (360, 960), (620, 900), (860, 1000), (900, 1220), (640, 1300), (380, 1300)], outline=220)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('新疆建省 · 设巡抚于迪化', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('新疆省', 50), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '建省之议 左宗棠多次奏请', t, t - u + P)

# ================================================================ 第五回 心忧天下
def art_q_fujian(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=4)
    for k in range(2):
        warship(A, 640 + k * 240, 1220, 80, t)
    zuo(A, 240, 1200, 190, dir=1, arm=lerp(-8, 100, ease_out(u / 0.6)), old=1.0)
    A.flush(cv)
    paste(cv, text_img('中法战争 · 七十三岁督办福建军务', SERIF, 44, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    zuo(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于福州 · 年七十四', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '相传临终犹言 此次和局 误尽苍生', t, t - u + P)

def art_q_wenxiang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('文襄', 90, ZHU), 540, 1140, t, t - u + 0.6)
    paste(cv, text_img('赠太傅 · 谥文襄', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_oldwillow(A, cv, t, u):
    dunes(A, GROUND)
    ground(A, GROUND)
    willow(A, 540, GROUND, 420, t)
    A.flush(cv)
    paste(cv, text_img('甘肃 新疆 · 仍有百年左公柳', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_q_sixth(A, cv, t, u):
    A.d['huyang'].polygon([(240, 1200), (360, 960), (620, 900), (860, 1000), (900, 1220), (640, 1300), (380, 1300)], fill=220)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('新疆约占中国国土六分之一', SERIF, 46, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_q_jinliang(A, cv, t, u):
    ground(A, GROUND)
    zuo(A, 540, GROUND, 230, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('自比诸葛亮 自号今亮', SERIF, 48, HUYANG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_q_heart(A, cv, t, u):
    for x in (300, 780):
        A.d['red'].rectangle((x - 50, 900, x + 50, 1400), fill=230)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('身\n无\n半\n亩', SERIF, 46, INK, 'Black', bleed=False, spacing=8), 780, 1150, 1, 1)
    paste(cv, text_img('心\n忧\n天\n下', SERIF, 46, INK, 'Black', bleed=False, spacing=8), 300, 1150, 1, 1)
    paste(cv, text_img('少年写下的对联 他用一生兑现', SERIF, 44, HUYANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_q_legacy(A, cv, t, u):
    willow(A, 860, 1440, 120, t)

def art_q_title(A, cv, t, u):
    willow(A, 820, 1440, 260, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    zuo(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '身无半亩'), 48: ('第二回', '今亮'), 80: ('第三回', '塞防'),
            112: ('第四回', '舆榇出关'), 144: ('第五回', '心忧天下')}

CARDS = [
    C(0, 2, 'war', 'num', num='六十四岁', line='带兵收复新疆', art=art_q_hook_old),
    C(2, 4, 'works', 'num', num='三千里柳', line='一路种向玉门关', art=art_q_hook_willow),
    C(4, 6, 'night', 'num', num='一副对联', line='写尽一生抱负', art=art_q_hook_couplet),
    C(6, 8, 'life', 'num', num='上门女婿', line='后来封了侯爵', art=art_q_hook_son),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 身无半亩
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1812, main='生于湘阴', sub='家境清寒', art=art_q_birth),
    C(22, 26, 'empire', 'card', year=1832, main='中举人', sub='二十一岁', art=art_q_juren),
    C(26, 30, 'life', 'card', year=1832, main='入赘周家', sub='上门女婿', art=art_q_ruzhui),
    C(30, 34, 'works', 'card', year=1834, main='身无半亩', sub='心忧天下', note='对联写作年份约略', art=art_q_couplet),
    C(34, 38, 'fate', 'card', year=1838, main='三试不第', sub='不复应考', art=art_q_luodi),
    C(38, 42, 'night', 'card', year=1839, main='安化授徒', sub='陶澍之托', art=art_q_anhua),
    C(42, 48, 'night', 'card', year=1849, main='湘江夜话', sub='林则徐', art=art_q_linzexu),
    # ---- 第二回 今亮
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'court', 'card', year=1852, main='入幕', sub='四十一岁', art=art_q_mufu),
    C(54, 58, 'works', 'card', year=1854, main='骆秉章幕府', sub='自号今亮', art=art_q_luo),
    C(58, 64, 'death', 'card', year=1859, main='樊燮案', sub='险遭不测', art=art_q_fanxie),
    C(64, 68, 'empire', 'card', year=1860, main='化险为夷', sub='潘祖荫上疏', art=art_q_pan),
    C(68, 72, 'war', 'card', year=1860, main='组建楚军', sub='四十九岁', art=art_q_chujun),
    C(72, 76, 'court', 'card', year=1862, main='浙江巡抚', sub='收复杭州', art=art_q_zhejiang),
    C(76, 80, 'works', 'card', year=1866, main='福州船政', sub='马尾', art=art_q_mawei),
    # ---- 第三回 塞防
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'fate', 'card', year=1866, main='陕甘总督', sub='经营西北', art=art_q_shaangan),
    C(86, 90, 'works', 'card', year=1872, main='兰州制造', sub='西北工业', art=art_q_lanzhou),
    C(90, 98, 'court', 'saifang', year=1875),
    C(98, 102, 'empire', 'card', year=1875, main='督办新疆', sub='六十四岁', art=art_q_dubang),
    C(102, 108, 'war', 'card', year=1876, main='缓进急战', sub='收复新疆', art=art_q_huanjin),
    C(108, 112, 'court', 'card', year=1878, main='封侯', sub='二等恪靖侯', art=art_q_hou),
    # ---- 第四回 舆榇出关
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'death', 'card', year=1879, main='伊犁危机', sub='崇厚签约', art=art_q_chonghou),
    C(118, 124, 'fate', 'card', year=1880, main='舆榇出关', sub='六十九岁', art=art_q_coffin),
    C(124, 130, 'works', 'card', year=1880, main='左公柳', sub='三千里', art=art_q_liu),
    C(130, 134, 'court', 'card', year=1881, main='收回伊犁', sub='曾纪泽改约', art=art_q_yili),
    C(134, 138, 'empire', 'card', year=1881, main='入值军机', sub='两江总督', art=art_q_junji),
    C(138, 144, 'empire', 'card', year=1884, main='新疆建省', sub='迪化', art=art_q_province),
    # ---- 第五回 心忧天下
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'war', 'card', year=1884, main='督师福建', sub='七十三岁', art=art_q_fujian),
    C(150, 154, 'death', 'card', year=1885, main='左宗棠去世', sub='福州', art=art_q_death),
    C(154, 158, 'court', 'card', year=1885, main='谥文襄', sub='赠太傅', art=art_q_wenxiang),
    C(158, 162, 'works', 'card', year=1885, main='左公柳', sub='百年犹存', art=art_q_oldwillow),
    C(162, 166, 'empire', 'card', year=1885, main='六分之一', sub='国土', art=art_q_sixth),
    C(166, 168, 'fate', 'card', year=1885, main='今亮', sub='狂生', art=art_q_jinliang),
    C(168, 170, 'end', 'card', year=1885, main='心忧天下', sub='一生兑现', art=art_q_heart),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='柒拾伍', col=HUYANG, acc=LIULV, born=1812, died=1885, age0=1811,
    born_lab='1812年', died_lab='1885年', years_txt='公元1812 — 1885',
    hook_q='他三次会试落榜 · 为什么能收复新疆？',
    name_line='左宗棠 · 字季高', name='左宗棠', seal='今亮', title_art=art_q_title,
    q1='民族英雄？', q2='湖南狂生？',
    end_art=art_q_legacy, end_big='心忧天下', end_seal='今亮',
    end_l1='他六十四岁才去做最大的事', end_l2='为中国留住了六分之一的国土',
    end_brush='左公柳', end_ask='你去过新疆吗？评论区聊聊', next='敬请期待'),
    scenes=dict(chapter=scene_chapter, saifang=scene_saifang))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
