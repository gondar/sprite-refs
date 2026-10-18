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
Y,X=np.mgrid[0:cs,0:cs]
reg=((X-(905-cx))**2+(Y-(280-cy))**2<75**2)&~((X>=866-cx)&(X<930-cx)&(Y>=250-cy)&(Y<298-cy))
# compare edges (gradient of luminance), robust to colour shift
def ed(im):
    L=ndi.gaussian_filter(im.mean(2),1.2); return np.hypot(ndi.sobel(L,0),ndi.sobel(L,1))
Oe=ed(O)
f=lambda p: np.abs(ed(warp(E,*p))-Oe)[reg].mean()
best=min(((f((s,dx,dy)),(s,dx,dy)) for s in np.arange(0.92,1.10,0.02) for dx in range(-12,13,2) for dy in range(-12,13,2)))
print('grid',best)
r=optimize.minimize(f,best[1],method='Nelder-Mead',options=dict(xatol=0.05,fatol=0.01))
print('reg',np.round(r.x,3),'err',round(float(r.fun),2))
Ew=warp(E,*r.x)
# write back as a 1024 'raw' already aligned to the crop so cutB's register sees ~identity
Image.fromarray(np.clip(Ew,0,255).astype(np.uint8)).resize((1024,1024),Image.LANCZOS).save(sys.argv[2])
v=np.hstack([O,Ew,(O+Ew)/2]); Image.fromarray(v[50:150].clip(0,255).astype(np.uint8)).resize((v.shape[1]*3,300)).save('reg2_view.jpg')
