import json, sys, numpy as np
from PIL import Image, ImageDraw
d = sys.argv[1]; M = json.load(open(d + '/leszy-anim.json'))
rows = []
for n, a in M['animacje'].items():
    s = Image.open(f"{d}/{a['plik']}").convert('RGBA'); fr = []
    for i in range(a['klatki']):
        c = s.crop((i * a['w'], 0, (i + 1) * a['w'], a['h'])); bg = Image.new('RGBA', (a['w'], 410), (40, 52, 70, 255))
        bg.alpha_composite(c, (0, 410 - a['h'])); dr = ImageDraw.Draw(bg)
        ox, oy = a['oczy'][i]; oy += 410 - a['h']; r = a['rozstaw'][i] / 2
        for sx in (-r, r): dr.ellipse([ox + sx - 2.5, oy - 1.5, ox + sx + 2.5, oy + 1.5], fill=(207, 243, 230, 255))
        px, py = a['pivot']; dr.line([(px - 6, 409), (px + 6, 409)], fill=(255, 180, 94, 255), width=2)
        fr.append(bg)
    fr[0].save(f'{d}/{n}.gif', save_all=True, append_images=fr[1:], duration=int(1000 / a['fps']), loop=0, disposal=2)
    rows.append((n, fr))
W = max(sum(f.width for f in fr) for _, fr in rows)
sheet = Image.new('RGBA', (W, 410 * len(rows)), (20, 26, 36, 255))
for r, (n, fr) in enumerate(rows):
    x = 0
    for f in fr: sheet.paste(f, (x, r * 410)); x += f.width
    ImageDraw.Draw(sheet).text((4, r * 410 + 4), n, fill=(255, 200, 120, 255))
sheet.save(d + '/kontakt.png'); print('ok')
