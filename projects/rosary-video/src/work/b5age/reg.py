import numpy as np,sys
from PIL import Image
from scipy import ndimage as ndi, optimize
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
cx,cy,cs=816,182,192
full=np.asarray(Image.open(S+'/pub/i5/B5_full.jpg').convert('RGB')).astype(np.float32)
O=full[cy:cy+cs,cx:cx+cs]
E=np.asarray(Image.open(sys.argv[1]).convert('RGB').resize((cs,cs),Image.LANCZOS)).astype(np.float32)
def warp(im,s,dx,dy):
    H,W=im.shape[:2]; c=(H-1)/2
    return np.dstack([ndi.affine_transform(im[...,k],[1/s,1/s],offset=[c-(c+dy)/s,c-(c+dx)/s],order=1,mode='nearest') for k in range(3)])
# register on the region around head but excluding the face itself (cloth outline, neck, background)
Y,X=np.mgrid[0:cs,0:cs]; hx,hy=912-cx,278-cy
reg=((X-hx)**2+(Y-hy)**2<70**2)&~(((X-hx+4)/30)**2+((Y-hy)/34)**2<1)
Ob=ndi.gaussian_filter(O,(1.5,1.5,0)); Eb=ndi.gaussian_filter(E,(1.5,1.5,0))
f=lambda p: np.abs(warp(Eb,*p)-Ob)[reg].mean()
best=min(((f((s,dx,dy)),(s,dx,dy)) for s in (0.97,0.985,1.0,1.015,1.03) for dx in range(-6,7,2) for dy in range(-6,7,2)))
r=optimize.minimize(f,best[1],method='Nelder-Mead',options=dict(xatol=0.05,fatol=0.01))
print('reg',np.round(r.x,3),'err',round(float(r.fun),2))
Ew=warp(E,*r.x); np.save(sys.argv[2],Ew)
