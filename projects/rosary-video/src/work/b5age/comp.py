import numpy as np
from PIL import Image
from scipy import ndimage as ndi
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
cx,cy,cs=816,182,192
full=np.asarray(Image.open(S+'/pub/i5/B5_full.jpg').convert('RGB')).astype(np.float32)
O=full[cy:cy+cs,cx:cx+cs]; E=np.load('Ew.npy')
Y,X=np.mgrid[0:cs,0:cs].astype(np.float32)
# face ellipse in frame px: centre (905,280), radii; slightly rotated head -> generous
fx,fy,rx,ry=905-cx,276-cy,37,43
m=(((X-fx)/rx)**2+((Y-fy)/ry)**2)<=1
m=ndi.gaussian_filter(m.astype(np.float32),3.0)
m=np.clip((m-0.05)/0.9,0,1)
C=O*(1-m[...,None])+E*m[...,None]
np.save('mask.npy',m); np.save('C.npy',C)
d=np.abs(E-O).max(2)
v=np.hstack([O,C,np.dstack([d*3]*3).clip(0,255),np.dstack([m*255]*3)])
Image.fromarray(v.clip(0,255).astype(np.uint8)).resize((v.shape[1]*3,cs*3),Image.LANCZOS).save('cmp.jpg',quality=90)
