"""Render one mid-scene frame per card into contact sheets: python3 tools/preview.py render_xxx outdir"""
import sys, os, importlib, glob, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw
mod = importlib.import_module(sys.argv[1]); out = sys.argv[2]
shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
ts = []
for c in mod.CARDS:
    d = min(c[1], c[0] + 8) - c[0]
    ts.append(mod.bt(c[0]) + (d * 0.7 if c[3] != 'end' else 4) * mod.P)
for t in ts:
    Image.frombytes('RGB', (1080, 1920), mod.render(int(t * 30))).resize((240, 427)).save(f'{out}/a_{t:07.2f}.png')
fs = sorted(glob.glob(f'{out}/a_*.png'))
for s in range(0, len(fs), 27):
    c = Image.new('RGB', (240 * 9, 447 * 3), 'white'); d = ImageDraw.Draw(c)
    for i, f in enumerate(fs[s:s + 27]):
        x, y = (i % 9) * 240, (i // 9) * 447; c.paste(Image.open(f), (x, y + 20)); d.text((x + 4, y + 4), os.path.basename(f)[2:-4] + 's', fill='black')
    c.save(f'{out}/sheet_{s // 27}.png')
print('sheets:', sorted(glob.glob(f'{out}/sheet_*.png')))
