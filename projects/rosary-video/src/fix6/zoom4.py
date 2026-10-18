import sys,numpy as np
from PIL import Image
a,b,x0,y0,x1,y1,out=sys.argv[1],sys.argv[2],*map(int,sys.argv[3:7]),sys.argv[7]
def fl(p):
    im=Image.open(p).convert('RGBA'); bg=Image.new('RGBA',im.size,(128,128,128,255)); bg.alpha_composite(im); return bg.convert('RGB').crop((x0,y0,x1,y1))
A,B=fl(a),fl(b); w,h=A.size
o=Image.new('RGB',(w*8+8,h*4),(255,255,255)); o.paste(A.resize((w*4,h*4),Image.LANCZOS),(0,0)); o.paste(B.resize((w*4,h*4),Image.LANCZOS),(w*4+8,0)); o.save(out,quality=92)
