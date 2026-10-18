# analyse blink bag frames: alpha fit between home(open) and most-closed frame
import json,sys,numpy as np
from PIL import Image
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/'
def load(cutjson,fig,gn):
    c=json.load(open(P+cutjson))[fig];w,h=c['w'],c['h'];g=[g for g in c['gestures'] if g['name']==gn][0]
    sh=np.asarray(Image.open(P+g['file']).convert('RGBA')).astype(float)
    fr=[sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w] for k in range(g['frames'])]
    home=np.asarray(Image.open(P+c['home']).convert('RGBA')).astype(float)
    return c,g,fr,home
def flat(a): return a[...,:3]*a[...,3:]/255
if __name__=='__main__':
    cj,fig,gn=sys.argv[1:4]
    c,g,fr,home=load(cj,fig,gn)
    H=flat(home); F=[flat(f) for f in fr]
    D=np.array([np.abs(f-H).sum(2) for f in F])
    from scipy import ndimage
    kc=int(np.argmax([np.percentile(x,99.5) for x in D]))
    m=ndimage.binary_dilation(ndimage.binary_opening(D[kc]>80),iterations=3)
    ys,xs=np.where(m)
    print(cj,fig,gn,'frames',len(F),'bbox',xs.min(),ys.min(),xs.max(),ys.max() if len(xs) else None)
    # eye region = pixels changed; use largest change frame as closed
    d=[D[k][m].mean() for k in range(len(F))]
    C=F[kc]
    v=(C-H)[m]
    for k,f in enumerate(F):
        u=(f-H)[m]; a=(u*v).sum()/max((v*v).sum(),1e-6); r=np.abs(u-a*v).mean()
        dc=np.abs(f-C)[m].mean(); dh=np.abs(f-H)[m].mean()
        print(f' f{k:2d} dh={dh:6.2f} dc={dc:6.2f} alpha={a:5.2f} resid={r:5.2f}')
