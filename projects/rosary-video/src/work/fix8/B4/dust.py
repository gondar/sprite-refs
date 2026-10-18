# cut the painted dust swirls of B4 into soft-alpha sway layers and unmix them out of the plate
import json,numpy as np,cv2
from PIL import Image
from scipy import ndimage as ndi
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
W,H=1376,768
I=np.asarray(Image.open(S+'work/fix8/B4_plate_clean_orig.jpg').convert('RGB')).astype(np.float32)
P0=np.asarray(Image.open(S+'work/fix8/B4_plate_clean_orig.jpg').convert('RGB')).astype(np.float32)
L=I.mean(2); sat=I.max(2)-I.min(2)
D=lambda pts,o,sc=2:[(o[0]+x/sc,o[1]+y/sc) for x,y in pts]
STROKES={'dustL':[(D([(40,245),(120,272),(180,290),(250,290),(320,270),(380,230),(415,190),(440,150),(462,115),(490,95),(530,95),(548,125),(532,155),(500,160),(482,140),(497,118),(515,118)],(120,310)),32),
                  (D([(545,135),(600,142),(650,128),(700,108),(760,92),(820,85)],(120,310)),34),
                  (D([(430,92),(470,78),(520,72),(570,80)],(120,310)),20)],
         'dustR':[]}
DISCS={'dustR':[(1117,168,66)],'dustL':[(372,372,34)]}
POLYS={'dustL':[D([(540,105),(830,78),(830,215),(540,178)],(120,310))],'dustR':[[(985,222),(1060,210),(1125,215),(1185,195),(1236,182),(1236,214),(1160,232),(1085,248),(985,254)]]}
REG={'dustL':(128,318,530,488),'dustR':(975,95,1242,262)}
out=P0.copy(); info={}
for nm,(x0,y0,x1,y1) in REG.items():
    sl=(slice(y0,y1),slice(x0,x1)); Ls=L[sl]
    Mk=np.zeros((H,W),np.uint8)
    for st,th in STROKES[nm]: cv2.polylines(Mk,[np.array(st,np.int32)],False,255,th,cv2.LINE_AA)
    for (cx,cy,r) in DISCS.get(nm,[]): cv2.circle(Mk,(cx,cy),r,255,-1,cv2.LINE_AA)
    for poly in POLYS.get(nm,[]): cv2.fillPoly(Mk,[np.array(poly,np.int32)],255,cv2.LINE_AA)
    mk=np.clip(ndi.gaussian_filter(ndi.binary_dilation(Mk>0,iterations=8).astype(np.float32),5)*1.2,0,1)[sl]
    # wall without dust: inpaint each channel under the dilated mask (smooth), keep the painting's fine detail
    hole=(ndi.binary_dilation(Mk>0,iterations=16)).astype(np.uint8)*255
    I8=np.clip(I,0,255).astype(np.uint8); bgf=cv2.inpaint(I8,hole,21,cv2.INPAINT_TELEA).astype(np.float32)
    bg=np.stack([ndi.gaussian_filter(bgf[...,k],6) for k in range(3)],-1)[sl]
    Is=I[sl]; lo=np.stack([ndi.gaussian_filter(Is[...,k],2) for k in range(3)],-1)
    E=np.clip(lo-bg,0,None)*mk[...,None]          # low-frequency dust excess
    ex=E.mean(2); K=max(np.percentile(ex[mk>0.5],99.5)/0.7,6)
    a=np.clip(ex/K,0,0.75); a=ndi.gaussian_filter(a,1.0); a[a<0.03]=0
    yy,xx=np.mgrid[y0:y1,x0:x1]; e=np.minimum.reduce([xx-x0,x1-1-xx,yy-y0,y1-1-yy]).astype(np.float32); a*=np.clip(e/14,0,1)
    Pm=Is-E                                         # plate: dust haze removed, detail kept
    # layer colour so that plate*(1-a)+col*a == painting exactly
    col=np.where(a[...,None]>0.02,Pm+(Is-Pm)/np.maximum(a[...,None],0.02),Pm)
    col=np.clip(col,0,255); 
    out[sl]=Pm
    c=col[a>0.3].mean(0)
    A=np.zeros((H,W),np.float32); A[sl]=a
    rgba=np.zeros((y1-y0,x1-x0,4),np.uint8); rgba[...,:3]=np.clip(np.round(col),0,255); rgba[...,3]=np.clip(a*255,0,255)
    Image.fromarray(rgba).save(S+'pub/i6/fx/B4_%s.png'%nm)
    info[nm]=dict(bbox=[round(x0/W,4),round(y0/H,4),round((x1-x0)/W,4),round((y1-y0)/H,4)],col=[round(float(v)) for v in c],amax=round(float(a.max()),2),px=int((a>0.1).sum()))
    # composite check
    comp=out[sl]*(1-a[...,None])+np.round(col)*a[...,None]; info[nm]['comp_err']=round(float(np.abs(comp-I[sl]).mean()),2)
Image.fromarray(np.clip(np.round(out),0,255).astype(np.uint8)).save(S+'pub/i6/fx/B4_plate_clean.jpg',quality=95)
print(json.dumps(info))
