# 秦始皇 · 千古一帝 —— 古风水墨卡点版 (1080x1920, 30fps, 纯代码)
# 卡点只作用于画面元素（墨迹晕开、印章落下、墨色转场），整屏不缩放、不震动。
import math, os, sys, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
DUR = 27.3
BPM = 105.6
P = 60 / BPM
B0 = 0.4
def bt(k): return B0 + k * P

FD = os.path.join(HERE, 'fonts')
BRUSH = os.path.join(FD, 'MaShanZheng-Regular.ttf')
WILD = os.path.join(FD, 'ZhiMangXing-Regular.ttf')
SERIF = os.path.join(FD, 'NotoSerifSC.ttf')

INK = (30, 26, 24)
ZHU = (178, 34, 26)      # 朱砂
ZHE = (128, 82, 36)      # 赭石
PAPER = (236, 226, 204)  # 宣纸

@lru_cache(None)
def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight: f.set_variation_by_name(weight)
    return f

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def lerp(a, b, t): return a + (b - a) * t

CN = '零一二三四五六七八九'
def cn_num(n):
    if n < 10: return CN[n]
    if n < 20: return '十' + (CN[n % 10] if n % 10 else '')
    if n < 100: return CN[n // 10] + '十' + (CN[n % 10] if n % 10 else '')
    h, r = divmod(n, 100)
    s = CN[h] + '百'
    if r == 0: return s
    if r < 10: return s + '零' + CN[r]
    return s + CN[r // 10] + '十' + (CN[r % 10] if r % 10 else '')

# ---------------------------------------------------------------- paper & tints
rng = np.random.default_rng(3)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def smooth_noise(shape, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((shape[0] // scale + 2, shape[1] // scale + 2)).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((shape[1] + 2 * scale, shape[0] + 2 * scale), Image.BICUBIC)
    return np.asarray(im, np.float32)[scale:scale + shape[0], scale:scale + shape[1]] / 255

def make_paper():
    base = np.array(PAPER, np.float32)
    mott = smooth_noise((H, W), 160, 1) * 0.6 + smooth_noise((H, W), 40, 2) * 0.4
    arr = base * (0.93 + 0.1 * mott[..., None])
    arr += rng.normal(0, 3.2, (H, W, 1))
    fib = Image.new('L', (W, H), 0); d = ImageDraw.Draw(fib)
    for _ in range(2600):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        a = rng.uniform(0, math.pi); L = rng.uniform(8, 40)
        d.line((x, y, x + L * math.cos(a), y + L * math.sin(a)), fill=int(rng.uniform(20, 60)), width=1)
    arr -= np.asarray(fib, np.float32)[..., None] * 0.18
    r = np.sqrt(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
    vig = np.clip(1.06 - r ** 2.2 * 0.38, 0.55, 1)[..., None]
    arr = arr * vig + (1 - vig) * np.array([90, 60, 30], np.float32) * 0.35
    return np.clip(arr, 0, 255)
PAPER_ARR = make_paper()

THEMES = {
    'hook':   dict(tint=(1.00, 1.00, 1.00), mtn=0.55, wm='秦', sun=None, part='petal'),
    'life':   dict(tint=(1.02, 0.98, 0.90), mtn=0.50, wm='政', sun=None, part='petal'),
    'war':    dict(tint=(1.00, 0.90, 0.84), mtn=0.85, wm='戰', sun=(ZHU, 250, (W * 0.5, 430)), part='ash'),
    'empire': dict(tint=(1.04, 0.98, 0.84), mtn=0.55, wm='皇', sun=((200, 150, 60), 330, (W * 0.5, 820)), part='gold'),
    'works':  dict(tint=(0.88, 0.94, 0.98), mtn=0.75, wm='城', sun=None, part='snow'),
    'death':  dict(tint=(0.86, 0.86, 0.86), mtn=0.70, wm='亡', sun=((120, 120, 120), 200, (W * 0.72, 560)), part='ash'),
    'end':    dict(tint=(1.00, 0.98, 0.94), mtn=0.60, wm='帝', sun=(ZHU, 200, (W * 0.5, 720)), part='petal'),
}

@lru_cache(None)
def base_bg(theme):
    th = THEMES[theme]
    arr = PAPER_ARR * np.array(th['tint'], np.float32)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    if th['sun']:
        col, r, (cx, cy) = th['sun']
        s = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (125,))
        s = s.filter(ImageFilter.GaussianBlur(6))
        im.alpha_composite(s)
    return im

# ---------------------------------------------------------------- ink-wash mountains
def ridge(seed, base, amp, rough):
    r = np.random.default_rng(seed)
    xs = np.arange(W + 400); y = np.zeros(len(xs))
    for o in range(6):
        f = (o + 1) ** 1.7 / 900 * rough
        y += amp / (o + 1) ** 1.25 * np.sin(xs * f * 2 * math.pi + r.uniform(0, 6.28))
    return base + y

MTN = []
for i, (base, amp, rough, dens) in enumerate([(1250, 170, 0.9, 0.35), (1420, 140, 1.3, 0.55), (1600, 100, 1.7, 0.8)]):
    ys = ridge(21 + i, base, amp, rough)
    Wd = W + 400
    yg = np.arange(H, dtype=np.float32)[:, None]
    depth = yg - ys[None, :].astype(np.float32)
    # dark at the ridge, washing out downward like ink on wet paper
    a = np.where(depth > 0, 0.25 + 0.75 * np.exp(-depth / (90 + 40 * i)), 0)
    tex = smooth_noise((H, Wd), 24, 30 + i) * 0.5 + 0.5
    a = a * tex * dens
    # mist band below each ridge
    a *= 1 - 0.55 * np.exp(-((depth - 200) / 70) ** 2)
    m = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), 'L').filter(ImageFilter.GaussianBlur(2.5))
    MTN.append((m, ys))
SMOOTH_FRONT = np.convolve(np.pad(MTN[1][1], 60, mode='edge'), np.ones(121) / 121, mode='same')[60:-60]
SMOOTH_FRONT = 1385 + (SMOOTH_FRONT - SMOOTH_FRONT.mean()) * 0.45

# ---------------------------------------------------------------- particles
N_P = 46
PT = dict(x=rng.uniform(0, W, N_P), sp=rng.uniform(50, 150, N_P), ph=rng.uniform(0, 3000, N_P),
          sz=rng.uniform(0.6, 1.4, N_P), wob=rng.uniform(20, 80, N_P), wf=rng.uniform(0.3, 1.2, N_P),
          rot=rng.uniform(0, 360, N_P), rs=rng.uniform(-90, 90, N_P))

@lru_cache(None)
def particle_sprite(kind, q):
    s = 40
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == 'petal':
        col = [(214, 120, 120), (200, 80, 80), (230, 160, 150)][q]
        d.ellipse((10, 15, 30, 25), fill=col + (220,)); d.ellipse((13, 17, 26, 23), fill=tuple(min(255, c + 25) for c in col) + (220,))
    elif kind == 'gold':
        d.ellipse((16, 16, 24, 24), fill=(200, 150, 60, 200))
    elif kind == 'snow':
        d.ellipse((15, 15, 25, 25), fill=(255, 255, 255, 230))
    else:  # ash / ink flakes
        d.polygon([(12, 18), (26, 14), (28, 24), (16, 27)], fill=(60, 55, 50, 170))
    return im.filter(ImageFilter.GaussianBlur(0.8))

def draw_particles(canvas, t, kind):
    for i in range(N_P):
        span = H + 200
        y = (PT['ph'][i] + t * PT['sp'][i]) % span - 100
        x = (PT['x'][i] + PT['wob'][i] * math.sin(t * PT['wf'][i] + i) + t * 25) % (W + 80) - 40
        spr = particle_sprite(kind, i % 3)
        paste(canvas, spr, x, y, PT['sz'][i], 0.85, rot=PT['rot'][i] + t * PT['rs'][i])

# ---------------------------------------------------------------- text & ink helpers
DRY = smooth_noise((1400, 1400), 6, 77)

@lru_cache(512)
def text_img(text, path, size, color, weight=None, bleed=True, spacing=0, vertical=False):
    f = font(path, size, weight)
    pad = int(size * 0.35)
    if vertical:
        step = size * 1.05
        w = int(size * 1.2) + pad * 2; h = int(step * len(text)) + pad * 2
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for i, ch in enumerate(text):
            d.text(((w - f.getlength(ch)) / 2, pad + i * step - size * 0.08), ch, font=f, fill=color + (255,))
    else:
        lines = text.split('\n')
        widths = [f.getlength(ln) + spacing * max(0, len(ln) - 1) for ln in lines]
        w = int(max(widths)) + pad * 2; h = int(size * 1.25 * len(lines)) + pad * 2
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        y = pad
        for ln, lw in zip(lines, widths):
            x = (w - lw) / 2
            for ch in ln:
                d.text((x, y), ch, font=f, fill=color + (255,)); x += f.getlength(ch) + spacing
            y += size * 1.25
    if bleed:
        # dry-brush texture + soft ink bleed halo on paper
        a = np.asarray(im.getchannel('A'), np.float32)
        dry = DRY[:a.shape[0], :a.shape[1]] if a.shape[0] <= 1400 and a.shape[1] <= 1400 else 1
        a = a * (0.82 + 0.18 * dry)
        halo = np.asarray(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(size * 0.045)), np.float32)
        a = np.maximum(a, halo * 0.35)
        im.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return im

@lru_cache(64)
def reveal_field(w, h):
    """Noise field for ink-bleed reveal: centre first, ragged edges."""
    n = smooth_noise((h, w), 18, w * 7 + h)
    yy_, xx_ = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx_ - w / 2) / (w / 2)) ** 2 + ((yy_ - h / 2) / (h / 2)) ** 2)
    return np.clip(r * 0.55 + n * 0.45, 0, 1)

