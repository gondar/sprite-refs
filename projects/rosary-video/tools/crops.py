# python crops.py <id> x0,y0,x1,y1 (1280x720 snap px) scale out t1,t2,...  -> side-by-side crops
import sys
from PIL import Image,ImageDraw
id=sys.argv[1];b=tuple(map(int,sys.argv[2].split(',')));s=float(sys.argv[3]);out=sys.argv[4];ts=sys.argv[5].split(',')
ims=[]
for t in ts:
    im=Image.open(f'{id}/snap/t_{float(t):.2f}.png').convert('RGB').crop(b);im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    ImageDraw.Draw(im).text((3,3),t,fill=(255,255,0));ims.append(im)
O=Image.new('RGB',(sum(i.width+4 for i in ims),ims[0].height));x=0
for i in ims:O.paste(i,(x,0));x+=i.width+4
O.save(out,quality=92);print(O.size)
