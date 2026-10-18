# python3 zoomcmp.py cutjson fig gest x0,y0,x1,y1 scale out [backup]  -> rows: old frames / new frames
import json,sys,numpy as np
from PIL import Image,ImageDraw
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/'
cj,fig,gn,bb,sc,out=sys.argv[1:7]; b=[int(v) for v in bb.split(',')]; sc=float(sc)
c=json.load(open(P+cj))[fig];w,h=c['w'],c['h'];g=[g for g in c['gestures'] if g['name']==gn][0]
def frames(path):
    sh=np.asarray(Image.open(path).convert('RGBA')).astype(float)
    return [sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w] for k in range(g['frames'])]
def flat(a): return a[...,:3]*a[...,3:]/255+70*(1-a[...,3:]/255)
rows=[('new',frames(P+g['file']))]
import os
bk=os.path.dirname(os.path.abspath(__file__))+'/backup/'+g['file'].replace('/','_')
if os.path.exists(bk): rows.insert(0,('old',frames(bk)))
H=np.asarray(Image.open(P+c['home']).convert('RGBA')).astype(float)
tw,th=int((b[2]-b[0])*sc),int((b[3]-b[1])*sc); n=g['frames']+1
O=Image.new('RGB',(n*(tw+2),len(rows)*(th+12)),(0,0,0))
for r,(lab,fr) in enumerate(rows):
    for k,a in enumerate([H]+fr):
        x,y=k*(tw+2),r*(th+12)
        O.paste(Image.fromarray(flat(a)[b[1]:b[3],b[0]:b[2]].clip(0,255).astype('uint8')).resize((tw,th),Image.LANCZOS),(x,y+12))
        ImageDraw.Draw(O).text((x+2,y),lab+(' home' if k==0 else ' f%d'%(k-1)),fill=(255,255,0))
O.save(out,quality=92); print(out,O.size)
