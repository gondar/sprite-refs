# hard-cut blink bags for B5 mary: every frame is exactly home (open) or exactly the closed frame; lossless WebP
import json,numpy as np,os
from PIL import Image
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/'
cj=json.load(open(P+'i7/cut/B5/cut.json'))['mary']; w,h=cj['w'],cj['h']
HOME=np.asarray(Image.open(P+cj['home']).convert('RGBA'))
CL=np.asarray(Image.open('B5_mary_closed.png').convert('RGBA'))
def sm(u): return u*u*(3-2*u)
def track(keys,t):
    if t<=keys[0][0]: return keys[0][1]
    for (t0,v0),(t1,v1) in zip(keys,keys[1:]):
        if t<=t1: return v0+(v1-v0)*sm((t-t0)/(t1-t0))
    return keys[-1][1]
K={'blink':[[0,0],[0.2,0],[0.26,1],[0.42,1],[0.5,0],[0.75,0]],
   'blink2':[[0,0],[0.2,0],[0.26,1],[0.38,1],[0.45,0],[0.62,0],[0.68,1],[0.8,1],[0.88,0],[1.25,0]]}
for g in cj['gestures']:
    if g['name'] not in K: continue
    N=g['frames']; st=['C' if track(K[g['name']],i/12)>=0.5 else 'o' for i in range(N)]; st[0]=st[-1]='o'
    sh=np.zeros((g['rows']*h,g['cols']*w,4),np.uint8)
    for k in range(N): sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w]=CL if st[k]=='C' else HOME
    fn=P+g['file']; Image.fromarray(sh).save(fn,'WEBP',lossless=True,exact=True,method=6)
    dec=np.asarray(Image.open(fn).convert('RGBA'))
    print(g['name'],''.join(st),'exact roundtrip',(dec==sh).all(),os.path.getsize(fn)//1024,'KB')
