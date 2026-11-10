"""千古人物志 · 第玖拾柒集 · 貂蝉 (文学形象，史无其人)
Look: 月华紫 + 貂红, little crescent-moon corners, Chang'an palace roofs behind.
Chapter card: 闭月 — a full moon that clouds cover a little more each chapter; in the last chapter it is hidden.
Set pieces: custom 8-beat scene 'lianhuan' (连环计, labelled 演义), 6-beat 史书一行, 6-beat 拜月, 6-beat 貂蝉冠.
She is a literary figure: no birth or death years (no_age); the years shown belong to the history around the story.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zhangzhongjing as Zj  # engine + helpers (previous episode)
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
from render_lvbu import lv
from render_zhuxi import book

F.RIPPLE = False
YUEHUA = (150, 138, 186)            # 月华紫
DIAOHONG = (186, 70, 84)            # 貂红
YUEHUA_D = (92, 74, 132)            # 月华紫 (text)
S.LAYERS.append(('yuehua', YUEHUA, 0.9, 1.0))
S.LAYERS.append(('diaohong', DIAOHONG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='月', life='貂', court='汉', night='月', war='乱', empire='戏', works='书', fate='计', death='散', end='月')
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
G.THEMES['empire']['sun'] = (DIAOHONG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (YUEHUA, 170, (W * 0.5, 720))
G.THEMES['night']['sun'] = (YUEHUA, 180, (W * 0.5, 760))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _x in (110, 970):               # palace eaves at the margins
    _d.polygon([(_x - 90, 1340), (_x + 90, 1340), (_x + 60, 1310), (_x - 60, 1310)], fill=(110, 104, 120, 70))
    _d.rectangle((_x - 50, 1340, _x + 50, 1420), fill=(120, 114, 128, 50))
for _k in range(3):
    _d.line((200, 1424 + _k * 12, 880, 1424 + _k * 12), fill=YUEHUA + (40 - _k * 10,), width=2)
MTN_COL = {'night': (30, 28, 44), 'death': (60, 58, 66), 'war': (110, 64, 60), 'fate': (96, 92, 106)}
def draw_background(t, theme):
    """长安: soft hills, palace eaves at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(198, 194, 202), (166, 160, 176), MTN_COL.get(theme, (112, 106, 128))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.72))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """新月: a crescent moon in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=YUEHUA + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=YUEHUA + (220,), width=3)
        cx, cy = x + sx * 52, y + sy * 52
        a0, a1 = (100, 260) if sx > 0 else (280, 80)
        d.arc((cx - 22, cy - 22, cx + 22, cy + 22), a0, a1, fill=(226, 196, 120, 235), width=9)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def diao(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, dance=0.0, t=0.0, **kw):
    """貂蝉: a young woman of the Han court — a high bun with a hairpin, a long red-violet robe, a flying sash."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', female=True, layer=layer, kneel=kneel, bow=bow, **kw)
    if kw.get('fall'):
        return hand
    top = y - (0.62 if kneel else 1.0) * h
    A.d[layer].ellipse((x - 0.06 * h, top - 0.12 * h, x + 0.06 * h, top + 0.02 * h), fill=255)
    A.d['yuehua'].line((x - 0.08 * h, top - 0.06 * h, x + 0.1 * h, top - 0.1 * h), fill=255, width=max(2, int(0.01 * h)))
    if not kneel:
        A.d['diaohong'].polygon([(x - 0.11 * h, y - 0.62 * h), (x + 0.11 * h, y - 0.62 * h), (x + 0.16 * h, y - 0.02 * h), (x - 0.16 * h, y - 0.02 * h)], fill=170)
    sw = dance
    pts = [(x - 0.14 * h + 0.5 * h * sw * math.sin(t * 3 + k * 0.6) * k / 6, y - 0.65 * h + k * 0.08 * h - 0.2 * h * sw * math.cos(t * 3 + k * 0.5) * k / 6) for k in range(7)]
    A.d['yuehua'].line(pts, fill=255, width=max(3, int(0.018 * h)))
    return hand

