# restore the painted floor shadows under Simeon's and Joseph's feet in the R4 plate
import json,numpy as np,cv2
from PIL import Image
from scipy import ndimage as ndi
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
W,H=1376,768
plate=np.asarray(Image.open(S+'work/fix8/R4/R4_plate_clean_orig.jpg').convert('RGB')).astype(np.float32)
full=np.asarray(Image.open(S+'pub/i5/R4_full.jpg').convert('RGB')).astype(np.float32)
J=json.load(open(S+'pub/i5/R4.json')); A=np.zeros((H,W),np.float32)
for f in J['figs']:
    a=np.asarray(Image.open(S+'pub/'+f['file']).convert('RGBA'))[...,3].astype(np.float32)/255
    x0,y0=round(f['bbox'][0]*W),round(f['bbox'][1]*H); h,w=a.shape
    A[y0:y0+h,x0:x0+w]=np.maximum(A[y0:y0+h,x0:x0+w],a[:H-y0,:W-x0])
band=np.zeros((H,W),bool)
band[650:716,395:625]=True; band[650:716,955:1095]=True
# 1) uncovered floor: take the painting itself
free=band&(A<0.05)
out=plate.copy(); out[free]=full[free]
# 2) under the figures: inpaint the shadow RATIO full/plate (smooth field) and apply it to the plate texture,
#    so a moving figure reveals shadowed floor with intact stone cracks, not a bright smear
hole=(band&(A>=0.05))
ratio=np.ones((H,W,3),np.float32); ratio[free]=(full[free]+4)/(plate[free]+4)
r8=np.clip(ratio*128,0,255).astype(np.uint8)
ri=cv2.inpaint(r8,hole.astype(np.uint8)*255,15,cv2.INPAINT_TELEA).astype(np.float32)/128
ri=np.stack([ndi.gaussian_filter(ri[...,c],3) for c in range(3)],-1)
rh=np.where(hole[...,None],ri,ratio)
out[hole]=plate[hole]*rh[hole]
# 3) feather the band edge into the old plate (8 px) so the rectangle itself leaves no seam
wgt=ndi.gaussian_filter(band.astype(np.float32),4); wgt=np.where(band,np.maximum(wgt,0.5),wgt); wgt=np.clip((wgt-0.0)*1.0,0,1)
wgt[free]=1.0
res=plate*(1-wgt[...,None])+out*wgt[...,None]
im=Image.fromarray(np.clip(np.round(res),0,255).astype(np.uint8))
im.save(S+'pub/i6/fx/R4_plate_clean.jpg',quality=95); im.save(S+'pub/i5/R4_plate.jpg',quality=95)
print('free px',free.sum(),'inpainted px',hole.sum())
