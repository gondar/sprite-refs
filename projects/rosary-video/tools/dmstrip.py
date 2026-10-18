import json,sys
from PIL import Image,ImageDraw
d=sys.argv[1];ts=sys.argv[2].split(',');box=tuple(map(int,sys.argv[3].split(',')));out=sys.argv[4]
fr=[]
for t in ts:
    im=Image.open(f'{d}/t_{float(t):.2f}.png').convert('RGB').crop(box)
    ImageDraw.Draw(im).text((4,4),t,fill=(255,255,0));fr.append(im)
w,h=fr[0].size;cols=min(5,len(fr));rows=(len(fr)+cols-1)//cols
S=Image.new('RGB',(w*cols,h*rows))
for k,f in enumerate(fr):S.paste(f,((k%cols)*w,(k//cols)*h))
S.save(out,quality=90)