def dong(A, x, y, h, dir=-1, layer='mid', **kw):
    """董卓: a heavy, broad warlord-chancellor."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        A.d[layer].ellipse((x - 0.2 * h, y - 0.72 * h, x + 0.2 * h, y - 0.28 * h), fill=255)
    return hand

def wangyun(A, x, y, h, dir=1, layer='ink', **kw):
    return person(A, x, y, h, dir=dir, robe=True, hat='knot', layer=layer, **kw)

def moon(A, cx, cy, r, cover, t):
    """闭月: a full moon; a bank of cloud slides across it, covering fraction `cover`."""
    A.d['yuehua'].ellipse((cx - r * 1.25, cy - r * 1.25, cx + r * 1.25, cy + r * 1.25), fill=40)
    A.d['wash'].ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    A.d['qiuhuang'].ellipse((cx - r * 0.96, cy - r * 0.96, cx + r * 0.96, cy + r * 0.96), fill=120)
    if cover > 0:
        x1 = cx - r * 1.4 + 2.8 * r * cover
        for k in range(5):
            yy = cy - r + k * 0.5 * r
            A.d['mid'].ellipse((x1 - 2.2 * r + 30 * math.sin(t + k), yy - 0.35 * r, x1 + 30 * math.sin(t + k), yy + 0.35 * r), fill=235)

def chan_cap(A, cx, cy, s):
    """貂蝉冠: a Han official's cap with a sable tail and a gold cicada plaque."""
    A.d['ink'].polygon([(cx - s, cy + 0.4 * s), (cx + s, cy + 0.4 * s), (cx + 0.7 * s, cy - 0.5 * s), (cx - 0.7 * s, cy - 0.5 * s)], fill=255)
    A.d['ink'].rectangle((cx - 1.1 * s, cy + 0.4 * s, cx + 1.1 * s, cy + 0.55 * s), fill=255)
    A.d['qiuhuang'].ellipse((cx - 0.25 * s, cy - 0.2 * s, cx + 0.25 * s, cy + 0.2 * s), fill=255)
    A.d['ink'].line((cx, cy - 0.2 * s, cx, cy + 0.2 * s), fill=255, width=3)
    pts = [(cx + 0.6 * s + 0.12 * s * k, cy - 0.5 * s - 0.25 * s * k + 0.04 * s * k * k) for k in range(6)]
    A.d['yaolu'].line(pts, fill=255, width=max(6, int(0.18 * s)))

def pavilion(A, cx, base, w):
    A.d['ink'].polygon([(cx - w, base - 0.9 * w), (cx + w, base - 0.9 * w), (cx, base - 1.3 * w)], fill=255)
    for x in (cx - 0.8 * w, cx + 0.8 * w):
        A.d['ink'].rectangle((x - 8, base - 0.9 * w, x + 8, base), fill=255)
    A.d['mid'].rectangle((cx - w, base - 0.25 * w, cx + w, base - 0.2 * w), fill=255)

