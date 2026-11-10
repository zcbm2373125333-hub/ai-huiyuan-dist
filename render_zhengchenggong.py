"""千古人物志 · 第玖拾集 · 郑成功 (1624–1662)
Look: 潮水蓝 + 砂金, little anchors and wave crests in the corners, sea and offshore islands behind.
Chapter card: 罗盘 — a mariner's compass whose needle swings to the next place each chapter (平户 安平 南京 台湾); in the last chapter it stops.
Set pieces: custom 8-beat scene 'luermen' (鹿耳门涨潮), 6-beat 焚青衣, 6-beat 围南京, 6-beat 围热兰遮.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_songyingxing as Sy    # engine + helpers (previous episode)
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
from render_wangyangming import desk, scroll, lamp
from render_simayi import emperor
from render_jianzhen import temple
from render_sunwu import banner, army
from render_songtaizu import tent
from render_qijiguang import ming_soldier

F.RIPPLE = False
CHAOSHUI = (38, 96, 124)            # 潮水蓝
SHAJIN = (186, 132, 60)             # 砂金
S.LAYERS.append(('chaoshui', CHAOSHUI, 0.9, 1.0))
S.LAYERS.append(('shajin', SHAJIN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='海', life='郑', court='明', night='潮', war='战', empire='国', works='台', fate='孤', death='逝', end='海')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = (SHAJIN, 200, (W * 0.5, 800))
G.THEMES['war']['sun'] = (ZHU, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (CHAOSHUI, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (SHAJIN, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(5):                 # sea swell lines
    for _i in range(0, 960, 60):
        _d.arc((60 + _i, 1416 + _k * 12, 120 + _i, 1440 + _k * 12), 180, 360, fill=CHAOSHUI + (70 - _k * 10,), width=3)
for _x, _w in ((150, 90), (930, 70)):   # offshore islets at the margins
    _d.polygon([(_x - _w, 1420), (_x - _w * 0.3, 1360), (_x + _w * 0.2, 1372), (_x + _w, 1420)], fill=(110, 120, 110, 70))
MTN_COL = {'night': (28, 36, 46), 'death': (60, 62, 66), 'war': (110, 64, 50), 'fate': (90, 98, 104)}
def draw_background(t, theme):
    """海上: low island hills, a swell of sea lines, two islets at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 196, 196), (150, 166, 170), MTN_COL.get(theme, (96, 118, 128))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.7))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """锚: a small anchor in each corner over a wave crest."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=CHAOSHUI + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=CHAOSHUI + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.line((cx, cy - 26, cx, cy + 22), fill=(90, 70, 50, 230), width=4)
        d.line((cx - 14, cy - 14, cx + 14, cy - 14), fill=(90, 70, 50, 230), width=3)
        d.ellipse((cx - 6, cy - 34, cx + 6, cy - 22), outline=(90, 70, 50, 230), width=3)
        d.arc((cx - 22, cy, cx + 22, cy + 30), 0, 180, fill=SHAJIN + (230,), width=4)

# ================================================================ primitives
def zheng(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, armour=False, **kw):
    """郑成功: a young scholar in a blue robe — or, after 1646, a general in helmet with a gold cape."""
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if kw.get('fall'):
        return hand
    top = y - (0.48 if kneel else 0.78) * h
    if armour:
        A.d['shajin'].polygon([(x - dir * 0.02 * h, top), (x - dir * 0.12 * h, top), (x - dir * 0.34 * h, y - 0.06 * h), (x - dir * 0.1 * h, y - 0.06 * h)], fill=230)
        A.d['red'].line((x, y - 0.99 * h, x - dir * 0.08 * h, y - 1.1 * h), fill=255, width=max(3, int(0.03 * h)))
    else:
        A.d['chaoshui'].polygon([(x - 0.1 * h, top), (x + 0.1 * h, top), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=150)
    return hand

def dutch(A, x, y, h, dir=-1, layer='mid', **kw):
    """荷兰人: bare head under a broad-brimmed hat, short coat."""
    hand = person(A, x, y, h, dir=dir, robe=False, hat='none', layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        A.d[layer].ellipse((x - 0.16 * h, y - 1.03 * h, x + 0.16 * h, y - 0.97 * h), fill=255)
        A.d[layer].rectangle((x - 0.07 * h, y - 1.13 * h, x + 0.07 * h, y - 1.0 * h), fill=255)
    return hand

def junk(A, x, y, s, t, sails=2, layer='chaoshui', flag_=True):
    """福船: a high-sterned junk with battened sails."""
    bob = 6 * math.sin(t * 2 + x * 0.013)
    A.d['ink'].polygon([(x - s, y - 0.35 * s + bob), (x - 0.7 * s, y - 0.12 * s + bob), (x + 0.9 * s, y - 0.12 * s + bob),
                        (x + 1.05 * s, y - 0.3 * s + bob), (x + 0.8 * s, y + 0.12 * s + bob), (x - 0.8 * s, y + 0.12 * s + bob)], fill=255)
    for k in range(sails):
        mx = x - 0.3 * s + k * 0.55 * s
        A.d['ink'].line((mx, y - 0.12 * s + bob, mx, y - 1.25 * s + bob), fill=255, width=4)
        A.d[layer].polygon([(mx - 0.28 * s, y - 1.15 * s + bob), (mx + 0.22 * s, y - 1.2 * s + bob), (mx + 0.25 * s, y - 0.3 * s + bob), (mx - 0.3 * s, y - 0.3 * s + bob)], fill=220)
        for j in range(5):
            yy = y - 1.05 * s + j * 0.17 * s + bob
            A.d['ink'].line((mx - 0.28 * s, yy, mx + 0.24 * s, yy), fill=150, width=2)
    if flag_:
        mx = x - 0.3 * s
        A.d['red'].polygon([(mx, y - 1.25 * s + bob), (mx + 0.3 * s, y - 1.18 * s + bob), (mx, y - 1.1 * s + bob)], fill=255)

def fort(A, cx, base, w, t, lower=0.0, ming=False):
    """热兰遮城: a square brick fort with corner bastions; the tricolour flag is lowered as `lower` → 1."""
    d = A.d['shajin']
    d.rectangle((cx - w, base - 0.42 * w, cx + w, base), fill=230)
    for sx in (-1, 1):
        bx = cx + sx * 0.88 * w
        d.rectangle((bx - 0.14 * w, base - 0.62 * w, bx + 0.14 * w, base), fill=255)
        for j in range(3):
            A.d['ink'].rectangle((bx - 0.14 * w + j * 0.11 * w, base - 0.68 * w, bx - 0.08 * w + j * 0.11 * w, base - 0.62 * w), fill=220)
    A.d['mid'].rectangle((cx - 0.5 * w, base - 0.72 * w, cx + 0.5 * w, base - 0.42 * w), fill=230)
    for k in range(int(w // 40)):
        A.d['ink'].rectangle((cx - w + k * 80, base - 0.46 * w, cx - w + k * 80 + 40, base - 0.42 * w), fill=200)
    px, ptop = cx, base - 1.25 * w
    A.d['ink'].line((px, base - 0.72 * w, px, ptop), fill=255, width=5)
    if ming:
        banner(A, px, base - 0.72 * w, 0.53 * w, t, layer='red')
    else:
        fy = lerp(ptop, base - 0.84 * w, clamp(lower))
        wv = 5 * math.sin(t * 4)
        for j, ly in enumerate(('red', 'wash', 'chaoshui')):
            A.d[ly].polygon([(px, fy + j * 18), (px + 110, fy + j * 18 + wv), (px + 110, fy + j * 18 + 18 + wv), (px, fy + j * 18 + 18)], fill=255)

def compass(A, cx, cy, r, ang):
    """罗盘: wooden ring, eight ticks, a two-colour needle at angle `ang` (radians, 0 = up)."""
    A.d['shajin'].ellipse((cx - r, cy - r, cx + r, cy + r), fill=230)
    A.d['wash'].ellipse((cx - 0.75 * r, cy - 0.75 * r, cx + 0.75 * r, cy + 0.75 * r), fill=255)
    A.d['ink'].ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=max(3, int(0.03 * r)))
    A.d['ink'].ellipse((cx - 0.75 * r, cy - 0.75 * r, cx + 0.75 * r, cy + 0.75 * r), outline=200, width=2)
    for k in range(24):
        a = k * math.pi / 12
        r0 = 0.8 * r if k % 3 else 0.76 * r
        A.d['ink'].line((cx + r0 * math.sin(a), cy - r0 * math.cos(a), cx + 0.95 * r * math.sin(a), cy - 0.95 * r * math.cos(a)), fill=200, width=2 if k % 3 else 4)
    s, c = math.sin(ang), math.cos(ang)
    tip = (cx + 0.68 * r * s, cy - 0.68 * r * c); tail = (cx - 0.68 * r * s, cy + 0.68 * r * c)
    side = (0.08 * r * c, 0.08 * r * s)
    A.d['red'].polygon([tip, (cx + side[0], cy + side[1]), (cx - side[0], cy - side[1])], fill=255)
    A.d['ink'].polygon([tail, (cx + side[0], cy + side[1]), (cx - side[0], cy - side[1])], fill=255)
    A.d['ink'].ellipse((cx - 0.06 * r, cy - 0.06 * r, cx + 0.06 * r, cy + 0.06 * r), fill=255)

def sea(A, top, t, rows=2, amp=4):
    A.d['ocean'].rectangle((60, top, W - 60, GROUND + 40), fill=150)
    waves(A, top + 10, t, rows=rows, amp=amp)

# ================================================================ chapter card
CH = {16: (1.6, 1.6, '平户'), 48: (1.6, -0.7, '安平'), 80: (-0.7, 0.1, '南京'), 112: (0.1, 2.4, '台湾'), 144: (2.4, 2.4, '台湾')}
def art_compass_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b, place = CH.get(kb, (0.0, 1.0, ''))
    q = ease_out(u / (1.4 * P))
    wob = 0.08 * math.sin(t * 5) * (1 - q) if kb != 144 else 0.0
    compass(A, 540, 1000, 200, lerp(a, b, q) + wob)
    A.flush(cv)
    paste(cv, text_img(place, SERIF, 40, CHAOSHUI, 'Black', bleed=False, spacing=8), W / 2, 1240, 1, clamp((q - 0.5) / 0.3))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_compass_chapter)
    ink_in(cv, text_img(no, SERIF, 56, CHAOSHUI, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_z_hook_fort(A, cv, t, u):
    sea(A, 1300, t)
    fort(A, 540, 1300, 300, t, lower=clamp(u / (1.4 * P)))

def art_z_hook_name(A, cv, t, u):
    ground(A, GROUND)
    zheng(A, 540, GROUND, 300, dir=1, arm=40)
    A.flush(cv)
    stamp(cv, seal('朱', 70), 820, 1100, t, t - u + 0.6 * P, rot=6)

def art_z_hook_robe(A, cv, t, u):
    ground(A, GROUND)
    A.d['chaoshui'].polygon([(420, GROUND - 40), (660, GROUND - 40), (620, GROUND - 200), (460, GROUND - 200)], fill=200)
    flames(A, 540, GROUND - 30, 260, 260 * clamp(u / (1.0 * P)), t, n=4, seed=901, smoke=True)

def art_z_hook_tide(A, cv, t, u):
    q = ease_out(u / (1.6 * P))
    A.d['dune'].chord((240, GROUND - 120, 840, GROUND + 160), 180, 360, fill=230)
    A.d['ocean'].rectangle((60, lerp(GROUND - 20, GROUND - 120, q), W - 60, GROUND + 40), fill=150)
    junk(A, lerp(180, 860, q), lerp(GROUND - 20, GROUND - 120, q), 110, t)

# ================================================================ 第一回 平户
def art_z_birth(A, cv, t, u):
    sea(A, 1320, t)
    A.d['dune'].polygon([(60, GROUND), (60, 1300), (380, 1240), (560, 1300), (620, GROUND)], fill=230)
    A.d['ink'].ellipse((300, 1250, 380, 1296), fill=255)
    person(A, 420, 1300, 170, dir=1, female=True, baby=True, arm=60, layer='ink')
    A.flush(cv)
    paste(cv, text_img('生于日本平户 母亲田川氏', SERIF, 46, CHAOSHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '相传生于海边石上 民间传说', t, t - u + P)

def art_z_father(A, cv, t, u):
    sea(A, 1240, t)
    for k in range(4):
        junk(A, 200 + k * 220, 1260 - (k % 2) * 30, 80, t, sails=2, layer='mid')
    person(A, 540, 1100, 160, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    paste(cv, text_img('父亲郑芝龙 称雄东南海上', SERIF, 46, CHAOSHUI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '是年受明朝招抚', t, t - u + P)

def art_z_home(A, cv, t, u):
    sea(A, 1240, t)
    junk(A, lerp(860, 300, ease_out(u / (3 * P))), 1260, 110, t)
    A.flush(cv)
    paste(cv, text_img('七岁回到泉州安平', SERIF, 48, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '母亲留在日本', t, t - u + P)

def art_z_xiucai(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 420, layer='mid')
    zheng(A, 300, GROUND, 170, dir=1, kneel=True, arm=100)
    lamp(A, 780, GROUND - 74, 28, t, glow=0.8)
    A.flush(cv)
    paste(cv, text_img('十五岁 考中南安县学生员', SERIF, 46, CHAOSHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_taixue(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='南京', layer='mid', open_=1.0)
    ground(A, GROUND)
    zheng(A, 400, GROUND, 190, dir=1, arm=60)
    person(A, 680, GROUND, 190, dir=-1, robe=True, hat='knot', arm=40, layer='mid')
    A.flush(cv)
    paste(cv, text_img('入南京国子监 拜师钱谦益', SERIF, 46, CHAOSHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '钱谦益为他取字大木', t, t - u + P)

def art_z_nanjing_fall(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='南京', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(3):
        banner(A, 260 + k * 280, 1080, 150, t, layer='mid', fallen=clamp((u - k * 0.3 * P) / P))
    A.flush(cv)
    paste(cv, text_img('清军南下 弘光朝覆亡', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_guoxing(A, cv, t, u):
    """6-beat: 隆武 grants him the imperial surname 朱 and the name 成功."""
    ph = u / P
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 760, GROUND, 200, dir=-1, arm=lerp(-8, 60, clamp((ph - 1) / 0.5)))
    zheng(A, 380, GROUND, 180, dir=1, kneel=ph < 4, bow=30 if ph < 4 else 0, arm=-8)
    A.flush(cv)
    stamp(cv, seal('朱', 70), 860, 1020, t, t - u + 1.5 * P, rot=6)
    lab = '隆武帝赐姓朱 改名成功' if ph < 4 else '人称国姓爷'
    paste(cv, text_img(lab, SERIF, 48, CHAOSHUI if ph < 4 else ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '国姓爷 荷兰人写作Koxinga', t, t - u + 4 * P)

# ================================================================ 第二回 孤臣
def art_z_father_surrender(A, cv, t, u):
    ground(A, GROUND)
    banner(A, 820, GROUND, 320, t, layer='shajin')
    person(A, lerp(300, 620, ease_out(u / (2 * P))), GROUND, 190, dir=1, robe=True, hat='knot', bow=30, arm=60, layer='mid')
    zheng(A, 200, GROUND, 180, dir=1, arm=lerp(-8, 80, clamp((u - P) / 0.4)))
    A.flush(cv)
    paste(cv, text_img('父亲郑芝龙 降清北上', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '他苦劝不从 父子从此决裂', t, t - u + P)

def art_z_mother(A, cv, t, u):
    city_wall(A, 160, 920, 1120, layer='mid')
    flames(A, 540, 1120, 640, 220, t, n=6, seed=1646, smoke=True)
    ground(A, GROUND)
    person(A, 540, GROUND, 180, dir=1, female=True, fall=-88 * clamp((u - 1.5 * P) / 0.6), arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('清军攻破安平 母亲殉难', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '一说受辱后自尽 各书记载不一', t, t - u + P)

def art_z_burn(A, cv, t, u):
    """6-beat set piece: 焚青衣 — at the Confucian temple he burns his scholar's robe, bows, and rises in armour."""
    ph = u / P
    temple(A, 540, 1220, 360, layer='shajin')
    ground(A, GROUND)
    if ph < 3.5:
        zheng(A, 330, GROUND, 180, dir=1, kneel=ph > 1, bow=30 if ph > 1 else 0, arm=60)
        A.d['chaoshui'].polygon([(560, GROUND - 30), (720, GROUND - 30), (690, GROUND - 140), (590, GROUND - 140)], fill=int(220 * clamp(1 - (ph - 1.2) / 2)))
        if ph > 1:
            flames(A, 640, GROUND - 20, 200, 220 * clamp((ph - 1) / 0.6), t, n=4, seed=902, smoke=True)
        lab, col = '至孔庙 焚去儒服', CHAOSHUI
    else:
        flames(A, 640, GROUND - 20, 140, 90 * clamp(1 - (ph - 3.5) / 1.5), t, n=3, seed=903, smoke=True)
        zheng(A, 330, GROUND, 200, dir=1, armour=True, arm=lerp(-8, 140, clamp((ph - 3.8) / 0.5)))
        lab, col = '昔为孺子 今为孤臣', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 50, col, 'Black', bleed=False, spacing=8), W / 2, 760, 1, 1)
    note_in(cv, '谨谢儒服 唯先师昭鉴之', t, t - u + 4 * P)

