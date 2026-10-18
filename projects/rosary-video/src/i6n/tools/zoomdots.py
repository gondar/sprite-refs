# zoomdots.py NAME SHEET ENTRY CONTACTS OUT f1,f2,... [crop x0,y0,x1,y1] : selected cells at 3x with the contact dots
import sys, json
from PIL import Image, ImageDraw
nm, sh, en, ct, out, fr = sys.argv[1:7]
E = json.load(open(en)); E = E.get(nm, E); C = json.load(open(ct))['contacts']
cw, ch, cols = E['cw'], E['ch'], E['cols']; S = Image.open(sh)
box = tuple(map(int, sys.argv[7].split(','))) if len(sys.argv) > 7 else (0, 0, cw, ch)
z = 3; W, H = (box[2] - box[0]) * z, (box[3] - box[1]) * z; fr = list(map(int, fr.split(',')))
im = Image.new('RGB', (W * len(fr), H), (236, 230, 214)); d = ImageDraw.Draw(im)
for k, i in enumerate(fr):
    c = S.crop(((i % cols) * cw + box[0], (i // cols) * ch + box[1], (i % cols) * cw + box[2], (i // cols) * ch + box[3])).resize((W, H), Image.LANCZOS)
    im.paste(c, (k * W, 0), c); d.text((k * W + 5, 5), str(i), fill=(0, 0, 0))
    for key, col in (('nose', (255, 0, 160)), ('paw', (255, 210, 0))):
        if key in C:
            x, y = C[key][i]; X, Y = k * W + (x - box[0]) * z, (y - box[1]) * z
            d.ellipse((X - 6, Y - 6, X + 6, Y + 6), outline=(0, 0, 0), width=2, fill=col)
    if 'gaze' in C:
        x, y = C['nose'][i]; gx, gy = C['gaze'][i]; X, Y = k * W + (x - box[0]) * z, (y - box[1]) * z
        d.line((X, Y, X + gx * 90, Y + gy * 90), fill=(0, 150, 0), width=3)
im.save(out, quality=90)
