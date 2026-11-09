"""千古人物志 · 第柒拾柒集 · 刘备 (161–223)
Look: 蜀锦红 + 桑叶绿, 草鞋 corner borders (a woven sandal), 巴蜀 hills behind.
Chapter card: 桑盖 — the mulberry tree by his childhood home grows a little each chapter; in the last chapter its crown turns into
the gold canopy of the carriage he once said he would ride.
Set pieces: custom 8-beat scene 'zhujiu' (煮酒论英雄), 6-beat 三顾茅庐, 6-beat 长坂携民, 6-beat 定军山, 6-beat 夷陵, 6-beat 白帝托孤.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_lvbu as Lb            # engine + helpers (previous episode)
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
from render_sunwu import army, banner
from render_songtaizu import tent
from render_huatuo import caocao
from render_guanyu import guan, zhangfei
from render_zhuge import kongming, thatched
from render_sunquan import warship as wu_ship

F.RIPPLE = False
SHUJIN = (150, 52, 62)              # 蜀锦红
SANGYE = (96, 128, 70)              # 桑叶绿
S.LAYERS.append(('shujin', SHUJIN, 0.9, 1.0))
S.LAYERS.append(('sangye', SANGYE, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='刘', life='桑', court='汉', night='英', war='战', empire='蜀', works='德', fate='奔', death='托', end='德')
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
G.THEMES['empire']['sun'] = (SHUJIN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (SANGYE, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # a winding mountain road
    _d.line([(40 + i * 30, 1458 + _k * 12 + 8 * math.sin(i * 0.5 + _k)) for i in range(35)], fill=(120, 110, 90, 44 - _k * 10), width=3)
for _x in (110, 970):               # small mulberry trees at the margins
    _d.line((_x, 1446, _x, 1350), fill=(110, 90, 70, 70), width=6)
    _d.ellipse((_x - 50, 1290, _x + 50, 1370), fill=SANGYE + (60,))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (96, 96, 100)}
def draw_background(t, theme):
    """巴蜀: steep green hills, a mountain road, mulberries at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 192, 186), (156, 166, 150), MTN_COL.get(theme, (106, 122, 100))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.8))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """草鞋: a woven straw sandal in each corner — he once sold them."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=SHUJIN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=SHUJIN + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.ellipse((cx - 14, cy - 30, cx + 14, cy + 30), outline=(170, 140, 80, 230), width=4)
        for k in range(4):
            d.line((cx - 12, cy - 18 + k * 12, cx + 12, cy - 18 + k * 12), fill=(170, 140, 80, 230), width=2)
        d.line((cx - 14, cy - 10, cx + 20, cy - 24), fill=SHUJIN + (230,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def bei(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, crown=False, armour=False, **kw):
    """刘备: long arms, large ears, short beard; a scholar's cap, later a 冕 when king/emperor; a pair of swords at war."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else ('none' if up else 'knot'), layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up and not armour:
        if crown:
            d.rectangle((x - 0.15 * h, y - 1.08 * h, x + 0.15 * h, y - 1.03 * h), fill=255)
            d.rectangle((x - 0.05 * h, y - 1.03 * h, x + 0.05 * h, y - 0.95 * h), fill=255)
            for k in range(4):
                A.d['shujin'].line((x - 0.13 * h + k * 0.085 * h, y - 1.03 * h, x - 0.13 * h + k * 0.085 * h, y - 0.97 * h), fill=255, width=2)
        else:
            d.rectangle((x - 0.07 * h, y - 1.05 * h, x + 0.07 * h, y - 0.94 * h), fill=255)
    if up:
        d.ellipse((x - dir * 0.1 * h - 0.025 * h, y - 0.92 * h, x - dir * 0.1 * h + 0.025 * h, y - 0.82 * h), fill=255)
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.02 * h, y - 0.84 * h), (x + dir * 0.08 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.74 * h)], fill=255)
        A.d['shujin'].rectangle((x - 0.08 * h, y - 0.56 * h, x + 0.08 * h, y - 0.52 * h), fill=255)
    return hand

