# sheet.py home closed out cols rows frames closed_idx(comma)  -> WebP q80 sheet; open frames = home exactly
import sys,numpy as np
from PIL import Image
home=np.asarray(Image.open(sys.argv[1]).convert('RGBA')); clo=np.asarray(Image.open(sys.argv[2]).convert('RGBA'))
out=sys.argv[3]; cols,rows,n=map(int,sys.argv[4:7]); cl=set(int(x) for x in sys.argv[7].split(','))
H,W=home.shape[:2]; sh=np.zeros((rows*H,cols*W,4),np.uint8)
for k in range(n):
    r,c=divmod(k,cols); sh[r*H:(r+1)*H,c*W:(c+1)*W]=clo if k in cl else home
Image.fromarray(sh).save(out,'WEBP',quality=80,method=6); print(out,sh.shape,sorted(cl))
