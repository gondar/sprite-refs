# islands.py DIR : keep only the figure — the largest connected component (alpha > 8, bridged by 2 px) and a 3 px
# margin round it; everything else (an insect H3 drew for look_up_follow, faint keying specks) gets alpha 0
import sys, glob, numpy as np
from PIL import Image
from scipy import ndimage as ndi
tot=0
for f in sorted(glob.glob(sys.argv[1]+'/*.png')):
    x=np.asarray(Image.open(f).convert('RGBA')).copy(); al=x[...,3]>8
    lab,n=ndi.label(ndi.binary_dilation(al,iterations=2))
    sz=ndi.sum(al,lab,range(1,n+1)); big=np.argmax(sz)+1
    keep=ndi.binary_dilation((lab==big)&al,iterations=3)
    drop=(x[...,3]>0)&~keep
    if drop.sum(): tot+=int(drop.sum()); x[...,3][drop]=0; x[...,:3][x[...,3]==0]=0; Image.fromarray(x).save(f)
print(sys.argv[1],'px removed',tot)
