# C1: Jesus mask = pixels where the green-key edit equals the full image (edit kept him pixel-aligned),
# limited to the |full-plate| region, plus a soft disc for the head halo. RGB from full.
import numpy as np, json
from PIL import Image
from scipy import ndimage
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/i5/'
f=np.array(Image.open(P+'C1_full.jpg')).astype(float); H,W=f.shape[:2]
g=np.array(Image.open(P+'C1_gen_figs_raw.png').convert('RGB')).astype(float)
pl=np.array(Image.open(P+'C1_gen_plate_raw.png').convert('RGB')).astype(float)
same=ndimage.gaussian_filter(np.abs(f-g).max(2),1.2)<34
region=ndimage.binary_dilation(ndimage.gaussian_filter(np.abs(f-pl).max(2),2)>18,iterations=4)
region[:, :int(.40*W)]=0; region[:, int(.62*W):]=0; region[int(.74*H):]=0
m=ndimage.binary_opening(same&region,iterations=1)
lab,n=ndimage.label(m); s=ndimage.sum(np.ones_like(m),lab,range(1,n+1))
m=np.isin(lab,1+np.where(s>400)[0])
m=ndimage.binary_fill_holes(ndimage.binary_closing(m,iterations=4))
m=ndimage.binary_dilation(m,iterations=3)
# staff top/banner: lenient key on the aligned edit (colour comes from full)
kk=g[...,1]-np.maximum(g[...,0],g[...,2])
ka=1-np.clip((kk-60)/(190-60),0,1)
box=np.zeros((H,W),bool); box[195:268,750:800]=1
top=np.where(box,ka,0); top[ndimage.binary_opening(top>0.5,iterations=0 or 1)==0]*=1
yy0,xx0=np.mgrid[:H,:W]
# staff shaft: straight line fitted from the full image
sx=765-0.105*(yy0-320)
shaft=np.clip(3.4-np.abs(xx0-sx),0,1)*((yy0>=240)&(yy0<=534))
m=np.maximum(m.astype(float),np.maximum(top,shaft))
# head halo disc
yy,xx=np.mgrid[:H,:W]
cy,cx=[int(v) for v in __import__('sys').argv[1:3]] if len(__import__('sys').argv)>2 else (300,692)
r=np.hypot(yy-cy,xx-cx)
disc=np.clip((50-r)/8,0,1)
a=np.maximum(ndimage.gaussian_filter(m,0.7),disc)
ys,xs=np.where(a>0.03); y0,y1,x0,x1=ys.min()-2,ys.max()+3,xs.min()-2,xs.max()+3
Image.fromarray(np.dstack([f,a*255])[y0:y1,x0:x1].round().astype(np.uint8),'RGBA').save(P+'C1_fig_jesus.png',optimize=True)
hole=ndimage.gaussian_filter(ndimage.binary_dilation(a>0.03,iterations=18).astype(float),5)[...,None]
plate=f*(1-hole)+pl*hole
Image.fromarray(plate.round().astype(np.uint8)).save(P+'C1_plate.jpg',quality=82,optimize=True,progressive=True)
comp=plate*(1-a[...,None])+f*a[...,None]; err=np.abs(comp-f).mean(2)
print('composite vs full mean',err.mean().round(2),'p99',np.percentile(err,99).round(1))
bb=[round(x0/W,4),round(y0/H,4),round((x1-x0)/W,4),round((y1-y0)/H,4)]; print(bb)
json.dump({'jesus':bb},open(P+'C1_bbox_tmp.json','w'))
mag=np.array([255.,0,255])
chk=np.concatenate([comp,mag*(1-a[...,None])+f*a[...,None]],1)

Image.fromarray(np.concatenate([comp,plate],1).astype(np.uint8)).resize((1376,384)).save(P+'C1_check.jpg',quality=80)
