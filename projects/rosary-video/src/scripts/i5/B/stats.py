import sys,numpy as np
from PIL import Image
for p in sys.argv[1:]:
    im=Image.open(p).convert('RGB'); a=np.asarray(im).astype(float)
    hsv=np.asarray(im.convert('HSV')).astype(float)
    h=hsv[...,0]*360/255; s=hsv[...,1]; v=hsv[...,2]
    sat=s>40*255/100
    warm=((h<50)|(h>340))&sat
    print(p.split('/')[-1],'warm/all %.1f%%'%(100*warm.mean()),'warm/sat %.1f%%'%(100*warm[sat].mean() if sat.any() else 0),'meanRGB',a.reshape(-1,3).mean(0).round(1),'meanV %.1f'%v.mean())
