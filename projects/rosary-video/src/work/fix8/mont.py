import json,sys,numpy as np
from PIL import Image,ImageDraw
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/'
L=[l.split() for l in open(sys.argv[1]) if l.strip()]; out=sys.argv[2]; TH=90
def flat(a): return a[...,:3]*a[...,3:]/255+70*(1-a[...,3:]/255)
rows=[]
for cj,fig,gn,bb in L:
    b=[int(v) for v in bb.split(',')]
    c=json.load(open(P+'i7/cut/'+cj))[fig];w,h=c['w'],c['h'];g=[g for g in c['gestures'] if g['name']==gn][0]
    sh=np.asarray(Image.open(P+g['file']).convert('RGBA')).astype(float)
    fr=[sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w] for k in range(g['frames'])]
    sc=TH/(b[3]-b[1]); tw=int((b[2]-b[0])*sc)
    R=Image.new('RGB',(len(fr)*(tw+2)+120,TH+12))
    ImageDraw.Draw(R).text((2,40),cj.split('/')[0]+' '+fig+'\n'+gn,fill=(255,255,0))
    for k,a in enumerate(fr):
        R.paste(Image.fromarray(flat(a)[b[1]:b[3],b[0]:b[2]].clip(0,255).astype('uint8')).resize((tw,TH),Image.LANCZOS),(120+k*(tw+2),12))
        ImageDraw.Draw(R).text((122+k*(tw+2),0),'f%d'%k,fill=(255,255,0))
    rows.append(R)
W=max(r.size[0] for r in rows); O=Image.new('RGB',(W,sum(r.size[1] for r in rows))); y=0
for r in rows: O.paste(r,(0,y)); y+=r.size[1]
O.save(out,quality=92); print(out,O.size)
