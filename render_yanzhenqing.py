"""千古人物志 · 第壹佰集 · 颜真卿 (709–784)
Look: 赭墨 + 松青, little seal-paste corners, the city walls of 平原 behind.
Chapter card: 神道碑 — a stele whose grid of characters (颜勤礼碑 title) fills in a little more each chapter.
Set pieces: custom 8-beat scene 'jizhi' (祭侄文稿), 6-beat 平原备城, 6-beat 常山, 6-beat 蔡州.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_shangguanwaner as Sg   # engine + helpers (previous episode)
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
from render_simayi import emperor
from render_sunwu import army, banner
from render_zhuxi import book
from render_quyuan import river

F.RIPPLE = False
ZHEMO = (128, 74, 52)               # 赭墨
SONGQING = (70, 104, 92)            # 松青
S.LAYERS.append(('zhemo', ZHEMO, 0.9, 1.0))
S.LAYERS.append(('songqing', SONGQING, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='颜', life='颜', court='唐', night='祭', war='战', empire='忠', works='书', fate='谪', death='烈', end='颜')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = ((200, 170, 100), 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (SONGQING, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (ZHEMO, 170, (W * 0.5, 720))
G.THEMES['night']['sun'] = None
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _x in (60, 900):                # crenellated wall stubs at the margins
    _d.rectangle((_x, 1350, _x + 120, 1420), fill=(120, 108, 98, 60))
    for _k in range(4):
        _d.rectangle((_x + _k * 32, 1334, _x + _k * 32 + 18, 1350), fill=(120, 108, 98, 60))
for _k in range(3):
    _d.line((200, 1424 + _k * 12, 880, 1424 + _k * 12), fill=ZHEMO + (40 - _k * 10,), width=2)
MTN_COL = {'night': (30, 28, 30), 'death': (60, 58, 58), 'war': (112, 66, 52), 'fate': (96, 92, 90)}
def draw_background(t, theme):
    """河北: broad hills, city-wall stubs at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(198, 194, 188), (166, 160, 150), MTN_COL.get(theme, (116, 110, 100))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.72))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """印泥: a small square seal-paste box in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=ZHEMO + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=ZHEMO + (220,), width=3)
        cx, cy = x + sx * 50, y + sy * 50
        d.rectangle((cx - 20, cy - 20, cx + 20, cy + 20), fill=(180, 40, 36, 230))
        d.rectangle((cx - 12, cy - 12, cx + 12, cy + 12), outline=(240, 220, 200, 230), width=2)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def yan_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """颜真卿: a broad-shouldered Tang official — black 幞头 with two tails, an ochre robe, a full beard (white with age)."""
    b = bow + 6 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    if kw.get('fall'):
        return hand
    if up:
        A.d[layer].chord((x - 0.08 * h, y - 1.08 * h, x + 0.08 * h, y - 0.92 * h), 180, 360, fill=255)
        A.d[layer].line((x - dir * 0.06 * h, y - 0.98 * h, x - dir * 0.18 * h, y - 0.86 * h), fill=255, width=max(2, int(0.014 * h)))
        A.d['wash' if old > 0.5 else layer].polygon([(x, y - 0.86 * h), (x + dir * 0.09 * h, y - 0.86 * h), (x + dir * 0.05 * h, y - 0.6 * h), (x - dir * 0.01 * h, y - 0.64 * h)], fill=255)
    top = y - (0.48 if kneel else 0.76) * h
    A.d['zhemo'].polygon([(x - 0.12 * h, top), (x + 0.12 * h, top), (x + 0.15 * h, y - 0.05 * h), (x - 0.15 * h, y - 0.05 * h)], fill=170)
    return hand

def rebel(A, x, y, h, dir=-1, layer='mid', **kw):
    hand = person(A, x, y, h, dir=dir, robe=False, hat='helmet', layer=layer, **kw)
    return hand

STELE = '唐故秘书省著作郎夔州都督府长史上护军颜君神道碑'
def stele_grid(A, cv, cx, base, w, h, n, t=0.0):
    """神道碑: a stele with a carved head; `n` characters filled into its grid (4 columns, right to left)."""
    A.d['mid'].rectangle((cx - w, base - h, cx + w, base), fill=230)
    A.d['ink'].rectangle((cx - w, base - h, cx + w, base), outline=255, width=5)
    A.d['mid'].chord((cx - 1.1 * w, base - h - 0.5 * w, cx + 1.1 * w, base - h + 0.5 * w), 180, 360, fill=230)
    A.d['ink'].rectangle((cx - 1.2 * w, base, cx + 1.2 * w, base + 20), fill=255)
    A.flush(cv)
    cols, rows = 4, 6
    cw = 2 * w / (cols + 0.4); ch = (h - 40) / rows
    for i in range(min(n, cols * rows)):
        c, r = i // rows, i % rows
        x = cx + w - 0.7 * cw - c * cw; y = base - h + 20 + (r + 0.5) * ch
        paste(cv, text_img(STELE[i % len(STELE)], SERIF, int(min(cw, ch) * 0.72), INK, 'Black', bleed=False), x, y, 1, 1)

def handscroll(A, cx, cy, w, h, p):
    A.d['wash'].rectangle((cx - w * p, cy - h, cx + w * p, cy + h), fill=255)
    A.d['ink'].rectangle((cx - w * p, cy - h, cx + w * p, cy + h), outline=180, width=3)
    for sx in (-1, 1):
        A.d['zhemo'].rectangle((cx + sx * w * p - 10, cy - h - 16, cx + sx * w * p + 10, cy + h + 16), fill=255)

# ================================================================ chapter card
CH = {16: (0, 4), 48: (4, 10), 80: (10, 16), 112: (16, 22), 144: (22, 24)}
def art_stele_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (4, 10))
    q = ease_out(u / (1.4 * P))
    stele_grid(A, cv, 540, 1250, 200, 420, int(lerp(a, b, clamp((q - 0.2) / 0.6))), t=t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_stele_chapter)
    ink_in(cv, text_img(no, SERIF, 56, ZHEMO, 'Black', bleed=False, spacing=12), W / 2, 1330, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1450, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_y_hook_scroll(A, cv, t, u):
    handscroll(A, 540, 1080, 400, 160, ease_out(u / (1.2 * P)))
    A.flush(cv)
    paste(cv, text_img('呜呼哀哉', SERIF, 60, INK, 'Black', bleed=False, spacing=10), W / 2, 1080, 1, clamp((u - P) / 0.4))

def art_y_hook_old(A, cv, t, u):
    ground(A, GROUND)
    yan_(A, lerp(200, 520, ease_out(u / (2 * P))), GROUND, 230, dir=1, ph=t * 2, old=0.9, arm=-8)
    for k in range(4):
        rebel(A, 700 + k * 80, GROUND, 170, dir=-1, spear=True, arm=40)

def art_y_hook_copy(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    person(A, 320, GROUND, 140, dir=1, robe=False, hat='none', kneel=True, arm=100, layer='ink')
    A.flush(cv)
    paste(cv, text_img('颜', BRUSH, 220, INK, bleed=False), 640, 1080, 1, clamp(u / P))

def art_y_hook_wall(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].rectangle((x - 70, GROUND - (60 if k != 2 else 260), x + 70, GROUND), fill=200)
    ground(A, GROUND)
    if True:
        banner(A, 540, GROUND - 260, 160, t, layer='red')

# ================================================================ 第一回 家学
def art_y_birth(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('生于长安 出身琅琊颜氏', SERIF, 50, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '颜之推五世孙 世代以儒学书法传家', t, t - u + P)

def art_y_father(A, cv, t, u):
    ground(A, GROUND)
    person(A, 680, GROUND, 190, dir=-1, female=True, arm=60, layer='mid')
    person(A, 480, GROUND, 90, dir=1, robe=True, hat='none', arm=60, layer='ink')
    A.flush(cv)
    paste(cv, text_img('三岁丧父 母亲殷氏亲自教养', SERIF, 48, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_y_mud(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((360, GROUND - 40, 720, GROUND - 8), fill=200)
    yan_(A, 300, GROUND, 140, dir=1, kneel=True, arm=100)
    A.d['songqing'].ellipse((480 - 40, GROUND - 40, 480 + 40, GROUND - 10), fill=255)
    A.flush(cv)
    paste(cv, text_img('家贫无纸笔 以黄土扫墙练字', SERIF, 48, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '后人记载 或有渲染', t, t - u + P)

def art_y_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    yan_(A, 540, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('二十六岁 进士及第', SERIF, 52, ZHEMO, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_y_zhang(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
    yan_(A, 380, GROUND, 190, dir=1, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('向草圣张旭请教笔法', SERIF, 50, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '自称得其笔法 年份约略', t, t - u + P)

def art_y_duobao(A, cv, t, u):
    ground(A, GROUND)
    for k in range(7):
        w = 120 - k * 12
        A.d['mid'].rectangle((540 - w, GROUND - 60 - k * 70, 540 + w, GROUND - k * 70), fill=220)
        A.d['ink'].polygon([(540 - w - 20, GROUND - 60 - k * 70), (540 + w + 20, GROUND - 60 - k * 70), (540 + w, GROUND - 74 - k * 70), (540 - w, GROUND - 74 - k * 70)], fill=255)
    A.flush(cv)
    paste(cv, text_img('四十四岁 书多宝塔碑', SERIF, 50, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '早期楷书代表作', t, t - u + P)

# ================================================================ 第二回 平原
def art_y_pingyuan(A, cv, t, u):
    """6-beat set piece: 平原备城 — sent out by 杨国忠, he sees 安禄山 coming; he deepens the moat and stocks grain, and to hide it parties on boats with guests."""
    ph = u / P
    city_wall(A, 160, 920, 1080, gate_x=540, label='平原', layer='mid', open_=1.0)
    ground(A, GROUND)
    if ph < 2:
        yan_(A, lerp(-80, 540, clamp(ph / 2)), GROUND, 190, dir=1, ph=t * 2, arm=-8)
        lab = '被杨国忠排挤 出任平原太守'
    elif ph < 4:
        for k in range(5):
            person(A, 200 + k * 150, GROUND, 140, dir=1, robe=False, hat='knot', bow=50, arm=150, layer='ink')
        lab = '暗中加高城墙 疏浚壕沟 储备粮草'
    else:
        A.d['ocean'].rectangle((160, GROUND - 30, 920, GROUND + 20), fill=170)
        boat(A, 540, GROUND - 20, 110, t)
        lab = '表面上却天天与文士泛舟饮酒'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHEMO, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '以掩人耳目 安禄山果然不加防备', t, t - u + 4 * P)

def art_y_rebellion(A, cv, t, u):
    ground(A, GROUND)
    army(A, lerp(-300, 300, ease_out(u / (3 * P))), GROUND, 9, dir=1, t=t, march=True, h=110)
    flames(A, 800, GROUND, 300, 160, t, n=3, seed=755, smoke=True)
    A.flush(cv)
    paste(cv, text_img('安史之乱爆发 河北诸郡望风而降', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_y_alone(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].rectangle((x - 70, GROUND - (60 if k != 2 else 260), x + 70, GROUND), fill=200)
    ground(A, GROUND)
    banner(A, 540, GROUND - 260, 160, t, layer='red')
    A.flush(cv)
    paste(cv, text_img('二十四郡 唯平原城守具备', SERIF, 48, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '玄宗叹 朕不识颜真卿 所为得如此', t, t - u + P)

def art_y_changshan(A, cv, t, u):
    """6-beat set piece: 常山 — his cousin 颜杲卿 holds 常山 against the rebels; the city falls; father and son are killed; 杲卿 curses 安禄山 to the end."""
    ph = u / P
    city_wall(A, 160, 920, 1080, gate_x=540, label='常山', layer='mid', open_=1.0 if ph > 2 else 0.0)
    ground(A, GROUND)
    if ph < 2:
        person(A, 540, 1080, 120, dir=1, robe=False, hat='helmet', arm=140, layer='ink')
        lab, col = '堂兄颜杲卿起兵 死守常山', ZHEMO
    elif ph < 4:
        army(A, 160, GROUND, 8, dir=1, t=t, march=True, h=100)
        flames(A, 540, 1080, 600, 160, t, n=5, seed=756, smoke=True)
        lab, col = '援兵不至 城破被俘', ZHU
    else:
        person(A, 540, GROUND, 200, dir=1, robe=True, hat='knot', kneel=True, arm=120, layer='ink')
        lab, col = '骂贼不绝口 父子同死', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '侄子颜季明亦遇害', t, t - u + 2 * P)

def art_y_flee(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 220), (x + 240, GROUND)], fill=140)
    ground(A, GROUND)
    yan_(A, lerp(900, 300, ease_out(u / (3 * P))), GROUND, 190, dir=-1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('孤城难守 弃郡渡河 投奔肃宗', SERIF, 46, ZHEMO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 祭侄
def art_y_head(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((440, GROUND - 120, 640, GROUND), fill=255)
    A.d['ink'].rectangle((420, GROUND - 130, 660, GROUND - 116), fill=255)
    yan_(A, 300, GROUND, 190, dir=1, kneel=True, bow=30, arm=-8, old=0.3)
    A.flush(cv)
    paste(cv, text_img('派人寻找亲人遗骸 只寻回侄子的头颅', SERIF, 44, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

JIZHI = ['维乾元元年', '岁次戊戌', '惟尔挺生', '夙标幼德', '父陷子死', '巢倾卵覆', '天不悔祸', '谁为荼毒', '呜呼哀哉']
def scene_jizhi(cv, t, c, k):
    """8-beat custom scene: 祭侄文稿 — he writes the draft of the sacrificial address; the opening is calm, then the lines lean,
    words are struck out, the ink goes dry and the brush flies; the scroll ends with 呜呼哀哉."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    handscroll(A, 540, 1040, 470, 260, ease_out(clamp(ph / 0.8)))
    ground(A, GROUND)
    yan_(A, 160, GROUND, 160, dir=1, kneel=True, arm=lerp(90, 110, 0.5 + 0.5 * math.sin(t * (4 + ph))), old=0.3)
    A.flush(cv)
    n = min(len(JIZHI), int(max(0, ph - 0.8) / 0.75) + 1) if ph > 0.8 else 0
    rng = random.Random(100)
    for i in range(n):
        x = 940 - i * 100
        tilt = 0.0 if i < 4 else (i - 3) * 0.04
        dry = clamp((i - 3) / 5)
        col = tuple(int(lerp(c0, 120, dry * 0.5)) for c0 in INK)
        a = clamp((ph - 0.8 - i * 0.75) / 0.4)
        im = text_img('\n'.join(JIZHI[i]), BRUSH, 52, col, bleed=False, spacing=0)
        im = im.rotate(math.degrees(tilt) * (1 if i % 2 else -1), expand=True)
        paste(cv, im, x, 1040, 1, a)
        if i in (4, 6):
            fx_ = Art()
            fx_.d['ink'].line((x - 40, 940 + rng.randint(0, 60), x + 40, 1000 + rng.randint(0, 60)), fill=230, width=8)
            fx_.flush(cv)
    fx = Art()
    chars_in(cv, fx, '祭侄文稿', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=100)
    fx.flush(cv)
    if ph < 3:
        lab, col = '起笔尚平静', ZHEMO
    elif ph < 6:
        lab, col = '越写越急 涂改 枯笔 字字悲愤', ZHU
    else:
        lab, col = '天下第二行书', ZHU
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '全文二百三十余字 原作今藏台北故宫', t, s0 + 5 * P)

