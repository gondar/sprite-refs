# hard-cut a blink bag: every frame becomes exactly home (open) or one clean closed frame
# python3 fixbag.py <cut.json rel to pub> <fig> <gesture> [--closed-ov ov.png x y] [--dry]
import json,sys,os,shutil,numpy as np
from PIL import Image
from scipy import ndimage as ndi
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/'
B=os.path.dirname(os.path.abspath(__file__))+'/backup/'
cj,fig,gn=sys.argv[1:4]; a=sys.argv[4:]
c=json.load(open(P+cj))[fig]; w,h=c['w'],c['h']; g=[g for g in c['gestures'] if g['name']==gn][0]
fn=P+g['file']; bk=B+g['file'].replace('/','_')
if not os.path.exists(bk): shutil.copy(fn,bk)
sh=np.asarray(Image.open(bk).convert('RGBA'))
fr=[sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w].astype(float) for k in range(g['frames'])]
HOME=np.asarray(Image.open(P+c['home']).convert('RGBA')).copy()
flat=lambda x:x[...,:3]*x[...,3:]/255
Hf=flat(HOME.astype(float)); F=[flat(f) for f in fr]
D=np.array([np.abs(f-Hf).sum(2) for f in F])
kc=int(np.argmax([np.percentile(x,99.5) for x in D]))
m=ndi.binary_dilation(ndi.binary_opening(D[kc]>80),iterations=3)
v=(F[kc]-Hf)[m]
al=[float(((f-Hf)[m]*v).sum()/(v*v).sum()) for f in F]
# whole-figure check: open frames must differ from home only by codec noise
for k,f in enumerate(F):
    if al[k]<0.5:
        out=np.abs(f-Hf).sum(2)[~ndi.binary_dilation(m,iterations=8)]
        assert out.mean()<8 and np.percentile(out,99.9)<160, (k,out.mean(),np.percentile(out,99.9))
if '--closed-ov' in a:
    i=a.index('--closed-ov'); ov=np.asarray(Image.open(a[i+1])).astype(float); ox,oy=int(a[i+2]),int(a[i+3])
    E=np.zeros((h,w,3)); M=np.zeros((h,w)); oh,ow=ov.shape[:2]
    x0,y0=max(ox,0),max(oy,0); x1,y1=min(ox+ow,w),min(oy+oh,h)
    E[y0:y1,x0:x1]=ov[y0-oy:y1-oy,x0-ox:x1-ox,:3]; M[y0:y1,x0:x1]=ov[y0-oy:y1-oy,x0-ox:x1-ox,3]/255
    A=HOME[...,3]/255.; M*=(A>0.99)
    CL=HOME.copy().astype(float); CL[...,:3]=HOME[...,:3]*(1-M[...,None])+E*M[...,None]
    CL=np.clip(np.round(CL),0,255).astype(np.uint8)
    # sanity: new closed vs decoded closed outside the tear area
    d=np.abs(flat(CL.astype(float))-F[kc]).sum(2); print('new closed vs old closed: mean in eye',d[m].mean().round(2))
else:
    # closed frame = home everywhere except the feathered eye area, taken from the cleanest closed frame
    em=ndi.binary_dilation(D[kc]>12,iterations=4)&ndi.binary_dilation(m,iterations=10)
    fm=np.clip(ndi.gaussian_filter(em.astype(float),1.5)*1.5,0,1)*em
    fm=np.maximum(fm,ndi.binary_dilation(D[kc]>12,iterations=1)*1.0*em)
    CL=HOME.astype(float).copy(); CL=CL*(1-fm[...,None])+fr[kc]*fm[...,None]
    CL=np.clip(np.round(CL),0,255).astype(np.uint8)
N=len(fr); st=['C' if x>=0.5 else 'o' for x in al]; st[0]=st[-1]='o'
print(cj,fig,gn,'closed src f%d'%kc,'alpha',' '.join('%.2f'%x for x in al))
print('  schedule',''.join(st),'(blends replaced: %s)'%[k for k,x in enumerate(al) if 0.05<x<0.97])
if '--dry' in a: sys.exit()
sheet=np.zeros((g['rows']*h,g['cols']*w,4),np.uint8)
for k in range(N):
    sheet[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w]=CL if st[k]=='C' else HOME
q=int(os.environ.get('Q','80'))
Image.fromarray(sheet).save(fn,'WEBP',lossless=True,method=6) if os.environ.get('LOSSLESS') else Image.fromarray(sheet).save(fn,'WEBP',quality=q,method=6)
print('  wrote',fn,os.path.getsize(bk)//1024,'->',os.path.getsize(fn)//1024,'KB')