def mulberry(A, x, base, h, leaves=1.0, layer='sangye'):
    A.d['huyang'].line((x, base, x + 0.04 * h, base - 0.55 * h), fill=255, width=max(6, int(0.07 * h)))
    for a in (-0.7, 0.0, 0.7):
        A.d['huyang'].line((x + 0.04 * h, base - 0.55 * h, x + 0.04 * h + 0.3 * h * math.sin(a), base - 0.55 * h - 0.25 * h * math.cos(a)), fill=255, width=max(4, int(0.04 * h)))
    r = random.Random(3)
    for k in range(int(24 * leaves)):
        a = r.uniform(-1.6, 1.6); d = r.uniform(0.1, 0.45) * h
        cx, cy = x + 0.04 * h + d * math.sin(a), base - 0.75 * h - 0.3 * d * math.cos(a)
        A.d[layer].ellipse((cx - 0.09 * h, cy - 0.06 * h, cx + 0.09 * h, cy + 0.06 * h), fill=255)

def fire_camps(A, n, t, burn=0.0):
    for k in range(n):
        x = 100 + k * (880 / max(1, n - 1))
        tent(A, x, GROUND, 120, 100, layer='mid', open_=0.0)
        if burn > k / n:
            flames(A, x, GROUND - 40, 140, 160, t, n=2, seed=k, smoke=True)