# ================================================================ chapter card
CH = {16: (0.0, 0.0), 48: (0.0, 0.25), 80: (0.25, 0.5), 112: (0.5, 0.75), 144: (0.75, 1.0)}
def art_moon_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (0.0, 0.25))
    q = ease_out(u / (1.4 * P))
    moon(A, 540, 1030, 200, lerp(a, b, q), t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_moon_chapter)
    ink_in(cv, text_img(no, SERIF, 56, YUEHUA_D, 'Black', bleed=False, spacing=12), W / 2, 1320, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1445, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_d_hook_none(A, cv, t, u):
    ground(A, GROUND)
    diao(A, 540, GROUND, 320, dir=1, arm=-8, layer='mid' if u > P else 'ink')

def art_d_hook_moon(A, cv, t, u):
    moon(A, 540, 1040, 200, clamp(u / (1.6 * P)), t)

def art_d_hook_two(A, cv, t, u):
    ground(A, GROUND)
    dong(A, 760, GROUND, 230, dir=-1, arm=-8)
    lv(A, 320, GROUND, 230, dir=1, arm=-8, ji=False)
    diao(A, 540, GROUND, 200, dir=1 if math.sin(t * 2) > 0 else -1, arm=-8)

def art_d_hook_cap(A, cv, t, u):
    chan_cap(A, 540, 1100, 160)

# ================================================================ 第一回 乱世
def art_d_dongzhuo(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='洛阳', layer='mid', open_=1.0)
    ground(A, GROUND)
    army(A, lerp(-200, 200, ease_out(u / (3 * P))), GROUND, 6, dir=1, t=t, march=True, h=110)
    A.flush(cv)
    paste(cv, text_img('董卓率西凉兵入洛阳', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '以下历史背景见三国志', t, t - u + P)

def art_d_feili(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    dong(A, 640, GROUND, 230, dir=-1, arm=80)
    person(A, 380, GROUND, 120, dir=1, robe=True, hat='crown', kneel=True, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('废少帝 立献帝 专擅朝政', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_d_burn(A, cv, t, u):
    palace(A, 540, 1300, 320, collapse=clamp(u / (3 * P)) * 0.6, layer='mid')
    flames(A, 540, 1220, 620, 240, t, n=6, seed=190, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('火烧洛阳 挟天子迁都长安', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_d_lvbu(A, cv, t, u):
    ground(A, GROUND)
    dong(A, 720, GROUND, 230, dir=-1, arm=60)
    lv(A, 360, GROUND, 240, dir=1, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('吕布认董卓为义父', SERIF, 50, YUEHUA_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '誓为父子 史有明载', t, t - u + P)

def art_d_ji(A, cv, t, u):
    ground(A, GROUND)
    dong(A, 720, GROUND, 230, dir=-1, arm=lerp(-8, 120, clamp((u - P) / 0.3)))
    lv(A, lerp(360, 260, clamp((u - P) / 0.5)), GROUND, 240, dir=1, arm=-8, ji=False)
    A.d['ink'].line((640, GROUND - 200, lerp(640, 300, clamp((u - P) / 0.4)), GROUND - 230), fill=255, width=8)
    A.flush(cv)
    paste(cv, text_img('董卓一怒 拔手戟掷向吕布', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '三国志 吕布传', t, t - u + P)

# ================================================================ 第二回 侍婢
def art_d_record(A, cv, t, u):
    """6-beat set piece: 史书一行 — the only historical kernel: one line in 三国志 about 吕布 and an unnamed maid of 董卓."""
    ph = u / P
    ground(A, GROUND)
    scroll(A, 540, 1100, 560, 320, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('布与卓侍婢私通\n恐事发觉 心不自安', SERIF, 46, INK, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp((ph - 0.8) / 0.4))
    if ph > 3:
        paste(cv, text_img('侍婢', SERIF, 60, ZHU, 'Black', bleed=False), 760, 1220, 1, clamp((ph - 3) / 0.4))
    lab = '三国志 吕布传 只有这一句' if ph < 3 else '没有名字 没有来历 没有结局'
    paste(cv, text_img(lab, SERIF, 48, YUEHUA_D if ph < 3 else ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '历史上并无貂蝉其人', t, t - u + 2 * P)

def art_d_wangyun(A, cv, t, u):
    ground(A, GROUND)
    wangyun(A, 540, GROUND, 220, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('司徒王允 暗中谋诛董卓', SERIF, 48, YUEHUA_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_d_kill(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    dong(A, 700, GROUND, 230, dir=-1, fall=-88 * clamp((u - P) / 0.5), arm=-8)
    lv(A, 380, GROUND, 240, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('王允说动吕布 刺杀董卓', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '吕布怕私通之事败露 这是动机之一', t, t - u + P)

def art_d_after(A, cv, t, u):
    ground(A, GROUND)
    lv(A, lerp(540, 980, ease_out(u / (3 * P))), GROUND, 220, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('此后吕布流离东奔', SERIF, 50, YUEHUA_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_d_baimen(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='白门', layer='mid')
    ground(A, GROUND)
    lv(A, 540, GROUND, 230, dir=1, bound=True, kneel=True, arm=-8)
    A.flush(cv)
    paste(cv, text_img('白门楼 吕布被曹操所杀', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '那位侍婢 史书再无一字', t, t - u + P)

# ================================================================ 第三回 连环计
def art_d_zaju(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((220, GROUND - 40, 860, GROUND), fill=255)
    for x in (240, 840):
        A.d['diaohong'].rectangle((x - 10, 900, x + 10, GROUND - 40), fill=255)
    A.d['diaohong'].rectangle((220, 880, 860, 920), fill=255)
    diao(A, 540, GROUND - 40, 200, dir=1, dance=0.6, t=t, arm=60)
    A.flush(cv)
    paste(cv, text_img('元代杂剧 第一次出现貂蝉之名', SERIF, 46, YUEHUA_D, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '锦云堂暗定连环计 等剧', t, t - u + P)

def art_d_yanyi(A, cv, t, u):
    ground(A, GROUND)
    book(A, 540, GROUND, 220, 300, layer='diaohong')
    A.flush(cv)
    paste(cv, text_img('三国演义把她写成了连环计主角', SERIF, 44, YUEHUA_D, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))

def scene_lianhuan(cv, t, c, k):
    """8-beat custom scene: 连环计 (三国演义) — 王允 promises her to 吕布, then gives her to 董卓; at 凤仪亭 吕布 finds her in tears;
    father and son fall out; 吕布 kills 董卓."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    if ph < 2:
        wangyun(A, 540, GROUND, 200, dir=1, arm=60)
        diao(A, 700, GROUND, 180, dir=-1, arm=-8)
        lv(A, 300, GROUND, 230, dir=1, arm=-8, ji=False) if ph < 1 else dong(A, 300, GROUND, 230, dir=1, arm=-8)
        lab = '王允先许吕布 又献董卓' if ph >= 1 else '王允将她许给吕布'
        col = YUEHUA_D
    elif ph < 5:
        pavilion(A, 600, GROUND, 230)
        diao(A, 600, GROUND, 180, dir=-1, bow=20, arm=-8)
        lv(A, 360, GROUND, 230, dir=1, arm=60, ji=False)
        if ph > 3.5:
            dong(A, 900, GROUND, 230, dir=-1, arm=120)
        lab, col = ('凤仪亭 她向吕布哭诉', YUEHUA_D) if ph < 3.5 else ('董卓撞见 父子反目', ZHU)
    else:
        palace(A, 540, 1300, 300, layer='mid')
        dong(A, 700, GROUND, 230, dir=-1, fall=-88 * clamp((ph - 5.5) / 0.5), arm=-8)
        lv(A, 380, GROUND, 240, dir=1, arm=60)
        lab, col = '吕布刺杀董卓 连环计成', ZHU
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '连环计', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=97)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '此段情节出自三国演义 非史实', t, s0 + 0.5 * P)

def art_d_baiyue(A, cv, t, u):
    """6-beat set piece: 拜月 — in the garden at night she prays to the moon; a cloud passes and the moon hides — 闭月."""
    ph = u / P
    moon(A, 720, 940, 120, clamp((ph - 2) / 2.5), t)
    ground(A, GROUND)
    A.d['ink'].rectangle((300, GROUND - 60, 400, GROUND), fill=255)
    diao(A, 480, GROUND, 190, dir=1, kneel=ph > 1, bow=20 if ph > 1 else 0, arm=60)
    A.flush(cv)
    lab, col = ('月下焚香拜月', YUEHUA_D) if ph < 3 else ('月亮羞得躲进云里', DIAOHONG)
    paste(cv, text_img(lab, SERIF, 50, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '闭月之说为后世民间传说', t, t - u + P)

def art_d_meiren(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    for i, (n, w) in enumerate([('西施', '沉鱼'), ('王昭君', '落雁'), ('貂蝉', '闭月'), ('杨贵妃', '羞花')]):
        a = clamp((u - i * 0.3 * P) / 0.3)
        paste(cv, text_img(f'{w}  {n}', SERIF, 52, DIAOHONG if n == '貂蝉' else INK, 'Black', bleed=False, spacing=8), W / 2, 980 + i * 100, 1, a)
    paste(cv, text_img('位列中国古代四大美女', SERIF, 48, YUEHUA_D, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '四人中只有她不见于正史', t, t - u + P)

def art_d_sanying(A, cv, t, u):
    ground(A, GROUND)
    lv(A, 540, GROUND, 260, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('人中吕布 马中赤兔', SERIF, 50, YUEHUA_D, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '吕布见第七十六集', t, t - u + P)

# ================================================================ 第四回 结局
def art_d_endings(A, cv, t, u):
    ground(A, GROUND)
    diao(A, 540, GROUND, 240, dir=1, arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('她的结局 演义里没有交代', SERIF, 48, YUEHUA_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_d_end1(A, cv, t, u):
    ground(A, GROUND)
    diao(A, 540, GROUND, 220, dir=1, kneel=True, bow=30, arm=-8)
    A.flush(cv)
    paste(cv, text_img('一说被关羽所斩', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '出自明清戏曲 关公月下斩貂蝉', t, t - u + P)

def art_d_end2(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 220), (x + 240, GROUND)], fill=140)
    ground(A, GROUND)
    diao(A, lerp(540, 960, ease_out(u / (3 * P))), GROUND, 200, dir=1, ph=t * 2, arm=-8)
    A.flush(cv)
    paste(cv, text_img('一说出家为尼 隐入山林', SERIF, 50, YUEHUA_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '均为民间传说', t, t - u + P)

def art_d_place(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        A.d['mid'].rectangle((200 + k * 260, GROUND - 160, 340 + k * 260, GROUND), fill=200)
    A.flush(cv)
    paste(cv, text_img('多地自称貂蝉故里', SERIF, 50, YUEHUA_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '山西 甘肃等地皆有传说', t, t - u + P)

def art_d_cap(A, cv, t, u):
    """6-beat set piece: 貂蝉冠 — the name itself: a Han cap ornament of sable tail and gold cicada worn by high officials."""
    ph = u / P
    chan_cap(A, 540, 1100, 180)
    A.flush(cv)
    lab, col = ('貂蝉 原是汉代官帽上的饰物', YUEHUA_D) if ph < 3 else ('貂尾 金蝉 侍中所戴', DIAOHONG)
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '一说侍婢因掌管此冠而得名 亦属推测', t, t - u + 3 * P)

# ================================================================ 第五回 闭月
def art_d_opera(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((220, GROUND - 40, 860, GROUND), fill=255)
    diao(A, 460, GROUND - 40, 200, dir=1, dance=0.8, t=t, arm=60)
    lv(A, 680, GROUND - 40, 220, dir=-1, arm=-8, ji=False)
    A.flush(cv)
    paste(cv, text_img('京剧 吕布与貂蝉 久演不衰', SERIF, 48, YUEHUA_D, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_d_screen(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((180, 940, 900, 1380), outline=255, width=14)
    diao(A, 540, 1340, 300, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('影视 游戏中的常客', SERIF, 50, YUEHUA_D, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_d_why(A, cv, t, u):
    ground(A, GROUND)
    diao(A, 540, GROUND, 260, dir=1, arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('乱世里 一个弱女子改变了天下', SERIF, 46, YUEHUA_D, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('人们愿意相信这样的故事', SERIF, 46, DIAOHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_d_end(A, cv, t, u):
    moon(A, 540, 1060, 200, 0.6 + 0.1 * math.sin(t), t)
    A.flush(cv)
    paste(cv, text_img('史书无名 月下有影', SERIF, 52, YUEHUA_D, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))

def art_d_legacy(A, cv, t, u):
    moon(A, 860, 1380, 50, 0.4, t)

def art_d_title(A, cv, t, u):
    moon(A, 820, 1150, 120, 0.3, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    diao(A, 380, 1460, 680, dir=1, dance=0.3, t=t, arm=lerp(-5, 40, ease_out(u / (2 * P))))

from render_sunwu import army

# ================================================================ script
CHAPTERS = {16: ('第一回', '乱世'), 48: ('第二回', '侍婢'), 80: ('第三回', '连环计'),
            112: ('第四回', '结局'), 144: ('第五回', '闭月')}

CARDS = [
    C(0, 2, 'night', 'num', num='四大美女', line='只有她史书无名', art=art_d_hook_none),
    C(2, 4, 'life', 'num', num='闭月', line='月亮见了都躲起来', art=art_d_hook_moon),
    C(4, 6, 'fate', 'num', num='连环计', line='父子为她反目', art=art_d_hook_two),
    C(6, 8, 'works', 'num', num='貂蝉二字', line='原是官帽上的饰物', art=art_d_hook_cap),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 乱世
    C(16, 18, 'war', 'chapter'),
    C(18, 22, 'war', 'card', year=189, main='董卓进京', sub='西凉兵', art=art_d_dongzhuo),
    C(22, 26, 'court', 'card', year=189, main='废立', sub='专擅朝政', art=art_d_feili),
    C(26, 32, 'death', 'card', year=190, main='火烧洛阳', sub='迁都长安', art=art_d_burn),
    C(32, 38, 'life', 'card', year=190, main='父子', sub='吕布与董卓', art=art_d_lvbu),
    C(38, 48, 'fate', 'card', year=191, main='掷戟', sub='嫌隙初生', note='年份约略', art=art_d_ji),
    # ---- 第二回 侍婢
    C(48, 50, 'night', 'chapter'),
    C(50, 58, 'works', 'card', year=191, main='史书一行', sub='侍婢', art=art_d_record),
    C(58, 62, 'court', 'card', year=192, main='王允', sub='密谋', art=art_d_wangyun),
    C(62, 68, 'death', 'card', year=192, main='诛董卓', sub='吕布动手', art=art_d_kill),
    C(68, 72, 'life', 'card', year=193, main='东奔', sub='吕布流离', art=art_d_after),
    C(72, 80, 'fate', 'card', year=198, main='白门楼', sub='吕布之死', art=art_d_baimen),
    # ---- 第三回 连环计
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'works', 'card', year=1300, main='元杂剧', sub='始有其名', note='年份约略', art=art_d_zaju),
    C(86, 90, 'court', 'card', year=1370, main='三国演义', sub='成为主角', note='年份约略', art=art_d_yanyi),
    C(90, 98, 'fate', 'lianhuan', year=1370),
    C(98, 104, 'night', 'card', year=1370, main='拜月', sub='闭月传说', art=art_d_baiyue),
    C(104, 108, 'empire', 'card', year=1370, main='四大美女', sub='闭月', art=art_d_meiren),
    C(108, 112, 'war', 'card', year=1370, main='人中吕布', sub='演义名句', art=art_d_sanying),
    # ---- 第四回 结局
    C(112, 114, 'death', 'chapter'),
    C(114, 118, 'night', 'card', year=1370, main='下落不明', sub='演义未写', art=art_d_endings),
    C(118, 124, 'death', 'card', year=1600, main='月下斩貂蝉', sub='戏曲', note='年份约略', art=art_d_end1),
    C(124, 130, 'life', 'card', year=1600, main='出家', sub='另一种结局', note='年份约略', art=art_d_end2),
    C(130, 136, 'court', 'card', year=1600, main='故里之争', sub='多地传说', art=art_d_place),
    C(136, 144, 'works', 'card', year=1600, main='貂蝉冠', sub='名字的来历', art=art_d_cap),
    # ---- 第五回 闭月
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'empire', 'card', year=1900, main='京剧', sub='久演不衰', note='年份约略', art=art_d_opera),
    C(152, 158, 'life', 'card', year=2000, main='荧屏', sub='影视游戏', art=art_d_screen),
    C(158, 164, 'night', 'card', year=2000, main='为何相信', sub='乱世传奇', art=art_d_why),
    C(164, 170, 'end', 'card', year=2000, main='月下有影', sub='史书无名', art=art_d_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='玖拾柒', col=YUEHUA_D, acc=DIAOHONG, born=185, died=2000, age0=184, no_age=True,
    born_lab='文学形象', died_lab='史无其人', years_txt='文学形象 · 史无其人',
    hook_q='史书里找不到她 · 她为什么能成为四大美女之一？',
    name_line='貂蝉 · 文学形象', name='貂蝉', seal='闭月', title_art=art_d_title,
    q1='巾帼英雄？', q2='虚构人物？',
    end_art=art_d_legacy, end_big='闭月', end_seal='貂蝉',
    end_l1='史书只记下一个无名侍婢', end_l2='后人替她写了一千年',
    end_brush='闭月之容', end_ask='你觉得历史上真有貂蝉吗？评论区聊聊', next='祖冲之'),
    scenes=dict(chapter=scene_chapter, lianhuan=scene_lianhuan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
