import cv2, numpy as np, json
from PIL import Image
P='pub/'
pts=[(555,330),(595,367),(772,377),(680,480),(715,512),(920,477),(947,492),(805,498)]
def fix(im):
    im=im.astype(np.float32)
    # darken white streaks in the beam crop by ~40% toward local background
    x0,y0,x1,y1=480,180,980,560
    L=im.mean(2); bg=cv2.GaussianBlur(im,(0,0),7); Lb=bg.mean(2)
    sat=im.max(2)-im.min(2)
    m=np.zeros(L.shape,np.float32); 
    sub=((L-Lb)>14)&(sat<70)
    m[y0:y1,x0:x1]=sub[y0:y1,x0:x1]
    m=cv2.GaussianBlur(m,(0,0),1.0)*0.4
    im=im*(1-m[...,None])+bg*m[...,None]
    im=im.clip(0,255).astype(np.uint8)
    circ=np.zeros(L.shape,np.uint8)
    for x,y in pts: cv2.circle(circ,(x,y),28,1,-1)
    med=cv2.medianBlur(im,13)
    Lf=im.astype(np.float32).mean(2); Lm=med.astype(np.float32).mean(2)
    line=((Lf-Lm)>7)&(circ>0)
    mk=cv2.dilate(line.astype(np.uint8),np.ones((3,3),np.uint8))&circ
    out=med
    a=np.clip(cv2.GaussianBlur(mk.astype(np.float32),(0,0),0.8)*1.6,0,1)[...,None]
    return (out*a+im*(1-a)).astype(np.uint8)
for f in ['i5/R5_plate.jpg','i6/fx/R5_plate_clean.jpg','i5/R5_full.jpg']:
    im=cv2.imread('scripts/i5/R3R5/bak/'+f.split('/')[-1]); out=fix(im)
    if f.endswith('full.jpg'):   # keep figures' own pixels exactly
        rgb=Image.fromarray(out[...,::-1]).convert('RGBA')
        for g in json.load(open(P+'i5/R5.json'))['figs']:
            x,y=round(g['bbox'][0]*1376),round(g['bbox'][1]*768); rgb.alpha_composite(Image.open(P+g['file']),(x,y))
        out=np.asarray(rgb.convert('RGB'))[...,::-1]
    cv2.imwrite(P+f,out,[cv2.IMWRITE_JPEG_QUALITY,90])
im=cv2.imread(P+'i5/R5_plate.jpg'); cv2.imwrite('scripts/i5/R3R5/z5sp.png',im[180:560,480:980])
