# Wycina duchy (Mojżesz, Eliasz) z edycji e1 i nakłada je na stary S4_full jako półprzezroczyste warstwy.
import numpy as np, json, sys
from PIL import Image, ImageFilter
from scipy import ndimage as nd
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
D=S+'/scripts/i5/S4sp/'
o=np.asarray(Image.open(D+'S4_full_before_spirits.jpg').convert('RGB'),float)   # kopia starego S4_full
e=np.asarray(Image.open(D+'e1.jpg').convert('RGB'),float)
e=np.vstack([e[1:],e[-1:]])                                     # edycja jest 1 px niżej
H,W=o.shape[:2]
jes=np.zeros((H,W));J=np.asarray(Image.open(S+'/pub/i5/S4_fig_jesus.png'))[...,3]/255.
x0,y0=round(.5778*W),round(.1901*H);jes[y0:y0+J.shape[0],x0:x0+J.shape[1]]=J
jes=nd.binary_dilation(jes>.2,iterations=3)
d=nd.gaussian_filter(np.abs(e-o).mean(2),2.0)
from PIL import ImageDraw
POLY={'moses':[(680,108),(708,108),(728,150),(792,168),(798,206),(762,228),(732,252),(738,330),(702,378),(606,382),(598,330),(622,250),(632,158),(668,148)],
      'elijah':[(1028,110),(1092,108),(1112,150),(1142,180),(1152,260),(1162,320),(1152,362),(1062,366),(1038,320),(1032,250),(1018,210),(1022,160)]}
FADE={'moses':(335,380),'elijah':(312,362)}
SP={'moses':dict(box=(565,100,800,430),k=.9,lift=.08),'elijah':dict(box=(995,100,1215,425),k=.74,lift=.24)}
full=o.copy();meta={}
for n,c in SP.items():
    X0,Y0,X1,Y1=c['box'];m=np.zeros((H,W),bool);sub=d[Y0:Y1,X0:X1]>7
    sub=nd.binary_closing(sub,iterations=4);sub=nd.binary_fill_holes(sub)
    lab,k=nd.label(sub);sz=nd.sum(sub,lab,range(1,k+1));keep=[i+1 for i,s in enumerate(sz) if s>400]
    sub=np.isin(lab,keep);m[Y0:Y1,X0:X1]=nd.binary_dilation(sub,iterations=5)
    pm=Image.new('L',(W,H),0);ImageDraw.Draw(pm).polygon(POLY[n],fill=1);pm=np.asarray(pm)>0
    m&=pm;m&=~jes
    f0,f1=FADE[n];ramp=np.clip((f1-np.arange(H))/(f1-f0),0,1)[:,None]
    a=nd.gaussian_filter(m.astype(float),3.0)*c['k']*ramp;a[jes]=0
    col=e*(1-c['lift'])+np.array([255,250,232])*c['lift']             # trochę bardziej "światło"
    ys,xs=np.where(a>0.01);P=12;bx0,bx1,by0,by1=xs.min()-P,xs.max()+1+P,ys.min()-P,ys.max()+1+P   # margines na unoszenie
    rgba=np.dstack([col,a*255])[by0:by1,bx0:bx1].clip(0,255).astype('uint8')
    Image.fromarray(rgba,'RGBA').save(S+f'/pub/i5/S4_fig_{n}.png')
    full=full*(1-a[...,None])+col*a[...,None]
    meta[n]=[bx0/W,by0/H,(bx1-bx0)/W,(by1-by0)/H]
Image.fromarray(full.clip(0,255).astype('uint8')).save(S+'/pub/i5/S4_full.jpg',quality=92)
print(json.dumps({k:[round(v,4) for v in b] for k,b in meta.items()}))
