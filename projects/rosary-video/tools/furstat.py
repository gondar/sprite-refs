# python furstat.py <png> x0,y0,x1,y1 [bgbox] -> fur pixels (PIL HSV H 10-35, S>110) mean luma L and S; plus bg ring
import sys,numpy as np
from PIL import Image
im=Image.open(sys.argv[1]).convert('RGB');b=tuple(map(int,sys.argv[2].split(',')))
c=im.crop(b);h=np.asarray(c.convert('HSV')).astype(float);L=np.asarray(c.convert('L')).astype(float)
m=(h[...,0]>=10)&(h[...,0]<=35)&(h[...,1]>110)
print(sys.argv[1].split('/')[-1],'fur n=%d L=%.0f S=%.0f'%(m.sum(),L[m].mean() if m.any() else -1,h[...,1][m].mean() if m.any() else -1),'| box all L=%.0f S=%.0f'%(L[~m].mean(),h[...,1][~m].mean()))
