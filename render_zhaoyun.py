"""千古人物志 · 第柒拾玖集 · 赵云 (?–229)
Look: 常山青 + 龙胆金, 枪缨 corner borders (a spear point with a red tassel), 常山 hills and the 汉水 behind.
Chapter card: 阿斗 — the boy he twice saved: a swaddled baby, a child, a youth, a crowned emperor, while the spear stands beside him;
in the last chapter the spear is laid down.
Set pieces: custom 8-beat scene 'changban' (长坂救主), 6-beat 博望擒夏侯兰, 6-beat 拒婚, 6-beat 截江夺阿斗, 6-beat 空营计, 6-beat 箕谷.
Birth year unknown, so no ages are shown (no_age). Lines from 云别传 are labelled in the notes.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zhouyu as Zy          # engine + helpers (previous episode)
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
from render_liubei import bei
from render_zhuge import kongming
from render_guanyu import zhangfei

F.RIPPLE = False
CHANGSHAN = (66, 80, 112)           # 常山青
LONGDAN = (190, 146, 48)            # 龙胆金
S.LAYERS.append(('changshan', CHANGSHAN, 0.9, 1.0))
S.LAYERS.append(('longdan', LONGDAN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='赵', life='常', court='汉', night='胆', war='战', empire='龙', works='忠', fate='谨', death='长', end='胆')
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
G.THEMES['empire']['sun'] = (LONGDAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (LONGDAN, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # the 汉水
    _d.line([(40 + i * 30, 1456 + _k * 14 + 4 * math.sin(i * 0.45 + _k)) for i in range(35)], fill=CHANGSHAN + (48 - _k * 10,), width=3)
for _x in (110, 970):               # spear racks at the margins
    for _j in range(3):
        _d.line((_x - 20 + _j * 20, 1446, _x - 20 + _j * 20, 1300), fill=(110, 110, 120, 70), width=3)
        _d.polygon([(_x - 24 + _j * 20, 1300), (_x - 16 + _j * 20, 1300), (_x - 20 + _j * 20, 1280)], fill=(130, 130, 140, 80))
        _d.ellipse((_x - 26 + _j * 20, 1302, _x - 14 + _j * 20, 1316), fill=(180, 50, 40, 80))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (92, 96, 104)}
def draw_background(t, theme):
    """常山: rounded hills, the 汉水, spear racks at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 192, 198), (156, 162, 176), MTN_COL.get(theme, (100, 110, 132))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """枪缨: a spear point with a red tassel in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=CHANGSHAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=CHANGSHAN + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.line((cx - 26, cy + 26, cx + 14, cy - 14), fill=(90, 70, 50, 230), width=4)
        d.polygon([(cx + 10, cy - 18), (cx + 18, cy - 10), (cx + 32, cy - 32)], fill=(150, 160, 176, 240))
        d.ellipse((cx - 2, cy - 6, cx + 14, cy + 10), fill=(186, 50, 40, 230))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def spear(A, x, y, L_, ang, layer='fangtian'):
    tx, ty = x + L_ * math.sin(ang), y - L_ * math.cos(ang)
    A.d['ink'].line((x, y, tx, ty), fill=255, width=max(3, int(L_ * 0.016)))
    nx, ny = math.cos(ang), math.sin(ang)
    s = 0.09 * L_
    A.d[layer].polygon([(tx - nx * 0.3 * s, ty - ny * 0.3 * s), (tx + nx * 0.3 * s, ty + ny * 0.3 * s),
                        (tx + 1.2 * s * math.sin(ang), ty - 1.2 * s * math.cos(ang))], fill=255)
    A.d['red'].ellipse((tx - 0.4 * s, ty - 0.4 * s + 0.4 * s, tx + 0.4 * s, ty + 0.4 * s + 0.4 * s), fill=255)

def yun(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, qiang=True, baby=False, old=0.0, **kw):
    """赵云: a tall, handsome general — white plumed helmet, silver armour, a long spear; at 长坂 a baby held to his chest."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=False, hat='helmet', layer=layer, kneel=kneel, bow=b, **kw)
    if up:
        A.d['wash'].polygon([(x - 0.02 * h, y - 1.06 * h), (x + 0.02 * h, y - 1.06 * h), (x - dir * 0.1 * h, y - 1.24 * h)], fill=255)
        A.d['fangtian'].rectangle((x - 0.1 * h, y - 0.76 * h, x + 0.1 * h, y - 0.5 * h), fill=200)
        A.d['wash'].polygon([(x - dir * 0.04 * h, y - 0.8 * h), (x - dir * 0.18 * h, y - 0.24 * h), (x - dir * 0.06 * h, y - 0.26 * h)], fill=230)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.02 * h, y - 0.84 * h), (x + dir * 0.08 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.72 * h)], fill=255)
        if qiang:
            spear(A, x + dir * 0.24 * h, y, 1.3 * h, dir * 0.05)
    if baby:
        A.d['longdan'].ellipse((x + dir * 0.02 * h - 0.07 * h, y - 0.72 * h, x + dir * 0.02 * h + 0.07 * h, y - 0.56 * h), fill=255)
        A.d['wash'].ellipse((x + dir * 0.04 * h - 0.03 * h, y - 0.74 * h, x + dir * 0.04 * h + 0.03 * h, y - 0.68 * h), fill=255)
    return hand

