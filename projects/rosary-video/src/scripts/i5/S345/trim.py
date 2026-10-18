# trim.py: drop ground/shadow/prop areas from the figure masks (they stay in the plate as full pixels)
import numpy as np
from scipy import ndimage
from PIL import Image
W='work/'
Y,X=np.mgrid[0:768,0:1376]
EX={'S3':[(X<440)&(Y>455),(Y>645),(Y>600)&((X<500)|(X>610))&(X<740),(X>860)&(X<905)&(Y>450)&(Y<545),
          (X>740)&(X<870)&(Y>614),(X>1150)&(Y>560)],
    'S4':[(Y>432)&(X>690),(Y>640)&(X<380),(X>380)&(X<420)&(Y>470)&(Y<520),(X<375)&(Y>640)],
    'S5':[(X<600)&(Y>615),(X>690)&(X<1010)&(Y>548),(X>940)&(X<990)&(Y>518),(X>1270)&(Y>560),(X>1010)&(Y>650)]}
for s,ex in EX.items():
    M=np.asarray(Image.open(W+f'{s}_mask.png'))>0
    if not __import__('os').path.exists(W+f'{s}_mask_orig.png'): Image.fromarray((M*255).astype(np.uint8)).save(W+f'{s}_mask_orig.png')
    M=np.asarray(Image.open(W+f'{s}_mask_orig.png'))>0
    E=np.zeros_like(M)
    for e in ex: E|=e
    Image.fromarray(((E&ndimage.binary_dilation(M,iterations=12))*255).astype(np.uint8)).save(W+f'{s}_excl.png')
    M=M&~E
    Image.fromarray((M*255).astype(np.uint8)).save(W+f'{s}_mask.png'); print(s,M.sum())
