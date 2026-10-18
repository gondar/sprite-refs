import sys
from PIL import Image, ImageDraw
for s in sys.argv[1:]:
    im=Image.open(f'pub/i5/{s}_full.jpg').convert('RGB'); W,H=im.size; d=ImageDraw.Draw(im)
    for k in range(1,20):
        x=k*W/20; y=k*H/20
        c=(255,255,0) if k%2==0 else (120,120,0)
        d.line([(x,0),(x,H)],fill=c,width=1); d.line([(0,y),(W,y)],fill=c,width=1)
        if k%2==0: d.text((x+2,2),f'{k/20:.1f}',fill=(255,255,0)); d.text((2,y+2),f'{k/20:.1f}',fill=(255,255,0))
    im.save(f'scripts/i5/B/grid_{s}.jpg',quality=80)
