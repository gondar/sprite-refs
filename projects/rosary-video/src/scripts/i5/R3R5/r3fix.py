from PIL import Image; import numpy as np
from scipy import ndimage as ndi
im=Image.open('R3_full_a_orig.jpg').convert('RGB'); a=np.asarray(im).astype(float); H,W=a.shape[:2]
hsv=np.asarray(im.convert('HSV')).astype(float)
Y,X=np.mgrid[0:H,0:W]
def ell(cx,cy,rx,ry): return (((X-cx)/rx)**2+((Y-cy)/ry)**2)<=1
face=ell(1118,318,50,48)
skin=face&(hsv[...,1]>40)&(hsv[...,2]>120)
s=hsv[...,1]; h=hsv[...,0]
ref=np.median(s[skin]); print('median skin sat',ref)
cheeks=ell(1092,323,17,14)|ell(1146,335,17,14)
red=cheeks&(hsv[...,2]>110)&((h<14)|(h>240))&(s>ref+6)
m=ndi.gaussian_filter(ndi.binary_closing(red,iterations=3).astype(float),4); m=np.clip(m*2.2,0,1)*ndi.binary_dilation(cheeks,iterations=3)*(hsv[...,2]>100)
# pull colour toward skin: reduce chroma
lum=a.mean(2,keepdims=True)
skincol=np.median(a[skin&~red],axis=0); print('skin',skincol)
ok=(skin&~ndi.binary_dilation(red,iterations=4)).astype(float)
ll=ndi.gaussian_filter(lum[...,0]*ok,9)/(ndi.gaussian_filter(ok,9)+1e-6)
ll=ll[...,None]
target=(skincol/skincol.mean())*ll
out=a*(1-m[...,None]*0.85)+target*m[...,None]*0.85
# slightly paler overall face
pale=ndi.gaussian_filter(face.astype(float),6)[...,None]
out=out*(1-0.10*pale)+ (out.mean(2,keepdims=True))*0.10*pale
# soft warm glow around baby head, additive, small
cx,cy,r=1020,392,62
d=np.sqrt((X-cx)**2+(Y-cy)**2)/r
g=np.exp(-d**2*1.6)*(d<2.2)
warm=np.array([255,196,120])
out=out+(g[...,None]*0.32)*(warm-out)*0.9
o=Image.fromarray(out.clip(0,255).astype(np.uint8)); o.save('R3_full_c.jpg',quality=92)
o.crop((940,220,1240,500)).resize((600,560)).save('z3c.png')
print('red px',red.sum())