def art_z_qibing(A, cv, t, u):
    sea(A, 1300, t)
    A.d['dune'].polygon([(300, 1300), (420, 1200), (660, 1190), (780, 1300)], fill=230)
    for k in range(min(6, int(u / (0.3 * P)) + 1)):
        ming_soldier(A, 380 + k * 60, 1210, 90, dir=1, layer='ink')
    banner(A, 700, 1200, 200, t, layer='red')
    A.flush(cv)
    paste(cv, text_img('在南澳 烈屿起兵抗清', SERIF, 48, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '据载初起时仅数十人', t, t - u + P)

def art_z_xiamen(A, cv, t, u):
    sea(A, 1260, t)
    A.d['dune'].polygon([(560, 1260), (660, 1150), (880, 1140), (980, 1260)], fill=230)
    banner(A, 760, 1150, 200, t, layer='red')
    for k in range(3):
        junk(A, lerp(120, 380, ease_out(u / (2 * P))) + k * 70, 1280 + (k % 2) * 20, 70, t)
    A.flush(cv)
    paste(cv, text_img('夺取厦门 金门 以为根基', SERIF, 48, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_z_siming(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='思明', layer='mid', open_=1.0)
    ground(A, GROUND)
    zheng(A, 540, GROUND, 190, dir=1, armour=True, arm=60)
    A.flush(cv)
    paste(cv, text_img('改中左所为思明州', SERIF, 48, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '思明 即思念明朝', t, t - u + P)

def art_z_trade(A, cv, t, u):
    sea(A, 1240, t)
    for k in range(3):
        x = lerp(-200, 900, ((t * 0.08 + k / 3) % 1))
        junk(A, x, 1260 - (k % 2) * 40, 80, t, sails=2, layer='shajin')
    A.flush(cv)
    paste(cv, text_img('设五商十行 船通日本 南洋', SERIF, 46, CHAOSHUI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '以海上贸易养兵', t, t - u + P)

# ================================================================ 第三回 北伐
def art_z_storm(A, cv, t, u):
    sea(A, 1200, t, rows=4, amp=18)
    for k in range(4):
        tilt = 0.4 * math.sin(t * 2 + k)
        sink = clamp((u - (1 + k * 0.5) * P) / P) * 120 if k % 2 else 0
        junk(A, 200 + k * 220, 1220 + sink, 80, t * 2, sails=2)
    for k in range(10):
        x = (k * 97 + t * 400) % 1000 + 40
        A.d['wash'].line((x, 900, x - 40, 1100), fill=120, width=2)
    A.flush(cv)
    paste(cv, text_img('北上途中 羊山遇飓风', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '船覆兵溺 只得折返', t, t - u + P)

def art_z_yangtze(A, cv, t, u):
    sea(A, 1260, t, rows=2, amp=3)
    for k in range(6):
        junk(A, lerp(-300, 400, ease_out(u / (3 * P))) + k * 120, 1270 - (k % 2) * 30, 60, t)
    A.flush(cv)
    paste(cv, text_img('再度北伐 大军入长江', SERIF, 48, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '号称十七万 兵数各书不一', t, t - u + P)

def art_z_zhenjiang(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='镇江', layer='mid', open_=clamp(u / P))
    ground(A, GROUND)
    for k in range(2):
        banner(A, 260 + k * 560, 1080, 150, t, layer='red')
    army(A, 120, GROUND, 6, dir=1, t=t, march=True, h=110)
    A.flush(cv)
    paste(cv, text_img('攻克镇江 江南震动', SERIF, 50, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_nanjing(A, cv, t, u):
    """6-beat set piece: 围南京 — the army camps around the walls; he waits for surrender; the defenders sally out at night and the camps burn."""
    ph = u / P
    city_wall(A, 360, 1020, 1060, gate_x=700, label='南京', layer='mid', open_=1.0 if ph >= 4 else 0.0)
    ground(A, GROUND)
    for k in range(3):
        tent(A, 110 + k * 100, GROUND, 90, 90, layer='chaoshui')
    if ph < 2:
        army(A, 80, GROUND - 100, 5, dir=1, t=t, h=80)
        lab, col = '大军围城 州县纷纷响应', CHAOSHUI
    elif ph < 4:
        zheng(A, 260, GROUND - 90, 150, dir=1, armour=True, arm=-8)
        lab, col = '围而不攻 坐待守军出降', CHAOSHUI
    else:
        flames(A, 210, GROUND - 40, 360, 200 * clamp((ph - 4) / 0.6), t, n=5, seed=1659, smoke=True)
        army(A, 600, GROUND, 4, dir=-1, layer='ink', t=t, march=True, h=110)
        lab, col = '清军出城突袭 大营溃败', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '误信守军缓兵之计 坐失战机', t, t - u + 2 * P)

def art_z_defeat(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        banner(A, 200 + k * 220, GROUND, 220, t, layer='red', fallen=clamp(0.6 + 0.1 * k))
    person(A, 760, GROUND, 160, dir=-1, fall=-80, arm=-8, hat='helmet', robe=False, layer='mid')
    A.flush(cv)
    paste(cv, text_img('大将甘辉被俘不屈而死', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_retreat(A, cv, t, u):
    sea(A, 1260, t)
    for k in range(3):
        junk(A, lerp(500, -100, ease_out(u / (3 * P))) + k * 160, 1280, 70, t, layer='mid')
    A.flush(cv)
    paste(cv, text_img('退回厦门 元气大伤', SERIF, 50, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_z_xiamen_war(A, cv, t, u):
    sea(A, 1240, t, rows=3, amp=8)
    junk(A, 300, 1260, 100, t)
    for k in range(3):
        junk(A, 760 + k * 90, 1260, 60, t, sails=1, layer='mid', flag_=False)
        if u > (1 + k * 0.4) * P:
            flames(A, 760 + k * 90, 1240, 90, 120, t, n=2, seed=930 + k, smoke=True)
    A.flush(cv)
    paste(cv, text_img('清军来攻厦门 被他击退', SERIF, 48, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

# ================================================================ 第四回 东渡
def art_z_map(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1120, 520, 320, ease_out(u / (1.2 * P)), layer='wash')
    q = clamp((u - 0.8 * P) / P)
    if q > 0:
        A.d['dune'].polygon([(560, 1000), (620, 980), (640, 1120), (600, 1250), (560, 1220)], fill=int(220 * q))
        A.d['chaoshui'].line((380, 1120, 560, 1140), fill=int(255 * q), width=4)
    A.flush(cv)
    paste(cv, text_img('何斌献上台湾水道图', SERIF, 48, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '何斌原为荷兰人的通事', t, t - u + P)

def art_z_decide(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 540, GROUND, 520, 260, layer='chaoshui', open_=1.0)
    zheng(A, 540, GROUND, 200, dir=1, armour=True, arm=lerp(-8, 120, clamp((u - P) / 0.4)))
    for k in range(2):
        person(A, 220 + k * 640, GROUND, 160, dir=1 if k == 0 else -1, robe=False, hat='helmet', bow=20, arm=40, layer='mid')
    A.flush(cv)
    paste(cv, text_img('诸将畏惧风涛 他决意东征', SERIF, 46, CHAOSHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_luermen(cv, t, c, k):
    """8-beat custom scene: 鹿耳门 — two sandbars choke the shallow channel; the tide rises over them;
    the junks file through one after another, toward the Dutch fort on the far shore."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    tide = clamp((ph - 1) / 2.5)
    lvl = lerp(GROUND - 40, GROUND - 150, tide)
    fort(A, 920, GROUND - 170, 90, t)
    for x0, x1 in ((330, 470), (590, 730)):
        A.d['dune'].chord((x0, GROUND - 130, x1, GROUND + 60), 180, 360, fill=230)
    A.d['ocean'].rectangle((60, lvl, W - 60, GROUND + 40), fill=150)
    waves(A, lvl + 6, t, rows=2, amp=4)
    for j in range(4):
        go = clamp((ph - 3.5 - j * 0.7) / 2.5)
        x = lerp(140 - j * 80, 760, ease_out(go))
        if go > 0 or j == 0:
            junk(A, x, lvl + 20, 70, t)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '鹿耳门', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=90)
    fx.flush(cv)
    if ph < 1.5:
        lab, col = '水浅礁多 荷兰人以为大船难入', CHAOSHUI
    elif ph < 3.5:
        lab, col = '恰逢大潮 水位陡涨', CHAOSHUI
    else:
        lab, col = '船队鱼贯而入 直抵台江', ZHU
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '涨潮属实 焚香祷潮之说为民间传说', t, s0 + 3 * P)

def art_z_zeelandia(A, cv, t, u):
    """6-beat set piece: 围热兰遮 — 赤崁 (Provintia) surrenders first; the main fort holds out; months of siege and cannon fire."""
    ph = u / P
    sea(A, 1300, t)
    fort(A, 700, 1300, 220, t)
    if ph < 2:
        A.d['mid'].rectangle((140, 1180, 300, 1300), fill=230)
        A.d['wash'].rectangle((200, 1100, 216, 1180), fill=255)
        lab, col = '先下赤崁城', CHAOSHUI
    elif ph < 4:
        for k in range(3):
            A.d['ink'].rectangle((120 + k * 110, 1270, 200 + k * 110, 1290), fill=255)
            A.d['ink'].line((200 + k * 110, 1280, 250 + k * 110, 1265), fill=255, width=10)
        if int(t * 2) % 2:
            flames(A, 260 + 110 * (int(t * 2) % 3), 1265, 40, 30, t, n=1, seed=904, smoke=True)
        lab, col = '炮击热兰遮城', ZHU
    else:
        for k in range(5):
            ming_soldier(A, 140 + k * 70, 1300, 90, dir=1, layer='ink')
        lab, col = '围困长达九个月', CHAOSHUI
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '荷兰人据台已三十八年', t, t - u + P)

def art_z_father_killed(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 190, dir=1, robe=True, hat='knot', fall=-88 * clamp((u - P) / 0.6), arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('郑芝龙在北京被杀', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '降清十五年 终被处斩', t, t - u + P)

def art_z_surrender(A, cv, t, u):
    sea(A, 1300, t)
    q = clamp(u / (1.6 * P))
    if q < 1:
        fort(A, 540, 1300, 240, t, lower=q)
    else:
        fort(A, 540, 1300, 240, t, ming=True)
    A.flush(cv)
    paste(cv, text_img('荷兰长官揆一签约投降', SERIF, 48, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('复台', 56), 860, 1020, t, t - u + 2 * P, rot=6)

# ================================================================ 第五回 延平
def art_z_tuntian(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        A.d['grass'].rectangle((140 + k * 220, GROUND - 26, 300 + k * 220, GROUND - 6), fill=200)
    for j in range(4):
        ming_soldier(A, 200 + j * 200, GROUND - 8, 120, dir=1, bow=50, arm=150, layer='ink', weapon='none')
    A.flush(cv)
    paste(cv, text_img('设承天府 寓兵于农 开垦荒地', SERIF, 46, CHAOSHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    zheng(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('收复台湾不到半年 病逝', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '相传临终掩面 自言无面目见先帝', t, t - u + P)

def art_z_shilang(A, cv, t, u):
    sea(A, 1260, t)
    for k in range(5):
        junk(A, lerp(-200, 500, ease_out(u / (3 * P))) + k * 110, 1280 - (k % 2) * 30, 60, t, layer='mid', flag_=False)
    A.flush(cv)
    paste(cv, text_img('施琅率清军渡海 郑氏归清', SERIF, 46, CHAOSHUI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '其孙郑克塽出降', t, t - u + P)

def art_z_kangxi(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].polygon([(380, GROUND), (420, GROUND - 120), (660, GROUND - 120), (700, GROUND)], fill=200)
    A.d['ink'].rectangle((520, GROUND - 260, 560, GROUND - 120), fill=255)
    A.flush(cv)
    paste(cv, text_img('康熙准其归葬南安故里', SERIF, 48, CHAOSHUI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '称其为明室遗臣 非乱臣贼子', t, t - u + P)

def art_z_ci(A, cv, t, u):
    temple(A, 540, 1240, 340, layer='shajin')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('沈葆桢奏请 建延平郡王祠', SERIF, 46, CHAOSHUI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('延平', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_end(A, cv, t, u):
    sea(A, 1300, t)
    junk(A, 540, 1310, 140, t)
    A.flush(cv)
    paste(cv, text_img('开辟荆榛逐荷夷', SERIF, 52, CHAOSHUI, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '郑成功复台诗', t, t - u + P)

def art_z_legacy(A, cv, t, u):
    compass(A, 860, 1360, 60, 2.4 + 0.05 * math.sin(t))

def art_z_title(A, cv, t, u):
    sea(A, 1440, t)
    junk(A, 820, 1300, 120, t)
    zheng(A, 380, 1460, 680, dir=1, armour=True, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '平户'), 48: ('第二回', '孤臣'), 80: ('第三回', '北伐'),
            112: ('第四回', '东渡'), 144: ('第五回', '延平')}

CARDS = [
    C(0, 2, 'war', 'num', num='三十九岁', line='赶走荷兰人 收复台湾', art=art_z_hook_fort),
    C(2, 4, 'empire', 'num', num='国姓爷', line='皇帝赐他姓朱', art=art_z_hook_name),
    C(4, 6, 'fate', 'num', num='父亲降清', line='他焚衣起兵', art=art_z_hook_robe),
    C(6, 8, 'night', 'num', num='一场大潮', line='送船队进了鹿耳门', art=art_z_hook_tide),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 平户
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1624, main='生于平户', sub='日本', art=art_z_birth),
    C(22, 26, 'works', 'card', year=1628, main='海上霸主', sub='父亲郑芝龙', art=art_z_father),
    C(26, 30, 'night', 'card', year=1630, main='七岁归国', sub='泉州安平', art=art_z_home),
    C(30, 34, 'life', 'card', year=1638, main='考中秀才', sub='十五岁', art=art_z_xiucai),
    C(34, 38, 'court', 'card', year=1644, main='入国子监', sub='南京', art=art_z_taixue),
    C(38, 42, 'fate', 'card', year=1645, main='南京陷落', sub='弘光覆亡', art=art_z_nanjing_fall),
    C(42, 48, 'empire', 'card', year=1645, main='国姓爷', sub='赐姓改名', art=art_z_guoxing),
    # ---- 第二回 孤臣
    C(48, 50, 'fate', 'chapter'),
    C(50, 54, 'death', 'card', year=1646, main='父亲降清', sub='父子决裂', art=art_z_father_surrender),
    C(54, 58, 'war', 'card', year=1646, main='母亲殉难', sub='安平城破', art=art_z_mother),
    C(58, 64, 'night', 'card', year=1646, main='焚青衣', sub='孔庙辞儒', art=art_z_burn),
    C(64, 68, 'war', 'card', year=1647, main='起兵', sub='二十四岁', art=art_z_qibing),
    C(68, 72, 'works', 'card', year=1650, main='夺取厦门', sub='以为根基', art=art_z_xiamen),
    C(72, 76, 'court', 'card', year=1655, main='思明州', sub='厦门改名', art=art_z_siming),
    C(76, 80, 'life', 'card', year=1655, main='五商十行', sub='以商养兵', note='年份约略', art=art_z_trade),
    # ---- 第三回 北伐
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'fate', 'card', year=1658, main='羊山风暴', sub='首次北伐', art=art_z_storm),
    C(86, 90, 'works', 'card', year=1659, main='入长江', sub='再度北伐', art=art_z_yangtze),
    C(90, 94, 'empire', 'card', year=1659, main='克镇江', sub='江南震动', art=art_z_zhenjiang),
    C(94, 100, 'war', 'card', year=1659, main='围南京', sub='功败垂成', art=art_z_nanjing),
    C(100, 104, 'death', 'card', year=1659, main='大败', sub='甘辉殉难', art=art_z_defeat),
    C(104, 108, 'fate', 'card', year=1659, main='退守厦门', sub='元气大伤', art=art_z_retreat),
    C(108, 112, 'war', 'card', year=1660, main='厦门海战', sub='击退清军', art=art_z_xiamen_war),
    # ---- 第四回 东渡
    C(112, 114, 'night', 'chapter'),
    C(114, 118, 'works', 'card', year=1661, main='何斌献图', sub='台湾水道', art=art_z_map),
    C(118, 122, 'court', 'card', year=1661, main='决意东征', sub='力排众议', art=art_z_decide),
    C(122, 130, 'night', 'luermen', year=1661),
    C(130, 136, 'war', 'card', year=1661, main='围热兰遮', sub='九个月', art=art_z_zeelandia),
    C(136, 140, 'death', 'card', year=1661, main='父亲被杀', sub='北京', art=art_z_father_killed),
    C(140, 144, 'empire', 'card', year=1662, main='收复台湾', sub='荷兰投降', art=art_z_surrender),
    # ---- 第五回 延平
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'life', 'card', year=1662, main='开垦台湾', sub='屯田', art=art_z_tuntian),
    C(150, 154, 'death', 'card', year=1662, main='郑成功病逝', sub='三十九岁', art=art_z_death),
    C(154, 158, 'fate', 'card', year=1683, main='施琅攻台', sub='郑氏归清', art=art_z_shilang),
    C(158, 162, 'court', 'card', year=1700, main='归葬南安', sub='康熙准许', art=art_z_kangxi),
    C(162, 166, 'empire', 'card', year=1875, main='延平郡王祠', sub='沈葆桢', art=art_z_ci),
    C(166, 170, 'end', 'card', year=1875, main='开辟荆榛', sub='复台诗', art=art_z_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='玖拾', col=CHAOSHUI, acc=SHAJIN, born=1624, died=1662, age0=1623,
    born_lab='1624年', died_lab='1662年', years_txt='公元1624 — 1662',
    hook_q='父亲投降了清朝 · 他为什么偏要抗争到底？',
    name_line='郑成功 · 本名郑森', name='郑成功', seal='国姓', title_art=art_z_title,
    q1='民族英雄？', q2='孤臣孽子？',
    end_art=art_z_legacy, end_big='收复台湾', end_seal='延平',
    end_l1='父亲选了一条好走的路', end_l2='他选了一条最难走的路',
    end_brush='开辟荆榛', end_ask='郑成功一生 你最佩服他哪一刻？评论区聊聊', next='纪晓岚'),
    scenes=dict(chapter=scene_chapter, luermen=scene_luermen))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
