# R1: remove stone wall/grass from Mary's lower mask by colour (pink robe vs stone/grass)
import numpy as np
from PIL import Image
from scipy import ndimage
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/scripts/i5/work/'
f=np.array(Image.open(S+'R1_full.png').convert('RGB')).astype(float)
M=np.array(Image.open(S+'R1_mask.png'))>0
r,g,b=f[...,0],f[...,1],f[...,2]
H,W=M.shape
zone=np.zeros_like(M); zone[545:,830:]=True; zone[505:545,990:]=True
pink=(r-g>18)&(r-b>8)
dark=f.mean(2)<110   # pencil lines
body=pink|dark
body=ndimage.binary_closing(body,iterations=2)
z=M&zone
keepz=z&body
# keep only parts connected to Mary's upper body
keepz=ndimage.binary_opening(keepz,iterations=2)
lab,n=ndimage.label(keepz); sz=ndimage.sum(keepz,lab,range(1,n+1))
keepz=lab==(np.argmax(sz)+1)
keepz=ndimage.binary_fill_holes(ndimage.binary_closing(keepz,iterations=3))
keepz=ndimage.binary_dilation(keepz,iterations=2)&z
M2=(M&~zone)|keepz
Image.fromarray((M2*255).astype(np.uint8)).save(S+'R1_mask.png')
ov=f.copy(); ov[~M2]*=0.2; ov[M&~M2]=[255,0,0]
Image.fromarray(ov.astype(np.uint8)).crop((650,150,1200,740)).save(S+'R1_fixov.jpg',quality=85)
