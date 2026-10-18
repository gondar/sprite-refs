import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
F=np.array(Image.open('S5_full_new.png').convert('RGB')).astype(float)
hair=np.median(F[440:470,800:840].reshape(-1,3),0); print('hair',hair)
col=hair*1.3+np.array([8,4,0])
m=Image.new('L',(1376,768),0); d=ImageDraw.Draw(m)
d.polygon([(789,492),(797,493),(800,506),(799,518),(794,523),(788,514),(786,502)],fill=255)
d.polygon([(842,493),(850,492),(853,502),(851,514),(845,523),(840,518),(839,506)],fill=255)
a=ndimage.gaussian_filter(np.array(m).astype(float)/255,0.8)[...,None]*0.95
# strand texture: darker vertical streaks
yy,xx=np.mgrid[0:768,0:1376]; tex=1-0.12*(np.sin(xx*2.1+yy*0.4)>0.6)
C=col*tex[...,None]
F2=F*(1-a)+C*a
Image.fromarray(F2.clip(0,255).astype(np.uint8)).save('S5_full_new2.png')
Image.fromarray(F2[420:560,740:900].clip(0,255).astype(np.uint8)).resize((640,560),Image.LANCZOS).save('head2_x4.jpg')
