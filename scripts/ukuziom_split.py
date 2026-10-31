import sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
src, keyed, outdir = sys.argv[1:4]
import os; os.makedirs(outdir, exist_ok=True)
a = np.asarray(Image.open(keyed).convert('RGBA')).copy()
al = a[..., 3] > 60
# drop drawn baselines: a thin row-run spanning > 60 % of the width
H, W = al.shape
rows = al.sum(1)
for y in (range(H) if os.environ.get("LINES") else []):
    if rows[y] > 0.6 * W: a[max(0, y - 3):y + 4, :, 3] = 0
al = a[..., 3] > 60
lab, n = ndi.label(ndi.binary_dilation(al, iterations=12))
objs = []
for i, sl in enumerate(ndi.find_objects(lab)):
    m = (lab[sl] == i + 1) & (a[sl][..., 3] > 0)
    if m.sum() < 0.01 * H * W / 10: continue
    objs.append((sl, m))
# reading order: rows by centre y (bands), then x
objs.sort(key=lambda o: ((o[0][0].start + o[0][0].stop) // 2 // (H // 6), o[0][1].start))
sheet = Image.new('RGB', (len(objs) * 260, 300), (40, 40, 40)); d = ImageDraw.Draw(sheet)
for k, (sl, m) in enumerate(objs):
    crop = a[sl].copy(); crop[..., 3] = np.where(m, crop[..., 3], 0)
    im = Image.fromarray(crop); im.save(f'{outdir}/f{k:02d}.png')
    t = im.copy(); t.thumbnail((250, 250)); sheet.paste(t, (k * 260 + 5, 5), t); d.text((k * 260 + 8, 270), str(k), fill=(255, 255, 0))
    print(k, 'bbox y', sl[0].start, sl[0].stop, 'x', sl[1].start, sl[1].stop, 'size', crop.shape[1], crop.shape[0])
sheet.save(f'{outdir}/contact.png')
