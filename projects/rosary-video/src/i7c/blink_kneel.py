# C2 kneel: tight hand-placed closed eyes (3/4 face; eyes squeezed between contour and nose line)
import numpy as np,cv2,json
from PIL import Image
from scipy import ndimage as ndi
full=cv2.imread('../pub/i5/C2_full.jpg').astype(np.float32)
X0,Y0,X1,Y1=1080,440,1120,472; crop=full[Y0:Y1,X0:X1].copy(); h,w=crop.shape[:2]
Yg,Xg=np.mgrid[0:h,0:w].astype(np.float32); S=8
EYES=[dict(c=(1092.0,452.8),r=(3.4,3.1),skin=None,lo=150,lid=[(1089.6,453.0),(1092.3,454.4),(1095.0,453.4)]),
      dict(c=(1107.5,460.0),r=(5.7,5.9),skin=None,lo=130,lid=[(1102.8,460.6),(1107.5,462.6),(1112.2,460.8)])]
out=crop.copy(); mask=np.zeros((h,w),np.float32)
for e in EYES:
    cx,cy=e['c'][0]-X0,e['c'][1]-Y0; rx,ry=e['r']
    m=(((Xg-cx)/rx)**2+((Yg-cy)/ry)**2)<=1
    if e['skin']: col=np.median(np.array([full[y,x] for x,y in e['skin']]),0); shade=np.broadcast_to(col,crop.shape)
    else:
        ring=((((Xg-cx)/(rx+3))**2+((Yg-cy)/(ry+3))**2)<=1)&~((((Xg-cx)/(rx+1))**2+((Yg-cy)/(ry+1))**2)<=1)
        L=crop.mean(2); ring&=(L>e['lo'])&(L<235)
        wr=ring.astype(np.float32); den=cv2.GaussianBlur(wr,(0,0),2.5)+1e-6
        shade=np.dstack([cv2.GaussianBlur(crop[...,k]*wr,(0,0),2.5)/den for k in range(3)])
    out[m]=shade[m]; mask=np.maximum(mask,m.astype(np.float32))
big=cv2.resize(out,(w*S,h*S),interpolation=cv2.INTER_CUBIC)
dark=(40,48,62)
for e in EYES:
    pts=np.array([[(x-X0)*S+S/2,(y-Y0)*S+S/2] for x,y in e['lid']],np.float32)
    t=np.linspace(0,1,20); p0,p1,p2=pts
    curve=((1-t)[:,None]**2*p0+2*((1-t)*t)[:,None]*p1+(t**2)[:,None]*p2).astype(np.int32)
    cv2.polylines(big,[curve],False,dark,thickness=int(1.4*S),lineType=cv2.LINE_AA)
out=cv2.resize(big,(w,h),interpolation=cv2.INTER_AREA)
a=np.clip(cv2.GaussianBlur(cv2.dilate(mask,np.ones((3,3),np.uint8)),(0,0),0.7)*1.3,0,1)
rgba=np.dstack([cv2.cvtColor(np.clip(out,0,255).astype(np.uint8),cv2.COLOR_BGR2RGB),(a*255).astype(np.uint8)])
Image.fromarray(rgba).save('ov/C2_kneel_blink.png'); json.dump(dict(xy=[X0,Y0]),open('ov/C2_kneel_blink.json','w'))
comp=(crop*(1-a[...,None])+out*a[...,None]).astype(np.uint8)
cv2.imwrite('kneel_new.jpg',cv2.resize(np.hstack([crop.astype(np.uint8),comp]),(w*2*12,h*12),interpolation=cv2.INTER_CUBIC))
