"""Shared episode tail (from ep19 on): wiring, year line, title / question / end scenes, HUD, main.
Each episode builds CARDS + CHAPTERS + its arts, then calls epkit.setup(...) and epkit.main(render)."""
import math, sys, subprocess
from PIL import Image, ImageDraw
import render_long as L
import render_gufeng as G
from render_gufeng import (W, H, FPS, bt, INK, ZHE, BRUSH, SERIF, font, clamp, lerp, ease_out, cn_num,
                           text_img, paste, ink_in, seal, stamp)
from render_story import Art
from render_full import chars_in, type_in
from render_long import stage, DIM, P
from render_yuefei import cn_year

END_BEAT = 170
_PREV = ('render_long', 'render_wudi', 'render_taizong', 'render_wuzetian', 'render_songtaizu', 'render_mingtaizu',
         'render_kangxi', 'render_yongzheng', 'render_qianlong', 'render_genghis', 'render_liubang', 'render_caocao',
         'render_zhuge', 'render_yuefei', 'render_wentianxiang', 'render_qijiguang', 'render_zhenghe',
         'render_wangyangming', 'render_zhangjuzheng', 'render_yuqian', 'render_kongzi', 'render_quyuan',
         'render_xiangyu', 'render_hanxin', 'render_zhangqian', 'render_simaqian')