def white_horse(A, x, y, s, dir=1, ph=0.0, moving=True, rider_=True, baby=False):
    horse(A, x, y, s, dir=dir, ph=ph, layer='wash', moving=moving)
    A.d['ink'].line((x - 0.5 * s, y - 0.5 * s, x + 0.5 * s, y - 0.5 * s), fill=80, width=2)
    if rider_:
        yun(A, x - dir * 0.05 * s, y - 0.62 * s, 0.75 * s, dir=dir, arm=60, qiang=False, baby=baby)
        spear(A, x + dir * 0.3 * s, y - 0.6 * s, 1.2 * s, dir * 1.2)

def adou(A, x, y, h, stage_, layer='longdan'):
    """阿斗 at different ages: 0 nothing, 1 swaddled baby, 2 child, 3 youth, 4 crowned."""
    if stage_ == 1:
        A.d[layer].ellipse((x - 0.25 * h, y - 0.35 * h, x + 0.25 * h, y), fill=255)
        A.d['wash'].ellipse((x - 0.09 * h, y - 0.36 * h, x + 0.09 * h, y - 0.2 * h), fill=255)
    elif stage_ >= 2:
        hh = [0, 0, 0.5, 0.8, 1.0][stage_] * h
        person(A, x, y, hh, dir=-1, robe=True, hat='crown' if stage_ == 4 else 'none', arm=-8, layer=layer)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 4)}
