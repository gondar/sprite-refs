import numpy as np, json
from PIL import Image
from scipy import ndimage
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
F=np.array(Image.open('S5_full_new2.png').convert('RGB')).astype(float)
P=np.array(Image.open(S+'scripts/i5/S5v3/work/S5_plate.png').convert('RGB')).astype(float)
H,W=F.shape[:2]
J=json.load(open(S+'pub/i5/S5.json'))
fr=[f for f in J['figs'] if f['name']=='frontr'][0]
L=Image.open(S+'pub/i5/S5_fig_frontr.png'); x0=round(fr['bbox'][0]*W); y0=round(fr['bbox'][1]*H)
A=np.zeros((H,W)); A[y0:y0+L.height,x0:x0+L.width]=np.array(L)[...,3]/255.
# edit region in full coords
em=np.zeros((H,W)); em[314:768,556:1161]=np.array(Image.open('mask_s5.png'))/255.
d=ndimage.gaussian_filter(np.abs(ndimage.gaussian_filter(F,(1.5,1.5,0))-ndimage.gaussian_filter(P,(1.5,1.5,0))).max(2),1.5)
R=np.zeros((H,W),bool); R[400:768,680:940]=True
m=(d>18)&R
m=ndimage.binary_closing(m,iterations=5); m=ndimage.binary_fill_holes(m); m=ndimage.binary_opening(m,iterations=3)
lab,n=ndimage.label(m); sz=ndimage.sum(m,lab,range(1,n+1)); m=lab==(np.argmax(sz)+1)
m=ndimage.binary_fill_holes(m)
np.save('newfig_m.npy',m)
ov=F.copy(); ov[~m]*=0.35
Image.fromarray(ov[380:768,640:1000].astype(np.uint8)).resize((720,776)).save('newfig_ov.jpg')
# watershed figure vs background
grad=ndimage.gaussian_gradient_magnitude(F.mean(2),1.2)
cost=np.clip(grad*4,0,250).astype(np.uint8)
mk=np.zeros((H,W),np.int16)
mk[(d<10)]=2
mk[:425,:]=2
AN=A.copy(); AN[:, :925]=0; mk[AN>0.5]=2
X0,X1,Y0,Y1=680,940,400,768
mk[Y0:Y1,X0:X0+3]=2; mk[Y0:Y1,X1-3:X1]=2
mk[548:690,745:905]=1; mk[665:700,705:720]=1; mk[445:505,795:845]=1; mk[505:548,785:860]=1
sub=cost[Y0:Y1,X0:X1]; smk=mk[Y0:Y1,X0:X1].copy()
lab=ndimage.watershed_ift(sub,smk)
fm=np.zeros((H,W),bool); fm[Y0:Y1,X0:X1]=lab==1
fm=ndimage.binary_fill_holes(fm)
np.save('newfig_m.npy',fm)
ov=F.copy(); ov[~fm]*=0.35
Image.fromarray(ov[380:768,640:1000].astype(np.uint8)).resize((720,776)).save('newfig_ov.jpg')

fm=ndimage.binary_closing(fm,iterations=2)&R
alpha=np.maximum(AN, ndimage.gaussian_filter(fm.astype(float),0.8)*(ndimage.binary_dilation(fm,iterations=1)))
# keep neighbour exactly as before; new fig alpha
ys,xs=np.where(alpha>0.004); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
rgba=np.dstack([F[y0:y1,x0:x1],alpha[y0:y1,x0:x1]*255]).round().clip(0,255).astype(np.uint8)
Image.fromarray(rgba,'RGBA').save('S5_fig_frontr_new.png',optimize=True)
bb=[round(x0/W,4),round(y0/H,4),round((x1-x0)/W,4),round((y1-y0)/H,4)]
print('bbox',bb,(x0,y0,x1-x0,y1-y0))
json.dump(dict(bbox=bb,px=[int(x0),int(y0)]),open('frontr_bb.json','w'))
# plate
PL=np.array(Image.open(S+'pub/i5/S5_plate.jpg').convert('RGB')).astype(float)
D=ndimage.gaussian_filter(ndimage.binary_dilation(fm,iterations=5).astype(float),2)[...,None]
emd=ndimage.gaussian_filter(np.maximum(em,ndimage.binary_dilation(fm,iterations=14)),3)[...,None]
base=PL*(1-emd)+F*emd
PN=P*D+base*(1-D)
Image.fromarray(PN.clip(0,255).astype(np.uint8)).save('S5_plate_new.png')
