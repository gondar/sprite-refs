# despill.py NAME : the outline in this style is warm brown (B < G < R); H3's blue ground bleeds into the outermost
# 1-2 px as a teal/blue rim. On those pixels clamp B to 0.9*G and G to R. Rewrites prev/NAME_sheet.png and stage/NAME.webp.
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
nm=sys.argv[1]
x=np.asarray(Image.open(f'prev/{nm}_sheet.png').convert('RGBA')).astype(float)
al=x[...,3]; edge=(al>0)&(ndi.distance_transform_edt(al>=128)<=2.5)
r,g,b=x[...,0],x[...,1],x[...,2]
nb=np.where(edge,np.minimum(b,0.9*g),b); ng=np.where(edge,np.minimum(g,r),g)
before=((b>r+10)&(b>g)&edge).sum()
x[...,1]=ng; x[...,2]=nb
im=Image.fromarray(np.round(x).clip(0,255).astype(np.uint8),'RGBA')
im.save(f'prev/{nm}_sheet.png',optimize=True); im.save(f'stage/{nm}.webp','WEBP',quality=88,alpha_quality=100,method=6)
print(nm,'bluish edge px fixed',int(before))
