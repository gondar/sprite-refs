import numpy as np
from PIL import Image
from scipy import ndimage
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
o=np.array(Image.open('crop_in.png').convert('RGB')).astype(float)
E=np.load('ed_reg.npy')
d=ndimage.gaussian_filter(np.abs(E-o).max(2),2)
m=d>22
R=np.zeros_like(m); R[105:454,132:378]=True
m&=R
m=ndimage.binary_closing(m,iterations=6); m=ndimage.binary_fill_holes(m)
lab,n=ndimage.label(m); sz=ndimage.sum(m,lab,range(1,n+1)); m=lab==(np.argmax(sz)+1)
m=ndimage.binary_fill_holes(ndimage.binary_dilation(m,iterations=5))&R
a=ndimage.gaussian_filter(m.astype(float),3)*ndimage.gaussian_filter(R.astype(float),2)
a=a[...,None]
C=E*a+o*(1-a)
full=np.array(Image.open(S+'pub/i5/S5_full.jpg').convert('RGB')).astype(float)
F=full.copy(); F[314:768,556:1161]=C
Image.fromarray(F.astype(np.uint8)).save('S5_full_new.png')
Image.fromarray((a[...,0]*255).astype(np.uint8)).save('mask_s5.png')
v=np.concatenate([o,C],1); Image.fromarray(v.astype(np.uint8)).resize((v.shape[1]*2,v.shape[0]*2),Image.LANCZOS).save('s5_before_after.jpg',quality=88)
ov=C.copy(); ov[a[...,0]<0.05]*=0.4; Image.fromarray(ov.astype(np.uint8)).save('mask_ov.jpg')