# ================================================================ chapter card
CH = {16: (0.2, 0.4), 48: (0.4, 0.6), 80: (0.6, 0.8), 112: (0.8, 1.0), 144: (1.0, 1.0)}
def art_tree_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (0.4, 0.6))
    q = ease_out(u / (1.2 * P))
    A.d['mid'].rectangle((240, 1200, 840, 1214), fill=200)
    if kb == 144 and q > 0.5:
        r = 260
        A.d['qiuhuang'].chord((540 - r, 940 - 0.5 * r, 540 + r, 940 + 0.5 * r), 180, 360, fill=255)
        A.d['ink'].line((540, 940, 540, 1200), fill=255, width=8)
        for k in range(7):
            A.d['shujin'].line((540 - r + k * r / 3, 940, 540 - r + k * r / 3, 990), fill=255, width=4)
    else:
        mulberry(A, 540, 1200, 360, leaves=lerp(a, b, q))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_tree_chapter)
    ink_in(cv, text_img(no, SERIF, 56, SHUJIN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_e_hook_sandal(A, cv, t, u):
    ground(A, GROUND)
    for i in range(min(8, int(u / (0.15 * P)) + 1)):
        x = 220 + (i % 4) * 200; y = GROUND - 40 - (i // 4) * 110
        A.d['dune'].ellipse((x - 30, y - 70, x + 30, y + 70), fill=230)

def art_e_hook_hut(A, cv, t, u):
    ground(A, GROUND)
    thatched(A, 720, GROUND, 300, layer='mid')
    bei(A, lerp(120, 420, ease_out(u / (1.2 * P))), GROUND, 220, dir=1, ph=t * 3, arm=-8)

def art_e_hook_fire(A, cv, t, u):
    ground(A, GROUND)
    fire_camps(A, 6, t, burn=clamp(u / (1.2 * P)))

def art_e_hook_scroll(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 320, ease_out(u / (1.0 * P)), layer='wash')

# ================================================================ 第一回 桑树
def art_e_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x - 60, GROUND - 220), (x + 60, GROUND - 220), (x + 220, GROUND)], fill=150)
    A.d['wash'].rectangle((360, GROUND - 160, 600, GROUND), fill=255)
    A.d['ink'].polygon([(340, GROUND - 160), (620, GROUND - 160), (480, GROUND - 220)], fill=255)
    mulberry(A, 760, GROUND, 360)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('涿郡涿县 · 自称中山靖王之后', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('涿县', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '其世系已不可确考', t, t - u + P)

def art_e_weave(A, cv, t, u):
    ground(A, GROUND)
    person(A, 680, GROUND, 190, dir=-1, robe=True, hat='knot', female=True, kneel=True, arm=lerp(80, 120, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    person(A, 400, GROUND, 120, dir=1, robe=True, hat='none', kneel=True, arm=lerp(80, 120, 0.5 + 0.5 * math.sin(t * 4 + 1)), layer='shujin')
    for k in range(6):
        A.d['dune'].ellipse((480 + k * 30 - 12, GROUND - 40, 480 + k * 30 + 12, GROUND), fill=230)
    A.flush(cv)
    paste(cv, text_img('少孤 · 与母贩履织席为业', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_e_tree(A, cv, t, u):
    ground(A, GROUND)
    mulberry(A, 600, GROUND, 520)
    person(A, 300, GROUND, 120, dir=1, robe=True, hat='none', arm=lerp(-8, 150, ease_out(u / 0.6)), layer='shujin')
    A.flush(cv)
    type_in(cv, text_img('吾必当乘此羽葆盖车', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.4, 0.6)
    note_in(cv, '屋旁桑树高五丈 远望如车盖 叔父急止 勿妄语', t, t - u + P)

def art_e_luzhi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='sangye')
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='knot', kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    bei(A, 300, GROUND, 140, dir=1, kneel=True, arm=90)
    person(A, 420, GROUND, 140, dir=1, robe=True, hat='none', kneel=True, arm=90, layer='mid')
    A.flush(cv)
    paste(cv, text_img('十五岁从卢植求学 · 与公孙瓒同窗', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_e_youth(A, cv, t, u):
    ground(A, GROUND)
    horse(A, 760, GROUND, 140, dir=-1, ph=0, moving=False, layer='mid')
    bei(A, 440, GROUND, 220, dir=1, arm=lerp(-8, 40, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    paste(cv, text_img('不甚乐读书 · 喜狗马 音乐 美衣服', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '身长七尺五寸 垂手下膝 顾自见其耳', t, t - u + P)

def art_e_rise(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    bei(A, 420, GROUND, 200, dir=1, armour=True, arm=60)
    guan(A, 600, GROUND, 210, dir=1, arm=40)
    zhangfei(A, 260, GROUND, 200, dir=1, spear=True, arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('黄巾起 · 刘备起兵 关羽张飞相随', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '寝则同床 恩若兄弟 桃园结义出自演义', t, t - u + P)

def art_e_duyou(A, cv, t, u):
    ground(A, GROUND)
    mulberry(A, 760, GROUND, 360, leaves=0.6)
    person(A, 720, GROUND, 160, dir=-1, robe=True, hat='knot', bow=40, arm=-8, layer='mid')
    A.d['ink'].line((720, GROUND - 160, 760, GROUND - 300), fill=255, width=4)
    bei(A, 440, GROUND, 200, dir=1, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 6)))
    A.flush(cv)
    paste(cv, text_img('督邮不见 · 缚而鞭之二百 弃官而去', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '演义改作张飞所为', t, t - u + P)

def art_e_xuzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='徐州', layer='mid', open_=1.0)
    ground(A, GROUND)
    bei(A, 540, GROUND, 190, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('陶谦病笃 · 以徐州相托', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 颠沛
def art_e_lose(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    city_wall(A, 160, 920, 1080, gate_x=540, label='下邳', layer='mid', open_=1.0)
    ground(A, GROUND)
    for j in range(4):
        person(A, lerp(-100, 480, ease_out(u / (3 * P))) - j * 90, GROUND, 130, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='chitu')
    A.flush(cv)
    paste(cv, text_img('吕布袭取下邳 · 刘备妻子被俘', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_e_tocao(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    caocao(A, 720, GROUND, 210, dir=-1, arm=lerp(-8, 70, ease_out(u / 0.6)))
    bei(A, 400, GROUND, 200, dir=1, bow=20, arm=60)
    A.flush(cv)
    paste(cv, text_img('走投曹操 · 表为豫州牧', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_zhujiu(cv, t, c, k):
    """8-beat custom scene: 煮酒论英雄 — 曹操 says over wine: the heroes of the world are only you and I; 刘备 drops his chopsticks;
    thunder rolls; he blames the thunder."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    for k in range(3):
        A.d['qingtian'].ellipse((300 + k * 160 - 40, 1100 - 30 - 10 * (k % 2), 300 + k * 160 + 40, 1100 + 30), fill=200)
    desk(A, 540, GROUND, 360, layer='mid')
    A.d['qiuhuang'].ellipse((510, GROUND - 110, 570, GROUND - 74), fill=255)
    for kk in range(4):
        q = (t * 0.5 + kk / 4) % 1
        A.d['wash'].ellipse((540 - 10 - 14 * q, GROUND - 130 - 100 * q - 10, 540 + 10 + 14 * q, GROUND - 130 - 100 * q + 10), fill=int(180 * (1 - q)))
    caocao(A, 760, GROUND, 170, dir=-1, kneel=True, arm=lerp(60, 120, clamp((ph - 2) / 0.6)) if ph < 5 else 60)
    drop = clamp((ph - 4) / 0.4)
    bei(A, 320, GROUND, 170, dir=1, kneel=True, arm=lerp(90, 40, drop), bow=lerp(0, -10, drop))
    if ph >= 4:
        A.d['ink'].line((380, GROUND - 74 - 40 * (1 - drop), 420, GROUND - 74 + 6 * drop), fill=255, width=3)
    if 5 <= ph < 6.5:
        A.d['wash'].polygon([(700, 620), (660, 760), (700, 760), (640, 940), (740, 720), (700, 720), (760, 620)], fill=255)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '煮酒论英雄', BRUSH, 140, INK, W / 2, 440, t, s0, stagger=0.06, seed=77)
    fx.flush(cv)
    if ph < 2:
        lab, col = '青梅煮酒 曹操邀饮', SHUJIN
    elif ph < 4:
        lab, col = '今天下英雄 唯使君与操耳', ZHU
    elif ph < 5:
        lab, col = '刘备手中匕箸落地', SHUJIN
    else:
        lab, col = '适闻雷声 故失匕箸', SHUJIN
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '论英雄见三国志 以雷声掩饰见华阳国志', t, s0 + 4 * P)

def art_e_yidai(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mid')
    person(A, 760, GROUND, 170, dir=-1, robe=True, hat='knot', kneel=True, arm=100, layer='ink')
    bei(A, 320, GROUND, 170, dir=1, kneel=True, arm=100)
    A.d['wash'].rectangle((480, GROUND - 100, 600, GROUND - 76), fill=255)
    lamp(A, 540, GROUND - 74, 26, t, glow=0.6)
    A.flush(cv)
    paste(cv, text_img('与董承受衣带诏 · 密谋诛曹', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_e_yuanshao(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    army(A, lerp(-300, 200, ease_out(u / (3 * P))), GROUND, 5, dir=1, layer='ink', t=t, march=True, h=100)
    bei(A, lerp(560, 1100, ease_out(u / (3 * P))), GROUND, 170, dir=1, ph=t * 5, arm=-8)
    A.flush(cv)
    paste(cv, text_img('曹操东征 · 刘备大败 北投袁绍', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '关羽被擒 后挂印封金而归', t, t - u + P)

def art_e_xinye(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='新野', layer='mid', open_=1.0)
    ground(A, GROUND)
    bei(A, 540, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('南依刘表 · 屯驻新野', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_e_birou(A, cv, t, u):
    ground(A, GROUND)
    bei(A, 540, GROUND, 230, dir=1, bow=20, arm=-8, old=0.3)
    A.flush(cv)
    type_in(cv, text_img('髀肉复生 · 老将至矣 功业不建', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.3, 0.5)
    note_in(cv, '见九州春秋 刘表席间如厕而叹', t, t - u + 0.5)

# ================================================================ 第三回 三顾
def art_e_sangu(A, cv, t, u):
    """6-beat set piece: 三顾茅庐 — he goes to the thatched hut in 隆中 three times; then the 隆中对: take 荆州 and 益州, ally with 孙权;
    孤之有孔明 犹鱼之有水也."""
    ph = u / P
    for i in range(30):
        q = (t * 0.4 + i / 30) % 1
        x = 80 + (i * 61) % 920
        A.d['wash'].ellipse((x - 4, lerp(600, 1400, q) - 4, x + 4, lerp(600, 1400, q) + 4), fill=int(200 * clamp(1 - ph / 2)))
    thatched(A, 760, GROUND, 300, layer='mid')
    ground(A, GROUND)
    if ph < 2:
        n = min(3, int(ph / 0.65) + 1)
        bei(A, lerp(120, 480, ease_out(((ph % 0.65) / 0.65))), GROUND, 190, dir=1, ph=t * 3, arm=-8, old=0.3)
        lab, col = f'第{cn_num(n)}次登门', SHUJIN
    elif ph < 4:
        kongming(A, 660, GROUND, 190, dir=-1, kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 2)))
        bei(A, 420, GROUND, 180, dir=1, kneel=True, arm=60, old=0.3)
        A.d['wash'].rectangle((480, GROUND - 90, 600, GROUND - 60), fill=255)
        lab, col = '隆中对 · 跨有荆益 联吴抗曹', SHUJIN
    else:
        kongming(A, 640, GROUND, 190, dir=-1, arm=60)
        bei(A, 440, GROUND, 190, dir=1, arm=lerp(-8, 80, clamp((ph - 4) / 0.6)), old=0.3)
        lab, col = '孤之有孔明 犹鱼之有水也', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('隆中', 56), 860, 1020, t, t - u + 2 * P, rot=6)
    note_in(cv, '凡三往 乃见 时年四十七', t, t - u + P)

def art_e_adou(A, cv, t, u):
    ground(A, GROUND)
    person(A, 520, GROUND, 190, dir=1, robe=True, hat='knot', female=True, arm=100, layer='mid')
    bei(A, 760, GROUND, 200, dir=-1, arm=lerp(-8, 60, ease_out(u / 0.6)), old=0.3)
    A.flush(cv)
    paste(cv, text_img('甘夫人生刘禅 · 小名阿斗', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_e_changban(A, cv, t, u):
    """6-beat set piece: 长坂 — 刘琮 surrenders to 曹操; 刘备 will not abandon the people: over a hundred thousand follow, ten li a day;
    曹操's riders catch them at 长坂."""
    ph = u / P
    ground(A, GROUND)
    if ph < 3:
        for j in range(14):
            person(A, lerp(-100, 1100, ((t * 0.02 + j / 14) % 1)), GROUND - 6 * (j % 3), 90 + 10 * (j % 2), dir=1, robe=False, hat='knot', load=j % 2 == 0, ph=t * 2 + j, arm=160 if j % 2 == 0 else -8, layer='mid' if j % 3 else 'ink')
        bei(A, 540, GROUND, 180, dir=1, ph=t * 2, arm=-8, old=0.3)
        lab, col = ('刘琮降曹 · 刘备南撤' if ph < 1.2 else '携民十余万 日行十余里'), SHUJIN
    else:
        for j in range(5):
            rider(A, lerp(-100, 500, clamp((ph - 3) / 2)) - j * 120, GROUND, 110, dir=1, ph=t * 7 + j, layer='ink', spear=True)
        person(A, 820, GROUND, 190, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='sangye')
        A.d['wash'].ellipse((790, GROUND - 130, 820, GROUND - 100), fill=255)
        lab, col = '曹军追及长坂 · 赵云护阿斗 张飞据水断桥', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 42 if ph >= 3 else 46, col, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    note_in(cv, '今人归吾 吾何忍弃去 摔阿斗出自演义', t, t - u + P)

def art_e_chibi(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    waves(A, 1190, t, rows=2, amp=4)
    for k in range(4):
        wu_ship(A, 200 + k * 220, 1200, 60, t, fire=clamp(u / (2 * P)) if k % 2 else 0.0)
    A.flush(cv)
    paste(cv, text_img('孙刘联军 · 破曹于赤壁', SERIF, 48, SHUJIN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('赤壁', 56), 860, 1020, t, t - u + P, rot=6)

def art_e_jingzhou(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='shujin')
    ground(A, GROUND)
    person(A, 660, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, sword=60, arm=60, layer='mid')
    bei(A, 420, GROUND, 200, dir=1, arm=-8, old=0.3)
    A.flush(cv)
    paste(cv, text_img('领荆州牧 · 娶孙权之妹', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '孙夫人侍婢百余人 皆亲执刀侍立', t, t - u + P)

def art_e_rushu(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 40, GROUND - 440), (x + 40, GROUND - 440), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    army(A, lerp(-300, 500, ease_out(u / (5 * P))), GROUND, 6, dir=1, layer='shujin', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('应刘璋之邀 · 率军入蜀', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '入蜀三年 终与刘璋反目', t, t - u + 2 * P)

# ================================================================ 第四回 三分
def art_e_chengdu(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='成都', layer='mid', open_=clamp((u - P) / P))
    ground(A, GROUND)
    bei(A, 540, GROUND, 200, dir=1, arm=-8, old=0.4)
    A.flush(cv)
    paste(cv, text_img('围成都 刘璋出降 · 领益州牧', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('益州', 56), 860, 1020, t, t - u + P, rot=6)

def art_e_dingjun(A, cv, t, u):
    """6-beat set piece: 定军山 — 刘备 contests 汉中 with 曹操; 黄忠 charges down 定军山 and kills 夏侯渊; 曹操 withdraws: 鸡肋."""
    ph = u / P
    A.d['mid'].polygon([(80, GROUND), (360, 900), (640, GROUND)], fill=180)
    ground(A, GROUND)
    if ph < 2:
        army(A, 560, GROUND, 4, dir=-1, layer='ink', t=t, march=False, h=100)
        bei(A, 200, GROUND, 190, dir=1, armour=True, arm=60, old=0.5)
        lab, col = '与曹操争夺汉中', SHUJIN
    elif ph < 4:
        q = clamp((ph - 2) / 1.5)
        rider(A, lerp(360, 700, q), lerp(900, GROUND, q), 130, dir=1, ph=t * 8, layer='shujin', spear=True)
        person(A, 820, GROUND, 170, dir=-1, robe=False, hat='helmet', fall=lerp(0, 80, clamp((ph - 3.2) / 0.5)), arm=-8, layer='ink')
        lab, col = '黄忠居高临下 斩夏侯渊', ZHU
    else:
        caocao(A, 700, GROUND, 190, dir=1, ph=t * 3, arm=-8)
        lab, col = '曹操叹曰 鸡肋 · 引军退走', SHUJIN
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('定军山', 50), 860, 1020, t, t - u + 2 * P, rot=6)

def art_e_wang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='shujin')
    ground(A, GROUND)
    bei(A, 540, GROUND, 210, dir=1, crown=True, arm=lerp(-8, 60, ease_out(u / 0.5)), old=0.5)
    A.flush(cv)
    paste(cv, text_img('进位汉中王 · 时年五十九', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('汉中王', 50), 860, 1020, t, t - u + P, rot=6)

def art_e_guanyu(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    guan(A, 540, GROUND, 220, dir=1, fall=lerp(0, 80, clamp((u - P) / P)), arm=-8, glaive=False)
    A.flush(cv)
    paste(cv, text_img('吕蒙白衣渡江 · 关羽败亡 荆州尽失', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_e_emperor(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qiuhuang')
    ground(A, GROUND)
    bei(A, 540, GROUND, 210, dir=1, crown=True, arm=lerp(-8, 60, ease_out(u / 0.5)), old=0.6)
    A.flush(cv)
    paste(cv, text_img('于成都称帝 · 国号汉 史称蜀汉', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('章武', 56), 860, 1020, t, t - u + P, rot=6)

def art_e_zhangfei(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    tent(A, 540, GROUND, 360, 260, layer='mid', open_=1.0)
    zhangfei(A, 540, GROUND, 200, dir=1, fall=-88, arm=-8)
    A.flush(cv)
    paste(cv, text_img('张飞为部将张达 范强所杀', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_e_east(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for j in range(4):
        person(A, 120 + j * 90, GROUND, 150, dir=1, robe=True, hat='knot', kneel=True, bow=30, arm=90, layer='ink')
    bei(A, 740, GROUND, 210, dir=-1, armour=True, arm=lerp(-8, 120, ease_out(u / 0.6)), old=0.6)
    A.flush(cv)
    paste(cv, text_img('不听劝阻 · 亲率大军东征孙吴', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '赵云等力谏 国贼是曹操 非孙权也', t, t - u + P)

# ================================================================ 第五回 白帝
def art_e_yiling(A, cv, t, u):
    """6-beat set piece: 夷陵 — camps strung for seven hundred li along the 长江 gorges; 陆逊 waits half a year, then attacks with fire;
    camp after camp burns; 刘备 flees to 白帝城."""
    ph = u / P
    ground(A, GROUND)
    burn = clamp((ph - 2) / 2.5)
    fire_camps(A, 7, t, burn=burn)
    if ph >= 4.5:
        bei(A, lerp(540, 1100, clamp((ph - 4.5) / 1.5)), GROUND, 170, dir=1, ph=t * 5, arm=-8, old=0.7)
    A.flush(cv)
    lab = '连营七百里' if ph < 2 else ('陆逊火攻 · 连破四十余营' if ph < 4.5 else '大败 退守白帝城')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('夷陵', 56), 860, 1020, t, t - u + 2 * P, rot=6)

def art_e_tuogu(A, cv, t, u):
    """6-beat set piece: 白帝托孤 — dying at 永安, he calls 诸葛亮: your talent is ten times 曹丕's; if my son can be helped, help him;
    if not, you may take it yourself."""
    ph = u / P
    ground(A, GROUND)
    A.d['mid'].rectangle((200, GROUND - 90, 600, GROUND - 60), fill=230)
    bei(A, 360, GROUND - 90, 200, dir=1, kneel=True, bow=10, arm=lerp(-8, 90, clamp((ph - 0.5) / 0.6)), old=1.0)
    kongming(A, 720, GROUND, 190, dir=-1, kneel=True, bow=lerp(10, 40, clamp((ph - 4) / 0.6)), fan=False, arm=60)
    lamp(A, 880, GROUND, 50, t, glow=0.7)
    A.flush(cv)
    if ph < 2:
        lab, col = '君才十倍曹丕 必能安国', SHUJIN
    elif ph < 4:
        lab, col = '若嗣子可辅 辅之 如其不才 君可自取', ZHU
    else:
        lab, col = '臣敢竭股肱之力 效忠贞之节 继之以死', SHUJIN
    paste(cv, text_img(lab, SERIF, 42, col, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    stamp(cv, seal('永安', 56), 860, 1020, t, t - u + P, rot=6)

def art_e_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    bei(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于永安宫 · 年六十三', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_e_yizhao(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 560, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('勿以恶小而为之\n勿以善小而不为', SERIF, 48, INK, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('遗诏敕后主', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_e_verdict(A, cv, t, u):
    ground(A, GROUND)
    bei(A, 540, GROUND, 240, dir=1, arm=-8, old=0.4)
    A.flush(cv)
    paste(cv, text_img('弘毅宽厚 知人待士', SERIF, 48, SHUJIN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '陈寿评曰 盖有高祖之风 英雄之器焉', t, t - u + P)

def art_e_huiling(A, cv, t, u):
    mulberry(A, 280, GROUND, 360, leaves=0.8)
    A.d['mid'].chord((420, GROUND - 160, 660, GROUND + 160), 180, 360, fill=230)
    A.d['ink'].rectangle((520, GROUND - 200, 560, GROUND - 60), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('惠陵 · 今在成都武侯祠内', SERIF, 46, SHUJIN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '君臣合祀 世所罕见', t, t - u + P)

def art_e_legacy(A, cv, t, u):
    mulberry(A, 860, 1440, 140)

def art_e_title(A, cv, t, u):
    mulberry(A, 820, 1440, 300)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    bei(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '桑树'), 48: ('第二回', '颠沛'), 80: ('第三回', '三顾'),
            112: ('第四回', '三分'), 144: ('第五回', '白帝')}

CARDS = [
    C(0, 2, 'life', 'num', num='织席贩履', line='最后当了皇帝', art=art_e_hook_sandal),
    C(2, 4, 'works', 'num', num='四十七岁', line='才遇到诸葛亮', art=art_e_hook_hut),
    C(4, 6, 'war', 'num', num='一场大火', line='烧光半生心血', art=art_e_hook_fire),
    C(6, 8, 'death', 'num', num='一道遗诏', line='劝人勿以恶小而为之', art=art_e_hook_scroll),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 桑树
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=161, main='生于涿县', sub='汉室宗亲', art=art_e_birth),
    C(22, 26, 'works', 'card', year=167, main='织席贩履', sub='少孤家贫', note='年份约略', art=art_e_weave),
    C(26, 30, 'night', 'card', year=168, main='桑树如盖', sub='童言无忌', art=art_e_tree),
    C(30, 34, 'court', 'card', year=175, main='从学卢植', sub='十五岁', art=art_e_luzhi),
    C(34, 38, 'life', 'card', year=176, main='好交豪侠', sub='不乐读书', art=art_e_youth),
    C(38, 42, 'war', 'card', year=184, main='起兵', sub='关张相随', art=art_e_rise),
    C(42, 46, 'fate', 'card', year=185, main='鞭打督邮', sub='弃官而去', art=art_e_duyou),
    C(46, 48, 'empire', 'card', year=194, main='领徐州', sub='陶谦相托', art=art_e_xuzhou),
    # ---- 第二回 颠沛
    C(48, 50, 'fate', 'chapter'),
    C(50, 54, 'fate', 'card', year=196, main='失徐州', sub='吕布袭取', art=art_e_lose),
    C(54, 58, 'court', 'card', year=198, main='投曹操', sub='豫州牧', art=art_e_tocao),
    C(58, 66, 'night', 'zhujiu', year=199),
    C(66, 70, 'night', 'card', year=199, main='衣带诏', sub='董承', art=art_e_yidai),
    C(70, 74, 'war', 'card', year=200, main='兵败投袁', sub='关羽被擒', art=art_e_yuanshao),
    C(74, 78, 'life', 'card', year=201, main='依刘表', sub='屯新野', art=art_e_xinye),
    C(78, 80, 'fate', 'card', year=205, main='髀肉复生', sub='老将至矣', note='年份约略', art=art_e_birou),
    # ---- 第三回 三顾
    C(80, 82, 'works', 'chapter'),
    C(82, 88, 'empire', 'card', year=207, main='三顾茅庐', sub='鱼之有水', art=art_e_sangu),
    C(88, 92, 'life', 'card', year=207, main='得子阿斗', sub='刘禅', art=art_e_adou),
    C(92, 98, 'death', 'card', year=208, main='长坂', sub='携民渡江', art=art_e_changban),
    C(98, 102, 'war', 'card', year=208, main='赤壁', sub='孙刘联盟', art=art_e_chibi),
    C(102, 106, 'court', 'card', year=209, main='领荆州', sub='孙夫人', art=art_e_jingzhou),
    C(106, 112, 'works', 'card', year=211, main='入蜀', sub='刘璋相邀', art=art_e_rushu),
    # ---- 第四回 三分
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'empire', 'card', year=214, main='取成都', sub='益州牧', art=art_e_chengdu),
    C(118, 124, 'war', 'card', year=219, main='定军山', sub='争夺汉中', art=art_e_dingjun),
    C(124, 128, 'court', 'card', year=219, main='汉中王', sub='五十九岁', art=art_e_wang),
    C(128, 132, 'death', 'card', year=219, main='关羽之死', sub='荆州尽失', art=art_e_guanyu),
    C(132, 136, 'empire', 'card', year=221, main='称帝', sub='蜀汉', art=art_e_emperor),
    C(136, 140, 'death', 'card', year=221, main='张飞遇害', sub='部将所杀', art=art_e_zhangfei),
    C(140, 144, 'war', 'card', year=221, main='东征', sub='为关羽复仇', art=art_e_east),
    # ---- 第五回 白帝
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'war', 'card', year=222, main='夷陵之战', sub='火烧连营', art=art_e_yiling),
    C(152, 158, 'death', 'card', year=223, main='白帝托孤', sub='君可自取', art=art_e_tuogu),
    C(158, 162, 'death', 'card', year=223, main='刘备去世', sub='年六十三', art=art_e_death),
    C(162, 166, 'works', 'card', year=223, main='遗诏', sub='勿以恶小', art=art_e_yizhao),
    C(166, 168, 'court', 'card', year=223, main='弘毅宽厚', sub='陈寿之评', art=art_e_verdict),
    C(168, 170, 'end', 'card', year=223, main='惠陵', sub='成都', art=art_e_huiling),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='柒拾柒', col=SHUJIN, acc=SANGYE, born=161, died=223, age0=160,
    born_lab='161年', died_lab='223年', years_txt='公元161 — 223',
    hook_q='他屡战屡败半辈子 · 凭什么三分天下？',
    name_line='刘备 · 字玄德', name='刘备', seal='玄德', title_art=art_e_title,
    q1='仁德之君？', q2='乱世枭雄？',
    end_art=art_e_legacy, end_big='惟贤惟德', end_seal='玄德',
    end_l1='他输了大半辈子', end_l2='却从没丢下跟着他的人',
    end_brush='弘毅宽厚', end_ask='刘备的仁义 是真心还是手段？评论区聊聊', next='周瑜'),
    scenes=dict(chapter=scene_chapter, zhujiu=scene_zhujiu))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