def paste(canvas, im, cx, cy, scale=1.0, alpha=1.0, rot=0, reveal=None):
    if alpha <= 0.01 or scale <= 0.01: return
    if reveal is not None and reveal < 1:
        if reveal <= 0: return
        fld = reveal_field(im.width, im.height)
        m = np.clip((reveal * 1.25 - fld) / 0.18, 0, 1)
        a = np.asarray(im.getchannel('A'), np.float32) * m
        im = im.copy(); im.putalpha(Image.fromarray(a.astype(np.uint8)))
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        a = im.getchannel('A').point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    x = int(cx - im.width / 2); y = int(cy - im.height / 2)
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + im.width), min(H, y + im.height)
    if x1 <= x0 or y1 <= y0: return
    canvas.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def ink_in(canvas, im, cx, cy, t, start, dur=0.3, settle=1.06, alpha=1.0):
    """Beat entrance: ink bleeds outward from the centre, tiny settle (no shake)."""
    u = t - start
    if u < 0: return
    p = ease_out(u / dur)
    paste(canvas, im, cx, cy, lerp(settle, 1.0, ease_out(u / 0.5)), alpha, reveal=p)

@lru_cache(64)
def seal(text, size, col=ZHU):
    f = font(SERIF, size, 'Black')
    n = len(text); cols = 1 if n <= 2 else 2; rows = math.ceil(n / cols)
    cell = int(size * 1.08)
    w = cols * cell + int(size * 0.5); h = rows * cell + int(size * 0.5)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=int(size * 0.1), fill=col + (255,))
    for i, ch in enumerate(text):
        c = cols - 1 - i // rows; r = i % rows
        d.text((int(size * 0.25) + c * cell + (cell - f.getlength(ch)) / 2, int(size * 0.25) + r * cell - size * 0.12),
               ch, font=f, fill=(250, 236, 220, 255))
    r = np.random.default_rng(len(text) * 31 + size)
    a = np.array(im.getchannel('A'), np.float32)
    a[r.random(a.shape) < 0.07] *= 0.2
    edge = smooth_noise(a.shape, 5, size) < 0.18
    a[edge] *= 0.3
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im

