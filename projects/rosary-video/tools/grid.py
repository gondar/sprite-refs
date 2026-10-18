# python grid.py <snapdir> x0,y0,x1,y1 out scale t1,t2,... [cols]
import sys
from PIL import Image,ImageDraw
d,box,out,sc,ts=sys.argv[1],tuple(map(int,sys.argv[2].split(','))),sys.argv[3],float(sys.argv[4]),sys.argv[5].split(',')
cols=int(sys.argv[6]) if len(sys.argv)>6 else 6
w,h=int((box[2]-box[0])*sc),int((box[3]-box[1])*sc);rows=(len(ts)+cols-1)//cols
G=Image.new('RGB',(w*cols,h*rows),'black');dr=ImageDraw.Draw(G)
for i,t in enumerate(ts):
  im=Image.open(f'{d}/t_{float(t):.2f}.png').convert('RGB').crop(box).resize((w,h));x,y=(i%cols)*w,(i//cols)*h
  G.paste(im,(x,y));dr.rectangle([x,y,x+44,y+14],fill='black');dr.text((x+2,y+1),t,fill='yellow')
G.save(out,quality=90)
