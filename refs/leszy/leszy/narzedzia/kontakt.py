import sys, glob, numpy as np
from PIL import Image, ImageDraw
d, out, step = sys.argv[1], sys.argv[2], int(sys.argv[3])
fs = sorted(glob.glob(d + '/f_*.png'))[::step]
W, H = 96, 168; cols = 18
rows = (len(fs) + cols - 1) // cols
c = Image.new('RGBA', (cols * W, rows * (H + 12)), (150, 160, 175, 255)); dr = ImageDraw.Draw(c)
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGBA').resize((W, H))
    x, y = (i % cols) * W, (i // cols) * (H + 12)
    c.alpha_composite(im, (x, y + 12)); dr.text((x + 2, y), f[-7:-4], fill=(0, 0, 0, 255))
c.save(out)
