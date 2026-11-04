"""grid.py PACKDIR GESTURE OUT [every] [cols]: the gesture's frames on a grid on a mid-grey ground (every Nth), labelled"""
import glob, sys
from PIL import Image, ImageDraw
pk, g, out = sys.argv[1:4]; ev = int(sys.argv[4]) if len(sys.argv) > 4 else 2; cols = int(sys.argv[5]) if len(sys.argv) > 5 else 6
fs = sorted(glob.glob(f'{pk}/frames/{g}_*.png'))[::ev]
W, H = Image.open(fs[0]).size; rows = (len(fs) + cols - 1) // cols
im = Image.new('RGBA', (cols * W, rows * H), (110, 110, 110, 255)); d = ImageDraw.Draw(im)
for i, f in enumerate(fs):
    x, y = (i % cols) * W, (i // cols) * H; im.alpha_composite(Image.open(f), (x, y)); d.rectangle((x, y, x + W - 1, y + H - 1), outline=(80, 80, 80))
    d.text((x + 4, y + 4), f.rsplit('_', 1)[1][:2], fill=(255, 255, 255))
im.convert('RGB').save(out)
