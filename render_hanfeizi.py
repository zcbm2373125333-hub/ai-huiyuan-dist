"""千古人物志 · 第玖拾伍集 · 韩非子 (约前280–前233)
Look: 铁青 + 竹简黄, little bronze-weight (秦权) corners, the walls of a small state behind.
Chapter card: 法 术 势 — a black lacquer frame; the three words appear one per chapter; in the last chapter a 秦 seal is pressed beneath.
Set pieces: custom 8-beat scene 'ruqin' (入秦而死), 6-beat 寓言, 6-beat 逆鳞, 6-beat 一统.
Birth year is approximate (no_age); death year 233 BC is recorded.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_mozi as Mo            # engine + helpers (previous episode)
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
from render_lisi import li, emperor as qinwang
from render_mengtian import soldier
from render_sunwu import army, banner

F.RIPPLE = False
TIEQING = (72, 86, 98)              # 铁青
ZHUJIAN = (196, 164, 96)            # 竹简黄
S.LAYERS.append(('tieqing', TIEQING, 0.9, 1.0))
S.LAYERS.append(('zhujian', ZHUJIAN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='法', life='韩', court='术', night='孤', war='秦', empire='势', works='书', fate='难', death='狱', end='法')
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
G.THEMES['empire']['sun'] = (TIEQING, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (ZHUJIAN, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _x in (60, 900):                # low rammed-earth walls at the margins
    _d.rectangle((_x, 1360, _x + 120, 1420), fill=(120, 110, 96, 60))
    for _k in range(4):
        _d.rectangle((_x + _k * 32, 1344, _x + _k * 32 + 18, 1360), fill=(120, 110, 96, 60))
for _k in range(3):
    _d.line((200, 1424 + _k * 12, 880, 1424 + _k * 12), fill=TIEQING + (40 - _k * 10,), width=2)
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 64), 'war': (110, 64, 50), 'fate': (92, 96, 102)}
def draw_background(t, theme):
    """韩国: hard grey hills, rammed-earth walls at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(192, 194, 196), (160, 164, 170), MTN_COL.get(theme, (100, 110, 120))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """秦权: a bell-shaped bronze weight in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=TIEQING + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=TIEQING + (220,), width=3)
        cx, cy = x + sx * 52, y + sy * 52
        d.polygon([(cx - 20, cy + 18), (cx + 20, cy + 18), (cx + 12, cy - 10), (cx - 12, cy - 10)], fill=ZHUJIAN + (230,))
        d.ellipse((cx - 8, cy - 24, cx + 8, cy - 8), outline=(90, 80, 60, 230), width=3)

# ================================================================ primitives
def han_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, **kw):
    """韩非: a young prince of Han — tall cap, iron-blue robe; a scholar who stammers and so writes."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if kw.get('fall'):
        return hand
    if up:
        A.d[layer].rectangle((x - 0.04 * h, y - 1.16 * h, x + 0.04 * h, y - 0.94 * h), fill=255)
        A.d[layer].line((x - 0.1 * h, y - 1.0 * h, x + 0.1 * h, y - 1.0 * h), fill=255, width=max(2, int(0.012 * h)))
    top = y - (0.48 if kneel else 0.76) * h
    A.d['tieqing'].polygon([(x - 0.1 * h, top), (x + 0.1 * h, top), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=170)
    return hand

def stump(A, x, base, s):
    A.d['ink'].polygon([(x - 0.5 * s, base), (x + 0.5 * s, base), (x + 0.4 * s, base - 0.7 * s), (x - 0.4 * s, base - 0.7 * s)], fill=255)
    A.d['zhujian'].ellipse((x - 0.4 * s, base - 0.78 * s, x + 0.4 * s, base - 0.62 * s), fill=255)

def rabbit(A, x, y, s, dir=1, layer='mid', down=False):
    d = A.d[layer]
    if down:
        d.ellipse((x - 0.5 * s, y - 0.3 * s, x + 0.5 * s, y), fill=255)
        d.ellipse((x + dir * 0.4 * s - 0.2 * s, y - 0.25 * s, x + dir * 0.4 * s + 0.2 * s, y), fill=255)
        return
    d.ellipse((x - 0.45 * s, y - 0.5 * s, x + 0.35 * s, y), fill=255)
    d.ellipse((x + dir * 0.35 * s - 0.2 * s, y - 0.75 * s, x + dir * 0.35 * s + 0.2 * s, y - 0.4 * s), fill=255)
    for k in (0, 1):
        ex = x + dir * (0.3 + 0.1 * k) * s
        d.polygon([(ex - 0.05 * s, y - 0.7 * s), (ex + 0.05 * s, y - 0.7 * s), (ex + dir * 0.05 * s, y - 1.15 * s)], fill=255)

def dragon(A, cx, cy, s, t, layer='tieqing', scale=0.0):
    """龙: a sinuous body of overlapping discs; `scale` > 0 lights one reversed scale under the throat."""
    for k in range(16):
        f = k / 15
        x = cx - s + 2 * s * f; y = cy + 0.25 * s * math.sin(f * 7 + t * 2)
        r = (0.16 - 0.08 * f) * s if k else 0.2 * s
        A.d[layer].ellipse((x - r, y - r, x + r, y + r), fill=255)
    hx, hy = cx - s, cy + 0.25 * s * math.sin(t * 2)
    A.d['ink'].polygon([(hx - 0.3 * s, hy - 0.05 * s), (hx, hy - 0.18 * s), (hx + 0.05 * s, hy + 0.15 * s), (hx - 0.25 * s, hy + 0.12 * s)], fill=255)
    A.d['ink'].line((hx - 0.05 * s, hy - 0.16 * s, hx + 0.1 * s, hy - 0.4 * s), fill=255, width=4)
    if scale > 0:
        A.d['red'].polygon([(hx + 0.08 * s, hy + 0.18 * s), (hx + 0.18 * s, hy + 0.1 * s), (hx + 0.16 * s, hy + 0.26 * s)], fill=int(255 * scale))

def frame3(A, cv, cx, cy, s, n, q=1.0, qin=0.0, t=0.0):
    A.d['ink'].rectangle((cx - s, cy - 0.5 * s, cx + s, cy + 0.5 * s), outline=255, width=10)
    A.d['tieqing'].rectangle((cx - s + 14, cy - 0.5 * s + 14, cx + s - 14, cy + 0.5 * s - 14), fill=90)
    A.flush(cv)
    for i, ch in enumerate('法术势'):
        if i < n:
            a = 1.0 if i < n - 1 else q
            paste(cv, text_img(ch, SERIF, int(0.42 * s), INK, 'Black', bleed=False), cx - 0.62 * s + i * 0.62 * s, cy, 1, a)
    if qin > 0:
        stamp(cv, seal('秦', int(0.3 * s), ZHU), cx + 0.8 * s, cy + 0.55 * s, t, t - 0.01 - (1 - qin))

# ================================================================ chapter card
CH = {16: 0, 48: 1, 80: 2, 112: 3, 144: 3}
def art_fa_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = CH.get(kb, 1)
    q = ease_out(u / (1.2 * P))
    frame3(A, cv, 540, 1060, 300, n, q=clamp((q - 0.2) / 0.5), qin=1.0 if (kb == 144 and q > 0.5) else 0.0, t=t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_fa_chapter)
    ink_in(cv, text_img(no, SERIF, 56, TIEQING, 'Black', bleed=False, spacing=12), W / 2, 1320, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1445, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_h_hook_mouth(A, cv, t, u):
    ground(A, GROUND)
    han_(A, 540, GROUND, 300, dir=1, arm=-8)
    A.flush(cv)
    for k in range(3):
        a = clamp((u - k * 0.3 * P) / 0.2)
        paste(cv, text_img('我…', SERIF, 50, TIEQING, 'Black', bleed=False), 760 + k * 40, 980 - k * 60, 1, a * (1 - 0.3 * k))

def art_h_hook_king(A, cv, t, u):
    ground(A, GROUND)
    qinwang(A, 540, GROUND, 280, dir=1, arm=lerp(-8, 80, clamp(u / P)))
    slips(A, 680, GROUND - 160, 8, 120, layer='zhujian', tied=False)

def art_h_hook_cup(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].polygon([(470, GROUND - 160), (610, GROUND - 160), (580, GROUND - 40), (500, GROUND - 40)], fill=255)
    A.d['ink'].rectangle((530, GROUND - 40, 550, GROUND - 10), fill=255)
    A.d['ink'].rectangle((480, GROUND - 14, 600, GROUND), fill=255)
    A.d['red'].ellipse((490, GROUND - 168, 590, GROUND - 148), fill=200)

def art_h_hook_rabbit(A, cv, t, u):
    ground(A, GROUND)
    stump(A, 540, GROUND, 120)
    rabbit(A, lerp(900, 600, clamp(u / P)), GROUND, 90, dir=-1, down=u > P)

# ================================================================ 第一回 公子
def art_h_birth(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('生为韩国公子', SERIF, 52, TIEQING, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '生年不详 约在前280年前后', t, t - u + P)

def art_h_weak(A, cv, t, u):
    ground(A, GROUND)
    for k in range(7):
        x = 160 + k * 125
        A.d['tieqing' if k == 2 else 'mid'].rectangle((x - 50, GROUND - (80 if k == 2 else 160 + 40 * (k == 6)), x + 50, GROUND), fill=200)
    A.flush(cv)
    paste(cv, text_img('韩国是七国中最弱的一个', SERIF, 48, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '紧挨着强秦', t, t - u + P)

def art_h_stammer(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 420, layer='mid')
    han_(A, 300, GROUND, 180, dir=1, kneel=True, arm=100)
    slips(A, 460, GROUND - 74, 10, 70, layer='zhujian', tied=False)
    A.flush(cv)
    paste(cv, text_img('为人口吃 不能道说 而善著书', SERIF, 46, TIEQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '史记 老子韩非列传', t, t - u + P)

def art_h_xunzi(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 210, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
    han_(A, 300, GROUND, 180, dir=1, kneel=True, arm=-8)
    li(A, 480, GROUND, 180, dir=1, kneel=True, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('与李斯同拜荀子为师', SERIF, 50, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '荀子主张人性本恶', t, t - u + P)

def art_h_lisi(A, cv, t, u):
    ground(A, GROUND)
    li(A, 380, GROUND, 200, dir=1, arm=-8)
    han_(A, 700, GROUND, 200, dir=-1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('李斯自认为不如韩非', SERIF, 50, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_h_return(A, cv, t, u):
    palace(A, 760, 1300, 240, layer='mid')
    ground(A, GROUND)
    han_(A, lerp(200, 560, ease_out(u / (3 * P))), GROUND, 190, dir=1, ph=t * 2, arm=-8)
    A.flush(cv)
    paste(cv, text_img('学成回到韩国', SERIF, 52, TIEQING, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 孤愤
def art_h_jian(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='crown', arm=-8, layer='ink')
    han_(A, 340, GROUND, 180, dir=1, kneel=True, bow=20, arm=80)
    A.flush(cv)
    paste(cv, text_img('屡次上书劝谏韩王 不被采纳', SERIF, 46, TIEQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_gufen(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 420, layer='mid')
    han_(A, 300, GROUND, 180, dir=1, kneel=True, arm=lerp(95, 110, 0.5 + 0.5 * math.sin(t * 5)))
    lamp(A, 760, GROUND - 74, 28, t, glow=0.9)
    n = int(clamp(u / (3 * P)) * 20)
    for i in range(n):
        slips(A, 120 + i * 20, GROUND - 200 - (i % 2) * 6, 1, 110, layer='zhujian', tied=False)
    A.flush(cv)
    paste(cv, text_img('愤而著书 孤愤 五蠹 说难', SERIF, 48, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '共十余万言 后人辑为韩非子', t, t - u + P)

def art_h_fables(A, cv, t, u):
    """6-beat set piece: 寓言 — 守株待兔 (a farmer waits by the stump for another rabbit while weeds grow), then 自相矛盾."""
    ph = u / P
    ground(A, GROUND)
    if ph < 3:
        stump(A, 600, GROUND, 120)
        rabbit(A, lerp(960, 680, clamp(ph / 0.8)), GROUND, 90, dir=-1, down=ph > 0.8)
        person(A, 380, GROUND, 180, dir=1, robe=False, hat='knot', kneel=ph > 1.6, arm=-8, layer='ink')
        if ph > 1.6:
            for k in range(14):
                x = 120 + k * 64
                A.d['grass'].line((x, GROUND, x + 6, GROUND - 60 * clamp((ph - 1.6) / 1.2)), fill=230, width=4)
        lab, col = '守株待兔', TIEQING
    else:
        person(A, 540, GROUND, 200, dir=1, robe=False, hat='knot', arm=60, layer='ink', spear=True)
        A.d['mid'].ellipse((640, GROUND - 200, 740, GROUND - 60), fill=255)
        A.d['ink'].ellipse((640, GROUND - 200, 740, GROUND - 60), outline=255, width=4)
        lab, col = '自相矛盾', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 56, col, 'Black', bleed=False, spacing=12), W / 2, 760, 1, 1)
    note_in(cv, '郑人买履 滥竽充数 也都出自此书', t, t - u + 3 * P)

def art_h_wudu(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        x = 200 + k * 170
        A.d['ink'].ellipse((x - 30, GROUND - 40, x + 30, GROUND - 10), fill=255)
        A.d['ink'].line((x - 30, GROUND - 25, x - 60, GROUND - 40), fill=255, width=3)
    A.flush(cv)
    paste(cv, text_img('五蠹 世异则事异 事异则备变', SERIF, 46, TIEQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '时代变了 办法也要变', t, t - u + P)

def art_h_fashushi(A, cv, t, u):
    frame3(A, cv, 540, 1120, 280, 3, q=1.0)
    paste(cv, text_img('集法 术 势于一身', SERIF, 50, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '法家集大成者', t, t - u + P)

def art_h_nilin(A, cv, t, u):
    """6-beat set piece: 逆鳞 — a dragon can be tamed and ridden, but under its throat is one reversed scale; touch it and it kills."""
    ph = u / P
    dragon(A, 600, 1120, 360, t, scale=clamp((ph - 2) / 0.6))
    ground(A, GROUND)
    A.flush(cv)
    if ph < 2:
        lab, col = '龙可以驯服 可以骑', TIEQING
    elif ph < 4:
        lab, col = '喉下有逆鳞 触之必杀人', ZHU
    else:
        lab, col = '人主亦有逆鳞', ZHU
    paste(cv, text_img(lab, SERIF, 50, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '韩非子 说难 讲游说君主之难', t, t - u + P)

# ================================================================ 第三回 入秦
def art_h_qinread(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    qinwang(A, 540, GROUND, 220, dir=1, arm=100)
    A.flush(cv)
    paste(cv, text_img('秦王嬴政读到孤愤 五蠹', SERIF, 48, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('得见此人与之游 死不恨矣', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_h_attack(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='韩', layer='mid')
    ground(A, GROUND)
    army(A, 40, GROUND, 8, dir=1, t=t, march=True, h=110)
    A.flush(cv)
    paste(cv, text_img('秦军急攻韩国', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def scene_ruqin(cv, t, c, k):
    """8-beat custom scene: 入秦 — sent to Qin as envoy; the king is pleased; 李斯 and 姚贾 slander him; prison; poison;
    the king relents and sends a pardon — too late."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    if ph < 2:
        palace(A, 540, 1300, 300, layer='mid')
        qinwang(A, 760, GROUND, 210, dir=-1, arm=60)
        han_(A, 340, GROUND, 190, dir=1, bow=20, arm=-8)
        lab, col = '奉韩王之命 出使秦国', TIEQING
    elif ph < 4:
        palace(A, 540, 1300, 300, layer='mid')
        qinwang(A, 760, GROUND, 210, dir=-1, arm=-8)
        li(A, 520, GROUND, 190, dir=1, bow=20, arm=80, layer='ink')
        person(A, 360, GROUND, 180, dir=1, robe=True, hat='knot', bow=20, arm=60, layer='mid')
        lab, col = '李斯 姚贾进谗 终为韩不为秦', ZHU
    elif ph < 6:
        for kk in range(7):
            A.d['ink'].rectangle((300 + kk * 70, GROUND - 400, 312 + kk * 70, GROUND), fill=255)
        A.d['ink'].rectangle((290, GROUND - 410, 800, GROUND - 396), fill=255)
        han_(A, 560, GROUND, 180, dir=1, kneel=True, bow=20 if ph > 5 else 0, arm=60)
        if ph > 4.5:
            A.d['ink'].polygon([(640, GROUND - 60), (700, GROUND - 60), (690, GROUND - 10), (650, GROUND - 10)], fill=255)
        lab, col = '下狱 李斯派人送去毒药', ZHU
    else:
        A.d['ink'].rectangle((300, GROUND - 400, 312, GROUND), fill=255)
        person(A, lerp(-80, 460, clamp((ph - 6) / 1.5)), GROUND, 180, dir=1, ph=t * 6, robe=False, hat='knot', arm=80, layer='mid')
        han_(A, 720, GROUND - 20, 200, dir=1, fall=-88, arm=-8)
        lab, col = '秦王后悔 赦令到时 他已死去', ZHU
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '入秦', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=95)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '欲自陈 不得见', t, s0 + 4 * P)

def art_h_sima(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('余独悲韩子\n为说难而不能自脱耳', SERIF, 36, INK, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('司马迁为他叹息', SERIF, 50, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_h_irony(A, cv, t, u):
    ground(A, GROUND)
    dragon(A, 600, 1080, 300, t, scale=1.0)
    A.flush(cv)
    paste(cv, text_img('写尽了游说之难 自己却没能躲过', SERIF, 44, ZHU, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))

# ================================================================ 第四回 一统
def art_h_hanfall(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='韩', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(3):
        banner(A, 260 + k * 280, 1080, 150, t, layer='mid', fallen=clamp((u - k * 0.3 * P) / P))
    A.flush(cv)
    paste(cv, text_img('他死后三年 韩国被秦所灭', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '六国中第一个灭亡', t, t - u + P)

def art_h_unify(A, cv, t, u):
    """6-beat set piece: 一统 — six walls fall one by one; one Qin banner over them all."""
    ph = u / P
    ground(A, GROUND)
    n = min(6, int(ph / 0.8) + 1)
    for i in range(6):
        x = 150 + i * 156
        fallen = i < n
        A.d['mid'].rectangle((x - 55, GROUND - (40 if fallen else 160), x + 55, GROUND), fill=200)
    if ph >= 5:
        banner(A, 540, GROUND - 40, 380, t, layer='ink')
    A.flush(cv)
    lab = '韩 赵 魏 楚 燕 齐 相继灭亡'[: 2 + 2 * n] if ph < 5 else '秦统一天下'
    paste(cv, text_img(lab, SERIF, 50, TIEQING if ph < 5 else ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '秦以韩非的学说治国', t, t - u + 3 * P)

def art_h_law(A, cv, t, u):
    ground(A, GROUND)
    slips(A, 300, GROUND, 24, 260, layer='zhujian')
    A.flush(cv)
    paste(cv, text_img('以法为教 以吏为师', SERIF, 52, TIEQING, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '语出韩非子 五蠹', t, t - u + P)

def art_h_lisi_end(A, cv, t, u):
    ground(A, GROUND)
    li(A, 540, GROUND, 210, dir=1, kneel=True, bow=30, arm=-8)
    A.flush(cv)
    paste(cv, text_img('二十五年后 李斯也死于狱中', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '被赵高诬陷 腰斩于咸阳', t, t - u + P)

def art_h_qinfall(A, cv, t, u):
    palace(A, 540, 1300, 320, collapse=clamp(u / (2 * P)), layer='mid')
    flames(A, 540, 1200, 560, 200, t, n=5, seed=206, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('秦二世而亡', SERIF, 54, ZHU, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '严刑峻法的代价', t, t - u + P)

# ================================================================ 第五回 外儒内法
def art_h_waiz(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('汉以后 表面尊儒 内里用法', SERIF, 48, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '史称外儒内法', t, t - u + P)

def art_h_idioms(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    words = ['守株待兔', '自相矛盾', '郑人买履', '滥竽充数', '讳疾忌医', '老马识途']
    for i, w in enumerate(words):
        a = clamp((u - i * 0.3 * P) / 0.3)
        paste(cv, text_img(w, SERIF, 50, TIEQING if i % 2 else INK, 'Black', bleed=False, spacing=6), 330 + (i % 2) * 420, 1000 + (i // 2) * 120, 1, a)
    paste(cv, text_img('今天还挂在我们嘴边', SERIF, 48, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_h_book(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        bundle(A, 260 + k * 140, GROUND, 110)
    A.flush(cv)
    paste(cv, text_img('韩非子五十五篇 流传至今', SERIF, 48, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_h_end(A, cv, t, u):
    frame3(A, cv, 540, 1120, 280, 3, q=1.0, qin=1.0, t=t)
    paste(cv, text_img('不期修古 不法常可', SERIF, 50, TIEQING, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_h_legacy(A, cv, t, u):
    bundle(A, 860, 1420, 70)

def art_h_title(A, cv, t, u):
    slips(A, 720, 1440, 12, 220, layer='zhujian')
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    han_(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '公子'), 48: ('第二回', '孤愤'), 80: ('第三回', '入秦'),
            112: ('第四回', '一统'), 144: ('第五回', '法')}

CARDS = [
    C(0, 2, 'life', 'num', num='说话结巴', line='却写出十余万言', art=art_h_hook_mouth),
    C(2, 4, 'empire', 'num', num='秦王读他', line='说见他一面死也无憾', art=art_h_hook_king),
    C(4, 6, 'death', 'num', num='一杯毒药', line='同学送来的', art=art_h_hook_cup),
    C(6, 8, 'night', 'num', num='守株待兔', line='是他讲的故事', art=art_h_hook_rabbit),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 公子
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-280, main='韩国公子', sub='宗室之后', note='年份约略', art=art_h_birth),
    C(22, 26, 'fate', 'card', year=-270, main='韩国积弱', sub='七国最弱', note='年份约略', art=art_h_weak),
    C(26, 32, 'works', 'card', year=-265, main='口吃', sub='善于著书', note='年份约略', art=art_h_stammer),
    C(32, 38, 'court', 'card', year=-255, main='师从荀子', sub='兰陵', note='年份约略', art=art_h_xunzi),
    C(38, 44, 'night', 'card', year=-255, main='同窗李斯', sub='自愧不如', art=art_h_lisi),
    C(44, 48, 'life', 'card', year=-250, main='回到韩国', sub='学成', note='年份约略', art=art_h_return),
    # ---- 第二回 孤愤
    C(48, 50, 'night', 'chapter'),
    C(50, 54, 'court', 'card', year=-245, main='上书', sub='不被采纳', note='年份约略', art=art_h_jian),
    C(54, 60, 'works', 'card', year=-240, main='孤愤', sub='十余万言', note='年份约略', art=art_h_gufen),
    C(60, 66, 'life', 'card', year=-240, main='寓言', sub='守株待兔', art=art_h_fables),
    C(66, 70, 'war', 'card', year=-240, main='五蠹', sub='世异事异', art=art_h_wudu),
    C(70, 74, 'empire', 'card', year=-240, main='法术势', sub='集大成', art=art_h_fashushi),
    C(74, 80, 'fate', 'card', year=-240, main='逆鳞', sub='说难', art=art_h_nilin),
    # ---- 第三回 入秦
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'empire', 'card', year=-234, main='秦王读书', sub='嬴政', art=art_h_qinread),
    C(86, 90, 'war', 'card', year=-234, main='秦攻韩', sub='兵临城下', art=art_h_attack),
    C(90, 98, 'death', 'ruqin', year=-233),
    C(98, 104, 'works', 'card', year=-233, main='说难', sub='不能自脱', art=art_h_sima),
    C(104, 112, 'fate', 'card', year=-233, main='逆鳞之祸', sub='命运的讽刺', art=art_h_irony),
    # ---- 第四回 一统
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'fate', 'card', year=-230, main='韩亡', sub='六国之首', art=art_h_hanfall),
    C(118, 124, 'war', 'card', year=-221, main='秦统一', sub='六国尽灭', art=art_h_unify),
    C(124, 130, 'court', 'card', year=-213, main='以法为教', sub='以吏为师', art=art_h_law),
    C(130, 136, 'death', 'card', year=-208, main='李斯之死', sub='同门结局', art=art_h_lisi_end),
    C(136, 144, 'night', 'card', year=-207, main='秦亡', sub='二世而终', art=art_h_qinfall),
    # ---- 第五回 法
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'court', 'card', year=-100, main='外儒内法', sub='两千年', note='年份约略', art=art_h_waiz),
    C(152, 158, 'life', 'card', year=-100, main='成语', sub='挂在嘴边', art=art_h_idioms),
    C(158, 164, 'works', 'card', year=-100, main='五十五篇', sub='韩非子', art=art_h_book),
    C(164, 170, 'end', 'card', year=-100, main='因时而变', sub='不法常可', art=art_h_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='玖拾伍', col=TIEQING, acc=ZHUJIAN, born=-280, died=-233, age0=-281, no_age=True,
    born_lab='约前280年', died_lab='前233年', years_txt='约公元前280 — 前233',
    hook_q='秦王最想见的人 · 为什么一到秦国就死了？',
    name_line='韩非 · 法家集大成者', name='韩非子', seal='法术', title_art=art_h_title,
    q1='冷酷权谋？', q2='治国良方？',
    end_art=art_h_legacy, end_big='法术势', end_seal='韩非',
    end_l1='他教会了帝王怎么驾驭天下', end_l2='自己却死在了帝王的猜忌里',
    end_brush='世异事异', end_ask='韩非子的寓言 你最喜欢哪一个？评论区聊聊', next='张仲景'),
    scenes=dict(chapter=scene_chapter, ruqin=scene_ruqin))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