def art_dou_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    A.d['mid'].rectangle((240, 1200, 840, 1214), fill=200)
    adou(A, 620, 1200, 300, b if q > 0.5 else a)
    if kb == 144:
        spear(A, 420, 1200, 300, lerp(0, -1.5, clamp((q - 0.4) / 0.6)))
    else:
        spear(A, 420, 1200, 380, 0)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_dou_chapter)
    ink_in(cv, text_img(no, SERIF, 56, CHANGSHAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_z_hook_baby(A, cv, t, u):
    ground(A, GROUND)
    white_horse(A, lerp(200, 600, ease_out(u / (1.2 * P))), GROUND, 200, dir=1, ph=t * 7, baby=True)

def art_z_hook_river(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    waves(A, 1190, t, rows=2, amp=4)
    boat(A, lerp(300, 600, ease_out(u / (1.2 * P))), 1200, 120, t)

def art_z_hook_gate(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label=None, layer='mid', open_=clamp(u / (1.0 * P)))
    ground(A, GROUND)

def art_z_hook_slips(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 300, 360, ease_out(u / (1.0 * P)), layer='wash')

# ================================================================ 第一回 常山
def art_z_birth(A, cv, t, u):
    for k in range(4):
        x = 140 + k * 260
        A.d['mid'].polygon([(x - 220, GROUND), (x - 40, GROUND - 260), (x + 40, GROUND - 260), (x + 220, GROUND)], fill=150)
    ground(A, GROUND)
    yun(A, 540, GROUND, 250, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('常山真定人 · 身长八尺 姿颜雄伟', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('常山', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '生年不详 外貌之描写见云别传', t, t - u + P)

def art_z_gongsun(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 220), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    for j in range(5):
        person(A, lerp(-100, 500, ease_out(u / (3 * P))) - j * 90, GROUND, 130, dir=1, robe=False, hat='knot', spear=True, arm=40, ph=t * 4 + j, layer='mid')
    yun(A, lerp(0, 600, ease_out(u / (3 * P))), GROUND, 190, dir=1, ph=t * 4, arm=-8)
    A.flush(cv)
    paste(cv, text_img('率本郡义从 · 投奔公孙瓒', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_meet(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 820, GROUND, 260, 200, layer='mid', open_=1.0)
    bei(A, 640, GROUND, 200, dir=-1, arm=lerp(-8, 80, ease_out(u / 0.6)))
    yun(A, 380, GROUND, 210, dir=1, bow=15, arm=60)
    A.flush(cv)
    paste(cv, text_img('公孙瓒遣其随刘备 · 刘备深加接纳', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_farewell(A, cv, t, u):
    ground(A, GROUND)
    bei(A, 600, GROUND, 200, dir=-1, arm=90)
    yun(A, 470, GROUND, 210, dir=1, arm=90, qiang=False)
    A.flush(cv)
    paste(cv, text_img('以兄丧辞归 · 刘备捉手而别', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '云辞曰 终不背德也 见云别传', t, t - u + P)

def art_z_ye(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    A.d['mid'].rectangle((280, GROUND - 80, 800, GROUND - 50), fill=230)
    lamp(A, 880, GROUND, 50, t, glow=0.7)
    A.flush(cv)
    paste(cv, text_img('刘备依袁绍 赵云往邺相见 · 同床眠卧', SERIF, 44, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见云别传', t, t - u + P)

def art_z_buqu(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    n = min(8, int(clamp(u / (2.5 * P)) * 8) + 1)
    for j in range(n):
        person(A, 120 + j * 90, GROUND, 130, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='changshan')
    yun(A, 880, GROUND, 200, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('为刘备密募数百人 · 皆称刘左将军部曲', SERIF, 44, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_bowang(A, cv, t, u):
    """6-beat set piece: 博望 — he captures 夏侯兰, a man from his own county; begs his life from 刘备 and recommends him as a judge,
    but never keeps him close: such was his caution."""
    ph = u / P
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    if ph < 2:
        yun(A, lerp(200, 520, clamp(ph / 1.5)), GROUND, 200, dir=1, ph=t * 5, arm=60)
        person(A, 720, GROUND, 180, dir=-1, robe=False, hat='helmet', fall=lerp(0, 60, clamp((ph - 1.2) / 0.5)), arm=-8, layer='ink')
        lab = '博望之战 · 生擒夏侯兰'
    elif ph < 4:
        bei(A, 760, GROUND, 200, dir=-1, arm=-8)
        yun(A, 520, GROUND, 190, dir=1, bow=25, arm=90)
        person(A, 300, GROUND, 160, dir=1, robe=False, hat='knot', kneel=True, bow=30, layer='ink')
        lab = '夏侯兰是同乡 · 赵云为其求情'
    else:
        yun(A, 300, GROUND, 200, dir=1, arm=-8)
        person(A, 800, GROUND, 170, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
        lab = '荐为军正 · 却从不让他接近自己'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '其慎虑类如此 见云别传', t, t - u + 4 * P)

# ================================================================ 第二回 长坂
def scene_changban(cv, t, c, k):
    """8-beat custom scene: 长坂 — 曹操's cavalry overtake the fleeing column; 刘备 abandons wife and children and flees;
    赵云 holds the infant 刘禅 to his chest and guards 甘夫人 through the rout."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    for i in range(30):
        q = (t * 0.5 + i / 30) % 1
        A.d['dune'].ellipse((80 + (i * 61) % 920 - 20, 1300 - 200 * q - 10, 80 + (i * 61) % 920 + 20, 1300 - 200 * q + 10), fill=int(120 * (1 - q)))
    ground(A, GROUND)
    if ph < 2.5:
        for j in range(5):
            rider(A, lerp(-100, 900, ((t * 0.15 + j / 5) % 1)), GROUND, 110, dir=1, ph=t * 7 + j, layer='ink', spear=True)
        for j in range(6):
            person(A, lerp(200, 1000, ((t * 0.05 + j / 6) % 1)), GROUND, 90, dir=1, robe=False, hat='knot', ph=t * 4 + j, arm=150, layer='mid')
        lab, col = '曹军轻骑一日一夜追及长坂 · 刘备弃妻子南走', ZHU
    elif ph < 5.5:
        white_horse(A, lerp(-100, 600, clamp((ph - 2.5) / 3)), GROUND, 190, dir=1, ph=t * 7, baby=True)
        person(A, lerp(-260, 440, clamp((ph - 2.5) / 3)), GROUND, 150, dir=1, robe=True, hat='knot', female=True, ph=t * 4, arm=-8, layer='longdan')
        for j in range(3):
            rider(A, 900 - j * 120, GROUND, 110, dir=-1, ph=t * 6 + j, layer='ink', spear=True)
        lab, col = '赵云身抱弱子 · 保护甘夫人 皆得免难', CHANGSHAN
    else:
        white_horse(A, 540, GROUND, 200, dir=1, ph=0, moving=False, baby=True)
        lab, col = '弱子 即后主刘禅', CHANGSHAN
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '长坂救主', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=79)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 42, col, 'Black', bleed=False, spacing=2), W / 2, 575, 1, 1)
    note_in(cv, '正史仅此数语 单骑七进七出出自演义', t, s0 + 3 * P)

def art_z_shouji(A, cv, t, u):
    ground(A, GROUND)
    bei(A, 380, GROUND, 200, dir=1, arm=lerp(-8, 150, clamp(u / (0.5 * P))))
    q = clamp((u - 0.5 * P) / (0.6 * P))
    A.d['fangtian'].line((lerp(440, 820, q) - 30, GROUND - 200, lerp(440, 820, q) + 30, GROUND - 200), fill=255, width=6)
    person(A, 800, GROUND, 170, dir=-1, robe=False, hat='helmet', bow=20, arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('或言赵云已北去 · 刘备以手戟掷之', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('子龙不弃我走也', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.4))
    note_in(cv, '见云别传', t, t - u + P)

def art_z_yamen(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 760, GROUND, 300, 220, layer='changshan', open_=1.0)
    yun(A, 420, GROUND, 220, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('迁为牙门将军', SERIF, 48, CHANGSHAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_guiyang(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='桂阳', layer='mid', open_=1.0)
    ground(A, GROUND)
    yun(A, 540, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('随刘备平定江南 · 领桂阳太守', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_marriage(A, cv, t, u):
    """6-beat set piece: 拒婚 — 赵范 offers his widowed sister-in-law; 赵云 declines: we share a surname, your brother is as my brother;
    soon 赵范 flees, and 赵云 is untouched by it."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mid')
    if ph < 2:
        person(A, 760, GROUND, 180, dir=-1, robe=True, hat='knot', kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
        person(A, 900, GROUND, 170, dir=-1, robe=True, hat='knot', female=True, arm=-8, layer='pink')
        yun(A, 320, GROUND, 170, dir=1, kneel=True, arm=-8, qiang=False)
        lab = '赵范欲以寡嫂樊氏妻之'
    elif ph < 4:
        person(A, 760, GROUND, 180, dir=-1, robe=True, hat='knot', kneel=True, arm=-8, layer='ink')
        yun(A, 320, GROUND, 170, dir=1, kneel=True, arm=lerp(-8, 110, clamp((ph - 2) / 0.6)), qiang=False)
        lab = '相与同姓 卿兄犹我兄 · 固辞不许'
    else:
        yun(A, 540, GROUND, 220, dir=1, arm=-8)
        lab = '后赵范果然逃走 · 赵云无所牵连'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if 2 <= ph < 4 else CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '见云别传', t, t - u + P)

def art_z_neishi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for j in range(4):
        person(A, 700 + j * 80, GROUND, 140, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='jiangdong')
    person(A, 560, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, sword=60, arm=60, layer='pink')
    yun(A, 300, GROUND, 200, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('刘备入蜀 留赵云掌内事 · 孙夫人骄豪 多将吴吏兵', SERIF, 42, CHANGSHAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 截江
def art_z_jiejiang(A, cv, t, u):
    """6-beat set piece: 截江夺阿斗 — 孙权 sends ships for his sister; she means to take the boy 刘禅 to 吴;
    赵云 and 张飞 block the river and bring the boy back."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1140, W - 60, GROUND + 40), fill=160)
    waves(A, 1150, t, rows=3, amp=5)
    Zy.wu_ship(A, lerp(500, 760, clamp(ph / 2)), 1170, 90, t)
    if ph < 2:
        person(A, lerp(500, 760, clamp(ph / 2)), 1060, 120, dir=1, robe=True, hat='knot', female=True, arm=60, layer='pink')
        adou(A, lerp(540, 800, clamp(ph / 2)), 1060, 100, 2)
        lab = '孙夫人欲携阿斗回吴'
    elif ph < 4:
        boat(A, lerp(-100, 420, clamp((ph - 2) / 1.5)), 1180, 90, t)
        yun(A, lerp(-100, 420, clamp((ph - 2) / 1.5)), 1130, 130, dir=1, arm=60)
        zhangfei(A, lerp(-180, 340, clamp((ph - 2) / 1.5)), 1130, 130, dir=1, spear=True, arm=40)
        lab = '赵云 张飞勒兵截江'
    else:
        boat(A, lerp(420, -100, clamp((ph - 4) / 2)), 1180, 90, t)
        yun(A, lerp(420, -100, clamp((ph - 4) / 2)), 1130, 130, dir=-1, arm=60, baby=True, qiang=False)
        lab = '乃得后主还'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4 else CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('截江', 56), 860, 1020, t, t - u + 2 * P, rot=6)
    note_in(cv, '第二次救下刘禅 见汉晋春秋及云别传', t, t - u + 4 * P)

def art_z_rushu(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    river(A, 1210, t, rows=3, amp=4)
    for k in range(3):
        boat(A, lerp(-100, 600, ease_out(u / (3 * P))) - k * 160, 1220, 70, t)
    A.flush(cv)
    paste(cv, text_img('与诸葛亮 张飞溯江入蜀 · 定江阳 犍为', SERIF, 44, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_tian(A, cv, t, u):
    for k in range(5):
        A.d['grass'].rectangle((120 + k * 170, 1240, 270 + k * 170, GROUND - 20), fill=150 + 20 * (k % 2))
    ground(A, GROUND)
    bei(A, 760, GROUND, 200, dir=-1, arm=-8)
    yun(A, 460, GROUND, 200, dir=1, bow=15, arm=lerp(-8, 100, ease_out(u / 0.6)), qiang=False)
    A.flush(cv)
    paste(cv, text_img('刘备欲分成都田宅 · 赵云谏宜归还百姓', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '令安居复业 然后可役调 刘备从之 见云别传', t, t - u + P)

def art_z_yijun(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='changshan')
    ground(A, GROUND)
    yun(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('成都既定 · 以赵云为翊军将军', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_hanzhong(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    for j in range(5):
        rider(A, lerp(-100, 600, ease_out(u / (4 * P))) - j * 110, GROUND, 110, dir=1, ph=t * 6 + j, layer='changshan', spear=True)
    A.flush(cv)
    paste(cv, text_img('黄忠劫粮逾期不还 · 赵云率数十骑出营探视', SERIF, 44, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_tuwei(A, cv, t, u):
    ground(A, GROUND)
    army(A, 520, GROUND, 6, dir=-1, layer='ink', t=t, march=True, h=100)
    white_horse(A, lerp(200, 640, 0.5 + 0.5 * math.sin(t * 1.4)), GROUND, 160, dir=1 if math.cos(t * 1.4) > 0 else -1, ph=t * 7)
    A.flush(cv)
    paste(cv, text_img('猝遇曹操大军 且战且退 · 回马救出部将张著', SERIF, 44, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 汉水
def art_z_kongying(A, cv, t, u):
    """6-beat set piece: 空营计 — back in camp, he opens the gates wide, lowers the banners and silences the drums;
    曹 troops suspect an ambush and pull back; then drums thunder and crossbows shoot; 曹军 flee into the 汉水."""
    ph = u / P
    city_wall(A, 460, 1020, 1080, gate_x=740, label=None, layer='mid', open_=1.0)
    ground(A, GROUND)
    if ph < 3:
        banner(A, 560, 1080, 160, t, layer='changshan', fallen=0.9)
        army(A, lerp(-300, 0, clamp(ph / 2)), GROUND, 5, dir=1, layer='ink', t=t, march=ph < 2, h=100)
        lab = '大开营门 偃旗息鼓' if ph < 1.5 else '曹军疑有伏兵 引去'
    else:
        banner(A, 560, 1080, 160, t, layer='changshan')
        for k in range(10):
            q = (t * 2 + k / 10) % 1
            A.d['ink'].line((lerp(700, 100, q), 1100 + k * 20, lerp(700, 100, q) - 50, 1100 + k * 20), fill=255, width=3)
        army(A, lerp(0, -500, clamp((ph - 3) / 2)), GROUND, 5, dir=-1, layer='ink', t=t, march=True, h=100)
        lab = '雷鼓震天 劲弩后射 · 曹军惊溃'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44 if ph >= 3 else 46, ZHU if ph >= 3 else CHANGSHAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    note_in(cv, '见云别传', t, t - u + P)

def art_z_dan(A, cv, t, u):
    ground(A, GROUND)
    bei(A, 380, GROUND, 210, dir=1, arm=lerp(-8, 100, ease_out(u / 0.6)), crown=True, old=0.5)
    yun(A, 680, GROUND, 220, dir=-1, bow=15, arm=-8)
    A.flush(cv)
    paste(cv, text_img('子龙一身都是胆也', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '刘备次日视察营地所叹 见云别传', t, t - u + P)

def art_z_jian(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    bei(A, 760, GROUND, 200, dir=-1, crown=True, arm=-8, old=0.6)
    yun(A, 400, GROUND, 190, dir=1, kneel=True, bow=25, arm=90, qiang=False)
    A.flush(cv)
    paste(cv, text_img('国贼是曹操 非孙权也 · 刘备不听', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '谏伐吴 见云别传', t, t - u + P)

def art_z_yiling(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 40, GROUND - 400), (x + 40, GROUND - 400), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    for j in range(5):
        person(A, lerp(1100, 300, ease_out(u / (3 * P))) + j * 90, GROUND, 130, dir=-1, robe=False, hat='helmet', spear=True, arm=40, ph=t * 4 + j, layer='changshan')
    A.flush(cv)
    paste(cv, text_img('夷陵大败 · 赵云自江州进兵永安接应', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_houzhu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qiuhuang')
    ground(A, GROUND)
    adou(A, 720, GROUND, 200, 4)
    yun(A, 420, GROUND, 200, dir=1, bow=20, arm=90, old=0.5)
    A.flush(cv)
    paste(cv, text_img('刘备崩于永安 · 后主即位', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_hou(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='changshan')
    ground(A, GROUND)
    yun(A, 540, GROUND, 210, dir=1, arm=60, old=0.6)
    A.flush(cv)
    paste(cv, text_img('封永昌亭侯 · 迁镇东将军', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('亭侯', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_hanzhong2(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 40, GROUND - 400), (x + 40, GROUND - 400), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    kongming(A, 700, GROUND, 200, dir=-1, arm=60)
    yun(A, 420, GROUND, 200, dir=1, arm=-8, old=0.7)
    A.flush(cv)
    paste(cv, text_img('诸葛亮北伐 · 赵云随军屯驻汉中', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 箕谷
def art_z_jigu(A, cv, t, u):
    """6-beat set piece: 箕谷 — as the decoy army he holds 箕谷 against 曹真's main force; outnumbered, he loses the field,
    but gathers his men and holds firm: no rout."""
    ph = u / P
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 40, GROUND - 420), (x + 40, GROUND - 420), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    if ph < 2:
        banner(A, 300, GROUND, 300, t, layer='changshan')
        for j in range(4):
            person(A, 380 + j * 80, GROUND, 120, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='changshan')
        lab = '与邓芝为疑兵 · 据守箕谷'
    elif ph < 4:
        army(A, lerp(1100, 600, clamp((ph - 2) / 1.5)), GROUND, 7, dir=-1, layer='ink', t=t, march=True, h=100)
        yun(A, 360, GROUND, 190, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 6)), old=0.8)
        lab = '兵弱敌强 · 失利于箕谷'
    else:
        for j in range(5):
            person(A, 200 + j * 70, GROUND, 120, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='changshan')
        yun(A, 640, GROUND, 200, dir=-1, arm=60, old=0.8)
        lab = '敛众固守 · 不至大败'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if 2 <= ph < 4 else CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('箕谷', 56), 860, 1020, t, t - u + 0.4, rot=6)

def art_z_bian(A, cv, t, u):
    tent(A, 540, GROUND, 400, 280, layer='mid', open_=1.0)
    ground(A, GROUND)
    yun(A, 540, GROUND, 190, dir=1, bow=20, arm=-8, old=0.8)
    A.flush(cv)
    paste(cv, text_img('诸葛亮自贬三等 · 赵云贬为镇军将军', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_juan(A, cv, t, u):
    ground(A, GROUND)
    for i in range(6):
        A.d['wash'].rectangle((420 + (i % 3) * 80, GROUND - 40 - (i // 3) * 40, 490 + (i % 3) * 80, GROUND - 6 - (i // 3) * 40), fill=255)
    kongming(A, 780, GROUND, 190, dir=-1, arm=lerp(-8, 80, ease_out(u / 0.6)))
    yun(A, 280, GROUND, 190, dir=1, arm=lerp(-8, 90, ease_out((u - P) / 0.6)), old=0.8, qiang=False)
    A.flush(cv)
    paste(cv, text_img('军事无利 何为有赐', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '诸葛亮欲以余绢分赐将士 见云别传', t, t - u + P)

def art_z_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    yun(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, qiang=False)
    spear(A, 860, GROUND, 360, 0)
    lamp(A, 180, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('建兴七年 · 赵云卒', SERIF, 48, CHANGSHAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_shunping(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('顺平', 90, ZHU), 540, 1140, t, t - u + 0.6)
    paste(cv, text_img('追谥顺平侯 · 柔贤慈惠曰顺 执事有班曰平', SERIF, 42, CHANGSHAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_z_novel(A, cv, t, u):
    ground(A, GROUND)
    A.d['red'].rectangle((200, 960, 880, 1000), fill=200)
    A.d['ink'].rectangle((200, 1000, 220, GROUND), fill=255); A.d['ink'].rectangle((860, 1000, 880, GROUND), fill=255)
    A.d['dune'].rectangle((200, GROUND - 60, 880, GROUND), fill=230)
    yun(A, 540, GROUND - 60, 220, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    paste(cv, text_img('七进七出 常胜将军 · 皆出自演义', SERIF, 46, CHANGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '正史本传寥寥数百字 却无一处失德', t, t - u + P)

def art_z_legacy(A, cv, t, u):
    spear(A, 860, 1440, 180, 0.1)

def art_z_title(A, cv, t, u):
    white_horse(A, 820, 1440, 200, dir=-1, ph=0, moving=False, rider_=False)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    yun(A, 380, 1460, 640, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '常山'), 48: ('第二回', '长坂'), 80: ('第三回', '截江'),
            112: ('第四回', '汉水'), 144: ('第五回', '箕谷')}

CARDS = [
    C(0, 2, 'war', 'num', num='怀抱幼主', line='护送脱险', art=art_z_hook_baby),
    C(2, 4, 'works', 'num', num='截江夺子', line='第二次救下阿斗', art=art_z_hook_river),
    C(4, 6, 'night', 'num', num='一座空营', line='吓退曹操大军', art=art_z_hook_gate),
    C(6, 8, 'fate', 'num', num='寥寥数百字', line='成了完美英雄', art=art_z_hook_slips),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 常山
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=191, main='常山真定', sub='姿颜雄伟', art=art_z_birth),
    C(22, 26, 'war', 'card', year=191, main='投公孙瓒', sub='本郡义从', art=art_z_gongsun),
    C(26, 30, 'court', 'card', year=192, main='初遇刘备', sub='深加接纳', art=art_z_meet),
    C(30, 34, 'fate', 'card', year=192, main='捉手而别', sub='终不背德', note='年份约略', art=art_z_farewell),
    C(34, 38, 'night', 'card', year=200, main='邺城重逢', sub='同床眠卧', art=art_z_ye),
    C(38, 42, 'empire', 'card', year=200, main='密募部曲', sub='数百人', art=art_z_buqu),
    C(42, 48, 'works', 'card', year=202, main='博望', sub='擒夏侯兰', art=art_z_bowang),
    # ---- 第二回 长坂
    C(48, 50, 'war', 'chapter'),
    C(50, 58, 'death', 'changban', year=208),
    C(58, 62, 'fate', 'card', year=208, main='手戟掷之', sub='子龙不弃我', art=art_z_shouji),
    C(62, 66, 'empire', 'card', year=208, main='牙门将军', sub='迁', art=art_z_yamen),
    C(66, 70, 'war', 'card', year=209, main='领桂阳', sub='平定江南', art=art_z_guiyang),
    C(70, 76, 'night', 'card', year=209, main='拒婚', sub='卿兄犹我兄', art=art_z_marriage),
    C(76, 80, 'court', 'card', year=211, main='掌内事', sub='孙夫人', art=art_z_neishi),
    # ---- 第三回 截江
    C(80, 82, 'works', 'chapter'),
    C(82, 88, 'death', 'card', year=212, main='截江夺斗', sub='再救后主', note='年份约略', art=art_z_jiejiang),
    C(88, 92, 'empire', 'card', year=214, main='入蜀', sub='江阳犍为', art=art_z_rushu),
    C(92, 96, 'works', 'card', year=214, main='还田于民', sub='谏分田宅', art=art_z_tian),
    C(96, 100, 'court', 'card', year=214, main='翊军将军', sub='成都', art=art_z_yijun),
    C(100, 106, 'war', 'card', year=219, main='汉中之战', sub='出营接应', art=art_z_hanzhong),
    C(106, 112, 'fate', 'card', year=219, main='回马救将', sub='张著', art=art_z_tuwei),
    # ---- 第四回 汉水
    C(112, 114, 'night', 'chapter'),
    C(114, 120, 'night', 'card', year=219, main='空营计', sub='偃旗息鼓', art=art_z_kongying),
    C(120, 124, 'empire', 'card', year=219, main='一身是胆', sub='刘备之叹', art=art_z_dan),
    C(124, 128, 'court', 'card', year=221, main='谏伐吴', sub='国贼是曹', art=art_z_jian),
    C(128, 132, 'death', 'card', year=222, main='夷陵之后', sub='永安接应', art=art_z_yiling),
    C(132, 136, 'fate', 'card', year=223, main='后主即位', sub='刘禅', art=art_z_houzhu),
    C(136, 140, 'empire', 'card', year=223, main='永昌亭侯', sub='镇东将军', art=art_z_hou),
    C(140, 144, 'works', 'card', year=227, main='屯驻汉中', sub='随军北伐', art=art_z_hanzhong2),
    # ---- 第五回 箕谷
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'war', 'card', year=228, main='箕谷之战', sub='敛众固守', art=art_z_jigu),
    C(152, 156, 'fate', 'card', year=228, main='贬镇军', sub='自领其咎', art=art_z_bian),
    C(156, 160, 'works', 'card', year=228, main='余绢不赏', sub='待冬赐之', art=art_z_juan),
    C(160, 164, 'death', 'card', year=229, main='赵云去世', sub='建兴七年', art=art_z_death),
    C(164, 168, 'court', 'card', year=261, main='顺平侯', sub='追谥', art=art_z_shunping),
    C(168, 170, 'end', 'card', year=1522, main='常胜将军', sub='演义之名', art=art_z_novel),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='柒拾玖', col=CHANGSHAN, acc=LONGDAN, born=191, died=229, age0=190, no_age=True,
    born_lab='生年不详', died_lab='229年', years_txt='生年不详 — 公元229',
    hook_q='正史只给他寥寥数百字 · 为什么成了完美英雄？',
    name_line='赵云 · 字子龙', name='赵云', seal='子龙', title_art=art_z_title,
    q1='常胜将军？', q2='低调忠臣？',
    end_art=art_z_legacy, end_big='一身是胆', end_seal='子龙',
    end_l1='史书给他的笔墨很少', end_l2='他却两次救下了刘家的骨血',
    end_brush='忠勇谨慎', end_ask='你心中三国最完美的武将是谁？评论区聊聊', next='鉴真'),
    scenes=dict(chapter=scene_chapter, changban=scene_changban))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
