import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi, optimize
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
O=np.asarray(Image.open('in_mary.png').convert('RGB')).astype(np.float32)
E=np.asarray(Image.open(sys.argv[1]).convert('RGB').resize((512,512),Image.LANCZOS)).astype(np.float32)
# figure mask in crop coords
fig=np.asarray(Image.open(S+'/pub/i5/C5_fig_mary.png'))[...,3]/255.
M=np.zeros((512,512)); M[300-236:300-236+373,777-664:777-664+274]=fig
far=~ndi.binary_dilation(M>0.05,iterations=40)   # background only, for registration
def warp(im,s,dx,dy):
    c=255.5
    return np.dstack([ndi.affine_transform(im[...,k],[1/s,1/s],offset=[c-(c+dy)/s,c-(c+dx)/s],order=1,mode='nearest') for k in range(3)])
Ob=ndi.gaussian_filter(O,(2,2,0)); Eb=ndi.gaussian_filter(E,(2,2,0))
f=lambda p: np.abs(warp(Eb,*p)-Ob)[far].mean()
best=min((f((s,dx,dy)),(s,dx,dy)) for s in (0.99,1.0,1.01) for dx in (-3,-1.5,0,1.5,3) for dy in (-3,-1.5,0,1.5,3))
r=optimize.minimize(f,best[1],method='Nelder-Mead',options=dict(xatol=0.05,fatol=0.01))
print('reg',np.round(r.x,3),'bg err',round(float(r.fun),2))
W=warp(E,*r.x); np.save(sys.argv[1]+'.reg.npy',W)
d=np.abs(ndi.gaussian_filter(W,(1.5,1.5,0))-ndi.gaussian_filter(O,(1.5,1.5,0))).max(2)
print('bg diff outside fig+40: mean',d[far].mean().round(2),'p99',np.percentile(d[far],99).round(1))
vis=np.hstack([O,W,np.dstack([np.clip(d*4,0,255)]*3)*0.7+np.dstack([M*255]*3)*0.3])
Image.fromarray(vis.clip(0,255).astype(np.uint8)).save(sys.argv[1]+'_diff.jpg')
