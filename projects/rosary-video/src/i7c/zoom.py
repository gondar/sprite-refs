# zoom.py ID x0 y0 w h scale out  -> gridded zoom (10px light lines, 50px red)
import sys
from PIL import Image, ImageDraw
i,x0,y0,w,h,s,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7]
im=Image.open('../pub/i5/%s_full.jpg'%i).crop((x0,y0,x0+w,y0+h)).resize((w*s,h*s),Image.LANCZOS); d=ImageDraw.Draw(im)
for x in range((x0//10+1)*10,x0+w,10): d.line([((x-x0)*s,0),((x-x0)*s,h*s)],fill=(255,0,0) if x%50==0 else (255,210,210),width=1)
for y in range((y0//10+1)*10,y0+h,10): d.line([(0,(y-y0)*s),(w*s,(y-y0)*s)],fill=(255,0,0) if y%50==0 else (255,210,210),width=1)
im.save(out)
