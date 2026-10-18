import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi, optimize
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
X0,Y0,CS=473,0,480
full=np.asarray(Image.open(S+'/pub/i5/C4_full.jpg').convert('RGB')).astype(np.float32)
O=full[Y0:Y0+CS,X0:X0+CS]
E=np.asarray(Image.open(sys.argv[1]).convert('RGB').resize((CS,CS),Image.LANCZOS)).astype(np.float32)
fig=np.asarray(Image.open(S+'/pub/i5/C4_fig_mary.png'))[...,3]
A=np.zeros((CS,CS)); A[26:26+452,602-X0:602-X0+222]=fig/255.
def warp(im,s,dx,dy):
    c=(CS-1)/2
    return np.dstack([ndi.affine_transform(im[...,k],[1/s,1/s],offset=[c-(c+dy)/s,c-(c+dx)/s],order=1,mode='nearest') for k in range(3)])
# register on the region of interest selected by argv[2]: 'feet' = lower Mary (dress hem+feet), 'bg' = outside Mary
Ob=ndi.gaussian_filter(O,(2,2,0)); Eb=ndi.gaussian_filter(E,(2,2,0))
mode=sys.argv[2]
if mode=='bg': W=(ndi.binary_dilation(A>0.05,iterations=20)==0)
else:
    W=np.zeros((CS,CS),bool); W[300:470,120:380]=True
W[:10]=W[-10:]=W[:,:10]=W[:,-10:]=False
f=lambda p: np.abs(warp(Eb,*p)-Ob)[W].mean()
best=min(((f((s,dx,dy)),(s,dx,dy)) for s in (0.98,1.0,1.02) for dx in range(-8,9,2) for dy in range(-8,9,2)))
r=optimize.minimize(f,best[1],method='Nelder-Mead',options=dict(xatol=0.05,fatol=0.01))
print(mode,np.round(r.x,2),'err',round(float(r.fun),2))
np.save('E_%s.npy'%mode,warp(E,*r.x))