def stamp(canvas, im, cx, cy, t, start, rot=0):
    """Seal press: quick drop from slightly larger, ink density builds — on-beat but steady."""
    u = t - start
    if u < 0: return
    paste(canvas, im, cx, cy, lerp(1.35, 1.0, ease_expo(u / 0.16)), clamp(u / 0.05), rot=rot)

@lru_cache(None)
def ink_blot(seed, size):
    r = np.random.default_rng(seed)
    im = Image.new('L', (size, size), 0); d = ImageDraw.Draw(im)
    c = size / 2
    d.ellipse((c - size * 0.2, c - size * 0.2, c + size * 0.2, c + size * 0.2), fill=255)
    for _ in range(40):
        a = r.uniform(0, 2 * math.pi); dist = r.uniform(0.1, 0.42) * size; rr = r.uniform(0.01, 0.07) * size * (1 - dist / size)
        x, y = c + dist * math.cos(a), c + dist * math.sin(a)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)
    im = im.filter(ImageFilter.GaussianBlur(size * 0.015))
    a = np.asarray(im, np.float32) / 255
    n = smooth_noise((size, size), max(4, size // 40), seed + 9)
    a = np.clip((a + n * 0.25 - 0.45) / 0.12, 0, 1) * (0.75 + 0.25 * n)
    out = Image.new('RGBA', (size, size), INK + (0,)); out.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return out

# ---------------------------------------------------------------- script
CARDS = [
    (0, 2, 'hook', 'num', dict(num='十三岁', line='继位为王')),
    (2, 4, 'hook', 'num', dict(num='三十九岁', line='一统天下')),
    (4, 6, 'hook', 'num', dict(num='五十岁', line='崩于东巡路上')),
    (6, 8, 'hook', 'title', {}),
    (8, 10, 'life', 'card', dict(year=259, main='生于邯郸', sub='秦国质子之子 · 生在敌国赵都')),
    (10, 12, 'life', 'card', dict(year=257, main='九死一生', sub='秦赵血战 · 母子藏匿 · 屡遭追杀')),
    (12, 14, 'life', 'card', dict(year=247, main='继位秦王', sub='年仅十三 · 吕不韦为相')),
    (14, 16, 'life', 'card', dict(year=238, main='亲政夺权', sub='平嫪毐之乱 · 罢吕不韦 · 大权独揽')),
    (16, 24, 'war', 'six', {}),
    (24, 26, 'empire', 'card', dict(year=221, main='始皇帝', sub='德兼三皇 · 功过五帝', seal='皇帝')),
    (26, 30, 'empire', 'list', dict(year=221, items=['书同文', '车同轨', '统一度量衡', '废分封 立郡县'])),
    (30, 32, 'empire', 'card', dict(year=221, main='大一统', sub='百代都行秦政法', pre='中国 第一次')),
    (32, 34, 'works', 'card', dict(year=215, main='北筑长城', sub='蒙恬率三十万大军 · 北击匈奴')),
    (34, 36, 'works', 'card', dict(year=214, main='修驰道\n凿灵渠', sub='车马通天下 · 水路连岭南', msize=190)),
    (36, 38, 'works', 'card', dict(year=213, main='焚书坑儒', sub='功过是非 · 争议两千年')),
    (38, 40, 'works', 'card', dict(year=211, main='求仙问药', sub='遣徐福东渡 · 只为长生不老')),
    (40, 42, 'death', 'card', dict(year=210, main='崩于沙丘', sub='第五次东巡途中 · 终年五十岁')),
    (42, 44, 'death', 'card', dict(year=207, main='二世而亡', sub='大秦帝国 · 仅存十五年')),
    (44, 99, 'end', 'end', {}),
]
CHAPTER_BEATS = [8, 16, 24, 32, 40, 44]
STATES = ['韩', '赵', '魏', '楚', '燕', '齐']
STATE_YEARS = [230, 228, 225, 223, 222, 221]
HEX_POS = {'赵': (-1, -1), '燕': (1, -1), '韩': (-2, 0), '齐': (2, 0), '魏': (-1, 1), '楚': (1, 1)}

def card_at(t):
    k = (t - B0) / P
    for c in CARDS:
        if c[0] <= k < c[1]: return c, k
    return CARDS[0], k

def year_at(t):
    pts = []
    for c in CARDS:
        if c[3] in ('card', 'list') and c[0] >= 8: pts.append((bt(c[0]), c[4]['year']))
        if c[3] == 'six':
            for i, y in enumerate(STATE_YEARS): pts.append((bt(16 + i), y))
    pts.sort()
    if t <= pts[0][0]: return pts[0][1]
    prev = pts[0][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t < t1: return lerp(prev, y0, ease_out((t - t0) / 0.4))
        prev = y0
    return lerp(prev, pts[-1][1], ease_out((t - pts[-1][0]) / 0.4))

# ---------------------------------------------------------------- background
def draw_background(t, theme):
    th = THEMES[theme]
    canvas = base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    for i, (m, ys) in enumerate(MTN):
        off = int(200 + t * 6 * (i + 1)) % 400   # slow, steady drift
        layer = Image.new('RGBA', (W, H), INK + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(v * th['mtn'])))
        canvas.alpha_composite(layer)
        if theme == 'works' and i == 2:
            draw_wall(canvas, t, off)
    return canvas

def draw_wall(canvas, t, off):
    prog = ease_out((t - bt(32)) / (P * 4))
    if prog <= 0: return
    ys = SMOOTH_FRONT
    d = ImageDraw.Draw(canvas)
    xmax = int(W * prog); col = (52, 50, 48, 235)
    pts = [(x, ys[x + off]) for x in range(0, xmax, 6)]
    if len(pts) > 1:
        d.line(pts, fill=col, width=9)
        for x in range(0, xmax, 26):
            d.rectangle((x, ys[x + off] - 16, x + 11, ys[x + off]), fill=col)
        for x in range(90, xmax, 260):
            y = ys[x + off]
            d.rectangle((x - 18, y - 56, x + 18, y), fill=col)
            d.polygon([(x - 28, y - 56), (x + 28, y - 56), (x, y - 80)], fill=col)

def draw_frame_border(canvas):
    d = ImageDraw.Draw(canvas)
    m, L = 44, 90
    col = INK + (150,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * L, y), fill=col, width=3); d.line((x, y, x, y + sy * L), fill=col, width=3)
        d.line((x + sx * 12, y + sy * 12, x + sx * 50, y + sy * 12), fill=col, width=2)
        d.line((x + sx * 12, y + sy * 12, x + sx * 12, y + sy * 50), fill=col, width=2)

# ---------------------------------------------------------------- scenes
def splash_deco(canvas, t, start, seed, x, y, size=360, alpha=0.5):
    u = t - start
    if u < 0: return
    paste(canvas, ink_blot(seed, size), x, y, lerp(0.3, 1.0, ease_expo(u / 0.25)), alpha * clamp(u / 0.05))

def year_column(canvas, t, year, start):
    s = '公元前' + cn_num(year) + '年'
    im = text_img(s, SERIF, 40, INK, 'Bold', bleed=False, vertical=True)
    ink_in(canvas, im, 100, 560 + im.height / 2 - 60, t, start, dur=0.35, settle=1.0)
    u = ease_out((t - start) / 0.4)
    d = ImageDraw.Draw(canvas)
    d.line((140, 510, 140, 510 + (im.height - 20) * u), fill=ZHU + (220,), width=4)

def scene_num(canvas, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    d = c[4]
    size = 250 if len(d['num']) <= 3 else 205
    splash_deco(canvas, t, s0, c[0] + 3, W / 2, 860, 760, 0.12)
    ink_in(canvas, text_img(d['num'], BRUSH, size, INK), W / 2, 860, t, s0)
    line = text_img(d['line'], BRUSH, 130, ZHU)
    ink_in(canvas, line, W / 2, 1120, t, s1, dur=0.25)

def scene_title(canvas, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    splash_deco(canvas, t, s0, 99, W / 2, 900, 980, 0.16)
    ink_in(canvas, text_img('秦始皇', BRUSH, 290, INK), W / 2, 880, t, s0, dur=0.35)
    ink_in(canvas, text_img('嬴 政', SERIF, 60, ZHE, 'Bold', bleed=False, spacing=20), W / 2, 680, t, s0 + 0.12)
    stamp(canvas, seal('千古一帝', 88), W / 2 + 10, 1190, t, s1, rot=-4)

def scene_card(canvas, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    d = c[4]
    year_column(canvas, t, d['year'], s0)
    splash_deco(canvas, t, s0, c[0] * 5 + 1, W / 2 + 40, 900, 820, 0.10)
    if 'pre' in d:
        ink_in(canvas, text_img(d['pre'], SERIF, 76, ZHE, 'Bold', bleed=False, spacing=8), W / 2, 690, t, s0, settle=1.0)
    msize = d.get('msize', 220 if len(d['main']) <= 3 else 195)
    ink_in(canvas, text_img(d['main'], BRUSH, msize, INK), W / 2 + 45, 900, t, s0)
    if t >= s1:
        sub = text_img(d['sub'], SERIF, 46, (70, 50, 30), 'SemiBold', bleed=False, spacing=3)
        v = t - s1
        paste(canvas, sub, W / 2 + 30, lerp(1170, 1150, ease_out(v / 0.3)) + (60 if '\n' in d['main'] else 0), 1, clamp(v / 0.15))
        if 'seal' in d:
            stamp(canvas, seal(d['seal'], 86), W / 2 + 380, 700, t, s1, rot=6)

def scene_list(canvas, t, c, k):
    d = c[4]
    year_column(canvas, t, d['year'], bt(24))
    paste(canvas, text_img('定 万 世 之 制', SERIF, 52, ZHE, 'Bold', bleed=False), W / 2 + 30, 600, 1, 1)
    for i, it in enumerate(d['items']):
        st = bt(c[0] + i)
        if t < st: continue
        cur = i == int(k - c[0])
        size = 150 if len(it) <= 3 else (125 if len(it) <= 5 else 110)
        y = 790 + i * 200
        im = text_img(it, BRUSH, size, INK)
        ink_in(canvas, im, W / 2 + 60, y, t, st, alpha=1.0 if cur else 0.55)
        u = t - st
        if u > 0.05:
            stamp(canvas, seal('壹贰叁肆'[i], 46), 250 - (0 if len(it) <= 3 else 60) - (40 if len(it) > 5 else 0), y, t, st + 0.05)

@lru_cache(None)
def state_disc(ch, dead):
    s = 240
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    ring = ink_blot(len(ch) + ord(ch) % 50, s)  # ink ring = blot minus inner
    a = np.asarray(ring.getchannel('A'), np.float32)
    yy_, xx_ = np.mgrid[0:s, 0:s]
    rr = np.sqrt((xx_ - s / 2) ** 2 + (yy_ - s / 2) ** 2)
    a = a * (rr > s * 0.27) * (rr < s * 0.40) + (rr < s * 0.40) * (rr > s * 0.36) * 140
    ring.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    if dead:
        ring = ring.copy(); ring.putalpha(ring.getchannel('A').point(lambda v: int(v * 0.35)))
    im.alpha_composite(ring)
    g = text_img(ch, BRUSH, 120, (150, 140, 130) if dead else INK)
    im.alpha_composite(g, ((s - g.width) // 2, (s - g.height) // 2 - 6))
    return im

@lru_cache(None)
def half_masks(s):
    a = Image.new('L', (s, s), 0); ImageDraw.Draw(a).polygon([(0, 0), (s, 0), (0, s)], fill=255)
    return a, ImageChops.invert(a)

def brush_slash(canvas, x0, y0, x1, y1, prog, alpha):
    if prog <= 0 or alpha <= 0: return
    d = ImageDraw.Draw(canvas)
    n = 14
    for j in range(n):
        f = j / n
        if f > prog: break
        xa, ya = lerp(x0, x1, f), lerp(y0, y1, f)
        xb, yb = lerp(x0, x1, min(prog, f + 1 / n)), lerp(y0, y1, min(prog, f + 1 / n))
        wdt = int(4 + 14 * math.sin(math.pi * (f + 0.5 / n)))
        d.line((xa, ya, xb, yb), fill=ZHU + (int(230 * alpha),), width=wdt)

def scene_six(canvas, t, c, k):
    s0 = bt(16)
    cx0, cy0, R = W / 2, 935, 190
    gather = t >= bt(22)
    if not gather:
        ink_in(canvas, text_img('十年 灭六国', BRUSH, 160, INK), W / 2, 420, t, s0)
    idx = int(k - 16)
    if 0 <= idx < 6:
        lab = text_img(f'公元前{cn_num(STATE_YEARS[idx])}年 · 灭{STATES[idx]}', SERIF, 56, ZHU, 'Black', bleed=False, spacing=4)
        ink_in(canvas, lab, W / 2, 1410, t, bt(16 + idx), dur=0.2, settle=1.0)
    gu = ease_expo((t - bt(22)) / 0.4) if gather else 0
    stamp(canvas, seal('秦', 110), cx0, cy0, t, s0)
    if gather:
        stamp(canvas, seal('秦', 260), cx0, cy0, t, bt(22))
    for i, ch in enumerate(STATES):
        hx, hy = HEX_POS[ch]
        px = cx0 + hx * R * (0.95 if abs(hx) == 2 else 0.92); py = cy0 + hy * R * 1.55
        ka = bt(16 + i)
        if gather:
            paste(canvas, state_disc(ch, True), lerp(px, cx0, gu), lerp(py, cy0, gu), 1 - 0.7 * gu, 1 - gu)
            continue
        if t < ka:
            paste(canvas, state_disc(ch, False), px, py); continue
        u = t - ka
        L = 150
        if u < 0.45:
            disc = state_disc(ch, False)
            a, b = half_masks(disc.width)
            sep = ease_out((u - 0.08) / 0.37) * 40 if u > 0.08 else 0
            for msk, sgn in ((a, -1), (b, 1)):
                part = disc.copy(); part.putalpha(ImageChops.multiply(disc.getchannel('A'), msk))
                paste(canvas, part, px + sgn * sep, py + sgn * sep * 0.6, 1, 1 - clamp((u - 0.08) / 0.37))
            paste(canvas, state_disc(ch, True), px, py, 1, clamp(u / 0.45))
        else:
            paste(canvas, state_disc(ch, True), px, py)
        brush_slash(canvas, px + L * 0.7, py - L * 0.7, px - L * 0.7, py + L * 0.7, ease_out(u / 0.1), 1.0)
    if gather:
        ink_in(canvas, text_img('六王毕', BRUSH, 200, INK), W / 2, 450, t, bt(22))
        ink_in(canvas, text_img('四海一', BRUSH, 200, ZHU), W / 2, 1300, t, bt(23))

def scene_end(canvas, t, c, k):
    s0 = bt(44); u = t - s0
    ink_in(canvas, text_img('千古一帝', BRUSH, 230, INK), W / 2, 760, t, s0, dur=0.45)
    stamp(canvas, seal('秦始皇帝', 64), W / 2 + 370, 520, t, s0 + 0.3, rot=6)
    l1 = text_img('王朝只存十五年', SERIF, 50, (70, 50, 30), 'SemiBold', bleed=False, spacing=6)
    l2 = text_img('他定下的“中国” 延续两千年', SERIF, 54, INK, 'Bold', bleed=False, spacing=6)
    paste(canvas, l1, W / 2, 960, 1, clamp((u - 0.25) / 0.25))
    paste(canvas, l2, W / 2, 1040, 1, clamp((u - 0.45) / 0.25))
    # engagement: debate question + follow card
    q = text_img('暴君？明君？', BRUSH, 120, ZHU)
    ink_in(canvas, q, W / 2, 1200, t, s0 + 0.6, dur=0.3)
    ask = text_img('评论区留下你的看法', SERIF, 42, (70, 50, 30), 'SemiBold', bleed=False, spacing=4)
    paste(canvas, ask, W / 2, 1300, 1, clamp((u - 0.8) / 0.25))
    v = u - 1.0
    if v > 0:
        d = ImageDraw.Draw(canvas)
        a = int(255 * clamp(v / 0.25))
        bw, bh, by = 400, 92, 1430
        d.rounded_rectangle((W / 2 - bw / 2, by - bh / 2, W / 2 + bw / 2, by + bh / 2), radius=46, fill=ZHU + (a,))
        f = font(SERIF, 42, 'Bold')
        s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, by - 30), s, font=f, fill=(252, 240, 226, a))
        nx = text_img('下集预告 · 汉武帝刘彻', SERIF, 36, (90, 70, 50), 'Medium', bleed=False, spacing=4)
        paste(canvas, nx, W / 2, 1525, 1, clamp(v / 0.3))

SCENES = dict(num=scene_num, title=scene_title, card=scene_card, list=scene_list, six=scene_six, end=scene_end)

# ---------------------------------------------------------------- HUD
def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第壹集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    # hook question — keeps viewers watching past the first seconds
    if t < bt(8):
        q = text_img('史上第一位皇帝\n一生到底有多狠？', SERIF, 50, INK, 'Black', bleed=False, spacing=4)
        paste(canvas, q, W / 2, 400, 1, 1)
        d = ImageDraw.Draw(canvas)
        d.line((W / 2 - 230, 495, W / 2 + 230, 495), fill=ZHU + (220,), width=4)
    if bt(8) - 0.15 <= t < bt(44):
        a = clamp((t - (bt(8) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((259 - yr) / (259 - 210))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=INK + (220,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=ZHU + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), '前259', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength('前210'), 102), '前210', font=f, fill=INK + (170,))
        lab = cn_num(int(round(260 - yr))) + '岁' if yr > 209.5 else '身后'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=ZHU + (255,))
        if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * a)))
        canvas.alpha_composite(ov, (0, y - 80))

# ---------------------------------------------------------------- frame
@lru_cache(None)
def transition_field():
    w, h = W // 4, H // 4
    yy_, xx_ = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx_ - w / 2) / (w / 2)) ** 2 + ((yy_ - h / 2) / (h / 2)) ** 2) / 1.42
    n = smooth_noise((h, w), 45, 5) * 0.7 + smooth_noise((h, w), 8, 6) * 0.3
    f = np.clip(r * 0.88 + n * 0.12, 0, 1)
    return np.asarray(Image.fromarray((f * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255

def compose(t):
    c, k = card_at(t)
    if t < B0: c = CARDS[0]
    canvas = draw_background(t, c[2])
    draw_particles(canvas, t, THEMES[c[2]]['part'])
    if t >= B0: SCENES[c[3]](canvas, t, c, k)
    draw_frame_border(canvas)
    draw_hud(canvas, t)
    return canvas

TR = 0.32
def render(fi):
    t = fi / FPS
    canvas = compose(t)
    arr = np.asarray(canvas.convert('RGB'), np.float32)
    # chapter change: ink spreads from the centre, new scene revealed inside it
    for cb in CHAPTER_BEATS:
        s = bt(cb)
        if s <= t < s + TR:
            prev = np.asarray(compose(s - 1 / FPS).convert('RGB'), np.float32)
            p = ease_out((t - s) / TR) * 1.15
            fld = transition_field()
            m = np.clip((p - fld) / 0.06, 0, 1)[..., None]
            edge = np.clip(1 - np.abs(p - 0.04 - fld) / 0.035, 0, 1)[..., None] * 0.7
            arr = prev * (1 - m) + arr * m
            arr = arr * (1 - edge) + np.array(INK, np.float32) * edge
    fade = 1.0
    if t > DUR - 0.5: fade = clamp((DUR - t) / 0.5)
    arr = arr * fade + np.array(PAPER, np.float32) * 0.0 * (1 - fade)
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()

if __name__ == '__main__':
    from multiprocessing import Pool
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for ts in sys.argv[2].split(','):
            Image.frombytes('RGB', (W, H), render(int(float(ts) * FPS))).save(out.replace('.png', f'_{ts}.png'))
        sys.exit()
    nfr = int(DUR * FPS)
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-i', os.path.join(HERE, 'music_clean.wav'),
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, fr in enumerate(pool.imap(render, range(nfr), chunksize=4)):
            ff.stdin.write(fr)
            if i % 120 == 0: print(i, '/', nfr, flush=True)
    ff.stdin.close(); ff.wait()
    print('done', out)
