# C1 stone: mask from |plate - plate_without_stone| (both edits of the same frame), RGB from full.
import numpy as np, json
from PIL import Image
from scipy import ndimage
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/i5/'
f=np.array(Image.open(P+'C1_full.jpg')).astype(float); H,W=f.shape[:2]
pl=np.array(Image.open(P+'C1_plate.jpg')).astype(float)
ns=np.array(Image.open(P+'C1_gen_nostone_raw.png').convert('RGB')).astype(float)
d=ndimage.gaussian_filter(np.abs(pl-ns).max(2),2)
m=d>22; box=np.zeros_like(m); box[250:570,200:520]=1; m&=box
m=ndimage.binary_opening(m,iterations=2)
lab,n=ndimage.label(m); s=ndimage.sum(np.ones_like(m),lab,range(1,n+1)); m=lab==(1+np.argmax(s))
m=ndimage.binary_fill_holes(ndimage.binary_closing(m,iterations=5))
# fit circle to mask, intersect with disc (+2px) to drop stray changed rock
ys,xs=np.where(m); cy,cx=ys.mean(),xs.mean()
yy,xx=np.mgrid[:H,:W]
print('centre',round(cx),round(cy),'bbox',xs.min(),xs.max(),ys.min(),ys.max())
a=ndimage.gaussian_filter(m.astype(float),0.8)
y0,y1,x0,x1=ys.min()-3,ys.max()+4,xs.min()-3,xs.max()+4
Image.fromarray(np.dstack([f,a*255])[y0:y1,x0:x1].round().astype(np.uint8),'RGBA').save(P+'C1_fig_stone.png',optimize=True)
hole=ndimage.gaussian_filter(ndimage.binary_dilation(m,iterations=10).astype(float),4)[...,None]
out=pl*(1-hole)+ns*hole
Image.fromarray(out.round().astype(np.uint8)).save(P+'C1_plate.jpg',quality=82,optimize=True,progressive=True)
bb=[round(x0/W,4),round(y0/H,4),round((x1-x0)/W,4),round((y1-y0)/H,4)]
cen=[round((cx-x0)/(x1-x0),3),round((cy-y0)/(y1-y0),3)]
print(bb,cen); t=json.load(open(P+'C1_bbox_tmp.json')); t['stone']=bb; t['stone_pivot']=cen; json.dump(t,open(P+'C1_bbox_tmp.json','w'))