def art_y_why2(A, cv, t, u):
    A.flush(cv)
    paste(cv, text_img('兰亭序 第一', SERIF, 52, INK, 'Black', bleed=False, spacing=8), W / 2, 1000, 1, clamp(u / 0.4))
    paste(cv, text_img('祭侄文稿 第二', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 1110, 1, clamp((u - 0.5 * P) / 0.4))
    paste(cv, text_img('寒食帖 第三', SERIF, 52, INK, 'Black', bleed=False, spacing=8), W / 2, 1220, 1, clamp((u - P) / 0.4))
    paste(cv, text_img('天下三大行书', SERIF, 50, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_y_no_art(A, cv, t, u):
    ground(A, GROUND)
    handscroll(A, 540, 1100, 420, 200, 1.0)
    A.flush(cv)
    paste(cv, text_img('无意于书 却成千古绝唱', SERIF, 50, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '情动于中而形于言', t, t - u + P)

def art_y_court(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    yan_(A, 540, GROUND, 200, dir=1, arm=60, old=0.4)
    A.flush(cv)
    paste(cv, text_img('回朝任刑部尚书 直言敢谏', SERIF, 48, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '屡遭权臣排挤 几度外放', t, t - u + P)

def art_y_zuowei(A, cv, t, u):
    ground(A, GROUND)
    handscroll(A, 540, 1100, 400, 180, 1.0)
    A.flush(cv)
    paste(cv, text_img('争座位帖', SERIF, 60, INK, 'Black', bleed=False, spacing=10), W / 2, 1100, 1, clamp(u / 0.4))
    paste(cv, text_img('写信斥责权臣郭英乂乱了朝班座次', SERIF, 42, ZHEMO, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '也是行书名帖', t, t - u + P)

# ================================================================ 第四回 颜体
def art_y_magu(A, cv, t, u):
    ground(A, GROUND)
    stele_grid(A, cv, 540, GROUND, 180, 380, 12, t=t)
    paste(cv, text_img('六十三岁 书麻姑仙坛记', SERIF, 50, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_y_qinli(A, cv, t, u):
    ground(A, GROUND)
    stele_grid(A, cv, 540, GROUND, 200, 420, 24, t=t)
    paste(cv, text_img('七十一岁 书颜勤礼碑', SERIF, 52, ZHEMO, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '为曾祖立碑 颜体楷书的巅峰', t, t - u + P)

def art_y_style(A, cv, t, u):
    A.flush(cv)
    paste(cv, text_img('颜', SERIF, 300, INK, 'Black', bleed=False), W / 2, 1100, 1, clamp(u / 0.6))
    paste(cv, text_img('横轻竖重 方中带圆 雄浑宽博', SERIF, 46, ZHEMO, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '一改初唐瘦硬之风', t, t - u + P)

def art_y_jinliu(A, cv, t, u):
    A.flush(cv)
    paste(cv, text_img('颜筋柳骨', SERIF, 72, INK, 'Black', bleed=False, spacing=14), W / 2, 1100, 1, clamp(u / 0.4))
    paste(cv, text_img('与柳公权并称', SERIF, 50, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_y_sushi(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 220, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    paste(cv, text_img('诗至杜子美 文至韩退之 书至颜鲁公', SERIF, 42, ZHEMO, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '苏轼之评', t, t - u + P)

# ================================================================ 第五回 蔡州
def art_y_lixilie(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND, 200, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
    emperor(A, 380, GROUND, 200, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('李希烈叛乱 宰相卢杞荐他前去劝降', SERIF, 44, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '朝野皆知 此去凶多吉少', t, t - u + P)

def art_y_go(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 220), (x + 240, GROUND)], fill=140)
    ground(A, GROUND)
    yan_(A, lerp(200, 800, ease_out(u / (3 * P))), GROUND, 210, dir=1, ph=t * 2, old=0.9, arm=-8)
    A.flush(cv)
    paste(cv, text_img('七十五岁 慨然前往', SERIF, 52, ZHEMO, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_y_caizhou(A, cv, t, u):
    """6-beat set piece: 蔡州 — held by the rebels for over a year: they dig a pit to bury him alive, then pile firewood and threaten to burn him; he walks toward the fire."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        A.d['ink'].rectangle((360, GROUND - 6, 720, GROUND + 40), fill=255)
        for k in range(3):
            rebel(A, 760 + k * 80, GROUND, 170, dir=-1, spear=True, arm=40)
        yan_(A, 300, GROUND, 200, dir=1, old=0.9, arm=-8)
        lab, col = '叛军挖坑 要活埋他', ZHU
    elif ph < 4:
        for k in range(8):
            A.d['zhemo'].line((380 + k * 40, GROUND, 400 + k * 40, GROUND - 120), fill=255, width=10)
        flames(A, 540, GROUND, 360, 220 * clamp((ph - 2) / 0.6), t, n=5, seed=784, smoke=True)
        yan_(A, lerp(200, 330, clamp((ph - 2.5) / 1.2)), GROUND, 200, dir=1, ph=t * 2, old=0.9, arm=-8)
        lab, col = '架柴点火 他径直走向火堆', ZHU
    else:
        yan_(A, 540, GROUND, 200, dir=1, old=0.9, arm=-8)
        lab, col = '叛军拦下 终究不肯屈服', ZHEMO
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '被扣押一年有余', t, t - u + 2 * P)

def art_y_death(A, cv, t, u):
    palace(A, 540, 1300, 260, layer='mid')
    ground(A, GROUND)
    yan_(A, 540, GROUND, 210, dir=1, kneel=True, bow=10, old=0.9, arm=-8)
    A.flush(cv)
    paste(cv, text_img('在蔡州龙兴寺被缢杀', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '终年七十六岁', t, t - u + P)

def art_y_wenzhong(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((440, GROUND - 420, 640, GROUND), fill=230)
    A.d['ink'].rectangle((440, GROUND - 420, 640, GROUND), outline=255, width=5)
    A.flush(cv)
    paste(cv, text_img('谥\n文\n忠', SERIF, 60, INK, 'Black', bleed=False, spacing=8), W / 2, GROUND - 210, 1, clamp((u - 0.5 * P) / 0.4))
    paste(cv, text_img('德宗追赠司徒 封鲁郡公', SERIF, 48, ZHEMO, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '世称颜鲁公', t, t - u + P)

def art_y_copy(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='mid')
    for k in range(3):
        person(A, 300 + k * 240, GROUND, 130, dir=1, robe=False, hat='none', kneel=True, arm=100, layer='ink')
    A.flush(cv)
    paste(cv, text_img('一千二百多年后 孩子们还在临他的字', SERIF, 44, ZHEMO, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))

def art_y_end(A, cv, t, u):
    ground(A, GROUND)
    stele_grid(A, cv, 540, GROUND, 200, 420, 24, t=t)
    paste(cv, text_img('字如其人', SERIF, 60, ZHEMO, 'Black', bleed=False, spacing=12), W / 2, 760, 1, clamp(u / 0.4))

def art_y_legacy(A, cv, t, u):
    A.d['red'].rectangle((830, 1350, 890, 1410), fill=230)

def art_y_title(A, cv, t, u):
    handscroll(A, 790, 1120, 190, 110, 1.0)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    yan_(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '家学'), 48: ('第二回', '平原'), 80: ('第三回', '祭侄'),
            112: ('第四回', '颜体'), 144: ('第五回', '蔡州')}

CARDS = [
    C(0, 2, 'night', 'num', num='天下第二行书', line='是一篇哭侄子的祭文', art=art_y_hook_scroll),
    C(2, 4, 'death', 'num', num='七十五岁', line='他独自走进叛军营中', art=art_y_hook_old),
    C(4, 6, 'works', 'num', num='颜体', line='书法课本第一课', art=art_y_hook_copy),
    C(6, 8, 'war', 'num', num='二十四郡', line='只有他守住了城', art=art_y_hook_wall),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 家学
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=709, main='生于长安', sub='琅琊颜氏', art=art_y_birth),
    C(22, 26, 'fate', 'card', year=711, main='三岁丧父', sub='母亲教养', art=art_y_father),
    C(26, 30, 'works', 'card', year=720, main='黄土练字', sub='家贫', note='年份约略', art=art_y_mud),
    C(30, 34, 'court', 'card', year=734, main='进士', sub='二十六岁', art=art_y_jinshi),
    C(34, 40, 'night', 'card', year=745, main='请教张旭', sub='得其笔法', note='年份约略', art=art_y_zhang),
    C(40, 48, 'works', 'card', year=752, main='多宝塔碑', sub='四十四岁', art=art_y_duobao),
    # ---- 第二回 平原
    C(48, 50, 'war', 'chapter'),
    C(50, 56, 'court', 'card', year=753, main='平原太守', sub='暗中备战', art=art_y_pingyuan),
    C(56, 60, 'war', 'card', year=755, main='安史之乱', sub='河北沦陷', art=art_y_rebellion),
    C(60, 66, 'empire', 'card', year=755, main='孤城', sub='平原独存', art=art_y_alone),
    C(66, 72, 'death', 'card', year=756, main='常山', sub='颜杲卿', art=art_y_changshan),
    C(72, 80, 'fate', 'card', year=756, main='渡河', sub='投奔肃宗', art=art_y_flee),
    # ---- 第三回 祭侄
    C(80, 82, 'night', 'chapter'),
    C(82, 86, 'death', 'card', year=758, main='寻亲', sub='只余首级', art=art_y_head),
    C(86, 94, 'night', 'jizhi', year=758),
    C(94, 98, 'works', 'card', year=758, main='三大行书', sub='天下第二', art=art_y_why2),
    C(98, 104, 'life', 'card', year=758, main='无意于书', sub='千古绝唱', art=art_y_no_art),
    C(104, 108, 'court', 'card', year=760, main='刑部尚书', sub='屡遭排挤', note='年份约略', art=art_y_court),
    C(108, 112, 'fate', 'card', year=764, main='争座位帖', sub='斥责权臣', art=art_y_zuowei),
    # ---- 第四回 颜体
    C(112, 114, 'works', 'chapter'),
    C(114, 120, 'night', 'card', year=771, main='麻姑仙坛记', sub='六十三岁', art=art_y_magu),
    C(120, 126, 'works', 'card', year=779, main='颜勤礼碑', sub='七十一岁', art=art_y_qinli),
    C(126, 132, 'empire', 'card', year=779, main='颜体', sub='雄浑宽博', art=art_y_style),
    C(132, 136, 'life', 'card', year=779, main='颜筋柳骨', sub='并称', art=art_y_jinliu),
    C(136, 144, 'court', 'card', year=779, main='书至鲁公', sub='苏轼之评', art=art_y_sushi),
    # ---- 第五回 蔡州
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'war', 'card', year=783, main='李希烈叛', sub='奉命劝降', art=art_y_lixilie),
    C(150, 154, 'fate', 'card', year=783, main='慨然前往', sub='七十五岁', art=art_y_go),
    C(154, 160, 'death', 'card', year=784, main='蔡州', sub='威武不屈', art=art_y_caizhou),
    C(160, 163, 'death', 'card', year=784, main='颜真卿遇害', sub='七十六岁', art=art_y_death),
    C(163, 166, 'empire', 'card', year=785, main='谥文忠', sub='颜鲁公', art=art_y_wenzhong),
    C(166, 168, 'life', 'card', year=2000, main='临帖', sub='代代相传', art=art_y_copy),
    C(168, 170, 'end', 'card', year=2000, main='字如其人', sub='颜鲁公', art=art_y_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='壹佰', col=ZHEMO, acc=SONGQING, born=709, died=784, age0=708,
    born_lab='709年', died_lab='784年', years_txt='公元709 — 784',
    hook_q='书法写得最好的人 · 为什么死得最壮烈？',
    name_line='颜真卿 · 字清臣', name='颜真卿', seal='鲁公', title_art=art_y_title,
    q1='书法大家？', q2='忠烈之臣？',
    end_art=art_y_legacy, end_big='祭侄文稿', end_seal='清臣',
    end_l1='他的字端正雄浑', end_l2='他的人也站得笔直',
    end_brush='字如其人', end_ask='你练字临过颜体吗？评论区聊聊', next='黄巢'),
    scenes=dict(chapter=scene_chapter, jizhi=scene_jizhi))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
