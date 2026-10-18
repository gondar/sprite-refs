# peek.py scene fig gesture out : home | each frame crop around the change, x6
import sys,json,numpy as np
from PIL import Image
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/'
sc,fig,gn,out=sys.argv[1:5]; box=None
if len(sys.argv)>5: box=list(map(int,sys.argv[5].split(',')))
c=json.load(open(P+'i7/cut/%s/cut.json'%sc))[fig]; w,h=c['w'],c['h']; g=[g for g in c['gestures'] if g['name']==gn][0]
sh=np.asarray(Image.open(P+g['file']).convert('RGBA')).astype(float)
H=np.asarray(Image.open(P+c['home']).convert('RGBA')).astype(float)
fl=lambda x:x[...,:3]*x[...,3:]/255+128*(1-x[...,3:]/255)
fr=[fl(sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w]) for k in range(g['frames'])]
Hf=fl(H); D=[np.abs(f-Hf).sum(2) for f in fr]
print('per-frame mean diff',[round(float(d.mean()),2) for d in D])
if box is None:
    kc=int(np.argmax([d.sum() for d in D])); ys,xs=np.nonzero(D[kc]>40)
    box=[xs.min()-6,ys.min()-6,xs.max()+7,ys.max()+7]; print('box',box)
x0,y0,x1,y1=box
tiles=[Hf[y0:y1,x0:x1]]+[f[y0:y1,x0:x1] for f in fr]
v=np.concatenate([np.pad(t,((1,1),(1,1),(0,0)),constant_values=255) for t in tiles],1)
s=6; Image.fromarray(v.clip(0,255).astype(np.uint8)).resize((v.shape[1]*s,v.shape[0]*s),Image.NEAREST).save(out)
