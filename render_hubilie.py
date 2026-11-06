"""千古人物志 · 第柒拾集 · 忽必烈 (1215–1294)
Look: 草原绿 + 金帐黄, 金帐 corner borders (a small golden yurt dome), a steppe that turns into city walls on the right.
Chapter card: 从金帐到大都 — the same horizon grows from an empty steppe to a yurt, to 开平's walls, to 大都's palace, to ships at sea;
in the last chapter the sun sets over palace and yurt together.
Set pieces: custom 8-beat scene 'gelang' (革囊渡江 · 止杀令), 6-beat 汗位之争, 6-beat 襄阳回回炮, 6-beat 崖山, 6-beat 东征台风.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zhuxi as Zx           # engine + helpers (previous episode)
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
from render_zhangqian import yurt
from render_genghis import trebuchet
from render_songtaizu import elephant

F.RIPPLE = False
CAOYUAN = (96, 128, 72)             # 草原绿
JINZHANG = (198, 150, 50)           # 金帐黄
S.LAYERS.append(('caoyuan', CAOYUAN, 0.9, 1.0))
S.LAYERS.append(('jinzhang', JINZHANG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='元', life='汗', court='朝', night='星', war='战', empire='元', works='都', fate='命', death='殇', end='一')
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
G.THEMES['empire']['sun'] = (JINZHANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (JINZHANG, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # steppe grass lines on the left, fading to the right
    _d.line([(40 + i * 18, 1450 + _k * 16 + 4 * math.sin(i * 0.6 + _k)) for i in range(28)], fill=CAOYUAN + (50 - _k * 12,), width=3)
for _x in (120, 220):               # two distant yurts on the left
    _d.rectangle((_x - 28, 1414, _x + 28, 1440), fill=(230, 226, 214, 70)); _d.chord((_x - 28, 1388, _x + 28, 1440), 180, 360, fill=(230, 226, 214, 70))
_d.rectangle((700, 1400, 1040, 1440), fill=(110, 100, 90, 46))     # a city wall on the right
for _i in range(9):
    _d.rectangle((704 + _i * 38, 1388, 724 + _i * 38, 1400), fill=(110, 100, 90, 46))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (112, 70, 50), 'fate': (96, 98, 96)}
def draw_background(t, theme):
    """草原与城: low steppe hills, yurts on the left, a wall on the right."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 194, 180), (164, 168, 146), MTN_COL.get(theme, (110, 128, 96))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.6))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """金帐: a small golden yurt dome in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=CAOYUAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=CAOYUAN + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.rectangle((cx - 28, cy, cx + 28, cy + 20), fill=JINZHANG + (230,))
        d.chord((cx - 28, cy - 26, cx + 28, cy + 26), 180, 360, fill=JINZHANG + (230,))
        d.rectangle((cx - 6, cy + 4, cx + 6, cy + 20), fill=(60, 50, 40, 230))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def kub(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, armour=False, **kw):
    """忽必烈: Mongol khan — round brimmed hat with a gold top, braids behind the ears, beard (white when old)."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else ('none' if up else 'knot'), layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up and not armour:
        d.ellipse((x - 0.14 * h, y - 0.98 * h, x + 0.14 * h, y - 0.94 * h), fill=255)
        d.chord((x - 0.08 * h, y - 1.08 * h, x + 0.08 * h, y - 0.92 * h), 180, 360, fill=255)
        A.d['jinzhang'].ellipse((x - 0.025 * h, y - 1.12 * h, x + 0.025 * h, y - 1.07 * h), fill=255)
        d.line((x - dir * 0.06 * h, y - 0.92 * h, x - dir * 0.08 * h, y - 0.8 * h), fill=255, width=max(2, int(0.018 * h)))
    if up:
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.02 * h, y - 0.84 * h), (x + dir * 0.09 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.72 * h)], fill=255)
        A.d['jinzhang'].rectangle((x - 0.08 * h, y - 0.56 * h, x + 0.08 * h, y - 0.52 * h), fill=255)
    return hand

def banknote(A, cx, cy, s):
    A.d['wash'].rectangle((cx - 0.6 * s, cy - s, cx + 0.6 * s, cy + s), fill=255)
    A.d['ink'].rectangle((cx - 0.6 * s, cy - s, cx + 0.6 * s, cy + s), outline=255, width=6)
    A.d['ink'].rectangle((cx - 0.5 * s, cy - 0.9 * s, cx + 0.5 * s, cy + 0.9 * s), outline=180, width=2)
    for k in range(6):
        A.d['ink'].ellipse((cx - 0.3 * s + (k % 3) * 0.3 * s - 10, cy - 0.1 * s + (k // 3) * 0.25 * s - 10, cx - 0.3 * s + (k % 3) * 0.3 * s + 10, cy - 0.1 * s + (k // 3) * 0.25 * s + 10), outline=200, width=3)
    A.d['red'].rectangle((cx - 0.2 * s, cy + 0.5 * s, cx + 0.2 * s, cy + 0.8 * s), fill=220)

def skin_raft(A, x, y, s, t, k=0):
    """革囊: inflated sheepskins lashed together, a soldier paddling on top."""
    bob = 6 * math.sin(t * 3 + k)
    for i in range(3):
        A.d['dune'].ellipse((x - s + i * 0.66 * s, y - 0.25 * s + bob, x - 0.3 * s + i * 0.66 * s, y + 0.15 * s + bob), fill=255)
    person(A, x, y - 0.2 * s + bob, 0.9 * s, dir=1, robe=False, hat='helmet', arm=lerp(80, 150, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='ink')

def low_wall(A, x0, x1, top, base, layer='mid'):
    A.d[layer].rectangle((x0, top, x1, base), fill=230)
    for i in range(int((x1 - x0) / 40)):
        A.d[layer].rectangle((x0 + 4 + i * 40, top - 16, x0 + 24 + i * 40, top), fill=230)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 5)}
def horizon(A, cv, t, stage_):
    A.d['caoyuan'].rectangle((240, 1180, 840, 1200), fill=200)
    if stage_ >= 1 and stage_ < 5:
        yurt(A, 380 if stage_ >= 2 else 540, 1180, 160, 120, layer='mid')
        A.d['jinzhang'].ellipse((370 if stage_ >= 2 else 530, 1050, 390 if stage_ >= 2 else 550, 1070), fill=255)
    if stage_ >= 2:
        low_wall(A, 520, 820, 1100, 1180)
    if stage_ >= 3:
        palace(A, 670, 1100, 150, layer='jinzhang')
    if stage_ >= 4:
        for k in range(3):
            boat(A, 330 + k * 90, 1200, 40, t)
    if stage_ >= 5:
        yurt(A, 340, 1180, 160, 120, layer='mid')
        A.d['jinzhang'].ellipse((470, 900, 610, 1040), fill=200)

def art_khan_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    horizon(A, cv, t, b if q > 0.5 else a)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_khan_chapter)
    ink_in(cv, text_img(no, SERIF, 56, CAOYUAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_k_hook_dadu(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='大都', layer='mid', open_=clamp(u / (1.2 * P)))
    ground(A, GROUND)

def art_k_hook_note(A, cv, t, u):
    banknote(A, 540, 1060, 200)
    A.flush(cv)
    paste(cv, text_img('\n'.join('中统元宝交钞'), SERIF, 38, INK, 'Black', bleed=False, spacing=2), 540, 1020, 1, clamp(u / 0.4))

def art_k_hook_storm(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1100, W - 60, GROUND + 40), fill=170)
    waves(A, 1110, t, rows=3, amp=6 + 18 * clamp(u / (1.2 * P)))
    for k in range(4):
        boat(A, 200 + k * 220, 1130 + 10 * math.sin(t * 3 + k), 60, t)

def art_k_hook_seal(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('大元', 120, ZHU), 540, 1080, t, t - u + 0.4)
    paste(cv, text_img('大哉乾元', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=8), W / 2, 1280, 1, clamp((u - 0.8) / 0.4))

# ================================================================ 第一回 黄金家族
def art_k_birth(A, cv, t, u):
    ground(A, GROUND)
    yurt(A, 540, GROUND, 360, 240, layer='mid')
    for j in range(3):
        horse(A, 140 + j * 90, GROUND, 70, dir=1, ph=0, head_down=0.6, moving=False, layer='caoyuan')
    A.flush(cv)
    paste(cv, text_img('成吉思汗之孙 · 父拖雷 母唆鲁禾帖尼', SERIF, 42, CAOYUAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('拖雷', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '母亲以贤明著称 善待汉地百姓', t, t - u + P)

def art_k_hunt(A, cv, t, u):
    ground(A, GROUND)
    person(A, 700, GROUND, 230, dir=-1, robe=True, hat='helmet', arm=lerp(-8, 70, ease_out((u - P) / 0.6)), layer='ink')
    person(A, 520, GROUND, 120, dir=1, robe=True, hat='none', arm=lerp(-8, 60, ease_out((u - P) / 0.6)), layer='caoyuan')
    A.d['dune'].ellipse((260, GROUND - 30, 320, GROUND), fill=255)
    A.flush(cv)
    paste(cv, text_img('少年首猎 · 祖父亲为其抹指', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '蒙古旧俗 事见波斯史书史集', t, t - u + P)

def art_k_father(A, cv, t, u):
    ground(A, GROUND)
    yurt(A, 700, GROUND, 300, 200, layer='mid')
    person(A, 300, GROUND, 140, dir=1, robe=True, hat='none', kneel=True, bow=30, layer='caoyuan')
    A.flush(cv)
    paste(cv, text_img('父拖雷伐金归途 病逝', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_xingzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='邢州', layer='mid', open_=1.0)
    ground(A, GROUND)
    for j in range(4):
        person(A, lerp(560, 1100, ((t * 0.06 + j / 4) % 1)), GROUND, 90, dir=1, robe=False, hat='knot', load=True, ph=t * 4 + j, arm=160, layer='ink')
    A.flush(cv)
    paste(cv, text_img('分得邢州封地 · 官吏扰民 百姓逃散', SERIF, 44, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_mufu(A, cv, t, u):
    """6-beat: 金莲川幕府 — Han scholars arrive one by one at his tent: 刘秉忠, 姚枢, 许衡 ..."""
    ph = u / P
    for i in range(14):
        x = 120 + (i * 67) % 840
        A.d['jinzhang'].ellipse((x - 10, GROUND - 16, x + 10, GROUND + 4), fill=220)
    ground(A, GROUND)
    yurt(A, 780, GROUND, 300, 210, layer='mid')
    kub(A, 620, GROUND, 190, dir=-1, arm=lerp(-8, 80, clamp((ph - 1) / 0.6)))
    n = min(4, int(clamp(ph / 4) * 4) + 1)
    for j in range(n):
        person(A, 150 + j * 100, GROUND, 160, dir=1, robe=True, hat='knot', bow=15, arm=60, layer='ink' if j % 2 else 'caoyuan')
    A.flush(cv)
    lab = '思大有为于天下' if ph < 3 else '召刘秉忠 姚枢等汉儒 · 问以治道'
    paste(cv, text_img(lab, SERIF, 46 if ph < 3 else 42, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    note_in(cv, '后人称为金莲川幕府', t, t - u + 2 * P)

def art_k_monan(A, cv, t, u):
    yurt(A, 540, GROUND, 420, 280, layer='jinzhang')
    ground(A, GROUND)
    person(A, 720, GROUND, 200, dir=-1, robe=True, hat='helmet', arm=lerp(-8, 100, ease_out(u / 0.6)), layer='ink')
    kub(A, 380, GROUND, 190, dir=1, bow=15, arm=60)
    A.flush(cv)
    paste(cv, text_img('兄蒙哥即汗位 · 命其总领漠南汉地', SERIF, 44, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_hanfa(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='邢州', layer='mid', open_=1.0)
    ground(A, GROUND)
    for j in range(4):
        person(A, lerp(1100, 560, ((t * 0.06 + j / 4) % 1)), GROUND, 90, dir=-1, robe=False, hat='knot', load=True, ph=t * 4 + j, arm=160, layer='caoyuan')
    A.flush(cv)
    paste(cv, text_img('派良吏治邢州 · 流民归来 户口倍增', SERIF, 44, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('汉法', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第二回 革囊渡江
def scene_gelang(cv, t, c, k):
    """8-beat custom scene: 征大理 — the army crosses the 金沙江 on inflated sheepskins; reaches 大理;
    on 姚枢's advice, silk banners are torn and written with the order: no killing."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    if ph < 3:
        for k in range(3):
            A.d['mid'].polygon([(-60 + k * 420, 1180), (140 + k * 420, 840), (360 + k * 420, 1180)], fill=140)
        A.d['ocean'].rectangle((0, 1180, W, GROUND + 40), fill=180)
        river(A, 1190, t, rows=3, amp=8, speed=2.0)
        for k in range(4):
            skin_raft(A, lerp(-120, 1100, ((ph / 3) * 0.8 + k * 0.22) % 1.2 - 0.1), 1230 + (k % 2) * 60, 70, t, k)
        lab = '金沙江天险 · 乘革囊及筏渡江'
    elif ph < 5:
        city_wall(A, 200, 880, 1060, gate_x=540, label='大理', layer='mid', open_=clamp((ph - 3.5) / 1))
        ground(A, GROUND)
        army(A, lerp(-200, 200, clamp((ph - 3) / 1.5)), GROUND, 5, dir=1, layer='ink', t=t, march=ph < 4.5, h=100)
        lab = '直趋大理 · 国主出走'
    else:
        city_wall(A, 200, 880, 1060, gate_x=540, label='大理', layer='mid', open_=1.0)
        ground(A, GROUND)
        for k in range(3):
            x = 300 + k * 240
            A.d['ink'].line((x, GROUND, x, GROUND - 330), fill=255, width=6)
            A.d['wash'].rectangle((x + 4, GROUND - 330, x + 110, GROUND - 160 + 8 * math.sin(t * 3 + k)), fill=255)
        kub(A, 160, GROUND, 180, dir=1, armour=True, arm=lerp(-8, 90, clamp((ph - 5) / 0.6)))
        lab = '裂帛为旗 · 书止杀之令'
    A.flush(cv)
    if ph >= 5:
        for k in range(3):
            paste(cv, text_img('止\n杀', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), 357 + k * 240, GROUND - 250, 1, clamp((ph - 5.3 - k * 0.3) / 0.3))
    fx = Art()
    chars_in(cv, fx, '革囊渡江', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=70)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 5 else CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    if ph >= 5:
        note_in(cv, '姚枢以宋初曹彬下江南不杀一人进言', t, s0 + 5 * P)

