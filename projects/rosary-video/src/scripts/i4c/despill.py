# usage: despill.py IN.png OUT.png  -- kill enclosed green pockets, clamp green spill, drop 1px halo
import sys, numpy as np
from PIL import Image
from scipy import ndimage
a=np.array(Image.open(sys.argv[1]).convert("RGBA")).astype(float)
r,g,b,al=a[...,0],a[...,1],a[...,2],a[...,3]
mx=np.maximum(r,b)
spill=g-mx
pocket=(spill>60)&(g>150)            # nearly pure key colour left inside the figure
al[ndimage.binary_dilation(pocket,iterations=1)]=0
# soften alpha where greenish spill remains on edges
edge=(spill>15)&(al<255)
al[edge]*=np.clip(1-(spill[edge]-15)/80,0,1)
g[:]=np.minimum(g,mx+6)              # despill: green never exceeds max(R,B) by much
# erode alpha by 1px to drop the dark-green halo line
hard=ndimage.binary_erosion(al>128,iterations=1)
al[:]=np.where(hard,al,np.minimum(al,ndimage.uniform_filter(al,3)*0.6))
im=Image.fromarray(np.dstack([r,g,b,al]).clip(0,255).astype(np.uint8),"RGBA")
bb=im.getchannel("A").point(lambda v:255 if v>8 else 0).getbbox(); im=im.crop(bb)
im.save(sys.argv[2],optimize=True); print(sys.argv[2],im.size)