def setup(CARDS, CHAPTERS, cfg, scenes=None):
    """cfg keys: ep (拾玖), col, acc, born, died, age0, hook_q, name_line, name, seal, title_art,
    q1, q2, end_art, end_big, end_l1, end_l2, end_brush, end_ask, end_seal, next."""
    mods = [m for n, m in list(sys.modules.items()) if n.startswith('render_') and m is not None]
    L.CARDS = CARDS; G.CARDS = CARDS
    for mod in mods:
        mod.CHAPTERS = CHAPTERS
    G.CHAPTER_BEATS = [0, 16, 48, 80, 112, 144, END_BEAT]
    L.CUTS = sorted({c[0] for c in CARDS if c[0] not in G.CHAPTER_BEATS})
    col, acc = cfg['col'], cfg['acc']
    BORN, DIED = cfg['born'], cfg['died']
    AGE0 = cfg.get('age0', BORN)
    pts = sorted((bt(c[0]), c[4]['year']) for c in CARDS if 'year' in c[4])

    def year_at(t):
        if t <= pts[0][0]: return pts[0][1]
        prev = pts[0][1]
        for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
            if t < t1: return lerp(prev, y0, ease_out((t - t0) / 0.4))
            prev = y0
        return lerp(prev, pts[-1][1], ease_out((t - pts[-1][0]) / 0.4))
    for mod in [G] + mods:
        mod.year_at = year_at

    def year_line(cv, t, year, start):
        yr = int(round(year_at(t))) if t >= bt(16) else year
        im = text_img(('公元' + (cn_num(yr) if yr < 100 else cn_year(yr)) if yr > 0 else '公元前' + cn_num(-yr)) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
        ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
        w = 200 * ease_out((t - start) / 0.4)
        ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=col + (220,), width=3)
    L.year_line = year_line

    def scene_title(cv, t, c, k):
        s0 = bt(c[0])
        stage(cv, t, c, cfg['title_art'])
        fx = Art()
        ink_in(cv, text_img(cfg['name_line'], SERIF, 46, col, 'Black', bleed=False, spacing=8), W / 2, 300, t, s0)
        chars_in(cv, fx, cfg['name'], BRUSH, 210 if len(cfg['name']) <= 3 else 180, INK, W / 2, 450, t, s0, stagger=0.1, seed=77)
        fx.flush(cv)
        stamp(cv, seal(cfg['seal'], 66), 900, 640, t, bt(c[0] + 2), rot=-5)
        type_in(cv, text_img(f'公元{BORN} — {DIED}' if BORN > 0 else cfg['years_txt'], SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4),
                W / 2, 590, t, bt(c[0] + 2), 0.4)

    def scene_question(cv, t, c, k):
        s0 = bt(c[0])
        stage(cv, t, c, c[4]['art'])
        fx = Art()
        chars_in(cv, fx, cfg['q1'], BRUSH, 120, col, W / 2, 420, t, s0, stagger=0.07, seed=5)
        chars_in(cv, fx, cfg['q2'], BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
        fx.flush(cv)
        type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

    END = bt(END_BEAT)
    def scene_end(cv, t, c, k):
        u = t - END
        A = Art()
        cfg['end_art'](A, cv, t, u)
        A.flush(cv, alpha=clamp(u / 0.6) * 0.25)
        fx = Art()
        big = cfg['end_big']
        chars_in(cv, fx, big, BRUSH, 220 if len(big) <= 4 else 180, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
        fx.flush(cv)
        stamp(cv, seal(cfg['end_seal'], 60), W / 2 + 390, 540, t, END + 0.45, rot=6)
        type_in(cv, text_img(cfg['end_l1'], SERIF, 48, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.4)
        type_in(cv, text_img(cfg['end_l2'], SERIF, 52, INK, 'Bold', bleed=False, spacing=4), W / 2, 1040, t, END + 0.85, 0.45)
        chars_in(cv, None, cfg['end_brush'], BRUSH, 100, col, W / 2, 1190, t, END + 1.15, stagger=0.06, drop=30, splash=False)
        type_in(cv, text_img(cfg['end_ask'], SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
        v = u - 1.75
        if v > 0:
            pulse = 1 + 0.035 * math.sin(v * 7)
            bw, bh = 400 * pulse, 92 * pulse
            a = int(255 * clamp(v / 0.25))
            btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
            d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=col + (a,))
            f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
            d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(250, 250, 245, a))
            prog = ease_out(v / 0.6)
            pts_ = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                     100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
            d.line(pts_, fill=acc + (230,), width=5)
            cv.alpha_composite(btn, (0, 1330))
            paste(cv, text_img('下集预告 · ' + cfg['next'], SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
                  W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

    G.SCENES.update(title=scene_title, question=scene_question, end=scene_end, **(scenes or {}))

    def draw_hud(canvas, t):
        ti = text_img(f'人物志 · 第{cfg["ep"]}集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6)
        paste(canvas, seal('千古', 34), min(330, 570 - ti.width / 2 - 45), 170, 1, 1)
        paste(canvas, ti, 570, 170, 1, 1)
        if t < bt(8):
            q = text_img(cfg['hook_q'], SERIF, 36, INK, 'Black', bleed=False, spacing=2)
            paste(canvas, q, W / 2, 290, 1, 1)
            ImageDraw.Draw(canvas).line((W / 2 - 340, 335, W / 2 + 340, 335), fill=col + (220,), width=3)
        cur = None
        for b, ch in CHAPTERS.items():
            if bt(b) <= t < bt(END_BEAT): cur = ch
        if cur:
            paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, col, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
        if bt(16) - 0.15 <= t < bt(END_BEAT):
            a = clamp((t - (bt(16) - 0.15)) / 0.25)
            y = 1560; x0, x1 = 170, W - 170
            yr = year_at(t)
            p = clamp((yr - BORN) / (DIED - BORN))
            ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
            d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
            xp = lerp(x0, x1, p)
            d.line((x0, 80, xp, 80), fill=col + (230,), width=6)
            d.ellipse((xp - 12, 68, xp + 12, 92), fill=acc + (255,))
            f = font(SERIF, 30, 'Medium')
            lb0 = cfg.get('born_lab', f'{BORN}年'); lb1 = cfg.get('died_lab', f'{DIED}年')
            d.text((x0, 102), lb0, font=f, fill=INK + (170,))
            d.text((x1 - f.getlength(lb1), 102), lb1, font=f, fill=INK + (170,))
            lab = ('' if cfg.get('no_age') else cn_num(max(1, int(round(yr - AGE0)))) + '岁') if yr <= DIED + 0.5 else '身后'
            fb = font(SERIF, 38, 'Bold')
            d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=col + (255,))
            if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * a)))
            canvas.alpha_composite(ov, (0, y - 80))
    G.draw_hud = draw_hud
    return year_at

def main(render):
    from multiprocessing import Pool
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for ts in sys.argv[2].split(','):
            Image.frombytes('RGB', (W, H), render(int(float(ts) * FPS))).save(out.replace('.png', f'_{ts}.png'))
        sys.exit()
    nfr = int(round(G.DUR * FPS))
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-i', L.MUSIC,
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, fr in enumerate(pool.imap(render, range(nfr), chunksize=4)):
            ff.stdin.write(fr)
            if i % 300 == 0: print(i, '/', nfr, flush=True)
    ff.stdin.close(); ff.wait()
    if ff.returncode != 0: sys.exit(1)
    print('done', out)
