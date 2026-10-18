# usage: tight.py ID -> work/ID_tight.png : inside diff mask, keep regions enclosed by the figure's pencil outline
import sys, numpy as np
from PIL import Image
from scipy import ndimage
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/scripts/i5/work/'
i=sys.argv[1]; ET=float(sys.argv[2]) if len(sys.argv)>2 else 25
f=np.array(Image.open(S+f'{i}_full.png').convert('RGB')).astype(float)
M=np.array(Image.open(S+f'{i}_mask.png'))>0
L=f.mean(2)
# dark line detection: darker than local surroundings
E=(ndimage.uniform_filter(L,9)-L)>ET
E=ndimage.binary_closing(E,iterations=1)
R=M&~E
lab,n=ndimage.label(R)
border=M&~ndimage.binary_erosion(M,iterations=2)
touch=np.unique(lab[border]); touch=touch[touch>0]
keep=np.isin(lab,np.setdiff1d(np.arange(1,n+1),touch))
k=keep|(E&M&ndimage.binary_dilation(keep,iterations=3))
k=ndimage.binary_closing(k,iterations=2); k=ndimage.binary_fill_holes(k)
k=ndimage.binary_opening(k,iterations=1)
l2,n2=ndimage.label(k); sz=ndimage.sum(k,l2,range(1,n2+1))
k=np.isin(l2,[j+1 for j in range(n2) if sz[j]>300])
Image.fromarray((k*255).astype(np.uint8)).save(S+f'{i}_tight.png')
ov=f.copy(); ov[~k]*=0.2; ov[M&~k]=ov[M&~k]*0+[255,0,0]
Image.fromarray(ov.astype(np.uint8)).save(S+f'{i}_tightov.jpg',quality=85)
print(M.sum(),k.sum())
