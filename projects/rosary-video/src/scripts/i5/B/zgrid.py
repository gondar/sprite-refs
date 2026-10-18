import sys
from PIL import Image, ImageDraw
s,x0,y0,cs,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
im=Image.open(f'pub/i5/{s}_full.jpg').convert('RGB').crop((x0,y0,x0+cs,y0+cs)); k=900/cs
im=im.resize((900,900),Image.LANCZOS); d=ImageDraw.Draw(im)
for v in range((x0//20+1)*20,x0+cs,20):
    X=(v-x0)*k; d.line([(X,0),(X,900)],fill=(255,255,0) if v%100==0 else (90,90,0)); 
    if v%100==0: d.text((X+2,2),str(v),fill=(255,255,0))
for v in range((y0//20+1)*20,y0+cs,20):
    Y=(v-y0)*k; d.line([(0,Y),(900,Y)],fill=(255,255,0) if v%100==0 else (90,90,0))
    if v%100==0: d.text((2,Y+2),str(v),fill=(255,255,0))
im.save(out,quality=85)