def art_k_kaiping(A, cv, t, u):
    q = ease_out(u / (2.5 * P))
    city_wall(A, 540 - 380 * q, 540 + 380 * q, 1080, gate_x=540, label='开平' if q > 0.5 else None, layer='mid', open_=1.0)
    ground(A, GROUND)
    person(A, 140, GROUND, 170, dir=1, robe=True, hat='knot', arm=110, layer='caoyuan')
    A.flush(cv)
    paste(cv, text_img('刘秉忠选址 · 营建开平城 后称上都', SERIF, 44, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_nanzheng(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 280), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    for j in range(4):
        rider(A, lerp(-100, 700, ease_out(u / (3 * P))) - j * 140, GROUND, 120, dir=1, ph=t * 6 + j, layer='caoyuan' if j == 0 else 'ink', spear=True)
    A.flush(cv)
    paste(cv, text_img('蒙哥亲征四川 · 忽必烈进攻鄂州', SERIF, 44, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_diaoyu(A, cv, t, u):
    A.d['mid'].polygon([(240, GROUND), (420, 1040), (660, 1040), (840, GROUND)], fill=200)
    city_wall(A, 400, 680, 1000, label='钓鱼城', layer='mid')
    A.d['ocean'].rectangle((60, GROUND - 40, W - 60, GROUND + 40), fill=150)
    ground(A, GROUND)
    yurt(A, 160, GROUND - 40, 140, 100, layer='mid')
    A.flush(cv)
    paste(cv, text_img('蒙哥汗卒于合州钓鱼城下', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '一说中炮石受伤 一说染疫而亡', t, t - u + P)

def art_k_beigui(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 360
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    for j in range(3):
        rider(A, lerp(900, 100, ((t * 0.1 + j / 3) % 1)), GROUND, 120, dir=-1, ph=t * 6 + j, layer='caoyuan' if j == 0 else 'ink')
    A.flush(cv)
    paste(cv, text_img('贾似道遣使议和 · 忽必烈星夜北归', SERIF, 44, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '贾似道隐瞒议和 向朝廷谎报大捷', t, t - u + P)

def art_k_khans(A, cv, t, u):
    """6-beat set piece: 汗位之争 — two kurultai, two khans: 忽必烈 at 开平, 阿里不哥 at 和林; four years of war; 1264 the younger brother submits."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        yurt(A, 260, GROUND, 260, 180, layer='jinzhang')
        yurt(A, 820, GROUND, 260, 180, layer='mid')
        kub(A, 420, GROUND, 180, dir=1, arm=lerp(-8, 120, clamp(ph / 0.6)))
        person(A, 660, GROUND, 180, dir=-1, robe=True, hat='helmet', arm=lerp(-8, 120, clamp((ph - 1) / 0.6)), layer='ink')
        A.flush(cv)
        lab, col = '开平 忽必烈称汗 · 和林 阿里不哥亦称汗', CAOYUAN
    elif ph < 4:
        army(A, lerp(-100, 300, clamp((ph - 2) / 1.5)), GROUND, 5, dir=1, layer='caoyuan', t=t, march=True, h=100)
        army(A, lerp(1180, 780, clamp((ph - 2) / 1.5)), GROUND, 5, dir=-1, layer='ink', t=t, march=True, h=100)
        A.flush(cv)
        lab, col = '兄弟相争 四年', ZHU
    else:
        kub(A, 420, GROUND, 190, dir=1, arm=60)
        person(A, 680, GROUND, 150, dir=-1, robe=True, hat='helmet', kneel=True, bow=30, layer='ink')
        A.flush(cv)
        lab, col = '阿里不哥兵败归降', CAOYUAN
    paste(cv, text_img(lab, SERIF, 42, col, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    note_in(cv, '此后蒙古四大汗国渐行渐远', t, t - u + 4 * P)

# ================================================================ 第三回 大哉乾元
def art_k_zhongtong(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='jinzhang')
    ground(A, GROUND)
    kub(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('开平即位 · 建元中统 时年四十六', SERIF, 44, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('中统', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '蒙古大汗首次使用汉式年号', t, t - u + P)

def art_k_chao(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        banknote(A, 300 + k * 240, 1150 + 20 * (k % 2), 100)
    A.flush(cv)
    paste(cv, text_img('发行中统元宝交钞 · 以丝银为本', SERIF, 44, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '马可波罗游记惊叹以纸为币', t, t - u + P)

def art_k_dadu(A, cv, t, u):
    q = ease_out(u / (3 * P))
    A.d['mid'].rectangle((200, 900, 880, 1300), fill=60)
    A.d['ink'].rectangle((200, 900, 880, 1300), outline=255, width=6)
    A.d['jinzhang'].line((540, 900, 540, 900 + 400 * q), fill=255, width=8)
    for k in range(int(q * 6)):
        A.d['mid'].rectangle((260 + (k % 3) * 220, 960 + (k // 3) * 180, 380 + (k % 3) * 220, 1060 + (k // 3) * 180), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('营建大都 · 中轴对称 前朝后市', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('大都', 56), 860, 1440, t, t - u + P, rot=6)

def art_k_basiba(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='jinzhang')
    person(A, 260, GROUND, 170, dir=1, robe=True, hat='none', kneel=True, arm=100, layer='mid')
    scroll(A, 560, GROUND - 160, 300, 120, ease_out(u / (1.5 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('帝师八思巴创制新字 · 颁行天下', SERIF, 44, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('国字', 56), 860, 1020, t, t - u + P, rot=6)

def art_k_dayuan(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='jinzhang')
    ground(A, GROUND)
    scroll(A, 540, 1060, 420, 140, ease_out(u / (1.0 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('大哉乾元', SERIF, 56, INK, 'Black', bleed=False, spacing=10), W / 2, 1060, 1, clamp((u - 0.6) / 0.4))
    paste(cv, text_img('取易经之义 · 定国号为大元', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_xiangyang(A, cv, t, u):
    """6-beat set piece: 襄阳之战 — five years of siege across the Han river; Persian engineers build the 回回炮;
    150-catty stones crack the towers; 吕文焕 surrenders."""
    ph = u / P
    city_wall(A, 520, 1000, 1060, gate_x=760, label='襄阳', layer='mid', open_=1.0 if ph >= 4.5 else 0.0)
    A.d['ocean'].rectangle((60, GROUND - 30, W - 60, GROUND + 40), fill=140)
    ground(A, GROUND)
    if ph < 2:
        army(A, 60, GROUND, 4, dir=1, layer='caoyuan', t=t, march=False, h=90)
        lab = f'围城 · 第{cn_num(min(5, int(ph / 0.4) + 1))}年'
    else:
        sw = clamp(((ph - 2) % 1.0) / 0.4)
        trebuchet(A, 220, GROUND, 200, sw, layer='ink')
        if sw >= 1:
            q = clamp(((ph - 2) % 1.0 - 0.4) / 0.4)
            sx = lerp(260, 700, q); sy = lerp(GROUND - 260, 1060, q) - 200 * math.sin(math.pi * q)
            A.d['ink'].ellipse((sx - 16, sy - 16, sx + 16, sy + 16), fill=255)
        if ph > 3:
            flames(A, 700, 1060, 160, 120 * clamp((ph - 3) / 1), t, n=3, seed=1273, smoke=True)
        lab = '回回炮 · 石重一百五十斤' if ph < 4.5 else '吕文焕出降'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '襄樊之战前后近六年 襄阳失则南宋门户洞开', t, t - u + P)

def art_k_linan(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for j in range(4):
        person(A, 300 + j * 90, GROUND, 140, dir=1, robe=True, hat='knot', kneel=True, bow=30, layer='ink')
    person(A, 780, GROUND, 190, dir=-1, robe=False, hat='helmet', arm=60, layer='caoyuan')
    A.flush(cv)
    paste(cv, text_img('伯颜兵临临安 · 谢太后奉表出降', SERIF, 44, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 四海
def art_k_yashan(A, cv, t, u):
    """6-beat set piece: 崖山 — the Song fleet chained together at sea; fire and the Yuan attack; 陆秀夫 leaps into the sea carrying the boy emperor."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1080, W - 60, GROUND + 40), fill=180)
    waves(A, 1090, t, rows=3, amp=6)
    for k in range(6):
        boat(A, 140 + k * 160, 1110 + 6 * math.sin(t * 2 + k), 60, t)
    A.d['ink'].line((120, 1120, 960, 1120), fill=200, width=4)
    if ph > 1.5:
        flames(A, 540, 1100, 500, 160 * clamp((ph - 1.5) / 1), t, n=6, seed=1279, smoke=True)
    if ph > 3.5:
        q = clamp((ph - 3.5) / 1.2)
        person(A, 800, lerp(1090, 1260, q), 150, dir=1, robe=True, hat='knot', load=True, arm=160, fall=lerp(0, 60, q), layer='ink')
    A.flush(cv)
    lab = '南宋最后的船队 · 千舟连锁' if ph < 1.5 else ('元军火攻 · 海战一日' if ph < 3.5 else '陆秀夫负幼帝投海')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 1.5 else CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '史载随之赴海者甚众 此即宋朝终章', t, t - u + 3.5 * P)

def art_k_unify(A, cv, t, u):
    q = ease_out(u / (3 * P))
    A.d['caoyuan'].ellipse((540 - 360, 1080 - 240, 540 + 360, 1080 + 240), fill=int(200 * q))
    A.d['ink'].ellipse((540 - 360, 1080 - 240, 540 + 360, 1080 + 240), outline=200, width=4)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('结束三百余年南北分立', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('一统', 56), 860, 1440, t, t - u + P, rot=6)

def art_k_shoushi(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 360
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    A.d['mid'].rectangle((420, GROUND - 260, 660, GROUND), fill=220)
    A.d['ink'].rectangle((380, GROUND - 280, 700, GROUND - 260), fill=255)
    person(A, 540, GROUND - 280, 120, dir=1, robe=True, hat='knot', arm=140, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('郭守敬编授时历 · 一年三百六十五日二四二五', SERIF, 40, CAOYUAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '与今日公历一年之长相同', t, t - u + P)

def art_k_typhoon(A, cv, t, u):
    """6-beat set piece: 弘安之役 — a vast fleet crosses to Japan; a typhoon rises; the ships founder."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1060, W - 60, GROUND + 40), fill=170 + int(60 * clamp((ph - 2) / 1)))
    storm = clamp((ph - 2) / 1.5)
    waves(A, 1070, t, rows=3, amp=4 + 30 * storm)
    if storm > 0:
        for k in range(40):
            q = (t * 2.5 + k / 40) % 1
            x = 80 + (k * 53) % 920
            A.d['wash'].line((x + 60 * q, lerp(620, 1300, q), x + 60 * q - 20, lerp(620, 1300, q) + 30), fill=int(160 * storm), width=2)
    n = 7 if ph < 4 else max(0, 7 - int((ph - 4) / 0.25))
    for k in range(n):
        boat(A, 120 + k * 135, 1090 + 30 * storm * math.sin(t * 4 + k), 55, t)
    A.flush(cv)
    lab = '十余万大军 · 渡海东征' if ph < 2 else ('台风骤起' if ph < 4 else '舟师覆没 · 生还者十之一二')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '首次东征在1274年 亦无功而返', t, t - u + P)

def art_k_zhenjin(A, cv, t, u):
    ground(A, GROUND)
    yurt(A, 760, GROUND, 300, 200, layer='mid')
    kub(A, 380, GROUND, 190, dir=1, bow=25, arm=-8, old=0.7)
    A.flush(cv)
    paste(cv, text_img('皇后察必 太子真金相继去世', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '晚年借酒消愁 体衰多病', t, t - u + P)

def art_k_naiyan(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    ex = lerp(-100, 520, ease_out(u / (3 * P)))
    elephant(A, ex, GROUND, 200, dir=1, ph=t * 3, layer='mid')
    A.d['jinzhang'].rectangle((ex - 70, GROUND - 330, ex + 50, GROUND - 260), fill=255)
    kub(A, ex - 10, GROUND - 260, 100, dir=1, arm=60, old=0.9)
    A.flush(cv)
    paste(cv, text_img('七十三岁 · 乘象舆亲征乃颜', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('象舆', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第五回 元世祖
def art_k_tonghui(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=160)
    waves(A, 1170, t, rows=2, amp=3)
    for k in range(8):
        boat(A, ((k * 140 + t * 40) % 1100) - 40, 1190 + (k % 2) * 40, 45, t, sail=k % 2 == 0)
    low_wall(A, 120, 960, 1060, 1160)
    A.flush(cv)
    paste(cv, text_img('郭守敬开通惠河 · 漕船直入大都', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '见积水潭舳舻蔽水 大悦', t, t - u + P)

def art_k_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    kub(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于大都紫檀殿 · 年八十', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_burial(A, cv, t, u):
    ground(A, GROUND)
    for j in range(8):
        horse(A, lerp(1100, -100, ((t * 0.05 + j / 8) % 1)), GROUND - 4 * (j % 2), 90, dir=-1, ph=t * 5 + j, layer='mid')
    A.flush(cv)
    paste(cv, text_img('葬于漠北起辇谷 · 不封不树', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '元帝陵墓所在 至今未被发现', t, t - u + P)

def art_k_xingsheng(A, cv, t, u):
    ground(A, GROUND)
    n = min(11, int(clamp(u / (2.5 * P)) * 11) + 1)
    for i in range(n):
        x = 220 + (i % 4) * 210; y = 940 + (i // 4) * 130
        A.d['caoyuan' if i % 2 else 'jinzhang'].rectangle((x - 80, y - 50, x + 80, y + 50), fill=200)
    A.flush(cv)
    paste(cv, text_img('首创行省制度 · 省之名沿用至今', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '元设中书省及十一行省', t, t - u + P)

def art_k_fall(A, cv, t, u):
    palace(A, 540, 1300, 320, collapse=clamp(u / (3 * P)) * 0.6, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('元朝定国号至北退 · 不足百年', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_beijing(A, cv, t, u):
    A.d['mid'].rectangle((240, 900, 840, 1300), fill=60)
    A.d['ink'].rectangle((240, 900, 840, 1300), outline=255, width=6)
    A.d['jinzhang'].line((540, 900, 540, 1300), fill=255, width=8)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('北京城的格局 · 奠基于元大都', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_k_final(A, cv, t, u):
    yurt(A, 320, GROUND, 220, 150, layer='mid')
    palace(A, 720, 1300, 220, layer='jinzhang')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('马背上得天下 · 以汉法治天下', SERIF, 46, CAOYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_k_legacy(A, cv, t, u):
    yurt(A, 860, 1380, 80, 60, layer='jinzhang')

def art_k_title(A, cv, t, u):
    yurt(A, 820, 1440, 220, 150, layer='jinzhang')
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    kub(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '黄金家族'), 48: ('第二回', '革囊渡江'), 80: ('第三回', '大哉乾元'),
            112: ('第四回', '四海'), 144: ('第五回', '元世祖')}

CARDS = [
    C(0, 2, 'empire', 'num', num='一座大都', line='就是今天的北京', art=art_k_hook_dadu),
    C(2, 4, 'works', 'num', num='一张纸币', line='通行整个帝国', art=art_k_hook_note),
    C(4, 6, 'war', 'num', num='两次东征', line='都败给了风暴', art=art_k_hook_storm),
    C(6, 8, 'court', 'num', num='一个国号', line='取自易经', art=art_k_hook_seal),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 黄金家族
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1215, main='生于草原', sub='拖雷之子', art=art_k_birth),
    C(22, 26, 'war', 'card', year=1224, main='少年首猎', sub='祖父抹指', art=art_k_hunt),
    C(26, 30, 'death', 'card', year=1232, main='父亲去世', sub='拖雷', art=art_k_father),
    C(30, 34, 'fate', 'card', year=1236, main='邢州封地', sub='百姓逃散', art=art_k_xingzhou),
    C(34, 40, 'court', 'card', year=1244, main='延揽汉儒', sub='问以治道', art=art_k_mufu),
    C(40, 44, 'empire', 'card', year=1251, main='总领漠南', sub='兄长蒙哥即位', art=art_k_monan),
    C(44, 48, 'works', 'card', year=1251, main='试行汉法', sub='邢州大治', art=art_k_hanfa),
    # ---- 第二回 革囊渡江
    C(48, 50, 'war', 'chapter'),
    C(50, 58, 'war', 'gelang', year=1253),
    C(58, 62, 'works', 'card', year=1256, main='营建开平', sub='后称上都', art=art_k_kaiping),
    C(62, 66, 'war', 'card', year=1258, main='分路伐宋', sub='兵锋南指', art=art_k_nanzheng),
    C(66, 70, 'death', 'card', year=1259, main='蒙哥之死', sub='钓鱼城下', art=art_k_diaoyu),
    C(70, 74, 'night', 'card', year=1259, main='星夜北归', sub='鄂州议和', art=art_k_beigui),
    C(74, 80, 'fate', 'card', year=1260, main='两个大汗', sub='兄弟相争', art=art_k_khans),
    # ---- 第三回 大哉乾元
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'empire', 'card', year=1260, main='建元中统', sub='汉式年号', art=art_k_zhongtong),
    C(86, 90, 'works', 'card', year=1260, main='中统宝钞', sub='纸币通行', art=art_k_chao),
    C(90, 94, 'court', 'card', year=1267, main='营建大都', sub='刘秉忠规划', art=art_k_dadu),
    C(94, 98, 'night', 'card', year=1269, main='八思巴字', sub='国字', art=art_k_basiba),
    C(98, 102, 'empire', 'card', year=1271, main='国号大元', sub='大哉乾元', art=art_k_dayuan),
    C(102, 108, 'war', 'card', year=1273, main='襄阳之战', sub='回回炮', art=art_k_xiangyang),
    C(108, 112, 'court', 'card', year=1276, main='临安受降', sub='南宋投降', art=art_k_linan),
    # ---- 第四回 四海
    C(112, 114, 'night', 'chapter'),
    C(114, 120, 'death', 'card', year=1279, main='崖山', sub='宋亡', art=art_k_yashan),
    C(120, 124, 'empire', 'card', year=1279, main='天下一统', sub='南北归一', art=art_k_unify),
    C(124, 128, 'night', 'card', year=1280, main='授时历', sub='郭守敬', art=art_k_shoushi),
    C(128, 134, 'war', 'card', year=1281, main='东征日本', sub='台风', art=art_k_typhoon),
    C(134, 138, 'death', 'card', year=1285, main='晚年丧子', sub='太子真金', art=art_k_zhenjin),
    C(138, 144, 'war', 'card', year=1287, main='象舆亲征', sub='乃颜之乱', art=art_k_naiyan),
    # ---- 第五回 元世祖
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'works', 'card', year=1293, main='通惠河', sub='舳舻蔽水', art=art_k_tonghui),
    C(150, 154, 'death', 'card', year=1294, main='忽必烈去世', sub='年八十', art=art_k_death),
    C(154, 158, 'fate', 'card', year=1294, main='起辇谷', sub='不封不树', art=art_k_burial),
    C(158, 162, 'court', 'card', year=1294, main='行省制度', sub='沿用至今', art=art_k_xingsheng),
    C(162, 166, 'death', 'card', year=1368, main='元朝北退', sub='不足百年', art=art_k_fall),
    C(166, 168, 'works', 'card', year=1368, main='大都', sub='今日北京', art=art_k_beijing),
    C(168, 170, 'end', 'card', year=1368, main='马背与汉法', sub='元世祖', art=art_k_final),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='柒拾', col=CAOYUAN, acc=JINZHANG, born=1215, died=1294, age0=1214,
    born_lab='1215年', died_lab='1294年', years_txt='公元1215 — 1294',
    hook_q='他是成吉思汗的孙子 · 为什么要做中原的皇帝？',
    name_line='忽必烈 · 元世祖', name='忽必烈', seal='薛禅', title_art=art_k_title,
    q1='一代雄主？', q2='马上天子？',
    end_art=art_k_legacy, end_big='大哉乾元', end_seal='薛禅',
    end_l1='他在马背上打下天下', end_l2='又用汉法坐稳了天下',
    end_brush='天下一统', end_ask='如果你是忽必烈 汉法和祖制怎么选？评论区聊聊', next='李时珍'),
    scenes=dict(chapter=scene_chapter, gelang=scene_gelang))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
