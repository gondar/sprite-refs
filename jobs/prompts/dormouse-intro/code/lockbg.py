import sys, numpy as np, cv2
from PIL import Image
k0=np.asarray(Image.open('K0_a.png').convert('RGB')).astype(np.float32)
for i in (1,2):
    k=np.asarray(Image.open('K%d_a.png'%i).convert('RGB')).astype(np.float32)
    d=cv2.GaussianBlur(np.abs(k-k0).mean(2),(0,0),3)
    m=(d>14).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(m)
    keep=np.zeros_like(m)
    for j in range(1,n):
        if st[j,4]>1500: keep[lab==j]=1
    keep=cv2.morphologyEx(keep,cv2.MORPH_CLOSE,np.ones((31,31),np.uint8))
    keep=cv2.dilate(keep,np.ones((25,25),np.uint8))
    a=cv2.GaussianBlur(keep.astype(np.float32),(0,0),8)[...,None]
    bg=(1-keep).astype(bool)
    g=(k0[bg].mean(0)+1)/(k[bg].mean(0)+1); print(i,'gain',g.round(3), 'mask frac',keep.mean().round(3))
    kc=np.clip(k*g,0,255)
    out=kc*a+k0*(1-a)
    Image.fromarray(out.round().astype(np.uint8)).save('K%d.png'%i)
    Image.fromarray((a[...,0]*255).astype(np.uint8)).save('mask%d.png'%i)
Image.fromarray(k0.astype(np.uint8)).save('K0.png')
