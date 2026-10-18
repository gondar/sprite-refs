import numpy as np,cv2,os,json,glob
P=[(np.s_[20:260,20:340],180),(np.s_[520:750,20:340],180),(np.s_[520:750,1000:1320],1160),(np.s_[640:760,560:900],730),(np.s_[20:200,600:900],750)]
H,W=768,1344
X,Y=np.meshgrid(np.arange(W,dtype=np.float32),np.arange(H,dtype=np.float32))
def fit(ref,g):
    xs=[];dx=[];w=[]
    for s,xc in P:
        (sx,sy),r=cv2.phaseCorrelate(ref[s],g[s]); xs.append(xc);dx.append(sx);w.append(r)
    xs=np.array(xs,float);dx=np.array(dx);w=np.array(w)+1e-3
    for _ in range(2):
        M=np.vstack([np.ones_like(xs),xs]).T*np.sqrt(w)[:,None]
        c=np.linalg.lstsq(M,dx*np.sqrt(w),rcond=None)[0]
        r=np.abs(dx-(c[0]+c[1]*xs))
        if r.max()>1.0 and len(xs)>3: k=r.argmax(); xs=np.delete(xs,k);dx=np.delete(dx,k);w=np.delete(w,k)
    return c
def warp(im,a,b): return cv2.remap(im,(X+a+b*X).astype(np.float32),Y,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
import sys
DIRS=sys.argv[1:]
out={}
for d in DIRS:
    ims=[cv2.imread('%s/%04d.png'%(d,i)) for i in range(1,len(glob.glob(d+'/*.png'))+1)]
    ref=cv2.cvtColor(ims[0],cv2.COLOR_BGR2GRAY).astype(np.float32)
    C=np.zeros((len(ims),2))
    for it in range(3):
        R=[]
        for i,im in enumerate(ims):
            g=cv2.cvtColor(warp(im,*C[i]),cv2.COLOR_BGR2GRAY).astype(np.float32)
            R.append(fit(ref,g))
        R=np.array(R)
        # map composition: x -> x + a + b x, then residual: approx add with (1+b) factor
        C=C+R*np.array([1,1])
        C[0]=0
        print(d,it,'max resid a',np.abs(R[:,0]).max().round(2),'b',np.abs(R[:,1]).max().round(5))
    # smooth
    k=np.ones(5)/5
    Cs=np.stack([np.convolve(np.pad(C[:,j],2,mode='edge'),k,'valid') for j in (0,1)],1); Cs[0]=0
    os.makedirs(d+'g',exist_ok=True)
    for i,im in enumerate(ims): cv2.imwrite('%sg/%04d.png'%(d,i+1),warp(im,*Cs[i]))
    out[d]=Cs.tolist()
json.dump(out,open('geo_'+'_'.join(DIRS)+'.json','w'))
