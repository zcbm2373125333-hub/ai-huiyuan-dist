"""Post-render review sheets (every 0.5s) + 2s storyboard: python3 tools/review.py video.mp4 outdir storyboard.png"""
import sys, os, glob, subprocess, shutil
from PIL import Image, ImageDraw
v, out, sb = sys.argv[1:4]
shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
subprocess.run(['ffmpeg', '-v', 'error', '-i', v, '-vf', 'fps=2,scale=120:213', f'{out}/f_%03d.png'], check=True)
fs = sorted(glob.glob(f'{out}/f_*.png'))
for s in range(0, len(fs), 96):
    c = Image.new('RGB', (120 * 16, 228 * 6), 'white'); d = ImageDraw.Draw(c)
    for i, f in enumerate(fs[s:s + 96]):
        x, y = (i % 16) * 120, (i // 16) * 228; c.paste(Image.open(f), (x, y + 14)); d.text((x + 3, y + 1), f'{(s + i) * 0.5:.1f}', fill='black')
    c.save(f'{out}/sheet_{s // 96}.png')
c = Image.new('RGB', (120 * 12, 228 * 4), 'white'); d = ImageDraw.Draw(c)
for i, f in enumerate(fs[::4][:48]):
    x, y = (i % 12) * 120, (i // 12) * 228; c.paste(Image.open(f), (x, y + 14)); d.text((x + 3, y + 1), f'{i * 2}s', fill='black')
c.save(sb)
print('review sheets:', sorted(glob.glob(f'{out}/sheet_*.png')), 'storyboard:', sb)
